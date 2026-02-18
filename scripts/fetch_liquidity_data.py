from __future__ import annotations

from pathlib import Path
import time
import pandas as pd
import urllib.error


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "liquidity_data.csv"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

SERIES = {
    "TGA": "WTREGEN",     # Treasury General Account (Millions of $)
    "RRP": "RRPONTSYD",   # Overnight Reverse Repo (Millions of $)
    "WALCL": "WALCL",     # Fed Total Assets (Millions of $) - weekly
}

def fetch_fred(series_id: str, retries: int = 3, delay: int = 5) -> pd.DataFrame:
    """Fetch a FRED series with retries. On failure, return empty DataFrame (fail-soft)."""
    url = f"{FRED_CSV}{series_id}"

    last_err = None
    for attempt in range(retries):
        try:
            df = pd.read_csv(url)
            df.columns = ["date", series_id]
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
            df = df.dropna(subset=["date", series_id]).sort_values("date").reset_index(drop=True)
            return df
        except Exception as e:
            last_err = e
            print(f"[WARN] fetch_fred({series_id}) attempt {attempt + 1}/{retries} failed: {type(e).__name__}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)

    print(f"[ERROR] fetch_fred({series_id}) failed after {retries} attempts. Last error: {type(last_err).__name__}: {last_err}")
    return pd.DataFrame(columns=["date", series_id])


def safe_read_existing(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    if csv_path.stat().st_size == 0:
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    try:
        df = pd.read_csv(csv_path)
        if df.empty or "date" not in df.columns:
            return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])
        return df
    except Exception:
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    tga_df = fetch_fred(SERIES["TGA"])
    rrp_df = fetch_fred(SERIES["RRP"])
    walcl_df = fetch_fred(SERIES["WALCL"])

    # ✅ fail-soft: if any required series is missing, don't break the workflow
    if tga_df.empty or rrp_df.empty or walcl_df.empty:
        print("[WARN] liquidity fetch incomplete (one or more series empty). Skipping update; keeping previous CSV.")
        return

    as_of = min(tga_df.iloc[-1]["date"], rrp_df.iloc[-1]["date"])

    def last_value_on_or_before(df: pd.DataFrame, col: str) -> float:
        sub = df[df["date"] <= as_of]
        if sub.empty:
            raise ValueError(f"No data on or before {as_of.date()} for {col}")
        return float(sub.iloc[-1][col])

    tga = last_value_on_or_before(tga_df, SERIES["TGA"])
    rrp = last_value_on_or_before(rrp_df, SERIES["RRP"])
    walcl = last_value_on_or_before(walcl_df, SERIES["WALCL"])

    net_liq = walcl - tga - rrp

    new_row = pd.DataFrame([{
        "date": as_of.strftime("%Y-%m-%d"),
        "TGA": tga,
        "RRP": rrp,
        "WALCL": walcl,
        "NET_LIQ": net_liq,
    }])

    old = safe_read_existing(OUT_CSV)

    combined = pd.concat([old, new_row], ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
    combined = combined.dropna(subset=["date"]).sort_values("date")
    combined = combined.drop_duplicates(subset=["date"], keep="last")
    combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")

    combined.to_csv(OUT_CSV, index=False)
    print(f"[OK] liquidity_data updated: {OUT_CSV} (rows={len(combined)})")


if __name__ == "__main__":
    main()
