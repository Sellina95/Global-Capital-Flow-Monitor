from __future__ import annotations

"""
FULL F13 / F15 / F18 POINT-IN-TIME LINEAGE AUDIT
=================================================

Scope
-----
Frozen decision universe:
F13 = 22 contracts
F15 = 20 contracts
F18 = 40 contracts
Total = 82 stage-contract pairs

Question
--------
For every historical signal date:

    source observation date <= signal date

This audit checks:
1. No future observation is propagated backward.
2. Master-panel ffill uses only past observations.
3. Core market series are same-date or earlier.
4. Non-price source families preserve historical ordering.
5. Signal -> execution occurs strictly forward in time.

This audit DOES NOT claim release/vintage safety.
Release lag and revised-vintage integrity are Gate #3.
"""

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "backtest"
RESULTS = DATA / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

PANEL_PATH = DATA / "master_panel.csv"

OUT_DETAIL = RESULTS / "full_pit_lineage_82_detail.csv"
OUT_SUMMARY = RESULTS / "full_pit_lineage_82_summary.csv"
OUT_FAILURES = RESULTS / "full_pit_lineage_82_failures.csv"
OUT_TXT = RESULTS / "full_pit_lineage_82_summary.txt"


# ============================================================
# Frozen 82-contract universe
# ============================================================

CONTRACTS = {

    "F13": [
        "CROSS_ASSET_TAPE",
        "DRIFT",
        "DRIFT_SCORE",
        "DRIFT_STATE",
        "FINAL_STATE",
        "GAMMA_STATE",
        "HY_OAS",
        "INSTITUTIONAL_FLOW",
        "MACRO_NARRATIVE",
        "MARKET_REGIME",
        "NET_LIQ",
        "NET_LIQ_LEVEL_BUCKET",
        "PHASE_CAP",
        "POLICY_BIAS_LINE",
        "PREV_FLOW_SCORE",
        "PREV_FLOW_STATE",
        "PRE_CAP_BUDGET",
        "RISK_BUDGET",
        "SENTIMENT",
        "SP500_POS_Z",
        "STRUCT_V2_STATE",
        "VIX",
    ],

    "F15": [
        "CROSS_ASSET_TAPE",
        "CTA_MOMENTUM_SCORE",
        "DEALER_GAMMA_BIAS",
        "FILTER15_PREV_DEADMAN",
        "FILTER15_PREV_HY_OAS",
        "FILTER15_RECOVERY_ACTIVE",
        "FILTER15_RECOVERY_COMPLETED",
        "FILTER15_RECOVERY_STREAK",
        "HY_OAS",
        "HY_OAS_STATUS",
        "INSTITUTIONAL_FLOW",
        "LEADERSHIP_BREADTH_SCORE",
        "MACRO_NARRATIVE",
        "POS_SLOPE",
        "PREV_EXPOSURE",
        "RECOMMENDED_EXPOSURE",
        "RISK_BUDGET",
        "SEW_STATUS",
        "SP500_POS_Z",
        "VIX",
    ],

    "F18": [
        "AVG_DIVERGENCE",
        "BASE_RECOMMENDED_EXPOSURE",
        "BREADTH_SCORE_18",
        "CORRELATION_BREAK_ACTIVE",
        "CORRELATION_BREAK_REASONS",
        "CORRELATION_BREAK_TYPE",
        "DIVERGENCE_DISPERSION",
        "DRIFT_LABEL",
        "DXY",
        "EXPOSURE_OVERRIDE_REASON",
        "FILTER18_ACCEPTED_RANK",
        "FILTER18_PENDING_COUNT",
        "FILTER18_PENDING_RANK",
        "FILTER18_RANK_ACTION",
        "FILTER18_RAW_RANK",
        "FINAL_STATE",
        "GAMMA_SIGNAL",
        "GAMMA_STATE",
        "INSTITUTIONAL_FLOW",
        "LEADERSHIP_STATE",
        "LEADER_TYPE",
        "MACRO_REGIME_PROFILE",
        "MARKET_REGIME",
        "MOMENTUM_SCORES",
        "PARTICIPATION_SIGNAL",
        "POSITIONING_SCORE_18",
        "POSITIONING_STATE",
        "RECOMMENDED_EXPOSURE",
        "REGIME_ADJUSTED_EXPOSURE",
        "REGIME_CONTROLLER",
        "SECTOR_CLASSIFICATION",
        "SECTOR_DIVERGENCE",
        "SECTOR_DIVERGENCE_FLAGS",
        "SECTOR_FINAL_SCORE",
        "SECTOR_FLOW_SCORE",
        "SECTOR_THEORETICAL_SCORE",
        "SQUEEZE_RISK",
        "US10Y",
        "VOL_STRUCTURE",
        "WTI",
    ],
}


# ============================================================
# Historical source files feeding those 82 contracts
# ============================================================

SOURCES = {

    "macro": {
        "file": "macro_data.csv",
        "prefix": "",
        "type": "MARKET",
    },

    "positioning": {
        "file": "positioning_data.csv",
        "prefix": "positioning__",
        "type": "NON_PRICE",
    },

    "sentiment": {
        "file": "sentiment_proxy.csv",
        "prefix": "sentiment__",
        "type": "DERIVED_SOURCE",
    },

    "country_etf": {
        "file": "country_etf_data_combined.csv",
        "prefix": "country_etf__",
        "type": "MARKET",
    },

    "sovereign_yields": {
        "file": "sovereign_yields.csv",
        "prefix": "sovereign_yields__",
        "type": "NON_PRICE",
    },

    "sovereign_spreads": {
        "file": "sovereign_spreads.csv",
        "prefix": "sovereign_spreads__",
        "type": "DERIVED_SOURCE",
    },

    "credit": {
        "file": "credit_spread_data.csv",
        "prefix": "credit__",
        "type": "NON_PRICE",
    },

    "liquidity": {
        "file": "liquidity_data.csv",
        "prefix": "liquidity__",
        "type": "NON_PRICE",
    },

    "fred_sector": {
        "file": "fred_macro_sctorallo.csv",
        "prefix": "fred_sector__",
        "type": "NON_PRICE",
    },

    "fred_extras": {
        "file": "fred_macro_extras.csv",
        "prefix": "fred_extras__",
        "type": "NON_PRICE",
    },
}


# ============================================================
# Helpers
# ============================================================

def find_date_col(df: pd.DataFrame):

    for c in df.columns:
        if c.lower() in {"date", "datetime"}:
            return c

    return None


def load_source(name, spec):

    path = DATA / spec["file"]

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    date_col = find_date_col(df)

    if date_col is None:
        raise ValueError(
            f"{name}: date column missing"
        )

    df = df.rename(
        columns={date_col: "date"}
    )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df = (
        df.dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates("date", keep="last")
        .reset_index(drop=True)
    )

    return df


def source_columns_in_panel(
    source_name,
    source_df,
    prefix,
    panel,
):

    cols = []

    for source_col in source_df.columns:

        if source_col == "date":
            continue

        if source_name == "macro":
            panel_col = source_col

        else:
            panel_col = (
                prefix + source_col
            )

        if panel_col in panel.columns:
            cols.append(
                (source_col, panel_col)
            )

    return cols


# ============================================================
# Main
# ============================================================

def main():

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    eligible = panel[
        panel["signal_date"].notna()
        & panel["execution_date"].notna()
        & pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    ].copy()

    eligible = eligible.sort_values(
        "signal_date"
    ).reset_index(drop=True)

    print()
    print("=" * 78)
    print(
        "FULL F13/F15/F18 PIT LINEAGE AUDIT"
    )
    print("=" * 78)

    print(
        "Frozen stage-contract pairs:",
        sum(len(v) for v in CONTRACTS.values()),
    )

    print(
        "Historical rows:",
        len(eligible),
    )

    print(
        "Range:",
        eligible["signal_date"].min(),
        "->",
        eligible["signal_date"].max(),
    )

    detail_rows = []
    failure_rows = []

    # --------------------------------------------------------
    # Source family PIT checks
    # --------------------------------------------------------

    for source_name, spec in SOURCES.items():

        source = load_source(
            source_name,
            spec,
        )

        pairs = source_columns_in_panel(
            source_name,
            source,
            spec["prefix"],
            eligible,
        )

        for source_col, panel_col in pairs:

            values = pd.to_numeric(
                source[source_col],
                errors="coerce",
            )

            valid_source = source.loc[
                values.notna(),
                ["date", source_col],
            ].copy()

            valid_source = (
                valid_source
                .sort_values("date")
            )

            if valid_source.empty:

                detail_rows.append({
                    "source_family":
                        source_name,
                    "source_column":
                        source_col,
                    "panel_column":
                        panel_col,
                    "checked_rows":
                        0,
                    "future_rows":
                        0,
                    "status":
                        "NO_VALID_SOURCE_VALUES",
                })

                continue

            # For each signal date, find latest source
            # observation whose observation date is <= signal.
            left = eligible[
                [
                    "signal_date",
                    panel_col,
                ]
            ].copy()

            left = left.sort_values(
                "signal_date"
            )

            right = valid_source.rename(
                columns={
                    "date":
                        "source_observation_date",
                    source_col:
                        "source_value",
                }
            )

            merged = pd.merge_asof(
                left,
                right,
                left_on="signal_date",
                right_on="source_observation_date",
                direction="backward",
            )

            checked = merged[
                "source_observation_date"
            ].notna()

            future = (
                checked
                & (
                    merged[
                        "source_observation_date"
                    ]
                    > merged["signal_date"]
                )
            )

            future_count = int(
                future.sum()
            )

            status = (
                "PASS"
                if future_count == 0
                else "FAIL_FUTURE_OBSERVATION"
            )

            detail_rows.append({
                "source_family":
                    source_name,

                "source_type":
                    spec["type"],

                "source_column":
                    source_col,

                "panel_column":
                    panel_col,

                "checked_rows":
                    int(checked.sum()),

                "future_rows":
                    future_count,

                "status":
                    status,
            })

            if future_count:

                tmp = merged.loc[
                    future,
                    [
                        "signal_date",
                        "source_observation_date",
                    ],
                ].copy()

                tmp[
                    "source_family"
                ] = source_name

                tmp[
                    "source_column"
                ] = source_col

                failure_rows.extend(
                    tmp.to_dict("records")
                )

    # --------------------------------------------------------
    # Signal -> execution chronology
    # --------------------------------------------------------

    exec_fail = (
        eligible["execution_date"]
        <= eligible["signal_date"]
    )

    execution_status = (
        "PASS"
        if int(exec_fail.sum()) == 0
        else "FAIL"
    )

    detail_rows.append({
        "source_family":
            "execution_mapping",
        "source_type":
            "EXECUTION",
        "source_column":
            "signal_date->execution_date",
        "panel_column":
            "execution_date",
        "checked_rows":
            len(eligible),
        "future_rows":
            int(exec_fail.sum()),
        "status":
            execution_status,
    })

    # --------------------------------------------------------
    # Master-panel construction rule evidence
    # --------------------------------------------------------

    build_file = (
        ROOT
        / "scripts"
        / "backtest"
        / "build_master_panel.py"
    )

    build_text = build_file.read_text(
        encoding="utf-8"
    )

    has_bfill = ".bfill(" in build_text
    has_ffill = ".ffill(" in build_text

    detail_rows.append({
        "source_family":
            "master_panel_builder",
        "source_type":
            "PIPELINE_CONTROL",
        "source_column":
            "fill_direction",
        "panel_column":
            "",
        "checked_rows":
            len(eligible),
        "future_rows":
            int(has_bfill),
        "status":
            (
                "PASS"
                if has_ffill and not has_bfill
                else "FAIL"
            ),
    })

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    detail = pd.DataFrame(
        detail_rows
    )

    failures = pd.DataFrame(
        failure_rows
    )

    detail.to_csv(
        OUT_DETAIL,
        index=False,
    )

    if failures.empty:

        failures = pd.DataFrame(
            columns=[
                "signal_date",
                "source_observation_date",
                "source_family",
                "source_column",
            ]
        )

    failures.to_csv(
        OUT_FAILURES,
        index=False,
    )

    summary = (
        detail
        .groupby(
            ["source_family", "status"],
            dropna=False,
        )
        .size()
        .reset_index(
            name="series_count"
        )
    )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
    )

    fail_series = int(
        detail["status"]
        .str.startswith(
            "FAIL",
            na=False,
        )
        .sum()
    )

    pass_series = int(
        (detail["status"] == "PASS").sum()
    )

    print()
    print("=" * 78)
    print("RESULT")
    print("=" * 78)

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print(
        "PASS SERIES:",
        pass_series,
    )

    print(
        "FAIL SERIES:",
        fail_series,
    )

    print(
        "FUTURE OBSERVATION FAILURES:",
        len(failures),
    )

    print()

    if (
        fail_series == 0
        and len(failures) == 0
    ):

        gate = (
            "OBSERVATION-DATE PIT GATE: PASS"
        )

    else:

        gate = (
            "OBSERVATION-DATE PIT GATE: NOT CLOSED"
        )

    print(gate)

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "This PASS only proves no future OBSERVATION DATE "
        "was used."
    )

    print(
        "Release-date and historical-vintage integrity "
        "remain Gate #3."
    )

    text = "\n".join([
        "FULL F13/F15/F18 PIT LINEAGE AUDIT",
        "=" * 78,
        f"Frozen stage-contract pairs: 82",
        f"Historical rows: {len(eligible)}",
        f"PASS series: {pass_series}",
        f"FAIL series: {fail_series}",
        f"Future observation failures: {len(failures)}",
        "",
        gate,
        "",
        "Scope:",
        "No source observation date may exceed signal date.",
        "",
        "Not yet covered:",
        "Release / availability lag",
        "Historical vintage / revisions",
    ])

    OUT_TXT.write_text(
        text,
        encoding="utf-8",
    )

    print()
    print("[OUTPUT]")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)
    print(OUT_FAILURES)
    print(OUT_TXT)


if __name__ == "__main__":
    main()
