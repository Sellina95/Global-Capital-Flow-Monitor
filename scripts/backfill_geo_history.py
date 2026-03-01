# scripts/backfill_geo_history.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "macro_data.csv"

DEFAULT_LOOKBACK_DAYS = 180

# NOTE: USDCNH는 러너에서 download가 1줄만 내려오는 경우가 있어서 fallback을 강하게 함
GEO_TICKERS: Dict[str, List[str]] = {
    "GOLD": ["GC=F"],
    "USDCNH": ["CNH=X", "CNY=X"],  # offshore -> onshore
    "USDJPY": ["JPY=X"],
    "USDMXN": ["MXN=X"],
    "SEA": ["SEA"],
    "BDRY": ["BDRY"],
    "ITA": ["ITA"],
    "XAR": ["XAR"],
    "EEM": ["EEM"],
    "EMB": ["EMB"],
    "QQQ": ["QQQ"],
    "SPY": ["SPY"],
}


def _safe_close_from_download(df: pd.DataFrame) -> Optional[pd.Series]:
    """yf.download 결과에서 Close Series 추출 (MultiIndex 방어)."""
    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
        if not close_cols:
            return None
        s = df[close_cols].iloc[:, -1]
    else:
        if "Close" not in df.columns:
            return None
        s = df["Close"]

    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return None
    return s


def _download_close_series_robust(ticker: str, lookback_days: int) -> pd.DataFrame:
    """
    1) yf.download로 시도
    2) 너무 적게(<=3 rows) 오면 yf.Ticker().history로 재시도 (FX에서 특히 필요)
    반환: date_key(normalized) + value
    """
    # --- 1) download ---
    try:
        df = yf.download(
            ticker,
            period=f"{lookback_days}d",
            interval="1d",
            progress=False,
            auto_adjust=False,
            group_by="column",
            threads=False,
        )
    except Exception:
        df = None

    s = _safe_close_from_download(df) if df is not None else None

    # --- 2) fallback: history (download가 1줄만 오는 FX 방어) ---
    if s is None or len(s) <= 3:
        try:
            hist = yf.Ticker(ticker).history(period=f"{max(lookback_days, 120)}d", interval="1d", auto_adjust=False)
            if hist is not None and not hist.empty and "Close" in hist.columns:
                s2 = pd.to_numeric(hist["Close"], errors="coerce").dropna()
                if not s2.empty and len(s2) > (0 if s is None else len(s)):
                    s = s2
        except Exception:
            pass

    if s is None or s.empty:
        return pd.DataFrame()

    out = pd.DataFrame({
        "date_key": pd.to_datetime(s.index, errors="coerce").normalize(),
        "value": s.values,
    }).dropna(subset=["date_key"])

    return out


def _normalize_macro_dates(df: pd.DataFrame) -> pd.DataFrame:
    # date_key 생성
    if "date" in df.columns:
        df["date_key"] = pd.to_datetime(df["date"], errors="coerce").dt.normalize()
    elif "datetime" in df.columns:
        df["date_key"] = pd.to_datetime(df["datetime"], errors="coerce").dt.normalize()
    else:
        raise ValueError("No date/datetime column found in macro_data.csv")

    df = df.dropna(subset=["date_key"]).sort_values("date_key").reset_index(drop=True)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    args = ap.parse_args()
    lookback_days = int(args.days)

    if not CSV_PATH.exists():
        raise FileNotFoundError("macro_data.csv not found")

    df = pd.read_csv(CSV_PATH)
    df = df.loc[:, ~df.columns.duplicated()].copy()
    df = _normalize_macro_dates(df)

    # 백업
    stamp = pd.Timestamp.utcnow().strftime("%Y%m%d_%H%M%S")
    backup = CSV_PATH.with_suffix(f".csv.bak_{stamp}")
    df.to_csv(backup, index=False)
    print(f"[OK] backup saved -> {backup}")

    dmin = df["date_key"].min().date()
    dmax = df["date_key"].max().date()
    print(f"[INFO] backfill window: {dmin} ~ {dmax} (LOOKBACK_DAYS={lookback_days})")
    print()

    # 각 지표 다운로드 후 merge
    for col, tickers in GEO_TICKERS.items():
        print(f"[FETCH] {col} tickers={tickers}")

        best = pd.DataFrame()
        best_src = None

        for t in tickers:
            hist = _download_close_series_robust(t, lookback_days)
            if hist.empty:
                continue
            # best = rows 많고 date_key 유효한 것
            if best.empty or len(hist) > len(best):
                best = hist
                best_src = t

        if best.empty:
            print("  -> no data")
            continue

        print(f"  -> got {len(best)} rows (source={best_src})")

        best = best.rename(columns={"value": col})
        df = df.merge(best, on="date_key", how="left", suffixes=("", "_bf"))

        if col in df.columns and f"{col}_bf" in df.columns:
            df[col] = df[col].where(df[col].notna(), df[f"{col}_bf"])
            df = df.drop(columns=[f"{col}_bf"])
        elif col not in df.columns and f"{col}_bf" in df.columns:
            df[col] = df[f"{col}_bf"]
            df = df.drop(columns=[f"{col}_bf"])

        nn = int(df[col].notna().sum()) if col in df.columns else 0
        print(f"  -> merged (now non-null count={nn})")
        print()

    df = df.drop(columns=["date_key"])
    df.to_csv(CSV_PATH, index=False)
    print("[DONE] Backfill complete safely.")


if __name__ == "__main__":
    main()
