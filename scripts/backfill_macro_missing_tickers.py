#macro_data.csv 파일에 특정 티커 과거데이터가 없을시 아래 티커에 넣고 돌리면 생성
import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


MACRO_PATH = "data/macro_data.csv"
START_DATE = "2022-01-01"

BACKFILL_TICKERS = {
    "RSP": "RSP",
    "QQQE": "QQQE",
    "SMH": "SMH",
    "SOXX": "SOXX",
    "IWM": "IWM",
    "XLI": "XLI",
    "XLY": "XLY",
    "VIX3M": "^VIX3M",
    "VIX9D": "^VIX9D",
}


def load_macro_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"[ERROR] Macro data file not found: {path}")

    df = pd.read_csv(path)

    if "date" not in df.columns:
        raise ValueError("[ERROR] macro_data.csv must contain a 'date' column.")

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df = df.sort_index()

    return df


def fetch_backfill_data() -> pd.DataFrame:
    end_date = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

    fetched = pd.DataFrame()

    for column_name, yahoo_ticker in BACKFILL_TICKERS.items():
        try:
            raw = yf.download(
                yahoo_ticker,
                start=START_DATE,
                end=end_date,
                auto_adjust=True,
                progress=False,
                threads=False,
            )

            if raw.empty:
                print(f"[WARN] No data returned for {column_name} ({yahoo_ticker})")
                continue

            if isinstance(raw.columns, pd.MultiIndex):
                close = raw["Close"].iloc[:, 0]
            else:
                close = raw["Close"]

            close.index = pd.to_datetime(close.index).tz_localize(None)
            fetched[column_name] = close

            print(f"[OK] fetched {column_name} from {yahoo_ticker}")

        except Exception as e:
            print(f"[WARN] failed to fetch {column_name} ({yahoo_ticker}): {e}")

    fetched.index.name = "date"
    fetched = fetched.sort_index()

    return fetched


def merge_backfill(macro_df: pd.DataFrame, backfill_df: pd.DataFrame) -> pd.DataFrame:
    merged = macro_df.copy()

    for col in BACKFILL_TICKERS.keys():
        if col not in merged.columns:
            merged[col] = pd.NA

    for col in backfill_df.columns:
        # 기존 값 유지 + 비어 있는 과거값 채우기 + 최신 fetch 값으로 갱신
        merged[col] = merged[col].combine_first(backfill_df[col])
        merged[col].update(backfill_df[col])

    merged = merged.sort_index()
    merged = merged[~merged.index.duplicated(keep="last")]

    return merged


def restore_datetime_column(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()

    output.index = pd.to_datetime(output.index)
    output.index.name = "date"

    output = output.reset_index()

    if "datetime" not in output.columns:
        output.insert(0, "datetime", output["date"])

    output["datetime"] = pd.to_datetime(output["datetime"]).dt.strftime("%Y-%m-%d")
    output["date"] = pd.to_datetime(output["date"]).dt.strftime("%Y-%m-%d")

    return output


def main() -> None:
    macro_df = load_macro_data(MACRO_PATH)
    backfill_df = fetch_backfill_data()

    if backfill_df.empty:
        raise ValueError("[ERROR] Backfill returned empty dataframe.")

    merged = merge_backfill(macro_df, backfill_df)
    output = restore_datetime_column(merged)

    output.to_csv(MACRO_PATH, index=False)

    print("[OK] macro_data.csv backfill completed")
    print(f"- path: {MACRO_PATH}")
    print(f"- rows: {len(output)}")
    print(f"- columns backfilled: {list(BACKFILL_TICKERS.keys())}")
    print(f"- start: {output['date'].min()}")
    print(f"- end: {output['date'].max()}")


if __name__ == "__main__":
    main()