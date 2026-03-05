# experiments/geo/fetch_geo_history.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = EXP_DATA_DIR / "geo_history.csv"
META_JSON = EXP_DATA_DIR / "sources_meta.json"

# ---- Backtest horizon ----
DAYS = 2400  # 넉넉히

# ---- yfinance sources (Close 기준) ----
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

def _series_from_history(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype="float64")

    # yfinance가 가끔 MultiIndex 형태로 주는 경우 방어
    if isinstance(df.columns, pd.MultiIndex):
        # 가능한 후보: ('Close', ticker) 또는 ('Adj Close', ticker)
        for lvl0 in ["Close", "Adj Close"]:
            if lvl0 in df.columns.get_level_values(0):
                sub = df[lvl0]
                # 단일 컬럼이면 Series로
                if isinstance(sub, pd.DataFrame) and sub.shape[1] >= 1:
                    s = sub.iloc[:, 0]
                else:
                    s = sub
                s = pd.to_numeric(s, errors="coerce").dropna()
                s.index = pd.to_datetime(s.index, errors="coerce")
                return s.dropna()
        return pd.Series(dtype="float64")

    # 일반 컬럼
    col = None
    if "Close" in df.columns:
        col = "Close"
    elif "Adj Close" in df.columns:
        col = "Adj Close"

    if col is None:
        return pd.Series(dtype="float64")

    s = pd.to_numeric(df[col], errors="coerce")
    s.index = pd.to_datetime(df.index, errors="coerce")
    s = s.dropna()
    return s

def _fetch_yf_close(ticker: str, days: int) -> pd.Series:
    # 1) download 시도
    try:
        df = yf.download(
            ticker,
            period=f"{days}d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,  # CI에서 가끔 threads가 불안정해서 끔
        )
        s = _series_from_history(df)
        if not s.empty:
            return s
    except Exception:
        pass

    # 2) history 폴백
    try:
        tk = yf.Ticker(ticker)
        df2 = tk.history(period=f"{days}d", interval="1d", auto_adjust=False)
        s2 = _series_from_history(df2)
        return s2
    except Exception:
        return pd.Series(dtype="float64")

def _load_sovereign_spreads_csv() -> pd.DataFrame:
    path = BASE_DIR / "data" / "sovereign_spreads.csv"
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    if df is None or df.empty:
        return pd.DataFrame()

    if "date" not in df.columns:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")

    spread_cols = [c for c in df.columns if c.endswith("_SPREAD")]
    keep = ["date"] + spread_cols
    return df[keep].copy()

def main() -> None:
    meta: Dict[str, Any] = {"days": DAYS, "sources": {}}
    series_list: List[pd.Series] = []

    # 1) yfinance series fetch (가능한 것만)
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
                series_list.append(s.rename(key))

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

    # 2) concat (yfinance가 전멸해도 진행 가능하게)
    df: pd.DataFrame
    if series_list:
        df = pd.concat(series_list, axis=1)
        df.index = pd.to_datetime(df.index, errors="coerce")
        df = df[~df.index.isna()].sort_index()
        df = df.reset_index().rename(columns={"index": "date"})
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
    else:
        # yfinance가 전부 죽은 케이스: 일단 빈 df 만들어두고 spreads로 살린다
        df = pd.DataFrame({"date": pd.to_datetime([])})

    # 3) merge sovereign spreads (CDS proxy)
    sov = _load_sovereign_spreads_csv()
    if not sov.empty:
        print("[MERGE] sovereign_spreads.csv -> geo_history")
        if df.empty:
            # yfinance가 전멸이면 spreads 날짜를 베이스로 생성
            df = sov.copy()
        else:
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

    # 4) 최종 방어: 그래도 데이터가 아예 없으면 그때만 실패
    if df is None or df.empty or "date" not in df.columns:
        raise RuntimeError(
            "No data available: yfinance all EMPTY/ERROR AND sovereign_spreads.csv missing/empty."
        )

    # 숫자 컬럼 정리
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")

    for c in df.columns:
        if c == "date":
            continue
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df.to_csv(OUT_CSV, index=False)
    META_JSON.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] wrote: {OUT_CSV} (rows={len(df)})")
    print(f"[OK] meta : {META_JSON}")

if __name__ == "__main__":
    main()
