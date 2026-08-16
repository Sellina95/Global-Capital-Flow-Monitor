from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_v3_canonical_counterfactual_v1"
)

BASELINE_PATH = (
    RESULT_DIR
    / "canonical_baseline_replay.csv"
)

V3_PATH = (
    RESULT_DIR
    / "macro_v3_counterfactual_daily.csv"
)

OUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_v3_regime_attribution_v1"
)

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# LOAD
# ============================================================

if not BASELINE_PATH.exists():
    raise FileNotFoundError(BASELINE_PATH)

if not V3_PATH.exists():
    raise FileNotFoundError(V3_PATH)


baseline = pd.read_csv(
    BASELINE_PATH,
    parse_dates=[
        "signal_date",
        "execution_date",
    ],
)

v3 = pd.read_csv(
    V3_PATH,
    parse_dates=[
        "signal_date",
        "execution_date",
    ],
)


# ============================================================
# CONTRACT CHECK
# ============================================================

required_baseline = {
    "signal_date",
    "execution_date",
    "macro_narrative",
    "market_regime",
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
    "cash_weight",
}

required_v3 = {
    "signal_date",
    "execution_date",
    "raw_macro_narrative",
    "strategic_macro_state",
    "raw_market_regime",
    "strategic_market_regime",
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
    "cash_weight",
}

missing_baseline = (
    required_baseline
    - set(baseline.columns)
)

missing_v3 = (
    required_v3
    - set(v3.columns)
)

if missing_baseline:
    raise RuntimeError(
        "Baseline missing fields: "
        f"{sorted(missing_baseline)}"
    )

if missing_v3:
    raise RuntimeError(
        "V3 missing fields: "
        f"{sorted(missing_v3)}"
    )


# ============================================================
# MERGE
#
# V3 has one fewer observation because the first P2 state
# cannot be resolved without future backfill.
# ============================================================

df = baseline.merge(
    v3,
    on=[
        "signal_date",
        "execution_date",
    ],
    how="inner",
    suffixes=(
        "_baseline",
        "_v3",
    ),
)

if len(df) != len(v3):
    raise RuntimeError(
        "Merged row count does not equal "
        "V3 evaluation row count."
    )


# ============================================================
# IDENTITY CHECKS
# ============================================================

raw_macro_identity = (
    df["macro_narrative"].astype(str)
    ==
    df["raw_macro_narrative"].astype(str)
)

raw_regime_identity = (
    df["market_regime"].astype(str)
    ==
    df["raw_market_regime"].astype(str)
)

if not raw_macro_identity.all():
    raise RuntimeError(
        "RAW macro identity failed."
    )

if not raw_regime_identity.all():
    bad = int(
        (~raw_regime_identity).sum()
    )

    raise RuntimeError(
        "RAW market regime identity failed: "
        f"{bad} rows"
    )


# ============================================================
# NUMERIC DELTAS
# ============================================================

numeric_fields = [
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
    "cash_weight",
]

for field in numeric_fields:

    b = pd.to_numeric(
        df[f"{field}_baseline"],
        errors="coerce",
    )

    c = pd.to_numeric(
        df[f"{field}_v3"],
        errors="coerce",
    )

    df[f"{field}_delta"] = (
        c - b
    )

    df[f"{field}_changed"] = (
        (
            b.isna()
            ^ c.isna()
        )
        |
        (
            b.notna()
            & c.notna()
            & ((c - b).abs() > 1e-9)
        )
    )


df["macro_changed"] = (
    df["macro_narrative"].astype(str)
    !=
    df["strategic_macro_state"].astype(str)
)

df["regime_changed"] = (
    df["market_regime"].astype(str)
    !=
    df[
        "strategic_market_regime"
    ].astype(str)
)


# ============================================================
# 1. MARKET REGIME TRANSITION MATRIX
# ============================================================

regime_matrix = (
    df.groupby(
        [
            "market_regime",
            "strategic_market_regime",
        ],
        dropna=False,
    )
    .agg(
        observations=(
            "signal_date",
            "size",
        ),
        mean_risk_budget_delta=(
            "risk_budget_13_delta",
            "mean",
        ),
        mean_exposure_delta=(
            "exposure_15_delta",
            "mean",
        ),
        mean_allocated_equity_delta=(
            "allocated_equity_18_delta",
            "mean",
        ),
        mean_cash_delta=(
            "cash_weight_delta",
            "mean",
        ),
    )
    .reset_index()
)

regime_matrix["changed"] = (
    regime_matrix[
        "market_regime"
    ].astype(str)
    !=
    regime_matrix[
        "strategic_market_regime"
    ].astype(str)
)

regime_matrix = regime_matrix.sort_values(
    [
        "changed",
        "observations",
    ],
    ascending=[
        False,
        False,
    ],
)


# ============================================================
# 2. ONLY CHANGED MARKET REGIME PATHS
# ============================================================

changed_regime = regime_matrix[
    regime_matrix["changed"]
].copy()

changed_total = int(
    df["regime_changed"].sum()
)

if changed_total:

    changed_regime[
        "share_of_changed_regime_days"
    ] = (
        changed_regime[
            "observations"
        ]
        / changed_total
    )

else:

    changed_regime[
        "share_of_changed_regime_days"
    ] = np.nan


# ============================================================
# 3. RAW MACRO -> STRATEGIC MACRO MATRIX
# ============================================================

macro_matrix = (
    df.groupby(
        [
            "macro_narrative",
            "strategic_macro_state",
        ],
        dropna=False,
    )
    .agg(
        observations=(
            "signal_date",
            "size",
        ),
        regime_changed_days=(
            "regime_changed",
            "sum",
        ),
        risk_budget_changed_days=(
            "risk_budget_13_changed",
            "sum",
        ),
        exposure_changed_days=(
            "exposure_15_changed",
            "sum",
        ),
        mean_risk_budget_delta=(
            "risk_budget_13_delta",
            "mean",
        ),
        mean_exposure_delta=(
            "exposure_15_delta",
            "mean",
        ),
        mean_allocated_equity_delta=(
            "allocated_equity_18_delta",
            "mean",
        ),
    )
    .reset_index()
)

macro_matrix["macro_changed"] = (
    macro_matrix[
        "macro_narrative"
    ].astype(str)
    !=
    macro_matrix[
        "strategic_macro_state"
    ].astype(str)
)

macro_matrix = macro_matrix.sort_values(
    [
        "macro_changed",
        "observations",
    ],
    ascending=[
        False,
        False,
    ],
)


# ============================================================
# 4. STRATEGIC STATE OCCUPANCY
#
# This is critical:
# Did persistence simply keep defensive states alive much
# longer than the RAW architecture?
# ============================================================

raw_occupancy = (
    df.groupby(
        "macro_narrative",
        dropna=False,
    )
    .size()
    .rename(
        "raw_days"
    )
)

strategic_occupancy = (
    df.groupby(
        "strategic_macro_state",
        dropna=False,
    )
    .size()
    .rename(
        "strategic_days"
    )
)

occupancy = pd.concat(
    [
        raw_occupancy,
        strategic_occupancy,
    ],
    axis=1,
).fillna(0)

occupancy["raw_days"] = (
    occupancy["raw_days"]
    .astype(int)
)

occupancy["strategic_days"] = (
    occupancy["strategic_days"]
    .astype(int)
)

occupancy[
    "strategic_minus_raw_days"
] = (
    occupancy["strategic_days"]
    -
    occupancy["raw_days"]
)

occupancy["raw_share"] = (
    occupancy["raw_days"]
    / len(df)
)

occupancy["strategic_share"] = (
    occupancy["strategic_days"]
    / len(df)
)

occupancy["share_delta"] = (
    occupancy["strategic_share"]
    -
    occupancy["raw_share"]
)

occupancy = (
    occupancy
    .reset_index()
    .rename(
        columns={
            "index": "macro_state"
        }
    )
    .sort_values(
        "strategic_minus_raw_days",
        ascending=False,
    )
)


# ============================================================
# 5. STRATEGIC STATE CAPITAL EFFECT
# ============================================================

state_effect = (
    df.groupby(
        "strategic_macro_state",
        dropna=False,
    )
    .agg(
        observations=(
            "signal_date",
            "size",
        ),
        raw_macro_disagreement_days=(
            "macro_changed",
            "sum",
        ),
        regime_changed_days=(
            "regime_changed",
            "sum",
        ),
        risk_budget_changed_days=(
            "risk_budget_13_changed",
            "sum",
        ),
        exposure_changed_days=(
            "exposure_15_changed",
            "sum",
        ),
        mean_risk_budget_delta=(
            "risk_budget_13_delta",
            "mean",
        ),
        median_risk_budget_delta=(
            "risk_budget_13_delta",
            "median",
        ),
        mean_exposure_delta=(
            "exposure_15_delta",
            "mean",
        ),
        median_exposure_delta=(
            "exposure_15_delta",
            "median",
        ),
        mean_allocated_equity_delta=(
            "allocated_equity_18_delta",
            "mean",
        ),
        mean_cash_delta=(
            "cash_weight_delta",
            "mean",
        ),
    )
    .reset_index()
)

state_effect[
    "exposure_total_effect"
] = (
    state_effect[
        "mean_exposure_delta"
    ]
    *
    state_effect[
        "observations"
    ]
)

state_effect = state_effect.sort_values(
    "exposure_total_effect",
    ascending=True,
)


# ============================================================
# 6. NEGATIVE EXPOSURE ATTRIBUTION
#
# Which regime transitions explain the total downward
# exposure pressure?
# ============================================================

negative_exposure = changed_regime[
    changed_regime[
        "mean_exposure_delta"
    ] < 0
].copy()

negative_exposure[
    "total_exposure_effect"
] = (
    negative_exposure[
        "mean_exposure_delta"
    ]
    *
    negative_exposure[
        "observations"
    ]
)

negative_exposure = (
    negative_exposure
    .sort_values(
        "total_exposure_effect",
        ascending=True,
    )
)


# ============================================================
# 7. POSITIVE EXPOSURE ATTRIBUTION
# ============================================================

positive_exposure = changed_regime[
    changed_regime[
        "mean_exposure_delta"
    ] > 0
].copy()

positive_exposure[
    "total_exposure_effect"
] = (
    positive_exposure[
        "mean_exposure_delta"
    ]
    *
    positive_exposure[
        "observations"
    ]
)

positive_exposure = (
    positive_exposure
    .sort_values(
        "total_exposure_effect",
        ascending=False,
    )
)


# ============================================================
# 8. DEFENSIVE HOLD DIAGNOSTIC
# ============================================================

defensive_terms = (
    "RISK-OFF",
    "STAGFLATION",
    "INFLATION",
    "EVENT-WATCHING",
)

def is_defensive(value) -> bool:

    text = str(value).upper()

    return any(
        term in text
        for term in defensive_terms
    )


df["baseline_defensive_regime"] = (
    df["market_regime"]
    .map(is_defensive)
)

df["v3_defensive_regime"] = (
    df[
        "strategic_market_regime"
    ]
    .map(is_defensive)
)

df["new_defensive_day"] = (
    (~df["baseline_defensive_regime"])
    &
    df["v3_defensive_regime"]
)

df["released_defensive_day"] = (
    df["baseline_defensive_regime"]
    &
    (~df["v3_defensive_regime"])
)

defensive_summary = pd.DataFrame(
    [
        {
            "metric": "baseline_defensive_days",
            "value": int(
                df[
                    "baseline_defensive_regime"
                ].sum()
            ),
        },
        {
            "metric": "v3_defensive_days",
            "value": int(
                df[
                    "v3_defensive_regime"
                ].sum()
            ),
        },
        {
            "metric": "new_defensive_days",
            "value": int(
                df[
                    "new_defensive_day"
                ].sum()
            ),
        },
        {
            "metric": "released_defensive_days",
            "value": int(
                df[
                    "released_defensive_day"
                ].sum()
            ),
        },
    ]
)


# ============================================================
# SAVE
# ============================================================

daily_path = (
    OUT_DIR
    / "macro_v3_regime_attribution_daily.csv"
)

regime_path = (
    OUT_DIR
    / "market_regime_transition_matrix.csv"
)

macro_path = (
    OUT_DIR
    / "macro_state_transition_matrix.csv"
)

occupancy_path = (
    OUT_DIR
    / "macro_state_occupancy.csv"
)

state_effect_path = (
    OUT_DIR
    / "strategic_state_capital_effect.csv"
)

negative_path = (
    OUT_DIR
    / "negative_exposure_attribution.csv"
)

positive_path = (
    OUT_DIR
    / "positive_exposure_attribution.csv"
)

defensive_path = (
    OUT_DIR
    / "defensive_regime_summary.csv"
)

audit_path = (
    OUT_DIR
    / "macro_v3_regime_attribution_audit.txt"
)


df.to_csv(
    daily_path,
    index=False,
)

regime_matrix.to_csv(
    regime_path,
    index=False,
)

macro_matrix.to_csv(
    macro_path,
    index=False,
)

occupancy.to_csv(
    occupancy_path,
    index=False,
)

state_effect.to_csv(
    state_effect_path,
    index=False,
)

negative_exposure.to_csv(
    negative_path,
    index=False,
)

positive_exposure.to_csv(
    positive_path,
    index=False,
)

defensive_summary.to_csv(
    defensive_path,
    index=False,
)


# ============================================================
# TERMINAL REPORT
# ============================================================

print("=" * 126)
print("MACRO V3 — REGIME / CAPITAL ATTRIBUTION")
print("=" * 126)

print()
print("===== CONTRACT =====")
print(
    "Rows                    :",
    len(df),
)
print(
    "RAW macro identity      :",
    "PASS",
)
print(
    "RAW regime identity     :",
    "PASS",
)
print(
    "Returns used            : NO",
)
print(
    "13/15/18 recalculated   : NO",
)

print()
print("===== TOP CHANGED MARKET_REGIME PATHS =====")

show_regime = (
    changed_regime
    .head(20)
    .copy()
)

if show_regime.empty:

    print("NONE")

else:

    display_cols = [
        "market_regime",
        "strategic_market_regime",
        "observations",
        "share_of_changed_regime_days",
        "mean_risk_budget_delta",
        "mean_exposure_delta",
        "mean_allocated_equity_delta",
    ]

    print(
        show_regime[
            display_cols
        ].to_string(
            index=False,
            formatters={
                "share_of_changed_regime_days":
                    lambda x: f"{x:.2%}",
                "mean_risk_budget_delta":
                    lambda x: f"{x:+.3f}",
                "mean_exposure_delta":
                    lambda x: f"{x:+.3f}",
                "mean_allocated_equity_delta":
                    lambda x: f"{x:+.3f}",
            },
        )
    )


print()
print("===== MACRO STATE OCCUPANCY =====")

print(
    occupancy.to_string(
        index=False,
        formatters={
            "raw_share":
                lambda x: f"{x:.2%}",
            "strategic_share":
                lambda x: f"{x:.2%}",
            "share_delta":
                lambda x: f"{x:+.2%}",
        },
    )
)


print()
print("===== STRATEGIC STATE CAPITAL EFFECT =====")

print(
    state_effect.to_string(
        index=False,
        formatters={
            "mean_risk_budget_delta":
                lambda x: f"{x:+.3f}",
            "median_risk_budget_delta":
                lambda x: f"{x:+.3f}",
            "mean_exposure_delta":
                lambda x: f"{x:+.3f}",
            "median_exposure_delta":
                lambda x: f"{x:+.3f}",
            "mean_allocated_equity_delta":
                lambda x: f"{x:+.3f}",
            "mean_cash_delta":
                lambda x: f"{x:+.3f}",
            "exposure_total_effect":
                lambda x: f"{x:+.1f}",
        },
    )
)


print()
print("===== TOP NEGATIVE EXPOSURE PATHS =====")

if negative_exposure.empty:

    print("NONE")

else:

    print(
        negative_exposure[
            [
                "market_regime",
                "strategic_market_regime",
                "observations",
                "mean_exposure_delta",
                "total_exposure_effect",
            ]
        ]
        .head(15)
        .to_string(
            index=False,
            formatters={
                "mean_exposure_delta":
                    lambda x: f"{x:+.3f}",
                "total_exposure_effect":
                    lambda x: f"{x:+.1f}",
            },
        )
    )


print()
print("===== DEFENSIVE REGIME DIAGNOSTIC =====")

print(
    defensive_summary.to_string(
        index=False,
    )
)


# ============================================================
# AUDIT MEMO
# ============================================================

baseline_defensive = int(
    df[
        "baseline_defensive_regime"
    ].sum()
)

v3_defensive = int(
    df[
        "v3_defensive_regime"
    ].sum()
)

new_defensive = int(
    df[
        "new_defensive_day"
    ].sum()
)

released_defensive = int(
    df[
        "released_defensive_day"
    ].sum()
)

overall_exposure_delta = float(
    df[
        "exposure_15_delta"
    ].mean()
)

overall_budget_delta = float(
    df[
        "risk_budget_13_delta"
    ].mean()
)


audit = f"""
MACRO V3 — REGIME ATTRIBUTION V1

PURPOSE
-------
Explain why the frozen Macro V3 intervention materially
changed the existing capital chain.

This audit does NOT select a strategy and does NOT evaluate
returns.

CONTRACT
--------
Rows                        : {len(df)}
RAW macro identity          : PASS
RAW market regime identity  : PASS

OVERALL CAPITAL EFFECT
----------------------
Mean Risk Budget delta      : {overall_budget_delta:+.4f}
Mean Exposure delta         : {overall_exposure_delta:+.4f}

DEFENSIVE REGIME
----------------
Baseline defensive days     : {baseline_defensive}
V3 defensive days           : {v3_defensive}
New defensive days          : {new_defensive}
Released defensive days     : {released_defensive}

INTERPRETATION GATE
-------------------
Do NOT promote Macro V3 to Production from transition
reduction alone.

Determine whether the negative exposure effect is caused by:

1. economically justified strategic persistence,

2. excessive persistence of defensive macro states,

3. MARKET_REGIME remapping semantics,

4. interaction with existing downstream Filter13/15/18
   controls.

Only after structural attribution is understood should
performance evaluation be authorized.

SAFETY
------
Production modified         : NO
Filter13 modified           : NO
Filter15 modified           : NO
Filter18 modified           : NO
13/15/18 recalculated       : NO
Returns used                : NO
CAGR used                   : NO
Sharpe used                 : NO
Parameter tuning            : NO
Commit                      : NO
""".strip()

audit_path.write_text(
    audit,
    encoding="utf-8",
)


print()
print("===== ARTIFACTS =====")
print("Daily      :", daily_path)
print("Regime     :", regime_path)
print("Macro      :", macro_path)
print("Occupancy  :", occupancy_path)
print("State      :", state_effect_path)
print("Negative   :", negative_path)
print("Positive   :", positive_path)
print("Defensive  :", defensive_path)
print("Audit      :", audit_path)

print()
print("PRODUCTION MODIFIED : NO")
print("FILTER13/15/18      : UNCHANGED")
print("13/15/18 RECALC     : NO")
print("RETURNS USED        : NO")
print("PERFORMANCE USED    : NO")
print("PARAMETER TUNING    : NO")
print("COMMIT              : NO")

print()
print("=" * 126)
print("ATTRIBUTION COMPLETE — DO NOT COMMIT")
print("=" * 126)
