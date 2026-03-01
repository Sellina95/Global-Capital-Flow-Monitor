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

    # 1) 새 row 만들기
    row = {"date": now}
    row.update(values)
    df_row = pd.DataFrame([row])

    # 2) 파일 없으면 그냥 새로 생성
    if not CSV_PATH.exists():
        df_row.to_csv(CSV_PATH, index=False)
        print(f"\n✅ Created new CSV: {CSV_PATH}")
        print(df_row)
        return

    # 3) ✅ 파일이 이미 있으면: 헤더에 새 컬럼이 있는지 확인
    existing = pd.read_csv(CSV_PATH, nrows=0)
    existing_cols = list(existing.columns)

    # 우리가 넣고 싶은 전체 컬럼 = (기존 + 새 row 컬럼)
    desired_cols = list(dict.fromkeys(existing_cols + list(df_row.columns)))

    # ✅ 기존 헤더에 없는 컬럼이 생겼다면: 스키마 마이그레이션(백업 + rewrite)
    missing_in_file = [c for c in df_row.columns if c not in existing_cols]
    if missing_in_file:
        backup_path = CSV_PATH.with_suffix(".csv.bak")
        CSV_PATH.replace(backup_path)  # 원본 백업(이동)

        # 백업 파일 로드 → 컬럼 확장 → 다시 저장
        old_df = pd.read_csv(backup_path)
        for c in desired_cols:
            if c not in old_df.columns:
                old_df[c] = pd.NA

        # 컬럼 순서 정렬 (기존 컬럼 유지 + 뒤에 새 컬럼)
        old_df = old_df[desired_cols]
        old_df.to_csv(CSV_PATH, index=False)
        print(f"[OK] macro_data.csv schema upgraded. backup -> {backup_path}")
        print(f"[OK] added columns: {missing_in_file}")

        # 기존 헤더 새로 읽기
        existing_cols = desired_cols

    # 4) ✅ append (항상 CSV 헤더 컬럼 순서에 맞춰서 저장)
    # 파일 컬럼에 없는 키는 무시되지 않도록, 없으면 NaN으로 채움
    for c in existing_cols:
        if c not in df_row.columns:
            df_row[c] = pd.NA
    df_row = df_row[existing_cols]

    df_row.to_csv(CSV_PATH, mode="a", index=False, header=False)

    print(f"\n✅ Appended row to {CSV_PATH}")
    print(df_row)
    
if __name__ == "__main__":
    vals = fetch_macro_data()
    append_to_csv(vals)
