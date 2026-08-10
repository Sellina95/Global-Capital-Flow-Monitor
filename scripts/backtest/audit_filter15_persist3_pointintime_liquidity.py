from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

DETAIL_PATH = (
    RESULT_DIR /
    "filter15_credit_persistence_release_detail.csv"
)

PANEL_PATH = (
    ROOT /
    "data" /
    "backtest" /
    "master_panel.csv"
)

SUMMARY_PATH = (
    RESULT_DIR /
    "filter15_persist3_pointintime_liquidity_summary.csv"
)


def evaluate(df, mask, name):

    x = df.loc[mask]

    r60 = x["spy_return_60d"].dropna()

    return {
        "scenario": name,
        "events": len(x),

        "avg_spy_60d":
            r60.mean() if len(r60) else None,

        "median_spy_60d":
            r60.median() if len(r60) else None,

        "positive_rate":
            (r60 > 0).mean()
            if len(r60)
            else None,

        "negative_rate":
            (r60 < 0).mean()
            if len(r60)
            else None,

        "worst_60d":
            r60.min()
            if len(r60)
            else None,
    }


def main():

    release = pd.read_csv(
        DETAIL_PATH
    )

    panel = pd.read_csv(
        PANEL_PATH
    )


    release["signal_date"] = pd.to_datetime(
        release["signal_date"]
    )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"]
    )


    release = release[
        release["persist_3_release"]
        ==
        True
    ].copy()


    panel = panel.sort_values(
        "signal_date"
    )


    panel["net_liq_5d_change"] = (
        panel["liquidity__NET_LIQ"]
        -
        panel["liquidity__NET_LIQ"]
        .shift(5)
    )


    panel["net_liq_20d_change"] = (
        panel["liquidity__NET_LIQ"]
        -
        panel["liquidity__NET_LIQ"]
        .shift(20)
    )


    df = release.merge(
        panel[
            [
                "signal_date",
                "positioning__SP500_POS_Z",
                "liquidity__NET_LIQ",
                "net_liq_5d_change",
                "net_liq_20d_change",
            ]
        ],
        on="signal_date",
        how="left",
    )


    pos_ok = (
        df["positioning__SP500_POS_Z"]
        <
        1.5
    )


    scenarios = {

        "STRICT_MEDIAN_RESEARCH":
            (
                pos_ok
                &
                (
                    df["liquidity__NET_LIQ"]
                    >
                    df["liquidity__NET_LIQ"]
                    .median()
                )
            ),

        "POS_Z_PLUS_LIQ_5D_UP":
            (
                pos_ok
                &
                (
                    df["net_liq_5d_change"]
                    >
                    0
                )
            ),

        "POS_Z_PLUS_LIQ_20D_UP":
            (
                pos_ok
                &
                (
                    df["net_liq_20d_change"]
                    >
                    0
                )
            ),

        "POS_Z_PLUS_LIQ_20D_STABLE":
            (
                pos_ok
                &
                (
                    df["net_liq_20d_change"]
                    >=
                    0
                )
            ),
    }


    results = []

    for name, mask in scenarios.items():

        results.append(
            evaluate(
                df,
                mask,
                name,
            )
        )


    summary = pd.DataFrame(
        results
    )


    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 75)
    print(
        "FILTER15 PERSIST3 POINT-IN-TIME LIQUIDITY AUDIT"
    )
    print("=" * 75)

    print(
        summary.to_string(
            index=False
        )
    )


    print("\nSaved:")
    print(SUMMARY_PATH)


if __name__ == "__main__":
    main()