from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

DETAIL_PATH = (
    RESULT_DIR /
    "filter15_release_gate_full_period_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR /
    "filter15_missed_recovery_summary.csv"
)

OUTPUT_PATH = (
    RESULT_DIR /
    "filter15_missed_recovery_detail.csv"
)


def summarize(df, mask, name):

    x = df.loc[mask].copy()

    r60 = x["spy_return_60d"].dropna()

    return {
        "group": name,
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

        "above_5pct_rate":
            (r60 > 5).mean()
            if len(r60)
            else None,

        "above_10pct_rate":
            (r60 > 10).mean()
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

    df = pd.read_csv(
        DETAIL_PATH
    )


    df["signal_date"] = pd.to_datetime(
        df["signal_date"]
    )


    # Current Release
    current = (
        df["current_release"]
        == True
    )

    # Candidate Release
    candidate = (
        df["candidate_release"]
        == True
    )


    # Candidate가 제거한 Recovery
    missed = (
        current
        &
        (~candidate)
    )


    results = []

    results.append(
        summarize(
            df,
            candidate,
            "CANDIDATE_CAPTURED"
        )
    )


    results.append(
        summarize(
            df,
            missed,
            "MISSED_BY_CANDIDATE"
        )
    )


    summary = pd.DataFrame(
        results
    )


    detail = df.loc[
        missed
    ].copy()


    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )


    detail.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 75)
    print(
        "FILTER15 MISSED RECOVERY AUDIT"
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
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()