import os
import yfinance as yf
import pandas as pd
from datetime import datetime

# 국가별 ETF 목록 정의 (전체 ETF 리스트)
country_etf_list = [
    "EIS",    # Israel ETF
    "SPY",    # S&P 500 ETF (미국)
    "EEM",    # Emerging Markets ETF
    "EMB",    # Emerging Market Bonds ETF
    "GLD",    # Gold ETF
    "VXX",    # Volatility ETF
    "FXI",    # China ETF
    "EWJ",    # Japan ETF
    "BND",    # Total Bond Market ETF
]

def load_etf_data_from_csv(file_path: str) -> pd.DataFrame:
    """
    주어진 파일 경로에서 ETF 데이터를 로드하고 DataFrame으로 반환합니다.
    """
    try:
        df = pd.read_csv(file_path)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)  # 'Date'를 인덱스로 설정
        return df
    except Exception as e:
        print(f"[ERROR] Failed to load: {e}")
        return pd.DataFrame()  # 파일을 로드할 수 없을 경우 빈 DataFrame 반환

def get_etf_data(etf_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    ETF 데이터를 Yahoo Finance에서 받아오는 함수
    """
    ticker = yf.Ticker(etf_symbol)
    df = ticker.history(start=start_date, end=end_date)
    return df

def download_all_etfs_and_save():
    """
    모든 ETF 데이터를 다운로드하여 하나의 파일에 저장
    """
    # 'data' 폴더 생성
    os.makedirs('data', exist_ok=True)

    start_date = '2023-01-01'
    end_date = datetime.now().strftime('%Y-%m-%d')

    etf_frames = []  # 모든 ETF 데이터를 담을 리스트

    print(f"[INFO] Running combined ETF download...")

    for symbol in country_etf_list:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)

            if not df.empty:
                # 'Close' 가격만 추출하고 타임존 제거
                close_data = df['Close'].rename(symbol)
                close_data.index = close_data.index.tz_localize(None)  # 타임존 제거
                etf_frames.append(close_data)  # 리스트에 추가
        except Exception as e:
            print(f"[ERROR] Failed {symbol}: {e}")

    # 모든 ETF 데이터가 저장된 리스트를 DataFrame으로 병합
    if etf_frames:
        combined_df = pd.concat(etf_frames, axis=1)
        combined_df.sort_index(ascending=True, inplace=True)  # 날짜별로 정렬
        combined_df.to_csv('data/country_etf_data_combined.csv')
        print("[SUCCESS] Integrated CSV created at data/country_etf_data_combined.csv")
    else:
        print("[ERROR] No data to save")

# 파일이 직접 실행될 때만 호출
if __name__ == "__main__":
    download_all_etfs_and_save()
