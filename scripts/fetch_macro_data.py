# scripts/fetch_macro_data.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, List

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
    "HYG": "HYG",
    "LQD": "LQD",
    

    # ✅ Sector ETFs (Correlation Break / Sector Layer용)
    "XLK": "XLK",         # Technology
    "XLF": "XLF",         # Financials
    "XLE": "XLE",         # Energy
    "XLRE": "XLRE",       # Real Estate

    # 🔥 Growth vs Market Core
    "QQQ": "QQQ",
    "SPY": "SPY",
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

    # ✅ last가 Series로 떨어지는 케이스 방어
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
            group_by="column",
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

    # ✅ row는 둘 다 채워두자 (호환성)
    row = {"datetime": now, "date": now}
    row.update(values)

    df_row = pd.DataFrame([row])

    file_exists = CSV_PATH.exists()

    if file_exists:
        # ✅ 기존 헤더를 읽어서 그 순서대로 컬럼 맞춰서 저장 (핵심!)
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            header_cols = f.readline().strip().split(",")

        # 없는 컬럼은 생성 (NaN)
        for c in header_cols:
            if c not in df_row.columns:
                df_row[c] = pd.NA

        # 헤더 순서대로 재정렬
        df_row = df_row[header_cols]

        # ✅ append
        df_row.to_csv(CSV_PATH, mode="a", index=False, header=False)
    else:
        # ✅ 새 파일이면 원하는 표준 헤더로 생성
        # (여기서는 datetime, US10Y..., date, XLK... 형태로 만들고 싶다면 순서 강제 가능)
        df_row.to_csv(CSV_PATH, mode="w", index=False, header=True)

    print(f"\n✅ Saved row to {CSV_PATH}")
    print(df_row)
    
if __name__ == "__main__":
    vals = fetch_macro_data()
    append_to_csv(vals)
