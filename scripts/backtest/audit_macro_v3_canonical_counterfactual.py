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
    / "macro_v3_execution_contract_v1"
    / "macro_v3_execution_contract_daily.csv"
)

OUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_v3_canonical_counterfactual_v1"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

BASELINE_REPLAY_PATH = OUT_DIR / "canonical_baseline_replay.csv"
AUDIT_PATH = OUT_DIR / "canonical_baseline_identity_audit.txt"


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
    "strategic_macro_state",
}

missing = required_contract - set(contract.columns)

if missing:
    raise RuntimeError(
        f"Missing V3 contract columns: {sorted(missing)}"
    )


# ============================================================
# V3 WARM-UP CONTRACT
# ============================================================

missing_state = contract["strategic_macro_state"].isna()

if missing_state.any():

    missing_positions = [
        contract.index.get_loc(idx)
        for idx in contract.index[missing_state]
    ]

    expected_prefix = list(range(len(missing_positions)))

    if missing_positions != expected_prefix:
        raise RuntimeError(
            "Strategic macro state contains non-initial missing rows."
        )

    print()
    print("===== V3 P2 WARM-UP =====")
    print("Unresolved rows :", int(missing_state.sum()))
    print(
        "Dates           :",
        ", ".join(
            contract.loc[
                missing_state,
                "signal_date",
            ].dt.strftime("%Y-%m-%d")
        ),
    )
    print("Future backfill : NO")
    print("Treatment       : EXCLUDE FROM V3 EVALUATION")


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
