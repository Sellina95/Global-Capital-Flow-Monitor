# experiments/geo/fetch_geo_history.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List
from dataclasses import dataclass
from io import BytesIO
import json
import time
import urllib.request
import urllib.error

import pandas as pd
import yfinance as yf


BASE_DIR = Path(__file__).resolve().parents[2]
EXP_DIR = BASE_DIR / "exp_data" / "geo"
OUT_PATH = EXP_DIR / "geo_history.csv"          # (TSV)
META_PATH = EXP_DIR / "sources_meta.json"

START_DATE = "2016-08-16"

# --- network robustness knobs (GitHub Actions friendly) ---
HTTP_TIMEOUT_SEC = 45
RETRIES = 6
BACKOFF_SEC = 2.5

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

# Stooq daily download URL
STOOQ_DL = "https://stooq.com/q/d/l/?s={symbol}&i=d"

# -----------------------------
# Desired output schema / order
# -----------------------------
BASE_COLS_ORDER = [
    "date",
    "VIX", "WTI", "GOLD",
    "USDCNH", "USDJPY", "USDMXN",
    "US10Y_Y", "KR10Y_Y", "JP10Y_Y", "CN10Y_Y", "IL10Y_Y", "TR10Y_Y",
    "EEM", "EMB", "SEA", "BDRY", "ITA", "XAR",
    "KR10Y_SPREAD", "JP10Y_SPREAD", "CN10Y_SPREAD", "IL10Y_SPREAD", "TR10Y_SPREAD",
]

# -----------------------------
# Helpers
# -----------------------------
def _utc_today_str() -> str:
    # Use Timestamp.now('UTC') to avoid deprecated utcnow warnings
    return pd.Timestamp.now("UTC").strftime("%Y-%m-%d")


def _sleep_backoff(i: int) -> None:
    time.sleep(BACKOFF_SEC * (i + 1))


def _http_get_bytes(url: str) -> bytes:
    """
    Robust HTTP GET for GitHub Actions.
    - timeout
    - retries with backoff
    """
    last_err: Optional[Exception] = None
    for i in range(RETRIES):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Global-Capital-Flow-Monitor/1.0 (GitHubActions)",
                    "Accept": "text/csv,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SEC) as resp:
                return resp.read()
        except Exception as e:
            last_err = e
            _sleep_backoff(i)
    raise last_err if last_err else RuntimeError("Unknown HTTP error")


def _looks_like_html(b: bytes) -> bool:
    head = b[:300].lower()
    return (b"<html" in head) or (b"<!doctype html" in head)


def _coerce_series(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    return s


def _normalize_date_index(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).sort_values(date_col)
    df = df.drop_duplicates(subset=[date_col], keep="last")
    df = df.set_index(date_col)
    return df


def _safe_write_meta(meta: Dict[str, Any]) -> None:
    META_PATH.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def _safe_read_existing_geo() -> Optional[pd.DataFrame]:
    if not OUT_PATH.exists() or OUT_PATH.stat().st_size == 0:
        return None
    try:
        # Our experiment writes TSV. Read as TSV first.
        df = pd.read_csv(OUT_PATH, sep="\t")
        if "date" not in df.columns:
            # fallback: sniff
            df = pd.read_csv(OUT_PATH, sep=None, engine="python")
        if "date" not in df.columns:
            return None
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date")
        return df.reset_index(drop=True)
    except Exception:
        return None


# -----------------------------
# Fetchers
# -----------------------------
@dataclass
class FetchResult:
    series: Optional[pd.Series]
    status: str
    error: Optional[str]
    rows: int
    from_date: Optional[str]
    to_date: Optional[str]
    source: str
    ticker_or_id: str


def fetch_fred_series(key: str, series_id: str) -> FetchResult:
    url = f"{FRED_CSV}{series_id}"
    try:
        raw = _http_get_bytes(url)
        if _looks_like_html(raw):
            raise RuntimeError("FRED returned HTML (likely rate-limit/timeout page).")

        df = pd.read_csv(BytesIO(raw))

        # FRED csv typically: DATE,<series_id>
        # Sometimes it may have different first column name; handle robustly.
        if df.shape[1] < 2:
            raise RuntimeError(f"FRED csv has <2 columns (cols={list(df.columns)}).")

        # Pick date col
        date_col = "DATE" if "DATE" in df.columns else df.columns[0]
        val_col = series_id if series_id in df.columns else df.columns[1]

        df = df[[date_col, val_col]].copy()
        df.columns = ["date", key]
        df = _normalize_date_index(df, "date")
        df[key] = _coerce_series(df[key])
        df = df.dropna(subset=[key])

        s = df[key]
        # Keep full history; caller filters by START_DATE
        fr = s.index.min().strftime("%Y-%m-%d") if len(s) else None
        to = s.index.max().strftime("%Y-%m-%d") if len(s) else None
        return FetchResult(series=s, status="OK", error=None, rows=int(len(s)), from_date=fr, to_date=to, source="FRED", ticker_or_id=series_id)
    except Exception as e:
        return FetchResult(series=None, status="ERROR", error=f"{type(e).__name__}: {e}", rows=0, from_date=None, to_date=None, source="FRED", ticker_or_id=series_id)


def _yf_lastclose_series(ticker: str, start: str, end: str) -> pd.Series:
    """
    Download full daily series for [start, end] and return Close as a Series indexed by date.
    """
    df = yf.download(
        ticker,
        start=start,
        end=end,
        interval="1d",
        progress=False,
        group_by="column",
        threads=False,
        auto_adjust=False,
    )
    if df is None or df.empty:
        return pd.Series(dtype="float64")

    # MultiIndex close handling
    if isinstance(df.columns, pd.MultiIndex):
        close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
        if not close_cols:
            return pd.Series(dtype="float64")
        close = df[close_cols]
        # if multiple tickers, take last non-null across columns
        close = close.dropna(how="all")
        if close.empty:
            return pd.Series(dtype="float64")
        s = close.iloc[:, -1]
    else:
        if "Close" not in df.columns:
            return pd.Series(dtype="float64")
        s = df["Close"]

    s = pd.to_numeric(s, errors="coerce").dropna()
    s.index = pd.to_datetime(s.index, errors="coerce")
    s = s.dropna()
    s.name = "close"
    return s


def fetch_yfinance_series(key: str, tickers: List[str], start: str, end: str) -> FetchResult:
    last_err: Optional[str] = None
    for t in tickers:
        try:
            s = _yf_lastclose_series(t, start, end)
            if s is None or s.empty:
                last_err = f"EMPTY for {t}"
                continue
            fr = s.index.min().strftime("%Y-%m-%d")
            to = s.index.max().strftime("%Y-%m-%d")
            s.name = key
            return FetchResult(series=s, status="OK", error=None, rows=int(len(s)), from_date=fr, to_date=to, source="yfinance", ticker_or_id=t)
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            continue
    return FetchResult(series=None, status="ERROR", error=last_err or "Unknown yfinance error", rows=0, from_date=None, to_date=None, source="yfinance", ticker_or_id="|".join(tickers))


def fetch_stooq_series(key: str, symbol: str) -> FetchResult:
    url = STOOQ_DL.format(symbol=symbol)
    try:
        raw = _http_get_bytes(url)
        if _looks_like_html(raw):
            raise RuntimeError("STOOQ returned HTML.")
        df = pd.read_csv(BytesIO(raw))
        # Expected columns: Date,Open,High,Low,Close,Volume
        if "Date" not in df.columns or "Close" not in df.columns:
            raise RuntimeError(f"Unexpected STOOQ schema cols={list(df.columns)[:10]}")
        df = df[["Date", "Close"]].copy()
        df.columns = ["date", key]
        df = _normalize_date_index(df, "date")
        df[key] = _coerce_series(df[key])
        df = df.dropna(subset=[key])
        s = df[key]
        fr = s.index.min().strftime("%Y-%m-%d") if len(s) else None
        to = s.index.max().strftime("%Y-%m-%d") if len(s) else None
        return FetchResult(series=s, status="OK", error=None, rows=int(len(s)), from_date=fr, to_date=to, source="STOOQ", ticker_or_id=symbol)
    except Exception as e:
        return FetchResult(series=None, status="ERROR", error=f"{type(e).__name__}: {e}", rows=0, from_date=None, to_date=None, source="STOOQ", ticker_or_id=symbol)


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    EXP_DIR.mkdir(parents=True, exist_ok=True)

    end_date = _utc_today_str()

    # Build source plan:
    # - Use FRED for yields (and also try for VIX/WTI/GOLD/FX)
    # - If FRED fails, fallback to yfinance for VIX/WTI/GOLD/FX
    # - Use STOOQ for ETFs (works in your log)
    plan: List[Tuple[str, str, Any]] = []

    # FRED-first series
    fred_map = {
        "VIX": "VIXCLS",
        "WTI": "DCOILWTICO",
        "GOLD": "GOLDAMGBD228NLBM",
        "USDJPY": "DEXJPUS",
        "USDMXN": "DEXMXUS",
        "US10Y_Y": "DGS10",
        "KR10Y_Y": "IRLTLT01KRM156N",
        "JP10Y_Y": "IRLTLT01JPM156N",
        "CN10Y_Y": "IRLTLT01CNM156N",
        "IL10Y_Y": "IRLTLT01ILM156N",
        "TR10Y_Y": "IRLTLT01TRM156N",
        # USDCNH: FRED는 onshore(CNY) 성격이라 fallback로만 쓰고, yfinance CNH=X를 우선으로 둘 거야.
        "USDCNH_FRED_FALLBACK": "DEXCHUS",
    }

    # STOOQ ETF symbols (daily)
    stooq_map = {
        "EEM": "eem.us",
        "EMB": "emb.us",
        "SEA": "sea.us",
        "BDRY": "bdry.us",
        "ITA": "ita.us",
        "XAR": "xar.us",
    }

    # yfinance fallbacks (full history)
    yf_map = {
        "VIX": ["^VIX"],
        "WTI": ["CL=F"],
        "GOLD": ["GC=F"],
        "USDJPY": ["JPY=X"],
        "USDMXN": ["MXN=X"],
        # CNH first, then CNY
        "USDCNH": ["CNH=X", "CNY=X"],
    }

    # 1) fetch FRED (except USDCNH main)
    results: Dict[str, FetchResult] = {}
    meta: Dict[str, Any] = {"start": START_DATE, "end": end_date, "sources": {}}

    for key, sid in fred_map.items():
        if key == "USDCNH_FRED_FALLBACK":
            continue
        print(f"[FETCH] {key} <- FRED:{sid}")
        r = fetch_fred_series(key, sid)
        results[key] = r
        meta["sources"][key] = {
            "source": r.source,
            "ticker": r.ticker_or_id,
            "status": r.status,
            "rows": r.rows,
            "error": r.error,
            "from": r.from_date,
            "to": r.to_date,
        }

    # 2) fetch STOOQ ETFs
    for key, sym in stooq_map.items():
        print(f"[FETCH] {key} <- STOOQ:{sym}")
        r = fetch_stooq_series(key, sym)
        results[key] = r
        meta["sources"][key] = {
            "source": r.source,
            "ticker": r.ticker_or_id,
            "status": r.status,
            "rows": r.rows,
            "error": r.error,
            "from": r.from_date,
            "to": r.to_date,
        }

    # 3) USDCNH (yfinance first)
    print("[FETCH] USDCNH <- yfinance:CNH=X (fallback CNY=X)")
    r_cnh = fetch_yfinance_series("USDCNH", yf_map["USDCNH"], START_DATE, end_date)
    if r_cnh.status != "OK":
        # fallback to FRED DEXCHUS if yfinance fails
        sid = fred_map["USDCNH_FRED_FALLBACK"]
        print(f"[FETCH] USDCNH <- FRED:{sid} (fallback)")
        r_f = fetch_fred_series("USDCNH", sid)
        results["USDCNH"] = r_f
        meta["sources"]["USDCNH"] = {
            "source": r_f.source,
            "ticker": r_f.ticker_or_id,
            "status": r_f.status,
            "rows": r_f.rows,
            "error": r_f.error,
            "from": r_f.from_date,
            "to": r_f.to_date,
        }
    else:
        results["USDCNH"] = r_cnh
        meta["sources"]["USDCNH"] = {
            "source": r_cnh.source,
            "ticker": r_cnh.ticker_or_id,
            "status": r_cnh.status,
            "rows": r_cnh.rows,
            "error": r_cnh.error,
            "from": r_cnh.from_date,
            "to": r_cnh.to_date,
        }

    # 4) For the “FRED-first” market series, if FRED failed, fallback to yfinance.
    for key in ["VIX", "WTI", "GOLD", "USDJPY", "USDMXN"]:
        if results.get(key) is None or results[key].status != "OK":
            print(f"[FALLBACK] {key} <- yfinance")
            r2 = fetch_yfinance_series(key, yf_map[key], START_DATE, end_date)
            if r2.status == "OK":
                results[key] = r2
                meta["sources"][key] = {
                    "source": r2.source,
                    "ticker": r2.ticker_or_id,
                    "status": r2.status,
                    "rows": r2.rows,
                    "error": r2.error,
                    "from": r2.from_date,
                    "to": r2.to_date,
                }

    # -----------------------------
    # Assemble dataframe (index=date)
    # -----------------------------
    series_list: List[pd.Series] = []
    for k in BASE_COLS_ORDER:
        if k == "date":
            continue
        # spreads are computed later
        if k.endswith("_SPREAD"):
            continue
        fr = results.get(k)
        if fr is None or fr.status != "OK" or fr.series is None or fr.series.empty:
            continue
        s = fr.series.copy()
        s.name = k
        s.index = pd.to_datetime(s.index, errors="coerce")
        s = s.dropna()
        series_list.append(s)

    if len(series_list) == 0:
        # Nothing fetched -> keep existing file, do NOT zero-out.
        existing = _safe_read_existing_geo()
        if existing is not None and not existing.empty:
            print("[WARN] All series fetch failed. Keeping existing geo_history.csv.")
            _safe_write_meta(meta)
            return
        # no existing -> write skeleton
        empty = pd.DataFrame(columns=BASE_COLS_ORDER)
        empty.to_csv(OUT_PATH, sep="\t", index=False, encoding="utf-8")
        _safe_write_meta(meta)
        print(f"[OK] wrote empty skeleton: {OUT_PATH} (rows=0)")
        return

    df = pd.concat(series_list, axis=1, sort=True)
    df = df.sort_index()

    # filter start/end
    df = df.loc[pd.to_datetime(START_DATE): pd.to_datetime(end_date)]

    # Ensure columns exist (even if missing)
    for col in BASE_COLS_ORDER:
        if col == "date":
            continue
        if col.endswith("_SPREAD"):
            continue
        if col not in df.columns:
            df[col] = pd.NA

    # Compute spreads if yields exist
    def _spread(cc: str) -> str:
        return f"{cc}10Y_SPREAD"

    if "US10Y_Y" in df.columns:
        us = pd.to_numeric(df["US10Y_Y"], errors="coerce")
        for cc in ["KR", "JP", "CN", "IL", "TR"]:
            ycol = f"{cc}10Y_Y"
            scol = f"{cc}10Y_SPREAD"
            if ycol in df.columns:
                yy = pd.to_numeric(df[ycol], errors="coerce")
                df[scol] = yy - us
            else:
                df[scol] = pd.NA
    else:
        for cc in ["KR", "JP", "CN", "IL", "TR"]:
            df[f"{cc}10Y_SPREAD"] = pd.NA

    # reset index -> date column (NO KeyError ever)
    out = df.reset_index().rename(columns={"index": "date"})
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date")
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")

    # enforce final column order
    for col in BASE_COLS_ORDER:
        if col not in out.columns:
            out[col] = pd.NA
    out = out[BASE_COLS_ORDER]

    # If out is empty, keep existing
    if out.empty:
        existing = _safe_read_existing_geo()
        if existing is not None and not existing.empty:
            print("[WARN] geo_history result empty after merge/filter. Keeping existing geo_history.csv.")
            _safe_write_meta(meta)
            return

    # Save as TSV (consistent with earlier logs)
    out.to_csv(OUT_PATH, sep="\t", index=False, encoding="utf-8")
    _safe_write_meta(meta)

    print(f"[OK] wrote: {OUT_PATH} (rows={len(out)})")
    print(f"[OK] meta : {META_PATH}")


if __name__ == "__main__":
    main()
