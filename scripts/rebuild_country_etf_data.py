import pandas as pd
import yfinance as yf

START_DATE = "2022-01-01"
END_DATE = None

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

# Close price만 사용
df = data["Close"]

df = df.reset_index()
df = df.rename(columns={"Date": "Date"})

df.to_csv("data/country_etf_data_combined.csv", index=False)

print("Saved: data/country_etf_data_combined.csv")