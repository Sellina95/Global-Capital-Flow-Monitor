import pandas as pd
import yfinance as yf
from pathlib import Path

# =========================
# OUTPUT PATH (절대 여기로 고정)
# =========================
BASE_DIR = Path(__file__).resolve().parents[2]
OUT_PATH = BASE_DIR / "data" / "backtest" / "macro_data_2008.csv"

# =========================
# FULL MACRO UNIVERSE (너가 준 리스트 그대로 반영)
# =========================
TICKERS = {
    # Rates / Macro
    "US10Y": "^TNX",
    "DXY": "DX-Y.NYB",
    "WTI": "CL=F",
    "VIX": "^VIX",
    "VIX3M": "^VIX3M",

    # FX
    "USDKRW": "KRW=X",
    "USDCNH": "CNH=X",
    "USDJPY": "JPY=X",
    "USDMXN": "MXN=X",

    # US Equity
    "SPY": "SPY",
    "QQQ": "QQQ",
    "IWM": "IWM",
    "RSP": "RSP",

    # Sector
    "XLK": "XLK",
    "XLF": "XLF",
    "XLE": "XLE",
    "XLI": "XLI",
    "XLY": "XLY",
    "XLV": "XLV",
    "XLU": "XLU",
    "XLRE": "XLRE",

    # Tech / Semis
    "SMH": "SMH",
    "SOXX": "SOXX",

    # Credit
    "HYG": "HYG",
    "LQD": "LQD",
    "EMB": "EMB",

    # Global Equity
    "EEM": "EEM",
    "ITA": "ITA",

    # Commodities
    "GOLD": "GC=F",
}

# =========================
# DOWNLOAD FUNCTION (절대 안전 버전)
# =========================
def fetch(ticker):
    import yfinance as yf  # 🔥 로컬 고정 (오염 방지)

    df = yf.download(ticker, start="2008-01-01", progress=False)

    if df is None or df.empty:
        print(f"[WARN EMPTY] {ticker}")
        return None

    return df["Close"]

# =========================
# BUILD DATASET
# =========================
def build():
    data = []

    for name, ticker in TICKERS.items():
        print(f"[FETCH] {name} ({ticker})")
        s = fetch(ticker)
        if s is not None:
            data.append(s)

    if len(data) == 0:
        raise Exception("NO DATA DOWNLOADED")

    df = pd.concat(data, axis=1)
    df = df.sort_index()

    return df


# =========================
# MAIN
# =========================
def main():
    df = build()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH)

    print("\n======================")
    print("DONE")
    print(f"SAVED -> {OUT_PATH}")
    print("======================")


if __name__ == "__main__":
    main()