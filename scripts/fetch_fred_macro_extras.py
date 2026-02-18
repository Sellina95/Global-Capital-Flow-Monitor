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
    def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    fci_df = fetch_fred(SERIES["FCI"]).rename(columns={SERIES["FCI"]: "FCI"})
    real_df = fetch_fred(SERIES["REAL_RATE"]).rename(columns={SERIES["REAL_RATE"]: "REAL_RATE"})

    # 최근 구간만 넉넉히 (ffill용)
    fci_df = fci_df.tail(180)
    real_df = real_df.tail(180)

    merged = pd.merge(fci_df, real_df, on="date", how="outer")
    merged = merged.sort_values("date").drop_duplicates(subset=["date"], keep="last")

    # ✅ 주간/결측을 일간으로 메꾸기
    merged["FCI"] = merged["FCI"].ffill()
    merged["REAL_RATE"] = merged["REAL_RATE"].ffill()

    # 마지막 90행 정도만 저장
    merged = merged.dropna(subset=["date"]).tail(90)

    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")
    merged.to_csv(OUT_CSV, index=False)

    print(f"[OK] fred_macro_extras updated: {OUT_CSV} (rows={len(merged)})")


if __name__ == "__main__":
    main()
