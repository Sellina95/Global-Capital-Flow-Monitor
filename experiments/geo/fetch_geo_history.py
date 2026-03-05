# experiments/geo/fetch_geo_history.py

from __future__ import annotations
import json
from io import StringIO
from pathlib import Path
from typing import List, Tuple, Dict, Any

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent.parent
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"

OUT_CSV = EXP_DATA_DIR / "geo_history.csv"
OUT_META = EXP_DATA_DIR / "sources_meta.json"

START_DATE = "2016-08-16"


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# FRED DATA
# ------------------------------------------------------------
def fetch_fred(series_id: str, start: str, end: str, col: str) -> pd.Series:

    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    df = pd.read_csv(StringIO(r.text))

    if "DATE" not in df.columns:
        raise RuntimeError(f"FRED schema error {series_id}")

    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    df = df.dropna(subset=["DATE"])

    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")

    df = df[(df["DATE"] >= start) & (df["DATE"] <= end)]

    s = df.set_index("DATE")[series_id]
    s.name = col

    return s


# ------------------------------------------------------------
# STOOQ DATA
# ------------------------------------------------------------
def fetch_stooq(symbol: str, start: str, end: str, col: str) -> pd.Series:

    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    df = pd.read_csv(StringIO(r.text))

    date_col = "Date" if "Date" in df.columns else "date"

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")

    df = df[(df[date_col] >= start) & (df[date_col] <= end)]

    s = df.set_index(date_col)["Close"]
    s.name = col

    return s


# ------------------------------------------------------------
# SPREADS
# ------------------------------------------------------------
def build_spreads(df: pd.DataFrame) -> pd.DataFrame:

    if "US10Y_Y" not in df.columns:
        return df

    base = df["US10Y_Y"]

    mapping = {
        "KR10Y_Y": "KR10Y_SPREAD",
        "JP10Y_Y": "JP10Y_SPREAD",
        "CN10Y_Y": "CN10Y_SPREAD",
        "IL10Y_Y": "IL10Y_SPREAD",
        "TR10Y_Y": "TR10Y_SPREAD",
    }

    for k, v in mapping.items():
        if k in df.columns:
            df[v] = df[k] - base

    return df


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():

    ensure_dir(EXP_DATA_DIR)

    end_date = pd.Timestamp.utcnow().strftime("%Y-%m-%d")

    fred_series: List[Tuple[str, str]] = [
        ("VIX", "VIXCLS"),
        ("WTI", "DCOILWTICO"),
        ("GOLD", "GOLDAMGBD228NLBM"),
        ("USDCNH", "DEXCHUS"),
        ("USDJPY", "DEXJPUS"),
        ("USDMXN", "DEXMXUS"),
        ("US10Y_Y", "DGS10"),
        ("KR10Y_Y", "IRLTLT01KRM156N"),
        ("JP10Y_Y", "IRLTLT01JPM156N"),
        ("CN10Y_Y", "IRLTLT01CNM156N"),
        ("IL10Y_Y", "IRLTLT01ILM156N"),
        ("TR10Y_Y", "IRLTLT01TRM156N"),
    ]

    stooq_series: List[Tuple[str, str]] = [
        ("EEM", "eem.us"),
        ("EMB", "emb.us"),
        ("SEA", "sea.us"),
        ("BDRY", "bdry.us"),
        ("ITA", "ita.us"),
        ("XAR", "xar.us"),
    ]

    meta: Dict[str, Any] = {"sources": {}}

    series_list: List[pd.Series] = []

    # ------------------------------------------------------------
    # FETCH FRED
    # ------------------------------------------------------------
    for col, sid in fred_series:

        try:
            print(f"[FETCH] {col} <- FRED:{sid}")

            s = fetch_fred(sid, START_DATE, end_date, col)

            series_list.append(s)

            meta["sources"][col] = {"status": "OK"}

        except Exception as e:

            meta["sources"][col] = {"status": "ERROR", "error": str(e)}

    # ------------------------------------------------------------
    # FETCH STOOQ
    # ------------------------------------------------------------
    for col, sym in stooq_series:

        try:

            print(f"[FETCH] {col} <- STOOQ:{sym}")

            s = fetch_stooq(sym, START_DATE, end_date, col)

            series_list.append(s)

            meta["sources"][col] = {"status": "OK"}

        except Exception as e:

            meta["sources"][col] = {"status": "ERROR", "error": str(e)}

    # ------------------------------------------------------------
    # CONCAT
    # ------------------------------------------------------------
    df = pd.concat(series_list, axis=1)

    df = df.sort_index()

    # ------------------------------------------------------------
    # RESET INDEX (KEYERROR 방지 핵심)
    # ------------------------------------------------------------
    out = df.reset_index()

    first_col = out.columns[0]

    out = out.rename(columns={first_col: "date"})

    if "date" not in out.columns:
        raise RuntimeError(f"date column missing {out.columns}")

    out["date"] = pd.to_datetime(out["date"], errors="coerce")

    out = out.dropna(subset=["date"])

    # ------------------------------------------------------------
    # SPREAD
    # ------------------------------------------------------------
    out = build_spreads(out)

    # ------------------------------------------------------------
    # FILL
    # ------------------------------------------------------------
    num_cols = [c for c in out.columns if c != "date"]

    out[num_cols] = out[num_cols].ffill().bfill()

    # ------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------
    out.to_csv(OUT_CSV, sep="\t", index=False)

    with open(OUT_META, "w") as f:
        json.dump(meta, f, indent=2)

    print("saved:", OUT_CSV)
    print("rows:", len(out))


if __name__ == "__main__":
    main()
