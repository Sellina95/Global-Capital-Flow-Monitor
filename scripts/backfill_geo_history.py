# scripts/backfill_geo_history.py
from __future__ import annotations

from pathlib import Path
from typing import Dict
import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "macro_data.csv"

GEO_TICKERS: Dict[str, str] = {
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
    "QQQ": "QQQ",
    "SPY": "SPY",
}

LOOKBACK_DAYS = 120


def _download_close_series(ticker: str) -> pd.DataFrame:
    df = yf.download(
        ticker,
        period=f"{LOOKBACK_DAYS}d",
        interval="1d",
        progress=False,
        auto_adjust=False,
    )

    if df is None or df.empty:
        return pd.DataFrame()

    # Close 컬럼 추출
    if isinstance(df.columns, pd.MultiIndex):
        close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
        if not close_cols:
            return pd.DataFrame()
        s = df[close_cols].iloc[:, -1]
    else:
        if "Close" not in df.columns:
            return pd.DataFrame()
        s = df["Close"]

    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return pd.DataFrame()

    out = pd.DataFrame({
        "date_key": pd.to_datetime(s.index).normalize(),
        "value": s.values
    })

    return out


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError("macro_data.csv not found")

    df = pd.read_csv(CSV_PATH)

    # date 정규화
    if "date" in df.columns:
        df["date_key"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    elif "datetime" in df.columns:
        df["date_key"] = pd.to_datetime(df["datetime"], errors="coerce").dt.normalize()
    else:
        raise ValueError("No date column found")

    df = df.dropna(subset=["date_key"]).sort_values("date_key")

    # 백업
    backup = CSV_PATH.with_suffix(".csv.bak")
    df.to_csv(backup, index=False)
    print(f"[OK] backup saved -> {backup}")

    # 각 지표 다운로드 후 merge
    for col, ticker in GEO_TICKERS.items():
        print(f"[FETCH] {col} ({ticker})")

        hist = _download_close_series(ticker)
        if hist.empty:
            print("  -> no data")
            continue

        hist = hist.rename(columns={"value": col})

        df = df.merge(hist, on="date_key", how="left", suffixes=("", "_bf"))

        if col in df.columns and f"{col}_bf" in df.columns:
            df[col] = df[col].where(df[col].notna(), df[f"{col}_bf"])
            df = df.drop(columns=[f"{col}_bf"])
        elif col not in df.columns:
            df[col] = df[f"{col}_bf"]
            df = df.drop(columns=[f"{col}_bf"])

        print("  -> merged")

    df = df.drop(columns=["date_key"])

    df.to_csv(CSV_PATH, index=False)
    print("[DONE] Backfill complete safely.")


if __name__ == "__main__":
    main()
