# scripts/fetch_macro_data.py
from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime

import pandas as pd
import yfinance as yf


# ===== 1) Paths =====
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "macro_data.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ===== 2) Tickers =====
INDICATORS = {
    "US10Y": "^TNX",      # US 10Y yield (Yahoo: TNX is yield*10; you already handle as-is)
    "DXY": "DX-Y.NYB",    # Dollar Index
    "WTI": "CL=F",        # WTI Crude
    "VIX": "^VIX",        # VIX
    "USDKRW": "KRW=X",    # USD/KRW
    # (추가 지표가 있으면 여기만 늘리면 됨: "HYG": "HYG", "LQD": "LQD" ...)
}

def _extract_last_close(hist: pd.DataFrame, ticker: str) -> float:
    """
    yfinance 결과가 어떤 형태로 와도 마지막 Close 값을 'float 1개'로 확정해서 반환.
    """
    if hist is None or hist.empty:
        raise ValueError(f"{ticker}: empty history")

    if "Close" not in hist.columns:
        raise ValueError(f"{ticker}: 'Close' column missing. cols={list(hist.columns)}")

    close = hist["Close"]

    # Case A) close가 Series인 경우 (정상)
    if isinstance(close, pd.Series):
        val = close.dropna().iloc[-1]
        return float(val)

    # Case B) close가 DataFrame인 경우 (멀티 인덱스/특이 케이스)
    if isinstance(close, pd.DataFrame):
        last_row = close.dropna(how="all").iloc[-1]   # Series
        # 여러 컬럼이면 첫 번째 유효값을 선택
        for v in last_row.tolist():
            if pd.notna(v):
                return float(v)
        raise ValueError(f"{ticker}: Close row exists but all NaN")

    # Case C) 예상 밖 타입
    raise TypeError(f"{ticker}: unexpected Close type: {type(close)}")


def fetch_macro_data() -> dict:
    results: dict[str, float] = {}

    for name, ticker in INDICATORS.items():
        print(f"Fetching {name} ({ticker}) ...")

        # yf.download보다 Ticker().history가 단일 티커에서 더 안정적임
        hist = yf.Ticker(ticker).history(period="5d")  # 최근 5영업일에서 마지막 값
        value = _extract_last_close(hist, ticker)

        results[name] = value
        print(f"  → {name}: {value}")

    return results


def append_to_csv(values: dict) -> None:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {"datetime": now}
    row.update(values)

    df_row = pd.DataFrame([row])

    file_exists = CSV_PATH.exists()
    df_row.to_csv(CSV_PATH, mode="a", index=False, header=not file_exists)

    print(f"\n✅ Saved row to {CSV_PATH}")
    print(df_row)


if __name__ == "__main__":
    vals = fetch_macro_data()
    append_to_csv(vals)
