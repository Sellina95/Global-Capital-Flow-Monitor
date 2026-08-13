from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import filters.strategist_filters as sf

from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.institutional_backtest import (
    disable_live_side_effects,
    neutralize_all_side_effects,
)
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)


DATA_DIR = ROOT / "data" / "backtest"
RESULT_DIR = DATA_DIR / "results"

PANEL_PATH = DATA_DIR / "master_panel.csv"

DETAIL_PATH = (
    RESULT_DIR
    / "filter13_canonical_baseline_daily.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_canonical_baseline_summary.txt"
)


# ============================================================
# Helpers
# ============================================================

def to_float(value: Any) -> float:
    try:
        if value is None:
            return np.nan
        return float(value)
    except Exception:
        return np.nan


def base_budget_from_sentiment(sent_state: str) -> float:
    """
    Exact Production Narrative Engine base-budget contract.

    IMPORTANT:
    Production does not persist base_budget as a variable.
    Therefore it is reconstructed ONLY from the exact
    Production sent_state captured from the same execution.
    """
    state = str(sent_state or "N/A").upper()

    if state == "FEAR":
        return 35.0

    if state == "GREED":
        return 70.0

    if state == "NEUTRAL":
        return 55.0

    return 50.0


# ============================================================
# Exact Production Narrative local-variable capture
#
# No AST.
# No replayed budget formula.
# No legacy attribution CSV.
# No candidate injection.
#
# We execute the real narrative_engine_filter() and capture
# its local variables from the SAME Python frame at return.
# ============================================================

def run_narrative_with_trace(
    market_data: dict[str, Any],
) -> dict[str, Any]:

    captured: dict[str, Any] = {}

    target_code = sf.narrative_engine_filter.__code__

    def tracer(frame, event, arg):

        if (
            frame.f_code is target_code
            and event == "return"
        ):
            loc = dict(frame.f_locals)

            keys = [
                "sent_state",
                "fear",
                "credit_calm",
                "liq_dir_tag",
                "liq_level_bucket",
                "struct_v2",
                "systemic_confirmed",
                "systemic_watch",
                "v2_cap",
                "drift_tilt",
                "flow_gamma_tilt",
                "flow_continuity_tilt",
                "flow_regime_tilt",
                "macro_tilt",
                "pos_z",
                "phase",
                "phase_upper",
                "cap",
                "final_cap",
                "pre_cap_budget",
                "budget",
                "flow_score",
                "macro_narrative",
                "hy_status",
            ]

            for key in keys:
                captured[key] = loc.get(key)

        return tracer

    old_trace = sys.gettrace()

    try:
        sys.settrace(tracer)

        with contextlib.redirect_stdout(io.StringIO()):
            sf.narrative_engine_filter(
                market_data
            )

    finally:
        sys.settrace(old_trace)

    if not captured:
        raise RuntimeError(
            "Narrative Engine local-variable capture failed."
        )

    return captured


# ============================================================
# Main
# ============================================================

def main() -> None:

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    panel = (
        panel
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    rows: list[dict[str, Any]] = []

    previous_flow_memory = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    previous_exposure = 50.0

    print()
    print("=" * 80)
    print("FILTER13 CANONICAL PRODUCTION BASELINE")
    print("=" * 80)
    print()
    print(
        "Source = current master_panel + "
        "current Production pre-13 execution chain + "
        "current Production narrative_engine_filter"
    )
    print()
    print("Legacy attribution CSV : NOT USED")
    print("Legacy daily_positions : NOT USED")
    print("Candidate logic         : NOT USED")
    print("AST / copied budget     : NOT USED")
    print()

    mask = (
        panel["execution_date"].notna()
        & pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    )

    indices = panel.index[mask].tolist()

    for count, i in enumerate(indices, start=1):

        panel_row = panel.iloc[i]

        try:
            market_data = build_market_data(
                panel=panel,
                row_index=i,
                previous_exposure=previous_exposure,
            )

            disable_live_side_effects(
                previous_exposure
            )

            neutralize_all_side_effects(
                previous_exposure
            )

            next_flow_memory = (
                prepare_filter13_execution_state(
                    market_data=market_data,
                    panel=panel,
                    row_index=i,
                    previous_flow_memory=previous_flow_memory,
                )
            )

            trace = run_narrative_with_trace(
                market_data
            )

            # ------------------------------------------------
            # Canonical values written by Production itself
            # ------------------------------------------------

            production_pre_cap = to_float(
                market_data.get(
                    "PRE_CAP_BUDGET"
                )
            )

            production_phase_cap = to_float(
                market_data.get(
                    "PHASE_CAP"
                )
            )

            production_budget = to_float(
                market_data.get(
                    "RISK_BUDGET"
                )
            )

            final_state = (
                market_data.get(
                    "FINAL_STATE",
                    {},
                )
                or {}
            )

            final_state_budget = to_float(
                final_state.get(
                    "risk_budget"
                )
            )

            final_state_macro_tilt = to_float(
                final_state.get(
                    "macro_tilt"
                )
            )

            # ------------------------------------------------
            # SAME-FRAME parity
            # ------------------------------------------------

            trace_pre_cap = to_float(
                trace.get(
                    "pre_cap_budget"
                )
            )

            trace_budget = to_float(
                trace.get(
                    "budget"
                )
            )

            trace_macro_tilt = to_float(
                trace.get(
                    "macro_tilt"
                )
            )

            trace_final_cap = to_float(
                trace.get(
                    "final_cap"
                )
            )

            pre_cap_error = (
                production_pre_cap
                - trace_pre_cap
            )

            budget_error = (
                production_budget
                - trace_budget
            )

            final_state_budget_error = (
                production_budget
                - final_state_budget
            )

            macro_tilt_error = (
                final_state_macro_tilt
                - trace_macro_tilt
            )

            phase_cap_error = (
                production_phase_cap
                - trace_final_cap
            )

            sent_state = str(
                trace.get(
                    "sent_state",
                    "N/A",
                )
            )

            base_budget = (
                base_budget_from_sentiment(
                    sent_state
                )
            )

            row = {
                "signal_date":
                    market_data.get(
                        "SIGNAL_DATE",
                        panel_row.get(
                            "signal_date"
                        ),
                    ),

                "execution_date":
                    market_data.get(
                        "EXECUTION_DATE",
                        panel_row.get(
                            "execution_date"
                        ),
                    ),

                # --------------------------------------------
                # Exact Production input state
                # --------------------------------------------

                "sent_state":
                    sent_state,

                "base_budget":
                    base_budget,

                "fear":
                    trace.get("fear"),

                "credit_calm":
                    trace.get("credit_calm"),

                "liq_dir_tag":
                    trace.get("liq_dir_tag"),

                "liq_level_bucket":
                    trace.get(
                        "liq_level_bucket"
                    ),

                "struct_v2":
                    trace.get("struct_v2"),

                "systemic_confirmed":
                    trace.get(
                        "systemic_confirmed"
                    ),

                "systemic_watch":
                    trace.get(
                        "systemic_watch"
                    ),

                "drift_tilt":
                    trace.get(
                        "drift_tilt"
                    ),

                "flow_gamma_tilt":
                    trace.get(
                        "flow_gamma_tilt"
                    ),

                "flow_continuity_tilt":
                    trace.get(
                        "flow_continuity_tilt"
                    ),

                "flow_regime_tilt":
                    trace.get(
                        "flow_regime_tilt"
                    ),

                "macro_tilt":
                    trace_macro_tilt,

                "pos_z":
                    trace.get("pos_z"),

                "flow_score":
                    trace.get(
                        "flow_score"
                    ),

                "macro_narrative":
                    trace.get(
                        "macro_narrative"
                    ),

                "phase":
                    trace.get("phase"),

                "hy_status":
                    trace.get(
                        "hy_status"
                    ),

                # --------------------------------------------
                # Exact Production cap state
                # --------------------------------------------

                "phase_cap_raw":
                    trace.get("cap"),

                "v2_cap":
                    trace.get("v2_cap"),

                "final_cap":
                    trace_final_cap,

                "pre_cap_budget":
                    production_pre_cap,

                "risk_budget":
                    production_budget,

                # --------------------------------------------
                # Independent same-frame audit
                # --------------------------------------------

                "trace_pre_cap_budget":
                    trace_pre_cap,

                "trace_risk_budget":
                    trace_budget,

                "final_state_budget":
                    final_state_budget,

                "final_state_macro_tilt":
                    final_state_macro_tilt,

                "pre_cap_error":
                    pre_cap_error,

                "budget_error":
                    budget_error,

                "final_state_budget_error":
                    final_state_budget_error,

                "macro_tilt_error":
                    macro_tilt_error,

                "phase_cap_error":
                    phase_cap_error,

                "status":
                    "OK",

                "error":
                    "",
            }

            rows.append(row)

            previous_flow_memory = (
                next_flow_memory
            )

        except Exception as exc:

            rows.append({
                "signal_date":
                    panel_row.get(
                        "signal_date"
                    ),

                "execution_date":
                    panel_row.get(
                        "execution_date"
                    ),

                "status":
                    "ERROR",

                "error":
                    (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
            })

        if (
            count % 100 == 0
            or count == len(indices)
        ):
            print(
                f"\rProcessed "
                f"{count:,}/{len(indices):,}",
                end="",
                flush=True,
            )

    print()

    result = pd.DataFrame(rows)

    result[
        "signal_date"
    ] = pd.to_datetime(
        result["signal_date"],
        errors="coerce",
    )

    result = (
        result
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    ok = result[
        result["status"].eq("OK")
    ].copy()

    errors = result[
        result["status"].eq("ERROR")
    ].copy()

    if ok.empty:
        print()
        print("NO SUCCESSFUL ROWS — FIRST EXECUTION ERRORS")
        print(
            errors[
                ["signal_date", "error"]
            ]
            .head(20)
            .to_string(index=False)
        )
        raise RuntimeError(
            "Canonical audit produced zero successful rows."
        )

    # ========================================================
    # HARD PARITY GATES
    # ========================================================

    tolerance = 1e-9

    parity_columns = [
        "pre_cap_error",
        "budget_error",
        "final_state_budget_error",
        "macro_tilt_error",
        "phase_cap_error",
    ]

    fail_counts = {}

    max_errors = {}

    for col in parity_columns:

        values = pd.to_numeric(
            ok[col],
            errors="coerce",
        )

        fail_counts[col] = int(
            (
                values.abs()
                > tolerance
            ).sum()
        )

        max_errors[col] = (
            float(
                values.abs().max()
            )
            if len(values)
            else np.nan
        )

    total_parity_fail = sum(
        fail_counts.values()
    )

    # ========================================================
    # Extra structural checks
    # ========================================================

    missing_pre_cap = int(
        pd.to_numeric(
            ok["pre_cap_budget"],
            errors="coerce",
        ).isna().sum()
    )

    missing_budget = int(
        pd.to_numeric(
            ok["risk_budget"],
            errors="coerce",
        ).isna().sum()
    )

    invalid_budget = int(
        (
            (
                pd.to_numeric(
                    ok["risk_budget"],
                    errors="coerce",
                )
                < 0
            )
            |
            (
                pd.to_numeric(
                    ok["risk_budget"],
                    errors="coerce",
                )
                > 100
            )
        ).sum()
    )

    cap_violation = int(
        (
            pd.to_numeric(
                ok["risk_budget"],
                errors="coerce",
            )
            >
            pd.to_numeric(
                ok["final_cap"],
                errors="coerce",
            )
            + tolerance
        ).sum()
    )

    # ========================================================
    # Save
    # ========================================================

    result.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    lines = []

    lines.append(
        "FILTER13 CANONICAL PRODUCTION BASELINE"
    )
    lines.append("=" * 70)
    lines.append("")

    lines.append(
        f"Panel rows             : "
        f"{len(panel):,}"
    )

    lines.append(
        f"Successful rows        : "
        f"{len(ok):,}"
    )

    lines.append(
        f"Execution errors       : "
        f"{len(errors):,}"
    )

    lines.append("")

    lines.append(
        "SOURCE CONTRACT"
    )

    lines.append(
        "- current master_panel.csv"
    )

    lines.append(
        "- current prepare_filter13_execution_state()"
    )

    lines.append(
        "- current Production narrative_engine_filter()"
    )

    lines.append(
        "- same-frame local-variable capture"
    )

    lines.append(
        "- legacy attribution CSV NOT USED"
    )

    lines.append(
        "- legacy daily_positions.csv NOT USED"
    )

    lines.append(
        "- candidate logic NOT USED"
    )

    lines.append("")

    lines.append(
        "SAME-FRAME PARITY"
    )

    for col in parity_columns:

        lines.append(
            f"{col:30s}: "
            f"fail={fail_counts[col]:,}, "
            f"max_abs_error="
            f"{max_errors[col]:.12f}"
        )

    lines.append("")

    lines.append(
        "STRUCTURAL CHECKS"
    )

    lines.append(
        f"Missing PRE_CAP_BUDGET : "
        f"{missing_pre_cap:,}"
    )

    lines.append(
        f"Missing RISK_BUDGET    : "
        f"{missing_budget:,}"
    )

    lines.append(
        f"Invalid budget         : "
        f"{invalid_budget:,}"
    )

    lines.append(
        f"Final-cap violations   : "
        f"{cap_violation:,}"
    )

    lines.append("")

    avg_budget = pd.to_numeric(
        ok["risk_budget"],
        errors="coerce",
    ).mean()

    avg_pre_cap = pd.to_numeric(
        ok["pre_cap_budget"],
        errors="coerce",
    ).mean()

    lines.append(
        f"Average Pre-Cap Budget : "
        f"{avg_pre_cap:.6f}"
    )

    lines.append(
        f"Average Final Budget   : "
        f"{avg_budget:.6f}"
    )

    lines.append("")

    hard_fail = (
        len(errors) > 0
        or total_parity_fail > 0
        or missing_pre_cap > 0
        or missing_budget > 0
        or invalid_budget > 0
        or cap_violation > 0
    )

    if hard_fail:

        lines.append(
            "FINAL STATUS: FAIL"
        )

        lines.append(
            "STOP — canonical baseline is not "
            "internally identical to Production."
        )

    else:

        lines.append(
            "FINAL STATUS: PASS"
        )

        lines.append(
            "Canonical Filter13 baseline is now frozen."
        )

        lines.append(
            "This file may be used as the ONLY "
            "Filter13 candidate research baseline."
        )

    summary_text = "\n".join(
        lines
    )

    SUMMARY_PATH.write_text(
        summary_text,
        encoding="utf-8",
    )

    print()
    print(summary_text)

    print()
    print("Saved:")
    print(DETAIL_PATH)
    print(SUMMARY_PATH)

    if hard_fail:

        if not errors.empty:
            print()
            print("FIRST EXECUTION ERRORS")
            print(
                errors[
                    [
                        "signal_date",
                        "error",
                    ]
                ]
                .head(20)
                .to_string(
                    index=False
                )
            )

        parity_fail_mask = pd.Series(
            False,
            index=ok.index,
        )

        for col in parity_columns:
            parity_fail_mask |= (
                pd.to_numeric(
                    ok[col],
                    errors="coerce",
                )
                .abs()
                > tolerance
            )

        mismatch = ok[
            parity_fail_mask
        ]

        if not mismatch.empty:
            print()
            print("FIRST PARITY FAILURES")

            cols = [
                "signal_date",
                "pre_cap_budget",
                "trace_pre_cap_budget",
                "risk_budget",
                "trace_risk_budget",
                "final_cap",
                "macro_tilt",
                "pre_cap_error",
                "budget_error",
                "phase_cap_error",
            ]

            print(
                mismatch[
                    cols
                ]
                .head(20)
                .to_string(
                    index=False
                )
            )

        raise RuntimeError(
            "FILTER13 CANONICAL BASELINE FAILED. "
            "Do NOT run candidate research."
        )


if __name__ == "__main__":
    main()
