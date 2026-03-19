from __future__ import annotations

from pathlib import Path
from typing import Optional
from datetime import datetime, timezone, timedelta
import time
from io import BytesIO
import urllib.request
import urllib.error

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "fred_macro_extras.csv"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

SERIES = {
    "FCI": "NFCI",         # Chicago Fed National Financial Conditions Index (weekly)
    "REAL_RATE": "DFII10", # 10Y TIPS Real Yield (daily)
}

HTTP_TIMEOUT_SEC = 20
RETRIES = 4
BACKOFF_SEC = 2.0
KST = timezone(timedelta(hours=9))


def _http_get_bytes(url: str) -> bytes:
    last_err: Optional[Exception] = None
    for i in range(RETRIES):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Global-Capital-Flow-Monitor/1.0 (GitHubActions)",
                    "Accept": "text/csv,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            time.sleep(BACKOFF_SEC * (i + 1))
    raise last_err if last_err else RuntimeError("Unknown HTTP error")


def fetch_fred(series_id: str) -> pd.DataFrame:
    url = f"{FRED_CSV}{series_id}"
    raw = _http_get_bytes(url)

    df = pd.read_csv(BytesIO(raw))
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def _load_existing() -> pd.DataFrame:
    base_cols = ["date", "FCI", "REAL_RATE"]

    if not OUT_CSV.exists():
        return pd.DataFrame(columns=base_cols)

    try:
        df = pd.read_csv(OUT_CSV)
        if "date" not in df.columns:
            return pd.DataFrame(columns=base_cols)

        for col in base_cols:
            if col not in df.columns:
                df[col] = pd.NA

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["FCI"] = pd.to_numeric(df["FCI"], errors="coerce")
        df["REAL_RATE"] = pd.to_numeric(df["REAL_RATE"], errors="coerce")

        df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates(subset=["date"], keep="last")
        return df.reset_index(drop=True)[base_cols]
    except Exception as e:
        print(f"[WARN] _load_existing failed: {type(e).__name__}: {e}")
        return pd.DataFrame(columns=base_cols)


def _safe_fetch(series_key: str) -> Optional[pd.DataFrame]:
    series_id = SERIES[series_key]
    try:
        df = fetch_fred(series_id)
        df = df.rename(columns={series_id: series_key})
        return df
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, Exception) as e:
        print(f"[WARN] FRED fetch failed for {series_key} ({series_id}): {type(e).__name__}: {e}")
        return None


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing = _load_existing()
    fci_df = _safe_fetch("FCI")
    real_df = _safe_fetch("REAL_RATE")

    today_kst = datetime.now(KST).date()
    today_ts = pd.Timestamp(today_kst)

    candidate_starts = []

    if not existing.empty:
        candidate_starts.append(existing["date"].min())

    if fci_df is not None and not fci_df.empty:
        candidate_starts.append(fci_df["date"].min())

    if real_df is not None and not real_df.empty:
        candidate_starts.append(real_df["date"].min())

    if candidate_starts:
        start_date = min(candidate_starts)
    else:
        start_date = today_ts

    # ✅ 오늘까지 날짜 무조건 생성
    full_dates = pd.date_range(start=start_date, end=today_ts, freq="D")
    base = pd.DataFrame({"date": full_dates})

    # 기존 csv merge
    merged = base.merge(existing, on="date", how="left")

    def _merge_series(base_df: pd.DataFrame, new_df: Optional[pd.DataFrame], col: str) -> pd.DataFrame:
        if new_df is None or new_df.empty:
            if col not in base_df.columns:
                base_df[col] = pd.NA
            return base_df

        new_df = new_df[["date", col]].copy()
        new_df[col] = pd.to_numeric(new_df[col], errors="coerce")
        new_df = new_df.rename(columns={col: f"{col}__new"})

        out = pd.merge(base_df, new_df, on="date", how="left")

        if col not in out.columns:
            out[col] = pd.NA

        out[col] = out[f"{col}__new"].combine_first(out[col])
        out = out.drop(columns=[f"{col}__new"])
        return out

    merged = _merge_series(merged, fci_df, "FCI")
    merged = _merge_series(merged, real_df, "REAL_RATE")

    merged["FCI"] = pd.to_numeric(merged["FCI"], errors="coerce")
    merged["REAL_RATE"] = pd.to_numeric(merged["REAL_RATE"], errors="coerce")

    merged = merged.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")

    merged.to_csv(OUT_CSV, index=False)

    got_fci = "YES" if fci_df is not None and not fci_df.empty else "NO"
    got_real = "YES" if real_df is not None and not real_df.empty else "NO"

    print(f"[DEBUG] FCI last fetched date: {fci_df['date'].max() if fci_df is not None and not fci_df.empty else 'EMPTY'}")
    print(f"[DEBUG] REAL_RATE last fetched date: {real_df['date'].max() if real_df is not None and not real_df.empty else 'EMPTY'}")
    print(f"[DEBUG] CSV last date after update: {merged['date'].iloc[-1] if not merged.empty else 'EMPTY'}")
    print(f"[OK] fred_macro_extras updated: {OUT_CSV} (rows={len(merged)}) | fetched: FCI={got_fci}, REAL_RATE={got_real}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[WARN] fetch_fred_macro_extras hard-failed but will not stop pipeline: {type(e).__name__}: {e}")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if OUT_CSV.exists():
            print(f"[OK] Keeping existing: {OUT_CSV}")
        else:
            pd.DataFrame(columns=["date", "FCI", "REAL_RATE"]).to_csv(OUT_CSV, index=False)
            print(f"[OK] Wrote empty skeleton: {OUT_CSV}")
