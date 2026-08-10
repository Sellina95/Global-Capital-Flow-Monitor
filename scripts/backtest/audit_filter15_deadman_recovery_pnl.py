from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np


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

OUTPUT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "deadman_recovery_pnl_summary.csv"
)


def build_recovery_flag(
    row: pd.Series,
) -> bool:
    return bool(
        row["counterfactual_release"]
    )


def calculate_metrics(
    returns: pd.Series,
):

    cumulative = (
        1 + returns
    ).cumprod()

    total_return = (
        cumulative.iloc[-1] - 1
    )

    years = (
        len(returns)
        /
        252
    )

    cagr = (
        cumulative.iloc[-1]
        **
        (1 / years)
        - 1
        if years > 0
        else 0
    )

    rolling_max = cumulative.cummax()

    drawdown = (
        cumulative
        /
        rolling_max
        - 1
    )

    mdd = drawdown.min()

    volatility = (
        returns.std()
        *
        np.sqrt(252)
    )

    sharpe = (
        returns.mean()
        /
        returns.std()
        *
        np.sqrt(252)
        if returns.std() != 0
        else 0
    )

    return {
        "total_return":
            total_return * 100,

        "cagr":
            cagr * 100,

        "mdd":
            mdd * 100,

        "volatility":
            volatility * 100,

        "sharpe":
            sharpe,
    }


def main():

    df = pd.read_csv(INPUT)

    panel = pd.read_csv(PANEL)

    df["signal_date"] = pd.to_datetime(
        df["signal_date"]
    )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"]
    )

    panel = panel[
        [
            "signal_date",
            "SPY",
        ]
    ].copy()

    panel["SPY"] = pd.to_numeric(
        panel["SPY"],
        errors="coerce",
    )

    panel = (
        panel
        .dropna()
        .sort_values("signal_date")
    )

    df = (
        df
        .merge(
            panel,
            on="signal_date",
            how="inner",
        )
        .sort_values("signal_date")
    )


    # SPY daily return
    df["spy_return"] = (
        df["SPY"]
        .pct_change()
        .fillna(0)
    )


    df["recovery_flag"] = (
        df.apply(
            build_recovery_flag,
            axis=1,
        )
    )


    results = []


    scenarios = {
        "production": 0.0,
        "recovery_25": 0.25,
        "recovery_40": 0.40,
        "recovery_50": 0.50,
    }


    for name, recovery_ratio in scenarios.items():

        exposure = []

        for _, row in df.iterrows():

            if (
                name == "production"
                or not row["recovery_flag"]
            ):
                exp = row[
                    "production_exposure"
                ]

            else:
                exp = (
                    row["risk_budget_13"]
                    *
                    recovery_ratio
                )

            exposure.append(exp / 100)


        temp = df.copy()

        temp["exposure"] = exposure


        # 단순 exposure-adjusted equity return
        temp["strategy_return"] = (
            temp["spy_return"]
            *
            temp["exposure"]
        )


        metrics = calculate_metrics(
            temp["strategy_return"]
        )


        metrics["scenario"] = name
        metrics["average_exposure"] = (
            temp["exposure"]
            .mean()
            *
            100
        )

        metrics["recovery_days"] = int(
            (
                temp["recovery_flag"]
                &
                (name != "production")
            )
            .sum()
        )


        results.append(metrics)


    result = pd.DataFrame(results)

    result = result[
        [
            "scenario",
            "average_exposure",
            "recovery_days",
            "total_return",
            "cagr",
            "mdd",
            "volatility",
            "sharpe",
        ]
    ]


    result.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 70)
    print(
        "DEADMAN RECOVERY PNL COUNTERFACTUAL AUDIT"
    )
    print("=" * 70)

    print(result.to_string(index=False))

    print()
    print("Saved:")
    print(OUTPUT)


if __name__ == "__main__":
    main()