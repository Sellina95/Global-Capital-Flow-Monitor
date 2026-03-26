# 기존 코드 예시
import yfinance as yf
import pandas as pd
import os

# etf_symbols 딕셔너리 추가
etf_symbols = {
    "BND": "Vanguard Total Bond Market ETF",
    "EEM": "iShares MSCI Emerging Markets ETF",
    "EIS": "iShares MSCI Israel ETF",
    "EMB": "iShares J.P. Morgan USD Emerging Markets Bond ETF",
    "EWJ": "iShares MSCI Japan ETF",
    "FXI": "iShares China Large-Cap ETF",
    "GLD": "SPDR Gold Shares",
    "SPY": "SPDR S&P 500 ETF Trust",
    "VXX": "iPath Series B S&P 500 VIX Short-Term Futures ETN",
    "XLK": "Technology Select Sector SPDR",
    "XLV": "Health Care Select Sector SPDR",
    "XLP": "Consumer Staples Select Sector SPDR",
    "XLF": "Financials Select Sector SPDR",
    "QUAL": "iShares MSCI USA Quality Factor ETF",
    "COWZ": "Pacer US Cash Cows 100 ETF",
    "MTUM": "iShares MSCI USA Momentum Factor ETF"
}

# 티커에 대한 데이터를 Yahoo Finance에서 다운로드하여 CSV로 저장
def fetch_etf_data():
    etf_data = {}
    
    for ticker, name in etf_symbols.items():
        print(f"Downloading data for {name} ({ticker})...")
        data = yf.download(ticker, period="1y", progress=False)
        data['Ticker'] = ticker  # 티커 정보 추가
        etf_data[ticker] = data

    return etf_data

def save_etf_data_to_csv(etf_data):
    # 데이터를 data/etf_data.csv로 저장
    if not os.path.exists("data"):
        os.makedirs("data")
    
    for ticker, data in etf_data.items():
        data.to_csv(f"data/{ticker}_data.csv")  # 각 ETF를 개별 CSV로 저장

# 메인 함수 실행
if __name__ == "__main__":
    etf_data = fetch_etf_data()  # ETF 데이터 다운로드
    save_etf_data_to_csv(etf_data)  # 데이터 저장