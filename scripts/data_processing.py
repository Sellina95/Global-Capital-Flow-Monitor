import yfinance as yf
import pandas as pd

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
        df['Date'] = pd.to_datetime(df['Date'])  # Ensure Date is parsed as datetime
        print(f"[INFO] Data for {file_path.split('/')[-1]}: {df.head()}")
        return df
    except Exception as e:
        print(f"[ERROR] Failed to load ETF data from {file_path}: {e}")
        return pd.DataFrame()  # 파일을 로드할 수 없을 경우 빈 DataFrame 반환

def get_etf_data(etf_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    ETF 데이터를 Yahoo Finance에서 받아오는 함수
    """
    etf = yf.Ticker(etf_symbol)
    df = etf.history(start=start_date, end=end_date)

    # Ensure Date is a column
    df.reset_index(inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])  # Ensure Date is parsed as datetime

    if df.empty:
        print(f"[ERROR] No data for {etf_symbol} between {start_date} and {end_date}")
    else:
        print(f"[INFO] Data for {etf_symbol}: {df.head()}")
    
    return df

def save_etf_data_to_combined_csv(etf_symbol: str, start_date: str, end_date: str, all_etf_data: pd.DataFrame) -> pd.DataFrame:
    """
    ETF 데이터를 가져오고 combined CSV 파일에 저장
    """
    df = get_etf_data(etf_symbol, start_date, end_date)

    if df.empty:
        print(f"[ERROR] No data found for {etf_symbol}")
        return all_etf_data

    # Date를 컬럼으로 설정하고 병합
    df = df[['Date', 'Close']]
    df.set_index('Date', inplace=True)  # 'Date'를 인덱스로 설정

    # 병합: 기존 데이터와 병합
    if all_etf_data.empty:
        all_etf_data = df
    else:
        # 'suffixes'를 사용하여 중복된 컬럼에 접미사 추가
        all_etf_data = all_etf_data.merge(df, on='Date', how='outer', suffixes=('', f'_{etf_symbol}'))

    return all_etf_data

def download_all_etfs_and_save():
    """
    모든 ETF 데이터 다운로드 후 하나의 파일에 저장
    """
    start_date = '2023-01-01'
    end_date = '2023-12-31'

    all_etf_data = pd.DataFrame()  # 빈 DataFrame 생성

    for etf_symbol in country_etf_list:
        all_etf_data = save_etf_data_to_combined_csv(etf_symbol, start_date, end_date, all_etf_data)

    # 전체 데이터를 하나의 CSV 파일로 저장
    all_etf_data.to_csv('data/country_etf_data_combined.csv', index=True)
    print("[INFO] All ETF data combined and saved to data/country_etf_data_combined.csv")

# 실행
download_all_etfs_and_save()
