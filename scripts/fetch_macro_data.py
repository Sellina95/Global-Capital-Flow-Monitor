from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "macro_data.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KST = timezone(timedelta(hours=9))

# -------------------------
# Indicators
# -------------------------
INDICATORS: Dict[str, str] = {
    "US10Y": "^TNX",      # US 10Y
    "DXY": "DX-Y.NYB",    # Dollar Index
    "WTI": "CL=F",        # Oil
    "VIX": "^VIX",        # Volatility
    "USDKRW": "KRW=X",    # USD/KRW
    "HYG": "HYG",
    "LQD": "LQD",

    # Sector ETFs
    "XLK": "XLK",
    "XLF": "XLF",
    "XLE": "XLE",
    "XLRE": "XLRE",

    # Equity proxies
    "QQQ": "QQQ",
    "SPY": "SPY",

    # Geopolitical EW proxies
    "GOLD": "GC=F",
    "USDCNH": "CNH=X",
    "USDJPY": "JPY=X",
    "USDMXN": "MXN=X",

    # Geo EW v1 확장
    "SEA": "SEA",
    "BDRY": "BDRY",
    "ITA": "ITA",
    "XAR": "XAR",
    "EEM": "EEM",
    "EMB": "EMB",
}

# fallback tickers
FALLBACK_TICKERS = {
    "USDCNH": ["CNH=X", "CNY=X"],
    "DXY": ["DX-Y.NYB", "DX=F", "UUP"],
}

# 핵심 파이프라인이 죽으면 안 되는 지표들
REQUIRED_KEYS = {"US10Y", "DXY", "WTI", "VIX", "USDKRW", "HYG", "LQD"}

# 리포트 기준일(market_date)을 결정하는 "미국장 핵심 종가 바스켓"
# USDKRW처럼 시차가 다른 값은 제외
MARKET_DATE_KEYS = {"US10Y", "DXY", "WTI", "VIX", "HYG", "LQD", "SPY", "QQQ"}

# 시간 컬럼
TIME_COLS = ["datetime", "date"]


def _safe_last_close_and_date(df: pd.DataFrame) -> Tuple[Optional[float], Optional[str]]:
    """
    yfinance 결과에서 마지막 close 값과 해당 index 날짜(시장 기준 날짜)를 반환
    """
    if df is None or df.empty:
        return None, None

    try:
        # MultiIndex columns 대응
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
            asof_date = pd.Timestamp(last_valid_idx).strftime("%Y-%m-%d")
            return value, asof_date

        # 일반 columns
        close_col = None
        if "Close" in df.columns:
            close_col = "Close"
        else:
            cands = [c for c in df.columns if str(c).lower() == "close"]
            if cands:
                close_col = cands[0]

        if close_col is None:
            return None, None

        close = pd.to_numeric(df[close_col], errors="coerce").dropna()
        if close.empty:
            return None, None

        last_valid_idx = close.index[-1]
        value = float(close.iloc[-1])
        asof_date = pd.Timestamp(last_valid_idx).strftime("%Y-%m-%d")
        return value, asof_date

    except Exception:
        return None, None


def fetch_macro_data() -> Tuple[Dict[str, float], Optional[str]]:
    """
    Fetch all INDICATORS from yfinance.
    Returns:
      - results: {indicator: value}
      - market_date: 미국장 핵심 종가 바스켓 기준 시장 날짜
    """
    results: Dict[str, float] = {}
    required_asof_dates: List[str] = []
    market_date_candidates: List[str] = []

    def _fetch_last_close_robust(ticker: str) -> Tuple[Optional[float], Optional[str]]:
        # 1) try download
        try:
            df = yf.download(
                ticker,
                period="30d",
                interval="1d",
                progress=False,
                group_by="column",
                threads=False,
                auto_adjust=False,
            )
            v, d = _safe_last_close_and_date(df)
            if v is not None:
                return float(v), d
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")

        # 2) fallback: Ticker().history
        try:
            hist = yf.Ticker(ticker).history(period="90d", interval="1d", auto_adjust=False)
            if hist is None or hist.empty:
                return None, None
            v, d = _safe_last_close_and_date(hist)
            if v is not None:
                return float(v), d
        except Exception as e:
            print(f"Error with fallback for {ticker}: {e}")

        return None, None

    for name, ticker in INDICATORS.items():
        tickers_to_try = FALLBACK_TICKERS.get(name, [ticker])

        value = None
        used_src = None
        asof_date = None

        for t in tickers_to_try:
            print(f"Fetching {name} ({t}) ...")
            value, asof_date = _fetch_last_close_robust(t)
            if value is not None:
                used_src = t
                break

        if value is None:
            if name in REQUIRED_KEYS:
                print(
                    f"[WARNING] [{name}] No valid Close data from yfinance "
                    f"(tickers tried={tickers_to_try}). Storing NaN."
                )
            results[name] = float("nan")
            continue

        results[name] = float(value)

        if asof_date and name in REQUIRED_KEYS:
            required_asof_dates.append(asof_date)

        if asof_date and name in MARKET_DATE_KEYS:
            market_date_candidates.append(asof_date)

        print(f"  → {name}: {value} (source={used_src}, asof={asof_date})")

    # 리포트 기준일은 미국장 핵심 종가 바스켓 기준
    market_date = max(market_date_candidates) if market_date_candidates else None

    print(f"[DEBUG] required_asof_dates = {required_asof_dates}")
    print(f"[DEBUG] market_date_candidates = {market_date_candidates}")
    print(f"[DEBUG] derived market_date = {market_date}")

    return results, market_date


def _read_existing_header(csv_path: Path) -> List[str]:
    with open(csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip()
    return header.split(",") if header else []


def _compute_new_column_order(existing_cols: List[str], new_cols: List[str]) -> List[str]:
    """
    Keep existing order, append truly new columns to the end.
    Ensure TIME_COLS are present and stay in front.
    """
    existing_set = set(existing_cols)
    appended = [c for c in new_cols if c not in existing_set]

    merged = existing_cols + appended

    for tc in TIME_COLS:
        if tc not in merged:
            merged.insert(0, tc)

    merged_wo_time = [c for c in merged if c not in TIME_COLS]
    final_cols = TIME_COLS + merged_wo_time
    return final_cols


def _expand_and_rewrite_csv(csv_path: Path, final_cols: List[str]) -> None:
    """
    Rewrite existing CSV to include new columns (backfill NaN),
    and normalize column order.
    """
    df = pd.read_csv(csv_path)
    df = df.loc[:, ~df.columns.duplicated()].copy()

    for c in final_cols:
        if c not in df.columns:
            df[c] = pd.NA

    df = df[final_cols]
    df.to_csv(csv_path, index=False, encoding="utf-8")


def append_to_csv(values: Dict[str, float], market_date: Optional[str]) -> None:
    run_dt = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    row_date = market_date if market_date else datetime.now(KST).strftime("%Y-%m-%d")

    # datetime = 실행시각 / date = 시장기준일
    row = {"datetime": run_dt, "date": row_date}
    row.update(values)

    df_row = pd.DataFrame([row])

    if not CSV_PATH.exists():
        ordered = _compute_new_column_order([], list(df_row.columns))
        for c in ordered:
            if c not in df_row.columns:
                df_row[c] = pd.NA
        df_row = df_row[ordered]
        df_row.to_csv(CSV_PATH, mode="w", index=False, header=True, encoding="utf-8")
        print(f"\n✅ Created new CSV: {CSV_PATH}")
        print(df_row)
        return

    existing_cols = _read_existing_header(CSV_PATH)
    final_cols = _compute_new_column_order(existing_cols, list(df_row.columns))

    if set(final_cols) != set(existing_cols) or final_cols != existing_cols:
        _expand_and_rewrite_csv(CSV_PATH, final_cols)

    df_existing = pd.read_csv(CSV_PATH)

    for c in final_cols:
        if c not in df_row.columns:
            df_row[c] = pd.NA
        if c not in df_existing.columns:
            df_existing[c] = pd.NA

    df_row = df_row[final_cols]
    df_existing = df_existing[final_cols]

    # 같은 시장 날짜가 이미 있으면 update
    if "date" in df_existing.columns and row_date in df_existing["date"].astype(str).values:
        print(f"⚠ Existing row for market date {row_date} found. Updating instead of appending.")
        df_existing = df_existing[df_existing["date"].astype(str) != row_date]
        df_updated = pd.concat([df_existing, df_row], ignore_index=True)
        df_updated.to_csv(CSV_PATH, index=False, encoding="utf-8")
        print(f"\n✅ Updated row for market date {row_date} in {CSV_PATH}")
        print(df_row)
    else:
        df_row.to_csv(CSV_PATH, mode="a", index=False, header=False, encoding="utf-8")
        print(f"\n✅ Appended new row to {CSV_PATH}")
        print(df_row)


if __name__ == "__main__":
    vals, market_date = fetch_macro_data()
    append_to_csv(vals, market_date)