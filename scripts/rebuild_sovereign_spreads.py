import pandas as pd
from datetime import datetime

START_DATE = "2022-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

FRED_SERIES = {
    "US10Y_Y": "DGS10",              # daily
    "KR10Y_Y": "IRLTLT01KRM156N",    # monthly
    "JP10Y_Y": "IRLTLT01JPM156N",    # monthly
    "DE10Y_Y": "IRLTLT01DEM156N",    # monthly
    "IL10Y_Y": "IRLTLT01ILM156N",    # monthly
}

def download_fred_csv_series(series_code: str) -> pd.DataFrame:
    url = FRED_CSV + series_code
    df = pd.read_csv(url)

    df.columns = ["date", series_code]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df[series_code] = pd.to_numeric(df[series_code], errors="coerce")

    return df

full_index = pd.date_range(start=START_DATE, end=END_DATE, freq="D")
out_df = pd.DataFrame(index=full_index)

for col, fred_code in FRED_SERIES.items():
    try:
        df = download_fred_csv_series(fred_code)
        df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]
        df = df.set_index("date")
        out_df[col] = df[fred_code].reindex(full_index)
        print(f"[OK] FRED - {col}")
    except Exception as e:
        out_df[col] = pd.NA
        print(f"[ERROR] FRED - {col}: {e}")

# Spread 계산: 국가 10Y - US10Y
out_df["KR10Y_SPREAD"] = out_df["KR10Y_Y"] - out_df["US10Y_Y"]
out_df["JP10Y_SPREAD"] = out_df["JP10Y_Y"] - out_df["US10Y_Y"]
out_df["DE10Y_SPREAD"] = out_df["DE10Y_Y"] - out_df["US10Y_Y"]
out_df["IL10Y_SPREAD"] = out_df["IL10Y_Y"] - out_df["US10Y_Y"]

out_df = out_df.reset_index().rename(columns={"index": "date"})
out_df["date"] = out_df["date"].dt.strftime("%Y-%m-%d")

out_df.to_csv("data/sovereign_spreads.csv", index=False, encoding="utf-8-sig")
print("Saved: data/sovereign_spreads.csv")