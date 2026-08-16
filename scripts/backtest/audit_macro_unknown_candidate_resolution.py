from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INPUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_unknown_family_classification_gate_v1"
)

DETAIL_PATH = INPUT_DIR / "family_classification_detail.csv"

OUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_unknown_candidate_resolution_v1"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

D_SPLIT_PATH = OUT_DIR / "d_family_split_evidence.csv"
C_COLLISION_PATH = OUT_DIR / "c_family_collision_evidence.csv"
RESOLUTION_PATH = OUT_DIR / "candidate_resolution_summary.csv"
AUDIT_PATH = OUT_DIR / "candidate_resolution_audit.txt"


# ============================================================
# FROZEN INPUT CONTRACT
# ============================================================

D_FAMILIES = [
    "RATES_DOWN_USD_UP_VIX_UP",
    "RATES_DOWN_USD_UP_VIX_DOWN",
]

C_FAMILIES = [
    "RATES_DOWN_USD_DOWN_VIX_UP",
    "RATES_UP_USD_DOWN_VIX_DOWN",
    "RATES_UP_USD_DOWN_VIX_UP",
]

EXPECTED_COUNTS = {
    "RATES_DOWN_USD_UP_VIX_UP": 335,
    "RATES_DOWN_USD_UP_VIX_DOWN": 277,
    "RATES_DOWN_USD_DOWN_VIX_UP": 179,
    "RATES_UP_USD_DOWN_VIX_DOWN": 129,
    "RATES_UP_USD_DOWN_VIX_UP": 72,
}

EXPECTED_TOTAL = 992


# ============================================================
# EXISTING PRODUCTION NARRATIVE DEFINITIONS
#
# These reproduce the contemporaneous directional semantics
# already inspected from interpret_macro_narrative().
#
# IMPORTANT:
# This audit does NOT modify Production.
# ============================================================

EXISTING_STATE_RULES = {
    "STAGFLATION_RISK": {
        "US10Y_DIR": 1,
        "DXY_DIR": 1,
        "WTI_DIR": 1,
        "HY_SET": {"WATCH", "HOT"},
    },

    "CREDIT_STRESS": {
        # CREDIT_STRESS is primarily credit-driven.
        # Exact directional collision is therefore evaluated
        # separately through HY severity rather than pretending
        # it has a fixed rates/USD/WTI signature.
        "CREDIT_DRIVEN": True,
    },

    "INFLATION_PRESSURE": {
        "US10Y_DIR": 1,
        "DXY_DIR": 1,
        "WTI_DIR": 1,
    },

    "TIGHTENING_GROWTH_SCARE": {
        "US10Y_DIR": 1,
        "DXY_DIR": 1,
        "WTI_DIR": -1,
    },

    "DISINFLATION": {
        "US10Y_DIR": -1,
        "DXY_DIR": -1,
        "WTI_DIR": -1,
    },

    "REFLATION": {
        "US10Y_DIR": 1,
        "DXY_DIR": -1,
        "WTI_DIR": 1,
    },

    "POLICY_EASING": {
        "US10Y_DIR": -1,
        "DXY_DIR": -1,
        "VIX_NOT_UP": True,
    },
}


# ============================================================
# HELPERS
# ============================================================

def pct(n: int | float, d: int | float) -> float:
    if not d:
        return 0.0
    return 100.0 * float(n) / float(d)


def normalize_hy(value) -> str:
    return str(value).upper().strip()


def rule_match(row: pd.Series, rule: dict) -> bool:
    """
    Exact contemporaneous evidence match against an existing
    Production narrative definition.

    CREDIT_STRESS is handled separately because its Production
    definition is credit/event driven rather than a single
    directional tuple.
    """

    if rule.get("CREDIT_DRIVEN"):
        return False

    for field in (
        "US10Y_DIR",
        "DXY_DIR",
        "WTI_DIR",
    ):
        if field in rule:
            try:
                actual = int(row[field])
            except Exception:
                return False

            if actual != int(rule[field]):
                return False

    if rule.get("VIX_NOT_UP"):
        try:
            if int(row["VIX_DIR"]) == 1:
                return False
        except Exception:
            return False

    if "HY_SET" in rule:
        if normalize_hy(
            row["HY_OAS_STATUS"]
        ) not in rule["HY_SET"]:
            return False

    return True


def exact_tuple(row: pd.Series) -> str:
    return (
        f"US10Y={int(row['US10Y_DIR'])}"
        f"|DXY={int(row['DXY_DIR'])}"
        f"|VIX={int(row['VIX_DIR'])}"
        f"|WTI={int(row['WTI_DIR'])}"
        f"|HY={normalize_hy(row['HY_OAS_STATUS'])}"
    )


# ============================================================
# LOAD + IDENTITY
# ============================================================

if not DETAIL_PATH.exists():
    raise FileNotFoundError(
        f"Missing upstream artifact: {DETAIL_PATH}"
    )

df = pd.read_csv(DETAIL_PATH)

required = {
    "signal_date",
    "structural_family",
    "US10Y_DIR",
    "DXY_DIR",
    "VIX_DIR",
    "WTI_DIR",
    "HY_OAS_STATUS",
}

missing = sorted(required - set(df.columns))

if missing:
    raise RuntimeError(
        f"Missing required columns: {missing}"
    )

target = df[
    df["structural_family"].isin(
        list(EXPECTED_COUNTS)
    )
].copy()

if len(target) != EXPECTED_TOTAL:
    raise RuntimeError(
        "Target identity failure: "
        f"expected={EXPECTED_TOTAL}, actual={len(target)}"
    )

actual_counts = (
    target["structural_family"]
    .value_counts()
    .to_dict()
)

for family, expected in EXPECTED_COUNTS.items():

    actual = int(
        actual_counts.get(family, 0)
    )

    if actual != expected:
        raise RuntimeError(
            f"{family}: expected={expected}, actual={actual}"
        )

target["HY_OAS_STATUS"] = (
    target["HY_OAS_STATUS"]
    .map(normalize_hy)
)

for col in (
    "US10Y_DIR",
    "DXY_DIR",
    "VIX_DIR",
    "WTI_DIR",
):
    target[col] = pd.to_numeric(
        target[col],
        errors="raise",
    ).astype(int)

target["exact_evidence_tuple"] = target.apply(
    exact_tuple,
    axis=1,
)


# ============================================================
# PART 1 — D FAMILY SPLIT RESOLUTION
#
# No threshold is used to optimize performance.
#
# We simply expose the contemporaneous subfamilies generated
# by WTI x HY status.
# ============================================================

d = target[
    target["structural_family"].isin(D_FAMILIES)
].copy()

d_split = (
    d.groupby(
        [
            "structural_family",
            "WTI_DIR",
            "HY_OAS_STATUS",
        ],
        dropna=False,
    )
    .size()
    .reset_index(name="observations")
)

family_totals = (
    d.groupby("structural_family")
    .size()
    .rename("family_total")
    .reset_index()
)

d_split = d_split.merge(
    family_totals,
    on="structural_family",
    how="left",
    validate="many_to_one",
)

d_split["share_within_family"] = (
    100.0
    * d_split["observations"]
    / d_split["family_total"]
)

d_split = d_split.sort_values(
    [
        "structural_family",
        "observations",
    ],
    ascending=[True, False],
)

d_split.to_csv(
    D_SPLIT_PATH,
    index=False,
)


# ============================================================
# PART 2 — C FAMILY EXISTING-STATE COLLISION
#
# Question:
# Are these actually missing pieces of an existing narrative,
# or genuinely outside the current Production taxonomy?
# ============================================================

c = target[
    target["structural_family"].isin(C_FAMILIES)
].copy()

collision_rows: list[dict] = []

for family in C_FAMILIES:

    g = c[
        c["structural_family"] == family
    ].copy()

    n = len(g)

    row = {
        "structural_family": family,
        "observations": n,
    }

    any_existing_match = pd.Series(
        False,
        index=g.index,
    )

    for state, rule in EXISTING_STATE_RULES.items():

        if state == "CREDIT_STRESS":
            continue

        matched = g.apply(
            lambda r: rule_match(r, rule),
            axis=1,
        )

        count = int(matched.sum())

        row[
            f"collision__{state}"
        ] = count

        row[
            f"collision_share__{state}"
        ] = pct(count, n)

        any_existing_match = (
            any_existing_match | matched
        )

    # Production CREDIT_STRESS condition:
    # FRACTURE OR
    # HOT + VIX up + VIX_TODAY >= 22.
    #
    # VIX_TODAY is not required by the family-detail artifact.
    # Therefore:
    #
    # FRACTURE = exact observable collision.
    # HOT + VIX_UP = potential collision requiring level check.
    #
    # We deliberately do NOT infer VIX_TODAY.
    hy = g["HY_OAS_STATUS"]

    fracture = (
        hy == "FRACTURE"
    )

    hot_vix_up = (
        (hy == "HOT")
        & (g["VIX_DIR"] == 1)
    )

    fracture_count = int(
        fracture.sum()
    )

    potential_hot_count = int(
        hot_vix_up.sum()
    )

    row[
        "credit_stress_exact_fracture"
    ] = fracture_count

    row[
        "credit_stress_exact_fracture_share"
    ] = pct(
        fracture_count,
        n,
    )

    row[
        "credit_stress_potential_hot_vix_up"
    ] = potential_hot_count

    row[
        "credit_stress_potential_hot_vix_up_share"
    ] = pct(
        potential_hot_count,
        n,
    )

    any_existing_match = (
        any_existing_match | fracture
    )

    row[
        "exact_existing_state_collision_days"
    ] = int(
        any_existing_match.sum()
    )

    row[
        "exact_existing_state_collision_share"
    ] = pct(
        int(any_existing_match.sum()),
        n,
    )

    row[
        "outside_existing_exact_taxonomy_days"
    ] = int(
        (~any_existing_match).sum()
    )

    row[
        "outside_existing_exact_taxonomy_share"
    ] = pct(
        int((~any_existing_match).sum()),
        n,
    )

    collision_rows.append(row)


collision = pd.DataFrame(
    collision_rows
)

collision.to_csv(
    C_COLLISION_PATH,
    index=False,
)


# ============================================================
# PART 3 — PROVISIONAL RESOLUTION
#
# IMPORTANT:
# This is architecture resolution, NOT parameter selection.
#
# D remains D when economically distinct WTI branches exist.
#
# C remains C only when the family is structurally outside
# existing exact Production taxonomy.
#
# We do NOT create names or Production rules here.
# ============================================================

resolution_rows: list[dict] = []

for family in D_FAMILIES:

    g = d[
        d["structural_family"] == family
    ]

    n = len(g)

    up = int(
        (g["WTI_DIR"] == 1).sum()
    )

    down = int(
        (g["WTI_DIR"] == -1).sum()
    )

    up_share = pct(up, n)
    down_share = pct(down, n)

    material_two_way_wti = (
        up > 0
        and down > 0
        and min(
            up_share,
            down_share,
        ) >= 25.0
    )

    resolution_rows.append({
        "structural_family": family,
        "prior_disposition": "D",
        "observations": n,
        "resolution_test":
            "CONTEMPORANEOUS_WTI_BRANCHING",
        "wti_up_share": up_share,
        "wti_down_share": down_share,
        "material_two_way_wti":
            material_two_way_wti,
        "exact_existing_state_collision_share":
            None,
        "provisional_resolution": (
            "D_SPLIT_CONFIRMED"
            if material_two_way_wti
            else "REVIEW_D"
        ),
    })


for _, r in collision.iterrows():

    outside_share = float(
        r[
            "outside_existing_exact_taxonomy_share"
        ]
    )

    # This does NOT authorize a new state.
    # It only determines whether the candidate is already
    # captured by an exact existing Production definition.
    resolution_rows.append({
        "structural_family":
            r["structural_family"],
        "prior_disposition": "C",
        "observations":
            int(r["observations"]),
        "resolution_test":
            "EXISTING_TAXONOMY_COLLISION",
        "wti_up_share": None,
        "wti_down_share": None,
        "material_two_way_wti": None,
        "exact_existing_state_collision_share":
            float(
                r[
                    "exact_existing_state_collision_share"
                ]
            ),
        "provisional_resolution": (
            "C_REMAINS_CANDIDATE"
            if outside_share >= 75.0
            else "REVIEW_EXISTING_EXTENSION"
        ),
    })


resolution = pd.DataFrame(
    resolution_rows
)

resolution.to_csv(
    RESOLUTION_PATH,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

report: list[str] = []

report.append("=" * 160)
report.append(
    "MACRO UNKNOWN — CANDIDATE RESOLUTION GATE"
)
report.append("=" * 160)
report.append("")

report.append("===== CONTRACT =====")
report.append(
    f"Target observations       : {len(target)}"
)
report.append(
    f"D-family observations     : {len(d)}"
)
report.append(
    f"C-family observations     : {len(c)}"
)
report.append(
    "Identity                  : PASS"
)
report.append(
    "Returns used              : NO"
)
report.append(
    "Filter13/15/18 executed   : NO"
)
report.append(
    "Future state classifier   : NO"
)
report.append(
    "Production modified       : NO"
)
report.append("")

report.append(
    "===== D FAMILY — WTI x HY SPLIT ====="
)

with pd.option_context(
    "display.max_columns",
    None,
    "display.width",
    240,
):
    report.append(
        d_split.to_string(
            index=False,
            formatters={
                "share_within_family":
                    lambda x: f"{x:.2f}%",
            },
        )
    )

report.append("")
report.append(
    "===== C FAMILY — EXISTING TAXONOMY COLLISION ====="
)

collision_display = [
    "structural_family",
    "observations",
    "collision_share__STAGFLATION_RISK",
    "collision_share__INFLATION_PRESSURE",
    "collision_share__TIGHTENING_GROWTH_SCARE",
    "collision_share__DISINFLATION",
    "collision_share__REFLATION",
    "collision_share__POLICY_EASING",
    "credit_stress_exact_fracture_share",
    "credit_stress_potential_hot_vix_up_share",
    "exact_existing_state_collision_share",
    "outside_existing_exact_taxonomy_share",
]

with pd.option_context(
    "display.max_columns",
    None,
    "display.width",
    260,
):
    report.append(
        collision[
            collision_display
        ].to_string(
            index=False,
            formatters={
                col: (
                    lambda x: f"{x:.2f}%"
                )
                for col in collision_display
                if col.endswith("_share")
                or "collision_share__" in col
            },
        )
    )

report.append("")
report.append(
    "===== PROVISIONAL RESOLUTION ====="
)

with pd.option_context(
    "display.max_columns",
    None,
    "display.width",
    240,
):
    report.append(
        resolution.to_string(
            index=False,
            formatters={
                "wti_up_share":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
                "wti_down_share":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
                "exact_existing_state_collision_share":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
            },
        )
    )

report.append("")
report.append(
    "===== INTERPRETATION CONTRACT ====="
)

report.append(
"""
D_SPLIT_CONFIRMED means:

The original family contains material contemporaneous WTI
branches and must not be forced into one macro narrative.

It does NOT mean both branches require new macro states.


C_REMAINS_CANDIDATE means:

The family is mostly outside exact existing Production
narrative definitions.

It does NOT authorize a new Production state.


REVIEW_EXISTING_EXTENSION means:

A material portion already collides with an existing exact
Production narrative definition and should be reviewed before
creating any new taxonomy.
""".strip()
)

report.append("")
report.append(
    "===== CREDIT_STRESS CAUTION ====="
)

report.append(
"""
CREDIT_STRESS cannot be fully collision-tested from directional
family labels alone.

Production also uses VIX_TODAY >= 22 when HY is HOT.

This audit therefore reports:

1. FRACTURE exact collision
2. HOT + VIX_UP potential collision

No VIX level is invented or backfilled.
""".strip()
)

report.append("")
report.append(
    "===== ANTI-OVERFIT ====="
)

report.append(
"""
NO returns.
NO CAGR.
NO Sharpe.
NO portfolio PnL.
NO Filter13/15/18 optimization.
NO future state as classifier.
NO parameter selection from performance.

The next gate, if this audit is structurally coherent, is:

MACRO V4 CANDIDATE TAXONOMY SPEC FREEZE

That specification must be frozen BEFORE any downstream
counterfactual performance evaluation.
""".strip()
)

report.append("")
report.append("===== ARTIFACTS =====")
report.append(
    f"D Split    : {D_SPLIT_PATH}"
)
report.append(
    f"C Collision: {C_COLLISION_PATH}"
)
report.append(
    f"Resolution : {RESOLUTION_PATH}"
)
report.append(
    f"Audit      : {AUDIT_PATH}"
)

report.append("")
report.append(
    "PRODUCTION MODIFIED : NO"
)
report.append(
    "FILTER13/15/18      : UNCHANGED / NOT EXECUTED"
)
report.append(
    "RETURNS USED        : NO"
)
report.append(
    "PERFORMANCE USED    : NO"
)
report.append(
    "V4 IMPLEMENTED      : NO"
)
report.append(
    "COMMIT              : NO"
)

report.append("")
report.append("=" * 160)
report.append(
    "CANDIDATE RESOLUTION COMPLETE — DO NOT COMMIT"
)
report.append("=" * 160)

text = "\n".join(report)

AUDIT_PATH.write_text(
    text,
    encoding="utf-8",
)

print(text)
