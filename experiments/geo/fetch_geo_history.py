# experiments/geo/fetch_geo_history.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import json
import io

import pandas as pd
import requests
import yfinance as yf


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = EXP_DATA_DIR / "geo_history.csv"
META_JSON = EXP_DATA_DIR / "sources_meta.json"

DEFAULT_START = "2016-08-16"

# ✅ yfinance tickers (market proxies)
YF_TICKERS: Dict[str, str] = {
    "VIX": "^VIX",
    "WTI": "CL=F",
    "GOLD": "GC=F",
    "USDJPY": "JPY=X",
    "USDMXN": "MXN=X",
    "EEM": "EEM",
    "EMB": "EMB",
    "SEA": "SEA",
    "BDRY": "BDRY",
    "ITA": "ITA",
    "XAR": "XAR",
}

# ✅ FRED series (CSV URL)
FRED_SERIES: Dict[str, str] = {
    "USDCNH": "DEXCHUS",
    "US10Y_Y": "DGS10",
    "KR10Y_Y": "IRLTLT01KRM156N",
    "JP10Y_Y": "IRLTLT01JPM156N",
    "CN10Y_Y": "IRLTLT01CNM156N",
    "IL10Y_Y": "IRLTLT01ILM156N",
    "TR10Y_Y": "IRLTLT01TRM156N",
}

SPREAD_PAIRS: List[Tuple[str, str]] = [
    ("KR10Y_Y", "KR10Y_SPREAD"),
    ("JP10Y_Y", "JP10Y_SPREAD"),
    ("CN10Y_Y", "CN10Y_SPREAD"),
    ("IL10Y_Y", "IL10Y_SPREAD"),
    ("TR10Y_Y", "TR10Y_SPREAD"),
]


def _fred_csv_url(series_id: str, start: str, end: str) -> str:
    # end는 포함(coed inclusive)
    base = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    return f"{base}?id={series_id}&cosd={start}&coed={end}"


def _http_get_text(url: str, timeout: int = 20) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (GitHubActions; geo-backtest) requests",
        "Accept": "text/csv,text/plain,*/*",
    }
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text


def fetch_fred_series(series_id: str, start: str, end: str) -> pd.Series:
    url = _fred_csv_url(series_id, start, end)
    text = _http_get_text(url)
    df = pd.read_csv(io.StringIO(text))
    if df.empty or "DATE" not in df.columns or series_id not in df.columns:
        return pd.Series(dtype="float64")

    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    df = df.dropna(subset=["DATE"]).sort_values("DATE")

    s = pd.to_numeric(df[series_id], errors="coerce")
    s.index = df["DATE"]
    s.name = series_id
    return s.dropna()


def fetch_yfinance_close(ticker: str, start: str, end_exclusive: str) -> pd.Series:
    df = yf.download(
        ticker,
        start=start,
        end=end_exclusive,  # yfinance는 end가 exclusive라 "내일"로 넣어야 오늘 포함됨
        progress=False,
        auto_adjust=False,
        group_by="column",
        threads=True,
    )
    if df is None or df.empty:
        return pd.Series(dtype="float64")

    col = "Close" if "Close" in df.columns else ("Adj Close" if "Adj Close" in df.columns else None)
    if col is None:
        return pd.Series(dtype="float64")

    s = pd.to_numeric(df[col], errors="coerce").dropna()
    s.index = pd.to_datetime(s.index, errors="coerce")
    s = s[~s.index.isna()].sort_index()
    return s


def _series_to_frame(s: pd.Series, colname: str) -> pd.DataFrame:
    if s is None or s.empty:
        return pd.DataFrame(columns=["date", colname])
    out = pd.DataFrame({"date": s.index, colname: s.values})
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date")
    return out


def main() -> None:
    start = DEFAULT_START

    # ✅ today 포함되게:
    # - yfinance: end exclusive이므로 내일 날짜를 end로
    # - FRED: coed는 inclusive이므로 오늘 날짜로
    today_utc = pd.Timestamp.utcnow().date()
    yfin_end_exclusive = (today_utc + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    fred_end_inclusive = today_utc.strftime("%Y-%m-%d")

    meta: Dict[str, Any] = {
        "start": start,
        "end_yfinance_exclusive": yfin_end_exclusive,
        "end_fred_inclusive": fred_end_inclusive,
        "sources": {},
    }

    frames: List[pd.DataFrame] = []

    # 1) yfinance
    for key, ticker in YF_TICKERS.items():
        print(f"[FETCH] {key} <- {ticker}")
        try:
            s = fetch_yfinance_close(ticker, start, yfin_end_exclusive)
            status = "OK" if not s.empty else "EMPTY"
            frames.append(_series_to_frame(s, key))

            meta["sources"][key] = {
                "source": "yfinance",
                "ticker": ticker,
                "status": status,
                "rows": int(len(s)),
                "from": (str(s.index.min().date()) if not s.empty else None),
                "to": (str(s.index.max().date()) if not s.empty else None),
                "error": None,
            }
        except Exception as e:
            meta["sources"][key] = {
                "source": "yfinance",
                "ticker": ticker,
                "status": "ERROR",
                "rows": 0,
                "from": None,
                "to": None,
                "error": str(e),
            }

    # 2) FRED
    for key, series_id in FRED_SERIES.items():
        print(f"[FETCH] {key} <- FRED:{series_id}")
        try:
            s = fetch_fred_series(series_id, start, fred_end_inclusive)
            status = "OK" if not s.empty else "EMPTY"
            frames.append(_series_to_frame(s, key))

            meta["sources"][key] = {
                "source": "fred_csv",
                "series_id": series_id,
                "status": status,
                "rows": int(len(s)),
                "from": (str(s.index.min().date()) if not s.empty else None),
                "to": (str(s.index.max().date()) if not s.empty else None),
                "error": None,
            }
        except Exception as e:
            meta["sources"][key] = {
                "source": "fred_csv",
                "series_id": series_id,
                "status": "ERROR",
                "rows": 0,
                "from": None,
                "to": None,
                "error": str(e),
            }

    if not frames:
        raise RuntimeError("No series fetched (frames empty).")

    # 3) outer merge
    out = frames[0].copy()
    for f in frames[1:]:
        if f is None or f.empty:
            continue
        out = pd.merge(out, f, on="date", how="outer")

    if "date" not in out.columns:
        raise RuntimeError("Internal error: merged output missing 'date' column.")

    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)

    # ✅ 핵심: rows=0이면 절대 기존 파일 덮어쓰지 마
    if out.empty:
        META_JSON.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        raise RuntimeError(
            "geo_history result is EMPTY (rows=0). "
            "FRED/yfinance fetch가 모두 실패하거나 date 파싱이 깨졌음. "
            "기존 geo_history.csv는 보존됨."
        )

    # 4) spreads
    if "US10Y_Y" in out.columns:
        out["US10Y_Y"] = pd.to_numeric(out["US10Y_Y"], errors="coerce")
        for local_key, spread_key in SPREAD_PAIRS:
            if local_key in out.columns:
                out[local_key] = pd.to_numeric(out[local_key], errors="coerce")
                out[spread_key] = out[local_key] - out["US10Y_Y"]
            else:
                out[spread_key] = pd.NA
    else:
        for _, spread_key in SPREAD_PAIRS:
            out[spread_key] = pd.NA

    # 5) write (atomic)
    cols = ["date"] + [c for c in out.columns if c != "date"]
    out = out[cols]

    tmp_csv = OUT_CSV.with_suffix(".csv.tmp")
    out.to_csv(tmp_csv, index=False, encoding="utf-8")
    tmp_csv.replace(OUT_CSV)

    META_JSON.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] wrote: {OUT_CSV} (rows={len(out)})")
    print(f"[OK] meta : {META_JSON}")


if __name__ == "__main__":
    main()
