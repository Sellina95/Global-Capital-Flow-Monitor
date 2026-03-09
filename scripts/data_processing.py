import yfinance as yf
import pandas as pd


def load_etf_data_from_csv(file_path: str) -> pd.DataFrame:
    """
    주어진 파일 경로에서 ETF 데이터를 로드하고 DataFrame으로 반환합니다.
    """
    try:
        df = pd.read_csv(file_path)
        print(f"[INFO] Data for {file_path.split('/')[-1]}: {df.head()}")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to load ETF data from {file_path}: {e}")
        return pd.DataFrame()  # 파일을 로드할 수 없을 경우 빈 DataFrame 반환

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

def calculate_pct_change(df: pd.DataFrame) -> pd.Series:
    """
    주어진 데이터프레임에 대해 % 변화율을 계산하는 함수
    단일 열을 반환하도록 수정
    """
    pct_change = df['Close'].pct_change() * 100  # 'Close' 열 기준으로 계산
    return pct_change

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
