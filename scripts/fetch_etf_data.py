import yfinance as yf
import os
import pandas as pd

# ETF 목록 및 기호
etf_symbols = {
    "BND": "Vanguard Total Bond Market ETF",
    "EEM": "iShares MSCI Emerging Markets ETF",
    "EIS": "iShares MSCI Israel ETF",
    "EMB": "iShares J.P. Morgan USD Emerging Markets Bond ETF",
    "EWJ": "iShares MSCI Japan ETF",
    "FXI": "iShares China Large-Cap ETF",
    "GLD": "SPDR Gold Shares",
    "SPY": "SPDR S&P 500 ETF Trust",
    "VXX": "iPath Series B S&P 500 VIX Short-Term Futures ETN"
}

def download_etf_data(symbols: dict, start_date="2010-01-01", end_date="2026-01-01"):
    data = {}
    for ticker, name in symbols.items():
        print(f"[INFO] Downloading {name} data...")
        etf_data = yf.download(ticker, start=start_date, end=end_date)
        data[ticker] = etf_data
        # 저장 경로 설정
        file_path = f"data/{ticker}_data.csv"
        etf_data.to_csv(file_path)
        print(f"[INFO] {ticker} data saved to {file_path}")
    return data

if __name__ == "__main__":
    download_etf_data(etf_symbols)