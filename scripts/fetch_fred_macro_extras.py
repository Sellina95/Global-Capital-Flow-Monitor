# scripts/fetch_fred_macro_extras.py
from __future__ import annotations

from pathlib import Path
from typing import Optional
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

# --- network robustness knobs ---
HTTP_TIMEOUT_SEC = 20
RETRIES = 4
BACKOFF_SEC = 2.0


def _http_get_bytes(url: str) -> bytes:
    """
    Robust HTTP GET for GitHub Actions:
    - timeout
    - retries with backoff
    Raises last exception if all retries fail.
    """
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
            # exponential-ish backoff
            time.sleep(BACKOFF_SEC * (i + 1))
    raise last_err if last_err else RuntimeError("Unknown HTTP error")


def fetch_fred(series_id: str) -> pd.DataFrame:
    """
    Fetch a single FRED series CSV and return DataFrame(date, <series_id>).
    Raises on failure (caller decides fallback behavior).
    """
    url = f"{FRED_CSV}{series_id}"
    raw = _http_get_bytes(url)

    # pandas can read from buffer
    df = pd.read_csv(BytesIO(raw))
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    df = df.dropna(subset=["date", series_id]).sort_values("date").reset_index(drop=True)
    return df


def _load_existing() -> Optional[pd.DataFrame]:
    if not OUT_CSV.exists():
        return None
    try:
        df = pd.read_csv(OUT_CSV)
        if "date" not in df.columns:
            return None
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates(subset=["date"], keep="last")
        return df.reset_index(drop=True)
    except Exception:
        return None


def _safe_fetch(series_key: str) -> Optional[pd.DataFrame]:
    """
    Returns df(date, <colname>) or None.
    Never raises.
    """
    series_id = SERIES[series_key]
    try:
        df = fetch_fred(series_id)
        colname = series_key  # normalize to FCI / REAL_RATE
        df = df.rename(columns={series_id: colname})
        return df
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, Exception) as e:
        print(f"[WARN] FRED fetch failed for {series_key} ({series_id}): {type(e).__name__}: {e}")
        return None


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing = _load_existing()

    fci_df = _safe_fetch("FCI")
    real_df = _safe_fetch("REAL_RATE")

    # Keep enough history for merge/ffill
    if fci_df is not None:
        fci_df = fci_df.tail(360)
    if real_df is not None:
        real_df = real_df.tail(360)

    # If both failed, keep existing file as-is (pipeline must not fail)
    if fci_df is None and real_df is None:
        if existing is not None:
            # keep existing, but normalize formatting to be safe
            out = existing.copy()
            for c in ["FCI", "REAL_RATE"]:
                if c in out.columns:
                    out[c] = pd.to_numeric(out[c], errors="coerce")
            out = out.sort_values("date").drop_duplicates(subset=["date"], keep="last")
            out = out.tail(120).reset_index(drop=True)
            out["date"] = out["date"].dt.strftime("%Y-%m-%d")
            out.to_csv(OUT_CSV, index=False)
            print(f"[OK] fred_macro_extras unchanged (using existing cache): {OUT_CSV} (rows={len(out)})")
            return

        # No existing cache: write an empty skeleton and exit 0
        empty = pd.DataFrame(columns=["date", "FCI", "REAL_RATE"])
        empty.to_csv(OUT_CSV, index=False)
        print(f"[OK] fred_macro_extras created empty (FRED unavailable): {OUT_CSV} (rows=0)")
        return

    # Build base for merge:
    # - prefer freshly fetched series
    # - for missing series, fall back to existing file if available
    if existing is not None:
        base = existing.copy()
    else:
        base = pd.DataFrame({"date": pd.to_datetime([])})

    # Merge new series (if available) onto base
    def _merge_series(base_df: pd.DataFrame, new_df: Optional[pd.DataFrame], col: str) -> pd.DataFrame:
        if new_df is None:
            # ensure column exists
            if col not in base_df.columns:
                base_df[col] = pd.NA
            return base_df
        # merge
        out = pd.merge(base_df, new_df[["date", col]], on="date", how="outer", suffixes=("", "_new"))
        if f"{col}_new" in out.columns:
            if col not in out.columns:
                out[col] = pd.NA
            out[col] = out[col].where(out[col].notna(), out[f"{col}_new"])
            # if we actually fetched new data, let it overwrite old data for overlapping dates
            out[col] = out[f"{col}_new"].where(out[f"{col}_new"].notna(), out[col])
            out = out.drop(columns=[f"{col}_new"])
        return out

    merged = base
    merged = _merge_series(merged, fci_df, "FCI")
    merged = _merge_series(merged, real_df, "REAL_RATE")

    merged = merged.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    merged["FCI"] = pd.to_numeric(merged.get("FCI"), errors="coerce").ffill()
    merged["REAL_RATE"] = pd.to_numeric(merged.get("REAL_RATE"), errors="coerce").ffill()

    # Save last ~90 rows (you can widen if you want)
    merged = merged.dropna(subset=["date"]).tail(90).reset_index(drop=True)
    merged["date"] = pd.to_datetime(merged["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    merged.to_csv(OUT_CSV, index=False)
    got_fci = "YES" if fci_df is not None else "NO"
    got_real = "YES" if real_df is not None else "NO"
    print(f"[OK] fred_macro_extras updated: {OUT_CSV} (rows={len(merged)}) | fetched: FCI={got_fci}, REAL_RATE={got_real}")


if __name__ == "__main__":
    # IMPORTANT: never crash the whole workflow from this script
    try:
        main()
    except Exception as e:
        print(f"[WARN] fetch_fred_macro_extras hard-failed but will not stop pipeline: {type(e).__name__}: {e}")
        # last-resort: keep existing or create empty skeleton
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if OUT_CSV.exists():
            print(f"[OK] Keeping existing: {OUT_CSV}")
        else:
            pd.DataFrame(columns=["date", "FCI", "REAL_RATE"]).to_csv(OUT_CSV, index=False)
            print(f"[OK] Wrote empty skeleton: {OUT_CSV}")
