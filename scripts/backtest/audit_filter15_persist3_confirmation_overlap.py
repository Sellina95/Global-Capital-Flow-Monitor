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
    "filter15_persist3_confirmation_overlap_summary.csv"
)

DETAIL_OUTPUT = (
    RESULT_DIR /
    "filter15_persist3_confirmation_overlap_detail.csv"
)


def evaluate(
    df: pd.DataFrame,
    mask: pd.Series,
    name: str,
):

    x = df.loc[mask].copy()

    r60 = x["spy_return_60d"].dropna()

    return {
        "group": name,
        "events": len(x),

        "avg_spy_60d":
            r60.mean()
            if len(r60)
            else None,

        "median_spy_60d":
            r60.median()
            if len(r60)
            else None,

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

        "avg_pos_z":
            x["positioning__SP500_POS_Z"].mean()
            if len(x)
            else None,

        "avg_net_liq":
            x["liquidity__NET_LIQ"].mean()
            if len(x)
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


    # HY Persistence 3D만
    release = release[
        release["persist_3_release"] == True
    ].copy()


    df = release.merge(
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


    for col in [
        "positioning__SP500_POS_Z",
        "liquidity__NET_LIQ",
    ]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )


    # --------------------------------------------------
    # Confirmation Conditions
    # --------------------------------------------------

    pos_filter = (
        df["positioning__SP500_POS_Z"] < 1.5
    )


    # 이전과 동일하게 median 기반은 탐색용
    liq_threshold = (
        df["liquidity__NET_LIQ"]
        .median()
    )

    liq_filter = (
        df["liquidity__NET_LIQ"]
        >
        liq_threshold
    )


    df["POS_Z_PASS"] = pos_filter
    df["NET_LIQ_PASS"] = liq_filter


    # --------------------------------------------------
    # Groups
    # --------------------------------------------------

    groups = {

        "BOTH":
            pos_filter & liq_filter,

        "POS_Z_ONLY":
            pos_filter & ~liq_filter,

        "NET_LIQ_ONLY":
            ~pos_filter & liq_filter,

        "NEITHER":
            ~pos_filter & ~liq_filter,

    }


    results = []

    for name, mask in groups.items():

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


    df.to_csv(
        DETAIL_OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 75)
    print(
        "FILTER15 PERSIST3 CONFIRMATION OVERLAP AUDIT"
    )
    print("=" * 75)

    print(
        f"Total HY_PERSIST_3D events : {len(df)}"
    )

    print()

    print(
        summary.to_string(
            index=False
        )
    )


    print("\nSaved:")
    print(SUMMARY_PATH)
    print(DETAIL_OUTPUT)


if __name__ == "__main__":
    main()