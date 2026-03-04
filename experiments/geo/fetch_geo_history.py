# experiments/geo/fetch_geo_history.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple, List

import pandas as pd

# yfinance is already in your requirements (you were using it elsewhere)
import yfinance as yf


# -------------------------
# Paths
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
OUT_CSV = EXP_DATA_DIR / "geo_history.csv"

# Optional: merge sovereign spreads (your CDS proxy)
SOV_SPREADS_CSV = BASE_DIR / "data" / "sovereign_spreads.csv"


# -------------------------
# Config
# -------------------------
START_DATE = "2018-01-01"   # 충분히 길게 (2022/2023/2024 이벤트 커버)
END_DATE = None            # None => up to latest
MIN_ROWS_ACCEPT = 120      # 너무 비면 실패로 간주


# -------------------------
# Universe (column -> yfinance ticker)
# - 대부분 Adj Close를 쓰되, FX/Index는 Close가 더 자연스러운 케이스도 있어 둘 다 시도
# -------------------------
TICKERS: Dict[str, str] = {
    # Market reaction
    "VIX": "^VIX",
    "WTI": "CL=F",      # Crude Oil futures
    "GOLD": "GC=F",     # Gold futures
    "USDCNH": "CNH=X",
    "USDJPY": "JPY=X",
    "USDMXN": "MXN=X",

    # Capital flow proxies
    "EEM": "EEM",
    "EMB": "EMB",

    # Shipping / supply chain proxies
    "SEA": "SEA",       # Sea Limited (equity proxy)
    "BDRY": "BDRY",     # Breakwave Dry Bulk Shipping ETF

    # Defense attention proxies
    "ITA": "ITA",       # iShares US Aerospace & Defense
    "XAR": "XAR",       # SPDR S&P Aerospace & Defense
}


def _pick_price_series(df: pd.DataFrame) -> Optional[pd.Series]:
    """
    yfinance.download returns columns:
      - Single ticker: columns like ["Open","High","Low","Close","Adj Close","Volume"]
      - Multi ticker: MultiIndex columns
    We want a single price series per ticker:
      priority: Adj Close -> Close -> (fallback) Close-like
    """
    if df is None or df.empty:
        return None

    # Single ticker (normal columns)
    if isinstance(df.columns, pd.Index) and "Adj Close" in df.columns:
        s = df["Adj Close"].copy()
        if s.dropna().empty and "Close" in df.columns:
            s = df["Close"].copy()
        return s

    if isinstance(df.columns, pd.Index) and "Close" in df.columns:
        return df["Close"].copy()

    return None


def _download_one(ticker: str) -> Optional[pd.Series]:
    """
    Robust single-ticker download.
    Returns: price series indexed by date (DatetimeIndex), or None.
    """
    try:
        df = yf.download(
            ticker,
            start=START_DATE,
            end=END_DATE,
            progress=False,
            auto_adjust=False,
            actions=False,
            threads=False,
        )
    except Exception as e:
        print(f"[WARN] download failed: {ticker} ({type(e).__name__}: {e})")
        return None

    s = _pick_price_series(df)
    if s is None or s.dropna().empty:
        print(f"[WARN] empty series: {ticker}")
        return None

    s.name = ticker
    return s


def load_sovereign_spreads_df() -> pd.DataFrame:
    """
    Load your existing sovereign_spreads.csv if exists.
    Expected to have:
      date, KR10Y_SPREAD, JP10Y_SPREAD, CN10Y_SPREAD, IL10Y_SPREAD, TR10Y_SPREAD, ...
    """
    if not SOV_SPREADS_CSV.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(SOV_SPREADS_CSV)
    except Exception as e:
        print(f"[WARN] cannot read sovereign_spreads.csv: {type(e).__name__}: {e}")
        return pd.DataFrame()

    if df.empty or "date" not in df.columns:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)

    # keep only SPREAD columns + date
    keep = ["date"] + [c for c in df.columns if c.endswith("_SPREAD")]
    df = df[keep].copy()

    # numeric
    for c in keep:
        if c != "date":
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def main() -> None:
    EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1) download all series
    series_map: Dict[str, pd.Series] = {}
    meta: List[str] = []

    for col, ticker in TICKERS.items():
        print(f"[FETCH] {col} <- {ticker}")
        s = _download_one(ticker)
        if s is None:
            meta.append(f"{col}:EMPTY({ticker})")
            continue

        # normalize index -> date
        s = s.copy()
        s.index = pd.to_datetime(s.index, errors="coerce")
        s = s[~s.index.isna()].sort_index()
        s = s.rename(col)

        # drop duplicates in index
        s = s[~s.index.duplicated(keep="last")]
        series_map[col] = s
        meta.append(f"{col}:OK({ticker}) rows={len(s)}")

    if not series_map:
        raise RuntimeError("No geo series downloaded (all EMPTY).")

    # 2) merge into one df
    df = pd.concat(series_map.values(), axis=1)
    df = df.reset_index().rename(columns={"index": "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # 3) merge sovereign spreads (optional)
    sov = load_sovereign_spreads_df()
    if sov is not None and not sov.empty:
        df = pd.merge(df, sov, on="date", how="left")
        # spreads can be sparse -> ffill to align with daily market series
        for c in df.columns:
            if c.endswith("_SPREAD"):
                df[c] = pd.to_numeric(df[c], errors="coerce").ffill()

        print("[OK] merged sovereign spreads:", ", ".join([c for c in df.columns if c.endswith("_SPREAD")]))

    # 4) sanity
    if len(df) < MIN_ROWS_ACCEPT:
        # still write, but warn loudly
        print(f"[WARN] geo_history rows too small: {len(df)} (<{MIN_ROWS_ACCEPT})")

    # 5) write
    df.to_csv(OUT_CSV, index=False)
    print(f"[OK] wrote: {OUT_CSV} (rows={len(df)})")
    print("[META]", " | ".join(meta))


if __name__ == "__main__":
    main()
