from pathlib import Path

import pandas as pd
import yfinance as yf


BASE_PATH = Path("data/backtest/macro_data_2008.csv")
OUT_PATH = Path("data/backtest/country_etf_data_combined.csv")

BASE_TICKERS = ["SPY", "EEM", "EMB"]
DOWNLOAD_TICKERS = ["EIS", "GLD", "VXX", "FXI", "EWJ", "BND"]


def fetch_adjusted_close(ticker: str, start: str, end: str) -> pd.Series:
    hist = yf.Ticker(ticker).history(
        start=start,
        end=end,
        auto_adjust=True,
    )

    if hist.empty or "Close" not in hist.columns:
        print(f"[WARN] {ticker}: no data")
        return pd.Series(dtype=float, name=ticker)

    series = hist["Close"].copy()
    series.index = pd.to_datetime(series.index).tz_localize(None)
    series.name = ticker

    print(
        f"[OK] {ticker}: "
        f"{series.index.min().date()} ~ {series.index.max().date()} "
        f"({len(series):,} rows)"
    )
    return series


def main() -> None:
    base = pd.read_csv(BASE_PATH)

    required = ["Date", *BASE_TICKERS]
    missing = [c for c in required if c not in base.columns]
    if missing:
        raise ValueError(f"Missing columns in {BASE_PATH}: {missing}")

    base["Date"] = pd.to_datetime(base["Date"], errors="coerce")
    base = (
        base[required]
        .dropna(subset=["Date"])
        .drop_duplicates("Date", keep="last")
        .sort_values("Date")
        .set_index("Date")
    )

    start = base.index.min().strftime("%Y-%m-%d")
    end = (base.index.max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    out = base.copy()

    for ticker in DOWNLOAD_TICKERS:
        out = out.join(fetch_adjusted_close(ticker, start, end), how="left")

    ordered = [
        "EIS",
        "SPY",
        "EEM",
        "EMB",
        "GLD",
        "VXX",
        "FXI",
        "EWJ",
        "BND",
    ]

    out = out[ordered].reset_index()
    out["Date"] = out["Date"].dt.strftime("%Y-%m-%d")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    print(f"\nSaved: {OUT_PATH}")
    print(f"Period: {out['Date'].min()} ~ {out['Date'].max()}")
    print(f"Rows: {len(out):,}")

    print("\nFirst valid date:")
    for col in ordered:
        valid = out.loc[out[col].notna(), "Date"]
        first = valid.iloc[0] if not valid.empty else "NO DATA"
        print(f"{col}: {first}")

    print("\nMissing counts:")
    print(out[ordered].isna().sum().to_string())


if __name__ == "__main__":
    main()
