from __future__ import annotations
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

# FRED SERIES 정의 (FCI, REAL_RATE)
SERIES = {
    "FCI": "FCI",
    "REAL_RATE": "IR14230",
}

def fetch_fred(series_id: str) -> pd.DataFrame:
    """Fetch a FRED series via CSV download (no API key) and return clean dataframe."""
    url = f"{FRED_CSV}{series_id}"
    df = pd.read_csv(url)

    # FRED CSV format: DATE,<SERIESID>
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    df = df.dropna(subset=["date", series_id]).sort_values("date").reset_index(drop=True)
    
    return df

def load_fred_extras_df() -> pd.DataFrame:
    """Load FRED macro extras data (FCI, REAL_RATE)."""
    fci_df = fetch_fred(SERIES["FCI"])
    real_rate_df = fetch_fred(SERIES["REAL_RATE"])

    # Merge the two dataframes
    merged_df = pd.merge(fci_df, real_rate_df, on="date", how="outer")
    
    return merged_df

def main():
    # Example of using the fetch and load methods
    fci_real_rate_df = load_fred_extras_df()
    
    if fci_real_rate_df.empty:
        print("No data fetched")
        return
    
    print(fci_real_rate_df.head())  # Display the first few rows for testing

    # Save data for further use or future processing
    fci_real_rate_df.to_csv(DATA_DIR / "fred_macro_extras.csv", index=False)
    print(f"Data saved to {DATA_DIR / 'fred_macro_extras.csv'}")

if __name__ == "__main__":
    main()
