from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone, timedelta
import time
import pandas as pd
from urllib.error import URLError, HTTPError
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "sovereign_yields.csv"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
KST = timezone(timedelta(hours=9))

# 💡 [보정] 에러 났던 중국, 터키 티커를 더 안정적인 코드로 교체
SERIES = {
    "US10Y": "DGS10",
    "KR10Y": "IRLTLT01KRM156N",
    "JP10Y": "IRLTLT01JPM156N",
    "DE10Y": "IRLTLT01DEM156N",
    "CN10Y": "INTDSRCNM193N", # 중국 금리 대체 티커
    "IL10Y": "IRLTLT01ILM156N",
    "TR10Y": "INTDSRTRM193N", # 터키 금리 대체 티커
    "GB10Y": "IRLTLT01GBM156N",
    "MX10Y": "IRLTLT01MXM156N",
}

def fetch_fred_csv(series_id: str, max_retries: int = 3) -> pd.DataFrame:
    url = f"{FRED_CSV}{series_id}"
    for attempt in range(1, max_retries + 1):
        try:
            df = pd.read_csv(url)
            if df is None or df.empty: return pd.DataFrame()
            df.columns = ["date", series_id]
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
            return df.dropna(subset=["date"])
        except:
            time.sleep(1 * attempt)
    return pd.DataFrame()

def _load_existing() -> pd.DataFrame:
    if not OUT_CSV.exists(): return pd.DataFrame()
    try: return pd.read_csv(OUT_CSV, parse_dates=["date"])
    except: return pd.DataFrame()

def main(days: int = 365) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = _load_existing()

    # 1. 누락 감지 및 fetch_days 결정
    if existing.empty or "CN10Y" not in existing.columns or existing["CN10Y"].isna().all():
        print("🚨 누락 데이터 감지! 2000일치 풀 스캔 시작합니다.")
        fetch_days = 2000
    else:
        fetch_days = days

    fetched = {}
    for col, sid in SERIES.items():
        print(f"[FETCH] {col}")
        df = fetch_fred_csv(sid)
        if not df.empty:
            fetched[col] = df.rename(columns={sid: col})

    # 2. 병합 로직 (merged 변수 생성!)
    today_ts = pd.Timestamp(datetime.now(KST).date())
    start_date = existing["date"].min() if not existing.empty else today_ts - timedelta(days=fetch_days)
    
    full_dates = pd.date_range(start=start_date, end=today_ts, freq="D")
    merged = pd.DataFrame({"date": full_dates}) # 👈 여기서 merged가 탄생합니다!

    # 데이터 순차 병합
    for col in SERIES.keys():
        if col in fetched:
            new_data = fetched[col]
            merged = pd.merge(merged, new_data, on="date", how="left")
            if not existing.empty and col in existing.columns:
                merged[col] = merged[col].combine_first(existing[col])
        elif not existing.empty and col in existing.columns:
            merged = pd.merge(merged, existing[["date", col]], on="date", how="left")

    # 3. 데이터 자르기 및 저장 (이제 merged가 확실히 존재함!)
    merged = merged.sort_values("date").drop_duplicates("date", keep="last")
    if len(merged) > fetch_days:
        merged = merged.tail(fetch_days)

    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")
    merged.to_csv(OUT_CSV, index=False)
    print(f"✅ 업데이트 완료: {OUT_CSV} ({len(merged)} rows)")

if __name__ == "__main__":
    main()
