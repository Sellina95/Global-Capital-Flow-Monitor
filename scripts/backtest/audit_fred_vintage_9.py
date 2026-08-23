from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data" / "backtest"
ALFRED = DATA / "alfred_vintage_82"
RESULTS = DATA / "results"

RESULTS.mkdir(parents=True, exist_ok=True)

OUT_DETAIL = RESULTS / "fred_vintage_9_detail.csv"
OUT_SUMMARY = RESULTS / "fred_vintage_9_summary.csv"
OUT_TXT = RESULTS / "fred_vintage_9_summary.txt"


# ============================================================
# Frozen upstream source mapping
# ============================================================

SERIES = {
    "NFCI": {
        "raw_file": DATA / "fred_macro_extras.csv",
        "raw_column": "FCI",
    },
    "WTREGEN": {
        "raw_file": DATA / "liquidity_data.csv",
        "raw_column": "TGA",
    },
    "WALCL": {
        "raw_file": DATA / "liquidity_data.csv",
        "raw_column": "WALCL",
    },
    "DFII10": {
        "raw_file": DATA / "fred_macro_sctorallo.csv",
        "raw_column": "DFII10",
    },
    "DGS2": {
        "raw_file": DATA / "fred_macro_sctorallo.csv",
        "raw_column": "DGS2",
    },
    "T10Y2Y": {
        "raw_file": DATA / "fred_macro_sctorallo.csv",
        "raw_column": "T10Y2Y",
    },
    "T10YIE": {
        "raw_file": DATA / "fred_macro_sctorallo.csv",
        "raw_column": "T10YIE",
    },
    "DGS10": {
        "raw_file": DATA / "sovereign_yields.csv",
        "raw_column": "US10Y",
    },
    "BAMLH0A0HYM2": {
        "raw_file": DATA / "credit_spread_data.csv",
        "raw_column": "HY_OAS",
    },
}


TOL = 1e-10


# ============================================================
# Load ALFRED evidence
# ============================================================

def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)

    obj = json.loads(path.read_text())

    if "error_code" in obj:
        raise RuntimeError(
            f"{path.name}: {obj}"
        )

    return obj


def load_alfred(
    series_id: str,
    kind: str,
) -> pd.DataFrame:

    path = ALFRED / f"{series_id}_{kind}.json"

    obj = load_json(path)

    rows = []

    for obs in obj.get("observations", []):
        value = obs.get("value")

        if value in {None, "", "."}:
            continue

        try:
            value = float(value)
        except Exception:
            continue

        row = {
            "observation_date": pd.Timestamp(
                obs["date"]
            ).normalize(),
            f"{kind}_value": value,
        }

        if kind == "initial_release":
            row["first_available_date"] = pd.Timestamp(
                obs["realtime_start"]
            ).normalize()

        rows.append(row)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    return (
        df.sort_values("observation_date")
        .drop_duplicates(
            "observation_date",
            keep="last",
        )
        .reset_index(drop=True)
    )


# ============================================================
# Load frozen backtest raw source
# ============================================================

def load_raw(
    path: Path,
    value_col: str,
) -> pd.DataFrame:

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    date_col = next(
        (
            c for c in df.columns
            if c.lower() in {
                "date",
                "datetime",
                "observation_date",
            }
        ),
        None,
    )

    if date_col is None:
        raise RuntimeError(
            f"{path}: date column not found"
        )

    if value_col not in df.columns:
        raise RuntimeError(
            f"{path}: {value_col} not found"
        )

    out = df[
        [date_col, value_col]
    ].copy()

    out.columns = [
        "observation_date",
        "backtest_raw_value",
    ]

    out["observation_date"] = pd.to_datetime(
        out["observation_date"],
        errors="coerce",
    ).dt.normalize()

    out["backtest_raw_value"] = pd.to_numeric(
        out["backtest_raw_value"],
        errors="coerce",
    )

    return (
        out.dropna(
            subset=[
                "observation_date",
                "backtest_raw_value",
            ]
        )
        .sort_values("observation_date")
        .drop_duplicates(
            "observation_date",
            keep="last",
        )
        .reset_index(drop=True)
    )


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 80)
    print("FRED / ALFRED HISTORICAL VINTAGE AUDIT — 9 UPSTREAM SOURCES")
    print("=" * 80)

    print()
    print(
        "Question: Did the frozen backtest raw data use "
        "the value actually known at the time?"
    )

    print()
    print(
        "AUDIT ONLY — no Production, Backtest or PIT data "
        "will be modified."
    )

    all_detail = []
    summary_rows = []

    for series_id, spec in SERIES.items():

        print()
        print("-" * 80)
        print(series_id)
        print("-" * 80)

        try:
            initial = load_alfred(
                series_id,
                "initial_release",
            )

            latest = load_alfred(
                series_id,
                "latest",
            )

            raw = load_raw(
                spec["raw_file"],
                spec["raw_column"],
            )

            if initial.empty:
                raise RuntimeError(
                    "No initial-release evidence."
                )

            if latest.empty:
                raise RuntimeError(
                    "No latest-value evidence."
                )

            x = initial.merge(
                latest[
                    [
                        "observation_date",
                        "latest_value",
                    ]
                ],
                on="observation_date",
                how="left",
            )

            x = x.merge(
                raw,
                on="observation_date",
                how="inner",
            )

            if x.empty:
                raise RuntimeError(
                    "No comparable observations."
                )

            x["series"] = series_id
            x["raw_file"] = str(
                spec["raw_file"].relative_to(ROOT)
            )
            x["raw_column"] = spec["raw_column"]

            # ----------------------------------------------
            # Revision itself
            # ----------------------------------------------

            x["was_revised"] = (
                x["latest_value"].notna()
                & (
                    (
                        x["initial_release_value"]
                        - x["latest_value"]
                    ).abs()
                    > TOL
                )
            )

            # ----------------------------------------------
            # What did our historical raw file contain?
            # ----------------------------------------------

            x["diff_vs_initial"] = (
                x["backtest_raw_value"]
                - x["initial_release_value"]
            ).abs()

            x["diff_vs_latest"] = (
                x["backtest_raw_value"]
                - x["latest_value"]
            ).abs()

            x["matches_initial"] = (
                x["diff_vs_initial"] <= TOL
            )

            x["matches_latest"] = (
                x["latest_value"].notna()
                & (x["diff_vs_latest"] <= TOL)
            )

            def classify(row):

                if row["matches_initial"]:
                    return "PASS_INITIAL_PIT_VALUE"

                if row["matches_latest"]:
                    return "FAIL_REVISED_LATEST_VALUE"

                return "FAIL_OTHER_HISTORICAL_VINTAGE"

            x["status"] = x.apply(
                classify,
                axis=1,
            )

            comparable = len(x)

            initial_match = int(
                x["matches_initial"].sum()
            )

            latest_match = int(
                x["matches_latest"].sum()
            )

            other_vintage = int(
                (
                    x["status"]
                    == "FAIL_OTHER_HISTORICAL_VINTAGE"
                ).sum()
            )

            revised = int(
                x["was_revised"].sum()
            )

            failures = comparable - initial_match

            if failures == 0:
                gate = "PASS"
            else:
                gate = "FAIL"

            summary_rows.append({
                "series": series_id,
                "raw_file": str(
                    spec["raw_file"].relative_to(ROOT)
                ),
                "raw_column": spec["raw_column"],
                "comparable_rows": comparable,
                "revision_rows": revised,
                "initial_pit_matches": initial_match,
                "revised_latest_matches": latest_match,
                "other_vintage_matches": other_vintage,
                "pit_value_failures": failures,
                "pit_match_pct": (
                    initial_match
                    / comparable
                    * 100
                    if comparable
                    else np.nan
                ),
                "status": gate,
            })

            all_detail.append(x)

            print("Comparable:", comparable)
            print(
                "Correct initial/PIT:",
                initial_match,
            )
            print(
                "Matches current latest:",
                latest_match,
            )
            print(
                "Matches other historical vintage:",
                other_vintage,
            )
            print(
                "Observations revised:",
                revised,
            )
            print("STATUS:", gate)

        except Exception as exc:

            print(
                "UNRESOLVED:",
                exc,
            )

            summary_rows.append({
                "series": series_id,
                "raw_file": str(
                    spec["raw_file"].relative_to(ROOT)
                ),
                "raw_column": spec["raw_column"],
                "comparable_rows": 0,
                "revision_rows": 0,
                "initial_pit_matches": 0,
                "revised_latest_matches": 0,
                "other_vintage_matches": 0,
                "pit_value_failures": 0,
                "pit_match_pct": np.nan,
                "status": "UNRESOLVED",
            })

    # ========================================================
    # Save
    # ========================================================

    summary = pd.DataFrame(summary_rows)

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
        encoding="utf-8-sig",
    )

    if all_detail:
        detail = pd.concat(
            all_detail,
            ignore_index=True,
        )

        detail.to_csv(
            OUT_DETAIL,
            index=False,
            encoding="utf-8-sig",
        )
    else:
        detail = pd.DataFrame()

    pass_count = int(
        (summary["status"] == "PASS").sum()
    )

    fail_count = int(
        (summary["status"] == "FAIL").sum()
    )

    unresolved_count = int(
        (summary["status"] == "UNRESOLVED").sum()
    )

    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    display_cols = [
        "series",
        "comparable_rows",
        "initial_pit_matches",
        "revised_latest_matches",
        "other_vintage_matches",
        "pit_match_pct",
        "status",
    ]

    print(
        summary[display_cols].to_string(
            index=False
        )
    )

    print()
    print("PASS:", pass_count)
    print("FAIL:", fail_count)
    print("UNRESOLVED:", unresolved_count)

    if fail_count > 0:
        overall = (
            "FRED VINTAGE GATE: FAIL — "
            "historical vintage contamination exists."
        )
    elif unresolved_count > 0:
        overall = (
            "FRED VINTAGE GATE: UNRESOLVED"
        )
    else:
        overall = (
            "FRED VINTAGE GATE: PASS"
        )

    print()
    print(overall)

    txt = [
        "FRED / ALFRED HISTORICAL VINTAGE AUDIT — 9 SOURCES",
        "=" * 80,
        "",
        summary[display_cols].to_string(index=False),
        "",
        f"PASS: {pass_count}",
        f"FAIL: {fail_count}",
        f"UNRESOLVED: {unresolved_count}",
        "",
        overall,
        "",
        "AUDIT ONLY — no Production or Backtest logic modified.",
    ]

    OUT_TXT.write_text(
        "\n".join(txt),
        encoding="utf-8",
    )

    print()
    print("[OUTPUT]")
    print(OUT_SUMMARY)
    print(OUT_DETAIL)
    print(OUT_TXT)


if __name__ == "__main__":
    main()
