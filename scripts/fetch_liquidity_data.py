from __future__ import annotations
import time  # time 모듈 추가# scripts/fetch_liquidity_data.py


from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "liquidity_data.csv"

def fetch_fred(series_id: str) -> pd.DataFrame:
    """Fetch a FRED series via CSV download (no API key) and return clean dataframe."""
    url = f"{FRED_CSV}{series_id}"
    df = pd.read_csv(url)
    
    # FRED CSV format: DATE,<SERIESID>
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    df = df.dropna(subset=["date", series_id]).sort_values("date").reset_index(drop=True)
    
    return df




    

def safe_read_existing(csv_path: Path) -> pd.DataFrame:
    """
    Read existing liquidity_data.csv safely.
    - If file doesn't exist -> empty df
    - If file exists but empty/corrupted -> empty df
    """
    if not csv_path.exists():
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    # 파일 크기가 0이면(빈 파일) 바로 빈 DF 반환
    if csv_path.stat().st_size == 0:
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    try:
        df = pd.read_csv(csv_path)
        if df.empty or "date" not in df.columns:
            return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])
        return df
    except Exception:
        # EmptyDataError 포함 모든 파싱 에러 방어
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    tga_df = fetch_fred(SERIES["TGA"])
    rrp_df = fetch_fred(SERIES["RRP"])
    walcl_df = fetch_fred(SERIES["WALCL"])

    # as_of = TGA/RRP 둘 중 더 느린(더 과거) 최신일로 맞춤
    as_of = min(tga_df.iloc[-1]["date"], rrp_df.iloc[-1]["date"])

    def last_value_on_or_before(df: pd.DataFrame, col: str) -> float:
        sub = df[df["date"] <= as_of]
        # FRED 데이터는 거의 항상 존재하지만, 방어적으로 체크
        if sub.empty:
            raise ValueError(f"No data on or before {as_of.date()} for {col}")
        return float(sub.iloc[-1][col])

    tga = last_value_on_or_before(tga_df, SERIES["TGA"])
    rrp = last_value_on_or_before(rrp_df, SERIES["RRP"])
    walcl = last_value_on_or_before(walcl_df, SERIES["WALCL"])

    net_liq = walcl - tga - rrp

    new_row = pd.DataFrame([{
        "date": as_of.strftime("%Y-%m-%d"),
        "TGA": tga,
        "RRP": rrp,
        "WALCL": walcl,
        "NET_LIQ": net_liq,
    }])

    old = safe_read_existing(OUT_CSV)

    # 병합/정리
    combined = pd.concat([old, new_row], ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
    combined = combined.dropna(subset=["date"]).sort_values("date")
    combined = combined.drop_duplicates(subset=["date"], keep="last")
    combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")

    # 저장
    combined.to_csv(OUT_CSV, index=False)
    print(f"[OK] liquidity_data updated: {OUT_CSV} (rows={len(combined)})")

if __name__ == "__main__":
    main()

