import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

START_DATE = "2022-01-01"

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

if data is None or data.empty:
    print("[WARN] No data fetched → skip overwrite")
    exit()

df = data["Close"]

if df is None or df.empty:
    print("[WARN] Empty Close data → skip overwrite")
    exit()

# 컬럼 수 체크 (최소 몇 개는 있어야 정상)
if len(df.columns) < 3:
    print("[WARN] Too few ETF columns → skip overwrite")
    exit()

df = df.reset_index()
df = df.rename(columns={"Date": "Date"})

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date"]).sort_values("Date").drop_duplicates(subset=["Date"], keep="last")

df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

df.to_csv("data/country_etf_data_combined.csv", index=False)

print("Saved: data/country_etf_data_combined.csv")
print("Last date:", df["Date"].iloc[-1] if not df.empty else "EMPTY")