"""
Filter13 Input Lineage Audit - Gate 1

Purpose
-------
Verify that historical Filter13 attribution inputs are Point-in-Time safe.

This audit DOES NOT:
- modify production code
- modify backtest code
- recalculate Filter13
- infer missing historical values
- use current insights JSON files

It audits the already-generated:
    filter13_budget_attribution_final_daily.csv

Core rule
---------
For every historical signal date:

    ASOF_DATE <= SIGNAL_DATE

Any ASOF date later than signal date is a FUTURE LEAK.

Missing ASOF is NOT automatically a leak.
It is classified separately as:
- MISSING_ASOF
- NOT_APPLICABLE
- REVIEW_REQUIRED

Gate 1 scope
------------
1. Liquidity
2. HY / Credit
3. FRED extras
4. Sovereign
5. Sentiment
6. Positioning

Additional checks
-----------------
- source file existence
- source date coverage
- ASOF date exists in source history where possible
- future-date leakage
- stale observations
- audit summary

IMPORTANT
---------
PASS here means:
"No future ASOF was detected for the explicitly traceable inputs."

It does NOT yet prove every derived feature
(Drift/Gamma/Flow/Structural/etc.) is fully PIT-safe.
Those require dependency-level lineage in Gate 2.
"""

from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

INPUT_AUDIT_FILE = (
    RESULT_DIR
    / "filter13_budget_attribution_final_daily.csv"
)

OUTPUT_DAILY = (
    RESULT_DIR
    / "filter13_input_lineage_daily.csv"
)

OUTPUT_SUMMARY = (
    RESULT_DIR
    / "filter13_input_lineage_summary.csv"
)

OUTPUT_TXT = (
    RESULT_DIR
    / "filter13_input_lineage_summary.txt"
)


# ============================================================
# Source candidates
#
# We intentionally search known project locations rather than
# assuming one hard-coded filename is always correct.
# ============================================================

SOURCE_CANDIDATES = {

    "liquidity": [
        ROOT / "data" / "liquidity_data.csv",
        ROOT / "data" / "backtest" / "liquidity_data.csv",
    ],

    "hy": [
        ROOT / "data" / "credit_spread_data.csv",
        ROOT / "data" / "backtest" / "credit_spread_data.csv",
    ],

    "fred": [
        ROOT / "data" / "fred_macro_extras.csv",
        ROOT / "data" / "backtest" / "fred_macro_extras.csv",
    ],

    "sovereign": [
        ROOT / "data" / "sovereign_spreads.csv",
        ROOT / "data" / "sovereign_spread_data.csv",
        ROOT / "data" / "backtest" / "sovereign_spreads.csv",
        ROOT / "data" / "backtest" / "sovereign_spread_data.csv",
    ],

    "sentiment": [
        ROOT / "data" / "sentiment_proxy.csv",
        ROOT / "data" / "sentiment_data.csv",
        ROOT / "data" / "backtest" / "sentiment_proxy.csv",
        ROOT / "data" / "backtest" / "sentiment_data.csv",
    ],

    "positioning": [
        ROOT / "data" / "positioning_data.csv",
        ROOT / "data" / "backtest" / "positioning_data.csv",
    ],
}


ASOF_COLUMNS = {

    "liquidity": "_liq_asof",

    "hy": "_hy_asof",

    "fred": "_fred_asof",

    "sovereign": "_sov_asof",

    "sentiment": "_sentiment_asof",

    "positioning": "_pos_asof",
}


# ============================================================
# Helpers
# ============================================================

def find_existing_source(
    candidates,
) -> Optional[Path]:

    for path in candidates:

        if path.exists():
            return path

    return None


def detect_date_column(
    df: pd.DataFrame,
) -> Optional[str]:

    preferred = [
        "date",
        "DATE",
        "Date",
        "asof",
        "ASOF",
        "timestamp",
        "Timestamp",
    ]

    for col in preferred:

        if col in df.columns:
            return col

    return None


def load_source_metadata(
    name: str,
    candidates,
) -> Dict[str, Any]:

    path = find_existing_source(
        candidates
    )

    if path is None:

        return {
            "source_name": name,
            "source_exists": False,
            "source_path": None,
            "date_column": None,
            "min_date": None,
            "max_date": None,
            "dates": set(),
            "error": "SOURCE_NOT_FOUND",
        }

    try:

        df = pd.read_csv(path)

        date_col = detect_date_column(
            df
        )

        if date_col is None:

            return {
                "source_name": name,
                "source_exists": True,
                "source_path": str(path),
                "date_column": None,
                "min_date": None,
                "max_date": None,
                "dates": set(),
                "error": "DATE_COLUMN_NOT_FOUND",
            }

        dates = pd.to_datetime(
            df[date_col],
            errors="coerce",
        ).dropna()

        normalized_dates = set(
            dates.dt.normalize()
        )

        return {
            "source_name": name,
            "source_exists": True,
            "source_path": str(path),
            "date_column": date_col,
            "min_date": (
                dates.min()
                if not dates.empty
                else None
            ),
            "max_date": (
                dates.max()
                if not dates.empty
                else None
            ),
            "dates": normalized_dates,
            "error": None,
        }

    except Exception as exc:

        return {
            "source_name": name,
            "source_exists": True,
            "source_path": str(path),
            "date_column": None,
            "min_date": None,
            "max_date": None,
            "dates": set(),
            "error": repr(exc),
        }


def parse_date(
    value,
) -> Optional[pd.Timestamp]:

    if pd.isna(value):
        return None

    try:

        ts = pd.to_datetime(
            value,
            errors="coerce",
        )

        if pd.isna(ts):
            return None

        return pd.Timestamp(
            ts
        ).normalize()

    except Exception:
        return None


def audit_one_asof(
    signal_date: pd.Timestamp,
    asof_value,
    source_meta: Dict[str, Any],
) -> Dict[str, Any]:

    asof_date = parse_date(
        asof_value
    )

    # --------------------------------------------------------
    # Missing ASOF
    # --------------------------------------------------------

    if asof_date is None:

        return {
            "asof_date": None,
            "lag_days": None,
            "future_leak": False,
            "source_date_match": None,
            "status": "MISSING_ASOF",
        }

    lag_days = (
        signal_date
        - asof_date
    ).days

    # --------------------------------------------------------
    # Critical PIT rule
    # --------------------------------------------------------

    if asof_date > signal_date:

        return {
            "asof_date":
                asof_date.strftime(
                    "%Y-%m-%d"
                ),

            "lag_days":
                lag_days,

            "future_leak":
                True,

            "source_date_match":
                None,

            "status":
                "FAIL_FUTURE_LEAK",
        }

    # --------------------------------------------------------
    # Source unavailable
    # --------------------------------------------------------

    if not source_meta[
        "source_exists"
    ]:

        return {
            "asof_date":
                asof_date.strftime(
                    "%Y-%m-%d"
                ),

            "lag_days":
                lag_days,

            "future_leak":
                False,

            "source_date_match":
                None,

            "status":
                "REVIEW_SOURCE_NOT_FOUND",
        }

    if source_meta[
        "error"
    ] is not None:

        return {
            "asof_date":
                asof_date.strftime(
                    "%Y-%m-%d"
                ),

            "lag_days":
                lag_days,

            "future_leak":
                False,

            "source_date_match":
                None,

            "status":
                "REVIEW_SOURCE_METADATA",
        }

    # --------------------------------------------------------
    # Verify ASOF exists in source
    # --------------------------------------------------------

    source_date_match = (
        asof_date
        in source_meta[
            "dates"
        ]
    )

    if not source_date_match:

        status = (
            "REVIEW_ASOF_NOT_IN_SOURCE"
        )

    elif lag_days > 31:

        status = (
            "PASS_STALE_GT31D"
        )

    elif lag_days > 7:

        status = (
            "PASS_STALE_GT7D"
        )

    else:

        status = "PASS"

    return {
        "asof_date":
            asof_date.strftime(
                "%Y-%m-%d"
            ),

        "lag_days":
            lag_days,

        "future_leak":
            False,

        "source_date_match":
            source_date_match,

        "status":
            status,
    }


# ============================================================
# Main
# ============================================================

def main():

    print()
    print(
        "FILTER13 INPUT LINEAGE AUDIT"
    )
    print("=" * 70)

    # --------------------------------------------------------
    # Load final attribution output
    # --------------------------------------------------------

    if not INPUT_AUDIT_FILE.exists():

        raise FileNotFoundError(
            f"Missing attribution file: "
            f"{INPUT_AUDIT_FILE}"
        )

    df = pd.read_csv(
        INPUT_AUDIT_FILE
    )

    if "date" not in df.columns:

        raise ValueError(
            "Input attribution file "
            "does not contain 'date'."
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df = (
        df
        .dropna(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )

    print(
        "[INPUT]",
        INPUT_AUDIT_FILE,
    )

    print(
        "[ROWS]",
        len(df),
    )

    if not df.empty:

        print(
            "[RANGE]",
            df["date"].min().date(),
            "->",
            df["date"].max().date(),
        )

    # --------------------------------------------------------
    # Load source metadata
    # --------------------------------------------------------

    source_meta = {}

    print()
    print(
        "[SOURCE DISCOVERY]"
    )

    for name, candidates in (
        SOURCE_CANDIDATES.items()
    ):

        meta = load_source_metadata(
            name,
            candidates,
        )

        source_meta[name] = meta

        print()
        print(
            f"{name.upper()}:"
        )

        print(
            "  exists:",
            meta["source_exists"],
        )

        print(
            "  path:",
            meta["source_path"],
        )

        print(
            "  date_col:",
            meta["date_column"],
        )

        print(
            "  min_date:",
            meta["min_date"],
        )

        print(
            "  max_date:",
            meta["max_date"],
        )

        print(
            "  error:",
            meta["error"],
        )

    # --------------------------------------------------------
    # Daily lineage audit
    # --------------------------------------------------------

    rows = []

    for _, original_row in (
        df.iterrows()
    ):

        signal_date = pd.Timestamp(
            original_row["date"]
        ).normalize()

        out = {
            "date":
                signal_date.strftime(
                    "%Y-%m-%d"
                ),

            "original_pit_status":
                original_row.get(
                    "pit_status"
                ),
        }

        critical_fail = False

        review_required = False

        missing_count = 0

        pass_count = 0

        for source_name, asof_col in (
            ASOF_COLUMNS.items()
        ):

            if asof_col not in df.columns:

                out[
                    f"{source_name}_asof"
                ] = None

                out[
                    f"{source_name}_lag_days"
                ] = None

                out[
                    f"{source_name}_future_leak"
                ] = False

                out[
                    f"{source_name}_source_match"
                ] = None

                out[
                    f"{source_name}_status"
                ] = "COLUMN_NOT_AVAILABLE"

                missing_count += 1

                continue

            result = audit_one_asof(
                signal_date,
                original_row.get(
                    asof_col
                ),
                source_meta[
                    source_name
                ],
            )

            out[
                f"{source_name}_asof"
            ] = result[
                "asof_date"
            ]

            out[
                f"{source_name}_lag_days"
            ] = result[
                "lag_days"
            ]

            out[
                f"{source_name}_future_leak"
            ] = result[
                "future_leak"
            ]

            out[
                f"{source_name}_source_match"
            ] = result[
                "source_date_match"
            ]

            out[
                f"{source_name}_status"
            ] = result[
                "status"
            ]

            if result[
                "status"
            ] == "FAIL_FUTURE_LEAK":

                critical_fail = True

            elif result[
                "status"
            ].startswith(
                "REVIEW"
            ):

                review_required = True

            elif result[
                "status"
            ] in [
                "MISSING_ASOF",
                "COLUMN_NOT_AVAILABLE",
            ]:

                missing_count += 1

            elif result[
                "status"
            ].startswith(
                "PASS"
            ):

                pass_count += 1

        # ----------------------------------------------------
        # Overall daily status
        # ----------------------------------------------------

        if critical_fail:

            overall_status = (
                "FAIL_FUTURE_LEAK"
            )

        elif review_required:

            overall_status = (
                "REVIEW_REQUIRED"
            )

        elif missing_count > 0:

            overall_status = (
                "PASS_WITH_MISSING"
            )

        else:

            overall_status = (
                "PASS"
            )

        out[
            "traceable_pass_count"
        ] = pass_count

        out[
            "missing_count"
        ] = missing_count

        out[
            "overall_status"
        ] = overall_status

        rows.append(
            out
        )

    result_df = pd.DataFrame(
        rows
    )

    # --------------------------------------------------------
    # Save daily
    # --------------------------------------------------------

    result_df.to_csv(
        OUTPUT_DAILY,
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # Summary by source
    # --------------------------------------------------------

    summary_rows = []

    for source_name in (
        ASOF_COLUMNS.keys()
    ):

        status_col = (
            f"{source_name}_status"
        )

        leak_col = (
            f"{source_name}_future_leak"
        )

        lag_col = (
            f"{source_name}_lag_days"
        )

        if status_col not in (
            result_df.columns
        ):
            continue

        statuses = (
            result_df[
                status_col
            ]
            .value_counts(
                dropna=False
            )
            .to_dict()
        )

        lag_series = pd.to_numeric(
            result_df[
                lag_col
            ],
            errors="coerce",
        )

        summary_rows.append({

            "source":
                source_name,

            "source_path":
                source_meta[
                    source_name
                ][
                    "source_path"
                ],

            "source_min_date":
                source_meta[
                    source_name
                ][
                    "min_date"
                ],

            "source_max_date":
                source_meta[
                    source_name
                ][
                    "max_date"
                ],

            "rows":
                len(
                    result_df
                ),

            "future_leak_count":
                int(
                    result_df[
                        leak_col
                    ]
                    .fillna(False)
                    .astype(bool)
                    .sum()
                ),

            "pass_count":
                sum(
                    count
                    for status, count
                    in statuses.items()
                    if str(
                        status
                    ).startswith(
                        "PASS"
                    )
                ),

            "missing_asof_count":
                int(
                    statuses.get(
                        "MISSING_ASOF",
                        0,
                    )
                    +
                    statuses.get(
                        "COLUMN_NOT_AVAILABLE",
                        0,
                    )
                ),

            "review_count":
                sum(
                    count
                    for status, count
                    in statuses.items()
                    if str(
                        status
                    ).startswith(
                        "REVIEW"
                    )
                ),

            "avg_lag_days":
                (
                    lag_series.mean()
                    if lag_series.notna().any()
                    else None
                ),

            "max_lag_days":
                (
                    lag_series.max()
                    if lag_series.notna().any()
                    else None
                ),

            "status_breakdown":
                str(
                    statuses
                ),
        })

    summary_df = pd.DataFrame(
        summary_rows
    )

    summary_df.to_csv(
        OUTPUT_SUMMARY,
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # Global gate
    # --------------------------------------------------------

    future_leak_total = 0

    for source_name in (
        ASOF_COLUMNS.keys()
    ):

        col = (
            f"{source_name}"
            "_future_leak"
        )

        if col in result_df.columns:

            future_leak_total += int(
                result_df[
                    col
                ]
                .fillna(False)
                .astype(bool)
                .sum()
            )

    overall_counts = (
        result_df[
            "overall_status"
        ]
        .value_counts(
            dropna=False
        )
        .to_dict()
    )

    if future_leak_total > 0:

        gate = (
            "FAIL - FUTURE DATA "
            "DETECTED"
        )

    elif (
        result_df[
            "overall_status"
        ]
        == "REVIEW_REQUIRED"
    ).any():

        gate = (
            "REVIEW REQUIRED - "
            "NO CONFIRMED FUTURE LEAK"
        )

    else:

        gate = (
            "PASS - NO FUTURE ASOF "
            "DETECTED IN TRACEABLE INPUTS"
        )

    # --------------------------------------------------------
    # Text report
    # --------------------------------------------------------

    lines = []

    lines.append(
        "FILTER13 INPUT LINEAGE AUDIT"
    )

    lines.append(
        "=" * 70
    )

    lines.append(
        f"Rows: {len(result_df)}"
    )

    if not result_df.empty:

        lines.append(
            "Range: "
            f"{result_df['date'].min()} "
            "-> "
            f"{result_df['date'].max()}"
        )

    lines.append("")

    lines.append(
        f"GATE: {gate}"
    )

    lines.append(
        f"Future leak count: "
        f"{future_leak_total}"
    )

    lines.append("")

    lines.append(
        "Overall daily status:"
    )

    for key, value in (
        overall_counts.items()
    ):

        lines.append(
            f"  {key}: {value}"
        )

    lines.append("")

    lines.append(
        "SOURCE SUMMARY"
    )

    lines.append(
        "-" * 70
    )

    for _, row in (
        summary_df.iterrows()
    ):

        lines.append("")

        lines.append(
            f"[{row['source']}]"
        )

        lines.append(
            f"path: "
            f"{row['source_path']}"
        )

        lines.append(
            f"coverage: "
            f"{row['source_min_date']} "
            f"-> "
            f"{row['source_max_date']}"
        )

        lines.append(
            f"future_leak_count: "
            f"{row['future_leak_count']}"
        )

        lines.append(
            f"missing_asof_count: "
            f"{row['missing_asof_count']}"
        )

        lines.append(
            f"review_count: "
            f"{row['review_count']}"
        )

        lines.append(
            f"avg_lag_days: "
            f"{row['avg_lag_days']}"
        )

        lines.append(
            f"max_lag_days: "
            f"{row['max_lag_days']}"
        )

        lines.append(
            f"status: "
            f"{row['status_breakdown']}"
        )

    lines.append("")
    lines.append(
        "INTERPRETATION"
    )
    lines.append(
        "-" * 70
    )

    lines.append(
        "PASS means the explicitly "
        "recorded ASOF date was not "
        "later than the signal date."
    )

    lines.append(
        "MISSING_ASOF does NOT prove "
        "a future leak."
    )

    lines.append(
        "It means that dependency "
        "cannot yet be proven PIT-safe "
        "from the attribution output."
    )

    lines.append(
        "Derived dependencies such as "
        "Drift, Gamma, Flow, Structural "
        "must be audited separately at "
        "their source-input level."
    )

    OUTPUT_TXT.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Console
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "[LINEAGE GATE]"
    )
    print(
        gate
    )

    print()
    print(
        "[OVERALL STATUS]"
    )

    print(
        result_df[
            "overall_status"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print()
    print(
        "[SOURCE SUMMARY]"
    )

    display_cols = [
        "source",
        "future_leak_count",
        "missing_asof_count",
        "review_count",
        "avg_lag_days",
        "max_lag_days",
    ]

    print(
        summary_df[
            display_cols
        ]
        .to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Show failures/reviews
    # --------------------------------------------------------

    problem_rows = result_df[
        result_df[
            "overall_status"
        ].isin(
            [
                "FAIL_FUTURE_LEAK",
                "REVIEW_REQUIRED",
            ]
        )
    ]

    if not problem_rows.empty:

        print()
        print(
            "[ROWS REQUIRING REVIEW]"
        )

        review_cols = [
            "date",
            "overall_status",
        ]

        for source_name in (
            ASOF_COLUMNS.keys()
        ):

            review_cols.extend(
                [
                    f"{source_name}_asof",
                    f"{source_name}_status",
                ]
            )

        review_cols = [
            c
            for c in review_cols
            if c in problem_rows.columns
        ]

        print(
            problem_rows[
                review_cols
            ]
            .head(50)
            .to_string(
                index=False
            )
        )

    print()
    print(
        "[SAVED]",
        OUTPUT_DAILY,
    )

    print(
        "[SAVED]",
        OUTPUT_SUMMARY,
    )

    print(
        "[SAVED]",
        OUTPUT_TXT,
    )

    print()
    print(
        "FILTER13 INPUT LINEAGE "
        "GATE 1 COMPLETE."
    )

    print(
        "Do NOT expand to 6 months "
        "until missing/review inputs "
        "and derived dependencies "
        "are resolved."
    )


if __name__ == "__main__":
    main()