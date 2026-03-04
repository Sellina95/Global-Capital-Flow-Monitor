# experiments/geo/fetch_geo_history.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
OUT_CSV = EXP_DATA_DIR / "geo_history.csv"
META_JSON = EXP_DATA_DIR / "sources_meta.json"

DEFAULT_DAYS = 1200  # ~3-5년

YF_SOURCES: Dict[str, str] = {
    "VIX": "^VIX",
    "WTI": "CL=F",
    "USDCNH": "CNH=X",
    "USDJPY": "JPY=X",
    "USDMXN": "MXN=X",
    # 필요하면 켜
    # "GOLD": "GC=F",
    # "DXY": "DX-Y.NYB",
}

GEO_DATE_COL = "date"


def _ensure_dirs() -> None:
    EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _to_series_close(x: Any, col_name: str) -> Optional[pd.Series]:
    """
    yfinance download 결과(DataFrame/Series)를
    date index + numeric values Series(name=col_name)로 정규화.
    """
    if x is None:
        return None

    if isinstance(x, pd.Series):
        s = x.copy()
        s.name = col_name
        return s

    if isinstance(x, pd.DataFrame):
        df = x.copy()
        if df.empty:
            return None

        # MultiIndex columns (rare but possible)
        if isinstance(df.columns, pd.MultiIndex):
            close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
            if close_cols:
                s = df[close_cols[0]].copy()
                if isinstance(s, pd.DataFrame):
                    s = s.iloc[:, 0]
                s = pd.to_numeric(s, errors="coerce")
                s.name = col_name
                return s

            s = df.iloc[:, 0].copy()
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]
            s = pd.to_numeric(s, errors="coerce")
            s.name = col_name
            return s

        # Normal columns
        close_col = None
        for cand in ("Close", "Adj Close", "close", "adj close"):
            if cand in df.columns:
                close_col = cand
                break

        s = df[close_col] if close_col is not None else df.iloc[:, 0]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        s = pd.to_numeric(s, errors="coerce")
        s.name = col_name
        return s

    return None


def fetch_yf_series(ticker: str, col_name: str, days: int = DEFAULT_DAYS) -> Tuple[Optional[pd.Series], Dict[str, Any]]:
    meta: Dict[str, Any] = {"source": "yfinance", "ticker": ticker, "status": "INIT", "rows": 0, "error": None}

    try:
        df = yf.download(
            tickers=ticker,
            period=f"{int(days)}d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        s = _to_series_close(df, col_name)
        if s is None or s.dropna().empty:
            meta["status"] = "EMPTY"
            return None, meta

        s = s.dropna().copy()
        s.index = pd.to_datetime(s.index, errors="coerce")
        s = s[~s.index.isna()].sort_index()

        meta["status"] = "OK"
        meta["rows"] = int(len(s))
        meta["from"] = str(s.index.min().date())
        meta["to"] = str(s.index.max().date())
        return s, meta

    except Exception as e:
        meta["status"] = "ERROR"
        meta["error"] = f"{type(e).__name__}: {e}"
        return None, meta


def _reset_index_to_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    df.index(날짜)를 안전하게 'date' 컬럼으로 만들기.
    reset_index() 결과의 첫 컬럼이 뭐로 나오든 무조건 date로 rename.
    """
    out = df.reset_index()

    # ✅ 핵심: 첫번째 컬럼을 무조건 date로 만든다.
    first_col = out.columns[0]
    if first_col != GEO_DATE_COL:
        out = out.rename(columns={first_col: GEO_DATE_COL})

    return out


def main() -> None:
    _ensure_dirs()

    series_list: List[pd.Series] = []
    meta_out: Dict[str, Any] = {"days": DEFAULT_DAYS, "sources": {}}

    for col, ticker in YF_SOURCES.items():
        print(f"[FETCH] {col} <- {ticker}")
        s, meta = fetch_yf_series(ticker=ticker, col_name=col, days=DEFAULT_DAYS)
        meta_out["sources"][col] = meta
        if s is not None:
            series_list.append(s)

    if not series_list:
        raise RuntimeError("No geo series downloaded (all EMPTY/ERROR). Check tickers/network.")

    # ✅ warning 없애고 싶으면 sort=False 명시
    df = pd.concat(series_list, axis=1, sort=False).sort_index()

    out = _reset_index_to_date(df)

    # parse + clean
    out[GEO_DATE_COL] = pd.to_datetime(out[GEO_DATE_COL], errors="coerce")
    out = out.dropna(subset=[GEO_DATE_COL]).sort_values(GEO_DATE_COL)

    # numeric coercion
    for c in out.columns:
        if c == GEO_DATE_COL:
            continue
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out.to_csv(OUT_CSV, index=False)
    META_JSON.write_text(json.dumps(meta_out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] geo_history saved: {OUT_CSV} (rows={len(out)})")
    print(f"[OK] columns: {', '.join([c for c in out.columns if c != GEO_DATE_COL])}")
    print(f"[OK] meta saved: {META_JSON}")


if __name__ == "__main__":
    main()
