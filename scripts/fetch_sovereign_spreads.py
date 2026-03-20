from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "sovereign_spreads.csv"
TMP_CSV = DATA_DIR / "sovereign_spreads.tmp.csv"

KST = timezone(timedelta(hours=9))

# 실제 프로젝트에서 쓰는 컬럼 기준으로 넉넉하게 포함
YIELD_COLS = [
    "US10Y_Y",
    "KR10Y_Y",
    "JP10Y_Y",
    "CN10Y_Y",
    "DE10Y_Y",
    "IL10Y_Y",
    "TR10Y_Y",
    "GB10Y_Y",
    "MX10Y_Y",
]

SPREAD_COLS = [
    "KR10Y_SPREAD",
    "JP10Y_SPREAD",
    "CN10Y_SPREAD",
    "DE10Y_SPREAD",
    "IL10Y_SPREAD",
    "TR10Y_SPREAD",
    "GB10Y_SPREAD",
    "MX10Y_SPREAD",
]


def _safe_read_existing() -> pd.DataFrame:
    if not OUT_CSV.exists() or OUT_CSV.stat().st_size == 0:
        return pd.DataFrame(columns=["date"] + YIELD_COLS + SPREAD_COLS)
    try:
        df = pd.read_csv(OUT_CSV)
        return df
    except Exception:
        return pd.DataFrame(columns=["date"] + YIELD_COLS + SPREAD_COLS)


def _ensure_date(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if "date" not in df.columns:
        return df

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    return df.reset_index(drop=True)


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

    for cc in ["KR", "JP", "CN", "DE", "IL", "TR", "GB", "MX"]:
        add_spread(cc)

    return df


def main() -> None:
    """
    기존 sovereign_spreads.csv를 daily calendar 구조로 보강:
    - 오늘까지 date 행 무조건 생성
    - yield 값은 기존 값 유지
    - 없는 값은 NaN
    - spread는 계산 가능할 때만 계산
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing = _ensure_date(_safe_read_existing())

    # 컬럼 보강
    base_cols = ["date"] + YIELD_COLS + SPREAD_COLS
    if existing.empty:
        existing = pd.DataFrame(columns=base_cols)

    for col in base_cols:
        if col not in existing.columns:
            existing[col] = pd.NA

    if not existing.empty and "date" in existing.columns:
        start_date = existing["date"].min()
    else:
        start_date = pd.Timestamp(datetime.now(KST).date())

    today_ts = pd.Timestamp(datetime.now(KST).date())

    # ✅ 오늘까지 날짜 무조건 생성
    full_dates = pd.date_range(start=start_date, end=today_ts, freq="D")
    base = pd.DataFrame({"date": full_dates})

    updated = base.merge(existing, on="date", how="left")

    # 숫자 컬럼 정리
    for col in YIELD_COLS + SPREAD_COLS:
        if col in updated.columns:
            updated[col] = pd.to_numeric(updated[col], errors="coerce")

    # spreads 재계산
    updated = _compute_spreads(updated)

    # 저장 전 정리
    updated = updated.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    updated["date"] = pd.to_datetime(updated["date"], errors="coerce")
    updated = updated.dropna(subset=["date"])
    updated["date"] = updated["date"].dt.strftime("%Y-%m-%d")

    updated.to_csv(TMP_CSV, index=False)
    TMP_CSV.replace(OUT_CSV)

    print(f"[OK] sovereign_spreads updated (daily rows + SPREAD cols): {OUT_CSV} (rows={len(updated)})")
    print("[DEBUG] last date:", updated["date"].iloc[-1] if not updated.empty else "EMPTY")
    print("[DEBUG] columns:", list(updated.columns))


if __name__ == "__main__":
    main()