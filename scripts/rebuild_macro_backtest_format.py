from pathlib import Path

import numpy as np
import pandas as pd


INPUT_PATH = Path("data/backtest/macro_data_2008.csv")
OUTPUT_PATH = Path("data/backtest/macro_data.csv")


COLUMN_MAP = {
    "Date": "date",
    "^TNX": "US10Y",
    "DX-Y.NYB": "DXY",
    "CL=F": "WTI",
    "^VIX": "VIX",
    "^VIX3M": "VIX3M",
    "KRW=X": "USDKRW",
    "CNH=X": "USDCNH",
    "JPY=X": "USDJPY",
    "MXN=X": "USDMXN",
    "GC=F": "GOLD",
}


OUTPUT_COLUMNS = [
    "date",
    "datetime",
    "US10Y",
    "DXY",
    "WTI",
    "VIX",
    "USDKRW",
    "HYG",
    "LQD",
    "XLK",
    "XLF",
    "XLE",
    "XLRE",
    "QQQ",
    "SPY",
    "XLI",
    "XLY",
    "RSP",
    "QQQE",
    "SMH",
    "SOXX",
    "IWM",
    "VIX3M",
    "VIX9D",
    "GOLD",
    "USDCNH",
    "USDJPY",
    "USDMXN",
    "SEA",
    "BDRY",
    "ITA",
    "XAR",
    "EEM",
    "EMB",
]


def main() -> None:
    df = pd.read_csv(INPUT_PATH)

    df = df.rename(columns=COLUMN_MAP)

    if "date" not in df.columns:
        raise ValueError("date column missing after rename")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = (
        df.dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates("date", keep="last")
        .reset_index(drop=True)
    )

    df["datetime"] = df["date"]

    # 운영 형식에는 있으나 2008 원본에 없는 컬럼
    missing_as_nan = ["QQQE", "VIX9D", "SEA", "BDRY", "XAR"]

    for col in missing_as_nan:
        if col not in df.columns:
            df[col] = np.nan

    # 혹시 다른 운영 컬럼이 비어 있어도 구조는 유지
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    out = df[OUTPUT_COLUMNS].copy()

    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out["datetime"] = pd.to_datetime(out["datetime"], errors="coerce").dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved: {OUTPUT_PATH}")
    print(f"Period: {out['date'].min()} ~ {out['date'].max()}")
    print(f"Rows: {len(out):,}")
    print("\nColumns:")
    print(list(out.columns))
    print("\nHead:")
    print(out.head(3).to_string(index=False))
    print("\nMissing counts:")
    print(out.isna().sum().to_string())


if __name__ == "__main__":
    main()
