import os
import pandas as pd
import yfinance as yf
from datetime import datetime

# ===== 1. 경로 설정 =====
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "macro_data.csv")

os.makedirs(DATA_DIR, exist_ok=True)

# ===== 2. 데이터 가져오기 =====

INDICATORS = {
    "US10Y": "^TNX",      # 미국 10년물
    "DXY": "DX-Y.NYB",    # 달러 인덱스
    "WTI": "CL=F",        # 유가
    "VIX": "^VIX",        # 변동성
    "USDKRW": "KRW=X",    # 원/달러
}

def fetch_macro_data():
    results = {}
    for name, ticker in INDICATORS.items():
        print(f"Fetching {name} ({ticker}) ...")
        df = yf.download(ticker, period="2d")

        # NaN 제거 후 마지막 종가만 float로 뽑기
        last_close = df["Close"].dropna().iloc[-1]
        value = float(last_close)
        results[name] = value
        print(f"  → {name}: {value}")
    return results

# ===== 3. CSV에 한 줄 추가 =====

def append_to_csv(values: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {"datetime": now}
    row.update(values)

    df_row = pd.DataFrame([row])

    file_exists = os.path.isfile(CSV_PATH)
    df_row.to_csv(CSV_PATH, mode="a", index=False, header=not file_exists)

    print(f"\n✅ Saved row to {CSV_PATH}")
    print(df_row)

# ===== 4. 실행부 =====

if __name__ == "__main__":
    vals = fetch_macro_data()
    append_to_csv(vals)


