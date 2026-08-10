from __future__ import annotations

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

EPISODE_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "deadman_recovery_episode_detail.csv"
)

PANEL_PATH = (
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
    / "deadman_recovery_context_analysis.csv"
)


def main():

    episodes = pd.read_csv(
        EPISODE_PATH
    )

    panel = pd.read_csv(
        PANEL_PATH
    )


    episodes["start_date"] = pd.to_datetime(
        episodes["start_date"],
        errors="coerce",
    )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"],
        errors="coerce",
    )


    # --------------------------------------------------
    # Recovery Episode 시작일만 분석
    # --------------------------------------------------

    result = episodes[
        [
            "episode_id",
            "start_date",
            "duration_days",
            "spy_return_60d_avg",
        ]
    ].copy()


    # --------------------------------------------------
    # 필요한 Market Context attach
    # --------------------------------------------------

    context_cols = [
    "signal_date",

    # Credit
    "credit__HY_OAS",

    # Volatility
    "VIX",

    # Liquidity
    "liquidity__NET_LIQ",

    # Positioning
    "positioning__SP500_POS_Z",
    "positioning__DEALER_GAMMA_BIAS",
    "positioning__CTA_MOMENTUM_SCORE",

    # Macro
    "fred_sector__FCI",
    "fred_sector__REAL_RATE",
    "fred_sector__T10Y2Y",

    ]


    available_cols = [
        c
        for c in context_cols
        if c in panel.columns
    ]


    panel_context = panel[
        available_cols
    ].copy()


    panel_context = panel_context.rename(
        columns={
            "signal_date": "start_date"
        }
    )


    result = result.merge(
        panel_context,
        on="start_date",
        how="left",
    )


    # --------------------------------------------------
    # Classification
    # --------------------------------------------------

    result["classification"] = "NORMAL"


    result.loc[
        result["spy_return_60d_avg"] < 0,
        "classification"
    ] = "FALSE_POSITIVE"


    result = result.sort_values(
        "spy_return_60d_avg"
    )


    result.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 70)
    print(
        "FILTER15 RECOVERY CONTEXT ANALYSIS"
    )
    print("=" * 70)


    print(
        result.to_string(index=False)
    )


    print()
    print("Saved:")
    print(OUTPUT)



if __name__ == "__main__":
    main()