# scripts/backfill_geo_history.py
from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Dict, Optional, List

import pandas as pd
import yfinance as yf


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "macro_data.csv"

# ✅ Geo EW + Geo proxies (backfill 대상)
GEO_TICKERS: Dict[str, str] = {
    "GOLD": "GC=F",
    "USDCNH": "CNH=X",
    "USDJPY": "JPY=X",
    "USDMXN": "MXN=X",
    "SEA": "SEA",
    "BDRY": "BDRY",
    "ITA": "ITA",
    "XAR": "XAR",
    "EEM": "EEM",
    "EMB": "EMB",
    # 원하면 아래도 backfill 가능 (이미 today는 들어오니까 과거 채우기용)
    "QQQ": "QQQ",
    "SPY": "SPY",
}

DEFAULT_LOOKBACK_DAYS = 120  # trading day 감안해서 넉넉히
OUT_COL_DATE = "date"        # generate_report가 쓰는 컬럼
ALT_COL_DATE = "datetime"    # 같이 존재할 수 있음


def _read_macro_csv() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"macro_data.csv not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)

    # date/datetime 처리: 둘 다 있으면 date 우선
    if OUT_COL_DATE in df.columns:
        df[OUT_COL_DATE] = pd.to_datetime(df[OUT_COL_DATE], errors="coerce")
    elif ALT_COL_DATE in df.columns:
        df[OUT_COL_DATE] = pd.to_datetime(df[ALT_COL_DATE], errors="coerce")
    else:
        raise ValueError("macro_data.csv must contain 'date' or 'datetime' column")

    df = df.dropna(subset=[OUT_COL_DATE]).sort_values(OUT_COL_DATE).reset_index(drop=True)
    return df


def _download_history(ticker: str, lookback_days: int) -> pd.Series:
    """
    Returns: Series indexed by date (datetime64[ns], normalized), values=Close(float)
    """
    df = yf.download(
        ticker,
        period=f"{lookback_days}d",
        interval="1d",
        progress=False,
        group_by="column",
        threads=False,
        auto_adjust=False,
    )

    if df is None or df.empty:
        return pd.Series(dtype="float64")

    # MultiIndex 방어
    if isinstance(df.columns, pd.MultiIndex):
        # pick Close block
        close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
        if not close_cols:
            return pd.Series(dtype="float64")
        close_block = df[close_cols]
        # ticker 하나면 (Close, TICKER) 형태일 수 있음
        # 마지막 컬럼을 선택
        if close_block.shape[1] >= 1:
            s = close_block.iloc[:, -1]
        else:
            return pd.Series(dtype="float64")
    else:
        if "Close" in df.columns:
            s = df["Close"]
        else:
            # close 소문자 방어
            cands = [c for c in df.columns if str(c).lower() == "close"]
            if not cands:
                return pd.Series(dtype="float64")
            s = df[cands[0]]

    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return pd.Series(dtype="float64")

    # index normalize to date only
    idx = pd.to_datetime(s.index, errors="coerce").normalize()
    s.index = idx
    s = s[~s.index.isna()]
    return s.astype("float64")


def main(lookback_days: int = DEFAULT_LOOKBACK_DAYS) -> None:
    df = _read_macro_csv()

    # ✅ 백업
    bak_path = CSV_PATH.with_suffix(".csv.bak")
    df.to_csv(bak_path, index=False)
    print(f"[OK] backup saved -> {bak_path}")

    # macro_data 날짜 축: normalize 해서 merge 키로 쓰기
    df["_d"] = pd.to_datetime(df[OUT_COL_DATE], errors="coerce").dt.normalize()
    df = df.dropna(subset=["_d"]).sort_values("_d").reset_index(drop=True)

    min_d = df["_d"].min()
    max_d = df["_d"].max()
    print(f"[INFO] macro date range: {min_d.date()} ~ {max_d.date()}")

    # backfill 결과를 담을 DataFrame (키=_d)
    backfill = pd.DataFrame({"_d": pd.date_range(min_d, max_d, freq="D")})
    backfill["_d"] = pd.to_datetime(backfill["_d"]).dt.normalize()

    # ✅ 각 티커 다운로드 후 join
    for col, ticker in GEO_TICKERS.items():
        print(f"[FETCH] {col} ({ticker}) ...")
        s = _download_history(ticker, lookback_days)

        if s.empty:
            print(f"  -> WARN: no history for {col}")
            continue

        tmp = s.rename(col).to_frame().reset_index().rename(columns={"index": "_d"})
        tmp["_d"] = pd.to_datetime(tmp["_d"], errors="coerce").dt.normalize()
        tmp = tmp.dropna(subset=["_d"]).drop_duplicates(subset=["_d"], keep="last")

        backfill = backfill.merge(tmp, on="_d", how="left")

        print(f"  -> OK: {col} rows={tmp[col].notna().sum()}")

    # ✅ 기존 df와 merge해서, 기존 값이 있으면 유지 / 없으면 backfill로 채움
    merged = df.merge(backfill, on="_d", how="left", suffixes=("", "_bf"))

    # 채우기 로직: df에 col이 없으면 새로 만들고, 있으면 NaN만 채움
    for col in GEO_TICKERS.keys():
        bf_col = col  # backfill DF에 들어온 컬럼 이름
        if bf_col not in merged.columns:
            continue

        if col not in df.columns:
            # 새 컬럼이면 그대로 채택
            merged[col] = merged[bf_col]
        else:
            # 기존에 컬럼이 있으면 NaN만 채움
            merged[col] = merged[col].where(merged[col].notna(), merged[bf_col])

        # backfill 임시 컬럼 제거(중복이면 같은 이름이라 제거 불가 → 아래에서 안전 처리)
        # (여기서는 bf_col과 col이 동일하므로 추가로 뺄 게 없음)

    # 정리
    merged = merged.drop(columns=["_d"], errors="ignore")

    # ✅ date / datetime 둘 다 있을 때 일관성: 둘 다 있으면 유지, 없으면 생성
    if OUT_COL_DATE not in merged.columns:
        raise ValueError("after merge, 'date' column missing (unexpected)")

    # 저장
    merged.to_csv(CSV_PATH, index=False)
    print(f"[OK] macro_data.csv updated -> {CSV_PATH}")
    print("[DONE] Geo history backfilled safely (existing data preserved).")


if __name__ == "__main__":
    main()
