from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "backtest"
RESULT_DIR = DATA_DIR / "results"

POSITIONS_PATH = RESULT_DIR / "daily_positions.csv"
QA_PATH = RESULT_DIR / "backtest_qa.csv"
ATTRIBUTION_PATH = RESULT_DIR / "exposure_attribution.csv"
ANNUAL_PATH = RESULT_DIR / "annual_exposure_summary.csv"
REGIME_PATH = RESULT_DIR / "regime_exposure_summary.csv"


REQUIRED_COLUMNS = [
    "signal_date",
    "execution_date",
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
    "cash_weight",
    "macro_profile",
    "sew_status",
    "status",
]


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def main() -> None:
    if not POSITIONS_PATH.exists():
        raise FileNotFoundError(POSITIONS_PATH)

    df = pd.read_csv(POSITIONS_PATH)

    missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    df["signal_date"] = pd.to_datetime(df["signal_date"], errors="coerce")
    df["execution_date"] = pd.to_datetime(df["execution_date"], errors="coerce")

    numeric_cols = [
        "risk_budget_13",
        "exposure_15",
        "allocated_equity_18",
        "cash_weight",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ==================================================
    # 1) BACKTEST QA
    # ==================================================
    allocation_total = df["allocated_equity_18"] + df["cash_weight"]

    qa_checks = {
        "rows": len(df),
        "duplicate_signal_dates": int(df["signal_date"].duplicated().sum()),
        "missing_signal_dates": int(df["signal_date"].isna().sum()),
        "missing_execution_dates": int(df["execution_date"].isna().sum()),
        "non_ok_rows": int((df["status"] != "OK").sum()),
        "missing_risk_budget": int(df["risk_budget_13"].isna().sum()),
        "missing_exposure": int(df["exposure_15"].isna().sum()),
        "missing_allocation": int(df["allocated_equity_18"].isna().sum()),
        "missing_cash": int(df["cash_weight"].isna().sum()),
        "negative_exposure": int((df["exposure_15"] < 0).sum()),
        "exposure_over_100": int((df["exposure_15"] > 100).sum()),
        "allocation_over_exposure": int(
            (df["allocated_equity_18"] > df["exposure_15"] + 0.2).sum()
        ),
        "allocation_total_failures": int(
            ((allocation_total - 100).abs() > 0.2).sum()
        ),
    }

    qa_pass = all(
        value == 0
        for key, value in qa_checks.items()
        if key != "rows"
    )

    qa_df = pd.DataFrame(
        [{"check": key, "value": value} for key, value in qa_checks.items()]
    )
    qa_df.loc[len(qa_df)] = ["qa_pass", qa_pass]
    qa_df.to_csv(QA_PATH, index=False, encoding="utf-8-sig")

    # ==================================================
    # 2) EXPOSURE ATTRIBUTION
    # ==================================================
    df["cut_13_to_15"] = df["risk_budget_13"] - df["exposure_15"]
    df["cut_15_to_18"] = df["exposure_15"] - df["allocated_equity_18"]
    df["total_cut_13_to_18"] = (
        df["risk_budget_13"] - df["allocated_equity_18"]
    )

    total_days = len(df)

    hard_deadman_mask = df["sew_status"].astype(str).eq("HARD_DEADMAN")
    compression_mask = df["sew_status"].astype(str).eq("RISK_COMPRESSION")
    normal_mask = df["sew_status"].astype(str).eq("NORMAL")
    zero_exposure_mask = df["exposure_15"].eq(0)
    full_cash_mask = df["cash_weight"].ge(99.9)

    attribution_rows = [
        {
            "metric": "total_days",
            "value": total_days,
            "share_of_days": 1.0,
        },
        {
            "metric": "average_risk_budget_13",
            "value": df["risk_budget_13"].mean(),
            "share_of_days": np.nan,
        },
        {
            "metric": "average_exposure_15",
            "value": df["exposure_15"].mean(),
            "share_of_days": np.nan,
        },
        {
            "metric": "average_allocated_equity_18",
            "value": df["allocated_equity_18"].mean(),
            "share_of_days": np.nan,
        },
        {
            "metric": "average_cash",
            "value": df["cash_weight"].mean(),
            "share_of_days": np.nan,
        },
        {
            "metric": "average_cut_13_to_15",
            "value": df["cut_13_to_15"].mean(),
            "share_of_days": np.nan,
        },
        {
            "metric": "average_cut_15_to_18",
            "value": df["cut_15_to_18"].mean(),
            "share_of_days": np.nan,
        },
        {
            "metric": "hard_deadman_days",
            "value": int(hard_deadman_mask.sum()),
            "share_of_days": hard_deadman_mask.mean(),
        },
        {
            "metric": "risk_compression_days",
            "value": int(compression_mask.sum()),
            "share_of_days": compression_mask.mean(),
        },
        {
            "metric": "normal_days",
            "value": int(normal_mask.sum()),
            "share_of_days": normal_mask.mean(),
        },
        {
            "metric": "zero_exposure_days",
            "value": int(zero_exposure_mask.sum()),
            "share_of_days": zero_exposure_mask.mean(),
        },
        {
            "metric": "full_cash_days",
            "value": int(full_cash_mask.sum()),
            "share_of_days": full_cash_mask.mean(),
        },
        {
            "metric": "days_15_cut_more_than_10pct",
            "value": int((df["cut_13_to_15"] >= 10).sum()),
            "share_of_days": (df["cut_13_to_15"] >= 10).mean(),
        },
        {
            "metric": "days_15_cut_more_than_20pct",
            "value": int((df["cut_13_to_15"] >= 20).sum()),
            "share_of_days": (df["cut_13_to_15"] >= 20).mean(),
        },
        {
            "metric": "days_18_returned_exposure_to_cash",
            "value": int((df["cut_15_to_18"] > 0.2).sum()),
            "share_of_days": (df["cut_15_to_18"] > 0.2).mean(),
        },
    ]

    attribution = pd.DataFrame(attribution_rows)
    attribution.to_csv(
        ATTRIBUTION_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # ==================================================
    # 3) ANNUAL SUMMARY
    # ==================================================
    df["year"] = df["signal_date"].dt.year

    annual = (
        df.groupby("year", dropna=False)
        .agg(
            days=("signal_date", "count"),
            avg_risk_budget_13=("risk_budget_13", "mean"),
            avg_exposure_15=("exposure_15", "mean"),
            avg_allocated_equity_18=("allocated_equity_18", "mean"),
            avg_cash=("cash_weight", "mean"),
            avg_cut_13_to_15=("cut_13_to_15", "mean"),
            avg_cut_15_to_18=("cut_15_to_18", "mean"),
            zero_exposure_days=("exposure_15", lambda s: int((s == 0).sum())),
            full_cash_days=("cash_weight", lambda s: int((s >= 99.9).sum())),
        )
        .reset_index()
    )

    annual.to_csv(ANNUAL_PATH, index=False, encoding="utf-8-sig")

    # ==================================================
    # 4) MACRO PROFILE SUMMARY
    # ==================================================
    regime = (
        df.groupby("macro_profile", dropna=False)
        .agg(
            days=("signal_date", "count"),
            avg_risk_budget_13=("risk_budget_13", "mean"),
            avg_exposure_15=("exposure_15", "mean"),
            avg_allocated_equity_18=("allocated_equity_18", "mean"),
            avg_cash=("cash_weight", "mean"),
            avg_cut_13_to_15=("cut_13_to_15", "mean"),
            zero_exposure_days=("exposure_15", lambda s: int((s == 0).sum())),
        )
        .reset_index()
        .sort_values("days", ascending=False)
    )

    regime.to_csv(REGIME_PATH, index=False, encoding="utf-8-sig")

    # ==================================================
    # 5) TERMINAL REPORT
    # ==================================================
    print("=" * 72)
    print("BACKTEST QA")
    print("=" * 72)

    for key, value in qa_checks.items():
        print(f"{key:32s}: {value}")

    print(f"{'QA RESULT':32s}: {'PASS' if qa_pass else 'FAIL'}")

    print("\n" + "=" * 72)
    print("EXPOSURE ATTRIBUTION")
    print("=" * 72)

    print(f"Period                 : {df['signal_date'].min().date()} ~ "
          f"{df['signal_date'].max().date()}")
    print(f"Total days             : {total_days:,}")
    print(f"Average Risk Budget 13 : {df['risk_budget_13'].mean():.2f}%")
    print(f"Average Exposure 15    : {df['exposure_15'].mean():.2f}%")
    print(f"Average Allocation 18  : {df['allocated_equity_18'].mean():.2f}%")
    print(f"Average Cash           : {df['cash_weight'].mean():.2f}%")
    print()
    print(f"Average cut 13 → 15    : {df['cut_13_to_15'].mean():.2f}%p")
    print(f"Average cut 15 → 18    : {df['cut_15_to_18'].mean():.2f}%p")
    print()
    print(
        f"Hard Deadman days      : {hard_deadman_mask.sum():,} "
        f"({pct(hard_deadman_mask.mean())})"
    )
    print(
        f"Risk Compression days  : {compression_mask.sum():,} "
        f"({pct(compression_mask.mean())})"
    )
    print(
        f"Normal days            : {normal_mask.sum():,} "
        f"({pct(normal_mask.mean())})"
    )
    print(
        f"Zero Exposure days     : {zero_exposure_mask.sum():,} "
        f"({pct(zero_exposure_mask.mean())})"
    )
    print(
        f"Full Cash days         : {full_cash_mask.sum():,} "
        f"({pct(full_cash_mask.mean())})"
    )

    print("\n" + "=" * 72)
    print("ANNUAL EXPOSURE SUMMARY")
    print("=" * 72)
    print(annual.round(2).to_string(index=False))

    print("\nSaved:")
    print(QA_PATH)
    print(ATTRIBUTION_PATH)
    print(ANNUAL_PATH)
    print(REGIME_PATH)


if __name__ == "__main__":
    main()
