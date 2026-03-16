import pandas as pd
import yfinance as yf
from datetime import datetime

START_DATE = "2022-01-01"
END_DATE = datetime.today().strftime("%Y-%m-%d")

# -----------------------------------------
# Main ticker map
# -----------------------------------------

YAHOO_TICKERS = {

    # Core Macro
    "US10Y": "^TNX",
    "DXY": "UUP",
    "WTI": "CL=F",
    "VIX": "^VIX",
    "USDKRW": "KRW=X",

    # Credit / Liquidity
    "HYG": "HYG",
    "LQD": "LQD",

    # Sector leadership
    "XLK": "XLK",
    "XLF": "XLF",
    "XLE": "XLE",
    "XLRE": "XLRE",

    # Broad market
    "QQQ": "QQQ",
    "SPY": "SPY",

    # Commodities
    "GOLD": "GC=F",

    # FX
    "USDCNH": "CNH=X",
    "USDJPY": "JPY=X",
    "USDMXN": "MXN=X",

    # Geo / Supply Chain proxies
    "SEA": "SEA",
    "BDRY": "BDRY",
    "ITA": "ITA",
    "XAR": "XAR",

    # EM stress
    "EEM": "EEM",
    "EMB": "EMB",
}

# -----------------------------------------
# Fallback ticker
# -----------------------------------------

FALLBACK_TICKERS = {
    "USDCNH": ["CNY=X"]
}

# -----------------------------------------
# Download function
# -----------------------------------------

def download_yahoo_series(ticker, start, end):

    df = yf.download(
        ticker,
        start=start,
        end=end,
        auto_adjust=False,
        progress=False
    )

    if df.empty:
        raise ValueError("No data")

    if "Adj Close" in df.columns:
        s = df["Adj Close"]
    else:
        s = df["Close"]

    return s


# -----------------------------------------
# Build full index
# -----------------------------------------

full_index = pd.date_range(start=START_DATE, end=END_DATE, freq="D")

macro_df = pd.DataFrame(index=full_index)


# -----------------------------------------
# Download loop
# -----------------------------------------

for col, ticker in YAHOO_TICKERS.items():

    try:

        s = download_yahoo_series(ticker, START_DATE, END_DATE)

        s.index = pd.to_datetime(s.index).normalize()

        macro_df[col] = s.reindex(full_index)

        print(f"[OK] Yahoo - {col}")

    except Exception:

        # fallback
        if col in FALLBACK_TICKERS:

            success = False

            for alt in FALLBACK_TICKERS[col]:

                try:

                    s = download_yahoo_series(alt, START_DATE, END_DATE)

                    s.index = pd.to_datetime(s.index).normalize()

                    macro_df[col] = s.reindex(full_index)

                    print(f"[OK] Fallback - {col} -> {alt}")

                    success = True

                    break

                except Exception:
                    pass

            if not success:

                macro_df[col] = pd.NA

                print(f"[ERROR] Yahoo - {col}")

        else:

            macro_df[col] = pd.NA

            print(f"[ERROR] Yahoo - {col}")


# -----------------------------------------
# Format date columns
# -----------------------------------------

macro_df = macro_df.reset_index()

macro_df.rename(columns={"index": "date"}, inplace=True)

macro_df["datetime"] = macro_df["date"].dt.strftime("%Y-%m-%d")

macro_df["date"] = macro_df["date"].dt.strftime("%Y-%m-%d")


# -----------------------------------------
# Column order
# -----------------------------------------

macro_df = macro_df[[
    "datetime","date",
    "US10Y","DXY","WTI","VIX","USDKRW",
    "HYG","LQD",
    "XLK","XLF","XLE","XLRE",
    "QQQ","SPY",
    "GOLD",
    "USDCNH","USDJPY","USDMXN",
    "SEA","BDRY","ITA","XAR",
    "EEM","EMB"
]]


# -----------------------------------------
# Save
# -----------------------------------------

macro_df.to_csv(
    "macro_data_full_test.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Saved: macro_data_full_test.csv")