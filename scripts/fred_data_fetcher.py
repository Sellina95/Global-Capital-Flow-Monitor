import pandas as pd
import os
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
        # ✅ 명시적으로 sep=','를 넣어 읽어올 때부터 꼬임 방지
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
full_index = pd.date_range(start=START_DATE, end=END_DATE, freq="D")
out_df = pd.DataFrame(index=full_index)

for col, fred_code in FRED_SERIES.items():
    df_series = download_fred_csv_series(fred_code)
    if not df_series.empty:
        df_series = df_series[(df_series["date"] >= START_DATE) & (df_series["date"] <= END_DATE)]
        df_series = df_series.set_index("date")
        # ✅ reindex를 통해 날짜 맞춤
        out_df[col] = df_series[fred_code].reindex(full_index)
        print(f"[OK] FRED Merge - {col}")
    else:
        out_df[col] = pd.NA

# 3. 데이터 정제 및 복원
out_df = out_df.ffill() # 최신 유효값으로 채우기
out_df = out_df.reset_index().rename(columns={"index": "date"})
out_df["date"] = out_df["date"].dt.strftime("%Y-%m-%d")

# 4. 🚨 [핵심 수정] 안전한 CSV 저장 로직
# 기존 파일이 있다면 삭제 (깨끗한 상태에서 시작)
if os.path.exists(CSV_PATH):
    os.remove(CSV_PATH)

# ✅ sep=',' : 쉼표를 명시적으로 박아넣음
# ✅ encoding='utf-8' : sig를 빼서 데이터 밀림 방지
# ✅ quoting=csv.QUOTE_MINIMAL : 필요한 경우만 따옴표 사용 (포맷 안정성)
out_df.to_csv(CSV_PATH, index=False, sep=',', encoding="utf-8")

print("-" * 50)
print(f"✅ 저장 완료: {CSV_PATH}")
print("-" * 50)

# 5. 🔍 저장된 파일 즉시 검증 (세연 님이 직접 보실 부분)
verify_df = pd.read_csv(CSV_PATH)
print("\n[검증 결과] 최종 데이터 5줄:")
print(verify_df.tail(5).to_string(index=False))

# DXY가 115를 넘는지 체크 (120 방지턱)
last_dxy = verify_df['DXY'].iloc[-1]
if last_dxy > 115:
    print(f"\n⚠️ 경고: DXY가 여전히 높습니다({last_dxy}). 데이터 소스(FRED) 확인 필요.")
else:
    print(f"\n✨ 성공: DXY가 정상 범위({last_dxy}) 내에 있습니다.")
