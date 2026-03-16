import pandas as pd
from datetime import datetime

START_DATE = "2022-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

FRED_SERIES = {
    "TGA": "WTREGEN",       # Treasury General Account
    "RRP": "RRPONTSYD",     # Reverse Repo
    "WALCL": "WALCL",       # Fed balance sheet
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

# 단위 맞추기
# WALCL, TGA는 보통 millions 수준
# RRPONTSYD도 millions로 들어오는 경우가 많음
# 일단 원본 단위 그대로 두고 계산
out_df["NET_LIQ"] = out_df["WALCL"] - out_df["TGA"] - out_df["RRP"]

out_df = out_df.reset_index().rename(columns={"index": "date"})
out_df["date"] = out_df["date"].dt.strftime("%Y-%m-%d")

out_df.to_csv("data/liquidity_data.csv", index=False, encoding="utf-8-sig")
print("Saved: data/liquidity_data.csv")