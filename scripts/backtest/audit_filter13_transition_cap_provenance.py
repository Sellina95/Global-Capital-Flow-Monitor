from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "data/backtest/results/filter13_budget_attribution_final_daily.csv"
)

OUT = (
    ROOT
    / "data/backtest/results/"
    "filter13_transition_cap_provenance.csv"
)


# ============================================================
# Load verified PIT attribution
# ============================================================

d = pd.read_csv(INPUT)

d["date"] = pd.to_datetime(
    d["date"],
    errors="coerce",
)

numeric_cols = [
    "base_budget",
    "structure_delta",
    "credit_delta",
    "liquidity_delta",
    "structural_v2_delta",
    "drift_delta",
    "flow_gamma_delta",
    "flow_continuity_delta",
    "flow_regime_delta",
    "macro_delta",
    "positioning_delta",
    "event_floor_delta",
    "pre_cap_budget",
    "phase_cap",
    "phase_cap_effect",
    "v2_cap",
    "final_cap",
    "final_cap_effect",
    "final_budget",
]

for c in numeric_cols:
    if c in d.columns:
        d[c] = pd.to_numeric(
            d[c],
            errors="coerce",
        )


# ============================================================
# TRANSITION / MIXED only
# ============================================================

x = d[
    d["market_regime"]
    .fillna("")
    .str.upper()
    .eq("TRANSITION / MIXED")
].copy()


# ============================================================
# Diagnose cap provenance
#
# Important:
# phase_cap / v2_cap / final_cap을 분리해서 본다.
#
# phase_cap=30/65가 정말 MARKET_REGIME 자체에서 왔는지,
# 아니면 다른 cap 결합 결과인지 확인한다.
# ============================================================

def classify_cap_source(row):

    phase_cap = row.get("phase_cap")
    v2_cap = row.get("v2_cap")
    final_cap = row.get("final_cap")

    if pd.isna(final_cap):
        return "NO_FINAL_CAP"

    matches = []

    if pd.notna(phase_cap) and final_cap == phase_cap:
        matches.append("PHASE")

    if pd.notna(v2_cap) and final_cap == v2_cap:
        matches.append("V2")

    if len(matches) == 0:
        return "OTHER_OR_COMBINED"

    if len(matches) == 1:
        return matches[0]

    return "+".join(matches)


x["cap_source_guess"] = x.apply(
    classify_cap_source,
    axis=1,
)


# ============================================================
# Binding
# ============================================================

x["phase_binding"] = (
    x["phase_cap_effect"] < 0
)

x["final_binding"] = (
    x["final_cap_effect"] < 0
)

x["phase_exposure_removed"] = (
    -x["phase_cap_effect"]
).clip(lower=0)

x["final_exposure_removed"] = (
    -x["final_cap_effect"]
).clip(lower=0)


# ============================================================
# Print
# ============================================================

print(
    "\n=== FILTER13 TRANSITION CAP "
    "PROVENANCE AUDIT ==="
)

print("\n[COUNT]")

print(
    "TRANSITION / MIXED DAYS:",
    len(x),
)


print(
    "\n=== PHASE CAP DISTRIBUTION ==="
)

print(
    x["phase_cap"]
    .value_counts(
        dropna=False
    )
    .sort_index()
)


print(
    "\n=== V2 CAP DISTRIBUTION ==="
)

print(
    x["v2_cap"]
    .value_counts(
        dropna=False
    )
    .sort_index()
)


print(
    "\n=== FINAL CAP DISTRIBUTION ==="
)

print(
    x["final_cap"]
    .value_counts(
        dropna=False
    )
    .sort_index()
)


print(
    "\n=== PHASE CAP × V2 CAP × FINAL CAP ==="
)

combo = (
    x.groupby(
        [
            "phase_cap",
            "v2_cap",
            "final_cap",
        ],
        dropna=False,
    )
    .agg(
        days=("date", "count"),

        binding_days=(
            "phase_binding",
            "sum",
        ),

        avg_pre_cap=(
            "pre_cap_budget",
            "mean",
        ),

        avg_phase_effect=(
            "phase_cap_effect",
            "mean",
        ),

        avg_final_budget=(
            "final_budget",
            "mean",
        ),
    )
    .reset_index()
    .sort_values(
        [
            "phase_cap",
            "v2_cap",
            "final_cap",
        ]
    )
)

print(
    combo.to_string(
        index=False
    )
)


print(
    "\n=== CAP SOURCE GUESS ==="
)

print(
    x["cap_source_guess"]
    .value_counts(
        dropna=False
    )
)


# ============================================================
# Compare cap=30 vs cap=65
# ============================================================

print(
    "\n=== TRANSITION CAP 30 VS 65 ==="
)

compare = (
    x[
        x["phase_cap"].isin(
            [30, 65]
        )
    ]
    .groupby(
        "phase_cap"
    )
    .agg(
        days=(
            "date",
            "count",
        ),

        binding_days=(
            "phase_binding",
            "sum",
        ),

        avg_base_budget=(
            "base_budget",
            "mean",
        ),

        avg_macro_delta=(
            "macro_delta",
            "mean",
        ),

        avg_pre_cap_budget=(
            "pre_cap_budget",
            "mean",
        ),

        avg_phase_effect=(
            "phase_cap_effect",
            "mean",
        ),

        avg_final_budget=(
            "final_budget",
            "mean",
        ),
    )
    .reset_index()
)

print(
    compare.to_string(
        index=False
    )
)


# ============================================================
# Full daily detail
# ============================================================

print(
    "\n=== TRANSITION DAILY DETAIL ==="
)

detail_cols = [
    "date",
    "market_regime",
    "macro_narrative",
    "struct_v2_state",
    "flow_score",
    "prev_flow_score",
    "base_budget",
    "structure_delta",
    "credit_delta",
    "liquidity_delta",
    "structural_v2_delta",
    "drift_delta",
    "flow_gamma_delta",
    "flow_continuity_delta",
    "flow_regime_delta",
    "macro_delta",
    "positioning_delta",
    "pre_cap_budget",
    "phase_cap",
    "phase_cap_effect",
    "v2_cap",
    "final_cap",
    "final_cap_effect",
    "final_budget",
    "cap_source_guess",
]

detail_cols = [
    c
    for c in detail_cols
    if c in x.columns
]

print(
    x[
        detail_cols
    ]
    .sort_values(
        "date"
    )
    .to_string(
        index=False
    )
)


# ============================================================
# Specifically suspicious cap=30 days
# ============================================================

print(
    "\n=== CAP 30 DAYS ONLY ==="
)

cap30 = (
    x[
        x["phase_cap"] == 30
    ][
        detail_cols
    ]
    .sort_values(
        "date"
    )
)

if cap30.empty:
    print("NONE")
else:
    print(
        cap30.to_string(
            index=False
        )
    )


# ============================================================
# Save
# ============================================================

x.to_csv(
    OUT,
    index=False,
)

print(
    "\n[SAVED]",
    OUT,
)

print(
    "\nTRANSITION CAP PROVENANCE AUDIT COMPLETE."
)

print(
    "No production Filter13 logic was modified."
)