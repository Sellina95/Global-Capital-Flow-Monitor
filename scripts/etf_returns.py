import os
import pandas as pd

def calculate_returns():
    all_returns = []
    data_directory = 'data/' 
    # ETF 심볼 리스트 (위와 동일)
    symbols = ["BND", "EEM", "EIS", "EMB", "EWJ", "FXI", "GLD", "SPY", "VXX", "XLK", "XLV", "XLP", "XLF", "QUAL", "COWZ", "MTUM"]

    for symbol in symbols:
        file_path = os.path.join(data_directory, f"{symbol}_data.csv")
        
        if os.path.exists(file_path):
            try:
                # 1. 일단 3줄 건너뛰고 읽어오기 (Date 데이터가 시작되는 지점)
                # 만약 에러가 나면 header=None으로 읽어서 강제로 구조를 봅니다.
                df = pd.read_csv(file_path, skiprows=3, header=None)
                
                # 2. 첫 번째 컬럼(날짜)과 두 번째 컬럼(수정 종가 또는 종가)만 추출
                # 예시 데이터 순서: Date(0), Price(1), Close(2)... 인지 확인이 필요하지만
                # 세연 님 데이터 예시 기준: 0번은 날짜, 1번은 Price(수정종가) 입니다.
                df = df.iloc[:, [0, 1]] 
                df.columns = ['Date', 'Price']
                
                # 3. 데이터 전처리
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
                df = df.dropna() # 날짜나 가격이 이상한 행 제거
                df = df.set_index('Date').sort_index()
                
                # 4. 수익률 계산
                returns = df['Price'].pct_change()
                returns.name = symbol 
                
                all_returns.append(returns)
                print(f"✅ {symbol}: 데이터 로드 및 수익률 계산 성공")
                
            except Exception as e:
                print(f"❌ {symbol} 처리 중 치명적 에러: {e}")
        else:
            print(f"⚠️ 파일 없음: {file_path}")

    if all_returns:
        combined_df = pd.concat(all_returns, axis=1)
        return combined_df
    return None

if __name__ == "__main__":
    final_returns_df = calculate_returns()
    if final_returns_df is not None:
        final_returns_df.to_csv("data/etf_daily_returns_combined.csv")
        print("🚀 모든 ETF 수익률 통합 완료!")
        print(final_returns_df.tail())
    else:
        print("❌ 통합할 데이터가 없습니다.")
