from __future__ import annotations

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "deadman_recovery_episode_detail.csv"
)

OUTPUT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "deadman_recovery_false_positive.csv"
)


def main():

    df = pd.read_csv(INPUT)

    df["start_date"] = pd.to_datetime(
        df["start_date"],
        errors="coerce",
    )

    # --------------------------------------------------
    # False Positive Definition
    # --------------------------------------------------
    # Recovery 이후 60D SPY 성과가 마이너스인 episode

    false_positive = df[
        df["spy_return_60d_avg"] < 0
    ].copy()


    false_positive = false_positive.sort_values(
        "spy_return_60d_avg"
    )


    false_positive.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 70)
    print("FILTER15 RECOVERY FALSE POSITIVE AUDIT")
    print("=" * 70)

    print(
        f"Total Episodes : {len(df)}"
    )

    print(
        f"False Positive : {len(false_positive)}"
    )


    if len(false_positive) > 0:

        print("\nWorst Recovery Episodes")
        print(
            false_positive[
                [
                    "episode_id",
                    "start_date",
                    "duration_days",
                    "start_hy_oas",
                    "avg_hy_oas",
                    "start_vix",
                    "avg_vix",
                    "spy_return_20d_avg",
                    "spy_return_60d_avg",
                ]
            ]
            .to_string(index=False)
        )


    print("\nSaved:")
    print(OUTPUT)



if __name__ == "__main__":
    main()