# experiments/geo/fetch_geo_history.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import json
import time

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
OUT_CSV = EXP_DATA_DIR / "geo_history.csv"
META_JSON = EXP_DATA_DIR / "sources_meta.json"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

# ✅ 최소 세트: 너의 7.2에 이미 쓰는 핵심만
# (원하면 여기 추가해도 됨. 실험용이라 프로덕션 영향 없음)
FRED_SERIES = {
    "US10Y": "DGS10",
    "DXY": "DTWEXBGS",          # Broad USD Index (FRED)
    "WTI": "DCOILWTICO",
    "VIX": "VIXCLS",
    "GOLD": "GOLDAMGBD228NLBM", # London gold fixing (USD)
    "USDCNH": "DEXCHUS",        # ⚠ 이건 CNH/CNY 소스가 다를 수 있음. 실패 가능.
    "USDJPY": "DEXJPUS",
    "USDMXN": "DEXMXUS",
}

# 간단한 재시도
RETRY = 3
SLEEP_SEC = 1.2


def _fetch_fred(series_id: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Returns (df, meta)
    df columns: date, <series_id>
    """
    meta: Dict[str, Any] = {"series_id": series_id, "status": "INIT", "rows": 0, "error": None}

    url = f"{FRED_CSV}{series_id}"
    last_err: Optional[str] = None

    for i in range(RETRY):
        try:
            df = pd.read_csv(url)
            if df is None or df.empty:
                meta["status"] = "EMPTY"
                meta["rows"] = 0
                return pd.DataFrame(columns=["date", series_id]), meta

            df.columns = ["date", series_id]
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
            df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

            meta["status"] = "OK"
            meta["rows"] = int(len(df))
            return df, meta

        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            meta["status"] = "RETRY"
            meta["error"] = last_err
            time.sleep(SLEEP_SEC * (i + 1))

    meta["status"] = "FAIL"
    meta["error"] = last_err
    return pd.DataFrame(columns=["date", series_id]), meta


def main(days: int = 1600) -> None:
    """
    days: keep last N rows after merge (대략 과거 ~몇년치)
    """
    EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    meta_all: Dict[str, Any] = {"fred": {}, "note": "geo history fetch (experiment only)"}

    merged: Optional[pd.DataFrame] = None

    for key, series_id in FRED_SERIES.items():
        print(f"[FETCH] {key} ({series_id})")
        df, meta = _fetch_fred(series_id)
        meta_all["fred"][key] = meta

        if df.empty:
            continue

        df = df.rename(columns={series_id: key})
        merged = df if merged is None else pd.merge(merged, df, on="date", how="outer")

    if merged is None or merged.empty:
        # 파일은 만들되 빈 파일로 저장 (실험환경에서 안전)
        empty = pd.DataFrame(columns=["date"] + list(FRED_SERIES.keys()))
        empty.to_csv(OUT_CSV, index=False)
        META_JSON.write_text(json.dumps(meta_all, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[WARN] All series empty. Wrote empty file: {OUT_CSV}")
        return

    merged = merged.sort_values("date").drop_duplicates(subset=["date"], keep="last")

    # 일부 시리즈는 휴일/주간 등 간헐적 → forward fill
    for c in merged.columns:
        if c != "date":
            merged[c] = pd.to_numeric(merged[c], errors="coerce").ffill()

    # 마지막 N일만
    merged = merged.dropna(subset=["date"]).tail(int(days)).reset_index(drop=True)
    merged["date"] = pd.to_datetime(merged["date"]).dt.strftime("%Y-%m-%d")

    merged.to_csv(OUT_CSV, index=False)
    META_JSON.write_text(json.dumps(meta_all, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] geo_history updated: {OUT_CSV} (rows={len(merged)})")
    print(f"[OK] meta saved: {META_JSON}")


if __name__ == "__main__":
    # 기본은 1600 rows 정도 (대략 6년+)
    main(days=1600)
