from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
YIELD_SOURCE = DATA_DIR / "sovereign_yields.csv" # 👈 원본 데이터 소스 추가
OUT_CSV = DATA_DIR / "sovereign_spreads.csv"
TMP_CSV = DATA_DIR / "sovereign_spreads.tmp.csv"

KST = timezone(timedelta(hours=9))

YIELD_COLS = ["US10Y_Y", "KR10Y_Y", "JP10Y_Y", "CN10Y_Y", "DE10Y_Y", "IL10Y_Y", "TR10Y_Y", "GB10Y_Y", "MX10Y_Y"]
SPREAD_COLS = ["KR10Y_SPREAD", "JP10Y_SPREAD", "CN10Y_SPREAD", "DE10Y_SPREAD", "IL10Y_SPREAD", "TR10Y_SPREAD", "GB10Y_SPREAD", "MX10Y_SPREAD"]

def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 원본 금리 데이터 로드 (sovereign_yields.csv)
    if not YIELD_SOURCE.exists():
        print(f"❌ 원본 파일 없음: {YIELD_SOURCE}")
        return
    
    # 원본을 읽을 때 컬럼명을 YIELD_COLS에 맞게 매핑 (매우 중요!)
    # yields 파일은 US10Y 형식이고, spreads 파일은 US10Y_Y 형식일 수 있으므로 보정합니다.
    yields_raw = pd.read_csv(YIELD_SOURCE)
    yields_raw['date'] = pd.to_datetime(yields_raw['date'])
    
    # 2. 기존 스프레드 파일 로드 (있다면)
    if OUT_CSV.exists():
        existing_spreads = pd.read_csv(OUT_CSV)
        existing_spreads['date'] = pd.to_datetime(existing_spreads['date'])
    else:
        existing_spreads = pd.DataFrame(columns=['date'])

    # 3. 날짜 범위 설정 (원본 데이터의 전체 기간 유지)
    start_date = yields_raw['date'].min()
    today_ts = pd.Timestamp(datetime.now(KST).date())
    full_dates = pd.date_range(start=start_date, end=today_ts, freq="D")
    base = pd.DataFrame({"date": full_dates})

    # 4. 데이터 병합 및 계산
    # 원본 금리 데이터를 base에 합침
    updated = base.merge(yields_raw, on="date", how="left")
    
    # 컬럼명 보정 (예: US10Y -> US10Y_Y)
    # yields.csv의 컬럼이 US10Y 형식이면 _Y를 붙여줍니다.
    rename_dict = {col.replace('_Y', ''): col for col in YIELD_COLS}
    updated = updated.rename(columns=rename_dict)

    # US10Y_Y가 있어야 스프레드 계산 가능
    if "US10Y_Y" in updated.columns:
        us_yield = pd.to_numeric(updated["US10Y_Y"], errors="coerce").ffill()
        
        for cc in ["KR", "JP", "CN", "DE", "IL", "TR", "GB", "MX"]:
            y_col = f"{cc}10Y_Y"
            s_col = f"{cc}10Y_SPREAD"
            if y_col in updated.columns:
                target_yield = pd.to_numeric(updated[y_col], errors="coerce").ffill()
                updated[s_col] = target_yield - us_yield

    # 5. 저장 전 정리
    updated = updated.sort_values("date").drop_duplicates("date", keep="last")
    updated["date"] = updated["date"].dt.strftime("%Y-%m-%d")

    # 필요한 컬럼만 추출 (date + YIELD + SPREAD)
    final_cols = ["date"] + [c for c in YIELD_COLS if c in updated.columns] + [c for c in SPREAD_COLS if c in updated.columns]
    updated[final_cols].to_csv(OUT_CSV, index=False)

    print(f"[OK] sovereign_spreads sync complete: {OUT_CSV} (rows={len(updated)})")

if __name__ == "__main__":
    main()
