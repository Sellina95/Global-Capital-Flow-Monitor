# experiments/geo/fetch_geo_history.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd

# yfinance는 requirements에 있다고 가정
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = EXP_DATA_DIR / "geo_history.csv"
META_JSON = EXP_DATA_DIR / "sources_meta.json"

# ---- Backtest horizon ----
DAYS = 2400  # 넉넉히 (대략 6~7년) / 필요하면 줄여도 됨

# ---- yfinance sources (Close 기준) ----
# key: 내부 컬럼명, ticker: yfinance ticker
YF_SOURCES: List[Tuple[str, str]] = [
    ("VIX", "^VIX"),
    ("WTI", "CL=F"),
    ("GOLD", "GC=F"),
    ("USDCNH", "CNH=X"),
    ("USDJPY", "JPY=X"),
    ("USDMXN", "MXN=X"),
    ("EEM", "EEM"),
    ("EMB", "EMB"),
    ("SEA", "SEA"),
    ("BDRY", "BDRY"),
    ("ITA", "ITA"),
    ("XAR", "XAR"),
]

def _fetch_yf_close(ticker: str, days: int) -> pd.Series:
    # yfinance는 period로 받는게 안정적
    # buffer 조금 더
    df = yf.download(ticker, period=f"{days}d", interval="1d", auto_adjust=False, progress=False)
    if df is None or df.empty:
        return pd.Series(dtype="float64")
    # yfinance 컬럼 케이스 대응
    col = "Close" if "Close" in df.columns else ("Adj Close" if "Adj Close" in df.columns else None)
    if col is None:
        return pd.Series(dtype="float64")
    s = pd.to_numeric(df[col], errors="coerce")
    s.index = pd.to_datetime(s.index, errors="coerce")
    s = s.dropna()
    return s

def _load_sovereign_spreads_csv() -> pd.DataFrame:
    """
    프로덕션에서 생성하는 data/sovereign_spreads.csv를 그대로 읽어서 실험 데이터에 병합.
    헤더 예:
    date, US10Y_Y, KR10Y_Y, ..., KR10Y_SPREAD, JP10Y_SPREAD, ...
    """
    path = BASE_DIR / "data" / "sovereign_spreads.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    if df.empty:
        return pd.DataFrame()

    # normalize date
    if "date" not in df.columns:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")

    # SPREAD 컬럼만 사용 (Y컬럼은 굳이 필요 없으면 제외)
    spread_cols = [c for c in df.columns if c.endswith("_SPREAD")]
    keep = ["date"] + spread_cols
    return df[keep].copy()

def main() -> None:
    meta: Dict[str, Any] = {"days": DAYS, "sources": {}}
    series_list: List[pd.Series] = []

    # 1) yfinance series
    for key, ticker in YF_SOURCES:
        print(f"[FETCH] {key} <- {ticker}")
        try:
            s = _fetch_yf_close(ticker, DAYS)
            status = "OK" if not s.empty else "EMPTY"

            meta["sources"][key] = {
                "source": "yfinance",
                "ticker": ticker,
                "status": status,
                "rows": int(len(s)),
                "error": None,
                "from": str(s.index.min().date()) if not s.empty else None,
                "to": str(s.index.max().date()) if not s.empty else None,
            }

            if not s.empty:
                s = s.rename(key)
                series_list.append(s)

        except Exception as e:
            meta["sources"][key] = {
                "source": "yfinance",
                "ticker": ticker,
                "status": "ERROR",
                "rows": 0,
                "error": str(e),
                "from": None,
                "to": None,
            }

    if not series_list:
        raise RuntimeError("No yfinance series downloaded (all EMPTY/ERROR).")

    # index = date
    df = pd.concat(series_list, axis=1)
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()].sort_index()
    df = df.reset_index().rename(columns={"index": "date"})

    # 2) merge sovereign spreads (CDS proxy)
    sov = _load_sovereign_spreads_csv()
    if not sov.empty:
        print("[MERGE] sovereign_spreads.csv -> geo_history")
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        # left merge: 실험데이터 날짜 기준, spreads는 ffill
        df = pd.merge(df, sov, on="date", how="left")
        spread_cols = [c for c in df.columns if c.endswith("_SPREAD")]
        for c in spread_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce").ffill()

        meta["sources"]["SOVEREIGN_SPREADS"] = {
            "source": "csv",
            "path": "data/sovereign_spreads.csv",
            "status": "OK",
            "cols": spread_cols,
            "rows": int(len(sov)),
        }
    else:
        meta["sources"]["SOVEREIGN_SPREADS"] = {
            "source": "csv",
            "path": "data/sovereign_spreads.csv",
            "status": "MISSING_OR_EMPTY",
            "cols": [],
            "rows": 0,
        }

    # 3) final clean
    df = df.sort_values("date").drop_duplicates("date", keep="last")

    # 숫자 컬럼 정리
    for c in df.columns:
        if c == "date":
            continue
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df.to_csv(OUT_CSV, index=False)
    (META_JSON).write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] wrote: {OUT_CSV} (rows={len(df)})")
    print(f"[OK] meta : {META_JSON}")

if __name__ == "__main__":
    main()
