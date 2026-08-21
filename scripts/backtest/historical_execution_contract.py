from __future__ import annotations

"""
Historical Execution Contract Adapter
=====================================

Purpose
-------
Reproduce Production-only runtime contracts for historical backtest
without using current/live state.

Repairs
-------
Filter15 persistent state:
1. FILTER15_PREV_DEADMAN
2. FILTER15_RECOVERY_ACTIVE
3. FILTER15_RECOVERY_COMPLETED
4. FILTER15_RECOVERY_STREAK
5. FILTER15_PREV_HY_OAS

Filter18 upstream state:
6. MOMENTUM_SCORES
7. POSITIONING_STATE
8. POSITIONING_SCORE_18
9. SQUEEZE_RISK
10. GAMMA_SIGNAL
11. VOL_STRUCTURE

Rules
-----
- Production code is never modified.
- Historical data up to current row_index only.
- No live JSON/state files.
- No future rows.
- Production positioning_stress_filter() itself is reused.
"""

from typing import Any

import pandas as pd

from filters.positioning_stress import positioning_stress_filter


SECTOR_TICKERS = [
    "XLK",
    "XLF",
    "XLE",
    "XLI",
    "XLB",
    "XLY",
    "XLP",
    "XLV",
    "XLU",
    "XLRE",
    "XLC",
]


# ============================================================
# Filter15 persistent historical state
# ============================================================

def initial_filter15_memory() -> dict[str, Any]:
    """
    Same neutral/default contract used when Production has no
    prior persisted Filter15 state.
    """
    return {
        "FILTER15_PREV_DEADMAN": False,
        "FILTER15_RECOVERY_ACTIVE": False,
        "FILTER15_RECOVERY_COMPLETED": False,
        "FILTER15_RECOVERY_STREAK": 0,
        "FILTER15_PREV_HY_OAS": None,
    }


def inject_filter15_memory(
    market_data: dict[str, Any],
    memory: dict[str, Any] | None,
) -> None:
    """
    Inject t-1 Filter15 state BEFORE today's Filter15 execution.
    """
    memory = memory or initial_filter15_memory()

    market_data["FILTER15_PREV_DEADMAN"] = bool(
        memory.get("FILTER15_PREV_DEADMAN", False)
    )

    market_data["FILTER15_RECOVERY_ACTIVE"] = bool(
        memory.get("FILTER15_RECOVERY_ACTIVE", False)
    )

    market_data["FILTER15_RECOVERY_COMPLETED"] = bool(
        memory.get("FILTER15_RECOVERY_COMPLETED", False)
    )

    market_data["FILTER15_RECOVERY_STREAK"] = int(
        memory.get("FILTER15_RECOVERY_STREAK", 0) or 0
    )

    market_data["FILTER15_PREV_HY_OAS"] = memory.get(
        "FILTER15_PREV_HY_OAS"
    )

    market_data["_FILTER15_STATE_SOURCE"] = (
        "HISTORICAL_T_MINUS_1_MEMORY"
    )


def capture_filter15_memory(
    market_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Capture state written by today's Production Filter15.
    This becomes tomorrow's historical memory.
    """
    return {
        "FILTER15_PREV_DEADMAN": bool(
            market_data.get("FILTER15_PREV_DEADMAN", False)
        ),

        "FILTER15_RECOVERY_ACTIVE": bool(
            market_data.get("FILTER15_RECOVERY_ACTIVE", False)
        ),

        "FILTER15_RECOVERY_COMPLETED": bool(
            market_data.get("FILTER15_RECOVERY_COMPLETED", False)
        ),

        "FILTER15_RECOVERY_STREAK": int(
            market_data.get("FILTER15_RECOVERY_STREAK", 0) or 0
        ),

        "FILTER15_PREV_HY_OAS":
            market_data.get("FILTER15_PREV_HY_OAS"),
    }


# ============================================================
# Filter18 Sector Momentum — exact Production semantics
# ============================================================

def _historical_return(
    panel: pd.DataFrame,
    row_index: int,
    column: str,
    lookback: int,
) -> float | None:

    if column not in panel.columns:
        return None

    previous_index = row_index - lookback

    if previous_index < 0:
        return None

    today_value = pd.to_numeric(
        panel.iloc[row_index].get(column),
        errors="coerce",
    )

    previous_value = pd.to_numeric(
        panel.iloc[previous_index].get(column),
        errors="coerce",
    )

    if (
        pd.isna(today_value)
        or pd.isna(previous_value)
        or previous_value == 0
    ):
        return None

    return float(
        today_value / previous_value - 1.0
    )


def build_historical_sector_momentum(
    market_data: dict[str, Any],
    panel: pd.DataFrame,
    row_index: int,
) -> None:
    """
    Historical equivalent of Production
    attach_sector_momentum_layer().

    Production semantics:
        4w  = 20 trading-row return
        12w = 60 trading-row return
        relative to SPY

        composite =
            0.6 * RS_4W
          + 0.4 * RS_12W

        >= +5% : +2
        >= +1% : +1
        <= -5% : -2
        <= -1% : -1
        otherwise 0
    """

    scores: dict[str, int] = {}

    spy_4w = _historical_return(
        panel,
        row_index,
        "SPY",
        20,
    )

    spy_12w = _historical_return(
        panel,
        row_index,
        "SPY",
        60,
    )

    for ticker in SECTOR_TICKERS:

        r_4w = _historical_return(
            panel,
            row_index,
            ticker,
            20,
        )

        r_12w = _historical_return(
            panel,
            row_index,
            ticker,
            60,
        )

        if (
            r_4w is None
            or r_12w is None
            or spy_4w is None
            or spy_12w is None
        ):
            scores[ticker] = 0
            continue

        rs_4w = r_4w - spy_4w
        rs_12w = r_12w - spy_12w

        composite_rs = (
            rs_4w * 0.6
            + rs_12w * 0.4
        )

        if composite_rs >= 0.05:
            score = 2

        elif composite_rs >= 0.01:
            score = 1

        elif composite_rs <= -0.05:
            score = -2

        elif composite_rs <= -0.01:
            score = -1

        else:
            score = 0

        scores[ticker] = score

    market_data["MOMENTUM_SCORES"] = scores

    market_data["_MOMENTUM_SOURCE"] = (
        "HISTORICAL_PIT_MASTER_PANEL_20D_60D"
    )


# ============================================================
# Filter18 Positioning Stress
# ============================================================

def _row_float(
    panel: pd.DataFrame,
    row_index: int,
    column: str,
) -> float:
    """
    Production volatility-structure attach semantics:
    missing VIX3M/VIX9D -> 0.0.
    """

    if column not in panel.columns:
        return 0.0

    value = pd.to_numeric(
        panel.iloc[row_index].get(column),
        errors="coerce",
    )

    if pd.isna(value):
        return 0.0

    return float(value)


def build_historical_positioning_stress(
    market_data: dict[str, Any],
    panel: pd.DataFrame,
    row_index: int,
) -> None:
    """
    Supply VIX term-structure inputs from historical panel,
    then execute the exact Production positioning_stress_filter.

    positioning_stress_filter generates:
        POSITIONING_STATE
        POSITIONING_SCORE_18
        SQUEEZE_RISK
        GAMMA_SIGNAL
        VOL_STRUCTURE
    """

    # Production attach_volatility_structure_layer
    # supplies these as flat numbers.
    market_data["VIX3M"] = _row_float(
        panel,
        row_index,
        "VIX3M",
    )

    market_data["VIX9D"] = _row_float(
        panel,
        row_index,
        "VIX9D",
    )

    positioning_stress_filter(
        market_data
    )

    market_data["_POSITIONING_STRESS_SOURCE"] = (
        "PRODUCTION_FUNCTION_WITH_HISTORICAL_PIT_INPUTS"
    )


# ============================================================
# Full repair entry point
# ============================================================

def prepare_historical_execution_contract(
    market_data: dict[str, Any],
    panel: pd.DataFrame,
    row_index: int,
    filter15_memory: dict[str, Any] | None,
) -> None:
    """
    Must run AFTER historical pre-F13 preparation
    and BEFORE F13 -> F15 -> F18 engine execution.

    None of these added Filter18 contracts alter F13/F15 logic;
    they are prepared early only so the canonical run_engine
    can remain F13 -> F15 -> F18.
    """

    inject_filter15_memory(
        market_data,
        filter15_memory,
    )

    build_historical_sector_momentum(
        market_data,
        panel,
        row_index,
    )

    build_historical_positioning_stress(
        market_data,
        panel,
        row_index,
    )
