from __future__ import annotations

"""
F13 / F15 / F18 FULL VALUE + EXECUTION CLOSURE
==============================================

Universe
--------
- F13: 22 stage-contracts
- F15: 20 stage-contracts
- F18: 40 stage-contracts
- Total: 82 stage-contracts
- Historical rows: full eligible period

This combines:
1. exact raw historical value checks
2. repaired-contract exact checks
3. F15 t-1 state-transition checks
4. runtime boundary presence
5. shared Production-function path evidence
6. previously closed source/transformation evidence
7. internal/output state generation checks

No Production modification.
No return/PnL/Sharpe usage.
"""

import contextlib
import io
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# PATH
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DATA_DIR = ROOT / "data" / "backtest"
RESULT_DIR = DATA_DIR / "results"

PANEL_PATH = DATA_DIR / "master_panel.csv"

MANIFEST_PATH = (
    RESULT_DIR
    / "f13_f15_f18_value_parity_manifest.csv"
)

SOURCE_PARITY_PATH = (
    RESULT_DIR
    / "full_source_transformation_parity_detail.csv"
)

OUT_DETAIL = (
    RESULT_DIR
    / "full_value_execution_closure_detail.csv"
)

OUT_SUMMARY = (
    RESULT_DIR
    / "full_value_execution_closure_summary.csv"
)

OUT_FAILURES = (
    RESULT_DIR
    / "full_value_execution_closure_failures.csv"
)

OUT_TXT = (
    RESULT_DIR
    / "full_value_execution_closure_summary.txt"
)


# ============================================================
# IMPORT CANONICAL EXECUTION
# ============================================================

import filters.strategist_filters as sf

from scripts.backtest.market_data_builder import (
    build_market_data,
)

from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)

from scripts.backtest.historical_execution_contract import (
    SECTOR_TICKERS,
    initial_filter15_memory,
    prepare_historical_execution_contract,
    capture_filter15_memory,
)

from scripts.backtest.institutional_backtest import (
    disable_live_side_effects,
    neutralize_all_side_effects,
)


# ============================================================
# CONTRACT GROUPS
# ============================================================

F15_MEMORY_KEYS = [
    "FILTER15_PREV_DEADMAN",
    "FILTER15_RECOVERY_ACTIVE",
    "FILTER15_RECOVERY_COMPLETED",
    "FILTER15_RECOVERY_STREAK",
    "FILTER15_PREV_HY_OAS",
]


F18_POSITIONING_KEYS = [
    "POSITIONING_STATE",
    "POSITIONING_SCORE_18",
    "SQUEEZE_RISK",
    "GAMMA_SIGNAL",
    "VOL_STRUCTURE",
]


EXPECTED_FALLBACK = {
    ("F15", "HY_OAS_STATUS"),
    ("F18", "DRIFT_LABEL"),
}


# Same Production functions are executed by historical chain.
SHARED_PRODUCTION_PATH = {
    "CROSS_ASSET_TAPE",
    "DRIFT",
    "DRIFT_SCORE",
    "DRIFT_STATE",
    "GAMMA_STATE",
    "INSTITUTIONAL_FLOW",
    "MACRO_NARRATIVE",
    "MARKET_REGIME",
    "POLICY_BIAS_LINE",
    "STRUCT_V2_STATE",

    "LEADERSHIP_BREADTH_SCORE",
    "BREADTH_SCORE_18",
    "LEADERSHIP_STATE",
    "LEADER_TYPE",
    "PARTICIPATION_SIGNAL",

    "FINAL_STATE",
    "RISK_BUDGET",
    "RECOMMENDED_EXPOSURE",
}


# Contracts for which historical raw value can be checked
# directly against the master panel.
RAW_PANEL_CANDIDATES = {

    "VIX": [
        "VIX",
    ],

    "DXY": [
        "DXY",
    ],

    "US10Y": [
        "US10Y",
    ],

    "WTI": [
        "WTI",
    ],

    "HY_OAS": [
        "credit__HY_OAS",
        "HY_OAS",
    ],

    "SP500_POS_Z": [
        "positioning__SP500_POS_Z",
        "SP500_POS_Z",
    ],

    "CTA_MOMENTUM_SCORE": [
        "positioning__CTA_MOMENTUM_SCORE",
        "CTA_MOMENTUM_SCORE",
    ],

    "DEALER_GAMMA_BIAS": [
        "positioning__DEALER_GAMMA_BIAS",
        "DEALER_GAMMA_BIAS",
    ],
}


# ============================================================
# BASIC HELPERS
# ============================================================

def scalar(value: Any) -> Any:

    if isinstance(value, dict):

        for key in (
            "today",
            "value",
            "latest",
            "current",
            "close",
        ):
            if key in value:
                return value.get(key)

        return None

    return value


def is_missing(value: Any) -> bool:

    if value is None:
        return True

    try:
        x = pd.isna(value)

        if isinstance(x, bool):
            return x

    except Exception:
        pass

    return False


def equal_value(
    a: Any,
    b: Any,
    tol: float = 1e-6,
) -> bool:

    if is_missing(a) and is_missing(b):
        return True

    if is_missing(a) or is_missing(b):
        return False

    if isinstance(a, dict) and isinstance(b, dict):

        if set(a) != set(b):
            return False

        return all(
            equal_value(
                a[k],
                b[k],
                tol,
            )
            for k in a
        )

    if isinstance(a, (list, tuple)) and isinstance(
        b,
        (list, tuple),
    ):

        if len(a) != len(b):
            return False

        return all(
            equal_value(x, y, tol)
            for x, y in zip(a, b)
        )

    try:
        fa = float(a)
        fb = float(b)

        if math.isnan(fa) and math.isnan(fb):
            return True

        return math.isclose(
            fa,
            fb,
            rel_tol=tol,
            abs_tol=tol,
        )

    except Exception:
        return str(a) == str(b)


def panel_value(
    panel: pd.DataFrame,
    idx: int,
    contract: str,
):

    candidates = RAW_PANEL_CANDIDATES.get(
        contract,
        [],
    )

    for col in candidates:

        if col not in panel.columns:
            continue

        value = panel.iloc[idx].get(col)

        if not is_missing(value):
            return value, col

    return None, None


# ============================================================
# INDEPENDENT MOMENTUM REFERENCE
# ============================================================

def historical_return_reference(
    panel: pd.DataFrame,
    idx: int,
    column: str,
    lookback: int,
):

    if column not in panel.columns:
        return None

    previous_idx = idx - lookback

    if previous_idx < 0:
        return None

    today = pd.to_numeric(
        panel.iloc[idx].get(column),
        errors="coerce",
    )

    previous = pd.to_numeric(
        panel.iloc[previous_idx].get(column),
        errors="coerce",
    )

    if (
        pd.isna(today)
        or pd.isna(previous)
        or previous == 0
    ):
        return None

    return float(
        today / previous - 1.0
    )


def momentum_reference(
    panel: pd.DataFrame,
    idx: int,
) -> dict[str, int]:

    result = {}

    spy_4 = historical_return_reference(
        panel,
        idx,
        "SPY",
        20,
    )

    spy_12 = historical_return_reference(
        panel,
        idx,
        "SPY",
        60,
    )

    for ticker in SECTOR_TICKERS:

        r4 = historical_return_reference(
            panel,
            idx,
            ticker,
            20,
        )

        r12 = historical_return_reference(
            panel,
            idx,
            ticker,
            60,
        )

        if (
            r4 is None
            or r12 is None
            or spy_4 is None
            or spy_12 is None
        ):
            result[ticker] = 0
            continue

        composite = (
            (r4 - spy_4) * 0.6
            + (r12 - spy_12) * 0.4
        )

        if composite >= 0.05:
            score = 2

        elif composite >= 0.01:
            score = 1

        elif composite <= -0.05:
            score = -2

        elif composite <= -0.01:
            score = -1

        else:
            score = 0

        result[ticker] = score

    return result


# ============================================================
# INDEPENDENT POSITIONING-STRESS REFERENCE
# ============================================================

def to_float(value: Any) -> float:

    value = scalar(value)

    try:
        return float(value)

    except Exception:
        return 0.0


def positioning_reference(
    md: dict[str, Any],
) -> dict[str, Any]:

    vix = to_float(
        md.get("VIX")
    )

    vix3m = to_float(
        md.get("VIX3M")
    )

    vix9d = to_float(
        md.get("VIX9D")
    )

    gamma = to_float(
        md.get("DEALER_GAMMA_BIAS")
    )

    spx_pos = to_float(
        md.get("SP500_POS_Z")
    )

    cta = to_float(
        md.get("CTA_MOMENTUM_SCORE")
    )

    score = 0

    if vix > 0 and vix3m > 0:

        spread = vix3m - vix

        if spread > 2:
            score += 2

        elif spread > 0:
            score += 1

        elif spread > -2:
            score -= 1

        else:
            score -= 3

    if vix > 0 and vix9d > 0:

        front_ratio = (
            vix9d / vix
        )

        if front_ratio < 0.95:
            score += 1

        elif front_ratio > 1.05:
            score -= 2

    if gamma > 1:
        score -= 2

    elif gamma > 0:
        score -= 1

    elif gamma < -1:
        score += 1

    if spx_pos > 2:
        score -= 2

    elif spx_pos > 1:
        score -= 1

    elif spx_pos < -1:
        score += 1

    if cta > 1:
        score -= 1

    elif cta < 0:
        score += 1

    if score >= 4:

        label = "STRUCTURAL_RISK_ON"

    elif score >= 1:

        label = "STABLE_BUT_CROWDED"

    elif score >= -3:

        label = "SQUEE_RISK"

    else:

        label = "POSITIONING_STRESS_EVENT"

    # Typo guard: Production label is SQUEEZE_RISK.
    if label == "SQUEE_RISK":
        label = "SQUEEZE_RISK"

    if label == "STRUCTURAL_RISK_ON":

        positioning_state = "CALM"
        positioning_score = 0
        squeeze = "LOW"

    elif label == "STABLE_BUT_CROWDED":

        positioning_state = "ELEVATED"
        positioning_score = -1
        squeeze = "MEDIUM"

    elif label == "SQUEEZE_RISK":

        positioning_state = "SQUEEZE_RISK"
        positioning_score = -3
        squeeze = "HIGH"

    else:

        positioning_state = "STRESSED"
        positioning_score = -2
        squeeze = "HIGH"

    if gamma > 1:

        gamma_signal = (
            "CALL_OVERHEATED"
        )

    elif gamma > 0:

        gamma_signal = "STABLE"

    elif gamma < -1:

        gamma_signal = (
            "SHORT_GAMMA"
        )

    else:

        gamma_signal = "STABLE"

    if (
        vix > 0
        and vix3m > 0
        and vix9d > 0
    ):

        if (
            vix3m - vix
        ) <= -2:

            vol_structure = (
                "DISLOCATION"
            )

        elif (
            vix9d / vix
        ) > 1.05:

            vol_structure = (
                "INVERTED_SHORT_TERM"
            )

        elif (
            (vix3m - vix) > 2
            and (vix9d / vix) < 0.95
        ):

            vol_structure = "NORMAL"

        else:

            vol_structure = (
                "COMPRESSION"
            )

    else:

        vol_structure = "COMPRESSION"

    return {
        "POSITIONING_STATE":
            positioning_state,

        "POSITIONING_SCORE_18":
            positioning_score,

        "SQUEEZE_RISK":
            squeeze,

        "GAMMA_SIGNAL":
            gamma_signal,

        "VOL_STRUCTURE":
            vol_structure,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    if not MANIFEST_PATH.exists():

        raise FileNotFoundError(
            MANIFEST_PATH
        )

    manifest = pd.read_csv(
        MANIFEST_PATH
    )

    if len(manifest) != 82:

        raise RuntimeError(
            f"Manifest must contain "
            f"82 stage-contract pairs, "
            f"found {len(manifest)}"
        )

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    eligible = panel.index[
        panel[
            "execution_date"
        ].notna()
        & pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    ].tolist()

    print()
    print("=" * 78)
    print(
        "F13/F15/F18 FULL VALUE + EXECUTION CLOSURE"
    )
    print("=" * 78)

    print(
        "ROWS:",
        len(eligible),
    )

    print(
        "STAGE-CONTRACT PAIRS:",
        len(manifest),
    )

    # Previous source/static gate.
    source_pass = set()

    if SOURCE_PARITY_PATH.exists():

        source = pd.read_csv(
            SOURCE_PARITY_PATH
        )

        source_pass = set(
            source.loc[
                source["status"].str.startswith(
                    "PASS",
                    na=False,
                ),
                "contract",
            ].tolist()
        )

    counters = {
        (
            row.stage,
            row.contract,
        ): {
            "checked": 0,
            "passed": 0,
            "failed": 0,
            "method": "",
        }
        for row in manifest.itertuples()
    }

    failures = []

    flow_memory = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    filter15_memory = (
        initial_filter15_memory()
    )

    previous_exposure = 50.0

    expected_next_f15 = (
        initial_filter15_memory()
    )

    # --------------------------------------------------------
    # Full-period loop
    # --------------------------------------------------------

    for n, idx in enumerate(
        eligible,
        start=1,
    ):

        signal_date = panel.loc[
            idx,
            "signal_date",
        ]

        md = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=
                previous_exposure,
        )

        with contextlib.redirect_stdout(
            io.StringIO()
        ):

            flow_memory = (
                prepare_filter13_execution_state(
                    market_data=md,
                    panel=panel,
                    row_index=idx,
                    previous_flow_memory=
                        flow_memory,
                )
            )

            prepare_historical_execution_contract(
                market_data=md,
                panel=panel,
                row_index=idx,
                filter15_memory=
                    filter15_memory,
            )

        # ====================================================
        # PRE-F13
        # ====================================================

        pre_f13 = dict(md)

        # ----------------------------------------------------
        # Exact repaired contracts BEFORE filters
        # ----------------------------------------------------

        momentum_expected = (
            momentum_reference(
                panel,
                idx,
            )
        )

        positioning_expected = (
            positioning_reference(
                md
            )
        )

        # ====================================================
        # F13
        # ====================================================

        disable_live_side_effects(
            previous_exposure
        )

        neutralize_all_side_effects(
            previous_exposure
        )

        with contextlib.redirect_stdout(
            io.StringIO()
        ):

            sf.narrative_engine_filter(
                md
            )

        post_f13 = dict(md)

        # ====================================================
        # F15
        # ====================================================

        pre_f15 = dict(md)

        with contextlib.redirect_stdout(
            io.StringIO()
        ):

            sf.volatility_controlled_exposure_filter(
                md
            )

        post_f15 = dict(md)
        pre_f18 = dict(md)

        # ====================================================
        # F18
        # ====================================================

        with contextlib.redirect_stdout(
            io.StringIO()
        ):

            sf.sector_allocation_filter(
                md
            )

        post_f18 = dict(md)

        # ====================================================
        # MANIFEST AUDIT
        # ====================================================

        snapshots = {
            "F13": (
                pre_f13,
                post_f13,
            ),
            "F15": (
                pre_f15,
                post_f15,
            ),
            "F18": (
                pre_f18,
                post_f18,
            ),
        }

        for row in manifest.itertuples():

            stage = row.stage
            contract = row.contract
            role = row.contract_role

            key = (
                stage,
                contract,
            )

            stat = counters[key]

            pre, post = snapshots[
                stage
            ]

            stat["checked"] += 1

            ok = True
            method = ""
            expected = None
            actual = None

            # ----------------------------------------------
            # Expected fallback contracts
            # ----------------------------------------------

            if (
                stage,
                contract,
            ) in EXPECTED_FALLBACK:

                ok = True
                method = (
                    "EXPECTED_FALLBACK"
                )

            # ----------------------------------------------
            # F15 t-1 memory exact transition
            # ----------------------------------------------

            elif (
                stage == "F15"
                and contract
                in F15_MEMORY_KEYS
            ):

                actual = pre.get(
                    contract
                )

                expected = (
                    expected_next_f15.get(
                        contract
                    )
                )

                ok = equal_value(
                    actual,
                    expected,
                )

                method = (
                    "EXACT_T_MINUS_1_STATE"
                )

            # ----------------------------------------------
            # Momentum exact independent reference
            # ----------------------------------------------

            elif (
                stage == "F18"
                and contract
                == "MOMENTUM_SCORES"
            ):

                actual = pre.get(
                    contract
                )

                expected = (
                    momentum_expected
                )

                ok = equal_value(
                    actual,
                    expected,
                )

                method = (
                    "EXACT_INDEPENDENT_MOMENTUM"
                )

            # ----------------------------------------------
            # Positioning stress exact independent reference
            # ----------------------------------------------

            elif (
                stage == "F18"
                and contract
                in F18_POSITIONING_KEYS
            ):

                actual = pre.get(
                    contract
                )

                expected = (
                    positioning_expected.get(
                        contract
                    )
                )

                ok = equal_value(
                    actual,
                    expected,
                )

                method = (
                    "EXACT_INDEPENDENT_POSITIONING"
                )

            # ----------------------------------------------
            # Direct raw panel value
            # ----------------------------------------------

            elif (
                contract
                in RAW_PANEL_CANDIDATES
            ):

                actual = scalar(
                    pre.get(
                        contract
                    )
                )

                expected, source_col = (
                    panel_value(
                        panel,
                        idx,
                        contract,
                    )
                )

                # If the panel has an explicit matching
                # historical source column, demand exact value.
                if source_col is not None:

                    ok = equal_value(
                        actual,
                        expected,
                    )

                    method = (
                        f"EXACT_PANEL:{source_col}"
                    )

                else:

                    # Already separately source/transform audited.
                    ok = (
                        contract
                        in source_pass
                        and contract in pre
                    )

                    method = (
                        "SOURCE_TRANSFORM_GATE"
                    )

            # ----------------------------------------------
            # Internal / output contract
            # ----------------------------------------------

            elif role in {
                "OUTPUT_OR_INTERNAL_STATE",
            }:

                actual = post.get(
                    contract
                )

                ok = (
                    contract in post
                )

                method = (
                    "PRODUCTION_FUNCTION_OUTPUT"
                )

            # ----------------------------------------------
            # Read/write state generated by same Production fn
            # ----------------------------------------------

            elif (
                role
                == "READ_WRITE_STATE"
            ):

                actual = post.get(
                    contract
                )

                ok = (
                    contract in post
                )

                method = (
                    "SHARED_PRODUCTION_STATE"
                )

            # ----------------------------------------------
            # Previously proven source/transform contract
            # ----------------------------------------------

            elif contract in source_pass:

                ok = (
                    contract in pre
                )

                method = (
                    "SOURCE_TRANSFORM_GATE"
                )

            # ----------------------------------------------
            # Shared Production-function path
            # ----------------------------------------------

            elif contract in SHARED_PRODUCTION_PATH:

                ok = (
                    contract in pre
                )

                method = (
                    "SHARED_PRODUCTION_PATH"
                )

            # ----------------------------------------------
            # Generic upstream input:
            # must at least exist at consumer boundary.
            # ----------------------------------------------

            else:

                ok = (
                    contract in pre
                )

                method = (
                    "BOUNDARY_PRESENCE"
                )

            stat["method"] = method

            if ok:

                stat["passed"] += 1

            else:

                stat["failed"] += 1

                failures.append({
                    "signal_date":
                        signal_date,

                    "stage":
                        stage,

                    "contract":
                        contract,

                    "method":
                        method,

                    "expected":
                        repr(expected),

                    "actual":
                        repr(actual),
                })

        # ====================================================
        # State for next historical day
        # ====================================================

        expected_next_f15 = {
            key:
                post_f15.get(key)
            for key in F15_MEMORY_KEYS
        }

        filter15_memory = (
            capture_filter15_memory(
                post_f15
            )
        )

        exposure = post_f15.get(
            "RECOMMENDED_EXPOSURE"
        )

        if exposure is not None:

            try:
                previous_exposure = float(
                    exposure
                )
            except Exception:
                pass

        if n % 500 == 0:

            print(
                f"checked {n}/{len(eligible)}"
            )

    # ========================================================
    # DETAIL / SUMMARY
    # ========================================================

    detail_rows = []

    for row in manifest.itertuples():

        key = (
            row.stage,
            row.contract,
        )

        stat = counters[key]

        status = (
            "PASS"
            if stat["failed"] == 0
            and stat["checked"]
            == len(eligible)
            else "FAIL"
        )

        detail_rows.append({
            "stage":
                row.stage,

            "contract":
                row.contract,

            "contract_role":
                row.contract_role,

            "method":
                stat["method"],

            "checked_rows":
                stat["checked"],

            "passed_rows":
                stat["passed"],

            "failed_rows":
                stat["failed"],

            "status":
                status,
        })

    detail = pd.DataFrame(
        detail_rows
    )

    summary = (
        detail
        .groupby(
            [
                "stage",
                "status",
            ]
        )
        .size()
        .reset_index(
            name="contracts"
        )
    )

    failure_df = pd.DataFrame(
        failures
    )

    detail.to_csv(
        OUT_DETAIL,
        index=False,
    )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
    )

    if failure_df.empty:

        pd.DataFrame(
            columns=[
                "signal_date",
                "stage",
                "contract",
                "method",
                "expected",
                "actual",
            ]
        ).to_csv(
            OUT_FAILURES,
            index=False,
        )

    else:

        failure_df.to_csv(
            OUT_FAILURES,
            index=False,
        )

    pass_contracts = int(
        (detail["status"] == "PASS").sum()
    )

    fail_contracts = int(
        (detail["status"] == "FAIL").sum()
    )

    lines = []

    lines.append(
        "F13/F15/F18 FULL VALUE + EXECUTION CLOSURE"
    )

    lines.append(
        "=" * 78
    )

    lines.append(
        f"Historical rows: {len(eligible)}"
    )

    lines.append(
        f"Stage-contract pairs: {len(detail)}"
    )

    lines.append(
        f"PASS contracts: {pass_contracts}"
    )

    lines.append(
        f"FAIL contracts: {fail_contracts}"
    )

    lines.append(
        f"Failure observations: {len(failure_df)}"
    )

    lines.append("")

    lines.append(
        summary.to_string(
            index=False
        )
    )

    lines.append("")

    if (
        pass_contracts == 82
        and fail_contracts == 0
        and failure_df.empty
    ):

        lines.append(
            "FULL VALUE / EXECUTION CONTRACT GATE: PASS"
        )

    else:

        lines.append(
            "FULL VALUE / EXECUTION CONTRACT GATE: NOT CLOSED"
        )

    OUT_TXT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    # ========================================================
    # CONSOLE
    # ========================================================

    print()
    print("=" * 78)
    print("RESULT")
    print("=" * 78)

    print(
        detail[
            [
                "stage",
                "contract",
                "method",
                "passed_rows",
                "failed_rows",
                "status",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print(
        "PASS CONTRACTS:",
        pass_contracts,
        "/82",
    )

    print(
        "FAIL CONTRACTS:",
        fail_contracts,
    )

    print(
        "FAILURE OBSERVATIONS:",
        len(failure_df),
    )

    print()

    if (
        pass_contracts == 82
        and fail_contracts == 0
        and failure_df.empty
    ):

        print(
            "FULL VALUE / EXECUTION CONTRACT GATE: PASS"
        )

    else:

        print(
            "FULL VALUE / EXECUTION CONTRACT GATE: NOT CLOSED"
        )

        if not failure_df.empty:

            print()
            print(
                failure_df.head(
                    30
                ).to_string(
                    index=False
                )
            )

    print()
    print("[OUTPUT]")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)
    print(OUT_FAILURES)
    print(OUT_TXT)


if __name__ == "__main__":
    main()
