# scripts/fetch_macro_data.py
from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "macro_data.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KST = timezone(timedelta(hours=9))

INDICATORS = {
    "US10Y": "^TNX",      # 미국 10년물
    "DXY": "DX-Y.NYB",    # 달러 인덱스
    "WTI": "CL=F",        # 유가
    "VIX": "^VIX",        # 변동성
    "USDKRW": "KRW=X",    # 원/달러
    # 이미 추가했다면 여기도 포함
    "HYG": "HYG",
    "LQD": "LQD",
}

def _safe_last_close(df: pd.DataFrame) -> Optional[float]:
    """yfinance 결과에서 마지막 close를 '무조건 float 하나'로 뽑아오기(Series/MultiIndex 방어)."""
    if df is None or df.empty:
        return None

    # MultiIndex columns (예: ('Close','^TNX')) 형태 방어
    if isinstance(df.columns, pd.MultiIndex):
        close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
        if not close_cols:
            return None
        close_block = df[close_cols].dropna(how="all")
        if close_block.empty:
            return None
        last_row = close_block.iloc[-1]  # Series (ticker들)
        last_row = last_row.dropna()
        if last_row.empty:
            return None
        return float(last_row.iloc[-1])

    # 일반 컬럼
    if "Close" not in df.columns:
        # 혹시 close 소문자 등 방어
        cands = [c for c in df.columns if str(c).lower() == "close"]
        if not cands:
            return None
        close_col = cands[0]
    else:
        close_col = "Close"

    close = df[close_col].dropna()
    if close.empty:
        return None

    last = close.iloc[-1]

    # ✅ 여기서 last가 Series로 떨어지는 케이스 방어
    if isinstance(last, pd.Series):
        last = last.dropna()
        if last.empty:
            return None
        last = last.iloc[-1]

    return float(last)

def fetch_macro_data() -> Dict[str, float]:
    results: Dict[str, float] = {}

    for name, ticker in INDICATORS.items():
        print(f"Fetching {name} ({ticker}) ...")

        df = yf.download(
            ticker,
            period="7d",
            interval="1d",
            progress=False,
            group_by="column",   # MultiIndex 가능성 있음 → 위에서 방어
            threads=False,
            auto_adjust=False,
        )

        value = _safe_last_close(df)
        if value is None:
            raise RuntimeError(f"[{name}] No valid Close data from yfinance (ticker={ticker}).")

        results[name] = value
        print(f"  → {name}: {value}")

    return results

def append_to_csv(values: Dict[str, float]) -> None:
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    row = {"date": now}
    row.update(values)

    df_row = pd.DataFrame([row])
    file_exists = CSV_PATH.exists()
    df_row.to_csv(CSV_PATH, mode="a", index=False, header=not file_exists)

    print(f"\n✅ Saved row to {CSV_PATH}")
    print(df_row)

if __name__ == "__main__":
    vals = fetch_macro_data()
    append_to_csv(vals)
