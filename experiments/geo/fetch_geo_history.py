# experiments/geo/fetch_geo_history.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Tuple
import json
import io

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)

OUT_TSV = EXP_DATA_DIR / "geo_history.csv"          # 이름은 csv 유지 (하지만 탭 구분)
META_JSON = EXP_DATA_DIR / "sources_meta.json"

DEFAULT_START = "2016-08-16"


# ✅ FRED (안정)
FRED_SERIES: Dict[str, str] = {
    "VIX": "VIXCLS",
    "WTI": "DCOILWTICO",
    "GOLD": "GOLDAMGBD228NLBM",
    "USDCNH": "DEXCHUS",
    "USDJPY": "DEXJPUS",
    "USDMXN": "DEXMXUS",

    "US10Y_Y": "DGS10",
    "KR10Y_Y": "IRLTLT01KRM156N",
    "JP10Y_Y": "IRLTLT01JPM156N",
    "CN10Y_Y": "IRLTLT01CNM156N",
    "IL10Y_Y": "IRLTLT01ILM156N",
    "TR10Y_Y": "IRLTLT01TRM156N",
}

# ✅ STOOQ (ETF/테마)
STOOQ_SERIES: Dict[str, str] = {
    "EEM": "eem.us",
    "EMB": "emb.us",
    "SEA": "sea.us",
    "BDRY": "bdry.us",
    "ITA": "ita.us",
    "XAR": "xar.us",
}

SPREAD_PAIRS: List[Tuple[str, str]] = [
    ("KR10Y_Y", "KR10Y_SPREAD"),
    ("JP10Y_Y", "JP10Y_SPREAD"),
    ("CN10Y_Y", "CN10Y_SPREAD"),
    ("IL10Y_Y", "IL10Y_SPREAD"),
    ("TR10Y_Y", "TR10Y_SPREAD"),
]


def _fred_csv_url(series_id: str, start: str, end: str) -> str:
    base = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    return f"{base}?id={series_id}&cosd={start}&coed={end}"


def _http_get_text(url: str, timeout: int = 30) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (GitHubActions; geo-backtest) requests",
        "Accept": "text/csv,text/plain,*/*",
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text


def fetch_fred_series(series_id: str, start: str, end: str) -> pd.Series:
    """
    ✅ FIXED: DATE를 index로 두고 numeric 변환 후 dropna.
    """
    url = _fred_csv_url(series_id, start, end)
    text = _http_get_text(url)

    df = pd.read_csv(io.StringIO(text))
    if df.empty or "DATE" not in df.columns or series_id not in df.columns:
        return pd.Series(dtype="float64")

    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    df = df.dropna(subset=["DATE"]).sort_values("DATE")

    s = pd.to_numeric(df[series_id], errors="coerce")
    s.index = df["DATE"]
    s = s.dropna()
    s = s[~s.index.isna()].sort_index()
    return s


def fetch_stooq_close(symbol: str, start: str) -> pd.Series:
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    text = _http_get_text(url)

    df = pd.read_csv(io.StringIO(text))
    if df.empty or "Date" not in df.columns or "Close" not in df.columns:
        return pd.Series(dtype="float64")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date")
    df = df[df["Date"] >= pd.to_datetime(start)].copy()

    s = pd.to_numeric(df["Close"], errors="coerce")
    s.index = df["Date"]
    s = s.dropna()
    s = s[~s.index.isna()].sort_index()
    return s


def _series_to_frame(s: pd.Series, colname: str) -> pd.DataFrame:
    # ✅ 빈 시리즈여도 컬럼 “형태”를 유지 (merge 시 컬럼이 빠지지 않게)
    if s is None or s.empty:
        return pd.DataFrame({"date": pd.to_datetime([]), colname: pd.Series(dtype="float64")})

    out = pd.DataFrame({"date": s.index, colname: s.values})
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date")
    return out


def main() -> None:
    start = DEFAULT_START
    today_utc = pd.Timestamp.now("UTC").date()
    end = today_utc.strftime("%Y-%m-%d")

    meta: Dict[str, Any] = {
        "start": start,
        "end_inclusive": end,
        "sources": {},
    }

    frames: List[pd.DataFrame] = []

    # 1) FRED
    for key, series_id in FRED_SERIES.items():
        print(f"[FETCH] {key} <- FRED:{series_id}")
        try:
            s = fetch_fred_series(series_id, start, end)
            frames.append(_series_to_frame(s, key))
            meta["sources"][key] = {
                "source": "fred_csv",
                "series_id": series_id,
                "status": "OK" if not s.empty else "EMPTY",
                "rows": int(len(s)),
                "from": (str(s.index.min().date()) if not s.empty else None),
                "to": (str(s.index.max().date()) if not s.empty else None),
                "error": None,
            }
        except Exception as e:
            frames.append(_series_to_frame(pd.Series(dtype="float64"), key))
            meta["sources"][key] = {
                "source": "fred_csv",
                "series_id": series_id,
                "status": "ERROR",
                "rows": 0,
                "from": None,
                "to": None,
                "error": str(e),
            }

    # 2) STOOQ
    for key, symbol in STOOQ_SERIES.items():
        print(f"[FETCH] {key} <- STOOQ:{symbol}")
        try:
            s = fetch_stooq_close(symbol, start)
            frames.append(_series_to_frame(s, key))
            meta["sources"][key] = {
                "source": "stooq_csv",
                "symbol": symbol,
                "status": "OK" if not s.empty else "EMPTY",
                "rows": int(len(s)),
                "from": (str(s.index.min().date()) if not s.empty else None),
                "to": (str(s.index.max().date()) if not s.empty else None),
                "error": None,
            }
        except Exception as e:
            frames.append(_series_to_frame(pd.Series(dtype="float64"), key))
            meta["sources"][key] = {
                "source": "stooq_csv",
                "symbol": symbol,
                "status": "ERROR",
                "rows": 0,
                "from": None,
                "to": None,
                "error": str(e),
            }

    # 3) outer merge (✅ 빈 프레임도 포함해야 컬럼이 유지됨)
    out = frames[0].copy()
    for f in frames[1:]:
        out = pd.merge(out, f, on="date", how="outer")

    if "date" not in out.columns:
        META_JSON.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        raise RuntimeError("Internal error: merged output missing 'date' column.")

    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)

    # 4) spreads (level)
    out["US10Y_Y"] = pd.to_numeric(out.get("US10Y_Y"), errors="coerce")
    for local_key, spread_key in SPREAD_PAIRS:
        out[local_key] = pd.to_numeric(out.get(local_key), errors="coerce")
        out[spread_key] = out[local_key] - out["US10Y_Y"]

    # ✅ 결과가 비면: 기존 파일 있으면 보존하고 워크플로우는 안 죽게
    if out.empty:
        META_JSON.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        if OUT_TSV.exists():
            print("[WARN] geo_history result is EMPTY. Existing geo_history.csv kept (no overwrite).")
            print(f"[OK] meta : {META_JSON}")
            return
        raise RuntimeError("geo_history result is EMPTY (rows=0) and no existing file to keep.")

    # date first
    cols = ["date"] + [c for c in out.columns if c != "date"]
    out = out[cols]

    # ✅ 탭 구분으로 저장 (헤더 붙는 문제 끝)
    tmp = OUT_TSV.with_suffix(".csv.tmp")
    out.to_csv(tmp, index=False, encoding="utf-8", sep="\t")
    tmp.replace(OUT_TSV)

    META_JSON.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] wrote: {OUT_TSV} (rows={len(out)})")
    print(f"[OK] meta : {META_JSON}")


if __name__ == "__main__":
    main()
