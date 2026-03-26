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

    # 데이터 폴더 경로 설정 (data 폴더 안에 파일들이 있다는 가정)
    data_directory = 'data/'  # 수정된 경로: data 폴더 안에 있는 각 ETF 파일들

    for symbol in etf_symbols:
        file_path = os.path.join(data_directory, f"{symbol}_data.csv")  # 경로 수정
        
        # 파일이 존재하는지 확인
        if os.path.exists(file_path):
            data = pd.read_csv(file_path, index_col="Date", parse_dates=True)  # 파일 읽기
            data['pct_change'] = data['Adj Close'].pct_change()  # 수익률 계산
            etf_data[symbol] = data['pct_change'].mean()  # 평균 수익률 기록
        else:
            print(f"Warning: {file_path} not found.")  # 파일이 없을 경우 경고 메시지
    
    return etf_data

def save_to_csv(etf_data):
    # 계산된 수익률을 CSV로 저장
    df = pd.DataFrame.from_dict(etf_data, orient='index', columns=['Mean Return'])
    df.to_csv("data/etf_returns.csv")  # 수정된 경로로 저장
    
    # 파일 내용 확인 (첫 5줄 출력)
    print(df.head())
    print("ETF 수익률이 'data/etf_returns.csv'에 저장되었습니다.")

if __name__ == "__main__":
    # ETF 수익률 계산
    etf_data = calculate_returns(etf_symbols)
    
    # CSV 파일로 저장
    save_to_csv(etf_data)