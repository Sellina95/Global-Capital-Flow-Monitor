from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple

import pandas as pd
import yfinance as yf
from zoneinfo import ZoneInfo  # ✅ 추가

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "macro_data.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KST = timezone(timedelta(hours=9))
NY = ZoneInfo("America/New_York")  # ✅ 핵심

# -------------------------
# Indicators
# -------------------------
INDICATORS: Dict[str, str] = {
    "US10Y": "^TNX",
    "DXY": "DX-Y.NYB",
    "WTI": "CL=F",
    "VIX": "^VIX",
    "USDKRW": "KRW=X",
    "HYG": "HYG",
    "LQD": "LQD",

    "XLK": "XLK",
    "XLF": "XLF",
    "XLE": "XLE",
    "XLRE": "XLRE",

    "QQQ": "QQQ",
    "SPY": "SPY",

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
}

FALLBACK_TICKERS = {
    "USDCNH": ["CNH=X", "CNY=X"],
    "DXY": ["DX-Y.NYB", "DX=F", "UUP"],
}

REQUIRED_KEYS = {"US10Y", "DXY", "WTI", "VIX", "USDKRW", "HYG", "LQD"}

MARKET_DATE_KEYS = {"US10Y", "DXY", "WTI", "VIX", "HYG", "LQD", "SPY", "QQQ"}

TIME_COLS = ["datetime", "date"]

# -------------------------
# 핵심: 날짜 정규화
# -------------------------
def _normalize_to_market_date(ts) -> Optional[str]:
    try:
        t = pd.Timestamp(ts)

        if pd.isna(t):
            return None

        if t.tzinfo is not None:
            t = t.tz_convert(NY)

        return t.strftime("%Y-%m-%d")
    except Exception:
        return None


# -------------------------
# 데이터 파싱
# -------------------------
def _safe_last_close_and_date(
    df: pd.DataFrame,
    max_market_date: Optional[str] = None,
) -> Tuple[Optional[float], Optional[str]]:
    if df is None or df.empty:
        return None, None

    try:
        max_dt = pd.to_datetime(max_market_date).date() if max_market_date else None

        if isinstance(df.columns, pd.MultiIndex):
            close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
            if not close_cols:
                return None, None

            close_block = df[close_cols].dropna(how="all")
            if close_block.empty:
                return None, None

            valid_rows = []

            for idx in close_block.index:
                asof = _normalize_to_market_date(idx)
                if asof is None:
                    continue

                asof_dt = pd.to_datetime(asof).date()
                if max_dt is not None and asof_dt > max_dt:
                    continue

                row = close_block.loc[idx].dropna()
                if row.empty:
                    continue

                valid_rows.append((idx, row, asof))

            if not valid_rows:
                return None, None

            _, last_row, asof_date = valid_rows[-1]
            value = float(last_row.iloc[-1])
            return value, asof_date

        close_col = "Close" if "Close" in df.columns else None
        if not close_col:
            return None, None

        close = pd.to_numeric(df[close_col], errors="coerce").dropna()
        if close.empty:
            return None, None

        valid_items = []

        for idx, value in close.items():
            asof = _normalize_to_market_date(idx)
            if asof is None:
                continue

            asof_dt = pd.to_datetime(asof).date()
            if max_dt is not None and asof_dt > max_dt:
                continue

            valid_items.append((idx, float(value), asof))

        if not valid_items:
            return None, None

        _, value, asof_date = valid_items[-1]
        return value, asof_date

    except Exception as e:
        print(f"⚠️ _safe_last_close_and_date failed: {e}")
        return None, None
              


# -------------------------
# fetch
# -------------------------
def fetch_macro_data() -> Tuple[Dict[str, float], Optional[str]]:
    results: Dict[str, float] = {}
    market_date_candidates: List[str] = []

    now_ny = pd.Timestamp.now(tz=NY)
    expected_market_date = (now_ny - pd.tseries.offsets.BDay(1)).strftime("%Y-%m-%d")

    print(f"[DEBUG] now_ny={now_ny}")
    print(f"[DEBUG] expected_market_date={expected_market_date}")

    def _fetch(ticker: str):
        try:
            df = yf.download(
                ticker,
                period="30d",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            return _safe_last_close_and_date(
                df,
                max_market_date=expected_market_date,
            )
        except Exception as e:
            print(f"⚠️ Fetch failed for {ticker}: {e}")
            return None, None

    for name, ticker in INDICATORS.items():
        value, asof_date = None, None

        for t in FALLBACK_TICKERS.get(name, [ticker]):
            value, asof_date = _fetch(t)
            if value is not None:
                break

        if value is None:
            results[name] = float("nan")
            continue

        results[name] = value

        if asof_date and name in MARKET_DATE_KEYS:
            market_date_candidates.append(asof_date)

    market_date = expected_market_date

    print(f"[DEBUG] market_date_candidates={market_date_candidates}")
    print(f"[DEBUG] final market_date={market_date}")

    return results, market_date


# -------------------------
# CSV 저장
# -------------------------
def append_to_csv(values: Dict[str, float], market_date: Optional[str]) -> None:
    """
    macro_data.csv에 market_date 기준으로 1일 1row 저장.
    - 같은 market_date가 있으면 append가 아니라 overwrite
    - date 기준 정렬
    - 수동 재실행해도 동일 market_date row만 갱신
    """
    run_dt = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    row_date = market_date if market_date else datetime.now(KST).strftime("%Y-%m-%d")

    row = {"datetime": run_dt, "date": row_date}
    row.update(values)

    df_row = pd.DataFrame([row])

    if not CSV_PATH.exists():
        df_row["date"] = pd.to_datetime(df_row["date"], errors="coerce")
        df_row = df_row.sort_values("date").reset_index(drop=True)
        df_row["date"] = df_row["date"].dt.strftime("%Y-%m-%d")
        df_row.to_csv(CSV_PATH, index=False)
        print(f"✅ Saved row for {row_date} (new file)")
        return

    df_existing = pd.read_csv(CSV_PATH)

    # date 컬럼 없으면 새 파일처럼 재생성
    if "date" not in df_existing.columns:
        df_row.to_csv(CSV_PATH, index=False)
        print(f"✅ Saved row for {row_date} (date column rebuilt)")
        return

    # 🔥 date 정규화
    df_existing["date"] = pd.to_datetime(df_existing["date"], errors="coerce")
    df_row["date"] = pd.to_datetime(df_row["date"], errors="coerce")

    # 깨진 날짜 row 제거
    df_existing = df_existing.dropna(subset=["date"]).copy()
    df_row = df_row.dropna(subset=["date"]).copy()

    if df_row.empty:
        print("❌ New macro row has invalid date. Skip save.")
        return

    row_date_dt = df_row["date"].iloc[0]
    row_date_str = row_date_dt.strftime("%Y-%m-%d")

    # 🔥 미래 날짜 방지: 최신 기존 날짜보다 1영업일 이상 과도하게 앞서면 차단
    if not df_existing.empty:
        latest = df_existing["date"].max()
        if pd.notna(latest):
            if row_date_dt > latest + pd.tseries.offsets.BDay(1):
                print(
                    f"⚠️ Future date blocked: row_date={row_date_str}, "
                    f"latest_existing={latest.strftime('%Y-%m-%d')}"
                )
                return

    # 🔥 같은 market_date는 overwrite only
    df_existing = df_existing[df_existing["date"] != row_date_dt].copy()

    df_updated = pd.concat([df_existing, df_row], ignore_index=True)

    # 🔥 날짜 기준 정렬
    df_updated["date"] = pd.to_datetime(df_updated["date"], errors="coerce")
    df_updated = df_updated.dropna(subset=["date"]).copy()
    df_updated = df_updated.sort_values("date").reset_index(drop=True)

    # 저장 전 문자열 복원
    df_updated["date"] = df_updated["date"].dt.strftime("%Y-%m-%d")

    df_updated.to_csv(CSV_PATH, index=False)

    print(f"✅ Saved row for {row_date_str} (overwrite-safe, sorted)")


# -------------------------
# run
# -------------------------
if __name__ == "__main__":
    vals, market_date = fetch_macro_data()
    append_to_csv(vals, market_date)
