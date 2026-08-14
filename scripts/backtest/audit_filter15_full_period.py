from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# Paths / Imports
# ============================================================

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
from scripts.backtest.institutional_backtest import (
    disable_live_side_effects,
    neutralize_all_side_effects,
)


DATA_DIR = ROOT / "data" / "backtest"
PANEL_PATH = DATA_DIR / "master_panel.csv"

RESULT_DIR = DATA_DIR / "results"
DAILY_OUT = RESULT_DIR / "filter15_full_period_audit.csv"
SUMMARY_OUT = RESULT_DIR / "filter15_full_period_audit.txt"


# ============================================================
# Helpers
# ============================================================

def _nested(
    obj: Any,
    *keys: str,
    default=None,
):
    current = obj

    for key in keys:
        if not isinstance(current, dict):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current


def _is_present(value: Any) -> bool:
    if value is None:
        return False

    try:
        if pd.isna(value):
            return False
    except Exception:
        pass

    return True


# ============================================================
# Main Audit
# ============================================================

def main() -> None:

    if not PANEL_PATH.exists():
        raise FileNotFoundError(
            f"master_panel not found: {PANEL_PATH}"
        )

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    # --------------------------------------------------------
    # PIT ordering gate
    # --------------------------------------------------------

    if not panel["signal_date"].is_monotonic_increasing:
        raise RuntimeError(
            "PIT FAIL: signal_date is not monotonic increasing."
        )

    mask = (
        panel["execution_date"].notna()
        & pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    )

    indices = panel.index[mask].tolist()

    if not indices:
        raise RuntimeError(
            "No executable historical rows found."
        )

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows: list[dict[str, Any]] = []

    previous_exposure = 50.0

    flow_memory: dict[str, Any] = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    # --------------------------------------------------------
    # Historical loop
    # --------------------------------------------------------

    for count, idx in enumerate(indices, start=1):

        source_row = panel.loc[idx]

        market_data = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=previous_exposure,
        )

        flow_memory = prepare_filter13_execution_state(
            market_data=market_data,
            panel=panel,
            row_index=idx,
            previous_flow_memory=flow_memory,
        )

        disable_live_side_effects(previous_exposure)
        neutralize_all_side_effects(previous_exposure)

        try:

            # ------------------------------------------------
            # Production Filter13
            # ------------------------------------------------

            with contextlib.redirect_stdout(io.StringIO()):
                sf.narrative_engine_filter(
                    market_data
                )

            risk_budget = market_data.get(
                "RISK_BUDGET"
            )

            # ------------------------------------------------
            # Capture exact Filter15 inputs BEFORE execution
            # ------------------------------------------------

            vix_today = _nested(
                market_data,
                "VIX",
                "today",
            )

            vix_pct = _nested(
                market_data,
                "VIX",
                "pct_change",
            )

            pos_z = market_data.get(
                "SP500_POS_Z"
            )

            pos_slope = market_data.get(
                "POS_SLOPE"
            )

            gamma = market_data.get(
                "DEALER_GAMMA_BIAS"
            )

            cta = market_data.get(
                "CTA_MOMENTUM_SCORE"
            )

            hy_today = _nested(
                market_data,
                "HY_OAS",
                "today",
            )

            hy_pct = _nested(
                market_data,
                "HY_OAS",
                "pct_change",
            )

            macro_narrative = market_data.get(
                "MACRO_NARRATIVE"
            )

            vix_z = _nested(
                market_data,
                "CROSS_ASSET_TAPE",
                "VIX_Z",
            )

            leadership_score = market_data.get(
                "LEADERSHIP_BREADTH_SCORE"
            )

            hy_status = market_data.get(
                "HY_OAS_STATUS"
            )

            # ------------------------------------------------
            # Production Filter15 — DIRECT CALL
            # ------------------------------------------------

            with contextlib.redirect_stdout(io.StringIO()):
                report = sf.volatility_controlled_exposure_filter(
                    market_data
                )

            exposure = market_data.get(
                "RECOMMENDED_EXPOSURE"
            )

            sew_status = market_data.get(
                "SEW_STATUS"
            )

            # ------------------------------------------------
            # Contract checks
            # ------------------------------------------------

            required_values = {
                "RISK_BUDGET": risk_budget,
                "VIX.today": vix_today,
                "VIX.pct_change": vix_pct,
                "SP500_POS_Z": pos_z,
                "POS_SLOPE": pos_slope,
                "DEALER_GAMMA_BIAS": gamma,
                "CTA_MOMENTUM_SCORE": cta,
                "HY_OAS.today": hy_today,
                "HY_OAS.pct_change": hy_pct,
                "MACRO_NARRATIVE": macro_narrative,
                "CROSS_ASSET_TAPE.VIX_Z": vix_z,
                "LEADERSHIP_BREADTH_SCORE": leadership_score,
            }

            missing = [
                name
                for name, value in required_values.items()
                if not _is_present(value)
            ]

            # HY_OAS_STATUS is intentionally NOT required.
            # Current Production Filter15 reads:
            #
            # market_data.get("HY_OAS_STATUS", "")
            #
            # and no top-level Production writer was found.
            # Therefore absence == Production fallback behavior.

            # ------------------------------------------------
            # Contract classification
            #
            # Historical warm-up is NOT a parity failure:
            #
            # - SP500_POS_Z requires 21 observations
            #   (rebuild_positioning_backtest.py:
            #    MIN_Z_PERIODS = 21)
            #
            # - CROSS_ASSET_TAPE.VIX_Z requires historical
            #   observations before a z-score can be produced.
            #
            # - pct_change is naturally unavailable on the
            #   first historical observation.
            #
            # Never backfill these fields with future data.
            # ------------------------------------------------

            warmup_allowed = {
                "VIX.pct_change",
                "SP500_POS_Z",
                "HY_OAS.pct_change",
                "CROSS_ASSET_TAPE.VIX_Z",
            }

            unexpected_missing = [
                name
                for name in missing
                if name not in warmup_allowed
            ]

            is_initial_warmup = (
                bool(missing)
                and not unexpected_missing
                and count <= 21
            )

            if not _is_present(exposure):
                status = "FAIL"

            elif unexpected_missing:
                status = "FAIL"

            elif is_initial_warmup:
                status = "EXPECTED_WARMUP"

            elif missing:
                # A warm-up-type field missing AFTER the
                # initial warm-up window is unexpected.
                status = "FAIL"

            else:
                status = "PASS"

            rows.append({
                "signal_date": market_data.get(
                    "SIGNAL_DATE",
                    source_row.get("signal_date"),
                ),
                "execution_date": market_data.get(
                    "EXECUTION_DATE",
                    source_row.get("execution_date"),
                ),

                "risk_budget_13": risk_budget,
                "exposure_15": exposure,

                "vix_today": vix_today,
                "vix_pct_change": vix_pct,

                "sp500_pos_z": pos_z,
                "pos_slope": pos_slope,

                "dealer_gamma_bias": gamma,
                "cta_momentum_score": cta,

                "hy_oas_today": hy_today,
                "hy_oas_pct_change": hy_pct,

                "macro_narrative": macro_narrative,
                "cross_asset_vix_z": vix_z,

                "leadership_breadth_score": leadership_score,

                "hy_oas_status": (
                    hy_status
                    if hy_status is not None
                    else ""
                ),

                "hy_oas_status_contract": (
                    "PRESENT"
                    if hy_status is not None
                    else "EXPECTED_PRODUCTION_FALLBACK"
                ),

                "sew_status": sew_status,

                "missing_required_inputs": (
                    "|".join(missing)
                ),

                "filter15_report_generated": bool(report),

                "status": status,
                "error": "",
            })

            if exposure is not None:
                previous_exposure = float(
                    exposure
                )

        except Exception as exc:

            rows.append({
                "signal_date": source_row.get(
                    "signal_date"
                ),
                "execution_date": source_row.get(
                    "execution_date"
                ),
                "risk_budget_13": market_data.get(
                    "RISK_BUDGET"
                ),
                "exposure_15": market_data.get(
                    "RECOMMENDED_EXPOSURE"
                ),
                "status": "ERROR",
                "error": (
                    f"{type(exc).__name__}: {exc}"
                ),
            })

        print(
            f"\rProcessed {count}/{len(indices)}",
            end="",
            flush=True,
        )

    print()

    # ========================================================
    # Results
    # ========================================================

    result = pd.DataFrame(rows)

    result.to_csv(
        DAILY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    total = len(result)

    pass_count = int(
        (result["status"] == "PASS").sum()
    )

    warmup_count = int(
        (result["status"] == "EXPECTED_WARMUP").sum()
    )

    fail_count = int(
        (result["status"] == "FAIL").sum()
    )

    error_count = int(
        (result["status"] == "ERROR").sum()
    )

    exposure_missing = int(
        result["exposure_15"].isna().sum()
    )

    # Only unexpected missing contracts count as failures.
    # EXPECTED_WARMUP is reported separately.
    missing_contract_days = int(
        (
            (result["status"] == "FAIL")
            & result.get(
                "missing_required_inputs",
                pd.Series("", index=result.index),
            )
            .fillna("")
            .ne("")
        ).sum()
    )

    # --------------------------------------------------------
    # Basic exposure sanity
    # --------------------------------------------------------

    exposure_numeric = pd.to_numeric(
        result["exposure_15"],
        errors="coerce",
    )

    below_zero = int(
        (exposure_numeric < 0).sum()
    )

    above_100 = int(
        (exposure_numeric > 100).sum()
    )

    # ========================================================
    # Summary
    # ========================================================

    lines = []

    lines.append(
        "=" * 72
    )
    lines.append(
        "FILTER15 FULL-PERIOD PRODUCTION EXECUTION AUDIT"
    )
    lines.append(
        "=" * 72
    )

    lines.append("")
    lines.append(
        f"Rows                 : {total}"
    )
    lines.append(
        f"PASS                 : {pass_count}"
    )
    lines.append(
        f"EXPECTED WARMUP      : {warmup_count}"
    )
    lines.append(
        f"FAIL                 : {fail_count}"
    )
    lines.append(
        f"ERROR                : {error_count}"
    )

    lines.append("")
    lines.append(
        f"Missing Exposure      : {exposure_missing}"
    )
    lines.append(
        f"Missing Contract Days : {missing_contract_days}"
    )
    lines.append(
        f"Exposure < 0          : {below_zero}"
    )
    lines.append(
        f"Exposure > 100        : {above_100}"
    )

    lines.append("")
    lines.append(
        "HY_OAS_STATUS         : EXPECTED_PRODUCTION_FALLBACK"
    )

    lines.append("")
    lines.append(
        "Production Filter15 function:"
    )
    lines.append(
        "filters.strategist_filters."
        "volatility_controlled_exposure_filter"
    )

    lines.append("")
    lines.append(
        "Production source modified: NO"
    )

    lines.append("")

    if (
        fail_count == 0
        and error_count == 0
        and exposure_missing == 0
        and missing_contract_days == 0
        and below_zero == 0
        and above_100 == 0
    ):
        lines.append(
            "RESULT: FULL-PERIOD EXECUTION PASS"
        )
    else:
        lines.append(
            "RESULT: FULL-PERIOD EXECUTION FAIL"
        )

    lines.append("")
    lines.append(
        "NOTE:"
    )
    lines.append(
        "PASS proves that the historical Backtest execution chain"
    )
    lines.append(
        "can supply the required Filter15 contract and execute the"
    )
    lines.append(
        "Production Filter15 function across the full period."
    )
    lines.append(
        "It does not by itself prove independent output parity."
    )

    summary = "\n".join(lines)

    SUMMARY_OUT.write_text(
        summary,
        encoding="utf-8",
    )

    print(summary)

    print()
    print(f"Saved: {DAILY_OUT}")
    print(f"Saved: {SUMMARY_OUT}")


if __name__ == "__main__":
    main()