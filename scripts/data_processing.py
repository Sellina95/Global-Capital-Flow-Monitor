import yfinance as yf
import pandas as pd
import os
from datetime import datetime

# 국가별 ETF 목록
country_etf_list = ["EIS", "SPY", "EEM", "EMB", "GLD", "VXX", "FXI", "EWJ", "BND"]

# --- [1] 기존 파일들과의 호환성을 위한 함수들 (Restore) ---

def load_etf_data_from_csv(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
        return df
    except Exception as e:
        print(f"[ERROR] Failed to load: {e}")
        return pd.DataFrame()

def get_etf_data(etf_symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    ticker = yf.Ticker(etf_symbol)
    df = ticker.history(start=start_date, end=end_date)
    return df

def save_etf_data_to_csv(etf_symbol: str, start_date: str, end_date: str, output_file: str) -> None:
    df = get_etf_data(etf_symbol, start_date, end_date)
    if not df.empty:
        df.to_csv(output_file)
        print(f"[INFO] {etf_symbol} saved to {output_file}")

# --- [2] 우리가 새로 만든 효율적인 통합 함수 ---

def download_all_etfs_and_save():
    os.makedirs('data', exist_ok=True)
    start_date = '2023-01-01'
    end_date = datetime.now().strftime('%Y-%m-%d')
    etf_frames = []

    print(f"[INFO] Running combined ETF download...")

    for symbol in country_etf_list:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            if not df.empty:
                # 'Close' 가격만 추출하고 타임존 제거
                close_data = df['Close'].rename(symbol)
                close_data.index = close_data.index.tz_localize(None)
                etf_frames.append(close_data)
        except Exception as e:
            print(f"[ERROR] Failed {symbol}: {e}")

    if etf_frames:
        combined_df = pd.concat(etf_frames, axis=1)
        combined_df.sort_index(ascending=True, inplace=True)
        combined_df.to_csv('data/country_etf_data_combined.csv')
        print("[SUCCESS] Integrated CSV created at data/country_etf_data_combined.csv")

# 파일이 직접 실행될 때만 통합 함수 호출
if __name__ == "__main__":
    download_all_etfs_and_save()
