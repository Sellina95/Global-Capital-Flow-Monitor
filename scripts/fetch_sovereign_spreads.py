# scripts/fetch_sovereign_spreads.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, List
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "sovereign_spreads.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Stooq daily data endpoint:
# https://stooq.com/q/d/l/?s=10yusy.b&i=d
STOOQ_DL = "https://stooq.com/q/d/l/?s={symbol}&i=d"

# ✅ Stooq에서 잘 잡히는 10Y yield 심볼들 (필요하면 더 추가 가능)
# US는 benchmark
YIELD_SYMBOLS: Dict[str, str] = {
    "US10Y_Y": "10yusy.b",
    "KR10Y_Y": "10ykry.b",
    "JP10Y_Y": "10yjpy.b",
    "CN10Y_Y": "10ycny.b",
    "DE10Y_Y": "10ydedy.b",
    "GB10Y_Y": "10ygbpy.b",
    "IL10Y_Y": "10yily.b",
    "TR10Y_Y": "10ytry.b",
    "MX10Y_Y": "10ymxpy.b",
}

DEFAULT_DAYS = 400  # enough for rolling windows + prev


def _download_stooq_close(symbol: str) -> pd.DataFrame:
    """
    Returns df: date, close
    Stooq columns are typically: Date, Open, High, Low, Close, Volume
    """
    url = STOOQ_DL.format(symbol=symbol)
    try:
        df = pd.read_csv(url)
    except Exception:
        return pd.DataFrame(columns=["date", "close"])

    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "close"])

    # normalize columns
    cols = {c.lower(): c for c in df.columns}
    date_col = cols.get("date")
    close_col = cols.get("close")

    if not date_col or not close_col:
        return pd.DataFrame(columns=["date", "close"])

    out = df[[date_col, close_col]].copy()
    out.columns = ["date", "close"]

    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)
    return out


def main(days: int = DEFAULT_DAYS) -> None:
    # download all yields
    series_frames: List[pd.DataFrame] = []
    meta = []

    for col, sym in YIELD_SYMBOLS.items():
        df = _download_stooq_close(sym)
        if df.empty:
            meta.append(f"{col}:EMPTY({sym})")
            continue

        # keep last N days
        df = df.tail(days).copy()
        df = df.rename(columns={"close": col})
        series_frames.append(df[["date", col]])
        meta.append(f"{col}:OK({sym}) rows={len(df)}")

    if not series_frames:
        # write empty but valid schema
        out = pd.DataFrame(columns=["date"] + list(YIELD_SYMBOLS.keys()))
        out.to_csv(OUT_CSV, index=False)
        print(f"[WARN] No sovereign yield data. wrote empty: {OUT_CSV}")
        print("[META]", " | ".join(meta))
        return

    # merge on date
    merged = series_frames[0]
    for f in series_frames[1:]:
        merged = pd.merge(merged, f, on="date", how="outer")

    merged = merged.sort_values("date").drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)

    # compute spreads vs US10Y_Y (same unit as Stooq yields)
    if "US10Y_Y" in merged.columns:
        us = merged["US10Y_Y"]
        for k in list(YIELD_SYMBOLS.keys()):
            if k == "US10Y_Y":
                continue
            sp = k.replace("_Y", "_SPREAD")
            if k in merged.columns:
                merged[sp] = merged[k] - us

    # ffill (국가별 결측 발생할 수 있음)
    merged = merged.sort_values("date").reset_index(drop=True)
    merged = merged.ffill()

    # output formatting
    merged["date"] = pd.to_datetime(merged["date"], errors="coerce")
    merged = merged.dropna(subset=["date"]).tail(250).reset_index(drop=True)  # 적당히 보관
    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")

    merged.to_csv(OUT_CSV, index=False)
    print(f"[OK] sovereign_spreads updated: {OUT_CSV} (rows={len(merged)})")
    print("[META]", " | ".join(meta))


if __name__ == "__main__":
    # optional: allow CLI --days
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=DEFAULT_DAYS)
    args = p.parse_args()
    main(days=args.days)
