import pandas as pd
from datetime import datetime

# 날짜 범위 설정
START_DATE = "2022-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

# FRED CSV 다운로드 URL
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

# 통합 FRED 시리즈
FRED_SERIES = {
    "FCI": "NFCI",         # Chicago Fed National Financial Conditions Index
    "REAL_RATE": "DFII10", # 기존 2번 필터 호환용
    "T10Y2Y": "T10Y2Y",    # 10Y - 2Y Yield Curve Spread
    "T10YIE": "T10YIE",    # 10Y Breakeven Inflation Rate
    "VIX": "VIXCLS",       # VIX
    "DFII10": "DFII10",    # 10Y Real Interest Rate
    "DGS2": "DGS2",        # 2Y Treasury Rate
    
}

def download_fred_csv_series(series_code: str) -> pd.DataFrame:
    url = FRED_CSV + series_code
    df = pd.read_csv(url)

    df.columns = ["date", series_code]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df[series_code] = pd.to_numeric(df[series_code], errors="coerce")

    return df

# 날짜 인덱스 생성
full_index = pd.date_range(start=START_DATE, end=END_DATE, freq="D")

# 최종 데이터프레임
out_df = pd.DataFrame(index=full_index)

# 각 FRED 시리즈 다운로드 후 병합
for col, fred_code in FRED_SERIES.items():
    try:
        df = download_fred_csv_series(fred_code)
        df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]
        df = df.set_index("date")

        # 원본 관측값
        series = df[fred_code].reindex(full_index)
        out_df[col] = series

        # 실제 관측일 보존
        obs_col = f"{col}_OBS_DATE"
        obs_dates = pd.Series(pd.NaT, index=full_index, dtype="datetime64[ns]")
        valid_mask = series.notna()
        obs_dates.loc[valid_mask] = obs_dates.index[valid_mask]
        out_df[obs_col] = obs_dates

        print(f"[OK] FRED - {col}")

    except Exception as e:
        out_df[col] = pd.NA
        out_df[f"{col}_OBS_DATE"] = pd.NaT
        print(f"[ERROR] FRED - {col}: {e}")

# 기존 Production 값 유지:
# 값과 실제 관측일을 함께 forward fill
out_df = out_df.ffill()

# date 컬럼 복원
out_df = out_df.reset_index().rename(columns={"index": "date"})
out_df["date"] = out_df["date"].dt.strftime("%Y-%m-%d")

# 관측일 컬럼은 YYYY-MM-DD 형태로 저장
for col in FRED_SERIES:
    obs_col = f"{col}_OBS_DATE"
    out_df[obs_col] = pd.to_datetime(
        out_df[obs_col], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

# 저장
out_df.to_csv("data/fred_macro_sctorallo.csv", index=False, encoding="utf-8-sig")
print("Saved: data/fred_macro_sctorallo.csv")
print(out_df.tail(10).to_string(index=False))
