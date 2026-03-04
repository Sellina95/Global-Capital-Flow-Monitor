# scripts/fetch_sovereign_spreads.py
from __future__ import annotations

from pathlib import Path
import argparse
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "sovereign_spreads.csv"
TMP_CSV = DATA_DIR / "sovereign_spreads.tmp.csv"

# 네가 이미 저장하고 있는 컬럼명 기준
YIELD_COLS = ["US10Y_Y", "KR10Y_Y", "JP10Y_Y", "CN10Y_Y", "IL10Y_Y", "TR10Y_Y"]

def _safe_read_existing() -> pd.DataFrame:
    if not OUT_CSV.exists() or OUT_CSV.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(OUT_CSV)
    except Exception:
        return pd.DataFrame()

def _ensure_date(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if "date" not in df.columns:
        return df
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    return df

def _compute_spreads(df: pd.DataFrame) -> pd.DataFrame:
    """
    XX10Y_SPREAD = XX10Y_Y - US10Y_Y
    """
    df = df.copy()
    if "US10Y_Y" not in df.columns:
        return df

    us = pd.to_numeric(df["US10Y_Y"], errors="coerce")

    def add_spread(cc: str):
        y_col = f"{cc}10Y_Y"
        s_col = f"{cc}10Y_SPREAD"
        if y_col not in df.columns:
            return
        yy = pd.to_numeric(df[y_col], errors="coerce")
        df[s_col] = yy - us

    for cc in ["KR", "JP", "CN", "IL", "TR", "DE", "GB", "MX"]:
        add_spread(cc)

    return df

def main() -> None:
    """
    이 파일은 "다운로드" 자체를 여기서 안 한다고 가정.
    (너가 이미 stooq/yfinance/fred에서 yield들을 OUT_CSV에 써놓고 있는 상태라 했으니까)

    만약 네 파이프라인이 여기서 다운로드까지 한다면,
    다운로드 결과 df를 만든 뒤 아래 로직만 적용해도 됨.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing = _ensure_date(_safe_read_existing())
    if existing.empty:
        # 빈 파일이면 그냥 최소 헤더라도 만들어두되,
        # 여기서는 "기존 파일 보존" 이슈가 있으니 실패로 처리하지 않음
        cols = ["date"] + YIELD_COLS + ["KR10Y_SPREAD"]
        pd.DataFrame(columns=cols).to_csv(OUT_CSV, index=False)
        print(f"[WARN] sovereign_spreads was empty → wrote header only: {OUT_CSV}")
        return

    # spreads 계산
    updated = _compute_spreads(existing)

    # 저장 전 체크: date + US10Y_Y는 있어야 의미 있음
    if "date" not in updated.columns or "US10Y_Y" not in updated.columns:
        print("[WARN] Missing required columns (date/US10Y_Y). Keep existing file.")
        return

    # tmp 저장 후 원본 교체 (원본 날아가는 사고 방지)
    updated["date"] = pd.to_datetime(updated["date"], errors="coerce")
    updated = updated.dropna(subset=["date"]).sort_values("date")
    updated["date"] = updated["date"].dt.strftime("%Y-%m-%d")

    updated.to_csv(TMP_CSV, index=False)
    TMP_CSV.replace(OUT_CSV)

    print(f"[OK] sovereign_spreads updated (with SPREAD cols): {OUT_CSV} (rows={len(updated)})")
    # 디버그: 헤더 확인
    print("[DEBUG] columns:", list(updated.columns))

if __name__ == "__main__":
    main()
