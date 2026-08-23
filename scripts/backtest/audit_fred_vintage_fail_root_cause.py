from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"

INPUT = RESULTS / "fred_vintage_9_detail.csv"

OUT_ALL = RESULTS / "fred_vintage_fail_root_cause.csv"
OUT_ISOLATED = RESULTS / "fred_vintage_isolated_mismatches.csv"
OUT_MATERIAL = RESULTS / "fred_vintage_material_contamination.csv"
OUT_SUMMARY = RESULTS / "fred_vintage_fail_root_cause_summary.txt"

MATERIAL = {
    "NFCI",
    "WTREGEN",
    "WALCL",
}

ISOLATED = {
    "DGS2",
    "T10Y2Y",
    "T10YIE",
    "DGS10",
}


def main():

    print("=" * 80)
    print("FRED VINTAGE FAIL — ROOT CAUSE / BLAST-RADIUS PRE-AUDIT")
    print("=" * 80)
    print()
    print("AUDIT ONLY — no data or decision logic will be modified.")

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Missing prior audit detail: {INPUT}"
        )

    df = pd.read_csv(INPUT)

    required = {
        "series",
        "observation_date",
        "first_available_date",
        "initial_release_value",
        "latest_value",
        "backtest_raw_value",
        "was_revised",
        "matches_initial",
        "matches_latest",
        "status",
    }

    missing = required - set(df.columns)

    if missing:
        raise RuntimeError(
            f"Missing required columns: {sorted(missing)}"
        )

    df["observation_date"] = pd.to_datetime(
        df["observation_date"],
        errors="coerce",
    )

    df["first_available_date"] = pd.to_datetime(
        df["first_available_date"],
        errors="coerce",
    )

    for col in [
        "initial_release_value",
        "latest_value",
        "backtest_raw_value",
    ]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    # Only actual PIT mismatches.
    fail = df[
        df["matches_initial"] != True
    ].copy()

    fail["abs_diff_vs_initial"] = (
        fail["backtest_raw_value"]
        - fail["initial_release_value"]
    ).abs()

    fail["abs_diff_vs_latest"] = (
        fail["backtest_raw_value"]
        - fail["latest_value"]
    ).abs()

    fail["signed_diff_vs_initial"] = (
        fail["backtest_raw_value"]
        - fail["initial_release_value"]
    )

    fail["release_lag_days"] = (
        fail["first_available_date"]
        - fail["observation_date"]
    ).dt.days

    fail["root_cause_bucket"] = np.select(
        [
            fail["matches_latest"] == True,
            (
                (fail["matches_latest"] != True)
                & (fail["was_revised"] == True)
            ),
        ],
        [
            "MATCHES_REVISED_LATEST",
            "MATCHES_OTHER_HISTORICAL_VINTAGE",
        ],
        default="UNRESOLVED_MISMATCH",
    )

    fail["severity_group"] = np.select(
        [
            fail["series"].isin(MATERIAL),
            fail["series"].isin(ISOLATED),
        ],
        [
            "MATERIAL_CONTAMINATION",
            "ISOLATED_MISMATCH",
        ],
        default="OTHER",
    )

    fail = fail.sort_values(
        ["severity_group", "series", "observation_date"]
    )

    fail.to_csv(
        OUT_ALL,
        index=False,
        encoding="utf-8-sig",
    )

    material = fail[
        fail["series"].isin(MATERIAL)
    ].copy()

    isolated = fail[
        fail["series"].isin(ISOLATED)
    ].copy()

    material.to_csv(
        OUT_MATERIAL,
        index=False,
        encoding="utf-8-sig",
    )

    isolated.to_csv(
        OUT_ISOLATED,
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # Summary by source
    # --------------------------------------------------------

    summary_rows = []

    for series, x in fail.groupby("series"):

        latest_matches = int(
            (x["matches_latest"] == True).sum()
        )

        other_vintage = int(
            (
                x["root_cause_bucket"]
                == "MATCHES_OTHER_HISTORICAL_VINTAGE"
            ).sum()
        )

        unresolved = int(
            (
                x["root_cause_bucket"]
                == "UNRESOLVED_MISMATCH"
            ).sum()
        )

        summary_rows.append({
            "series": series,
            "mismatch_rows": len(x),
            "first_mismatch": x["observation_date"].min(),
            "last_mismatch": x["observation_date"].max(),
            "matches_latest": latest_matches,
            "other_historical_vintage": other_vintage,
            "unresolved": unresolved,
            "max_abs_diff": x[
                "abs_diff_vs_initial"
            ].max(),
            "median_abs_diff": x[
                "abs_diff_vs_initial"
            ].median(),
        })

    summary = pd.DataFrame(summary_rows)

    if not summary.empty:
        summary = summary.sort_values(
            "mismatch_rows",
            ascending=False,
        )

    print()
    print("=" * 80)
    print("ROOT-CAUSE SUMMARY")
    print("=" * 80)

    if summary.empty:
        print("No mismatches.")
    else:
        print(summary.to_string(index=False))

    print()
    print("=" * 80)
    print("ISOLATED MISMATCHES — FULL ROWS")
    print("=" * 80)

    cols = [
        "series",
        "observation_date",
        "first_available_date",
        "initial_release_value",
        "backtest_raw_value",
        "latest_value",
        "signed_diff_vs_initial",
        "root_cause_bucket",
    ]

    if isolated.empty:
        print("NONE")
    else:
        print(
            isolated[cols].to_string(
                index=False
            )
        )

    print()
    print("=" * 80)
    print("MATERIAL CONTAMINATION")
    print("=" * 80)

    for series in ["NFCI", "WTREGEN", "WALCL"]:

        x = material[
            material["series"] == series
        ]

        print()
        print(series)
        print("-" * 40)

        if x.empty:
            print("No mismatch.")
            continue

        print("Mismatch rows:", len(x))
        print(
            "Period:",
            x["observation_date"].min().date(),
            "->",
            x["observation_date"].max().date(),
        )
        print(
            "Matches revised latest:",
            int((x["matches_latest"] == True).sum()),
        )
        print(
            "Other historical vintage:",
            int(
                (
                    x["root_cause_bucket"]
                    == "MATCHES_OTHER_HISTORICAL_VINTAGE"
                ).sum()
            ),
        )
        print(
            "Median abs difference:",
            x["abs_diff_vs_initial"].median(),
        )
        print(
            "Max abs difference:",
            x["abs_diff_vs_initial"].max(),
        )

    lines = [
        "FRED VINTAGE FAIL — ROOT CAUSE AUDIT",
        "=" * 80,
        "",
        "AUDIT ONLY — no Production / Backtest logic modified.",
        "",
        "SOURCE SUMMARY",
        "-" * 80,
        summary.to_string(index=False)
        if not summary.empty
        else "No mismatches.",
        "",
        "ISOLATED MISMATCHES",
        "-" * 80,
        isolated[cols].to_string(index=False)
        if not isolated.empty
        else "NONE",
        "",
        "Interpretation:",
        "MATERIAL = NFCI / WTREGEN / WALCL",
        "ISOLATED = DGS2 / T10Y2Y / T10YIE / DGS10",
        "",
        "No repair should be performed until these mismatches are reviewed.",
    ]

    OUT_SUMMARY.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print()
    print("[OUTPUT]")
    print(OUT_ALL)
    print(OUT_ISOLATED)
    print(OUT_MATERIAL)
    print(OUT_SUMMARY)


if __name__ == "__main__":
    main()
