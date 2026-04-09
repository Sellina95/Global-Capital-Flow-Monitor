from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone, timedelta
import time
import pandas as pd
from urllib.error import URLError, HTTPError

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "sovereign_yields.csv"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

KST = timezone(timedelta(hours=9))

SERIES = {
    "US10Y": "DGS10",
    "KR10Y": "IRLTLT01KRM156N",
    "JP10Y": "IRLTLT01JPM156N",
    "DE10Y": "IRLTLT01DEM156N",
    "CN10Y": "CHILT",           # 중국 (China 10Y)
    "IL10Y": "IRLTLT01ILM156N", # 이스라엘 (Israel 10Y)
    "TR10Y": "IRLTLT01TRM156N", # 터키 (Turkey 10Y)
    "GB10Y": "IRLTLT01GBM156N", # 영국 (UK 10Y)
    "MX10Y": "IRLTLT01MXM156N", # 멕시코 (Mexico 10Y)
}


def fetch_fred_csv(series_id: str, max_retries: int = 5, sleep_base: float = 1.5) -> pd.DataFrame:
    url = f"{FRED_CSV}{series_id}"
    last_err = None

    for attempt in range(1, max_retries + 1):
        try:
            df = pd.read_csv(url)
            if df is None or df.empty:
                return pd.DataFrame()
            df.columns = ["date", series_id]
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
            df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
            return df
        except (HTTPError, URLError, Exception) as e:
            last_err = e
            time.sleep(sleep_base * attempt)

    print(f"[WARN] fetch failed for {series_id}: {type(last_err).__name__}: {last_err}")
    return pd.DataFrame()


def _load_existing() -> pd.DataFrame:
    base_cols = ["date"] + list(SERIES.keys())

    if not OUT_CSV.exists() or OUT_CSV.stat().st_size == 0:
        return pd.DataFrame(columns=base_cols)

    try:
        df = pd.read_csv(OUT_CSV)
        if "date" not in df.columns:
            return pd.DataFrame(columns=base_cols)

        for col in base_cols:
            if col not in df.columns:
                df[col] = pd.NA

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        for col in SERIES.keys():
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates(subset=["date"], keep="last")
        return df.reset_index(drop=True)[base_cols]
    except Exception as e:
        print(f"[WARN] _load_existing failed: {type(e).__name__}: {e}")
        return pd.DataFrame(columns=base_cols)


def main(days: int = 365) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing = _load_existing()

    # 1. 누락 데이터 감지 및 fetch_days 결정
    if existing.empty or "CN10Y" not in existing.columns or existing["CN10Y"].isna().all():
        print("🚨 누락된 과거 데이터를 감지했습니다. 전체 기간(2000일) 조회를 시작합니다.")
        fetch_days = 2000
    else:
        fetch_days = days

    fetched = {}
    for col, sid in SERIES.items():
        print(f"[FETCH] {col} ({sid})")
        # 💡 [수정 포인트] 여기서 fetch_days를 사용해야 합니다!
        # 하지만 현재 fetch_fred_csv 함수 구조상 URL에 직접 기간을 넣지 않으므로, 
        # FRED CSV 다운로드 URL은 보통 전체 데이터를 줍니다.
        # 따라서 병합(Merge) 후 마지막에 '자르는(tail)' 기준을 fetch_days로 잡아야 합니다.
        
        df = fetch_fred_csv(sid)
        if df.empty:
            print("  -> no data")
            fetched[col] = None
            continue
        df = df.rename(columns={sid: col})
        fetched[col] = df
        print(f"  -> last fetched date: {df['date'].max()}")

    today_ts = pd.Timestamp(datetime.now(KST).date())

    # ... (중략: 병합 로직 동일) ...

    # 2. 마지막에 데이터를 자를 때 days 대신 fetch_days 사용
    if fetch_days is not None and len(merged) > fetch_days:
        merged = merged.tail(fetch_days).reset_index(drop=True) # 👈 여기서 fetch_days 적용!

    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")
    merged.to_csv(OUT_CSV, index=False)

    print(f"[DEBUG] CSV last date after update: {merged['date'].iloc[-1] if not merged.empty else 'EMPTY'}")
    print(f"[OK] sovereign_yields updated: {OUT_CSV} (rows={len(merged)})")

if __name__ == "__main__":
    main()
