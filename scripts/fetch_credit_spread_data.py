from __future__ import annotations

from pathlib import Path
import time
from datetime import datetime, timezone, timedelta

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "credit_spread_data.csv"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="
SERIES_ID = "BAMLH0A0HYM2"

KST = timezone(timedelta(hours=9))


def fetch_fred(series_id: str, retries: int = 3, delay: int = 5) -> pd.DataFrame:
    url = f"{FRED_CSV}{series_id}"
    last_err = None

    for attempt in range(retries):
        try:
            df = pd.read_csv(url)
            df.columns = ["date", series_id]
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
            df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
            return df
        except Exception as e:
            last_err = e
            print(f"[WARN] fetch_fred({series_id}) attempt {attempt + 1}/{retries} failed: {type(e).__name__}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)

    print(f"[ERROR] fetch_fred({series_id}) failed after {retries} attempts. Last error: {type(last_err).__name__}: {last_err}")
    return pd.DataFrame(columns=["date", series_id])


def safe_read_existing(csv_path: Path) -> pd.DataFrame:
    base_cols = ["date", "HY_OAS"]

    if not csv_path.exists():
        return pd.DataFrame(columns=base_cols)

    if csv_path.stat().st_size == 0:
        return pd.DataFrame(columns=base_cols)

    try:
        df = pd.read_csv(csv_path)
        if df.empty or "date" not in df.columns:
            return pd.DataFrame(columns=base_cols)

        for col in base_cols:
            if col not in df.columns:
                df[col] = pd.NA

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["HY_OAS"] = pd.to_numeric(df["HY_OAS"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        return df[base_cols]
    except Exception as e:
        print(f"[WARN] safe_read_existing failed: {type(e).__name__}: {e}")
        return pd.DataFrame(columns=base_cols)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    old = safe_read_existing(OUT_CSV)
    hy = fetch_fred(SERIES_ID)

    today_kst = datetime.now(KST).date()
    today_ts = pd.Timestamp(today_kst)

    candidate_starts = []

    if not old.empty:
        candidate_starts.append(old["date"].min())

    if not hy.empty:
        candidate_starts.append(hy["date"].min())

    if candidate_starts:
        start_date = min(candidate_starts)
    else:
        start_date = today_ts

    # ✅ 오늘까지 날짜 무조건 생성
    full_dates = pd.date_range(start=start_date, end=today_ts, freq="D")
    base = pd.DataFrame({"date": full_dates})

    # 기존 csv merge
    combined = base.merge(old, on="date", how="left")

    # 새 FRED 데이터 merge
    if not hy.empty:
        hy = hy.rename(columns={SERIES_ID: "HY_OAS__new"})
        hy = hy[["date", "HY_OAS__new"]]
        combined = combined.merge(hy, on="date", how="left")

        # 새 값이 있으면 새 값 우선, 없으면 기존 값 유지
        combined["HY_OAS"] = combined["HY_OAS__new"].combine_first(combined["HY_OAS"])
        combined = combined.drop(columns=["HY_OAS__new"])

    combined["HY_OAS"] = pd.to_numeric(combined["HY_OAS"], errors="coerce")
    combined = combined.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")

    combined.to_csv(OUT_CSV, index=False)

    print(f"[DEBUG] HY_OAS last fetched date: {hy['date'].max() if not hy.empty else 'EMPTY'}")
    print(f"[DEBUG] CSV last date after update: {combined['date'].iloc[-1] if not combined.empty else 'EMPTY'}")
    print(f"[OK] credit_spread_data updated: {OUT_CSV} (rows={len(combined)})")


if __name__ == "__main__":
    main()
