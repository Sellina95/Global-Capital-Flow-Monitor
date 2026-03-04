# scripts/fetch_sovereign_spreads.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "sovereign_spreads.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DAYS = 400

# ✅ Stooq direct CSV endpoint
STOOQ_CSV = "https://stooq.com/q/d/l/?s={ticker}&i=d"

# yields (in percent)
STOOQ_TICKERS: Dict[str, str] = {
    "US10Y_Y": "10yusy.b",
    "KR10Y_Y": "10ykry.b",
    "JP10Y_Y": "10yjpy.b",
    "CN10Y_Y": "10ycny.b",
    "IL10Y_Y": "10yily.b",
    "TR10Y_Y": "10ytry.b",
}

SPREAD_BASE = "US10Y_Y"
SPREAD_TARGETS: List[str] = ["KR10Y_Y", "JP10Y_Y", "CN10Y_Y", "IL10Y_Y", "TR10Y_Y"]


def _safe_read_existing() -> pd.DataFrame:
    if OUT_CSV.exists() and OUT_CSV.stat().st_size > 0:
        try:
            return pd.read_csv(OUT_CSV)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def _fetch_stooq_series(ticker: str, days: int) -> pd.DataFrame:
    """
    Fetch daily series from Stooq CSV endpoint.
    Returns DataFrame columns: date, value
    """
    t = (ticker or "").strip().lower()
    if not t:
        return pd.DataFrame(columns=["date", "value"])

    url = STOOQ_CSV.format(ticker=t)
    try:
        df = pd.read_csv(url)
    except Exception:
        return pd.DataFrame(columns=["date", "value"])

    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "value"])

    # stooq format usually: Date, Open, High, Low, Close, Volume
    # Sometimes: Date, Close
    cols = [c.lower() for c in df.columns]
    df.columns = cols

    if "date" not in df.columns:
        return pd.DataFrame(columns=["date", "value"])

    # pick close-like column
    close_col = None
    for cand in ["close", "zamkniecie", "c"]:  # extra fallback
        if cand in df.columns:
            close_col = cand
            break
    if close_col is None:
        # if 2 columns only, assume second is value
        if len(df.columns) >= 2:
            close_col = df.columns[1]
        else:
            return pd.DataFrame(columns=["date", "value"])

    out = df[["date", close_col]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.normalize()
    out["value"] = pd.to_numeric(out[close_col], errors="coerce")
    out = out.dropna(subset=["date", "value"]).sort_values("date")
    out = out.drop_duplicates(subset=["date"], keep="last")

    if out.empty:
        return pd.DataFrame(columns=["date", "value"])

    # keep last N days
    out = out.tail(days).reset_index(drop=True)
    return out[["date", "value"]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=DEFAULT_DAYS)
    args = ap.parse_args()
    days = int(args.days)

    existing = _safe_read_existing()

    frames = []
    meta = []

    for col, ticker in STOOQ_TICKERS.items():
        hist = _fetch_stooq_series(ticker, days=days)
        if hist.empty:
            meta.append(f"{col}:EMPTY({ticker})")
            continue
        meta.append(f"{col}:OK({ticker}) rows={len(hist)}")
        frames.append(hist.rename(columns={"value": col}))

    # ✅ 핵심: 전부 EMPTY면 기존 파일을 절대 덮어쓰지 않음
    if not frames:
        if not existing.empty:
            print(f"[WARN] All stooq series EMPTY. Keeping existing file unchanged: {OUT_CSV}")
        else:
            print(f"[WARN] All stooq series EMPTY and no existing file. Writing empty header file: {OUT_CSV}")
            pd.DataFrame({"date": []}).to_csv(OUT_CSV, index=False)
        print("[META]", " | ".join(meta))
        return

    merged = frames[0]
    for f in frames[1:]:
        merged = pd.merge(merged, f, on="date", how="outer")

    merged = merged.sort_values("date").drop_duplicates(subset=["date"], keep="last")

    # forward fill yields
    ycols = [c for c in merged.columns if c.endswith("_Y")]
    for c in ycols:
        merged[c] = pd.to_numeric(merged[c], errors="coerce").ffill()

    # compute spreads vs US10Y_Y
    if SPREAD_BASE in merged.columns:
        base = pd.to_numeric(merged[SPREAD_BASE], errors="coerce")
        for y_col in SPREAD_TARGETS:
            if y_col not in merged.columns:
                continue
            spread_col = y_col.replace("_Y", "_SPREAD")
            merged[spread_col] = pd.to_numeric(merged[y_col], errors="coerce") - base

    merged = merged.dropna(subset=["date"]).tail(250).reset_index(drop=True)
    merged["date"] = pd.to_datetime(merged["date"]).dt.strftime("%Y-%m-%d")

    # ✅ write
    merged.to_csv(OUT_CSV, index=False)
    print(f"[OK] sovereign_spreads updated: {OUT_CSV} (rows={len(merged)})")
    print("[META]", " | ".join(meta))


if __name__ == "__main__":
    main()
