import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


START_DATE = "2022-01-01"
OUTPUT_PATH = "data/shadow_etf_data.csv"

SHADOW_ETF_TICKERS = [
    "SPY",
    "QQQ",
    "QQQE",
    "SMH",
    "SOXX",
    "IWM",
    "XLF",
    "XLI",
    "XLY",
    "XLK",
]


def normalize_index(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "date"
    return df


def fetch_prices(start_date: str = START_DATE) -> pd.DataFrame:
    end_date = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

    raw = yf.download(
        SHADOW_ETF_TICKERS,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )

    if raw.empty:
        raise ValueError("[ERROR] No data returned from yfinance.")

    prices = pd.DataFrame()

    for ticker in SHADOW_ETF_TICKERS:
        try:
            if isinstance(raw.columns, pd.MultiIndex):
                if ticker in raw.columns.get_level_values(0):
                    prices[ticker] = raw[ticker]["Close"]
                else:
                    print(f"[WARN] Missing ticker from yfinance result: {ticker}")
            else:
                # fallback for single ticker structure
                prices[ticker] = raw["Close"]
        except Exception as e:
            print(f"[WARN] Failed to parse {ticker}: {e}")

    prices = normalize_index(prices)
    prices = prices.sort_index()
    prices = prices.dropna(how="all")

    return prices


def load_existing(path: str = OUTPUT_PATH) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()

    existing = pd.read_csv(path, parse_dates=["date"])
    existing = existing.set_index("date")
    existing = normalize_index(existing)
    existing = existing.sort_index()

    return existing


def merge_prices(existing: pd.DataFrame, latest: pd.DataFrame) -> pd.DataFrame:
    if existing.empty:
        merged = latest.copy()
    else:
        merged = existing.combine_first(latest)
        merged.update(latest)

    merged = merged.sort_index()
    merged = merged[~merged.index.duplicated(keep="last")]
    merged = merged.dropna(how="all")

    return merged


def main() -> None:
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    existing = load_existing()
    latest = fetch_prices()
    merged = merge_prices(existing, latest)

    merged.to_csv(OUTPUT_PATH, index=True)

    print("[OK] Shadow ETF data updated")
    print(f"- path: {OUTPUT_PATH}")
    print(f"- rows: {len(merged)}")
    print(f"- start: {merged.index.min().date() if not merged.empty else 'N/A'}")
    print(f"- end: {merged.index.max().date() if not merged.empty else 'N/A'}")
    print(f"- columns: {list(merged.columns)}")


if __name__ == "__main__":
    main()