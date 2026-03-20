import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

START_DATE = "2022-01-01"

# ✅ 오늘 기준 +1일 (yfinance는 end exclusive라서)
END_DATE = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

TICKERS = [
    "EIS",
    "SPY",
    "EEM",
    "EMB",
    "GLD",
    "VXX",
    "FXI",
    "EWJ",
    "BND"
]

print("Downloading ETF data...")

data = yf.download(
    TICKERS,
    start=START_DATE,
    end=END_DATE,
    auto_adjust=True,
    progress=False
)

df = data["Close"]

df = df.reset_index()
df = df.rename(columns={"Date": "Date"})

# ✅ date 정리
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"]).sort_values("Date").drop_duplicates(subset=["Date"], keep="last")

# stringify
df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

df.to_csv("data/country_etf_data_combined.csv", index=False)

print("Saved: data/country_etf_data_combined.csv")
print("Last date:", df["Date"].iloc[-1] if not df.empty else "EMPTY")