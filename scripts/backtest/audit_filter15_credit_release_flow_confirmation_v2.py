from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

POSITIONS_PATH = (
    RESULT_DIR /
    "daily_positions.csv"
)

MASTER_PANEL_PATH = (
    ROOT /
    "data" /
    "backtest" /
    "master_panel.csv"
)

DETAIL_PATH = (
    RESULT_DIR /
    "filter15_credit_release_flow_confirmation_v2_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR /
    "filter15_credit_release_flow_confirmation_v2_summary.csv"
)


# ==========================================================
# Import execution chain
# ==========================================================

sys.path.insert(0, str(ROOT))

from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)


# ==========================================================
# Helpers
# ==========================================================

def forward_return(series, horizon):
    return (
        series.shift(-horizon)
        /
        series
        - 1
    ) * 100


def summarize(df, mask, name):

    x = df.loc[mask].copy()

    r20 = x["spy_return_20d"].dropna()
    r60 = x["spy_return_60d"].dropna()

    return {
        "scenario": name,
        "events": len(x),

        "avg_flow_score":
            x["flow_score"].mean(),

        "avg_spy_20d":
            r20.mean(),

        "median_spy_20d":
            r20.median(),

        "positive_20d_rate":
            (r20 > 0).mean()
            if len(r20)
            else None,

        "avg_spy_60d":
            r60.mean(),

        "median_spy_60d":
            r60.median(),

        "positive_60d_rate":
            (r60 > 0).mean()
            if len(r60)
            else None,

        "negative_60d_rate":
            (r60 < 0).mean()
            if len(r60)
            else None,

        "worst_60d":
            r60.min()
            if len(r60)
            else None,

        "best_60d":
            r60.max()
            if len(r60)
            else None,
    }


# ==========================================================
# Main
# ==========================================================

def main():

    positions = pd.read_csv(
        POSITIONS_PATH
    )

    panel = pd.read_csv(
        MASTER_PANEL_PATH
    )


    positions["signal_date"] = pd.to_datetime(
        positions["signal_date"]
    )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"]
    )


    positions = (
        positions
        .sort_values("signal_date")
        .reset_index(drop=True)
    )


    panel = (
        panel
        .sort_values("signal_date")
        .reset_index(drop=True)
    )


    # ------------------------------------------------------
    # Build Flow Generator History
    # ------------------------------------------------------

    flow_scores = []
    flow_states = []

    flow_memory = {}

    for idx, row in panel.iterrows():

        market_data = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=None,
        )

        flow_memory = prepare_filter13_execution_state(
            market_data=market_data,
            panel=panel,
            row_index=idx,
            previous_flow_memory=flow_memory,
        )

        flow_scores.append(
            flow_memory.get(
                "flow_score",
                0
            )
        )

        flow_states.append(
            flow_memory.get(
                "flow_state",
                "N/A"
            )
        )


    flow_df = pd.DataFrame(
        {
            "signal_date":
                panel["signal_date"],

            "flow_score":
                flow_scores,

            "flow_state":
                flow_states,
        }
    )


    df = positions.merge(
        flow_df,
        on="signal_date",
        how="left",
    )


    # ------------------------------------------------------
    # SPY return
    # ------------------------------------------------------

    spy_df = panel[
        [
            "signal_date",
            "SPY",
        ]
    ]

    df = df.merge(
        spy_df,
        on="signal_date",
        how="left",
    )


    df["spy_return_20d"] = (
        forward_return(
            df["SPY"],
            20
        )
    )

    df["spy_return_60d"] = (
        forward_return(
            df["SPY"],
            60
        )
    )


    # ------------------------------------------------------
    # Credit Deadman
    # ------------------------------------------------------

    df["credit_deadman"] = (
        df["sew_status"]
        .astype(str)
        .eq(
            "HARD_DEADMAN"
        )
        &
        df["deadman_reason"]
        .astype(str)
        .str.contains(
            "Credit Crisis",
            case=False,
            na=False,
        )
    )


    df["prev_deadman"] = (
        df["credit_deadman"]
        .shift(1)
        .fillna(False)
    )


    # ------------------------------------------------------
    # Release Event
    # ------------------------------------------------------

    df["release_event"] = (
        df["prev_deadman"]
        &
        (df["hy_oas_today"] < 6)
        &
        (df["vix_today"] < 30)
    )


    df["flow_ge_3"] = (
        df["release_event"]
        &
        (df["flow_score"] >= 3)
    )

    df["flow_ge_5"] = (
        df["release_event"]
        &
        (df["flow_score"] >= 5)
    )


    detail = df.loc[
        df["release_event"],
        [
            "signal_date",
            "hy_oas_today",
            "vix_today",
            "flow_score",
            "flow_state",
            "spy_return_20d",
            "spy_return_60d",
            "flow_ge_3",
            "flow_ge_5",
        ],
    ]


    detail.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )


    summary = pd.DataFrame(
        [
            summarize(
                df,
                df["release_event"],
                "CURRENT_RELEASE",
            ),

            summarize(
                df,
                df["flow_ge_3"],
                "FLOW_SCORE_GE_3",
            ),

            summarize(
                df,
                df["flow_ge_5"],
                "FLOW_SCORE_GE_5",
            ),
        ]
    )


    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 70)
    print(
        "FILTER15 CREDIT RELEASE FLOW CONFIRMATION v2"
    )
    print("=" * 70)

    print(summary.to_string(index=False))

    print("\nSaved:")
    print(DETAIL_PATH)
    print(SUMMARY_PATH)



if __name__ == "__main__":
    main()