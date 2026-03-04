# scripts/fetch_sovereign_spreads.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "sovereign_spreads.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DAYS = 400

# ✅ Stooq tickers MUST be lowercase for yfinance
STOOQ_TICKERS: Dict[str, str] = {
    "US10Y_Y": "10yusy.b",
    "KR10Y_Y": "10ykry.b",
    "JP10Y_Y": "10yjpy.b",
    "CN10Y_Y": "10ycny.b",
    "IL10Y_Y": "10yily.b",
    "TR10Y_Y": "10ytry.b",
    # optional:
    # "DE10Y_Y": "10ydedy.b",
    # "GB10Y_Y": "10ygbpy.b",
    # "MX10Y_Y": "10ymxpy.b",
}

# spreads vs US10Y_Y
SPREAD_BASE = "US10Y_Y"
SPREAD_TARGETS: List[str] = [
    "KR10Y_Y",
    "JP10Y_Y",
    "CN10Y_Y",
    "IL10Y_Y",
    "TR10Y_Y",
]

def _download_close_series_anycase(ticker: str, days: int) -> pd.Series:
    """
    Robust download for stooq tickers:
    - try lowercase first
    - then original
    - then uppercase (just in case)
    """
    candidates = []
    t0 = (ticker or "").strip()
    if not t0:
        return pd.Series(dtype="float64")

    # prioritize lowercase for stooq
    for t in [t0.lower(), t0, t0.upper()]:
        if t and t not in candidates:
            candidates.append(t)

    for t in candidates:
        try:
            df = yf.download(
                t,
                period=f"{days}d",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )
        except Exception:
            continue

        if df is None or df.empty:
            continue

        # Close column extraction
        if isinstance(df.columns, pd.MultiIndex):
            close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
            if not close_cols:
                continue
            s = df[close_cols].iloc[:, -1]
        else:
            if "Close" not in df.columns:
                continue
            s = df["Close"]

        s = pd.to_numeric(s, errors="coerce").dropna()
        if s.empty:
            continue

        s.index = pd.to_datetime(s.index, errors="coerce").normalize()
        s = s[~s.index.duplicated(keep="last")].sort_index()
        return s

    return pd.Series(dtype="float64")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS)
    args = ap.parse_args()
    days = int(args.days)

    frames = []
    meta = []

    for col, ticker in STOOQ_TICKERS.items():
        # ✅ enforce lowercase base ticker for stooq
        t = (ticker or "").strip().lower()

        s = _download_close_series_anycase(t, days=days)
        if s.empty:
            meta.append(f"{col}:EMPTY({t})")
            continue

        meta.append(f"{col}:OK({t}) rows={len(s)}")
        frames.append(pd.DataFrame({"date": s.index, col: s.values}))

    # ✅ Never crash pipeline: if all EMPTY, still write a minimal csv and exit 0
    if not frames:
        out = pd.DataFrame({"date": []})
        out.to_csv(OUT_CSV, index=False)
        print(f"[WARN] All stooq series EMPTY. Wrote empty file: {OUT_CSV}")
        print("[META]", " | ".join(meta))
        return

    merged = frames[0]
    for f in frames[1:]:
        merged = pd.merge(merged, f, on="date", how="outer")

    merged = merged.sort_values("date").drop_duplicates(subset=["date"], keep="last")

    # forward fill yields (important for sparse series)
    ycols = [c for c in merged.columns if c.endswith("_Y")]
    for c in ycols:
        merged[c] = pd.to_numeric(merged[c], errors="coerce").ffill()

    # compute spreads
    if SPREAD_BASE in merged.columns:
        base = pd.to_numeric(merged[SPREAD_BASE], errors="coerce")
        for y_col in SPREAD_TARGETS:
            if y_col not in merged.columns:
                continue
            spread_col = y_col.replace("_Y", "_SPREAD")
            merged[spread_col] = pd.to_numeric(merged[y_col], errors="coerce") - base

    # keep stable size
    merged = merged.tail(min(250, len(merged))).reset_index(drop=True)
    merged["date"] = pd.to_datetime(merged["date"]).dt.strftime("%Y-%m-%d")

    merged.to_csv(OUT_CSV, index=False)
    print(f"[OK] sovereign_spreads updated: {OUT_CSV} (rows={len(merged)})")
    print("[META]", " | ".join(meta))


if __name__ == "__main__":
    main()
