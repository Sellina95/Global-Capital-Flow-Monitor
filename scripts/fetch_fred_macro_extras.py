# scripts/fetch_fred_macro_extras.py
from __future__ import annotations

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "fred_macro_extras.csv"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

SERIES = {
    "FCI": "NFCI",        # Chicago Fed National Financial Conditions Index
    "REAL_RATE": "DFII10" # 10Y TIPS Real Yield (percent)
}

def fetch_fred(series_id: str) -> pd.DataFrame:
    df = pd.read_csv(f"{FRED_CSV}{series_id}")
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    df = df.dropna(subset=["date", series_id]).sort_values("date").reset_index(drop=True)
    return df

def safe_read_existing(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return pd.DataFrame(columns=["date", "FCI", "REAL_RATE"])
    try:
        df = pd.read_csv(csv_path)
        if df.empty or "date" not in df.columns:
            return pd.DataFrame(columns=["date", "FCI", "REAL_RATE"])
        return df
    except Exception:
        return pd.DataFrame(columns=["date", "FCI", "REAL_RATE"])

def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fci_df = fetch_fred(SERIES["FCI"])
    real_df = fetch_fred(SERIES["REAL_RATE"])

    # as_of = 둘 중 더 "느린 최신일" 기준으로 스냅샷
    as_of = min(fci_df.iloc[-1]["date"], real_df.iloc[-1]["date"])

    def last_value_on_or_before(df: pd.DataFrame, col: str) -> float:
        sub = df[df["date"] <= as_of]
        if sub.empty:
            raise ValueError(f"No data on or before {as_of.date()} for {col}")
        return float(sub.iloc[-1][col])

    fci = last_value_on_or_before(fci_df, SERIES["FCI"])
    real_rate = last_value_on_or_before(real_df, SERIES["REAL_RATE"])

    new_row = pd.DataFrame([{
        "date": as_of.strftime("%Y-%m-%d"),
        "FCI": fci,
        "REAL_RATE": real_rate,
    }])

    old = safe_read_existing(OUT_CSV)
    # ✅ 초기 1회: 파일이 비었으면 최근 60개 관측치 백필
    if old.empty:
        # 두 시계열을 date로 merge해서 공통 날짜만 사용
        fci_df2 = fci_df.rename(columns={SERIES["FCI"]: "FCI"})
        real_df2 = real_df.rename(columns={SERIES["REAL_RATE"]: "REAL_RATE"})
        merged = pd.merge(fci_df2[["date", "FCI"]], real_df2[["date", "REAL_RATE"]], on="date", how="inner")
        merged = merged.dropna(subset=["date", "FCI", "REAL_RATE"]).sort_values("date").reset_index(drop=True)

        # 최근 60개만 저장 (원하면 90/120으로 늘려도 됨)
        backfill = merged.tail(60).copy()
        backfill["date"] = backfill["date"].dt.strftime("%Y-%m-%d")
        backfill.to_csv(OUT_CSV, index=False)
        print(f"[OK] fred_macro_extras backfilled: {OUT_CSV} (rows={len(backfill)})")
        return
        
    combined = pd.concat([old, new_row], ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
    combined = combined.dropna(subset=["date"]).sort_values("date")
    combined = combined.drop_duplicates(subset=["date"], keep="last")
    combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")

    combined.to_csv(OUT_CSV, index=False)
    print(f"[OK] fred_macro_extras updated: {OUT_CSV} (rows={len(combined)})")

if __name__ == "__main__":
    main()
