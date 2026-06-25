import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_PATH = BASE_DIR / "data" / "backtest" / "sovereign_yields.csv"
OUTPUT_PATH = BASE_DIR / "data" / "backtest" / "sovereign_spreads.csv"


def main():

    df = pd.read_csv(INPUT_PATH)

    spread_df = pd.DataFrame()
    spread_df["date"] = df["date"]

    countries = [
        "KR10Y",
        "JP10Y",
        "DE10Y",
        "CN10Y",
        "IL10Y",
        "TR10Y",
        "GB10Y",
        "MX10Y",
    ]

    for col in countries:
        spread_name = col.replace("10Y", "_US_SPREAD")
        spread_df[spread_name] = df[col] - df["US10Y"]

    spread_df.to_csv(OUTPUT_PATH, index=False)

    print("\n======================")
    print("DONE")
    print(f"SAVED -> {OUTPUT_PATH}")
    print("======================")
    print(spread_df.tail())


if __name__ == "__main__":
    main()