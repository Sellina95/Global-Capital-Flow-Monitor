from __future__ import annotations

import contextlib
import inspect
import io
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# Paths / imports
# ============================================================

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

CANONICAL_PATH = (
    RESULT_DIR
    / "filter13_canonical_baseline_daily.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter13_canonical_full_attribution_daily.csv"
)

LAYER_SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_canonical_full_attribution_layer_summary.csv"
)

ECONOMIC_SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_canonical_full_attribution_economic_summary.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_canonical_full_attribution_summary.txt"
)


TOL = 1e-9
EXPECTED_ROWS = 4645


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


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value)


def max_abs(series: pd.Series) -> float:
    x = pd.to_numeric(
        series,
        errors="coerce",
    ).abs()

    if x.dropna().empty:
        return 0.0

    return float(x.max())


# ============================================================
# Production source-map
#
# We do NOT hard-code source line numbers.
# Semantic anchors are resolved from CURRENT Production source.
# ============================================================

def build_production_source_contract():
    source_lines, start_line = inspect.getsourcelines(
        sf.narrative_engine_filter
    )

    source_by_lineno = {
        start_line + offset:
            line.rstrip("\n")
        for offset, line
        in enumerate(source_lines)
    }

    stripped = {
        lineno:
            text.strip()
        for lineno, text
        in source_by_lineno.items()
    }

    def find_line(
        token: str,
        *,
        after: int | None = None,
    ) -> int:

        candidates = []

        for lineno, text in stripped.items():

            if after is not None and lineno <= after:
                continue

            if token in text:
                candidates.append(lineno)

        if not candidates:
            raise RuntimeError(
                "Production source anchor not found: "
                f"{token!r}"
            )

        return min(candidates)

    # --------------------------------------------------------
    # Block boundaries
    # --------------------------------------------------------

    base_start = find_line(
        "# Base from sentiment"
    )

    structure_start = find_line(
        "# Structure tilt",
        after=base_start,
    )

    credit_start = find_line(
        "# Credit tilt",
        after=structure_start,
    )

    liquidity_start = find_line(
        "# Liquidity tilt",
        after=credit_start,
    )

    liquidity_level_start = find_line(
        'if liq_level_bucket == "HIGH":',
        after=liquidity_start,
    )

    structural_v2_start = find_line(
        "Structural v2 Penalty",
        after=liquidity_level_start,
    )

    drift_start = find_line(
        "Drift Adjustment",
        after=structural_v2_start,
    )

    flow_gamma_start = find_line(
        "flow_gamma_tilt = 0",
        after=drift_start,
    )

    flow_continuity_start = find_line(
        "flow_continuity_tilt = 0",
        after=flow_gamma_start,
    )

    flow_regime_start = find_line(
        "flow_regime_tilt = 0",
        after=flow_continuity_start,
    )

    macro_start = find_line(
        "macro_tilt = 0",
        after=flow_regime_start,
    )

    positioning_start = find_line(
        "Positioning Penalty",
        after=macro_start,
    )

    event_floor_start = find_line(
        "Event-Watching Floor",
        after=positioning_start,
    )

    phase_cap_start = find_line(
        "Phase Cap v2",
        after=event_floor_start,
    )

    pre_cap_line = find_line(
        "pre_cap_budget = budget",
        after=phase_cap_start,
    )

    final_budget_line = find_line(
        "budget = min(int(round(budget)), final_cap)",
        after=pre_cap_line,
    )

    clamp_line = find_line(
        "budget = _clamp(budget, 0, 100)",
        after=final_budget_line,
    )

    # --------------------------------------------------------
    # Classification ranges
    # --------------------------------------------------------

    ranges = [
        (
            "BASE",
            base_start,
            structure_start,
        ),
        (
            "STRUCTURE",
            structure_start,
            credit_start,
        ),
        (
            "CREDIT",
            credit_start,
            liquidity_start,
        ),
        (
            "LIQUIDITY_DIRECTION",
            liquidity_start,
            liquidity_level_start,
        ),
        (
            "LIQUIDITY_LEVEL",
            liquidity_level_start,
            structural_v2_start,
        ),
        (
            "STRUCTURAL_V2",
            structural_v2_start,
            drift_start,
        ),
        (
            "DRIFT",
            drift_start,
            flow_gamma_start,
        ),
        (
            "FLOW_GAMMA",
            flow_gamma_start,
            flow_continuity_start,
        ),
        (
            "FLOW_CONTINUITY",
            flow_continuity_start,
            flow_regime_start,
        ),
        (
            "FLOW_REGIME",
            flow_regime_start,
            macro_start,
        ),
        (
            "MACRO",
            macro_start,
            positioning_start,
        ),
        (
            "POSITIONING",
            positioning_start,
            event_floor_start,
        ),
        (
            "EVENT_FLOOR",
            event_floor_start,
            phase_cap_start,
        ),
    ]

    def classify(lineno: int) -> str | None:

        for stage, lo, hi in ranges:
            if lo <= lineno < hi:
                return stage

        return None

    return {
        "source_by_lineno":
            source_by_lineno,

        "classify":
            classify,

        "pre_cap_line":
            pre_cap_line,

        "final_budget_line":
            final_budget_line,

        "clamp_line":
            clamp_line,

        "anchors": {
            "base_start": base_start,
            "structure_start": structure_start,
            "credit_start": credit_start,
            "liquidity_start": liquidity_start,
            "liquidity_level_start": liquidity_level_start,
            "structural_v2_start": structural_v2_start,
            "drift_start": drift_start,
            "flow_gamma_start": flow_gamma_start,
            "flow_continuity_start": flow_continuity_start,
            "flow_regime_start": flow_regime_start,
            "macro_start": macro_start,
            "positioning_start": positioning_start,
            "event_floor_start": event_floor_start,
            "phase_cap_start": phase_cap_start,
            "pre_cap_line": pre_cap_line,
            "final_budget_line": final_budget_line,
            "clamp_line": clamp_line,
        },
    }


SOURCE_CONTRACT = build_production_source_contract()


# ============================================================
# Same-run Production line trace
#
# This observes REAL budget mutations made by
# narrative_engine_filter().
#
# It does NOT duplicate the Filter13 scoring formula.
# ============================================================

def run_narrative_with_stage_trace(
    market_data: dict[str, Any],
) -> dict[str, Any]:

    target_code = (
        sf.narrative_engine_filter.__code__
    )

    source_by_lineno = (
        SOURCE_CONTRACT[
            "source_by_lineno"
        ]
    )

    classify = (
        SOURCE_CONTRACT[
            "classify"
        ]
    )

    events: list[dict[str, Any]] = []

    captured_locals: dict[str, Any] = {}

    last_lineno: int | None = None
    last_budget: Any = None
    budget_seen = False

    def process_previous_line(
        frame,
        current_budget,
    ) -> None:
        nonlocal last_budget, budget_seen

        if last_lineno is None:
            return

        if current_budget is None:
            return

        current = to_float(
            current_budget
        )

        if pd.isna(current):
            return

        if not budget_seen:

            # First observable budget comes from the
            # Production base-budget assignment.
            stage = classify(
                last_lineno
            )

            if stage == "BASE":

                events.append({
                    "stage": "BASE",
                    "line":
                        last_lineno,

                    "source":
                        source_by_lineno.get(
                            last_lineno,
                            "",
                        ).strip(),

                    "before":
                        np.nan,

                    "after":
                        current,

                    "delta":
                        np.nan,
                })

            last_budget = current
            budget_seen = True
            return

        previous = to_float(
            last_budget
        )

        if pd.isna(previous):
            last_budget = current
            return

        if abs(
            current
            - previous
        ) <= TOL:
            return

        stage = classify(
            last_lineno
        )

        # Final cap lines are verified separately from
        # captured Production locals. They are intentionally
        # not attributed to pre-cap layers.
        if stage is not None:

            events.append({
                "stage":
                    stage,

                "line":
                    last_lineno,

                "source":
                    source_by_lineno.get(
                        last_lineno,
                        "",
                    ).strip(),

                "before":
                    previous,

                "after":
                    current,

                "delta":
                    current - previous,
            })

        last_budget = current

    def tracer(frame, event, arg):
        nonlocal last_lineno

        if frame.f_code is not target_code:
            return tracer

        if event == "line":

            current_budget = (
                frame.f_locals.get(
                    "budget"
                )
            )

            process_previous_line(
                frame,
                current_budget,
            )

            last_lineno = (
                frame.f_lineno
            )

        elif event == "return":

            current_budget = (
                frame.f_locals.get(
                    "budget"
                )
            )

            process_previous_line(
                frame,
                current_budget,
            )

            captured_locals.update(
                dict(
                    frame.f_locals
                )
            )

        return tracer

    old_trace = sys.gettrace()

    try:

        sys.settrace(
            tracer
        )

        with contextlib.redirect_stdout(
            io.StringIO()
        ):
            sf.narrative_engine_filter(
                market_data
            )

    finally:

        sys.settrace(
            old_trace
        )

    if not captured_locals:
        raise RuntimeError(
            "Production narrative local capture failed."
        )

    if not events:
        raise RuntimeError(
            "Production budget mutation capture failed."
        )

    return {
        "events":
            events,

        "locals":
            captured_locals,
    }


# ============================================================
# Forward economic diagnostics
#
# EX-POST ONLY.
# These fields are never fed into Production.
# ============================================================

def add_forward_market_outcomes(
    panel: pd.DataFrame,
) -> pd.DataFrame:

    out = panel.copy()

    out["SPY"] = pd.to_numeric(
        out["SPY"],
        errors="coerce",
    )

    for horizon in [
        5,
        20,
        60,
    ]:

        out[
            f"spy_fwd_{horizon}d"
        ] = (
            out["SPY"]
            .shift(-horizon)
            / out["SPY"]
            - 1.0
        ) * 100.0

    prices = (
        out["SPY"]
        .to_numpy(
            dtype=float
        )
    )

    def rolling_forward_mdd(
        horizon: int,
    ) -> np.ndarray:

        result = np.full(
            len(prices),
            np.nan,
            dtype=float,
        )

        for i in range(
            len(prices)
        ):

            end = min(
                len(prices),
                i + horizon + 1,
            )

            window = prices[
                i:end
            ]

            window = window[
                np.isfinite(window)
            ]

            if len(window) < 2:
                continue

            wealth = (
                window
                / window[0]
            )

            peak = np.maximum.accumulate(
                wealth
            )

            dd = (
                wealth
                / peak
                - 1.0
            )

            result[i] = (
                float(
                    np.min(dd)
                )
                * 100.0
            )

        return result

    out[
        "spy_fwd_mdd_20d"
    ] = rolling_forward_mdd(
        20
    )

    out[
        "spy_fwd_mdd_60d"
    ] = rolling_forward_mdd(
        60
    )

    return out


# ============================================================
# Main
# ============================================================

def main() -> None:

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Existing canonical baseline = independent parity anchor
    # --------------------------------------------------------

    if not CANONICAL_PATH.exists():
        raise FileNotFoundError(
            "Canonical Filter13 baseline missing:\n"
            f"{CANONICAL_PATH}"
        )

    canonical = pd.read_csv(
        CANONICAL_PATH
    )

    canonical[
        "signal_date"
    ] = pd.to_datetime(
        canonical[
            "signal_date"
        ],
        errors="coerce",
    )

    canonical = (
        canonical[
            canonical[
                "status"
            ].eq("OK")
        ]
        .copy()
        .sort_values(
            "signal_date"
        )
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    if len(canonical) != EXPECTED_ROWS:
        raise RuntimeError(
            "Canonical baseline row count changed: "
            f"{len(canonical):,} "
            f"!= {EXPECTED_ROWS:,}"
        )

    # --------------------------------------------------------
    # Current master panel
    # --------------------------------------------------------

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
        .sort_values(
            "signal_date"
        )
        .reset_index(
            drop=True
        )
    )

    panel_with_outcomes = (
        add_forward_market_outcomes(
            panel
        )
    )

    mask = (
        panel[
            "execution_date"
        ].notna()
        &
        pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    )

    indices = (
        panel.index[
            mask
        ].tolist()
    )

    if len(indices) != EXPECTED_ROWS:
        raise RuntimeError(
            "Current eligible row count changed: "
            f"{len(indices):,} "
            f"!= {EXPECTED_ROWS:,}"
        )

    # --------------------------------------------------------
    # Source anchors diagnostic
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print(
        "FILTER13 CANONICAL FULL ATTRIBUTION AUDIT"
    )
    print("=" * 80)
    print()

    print(
        "Source = CURRENT master_panel + "
        "CURRENT pre-13 Production chain + "
        "CURRENT narrative_engine_filter"
    )

    print()
    print(
        "Legacy attribution CSV : NOT USED"
    )
    print(
        "Legacy candidate CSV   : NOT USED"
    )
    print(
        "Copied budget formula  : NOT USED"
    )
    print(
        "Production modification: NONE"
    )
    print()

    print(
        "Dynamic Production source anchors:"
    )

    for name, lineno in (
        SOURCE_CONTRACT[
            "anchors"
        ].items()
    ):
        print(
            f"- {name:28s}: "
            f"{lineno}"
        )

    # --------------------------------------------------------
    # Sequential historical execution
    # --------------------------------------------------------

    previous_flow_memory = {
        "flow_state":
            "N/A",

        "flow_score":
            0,

        "persistence_days":
            0,
    }

    previous_exposure = 50.0

    rows: list[
        dict[str, Any]
    ] = []

    error_rows = []

    stages = [
        "STRUCTURE",
        "CREDIT",
        "LIQUIDITY_DIRECTION",
        "LIQUIDITY_LEVEL",
        "STRUCTURAL_V2",
        "DRIFT",
        "FLOW_GAMMA",
        "FLOW_CONTINUITY",
        "FLOW_REGIME",
        "MACRO",
        "POSITIONING",
        "EVENT_FLOOR",
    ]

    for count, i in enumerate(
        indices,
        start=1,
    ):

        panel_row = (
            panel.iloc[i]
        )

        try:

            market_data = (
                build_market_data(
                    panel=panel,
                    row_index=i,
                    previous_exposure=previous_exposure,
                )
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

            traced = (
                run_narrative_with_stage_trace(
                    market_data
                )
            )

            events = traced[
                "events"
            ]

            loc = traced[
                "locals"
            ]

            # ------------------------------------------------
            # Base
            # ------------------------------------------------

            base_events = [
                e
                for e in events
                if e[
                    "stage"
                ] == "BASE"
            ]

            if len(base_events) != 1:
                raise RuntimeError(
                    "Expected exactly one Base Budget "
                    f"event, got {len(base_events)}"
                )

            base_budget = to_float(
                base_events[0][
                    "after"
                ]
            )

            # ------------------------------------------------
            # Exact stage deltas observed from Production
            # ------------------------------------------------

            stage_delta = {
                stage: 0.0
                for stage in stages
            }

            stage_event_count = {
                stage: 0
                for stage in stages
            }

            for e in events:

                stage = e[
                    "stage"
                ]

                if stage not in stage_delta:
                    continue

                delta = to_float(
                    e[
                        "delta"
                    ]
                )

                if pd.isna(delta):
                    continue

                stage_delta[
                    stage
                ] += delta

                stage_event_count[
                    stage
                ] += 1

            # ------------------------------------------------
            # Reconstruct PRE-CAP from observed mutations
            # ------------------------------------------------

            reconstructed_pre_cap = (
                base_budget
                + sum(
                    stage_delta.values()
                )
            )

            captured_pre_cap = to_float(
                loc.get(
                    "pre_cap_budget"
                )
            )

            production_pre_cap = to_float(
                market_data.get(
                    "PRE_CAP_BUDGET"
                )
            )

            canonical_row = (
                canonical[
                    canonical[
                        "signal_date"
                    ].eq(
                        pd.Timestamp(
                            panel_row[
                                "signal_date"
                            ]
                        )
                    )
                ]
            )

            if len(canonical_row) != 1:
                raise RuntimeError(
                    "Canonical row lookup failed for "
                    f"{panel_row['signal_date']}"
                )

            canonical_row = (
                canonical_row.iloc[0]
            )

            canonical_pre_cap = to_float(
                canonical_row[
                    "pre_cap_budget"
                ]
            )

            canonical_budget = to_float(
                canonical_row[
                    "risk_budget"
                ]
            )

            # ------------------------------------------------
            # Exact cap decomposition
            #
            # Production:
            # final_cap = min(cap, v2_cap)
            # budget = min(int(round(budget)), final_cap)
            # clamp 0..100
            #
            # For attribution we mechanically decompose:
            # rounding -> Phase cap -> v2 cap -> clamp
            # ------------------------------------------------

            phase_cap = to_float(
                loc.get(
                    "cap"
                )
            )

            v2_cap = to_float(
                loc.get(
                    "v2_cap"
                )
            )

            captured_final_cap = (
                to_float(
                    loc.get(
                        "final_cap"
                    )
                )
            )

            rounded_pre_cap = float(
                int(
                    round(
                        captured_pre_cap
                    )
                )
            )

            rounding_delta = (
                rounded_pre_cap
                - captured_pre_cap
            )

            after_phase_cap = (
                min(
                    rounded_pre_cap,
                    phase_cap,
                )
                if pd.notna(
                    phase_cap
                )
                else rounded_pre_cap
            )

            phase_cap_delta = (
                after_phase_cap
                - rounded_pre_cap
            )

            after_v2_cap = (
                min(
                    after_phase_cap,
                    v2_cap,
                )
                if pd.notna(
                    v2_cap
                )
                else after_phase_cap
            )

            v2_final_cap_delta = (
                after_v2_cap
                - after_phase_cap
            )

            clamped_budget = float(
                max(
                    0,
                    min(
                        100,
                        after_v2_cap,
                    ),
                )
            )

            clamp_delta = (
                clamped_budget
                - after_v2_cap
            )

            reconstructed_final = (
                clamped_budget
            )

            production_budget = to_float(
                market_data.get(
                    "RISK_BUDGET"
                )
            )

            captured_budget = to_float(
                loc.get(
                    "budget"
                )
            )

            # ------------------------------------------------
            # Cap contract parity
            # ------------------------------------------------

            reconstructed_final_cap = (
                min(
                    phase_cap,
                    v2_cap,
                )
                if (
                    pd.notna(
                        phase_cap
                    )
                    and pd.notna(
                        v2_cap
                    )
                )
                else (
                    phase_cap
                    if pd.notna(
                        phase_cap
                    )
                    else v2_cap
                )
            )

            # ------------------------------------------------
            # Stage running budgets
            # ------------------------------------------------

            running = (
                base_budget
            )

            running_values = {
                "budget_after_base":
                    running
            }

            for stage in stages:

                running += (
                    stage_delta[
                        stage
                    ]
                )

                running_values[
                    "budget_after_"
                    + stage.lower()
                ] = running

            # ------------------------------------------------
            # Market outcomes
            # ------------------------------------------------

            outcome_row = (
                panel_with_outcomes.iloc[
                    i
                ]
            )

            row = {
                "signal_date":
                    panel_row[
                        "signal_date"
                    ],

                "execution_date":
                    panel_row[
                        "execution_date"
                    ],

                "sent_state":
                    normalize_text(
                        loc.get(
                            "sent_state"
                        )
                    ),

                "phase":
                    normalize_text(
                        loc.get(
                            "phase"
                        )
                    ),

                "macro_narrative":
                    normalize_text(
                        loc.get(
                            "macro_narrative"
                        )
                    ),

                "struct_v2":
                    normalize_text(
                        loc.get(
                            "struct_v2"
                        )
                    ),

                # --------------------------------------------
                # Dead-layer contract inputs
                # Captured directly from the SAME Production frame.
                # --------------------------------------------

                "mixed":
                    loc.get(
                        "mixed"
                    ),

                "easing":
                    loc.get(
                        "easing"
                    ),

                "tightening":
                    loc.get(
                        "tightening"
                    ),

                "liq_dir_tag":
                    normalize_text(
                        loc.get(
                            "liq_dir_tag"
                        )
                    ),

                "liq_level_bucket":
                    normalize_text(
                        loc.get(
                            "liq_level_bucket"
                        )
                    ),

                "base_budget":
                    base_budget,

                # --------------------------------------------
                # Layer deltas
                # --------------------------------------------

                "delta_structure":
                    stage_delta[
                        "STRUCTURE"
                    ],

                "delta_credit":
                    stage_delta[
                        "CREDIT"
                    ],

                "delta_liquidity_direction":
                    stage_delta[
                        "LIQUIDITY_DIRECTION"
                    ],

                "delta_liquidity_level":
                    stage_delta[
                        "LIQUIDITY_LEVEL"
                    ],

                "delta_structural_v2":
                    stage_delta[
                        "STRUCTURAL_V2"
                    ],

                "delta_drift":
                    stage_delta[
                        "DRIFT"
                    ],

                "delta_flow_gamma":
                    stage_delta[
                        "FLOW_GAMMA"
                    ],

                "delta_flow_continuity":
                    stage_delta[
                        "FLOW_CONTINUITY"
                    ],

                "delta_flow_regime":
                    stage_delta[
                        "FLOW_REGIME"
                    ],

                "delta_macro":
                    stage_delta[
                        "MACRO"
                    ],

                "delta_positioning":
                    stage_delta[
                        "POSITIONING"
                    ],

                "delta_event_floor":
                    stage_delta[
                        "EVENT_FLOOR"
                    ],

                "delta_rounding":
                    rounding_delta,

                "delta_phase_cap":
                    phase_cap_delta,

                "delta_v2_final_cap":
                    v2_final_cap_delta,

                "delta_final_clamp":
                    clamp_delta,

                # --------------------------------------------
                # Runtime values
                # --------------------------------------------

                "phase_cap":
                    phase_cap,

                "v2_cap":
                    v2_cap,

                "captured_final_cap":
                    captured_final_cap,

                "reconstructed_final_cap":
                    reconstructed_final_cap,

                "captured_pre_cap":
                    captured_pre_cap,

                "production_pre_cap":
                    production_pre_cap,

                "canonical_pre_cap":
                    canonical_pre_cap,

                "reconstructed_pre_cap":
                    reconstructed_pre_cap,

                "captured_risk_budget":
                    captured_budget,

                "production_risk_budget":
                    production_budget,

                "canonical_risk_budget":
                    canonical_budget,

                "reconstructed_risk_budget":
                    reconstructed_final,

                # --------------------------------------------
                # Parity
                # --------------------------------------------

                "precap_trace_reconstruction_error":
                    (
                        reconstructed_pre_cap
                        - captured_pre_cap
                    ),

                "precap_marketdata_error":
                    (
                        production_pre_cap
                        - captured_pre_cap
                    ),

                "precap_canonical_error":
                    (
                        canonical_pre_cap
                        - captured_pre_cap
                    ),

                "final_trace_reconstruction_error":
                    (
                        reconstructed_final
                        - captured_budget
                    ),

                "final_marketdata_error":
                    (
                        production_budget
                        - captured_budget
                    ),

                "final_canonical_error":
                    (
                        canonical_budget
                        - captured_budget
                    ),

                "final_cap_error":
                    (
                        reconstructed_final_cap
                        - captured_final_cap
                    ),

                # --------------------------------------------
                # Ex-post market outcomes
                # --------------------------------------------

                "spy_fwd_5d":
                    outcome_row[
                        "spy_fwd_5d"
                    ],

                "spy_fwd_20d":
                    outcome_row[
                        "spy_fwd_20d"
                    ],

                "spy_fwd_60d":
                    outcome_row[
                        "spy_fwd_60d"
                    ],

                "spy_fwd_mdd_20d":
                    outcome_row[
                        "spy_fwd_mdd_20d"
                    ],

                "spy_fwd_mdd_60d":
                    outcome_row[
                        "spy_fwd_mdd_60d"
                    ],

                "status":
                    "OK",

                "error":
                    "",
            }

            row.update(
                running_values
            )

            # Useful source execution counts.
            for stage in stages:

                row[
                    "events_"
                    + stage.lower()
                ] = (
                    stage_event_count[
                        stage
                    ]
                )

            rows.append(
                row
            )

            previous_flow_memory = (
                next_flow_memory
            )

        except Exception as exc:

            error_rows.append({
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
                f"{count:,}/"
                f"{len(indices):,}",
                end="",
                flush=True,
            )

    print()

    if error_rows:

        errors = pd.DataFrame(
            error_rows
        )

        print()
        print(
            "FIRST EXECUTION ERRORS"
        )

        print(
            errors.head(
                20
            ).to_string(
                index=False
            )
        )

        raise RuntimeError(
            "Filter13 full attribution had "
            f"{len(error_rows):,} execution errors."
        )

    detail = pd.DataFrame(
        rows
    )

    detail[
        "signal_date"
    ] = pd.to_datetime(
        detail[
            "signal_date"
        ],
        errors="coerce",
    )

    detail = (
        detail
        .sort_values(
            "signal_date"
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # HARD PARITY GATE
    # ========================================================

    parity_cols = [
        "precap_trace_reconstruction_error",
        "precap_marketdata_error",
        "precap_canonical_error",
        "final_trace_reconstruction_error",
        "final_marketdata_error",
        "final_canonical_error",
        "final_cap_error",
    ]

    fail_counts = {}
    max_errors = {}

    for col in parity_cols:

        values = pd.to_numeric(
            detail[col],
            errors="coerce",
        )

        fail_counts[
            col
        ] = int(
            (
                values.abs()
                > TOL
            ).sum()
        )

        max_errors[
            col
        ] = max_abs(
            values
        )

    total_fail = sum(
        fail_counts.values()
    )

    print()
    print(
        "## HARD PARITY GATE"
    )
    print()

    print(
        f"Rows                  : "
        f"{len(detail):,}"
    )

    print(
        f"Execution errors      : "
        f"{len(error_rows):,}"
    )

    for col in parity_cols:

        print(
            f"{col:40s}: "
            f"fail="
            f"{fail_counts[col]:,}, "
            f"max="
            f"{max_errors[col]:.12f}"
        )

    if (
        len(detail)
        != EXPECTED_ROWS
        or total_fail > 0
    ):

        detail.to_csv(
            DETAIL_PATH,
            index=False,
            encoding="utf-8-sig",
        )

        bad_mask = pd.Series(
            False,
            index=detail.index,
        )

        for col in parity_cols:

            bad_mask |= (
                pd.to_numeric(
                    detail[col],
                    errors="coerce",
                ).abs()
                > TOL
            )

        bad = detail[
            bad_mask
        ]

        if not bad.empty:

            print()
            print(
                "FIRST PARITY FAILURES"
            )

            show = [
                "signal_date",
                "base_budget",
                "captured_pre_cap",
                "reconstructed_pre_cap",
                "production_pre_cap",
                "canonical_pre_cap",
                "captured_risk_budget",
                "reconstructed_risk_budget",
                "production_risk_budget",
                "canonical_risk_budget",
            ] + parity_cols

            print(
                bad[
                    show
                ]
                .head(20)
                .to_string(
                    index=False
                )
            )

        raise RuntimeError(
            "FILTER13 FULL ATTRIBUTION PARITY FAILED. "
            "Economic interpretation is prohibited."
        )

    print()
    print(
        "FULL ATTRIBUTION PARITY: PASS"
    )

    # ========================================================
    # Attribution summaries
    # ========================================================

    layer_map = [
        (
            "Structure",
            "delta_structure",
            "budget_after_base",
        ),
        (
            "Credit",
            "delta_credit",
            "budget_after_structure",
        ),
        (
            "Liquidity Direction",
            "delta_liquidity_direction",
            "budget_after_credit",
        ),
        (
            "Liquidity Level",
            "delta_liquidity_level",
            "budget_after_liquidity_direction",
        ),
        (
            "Structural v2",
            "delta_structural_v2",
            "budget_after_liquidity_level",
        ),
        (
            "Drift",
            "delta_drift",
            "budget_after_structural_v2",
        ),
        (
            "Flow Gamma",
            "delta_flow_gamma",
            "budget_after_drift",
        ),
        (
            "Flow Continuity",
            "delta_flow_continuity",
            "budget_after_flow_gamma",
        ),
        (
            "Flow Regime",
            "delta_flow_regime",
            "budget_after_flow_continuity",
        ),
        (
            "Macro",
            "delta_macro",
            "budget_after_flow_regime",
        ),
        (
            "Positioning",
            "delta_positioning",
            "budget_after_macro",
        ),
        (
            "Event Floor",
            "delta_event_floor",
            "budget_after_positioning",
        ),
        (
            "Rounding",
            "delta_rounding",
            None,
        ),
        (
            "Phase Cap",
            "delta_phase_cap",
            None,
        ),
        (
            "Structural v2 Final Cap",
            "delta_v2_final_cap",
            None,
        ),
        (
            "Final Clamp",
            "delta_final_clamp",
            None,
        ),
    ]

    layer_rows = []
    econ_rows = []

    final_budget_series = pd.to_numeric(
        detail[
            "canonical_risk_budget"
        ],
        errors="coerce",
    )

    for (
        layer,
        delta_col,
        before_col,
    ) in layer_map:

        delta = pd.to_numeric(
            detail[
                delta_col
            ],
            errors="coerce",
        ).fillna(0.0)

        cut_mask = (
            delta < -TOL
        )

        add_mask = (
            delta > TOL
        )

        applied_mask = (
            delta.abs()
            > TOL
        )

        cut_values = delta[
            cut_mask
        ]

        add_values = delta[
            add_mask
        ]

        if (
            before_col is not None
            and before_col
            in detail.columns
        ):

            before = pd.to_numeric(
                detail[
                    before_col
                ],
                errors="coerce",
            )

            final_below_before_rate = (
                (
                    final_budget_series[
                        cut_mask
                    ]
                    <
                    before[
                        cut_mask
                    ]
                ).mean()
                if cut_mask.any()
                else np.nan
            )

        else:

            final_below_before_rate = (
                np.nan
            )

        layer_rows.append({
            "layer":
                layer,

            "applied_days":
                int(
                    applied_mask.sum()
                ),

            "cut_days":
                int(
                    cut_mask.sum()
                ),

            "add_days":
                int(
                    add_mask.sum()
                ),

            "avg_delta_all_days":
                float(
                    delta.mean()
                ),

            "total_delta":
                float(
                    delta.sum()
                ),

            "total_cut_abs":
                float(
                    -cut_values.sum()
                )
                if len(
                    cut_values
                )
                else 0.0,

            "avg_cut_when_cut":
                float(
                    cut_values.mean()
                )
                if len(
                    cut_values
                )
                else np.nan,

            "avg_add_when_add":
                float(
                    add_values.mean()
                )
                if len(
                    add_values
                )
                else np.nan,

            "final_below_stage_before_rate_on_cut_days":
                final_below_before_rate,
        })

        # ----------------------------------------------------
        # Ex-post economics on CUT days only
        # ----------------------------------------------------

        cut_days = detail[
            cut_mask
        ].copy()

        if cut_days.empty:

            econ_rows.append({
                "layer":
                    layer,

                "cut_days":
                    0,

                "avg_cut":
                    np.nan,

                "avg_spy_fwd_5d":
                    np.nan,

                "avg_spy_fwd_20d":
                    np.nan,

                "avg_spy_fwd_60d":
                    np.nan,

                "down_20d_rate":
                    np.nan,

                "down_60d_rate":
                    np.nan,

                "avg_fwd_mdd_20d":
                    np.nan,

                "avg_fwd_mdd_60d":
                    np.nan,

                "mdd20_le_minus5_rate":
                    np.nan,

                "mdd60_le_minus10_rate":
                    np.nan,
            })

            continue

        fwd5 = pd.to_numeric(
            cut_days[
                "spy_fwd_5d"
            ],
            errors="coerce",
        )

        fwd20 = pd.to_numeric(
            cut_days[
                "spy_fwd_20d"
            ],
            errors="coerce",
        )

        fwd60 = pd.to_numeric(
            cut_days[
                "spy_fwd_60d"
            ],
            errors="coerce",
        )

        mdd20 = pd.to_numeric(
            cut_days[
                "spy_fwd_mdd_20d"
            ],
            errors="coerce",
        )

        mdd60 = pd.to_numeric(
            cut_days[
                "spy_fwd_mdd_60d"
            ],
            errors="coerce",
        )

        econ_rows.append({
            "layer":
                layer,

            "cut_days":
                int(
                    cut_mask.sum()
                ),

            "avg_cut":
                float(
                    delta[
                        cut_mask
                    ].mean()
                ),

            "avg_spy_fwd_5d":
                float(
                    fwd5.mean()
                ),

            "avg_spy_fwd_20d":
                float(
                    fwd20.mean()
                ),

            "avg_spy_fwd_60d":
                float(
                    fwd60.mean()
                ),

            "down_20d_rate":
                float(
                    (
                        fwd20 < 0
                    ).mean()
                ),

            "down_60d_rate":
                float(
                    (
                        fwd60 < 0
                    ).mean()
                ),

            "avg_fwd_mdd_20d":
                float(
                    mdd20.mean()
                ),

            "avg_fwd_mdd_60d":
                float(
                    mdd60.mean()
                ),

            "mdd20_le_minus5_rate":
                float(
                    (
                        mdd20 <= -5
                    ).mean()
                ),

            "mdd60_le_minus10_rate":
                float(
                    (
                        mdd60 <= -10
                    ).mean()
                ),
        })

    layer_summary = pd.DataFrame(
        layer_rows
    )

    economic_summary = pd.DataFrame(
        econ_rows
    )

    # Largest actual budget reducers first.
    layer_summary = (
        layer_summary
        .sort_values(
            [
                "total_cut_abs",
                "cut_days",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    economic_summary = (
        economic_summary.merge(
            layer_summary[
                [
                    "layer",
                    "total_cut_abs",
                ]
            ],
            on="layer",
            how="left",
        )
        .sort_values(
            "total_cut_abs",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # Save outputs
    # ========================================================

    detail.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    layer_summary.to_csv(
        LAYER_SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    economic_summary.to_csv(
        ECONOMIC_SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Final report
    # ========================================================

    avg_base = float(
        pd.to_numeric(
            detail[
                "base_budget"
            ],
            errors="coerce",
        ).mean()
    )

    avg_pre_cap = float(
        pd.to_numeric(
            detail[
                "canonical_pre_cap"
            ],
            errors="coerce",
        ).mean()
    )

    avg_final = float(
        pd.to_numeric(
            detail[
                "canonical_risk_budget"
            ],
            errors="coerce",
        ).mean()
    )

    lines = []

    lines.append(
        "# FILTER13 CANONICAL FULL ATTRIBUTION"
    )

    lines.append("")

    lines.append(
        "## Source Contract"
    )

    lines.append("")

    lines.append(
        "- CURRENT master_panel.csv"
    )

    lines.append(
        "- CURRENT prepare_filter13_execution_state()"
    )

    lines.append(
        "- CURRENT Production narrative_engine_filter()"
    )

    lines.append(
        "- Runtime line-trace of actual Production budget mutations"
    )

    lines.append(
        "- Existing canonical baseline used only as an independent parity anchor"
    )

    lines.append(
        "- Legacy attribution / candidate artifacts NOT USED"
    )

    lines.append(
        "- Production code modified: NO"
    )

    lines.append("")

    lines.append(
        "## Hard Parity"
    )

    lines.append("")

    lines.append(
        f"Rows             : "
        f"{len(detail):,}"
    )

    lines.append(
        "Execution errors : 0"
    )

    for col in parity_cols:

        lines.append(
            f"{col:40s}: "
            f"fail=0, "
            f"max_abs_error="
            f"{max_errors[col]:.12f}"
        )

    lines.append("")

    lines.append(
        "FULL ATTRIBUTION PARITY: PASS"
    )

    lines.append("")

    lines.append(
        "## Budget Levels"
    )

    lines.append("")

    lines.append(
        f"Average Base Budget    : "
        f"{avg_base:.6f}"
    )

    lines.append(
        f"Average Pre-Cap Budget : "
        f"{avg_pre_cap:.6f}"
    )

    lines.append(
        f"Average Final Budget   : "
        f"{avg_final:.6f}"
    )

    lines.append("")

    lines.append(
        "## Layer Attribution"
    )

    lines.append("")

    lines.append(
        layer_summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "## Ex-Post Economic Diagnostics on Cut Days"
    )

    lines.append("")

    lines.append(
        economic_summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "## Interpretation Rules"
    )

    lines.append("")

    lines.append(
        "- Large total_cut_abs identifies where Filter13 removes the most risk."
    )

    lines.append(
        "- Forward returns / forward MDD are ex-post diagnostics only; they are NOT Production inputs."
    )

    lines.append(
        "- A cut layer with materially worse subsequent downside may represent useful protection."
    )

    lines.append(
        "- A cut layer followed by consistently strong positive returns may represent opportunity cost and should become a separate research ticket."
    )

    lines.append(
        "- No Production rule is changed by this audit."
    )

    lines.append(
        "- Candidate tuning is prohibited unless a separate research hypothesis is opened after this attribution closes."
    )

    lines.append("")

    lines.append(
        "FINAL STATUS: PASS"
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
    print(
        "Saved:"
    )

    print(
        DETAIL_PATH
    )

    print(
        LAYER_SUMMARY_PATH
    )

    print(
        ECONOMIC_SUMMARY_PATH
    )

    print(
        SUMMARY_PATH
    )


if __name__ == "__main__":
    main()
