from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "data" / "backtest" / "results"

INPUT_PATH = RESULT_DIR / "daily_positions.csv"
DETAIL_PATH = RESULT_DIR / "deadman_release_detail.csv"
MONTHLY_PATH = RESULT_DIR / "deadman_release_monthly.csv"
TRANSITION_PATH = RESULT_DIR / "deadman_transitions.csv"

START_DATE = pd.Timestamp("2008-12-01")
END_DATE = pd.Timestamp("2010-12-31")


def main() -> None:
    df = pd.read_csv(INPUT_PATH)

    required = [
        "signal_date",
        "risk_budget_13",
        "exposure_15",
        "cash_weight",
        "sew_status",
        "deadman_reason",
        "vix_today",
        "hy_oas_today",
    ]

    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df["signal_date"] = pd.to_datetime(df["signal_date"], errors="coerce")

    for col in [
        "risk_budget_13",
        "exposure_15",
        "cash_weight",
        "vix_today",
        "hy_oas_today",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    audit = df[
        df["signal_date"].between(START_DATE, END_DATE)
    ].copy()

    audit = audit.sort_values("signal_date").reset_index(drop=True)

    audit["deadman_on"] = audit["sew_status"].eq("HARD_DEADMAN")
    audit["previous_deadman_on"] = audit["deadman_on"].shift(1)

    audit["transition"] = ""

    audit.loc[
        audit["deadman_on"]
        & audit["previous_deadman_on"].eq(False),
        "transition",
    ] = "DEADMAN_ON"

    audit.loc[
        ~audit["deadman_on"]
        & audit["previous_deadman_on"].eq(True),
        "transition",
    ] = "DEADMAN_RELEASED"

    # 첫 관측일이 이미 ON인 경우
    if not audit.empty and bool(audit.loc[0, "deadman_on"]):
        audit.loc[0, "transition"] = "DEADMAN_ALREADY_ON"

    audit["hy_below_6"] = audit["hy_oas_today"] < 6.0
    audit["vix_below_30"] = audit["vix_today"] < 30.0

    audit["release_conditions_clear"] = (
        audit["hy_below_6"]
        & audit["vix_below_30"]
    )

    audit["year_month"] = audit["signal_date"].dt.to_period("M").astype(str)

    detail_cols = [
        "signal_date",
        "risk_budget_13",
        "exposure_15",
        "cash_weight",
        "sew_status",
        "deadman_on",
        "transition",
        "deadman_reason",
        "hy_oas_today",
        "vix_today",
        "hy_below_6",
        "vix_below_30",
        "release_conditions_clear",
    ]

    audit[detail_cols].to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    monthly = (
        audit.groupby("year_month")
        .agg(
            trading_days=("signal_date", "count"),
            deadman_days=("deadman_on", "sum"),
            avg_exposure=("exposure_15", "mean"),
            avg_cash=("cash_weight", "mean"),
            avg_hy_oas=("hy_oas_today", "mean"),
            min_hy_oas=("hy_oas_today", "min"),
            avg_vix=("vix_today", "mean"),
            max_vix=("vix_today", "max"),
            clear_condition_days=("release_conditions_clear", "sum"),
        )
        .reset_index()
    )

    monthly["deadman_share"] = (
        monthly["deadman_days"] / monthly["trading_days"]
    )

    monthly.to_csv(
        MONTHLY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    transitions = audit[
        audit["transition"].ne("")
    ][detail_cols].copy()

    transitions.to_csv(
        TRANSITION_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    released = audit[
        audit["transition"].eq("DEADMAN_RELEASED")
    ]

    first_hy_below_6 = audit[
        audit["hy_oas_today"] < 6
    ]["signal_date"]

    first_vix_below_30 = audit[
        audit["vix_today"] < 30
    ]["signal_date"]

    first_both_clear = audit[
        audit["release_conditions_clear"]
    ]["signal_date"]

    print("=" * 76)
    print("DEADMAN RELEASE AUDIT")
    print("=" * 76)
    print(
        f"Period                 : "
        f"{audit['signal_date'].min().date()} ~ "
        f"{audit['signal_date'].max().date()}"
    )
    print(f"Rows                   : {len(audit):,}")
    print(f"Deadman days           : {int(audit['deadman_on'].sum()):,}")
    print(
        f"Deadman share          : "
        f"{audit['deadman_on'].mean() * 100:.1f}%"
    )

    print()
    print(
        "First HY OAS < 6%      :",
        first_hy_below_6.iloc[0].date()
        if not first_hy_below_6.empty
        else "NEVER",
    )
    print(
        "First VIX < 30         :",
        first_vix_below_30.iloc[0].date()
        if not first_vix_below_30.empty
        else "NEVER",
    )
    print(
        "First both clear       :",
        first_both_clear.iloc[0].date()
        if not first_both_clear.empty
        else "NEVER",
    )
    print(
        "First Deadman release  :",
        released.iloc[0]["signal_date"].date()
        if not released.empty
        else "NEVER",
    )

    print("\n" + "=" * 76)
    print("TRANSITIONS")
    print("=" * 76)

    if transitions.empty:
        print("No transitions found.")
    else:
        print(
            transitions[
                [
                    "signal_date",
                    "transition",
                    "hy_oas_today",
                    "vix_today",
                    "exposure_15",
                    "deadman_reason",
                ]
            ].to_string(index=False)
        )

    print("\n" + "=" * 76)
    print("MONTHLY SUMMARY")
    print("=" * 76)
    print(monthly.round(2).to_string(index=False))

    print("\nSaved:")
    print(DETAIL_PATH)
    print(MONTHLY_PATH)
    print(TRANSITION_PATH)


if __name__ == "__main__":
    main()
