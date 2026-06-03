from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone, timedelta
import time
import pandas as pd

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
    "CN10Y": "INTDSRCNM193N",
    "IL10Y": "IRLTLT01ILM156N",
    "TR10Y": "INTDSRTRM193N",
    "GB10Y": "IRLTLT01GBM156N",
    "MX10Y": "IRLTLT01MXM156N",
}


def fetch_fred_csv(series_id: str, max_retries: int = 3) -> pd.DataFrame:
    url = f"{FRED_CSV}{series_id}"

    for attempt in range(1, max_retries + 1):
        try:
            df = pd.read_csv(url)

            if df is None or df.empty:
                return pd.DataFrame()

            df.columns = ["date", series_id]
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df[series_id] = pd.to_numeric(df[series_id], errors="coerce")

            df = df.dropna(subset=["date"])
            return df[["date", series_id]]

        except Exception as e:
            print(f"[WARN] FRED fetch failed: {series_id} attempt={attempt} error={e}")
            time.sleep(1 * attempt)

    return pd.DataFrame()


def _load_existing() -> pd.DataFrame:
    if not OUT_CSV.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(OUT_CSV, parse_dates=["date"])
        return df
    except Exception:
        return pd.DataFrame()


def main(days: int = 365) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    today_ts = pd.Timestamp(datetime.now(KST).date())
    existing = _load_existing()

    missing_major_data = (
        existing.empty
        or any(col not in existing.columns for col in SERIES.keys())
        or existing.drop(columns=["date"], errors="ignore").isna().all().any()
    )

    if missing_major_data:
        print("🚨 누락 데이터 감지! 2000일치 풀 스캔 시작합니다.")
        fetch_days = 2000
        start_date = today_ts - timedelta(days=fetch_days)
    else:
        fetch_days = days
        start_date = today_ts - timedelta(days=fetch_days)

    fetched = {}

    for col, sid in SERIES.items():
        print(f"[FETCH] {col}")
        df = fetch_fred_csv(sid)

        if not df.empty:
            df = df.rename(columns={sid: col})
            fetched[col] = df
            print(f"[OK] {col}: rows={len(df)}, last={df['date'].max().date()}")
        else:
            print(f"[WARN] {col}: no data fetched")

    full_dates = pd.date_range(start=start_date, end=today_ts, freq="D")
    merged = pd.DataFrame({"date": full_dates})

    for col in SERIES.keys():
        new_data = fetched.get(col)

        if new_data is not None and not new_data.empty:
            new_data = new_data[["date", col]].copy()
            merged = merged.merge(new_data, on="date", how="left")
        else:
            merged[col] = pd.NA

        if not existing.empty and col in existing.columns:
            old = existing[["date", col]].copy()
            old = old.rename(columns={col: f"{col}_old"})
            merged = merged.merge(old, on="date", how="left")

            merged[col] = merged[col].combine_first(merged[f"{col}_old"])
            merged = merged.drop(columns=[f"{col}_old"])

    merged = merged.sort_values("date").drop_duplicates("date", keep="last")

    if len(merged) > fetch_days:
        merged = merged.tail(fetch_days)

    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")
    merged.to_csv(OUT_CSV, index=False)

    print(f"✅ 업데이트 완료: {OUT_CSV} ({len(merged)} rows)")


if __name__ == "__main__":
    main()