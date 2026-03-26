import os
import pandas as pd

etf_symbols = {
    "BND": "Vanguard Total Bond Market", "EEM": "iShares MSCI Emerging Markets",
    "EIS": "iShares MSCI Israel", "EMB": "iShares J.P. Morgan USD EM Bond",
    "EWJ": "iShares MSCI Japan", "FXI": "iShares China Large-Cap",
    "GLD": "SPDR Gold Shares", "SPY": "SPDR S&P 500 ETF Trust",
    "VXX": "iPath S&P 500 VIX Short-Term", "XLK": "Technology Select Sector",
    "XLV": "Health Care Select Sector", "XLP": "Consumer Staples Select Sector",
    "XLF": "Financials Select Sector", "QUAL": "iShares MSCI USA Quality",
    "COWZ": "Pacer US Cash Cows 100", "MTUM": "iShares MSCI USA Momentum"
}

def calculate_returns():
    all_returns = []
    data_directory = 'data/' 

    for symbol in etf_symbols:
        file_path = os.path.join(data_directory, f"{symbol}_data.csv")
        
        if os.path.exists(file_path):
            try:
                # 1. 데이터 로드: 상단 2줄(Price..., Ticker..., Date...)을 건너뜁니다.
                # 세연 님의 파일 예시를 보면 3번째 줄부터 실제 날짜 데이터가 나오므로 skiprows=2 혹은 3을 시도해야 합니다.
                # 여기서는 'Date'라는 글자가 있는 줄까지 건너뛰고 읽어오겠습니다.
                df = pd.read_csv(file_path, skiprows=2) 
                
                # 컬럼명 정리 (공백 제거)
                df.columns = df.columns.str.strip()
                
                # 'Unnamed'로 시작하는 불필요한 컬럼이 생길 수 있어 정리
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

                # 첫 번째 컬럼 이름을 강제로 'Date'로 변경 (만약 이름이 비어있을 경우 대비)
                if df.columns[0] != 'Date':
                    df.rename(columns={df.columns[0]: 'Date'}, inplace=True)

                if 'Date' in df.columns and 'Close' in df.columns:
                    # 날짜 형식이 아닌 행(에러 방지) 제거 후 변환
                    df = df[df['Date'].str.contains(r'\d{4}-\d{2}-\d{2}', na=False)]
                    df['Date'] = pd.to_datetime(df['Date'])
                    df = df.set_index('Date')
                    
                    # 'Close' 컬럼을 숫자형으로 변환 (문자열 섞임 방지)
                    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
                    
                    # 수익률 계산
                    returns = df['Close'].pct_change()
                    returns.name = symbol 
                    
                    all_returns.append(returns)
                    print(f"✅ {symbol}: 계산 성공 (데이터 {len(df)}건)")
                else:
                    print(f"⚠️ {symbol}: 필수 컬럼(Date, Close)을 찾을 수 없습니다. 현재 컬럼: {df.columns.tolist()}")
            except Exception as e:
                print(f"❌ {symbol} 처리 중 에러 발생: {e}")
        else:
            print(f"⚠️ 파일 없음: {file_path}")

    if all_returns:
        combined_df = pd.concat(all_returns, axis=1)
        # 날짜순 정렬
        combined_df = combined_df.sort_index()
        return combined_df
    else:
        return None

if __name__ == "__main__":
    final_returns_df = calculate_returns()
    
    if final_returns_df is not None:
        output_path = "data/etf_daily_returns_combined.csv"
        final_returns_df.to_csv(output_path)
        print("-" * 30)
        print(f"🚀 통합 완료! 저장 경로: {output_path}")
        print(final_returns_df.tail()) # 최근 데이터 확인
    else:
        print("데이터 통합 실패.")
