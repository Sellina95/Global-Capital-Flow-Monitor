from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "credit_deadman_counterfactual_detail.csv"
)

PANEL = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

DETAIL_OUTPUT = (
    OUTPUT_DIR
    / "deadman_recovery_capture_detail.csv"
)

SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "deadman_recovery_capture_summary.csv"
)


def main():

    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    if not PANEL.exists():
        raise FileNotFoundError(PANEL)


    # --------------------------------------------------
    # Recovery Candidate
    # --------------------------------------------------

    release_df = pd.read_csv(INPUT)

    release_df["signal_date"] = pd.to_datetime(
        release_df["signal_date"],
        errors="coerce",
    )


    release_df = release_df[
        release_df["counterfactual_release"]
        == True
    ].copy()


    # --------------------------------------------------
    # Market Price Data
    # --------------------------------------------------

    panel = pd.read_csv(PANEL)

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"],
        errors="coerce",
    )


    panel = panel.sort_values(
        "signal_date"
    ).reset_index(drop=True)


    panel["SPY"] = pd.to_numeric(
        panel["SPY"],
        errors="coerce",
    )


    spy_map = (
        panel[
            [
                "signal_date",
                "SPY",
            ]
        ]
        .dropna()
        .reset_index(drop=True)
    )


    results = []


    for _, row in release_df.iterrows():

        date = row["signal_date"]


        current = spy_map[
            spy_map["signal_date"] >= date
        ]


        if len(current) == 0:
            continue


        entry_idx = current.index[0]


        future_20 = spy_map.iloc[
            entry_idx + 20
            :
            entry_idx + 21
        ]


        future_60 = spy_map.iloc[
            entry_idx + 60
            :
            entry_idx + 61
        ]


        spy_entry = spy_map.iloc[
            entry_idx
        ]["SPY"]


        ret20 = None
        ret60 = None


        if len(future_20) > 0:
            spy_20 = future_20.iloc[0]["SPY"]

            ret20 = (
                spy_20
                /
                spy_entry
                - 1
            ) * 100


        if len(future_60) > 0:
            spy_60 = future_60.iloc[0]["SPY"]

            ret60 = (
                spy_60
                /
                spy_entry
                - 1
            ) * 100


        results.append(
            {
                "signal_date": date,

                "hy_oas":
                    row["hy_oas"],

                "vix":
                    row["vix"],

                "risk_budget_13":
                    row["risk_budget_13"],

                "production_exposure":
                    row["production_exposure"],

                "counterfactual_exposure":
                    row["counterfactual_exposure"],

                "spy_return_20d":
                    ret20,

                "spy_return_60d":
                    ret60,
            }
        )


    result = pd.DataFrame(results)


    result.to_csv(
        DETAIL_OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )


    summary = pd.DataFrame(
        [
            {
                "release_candidates":
                    len(result),

                "avg_spy_return_20d":
                    result["spy_return_20d"]
                    .mean(),

                "avg_spy_return_60d":
                    result["spy_return_60d"]
                    .mean(),

                "positive_20d_rate":
                    (
                        result["spy_return_20d"]
                        > 0
                    )
                    .mean(),

                "positive_60d_rate":
                    (
                        result["spy_return_60d"]
                        > 0
                    )
                    .mean(),

                "negative_60d_rate":
                    (
                        result["spy_return_60d"]
                        < 0
                    )
                    .mean(),
            }
        ]
    )


    summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 70)
    print(
        "DEADMAN RECOVERY CAPTURE AUDIT"
    )
    print("=" * 70)

    print(
        f"Release Candidates : {len(result)}"
    )

    print()

    print(
        f"Average SPY 20D Return : "
        f"{result.spy_return_20d.mean():.2f}%"
    )

    print(
        f"Average SPY 60D Return : "
        f"{result.spy_return_60d.mean():.2f}%"
    )

    print()

    print(
        f"Positive 20D Rate : "
        f"{(
            (result.spy_return_20d > 0)
            .mean()
            * 100
        ):.1f}%"
    )

    print(
        f"Positive 60D Rate : "
        f"{(
            (result.spy_return_60d > 0)
            .mean()
            * 100
        ):.1f}%"
    )


    print("=" * 70)

    print(
        "Saved:"
    )

    print(DETAIL_OUTPUT)
    print(SUMMARY_OUTPUT)


if __name__ == "__main__":
    main()