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
    "filter15_deadman_release_gate_counterfactual_summary.csv"
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

        "best_60d":
            r60.max()
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


    # ------------------------------------------------
    # All Recovery Candidates
    # ------------------------------------------------

    current = release.copy()


    # Persistence 3D

    persist3 = current[
        current["persist_3_release"]
        ==
        True
    ].copy()


    df = persist3.merge(
        panel[
            [
                "signal_date",
                "positioning__SP500_POS_Z",
                "liquidity__NET_LIQ",
            ]
        ],
        on="signal_date",
        how="left",
    )


    df["positioning__SP500_POS_Z"] = pd.to_numeric(
        df["positioning__SP500_POS_Z"],
        errors="coerce",
    )

    df["liquidity__NET_LIQ"] = pd.to_numeric(
        df["liquidity__NET_LIQ"],
        errors="coerce",
    )


    pos_high = (
        df["positioning__SP500_POS_Z"]
        >=
        1.5
    )


    liq_weak = (
        df["liquidity__NET_LIQ"]
        <
        df["liquidity__NET_LIQ"].median()
    )


    scenarios = {

        "HY_PERSIST_3D":
            pd.Series(
                True,
                index=df.index
            ),

        "RISK_EXCLUSION":
            ~(
                pos_high
                &
                liq_weak
            ),

        "STRICT_CONFIRMATION":
            (
                ~pos_high
                &
                ~liq_weak
            ),
    }


    results = []


    for name, mask in scenarios.items():

        results.append(
            evaluate(
                df,
                mask,
                name
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
        "FILTER15 DEADMAN RELEASE GATE COUNTERFACTUAL"
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