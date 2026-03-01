from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "macro_data.csv"

KST = timezone(timedelta(hours=9))

# ✅ allow fallback tickers for flaky series (CNH especially)
GEO_TICKERS: Dict[str, List[str]] = {
    "GOLD": ["GC=F"],
    "USDCNH": ["CNH=X", "CNY=X"],  # try offshore first then onshore
    "USDJPY": ["JPY=X"],
    "USDMXN": ["MXN=X"],
    "SEA": ["SEA"],
    "BDRY": ["BDRY"],
    "ITA": ["ITA"],
    "XAR": ["XAR"],
    "EEM": ["EEM"],
    "EMB": ["EMB"],
    "QQQ": ["QQQ"],
    "SPY": ["SPY"],
}

LOOKBACK_DAYS = 180  # 넉넉히 (원하면 120으로 다시)


def _safe_close_series_from_download(df: pd.DataFrame) -> Optional[pd.Series]:
    """yfinance download df에서 Close series를 robust하게 뽑아옴."""
    if df is None or df.empty:
        return None

    # MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
        if not close_cols:
            return None
        # take last close column
        s = df[close_cols].iloc[:, -1]
        return pd.to_numeric(s, errors="coerce")

    # normal columns
    if "Close" in df.columns:
        return pd.to_numeric(df["Close"], errors="coerce")

    # fallback: any close-like col
    cands = [c for c in df.columns if str(c).lower() == "close"]
    if cands:
        return pd.to_numeric(df[cands[0]], errors="coerce")

    return None


def _download_close_series(
    ticker: str,
    start: str,
    end: str,
) -> pd.DataFrame:
    """
    start/end 범위로 daily close를 받아서
    date_key(정규화 날짜) + value 반환
    """
    # 1) download path
    try:
        df = yf.download(
            ticker,
            start=start,
            end=end,
            interval="1d",
            progress=False,
            auto_adjust=False,
            group_by="column",
            threads=False,
        )
        s = _safe_close_series_from_download(df)
        if s is not None:
            s = s.dropna()
            if not s.empty:
                out = pd.DataFrame({
                    "date_key": pd.to_datetime(s.index, errors="coerce").normalize(),
                    "value": s.values
                }).dropna(subset=["date_key"])
                if not out.empty:
                    return out
    except Exception:
        pass

    # 2) fallback: Ticker().history (FX에서 더 잘 될 때가 많음)
    try:
        hist = yf.Ticker(ticker).history(start=start, end=end, interval="1d", auto_adjust=False)
        if hist is None or hist.empty or "Close" not in hist.columns:
            return pd.DataFrame()
        s2 = pd.to_numeric(hist["Close"], errors="coerce").dropna()
        if s2.empty:
            return pd.DataFrame()
        out = pd.DataFrame({
            "date_key": pd.to_datetime(s2.index, errors="coerce").normalize(),
            "value": s2.values
        }).dropna(subset=["date_key"])
        return out
    except Exception:
        return pd.DataFrame()


def _coerce_column_to_numeric_nan(df: pd.DataFrame, col: str) -> None:
    """
    ✅ 핵심: 빈문자열/공백/'nan'문자 등도 모두 NaN으로 만든 뒤 numeric으로 변환.
    이게 없으면 where(notna()) 때문에 backfill이 막힌다.
    """
    if col not in df.columns:
        return
    df[col] = df[col].replace(["", " ", "  ", "nan", "NaN", "None"], pd.NA)
    df[col] = pd.to_numeric(df[col], errors="coerce")


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError("macro_data.csv not found")

    df = pd.read_csv(CSV_PATH)
    df = df.loc[:, ~df.columns.duplicated()].copy()

    # date 정규화
    if "date" in df.columns:
        base_dt = pd.to_datetime(df["date"], errors="coerce")
    elif "datetime" in df.columns:
        base_dt = pd.to_datetime(df["datetime"], errors="coerce")
        df["date"] = base_dt
    else:
        raise ValueError("No date/datetime column found in macro_data.csv")

    df["date_key"] = pd.to_datetime(base_dt, errors="coerce").dt.normalize()
    df = df.dropna(subset=["date_key"]).sort_values("date_key").reset_index(drop=True)

    # backup
    ts = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
    backup = CSV_PATH.with_suffix(f".csv.bak_{ts}")
    df.to_csv(backup, index=False)
    print(f"[OK] backup saved -> {backup}")

    # fetch range: df의 실제 범위 기반 + LOOKBACK_DAYS 제한
    max_d = df["date_key"].max()
    min_d = max_d - pd.Timedelta(days=LOOKBACK_DAYS)
    start = min_d.strftime("%Y-%m-%d")
    end = (max_d + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"[INFO] backfill window: {start} ~ {end} (LOOKBACK_DAYS={LOOKBACK_DAYS})")

    # ✅ 먼저 컬럼들을 numeric으로 coercion (backfill 막힘 방지)
    for col in GEO_TICKERS.keys():
        if col in df.columns:
            _coerce_column_to_numeric_nan(df, col)

    # download + merge
    for col, tickers in GEO_TICKERS.items():
        print(f"\n[FETCH] {col} tickers={tickers}")

        hist = pd.DataFrame()
        used = None
        for t in tickers:
            tmp = _download_close_series(t, start=start, end=end)
            if tmp is not None and not tmp.empty:
                hist = tmp
                used = t
                break

        if hist.empty:
            print("  -> no data")
            continue

        hist = hist.rename(columns={"value": col}).drop_duplicates(subset=["date_key"], keep="last")
        print(f"  -> got {len(hist)} rows (source={used})")

        # ensure target col exists
        if col not in df.columns:
            df[col] = pd.NA
            _coerce_column_to_numeric_nan(df, col)

        df = df.merge(hist, on="date_key", how="left", suffixes=("", "_bf"))

        # ✅ fill only where original is NaN
        df[col] = df[col].where(df[col].notna(), df[f"{col}_bf"])
        df = df.drop(columns=[f"{col}_bf"])

        filled = int(df[col].notna().sum())
        print(f"  -> merged (now non-null count={filled})")

    df = df.drop(columns=["date_key"])
    df.to_csv(CSV_PATH, index=False, encoding="utf-8")
    print("[DONE] Backfill complete safely.")


if __name__ == "__main__":
    main()
