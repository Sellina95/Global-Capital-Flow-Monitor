from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


# ============================================================
# PATH / IMPORT SAFETY
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


RESULT_ROOT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

SPEC_DIR = (
    RESULT_ROOT
    / "macro_v4_candidate_taxonomy_spec_v1"
)

SPEC_JSON = (
    SPEC_DIR
    / "macro_v4_candidate_taxonomy_spec.json"
)

EVIDENCE_DIR = (
    RESULT_ROOT
    / "macro_unknown_evidence_attribution_v1"
)

EVIDENCE_DAILY = (
    EVIDENCE_DIR
    / "unknown_evidence_daily.csv"
)

FAMILY_DIR = (
    RESULT_ROOT
    / "macro_unknown_structural_families_v1"
)

FAMILY_DAILY = (
    FAMILY_DIR
    / "unknown_structural_family_daily.csv"
)

OUT_DIR = (
    RESULT_ROOT
    / "macro_v4_research_classifier_v1"
)

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DAILY_OUT = (
    OUT_DIR
    / "macro_v4_classifier_daily.csv"
)

SUMMARY_OUT = (
    OUT_DIR
    / "macro_v4_classifier_summary.csv"
)

RULE_OUT = (
    OUT_DIR
    / "macro_v4_classifier_rule_counts.csv"
)

AUDIT_OUT = (
    OUT_DIR
    / "macro_v4_classifier_audit.txt"
)


# ============================================================
# FROZEN CONTRACT
# ============================================================

EXPECTED_SPEC_SHA256 = (
    "cd7174ea8ec93115b4fc9902fd55fe2b9"
    "ba443199929b01eae2bc4db4fb70bf3"
)

EXPECTED_UNKNOWN = 1328
EXPECTED_TARGET = 992
EXPECTED_REMAINING_UNKNOWN = 336

TARGET_FAMILIES = {
    "RATES_DOWN_USD_UP_VIX_UP",
    "RATES_DOWN_USD_UP_VIX_DOWN",
    "RATES_DOWN_USD_DOWN_VIX_UP",
    "RATES_UP_USD_DOWN_VIX_DOWN",
    "RATES_UP_USD_DOWN_VIX_UP",
}

FLAT_FAMILY = "FLAT_LOW_INFORMATION"


# ============================================================
# HELPERS
# ============================================================

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(
            lambda: f.read(1024 * 1024),
            b"",
        ):
            h.update(chunk)

    return h.hexdigest()


def normalize_state(value) -> str:
    if value is None:
        return ""

    if pd.isna(value):
        return ""

    return str(value).strip()


def normalize_hy(value) -> str:
    return normalize_state(value).upper()


def to_int_direction(value):
    try:
        if pd.isna(value):
            return None

        return int(float(value))

    except Exception:
        return None


def to_float_or_none(value):
    try:
        if value is None or pd.isna(value):
            return None

        return float(value)

    except Exception:
        return None


# ============================================================
# LOAD FROZEN SPEC
# ============================================================

if not SPEC_JSON.exists():
    raise FileNotFoundError(
        f"Missing frozen V4 spec: {SPEC_JSON}"
    )

with SPEC_JSON.open(
    "r",
    encoding="utf-8",
) as f:
    frozen_artifact = json.load(f)

if (
    "sha256" not in frozen_artifact
    or "spec" not in frozen_artifact
):
    raise RuntimeError(
        "Frozen V4 artifact contract invalid: "
        "expected sha256 + spec."
    )

frozen_spec = frozen_artifact["spec"]
embedded_spec_sha = str(
    frozen_artifact["sha256"]
).strip()

# IMPORTANT:
# Freeze script hashes the canonical semantic `spec` payload,
# NOT the wrapper JSON file itself.
spec_payload = json.dumps(
    frozen_spec,
    ensure_ascii=False,
    sort_keys=True,
    indent=2,
)

actual_spec_sha = hashlib.sha256(
    spec_payload.encode("utf-8")
).hexdigest()

spec_hash_identity = (
    embedded_spec_sha
    == EXPECTED_SPEC_SHA256
    and actual_spec_sha
    == EXPECTED_SPEC_SHA256
)

if not spec_hash_identity:
    raise RuntimeError(
        "\nFrozen V4 semantic spec SHA mismatch.\n"
        f"Expected : {EXPECTED_SPEC_SHA256}\n"
        f"Embedded : {embedded_spec_sha}\n"
        f"Computed : {actual_spec_sha}\n"
        "STOP — do not execute classifier."
    )


# ============================================================
# LOAD CANONICAL UNKNOWN EVIDENCE
# ============================================================

if not EVIDENCE_DAILY.exists():
    raise FileNotFoundError(
        f"Missing evidence daily: {EVIDENCE_DAILY}"
    )

if not FAMILY_DAILY.exists():
    raise FileNotFoundError(
        f"Missing family daily: {FAMILY_DAILY}"
    )

evidence = pd.read_csv(
    EVIDENCE_DAILY
)

families = pd.read_csv(
    FAMILY_DAILY
)


# ============================================================
# COLUMN CONTRACT
# ============================================================

required_evidence = {
    "signal_date",
    "raw_macro_narrative",
    "US10Y_DIR",
    "DXY_DIR",
    "VIX_DIR",
    "WTI_DIR",
    "HY_OAS_STATUS",
}

missing_evidence = (
    required_evidence
    - set(evidence.columns)
)

if missing_evidence:
    raise RuntimeError(
        "Evidence file missing columns: "
        + ", ".join(
            sorted(missing_evidence)
        )
    )


required_family = {
    "signal_date",
    "structural_family",
}

missing_family = (
    required_family
    - set(families.columns)
)

if missing_family:
    raise RuntimeError(
        "Family file missing columns: "
        + ", ".join(
            sorted(missing_family)
        )
    )


# ============================================================
# CANONICAL UNKNOWN IDENTITY
# ============================================================

evidence["signal_date"] = pd.to_datetime(
    evidence["signal_date"],
    errors="raise",
)

families["signal_date"] = pd.to_datetime(
    families["signal_date"],
    errors="raise",
)

evidence = evidence.sort_values(
    "signal_date"
).reset_index(drop=True)

families = families.sort_values(
    "signal_date"
).reset_index(drop=True)


unknown = evidence[
    evidence["raw_macro_narrative"]
    .astype(str)
    .str.strip()
    .eq("UNKNOWN_TRANSITION")
].copy()

if len(unknown) != EXPECTED_UNKNOWN:
    raise RuntimeError(
        "Canonical UNKNOWN identity failed: "
        f"{len(unknown)} != {EXPECTED_UNKNOWN}"
    )


# ============================================================
# MERGE STRUCTURAL FAMILY
# ============================================================

family_context = families[
    [
        "signal_date",
        "structural_family",
    ]
].copy()

if family_context["signal_date"].duplicated().any():
    raise RuntimeError(
        "Family daily contains duplicate signal_date."
    )

unknown = unknown.drop(
    columns=["structural_family"],
    errors="ignore",
)

unknown = unknown.merge(
    family_context,
    on="signal_date",
    how="left",
    validate="one_to_one",
)

if unknown["structural_family"].isna().any():
    bad = unknown.loc[
        unknown["structural_family"].isna(),
        "signal_date",
    ]

    raise RuntimeError(
        "Missing structural family for UNKNOWN rows. "
        f"Count={len(bad)}"
    )


# ============================================================
# OPTIONAL VIX LEVEL
#
# CREDIT_STRESS precedence must be preserved.
# But this classifier is applied ONLY after Production RAW
# narrative has already returned UNKNOWN_TRANSITION.
#
# Therefore an UNKNOWN row must NOT be retrospectively
# relabeled CREDIT_STRESS using invented VIX levels.
#
# If VIX_TODAY exists in canonical evidence we may audit it,
# but never invent/backfill it.
# ============================================================

vix_today_col = None

for candidate in (
    "VIX_TODAY",
    "vix_today",
):
    if candidate in unknown.columns:
        vix_today_col = candidate
        break


# ============================================================
# V4 RESEARCH CLASSIFIER
#
# IMPORTANT:
# - applies ONLY to Production UNKNOWN_TRANSITION
# - no future state
# - no returns
# - no downstream filters
# - WTI split only where frozen
# ============================================================

def classify_v4_candidate(row):
    raw = normalize_state(
        row.get("raw_macro_narrative")
    )

    family = normalize_state(
        row.get("structural_family")
    )

    wti = to_int_direction(
        row.get("WTI_DIR")
    )

    # --------------------------------------------------
    # GATE 0
    # V4 has no authority outside Production UNKNOWN.
    # --------------------------------------------------

    if raw != "UNKNOWN_TRANSITION":
        return {
            "v4_state": raw,
            "v4_rule_id": "NOT_APPLICABLE",
            "v4_applied": False,
            "collision_count": 0,
        }

    matches = []

    # --------------------------------------------------
    # D1
    # RATES DOWN / USD UP / VIX UP
    # split by contemporaneous WTI
    # --------------------------------------------------

    if family == "RATES_DOWN_USD_UP_VIX_UP":

        if wti == -1:
            matches.append(
                (
                    "D1_WTI_DOWN",
                    "V4_RATES_RELIEF_USD_VOL_PRESSURE_WTI_DOWN",
                )
            )

        if wti == 1:
            matches.append(
                (
                    "D1_WTI_UP",
                    "V4_RATES_RELIEF_USD_VOL_PRESSURE_WTI_UP",
                )
            )

    # --------------------------------------------------
    # D2
    # RATES DOWN / USD UP / VIX DOWN
    # split by contemporaneous WTI
    # --------------------------------------------------

    if family == "RATES_DOWN_USD_UP_VIX_DOWN":

        if wti == -1:
            matches.append(
                (
                    "D2_WTI_DOWN",
                    "V4_RATES_VOL_RELIEF_USD_PRESSURE_WTI_DOWN",
                )
            )

        if wti == 1:
            matches.append(
                (
                    "D2_WTI_UP",
                    "V4_RATES_VOL_RELIEF_USD_PRESSURE_WTI_UP",
                )
            )

    # --------------------------------------------------
    # C1
    # --------------------------------------------------

    if family == "RATES_DOWN_USD_DOWN_VIX_UP":
        matches.append(
            (
                "C1",
                "V4_NOMINAL_EASING_WITH_VOL_INFLATION_STRESS",
            )
        )

    # --------------------------------------------------
    # C2
    # --------------------------------------------------

    if family == "RATES_UP_USD_DOWN_VIX_DOWN":
        matches.append(
            (
                "C2",
                "V4_RATES_PRESSURE_WITH_BROAD_RISK_RELIEF",
            )
        )

    # --------------------------------------------------
    # C3
    # --------------------------------------------------

    if family == "RATES_UP_USD_DOWN_VIX_UP":
        matches.append(
            (
                "C3",
                "V4_RATES_VOL_PRESSURE_WITH_WEAK_USD",
            )
        )

    collision_count = len(matches)

    if collision_count > 1:
        return {
            "v4_state": "CLASSIFIER_COLLISION",
            "v4_rule_id": "COLLISION",
            "v4_applied": False,
            "collision_count": collision_count,
        }

    if collision_count == 1:
        rule_id, state = matches[0]

        return {
            "v4_state": state,
            "v4_rule_id": rule_id,
            "v4_applied": True,
            "collision_count": 1,
        }

    return {
        "v4_state": "UNKNOWN_TRANSITION",
        "v4_rule_id": "FALLBACK",
        "v4_applied": False,
        "collision_count": 0,
    }


classified_payload = unknown.apply(
    classify_v4_candidate,
    axis=1,
    result_type="expand",
)

classified = pd.concat(
    [
        unknown.reset_index(drop=True),
        classified_payload.reset_index(drop=True),
    ],
    axis=1,
)


# ============================================================
# VALIDATION GATES
# ============================================================

target_mask = classified[
    "structural_family"
].isin(
    TARGET_FAMILIES
)

flat_mask = classified[
    "structural_family"
].eq(
    FLAT_FAMILY
)

applied_mask = classified[
    "v4_applied"
].eq(True)

remaining_unknown_mask = classified[
    "v4_state"
].eq(
    "UNKNOWN_TRANSITION"
)

collision_mask = classified[
    "v4_rule_id"
].eq(
    "COLLISION"
)


target_observations = int(
    target_mask.sum()
)

applied_observations = int(
    applied_mask.sum()
)

remaining_unknown = int(
    remaining_unknown_mask.sum()
)

flat_observations = int(
    flat_mask.sum()
)

collision_rows = int(
    collision_mask.sum()
)


# ============================================================
# PIT RULE IDENTITY
#
# Every applied rule must be explainable exclusively by
# contemporaneous family + WTI direction.
# ============================================================

pit_failures = 0

for _, row in classified[
    applied_mask
].iterrows():

    family = normalize_state(
        row["structural_family"]
    )

    wti = to_int_direction(
        row["WTI_DIR"]
    )

    rule = normalize_state(
        row["v4_rule_id"]
    )

    valid = False

    if (
        family
        == "RATES_DOWN_USD_UP_VIX_UP"
        and wti == -1
        and rule == "D1_WTI_DOWN"
    ):
        valid = True

    elif (
        family
        == "RATES_DOWN_USD_UP_VIX_UP"
        and wti == 1
        and rule == "D1_WTI_UP"
    ):
        valid = True

    elif (
        family
        == "RATES_DOWN_USD_UP_VIX_DOWN"
        and wti == -1
        and rule == "D2_WTI_DOWN"
    ):
        valid = True

    elif (
        family
        == "RATES_DOWN_USD_UP_VIX_DOWN"
        and wti == 1
        and rule == "D2_WTI_UP"
    ):
        valid = True

    elif (
        family
        == "RATES_DOWN_USD_DOWN_VIX_UP"
        and rule == "C1"
    ):
        valid = True

    elif (
        family
        == "RATES_UP_USD_DOWN_VIX_DOWN"
        and rule == "C2"
    ):
        valid = True

    elif (
        family
        == "RATES_UP_USD_DOWN_VIX_UP"
        and rule == "C3"
    ):
        valid = True

    if not valid:
        pit_failures += 1


# ============================================================
# CREDIT_STRESS PRECEDENCE AUDIT
#
# Since V4 only receives RAW UNKNOWN rows, no RAW
# CREDIT_STRESS observation may exist in this classified set.
# ============================================================

raw_credit_stress_inside_classifier = int(
    classified[
        "raw_macro_narrative"
    ]
    .astype(str)
    .str.strip()
    .eq("CREDIT_STRESS")
    .sum()
)


# ============================================================
# EXPECTED GATES
# ============================================================

gates = {
    "SPEC_HASH_IDENTITY":
        spec_hash_identity,

    "UNKNOWN_TOTAL_IDENTITY":
        len(classified)
        == EXPECTED_UNKNOWN,

    "TARGET_TOTAL_IDENTITY":
        target_observations
        == EXPECTED_TARGET,

    "TARGET_CLASSIFIED_IDENTITY":
        applied_observations
        == EXPECTED_TARGET,

    "REMAINING_UNKNOWN_IDENTITY":
        remaining_unknown
        == EXPECTED_REMAINING_UNKNOWN,

    "FLAT_LOW_INFORMATION_IDENTITY":
        flat_observations
        == EXPECTED_REMAINING_UNKNOWN,

    "FLAT_LOW_INFORMATION_PRESERVED":
        bool(
            classified.loc[
                flat_mask,
                "v4_state",
            ]
            .eq("UNKNOWN_TRANSITION")
            .all()
        ),

    "CLASSIFIER_EXCLUSIVITY":
        collision_rows == 0,

    "PIT_RULE_IDENTITY":
        pit_failures == 0,

    "CREDIT_STRESS_OUTSIDE_V4_SCOPE":
        raw_credit_stress_inside_classifier == 0,

    "NO_UNAUTHORIZED_FAMILY_CLASSIFICATION":
        int(
            (
                applied_mask
                & ~target_mask
            ).sum()
        )
        == 0,
}


status = (
    "PASS"
    if all(gates.values())
    else "FAIL"
)


# ============================================================
# RULE COUNTS
# ============================================================

rule_counts = (
    classified
    .groupby(
        [
            "v4_rule_id",
            "v4_state",
        ],
        dropna=False,
    )
    .size()
    .reset_index(
        name="observations"
    )
    .sort_values(
        [
            "v4_rule_id",
            "v4_state",
        ]
    )
)


# ============================================================
# FAMILY SUMMARY
# ============================================================

family_summary = (
    classified
    .groupby(
        "structural_family",
        dropna=False,
    )
    .agg(
        observations=(
            "signal_date",
            "size",
        ),
        v4_applied=(
            "v4_applied",
            "sum",
        ),
        remaining_unknown=(
            "v4_state",
            lambda s: int(
                (
                    s
                    == "UNKNOWN_TRANSITION"
                ).sum()
            ),
        ),
        collisions=(
            "v4_rule_id",
            lambda s: int(
                (
                    s
                    == "COLLISION"
                ).sum()
            ),
        ),
    )
    .reset_index()
)

family_summary[
    "classification_rate"
] = (
    family_summary[
        "v4_applied"
    ]
    / family_summary[
        "observations"
    ]
)

family_summary[
    "classification_rate"
] = family_summary[
    "classification_rate"
].map(
    lambda x: f"{x:.2%}"
)


# ============================================================
# SAVE ARTIFACTS
# ============================================================

classified.to_csv(
    DAILY_OUT,
    index=False,
)

family_summary.to_csv(
    SUMMARY_OUT,
    index=False,
)

rule_counts.to_csv(
    RULE_OUT,
    index=False,
)


# ============================================================
# AUDIT TEXT
# ============================================================

lines = []

lines.append(
    "=" * 150
)

lines.append(
    "MACRO V4 — RESEARCH-ONLY CLASSIFIER VALIDATION"
)

lines.append(
    "=" * 150
)

lines.append("")
lines.append(
    "===== FROZEN SPEC ====="
)

lines.append(
    f"Expected SHA256 : {EXPECTED_SPEC_SHA256}"
)

lines.append(
    f"Actual SHA256   : {actual_spec_sha}"
)

lines.append(
    "Identity        : "
    + (
        "PASS"
        if spec_hash_identity
        else "FAIL"
    )
)

lines.append("")
lines.append(
    "===== CLASSIFIER SCOPE ====="
)

lines.append(
    f"Production UNKNOWN observations : {len(classified)}"
)

lines.append(
    f"Candidate target observations   : {target_observations}"
)

lines.append(
    f"V4 classified observations      : {applied_observations}"
)

lines.append(
    f"Remaining UNKNOWN               : {remaining_unknown}"
)

lines.append(
    f"FLAT_LOW_INFORMATION            : {flat_observations}"
)

lines.append(
    f"Collision rows                  : {collision_rows}"
)

lines.append(
    f"PIT rule failures               : {pit_failures}"
)

lines.append("")
lines.append(
    "===== EXPECTED CONTRACT ====="
)

lines.append(
    f"UNKNOWN before      : {EXPECTED_UNKNOWN}"
)

lines.append(
    f"Candidate target    : {EXPECTED_TARGET}"
)

lines.append(
    f"UNKNOWN after       : {EXPECTED_REMAINING_UNKNOWN}"
)

lines.append("")
lines.append(
    "===== FAMILY RESULT ====="
)

lines.append(
    family_summary.to_string(
        index=False
    )
)

lines.append("")
lines.append(
    "===== RULE COUNTS ====="
)

lines.append(
    rule_counts.to_string(
        index=False
    )
)

lines.append("")
lines.append(
    "===== VALIDATION GATES ====="
)

for name, passed in gates.items():
    lines.append(
        f"{name:<45} : "
        f"{'PASS' if passed else 'FAIL'}"
    )

lines.append("")
lines.append(
    "===== CAUSAL CONTRACT ====="
)

lines.append(
    "Classifier authority : Production UNKNOWN_TRANSITION only"
)

lines.append(
    "Future state used    : NO"
)

lines.append(
    "Returns used         : NO"
)

lines.append(
    "Filter13 executed    : NO"
)

lines.append(
    "Filter15 executed    : NO"
)

lines.append(
    "Filter18 executed    : NO"
)

lines.append(
    "New macro data       : NO"
)

lines.append(
    "VIX level backfill   : NO"
)

lines.append(
    "Parameter tuning     : NO"
)

lines.append("")
lines.append(
    "===== CREDIT_STRESS ====="
)

lines.append(
    "Existing Production CREDIT_STRESS has precedence."
)

lines.append(
    "V4 classifier receives only rows already classified"
)

lines.append(
    "by Production as UNKNOWN_TRANSITION."
)

lines.append(
    "Therefore V4 cannot overwrite Production CREDIT_STRESS."
)

lines.append("")
lines.append(
    "===== ARTIFACTS ====="
)

lines.append(
    f"Daily   : {DAILY_OUT}"
)

lines.append(
    f"Summary : {SUMMARY_OUT}"
)

lines.append(
    f"Rules   : {RULE_OUT}"
)

lines.append(
    f"Audit   : {AUDIT_OUT}"
)

lines.append("")
lines.append(
    "PRODUCTION MODIFIED : NO"
)

lines.append(
    "FILTER13/15/18      : UNCHANGED / NOT EXECUTED"
)

lines.append(
    "RETURNS USED        : NO"
)

lines.append(
    "PERFORMANCE USED    : NO"
)

lines.append(
    "PARAMETER SELECTED  : NO"
)

lines.append(
    "COMMIT              : NO"
)

lines.append("")
lines.append(
    f"STATUS : {status}"
)

if status == "PASS":
    lines.append("")
    lines.append(
        "NEXT IF PASS:"
    )
    lines.append(
        "MACRO V4 RESEARCH-ONLY CAUSAL PROPAGATION HARNESS"
    )
    lines.append(
        "-> preserve canonical Production baseline"
    )
    lines.append(
        "-> replace RAW UNKNOWN only with frozen V4 candidate state"
    )
    lines.append(
        "-> derive strategic state causally"
    )
    lines.append(
        "-> map MARKET_REGIME"
    )
    lines.append(
        "-> propagate through unchanged 13 / 15 / 18"
    )
    lines.append(
        "-> STILL NO RETURNS / PERFORMANCE SELECTION"
    )

lines.append("")
lines.append(
    "=" * 150
)

audit_text = "\n".join(
    lines
)

AUDIT_OUT.write_text(
    audit_text,
    encoding="utf-8",
)

print(
    audit_text
)

if status != "PASS":
    raise RuntimeError(
        "MACRO V4 classifier validation FAILED. "
        "Do not continue to downstream propagation."
    )
