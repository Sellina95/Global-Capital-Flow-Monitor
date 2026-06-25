import pandas as pd
from pathlib import Path

START_DATE = "2008-01-01"

BASE_DIR = Path(__file__).resolve().parents[2]
OUT_DIR = BASE_DIR / "data" / "backtest"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = OUT_DIR / "sovereign_yields.csv"

FRED_SERIES = {
    "US10Y": "DGS10",
    "KR10Y": "IRLTLT01KRM156N",
    "JP10Y": "IRLTLT01JPM156N",
    "DE10Y": "IRLTLT01DEM156N",
    "CN10Y": "IRLTLT01CNM156N",
    "IL10Y": "IRLTLT01ILM156N",
    "TR10Y": "IRLTLT01TRM156N",
    "GB10Y": "IRLTLT01GBM156N",
    "MX10Y": "IRLTLT01MXM156N",
}

TARGET_COLS = [
    "US10Y", "KR10Y", "JP10Y", "DE10Y",
    "CN10Y", "IL10Y", "TR10Y", "GB10Y", "MX10Y"
]


def fetch_fred_series(series_id: str, col_name: str) -> pd.DataFrame:
    url = (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}&observation_start={START_DATE}"
    )

    print(f"[FETCH] {col_name} ({series_id})")

    df = pd.read_csv(url)
    df.columns = ["date", col_name]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[col_name] = pd.to_numeric(df[col_name], errors="coerce")

    df = df.dropna(subset=["date"])
    df = df[df["date"] >= START_DATE]

    return df.set_index("date")[[col_name]]


def build():
    frames = []

    for col_name, series_id in FRED_SERIES.items():
        try:
            data = fetch_fred_series(series_id, col_name)
            frames.append(data)
        except Exception as e:
            print(f"[WARN FAIL] {col_name} ({series_id}): {e}")

    if not frames:
        raise Exception("NO DATA DOWNLOADED")

    df = pd.concat(frames, axis=1).sort_index()

    daily_index = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq="D"
    )

    df = df.reindex(daily_index)
    df.index.name = "date"
    df = df.ffill()
    df = df.reset_index()

    for col in TARGET_COLS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[["date"] + TARGET_COLS]

    return df


def main():
    df = build()
    df.to_csv(OUTPUT_PATH, index=False)

    print("\n======================")
    print("DONE")
    print(f"SAVED -> {OUTPUT_PATH}")
    print("======================")
    print(df.tail())


if __name__ == "__main__":
    main()