import os
import pandas as pd

# 1. 포트폴리오 가중치 설정
weights = {
    "BND": 0.15, "EEM": 0.10, "EIS": 0.05, "EMB": 0.10, "EWJ": 0.05,
    "FXI": 0.10, "GLD": 0.05, "SPY": 0.10, "VXX": 0.05, "XLK": 0.05,
    "XLV": 0.05, "XLP": 0.05, "XLF": 0.05, "QUAL": 0.05, "COWZ": 0.05, "MTUM": 0.05
}

def calculate_returns():
    """각 ETF 개별 파일을 읽어 일일 수익률을 계산합니다."""
    all_returns = []
    data_directory = 'data/' 
    symbols = list(weights.keys())

    for symbol in symbols:
        file_path = os.path.join(data_directory, f"{symbol}_data.csv")
        
        if os.path.exists(file_path):
            try:
                # 데이터 로드 (헤더 스킵 로직)
                df = pd.read_csv(file_path, skiprows=3, header=None)
                df = df.iloc[:, [0, 1]] 
                df.columns = ['Date', 'Price']
                
                # 전처리
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
                df = df.dropna().set_index('Date').sort_index()
                
                # 수익률 계산
                returns = df['Price'].pct_change()
                returns.name = symbol 
                
                all_returns.append(returns)
                print(f"✅ {symbol}: 계산 성공")
                
            except Exception as e:
                print(f"❌ {symbol} 처리 중 에러: {e}")
        else:
            print(f"⚠️ 파일 없음: {file_path}")

    if all_returns:
        return pd.concat(all_returns, axis=1)
    return None

if __name__ == "__main__":
    # 단계 1: 각 ETF 수익률 합치기 (헤더에 ETF 이름들이 들어갑니다)
    combined_df = calculate_returns()
    
    if combined_df is not None:
        # 단계 2: 내 포트폴리오 가중치 수익률 계산
        weight_series = pd.Series(weights)
        # 각 행별로 가중치를 곱해서 합산한 '내 성적' 컬럼 추가
        combined_df['Portfolio_Return'] = combined_df[weight_series.index].dot(weight_series)
        
        # 단계 3: 결과 저장 (이제 헤더에 ETF 이름들과 Portfolio_Return이 모두 포함됩니다!)
        output_path = "data/etf_daily_returns_combined.csv"
        combined_df.to_csv(output_path)
        
        print("-" * 30)
        print(f"🚀 [완벽 통합] ETF별 수익률과 포트폴리오 결과가 모두 저장되었습니다: {output_path}")
        print(combined_df.tail()) # 마지막 5일치 데이터 확인
    else:
        print("❌ 통합할 데이터가 없습니다.")
