# experiments/geo/fetch_geo_history.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import json
import pandas as pd

import yfinance as yf


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = EXP_DATA_DIR / "geo_history.csv"
META_JSON = EXP_DATA_DIR / "sources_meta.json"


# ----------------------------
# Config
# ----------------------------
DEFAULT_START = "2016-08-16"
DEFAULT_END = None  # None => today (UTC)


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
    # ⚠ USDCNH은 yfinance가 자주 1 row만 주거나 비는 케이스가 있어서 FRED로 받는 걸 권장
    # "USDCNH": "CNH=X",
}

# ✅ FRED series (CSV URL로 직접 fetch)
# - USDCNH: DEXCHUS (China / U.S. Foreign Exchange Rate)
# - US10Y: DGS10
# - Sovereign yields (가능한 것만; EMPTY여도 절대 죽지 않게)
FRED_SERIES: Dict[str, str] = {
    "USDCNH": "DEXCHUS",
    "US10Y_Y": "DGS10",
    "KR10Y_Y": "IRLTLT01KRM156N",
    "JP10Y_Y": "IRLTLT01JPM156N",
    "CN10Y_Y": "IRLTLT01CNM156N",  # 있으면 채워지고 없으면 EMPTY로 남음
    "IL10Y_Y": "IRLTLT01ILM156N",  # 없을 수 있음
    "TR10Y_Y": "IRLTLT01TRM156N",  # 없을 수 있음
}

# Spread 계산할 대상들: (local_yield_key, spread_key)
SPREAD_PAIRS: List[Tuple[str, str]] = [
    ("KR10Y_Y", "KR10Y_SPREAD"),
    ("JP10Y_Y", "JP10Y_SPREAD"),
    ("CN10Y_Y", "CN10Y_SPREAD"),
    ("IL10Y_Y", "IL10Y_SPREAD"),
    ("TR10Y_Y", "TR10Y_SPREAD"),
]


# ----------------------------
# Helpers
# ----------------------------
def _fred_csv_url(series_id: str, start: str, end: Optional[str]) -> str:
    # FRED 그래프 CSV 엔드포인트 (가장 단순/안정)
    # DATE, <series_id>
    base = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    params = f"?id={series_id}&cosd={start}"
    if end:
        params += f"&coed={end}"
    return base + params


def fetch_fred_series(series_id: str, start: str, end: Optional[str]) -> pd.Series:
    url = _fred_csv_url(series_id, start, end)
    df = pd.read_csv(url)
    if df.empty or "DATE" not in df.columns:
        return pd.Series(dtype="float64")

    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    df = df.dropna(subset=["DATE"]).sort_values("DATE")

    # 값 컬럼은 series_id 이름으로 옴
    if series_id not in df.columns:
        return pd.Series(dtype="float64")

    s = pd.to_numeric(df[series_id], errors="coerce")
    s.index = df["DATE"]
    s.name = series_id
    return s.dropna()


def fetch_yfinance_close(ticker: str, start: str, end: Optional[str]) -> pd.Series:
    df = yf.download(
        ticker,
        start=start,
        end=end,
        progress=False,
        auto_adjust=False,
        group_by="column",
        threads=True,
    )
    if df is None or df.empty:
        return pd.Series(dtype="float64")

    # yfinance: Close 우선, 없으면 Adj Close
    col = "Close" if "Close" in df.columns else ("Adj Close" if "Adj Close" in df.columns else None)
    if col is None:
        return pd.Series(dtype="float64")

    s = pd.to_numeric(df[col], errors="coerce").dropna()
    s.index = pd.to_datetime(s.index, errors="coerce")
    s = s[~s.index.isna()].sort_index()
    return s


def _series_to_frame(s: pd.Series, colname: str) -> pd.DataFrame:
    # date index -> column
    if s is None or s.empty:
        return pd.DataFrame(columns=["date", colname])
    out = pd.DataFrame({"date": s.index, colname: s.values})
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date")
    return out


# ----------------------------
# Main
# ----------------------------
def main() -> None:
    start = DEFAULT_START
    end = DEFAULT_END

    meta: Dict[str, Any] = {"start": start, "end": end, "sources": {}}

    frames: List[pd.DataFrame] = []

    # 1) yfinance pulls
    for key, ticker in YF_TICKERS.items():
        print(f"[FETCH] {key} <- {ticker}")
        try:
            s = fetch_yfinance_close(ticker, start, end)
            status = "OK" if not s.empty else "EMPTY"
            frm = _series_to_frame(s, key)
            frames.append(frm)

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

    # 2) FRED pulls (NO pandas_datareader)
    for key, series_id in FRED_SERIES.items():
        print(f"[FETCH] {key} <- FRED:{series_id}")
        try:
            s = fetch_fred_series(series_id, start, end)
            status = "OK" if not s.empty else "EMPTY"
            frm = _series_to_frame(s, key)
            frames.append(frm)

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

    # 3) Merge all frames on date
    # frames: each has columns ["date", <key>]
    # outer merge를 순차적으로
    if not frames:
        raise RuntimeError("No series fetched (frames empty).")

    out = frames[0].copy()
    for f in frames[1:]:
        if f is None or f.empty:
            continue
        out = pd.merge(out, f, on="date", how="outer")

    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)

    # 4) Sovereign spread 계산 (가능한 값만)
    # spread = local_10y - US10Y_Y
    if "US10Y_Y" in out.columns:
        out["US10Y_Y"] = pd.to_numeric(out["US10Y_Y"], errors="coerce")
        for local_key, spread_key in SPREAD_PAIRS:
            if local_key in out.columns:
                out[local_key] = pd.to_numeric(out[local_key], errors="coerce")
                out[spread_key] = out[local_key] - out["US10Y_Y"]
            else:
                # 컬럼이 없으면 생성만 (후속 코드에서 missing 확인 가능)
                out[spread_key] = pd.NA
    else:
        # US10Y 없으면 spreads 전부 NA로 생성
        for _, spread_key in SPREAD_PAIRS:
            out[spread_key] = pd.NA

    # 5) Write outputs
    # date column first
    cols = ["date"] + [c for c in out.columns if c != "date"]
    out = out[cols]

    out.to_csv(OUT_CSV, index=False, encoding="utf-8")
    META_JSON.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] wrote: {OUT_CSV} (rows={len(out)})")
    print(f"[OK] meta : {META_JSON}")


if __name__ == "__main__":
    main()
