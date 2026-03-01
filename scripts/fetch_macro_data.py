# scripts/fetch_macro_data.py
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

    # Geopolitical EW proxies (can be flaky on some days)
    "GOLD": "GC=F",
    "USDCNH": "CNY=X",
    "USDJPY": "JPY=X",
    "USDMXN": "MXN=X",

    # --------------------------------------------------------
    # ✅ NEW: Geo EW v1 확장 (data-friendly)
    # --------------------------------------------------------
    "SEA": "SEA",         # Shipping / supply chain proxy (ETF)
    "BDRY": "BDRY",       # Dry bulk shipping ETF (optional but useful)
    "ITA": "ITA",         # Defense / aerospace
    "XAR": "XAR",         # Defense / aerospace (alt)
    "EEM": "EEM",         # EM equity stress
    "EMB": "EMB",         # EM USD bond stress
}
# --- Fallback ticker mapping (for flaky FX like CNH) ---
FALLBACK_TICKERS = {
    "USDCNH": ["CNH=X", "CNY=X"],  # try offshore first, then onshore
}

# 핵심 파이프라인이 죽으면 안 되는 지표들(없으면 raise)
REQUIRED_KEYS = {"US10Y", "DXY", "WTI", "VIX", "USDKRW", "HYG", "LQD"}

# 항상 유지하고 싶은 시간 컬럼(리포트 로더 호환성)
TIME_COLS = ["datetime", "date"]


def _safe_last_close(df: pd.DataFrame) -> Optional[float]:
    """yfinance 결과에서 마지막 close를 float 하나로 뽑기 (Series/MultiIndex 방어)."""
    if df is None or df.empty:
        return None

    # MultiIndex columns 방어: ('Close', 'TICKER') 형태
    if isinstance(df.columns, pd.MultiIndex):
        close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
        if not close_cols:
            return None
        close_block = df[close_cols].dropna(how="all")
        if close_block.empty:
            return None
        last_row = close_block.iloc[-1].dropna()
        if last_row.empty:
            return None
        return float(last_row.iloc[-1])

    # 일반 컬럼
    close_col = None
    if "Close" in df.columns:
        close_col = "Close"
    else:
        cands = [c for c in df.columns if str(c).lower() == "close"]
        if cands:
            close_col = cands[0]
    if close_col is None:
        return None

    close = df[close_col].dropna()
    if close.empty:
        return None

    last = close.iloc[-1]
    if isinstance(last, pd.Series):
        last = last.dropna()
        if last.empty:
            return None
        last = last.iloc[-1]

    return float(last)


def fetch_macro_data() -> Dict[str, float]:
    """
    Fetch all INDICATORS from yfinance.
    - REQUIRED_KEYS missing => raise
    - Optional indicators missing => store as NaN
    - FX tickers (USDCNH) use robust fallback (download -> history)
    """
    results: Dict[str, float] = {}

    def _fetch_last_close_robust(ticker: str) -> Optional[float]:
        # 1) try download (fast path)
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
            v = _safe_last_close(df)
            if v is not None:
                return float(v)
        except Exception:
            pass

        # 2) fallback: Ticker().history (often more reliable for FX)
        try:
            hist = yf.Ticker(ticker).history(period="90d", interval="1d", auto_adjust=False)
            if hist is None or hist.empty:
                return None
            if "Close" not in hist.columns:
                return None
            close = hist["Close"].dropna()
            if close.empty:
                return None
            return float(close.iloc[-1])
        except Exception:
            return None

    for name, ticker in INDICATORS.items():
        # fallback tickers for USDCNH
        tickers_to_try = FALLBACK_TICKERS.get(name, [ticker])

        value = None
        used_src = None

        for t in tickers_to_try:
            print(f"Fetching {name} ({t}) ...")
            value = _fetch_last_close_robust(t)
            if value is not None:
                used_src = t
                break

        if value is None:
            if name in REQUIRED_KEYS:
                raise RuntimeError(f"[{name}] No valid Close data from yfinance (tickers tried={tickers_to_try}).")
            results[name] = float("nan")
            print(f"  → {name}: NaN (optional, skipped)")
            continue

        results[name] = float(value)
        if used_src:
            print(f"  → {name}: {value} (source={used_src})")
        else:
            print(f"  → {name}: {value}")

    return results


def _read_existing_header(csv_path: Path) -> List[str]:
    with open(csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip()
    return header.split(",") if header else []


def _compute_new_column_order(existing_cols: List[str], new_cols: List[str]) -> List[str]:
    """
    Keep existing order, append truly new columns to the end.
    Ensure TIME_COLS are present and stay in front (datetime, date).
    """
    existing_set = set(existing_cols)
    appended = [c for c in new_cols if c not in existing_set]

    # Base order = existing + appended
    merged = existing_cols + appended

    # Ensure time cols exist
    for tc in TIME_COLS:
        if tc not in merged:
            merged.insert(0, tc)

    # Force TIME_COLS to be the first two (stable)
    # Remove then re-insert in correct order
    merged_wo_time = [c for c in merged if c not in TIME_COLS]
    final_cols = TIME_COLS + merged_wo_time
    return final_cols


def _expand_and_rewrite_csv(csv_path: Path, final_cols: List[str]) -> None:
    """
    Rewrite existing CSV to include new columns (backfill NaN),
    and normalize column order to final_cols.
    This prevents 'field count mismatch' ParserError forever.
    """
    df = pd.read_csv(csv_path)
    df = df.loc[:, ~df.columns.duplicated()].copy()

    for c in final_cols:
        if c not in df.columns:
            df[c] = pd.NA

    df = df[final_cols]
    df.to_csv(csv_path, index=False, encoding="utf-8")


def append_to_csv(values: Dict[str, float]) -> None:
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    # ✅ 둘 다 채워서 호환성 유지 (너희 load_macro_df가 datetime/date 혼용 방어함)
    row = {"datetime": now, "date": now}
    row.update(values)

    df_row = pd.DataFrame([row])

    if not CSV_PATH.exists():
        # New file: write with deterministic order (time cols + indicators order)
        ordered = _compute_new_column_order([], list(df_row.columns))
        for c in ordered:
            if c not in df_row.columns:
                df_row[c] = pd.NA
        df_row = df_row[ordered]
        df_row.to_csv(CSV_PATH, mode="w", index=False, header=True, encoding="utf-8")
        print(f"\n✅ Created new CSV: {CSV_PATH}")
        print(df_row)
        return

    # Existing file: may need header expansion
    existing_cols = _read_existing_header(CSV_PATH)

    # Union columns (existing + row cols)
    final_cols = _compute_new_column_order(existing_cols, list(df_row.columns))

    # If header needs expansion (new cols introduced), rewrite entire file once
    if set(final_cols) != set(existing_cols) or final_cols != existing_cols:
        # rewrite existing CSV with expanded columns + normalized order
        _expand_and_rewrite_csv(CSV_PATH, final_cols)

    # Align df_row to final_cols (fill missing)
    for c in final_cols:
        if c not in df_row.columns:
            df_row[c] = pd.NA
    df_row = df_row[final_cols]

    # Append safely
    df_row.to_csv(CSV_PATH, mode="a", index=False, header=False, encoding="utf-8")

    print(f"\n✅ Saved row to {CSV_PATH}")
    print(df_row)


if __name__ == "__main__":
    vals = fetch_macro_data()
    append_to_csv(vals)
