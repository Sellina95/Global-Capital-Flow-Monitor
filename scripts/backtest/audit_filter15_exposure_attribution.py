from __future__ import annotations

"""
Filter15 Exposure Attribution Audit

Purpose
-------
Attribute the exact exposure change from:

    Filter13 RISK_BUDGET
        ->
    Filter15 RECOMMENDED_EXPOSURE

into Production execution-order components:

    VIX Convexity
    VIX Regime
    Positioning Heat / Unwind
    Gamma
    CTA
    Credit Level
    Credit Change
    Hard Deadman
    Rounding / Clamp

Important
---------
- Production source is READ ONLY.
- Uses historical PIT market_data.
- Uses the already validated Production pre-Filter13 execution chain.
- Calls actual Production Filter13 and Filter15.
- Independently replays Filter15 for attribution.
- Attribution must reconcile exactly to actual Production Filter15 output.
- No future-data backfill.
"""

from pathlib import Path
import sys
from typing import Any

import pandas as pd


# ============================================================
# Paths / Imports
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT))

import filters.strategist_filters as sf

from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)


PANEL_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

RESULT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

DAILY_OUT = (
    RESULT_DIR
    / "filter15_exposure_attribution_daily.csv"
)

SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_exposure_attribution_summary.csv"
)

TXT_OUT = (
    RESULT_DIR
    / "filter15_exposure_attribution_audit.txt"
)


# ============================================================
# Helpers
# ============================================================

def _to_float(x):
    if x is None:
        return None

    if isinstance(x, (int, float)):
        return float(x)

    try:
        return float(
            str(x)
            .replace(",", "")
            .replace("%", "")
            .strip()
        )
    except Exception:
        return None


def _clamp(x, lo=0, hi=100):
    """
    Exact Production Filter15 clamp.
    """
    return max(
        lo,
        min(
            int(round(x)),
            hi,
        ),
    )


def _delta(before, after):
    """
    Signed exposure-point change.

    Positive = exposure reduced.
    Negative = exposure increased.
    """
    return float(before) - float(after)


# ============================================================
# Independent Production-Order Attribution Replay
# ============================================================

def replay_filter15_attribution(
    market_data: dict[str, Any],
) -> dict[str, Any]:

    # --------------------------------------------------------
    # Inputs — same fallbacks as Production
    # --------------------------------------------------------

    risk_budget = _to_float(
        market_data.get(
            "RISK_BUDGET",
            50,
        )
    )

    if risk_budget is None:
        risk_budget = 50.0


    vix_series = (
        market_data.get(
            "VIX",
            {},
        )
        or {}
    )

    vix_today = _to_float(
        vix_series.get("today")
    )

    vix_pct = _to_float(
        vix_series.get("pct_change")
    )


    pos_z = _to_float(
        market_data.get(
            "SP500_POS_Z",
            0.0,
        )
    )

    if pos_z is None:
        pos_z = 0.0


    pos_slope = _to_float(
        market_data.get(
            "POS_SLOPE"
        )
    )

    if pos_slope is None:
        pos_slope = 0.0


    gamma = _to_float(
        market_data.get(
            "DEALER_GAMMA_BIAS",
            1.0,
        )
    )

    if gamma is None:
        gamma = 1.0


    cta = _to_float(
        market_data.get(
            "CTA_MOMENTUM_SCORE",
            1.0,
        )
    )

    if cta is None:
        cta = 1.0


    hy_oas = (
        market_data.get(
            "HY_OAS",
            {},
        )
        or {}
    )

    hy_level = _to_float(
        hy_oas.get("today")
    )

    hy_pct = _to_float(
        hy_oas.get("pct_change")
    )


    macro_narrative = str(
        market_data.get(
            "MACRO_NARRATIVE",
            "N/A",
        )
        or "N/A"
    ).upper()


    cross_asset_tape = (
        market_data.get(
            "CROSS_ASSET_TAPE",
            {},
        )
        or {}
    )


    # ========================================================
    # Start
    # ========================================================

    exposure = float(risk_budget)

    start_exposure = exposure

    drivers = []


    # ========================================================
    # 0. Hard Deadman / Risk Compression classification
    #
    # Production determines this BEFORE the multipliers,
    # but Hard Deadman is applied only at Final Override.
    # ========================================================

    hard_deadman = False
    hard_deadman_reason = ""

    risk_compression = False
    compression_reason = ""


    if (
        hy_level is not None
        and hy_level >= 6.0
    ):

        hard_deadman = True

        hard_deadman_reason = (
            f"Credit Crisis / HY_OAS "
            f"{hy_level:.2f}%"
        )

    elif macro_narrative == "CREDIT_STRESS":

        hard_deadman = True

        hard_deadman_reason = (
            "Structural Credit Stress"
        )

    elif (
        macro_narrative
        == "STAGFLATION_RISK"
        and cross_asset_tape.get(
            "VIX_Z",
            0,
        ) >= 3
    ):

        hard_deadman = True

        hard_deadman_reason = (
            "Stagflation Shock + "
            "Volatility Spike"
        )

    elif (
        vix_today is not None
        and vix_today >= 30
    ):

        hard_deadman = True

        hard_deadman_reason = (
            f"VIX Panic ({vix_today:.2f})"
        )

    elif abs(pos_z) > 2.0:

        risk_compression = True

        compression_reason = (
            f"POS_Z Extreme ({pos_z:.2f})"
        )

    elif abs(pos_slope) > 0.5:

        risk_compression = True

        compression_reason = (
            f"Aggressive Slope "
            f"({pos_slope:.2f})"
        )


    # ========================================================
    # 1. VIX Convexity
    #
    # Production applies this directly to exposure first.
    # ========================================================

    before = exposure


    if (
        vix_today is not None
        and vix_pct is not None
    ):

        if (
            vix_today >= 20
            and vix_pct >= 10
        ):

            exposure *= 0.85

            drivers.append(
                "VIX_CONVEXITY_SHOCK"
            )

        elif (
            vix_today >= 18
            and vix_pct >= 5
        ):

            exposure *= 0.92

            drivers.append(
                "VIX_CONVEXITY_WARNING"
            )


    after_vix_convexity = exposure

    vix_convexity_delta = _delta(
        before,
        exposure,
    )


    # ========================================================
    # 2. VIX Regime Multiplier
    #
    # Build exact Production multiplier first.
    # ========================================================

    multiplier = 1.0


    if vix_today is not None:

        if vix_today < 14:

            multiplier *= 1.05

            drivers.append(
                "LOW_VIX"
            )

        elif vix_today < 20:

            pass

        elif vix_today < 30:

            multiplier *= 0.80

            drivers.append(
                "HIGH_VIX"
            )

        else:

            multiplier *= 0.60

            drivers.append(
                "EXTREME_VIX"
            )


    if vix_pct is not None:

        if vix_pct > 5:

            multiplier *= 0.85

            drivers.append(
                "VIX_SPIKE"
            )

        elif vix_pct < -5:

            multiplier *= 1.05

            drivers.append(
                "VIX_FALL"
            )


    before = exposure

    exposure *= multiplier

    after_vix_regime = exposure

    vix_regime_delta = _delta(
        before,
        exposure,
    )


    # ========================================================
    # 3. Positioning Heat / Unwind
    # ========================================================

    positioning_multiplier = 1.0


    if pos_z >= 2.0:

        positioning_multiplier *= 0.85

        drivers.append(
            "EXTREME_POSITIONING_HEAT"
        )

    elif pos_z >= 1.7:

        positioning_multiplier *= 0.90

        drivers.append(
            "ELEVATED_POSITIONING_HEAT"
        )

    elif pos_z >= 1.5:

        positioning_multiplier *= 0.95

        drivers.append(
            "POSITIONING_HEAT"
        )


    if (
        pos_z > 2.0
        and pos_slope < 0
    ):

        positioning_multiplier *= 1.05

        drivers.append(
            "POSITION_UNWIND"
        )


    before = exposure

    exposure *= positioning_multiplier

    after_positioning = exposure

    positioning_delta = _delta(
        before,
        exposure,
    )


    # ========================================================
    # 4. Gamma
    # ========================================================

    gamma_multiplier = 1.0


    if gamma < 0.5:

        gamma_multiplier *= 0.85

        drivers.append(
            "NEGATIVE_GAMMA"
        )

    elif gamma > 1.5:

        gamma_multiplier *= 1.03

        drivers.append(
            "POSITIVE_GAMMA"
        )


    before = exposure

    exposure *= gamma_multiplier

    after_gamma = exposure

    gamma_delta = _delta(
        before,
        exposure,
    )


    # ========================================================
    # 5. CTA
    # ========================================================

    cta_multiplier = 1.0


    if cta <= 0:

        cta_multiplier *= 0.90

        drivers.append(
            "BEARISH_CTA"
        )


    before = exposure

    exposure *= cta_multiplier

    after_cta = exposure

    cta_delta = _delta(
        before,
        exposure,
    )


    # ========================================================
    # IMPORTANT PRODUCTION ORDER CHECK
    #
    # Production does:
    #
    # exposure *= multiplier
    # exposure *= pos_multiplier
    #
    # where pos_multiplier already contains:
    # positioning + gamma + CTA.
    #
    # Sequential multiplication above is mathematically
    # identical and allows exact marginal attribution.
    # ========================================================


    # ========================================================
    # Leadership Breadth Offset
    #
    # Current Production modifies pos_multiplier AFTER
    # exposure has already been multiplied by it.
    #
    # Therefore current Production has ZERO numerical
    # exposure effect from this block.
    #
    # We record the trigger but assign zero attribution.
    # ========================================================

    leadership_score = float(
        market_data.get(
            "LEADERSHIP_BREADTH_SCORE",
            0,
        )
        or 0
    )

    credit_status = market_data.get(
        "HY_OAS_STATUS",
        "",
    )

    credit_calm = (
        credit_status
        in [
            "COOL",
            "CALM",
            "NORMAL",
        ]
    )


    leadership_offset_triggered = (
        leadership_score >= 6
        and credit_calm is True
        and pos_z >= 2.0
    )


    leadership_delta = 0.0


    if leadership_offset_triggered:

        drivers.append(
            "LEADERSHIP_BREADTH_OFFSET_NO_NUMERIC_EFFECT"
        )


    # ========================================================
    # 6. Credit Level
    # ========================================================

    before = exposure


    if hy_level is not None:

        if hy_level >= 6.0:

            drivers.append(
                "CREDIT_CRISIS"
            )

        elif hy_level >= 5.0:

            exposure *= 0.75

            drivers.append(
                "CREDIT_STRESS"
            )

        elif hy_level >= 4.0:

            exposure *= 0.90

            drivers.append(
                "MILD_CREDIT_STRESS"
            )


    after_credit_level = exposure

    credit_level_delta = _delta(
        before,
        exposure,
    )


    # ========================================================
    # 7. Credit Change
    # ========================================================

    before = exposure


    if hy_pct is not None:

        if hy_pct >= 10:

            exposure *= 0.85

            drivers.append(
                "HY_OAS_SPIKE"
            )

        elif hy_pct >= 5:

            exposure *= 0.93

            drivers.append(
                "HY_OAS_RISING"
            )


    after_credit_change = exposure

    credit_change_delta = _delta(
        before,
        exposure,
    )


    # ========================================================
    # 8. Hard Deadman Final Override
    # ========================================================

    before = exposure


    if hard_deadman:

        exposure = 0.0

        oracle_status = (
            "HARD_DEADMAN"
        )

    elif risk_compression:

        oracle_status = (
            "RISK_COMPRESSION"
        )

    else:

        oracle_status = (
            "NORMAL"
        )


    after_deadman = exposure

    hard_deadman_delta = _delta(
        before,
        exposure,
    )


    # ========================================================
    # 9. Production Clamp / Rounding
    # ========================================================

    before_clamp = exposure

    final_exposure = float(
        _clamp(exposure)
    )

    rounding_clamp_delta = _delta(
        before_clamp,
        final_exposure,
    )


    # ========================================================
    # Reconciliation
    # ========================================================

    total_signed_reduction = (
        float(start_exposure)
        - float(final_exposure)
    )


    attributed_signed_reduction = (
        vix_convexity_delta
        + vix_regime_delta
        + positioning_delta
        + gamma_delta
        + cta_delta
        + leadership_delta
        + credit_level_delta
        + credit_change_delta
        + hard_deadman_delta
        + rounding_clamp_delta
    )


    reconciliation_error = (
        total_signed_reduction
        - attributed_signed_reduction
    )


    return {

        # Inputs
        "risk_budget_13":
            start_exposure,

        "vix_today":
            vix_today,

        "vix_pct_change":
            vix_pct,

        "sp500_pos_z":
            pos_z,

        "pos_slope":
            pos_slope,

        "dealer_gamma_bias":
            gamma,

        "cta_momentum_score":
            cta,

        "hy_oas_today":
            hy_level,

        "hy_oas_pct_change":
            hy_pct,

        "macro_narrative":
            macro_narrative,

        "cross_asset_vix_z":
            cross_asset_tape.get(
                "VIX_Z"
            ),

        "leadership_breadth_score":
            leadership_score,

        "hy_oas_status":
            credit_status,


        # Intermediate exposure
        "after_vix_convexity":
            after_vix_convexity,

        "after_vix_regime":
            after_vix_regime,

        "after_positioning":
            after_positioning,

        "after_gamma":
            after_gamma,

        "after_cta":
            after_cta,

        "after_credit_level":
            after_credit_level,

        "after_credit_change":
            after_credit_change,

        "after_deadman":
            after_deadman,

        "before_clamp":
            before_clamp,

        "expected_exposure_15":
            final_exposure,


        # Attribution
        "vix_convexity_delta":
            vix_convexity_delta,

        "vix_regime_delta":
            vix_regime_delta,

        "positioning_delta":
            positioning_delta,

        "gamma_delta":
            gamma_delta,

        "cta_delta":
            cta_delta,

        "leadership_delta":
            leadership_delta,

        "credit_level_delta":
            credit_level_delta,

        "credit_change_delta":
            credit_change_delta,

        "hard_deadman_delta":
            hard_deadman_delta,

        "rounding_clamp_delta":
            rounding_clamp_delta,


        # Totals
        "total_signed_reduction":
            total_signed_reduction,

        "attributed_signed_reduction":
            attributed_signed_reduction,

        "reconciliation_error":
            reconciliation_error,


        # State
        "hard_deadman":
            hard_deadman,

        "hard_deadman_reason":
            hard_deadman_reason,

        "risk_compression":
            risk_compression,

        "compression_reason":
            compression_reason,

        "oracle_status":
            oracle_status,

        "leadership_offset_triggered":
            leadership_offset_triggered,

        "drivers":
            "|".join(
                drivers
            ),
    }


# ============================================================
# Main
# ============================================================

def main():

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    if not PANEL_PATH.exists():

        raise FileNotFoundError(
            PANEL_PATH
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
        .sort_values(
            "signal_date"
        )
        .reset_index(
            drop=True
        )
    )


    previous_flow_memory = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }


    rows = []

    total = len(panel)


    for row_index in range(total):

        row = panel.iloc[
            row_index
        ]

        signal_date = row[
            "signal_date"
        ]

        execution_date = row[
            "execution_date"
        ]


        # Rows without execution date are not part
        # of executable backtest attribution.
        if pd.isna(
            execution_date
        ):

            continue


        try:

            # =================================================
            # Historical PIT market_data
            # =================================================

            market_data = (
                build_market_data(
                    panel,
                    row_index,
                )
            )


            # =================================================
            # Validated Production Pre-13 Chain
            # =================================================

            previous_flow_memory = (
                prepare_filter13_execution_state(
                    market_data=market_data,
                    panel=panel,
                    row_index=row_index,
                    previous_flow_memory=(
                        previous_flow_memory
                    ),
                )
            )


            # =================================================
            # Actual Production Filter13
            # =================================================

            sf.narrative_engine_filter(
                market_data
            )


            # =================================================
            # Independent Filter15 attribution replay
            # =================================================

            replay = (
                replay_filter15_attribution(
                    dict(
                        market_data
                    )
                )
            )


            # =================================================
            # Actual Production Filter15
            # =================================================

            sf.volatility_controlled_exposure_filter(
                market_data
            )


            actual_exposure = _to_float(
                market_data.get(
                    "RECOMMENDED_EXPOSURE"
                )
            )


            expected_exposure = (
                replay[
                    "expected_exposure_15"
                ]
            )


            if actual_exposure is None:

                parity_error = None
                exact_match = False

            else:

                parity_error = (
                    float(
                        actual_exposure
                    )
                    - float(
                        expected_exposure
                    )
                )

                exact_match = (
                    float(
                        actual_exposure
                    )
                    == float(
                        expected_exposure
                    )
                )


            reconciliation_error = float(
                replay[
                    "reconciliation_error"
                ]
            )


            if (
                actual_exposure is None
            ):

                audit_status = (
                    "OUTPUT_FAIL"
                )

            elif not exact_match:

                audit_status = (
                    "PARITY_FAIL"
                )

            elif abs(
                reconciliation_error
            ) > 1e-9:

                audit_status = (
                    "RECONCILIATION_FAIL"
                )

            else:

                audit_status = (
                    "PASS"
                )


            rows.append(
                {
                    "signal_date":
                        signal_date,

                    "execution_date":
                        execution_date,

                    **replay,

                    "actual_exposure_15":
                        actual_exposure,

                    "parity_error":
                        parity_error,

                    "exact_match":
                        exact_match,

                    "audit_status":
                        audit_status,
                }
            )


        except Exception as exc:

            rows.append(
                {
                    "signal_date":
                        signal_date,

                    "execution_date":
                        execution_date,

                    "audit_status":
                        "ERROR",

                    "error_message":
                        repr(exc),
                }
            )


        if (
            (row_index + 1) % 250
            == 0
            or
            row_index + 1
            == total
        ):

            print(
                f"Processed "
                f"{row_index + 1}/"
                f"{total}"
            )


    # ========================================================
    # Daily Output
    # ========================================================

    result = pd.DataFrame(
        rows
    )


    result.to_csv(
        DAILY_OUT,
        index=False,
    )


    # ========================================================
    # Audit Gate
    # ========================================================

    pass_count = int(
        (
            result[
                "audit_status"
            ]
            == "PASS"
        ).sum()
    )


    parity_fail_count = int(
        (
            result[
                "audit_status"
            ]
            == "PARITY_FAIL"
        ).sum()
    )


    reconciliation_fail_count = int(
        (
            result[
                "audit_status"
            ]
            == "RECONCILIATION_FAIL"
        ).sum()
    )


    output_fail_count = int(
        (
            result[
                "audit_status"
            ]
            == "OUTPUT_FAIL"
        ).sum()
    )


    error_count = int(
        (
            result[
                "audit_status"
            ]
            == "ERROR"
        ).sum()
    )


    parity_errors = pd.to_numeric(
        result.get(
            "parity_error"
        ),
        errors="coerce",
    )


    reconciliation_errors = (
        pd.to_numeric(
            result.get(
                "reconciliation_error"
            ),
            errors="coerce",
        )
    )


    max_parity_error = (
        float(
            parity_errors
            .abs()
            .max()
        )
        if parity_errors.notna().any()
        else float("nan")
    )


    max_reconciliation_error = (
        float(
            reconciliation_errors
            .abs()
            .max()
        )
        if reconciliation_errors
        .notna()
        .any()
        else float("nan")
    )


    audit_pass = (
        parity_fail_count == 0
        and reconciliation_fail_count == 0
        and output_fail_count == 0
        and error_count == 0
        and max_parity_error == 0.0
        and max_reconciliation_error
        <= 1e-9
    )


    # ========================================================
    # Attribution Summary
    # ========================================================

    delta_columns = {
        "VIX_CONVEXITY":
            "vix_convexity_delta",

        "VIX_REGIME":
            "vix_regime_delta",

        "POSITIONING":
            "positioning_delta",

        "GAMMA":
            "gamma_delta",

        "CTA":
            "cta_delta",

        "LEADERSHIP_OFFSET":
            "leadership_delta",

        "CREDIT_LEVEL":
            "credit_level_delta",

        "CREDIT_CHANGE":
            "credit_change_delta",

        "HARD_DEADMAN":
            "hard_deadman_delta",

        "ROUNDING_CLAMP":
            "rounding_clamp_delta",
    }


    summary_rows = []


    for driver, column in (
        delta_columns.items()
    ):

        values = pd.to_numeric(
            result[column],
            errors="coerce",
        ).fillna(0.0)


        reduction_days = int(
            (
                values > 1e-12
            ).sum()
        )


        increase_days = int(
            (
                values < -1e-12
            ).sum()
        )


        total_signed = float(
            values.sum()
        )


        total_reduction_only = float(
            values[
                values > 0
            ].sum()
        )


        total_increase_only = float(
            -values[
                values < 0
            ].sum()
        )


        avg_signed = float(
            values.mean()
        )


        avg_when_active = (
            float(
                values[
                    values.abs()
                    > 1e-12
                ].mean()
            )
            if (
                values.abs()
                > 1e-12
            ).any()
            else 0.0
        )


        summary_rows.append(
            {
                "driver":
                    driver,

                "reduction_days":
                    reduction_days,

                "increase_days":
                    increase_days,

                "total_signed_exposure_points":
                    total_signed,

                "total_reduction_exposure_points":
                    total_reduction_only,

                "total_increase_exposure_points":
                    total_increase_only,

                "avg_signed_exposure_points_per_day":
                    avg_signed,

                "avg_signed_when_active":
                    avg_when_active,
            }
        )


    summary = pd.DataFrame(
        summary_rows
    )


    summary = (
        summary
        .sort_values(
            "total_reduction_exposure_points",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


    summary.to_csv(
        SUMMARY_OUT,
        index=False,
    )


    # ========================================================
    # Portfolio-level totals
    # ========================================================

    risk_budget_series = pd.to_numeric(
        result[
            "risk_budget_13"
        ],
        errors="coerce",
    )


    exposure_series = pd.to_numeric(
        result[
            "actual_exposure_15"
        ],
        errors="coerce",
    )


    total_filter15_signed_reduction = float(
        (
            risk_budget_series
            - exposure_series
        ).sum()
    )


    avg_risk_budget = float(
        risk_budget_series.mean()
    )


    avg_exposure = float(
        exposure_series.mean()
    )


    avg_filter15_reduction = float(
        (
            risk_budget_series
            - exposure_series
        ).mean()
    )


    hard_deadman_days = int(
        pd.Series(
            result[
                "hard_deadman"
            ]
        )
        .fillna(False)
        .astype(bool)
        .sum()
    )


    risk_compression_days = int(
        pd.Series(
            result[
                "risk_compression"
            ]
        )
        .fillna(False)
        .astype(bool)
        .sum()
    )


    # ========================================================
    # Audit TXT
    # ========================================================

    lines = []

    lines.append(
        "# FILTER15 EXPOSURE ATTRIBUTION AUDIT"
    )

    lines.append("")


    lines.append(
        f"Executable Rows        : "
        f"{len(result)}"
    )

    lines.append(
        f"PASS                   : "
        f"{pass_count}"
    )

    lines.append(
        f"PARITY FAIL            : "
        f"{parity_fail_count}"
    )

    lines.append(
        f"RECONCILIATION FAIL    : "
        f"{reconciliation_fail_count}"
    )

    lines.append(
        f"OUTPUT FAIL            : "
        f"{output_fail_count}"
    )

    lines.append(
        f"ERROR                  : "
        f"{error_count}"
    )


    lines.append("")


    lines.append(
        f"Max Parity Error       : "
        f"{max_parity_error}"
    )

    lines.append(
        f"Max Reconciliation Err : "
        f"{max_reconciliation_error}"
    )


    lines.append("")


    lines.append(
        f"Average Filter13 Budget: "
        f"{avg_risk_budget:.4f}"
    )

    lines.append(
        f"Average Filter15 Exp.  : "
        f"{avg_exposure:.4f}"
    )

    lines.append(
        f"Average 13->15 Change  : "
        f"{avg_filter15_reduction:.4f}"
    )

    lines.append(
        f"Total Signed Reduction : "
        f"{total_filter15_signed_reduction:.4f}"
    )


    lines.append("")


    lines.append(
        f"Hard Deadman Days      : "
        f"{hard_deadman_days}"
    )

    lines.append(
        f"Risk Compression Days  : "
        f"{risk_compression_days}"
    )


    lines.append("")

    lines.append(
        "Attribution:"
    )


    for _, row in (
        summary.iterrows()
    ):

        lines.append(
            f"- {row['driver']}: "
            f"reduction_days="
            f"{int(row['reduction_days'])}, "
            f"increase_days="
            f"{int(row['increase_days'])}, "
            f"total_reduction="
            f"{row['total_reduction_exposure_points']:.4f}, "
            f"total_increase="
            f"{row['total_increase_exposure_points']:.4f}, "
            f"net="
            f"{row['total_signed_exposure_points']:.4f}"
        )


    lines.append("")

    lines.append(
        "Production source modified: NO"
    )

    lines.append(
        "Future-data backfill: NO"
    )

    lines.append(
        "Attribution order: "
        "Production execution order"
    )


    lines.append("")


    if audit_pass:

        lines.append(
            "RESULT: "
            "FILTER15 ATTRIBUTION AUDIT PASS"
        )

        lines.append(
            "FILTER15 ATTRIBUTION: VALIDATED"
        )

    else:

        lines.append(
            "RESULT: "
            "FILTER15 ATTRIBUTION AUDIT FAIL"
        )

        lines.append(
            "FILTER15 ATTRIBUTION: OPEN"
        )


    text = "\n".join(
        lines
    )


    TXT_OUT.write_text(
        text,
        encoding="utf-8",
    )


    # ========================================================
    # Console
    # ========================================================

    print()

    print(
        text
    )

    print()

    print(
        "===== ATTRIBUTION SUMMARY ====="
    )

    print(
        summary.to_string(
            index=False
        )
    )

    print()

    print(
        f"Saved: {DAILY_OUT}"
    )

    print(
        f"Saved: {SUMMARY_OUT}"
    )

    print(
        f"Saved: {TXT_OUT}"
    )


    if not audit_pass:

        bad = result[
            result[
                "audit_status"
            ]
            != "PASS"
        ]

        if not bad.empty:

            print()

            print(
                "===== FIRST FAILURES ====="
            )

            print(
                bad.head(
                    20
                ).to_string(
                    index=False
                )
            )


if __name__ == "__main__":
    main()