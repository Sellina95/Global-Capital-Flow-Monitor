from pathlib import Path
import pandas as pd

DATA = Path("data/backtest")
RESULT = DATA / "results"

RESULT.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("Institutional Backtest Engine")
print("=" * 60)

files = {
    "macro": DATA / "macro_data.csv",
    "positioning": DATA / "positioning_data.csv",
    "sentiment": DATA / "sentiment_proxy.csv",
    "country_etf": DATA / "country_etf_data_combined.csv",
    "yield": DATA / "sovereign_yields.csv",
    "spread": DATA / "sovereign_spreads.csv",
}

loaded = {}

for name, path in files.items():

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    print(f"{name:15s} : {len(df):6,d} rows")

    loaded[name] = df

print()
print("All datasets loaded successfully.")
print()

macro = loaded["macro"]

print("Macro Period")
print(macro["date"].min(), "->", macro["date"].max())

print()

print("Ready for Backtest.")
