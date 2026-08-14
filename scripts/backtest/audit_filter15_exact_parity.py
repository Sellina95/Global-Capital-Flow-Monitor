from __future__ import annotations

"""
Filter15 Production <-> Backtest Exact Parity Audit

Purpose
-------
Independently reproduce the numerical exposure calculation of:

    filters.strategist_filters.volatility_controlled_exposure_filter

using the SAME historical PIT market_data supplied to Production Filter15,
then compare:

    independent_expected_exposure
        vs
    market_data["RECOMMENDED_EXPOSURE"]

Audit principles
----------------
- Production source is READ ONLY.
- No future data is used.
- No historical inputs are backfilled.
- Initial warm-up observations are explicitly separated.
- Rows without an execution_date are NON_EXECUTABLE.
- The independent oracle does NOT call Production Filter15 internally.

PASS criterion
--------------
For the mature executable universe:

    expected_exposure == actual_exposure

with:

    PARITY_FAIL   = 0
    CONTRACT_FAIL = 0
    OUTPUT_FAIL   = 0
    ERROR         = 0
    Max Absolute Error = 0.0
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
    / "filter15_exact_parity_daily.csv"
)

TXT_OUT = (
    RESULT_DIR
    / "filter15_exact_parity_audit.txt"
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
    Exact Production Filter15 behavior:

        max(lo, min(int(round(x)), hi))
    """
    return max(
        lo,
        min(
            int(round(x)),
            hi,
        ),
    )


# ============================================================
# Independent Filter15 Oracle
# ============================================================

def independent_filter15_oracle(
    market_data: dict[str, Any],
) -> dict[str, Any]:

    # --------------------------------------------------------
    # Exact Production input/fallback contract
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


    # Production reads this although the current numerical
    # exposure logic does not directly use flow_score.
    flow = (
        market_data.get(
            "INSTITUTIONAL_FLOW",
            {},
        )
        or {}
    )

    flow_score = flow.get(
        "score",
        0,
    )

    try:
        flow_score = int(flow_score)
    except Exception:
        flow_score = 0


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


    exposure = float(risk_budget)

    hard_deadman = False
    hard_deadman_reason = ""

    risk_compression = False
    compression_reason = ""

    drivers = []


    # ========================================================
    # 0. Hard Deadman / Soft Compression
    # ========================================================

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

        drivers.append(
            "EXTREME_POSITIONING_HEAT"
        )

    elif abs(pos_slope) > 0.5:

        risk_compression = True

        compression_reason = (
            f"Aggressive Slope "
            f"({pos_slope:.2f})"
        )

        drivers.append(
            "AGGRESSIVE_POSITIONING_SLOPE"
        )


    # ========================================================
    # 1. VIX Regime
    # ========================================================

    multiplier = 1.0

    if vix_today is not None:

        if vix_today < 14:

            multiplier *= 1.05
            drivers.append("LOW_VIX")

        elif vix_today < 20:

            pass

        elif vix_today < 30:

            multiplier *= 0.80
            drivers.append("HIGH_VIX")

        else:

            multiplier *= 0.60
            drivers.append("EXTREME_VIX")


    if vix_pct is not None:

        if vix_pct > 5:

            multiplier *= 0.85
            drivers.append("VIX_SPIKE")

        elif vix_pct < -5:

            multiplier *= 1.05
            drivers.append("VIX_FALL")


    # Production applies convexity directly to exposure
    # before applying multiplier and pos_multiplier.

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


    # ========================================================
    # 2. Positioning
    # ========================================================

    pos_multiplier = 1.0

    if pos_z >= 2.0:

        pos_multiplier *= 0.85

        if (
            "EXTREME_POSITIONING_HEAT"
            not in drivers
        ):
            drivers.append(
                "EXTREME_POSITIONING_HEAT"
            )

    elif pos_z >= 1.7:

        pos_multiplier *= 0.90

        drivers.append(
            "ELEVATED_POSITIONING_HEAT"
        )

    elif pos_z >= 1.5:

        pos_multiplier *= 0.95

        drivers.append(
            "POSITIONING_HEAT"
        )


    if (
        pos_z > 2.0
        and pos_slope < 0
    ):

        pos_multiplier *= 1.05

        drivers.append(
            "POSITION_UNWIND"
        )


    # ========================================================
    # 3. Gamma Environment
    # ========================================================

    if gamma < 0.5:

        pos_multiplier *= 0.85

        drivers.append(
            "NEGATIVE_GAMMA"
        )

    elif gamma > 1.5:

        pos_multiplier *= 1.03

        drivers.append(
            "POSITIVE_GAMMA"
        )


    # ========================================================
    # 4. CTA
    # ========================================================

    if cta <= 0:

        pos_multiplier *= 0.90

        drivers.append(
            "BEARISH_CTA"
        )


    # Exact Production application order

    exposure *= multiplier
    exposure *= pos_multiplier


    exposure_after_vol_positioning = (
        exposure
    )


    # ========================================================
    # Leadership Breadth Offset
    #
    # IMPORTANT:
    # This intentionally reproduces CURRENT Production.
    #
    # Production changes pos_multiplier AFTER exposure has
    # already been multiplied by pos_multiplier.
    #
    # Therefore the offset currently does not change exposure.
    # Do NOT fix this inside a parity audit.
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

    leadership_offset_triggered = False

    if (
        leadership_score >= 6
        and credit_calm is True
        and pos_z >= 2.0
    ):

        pos_multiplier *= 1.05

        leadership_offset_triggered = True

        drivers.append(
            "LEADERSHIP_BREADTH_OFFSET"
        )


    # ========================================================
    # 5. Credit Layer
    # ========================================================

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


    exposure_before_override = (
        exposure
    )


    # ========================================================
    # 6. Confidence Scaling
    # ========================================================

    confidence_multiplier = 1.00


    # ========================================================
    # 7. Final Override
    # ========================================================

    if hard_deadman:

        exposure = 0

        status = "HARD_DEADMAN"

    elif risk_compression:

        status = "RISK_COMPRESSION"

    else:

        status = "NORMAL"


    expected_exposure = _clamp(
        exposure
    )


    return {
        "expected_exposure":
            expected_exposure,

        "risk_budget":
            risk_budget,

        "flow_score":
            flow_score,

        "vix_multiplier":
            multiplier,

        "positioning_multiplier":
            pos_multiplier,

        "confidence_multiplier":
            confidence_multiplier,

        "exposure_after_vol_positioning":
            exposure_after_vol_positioning,

        "exposure_before_override":
            exposure_before_override,

        "hard_deadman":
            hard_deadman,

        "hard_deadman_reason":
            hard_deadman_reason,

        "risk_compression":
            risk_compression,

        "compression_reason":
            compression_reason,

        "leadership_offset_triggered":
            leadership_offset_triggered,

        "status":
            status,

        "drivers":
            "|".join(drivers),
    }


# ============================================================
# Contract Audit
# ============================================================

WARMUP_FIELDS = {
    "VIX.pct_change",
    "SP500_POS_Z",
    "HY_OAS.pct_change",
    "CROSS_ASSET_TAPE.VIX_Z",
}


def missing_contract(
    market_data: dict[str, Any],
) -> list[str]:

    missing = []


    vix = (
        market_data.get(
            "VIX",
            {},
        )
        or {}
    )

    hy = (
        market_data.get(
            "HY_OAS",
            {},
        )
        or {}
    )

    tape = (
        market_data.get(
            "CROSS_ASSET_TAPE",
            {},
        )
        or {}
    )

    flow = (
        market_data.get(
            "INSTITUTIONAL_FLOW",
            {},
        )
        or {}
    )


    checks = {
        "RISK_BUDGET":
            market_data.get(
                "RISK_BUDGET"
            ),

        "VIX.today":
            vix.get("today"),

        "VIX.pct_change":
            vix.get("pct_change"),

        "SP500_POS_Z":
            market_data.get(
                "SP500_POS_Z"
            ),

        "POS_SLOPE":
            market_data.get(
                "POS_SLOPE"
            ),

        "DEALER_GAMMA_BIAS":
            market_data.get(
                "DEALER_GAMMA_BIAS"
            ),

        "CTA_MOMENTUM_SCORE":
            market_data.get(
                "CTA_MOMENTUM_SCORE"
            ),

        "HY_OAS.today":
            hy.get("today"),

        "HY_OAS.pct_change":
            hy.get("pct_change"),

        "INSTITUTIONAL_FLOW.score":
            flow.get(
                "score"
            ),

        "MACRO_NARRATIVE":
            market_data.get(
                "MACRO_NARRATIVE"
            ),

        "CROSS_ASSET_TAPE.VIX_Z":
            tape.get(
                "VIX_Z"
            ),

        "LEADERSHIP_BREADTH_SCORE":
            market_data.get(
                "LEADERSHIP_BREADTH_SCORE"
            ),
    }


    for name, value in checks.items():

        if value is None:

            missing.append(name)


    return missing


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
        .sort_values("signal_date")
        .reset_index(drop=True)
    )


    rows = []


    previous_flow_memory = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }


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


        try:

            # =================================================
            # 1. Historical PIT market_data
            # =================================================

            market_data = (
                build_market_data(
                    panel,
                    row_index,
                )
            )


            # =================================================
            # 2. Production Pre-Filter13 execution chain
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
            # 3. Actual Production Filter13
            # =================================================

            sf.narrative_engine_filter(
                market_data
            )


            # =================================================
            # 4. Contract snapshot BEFORE Filter15
            # =================================================

            missing = missing_contract(
                market_data
            )


            # =================================================
            # 5. Independent Filter15 Oracle
            # =================================================

            oracle = (
                independent_filter15_oracle(
                    dict(market_data)
                )
            )

            expected = oracle[
                "expected_exposure"
            ]


            # =================================================
            # 6. Actual Production Filter15
            # =================================================

            sf.volatility_controlled_exposure_filter(
                market_data
            )


            actual = _to_float(
                market_data.get(
                    "RECOMMENDED_EXPOSURE"
                )
            )


            # =================================================
            # 7. Exact comparison
            # =================================================

            if actual is None:

                error = None
                exact_match = False

            else:

                error = (
                    float(actual)
                    - float(expected)
                )

                exact_match = (
                    float(actual)
                    == float(expected)
                )


            # =================================================
            # 8. Universe / Contract Classification
            # =================================================

            unexpected_missing = [
                name
                for name in missing
                if name not in WARMUP_FIELDS
            ]


            initial_warmup = (
                bool(missing)
                and not unexpected_missing
                and row_index <= 30
            )


            # -------------------------------------------------
            # IMPORTANT:
            #
            # execution_date missing means there is no
            # executable backtest observation.
            #
            # It must not be treated as a mature parity failure.
            # -------------------------------------------------

            if pd.isna(
                execution_date
            ):

                parity_status = (
                    "NON_EXECUTABLE"
                )

            elif initial_warmup:

                parity_status = (
                    "EXPECTED_WARMUP"
                )

            elif unexpected_missing:

                parity_status = (
                    "CONTRACT_FAIL"
                )

            elif missing:

                parity_status = (
                    "CONTRACT_FAIL"
                )

            elif actual is None:

                parity_status = (
                    "OUTPUT_FAIL"
                )

            elif exact_match:

                parity_status = (
                    "PASS"
                )

            else:

                parity_status = (
                    "PARITY_FAIL"
                )


            rows.append(
                {
                    "signal_date":
                        signal_date,

                    "execution_date":
                        execution_date,

                    "risk_budget_13":
                        market_data.get(
                            "RISK_BUDGET"
                        ),

                    "expected_exposure_15":
                        expected,

                    "actual_exposure_15":
                        actual,

                    "parity_error":
                        error,

                    "exact_match":
                        exact_match,

                    "status":
                        parity_status,

                    "missing_required_inputs":
                        "|".join(
                            missing
                        ),

                    "oracle_status":
                        oracle[
                            "status"
                        ],

                    "hard_deadman":
                        oracle[
                            "hard_deadman"
                        ],

                    "hard_deadman_reason":
                        oracle[
                            "hard_deadman_reason"
                        ],

                    "risk_compression":
                        oracle[
                            "risk_compression"
                        ],

                    "compression_reason":
                        oracle[
                            "compression_reason"
                        ],

                    "vix_multiplier":
                        oracle[
                            "vix_multiplier"
                        ],

                    "positioning_multiplier":
                        oracle[
                            "positioning_multiplier"
                        ],

                    "leadership_offset_triggered":
                        oracle[
                            "leadership_offset_triggered"
                        ],

                    "drivers":
                        oracle[
                            "drivers"
                        ],
                }
            )


        except Exception as exc:

            rows.append(
                {
                    "signal_date":
                        signal_date,

                    "execution_date":
                        execution_date,

                    "risk_budget_13":
                        None,

                    "expected_exposure_15":
                        None,

                    "actual_exposure_15":
                        None,

                    "parity_error":
                        None,

                    "exact_match":
                        False,

                    "status":
                        "ERROR",

                    "missing_required_inputs":
                        "",

                    "oracle_status":
                        "",

                    "hard_deadman":
                        False,

                    "hard_deadman_reason":
                        "",

                    "risk_compression":
                        False,

                    "compression_reason":
                        "",

                    "vix_multiplier":
                        None,

                    "positioning_multiplier":
                        None,

                    "leadership_offset_triggered":
                        False,

                    "drivers":
                        "",

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
    # Save Daily
    # ========================================================

    result = pd.DataFrame(
        rows
    )


    result.to_csv(
        DAILY_OUT,
        index=False,
    )


    # ========================================================
    # Summary Counts
    # ========================================================

    pass_count = int(
        (
            result["status"]
            == "PASS"
        ).sum()
    )


    warmup_count = int(
        (
            result["status"]
            == "EXPECTED_WARMUP"
        ).sum()
    )


    non_executable_count = int(
        (
            result["status"]
            == "NON_EXECUTABLE"
        ).sum()
    )


    parity_fail_count = int(
        (
            result["status"]
            == "PARITY_FAIL"
        ).sum()
    )


    contract_fail_count = int(
        (
            result["status"]
            == "CONTRACT_FAIL"
        ).sum()
    )


    output_fail_count = int(
        (
            result["status"]
            == "OUTPUT_FAIL"
        ).sum()
    )


    error_count = int(
        (
            result["status"]
            == "ERROR"
        ).sum()
    )


    # ========================================================
    # Mature executable universe ONLY
    # ========================================================

    mature = result[
        ~result["status"].isin(
            [
                "EXPECTED_WARMUP",
                "NON_EXECUTABLE",
            ]
        )
    ].copy()


    errors = pd.to_numeric(
        mature[
            "parity_error"
        ],
        errors="coerce",
    )


    if errors.notna().any():

        max_abs_error = float(
            errors.abs().max()
        )

    else:

        max_abs_error = float(
            "nan"
        )


    exact_mismatch_count = int(
        (
            mature[
                "exact_match"
            ]
            == False
        ).sum()
    )


    # ========================================================
    # Final Release Gate
    # ========================================================

    closed = (
        parity_fail_count
        == 0

        and contract_fail_count
        == 0

        and output_fail_count
        == 0

        and error_count
        == 0

        and exact_mismatch_count
        == 0

        and max_abs_error
        == 0.0
    )


    # ========================================================
    # Audit Text
    # ========================================================

    lines = []

    lines.append(
        "# FILTER15 EXACT PARITY AUDIT"
    )

    lines.append("")


    lines.append(
        f"Rows                 : "
        f"{len(result)}"
    )

    lines.append(
        f"PASS                 : "
        f"{pass_count}"
    )

    lines.append(
        f"EXPECTED WARMUP      : "
        f"{warmup_count}"
    )

    lines.append(
        f"NON EXECUTABLE       : "
        f"{non_executable_count}"
    )

    lines.append(
        f"PARITY FAIL          : "
        f"{parity_fail_count}"
    )

    lines.append(
        f"CONTRACT FAIL        : "
        f"{contract_fail_count}"
    )

    lines.append(
        f"OUTPUT FAIL          : "
        f"{output_fail_count}"
    )

    lines.append(
        f"ERROR                : "
        f"{error_count}"
    )


    lines.append("")


    lines.append(
        f"Mature Exact Mismatch: "
        f"{exact_mismatch_count}"
    )

    lines.append(
        f"Max Absolute Error   : "
        f"{max_abs_error}"
    )


    lines.append("")


    lines.append(
        "Production Filter15:"
    )

    lines.append(
        "filters.strategist_filters."
        "volatility_controlled_exposure_filter"
    )


    lines.append("")


    lines.append(
        "Independent Oracle:"
    )

    lines.append(
        "audit_filter15_exact_parity.py"
    )


    lines.append("")


    lines.append(
        "Production source modified: NO"
    )

    lines.append(
        "Future-data backfill: NO"
    )


    lines.append("")


    if closed:

        lines.append(
            "RESULT: "
            "FILTER15 EXACT PARITY PASS"
        )

        lines.append(
            "FILTER15 PARITY: CLOSED"
        )

    else:

        lines.append(
            "RESULT: "
            "FILTER15 EXACT PARITY FAIL"
        )

        lines.append(
            "FILTER15 PARITY: OPEN"
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
        f"Saved: {DAILY_OUT}"
    )

    print(
        f"Saved: {TXT_OUT}"
    )


    # ========================================================
    # Genuine failures ONLY
    # ========================================================

    if not closed:

        bad = result[
            ~result[
                "status"
            ].isin(
                [
                    "PASS",
                    "EXPECTED_WARMUP",
                    "NON_EXECUTABLE",
                ]
            )
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