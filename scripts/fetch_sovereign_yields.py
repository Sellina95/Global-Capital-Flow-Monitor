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

    fetched = {}
    for col, sid in SERIES.items():
        print(f"[FETCH] {col} ({sid})")
        df = fetch_fred_csv(sid)
        if df.empty:
            print("  -> no data")
            fetched[col] = None
            continue
        df = df.rename(columns={sid: col})
        fetched[col] = df
        print(f"  -> last fetched date: {df['date'].max()}")

    today_ts = pd.Timestamp(datetime.now(KST).date())

    candidate_starts = []
    if not existing.empty:
        candidate_starts.append(existing["date"].min())

    for col, df in fetched.items():
        if df is not None and not df.empty:
            candidate_starts.append(df["date"].min())

    if candidate_starts:
        start_date = min(candidate_starts)
    else:
        start_date = today_ts

    # ✅ 오늘까지 날짜 무조건 생성
    full_dates = pd.date_range(start=start_date, end=today_ts, freq="D")
    base = pd.DataFrame({"date": full_dates})

    merged = base.merge(existing, on="date", how="left")

    def _merge_series(base_df: pd.DataFrame, new_df: pd.DataFrame | None, col: str) -> pd.DataFrame:
        if new_df is None or new_df.empty:
            if col not in base_df.columns:
                base_df[col] = pd.NA
            return base_df

        work = new_df[["date", col]].copy()
        work[col] = pd.to_numeric(work[col], errors="coerce")
        work = work.rename(columns={col: f"{col}__new"})

        out = base_df.merge(work, on="date", how="left")

        if col not in out.columns:
            out[col] = pd.NA

        # 새 값 있으면 새 값 우선, 없으면 기존 유지
        out[col] = out[f"{col}__new"].combine_first(out[col])
        out = out.drop(columns=[f"{col}__new"])
        return out

    for col in SERIES.keys():
        merged = _merge_series(merged, fetched.get(col), col)

    for col in SERIES.keys():
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    merged = merged.sort_values("date").drop_duplicates(subset=["date"], keep="last")

    if days is not None and len(merged) > days:
        merged = merged.tail(days).reset_index(drop=True)

    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")
    merged.to_csv(OUT_CSV, index=False)

    print(f"[DEBUG] CSV last date after update: {merged['date'].iloc[-1] if not merged.empty else 'EMPTY'}")
    print(f"[OK] sovereign_yields updated: {OUT_CSV} (rows={len(merged)})")


if __name__ == "__main__":
    main()
