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
    "US10Y": "^TNX",      # 미국 10년물 (주의: 경우에 따라 42.95 형태로 올 수 있음)
    "DXY": "DX-Y.NYB",    # 달러 인덱스
    "WTI": "CL=F",        # 유가
    "VIX": "^VIX",        # 변동성
    "USDKRW": "KRW=X",    # 원/달러
    "HYG": "HYG",         # High Yield bond ETF (가격)
    "LQD": "LQD",         # Investment Grade bond ETF (가격)
}

def fetch_macro_data():
    results = {}
    for name, ticker in INDICATORS.items():
        print(f"Fetching {name} ({ticker}) ...")
        df = yf.download(ticker, period="2d", progress=False)

        if df.empty or "Close" not in df.columns:
            raise ValueError(f"No data returned for {name} ({ticker})")

        last_close = df["Close"].dropna().iloc[-1]
        value = float(last_close)

        # ✅ US10Y 보정: ^TNX가 42.95처럼 오면 4.295로 변환
        if name == "US10Y" and value > 20:
            value = value / 10.0

        results[name] = value
        print(f"  → {name}: {value}")
    return results

def safe_append_row(row: dict):
    """
    CSV 컬럼이 늘어날 때(예: HYG/LQD 추가) CSV가 깨지지 않도록:
    - 기존 파일이 있으면 읽어서 컬럼 union
    - 새 row를 append
    - 전체를 다시 저장(헤더 포함)
    """
    new_df = pd.DataFrame([row])

    if not os.path.isfile(CSV_PATH) or os.path.getsize(CSV_PATH) == 0:
        new_df.to_csv(CSV_PATH, index=False)
        print(f"\n✅ Created {CSV_PATH}")
        print(new_df)
        return

    old_df = pd.read_csv(CSV_PATH)

    # 컬럼 union
    for c in new_df.columns:
        if c not in old_df.columns:
            old_df[c] = pd.NA
    for c in old_df.columns:
        if c not in new_df.columns:
            new_df[c] = pd.NA

    # 컬럼 순서: 기존 순서 유지 + 새 컬럼은 뒤로
    new_df = new_df[old_df.columns]

    combined = pd.concat([old_df, new_df], ignore_index=True)

    # datetime 정리
    if "datetime" in combined.columns:
        combined["datetime"] = pd.to_datetime(combined["datetime"], errors="coerce")
        combined = combined.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)
        combined["datetime"] = combined["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")

    combined.to_csv(CSV_PATH, index=False)
    print(f"\n✅ Updated {CSV_PATH} (rows={len(combined)})")
    print(new_df)

if __name__ == "__main__":
    vals = fetch_macro_data()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {"datetime": now, **vals}
    safe_append_row(row)
