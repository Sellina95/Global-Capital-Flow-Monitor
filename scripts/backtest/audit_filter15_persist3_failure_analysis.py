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

OUTPUT_DETAIL = (
    RESULT_DIR /
    "filter15_persist3_failure_detail.csv"
)

OUTPUT_SUMMARY = (
    RESULT_DIR /
    "filter15_persist3_failure_summary.csv"
)


FEATURES = [
    "hy_oas_today",
    "vix_today",
    "credit__HY_OAS",
    "liquidity__NET_LIQ",
    "positioning__SP500_POS_Z",
    "positioning__DEALER_GAMMA_BIAS",
    "positioning__CTA_MOMENTUM_SCORE",
    "fred_sector__FCI",
    "fred_sector__REAL_RATE",
    "fred_sector__T10Y2Y",
]


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


    # Persistence 3D만 추출
    release = release[
        release["persist_3_release"] == True
    ].copy()


    if len(release) == 0:
        raise ValueError(
            "No HY_PERSIST_3D release events found"
        )


    # Market Context Merge

    context_cols = [
        "signal_date"
    ] + [
        c for c in FEATURES
        if c in panel.columns
    ]

    df = release.merge(
        panel[context_cols],
        on="signal_date",
        how="left",
    )


    df["result"] = (
        df["spy_return_60d"]
        > 0
    ).map(
        {
            True: "SUCCESS",
            False: "FAILURE",
        }
    )


    # --------------------------------------------------
    # Detail
    # --------------------------------------------------

    df = df.sort_values(
        "spy_return_60d"
    )


    df.to_csv(
        OUTPUT_DETAIL,
        index=False,
        encoding="utf-8-sig",
    )


    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    summary_rows = []


    for label, group in df.groupby("result"):

        row = {
            "classification": label,
            "events": len(group),

            "avg_spy_60d":
                group["spy_return_60d"].mean(),

            "median_spy_60d":
                group["spy_return_60d"].median(),

        }


        for col in FEATURES:

            if col in group.columns:

                row[
                    f"avg_{col}"
                ] = group[col].mean()


        summary_rows.append(row)


    summary = pd.DataFrame(
        summary_rows
    )


    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 75)
    print(
        "FILTER15 HY_PERSIST_3D FAILURE ANALYSIS"
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


    print("\nWorst Recovery Cases")

    print(
        df[
            [
                "signal_date",
                "hy_oas_today",
                "vix_today",
                "spy_return_60d",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


    print("\nSaved:")
    print(OUTPUT_DETAIL)
    print(OUTPUT_SUMMARY)


if __name__ == "__main__":
    main()