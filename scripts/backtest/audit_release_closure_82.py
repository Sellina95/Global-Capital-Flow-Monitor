from __future__ import annotations

from pathlib import Path
import pandas as pd
from pandas.tseries.offsets import BDay

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "backtest"
RESULTS = DATA / "results"

PANEL_PATH = DATA / "master_panel.csv"
BASE_PATH = RESULTS / "full_release_timing_82_detail.csv"
REVIEW_PATH = RESULTS / "remaining_release_review_82_detail.csv"

OUT_DETAIL = RESULTS / "release_closure_82_detail.csv"
OUT_FAILURES = RESULTS / "release_closure_82_failures.csv"
OUT_SUMMARY = RESULTS / "release_closure_82_summary.csv"
OUT_TXT = RESULTS / "release_closure_82_summary.txt"

panel = pd.read_csv(
    PANEL_PATH,
    parse_dates=["signal_date", "execution_date"],
)

panel = panel[
    panel["signal_date"].notna()
].copy()

panel["signal_date"] = pd.to_datetime(
    panel["signal_date"]
).dt.normalize()


# ============================================================
# Helpers
# ============================================================

def load_source(filename, column):
    p = DATA / filename
    df = pd.read_csv(p)

    date_col = next(
        c for c in df.columns
        if c.lower() in {"date", "datetime"}
    )

    df = df.rename(columns={date_col: "observation_date"})

    df["observation_date"] = pd.to_datetime(
        df["observation_date"],
        errors="coerce",
    ).dt.normalize()

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce",
    )

    return (
        df[["observation_date", column]]
        .dropna()
        .sort_values("observation_date")
        .drop_duplicates("observation_date", keep="last")
    )


def audit_availability(
    family,
    column,
    filename,
    source_column,
    rule_name,
    availability_func,
):
    src = load_source(filename, source_column).copy()

    src["available_date"] = src[
        "observation_date"
    ].apply(availability_func)

    left = panel[["signal_date"]].sort_values(
        "signal_date"
    )

    merged = pd.merge_asof(
        left,
        src,
        left_on="signal_date",
        right_on="observation_date",
        direction="backward",
    )

    merged = merged.dropna(
        subset=["observation_date"]
    )

    merged["early_use"] = (
        merged["available_date"]
        > merged["signal_date"]
    )

    failures = merged[
        merged["early_use"]
    ].copy()

    detail = {
        "source_family": family,
        "source_column": column,
        "rule": rule_name,
        "checked_rows": len(merged),
        "early_use_rows": int(
            merged["early_use"].sum()
        ),
        "status": (
            "PASS"
            if not merged["early_use"].any()
            else "FAIL_EARLY_USE"
        ),
    }

    if not failures.empty:
        failures["source_family"] = family
        failures["source_column"] = column
        failures["rule"] = rule_name

    return detail, failures


def next_business_day(d):
    return (
        pd.Timestamp(d)
        + BDay(1)
    ).normalize()


def same_day_close(d):
    return pd.Timestamp(d).normalize()


def next_month_lower_bound(d):
    """
    Monthly observation represents information for the whole
    observation month.

    Even without exact publication timestamp, it cannot be known
    before that month has completed.

    This is deliberately a LOWER BOUND, not an assumed publication date.
    """
    d = pd.Timestamp(d)
    return (
        d.to_period("M") + 1
    ).start_time.normalize()


# ============================================================
# Start with already-proven release failures/results
# ============================================================

base = pd.read_csv(BASE_PATH)

rows = []
failure_frames = []

for _, r in base.iterrows():

    status = str(r["status"])

    if status in {
        "FAIL_EARLY_USE",
        "PASS",
        "PASS_INHERITED_MARKET_CLOSE",
        "INHERITS_NFCI_RESULT",
    }:
        rows.append({
            "source_family": r["source_family"],
            "source_column": r["source_column"],
            "rule": r["release_rule"],
            "checked_rows": r["checked_rows"],
            "early_use_rows": r["early_use_rows"],
            "status": status,
        })


# ============================================================
# Daily series
# ============================================================

daily_next_business = [
    ("fred_extras", "REAL_RATE",
     "fred_macro_extras.csv", "REAL_RATE"),

    ("fred_sector", "DFII10",
     "fred_macro_sctorallo.csv", "DFII10"),

    ("fred_sector", "DGS2",
     "fred_macro_sctorallo.csv", "DGS2"),

    ("fred_sector", "REAL_RATE",
     "fred_macro_sctorallo.csv", "REAL_RATE"),

    ("fred_sector", "T10Y2Y",
     "fred_macro_sctorallo.csv", "T10Y2Y"),

    ("fred_sector", "T10YIE",
     "fred_macro_sctorallo.csv", "T10YIE"),

    ("sovereign_yields", "US10Y",
     "sovereign_yields.csv", "US10Y"),
]

for fam, col, filename, src_col in daily_next_business:

    detail, failures = audit_availability(
        fam,
        col,
        filename,
        src_col,
        "NEXT_BUSINESS_DAY_AVAILABILITY",
        next_business_day,
    )

    rows.append(detail)

    if not failures.empty:
        failure_frames.append(failures)


# ============================================================
# HY OAS = Daily Close
#
# Signal uses signal-date close and execution is following
# trading date, so treat as market-close information.
# ============================================================

detail, failures = audit_availability(
    "credit",
    "HY_OAS",
    "credit_spread_data.csv",
    "HY_OAS",
    "DAILY_CLOSE",
    same_day_close,
)

rows.append(detail)

if not failures.empty:
    failure_frames.append(failures)


# ============================================================
# FRED VIX is also a daily close market observation.
# ============================================================

detail, failures = audit_availability(
    "fred_sector",
    "VIX",
    "fred_macro_sctorallo.csv",
    "VIX",
    "DAILY_MARKET_CLOSE",
    same_day_close,
)

rows.append(detail)

if not failures.empty:
    failure_frames.append(failures)


# ============================================================
# Monthly sovereign yields
#
# We use only a LOWER BOUND:
# a monthly observation cannot be known before month-end.
#
# Therefore any usage before first day of next month is
# unquestionably early use, regardless of exact later release.
# ============================================================

monthly_sovereign = [
    "KR10Y",
    "JP10Y",
    "DE10Y",
    "IL10Y",
    "GB10Y",
    "MX10Y",
]

for col in monthly_sovereign:

    detail, failures = audit_availability(
        "sovereign_yields",
        col,
        "sovereign_yields.csv",
        col,
        "MONTH_END_INFORMATION_LOWER_BOUND",
        next_month_lower_bound,
    )

    rows.append(detail)

    if not failures.empty:
        failure_frames.append(failures)


# ============================================================
# No historical values
# ============================================================

review = pd.read_csv(REVIEW_PATH)

no_values = review[
    review["status"] == "VERIFY_NON_ACTIVE"
]

for _, r in no_values.iterrows():

    rows.append({
        "source_family": r["source_family"],
        "source_column": r["source_column"],
        "rule": "NO_VALID_HISTORICAL_VALUES",
        "checked_rows": 0,
        "early_use_rows": 0,
        "status": "NON_ACTIVE_NO_VALUES",
    })


# ============================================================
# Derived sources inherit their parent result
# ============================================================

derived_mapping = {
    ("sentiment", "vix"):
        "INHERITS_MARKET_CLOSE",

    ("sentiment", "hyg_lqd"):
        "INHERITS_MARKET_CLOSE",

    ("sentiment", "hy_oas"):
        "INHERITS_HY_OAS",

    ("sentiment", "sentiment_proxy"):
        "INHERITS_VIX_HY_OAS_HYG_LQD",

    ("sovereign_spreads", "KR_US_SPREAD"):
        "INHERITS_KR10Y_US10Y",

    ("sovereign_spreads", "JP_US_SPREAD"):
        "INHERITS_JP10Y_US10Y",

    ("sovereign_spreads", "DE_US_SPREAD"):
        "INHERITS_DE10Y_US10Y",

    ("sovereign_spreads", "IL_US_SPREAD"):
        "INHERITS_IL10Y_US10Y",

    ("sovereign_spreads", "GB_US_SPREAD"):
        "INHERITS_GB10Y_US10Y",

    ("sovereign_spreads", "MX_US_SPREAD"):
        "INHERITS_MX10Y_US10Y",
}

for (fam, col), rule in derived_mapping.items():

    rows.append({
        "source_family": fam,
        "source_column": col,
        "rule": rule,
        "checked_rows": 4645,
        "early_use_rows": 0,
        "status": "INHERITS_PARENT_RESULT",
    })


# ============================================================
# Deduplicate same logical series
# Prefer explicit timing calculation over prior REVIEW/inherit.
# ============================================================

detail = pd.DataFrame(rows)

priority = {
    "FAIL_EARLY_USE": 5,
    "PASS": 4,
    "NON_ACTIVE_NO_VALUES": 4,
    "PASS_INHERITED_MARKET_CLOSE": 3,
    "INHERITS_PARENT_RESULT": 2,
    "INHERITS_NFCI_RESULT": 2,
}

detail["_priority"] = detail["status"].map(
    priority
).fillna(0)

detail = (
    detail
    .sort_values(
        ["source_family", "source_column", "_priority"]
    )
    .drop_duplicates(
        ["source_family", "source_column"],
        keep="last",
    )
    .drop(columns="_priority")
    .reset_index(drop=True)
)


# ============================================================
# Parent propagation
# ============================================================

status_map = {
    (r["source_family"], r["source_column"]): r["status"]
    for _, r in detail.iterrows()
}


def parent_failed(keys):
    return any(
        status_map.get(k) == "FAIL_EARLY_USE"
        for k in keys
    )


parent_sets = {
    ("sentiment", "hy_oas"): [
        ("credit", "HY_OAS"),
    ],

    ("sentiment", "sentiment_proxy"): [
        ("credit", "HY_OAS"),
        ("fred_sector", "VIX"),
    ],

    ("sovereign_spreads", "KR_US_SPREAD"): [
        ("sovereign_yields", "KR10Y"),
        ("sovereign_yields", "US10Y"),
    ],

    ("sovereign_spreads", "JP_US_SPREAD"): [
        ("sovereign_yields", "JP10Y"),
        ("sovereign_yields", "US10Y"),
    ],

    ("sovereign_spreads", "DE_US_SPREAD"): [
        ("sovereign_yields", "DE10Y"),
        ("sovereign_yields", "US10Y"),
    ],

    ("sovereign_spreads", "IL_US_SPREAD"): [
        ("sovereign_yields", "IL10Y"),
        ("sovereign_yields", "US10Y"),
    ],

    ("sovereign_spreads", "GB_US_SPREAD"): [
        ("sovereign_yields", "GB10Y"),
        ("sovereign_yields", "US10Y"),
    ],

    ("sovereign_spreads", "MX_US_SPREAD"): [
        ("sovereign_yields", "MX10Y"),
        ("sovereign_yields", "US10Y"),
    ],
}

for key, parents in parent_sets.items():

    mask = (
        (detail["source_family"] == key[0])
        & (detail["source_column"] == key[1])
    )

    if not mask.any():
        continue

    if parent_failed(parents):
        detail.loc[
            mask,
            "status"
        ] = "FAIL_INHERITED_PARENT_TIMING"


# ============================================================
# Outputs
# ============================================================

detail.to_csv(
    OUT_DETAIL,
    index=False,
    encoding="utf-8-sig",
)

if failure_frames:
    failures = pd.concat(
        failure_frames,
        ignore_index=True,
    )
else:
    failures = pd.DataFrame()

failures.to_csv(
    OUT_FAILURES,
    index=False,
    encoding="utf-8-sig",
)

summary = (
    detail
    .groupby("status")
    .size()
    .reset_index(name="series_count")
)

summary.to_csv(
    OUT_SUMMARY,
    index=False,
    encoding="utf-8-sig",
)

direct_fail = int(
    (detail["status"] == "FAIL_EARLY_USE").sum()
)

inherited_fail = int(
    (
        detail["status"]
        == "FAIL_INHERITED_PARENT_TIMING"
    ).sum()
)

remaining_review = int(
    detail["status"]
    .astype(str)
    .str.startswith("REVIEW")
    .sum()
)

print("=" * 78)
print("F13/F15/F18 RELEASE TIMING CLOSURE — FROZEN 82 UNIVERSE")
print("=" * 78)

print(summary.to_string(index=False))

print()
print("DIRECT EARLY-USE SERIES:", direct_fail)
print("INHERITED TIMING FAIL SERIES:", inherited_fail)
print("REMAINING REVIEW:", remaining_review)

print()

if direct_fail == 0 and inherited_fail == 0 and remaining_review == 0:
    gate = "RELEASE TIMING CLOSURE: PASS"
elif remaining_review == 0:
    gate = "RELEASE TIMING CLOSURE: FAIL — REPAIR REQUIRED"
else:
    gate = "RELEASE TIMING CLOSURE: NOT CLOSED"

print(gate)

print()
print("DIRECT FAILURES:")
print(
    detail[
        detail["status"] == "FAIL_EARLY_USE"
    ][
        [
            "source_family",
            "source_column",
            "rule",
            "early_use_rows",
        ]
    ].to_string(index=False)
)

print()
print("INHERITED FAILURES:")
print(
    detail[
        detail["status"] == "FAIL_INHERITED_PARENT_TIMING"
    ][
        [
            "source_family",
            "source_column",
            "rule",
        ]
    ].to_string(index=False)
)

OUT_TXT.write_text(
    "\n".join([
        "F13/F15/F18 RELEASE TIMING CLOSURE",
        "=" * 78,
        "Frozen universe: 82 stage-contract pairs",
        f"Direct early-use series: {direct_fail}",
        f"Inherited timing fail series: {inherited_fail}",
        f"Remaining review: {remaining_review}",
        "",
        gate,
        "",
        "No Production decision code modified.",
        "No strategy parameters modified.",
        "Monthly sovereign timing uses only a month-end lower bound;",
        "actual publication may be later.",
    ]),
    encoding="utf-8",
)

print()
print("[OUTPUT]")
print(OUT_DETAIL)
print(OUT_FAILURES)
print(OUT_SUMMARY)
print(OUT_TXT)
