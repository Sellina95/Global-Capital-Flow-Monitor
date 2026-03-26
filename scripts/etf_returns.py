import os
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
    etf_data = {}  # ETF별 수익률 데이터를 담을 dictionary

    # 파일 경로 (기존에 다운로드 받은 ETF 파일들이 이 경로에 있어야 한다고 가정)
    data_directory = 'data/' 기존 데이터가 저장된 폴더

    for symbol in etf_symbols:
        file_path = os.path.join(data_directory, f"{symbol}_data.csv")  # 각 ETF에 대한 데이터 파일 경로
        if os.path.exists(file_path):
            # header=1로 두 번째 줄을 헤더로 사용
            data = pd.read_csv(file_path, index_col="Date", header=1, parse_dates=True)  # 날짜별 데이터 로드
            data['pct_change'] = data['Close'].pct_change()  # Close 가격을 기준으로 수익률 계산
            etf_data[symbol] = data['pct_change'].mean()  # 평균 수익률을 기록

        else:
            print(f"Warning: {file_path} not found.")
    
    return etf_data

def save_to_csv(etf_data):
    # 계산된 수익률을 CSV로 저장
    df = pd.DataFrame.from_dict(etf_data, orient='index', columns=['Mean Return'])
    df.to_csv("data/etf_returns.csv")
    
    # 파일 내용 확인 (첫 5줄 출력)
    print(df.head())
    print("ETF 수익률이 'data/etf_returns.csv'에 저장되었습니다.")

if __name__ == "__main__":
    # ETF 수익률 계산
    etf_data = calculate_returns(etf_symbols)
    
    # CSV 파일로 저장
    save_to_csv(etf_data)