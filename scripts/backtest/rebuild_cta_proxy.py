from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/backtest")
MACRO_PATH = DATA_DIR / "macro_data.csv"
POSITIONING_PATH = DATA_DIR / "positioning_data.csv"
BACKUP_PATH = DATA_DIR / "positioning_data_before_cta_fix.csv"


def main() -> None:
    macro = pd.read_csv(MACRO_PATH)

    # 최초 원본 백업에서 다시 시작
    source_positioning = (
        BACKUP_PATH if BACKUP_PATH.exists() else POSITIONING_PATH
    )
    positioning = pd.read_csv(source_positioning)

    macro["date"] = pd.to_datetime(macro["date"], errors="coerce")
    positioning["date"] = pd.to_datetime(
        positioning["date"],
        errors="coerce",
    )

    macro = (
        macro.dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates("date", keep="last")
        .reset_index(drop=True)
    )

    positioning = (
        positioning.dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates("date", keep="last")
        .reset_index(drop=True)
    )

    # 실제 SPY 거래일만 사용
    spy_all = pd.to_numeric(macro["SPY"], errors="coerce")
    spy_trading = spy_all.dropna()

    ma50_trading = spy_trading.rolling(
        50,
        min_periods=50,
    ).mean()

    ma200_trading = spy_trading.rolling(
        200,
        min_periods=200,
    ).mean()

    cta_trading = pd.Series(
        np.nan,
        index=spy_trading.index,
        dtype=float,
    )

    valid_trading = (
        spy_trading.notna()
        & ma50_trading.notna()
        & ma200_trading.notna()
    )

    cta_trading.loc[valid_trading] = 0.0

    cta_trading.loc[
        valid_trading & (spy_trading > ma50_trading)
    ] += 0.5

    cta_trading.loc[
        valid_trading & (spy_trading > ma200_trading)
    ] += 0.5

    cta_trading.loc[
        valid_trading & (spy_trading < ma50_trading)
    ] -= 0.5

    cta_trading.loc[
        valid_trading & (spy_trading < ma200_trading)
    ] -= 0.5

    # 전체 캘린더로 복원 후 과거값만 전달
    cta_full = cta_trading.reindex(macro.index).ffill()

    first_valid_idx = (
        cta_trading.first_valid_index()
        if cta_trading.notna().any()
        else None
    )

    fetch_ok = pd.Series(0, index=macro.index, dtype=int)

    if first_valid_idx is not None:
        fetch_ok.loc[first_valid_idx:] = (
            cta_full.loc[first_valid_idx:].notna().astype(int)
        )

    proxy = pd.DataFrame({
        "date": macro["date"],
        "CTA_MOMENTUM_SCORE_NEW": cta_full,
        "CTA_FETCH_OK_NEW": fetch_ok,
    })

    result = positioning.merge(
        proxy,
        on="date",
        how="left",
    )

    result["CTA_MOMENTUM_SCORE"] = (
        result["CTA_MOMENTUM_SCORE_NEW"]
        .combine_first(result["CTA_MOMENTUM_SCORE"])
    )

    result["CTA_FETCH_OK"] = (
        result["CTA_FETCH_OK_NEW"]
        .fillna(0)
        .astype(int)
    )

    result = result.drop(columns=[
        "CTA_MOMENTUM_SCORE_NEW",
        "CTA_FETCH_OK_NEW",
    ])

    result["date"] = result["date"].dt.strftime("%Y-%m-%d")

    result.to_csv(
        POSITIONING_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Source: {source_positioning}")
    print(f"Saved : {POSITIONING_PATH}")

    print("\nCTA score counts:")
    print(
        result["CTA_MOMENTUM_SCORE"]
        .value_counts(dropna=False)
        .sort_index()
        .to_string()
    )

    print("\nCTA fetch status:")
    print(
        result["CTA_FETCH_OK"]
        .value_counts(dropna=False)
        .sort_index()
        .to_string()
    )

    valid_rows = result[result["CTA_FETCH_OK"].eq(1)]

    print("\nFirst valid CTA rows:")
    print(
        valid_rows[
            ["date", "CTA_MOMENTUM_SCORE", "CTA_FETCH_OK"]
        ]
        .head()
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
