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
        # 'Date'를 컬럼으로 변환 (인덱스에서 제외)
        df['Date'] = pd.to_datetime(df['Date'])
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

    # 'Date' 열을 인덱스에서 컬럼으로 변경
    df['Date'] = df.index
    df = df[['Date', 'Close']]  # 'Close'와 'Date'만 사용

    return df

def save_etf_data_to_csv(etf_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    ETF 데이터를 받아와서 CSV 파일로 저장하는 함수
    """
    # ETF 데이터 가져오기
    df = get_etf_data(etf_symbol, start_date, end_date)
    
    # 데이터가 없다면 종료
    if df.empty:
        print(f"[ERROR] No data for {etf_symbol}")
        return pd.DataFrame()

    return df


def download_all_etfs_and_save():
    start_date = '2023-01-01'
    end_date = '2023-12-31'

    all_etf_data = pd.DataFrame()  # 빈 DataFrame 생성

    for etf_symbol in country_etf_list:
        # ETF 데이터 저장
        df = save_etf_data_to_csv(etf_symbol, start_date, end_date)

        if not df.empty:
            df = df.rename(columns={'Close': etf_symbol})  # 'Close' 값을 ETF 심볼로 이름 변경
            if all_etf_data.empty:
                all_etf_data = df  # 첫 번째 데이터프레임
            else:
                all_etf_data = pd.merge(all_etf_data, df, on='Date', how='outer')  # 'Date' 기준으로 병합

    # 전체 데이터를 하나의 CSV 파일로 저장 (파일 이름: country_etf_data_combined.csv)
    all_etf_data.to_csv('data/country_etf_data_combined.csv', index=False)  # 인덱스는 저장하지 않음
    print("[INFO] All ETF data combined and saved to data/country_etf_data_combined.csv")

# 예시로 모든 ETF 데이터 다운로드
download_all_etfs_and_save()
