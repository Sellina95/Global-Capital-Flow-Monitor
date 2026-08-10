from __future__ import annotations

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

PANEL_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

OUTPUT_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter15_release_counterfactual_summary.csv"
)


def calculate_forward_return(
    df: pd.DataFrame,
    horizon: int,
):
    return (
        df["SPY"].shift(-horizon)
        /
        df["SPY"]
        - 1
    ) * 100


def main():

    df = pd.read_csv(
        PANEL_PATH
    )

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )


    numeric_cols = [
        "SPY",
        "VIX",
        "credit__HY_OAS",
        "positioning__SP500_POS_Z",
        "positioning__CTA_MOMENTUM_SCORE",
    ]


    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )


    df = (
        df
        .sort_values("signal_date")
        .reset_index(drop=True)
    )


    # Forward return

    df["spy_return_20d"] = calculate_forward_return(
        df,
        20,
    )

    df["spy_return_60d"] = calculate_forward_return(
        df,
        60,
    )


    # ==================================================
    # Release Scenarios
    # ==================================================

    scenarios = {}


    # Scenario A
    scenarios["CURRENT"] = (
        (df["credit__HY_OAS"] < 6.0)
        &
        (df["VIX"] < 30)
    )


    # Scenario B
    scenarios["POSITIONING_FILTER"] = (
        (df["credit__HY_OAS"] < 6.0)
        &
        (df["VIX"] < 30)
        &
        (df["positioning__SP500_POS_Z"] < 2.0)
    )


    # Scenario C
    scenarios["POSITIONING_CTA_FILTER"] = (
        (df["credit__HY_OAS"] < 6.0)
        &
        (df["VIX"] < 30)
        &
        (df["positioning__SP500_POS_Z"] < 2.0)
        &
        (df["positioning__CTA_MOMENTUM_SCORE"] <= 1.0)
    )


    results = []


    for name, mask in scenarios.items():

        release = df.loc[
            mask
        ].copy()


        release_days = len(
            release
        )


        false_positive = (
            release["spy_return_60d"]
            < 0
        ).sum()


        results.append(
            {
                "scenario":
                    name,

                "release_days":
                    release_days,

                "avg_spy_20d":
                    release["spy_return_20d"].mean(),

                "avg_spy_60d":
                    release["spy_return_60d"].mean(),

                "median_spy_60d":
                    release["spy_return_60d"].median(),

                "positive_60d_rate":
                    (
                        release["spy_return_60d"]
                        > 0
                    ).mean(),

                "false_positive_days":
                    int(false_positive),

                "false_positive_rate":
                    (
                        false_positive
                        /
                        release_days
                    )
                    if release_days > 0
                    else None,
            }
        )


    result = pd.DataFrame(
        results
    )


    result.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 70)
    print(
        "FILTER15 RELEASE COUNTERFACTUAL AUDIT"
    )
    print("=" * 70)

    print(
        result.to_string(index=False)
    )

    print()

    print("Saved:")
    print(OUTPUT_PATH)



if __name__ == "__main__":
    main()