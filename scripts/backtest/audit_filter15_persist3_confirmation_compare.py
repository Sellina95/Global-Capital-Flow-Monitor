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
    "filter15_persist3_confirmation_summary.csv"
)

OUTPUT_DETAIL = (
    RESULT_DIR /
    "filter15_persist3_confirmation_detail.csv"
)


def evaluate(
    df: pd.DataFrame,
    mask: pd.Series,
    name: str,
):

    x = df.loc[mask].copy()

    if len(x) == 0:
        return {
            "scenario": name,
            "events": 0,
        }

    r60 = x["spy_return_60d"].dropna()

    return {
        "scenario": name,
        "events": len(x),

        "avg_spy_60d":
            r60.mean(),

        "median_spy_60d":
            r60.median(),

        "positive_60d_rate":
            (r60 > 0).mean(),

        "negative_60d_rate":
            (r60 < 0).mean(),

        "worst_60d":
            r60.min(),

        "best_60d":
            r60.max(),

        "avg_pos_z":
            x["positioning__SP500_POS_Z"].mean(),

        "avg_net_liq":
            x["liquidity__NET_LIQ"].mean(),

        "avg_fci":
            x["fred_sector__FCI"].mean(),
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


    # --------------------------------------------------
    # HY Persistence 3D Event only
    # --------------------------------------------------

    release = release[
        release["persist_3_release"] == True
    ].copy()


    df = release.merge(
        panel[
            [
                "signal_date",

                "positioning__SP500_POS_Z",

                "liquidity__NET_LIQ",

                "fred_sector__FCI",

            ]
        ],
        on="signal_date",
        how="left",
    )


    # --------------------------------------------------
    # Normalize
    # --------------------------------------------------

    numeric_cols = [
        "positioning__SP500_POS_Z",
        "liquidity__NET_LIQ",
        "fred_sector__FCI",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )


    # --------------------------------------------------
    # Confirmation Candidates
    # --------------------------------------------------

    base = pd.Series(
        True,
        index=df.index,
    )


    scenarios = {

        "HY_PERSIST_3D":
            base,

        "HY_PERSIST_3D_POS_Z":
            (
                base
                &
                (df["positioning__SP500_POS_Z"] < 1.5)
            ),

        "HY_PERSIST_3D_NET_LIQ":
            (
                base
                &
                (
                    df["liquidity__NET_LIQ"]
                    >
                    df["liquidity__NET_LIQ"].median()
                )
            ),

        "HY_PERSIST_3D_FCI":
            (
                base
                &
                (
                    df["fred_sector__FCI"]
                    <
                    df["fred_sector__FCI"].median()
                )
            ),

        "HY_PERSIST_3D_COMBINED":
            (
                base
                &
                (df["positioning__SP500_POS_Z"] < 1.5)
                &
                (
                    df["liquidity__NET_LIQ"]
                    >
                    df["liquidity__NET_LIQ"].median()
                )
                &
                (
                    df["fred_sector__FCI"]
                    <
                    df["fred_sector__FCI"].median()
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


    df.to_csv(
        OUTPUT_DETAIL,
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
        "FILTER15 PERSIST3 CONFIRMATION COMPARISON"
    )
    print("=" * 75)

    print(
        summary.to_string(
            index=False
        )
    )


    print("\nSaved:")
    print(SUMMARY_PATH)
    print(OUTPUT_DETAIL)


if __name__ == "__main__":
    main()