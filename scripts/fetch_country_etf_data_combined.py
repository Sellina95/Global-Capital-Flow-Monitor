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
    "BND",
]

print("Downloading ETF data...")

data = yf.download(
    TICKERS,
    start=START_DATE,
    end=END_DATE,
    auto_adjust=True,
    progress=False,
    threads=True,
)

if data is None or data.empty:
    print("[WARN] No data fetched → skip overwrite")
    raise SystemExit(0)

if isinstance(data.columns, pd.MultiIndex):
    if "Close" not in data.columns.get_level_values(0):
        print(f"[WARN] Close level missing. columns={data.columns}")
        raise SystemExit(0)
    df = data["Close"].copy()
else:
    if "Close" not in data.columns:
        print(f"[WARN] Close column missing. columns={list(data.columns)}")
        raise SystemExit(0)
    df = data[["Close"]].copy()
    df.columns = TICKERS[:1]

if df is None or df.empty:
    print("[WARN] Empty Close data → skip overwrite")
    raise SystemExit(0)

if len(df.columns) < 3:
    print(f"[WARN] Too few ETF columns → skip overwrite. columns={list(df.columns)}")
    raise SystemExit(0)

df = df.reset_index()

# yfinance/pandas 환경에 따라 날짜 컬럼명이 Date, Datetime, index, date 등으로 달라질 수 있음
date_col = None
for candidate in ["Date", "Datetime", "date", "datetime", "index"]:
    if candidate in df.columns:
        date_col = candidate
        break

if date_col is None:
    print(f"[WARN] Date column missing after reset_index. columns={list(df.columns)}")
    raise SystemExit(0)

df = df.rename(columns={date_col: "Date"})

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = (
    df.dropna(subset=["Date"])
      .sort_values("Date")
      .drop_duplicates(subset=["Date"], keep="last")
)

df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

# 컬럼 정리: Date + tickers 중 실제 존재하는 것
ordered_cols = ["Date"] + [ticker for ticker in TICKERS if ticker in df.columns]
df = df[ordered_cols]

if df.empty:
    print("[WARN] Final dataframe empty → skip overwrite")
    raise SystemExit(0)

df.to_csv("data/country_etf_data_combined.csv", index=False)

print("Saved: data/country_etf_data_combined.csv")
print("Columns:", list(df.columns))
print("Last date:", df["Date"].iloc[-1])