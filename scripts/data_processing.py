import yfinance as yf
import pandas as pd
import os
from datetime import datetime

# 1. 국가별 ETF 목록
country_etf_list = ["EIS", "SPY", "EEM", "EMB", "GLD", "VXX", "FXI", "EWJ", "BND"]

def download_all_etfs_and_save():
    # 데이터 저장 폴더 생성 (없을 경우)
    os.makedirs('data', exist_ok=True)

    # 2026년 현재 시점에 맞춰 날짜 설정 (필요에 따라 수정하세요)
    start_date = '2023-01-01'
    end_date = datetime.now().strftime('%Y-%m-%d')

    # 모든 ETF 데이터를 담을 리스트
    etf_frames = []

    print(f"[INFO] Fetching data from {start_date} to {end_date}...")

    for symbol in country_etf_list:
        try:
            # Yahoo Finance에서 데이터 가져오기
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)

            if df.empty:
                print(f"[WARNING] No data found for {symbol}")
                continue

            # 'Close' 가격만 추출하고 컬럼명을 해당 티커(symbol)로 변경
            # timezone 정보가 있으면 제거하여 병합 시 오류 방지
            close_data = df['Close'].rename(symbol)
            close_data.index = close_data.index.tz_localize(None) 
            
            etf_frames.append(close_data)
            print(f"[SUCCESS] Downloaded {symbol}")

        except Exception as e:
            print(f"[ERROR] Failed to download {symbol}: {e}")

    # 모든 Series를 'Date' 기준으로 옆으로 병합 (axis=1)
    if etf_frames:
        combined_df = pd.concat(etf_frames, axis=1)
        
        # 날짜 내림차순 정렬 (최신 데이터가 위로 오게 하려면 False, 과거가 위면 True)
        combined_df.sort_index(ascending=True, inplace=True)

        # 3. 최종 통합 파일 하나만 저장
        output_path = 'data/country_etf_data_combined.csv'
        combined_df.to_csv(output_path)
        
        print("-" * 30)
        print(f"[FINISH] Combined data saved to: {output_path}")
        print(combined_df.tail()) # 마지막 5행 출력해서 확인
    else:
        print("[ERROR] No data was collected. Check your internet or symbols.")

if __name__ == "__main__":
    download_all_etfs_and_save()
