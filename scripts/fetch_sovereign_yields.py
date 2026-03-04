# scripts/fetch_sovereign_yields.py
from __future__ import annotations

from pathlib import Path
import time
import pandas as pd
from urllib.error import URLError, HTTPError

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "sovereign_yields.csv"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

# ✅ US는 daily benchmark를 쓰는 게 좋아서 DGS10 사용
# ✅ 나머지는 OECD long-term yields (보통 월/주/일 혼재) -> 리포트에서 ffill 처리
SERIES = {
    "US10Y": "DGS10",
    "KR10Y": "IRLTLT01KRM156N",  # Korea 10Y (OECD)
    "JP10Y": "IRLTLT01JPM156N",  # Japan 10Y (OECD)
    "DE10Y": "IRLTLT01DEM156N",  # Germany 10Y (OECD)
    # 필요시 추가:
    # "GB10Y": "IRLTLT01GBM156N",
    # "FR10Y": "IRLTLT01FRM156N",
    # "IT10Y": "IRLTLT01ITM156N",
    # "ES10Y": "IRLTLT01ESM156N",
}

def fetch_fred_csv(series_id: str, max_retries: int = 5, sleep_base: float = 1.5) -> pd.DataFrame:
    url = f"{FRED_CSV}{series_id}"
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            df = pd.read_csv(url)
            if df is None or df.empty:
                return pd.DataFrame()
            df.columns = ["date", series_id]
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
            df = df.dropna(subset=["date", series_id]).sort_values("date").reset_index(drop=True)
            return df
        except (HTTPError, URLError, Exception) as e:
            last_err = e
            time.sleep(sleep_base * attempt)
    print(f"[WARN] fetch failed for {series_id}: {type(last_err).__name__}: {last_err}")
    return pd.DataFrame()

def main(days: int = 365) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    frames = []
    for col, sid in SERIES.items():
        print(f"[FETCH] {col} ({sid})")
        df = fetch_fred_csv(sid)
        if df.empty:
            print("  -> no data")
            continue
        df = df.rename(columns={sid: col})
        frames.append(df.tail(days))

    if not frames:
        print("[WARN] all sovereign yield fetch failed. keeping existing if present.")
        if OUT_CSV.exists():
            print(f"[OK] kept existing: {OUT_CSV}")
            return
        pd.DataFrame(columns=["date"] + list(SERIES.keys())).to_csv(OUT_CSV, index=False)
        print(f"[OK] created empty: {OUT_CSV}")
        return

    merged = frames[0]
    for f in frames[1:]:
        merged = merged.merge(f, on="date", how="outer")

    merged = merged.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    merged = merged.tail(days).reset_index(drop=True)

    # stringify date
    merged["date"] = merged["date"].dt.strftime("%Y-%m-%d")
    merged.to_csv(OUT_CSV, index=False)
    print(f"[OK] sovereign_yields updated: {OUT_CSV} (rows={len(merged)})")

if __name__ == "__main__":
    main()
