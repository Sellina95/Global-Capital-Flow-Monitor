# experiments/geo/fetch_geo_history.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import yfinance as yf

# =========================
# Paths
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
OUT_CSV = EXP_DATA_DIR / "geo_history.csv"
META_JSON = EXP_DATA_DIR / "sources_meta.json"

# =========================
# Settings
# =========================
DAYS_DEFAULT = 1200
START_DEFAULT = "2018-01-01"  # ✅ period 대신 start 강제 (ticker별 시작시점 꼬임 방지)
MIN_ROWS_OK = 200            # ✅ 이 정도는 있어야 "쓸만한 히스토리"로 인정

# =========================
# Source universe (Geo EW v2 baseline)
# - 각 key는 geo_history.csv 컬럼명이 됨
# - value는 yfinance ticker 후보들(첫 성공값 사용)
# =========================
YF_SOURCES: Dict[str, List[str]] = {
    # Market reaction
    "VIX": ["^VIX"],
    "WTI": ["CL=F"],
    "GOLD": ["GC=F"],

    # FX stress / geopolitics
    # ✅ CNH=X가 가끔 1줄만 오는 이슈가 있어서 후보 2개
    "USDCNH": ["CNH=X", "USDCNH=X"],
    "USDJPY": ["JPY=X"],
    "USDMXN": ["MXN=X"],

    # Capital flow proxies
    "EEM": ["EEM"],
    "EMB": ["EMB"],

    # Supply chain / shipping
    "SEA": ["SEA"],
    "BDRY": ["BDRY"],

    # Defense attention
    "ITA": ["ITA"],
    "XAR": ["XAR"],
}

# =========================
# Helpers
# =========================
def _extract_close_series(dl: pd.DataFrame, ticker: str) -> pd.Series:
    """
    yfinance download 결과에서 "Adj Close" 우선, 없으면 "Close"로 시리즈 추출.
    yfinance는 단일/멀티티커에 따라 컬럼이:
      - 단일: columns=['Open','High','Low','Close','Adj Close','Volume']
      - 멀티: columns=MultiIndex([('Adj Close','EEM'),...])
    """
    if dl is None or dl.empty:
        return pd.Series(dtype="float64")

    # MultiIndex columns
    if isinstance(dl.columns, pd.MultiIndex):
        # prefer Adj Close
        for field in ["Adj Close", "Close"]:
            if (field, ticker) in dl.columns:
                s = dl[(field, ticker)].copy()
                s.name = ticker
                return pd.to_numeric(s, errors="coerce")
        # fallback: first column of that ticker if exists
        cols = [c for c in dl.columns if len(c) == 2 and c[1] == ticker]
        if cols:
            s = dl[cols[0]].copy()
            s.name = ticker
            return pd.to_numeric(s, errors="coerce")

    # SingleIndex columns
    for field in ["Adj Close", "Close"]:
        if field in dl.columns:
            s = dl[field].copy()
            s.name = ticker
            return pd.to_numeric(s, errors="coerce")

    # fallback: try any numeric column
    for c in dl.columns:
        if str(c).lower() in ("close", "adj close", "adj_close"):
            s = dl[c].copy()
            s.name = ticker
            return pd.to_numeric(s, errors="coerce")

    return pd.Series(dtype="float64")


def _download_one(tickers: List[str], start: str) -> Tuple[Optional[pd.Series], Dict[str, Any]]:
    """
    tickers 후보 리스트 중에서:
    - 데이터가 충분히(>=MIN_ROWS_OK) 있는 첫 ticker 채택
    - 모두 실패하면: 가장 "rows 많은" ticker라도 반환(단 rows==0이면 None)
    """
    meta_attempts: List[Dict[str, Any]] = []
    best_series: Optional[pd.Series] = None
    best_rows = 0
    best_ticker = None
    best_error = None

    for t in tickers:
        try:
            dl = yf.download(
                t,
                start=start,
                interval="1d",
                progress=False,
                auto_adjust=False,
                group_by="column",
                threads=True,
            )
            s = _extract_close_series(dl, t)
            s = s.dropna()
            rows = int(len(s))

            info = {
                "ticker": t,
                "rows": rows,
                "status": "OK" if rows > 0 else "EMPTY",
                "from": str(s.index.min().date()) if rows > 0 else None,
                "to": str(s.index.max().date()) if rows > 0 else None,
                "error": None,
            }
            meta_attempts.append(info)

            # 즉시 합격
            if rows >= MIN_ROWS_OK:
                best_series = s
                best_rows = rows
                best_ticker = t
                best_error = None
                break

            # 후보 중 최대 rows 저장
            if rows > best_rows:
                best_series = s
                best_rows = rows
                best_ticker = t
                best_error = None

        except Exception as e:
            best_error = str(e)
            meta_attempts.append({
                "ticker": t,
                "rows": 0,
                "status": "ERROR",
                "from": None,
                "to": None,
                "error": str(e),
            })

    # 최종 meta
    status = "OK" if (best_series is not None and best_rows > 0) else "EMPTY"
    meta = {
        "status": status,
        "ticker_used": best_ticker,
        "rows": best_rows,
        "from": str(best_series.index.min().date()) if (best_series is not None and best_rows > 0) else None,
        "to": str(best_series.index.max().date()) if (best_series is not None and best_rows > 0) else None,
        "error": best_error,
        "attempts": meta_attempts,
    }

    if best_series is None or best_rows == 0:
        return None, meta

    return best_series, meta


def main() -> None:
    EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    days = DAYS_DEFAULT
    start = START_DEFAULT

    meta_out: Dict[str, Any] = {
        "generated_at_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "days": days,
        "start": start,
        "sources": {},
    }

    series_list: List[pd.Series] = []

    for col, tickers in YF_SOURCES.items():
        print(f"[FETCH] {col} <- {tickers[0] if tickers else 'N/A'}")
        s, meta = _download_one(tickers, start=start)
        meta_out["sources"][col] = {
            "source": "yfinance",
            **meta,
        }

        if s is None or s.empty:
            continue

        # ✅ 여기서 절대 df.rename(col) 같은 거 안함
        s = s.copy()
        s.name = col  # ✅ 컬럼명은 "col"로 고정
        series_list.append(s)

    if not series_list:
        # 그래도 파일은 만들어서 파이프라인이 죽지 않게
        empty = pd.DataFrame({"date": []})
        empty.to_csv(OUT_CSV, index=False, encoding="utf-8")
        with META_JSON.open("w", encoding="utf-8") as f:
            json.dump(meta_out, f, ensure_ascii=False, indent=2)
        print(f"[WARN] No series downloaded. Wrote empty: {OUT_CSV}")
        return

    # ✅ concat 안정: sort=True로 warning 제거 + outer join
    df = pd.concat(series_list, axis=1, join="outer", sort=True)

    # ✅ 인덱스(date) -> 컬럼(date)
    out = df.reset_index()
    # reset_index() 결과 컬럼명이 "Date" 또는 "index"일 수 있어 둘 다 처리
    if "Date" in out.columns:
        out = out.rename(columns={"Date": "date"})
    elif "index" in out.columns:
        out = out.rename(columns={"index": "date"})

    # ✅ 여기서 KeyError('date') 절대 안 나게 방어
    if "date" not in out.columns:
        # 최후의 방어: 첫 컬럼을 date로 강제
        out = out.rename(columns={out.columns[0]: "date"})

    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")

    # 날짜를 YYYY-MM-DD로 통일
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")

    # ✅ 저장
    out.to_csv(OUT_CSV, index=False, encoding="utf-8")
    with META_JSON.open("w", encoding="utf-8") as f:
        json.dump(meta_out, f, ensure_ascii=False, indent=2)

    print(f"[OK] wrote: {OUT_CSV} (rows={len(out)})")
    print(f"[OK] meta : {META_JSON}")


if __name__ == "__main__":
    main()
