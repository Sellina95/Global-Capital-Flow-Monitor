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
        df['Date'] = pd.to_datetime(df['Date'])  # Date 컬럼을 날짜 형식으로 변환
        df.set_index('Date', inplace=True)  # Date를 인덱스로 설정
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

def save_etf_data_to_csv(etf_symbol: str, start_date: str, end_date: str, output_file: str) -> None:
    """
    ETF 데이터를 받아와서 CSV 파일로 저장하는 함수
    """
    # ETF 데이터 가져오기
    df = get_etf_data(etf_symbol, start_date, end_date)
    
    if df.empty:
        print(f"[ERROR] No data for {etf_symbol}")
        return
    
    # Date를 열로 변환
    df['Date'] = df.index
    
    # 필요한 열만 추출 (Date와 Close)
    df = df[['Date', 'Close']]
    
    # CSV 파일로 저장, 인덱스를 포함하지 않도록 index=False 설정
    df.to_csv(output_file, index=False)  # index=False로 인덱스 저장 방지
    print(f"[INFO] {etf_symbol} data saved to {output_file}")

# 전체 국가 ETF 리스트를 순회하며 데이터 가져오기 및 저장하기
def download_all_etfs_and_save():
    start_date = '2023-01-01'
    end_date = '2023-12-31'

    all_etf_data = pd.DataFrame()  # 빈 DataFrame 생성

    for etf_symbol in country_etf_list:
        output_file = f'data/{etf_symbol}_etf_data.csv'  # 파일명을 ETF 심볼로 설정
        save_etf_data_to_csv(etf_symbol, start_date, end_date, output_file)

        # 로드한 데이터 병합
        df = load_etf_data_from_csv(output_file)
        if not df.empty:
            all_etf_data = pd.concat([all_etf_data, df], axis=1)  # 'Date' 기준으로 병합할 예정

    # 전체 데이터를 하나의 CSV 파일로 저장
    all_etf_data.to_csv('data/country_etf_data_combined.csv', index=True)  # 인덱스 포함해서 저장
    print("[INFO] All ETF data combined and saved to data/country_etf_data_combined.csv")

# 예시로 모든 ETF 데이터 다운로드
download_all_etfs_and_save()
