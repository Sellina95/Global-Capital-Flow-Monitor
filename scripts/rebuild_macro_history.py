# scripts/rebuild_macro_history.py
from __future__ import annotations

from pathlib import Path
from datetime import timezone, timedelta
from typing import Dict, List

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "macro_data.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

KST = timezone(timedelta(hours=9))

LOOKBACK_DAYS = 120  # 90을 원하면 90으로 바꿔도 됨 (주말/휴장 감안해서 120 추천)

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

def _download_close(ticker: str) -> pd.Series:
    df = yf.download(
        ticker,
        period=f"{LOOKBACK_DAYS}d",
        interval="1d",
        progress=False,
        auto_adjust=False,
        group_by="column",
        threads=False,
    )
    if df is None or df.empty:
        return pd.Series(dtype="float64")

    # Close 추출 (MultiIndex 방어)
    if isinstance(df.columns, pd.MultiIndex):
        close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
        if not close_cols:
            return pd.Series(dtype="float64")
        s = df[close_cols].iloc[:, -1]
    else:
        if "Close" not in df.columns:
            # 혹시 close 컬럼명이 다른 케이스 방어
            cands = [c for c in df.columns if str(c).lower() == "close"]
            if not cands:
                return pd.Series(dtype="float64")
            s = df[cands[0]]
        else:
            s = df["Close"]

    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return pd.Series(dtype="float64")

    # 날짜 정규화 (일 단위)
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    return s

def main() -> None:
    # 1) 날짜 인덱스부터 만들기 (SPY 기준으로 trading calendar 생성)
    base = _download_close("SPY")
    if base.empty:
        raise RuntimeError("SPY history download failed (empty). yfinance 문제 or 시장 데이터 접근 실패")

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

    # 3) date/datetime 컬럼 생성 (호환성 위해 둘 다)
    # date_key를 문자열로 내보내고, datetime/date를 같은 값으로 채움
    # (generate_report / load_macro_df가 둘 중 하나로도 정상 동작)
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
