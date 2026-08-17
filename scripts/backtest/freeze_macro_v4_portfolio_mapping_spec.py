from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

OUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_v4_portfolio_mapping_spec_v1"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

SPEC_JSON = OUT_DIR / "macro_v4_portfolio_mapping_spec.json"
AUDIT_TXT = OUT_DIR / "macro_v4_portfolio_mapping_spec_audit.txt"


# ============================================================
# FROZEN MAPPING
#
# Source:
# - macro_v4_portfolio_mapping_gate_v1
# - macro_v4_mapping_semantic_sanity
#
# Selection contract:
# - NO returns
# - NO PnL
# - NO CAGR / Sharpe
# - NO Filter13/15/18 optimization
# ============================================================

MAPPING = {
    "V4_NOMINAL_EASING_WITH_VOL_INFLATION_STRESS": {
        "portfolio_regime": "EVENT-WATCHING / INFLATION",
        "filter13_macro_tilt": -6,
        "phase_cap_semantic": "NO LABEL-DRIVEN CAP",
        "reason": (
            "Nominal easing is offset by rising volatility and WTI, "
            "while contemporaneous credit is predominantly WATCH/HOT. "
            "Preserve inflation/risk stress rather than infer RISK-ON."
        ),
    },

    "V4_RATES_PRESSURE_WITH_BROAD_RISK_RELIEF": {
        "portfolio_regime": "TRANSITION / MIXED",
        "filter13_macro_tilt": 0,
        "phase_cap_semantic": "NO LABEL-DRIVEN CAP",
        "reason": (
            "Rates pressure conflicts with broader risk relief. "
            "Evidence does not justify a directional portfolio regime."
        ),
    },

    "V4_RATES_RELIEF_USD_VOL_PRESSURE_WTI_DOWN": {
        "portfolio_regime": "TRANSITION / MIXED",
        "filter13_macro_tilt": 0,
        "phase_cap_semantic": "NO LABEL-DRIVEN CAP",
        "reason": (
            "Rates and WTI relief conflict with USD and volatility pressure. "
            "Preserve mixed risk treatment."
        ),
    },

    "V4_RATES_RELIEF_USD_VOL_PRESSURE_WTI_UP": {
        "portfolio_regime": "EVENT-WATCHING / INFLATION",
        "filter13_macro_tilt": -6,
        "phase_cap_semantic": "NO LABEL-DRIVEN CAP",
        "reason": (
            "Rates relief is offset by USD pressure, rising volatility, "
            "and rising WTI. Inflation/risk stress remains economically relevant."
        ),
    },

    "V4_RATES_VOL_PRESSURE_WITH_WEAK_USD": {
        "portfolio_regime": "TRANSITION / MIXED",
        "filter13_macro_tilt": 0,
        "phase_cap_semantic": "NO LABEL-DRIVEN CAP",
        "reason": (
            "Weak USD is supportive but conflicts with rates and "
            "volatility pressure. Directional mapping is not justified."
        ),
    },

    "V4_RATES_VOL_RELIEF_USD_PRESSURE_WTI_DOWN": {
        "portfolio_regime": "TRANSITION / MIXED",
        "filter13_macro_tilt": 0,
        "phase_cap_semantic": "NO LABEL-DRIVEN CAP",
        "reason": (
            "Volatility and WTI relief are supportive but USD pressure "
            "remains. Do not infer full RISK-ON."
        ),
    },

    "V4_RATES_VOL_RELIEF_USD_PRESSURE_WTI_UP": {
        "portfolio_regime": "TRANSITION / MIXED",
        "filter13_macro_tilt": 0,
        "phase_cap_semantic": "NO LABEL-DRIVEN CAP",
        "reason": (
            "Volatility relief conflicts with USD and WTI pressure. "
            "Mixed portfolio treatment is retained."
        ),
    },
}


# ============================================================
# FREEZE CONTRACT
# ============================================================

spec = {
    "spec_name": "MACRO_V4_PORTFOLIO_MAPPING_SPEC_V1",
    "status": "FROZEN",
    "freeze_date": str(date.today()),

    "purpose": (
        "Freeze Macro V4 state -> portfolio regime semantics "
        "before causal propagation and before performance evaluation."
    ),

    "selection_contract": {
        "returns_used": False,
        "pnl_used": False,
        "cagr_used": False,
        "sharpe_used": False,
        "filter13_optimization_used": False,
        "filter15_optimization_used": False,
        "filter18_optimization_used": False,
        "future_information_used": False,
        "parameter_tuning_used": False,
    },

    "architecture_contract": {
        "macro_taxonomy_is_portfolio_action": False,
        "mixed_mapping_allowed": True,
        "production_modification_authorized": False,
        "research_branch_only": True,
        "next_gate": "MACRO_V4_CAUSAL_PROPAGATION",
    },

    "mapping": MAPPING,
}


# ============================================================
# HARD FREEZE GATES
# ============================================================

if len(MAPPING) != 7:
    raise RuntimeError(
        f"Expected exactly 7 V4 states, found {len(MAPPING)}"
    )

inflation_count = sum(
    x["portfolio_regime"] == "EVENT-WATCHING / INFLATION"
    for x in MAPPING.values()
)

mixed_count = sum(
    x["portfolio_regime"] == "TRANSITION / MIXED"
    for x in MAPPING.values()
)

if inflation_count != 2:
    raise RuntimeError(
        f"Expected 2 inflation-risk mappings, found {inflation_count}"
    )

if mixed_count != 5:
    raise RuntimeError(
        f"Expected 5 mixed mappings, found {mixed_count}"
    )

expected_tilts = {
    "EVENT-WATCHING / INFLATION": -6,
    "TRANSITION / MIXED": 0,
}

for state, config in MAPPING.items():

    expected = expected_tilts[
        config["portfolio_regime"]
    ]

    actual = config["filter13_macro_tilt"]

    if actual != expected:
        raise RuntimeError(
            f"{state}: expected tilt {expected}, found {actual}"
        )

    if config["phase_cap_semantic"] != "NO LABEL-DRIVEN CAP":
        raise RuntimeError(
            f"{state}: unexpected Phase Cap semantic"
        )


selection = spec["selection_contract"]

if any(selection.values()):
    raise RuntimeError(
        "Anti-overfit contract violated."
    )

if spec["architecture_contract"]["production_modification_authorized"]:
    raise RuntimeError(
        "Production modification must remain unauthorized."
    )


# ============================================================
# HASH
# Hash semantic payload BEFORE embedding hash itself.
# ============================================================

canonical_payload = json.dumps(
    spec,
    sort_keys=True,
    ensure_ascii=False,
    separators=(",", ":"),
)

sha256 = hashlib.sha256(
    canonical_payload.encode("utf-8")
).hexdigest()

artifact = {
    "sha256": sha256,
    "spec": spec,
}


SPEC_JSON.write_text(
    json.dumps(
        artifact,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# AUDIT
# ============================================================

lines = []

lines.append("=" * 140)
lines.append("MACRO V4 — PORTFOLIO MAPPING SPEC FREEZE")
lines.append("=" * 140)
lines.append("")

lines.append("===== FROZEN MAPPING =====")

for state, config in MAPPING.items():
    lines.append("")
    lines.append(state)
    lines.append(
        f"  -> {config['portfolio_regime']}"
    )
    lines.append(
        f"  -> Filter13 Macro Tilt: "
        f"{config['filter13_macro_tilt']:+d}"
    )
    lines.append(
        f"  -> Phase Cap: "
        f"{config['phase_cap_semantic']}"
    )

lines.append("")
lines.append("===== FREEZE GATES =====")
lines.append("7 V4 STATES                     : PASS")
lines.append("2 INFLATION-RISK MAPPINGS       : PASS")
lines.append("5 TRANSITION/MIXED MAPPINGS     : PASS")
lines.append("FILTER13 SEMANTIC IDENTITY      : PASS")
lines.append("NO LABEL-DRIVEN PHASE CAP       : PASS")
lines.append("ANTI-OVERFIT CONTRACT           : PASS")
lines.append("PRODUCTION AUTHORIZATION FALSE  : PASS")

lines.append("")
lines.append("===== ANTI-OVERFIT =====")
lines.append("Returns used       : NO")
lines.append("PnL used           : NO")
lines.append("CAGR used          : NO")
lines.append("Sharpe used        : NO")
lines.append("Future info used   : NO")
lines.append("Parameter tuning   : NO")

lines.append("")
lines.append("===== SHA256 =====")
lines.append(sha256)

lines.append("")
lines.append("===== ARTIFACTS =====")
lines.append(f"JSON  : {SPEC_JSON}")
lines.append(f"Audit : {AUDIT_TXT}")

lines.append("")
lines.append("STATUS : MACRO V4 PORTFOLIO MAPPING FROZEN")
lines.append("")
lines.append("NEXT   : MACRO V4 CAUSAL PROPAGATION")
lines.append(
    "         V4 -> Portfolio Regime -> Filter13 "
    "-> Filter15 -> Filter18"
)
lines.append("")
lines.append("PRODUCTION MODIFIED : NO")
lines.append("COMMIT              : NO")
lines.append("=" * 140)

AUDIT_TXT.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8",
)

print("\n".join(lines))
