# experiments/geo/fetch_geo_history.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import yfinance as yf

try:
    from pandas_datareader.data import DataReader
except Exception as e:
    raise RuntimeError(
        "pandas_datareader is required for FRED fetch. "
        "requirements.txt에 pandas_datareader가 있어야 해."
    ) from e


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = EXP_DATA_DIR / "geo_history.csv"
META_JSON = EXP_DATA_DIR / "sources_meta.json"

START_DATE = "2016-08-16"  # ✅ 요청대로 고정
END_DATE = None  # today

# -----------------------------
# yfinance sources (long history)
# -----------------------------
YF_SOURCES: List[Tuple[str, str]] = [
    ("VIX", "^VIX"),
    ("WTI", "CL=F"),
    ("GOLD", "GC=F"),
    ("USDJPY", "JPY=X"),
    ("USDMXN", "MXN=X"),
    ("EEM", "EEM"),
    ("EMB", "EMB"),
    ("SEA", "SEA"),
    ("BDRY", "BDRY"),
    ("ITA", "ITA"),
    ("XAR", "XAR"),
]

# -----------------------------
# FRED sources (stable history)
# -----------------------------
# ✅ USDCNH 대체(안정): FRED DEXCHUS = Chinese Yuan per U.S. Dollar
FRED_FX: List[Tuple[str, str]] = [
    ("USDCNH", "DEXCHUS"),
]

# ✅ Sovereign yields (FRED/OECD series) - 너가 이미 쓰던 것들 기반
# 주의: 각 시리즈는 "존재하면" 가져오고, 없으면 meta에 ERROR로만 남김
FRED_SOV_YIELDS: List[Tuple[str, str]] = [
    ("US10Y_Y", "DGS10"),
    ("KR10Y_Y", "IRLTLT01KRM156N"),
    ("JP10Y_Y", "IRLTLT01JPM156N"),
    ("CN10Y_Y", "IRLTLT01CNM156N"),
    ("IL10Y_Y", "IRLTLT01ILM156N"),
    ("TR10Y_Y", "IRLTLT01TRM156N"),
]


def _series_from_yf(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype="float64")

    if isinstance(df.columns, pd.MultiIndex):
        # prefer Close
        if ("Close" in df.columns.get_level_values(0)):
            sub = df["Close"]
            s = sub.iloc[:, 0] if isinstance(sub, pd.DataFrame) else sub
        elif ("Adj Close" in df.columns.get_level_values(0)):
            sub = df["Adj Close"]
            s = sub.iloc[:, 0] if isinstance(sub, pd.DataFrame) else sub
        else:
            return pd.Series(dtype="float64")
    else:
        col = "Close" if "Close" in df.columns else ("Adj Close" if "Adj Close" in df.columns else None)
        if col is None:
            return pd.Series(dtype="float64")
        s = df[col]

    s = pd.to_numeric(s, errors="coerce")
    s.index = pd.to_datetime(s.index, errors="coerce")
    s = s[~s.index.isna()].sort_index().dropna()
    return s


def fetch_yfinance_close(ticker: str, start: str) -> pd.Series:
    # 1) download
    try:
        df = yf.download(
            ticker,
            start=start,
            end=END_DATE,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        s = _series_from_yf(df)
        if not s.empty:
            return s
    except Exception:
        pass

    # 2) history fallback
    try:
        tk = yf.Ticker(ticker)
        df2 = tk.history(start=start, end=END_DATE, interval="1d", auto_adjust=False)
        s2 = _series_from_yf(df2)
        return s2
    except Exception:
        return pd.Series(dtype="float64")


def fetch_fred_series(series_id: str, start: str) -> pd.Series:
    df = DataReader(series_id, "fred", start=start, end=END_DATE)  # returns DataFrame
    if df is None or df.empty:
        return pd.Series(dtype="float64")
    s = df.iloc[:, 0]
    s = pd.to_numeric(s, errors="coerce")
    s.index = pd.to_datetime(s.index, errors="coerce")
    s = s[~s.index.isna()].sort_index().dropna()
    return s


def main() -> None:
    meta: Dict[str, Any] = {"start": START_DATE, "sources": {}}
    series_list: List[pd.Series] = []

    # -----------------------------
    # 1) yfinance block
    # -----------------------------
    ok_yf = 0
    for key, ticker in YF_SOURCES:
        print(f"[FETCH] {key} <- {ticker}")
        try:
            s = fetch_yfinance_close(ticker, START_DATE)
            status = "OK" if not s.empty else "EMPTY"
            meta["sources"][key] = {
                "source": "yfinance",
                "ticker": ticker,
                "status": status,
                "rows": int(len(s)),
                "from": str(s.index.min().date()) if not s.empty else None,
                "to": str(s.index.max().date()) if not s.empty else None,
                "error": None,
            }
            if not s.empty:
                ok_yf += 1
                series_list.append(s.rename(key))
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

    if ok_yf == 0:
        # ✅ 실험은 “일부만 살아도” 진행 가능하게 (전처럼 raise 하지 말고 진행)
        meta["warn"] = "No yfinance series downloaded (all EMPTY/ERROR). Continue with FRED only."

    # -----------------------------
    # 2) FRED FX (USDCNH)
    # -----------------------------
    for key, sid in FRED_FX:
        print(f"[FETCH] {key} <- FRED:{sid}")
        try:
            s = fetch_fred_series(sid, START_DATE)
            status = "OK" if not s.empty else "EMPTY"
            meta["sources"][key] = {
                "source": "fred",
                "series": sid,
                "status": status,
                "rows": int(len(s)),
                "from": str(s.index.min().date()) if not s.empty else None,
                "to": str(s.index.max().date()) if not s.empty else None,
                "error": None,
            }
            if not s.empty:
                series_list.append(s.rename(key))
        except Exception as e:
            meta["sources"][key] = {
                "source": "fred",
                "series": sid,
                "status": "ERROR",
                "rows": 0,
                "from": None,
                "to": None,
                "error": str(e),
            }

    # -----------------------------
    # 3) FRED Sovereign yields + spreads
    # -----------------------------
    sov_series: Dict[str, pd.Series] = {}
    for key, sid in FRED_SOV_YIELDS:
        print(f"[FETCH] {key} <- FRED:{sid}")
        try:
            s = fetch_fred_series(sid, START_DATE)
            status = "OK" if not s.empty else "EMPTY"
            meta["sources"][key] = {
                "source": "fred",
                "series": sid,
                "status": status,
                "rows": int(len(s)),
                "from": str(s.index.min().date()) if not s.empty else None,
                "to": str(s.index.max().date()) if not s.empty else None,
                "error": None,
            }
            if not s.empty:
                sov_series[key] = s
        except Exception as e:
            meta["sources"][key] = {
                "source": "fred",
                "series": sid,
                "status": "ERROR",
                "rows": 0,
                "from": None,
                "to": None,
                "error": str(e),
            }

    # spreads 계산(가능한 것만)
    if "US10Y_Y" in sov_series:
        us = sov_series["US10Y_Y"]
        for k in ["KR10Y_Y", "JP10Y_Y", "CN10Y_Y", "IL10Y_Y", "TR10Y_Y"]:
            if k in sov_series:
                spread_name = k.replace("_Y", "_SPREAD")
                sp = (sov_series[k] - us).rename(spread_name)
                series_list.append(sp)
                meta["sources"][spread_name] = {
                    "source": "computed",
                    "formula": f"{k} - US10Y_Y",
                    "status": "OK",
                }
    else:
        meta["sources"]["SOV_SPREADS"] = {
            "source": "computed",
            "status": "SKIPPED (missing US10Y_Y)",
        }

    # -----------------------------
    # 4) Build final dataframe
    # -----------------------------
    if not series_list:
        raise RuntimeError("No series collected from both yfinance and FRED. (series_list empty)")

    df_idx = pd.concat(series_list, axis=1, sort=False)
    df_idx.index = pd.to_datetime(df_idx.index, errors="coerce")
    df_idx = df_idx[~df_idx.index.isna()].sort_index()
    df_idx.index.name = "date"
    out = df_idx.reset_index()

    # numeric + sort
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    for c in out.columns:
        if c == "date":
            continue
        out[c] = pd.to_numeric(out[c], errors="coerce")

    # ✅ spreads는 매일 안 나올 수 있으니 forward-fill
    spread_cols = [c for c in out.columns if c.endswith("_SPREAD")]
    for c in spread_cols:
        out[c] = out[c].ffill()

    out.to_csv(OUT_CSV, index=False)
    META_JSON.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[OK] wrote: {OUT_CSV} (rows={len(out)})")
    print(f"[OK] meta : {META_JSON}")


if __name__ == "__main__":
    main()
