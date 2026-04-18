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
def _safe_last_close_and_date(df: pd.DataFrame) -> Tuple[Optional[float], Optional[str]]:
    if df is None or df.empty:
        return None, None

    try:
        if isinstance(df.columns, pd.MultiIndex):
            close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
            if not close_cols:
                return None, None

            close_block = df[close_cols].dropna(how="all")
            if close_block.empty:
                return None, None

            last_valid_idx = close_block.dropna(how="all").index[-1]
            last_row = close_block.loc[last_valid_idx].dropna()
            if last_row.empty:
                return None, None

            value = float(last_row.iloc[-1])
            asof_date = _normalize_to_market_date(last_valid_idx)
            return value, asof_date

        close_col = "Close" if "Close" in df.columns else None
        if not close_col:
            return None, None

        close = pd.to_numeric(df[close_col], errors="coerce").dropna()
        if close.empty:
            return None, None

        last_valid_idx = close.index[-1]
        value = float(close.iloc[-1])
        asof_date = _normalize_to_market_date(last_valid_idx)
        return value, asof_date

    except Exception:
        return None, None


# -------------------------
# fetch
# -------------------------
def fetch_macro_data() -> Tuple[Dict[str, float], Optional[str]]:
    results: Dict[str, float] = {}
    market_date_candidates: List[str] = []

    def _fetch(ticker: str):
        try:
            df = yf.download(ticker, period="30d", interval="1d", progress=False)
            return _safe_last_close_and_date(df)
        except:
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

    # 🔥 핵심: max → mode
    market_date = None
    if market_date_candidates:
        s = pd.Series(market_date_candidates, dtype="string")
        mode_vals = s.mode()
        if not mode_vals.empty:
            market_date = str(mode_vals.iloc[0])
        else:
            market_date = str(s.iloc[-1])

    print(f"[DEBUG] market_date_candidates={market_date_candidates}")
    print(f"[DEBUG] final market_date={market_date}")

    return results, market_date


# -------------------------
# CSV 저장
# -------------------------
def append_to_csv(values: Dict[str, float], market_date: Optional[str]) -> None:
    run_dt = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    row_date = market_date if market_date else datetime.now(KST).strftime("%Y-%m-%d")

    row = {"datetime": run_dt, "date": row_date}
    row.update(values)

    df_row = pd.DataFrame([row])

    if not CSV_PATH.exists():
        df_row.to_csv(CSV_PATH, index=False)
        return

    df_existing = pd.read_csv(CSV_PATH)

    # 🔥 미래 날짜 방지
    if "date" in df_existing.columns and not df_existing.empty:
        latest = pd.to_datetime(df_existing["date"], errors="coerce").max()
        if pd.notna(latest):
            if pd.to_datetime(row_date) > latest + pd.Timedelta(days=1):
                print("⚠️ Future date blocked → using latest existing date")
                row_date = latest.strftime("%Y-%m-%d")
                df_row["date"] = row_date

    # update or append
    df_existing = df_existing[df_existing["date"] != row_date]
    df_updated = pd.concat([df_existing, df_row], ignore_index=True)
    df_updated.to_csv(CSV_PATH, index=False)

    print(f"✅ Saved row for {row_date}")


# -------------------------
# run
# -------------------------
if __name__ == "__main__":
    vals, market_date = fetch_macro_data()
    append_to_csv(vals, market_date)
