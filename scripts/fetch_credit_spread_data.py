# scripts/fetch_credit_spread_data.py
from __future__ import annotations

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "credit_spread_data.csv"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

# ✅ ICE BofA US High Yield Index Option-Adjusted Spread (Percent)
# FRED series id: BAMLH0A0HYM2
SERIES_ID = "BAMLH0A0HYM2"


def fetch_fred(series_id: str) -> pd.DataFrame:
    df = pd.read_csv(f"{FRED_CSV}{series_id}")
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    df = df.dropna(subset=["date", series_id]).sort_values("date").reset_index(drop=True)
    return df


def safe_read_existing(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        return pd.DataFrame(columns=["date", "HY_OAS"])

    if csv_path.stat().st_size == 0:
        return pd.DataFrame(columns=["date", "HY_OAS"])

    try:
        df = pd.read_csv(csv_path)
        if df.empty or "date" not in df.columns:
            return pd.DataFrame(columns=["date", "HY_OAS"])
        return df
    except Exception:
        return pd.DataFrame(columns=["date", "HY_OAS"])


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    hy = fetch_fred(SERIES_ID)

    # last available in FRED
    as_of = hy.iloc[-1]["date"]
    hy_oas = float(hy.iloc[-1][SERIES_ID])

    new_row = pd.DataFrame([{
        "date": as_of.strftime("%Y-%m-%d"),
        "HY_OAS": hy_oas,
    }])

    old = safe_read_existing(OUT_CSV)

    combined = pd.concat([old, new_row], ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
    combined = combined.dropna(subset=["date"]).sort_values("date")
    combined = combined.drop_duplicates(subset=["date"], keep="last")
    combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")

    combined.to_csv(OUT_CSV, index=False)
    print(f"[OK] credit_spread_data updated: {OUT_CSV} (rows={len(combined)})")


if __name__ == "__main__":
    main()
