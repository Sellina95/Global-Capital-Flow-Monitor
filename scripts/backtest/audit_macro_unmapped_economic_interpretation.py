from __future__ import annotations

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

EVIDENCE_PATH = (
    ROOT
    / "data/backtest/results"
    / "macro_unknown_evidence_attribution_v1"
    / "unknown_evidence_daily.csv"
)

FAMILY_PATH = (
    ROOT
    / "data/backtest/results"
    / "macro_unknown_structural_families_v1"
    / "unknown_structural_family_daily.csv"
)

OUT_DIR = (
    ROOT
    / "data/backtest/results"
    / "macro_unmapped_economic_interpretation_v1"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

DAILY_OUT = OUT_DIR / "unmapped_economic_daily.csv"
SUMMARY_OUT = OUT_DIR / "unmapped_family_summary.csv"
HY_OUT = OUT_DIR / "unmapped_family_hy_profile.csv"
WTI_OUT = OUT_DIR / "unmapped_family_wti_profile.csv"
VIX_OUT = OUT_DIR / "unmapped_family_vix_profile.csv"
COMBO_OUT = OUT_DIR / "unmapped_family_exact_combinations.csv"
NEIGHBOR_OUT = OUT_DIR / "unmapped_family_neighbor_states.csv"
ERA_OUT = OUT_DIR / "unmapped_family_by_era.csv"
AUDIT_OUT = OUT_DIR / "unmapped_economic_interpretation_audit.txt"


# ============================================================
# LOAD
# ============================================================

if not EVIDENCE_PATH.exists():
    raise FileNotFoundError(EVIDENCE_PATH)

if not FAMILY_PATH.exists():
    raise FileNotFoundError(FAMILY_PATH)

evidence = pd.read_csv(
    EVIDENCE_PATH,
    parse_dates=["signal_date", "execution_date"],
)

families = pd.read_csv(
    FAMILY_PATH,
    parse_dates=["signal_date"],
)


# ============================================================
# CONTRACT CHECK
# ============================================================

if len(evidence) != 4645:
    raise RuntimeError(
        f"Expected 4645 evidence rows, got {len(evidence)}"
    )

if len(families) != 1328:
    raise RuntimeError(
        f"Expected 1328 UNKNOWN family rows, got {len(families)}"
    )

required_evidence = {
    "signal_date",
    "raw_macro_narrative",
    "US10Y_DIR",
    "DXY_DIR",
    "VIX_DIR",
    "WTI_DIR",
    "HY_OAS_STATUS",
}

missing = required_evidence - set(evidence.columns)

if missing:
    raise RuntimeError(
        f"Evidence missing columns: {sorted(missing)}"
    )

required_family = {
    "signal_date",
    "structural_family",
    "US10Y_DIR",
    "DXY_DIR",
    "VIX_DIR",
    "WTI_DIR",
    "HY_OAS_STATUS",
}

missing = required_family - set(families.columns)

if missing:
    raise RuntimeError(
        f"Family file missing columns: {sorted(missing)}"
    )


# ============================================================
# KEEP ONLY UNMAPPED VALID REGIONS
#
# FLAT_LOW_INFORMATION is deliberately excluded.
# We are NOT solving low-information persistence here.
# ============================================================

unmapped = families[
    ~families["structural_family"].isin(
        [
            "FLAT_LOW_INFORMATION",
            "MISSING_EVIDENCE",
        ]
    )
].copy()

if len(unmapped) != 992:
    raise RuntimeError(
        "Expected 992 UNMAPPED_VALID_REGION rows, "
        f"got {len(unmapped)}"
    )


# ============================================================
# MERGE RAW STATE CONTEXT
#
# raw_macro_narrative must remain UNKNOWN_TRANSITION.
# Neighbor states are diagnostic only.
# ============================================================

context_cols = [
    "signal_date",
    "raw_macro_narrative",
]

# Reuse neighbor columns if previous audit already created them.
for col in (
    "previous_raw_state",
    "next_raw_state",
):
    if col in evidence.columns:
        context_cols.append(col)

context = evidence[
    context_cols
].copy()

# Avoid pandas _x / _y suffix collisions.
# The evidence audit is canonical for RAW/neighbor state context.
context_payload_cols = [
    c for c in context_cols
    if c != "signal_date"
]

unmapped = unmapped.drop(
    columns=[
        c for c in context_payload_cols
        if c in unmapped.columns
    ],
    errors="ignore",
)

unmapped = unmapped.merge(
    context,
    on="signal_date",
    how="left",
    validate="one_to_one",
)

if unmapped["raw_macro_narrative"].isna().any():
    raise RuntimeError(
        "Failed to merge RAW macro state for some rows."
    )

bad_raw = (
    unmapped["raw_macro_narrative"]
    != "UNKNOWN_TRANSITION"
)

if bad_raw.any():
    raise RuntimeError(
        "UNMAPPED family contains non-UNKNOWN RAW state."
    )


# ============================================================
# BUILD NEIGHBOR STATES IF NOT ALREADY AVAILABLE
#
# IMPORTANT:
# These use t-1 / t+1 RAW states ONLY FOR DIAGNOSTICS.
# They are NOT allowed as candidate classification inputs.
# ============================================================

if (
    "previous_raw_state" not in unmapped.columns
    or "next_raw_state" not in unmapped.columns
):

    full = evidence[
        [
            "signal_date",
            "raw_macro_narrative",
        ]
    ].sort_values(
        "signal_date"
    ).copy()

    full["previous_raw_state"] = (
        full["raw_macro_narrative"].shift(1)
    )

    full["next_raw_state"] = (
        full["raw_macro_narrative"].shift(-1)
    )

    neighbor_context = full[
        [
            "signal_date",
            "previous_raw_state",
            "next_raw_state",
        ]
    ]

    unmapped = unmapped.drop(
        columns=[
            c
            for c in (
                "previous_raw_state",
                "next_raw_state",
            )
            if c in unmapped.columns
        ]
    )

    unmapped = unmapped.merge(
        neighbor_context,
        on="signal_date",
        how="left",
        validate="one_to_one",
    )


# ============================================================
# ERA
# ============================================================

unmapped["year"] = (
    unmapped["signal_date"].dt.year
)


def classify_era(year: int) -> str:

    if year <= 2010:
        return "2008-2010_GFC_AFTERMATH"

    if year <= 2014:
        return "2011-2014_EURO_QE"

    if year <= 2019:
        return "2015-2019_PRE_COVID"

    if year <= 2021:
        return "2020-2021_COVID"

    if year <= 2023:
        return "2022-2023_INFLATION"

    return "2024-2026_RECENT"


unmapped["era"] = (
    unmapped["year"].map(
        classify_era
    )
)


# ============================================================
# DESCRIPTIVE ECONOMIC AXES
#
# IMPORTANT:
# These labels are descriptions of contemporaneous evidence,
# NOT new Macro states.
# ============================================================

def rates_description(x):

    if x == -1:
        return "RATES_EASING"

    if x == 1:
        return "RATES_TIGHTENING"

    return "RATES_NEUTRAL"


def usd_description(x):

    if x == -1:
        return "USD_EASING"

    if x == 1:
        return "USD_TIGHTENING"

    return "USD_NEUTRAL"


def vix_description(x):

    if x == -1:
        return "VOL_EASING"

    if x == 1:
        return "VOL_RISING"

    return "VOL_NEUTRAL"


def oil_description(x):

    if x == -1:
        return "OIL_FALLING"

    if x == 1:
        return "OIL_RISING"

    return "OIL_NEUTRAL"


unmapped["rates_condition"] = (
    unmapped["US10Y_DIR"].map(
        rates_description
    )
)

unmapped["usd_condition"] = (
    unmapped["DXY_DIR"].map(
        usd_description
    )
)

unmapped["vol_condition"] = (
    unmapped["VIX_DIR"].map(
        vix_description
    )
)

unmapped["oil_condition"] = (
    unmapped["WTI_DIR"].map(
        oil_description
    )
)


# ============================================================
# ECONOMIC PRESSURE DESCRIPTION
#
# Again: descriptive research tag only.
#
# No portfolio action.
# No state assignment.
# ============================================================

def descriptive_pressure(row):

    rates = row["US10Y_DIR"]
    usd = row["DXY_DIR"]
    vix = row["VIX_DIR"]
    oil = row["WTI_DIR"]
    hy = str(row["HY_OAS_STATUS"]).upper()

    # Rates easing but USD + vol tightening:
    # conflicting growth / funding / risk evidence.
    if rates == -1 and usd == 1 and vix == 1:
        return "EASING_RATES_WITH_RISK_TIGHTENING"

    # Rates easing, USD tightening, vol easing:
    # rates relief but persistent dollar pressure.
    if rates == -1 and usd == 1 and vix == -1:
        return "RATES_RELIEF_WITH_USD_PRESSURE"

    # Rates + USD easing but VIX rising:
    # nominal conditions easing while risk aversion rises.
    if rates == -1 and usd == -1 and vix == 1:
        return "NOMINAL_EASING_WITH_VOL_STRESS"

    # Rates tightening, USD easing, vol easing:
    # growth/reflation-like cross current but oil may disagree.
    if rates == 1 and usd == -1 and vix == -1:
        return "RATES_PRESSURE_WITH_RISK_APPETITE"

    # Rates tightening, USD easing, vol rising:
    # mixed inflation/risk pressure.
    if rates == 1 and usd == -1 and vix == 1:
        return "RATES_AND_VOL_PRESSURE_WITH_WEAK_USD"

    return "OTHER_VALID_CROSS_CURRENT"


unmapped["descriptive_pressure"] = (
    unmapped.apply(
        descriptive_pressure,
        axis=1,
    )
)


# ============================================================
# FAMILY SUMMARY
# ============================================================

family_summary = (
    unmapped
    .groupby(
        "structural_family",
        dropna=False,
    )
    .agg(
        observations=("signal_date", "size"),
        first_date=("signal_date", "min"),
        last_date=("signal_date", "max"),
        years_present=("year", "nunique"),
        eras_present=("era", "nunique"),
        pressure_descriptions=(
            "descriptive_pressure",
            "nunique",
        ),
    )
    .reset_index()
)

family_summary["share_of_unmapped"] = (
    family_summary["observations"]
    / len(unmapped)
)

family_summary = family_summary.sort_values(
    "observations",
    ascending=False,
)


# ============================================================
# HY PROFILE
# ============================================================

hy_profile = (
    unmapped
    .groupby(
        [
            "structural_family",
            "HY_OAS_STATUS",
        ],
        dropna=False,
    )
    .size()
    .rename("observations")
    .reset_index()
)

family_totals = (
    unmapped
    .groupby(
        "structural_family"
    )
    .size()
    .rename("family_total")
)

hy_profile = hy_profile.merge(
    family_totals,
    on="structural_family",
    how="left",
)

hy_profile["share_within_family"] = (
    hy_profile["observations"]
    / hy_profile["family_total"]
)


# ============================================================
# WTI PROFILE
# ============================================================

wti_profile = (
    unmapped
    .groupby(
        [
            "structural_family",
            "WTI_DIR",
        ],
        dropna=False,
    )
    .size()
    .rename("observations")
    .reset_index()
)

wti_profile = wti_profile.merge(
    family_totals,
    on="structural_family",
    how="left",
)

wti_profile["share_within_family"] = (
    wti_profile["observations"]
    / wti_profile["family_total"]
)


# ============================================================
# VIX PROFILE
# ============================================================

vix_profile = (
    unmapped
    .groupby(
        [
            "structural_family",
            "VIX_DIR",
        ],
        dropna=False,
    )
    .size()
    .rename("observations")
    .reset_index()
)

vix_profile = vix_profile.merge(
    family_totals,
    on="structural_family",
    how="left",
)

vix_profile["share_within_family"] = (
    vix_profile["observations"]
    / vix_profile["family_total"]
)


# ============================================================
# EXACT COMBINATIONS
# ============================================================

exact_combinations = (
    unmapped
    .groupby(
        [
            "structural_family",
            "US10Y_DIR",
            "DXY_DIR",
            "VIX_DIR",
            "WTI_DIR",
            "HY_OAS_STATUS",
            "descriptive_pressure",
        ],
        dropna=False,
    )
    .size()
    .rename("observations")
    .reset_index()
)

exact_combinations = exact_combinations.merge(
    family_totals,
    on="structural_family",
    how="left",
)

exact_combinations[
    "share_within_family"
] = (
    exact_combinations["observations"]
    / exact_combinations["family_total"]
)

exact_combinations = (
    exact_combinations.sort_values(
        [
            "structural_family",
            "observations",
        ],
        ascending=[
            True,
            False,
        ],
    )
)


# ============================================================
# NEIGHBOR STATE DIAGNOSTICS
#
# FUTURE STATE IS DIAGNOSTIC ONLY.
# This table MUST NOT be used to define the candidate rule.
# ============================================================

neighbor_states = (
    unmapped
    .groupby(
        [
            "structural_family",
            "previous_raw_state",
            "next_raw_state",
        ],
        dropna=False,
    )
    .size()
    .rename("observations")
    .reset_index()
)

neighbor_states = neighbor_states.merge(
    family_totals,
    on="structural_family",
    how="left",
)

neighbor_states["share_within_family"] = (
    neighbor_states["observations"]
    / neighbor_states["family_total"]
)

neighbor_states = neighbor_states.sort_values(
    [
        "structural_family",
        "observations",
    ],
    ascending=[
        True,
        False,
    ],
)


# ============================================================
# ERA PROFILE
# ============================================================

era_profile = (
    unmapped
    .groupby(
        [
            "structural_family",
            "era",
        ],
        dropna=False,
    )
    .size()
    .rename("observations")
    .reset_index()
)

era_profile = era_profile.merge(
    family_totals,
    on="structural_family",
    how="left",
)

era_profile["share_within_family"] = (
    era_profile["observations"]
    / era_profile["family_total"]
)


# ============================================================
# SAVE
# ============================================================

unmapped.to_csv(
    DAILY_OUT,
    index=False,
)

family_summary.to_csv(
    SUMMARY_OUT,
    index=False,
)

hy_profile.to_csv(
    HY_OUT,
    index=False,
)

wti_profile.to_csv(
    WTI_OUT,
    index=False,
)

vix_profile.to_csv(
    VIX_OUT,
    index=False,
)

exact_combinations.to_csv(
    COMBO_OUT,
    index=False,
)

neighbor_states.to_csv(
    NEIGHBOR_OUT,
    index=False,
)

era_profile.to_csv(
    ERA_OUT,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print("=" * 136)
print("MACRO UNKNOWN — UNMAPPED ECONOMIC INTERPRETATION AUDIT")
print("=" * 136)

print()
print("===== CONTRACT =====")
print(f"Total historical observations : {len(evidence)}")
print(f"UNKNOWN observations          : {len(families)}")
print(f"UNMAPPED valid observations   : {len(unmapped)}")
print(
    "Share of UNKNOWN             : "
    f"{len(unmapped) / len(families):.2%}"
)
print("LOW_INFORMATION included      : NO")
print("Future state used for rules   : NO")
print("Returns used                  : NO")
print("13/15/18 executed             : NO")

print()
print("===== UNMAPPED FAMILY SUMMARY =====")

print(
    family_summary.to_string(
        index=False,
        formatters={
            "share_of_unmapped":
                lambda x: f"{x:.2%}",
        },
    )
)

print()
print("===== HY PROFILE =====")

print(
    hy_profile.to_string(
        index=False,
        formatters={
            "share_within_family":
                lambda x: f"{x:.2%}",
        },
    )
)

print()
print("===== WTI PROFILE =====")

print(
    wti_profile.to_string(
        index=False,
        formatters={
            "share_within_family":
                lambda x: f"{x:.2%}",
        },
    )
)

print()
print("===== DESCRIPTIVE PRESSURE SUMMARY =====")

pressure_summary = (
    unmapped
    .groupby(
        [
            "structural_family",
            "descriptive_pressure",
        ]
    )
    .size()
    .rename("observations")
    .reset_index()
)

pressure_summary = pressure_summary.merge(
    family_totals,
    on="structural_family",
    how="left",
)

pressure_summary["share_within_family"] = (
    pressure_summary["observations"]
    / pressure_summary["family_total"]
)

print(
    pressure_summary.to_string(
        index=False,
        formatters={
            "share_within_family":
                lambda x: f"{x:.2%}",
        },
    )
)

print()
print("===== TOP 5 EXACT COMBINATIONS PER FAMILY =====")

top_exact = (
    exact_combinations
    .groupby(
        "structural_family",
        group_keys=False,
    )
    .head(5)
)

print(
    top_exact.to_string(
        index=False,
        formatters={
            "share_within_family":
                lambda x: f"{x:.2%}",
        },
    )
)

print()
print("===== TOP 5 NEIGHBOR PATHS PER FAMILY =====")
print("DIAGNOSTIC ONLY — NEXT STATE MUST NOT DEFINE A RULE")

top_neighbors = (
    neighbor_states
    .groupby(
        "structural_family",
        group_keys=False,
    )
    .head(5)
)

print(
    top_neighbors.to_string(
        index=False,
        formatters={
            "share_within_family":
                lambda x: f"{x:.2%}",
        },
    )
)

print()
print("===== FAMILY PRESENCE BY ERA =====")

era_pivot = (
    era_profile
    .pivot(
        index="structural_family",
        columns="era",
        values="observations",
    )
    .fillna(0)
    .astype(int)
)

print(
    era_pivot.to_string()
)

print()
print("===== INTERPRETATION GATE =====")

print(
    """
This audit does NOT create Macro V4.

The five recurring UNMAPPED_VALID_REGION families are being
treated as evidence regions, not portfolio regimes.

For each family we now ask:

1. Is the evidence economically coherent?
2. Is HY credit behavior stable or heterogeneous?
3. Does WTI materially split the family?
4. Does the same family recur across multiple market eras?
5. Is the family adjacent to one existing state consistently,
   or does it bridge several different states?

Possible conclusions at the NEXT gate:

A. EXISTING-STATE EXTENSION
   Evidence is economically consistent with an existing
   Production narrative and the current rule is too narrow.

B. TRANSITION / MIXED REGION
   Evidence is structurally real but intentionally should not
   receive a directional named macro state.

C. CANDIDATE NEW TAXONOMY
   Evidence is coherent, persistent across eras and cannot be
   represented faithfully by an existing state.

D. SPLIT REQUIRED
   The family itself is too heterogeneous; HY / WTI / magnitude
   must divide it before interpretation.

Frequency alone does NOT authorize a state.

Future next-state information is diagnostic only and must
never be used to construct a PIT Production classifier.
""".strip()
)


# ============================================================
# AUDIT MEMO
# ============================================================

audit = f"""
MACRO UNMAPPED ECONOMIC INTERPRETATION AUDIT V1

SCOPE
-----
Historical observations : {len(evidence)}
UNKNOWN observations    : {len(families)}
UNMAPPED valid region   : {len(unmapped)}

PURPOSE
-------
Determine whether the recurring valid evidence regions
currently mapped to UNKNOWN_TRANSITION are:

- narrow versions of existing Macro narratives,
- genuine transition / mixed regions,
- candidates for new taxonomy,
- or internally heterogeneous regions requiring a split.

INPUT CONTRACT
--------------
Uses only previously reconstructed historical PIT evidence:

- US10Y direction
- DXY direction
- VIX direction
- WTI direction
- HY OAS status

No new Macro data is introduced.

LOW INFORMATION
---------------
FLAT_LOW_INFORMATION is excluded.

That problem belongs to the separate UNKNOWN persistence /
decay architecture.

FUTURE INFORMATION
------------------
next_raw_state may appear in diagnostic neighbor tables only.

It is explicitly forbidden as an input to any candidate
classification rule.

NO PERFORMANCE SELECTION
------------------------
Returns used       : NO
CAGR used          : NO
Sharpe used        : NO
Filter13 executed  : NO
Filter15 executed  : NO
Filter18 executed  : NO

DECISION STATUS
---------------
No Macro V4 state is authorized by this audit.

Production modified : NO
Parameter selected  : NO
Commit              : NO
""".strip()

AUDIT_OUT.write_text(
    audit,
    encoding="utf-8",
)


print()
print("===== ARTIFACTS =====")
print("Daily     :", DAILY_OUT)
print("Summary   :", SUMMARY_OUT)
print("HY        :", HY_OUT)
print("WTI       :", WTI_OUT)
print("VIX       :", VIX_OUT)
print("Exact     :", COMBO_OUT)
print("Neighbors :", NEIGHBOR_OUT)
print("Era       :", ERA_OUT)
print("Audit     :", AUDIT_OUT)

print()
print("PRODUCTION MODIFIED : NO")
print("FILTER13/15/18      : UNCHANGED / NOT EXECUTED")
print("RETURNS USED        : NO")
print("PERFORMANCE USED    : NO")
print("NEW MACRO STATE     : NO")
print("PARAMETER SELECTED  : NO")
print("COMMIT              : NO")

print()
print("=" * 136)
print("UNMAPPED ECONOMIC INTERPRETATION AUDIT COMPLETE — DO NOT COMMIT")
print("=" * 136)
