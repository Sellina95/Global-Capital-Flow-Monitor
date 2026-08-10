from __future__ import annotations

from pathlib import Path

import numpy as np
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
    "filter15_recovery_ramp_summary.csv"
)

DETAIL_PATH = (
    RESULT_DIR /
    "filter15_recovery_ramp_detail.csv"
)


def metrics(returns):

    r = pd.Series(
        returns
    ).dropna()

    equity = (
        1 + r
    ).cumprod()

    total_return = (
        equity.iloc[-1] - 1
    )

    years = len(r) / 252

    cagr = (
        equity.iloc[-1]
        **
        (1 / years)
        - 1
    )

    dd = (
        equity /
        equity.cummax()
        - 1
    )

    vol = (
        r.std()
        *
        np.sqrt(252)
    )

    sharpe = (
        r.mean()
        /
        r.std()
        *
        np.sqrt(252)
        if r.std() > 0
        else np.nan
    )

    return {
        "total_return":
            total_return * 100,

        "cagr":
            cagr * 100,

        "mdd":
            dd.min() * 100,

        "volatility":
            vol * 100,

        "sharpe":
            sharpe,
    }


def main():

    pos = pd.read_csv(
        POSITIONS_PATH
    )

    panel = pd.read_csv(
        PANEL_PATH
    )

    pos["signal_date"] = pd.to_datetime(
        pos["signal_date"]
    )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"]
    )


    panel = panel.sort_values(
        "signal_date"
    )


    panel["spy_return"] = (
        panel["SPY"]
        .pct_change()
        .shift(-1)
    )


    panel["net_liq_20d_change"] = (
        panel["liquidity__NET_LIQ"]
        -
        panel["liquidity__NET_LIQ"]
        .shift(20)
    )


    df = pos.merge(
        panel[
            [
                "signal_date",
                "spy_return",
                "positioning__SP500_POS_Z",
                "net_liq_20d_change",
            ]
        ],
        on="signal_date",
        how="left",
    )


    for c in [
        "exposure_15",
        "hy_oas_today",
        "vix_today",
        "positioning__SP500_POS_Z",
        "net_liq_20d_change",
    ]:
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )


    # -----------------------------------------
    # Credit Deadman State
    # -----------------------------------------

    df["credit_deadman"] = (
        df["sew_status"]
        .astype(str)
        .eq("HARD_DEADMAN")
    )


    baseline = []
    ramp25 = []
    ramp50 = []
    ramp100 = []

    active = False
    streak = 0


    for _, row in df.iterrows():

        deadman = row["credit_deadman"]

        if deadman:

            active = True
            streak = 0


        if active:

            recovery = (
                row["hy_oas_today"] < 6
                and
                row["vix_today"] < 30
            )

            if recovery:
                streak += 1
            else:
                streak = 0


        else:
            streak = 0


        pos_ok = (
            row["positioning__SP500_POS_Z"]
            <
            1.5
        )

        liq_ok = (
            row["net_liq_20d_change"]
            >=
            0
        )


        # ------------------------------
        # Baseline
        # ------------------------------

        baseline.append(
            row["exposure_15"]
        )


        # ------------------------------
        # Ramp 25
        # ------------------------------

        if active and streak >= 3:

            ramp25.append(
                row["exposure_15"]
                * 0.25
            )

        else:

            ramp25.append(
                0
            )


        # ------------------------------
        # Ramp 50
        # ------------------------------

        if active and streak >= 3 and pos_ok:

            ramp50.append(
                row["exposure_15"]
                * 0.50
            )

        else:

            ramp50.append(
                0
            )


        # ------------------------------
        # Ramp 100
        # ------------------------------

        if active and streak >= 3 and pos_ok and liq_ok:

            ramp100.append(
                row["exposure_15"]
            )

            active = False

        else:

            ramp100.append(
                0
            )


    df["ramp25"] = ramp25
    df["ramp50"] = ramp50
    df["ramp100"] = ramp100


    df["baseline_return"] = (
        df["spy_return"]
        *
        df["exposure_15"]
        /
        100
    )

    df["ramp25_return"] = (
        df["spy_return"]
        *
        df["ramp25"]
        /
        100
    )

    df["ramp50_return"] = (
        df["spy_return"]
        *
        df["ramp50"]
        /
        100
    )

    df["ramp100_return"] = (
        df["spy_return"]
        *
        df["ramp100"]
        /
        100
    )


    summary = pd.DataFrame(
        [
            {
                "scenario":
                    "BASELINE",

                "avg_exposure":
                    df["exposure_15"].mean(),

                "zero_days":
                    (df["exposure_15"] == 0).sum(),

                **metrics(
                    df["baseline_return"]
                )
            },

            {
                "scenario":
                    "RAMP_25",

                "avg_exposure":
                    df["ramp25"].mean(),

                "zero_days":
                    (df["ramp25"] == 0).sum(),

                **metrics(
                    df["ramp25_return"]
                )
            },

            {
                "scenario":
                    "RAMP_50",

                "avg_exposure":
                    df["ramp50"].mean(),

                "zero_days":
                    (df["ramp50"] == 0).sum(),

                **metrics(
                    df["ramp50_return"]
                )
            },

            {
                "scenario":
                    "RAMP_100",

                "avg_exposure":
                    df["ramp100"].mean(),

                "zero_days":
                    (df["ramp100"] == 0).sum(),

                **metrics(
                    df["ramp100_return"]
                )
            },
        ]
    )


    df.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig"
    )


    print("=" * 70)
    print(
        "FILTER15 RECOVERY RAMP COUNTERFACTUAL"
    )
    print("=" * 70)

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