import pandas as pd
from datetime import datetime

# 날짜 범위 설정
START_DATE = "2022-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

# FRED CSV 다운로드 URL
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

# FRED 시리즈 코드들
FRED_SERIES = {
    "T10Y2Y": "T10Y2Y",   # 10Y - 2Y Yield Curve Spread
    "T10YIE": "T10YIE",   # 10Y Breakeven Inflation Rate
    "VIX": "VIXCLS"       # VIX (Volatility Index)
}

def download_fred_csv_series(series_code: str) -> pd.DataFrame:
    url = FRED_CSV + series_code
    df = pd.read_csv(url)

    df.columns = ["date", series_code]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df[series_code] = pd.to_numeric(df[series_code], errors="coerce")

    return df

# 날짜 인덱스 생성 (2022-01-01 ~ 오늘)
full_index = pd.date_range(start=START_DATE, end=END_DATE, freq="D")

# 최종 데이터프레임
out_df = pd.DataFrame(index=full_index)

# 각 FRED 시리즈 다운로드 후 병합
for col, fred_code in FRED_SERIES.items():
    try:
        df = download_fred_csv_series(fred_code)
        df = df[(df["date"] >= START_DATE) & (df["date"] <= END_DATE)]
        df = df.set_index("date")
        out_df[col] = df[fred_code].reindex(full_index)
        print(f"[OK] FRED - {col}")
    except Exception as e:
        out_df[col] = pd.NA
        print(f"[ERROR] FRED - {col}: {e}")

# 🔥 핵심: 최신 유효값으로 forward fill
out_df = out_df.ffill()

# date 컬럼 복원
out_df = out_df.reset_index().rename(columns={"index": "date"})
out_df["date"] = out_df["date"].dt.strftime("%Y-%m-%d")

# CSV 저장
out_df.to_csv("data/fred_macro_sctorallo.csv", index=False, encoding="utf-8-sig")
print("Saved: data/fred_macro_sctorallo.csv")
print(out_df.tail(10).to_string(index=False))