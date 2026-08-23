from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

PIT_PANEL = (
    ROOT
    / "data"
    / "backtest"
    / "pit_safe"
    / "master_panel_pit_safe_with_sovereign.csv"
)

INITIAL_FILE = (
    ROOT
    / "data"
    / "backtest"
    / "alfred_vintage_82"
    / "NFCI_initial_release.json"
)

LATEST_FILE = (
    ROOT
    / "data"
    / "backtest"
    / "alfred_vintage_82"
    / "NFCI_latest.json"
)

RESULTS = ROOT / "data" / "backtest" / "results"

OUT_DETAIL = RESULTS / "nfci_revision_mismatch_root_cause_detail.csv"
OUT_SUMMARY = RESULTS / "nfci_revision_mismatch_root_cause_summary.txt"


def load_fred_json(path: Path, value_name: str) -> pd.DataFrame:
    obj = json.loads(path.read_text())

    if "error_code" in obj:
        raise RuntimeError(
            f"FRED evidence error: {obj}"
        )

    rows = []

    for x in obj.get("observations", []):
        value = x.get("value")

        if value in {None, "", "."}:
            continue

        try:
            value = float(value)
        except Exception:
            continue

        row = {
            "observation_date": pd.Timestamp(
                x["date"]
            ).normalize(),
            value_name: value,
        }

        if value_name == "initial_value":
            row["first_available_date"] = pd.Timestamp(
                x["realtime_start"]
            ).normalize()

        rows.append(row)

    return (
        pd.DataFrame(rows)
        .sort_values("observation_date")
        .drop_duplicates(
            "observation_date",
            keep="last",
        )
        .reset_index(drop=True)
    )


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("NFCI REVISION / PIT MISMATCH ROOT-CAUSE AUDIT")
    print("=" * 80)
    print()
    print("AUDIT ONLY — no data or decision logic will be modified.")
    print()

    # ------------------------------------------------------------
    # 1. Load frozen PIT panel
    # ------------------------------------------------------------

    panel = pd.read_csv(PIT_PANEL)

    date_col = None

    for candidate in [
        "signal_date",
        "datetime",
        "date",
        "Date",
    ]:
        if candidate in panel.columns:
            date_col = candidate
            break

    if date_col is None:
        raise RuntimeError(
            "Could not identify PIT panel date column."
        )

    panel[date_col] = pd.to_datetime(
        panel[date_col]
    ).dt.normalize()

    # Frozen #3 contract:
    # fred_extras__FCI is the direct NFCI upstream path.
    # Do NOT silently substitute fred_sector__FCI here.
    if "fred_extras__FCI" in panel.columns:
        panel_col = "fred_extras__FCI"
    else:
        raise RuntimeError(
            "Frozen PIT column fred_extras__FCI "
            "does not exist in PIT panel."
        )

    p = panel[
        [date_col, panel_col]
    ].copy()

    p = p.rename(
        columns={
            date_col: "signal_date",
            panel_col: "backtest_value",
        }
    )

    p["backtest_value"] = pd.to_numeric(
        p["backtest_value"],
        errors="coerce",
    )

    print("PIT panel column:", panel_col)
    print("PIT rows:", len(p))

    # ------------------------------------------------------------
    # 2. Load ALFRED evidence
    # ------------------------------------------------------------

    initial = load_fred_json(
        INITIAL_FILE,
        "initial_value",
    )

    latest = load_fred_json(
        LATEST_FILE,
        "latest_value",
    )

    history = initial.merge(
        latest,
        on="observation_date",
        how="left",
    )

    history["was_revised"] = (
        history["latest_value"].notna()
        & (
            (
                history["initial_value"]
                - history["latest_value"]
            ).abs()
            > 1e-10
        )
    )

    print("Initial-release observations:", len(initial))
    print(
        "Revised observations:",
        int(history["was_revised"].sum()),
    )

    # ------------------------------------------------------------
    # 3. Determine what value was actually available on each
    #    backtest signal date.
    #
    # This uses the most recently RELEASED observation,
    # not the observation carrying the same calendar date.
    # ------------------------------------------------------------

    available = history[
        [
            "observation_date",
            "first_available_date",
            "initial_value",
            "latest_value",
            "was_revised",
        ]
    ].copy()

    available = available.sort_values(
        "first_available_date"
    )

    p = p.sort_values("signal_date")

    x = pd.merge_asof(
        p,
        available,
        left_on="signal_date",
        right_on="first_available_date",
        direction="backward",
        allow_exact_matches=True,
    )

    # ------------------------------------------------------------
    # 4. Compare backtest value against:
    #
    # A) actual initial value available at that date
    # B) today's revised/latest value
    #
    # This tells us what the PIT panel resembles.
    # ------------------------------------------------------------

    x["diff_vs_initial"] = (
        x["backtest_value"]
        - x["initial_value"]
    ).abs()

    x["diff_vs_latest"] = (
        x["backtest_value"]
        - x["latest_value"]
    ).abs()

    tol = 1e-8

    x["matches_initial"] = (
        x["backtest_value"].notna()
        & x["initial_value"].notna()
        & (x["diff_vs_initial"] <= tol)
    )

    x["matches_latest"] = (
        x["backtest_value"].notna()
        & x["latest_value"].notna()
        & (x["diff_vs_latest"] <= tol)
    )

    # ------------------------------------------------------------
    # 5. Root-cause classification
    # ------------------------------------------------------------

    def classify(row):
        if pd.isna(row["backtest_value"]):
            return "NO_BACKTEST_VALUE"

        if pd.isna(row["initial_value"]):
            return "NO_ALFRED_VALUE_AVAILABLE"

        if row["matches_initial"]:
            return "PASS_MATCHES_INITIAL_PIT"

        if row["matches_latest"]:
            return "FAIL_MATCHES_REVISED_LATEST"

        return "MISMATCH_NEITHER_INITIAL_NOR_LATEST"

    x["root_cause"] = x.apply(
        classify,
        axis=1,
    )

    # ------------------------------------------------------------
    # 6. Extra diagnostics:
    #    test whether panel is using stale/shifted NFCI.
    # ------------------------------------------------------------

    x["initial_lag_1"] = x["initial_value"].shift(1)
    x["initial_lead_1"] = x["initial_value"].shift(-1)

    x["matches_initial_lag_1"] = (
        x["backtest_value"].notna()
        & x["initial_lag_1"].notna()
        & (
            (
                x["backtest_value"]
                - x["initial_lag_1"]
            ).abs()
            <= tol
        )
    )

    x["matches_initial_lead_1"] = (
        x["backtest_value"].notna()
        & x["initial_lead_1"].notna()
        & (
            (
                x["backtest_value"]
                - x["initial_lead_1"]
            ).abs()
            <= tol
        )
    )

    # ------------------------------------------------------------
    # 7. Save evidence
    # ------------------------------------------------------------

    x.to_csv(
        OUT_DETAIL,
        index=False,
        encoding="utf-8-sig",
    )

    comparable = x[
        x["backtest_value"].notna()
        & x["initial_value"].notna()
    ]

    counts = comparable[
        "root_cause"
    ].value_counts()

    match_initial = int(
        comparable["matches_initial"].sum()
    )

    match_latest = int(
        comparable["matches_latest"].sum()
    )

    lag1 = int(
        comparable["matches_initial_lag_1"].sum()
    )

    lead1 = int(
        comparable["matches_initial_lead_1"].sum()
    )

    total = len(comparable)

    # ------------------------------------------------------------
    # 8. Print simple institutional conclusion
    # ------------------------------------------------------------

    print()
    print("=" * 80)
    print("ROOT-CAUSE RESULT")
    print("=" * 80)

    print("Comparable signal dates:", total)
    print()
    print(
        "Matches actual initial/PIT value:",
        match_initial,
    )
    print(
        "Matches today's revised/latest value:",
        match_latest,
    )
    print(
        "Matches previous available value:",
        lag1,
    )
    print(
        "Matches next available value:",
        lead1,
    )

    print()
    print("CLASSIFICATION")
    print(counts.to_string())

    print()

    if total > 0 and match_latest > match_initial:
        conclusion = (
            "PRIMARY SUSPECT: REVISION LEAKAGE — "
            "PIT panel resembles revised/latest NFCI "
            "more than initial-release NFCI."
        )
    elif total > 0 and match_initial == total:
        conclusion = (
            "PASS — PIT panel matches historically "
            "available initial-release NFCI."
        )
    else:
        conclusion = (
            "ROOT CAUSE NOT YET PROVEN — "
            "panel does not simply match initial or latest values. "
            "Investigate transformation / alignment / source construction."
        )

    print(conclusion)

    summary_lines = [
        "NFCI REVISION / PIT MISMATCH ROOT-CAUSE AUDIT",
        "=" * 80,
        f"Comparable signal dates: {total}",
        f"Matches initial/PIT value: {match_initial}",
        f"Matches revised/latest value: {match_latest}",
        f"Matches previous available value: {lag1}",
        f"Matches next available value: {lead1}",
        "",
        "Classification:",
        counts.to_string(),
        "",
        conclusion,
        "",
        "AUDIT ONLY — no Production or Backtest logic modified.",
    ]

    OUT_SUMMARY.write_text(
        "\n".join(summary_lines),
        encoding="utf-8",
    )

    print()
    print("[OUTPUT]")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)


if __name__ == "__main__":
    main()
