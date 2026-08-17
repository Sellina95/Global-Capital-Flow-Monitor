from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import filters.strategist_filters as sf


# ============================================================
# PURPOSE
# ============================================================
#
# V4 Portfolio Mapping Freeze 직전 semantic sanity check.
#
# IMPORTANT:
# - Production 수정 없음
# - Filter13 실행 없음
# - Returns 사용 없음
# - Performance 사용 없음
# - Parameter tuning 없음
#
# 확인 대상:
#
# V4 State
#     -> proposed portfolio regime
#     -> existing Filter13 parser가 어떤 semantic으로 읽는가
#     -> macro tilt
#     -> obvious Phase Cap semantic
#
# ============================================================


PROPOSED_MAPPING = {
    "V4_NOMINAL_EASING_WITH_VOL_INFLATION_STRESS":
        "EVENT-WATCHING / INFLATION",

    "V4_RATES_PRESSURE_WITH_BROAD_RISK_RELIEF":
        "TRANSITION / MIXED",

    "V4_RATES_RELIEF_USD_VOL_PRESSURE_WTI_DOWN":
        "TRANSITION / MIXED",

    "V4_RATES_RELIEF_USD_VOL_PRESSURE_WTI_UP":
        "EVENT-WATCHING / INFLATION",

    "V4_RATES_VOL_PRESSURE_WITH_WEAK_USD":
        "TRANSITION / MIXED",

    "V4_RATES_VOL_RELIEF_USD_PRESSURE_WTI_DOWN":
        "TRANSITION / MIXED",

    "V4_RATES_VOL_RELIEF_USD_PRESSURE_WTI_UP":
        "TRANSITION / MIXED",
}


# ============================================================
# STATIC FILTER13 SEMANTIC RESOLUTION
#
# Mirrors the currently observed production semantics.
# It does NOT execute Filter13.
# ============================================================

def resolve_macro_tilt(regime: str) -> tuple[int, str]:

    phase_upper = regime.upper()

    if "GOLDILOCKS" in phase_upper:
        return 8, "GOLDILOCKS"

    elif "REFLATION" in phase_upper:
        return 6, "REFLATION"

    elif "LIQUIDITY" in phase_upper:
        return 5, "LIQUIDITY"

    elif "STAGFLATION" in phase_upper:
        return -12, "STAGFLATION"

    elif "INFLATION SHOCK" in phase_upper:
        return -12, "INFLATION SHOCK"

    elif "INFLATION" in phase_upper:
        return -6, "INFLATION"

    elif "HARD RISK-OFF" in phase_upper:
        return -20, "HARD RISK-OFF"

    return 0, "NO MACRO TILT"


def resolve_phase_cap_semantic(regime: str) -> str:

    phase_upper = regime.upper()

    if (
        phase_upper.startswith("WAITING")
        or "RANGE" in phase_upper
    ):
        return "CAP 60"

    if (
        phase_upper.startswith("SHOCK RISK-OFF")
        or "SYSTEMIC" in phase_upper
    ):
        return "POTENTIAL CAP 20"

    if phase_upper.startswith("HARD RISK-OFF"):
        return "DEFENSIVE CAP LOGIC"

    return "NO LABEL-DRIVEN CAP"


# ============================================================
# SOURCE PRESENCE CHECK
# ============================================================

source = inspect.getsource(
    sf.narrative_engine_filter
)

required_tokens = [
    '"GOLDILOCKS"',
    '"REFLATION"',
    '"LIQUIDITY"',
    '"STAGFLATION"',
    '"INFLATION SHOCK"',
    '"INFLATION"',
    '"HARD RISK-OFF"',
]

missing = [
    token
    for token in required_tokens
    if token not in source
]

if missing:
    raise RuntimeError(
        "Current Filter13 source no longer matches "
        "expected semantic contract. Missing: "
        + ", ".join(missing)
    )


# ============================================================
# REPORT
# ============================================================

print("=" * 150)
print("MACRO V4 — PORTFOLIO MAPPING SEMANTIC SANITY CHECK")
print("=" * 150)

print()
print("PURPOSE:")
print(
    "Inspect the downstream Filter13 meaning of the proposed "
    "V4 -> portfolio-regime mapping BEFORE mapping freeze."
)

print()
print("Production modified : NO")
print("Filter13 executed   : NO")
print("Filter15 executed   : NO")
print("Filter18 executed   : NO")
print("Returns used        : NO")
print("Performance used    : NO")
print("Mapping frozen      : NO")

print()
print("=" * 150)
print("PROPOSED MAPPING -> FILTER13 SEMANTICS")
print("=" * 150)

rows = []

for state, regime in PROPOSED_MAPPING.items():

    tilt, parser_match = resolve_macro_tilt(
        regime
    )

    cap_semantic = resolve_phase_cap_semantic(
        regime
    )

    rows.append(
        {
            "state": state,
            "regime": regime,
            "parser": parser_match,
            "tilt": tilt,
            "cap": cap_semantic,
        }
    )

    print()
    print(state)
    print(f"  -> Portfolio regime : {regime}")
    print(f"  -> Filter13 parser  : {parser_match}")
    print(f"  -> Macro tilt       : {tilt:+d}")
    print(f"  -> Phase cap        : {cap_semantic}")


# ============================================================
# DISTRIBUTION / CONCENTRATION CHECK
# ============================================================

print()
print("=" * 150)
print("MAPPING DISTRIBUTION")
print("=" * 150)

regime_counts = {}

for row in rows:
    regime_counts[row["regime"]] = (
        regime_counts.get(row["regime"], 0) + 1
    )

for regime, count in sorted(
    regime_counts.items()
):
    print(
        f"{regime:<35} : "
        f"{count}/{len(rows)} states"
    )


# ============================================================
# SANITY FLAGS
# ============================================================

flags = []

inflation_states = [
    row
    for row in rows
    if row["parser"] == "INFLATION"
]

mixed_states = [
    row
    for row in rows
    if row["regime"] == "TRANSITION / MIXED"
]

if len(inflation_states) != 2:
    flags.append(
        "Expected exactly 2 proposed inflation-risk mappings."
    )

if len(mixed_states) != 5:
    flags.append(
        "Expected exactly 5 proposed TRANSITION / MIXED mappings."
    )

unauthorized_extreme = [
    row
    for row in rows
    if (
        row["tilt"] <= -12
        or row["cap"] != "NO LABEL-DRIVEN CAP"
    )
]

if unauthorized_extreme:
    flags.append(
        "Proposed mapping unexpectedly invokes an extreme "
        "tilt or label-driven Phase Cap."
    )


print()
print("=" * 150)
print("SANITY GATES")
print("=" * 150)

print(
    "7 STATES COVERED                 :",
    "PASS"
    if len(rows) == 7
    else "FAIL",
)

print(
    "2 INFLATION-RISK STATES          :",
    "PASS"
    if len(inflation_states) == 2
    else "FAIL",
)

print(
    "5 TRANSITION/MIXED STATES        :",
    "PASS"
    if len(mixed_states) == 5
    else "FAIL",
)

print(
    "NO EXTREME TILT/CAP INTRODUCED   :",
    "PASS"
    if not unauthorized_extreme
    else "FAIL",
)

print()
print("=" * 150)
print("INTERPRETATION")
print("=" * 150)

print(
    """
The proposed mapping is intentionally conservative.

EVENT-WATCHING / INFLATION:
    Filter13 interprets the label through the existing
    INFLATION semantic and therefore applies macro tilt -6.

TRANSITION / MIXED:
    No directional Macro Tilt is introduced by the existing
    Filter13 macro parser.

None of the proposed V4 mappings should invoke:
    - GOLDILOCKS +8
    - REFLATION +6
    - LIQUIDITY +5
    - STAGFLATION -12
    - INFLATION SHOCK -12
    - HARD RISK-OFF -20
    - WAITING/RANGE cap 60
    - systemic/shock cap 20

This check does NOT determine whether the mapping is profitable.
It only verifies the downstream semantic consequence before freeze.
""".strip()
)

print()
print("=" * 150)

if flags:
    print("STATUS : REVIEW REQUIRED")

    for flag in flags:
        print(" -", flag)

    raise SystemExit(1)

print("STATUS : SEMANTIC SANITY PASS")
print()
print("NEXT   : FREEZE V4 PORTFOLIO MAPPING SPEC")
print("         THEN RUN V4 CAUSAL PROPAGATION")
print()
print("PRODUCTION MODIFIED : NO")
print("RETURNS USED        : NO")
print("PERFORMANCE USED    : NO")
print("PARAMETER TUNING    : NO")
print("COMMIT              : NO")

print("=" * 150)
