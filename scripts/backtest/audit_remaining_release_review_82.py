from __future__ import annotations

from pathlib import Path
import pandas as pd
from pandas.tseries.offsets import BDay

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "backtest"
RESULTS = DATA / "results"

IN_PATH = RESULTS / "full_release_timing_82_detail.csv"

OUT_DETAIL = RESULTS / "remaining_release_review_82_detail.csv"
OUT_SUMMARY = RESULTS / "remaining_release_review_82_summary.csv"

df = pd.read_csv(IN_PATH)

review = df[
    df["status"].astype(str).str.startswith("REVIEW")
].copy()


# ----------------------------------------------------------
# Classification
# ----------------------------------------------------------

DAILY_FRED = {
    ("credit", "HY_OAS"),
    ("fred_extras", "REAL_RATE"),
    ("fred_sector", "DFII10"),
    ("fred_sector", "DGS2"),
    ("fred_sector", "REAL_RATE"),
    ("fred_sector", "T10Y2Y"),
    ("fred_sector", "T10YIE"),
    ("fred_sector", "VIX"),
}

SOVEREIGN_MONTHLY = {
    ("sovereign_yields", "KR10Y"),
    ("sovereign_yields", "JP10Y"),
    ("sovereign_yields", "DE10Y"),
    ("sovereign_yields", "IL10Y"),
    ("sovereign_yields", "GB10Y"),
    ("sovereign_yields", "MX10Y"),
}

SOVEREIGN_US_DAILY = {
    ("sovereign_yields", "US10Y"),
}

PARENT_DERIVED = {
    "sentiment",
    "sovereign_spreads",
}


rows = []

for _, r in review.iterrows():

    fam = str(r["source_family"])
    col = str(r["source_column"])
    old_status = str(r["status"])

    key = (fam, col)

    if old_status == "REVIEW_NO_VALUES":

        rows.append({
            "source_family": fam,
            "source_column": col,
            "classification": "NO_HISTORICAL_VALUES",
            "required_rule": "VERIFY_NON_ACTIVE",
            "status": "VERIFY_NON_ACTIVE",
            "reason":
                "No valid historical source values were present in PIT audit.",
        })

    elif fam in PARENT_DERIVED:

        rows.append({
            "source_family": fam,
            "source_column": col,
            "classification": "DERIVED",
            "required_rule": "INHERIT_PARENT_AVAILABILITY",
            "status": "PARENT_RESULT_REQUIRED",
            "reason":
                "Derived value cannot be available before its latest parent.",
        })

    elif key in DAILY_FRED:

        rows.append({
            "source_family": fam,
            "source_column": col,
            "classification": "DAILY_FRED_OR_DAILY_CLOSE",
            "required_rule": "NEXT_AVAILABLE_BUSINESS_DAY_OR_CLOSE_RULE",
            "status": "DAILY_TIMING_REQUIRED",
            "reason":
                "Daily observation exists, but actual production availability "
                "must be aligned with report/signal timing.",
        })

    elif key in SOVEREIGN_MONTHLY:

        rows.append({
            "source_family": fam,
            "source_column": col,
            "classification": "OECD_MONTHLY_SOVEREIGN",
            "required_rule": "MONTHLY_PUBLICATION_LAG_REQUIRED",
            "status": "MONTHLY_LAG_REQUIRED",
            "reason":
                "Observation is monthly and cannot be assumed available "
                "on the first day of the observation month.",
        })

    elif key in SOVEREIGN_US_DAILY:

        rows.append({
            "source_family": fam,
            "source_column": col,
            "classification": "US_TREASURY_H15_DAILY",
            "required_rule": "NEXT_AVAILABLE_BUSINESS_DAY",
            "status": "DAILY_TIMING_REQUIRED",
            "reason":
                "DGS10/H.15 daily observation requires availability timing.",
        })

    else:

        rows.append({
            "source_family": fam,
            "source_column": col,
            "classification": "UNRESOLVED",
            "required_rule": "MANUAL_REVIEW",
            "status": "UNRESOLVED",
            "reason": "Not yet classified.",
        })


out = pd.DataFrame(rows)

out.to_csv(
    OUT_DETAIL,
    index=False,
    encoding="utf-8-sig",
)

summary = (
    out.groupby(
        ["classification", "status"],
        dropna=False,
    )
    .size()
    .reset_index(name="series_count")
)

summary.to_csv(
    OUT_SUMMARY,
    index=False,
    encoding="utf-8-sig",
)

print("=" * 80)
print("REMAINING RELEASE REVIEW — FROZEN 82-CONTRACT UNIVERSE")
print("=" * 80)

print(
    out[
        [
            "source_family",
            "source_column",
            "classification",
            "status",
        ]
    ].to_string(index=False)
)

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(summary.to_string(index=False))

print()
print("TOTAL:", len(out))
print("UNRESOLVED:", int((out["status"] == "UNRESOLVED").sum()))

print()
print("[OUTPUT]")
print(OUT_DETAIL)
print(OUT_SUMMARY)
