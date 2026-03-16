import pandas as pd
import yfinance as yf
from datetime import datetime

START_DATE = "2022-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

# 먼저 5개만 테스트
YAHOO_TICKERS = {
    "US10Y": "^TNX",
    "DXY": "UUP",
    "WTI": "CL=F",
    "VIX": "^VIX",
    "USDKRW": "KRW=X",
}

def download_yahoo_series(ticker: str, start: str, end: str) -> pd.Series:
    df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for ticker: {ticker}")

    if "Adj Close" in df.columns:
        series = df["Adj Close"]
    else:
        series = df["Close"]

    series.name = None
    return series

# 전체 날짜 틀 만들기
full_index = pd.date_range(start=START_DATE, end=END_DATE, freq="D")
macro_df = pd.DataFrame(index=full_index)

# Yahoo 다운로드
for col, ticker in YAHOO_TICKERS.items():
    try:
        s = download_yahoo_series(ticker, START_DATE, END_DATE)
        s.index = pd.to_datetime(s.index).normalize()
        macro_df[col] = s.reindex(full_index)
        print(f"[OK] Yahoo - {col}")
    except Exception as e:
        macro_df[col] = pd.NA
        print(f"[ERROR] Yahoo - {col}: {e}")

# 저장용 구조 만들기
macro_df = macro_df.reset_index().rename(columns={"index": "date"})
macro_df["datetime"] = macro_df["date"].dt.strftime("%Y-%m-%d")
macro_df["date"] = macro_df["date"].dt.strftime("%Y-%m-%d")

# 컬럼 순서 정리
macro_df = macro_df[["datetime", "date", "US10Y", "DXY", "WTI", "VIX", "USDKRW"]]

# 저장
macro_df.to_csv("macro_data_test.csv", index=False, encoding="utf-8-sig")
print("Saved: macro_data_test.csv")
