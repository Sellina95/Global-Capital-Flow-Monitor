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

def _read_existing_header_cols() -> Optional[List[str]]:
    """기존 CSV가 있으면 헤더 컬럼 순서를 읽어온다."""
    if not CSV_PATH.exists():
        return None
    try:
        with CSV_PATH.open("r", encoding="utf-8") as f:
            header = f.readline().strip()
        if not header:
            return None
        return [c.strip() for c in header.split(",")]
    except Exception:
        return None

def append_to_csv(values: Dict[str, float]) -> None:
    now_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    # ✅ 핵심: 헤더에 'datetime'이 있으니 반드시 채워줘야 함
    row = {
        "datetime": now_str,  # 기존 헤더 호환
        "date": now_str,      # 기존 코드/파서 호환
    }
    row.update(values)

    df_row = pd.DataFrame([row])

    # ✅ 기존 헤더가 있으면, 그 순서대로 맞춰서 저장 (컬럼 밀림 방지)
    existing_cols = _read_existing_header_cols()
    if existing_cols:
        for c in existing_cols:
            if c not in df_row.columns:
                df_row[c] = pd.NA
        df_row = df_row.reindex(columns=existing_cols)

    file_exists = CSV_PATH.exists()
    df_row.to_csv(CSV_PATH, mode="a", index=False, header=not file_exists)

    print(f"\n✅ Saved row to {CSV_PATH}")
    print(df_row)

if __name__ == "__main__":
    vals = fetch_macro_data()
    append_to_csv(vals)
