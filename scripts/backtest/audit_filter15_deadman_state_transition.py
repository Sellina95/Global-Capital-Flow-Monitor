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

OUTPUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

DETAIL_OUTPUT = (
    OUTPUT_DIR
    / "deadman_state_transition_detail.csv"
)

SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "deadman_state_transition_summary.csv"
)


def main():

    df = pd.read_csv(INPUT)

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )

    numeric_cols = [
        "hy_oas",
        "vix",
        "risk_budget_13",
        "production_exposure",
        "counterfactual_exposure",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    df = df.sort_values(
        "signal_date"
    ).reset_index(drop=True)


    # --------------------------------------------------
    # State labeling
    # --------------------------------------------------

    df["state"] = "NORMAL"

    df.loc[
        df["production_deadman"] == True,
        "state"
    ] = "DEADMAN"


    df.loc[
        df["counterfactual_release"] == True,
        "state"
    ] = "RECOVERY_WATCH"


    # --------------------------------------------------
    # Transition detection
    # --------------------------------------------------

    transitions = []

    current_state = None
    start_date = None
    days = 0

    for _, row in df.iterrows():

        state = row["state"]

        if current_state is None:
            current_state = state
            start_date = row["signal_date"]
            days = 1
            continue


        if state == current_state:
            days += 1

        else:

            transitions.append(
                {
                    "from_state": current_state,
                    "to_state": state,
                    "start_date": start_date,
                    "end_date": row["signal_date"],
                    "duration_days": days,
                }
            )

            current_state = state
            start_date = row["signal_date"]
            days = 1


    transitions.append(
        {
            "from_state": current_state,
            "to_state": "END",
            "start_date": start_date,
            "end_date": df.iloc[-1]["signal_date"],
            "duration_days": days,
        }
    )


    transition_df = pd.DataFrame(
        transitions
    )


    transition_df.to_csv(
        DETAIL_OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )


    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    recovery_entries = transition_df[
        transition_df["to_state"]
        ==
        "RECOVERY_WATCH"
    ]

    recovery_to_deadman = transition_df[
        (
            transition_df["from_state"]
            ==
            "RECOVERY_WATCH"
        )
        &
        (
            transition_df["to_state"]
            ==
            "DEADMAN"
        )
    ]


    summary = pd.DataFrame(
        [
            {
                "total_transitions":
                    len(transition_df),

                "recovery_entries":
                    len(recovery_entries),

                "recovery_to_deadman_events":
                    len(recovery_to_deadman),

                "avg_recovery_duration":
                    recovery_entries[
                        "duration_days"
                    ].mean(),

                "max_recovery_duration":
                    recovery_entries[
                        "duration_days"
                    ].max(),

                "avg_days_before_deadman_return":
                    recovery_to_deadman[
                        "duration_days"
                    ].mean(),
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
        "DEADMAN STATE TRANSITION AUDIT"
    )
    print("=" * 70)

    print(
        summary.to_string(index=False)
    )

    print()

    print("Saved:")
    print(DETAIL_OUTPUT)
    print(SUMMARY_OUTPUT)


if __name__ == "__main__":
    main()