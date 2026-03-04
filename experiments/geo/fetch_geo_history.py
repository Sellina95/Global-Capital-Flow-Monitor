# experiments/geo/fetch_geo_history.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd

# yfinance는 requirements.txt에 이미 있다고 가정
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
OUT_CSV = EXP_DATA_DIR / "geo_history.csv"
META_JSON = EXP_DATA_DIR / "sources_meta.json"

# ---------
# Config
# ---------
DEFAULT_DAYS = 1200  # 넉넉히 (대략 3~5년 커버). 필요하면 늘려도 됨.

# 실험용: 네가 지금 test_geo_events.py에서 쓰는 최소 컬럼 + (추가하면 여기서 늘려도 됨)
# key: output column, value: yahoo ticker
YF_SOURCES: Dict[str, str] = {
    "VIX": "^VIX",
    "WTI": "CL=F",
    "USDCNH": "CNH=X",
    "USDJPY": "JPY=X",
    "USDMXN": "MXN=X",
    # "GOLD": "GC=F",   # 원하면 켜
    # "DXY":  "DX-Y.NYB",
}

# -------------------------
# Helpers
# -------------------------
def _ensure_dirs() -> None:
    EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _to_series_close(x: Any, col_name: str) -> Optional[pd.Series]:
    """
    yfinance download 결과가 DataFrame/Series 어떤 형태든
    최종적으로 'date index' + 'values' 인 Series로 정규화.
    """
    if x is None:
        return None

    # case 1) already Series
    if isinstance(x, pd.Series):
        s = x.copy()
        s.name = col_name
        return s

    # case 2) DataFrame
    if isinstance(x, pd.DataFrame):
        df = x.copy()

        # yfinance는 보통 columns = [Open, High, Low, Close, Adj Close, Volume] 형태
        # 또는 멀티컬럼(티커 멀티)일 수도 있음. 여기서는 단일 티커만 요청하므로 단순 처리.
        # 그래도 방어적으로 처리.
        if df.empty:
            return None

        # 멀티인덱스 컬럼이면 Close 레벨 찾아보기
        if isinstance(df.columns, pd.MultiIndex):
            # 예: ('Close', 'AAPL') 이런 형태
            # Close 레벨을 포함하는 컬럼을 우선 선택
            close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
            if close_cols:
                s = df[close_cols[0]].copy()
                s.name = col_name
                return s
            # 못 찾으면 첫 번째 컬럼
            s = df.iloc[:, 0].copy()
            s.name = col_name
            return s

        # 일반 컬럼이면 Close 우선
        close_like = None
        for cand in ["Close", "Adj Close", "close", "adj close"]:
            if cand in df.columns:
                close_like = cand
                break

        if close_like is not None:
            s = df[close_like].copy()
        else:
            s = df.iloc[:, 0].copy()

        # Series로 만들기 + 이름 지정
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        s = pd.to_numeric(s, errors="coerce")
        s.name = col_name
        return s

    # unknown type
    return None


def fetch_yf_series(ticker: str, col_name: str, days: int = DEFAULT_DAYS) -> Tuple[Optional[pd.Series], Dict[str, Any]]:
    """
    Yahoo Finance에서 시계열 다운로드.
    실패해도 전체 파이프라인 안 죽게: (None, meta) 반환.
    """
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
        # df.index = DatetimeIndex
        s = _to_series_close(df, col_name)
        if s is None or s.dropna().empty:
            meta["status"] = "EMPTY"
            meta["rows"] = 0
            return None, meta

        s = s.dropna().copy()
        # 인덱스 정리
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


def main() -> None:
    _ensure_dirs()

    # 1) fetch all series
    series_list: List[pd.Series] = []
    meta_out: Dict[str, Any] = {"days": DEFAULT_DAYS, "sources": {}}

    for col, ticker in YF_SOURCES.items():
        print(f"[FETCH] {col} <- {ticker}")
        s, meta = fetch_yf_series(ticker=ticker, col_name=col, days=DEFAULT_DAYS)
        meta_out["sources"][col] = meta
        if s is not None:
            series_list.append(s)

    # 2) merge
    if not series_list:
        # 파일을 빈 상태로 덮어쓰지 말고, 명확히 실패 처리
        raise RuntimeError("No geo series downloaded (all EMPTY/ERROR). Check tickers or network.")

    df = pd.concat(series_list, axis=1)
    df = df.sort_index()

    # 3) normalize + save
    out = df.reset_index().rename(columns={"index": "date"})
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date")

    # 숫자화
    for c in out.columns:
        if c == "date":
            continue
        out[c] = pd.to_numeric(out[c], errors="coerce")

    # 저장
    out.to_csv(OUT_CSV, index=False)
    META_JSON.write_text(json.dumps(meta_out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] geo_history saved: {OUT_CSV} (rows={len(out)})")
    ok_cols = [c for c in out.columns if c != "date"]
    print(f"[OK] columns: {', '.join(ok_cols)}")
    print(f"[OK] meta saved: {META_JSON}")


if __name__ == "__main__":
    main()
