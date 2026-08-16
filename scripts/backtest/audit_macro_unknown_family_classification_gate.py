from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
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
    / "macro_unmapped_economic_interpretation_v1"
)

DAILY_PATH = INPUT_DIR / "unmapped_economic_daily.csv"

OUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_unknown_family_classification_gate_v1"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

EVIDENCE_PATH = OUT_DIR / "family_classification_evidence.csv"
DETAIL_PATH = OUT_DIR / "family_classification_detail.csv"
AUDIT_PATH = OUT_DIR / "family_classification_gate_audit.txt"


# ============================================================
# CONTRACT
# ============================================================

TARGET_FAMILIES = [
    "RATES_DOWN_USD_UP_VIX_UP",
    "RATES_DOWN_USD_UP_VIX_DOWN",
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
# HELPERS
# ============================================================

def pct(n: int | float, d: int | float) -> float:
    if not d:
        return 0.0
    return 100.0 * float(n) / float(d)


def safe_mode(series: pd.Series) -> str:
    s = series.dropna().astype(str)

    if s.empty:
        return "N/A"

    counts = s.value_counts()

    if counts.empty:
        return "N/A"

    return str(counts.index[0])


def concentration(series: pd.Series) -> float:
    """
    Largest category share.

    This is descriptive only.
    It is NOT a classification threshold.
    """
    s = series.dropna()

    if s.empty:
        return 0.0

    vc = s.value_counts()

    return float(vc.iloc[0] / vc.sum())


def entropy_normalized(series: pd.Series) -> float:
    """
    0 = concentrated
    1 = maximally heterogeneous

    Descriptive evidence only.
    """
    s = series.dropna()

    if s.empty:
        return 0.0

    probs = s.value_counts(normalize=True).astype(float).values

    if len(probs) <= 1:
        return 0.0

    entropy = -np.sum(probs * np.log(probs))
    max_entropy = np.log(len(probs))

    if max_entropy == 0:
        return 0.0

    return float(entropy / max_entropy)


def first_existing(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:

    for col in candidates:
        if col in df.columns:
            return col

    return None


def episode_stats(
    family_df: pd.DataFrame,
) -> tuple[int, float, float, int]:

    x = family_df.copy()

    if "signal_date" not in x.columns:
        return 0, 0.0, 0.0, 0

    x["signal_date"] = pd.to_datetime(
        x["signal_date"],
        errors="coerce",
    )

    x = x.sort_values("signal_date")

    if x.empty:
        return 0, 0.0, 0.0, 0

    # We deliberately use adjacency in the canonical
    # unmapped dataset rather than calendar-day distance.
    #
    # The previous structural-family audit already established
    # that these regions are mostly short-lived.
    #
    # This metric therefore asks:
    # "How often does the same family remain consecutive
    # within the UNMAPPED evidence stream?"
    family_change = (
        x["structural_family"]
        != x["structural_family"].shift(1)
    )

    episode_id = family_change.cumsum()

    durations = (
        x.groupby(episode_id)
        .size()
        .astype(int)
    )

    if durations.empty:
        return 0, 0.0, 0.0, 0

    return (
        int(len(durations)),
        float(durations.mean()),
        float(durations.median()),
        int(durations.max()),
    )


# ============================================================
# LOAD
# ============================================================

if not DAILY_PATH.exists():
    raise FileNotFoundError(
        f"Missing upstream artifact: {DAILY_PATH}"
    )

df = pd.read_csv(DAILY_PATH)

required = {
    "signal_date",
    "structural_family",
    "HY_OAS_STATUS",
    "WTI_DIR",
}

missing = sorted(required - set(df.columns))

if missing:
    raise RuntimeError(
        f"Missing required columns: {missing}"
    )


# ============================================================
# TARGET REGION IDENTITY
# ============================================================

target = df[
    df["structural_family"].isin(TARGET_FAMILIES)
].copy()

actual_total = len(target)

if actual_total != EXPECTED_TOTAL:
    raise RuntimeError(
        "UNMAPPED family total identity failure: "
        f"expected={EXPECTED_TOTAL}, actual={actual_total}"
    )

actual_counts = (
    target["structural_family"]
    .value_counts()
    .to_dict()
)

for family, expected in EXPECTED_COUNTS.items():

    actual = int(actual_counts.get(family, 0))

    if actual != expected:
        raise RuntimeError(
            f"{family} identity failure: "
            f"expected={expected}, actual={actual}"
        )


# ============================================================
# OPTIONAL CONTEXT COLUMNS
# ============================================================

previous_state_col = first_existing(
    target,
    [
        "previous_raw_state",
        "prev_raw_state",
    ],
)

next_state_col = first_existing(
    target,
    [
        "next_raw_state",
    ],
)

pressure_col = first_existing(
    target,
    [
        "descriptive_pressure",
    ],
)

era_col = first_existing(
    target,
    [
        "era",
    ],
)


# ============================================================
# DETAIL TABLE
# ============================================================

detail_cols = [
    "signal_date",
    "structural_family",
]

for col in (
    "US10Y_DIR",
    "DXY_DIR",
    "VIX_DIR",
    "WTI_DIR",
    "HY_OAS_STATUS",
    pressure_col,
    era_col,
    previous_state_col,
    next_state_col,
):
    if col and col in target.columns and col not in detail_cols:
        detail_cols.append(col)

detail = target[detail_cols].copy()

detail["hy_risk_flag"] = (
    detail["HY_OAS_STATUS"]
    .astype(str)
    .str.upper()
    .isin(["WATCH", "HOT", "FRACTURE"])
)

detail["hy_hot_or_fracture_flag"] = (
    detail["HY_OAS_STATUS"]
    .astype(str)
    .str.upper()
    .isin(["HOT", "FRACTURE"])
)

detail.to_csv(
    DETAIL_PATH,
    index=False,
)


# ============================================================
# FAMILY EVIDENCE
# ============================================================

rows: list[dict] = []

for family in TARGET_FAMILIES:

    g = target[
        target["structural_family"] == family
    ].copy()

    n = len(g)

    hy = (
        g["HY_OAS_STATUS"]
        .astype(str)
        .str.upper()
    )

    hy_cool = int((hy == "COOL").sum())
    hy_watch = int((hy == "WATCH").sum())
    hy_hot = int((hy == "HOT").sum())
    hy_fracture = int((hy == "FRACTURE").sum())

    hy_risk = (
        hy_watch
        + hy_hot
        + hy_fracture
    )

    wti_numeric = pd.to_numeric(
        g["WTI_DIR"],
        errors="coerce",
    )

    wti_up = int((wti_numeric == 1).sum())
    wti_down = int((wti_numeric == -1).sum())
    wti_flat = int((wti_numeric == 0).sum())

    episodes, mean_dur, median_dur, max_dur = (
        episode_stats(g)
    )

    if era_col:
        eras_present = int(
            g[era_col]
            .dropna()
            .nunique()
        )
    else:
        eras_present = np.nan

    prev_mode = (
        safe_mode(g[previous_state_col])
        if previous_state_col
        else "N/A"
    )

    prev_concentration = (
        concentration(g[previous_state_col])
        if previous_state_col
        else np.nan
    )

    prev_entropy = (
        entropy_normalized(g[previous_state_col])
        if previous_state_col
        else np.nan
    )

    # IMPORTANT:
    # Next state is diagnostic only.
    # It must never become a Production classifier feature.
    next_mode = (
        safe_mode(g[next_state_col])
        if next_state_col
        else "N/A"
    )

    next_concentration = (
        concentration(g[next_state_col])
        if next_state_col
        else np.nan
    )

    next_entropy = (
        entropy_normalized(g[next_state_col])
        if next_state_col
        else np.nan
    )

    pressure = (
        safe_mode(g[pressure_col])
        if pressure_col
        else "N/A"
    )

    hy_conc = concentration(hy)
    hy_entropy = entropy_normalized(hy)

    wti_category = wti_numeric.map(
        {
            -1.0: "DOWN",
            0.0: "FLAT",
            1.0: "UP",
        }
    ).fillna("MISSING")

    wti_conc = concentration(wti_category)
    wti_entropy = entropy_normalized(wti_category)

    rows.append({
        "structural_family": family,
        "observations": n,

        "descriptive_pressure": pressure,

        "hy_cool": hy_cool,
        "hy_watch": hy_watch,
        "hy_hot": hy_hot,
        "hy_fracture": hy_fracture,
        "hy_watch_hot_fracture_share": pct(
            hy_risk,
            n,
        ),
        "hy_hot_fracture_share": pct(
            hy_hot + hy_fracture,
            n,
        ),
        "hy_dominant_state": safe_mode(hy),
        "hy_dominant_share": 100.0 * hy_conc,
        "hy_entropy": hy_entropy,

        "wti_up": wti_up,
        "wti_down": wti_down,
        "wti_flat": wti_flat,
        "wti_up_share": pct(wti_up, n),
        "wti_down_share": pct(wti_down, n),
        "wti_dominant_state": safe_mode(
            wti_category
        ),
        "wti_dominant_share": (
            100.0 * wti_conc
        ),
        "wti_entropy": wti_entropy,

        "eras_present": eras_present,

        "episodes": episodes,
        "mean_episode_duration": mean_dur,
        "median_episode_duration": median_dur,
        "max_episode_duration": max_dur,

        "previous_state_mode": prev_mode,
        "previous_state_concentration": (
            100.0 * prev_concentration
            if pd.notna(prev_concentration)
            else np.nan
        ),
        "previous_state_entropy": prev_entropy,

        "next_state_mode_DIAGNOSTIC_ONLY": next_mode,
        "next_state_concentration_DIAGNOSTIC_ONLY": (
            100.0 * next_concentration
            if pd.notna(next_concentration)
            else np.nan
        ),
        "next_state_entropy_DIAGNOSTIC_ONLY": (
            next_entropy
        ),

        # ------------------------------------------------
        # IMPORTANT
        #
        # We intentionally DO NOT automatically assign
        # A/B/C/D here.
        #
        # These are evidence flags only.
        # ------------------------------------------------

        "evidence_hy_risk_dominant": (
            pct(hy_risk, n) >= 75.0
        ),

        "evidence_wti_highly_concentrated": (
            100.0 * wti_conc >= 80.0
        ),

        "evidence_wti_materially_split": (
            wti_up > 0
            and wti_down > 0
            and min(
                pct(wti_up, n),
                pct(wti_down, n),
            ) >= 25.0
        ),

        "evidence_broad_history": (
            bool(eras_present >= 4)
            if pd.notna(eras_present)
            else False
        ),

        "classification": "UNDECIDED",
    })


evidence = pd.DataFrame(rows)

evidence.to_csv(
    EVIDENCE_PATH,
    index=False,
)


# ============================================================
# AUDIT REPORT
# ============================================================

display_cols = [
    "structural_family",
    "observations",
    "descriptive_pressure",
    "hy_watch_hot_fracture_share",
    "hy_hot_fracture_share",
    "wti_up_share",
    "wti_down_share",
    "wti_dominant_share",
    "eras_present",
    "previous_state_mode",
    "previous_state_concentration",
    "next_state_mode_DIAGNOSTIC_ONLY",
    "next_state_concentration_DIAGNOSTIC_ONLY",
    "evidence_hy_risk_dominant",
    "evidence_wti_highly_concentrated",
    "evidence_wti_materially_split",
    "classification",
]

report = []
report.append("=" * 150)
report.append(
    "MACRO UNKNOWN — 5 FAMILY CLASSIFICATION GATE"
)
report.append("=" * 150)
report.append("")

report.append("===== CONTRACT =====")
report.append(
    f"Target observations       : {len(target)}"
)
report.append(
    f"Expected observations     : {EXPECTED_TOTAL}"
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
    "Future state used in rule : NO"
)
report.append(
    "Automatic A/B/C/D choice  : NO"
)
report.append(
    "Production modified       : NO"
)
report.append("")

report.append(
    "===== CLASSIFICATION EVIDENCE ====="
)

with pd.option_context(
    "display.max_columns",
    None,
    "display.width",
    260,
    "display.max_colwidth",
    60,
):
    report.append(
        evidence[
            display_cols
        ].to_string(
            index=False,
            formatters={
                "hy_watch_hot_fracture_share":
                    lambda x: f"{x:.2f}%",
                "hy_hot_fracture_share":
                    lambda x: f"{x:.2f}%",
                "wti_up_share":
                    lambda x: f"{x:.2f}%",
                "wti_down_share":
                    lambda x: f"{x:.2f}%",
                "wti_dominant_share":
                    lambda x: f"{x:.2f}%",
                "previous_state_concentration":
                    lambda x: (
                        "N/A"
                        if pd.isna(x)
                        else f"{x:.2f}%"
                    ),
                "next_state_concentration_DIAGNOSTIC_ONLY":
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
    "===== DECISION CONTRACT ====="
)

report.append(
"""
A — EXISTING-STATE EXTENSION

Use only if the family's contemporaneous economic evidence
is a faithful extension of an existing Production narrative.

The fact that the NEXT state often becomes an existing state
is NOT sufficient evidence.


B — TRANSITION / MIXED REGION

Use if the family is economically real but contains opposing
forces that should not be collapsed into a directional state.


C — CANDIDATE NEW TAXONOMY

Use only if the evidence is economically coherent, recurring
across eras, and cannot be represented faithfully by an
existing Production narrative.


D — SPLIT REQUIRED

Use if HY / WTI / magnitude materially changes the economic
meaning inside the family.

A split must be justified using contemporaneous PIT evidence.
""".strip()
)

report.append("")
report.append(
    "===== ANTI-OVERFIT GATE ====="
)

report.append(
"""
The following are forbidden for classification:

- forward returns
- CAGR
- Sharpe
- portfolio PnL
- Filter13 budget improvement
- Filter15 exposure improvement
- Filter18 allocation improvement
- next-state information as a classifier
- choosing a taxonomy because it produces better performance

Frequency alone does not authorize a macro state.

This gate exists to establish economic taxonomy BEFORE
portfolio-performance evaluation.
""".strip()
)

report.append("")
report.append(
    "===== REQUIRED NEXT DECISION ====="
)

report.append(
"""
Review the five families one by one.

For each family assign exactly one provisional disposition:

A = EXISTING-STATE EXTENSION
B = TRANSITION / MIXED REGION
C = CANDIDATE NEW TAXONOMY
D = SPLIT REQUIRED

Do not modify Production at this gate.

After the provisional dispositions are economically justified,
freeze a candidate Macro taxonomy specification.

Only after that specification is frozen may a research-only
counterfactual classifier be implemented.
""".strip()
)

report.append("")
report.append("===== ARTIFACTS =====")
report.append(
    f"Evidence : {EVIDENCE_PATH}"
)
report.append(
    f"Detail   : {DETAIL_PATH}"
)
report.append(
    f"Audit    : {AUDIT_PATH}"
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
    "NEW MACRO STATE     : NO"
)
report.append(
    "CLASSIFICATION      : UNDECIDED"
)
report.append(
    "COMMIT              : NO"
)

report.append("")
report.append("=" * 150)
report.append(
    "5 FAMILY CLASSIFICATION GATE COMPLETE — DO NOT COMMIT"
)
report.append("=" * 150)

text = "\n".join(report)

AUDIT_PATH.write_text(
    text,
    encoding="utf-8",
)

print(text)
