import os
import pandas as pd

# 1. 포트폴리오 가중치 설정 (세연 님의 레시피)
weights = {
    "BND": 0.15, "EEM": 0.10, "EIS": 0.05, "EMB": 0.10, "EWJ": 0.05,
    "FXI": 0.10, "GLD": 0.05, "SPY": 0.10, "VXX": 0.05, "XLK": 0.05,
    "XLV": 0.05, "XLP": 0.05, "XLF": 0.05, "QUAL": 0.05, "COWZ": 0.05, "MTUM": 0.05
}

def calculate_returns():
    """각 ETF 개별 파일을 읽어 일일 수익률을 계산하고 하나의 DataFrame으로 합칩니다."""
    all_returns = []
    data_directory = 'data/' 
    symbols = list(weights.keys()) # 가중치에 있는 심볼들만 처리

    for symbol in symbols:
        file_path = os.path.join(data_directory, f"{symbol}_data.csv")
        
        if os.path.exists(file_path):
            try:
                # [데이터 로드] 상단 3줄 건너뛰고 날짜(0), 가격(1)만 추출
                df = pd.read_csv(file_path, skiprows=3, header=None)
                df = df.iloc[:, [0, 1]] 
                df.columns = ['Date', 'Price']
                
                # [전처리] 날짜 및 숫자 변환
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
                df = df.dropna().set_index('Date').sort_index()
                
                # [수익률 계산]
                returns = df['Price'].pct_change()
                returns.name = symbol 
                
                all_returns.append(returns)
                print(f"✅ {symbol}: 수익률 계산 성공")
                
            except Exception as e:
                print(f"❌ {symbol} 처리 중 에러: {e}")
        else:
            print(f"⚠️ 파일 없음: {file_path}")

    if all_returns:
        # 모든 ETF 수익률을 날짜 기준으로 옆으로 합칩니다.
        combined_df = pd.concat(all_returns, axis=1)
        return combined_df
    return None

if __name__ == "__main__":
    # 단계 1: 개별 ETF 수익률 계산 및 통합
    final_returns_df = calculate_returns()
    
    if final_returns_df is not None:
        # 단계 2: 가중치(Weights) 적용하여 포트폴리오 최종 수익률 계산
        # (각 날짜별 수익률 * 가중치)를 모두 더해 'Portfolio_Return' 컬럼 생성
        portfolio_df = pd.DataFrame(index=final_returns_df.index)
        
        # 가중치 시리즈와 수익률 데이터프레임을 행렬 곱(dot)하여 한 번에 계산
        weight_series = pd.Series(weights)
        portfolio_df['Portfolio_Return'] = final_returns_df[weight_series.index].dot(weight_series)
        
        # 단계 3: 결과 저장 (세연 님이 원하시는 그 파일명!)
        output_path = "data/etf_daily_returns_combined.csv"
        portfolio_df.to_csv(output_path)
        
        print("-" * 30)
        print(f"🚀 [최종 성공] 포트폴리오 수익률 파일이 생성되었습니다: {output_path}")
        print(portfolio_df.tail()) # 마지막 5일치 성적표 출력
    else:
        print("❌ 통합할 데이터가 없어 작업을 중단합니다.")
