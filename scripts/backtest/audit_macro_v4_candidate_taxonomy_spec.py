from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

INPUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_unknown_candidate_resolution_v1"
)

CLASSIFICATION_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_unknown_family_classification_gate_v1"
)

OUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_v4_candidate_taxonomy_spec_v1"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

RESOLUTION_PATH = (
    INPUT_DIR
    / "candidate_resolution_summary.csv"
)

DETAIL_PATH = (
    CLASSIFICATION_DIR
    / "family_classification_detail.csv"
)

SPEC_JSON = (
    OUT_DIR
    / "macro_v4_candidate_taxonomy_spec.json"
)

RULES_CSV = (
    OUT_DIR
    / "macro_v4_candidate_taxonomy_rules.csv"
)

COVERAGE_CSV = (
    OUT_DIR
    / "macro_v4_candidate_taxonomy_coverage.csv"
)

AUDIT_TXT = (
    OUT_DIR
    / "macro_v4_candidate_taxonomy_spec_audit.txt"
)


# ============================================================
# Frozen candidate universe
# ============================================================

EXPECTED_FAMILIES = {
    "RATES_DOWN_USD_UP_VIX_UP": "D_SPLIT_CONFIRMED",
    "RATES_DOWN_USD_UP_VIX_DOWN": "D_SPLIT_CONFIRMED",
    "RATES_DOWN_USD_DOWN_VIX_UP": "C_REMAINS_CANDIDATE",
    "RATES_UP_USD_DOWN_VIX_DOWN": "C_REMAINS_CANDIDATE",
    "RATES_UP_USD_DOWN_VIX_UP": "C_REMAINS_CANDIDATE",
}

EXPECTED_OBSERVATIONS = {
    "RATES_DOWN_USD_UP_VIX_UP": 335,
    "RATES_DOWN_USD_UP_VIX_DOWN": 277,
    "RATES_DOWN_USD_DOWN_VIX_UP": 179,
    "RATES_UP_USD_DOWN_VIX_DOWN": 129,
    "RATES_UP_USD_DOWN_VIX_UP": 72,
}

EXPECTED_TOTAL = 992
EXPECTED_D_TOTAL = 612
EXPECTED_C_TOTAL = 380


# ============================================================
# Candidate taxonomy
#
# IMPORTANT:
# These are RESEARCH taxonomy IDs, not Production labels.
#
# We deliberately avoid pretending that these labels are
# economically validated Production narratives.
# ============================================================

RULES = [
    # --------------------------------------------------------
    # Priority 10
    # Existing Production CREDIT_STRESS always retains
    # precedence.
    #
    # Exact Production condition:
    #
    # HY == FRACTURE
    # OR
    # HY == HOT AND VIX_DIR == +1 AND VIX_TODAY >= 22
    #
    # This is not a new V4 rule.
    # It is frozen here as a precedence contract.
    # --------------------------------------------------------
    {
        "priority": 10,
        "rule_id": "P_EXISTING_CREDIT_STRESS",
        "rule_type": "EXISTING_PRODUCTION_PRECEDENCE",
        "family": "*",
        "us10y_dir": "*",
        "dxy_dir": "*",
        "vix_dir": "*",
        "wti_dir": "*",
        "hy_condition": (
            "FRACTURE OR "
            "(HOT AND VIX_DIR=1 AND VIX_TODAY>=22)"
        ),
        "candidate_state": "CREDIT_STRESS",
        "production_authorized": False,
        "notes": (
            "Existing Production CREDIT_STRESS precedence. "
            "V4 must never overwrite an observation already "
            "classified as CREDIT_STRESS."
        ),
    },

    # --------------------------------------------------------
    # D family 1
    # Rates down / USD up / VIX up.
    #
    # WTI materially two-way:
    # DOWN 64.78%
    # UP   35.22%
    #
    # Therefore split required.
    # --------------------------------------------------------
    {
        "priority": 100,
        "rule_id": "D1_WTI_DOWN",
        "rule_type": "V4_CANDIDATE_SPLIT",
        "family": "RATES_DOWN_USD_UP_VIX_UP",
        "us10y_dir": -1,
        "dxy_dir": 1,
        "vix_dir": 1,
        "wti_dir": -1,
        "hy_condition": "NON_CREDIT_STRESS",
        "candidate_state": (
            "V4_RATES_RELIEF_USD_VOL_PRESSURE_WTI_DOWN"
        ),
        "production_authorized": False,
        "notes": (
            "Research-only candidate. "
            "Risk tightening via USD/VIX while rates and WTI fall."
        ),
    },
    {
        "priority": 101,
        "rule_id": "D1_WTI_UP",
        "rule_type": "V4_CANDIDATE_SPLIT",
        "family": "RATES_DOWN_USD_UP_VIX_UP",
        "us10y_dir": -1,
        "dxy_dir": 1,
        "vix_dir": 1,
        "wti_dir": 1,
        "hy_condition": "NON_CREDIT_STRESS",
        "candidate_state": (
            "V4_RATES_RELIEF_USD_VOL_PRESSURE_WTI_UP"
        ),
        "production_authorized": False,
        "notes": (
            "Research-only candidate. "
            "Rates relief conflicts with USD/VIX and WTI pressure."
        ),
    },

    # --------------------------------------------------------
    # D family 2
    # Rates down / USD up / VIX down.
    #
    # WTI split almost exactly 50/50.
    # --------------------------------------------------------
    {
        "priority": 110,
        "rule_id": "D2_WTI_DOWN",
        "rule_type": "V4_CANDIDATE_SPLIT",
        "family": "RATES_DOWN_USD_UP_VIX_DOWN",
        "us10y_dir": -1,
        "dxy_dir": 1,
        "vix_dir": -1,
        "wti_dir": -1,
        "hy_condition": "NON_CREDIT_STRESS",
        "candidate_state": (
            "V4_RATES_VOL_RELIEF_USD_PRESSURE_WTI_DOWN"
        ),
        "production_authorized": False,
        "notes": (
            "Research-only candidate. "
            "Rates/VIX relief with USD strength and WTI weakness."
        ),
    },
    {
        "priority": 111,
        "rule_id": "D2_WTI_UP",
        "rule_type": "V4_CANDIDATE_SPLIT",
        "family": "RATES_DOWN_USD_UP_VIX_DOWN",
        "us10y_dir": -1,
        "dxy_dir": 1,
        "vix_dir": -1,
        "wti_dir": 1,
        "hy_condition": "NON_CREDIT_STRESS",
        "candidate_state": (
            "V4_RATES_VOL_RELIEF_USD_PRESSURE_WTI_UP"
        ),
        "production_authorized": False,
        "notes": (
            "Research-only candidate. "
            "Rates/VIX relief with USD strength and WTI pressure."
        ),
    },

    # --------------------------------------------------------
    # C family 1
    #
    # Rates down / USD down / VIX up / WTI up.
    #
    # HOT + VIX up can collide with Production CREDIT_STRESS
    # only when VIX_TODAY >= 22.
    # That precedence is handled above.
    # --------------------------------------------------------
    {
        "priority": 120,
        "rule_id": "C1",
        "rule_type": "V4_CANDIDATE_NEW_TAXONOMY",
        "family": "RATES_DOWN_USD_DOWN_VIX_UP",
        "us10y_dir": -1,
        "dxy_dir": -1,
        "vix_dir": 1,
        "wti_dir": 1,
        "hy_condition": "NON_CREDIT_STRESS",
        "candidate_state": (
            "V4_NOMINAL_EASING_WITH_VOL_INFLATION_STRESS"
        ),
        "production_authorized": False,
        "notes": (
            "Research-only candidate. "
            "Nominal easing conflicts with rising volatility "
            "and WTI."
        ),
    },

    # --------------------------------------------------------
    # C family 2
    #
    # Rates up / USD down / VIX down / WTI down.
    # --------------------------------------------------------
    {
        "priority": 130,
        "rule_id": "C2",
        "rule_type": "V4_CANDIDATE_NEW_TAXONOMY",
        "family": "RATES_UP_USD_DOWN_VIX_DOWN",
        "us10y_dir": 1,
        "dxy_dir": -1,
        "vix_dir": -1,
        "wti_dir": -1,
        "hy_condition": "NON_CREDIT_STRESS",
        "candidate_state": (
            "V4_RATES_PRESSURE_WITH_BROAD_RISK_RELIEF"
        ),
        "production_authorized": False,
        "notes": (
            "Research-only candidate. "
            "Rates pressure occurs alongside weaker USD, "
            "lower VIX and lower WTI."
        ),
    },

    # --------------------------------------------------------
    # C family 3
    #
    # Rates up / USD down / VIX up / WTI down.
    #
    # Again HOT + VIX up requires explicit CREDIT_STRESS
    # precedence if VIX_TODAY >= 22.
    # --------------------------------------------------------
    {
        "priority": 140,
        "rule_id": "C3",
        "rule_type": "V4_CANDIDATE_NEW_TAXONOMY",
        "family": "RATES_UP_USD_DOWN_VIX_UP",
        "us10y_dir": 1,
        "dxy_dir": -1,
        "vix_dir": 1,
        "wti_dir": -1,
        "hy_condition": "NON_CREDIT_STRESS",
        "candidate_state": (
            "V4_RATES_VOL_PRESSURE_WITH_WEAK_USD"
        ),
        "production_authorized": False,
        "notes": (
            "Research-only candidate. "
            "Rates and volatility pressure coexist with "
            "weaker USD and WTI."
        ),
    },

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------
    {
        "priority": 999,
        "rule_id": "FALLBACK",
        "rule_type": "FALLBACK",
        "family": "*",
        "us10y_dir": "*",
        "dxy_dir": "*",
        "vix_dir": "*",
        "wti_dir": "*",
        "hy_condition": "*",
        "candidate_state": "UNKNOWN_TRANSITION",
        "production_authorized": False,
        "notes": (
            "Anything not explicitly covered remains UNKNOWN. "
            "No forced classification."
        ),
    },
]


# ============================================================
# Helpers
# ============================================================

def sha256_text(text: str) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )


def fail(message: str) -> None:
    raise RuntimeError(message)


# ============================================================
# Input checks
# ============================================================

print("=" * 140)
print("MACRO V4 — CANDIDATE TAXONOMY SPEC FREEZE")
print("=" * 140)

if not RESOLUTION_PATH.exists():
    fail(
        f"Missing candidate resolution artifact: "
        f"{RESOLUTION_PATH}"
    )

resolution = pd.read_csv(RESOLUTION_PATH)

required_resolution_cols = {
    "structural_family",
    "observations",
    "provisional_resolution",
}

missing_cols = (
    required_resolution_cols
    - set(resolution.columns)
)

if missing_cols:
    fail(
        "Resolution artifact missing columns: "
        + ", ".join(sorted(missing_cols))
    )

resolution = resolution[
    resolution["structural_family"].isin(
        EXPECTED_FAMILIES
    )
].copy()

if len(resolution) != 5:
    fail(
        f"Expected 5 candidate families, got "
        f"{len(resolution)}"
    )


# ============================================================
# Gate 1 — upstream identity
# ============================================================

identity_rows = []

for family, expected_resolution in EXPECTED_FAMILIES.items():

    row = resolution[
        resolution["structural_family"] == family
    ]

    if len(row) != 1:
        fail(
            f"Family identity failure: {family}"
        )

    row = row.iloc[0]

    actual_obs = int(row["observations"])
    expected_obs = EXPECTED_OBSERVATIONS[family]

    actual_resolution = str(
        row["provisional_resolution"]
    )

    obs_pass = actual_obs == expected_obs
    resolution_pass = (
        actual_resolution == expected_resolution
    )

    identity_rows.append(
        {
            "structural_family": family,
            "expected_observations": expected_obs,
            "actual_observations": actual_obs,
            "observation_identity": (
                "PASS" if obs_pass else "FAIL"
            ),
            "expected_resolution": expected_resolution,
            "actual_resolution": actual_resolution,
            "resolution_identity": (
                "PASS" if resolution_pass else "FAIL"
            ),
        }
    )

identity = pd.DataFrame(identity_rows)

if (
    (identity["observation_identity"] != "PASS").any()
    or
    (identity["resolution_identity"] != "PASS").any()
):
    fail(
        "Upstream candidate-resolution identity failed."
    )

actual_total = int(
    resolution["observations"].sum()
)

actual_d_total = int(
    resolution.loc[
        resolution["provisional_resolution"]
        == "D_SPLIT_CONFIRMED",
        "observations",
    ].sum()
)

actual_c_total = int(
    resolution.loc[
        resolution["provisional_resolution"]
        == "C_REMAINS_CANDIDATE",
        "observations",
    ].sum()
)

if actual_total != EXPECTED_TOTAL:
    fail(
        f"Expected total {EXPECTED_TOTAL}, got "
        f"{actual_total}"
    )

if actual_d_total != EXPECTED_D_TOTAL:
    fail(
        f"Expected D total {EXPECTED_D_TOTAL}, got "
        f"{actual_d_total}"
    )

if actual_c_total != EXPECTED_C_TOTAL:
    fail(
        f"Expected C total {EXPECTED_C_TOTAL}, got "
        f"{actual_c_total}"
    )


# ============================================================
# Gate 2 — rule structural validation
# ============================================================

rules_df = pd.DataFrame(RULES)

if rules_df["rule_id"].duplicated().any():
    dupes = rules_df.loc[
        rules_df["rule_id"].duplicated(False),
        "rule_id",
    ].tolist()

    fail(
        "Duplicate rule IDs: "
        + ", ".join(map(str, dupes))
    )

if rules_df["priority"].duplicated().any():
    dupes = rules_df.loc[
        rules_df["priority"].duplicated(False),
        "priority",
    ].tolist()

    fail(
        "Duplicate priorities: "
        + ", ".join(map(str, dupes))
    )

if rules_df["candidate_state"].isna().any():
    fail("Candidate state contains missing values.")

# No Production authorization at this gate.
if rules_df["production_authorized"].astype(bool).any():
    fail(
        "Production authorization detected in research spec."
    )


# ============================================================
# Gate 3 — candidate family coverage
# ============================================================

coverage_rows = []

for family in EXPECTED_FAMILIES:

    family_rules = rules_df[
        rules_df["family"] == family
    ].copy()

    expected_resolution = EXPECTED_FAMILIES[family]

    if expected_resolution == "D_SPLIT_CONFIRMED":
        expected_rule_count = 2
    else:
        expected_rule_count = 1

    actual_rule_count = len(family_rules)

    coverage_pass = (
        actual_rule_count == expected_rule_count
    )

    if family.startswith(
        "RATES_DOWN_USD_UP_VIX_"
    ):
        if actual_rule_count:
            wti_values = set(
                pd.to_numeric(
                    family_rules["wti_dir"],
                    errors="coerce",
                ).dropna().astype(int)
            )
        else:
            wti_values = set()

        if expected_resolution == "D_SPLIT_CONFIRMED":
            split_pass = (
                wti_values == {-1, 1}
            )
        else:
            split_pass = True
    else:
        split_pass = True

    coverage_rows.append(
        {
            "structural_family": family,
            "upstream_resolution": expected_resolution,
            "observations": EXPECTED_OBSERVATIONS[family],
            "expected_rule_count": expected_rule_count,
            "actual_rule_count": actual_rule_count,
            "coverage_identity": (
                "PASS"
                if coverage_pass
                else "FAIL"
            ),
            "wti_split_identity": (
                "PASS"
                if split_pass
                else "FAIL"
            ),
        }
    )

coverage = pd.DataFrame(coverage_rows)

if (
    (coverage["coverage_identity"] != "PASS").any()
    or
    (coverage["wti_split_identity"] != "PASS").any()
):
    fail(
        "Candidate taxonomy coverage/split gate failed."
    )


# ============================================================
# Gate 4 — precedence / exclusivity contract
# ============================================================

credit_rules = rules_df[
    rules_df["rule_id"]
    == "P_EXISTING_CREDIT_STRESS"
]

if len(credit_rules) != 1:
    fail(
        "Exactly one CREDIT_STRESS precedence rule required."
    )

credit_priority = int(
    credit_rules.iloc[0]["priority"]
)

candidate_priorities = pd.to_numeric(
    rules_df.loc[
        rules_df["rule_type"].str.startswith(
            "V4_CANDIDATE"
        ),
        "priority",
    ],
    errors="raise",
)

credit_precedence_pass = bool(
    (candidate_priorities > credit_priority).all()
)

if not credit_precedence_pass:
    fail(
        "CREDIT_STRESS does not precede all V4 candidate rules."
    )

fallback = rules_df[
    rules_df["rule_id"] == "FALLBACK"
]

if len(fallback) != 1:
    fail("Exactly one fallback rule required.")

fallback_priority = int(
    fallback.iloc[0]["priority"]
)

if fallback_priority <= int(
    rules_df[
        rules_df["rule_id"] != "FALLBACK"
    ]["priority"].max()
):
    fail(
        "Fallback must have lowest precedence."
    )


# ============================================================
# Freeze specification
# ============================================================

spec = {
    "spec_name": "MACRO_V4_CANDIDATE_TAXONOMY",
    "version": "v1",
    "status": "RESEARCH_FROZEN",
    "purpose": (
        "Freeze research-only candidate taxonomy before "
        "classifier implementation or portfolio evaluation."
    ),

    "upstream_identity": {
        "target_observations": EXPECTED_TOTAL,
        "d_family_observations": EXPECTED_D_TOTAL,
        "c_family_observations": EXPECTED_C_TOTAL,
        "families": EXPECTED_OBSERVATIONS,
    },

    "architecture": {
        "raw_layer": (
            "Existing Production interpret_macro_narrative"
        ),
        "existing_high_priority_states": "KEEP",
        "credit_stress_precedence": "KEEP",
        "existing_directional_states": "KEEP",
        "v4_candidate_layer": (
            "APPLY ONLY TO CURRENT UNKNOWN_TRANSITION"
        ),
        "d_family_split_variable": "WTI_DIR",
        "fallback": "UNKNOWN_TRANSITION",
    },

    "credit_stress_contract": {
        "condition_1": "HY_OAS_STATUS == FRACTURE",
        "condition_2": (
            "HY_OAS_STATUS == HOT "
            "AND VIX_DIR == 1 "
            "AND VIX_TODAY >= 22"
        ),
        "precedence": (
            "BEFORE ALL V4 CANDIDATE RULES"
        ),
        "invent_vix_level": False,
        "future_backfill": False,
    },

    "candidate_rules": RULES,

    "research_constraints": {
        "production_modified": False,
        "filter13_modified": False,
        "filter15_modified": False,
        "filter18_modified": False,
        "returns_used": False,
        "performance_used": False,
        "parameter_tuning": False,
        "future_state_classifier": False,
        "new_macro_data_authorized": False,
        "production_authorized": False,
    },

    "next_gate": (
        "MACRO V4 RESEARCH-ONLY CLASSIFIER "
        "COVERAGE + EXCLUSIVITY + PIT IDENTITY"
    ),
}

spec_payload = canonical_json(spec)
spec_hash = sha256_text(spec_payload)

# Hash is calculated on the immutable semantic payload.
frozen_artifact = {
    "sha256": spec_hash,
    "spec": spec,
}

SPEC_JSON.write_text(
    canonical_json(frozen_artifact) + "\n",
    encoding="utf-8",
)

rules_df.sort_values(
    "priority"
).to_csv(
    RULES_CSV,
    index=False,
)

coverage.to_csv(
    COVERAGE_CSV,
    index=False,
)


# ============================================================
# Audit report
# ============================================================

gate_rows = [
    (
        "UPSTREAM_TOTAL_IDENTITY",
        actual_total == EXPECTED_TOTAL,
    ),
    (
        "D_FAMILY_TOTAL_IDENTITY",
        actual_d_total == EXPECTED_D_TOTAL,
    ),
    (
        "C_FAMILY_TOTAL_IDENTITY",
        actual_c_total == EXPECTED_C_TOTAL,
    ),
    (
        "FIVE_FAMILY_IDENTITY",
        len(resolution) == 5,
    ),
    (
        "RULE_ID_UNIQUENESS",
        not rules_df["rule_id"].duplicated().any(),
    ),
    (
        "PRIORITY_UNIQUENESS",
        not rules_df["priority"].duplicated().any(),
    ),
    (
        "FAMILY_COVERAGE",
        (
            coverage["coverage_identity"]
            == "PASS"
        ).all(),
    ),
    (
        "D_WTI_SPLIT_IDENTITY",
        (
            coverage["wti_split_identity"]
            == "PASS"
        ).all(),
    ),
    (
        "CREDIT_STRESS_PRECEDENCE",
        credit_precedence_pass,
    ),
    (
        "UNKNOWN_FALLBACK_PRESENT",
        len(fallback) == 1,
    ),
    (
        "PRODUCTION_AUTHORIZATION_FALSE",
        not rules_df[
            "production_authorized"
        ].astype(bool).any(),
    ),
]

all_pass = all(
    bool(value)
    for _, value in gate_rows
)

audit_lines = []

audit_lines.append("=" * 140)
audit_lines.append(
    "MACRO V4 — CANDIDATE TAXONOMY SPEC FREEZE"
)
audit_lines.append("=" * 140)
audit_lines.append("")

audit_lines.append("===== UPSTREAM CONTRACT =====")
audit_lines.append(
    f"Target observations : {actual_total}"
)
audit_lines.append(
    f"D-family observations: {actual_d_total}"
)
audit_lines.append(
    f"C-family observations: {actual_c_total}"
)
audit_lines.append(
    f"Families            : {len(resolution)}"
)
audit_lines.append("")

audit_lines.append("===== FAMILY CONTRACT =====")

for row in identity_rows:
    audit_lines.append(
        f"{row['structural_family']:<34} "
        f"obs={row['actual_observations']:<4} "
        f"resolution={row['actual_resolution']}"
    )

audit_lines.append("")

audit_lines.append("===== FROZEN PRECEDENCE =====")
audit_lines.append(
    "1. Existing Production CREDIT_STRESS"
)
audit_lines.append(
    "2. Existing Production named directional narratives"
)
audit_lines.append(
    "3. V4 candidate taxonomy ONLY for unresolved UNKNOWN"
)
audit_lines.append(
    "4. D families split using contemporaneous WTI_DIR"
)
audit_lines.append(
    "5. Anything unresolved remains UNKNOWN_TRANSITION"
)
audit_lines.append("")

audit_lines.append("===== CREDIT_STRESS =====")
audit_lines.append(
    "HY FRACTURE -> CREDIT_STRESS"
)
audit_lines.append(
    "HY HOT + VIX_DIR=UP + VIX_TODAY>=22 "
    "-> CREDIT_STRESS"
)
audit_lines.append(
    "VIX level invention/backfill -> FORBIDDEN"
)
audit_lines.append("")

audit_lines.append("===== CANDIDATE RULES =====")

for _, row in rules_df.sort_values(
    "priority"
).iterrows():

    audit_lines.append(
        f"{int(row['priority']):>3} | "
        f"{row['rule_id']:<26} | "
        f"{row['family']:<32} | "
        f"{row['candidate_state']}"
    )

audit_lines.append("")

audit_lines.append("===== COVERAGE =====")

for _, row in coverage.iterrows():

    audit_lines.append(
        f"{row['structural_family']:<34} "
        f"rules={row['actual_rule_count']}/"
        f"{row['expected_rule_count']} "
        f"coverage={row['coverage_identity']} "
        f"WTI_split={row['wti_split_identity']}"
    )

audit_lines.append("")

audit_lines.append("===== FREEZE GATES =====")

for name, passed in gate_rows:
    audit_lines.append(
        f"{name:<42}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

audit_lines.append("")

audit_lines.append("===== ANTI-OVERFIT CONTRACT =====")
audit_lines.append("Returns used          : NO")
audit_lines.append("CAGR / Sharpe used    : NO")
audit_lines.append("Filter13 optimized    : NO")
audit_lines.append("Filter15 optimized    : NO")
audit_lines.append("Filter18 optimized    : NO")
audit_lines.append("Future state classifier: NO")
audit_lines.append("New macro data        : NO")
audit_lines.append("Production modified   : NO")
audit_lines.append("Parameter tuning      : NO")
audit_lines.append("")

audit_lines.append("===== SHA256 =====")
audit_lines.append(spec_hash)
audit_lines.append("")

audit_lines.append("===== ARTIFACTS =====")
audit_lines.append(f"JSON    : {SPEC_JSON}")
audit_lines.append(f"Rules   : {RULES_CSV}")
audit_lines.append(f"Coverage: {COVERAGE_CSV}")
audit_lines.append(f"Audit   : {AUDIT_TXT}")
audit_lines.append("")

audit_lines.append(
    f"STATUS : "
    f"{'RESEARCH FROZEN' if all_pass else 'FAIL'}"
)
audit_lines.append("")

audit_lines.append("PRODUCTION MODIFIED : NO")
audit_lines.append("FILTER13/15/18      : UNCHANGED")
audit_lines.append("RETURNS USED        : NO")
audit_lines.append("PERFORMANCE USED    : NO")
audit_lines.append("V4 CLASSIFIER RUN   : NO")
audit_lines.append("COMMIT              : NO")
audit_lines.append("")

audit_lines.append("NEXT IF PASS:")
audit_lines.append(
    "MACRO V4 RESEARCH-ONLY CLASSIFIER"
)
audit_lines.append(
    "-> apply only to Production UNKNOWN_TRANSITION"
)
audit_lines.append(
    "-> preserve CREDIT_STRESS precedence"
)
audit_lines.append(
    "-> verify PIT coverage / exclusivity / identity"
)
audit_lines.append(
    "-> NO 13/15/18 and NO returns yet"
)
audit_lines.append("")

audit_lines.append("=" * 140)

AUDIT_TXT.write_text(
    "\n".join(audit_lines) + "\n",
    encoding="utf-8",
)

print("\n".join(audit_lines))

if not all_pass:
    raise RuntimeError(
        "MACRO V4 candidate taxonomy freeze gate failed."
    )
