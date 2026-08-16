from __future__ import annotations

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

CLASSIFIER_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_v4_research_classifier_v1"
)

OUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_v4_portfolio_mapping_gate_v1"
)

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

INPUT = CLASSIFIER_DIR / "macro_v4_classifier_daily.csv"

DETAIL = OUT_DIR / "v4_portfolio_mapping_detail.csv"
SUMMARY = OUT_DIR / "v4_portfolio_mapping_evidence.csv"
AUDIT = OUT_DIR / "v4_portfolio_mapping_gate_audit.txt"


print("=" * 150)
print("MACRO V4 — PORTFOLIO MAPPING EVIDENCE GATE")
print("=" * 150)


# ============================================================
# Load
# ============================================================

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing classifier artifact: {INPUT}"
    )

df = pd.read_csv(INPUT)

required = {
    "signal_date",
    "raw_macro_narrative",
    "structural_family",
    "v4_state",
    "v4_rule_id",
    "v4_applied",
}

missing = sorted(required - set(df.columns))

if missing:
    raise RuntimeError(
        f"Missing required columns: {missing}"
    )


# ============================================================
# Candidate rows only
# ============================================================

applied = df[
    df["v4_applied"].astype(str).str.upper().isin(
        {"TRUE", "1"}
    )
].copy()

if len(applied) != 992:
    raise RuntimeError(
        f"Expected 992 V4 applied rows, got {len(applied)}"
    )


# ============================================================
# Helpers
# ============================================================

def pct(mask: pd.Series) -> float:
    if len(mask) == 0:
        return float("nan")
    return float(mask.mean() * 100.0)


def normalized_series(
    frame: pd.DataFrame,
    col: str,
) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(
            ["N/A"] * len(frame),
            index=frame.index,
            dtype="object",
        )

    return (
        frame[col]
        .fillna("N/A")
        .astype(str)
        .str.upper()
    )


# ============================================================
# Discover contemporaneous evidence columns
# ============================================================

possible_columns = [
    "HY_OAS_STATUS",
    "VIX_TODAY",
    "VIX_DIR",
    "WTI_DIR",
    "US10Y_DIR",
    "DXY_DIR",
    "POLICY_BACKBONE_STATE",
    "policy_state",
]

available = [
    c for c in possible_columns
    if c in applied.columns
]

print("\n===== AVAILABLE PIT EVIDENCE =====")
for col in available:
    print(col)

if not available:
    print("No optional evidence columns found.")


# ============================================================
# State evidence
# ============================================================

rows = []

for state, g in applied.groupby(
    "v4_state",
    dropna=False,
):

    hy = normalized_series(
        g,
        "HY_OAS_STATUS",
    )

    policy_col = (
        "POLICY_BACKBONE_STATE"
        if "POLICY_BACKBONE_STATE" in g.columns
        else "policy_state"
    )

    policy = normalized_series(
        g,
        policy_col,
    )

    vix_today = pd.to_numeric(
        g.get(
            "VIX_TODAY",
            pd.Series(
                [float("nan")] * len(g),
                index=g.index,
            ),
        ),
        errors="coerce",
    )

    vix_dir = pd.to_numeric(
        g.get(
            "VIX_DIR",
            pd.Series(
                [float("nan")] * len(g),
                index=g.index,
            ),
        ),
        errors="coerce",
    )

    wti_dir = pd.to_numeric(
        g.get(
            "WTI_DIR",
            pd.Series(
                [float("nan")] * len(g),
                index=g.index,
            ),
        ),
        errors="coerce",
    )

    n = len(g)

    rows.append({
        "v4_state": state,
        "observations": n,

        "hy_cool_share":
            pct(hy == "COOL"),

        "hy_watch_share":
            pct(hy == "WATCH"),

        "hy_hot_share":
            pct(hy == "HOT"),

        "hy_fracture_share":
            pct(hy == "FRACTURE"),

        "hy_watch_hot_fracture_share":
            pct(
                hy.isin(
                    ["WATCH", "HOT", "FRACTURE"]
                )
            ),

        "vix_up_share":
            pct(vix_dir == 1),

        "vix_down_share":
            pct(vix_dir == -1),

        "vix_ge_22_share":
            pct(vix_today >= 22),

        "vix_lt_18_share":
            pct(vix_today < 18),

        "wti_up_share":
            pct(wti_dir == 1),

        "wti_down_share":
            pct(wti_dir == -1),

        "policy_easing_share":
            pct(
                policy.str.contains(
                    "EASING",
                    na=False,
                )
            ),

        "policy_tightening_share":
            pct(
                policy.str.contains(
                    "TIGHTENING",
                    na=False,
                )
            ),

        "policy_mixed_share":
            pct(
                policy.str.contains(
                    "MIXED",
                    na=False,
                )
            ),
    })


summary = pd.DataFrame(rows)

if len(summary) != 7:
    raise RuntimeError(
        f"Expected 7 V4 states, got {len(summary)}"
    )


# ============================================================
# Add semantic constraints
#
# IMPORTANT:
# These are NOT selected mappings.
# They describe what Filter13 would do if a mapping
# contains one of these Production regime semantics.
# ============================================================

summary["risk_semantic_constraint"] = ""

for idx, row in summary.iterrows():

    state = str(row["v4_state"])

    if "VOL_PRESSURE" in state:
        constraint = (
            "VIX pressure present; unconditional "
            "RISK-ON mapping requires justification"
        )

    elif "BROAD_RISK_RELIEF" in state:
        constraint = (
            "Rates pressure conflicts with broad risk relief; "
            "directional mapping requires justification"
        )

    elif "VOL_RELIEF" in state:
        constraint = (
            "Vol relief supportive, but USD pressure remains; "
            "do not infer full RISK-ON automatically"
        )

    else:
        constraint = (
            "Mixed macro evidence; mapping must preserve "
            "contemporaneous risk information"
        )

    summary.loc[
        idx,
        "risk_semantic_constraint",
    ] = constraint


summary["mapping_status"] = "UNDECIDED"


# ============================================================
# Save
# ============================================================

detail_cols = [
    c for c in [
        "signal_date",
        "raw_macro_narrative",
        "structural_family",
        "v4_rule_id",
        "v4_state",
        "HY_OAS_STATUS",
        "VIX_TODAY",
        "VIX_DIR",
        "WTI_DIR",
        "US10Y_DIR",
        "DXY_DIR",
        "POLICY_BACKBONE_STATE",
        "policy_state",
    ]
    if c in applied.columns
]

applied[
    detail_cols
].to_csv(
    DETAIL,
    index=False,
)

summary.to_csv(
    SUMMARY,
    index=False,
)


# ============================================================
# Audit
# ============================================================

audit = []

audit.append(
    "=" * 150
)

audit.append(
    "MACRO V4 — PORTFOLIO MAPPING EVIDENCE GATE"
)

audit.append(
    "=" * 150
)

audit.append("")
audit.append("===== CONTRACT =====")
audit.append(
    f"V4 observations       : {len(applied)}"
)
audit.append(
    f"V4 states             : {len(summary)}"
)
audit.append(
    "Returns used          : NO"
)
audit.append(
    "Filter13 executed     : NO"
)
audit.append(
    "Filter15 executed     : NO"
)
audit.append(
    "Filter18 executed     : NO"
)
audit.append(
    "Production modified   : NO"
)
audit.append(
    "Portfolio mapping     : UNDECIDED"
)

audit.append("")
audit.append(
    "===== STATE EVIDENCE ====="
)

display = summary.copy()

pct_cols = [
    c for c in display.columns
    if c.endswith("_share")
]

for col in pct_cols:
    display[col] = display[col].map(
        lambda x: (
            "N/A"
            if pd.isna(x)
            else f"{x:.2f}%"
        )
    )

audit.append(
    display.to_string(
        index=False
    )
)

audit.append("")
audit.append(
    "===== EXISTING FILTER13 SEMANTICS ====="
)

audit.extend([
    "GOLDILOCKS              -> macro tilt +8",
    "REFLATION               -> macro tilt +6",
    "LIQUIDITY               -> macro tilt +5",
    "TIGHTENING_GROWTH_SCARE -> macro tilt -8",
    "STAGFLATION             -> macro tilt -12",
    "INFLATION SHOCK         -> macro tilt -12",
    "INFLATION               -> macro tilt -6",
    "HARD RISK-OFF           -> macro tilt -20",
    "",
    "SHOCK / SYSTEMIC / confirmed severe credit",
    "                         -> Phase Cap may reach 20",
    "HARD RISK-OFF           -> defensive Phase Cap logic",
    "WAITING / RANGE         -> Phase Cap 60",
])

audit.append("")
audit.append(
    "===== DECISION CONTRACT ====="
)

audit.extend([
    "Do NOT choose mappings from returns.",
    "",
    "For each V4 state, choose an existing portfolio-regime",
    "semantic only if contemporaneous economic evidence",
    "supports the downstream risk action.",
    "",
    "A V4 taxonomy label describes the macro configuration.",
    "A portfolio regime determines risk treatment.",
    "They are deliberately separate contracts.",
    "",
    "TRANSITION / MIXED remains a valid mapping.",
    "There is no requirement that every V4 state become",
    "RISK-ON or RISK-OFF.",
])

audit.append("")
audit.append(
    "===== ANTI-OVERFIT ====="
)

audit.extend([
    "NO returns",
    "NO CAGR",
    "NO Sharpe",
    "NO PnL",
    "NO Filter13 optimization",
    "NO Filter15 optimization",
    "NO Filter18 optimization",
    "NO future-state classifier",
])

audit.append("")
audit.append(
    "===== ARTIFACTS ====="
)

audit.append(
    f"Detail   : {DETAIL}"
)

audit.append(
    f"Evidence : {SUMMARY}"
)

audit.append(
    f"Audit    : {AUDIT}"
)

audit.append("")
audit.append(
    "STATUS : EVIDENCE READY / MAPPING UNDECIDED"
)

audit.append("")
audit.append(
    "NEXT:"
)

audit.append(
    "Freeze V4 state -> portfolio regime mapping."
)

audit.append(
    "Only after mapping freeze may the causal "
    "13 -> 15 -> 18 harness run."
)

audit.append("")
audit.append(
    "=" * 150
)

AUDIT.write_text(
    "\n".join(audit) + "\n",
    encoding="utf-8",
)

print("\n" + "\n".join(audit))

