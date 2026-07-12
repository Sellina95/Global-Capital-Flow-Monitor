from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "data" / "backtest" / "results"

INPUT_PATH = RESULT_DIR / "daily_positions.csv"
OUTPUT_PATH = RESULT_DIR / "bull_market_attribution.csv"
DRIVER_PATH = RESULT_DIR / "bull_market_brake_drivers.csv"

BULL_YEARS = [2013, 2017, 2021, 2024]


def split_drivers(value: object) -> list[str]:
    if pd.isna(value):
        return []

    text = str(value).replace("⚠️", "").strip()

    if not text or text.upper() in {"NONE", "NAN"}:
        return []

    return [
        item.strip()
        for item in text.split(",")
        if item.strip()
    ]


def main() -> None:
    df = pd.read_csv(INPUT_PATH)

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )
    df["year"] = df["signal_date"].dt.year

    numeric_cols = [
        "risk_budget_13",
        "exposure_15",
        "allocated_equity_18",
        "cash_weight",
        "vix_today",
        "hy_oas_today",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["cut_13_to_15"] = (
        df["risk_budget_13"] - df["exposure_15"]
    )
    df["cut_15_to_18"] = (
        df["exposure_15"] - df["allocated_equity_18"]
    )

    bull = df[df["year"].isin(BULL_YEARS)].copy()

    summary = (
        bull.groupby("year")
        .agg(
            days=("signal_date", "count"),
            avg_budget_13=("risk_budget_13", "mean"),
            avg_exposure_15=("exposure_15", "mean"),
            avg_allocation_18=("allocated_equity_18", "mean"),
            avg_cash=("cash_weight", "mean"),
            avg_cut_13_to_15=("cut_13_to_15", "mean"),
            avg_cut_15_to_18=("cut_15_to_18", "mean"),
            avg_vix=("vix_today", "mean"),
            avg_hy_oas=("hy_oas_today", "mean"),
            deadman_days=(
                "sew_status",
                lambda s: int((s == "HARD_DEADMAN").sum()),
            ),
            compression_days=(
                "sew_status",
                lambda s: int((s == "RISK_COMPRESSION").sum()),
            ),
            normal_days=(
                "sew_status",
                lambda s: int((s == "NORMAL").sum()),
            ),
        )
        .reset_index()
    )

    summary["deadman_share"] = (
        summary["deadman_days"] / summary["days"]
    )
    summary["compression_share"] = (
        summary["compression_days"] / summary["days"]
    )

    summary.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    driver_rows = []

    for year in BULL_YEARS:
        year_df = bull[bull["year"] == year]
        counter: Counter[str] = Counter()

        if "brake_drivers" in year_df.columns:
            for value in year_df["brake_drivers"]:
                counter.update(split_drivers(value))

        for driver, count in counter.most_common():
            driver_rows.append({
                "year": year,
                "driver": driver,
                "days": count,
                "share_of_year": count / len(year_df) if len(year_df) else 0,
            })

    drivers = pd.DataFrame(driver_rows)

    drivers.to_csv(
        DRIVER_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print("=" * 86)
    print("BULL MARKET ATTRIBUTION")
    print("=" * 86)
    print(summary.round(2).to_string(index=False))

    print("\n" + "=" * 86)
    print("TOP BRAKE DRIVERS BY YEAR")
    print("=" * 86)

    for year in BULL_YEARS:
        print(f"\n[{year}]")

        year_drivers = drivers[drivers["year"] == year].head(10)

        if year_drivers.empty:
            print("No brake-driver data.")
        else:
            print(
                year_drivers[
                    ["driver", "days", "share_of_year"]
                ].to_string(index=False)
            )

    print("\nSaved:")
    print(OUTPUT_PATH)
    print(DRIVER_PATH)


if __name__ == "__main__":
    main()
