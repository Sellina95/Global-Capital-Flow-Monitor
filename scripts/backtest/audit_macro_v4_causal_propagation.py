from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import filters.strategist_filters as sf

from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)
from scripts.backtest.run_backtest import run_engine


# ============================================================
# PATHS
# ============================================================

PANEL_PATH = ROOT / "data" / "backtest" / "master_panel.csv"

BASELINE_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "final_13_15_18_parity_closeout"
    / "final_13_15_18_parity_daily.csv"
)

CONTRACT_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_v4_research_classifier_v1"
    / "macro_v4_classifier_daily.csv"
)

OUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_v4_causal_propagation_v1"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

BASELINE_REPLAY_PATH = OUT_DIR / "canonical_baseline_replay.csv"
AUDIT_PATH = OUT_DIR / "canonical_baseline_identity_audit.txt"


MAPPING_SPEC_PATH = (
    ROOT / "data" / "backtest" / "results"
    / "macro_v4_portfolio_mapping_spec_v1"
    / "macro_v4_portfolio_mapping_spec.json"
)

EXPECTED_MAPPING_HASH = "6ef7cba1e196fbb067385a2acc20e193adfd357d98669d74c3a745907e47d225"

mapping_artifact = json.loads(MAPPING_SPEC_PATH.read_text())

if mapping_artifact.get("sha256") != EXPECTED_MAPPING_HASH:
    raise RuntimeError("FROZEN V4 MAPPING HASH MISMATCH")

V4_MAPPING = mapping_artifact["spec"]["mapping"]

# ============================================================
# HELPERS
# ============================================================

def scalar(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("today")
    return value


def as_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def close_enough(a: Any, b: Any, tol: float = 1e-9) -> bool:
    aa = as_float(a)
    bb = as_float(b)

    if aa is None and bb is None:
        return True

    if aa is None or bb is None:
        return False

    return abs(aa - bb) <= tol


# ============================================================
# LOAD
# ============================================================

print("=" * 126)
print("MACRO V3 — CANONICAL COUNTERFACTUAL HARNESS")
print("=" * 126)

for path in (PANEL_PATH, BASELINE_PATH, CONTRACT_PATH):
    if not path.exists():
        raise FileNotFoundError(path)

panel = pd.read_csv(
    PANEL_PATH,
    parse_dates=["date", "signal_date", "execution_date"],
)

baseline = pd.read_csv(
    BASELINE_PATH,
    parse_dates=["signal_date", "execution_date"],
)

contract = pd.read_csv(
    CONTRACT_PATH,
    parse_dates=["signal_date", "execution_date"],
)

required_contract = {
    "signal_date",
    "execution_date",
    "raw_macro_narrative",
    "v4_state",
    "v4_applied",
}

missing = required_contract - set(contract.columns)

if missing:
    raise RuntimeError(
        f"Missing V4 contract columns: {sorted(missing)}"
    )


# ============================================================
# V4 CONTRACT
# Only rows explicitly classified with v4_applied=True
# enter the V4 causal intervention universe.

# ============================================================
# CANONICAL DATE UNIVERSE
#
# IMPORTANT:
# Use ORIGINAL master_panel indices.
# Never reset the panel index.
# ============================================================

baseline_dates = set(
    pd.to_datetime(
        baseline["signal_date"],
        errors="coerce",
    ).dropna()
)

indices = panel.index[
    panel["signal_date"].isin(baseline_dates)
    & panel["execution_date"].notna()
    & pd.to_numeric(
        panel["SPY"],
        errors="coerce",
    ).notna()
].tolist()

if not indices:
    raise RuntimeError("No canonical execution dates found.")


# ============================================================
# BASELINE REPLAY
#
# Gate 1:
# Reproduce existing canonical capital chain BEFORE introducing
# any Macro V3 intervention.
#
# If this does not match the frozen baseline, STOP.
# ============================================================

print()
print("===== GATE 1 — CANONICAL BASELINE REPLAY =====")
print("Rows expected :", len(indices))

rows: list[dict[str, Any]] = []

previous_exposure = 50.0

flow_memory: dict[str, Any] = {
    "flow_state": "N/A",
    "flow_score": 0,
    "persistence_days": 0,
}

for count, idx in enumerate(indices, start=1):

    market_data = build_market_data(
        panel=panel,
        row_index=idx,
        previous_exposure=previous_exposure,
    )

    with contextlib.redirect_stdout(io.StringIO()):

        flow_memory = prepare_filter13_execution_state(
            market_data=market_data,
            panel=panel,
            row_index=idx,
            previous_flow_memory=flow_memory,
        )

        engine_result = run_engine(
            market_data=market_data,
            previous_exposure=previous_exposure,
        )

    allocation = engine_result["allocation"]

    weights = allocation.get("weights", {}) or {}

    risk_budget = market_data.get("RISK_BUDGET")
    exposure = market_data.get("RECOMMENDED_EXPOSURE")

    allocated_equity = allocation.get(
        "allocated_equity",
        round(
            sum(float(v) for v in weights.values()),
            1,
        ),
    )

    cash_weight = allocation.get(
        "cash_weight",
        round(
            100.0 - float(allocated_equity),
            1,
        ),
    )

    rows.append({
        "signal_date": market_data.get("SIGNAL_DATE"),
        "execution_date": market_data.get("EXECUTION_DATE"),

        "macro_narrative": market_data.get(
            "MACRO_NARRATIVE"
        ),

        "market_regime": market_data.get(
            "MARKET_REGIME"
        ),

        "risk_budget_13": risk_budget,
        "exposure_15": exposure,
        "allocated_equity_18": allocated_equity,
        "cash_weight": cash_weight,

        "sector_final_score": market_data.get(
            "SECTOR_FINAL_SCORE",
            {},
        ),

        "builder_allocation": engine_result.get(
            "builder_allocation",
            {},
        ),

        "rank_raw": market_data.get("FILTER18_RAW_RANK", ""),
        "rank_accepted": market_data.get("FILTER18_ACCEPTED_RANK", ""),
        "rank_pending": market_data.get("FILTER18_PENDING_RANK", ""),
        "rank_pending_count": market_data.get("FILTER18_PENDING_COUNT", 0),
        "rank_action": market_data.get("FILTER18_RANK_ACTION", ""),

        "rebalance_input_weights": engine_result.get("rebalance_input_weights"),
        "rebalance_prev_weights": engine_result.get("rebalance_prev_weights"),
        "rebalance_output_weights": engine_result.get("rebalance_output_weights"),
        "rebalance_actions": engine_result.get("rebalance_actions"),

        "flow_state": flow_memory.get(
            "flow_state"
        ),

        "flow_score": flow_memory.get(
            "flow_score"
        ),

        "weights_json": json.dumps(
            weights,
            ensure_ascii=False,
            sort_keys=True,
        ),
    })

    if exposure is not None:
        previous_exposure = float(exposure)

    if count % 250 == 0 or count == len(indices):
        print(
            f"\rProcessed {count}/{len(indices)}",
            end="",
            flush=True,
        )

print()

replay = pd.DataFrame(rows)

replay["signal_date"] = pd.to_datetime(
    replay["signal_date"],
    errors="coerce",
)

replay["execution_date"] = pd.to_datetime(
    replay["execution_date"],
    errors="coerce",
)

replay.to_csv(
    BASELINE_REPLAY_PATH,
    index=False,
)


# ============================================================
# BASELINE IDENTITY
# ============================================================

compare_columns = [
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
    "cash_weight",
]

base_cols = [
    "signal_date",
    "execution_date",
] + compare_columns

missing_base = [
    c for c in base_cols
    if c not in baseline.columns
]

if missing_base:
    raise RuntimeError(
        f"Frozen baseline missing columns: {missing_base}"
    )

merged = baseline[base_cols].merge(
    replay[
        [
            "signal_date",
            "execution_date",
        ] + compare_columns
    ],
    on=[
        "signal_date",
        "execution_date",
    ],
    how="outer",
    suffixes=("_frozen", "_replay"),
    indicator=True,
)

date_identity = bool(
    (merged["_merge"] == "both").all()
)

summary: list[dict[str, Any]] = []

for column in compare_columns:

    frozen_col = f"{column}_frozen"
    replay_col = f"{column}_replay"

    comparable = merged["_merge"].eq("both")

    exact = merged.loc[
        comparable,
        [frozen_col, replay_col],
    ].apply(
        lambda r: close_enough(
            r[frozen_col],
            r[replay_col],
        ),
        axis=1,
    )

    mismatch_count = int((~exact).sum())

    summary.append({
        "field": column,
        "comparable_rows": int(comparable.sum()),
        "mismatch_rows": mismatch_count,
        "identity": mismatch_count == 0,
    })


# ============================================================
# RAW MACRO IDENTITY
# ============================================================

raw_compare = contract[
    [
        "signal_date",
        "raw_macro_narrative",
    ]
].merge(
    replay[
        [
            "signal_date",
            "macro_narrative",
        ]
    ],
    on="signal_date",
    how="inner",
)

raw_compare["match"] = (
    raw_compare["raw_macro_narrative"].astype(str)
    ==
    raw_compare["macro_narrative"].astype(str)
)

raw_macro_identity = bool(
    raw_compare["match"].all()
)

raw_macro_mismatch = int(
    (~raw_compare["match"]).sum()
)


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 126)
print("CANONICAL BASELINE IDENTITY")
print("=" * 126)

print()
print("Date-set identity :", "PASS" if date_identity else "FAIL")

for item in summary:
    print(
        f'{item["field"]:24s}: '
        f'{"PASS" if item["identity"] else "FAIL"} '
        f'(mismatch={item["mismatch_rows"]})'
    )

print()
print(
    "RAW macro identity :",
    "PASS" if raw_macro_identity else "FAIL",
    f"(mismatch={raw_macro_mismatch})",
)

capital_identity = all(
    item["identity"]
    for item in summary
)

status = (
    date_identity
    and capital_identity
    and raw_macro_identity
)

print()
print("=" * 126)
print("GATE 1 STATUS :", "PASS" if status else "FAIL")
print("=" * 126)

audit_lines = [
    "MACRO V3 — CANONICAL BASELINE IDENTITY GATE",
    "",
    f"Rows replayed       : {len(replay)}",
    f"Date-set identity   : {'PASS' if date_identity else 'FAIL'}",
    f"RAW macro identity  : {'PASS' if raw_macro_identity else 'FAIL'}",
    f"RAW macro mismatch  : {raw_macro_mismatch}",
    "",
]

for item in summary:
    audit_lines.append(
        f'{item["field"]}: '
        f'{"PASS" if item["identity"] else "FAIL"} '
        f'(mismatch={item["mismatch_rows"]})'
    )

audit_lines += [
    "",
    f"GATE 1 STATUS       : {'PASS' if status else 'FAIL'}",
    "",
    "PRODUCTION MODIFIED : NO",
    "FILTER13 MODIFIED   : NO",
    "FILTER15 MODIFIED   : NO",
    "FILTER18 MODIFIED   : NO",
    "MACRO V3 APPLIED    : NO",
    "RETURNS USED        : NO",
    "PERFORMANCE USED    : NO",
    "PARAMETER TUNING    : NO",
]

AUDIT_PATH.write_text(
    "\n".join(audit_lines),
    encoding="utf-8",
)

print()
print("Artifacts:")
print("Replay :", BASELINE_REPLAY_PATH)
print("Audit  :", AUDIT_PATH)

print()
print("PRODUCTION MODIFIED : NO")
print("FILTER13/15/18      : UNCHANGED")
print("MACRO V3 APPLIED    : NO")
print("RETURNS USED        : NO")
print("PERFORMANCE USED    : NO")
print("COMMIT              : NO")

if not status:
    raise RuntimeError(
        "Canonical baseline identity FAILED. "
        "Do not execute Macro V3 counterfactual."
    )

print()
print("=" * 126)
print("BASELINE IDENTITY PASS")
print("NEXT: APPLY ONE MACRO V3 INTERVENTION")
print("=" * 126)


# =====================================================================
# MACRO V3 — RESEARCH-ONLY INTERVENTION
#
# IMPORTANT
# ---------
# The canonical baseline gate above MUST have passed before this block.
#
# Intervention:
#   RAW_MACRO_NARRATIVE
#       -> P2 strategic state supplied by frozen V3 contract
#       -> UNKNOWN HOLD
#       -> remap MARKET_REGIME using current CROSS_ASSET_TAPE
#
# No changes to:
#   Production source
#   Filter13
#   Filter15
#   Filter18
#   master_panel
#
# No returns / performance used.
# =====================================================================

if not status:
    raise RuntimeError(
        "Baseline identity did not pass. "
        "V3 intervention prohibited."
    )

print()
print("=" * 126)
print("GATE 2 — MACRO V3 CANONICAL INTERVENTION")
print("=" * 126)

# ---------------------------------------------------------------------
# Strategic-state lookup from the already frozen/reconstructed
# P2 + UNKNOWN-HOLD contract.
# ---------------------------------------------------------------------

v4_contract = contract[
    [
        "signal_date",
        "raw_macro_narrative",
        "v4_state",
        "v4_applied",
    ]
].copy()

v4_contract["signal_date"] = pd.to_datetime(
    v4_contract["signal_date"],
    errors="coerce",
)

v4_contract = v4_contract[
    v4_contract["v4_applied"] == True
].copy()

v4_lookup = (
    v4_contract
    .set_index("signal_date")
    ["v4_state"]
    .to_dict()
)

raw_lookup = (
    v4_contract
    .set_index("signal_date")
    ["raw_macro_narrative"]
    .to_dict()
)


# ---------------------------------------------------------------------
# Independent V3 recursive state machine
#
# Baseline recursion MUST NOT leak into counterfactual recursion.
# ---------------------------------------------------------------------

v3_previous_exposure = 50.0

v3_flow_memory: dict[str, Any] = {
    "flow_state": "N/A",
    "flow_score": 0,
    "persistence_days": 0,
}

v3_rows: list[dict[str, Any]] = []

warmup_skipped = 0
raw_identity_failures = 0


for count, idx in enumerate(indices, start=1):

    signal_date = pd.to_datetime(
        panel.iloc[idx]["signal_date"]
    )

    v4_state = v4_lookup.get(signal_date)

    # --------------------------------------------------------------
    # P2 initial warm-up:
    # no strategic state exists before two PIT observations.
    # Never future-backfill.
    # --------------------------------------------------------------

    if pd.isna(v4_state):
        warmup_skipped += 1
        continue

    market_data = build_market_data(
        panel=panel,
        row_index=idx,
        previous_exposure=v3_previous_exposure,
    )

    # --------------------------------------------------------------
    # First reproduce the canonical Production-equivalent Pre-13
    # chain exactly.
    #
    # This generates the RAW narrative and current PIT tape.
    # --------------------------------------------------------------

    with contextlib.redirect_stdout(io.StringIO()):

        next_flow_memory = prepare_filter13_execution_state(
            market_data=market_data,
            panel=panel,
            row_index=idx,
            previous_flow_memory=v3_flow_memory,
        )

    generated_raw = market_data.get(
        "MACRO_NARRATIVE"
    )

    expected_raw = raw_lookup.get(
        signal_date
    )

    if str(generated_raw) != str(expected_raw):
        raw_identity_failures += 1
        raise RuntimeError(
            "RAW macro identity failure on "
            f"{signal_date.date()}: "
            f"generated={generated_raw!r}, "
            f"expected={expected_raw!r}"
        )

    raw_market_regime = market_data.get(
        "MARKET_REGIME"
    )

    current_tape = market_data.get(
        "CROSS_ASSET_TAPE",
        {},
    ) or {}

    if not isinstance(current_tape, dict):
        raise RuntimeError(
            f"CROSS_ASSET_TAPE is not dict on {signal_date.date()}"
        )

    # --------------------------------------------------------------
    # THE ONLY MACRO V3 INTERVENTION
    # --------------------------------------------------------------

    market_data["RAW_MACRO_NARRATIVE"] = generated_raw
    market_data["RAW_MARKET_REGIME"] = raw_market_regime

    v4_state = str(v4_state)

    if v4_state not in V4_MAPPING:
        raise RuntimeError(
            f"V4 state missing from frozen mapping: {v4_state}"
        )

    frozen_mapping = V4_MAPPING[v4_state]

    strategic_market_regime = str(
        frozen_mapping["portfolio_regime"]
    )

    market_data["STRATEGIC_MACRO_STATE"] = v4_state
    market_data["MACRO_NARRATIVE"] = strategic_market_regime
    market_data["MARKET_REGIME"] = strategic_market_regime

    # --------------------------------------------------------------
    # IMPORTANT CAUSAL BOUNDARY
    #
    # prepare_filter13_execution_state() already executed downstream
    # generators once using RAW macro/regime.
    #
    # Therefore replay the downstream Pre-13 generators from the
    # intervention boundary so Filter13 receives V3-consistent state.
    #
    # Order must remain identical to canonical Production chain:
    #
    # policy -> drift -> gamma -> flow -> structural
    #
    # Historical flow loader continues to use V3's own t-1 memory.
    # --------------------------------------------------------------

    with contextlib.redirect_stdout(io.StringIO()):

        sf.policy_filter_with_expectations(
            market_data
        )

        sf.drift_monitor_filter(
            market_data
        )

        sf.pseudo_gamma_filter(
            market_data
        )

        original_loader = sf.load_previous_flow_state

        try:
            sf.load_previous_flow_state = (
                lambda *args, **kwargs: dict(
                    v3_flow_memory
                )
            )

            sf.institutional_flow_engine_filter(
                market_data
            )

        finally:
            sf.load_previous_flow_state = (
                original_loader
            )

        sf.structural_filter(
            market_data
        )

    # --------------------------------------------------------------
    # Reconstruct V3 next-day flow memory from the replayed flow
    # result, not from the earlier RAW execution.
    # --------------------------------------------------------------

    institutional_flow = (
        market_data.get(
            "INSTITUTIONAL_FLOW",
            {},
        )
        or {}
    )

    current_flow_state = institutional_flow.get(
        "state",
        "NO CLEAR FLOW",
    )

    current_flow_score = institutional_flow.get(
        "score",
        0,
    )

    transition_info = sf.classify_flow_transition(
        prev_flow_state=str(
            v3_flow_memory.get(
                "flow_state",
                "N/A",
            )
        ),
        prev_flow_score=int(
            v3_flow_memory.get(
                "flow_score",
                0,
            )
            or 0
        ),
        current_flow_state=str(
            current_flow_state
        ),
        current_flow_score=int(
            current_flow_score
            or 0
        ),
        prev_persistence_days=int(
            v3_flow_memory.get(
                "persistence_days",
                0,
            )
            or 0
        ),
    )

    v3_flow_memory = {
        "flow_state": transition_info.get(
            "flow_state",
            current_flow_state,
        ),
        "flow_score": transition_info.get(
            "flow_score",
            current_flow_score,
        ),
        "persistence_days": transition_info.get(
            "persistence_days",
            0,
        ),
    }

    # --------------------------------------------------------------
    # Existing unchanged 13 -> 15 -> 18 engine
    # --------------------------------------------------------------

    with contextlib.redirect_stdout(io.StringIO()):

        engine_result = run_engine(
            market_data=market_data,
            previous_exposure=v3_previous_exposure,
        )

    allocation = engine_result["allocation"]

    weights = allocation.get(
        "weights",
        {},
    ) or {}

    risk_budget = market_data.get(
        "RISK_BUDGET"
    )

    exposure = market_data.get(
        "RECOMMENDED_EXPOSURE"
    )

    allocated_equity = allocation.get(
        "allocated_equity",
        round(
            sum(
                float(v)
                for v in weights.values()
            ),
            1,
        ),
    )

    cash_weight = allocation.get(
        "cash_weight",
        round(
            100.0 - float(allocated_equity),
            1,
        ),
    )

    v3_rows.append({
        "signal_date": market_data.get(
            "SIGNAL_DATE"
        ),
        "execution_date": market_data.get(
            "EXECUTION_DATE"
        ),

        "raw_macro_narrative": generated_raw,
        "v4_state": v4_state,

        "raw_market_regime": raw_market_regime,
        "strategic_market_regime": strategic_market_regime,

        "risk_budget_13": risk_budget,
        "exposure_15": exposure,
        "allocated_equity_18": allocated_equity,
        "cash_weight": cash_weight,

        "macro_profile": market_data.get(
            "MACRO_REGIME_PROFILE",
            "N/A",
        ),

        "sector_final_score": market_data.get(
            "SECTOR_FINAL_SCORE",
            {},
        ),

        "builder_allocation": engine_result.get(
            "builder_allocation",
            {},
        ),

        "rank_raw": market_data.get("FILTER18_RAW_RANK", ""),
        "rank_accepted": market_data.get("FILTER18_ACCEPTED_RANK", ""),
        "rank_pending": market_data.get("FILTER18_PENDING_RANK", ""),
        "rank_pending_count": market_data.get("FILTER18_PENDING_COUNT", 0),
        "rank_action": market_data.get("FILTER18_RANK_ACTION", ""),

        "rebalance_input_weights": engine_result.get("rebalance_input_weights"),
        "rebalance_prev_weights": engine_result.get("rebalance_prev_weights"),
        "rebalance_output_weights": engine_result.get("rebalance_output_weights"),
        "rebalance_actions": engine_result.get("rebalance_actions"),

        "flow_state": v3_flow_memory.get(
            "flow_state"
        ),

        "flow_score": v3_flow_memory.get(
            "flow_score"
        ),

        "weights_json": json.dumps(
            weights,
            ensure_ascii=False,
            sort_keys=True,
        ),
    })

    if exposure is not None:
        v3_previous_exposure = float(
            exposure
        )

    if count % 250 == 0 or count == len(indices):
        print(
            f"\rV3 processed {count}/{len(indices)}",
            end="",
            flush=True,
        )

print()


# =====================================================================
# SAVE V3 DAILY
# =====================================================================

v3 = pd.DataFrame(v3_rows)

v3["signal_date"] = pd.to_datetime(
    v3["signal_date"],
    errors="coerce",
)

v3["execution_date"] = pd.to_datetime(
    v3["execution_date"],
    errors="coerce",
)

V3_DAILY_PATH = (
    OUT_DIR
    / "macro_v3_counterfactual_daily.csv"
)

V3_SUMMARY_PATH = (
    OUT_DIR
    / "macro_v3_counterfactual_summary.csv"
)

V3_AUDIT_PATH = (
    OUT_DIR
    / "macro_v3_counterfactual_audit.txt"
)

v3.to_csv(
    V3_DAILY_PATH,
    index=False,
)


# =====================================================================
# BASELINE vs V3
# =====================================================================

comparison = replay.merge(
    v3,
    on=[
        "signal_date",
        "execution_date",
    ],
    how="inner",
    suffixes=("_baseline", "_v3"),
)

if comparison.empty:
    raise RuntimeError(
        "Baseline/V3 comparison is empty."
    )


def changed_numeric(
    left: pd.Series,
    right: pd.Series,
    tol: float = 1e-9,
) -> pd.Series:

    a = pd.to_numeric(
        left,
        errors="coerce",
    )

    b = pd.to_numeric(
        right,
        errors="coerce",
    )

    both_na = (
        a.isna()
        & b.isna()
    )

    return (
        (~both_na)
        & (
            a.isna()
            | b.isna()
            | ((a - b).abs() > tol)
        )
    )


comparison["macro_changed"] = (
    comparison[
        "macro_narrative"
    ].astype(str)
    !=
    comparison[
        "v4_state"
    ].astype(str)
)

comparison["regime_changed"] = (
    comparison[
        "market_regime"
    ].astype(str)
    !=
    comparison[
        "strategic_market_regime"
    ].astype(str)
)

for field in (
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
    "cash_weight",
):

    comparison[
        f"{field}_changed"
    ] = changed_numeric(
        comparison[
            f"{field}_baseline"
        ],
        comparison[
            f"{field}_v3"
        ],
    )

    comparison[
        f"{field}_delta"
    ] = (
        pd.to_numeric(
            comparison[
                f"{field}_v3"
            ],
            errors="coerce",
        )
        -
        pd.to_numeric(
            comparison[
                f"{field}_baseline"
            ],
            errors="coerce",
        )
    )


# =====================================================================
# TRANSITION COUNTS
# =====================================================================

baseline_macro = comparison[
    "macro_narrative"
].astype(str)

v3_macro = comparison[
    "v4_state"
].astype(str)

baseline_transitions = int(
    baseline_macro.ne(
        baseline_macro.shift(1)
    ).iloc[1:].sum()
)

v3_transitions = int(
    v3_macro.ne(
        v3_macro.shift(1)
    ).iloc[1:].sum()
)


# =====================================================================
# STRUCTURAL SUMMARY
# =====================================================================

summary_rows = [
    {
        "stage": "MACRO_STATE",
        "observations": len(comparison),
        "changed_days": int(
            comparison["macro_changed"].sum()
        ),
        "changed_rate": float(
            comparison["macro_changed"].mean()
        ),
        "mean_delta": None,
    },
    {
        "stage": "MARKET_REGIME",
        "observations": len(comparison),
        "changed_days": int(
            comparison["regime_changed"].sum()
        ),
        "changed_rate": float(
            comparison["regime_changed"].mean()
        ),
        "mean_delta": None,
    },
]

for field, label in (
    (
        "risk_budget_13",
        "FILTER13_RISK_BUDGET",
    ),
    (
        "exposure_15",
        "FILTER15_EXPOSURE",
    ),
    (
        "allocated_equity_18",
        "FILTER18_ALLOCATED_EQUITY",
    ),
    (
        "cash_weight",
        "CASH_WEIGHT",
    ),
):

    summary_rows.append({
        "stage": label,
        "observations": len(comparison),
        "changed_days": int(
            comparison[
                f"{field}_changed"
            ].sum()
        ),
        "changed_rate": float(
            comparison[
                f"{field}_changed"
            ].mean()
        ),
        "mean_delta": float(
            comparison[
                f"{field}_delta"
            ].mean()
        ),
    })

summary_df = pd.DataFrame(
    summary_rows
)

summary_df.to_csv(
    V3_SUMMARY_PATH,
    index=False,
)


# =====================================================================
# OUTPUT
# =====================================================================

print()
print("=" * 126)
print("MACRO V3 — CAUSAL PROPAGATION RESULT")
print("=" * 126)

print()
print("===== EXECUTION =====")
print(
    "V3 observations          :",
    len(v3),
)
print(
    "P2 warm-up skipped       :",
    warmup_skipped,
)
print(
    "RAW identity failures    :",
    raw_identity_failures,
)

print()
print("===== MACRO STRUCTURE =====")
print(
    "Baseline transitions     :",
    baseline_transitions,
)
print(
    "V3 strategic transitions:",
    v3_transitions,
)

if baseline_transitions:
    reduction = (
        1.0
        - (
            v3_transitions
            / baseline_transitions
        )
    ) * 100.0
else:
    reduction = 0.0

print(
    "Transition reduction     :",
    f"{reduction:.2f}%",
)

print()
print("===== CAPITAL CHAIN =====")

for _, row in summary_df.iterrows():

    rate = (
        float(row["changed_rate"])
        * 100.0
    )

    delta = row["mean_delta"]

    if pd.isna(delta):
        delta_text = "N/A"
    else:
        delta_text = f"{float(delta):+.4f}"

    print(
        f'{row["stage"]:28s} '
        f'changed={int(row["changed_days"]):4d} '
        f'({rate:6.2f}%) '
        f'mean_delta={delta_text}'
    )


audit = f"""
MACRO V3 — CANONICAL COUNTERFACTUAL

BASELINE IDENTITY GATE
----------------------
Status                  : PASS

V3 EXECUTION
------------
Observations             : {len(v3)}
P2 warm-up skipped       : {warmup_skipped}
RAW identity failures    : {raw_identity_failures}

MACRO STRUCTURE
---------------
Baseline transitions     : {baseline_transitions}
V3 transitions           : {v3_transitions}
Transition reduction     : {reduction:.2f}%

SAFETY
------
Production modified      : NO
Filter13 modified        : NO
Filter15 modified        : NO
Filter18 modified        : NO
Returns used             : NO
Performance used         : NO
Parameter tuning         : NO

INTERVENTION
------------
RAW_MACRO_NARRATIVE
-> P2 + UNKNOWN HOLD
-> STRATEGIC_MACRO_STATE
-> map_to_portfolio_regime(existing policy, strategic state, current PIT tape)
-> existing downstream generators
-> unchanged 13 -> 15 -> 18
""".strip()

V3_AUDIT_PATH.write_text(
    audit,
    encoding="utf-8",
)

print()
print("===== ARTIFACTS =====")
print("Daily   :", V3_DAILY_PATH)
print("Summary :", V3_SUMMARY_PATH)
print("Audit   :", V3_AUDIT_PATH)

print()
print("PRODUCTION MODIFIED : NO")
print("FILTER13/15/18      : UNCHANGED")
print("RETURNS USED        : NO")
print("PERFORMANCE USED    : NO")
print("PARAMETER TUNING    : NO")
print("COMMIT              : NO")

print()
print("=" * 126)
print("MACRO V3 COUNTERFACTUAL COMPLETE")
print("=" * 126)
