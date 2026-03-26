import yfinance as yf
import pandas as pd

# ETF 심볼 리스트 (전체)
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

def calculate_returns(etf_symbols):
    # 수익률 계산을 위한 데이터 가져오기
    etf_data = {}  # ETF별 수익률 데이터를 담을 dictionary

    for symbol, name in etf_symbols.items():
        # 각 ETF에 대해 데이터 가져오기 (Yahoo Finance에서 다운로드)
        data = yf.download(symbol, start="2021-01-01", end="2022-01-01")  # 원하는 기간 설정
        data['pct_change'] = data['Adj Close'].pct_change()  # 조정 종가 수익률 계산
        
        # 계산된 수익률을 저장
        etf_data[symbol] = data['pct_change'].mean()  # 평균 수익률을 기록
    
    return etf_data

def save_to_csv(etf_data):
    # 계산된 수익률을 CSV로 저장
    df = pd.DataFrame.from_dict(etf_data, orient='index', columns=['Mean Return'])
    df.to_csv("data/etf_returns.csv")
    print("ETF 수익률이 'data/etf_returns.csv'에 저장되었습니다.")

if __name__ == "__main__":
    # ETF 수익률 계산
    etf_data = calculate_returns(etf_symbols)
    
    # CSV 파일로 저장
    save_to_csv(etf_data)