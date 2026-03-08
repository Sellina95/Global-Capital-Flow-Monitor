import yfinance as yf
import pandas as pd

def get_etf_data(etf_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    주어진 ETF 심볼에 대한 데이터를 Yahoo Finance에서 가져와서 반환하는 함수
    - ETF 심볼 (예: "EIS")
    - 시작 날짜 (예: "2023-01-01")
    - 종료 날짜 (예: "2023-12-31")
    """
    # Yahoo Finance에서 ETF 데이터 가져오기
    etf = yf.Ticker(etf_symbol)
    df = etf.history(start=start_date, end=end_date)
    
    # 필요한 열만 선택하여 반환 (예: 'Date'와 'Close')
    df = df[['Close']]
    print(f"[INFO] Data for {etf_symbol}: {df.head()}")
    return df


def calculate_pct_change(df: pd.DataFrame) -> pd.Series:
    """
    DataFrame에서 % 변화 (pct_change)를 계산하고 반환하는 함수
    """
    return df.pct_change() * 100.0


def calculate_cumulative_return(df: pd.DataFrame, days: int) -> pd.Series:
    """
    DataFrame에서 n일 동안의 누적 변화를 계산하는 함수
    """
    return (df['Close'].pct_change().add(1).rolling(window=days).apply(lambda x: x.prod(), raw=True) - 1) * 100


def save_etf_data_to_csv(etf_symbol: str, start_date: str, end_date: str, output_file: str) -> None:
    """
    ETF 데이터를 받아와서 CSV 파일로 저장하는 함수
    """
    # ETF 데이터 가져오기
    df = get_etf_data(etf_symbol, start_date, end_date)
    
    # pct 변화 및 누적 변화 계산
    df['Pct Change'] = calculate_pct_change(df)
    df['5D Cum Return'] = calculate_cumulative_return(df, 5)
    
    # CSV 파일로 저장
    df.to_csv(output_file, index=True)
    print(f"[INFO] {etf_symbol} data saved to {output_file}")
    

# 예시: 이스라엘 ETF (EIS) 데이터 저장
save_etf_data_to_csv('EIS', '2023-01-01', '2023-12-31', 'data/country_etf_data.csv')
