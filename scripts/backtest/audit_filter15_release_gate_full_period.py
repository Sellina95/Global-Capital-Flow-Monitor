from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

POSITIONS_PATH = (
    RESULT_DIR /
    "daily_positions.csv"
)

PANEL_PATH = (
    ROOT /
    "data" /
    "backtest" /
    "master_panel.csv"
)

SUMMARY_PATH = (
    RESULT_DIR /
    "filter15_release_gate_full_period_summary.csv"
)

DETAIL_PATH = (
    RESULT_DIR /
    "filter15_release_gate_full_period_detail.csv"
)


def evaluate(df, mask, name):

    x = df.loc[mask].copy()

    r20 = x["spy_return_20d"].dropna()
    r60 = x["spy_return_60d"].dropna()

    return {
        "scenario": name,
        "events": len(x),

        "avg_spy_20d":
            r20.mean()
            if len(r20)
            else None,

        "avg_spy_60d":
            r60.mean()
            if len(r60)
            else None,

        "median_spy_60d":
            r60.median()
            if len(r60)
            else None,

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


def main():

    positions = pd.read_csv(
        POSITIONS_PATH
    )

    panel = pd.read_csv(
        PANEL_PATH
    )


    positions["signal_date"] = pd.to_datetime(
        positions["signal_date"]
    )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"]
    )


    panel = panel.sort_values(
        "signal_date"
    )


    # --------------------------------------------------
    # Forward Return
    # --------------------------------------------------

    panel["spy_return_20d"] = (
        panel["SPY"].shift(-20)
        /
        panel["SPY"]
        -
        1
    ) * 100


    panel["spy_return_60d"] = (
        panel["SPY"].shift(-60)
        /
        panel["SPY"]
        -
        1
    ) * 100


    # --------------------------------------------------
    # Liquidity Trend
    # Point-in-time
    # --------------------------------------------------

    panel["net_liq_20d_change"] = (
        panel["liquidity__NET_LIQ"]
        -
        panel["liquidity__NET_LIQ"].shift(20)
    )


    df = positions.merge(
        panel[
            [
                "signal_date",
                "SPY",
                "spy_return_20d",
                "spy_return_60d",
                "liquidity__NET_LIQ",
                "net_liq_20d_change",
                "positioning__SP500_POS_Z",
            ]
        ],
        on="signal_date",
        how="left",
    )


    # --------------------------------------------------
    # Credit Recovery State
    # --------------------------------------------------

    df["credit_recovered"] = (
        (df["hy_oas_today"] < 6)
        &
        (df["vix_today"] < 30)
    )


    # --------------------------------------------------
    # Recovery Persistence
    # --------------------------------------------------

    df["recovery_streak"] = (
        df["credit_recovered"]
        .groupby(
            (
                ~df["credit_recovered"]
            )
            .cumsum()
        )
        .cumcount()
        + 1
    )


    # --------------------------------------------------
    # Current Release
    # --------------------------------------------------

    df["current_release"] = (
        df["credit_recovered"]
        &
        (
            df["sew_status"]
            .shift(1)
            .astype(str)
            .eq("HARD_DEADMAN")
        )
    )


    # --------------------------------------------------
    # Candidate Release
    # --------------------------------------------------

    df["candidate_release"] = (
        (df["recovery_streak"] == 3)
        &
        (df["positioning__SP500_POS_Z"] < 1.5)
        &
        (df["net_liq_20d_change"] >= 0)
    )


    summary = pd.DataFrame(
        [
            evaluate(
                df,
                df["current_release"],
                "CURRENT_RELEASE"
            ),

            evaluate(
                df,
                df["candidate_release"],
                "CANDIDATE_RELEASE"
            ),
        ]
    )


    detail = df[
        df["current_release"]
        |
        df["candidate_release"]
    ][
        [
            "signal_date",
            "hy_oas_today",
            "vix_today",
            "positioning__SP500_POS_Z",
            "net_liq_20d_change",
            "spy_return_20d",
            "spy_return_60d",
            "current_release",
            "candidate_release",
        ]
    ]


    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )


    detail.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 75)
    print(
        "FILTER15 RELEASE GATE FULL PERIOD AUDIT"
    )
    print("=" * 75)

    print(
        summary.to_string(
            index=False
        )
    )

    print()

    print("Saved:")
    print(SUMMARY_PATH)
    print(DETAIL_PATH)


if __name__ == "__main__":
    main()