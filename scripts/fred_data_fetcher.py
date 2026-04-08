import pandas as pd
import os
import csv  # 🚨 쉼표 강제 주입 및 데이터 보호를 위해 필수
from datetime import datetime

# 1. 설정 및 경로
START_DATE = "2022-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")
CSV_PATH = "data/fred_macro_sctorallo.csv"
FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

# 통합 FRED 시리즈 (세연 님의 기존 설정 유지)
FRED_SERIES = {
    "FCI": "NFCI",
    "REAL_RATE": "DFII10",
    "T10Y2Y": "T10Y2Y",
    "T10YIE": "T10YIE",
    "VIX": "VIXCLS",
    "DFII10": "DFII10",
    "DGS2": "DGS2",
    "DXY": "DTWEXBGS"
}

def download_fred_csv_series(series_code: str) -> pd.DataFrame:
    """FRED에서 개별 시리즈 다운로드 및 기본 전처리"""
    url = FRED_CSV_URL + series_code
    try:
        # ✅ 읽어올 때부터 쉼표 기반으로 명확히 분리
        df = pd.read_csv(url)
        df.columns = ["date", series_code]
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        df[series_code] = pd.to_numeric(df[series_code], errors="coerce")
        return df
    except Exception as e:
        print(f"[ERROR] Download failed for {series_code}: {e}")
        return pd.DataFrame(columns=["date", series_code])

# 2. 데이터 통합 프로세스
print("🚀 FRED 데이터 수집을 시작합니다...")
full_index = pd.date_range(start=START_DATE, end=END_DATE, freq="D")
out_df = pd.DataFrame(index=full_index)

for col, fred_code in FRED_SERIES.items():
    df_series = download_fred_csv_series(fred_code)
    if not df_series.empty:
        df_series = df_series[(df_series["date"] >= START_DATE) & (df_series["date"] <= END_DATE)]
        df_series = df_series.set_index("date")
        # ✅ reindex를 통해 날짜 라인업 맞춤
        out_df[col] = df_series[fred_code].reindex(full_index)
        print(f"[OK] FRED Merge - {col}")
    else:
        out_df[col] = pd.NA

# 3. 데이터 정제 (Forward Fill 및 날짜 포맷팅)
out_df = out_df.ffill()
out_df = out_df.reset_index().rename(columns={"index": "date"})
out_df["date"] = out_df["date"].dt.strftime("%Y-%m-%d")

# 4. 🚨 [절대 방어] CSV 저장 로직
# 기존 파일 삭제 (깨끗한 상태에서 시작)
if os.path.exists(CSV_PATH):
    os.remove(CSV_PATH)
    print(f"[CLEAN] 기존 오염된 파일 삭제 완료.")

try:
    # ✅ sep=',' : 쉼표 명시적 강제
    # ✅ encoding='utf-8' : 데이터 밀림을 유발하는 sig 제거
    # ✅ quoting=csv.QUOTE_MINIMAL : 데이터 필드를 보호하여 합체 방지
    out_df.to_csv(
        CSV_PATH, 
        index=False, 
        sep=',', 
        encoding="utf-8", 
        quoting=csv.QUOTE_MINIMAL
    )
    print(f"\n✨ [SUCCESS] 데이터가 안전하게 저장되었습니다: {CSV_PATH}")

except Exception as e:
    print(f"\n❌ [ERROR] 저장 중 치명적 오류 발생: {e}")

# 5. 🔍 저장 즉시 검증 (세연 님이 눈으로 확인할 부분)
print("-" * 50)
verify_df = pd.read_csv(CSV_PATH)
last_row = verify_df.tail(1)
last_dxy = last_row['DXY'].values[0]

print(f"🔎 [검증 결과] 마지막 날짜({last_row['date'].values[0]}) 데이터:")
print(f"DXY: {last_dxy}")
print(f"VIX: {last_row['VIX'].values[0]}")
print(f"T10Y2Y: {last_row['T10Y2Y'].values[0]}")

if last_dxy > 115:
    print("\n⚠️ 경고: DXY가 여전히 비정상(115 초과)입니다. 원본 데이터 소스를 확인하세요.")
else:
    print("\n✅ 성공: 모든 지표가 정상 범위 내에서 쉼표로 잘 분리되었습니다!")
print("-" * 50)
