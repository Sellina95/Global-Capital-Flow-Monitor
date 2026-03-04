# scripts/fetch_sovereign_spreads.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "sovereign_spreads.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DAYS = 400

# Stooq tickers (yfinance)
# NOTE: some may return EMPTY depending on availability
STOOQ_TICKERS: Dict[str, str] = {
    "US10Y_Y": "10yusy.b",
    "KR10Y_Y": "10ykry.b",
    "JP10Y_Y": "10yjpy.b",
    "CN10Y_Y": "10ycny.b",
    "IL10Y_Y": "10yily.b",
    "TR10Y_Y": "10ytry.b",
    # optional if available:
    # "DE10Y_Y": "10ydedy.b",
    # "GB10Y_Y": "10ygbpy.b",
    # "MX10Y_Y": "10ymxpy.b",
}

# Which spreads to compute vs US10Y_Y
SPREAD_PAIRS: List[str] = [
    "KR10Y_Y",
    "JP10Y_Y",
    "CN10Y_Y",
    "IL10Y_Y",
    "TR10Y_Y",
    # add more if you add more tickers above
]

def _download_yield_series(ticker: str, days: int) -> pd.Series:
    df = yf.download(
        ticker,
        period=f"{days}d",
        interval="1d",
        progress=False,
        auto_adjust=False,
        threads=False,
    )
    if df is None or df.empty:
        return pd.Series(dtype="float64")

    # Close column usually exists
    if isinstance(df.columns, pd.MultiIndex):
        # find Close block
        close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
        if not close_cols:
            return pd.Series(dtype="float64")
        s = df[close_cols].iloc[:, -1]
    else:
        if "Close" not in df.columns:
            return pd.Series(dtype="float64")
        s = df["Close"]

    s = pd.to_numeric(s, errors="coerce").dropna()
    # normalize date index to date
    s.index = pd.to_datetime(s.index, errors="coerce").normalize()
    s = s[~s.index.duplicated(keep="last")]
    return s.sort_index()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS)
    args = ap.parse_args()
    days = int(args.days)

    frames = []
    meta = []

    for col, ticker in STOOQ_TICKERS.items():
        s = _download_yield_series(ticker, days=days)
        if s.empty:
            meta.append(f"{col}:EMPTY({ticker})")
            continue
        meta.append(f"{col}:OK({ticker}) rows={len(s)}")
        frames.append(pd.DataFrame({"date": s.index, col: s.values}))

    if not frames:
        raise RuntimeError("No sovereign yield series downloaded (all EMPTY).")

    # outer merge all yield columns on date
    merged = frames[0]
    for f in frames[1:]:
        merged = pd.merge(merged, f, on="date", how="outer")

    merged = merged.sort_values("date").drop_duplicates(subset=["date"], keep="last")

    # forward fill yields (last available) — important for non-trading / sparse series
    yield_cols = [c for c in merged.columns if c.endswith("_Y")]
    for c in yield_cols:
        merged[c] = pd.to_numeric(merged[c], errors="coerce").ffill()

    # compute spreads vs US10Y_Y
    if "US10Y_Y" not in merged.columns:
        raise RuntimeError("US10Y_Y missing; cannot compute spreads.")

    us = pd.to_numeric(merged["US10Y_Y"], errors="coerce")
    for y_col in SPREAD_PAIRS:
        if y_col not in merged.columns:
            continue
        spread_col = y_col.replace("_Y", "_SPREAD")
        merged[spread_col] = pd.to_numeric(merged[y_col], errors="coerce") - us

    # keep last N rows for stable size
    merged = merged.tail(min(days, 250)).reset_index(drop=True)
    merged["date"] = pd.to_datetime(merged["date"]).dt.strftime("%Y-%m-%d")

    merged.to_csv(OUT_CSV, index=False)
    print(f"[OK] sovereign_spreads updated: {OUT_CSV} (rows={len(merged)})")
    print("[META]", " | ".join(meta))

if __name__ == "__main__":
    main()
