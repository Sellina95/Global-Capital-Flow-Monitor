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

RESULT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

DETAIL_OUTPUT = (
    RESULT_DIR
    / "deadman_recovery_episode_detail.csv"
)

SUMMARY_OUTPUT = (
    RESULT_DIR
    / "deadman_recovery_episode_summary.csv"
)


def main():

    # ==================================================
    # Load counterfactual audit data
    # ==================================================

    df = pd.read_csv(INPUT)

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )


    # ==================================================
    # Attach SPY price
    # ==================================================

    panel = pd.read_csv(PANEL)

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"],
        errors="coerce",
    )

    panel["SPY"] = pd.to_numeric(
        panel["SPY"],
        errors="coerce",
    )

    panel = (
        panel[
            [
                "signal_date",
                "SPY",
            ]
        ]
        .dropna()
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
    )


    df = df.merge(
        panel,
        on="signal_date",
        how="left",
    )


    # ==================================================
    # Numeric conversion
    # ==================================================

    numeric_cols = [
        "hy_oas",
        "vix",
        "SPY",
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


    # ==================================================
    # Forward SPY Return
    # ==================================================

    df["spy_return_20d"] = (
        df["SPY"].shift(-20)
        /
        df["SPY"]
        - 1
    ) * 100


    df["spy_return_60d"] = (
        df["SPY"].shift(-60)
        /
        df["SPY"]
        - 1
    ) * 100



    # ==================================================
    # Recovery State Definition
    # ==================================================

    # Recovery Watch:
    # Credit 개선 + Volatility 안정

    df["recovery_state"] = (
        (df["hy_oas"] < 6.0)
        &
        (df["vix"] < 30)
    )


    # ==================================================
    # Episode Extraction
    # ==================================================

    episodes = []

    in_episode = False
    start_idx = None
    episode_id = 0


    for idx, row in df.iterrows():

        recovery = bool(
            row["recovery_state"]
        )


        # START
        if recovery and not in_episode:

            in_episode = True
            start_idx = idx



        # END
        elif (
            not recovery
            and in_episode
        ):

            episode = df.loc[
                start_idx:idx-1
            ]

            episode_id += 1


            episodes.append(
                {
                    "episode_id":
                        episode_id,

                    "start_date":
                        episode.iloc[0]["signal_date"],

                    "end_date":
                        episode.iloc[-1]["signal_date"],

                    "duration_days":
                        len(episode),


                    "start_hy_oas":
                        episode.iloc[0]["hy_oas"],

                    "end_hy_oas":
                        episode.iloc[-1]["hy_oas"],

                    "min_hy_oas":
                        episode["hy_oas"].min(),

                    "avg_hy_oas":
                        episode["hy_oas"].mean(),


                    "start_vix":
                        episode.iloc[0]["vix"],

                    "avg_vix":
                        episode["vix"].mean(),


                    "spy_return_20d_avg":
                        episode["spy_return_20d"].mean(),

                    "spy_return_60d_avg":
                        episode["spy_return_60d"].mean(),

                    "end_reason":
                        "RECOVERY_END",
                }
            )


            in_episode = False
            start_idx = None



    # ==================================================
    # Last Episode
    # ==================================================

    if in_episode:

        episode = df.loc[start_idx:]

        episode_id += 1

        episodes.append(
            {
                "episode_id":
                    episode_id,

                "start_date":
                    episode.iloc[0]["signal_date"],

                "end_date":
                    episode.iloc[-1]["signal_date"],

                "duration_days":
                    len(episode),

                "start_hy_oas":
                    episode.iloc[0]["hy_oas"],

                "end_hy_oas":
                    episode.iloc[-1]["hy_oas"],

                "min_hy_oas":
                    episode["hy_oas"].min(),

                "avg_hy_oas":
                    episode["hy_oas"].mean(),

                "start_vix":
                    episode.iloc[0]["vix"],

                "avg_vix":
                    episode["vix"].mean(),

                "spy_return_20d_avg":
                    episode["spy_return_20d"].mean(),

                "spy_return_60d_avg":
                    episode["spy_return_60d"].mean(),

                "end_reason":
                    "END",
            }
        )


    result = pd.DataFrame(
        episodes
    )


    # ==================================================
    # Save Detail
    # ==================================================

    result.to_csv(
        DETAIL_OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )


    # ==================================================
    # Summary
    # ==================================================

    summary = pd.DataFrame(
        [
            {
                "episodes":
                    len(result),

                "avg_duration":
                    result["duration_days"].mean(),

                "median_duration":
                    result["duration_days"].median(),

                "max_duration":
                    result["duration_days"].max(),

                "avg_spy_20d":
                    result["spy_return_20d_avg"].mean(),

                "avg_spy_60d":
                    result["spy_return_60d_avg"].mean(),

                "best_episode_60d":
                    result["spy_return_60d_avg"].max(),

                "worst_episode_60d":
                    result["spy_return_60d_avg"].min(),
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
        "DEADMAN RECOVERY EPISODE AUDIT v2"
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