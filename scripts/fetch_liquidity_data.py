from __future__ import annotations

from pathlib import Path
import time
from datetime import datetime, timezone, timedelta

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "liquidity_data.csv"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

SERIES = {
    "TGA": "WTREGEN",     # Treasury General Account (Millions of $)
    "RRP": "RRPONTSYD",   # Overnight Reverse Repo (Millions of $)
    "WALCL": "WALCL",     # Fed Total Assets (Millions of $) - weekly
}

KST = timezone(timedelta(hours=9))


def fetch_fred(series_id: str, retries: int = 3, delay: int = 5) -> pd.DataFrame:
    """Fetch a FRED series with retries. On failure, return empty DataFrame."""
    url = f"{FRED_CSV}{series_id}"

    last_err = None
    for attempt in range(retries):
        try:
            df = pd.read_csv(url)
            df.columns = ["date", series_id]
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
            df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
            return df
        except Exception as e:
            last_err = e
            print(f"[WARN] fetch_fred({series_id}) attempt {attempt + 1}/{retries} failed: {type(e).__name__}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)

    print(f"[ERROR] fetch_fred({series_id}) failed after {retries} attempts. Last error: {type(last_err).__name__}: {last_err}")
    return pd.DataFrame(columns=["date", series_id])


def safe_read_existing(csv_path: Path) -> pd.DataFrame:
    base_cols = ["date", "TGA", "RRP", "WALCL", "NET_LIQ"]

    if not csv_path.exists():
        return pd.DataFrame(columns=base_cols)

    if csv_path.stat().st_size == 0:
        return pd.DataFrame(columns=base_cols)

    try:
        df = pd.read_csv(csv_path)
        if df.empty or "date" not in df.columns:
            return pd.DataFrame(columns=base_cols)

        for col in base_cols:
            if col not in df.columns:
                df[col] = pd.NA

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        for col in ["TGA", "RRP", "WALCL", "NET_LIQ"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        return df[base_cols]
    except Exception as e:
        print(f"[WARN] safe_read_existing failed: {type(e).__name__}: {e}")
        return pd.DataFrame(columns=base_cols)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    old = safe_read_existing(OUT_CSV)

    tga_df = fetch_fred(SERIES["TGA"])
    rrp_df = fetch_fred(SERIES["RRP"])
    walcl_df = fetch_fred(SERIES["WALCL"])

    today_kst = datetime.now(KST).date()
    today_ts = pd.Timestamp(today_kst)

    # 시작일 결정:
    # 1) 기존 csv가 있으면 그 시작일 유지
    # 2) 없으면 FRED 데이터 시작일 중 가장 빠른 날 사용
    candidate_starts = []

    if not old.empty:
        candidate_starts.append(old["date"].min())

    for df in [tga_df, rrp_df, walcl_df]:
        if not df.empty:
            candidate_starts.append(df["date"].min())

    if candidate_starts:
        start_date = min(candidate_starts)
    else:
        start_date = today_ts

    # ✅ 핵심: 오늘까지 날짜를 무조건 daily로 생성
    full_dates = pd.date_range(start=start_date, end=today_ts, freq="D")
    base = pd.DataFrame({"date": full_dates})

    # 기존 csv merge
    combined = base.merge(old, on="date", how="left")

    # 새 FRED 데이터 merge (같은 날짜에 값 있으면 overwrite)
    for col, fred_code in SERIES.items():
        fred_df = {
            "TGA": tga_df,
            "RRP": rrp_df,
            "WALCL": walcl_df,
        }[col].copy()

        if fred_df.empty:
            combined[f"{col}__new"] = pd.NA
            continue

        fred_df = fred_df.rename(columns={fred_code: f"{col}__new"})
        fred_df = fred_df[["date", f"{col}__new"]]
        combined = combined.merge(fred_df, on="date", how="left")

        # 새 데이터가 있으면 새 데이터 우선, 없으면 기존 값 유지
        combined[col] = combined[f"{col}__new"].combine_first(combined[col])
        combined = combined.drop(columns=[f"{col}__new"])

    # NET_LIQ 재계산: 세 값이 모두 있을 때만 계산
    combined["NET_LIQ"] = pd.NA
    mask = combined["TGA"].notna() & combined["RRP"].notna() & combined["WALCL"].notna()
    combined.loc[mask, "NET_LIQ"] = (
        combined.loc[mask, "WALCL"]
        - combined.loc[mask, "TGA"]
        - combined.loc[mask, "RRP"]
    )

    # 타입 정리
    for col in ["TGA", "RRP", "WALCL", "NET_LIQ"]:
        combined[col] = pd.to_numeric(combined[col], errors="coerce")

    combined = combined.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")

    combined.to_csv(OUT_CSV, index=False)

    print(f"[DEBUG] TGA last fetched date: {tga_df['date'].max() if not tga_df.empty else 'EMPTY'}")
    print(f"[DEBUG] RRP last fetched date: {rrp_df['date'].max() if not rrp_df.empty else 'EMPTY'}")
    print(f"[DEBUG] WALCL last fetched date: {walcl_df['date'].max() if not walcl_df.empty else 'EMPTY'}")
    print(f"[DEBUG] CSV last date after update: {combined['date'].iloc[-1] if not combined.empty else 'EMPTY'}")
    print(f"[OK] liquidity_data updated: {OUT_CSV} (rows={len(combined)})")


if __name__ == "__main__":
    main()
