import yfinance as yf
import pandas as pd

# ETF 목록 (대표적인 국가들)
ETF_LIST = [
    "EIS",   # 이스라엘
    "SPY",   # 미국
    "VTI",   # 미국 전체 (Vanguard Total Stock Market ETF)
    "EEM",   # 이머징 마켓 (EM)
    "GLD",   # 금 (Gold ETF)
    "XLF",   # 금융 (Financials)
    "XLE",   # 에너지 (Energy)
    "XLY",   # 소비재 (Consumer Discretionary)
    "IWM",   # 소형주 (Small Cap)
    "VOO",   # S&P 500 ETF
]

# CSV 파일에 데이터를 저장하는 함수
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
    df.to_csv(output_file, mode='a', header=not pd.io.common.file_exists(output_file), index=True)
    print(f"[INFO] {etf_symbol} data saved to {output_file}")

# ETF 데이터를 Yahoo Finance에서 받아오는 함수
def get_etf_data(etf_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    ETF 데이터를 Yahoo Finance에서 받아오는 함수
    """
    # Yahoo Finance에서 ETF 데이터 가져오기
    etf = yf.Ticker(etf_symbol)
    df = etf.history(start=start_date, end=end_date)
    
    # 데이터가 제대로 받아졌는지 확인
    if df.empty:
        print(f"[ERROR] No data for {etf_symbol} between {start_date} and {end_date}")
    else:
        print(f"[INFO] Data for {etf_symbol}: {df.head()}")

    return df

# 주어진 데이터프레임에 대해 % 변화율을 계산하는 함수
def calculate_pct_change(df: pd.DataFrame) -> pd.Series:
    """
    주어진 데이터프레임에 대해 % 변화율을 계산하는 함수
    """
    pct_change = df['Close'].pct_change() * 100  # 'Close' 열 기준으로 계산
    return pct_change

# DataFrame에서 n일 동안의 누적 변화를 계산하는 함수
def calculate_cumulative_return(df: pd.DataFrame, days: int) -> pd.Series:
    """
    DataFrame에서 n일 동안의 누적 변화를 계산하는 함수
    """
    return (df['Close'].pct_change().add(1).rolling(window=days).apply(lambda x: x.prod(), raw=True) - 1) * 100

# ETF 리스트에서 모든 데이터를 다운로드하고 CSV 파일로 저장하는 함수
def download_and_save_etf_data(etf_list: list, start_date: str, end_date: str, output_file: str) -> None:
    """
    여러 국가 ETF 데이터를 다운로드하고 CSV로 저장하는 함수
    """
    for etf in etf_list:
        save_etf_data_to_csv(etf, start_date, end_date, output_file)

# 사용 예시: 2023년 1월 1일부터 2023년 12월 31일까지의 데이터를 다운로드하여 'data/country_etf_data.csv'에 저장
download_and_save_etf_data(ETF_LIST, '2023-01-01', '2023-12-31', 'data/country_etf_data.csv')
