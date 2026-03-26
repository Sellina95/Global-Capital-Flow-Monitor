import pandas as pd
import os

# 수익률 계산을 위한 함수
def calculate_daily_returns():
    etf_files = [f for f in os.listdir('data') if f.endswith('_data.csv')]
    etf_data = {}

    # 각 ETF 데이터 로드
    for file in etf_files:
        df = pd.read_csv(f"data/{file}", index_col="Date", parse_dates=True)
        ticker = file.split('_')[0]  # 파일 이름에서 ETF 티커 추출
        df['Adj Close'] = df['Adj Close'].fillna(0)  # 결측값 처리
        df['Pct Change'] = df['Adj Close'].pct_change()  # 일일 수익률 계산
        etf_data[ticker] = df

    # 모든 ETF의 수익률 출력
    for ticker, data in etf_data.items():
        print(f"[INFO] {ticker} daily returns:")
        print(data['Pct Change'].tail())  # 마지막 5일 수익률 출력

if __name__ == "__main__":
    calculate_daily_returns()