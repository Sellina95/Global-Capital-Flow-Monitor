# scripts/rebuild_macro_history.py
from __future__ import annotations

from pathlib import Path
from datetime import timezone, timedelta
from typing import Dict, List, Optional
import time

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "macro_data.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KST = timezone(timedelta(hours=9))

LOOKBACK_DAYS = 120  # 90을 원하면 90으로 바꿔도 됨 (주말/휴장 감안해서 120 추천)
MAX_RETRIES = 3
RETRY_SLEEP_SEC = 2

INDICATORS: Dict[str, str] = {
    "US10Y": "^TNX",
    "DXY": "DX-Y.NYB",
    "WTI": "CL=F",
    "VIX": "^VIX",
    "USDKRW": "KRW=X",
    "HYG": "HYG",
    "LQD": "LQD",

    "XLK": "XLK",
    "XLF": "XLF",
    "XLE": "XLE",
    "XLRE": "XLRE",

    "QQQ": "QQQ",
    "SPY": "SPY",

    "GOLD": "GC=F",
    "USDCNH": "CNH=X",
    "USDJPY": "JPY=X",
    "USDMXN": "MXN=X",

    "SEA": "SEA",
    "BDRY": "BDRY",
    "ITA": "ITA",
    "XAR": "XAR",
    "EEM": "EEM",
    "EMB": "EMB",
}

# 캘린더 기준 대체 후보
CALENDAR_CANDIDATES: List[str] = [
    "SPY",
    "QQQ",
    "HYG",
    "LQD",
    "XLK",
    "XLF",
]

def _extract_close_series(df: pd.DataFrame) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype="float64")

    # Close 추출 (MultiIndex 방어)
    if isinstance(df.columns, pd.MultiIndex):
        close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
        if not close_cols:
            return pd.Series(dtype="float64")
        s = df[close_cols].iloc[:, -1]
    else:
        if "Close" in df.columns:
            s = df["Close"]
        else:
            cands = [c for c in df.columns if str(c).lower() == "close"]
            if not cands:
                return pd.Series(dtype="float64")
            s = df[cands[0]]

    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return pd.Series(dtype="float64")

    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s


def _download_close_once(ticker: str) -> pd.Series:
    df = yf.download(
        ticker,
        period=f"{LOOKBACK_DAYS}d",
        interval="1d",
        progress=False,
        auto_adjust=False,
        group_by="column",
        threads=False,
    )
    return _extract_close_series(df)


def _download_close_fallback(ticker: str) -> pd.Series:
    try:
        hist = yf.Ticker(ticker).history(
            period=f"{LOOKBACK_DAYS}d",
            interval="1d",
            auto_adjust=False,
        )
        return _extract_close_series(hist)
    except Exception as e:
        print(f"[FALLBACK-ERROR] {ticker}: {e}")
        return pd.Series(dtype="float64")


def _download_close(ticker: str) -> pd.Series:
    """
    Retry + fallback 내장 다운로드
    """
    last_error: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            s = _download_close_once(ticker)
            if not s.empty:
                if attempt > 1:
                    print(f"[RETRY-SUCCESS] {ticker} succeeded on attempt {attempt}")
                return s
        except Exception as e:
            last_error = e
            print(f"[RETRY] {ticker} attempt {attempt}/{MAX_RETRIES} failed: {e}")

        time.sleep(RETRY_SLEEP_SEC)

    # fallback
    print(f"[FALLBACK] trying Ticker().history for {ticker}")
    s = _download_close_fallback(ticker)
    if not s.empty:
        return s

    if last_error is not None:
        print(f"[FINAL-FAIL] {ticker}: {last_error}")
    return pd.Series(dtype="float64")


def _build_calendar_base() -> pd.Series:
    """
    SPY 단일 실패로 죽지 않도록 캘린더 기준 대체 후보 순차 시도
    """
    for ticker in CALENDAR_CANDIDATES:
        print(f"[CALENDAR] trying base ticker: {ticker}")
        s = _download_close(ticker)
        if not s.empty:
            print(f"[CALENDAR] using {ticker} as base calendar ({len(s)} rows)")
            return s

    return pd.Series(dtype="float64")


def main() -> None:
    # 1) 날짜 인덱스부터 만들기 (SPY 단일 의존 제거)
    base = _build_calendar_base()
    if base.empty:
        raise RuntimeError(
            "Base calendar build failed. SPY/QQQ/HYG/LQD/XLK/XLF 모두 다운로드 실패"
        )

    out = pd.DataFrame(index=base.index)
    out.index.name = "date_key"

    # 2) 모든 지표 다운로드해서 날짜에 맞춰 붙이기
    for col, ticker in INDICATORS.items():
        print(f"[FETCH] {col} ({ticker}) ...")
        s = _download_close(ticker)
        if s.empty:
            print(f"  -> empty, kept as NaN")
            out[col] = pd.NA
            continue
        out[col] = s

    # 3) date/datetime 컬럼 생성
    out = out.reset_index()
    out["datetime"] = out["date_key"].dt.strftime("%Y-%m-%d %H:%M:%S")
    out["date"] = out["datetime"]

    # 컬럼 순서 정리
    ordered_cols: List[str] = ["datetime", "date"] + [k for k in INDICATORS.keys()]
    out = out[ordered_cols]

    # 4) 기존 파일 백업 후 저장
    if CSV_PATH.exists():
        bak = CSV_PATH.with_suffix(".csv.bak")
        CSV_PATH.replace(bak)
        print(f"[OK] existing macro_data.csv backed up -> {bak}")

    out.to_csv(CSV_PATH, index=False)
    print(f"[DONE] rebuilt macro_data.csv rows={len(out)} -> {CSV_PATH}")


if __name__ == "__main__":
    main()