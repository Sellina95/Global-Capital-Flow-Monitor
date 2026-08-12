from __future__ import annotations

import contextlib
import io
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# Bootstrap
# ============================================================

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


import filters.strategist_filters as sf
import scripts.backtest.run_backtest as rb

from scripts.backtest.audit_filter13_candidate_full_pipeline import (
    calc_candidate_budget,
    patch_filter13_budget,
)


# ============================================================
# Paths
# ============================================================

DATA_DIR = ROOT / "data" / "backtest"
RESULT_DIR = DATA_DIR / "results"

PANEL_PATH = (
    DATA_DIR
    / "master_panel.csv"
)

ATTR_PATH = (
    RESULT_DIR
    / "filter13_budget_attribution_final_daily.csv"
)

PRICE_PATH = (
    DATA_DIR
    / "sector_prices_filter13_candidate.csv"
)

# Earlier validated Filter18 baseline / Rank3D result
RANK_SUMMARY_PATH = (
    RESULT_DIR
    / "filter18_rank_persistence_counterfactual_summary.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "final_13_18_combined_candidate_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "final_13_18_combined_candidate_summary.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "final_13_18_combined_candidate_summary.txt"
)


# ============================================================
# Research contract
# ============================================================

FILTER13_LIMIT = 20.0
RANK_PERSISTENCE_DAYS = 3

HOLD_THRESHOLD = 2.0
REBALANCE_THRESHOLD = 5.0

COST_BPS_ONE_WAY = 5.0
TRADING_DAYS = 252


SECTOR_TO_ETF = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Consumer Discretionary": "XLY",
    "Health Care": "XLV",
    "Utilities": "XLU",
    "Consumer Staples": "XLP",
    "Materials": "XLB",
    "Communication Services": "VOX",
    "Real Estate": "IYR",
}


# ============================================================
# Helpers
# ============================================================

def safe_float(
    value,
    default=np.nan,
):
    try:
        x = float(value)

        if pd.isna(x):
            return default

        return x

    except Exception:
        return default


def rank_signature(
    score: dict[str, Any],
) -> str:
    """
    Same positive-score ranking concept used by
    Filter18 rotation attribution.
    """

    rows = []

    for sector, value in (
        score or {}
    ).items():

        x = safe_float(
            value
        )

        if (
            pd.notna(x)
            and x > 0
        ):
            rows.append(
                (
                    str(sector),
                    float(x),
                )
            )

    rows.sort(
        key=lambda item: (
            -item[1],
            item[0],
        )
    )

    return "|".join(
        sector
        for sector, _
        in rows
    )


def normalize_historical_filter15_inputs(
    market_data: dict[str, Any],
) -> None:
    """
    Audit-only normalization already required by
    historical Filter15 execution.
    """

    cross = (
        market_data.get(
            "CROSS_ASSET_TAPE",
            {},
        )
        or {}
    )

    if not isinstance(
        cross,
        dict,
    ):
        cross = {}

    value = safe_float(
        cross.get(
            "VIX_Z"
        ),
        default=0.0,
    )

    cross[
        "VIX_Z"
    ] = value

    market_data[
        "CROSS_ASSET_TAPE"
    ] = cross


def apply_rebalance_threshold_exact(
    target_weights: dict[str, float],
    previous_weights: dict[str, float],
) -> tuple[
    dict[str, float],
    dict[str, str],
]:
    """
    Exact production semantics:
    <2%p = HOLD
    2~5%p = SMALL ADJUST
    >=5%p = REBALANCE
    """

    adjusted = {}
    actions = {}

    for sector, target_w in (
        target_weights.items()
    ):

        previous = previous_weights.get(
            sector
        )

        if previous is None:

            adjusted[
                sector
            ] = target_w

            actions[
                sector
            ] = "NEW"

            continue

        diff = (
            target_w
            - previous
        )

        abs_diff = abs(
            diff
        )

        if (
            abs_diff
            < HOLD_THRESHOLD
        ):

            adjusted[
                sector
            ] = previous

            actions[
                sector
            ] = "HOLD"

        elif (
            abs_diff
            < REBALANCE_THRESHOLD
        ):

            adjusted[
                sector
            ] = target_w

            actions[
                sector
            ] = "SMALL ADJUST"

        else:

            adjusted[
                sector
            ] = target_w

            actions[
                sector
            ] = "REBALANCE"

    adjusted = {
        sector:
            round(
                weight,
                1,
            )
        for sector, weight
        in adjusted.items()
    }

    return (
        adjusted,
        actions,
    )


def calculate_turnover(
    current: dict[str, float],
    previous: dict[str, float],
    universe: list[str],
) -> float:

    return float(
        sum(
            abs(
                current.get(
                    sector,
                    0.0,
                )
                -
                previous.get(
                    sector,
                    0.0,
                )
            )
            for sector
            in universe
        )
        / 100.0
    )


def annualized_return(
    returns: pd.Series,
) -> float:

    clean = pd.to_numeric(
        returns,
        errors="coerce",
    ).dropna()

    if clean.empty:
        return np.nan

    total = float(
        (
            1.0
            + clean
        ).prod()
    )

    years = (
        len(clean)
        / TRADING_DAYS
    )

    if (
        years <= 0
        or total <= 0
    ):
        return np.nan

    return (
        total
        ** (
            1.0
            / years
        )
        - 1.0
    )


def annualized_volatility(
    returns: pd.Series,
) -> float:

    clean = pd.to_numeric(
        returns,
        errors="coerce",
    ).dropna()

    if len(clean) < 2:
        return np.nan

    return float(
        clean.std(
            ddof=1
        )
        * math.sqrt(
            TRADING_DAYS
        )
    )


def sharpe_ratio(
    returns: pd.Series,
) -> float:

    clean = pd.to_numeric(
        returns,
        errors="coerce",
    ).dropna()

    if len(clean) < 2:
        return np.nan

    std = clean.std(
        ddof=1
    )

    if std == 0:
        return np.nan

    return float(
        clean.mean()
        / std
        * math.sqrt(
            TRADING_DAYS
        )
    )


def max_drawdown(
    returns: pd.Series,
) -> float:

    clean = pd.to_numeric(
        returns,
        errors="coerce",
    )

    wealth = (
        1.0
        + clean.fillna(
            0.0
        )
    ).cumprod()

    peak = wealth.cummax()

    return float(
        (
            wealth
            / peak
            - 1.0
        ).min()
    )


# ============================================================
# Run FILTER13 LIMIT20 once and capture exact Filter18
# target/provenance
# ============================================================

def build_limit20_provenance(
    panel: pd.DataFrame,
    attr_lookup: dict,
) -> pd.DataFrame:

    mask = (
        panel[
            "execution_date"
        ].notna()
        &
        pd.to_numeric(
            panel[
                "SPY"
            ],
            errors="coerce",
        ).notna()
    )

    indices = (
        panel.index[
            mask
        ].tolist()
    )

    previous_exposure = 50.0

    flow_memory: dict[
        str,
        Any,
    ] = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    rows = []

    for count, idx in enumerate(
        indices,
        start=1,
    ):

        signal_date = pd.Timestamp(
            panel.iloc[
                idx
            ][
                "signal_date"
            ]
        )

        market_data = (
            rb.build_market_data(
                panel=panel,
                row_index=idx,
                previous_exposure=(
                    previous_exposure
                ),
            )
        )

        flow_memory = (
            rb.prepare_filter13_execution_state(
                market_data=market_data,
                panel=panel,
                row_index=idx,
                previous_flow_memory=(
                    flow_memory
                ),
            )
        )

        # ====================================================
        # Filter13 production baseline
        # ====================================================

        rb.disable_live_side_effects(
            previous_exposure
        )

        rb.neutralize_all_side_effects(
            previous_exposure
        )

        captured: dict[
            str,
            Any,
        ] = {}

        original_builder = (
            sf.build_tactical_allocation
        )

        def capture_builder(
            *args,
            **kwargs,
        ):

            score = (
                kwargs.get(
                    "score"
                )
                or (
                    args[0]
                    if len(args) > 0
                    else {}
                )
                or {}
            )

            deleveraging_required = (
                kwargs.get(
                    "deleveraging_required",
                    False,
                )
            )

            result = original_builder(
                *args,
                **kwargs,
            )

            captured[
                "score"
            ] = dict(
                score
            )

            captured[
                "deleveraging_required"
            ] = bool(
                deleveraging_required
            )

            captured[
                "allocation"
            ] = result

            return result

        sf.build_tactical_allocation = (
            capture_builder
        )

        try:

            with contextlib.redirect_stdout(
                io.StringIO()
            ):

                # --------------------------------------------
                # 13 production
                # --------------------------------------------

                sf.narrative_engine_filter(
                    market_data
                )

                production_budget = (
                    market_data.get(
                        "RISK_BUDGET"
                    )
                )

                # --------------------------------------------
                # LIMIT20 candidate budget
                # --------------------------------------------

                attr_row = (
                    attr_lookup.get(
                        signal_date.normalize()
                    )
                )

                candidate_budget = None

                if attr_row is not None:

                    candidate_budget = (
                        calc_candidate_budget(
                            attr_row,
                            FILTER13_LIMIT,
                        )
                    )

                if (
                    candidate_budget
                    is not None
                    and pd.notna(
                        candidate_budget
                    )
                ):

                    patch_filter13_budget(
                        market_data,
                        float(
                            candidate_budget
                        ),
                    )

                # --------------------------------------------
                # 15 production
                # --------------------------------------------

                normalize_historical_filter15_inputs(
                    market_data
                )

                sf.volatility_controlled_exposure_filter(
                    market_data
                )

                # --------------------------------------------
                # 18 production allocator
                # target output is captured
                # --------------------------------------------

                sf.sector_allocation_filter(
                    market_data
                )

        finally:

            sf.build_tactical_allocation = (
                original_builder
            )

        if not captured:

            raise RuntimeError(
                f"Filter18 capture failed on "
                f"{signal_date.date()}"
            )

        allocation = (
            captured.get(
                "allocation",
                {},
            )
            or {}
        )

        target_weights = (
            allocation.get(
                "weights",
                {},
            )
            or {}
        )

        score = (
            captured.get(
                "score",
                {},
            )
            or {}
        )

        exposure15 = (
            market_data.get(
                "RECOMMENDED_EXPOSURE"
            )
        )

        row = {
            "signal_date":
                signal_date,

            "execution_date":
                panel.iloc[
                    idx
                ][
                    "execution_date"
                ],

            "production_budget_13":
                production_budget,

            "candidate_budget_13":
                market_data.get(
                    "RISK_BUDGET"
                ),

            "exposure_15":
                exposure15,

            "rank_signature":
                rank_signature(
                    score
                ),

            "deleveraging_required":
                captured.get(
                    "deleveraging_required",
                    False,
                ),
        }

        for sector, weight in (
            target_weights.items()
        ):

            row[
                f"target__{sector}"
            ] = weight

        rows.append(
            row
        )

        if (
            exposure15 is not None
            and pd.notna(
                exposure15
            )
        ):

            previous_exposure = float(
                exposure15
            )

        if count % 500 == 0:

            print(
                f"[LIMIT20 PROVENANCE] "
                f"{count:,}/{len(indices):,}"
            )

    return pd.DataFrame(
        rows
    )


# ============================================================
# Sequential execution replay
# ============================================================

def replay_execution(
    source: pd.DataFrame,
    rank3d: bool,
    prices_return: pd.DataFrame,
) -> pd.DataFrame:

    df = (
        source
        .sort_values(
            "execution_date"
        )
        .reset_index(
            drop=True
        )
        .copy()
    )

    target_cols = [
        col
        for col in df.columns
        if col.startswith(
            "target__"
        )
    ]

    sectors = [
        col.replace(
            "target__",
            "",
            1,
        )
        for col in target_cols
    ]

    previous_executed = {}

    accepted_rank = None
    accepted_target = {}

    pending_rank = None
    pending_count = 0

    rows = []

    for _, row in df.iterrows():

        current_rank = str(
            row.get(
                "rank_signature",
                "",
            )
            or ""
        )

        deleveraging_required = bool(
            row.get(
                "deleveraging_required",
                False,
            )
        )

        source_target = {}

        for sector in sectors:

            value = pd.to_numeric(
                row.get(
                    f"target__{sector}"
                ),
                errors="coerce",
            )

            if pd.notna(
                value
            ):

                source_target[
                    sector
                ] = float(
                    value
                )

        # ====================================================
        # Rank persistence
        # ====================================================

        if not rank3d:

            target_for_execution = dict(
                source_target
            )

            rank_action = (
                "NO_PERSISTENCE"
            )

        elif accepted_rank is None:

            accepted_rank = (
                current_rank
            )

            accepted_target = dict(
                source_target
            )

            target_for_execution = dict(
                source_target
            )

            rank_action = (
                "INITIAL_ACCEPT"
            )

        elif deleveraging_required:

            # Safety always wins.
            accepted_rank = (
                current_rank
            )

            accepted_target = dict(
                source_target
            )

            pending_rank = None
            pending_count = 0

            target_for_execution = dict(
                source_target
            )

            rank_action = (
                "FORCED_DELEVERAGE_ACCEPT"
            )

        elif current_rank == accepted_rank:

            accepted_target = dict(
                source_target
            )

            pending_rank = None
            pending_count = 0

            target_for_execution = dict(
                source_target
            )

            rank_action = (
                "ACCEPTED_RANK_UPDATE"
            )

        else:

            if (
                pending_rank
                == current_rank
            ):

                pending_count += 1

            else:

                pending_rank = (
                    current_rank
                )

                pending_count = 1

            if (
                pending_count
                >= RANK_PERSISTENCE_DAYS
            ):

                accepted_rank = (
                    current_rank
                )

                accepted_target = dict(
                    source_target
                )

                pending_rank = None
                pending_count = 0

                target_for_execution = dict(
                    source_target
                )

                rank_action = (
                    "RANK_CONFIRMED"
                )

            else:

                target_for_execution = dict(
                    accepted_target
                )

                rank_action = (
                    "RANK_CHANGE_SUPPRESSED"
                )

        # ====================================================
        # Exact production execution semantics
        # ====================================================

        if deleveraging_required:

            executed = {
                sector:
                    round(
                        weight,
                        1,
                    )
                for sector, weight
                in target_for_execution.items()
            }

        else:

            executed, _ = (
                apply_rebalance_threshold_exact(
                    target_weights=(
                        target_for_execution
                    ),
                    previous_weights=(
                        previous_executed
                    ),
                )
            )

        turnover = (
            calculate_turnover(
                current=executed,
                previous=previous_executed,
                universe=sectors,
            )
        )

        execution_date = (
            row[
                "execution_date"
            ]
        )

        gross_return = np.nan

        if (
            pd.notna(
                execution_date
            )
            and execution_date
            in prices_return.index
        ):

            gross_return = 0.0

            for sector, weight_pct in (
                executed.items()
            ):

                ticker = (
                    SECTOR_TO_ETF.get(
                        sector
                    )
                )

                if (
                    ticker is None
                    or ticker
                    not in prices_return.columns
                ):
                    continue

                ticker_return = (
                    prices_return.at[
                        execution_date,
                        ticker,
                    ]
                )

                if pd.isna(
                    ticker_return
                ):
                    continue

                gross_return += (
                    float(
                        weight_pct
                    )
                    / 100.0
                    * float(
                        ticker_return
                    )
                )

        transaction_cost = (
            turnover
            * COST_BPS_ONE_WAY
            / 10000.0
        )

        net_return = (
            gross_return
            - transaction_cost
            if pd.notna(
                gross_return
            )
            else np.nan
        )

        rows.append(
            {
                "signal_date":
                    row[
                        "signal_date"
                    ],

                "execution_date":
                    execution_date,

                "candidate_budget_13":
                    row[
                        "candidate_budget_13"
                    ],

                "exposure_15":
                    row[
                        "exposure_15"
                    ],

                "deleveraging_required":
                    deleveraging_required,

                "rank_action":
                    rank_action,

                "turnover":
                    turnover,

                "transaction_cost":
                    transaction_cost,

                "strategy_return_gross":
                    gross_return,

                "strategy_return_net":
                    net_return,

                "allocated_equity":
                    sum(
                        executed.values()
                    ),
            }
        )

        previous_executed = dict(
            executed
        )

    return pd.DataFrame(
        rows
    )


# ============================================================
# Summarize scenario
# ============================================================

def summarize(
    name: str,
    df: pd.DataFrame,
) -> dict:

    gross = pd.to_numeric(
        df[
            "strategy_return_gross"
        ],
        errors="coerce",
    )

    net = pd.to_numeric(
        df[
            "strategy_return_net"
        ],
        errors="coerce",
    )

    return {
        "scenario":
            name,

        "days":
            len(
                df
            ),

        "avg_risk_budget_13":
            pd.to_numeric(
                df[
                    "candidate_budget_13"
                ],
                errors="coerce",
            ).mean(),

        "avg_exposure_15":
            pd.to_numeric(
                df[
                    "exposure_15"
                ],
                errors="coerce",
            ).mean(),

        "avg_allocated_equity":
            pd.to_numeric(
                df[
                    "allocated_equity"
                ],
                errors="coerce",
            ).mean(),

        "annualized_turnover":
            pd.to_numeric(
                df[
                    "turnover"
                ],
                errors="coerce",
            ).mean()
            * TRADING_DAYS,

        "total_cost_pct":
            pd.to_numeric(
                df[
                    "transaction_cost"
                ],
                errors="coerce",
            ).sum()
            * 100.0,

        "gross_cagr":
            annualized_return(
                gross
            )
            * 100.0,

        "net_cagr":
            annualized_return(
                net
            )
            * 100.0,

        "net_mdd":
            max_drawdown(
                net
            )
            * 100.0,

        "net_volatility":
            annualized_volatility(
                net
            )
            * 100.0,

        "net_sharpe":
            sharpe_ratio(
                net
            ),
    }


# ============================================================
# Main
# ============================================================

def main() -> None:

    for path in [
        PANEL_PATH,
        ATTR_PATH,
        PRICE_PATH,
        RANK_SUMMARY_PATH,
    ]:

        if not path.exists():

            raise FileNotFoundError(
                path
            )

    # ========================================================
    # Panel
    # ========================================================

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    # ========================================================
    # Canonical attribution
    # ========================================================

    attr = pd.read_csv(
        ATTR_PATH
    )

    attr[
        "signal_date"
    ] = pd.to_datetime(
        attr[
            "date"
        ],
        errors="coerce",
    )

    attr = (
        attr
        .dropna(
            subset=[
                "signal_date"
            ]
        )
        .sort_values(
            "signal_date"
        )
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
    )

    attr_lookup = {
        pd.Timestamp(
            row[
                "signal_date"
            ]
        ).normalize():
        row
        for _, row
        in attr.iterrows()
    }

    # ========================================================
    # Prices
    # ========================================================

    prices = pd.read_csv(
        PRICE_PATH
    )

    if (
        "execution_date"
        in prices.columns
    ):

        price_date_col = (
            "execution_date"
        )

    elif "date" in prices.columns:

        price_date_col = (
            "date"
        )

    else:

        raise ValueError(
            "Price date column missing."
        )

    prices[
        price_date_col
    ] = pd.to_datetime(
        prices[
            price_date_col
        ],
        errors="coerce",
    )

    prices = (
        prices
        .dropna(
            subset=[
                price_date_col
            ]
        )
        .set_index(
            price_date_col
        )
        .sort_index()
    )

    price_returns = prices.pct_change(
        fill_method=None
    )

    # ========================================================
    # 1) Run Filter13 LIMIT20 current full chain ONCE
    # ========================================================

    print()
    print(
        "=" * 120
    )

    print(
        "FINAL FILTER13 + FILTER18 COMBINED VALIDATION"
    )

    print(
        "=" * 120
    )

    print()

    print(
        "Running candidate-specific LIMIT20 provenance..."
    )

    limit20_source = (
        build_limit20_provenance(
            panel=panel,
            attr_lookup=attr_lookup,
        )
    )

    # ========================================================
    # 2) Filter13-only execution
    # ========================================================

    print()
    print(
        "Replaying FILTER13 LIMIT20 ONLY..."
    )

    filter13_only = replay_execution(
        source=limit20_source,
        rank3d=False,
        prices_return=price_returns,
    )

    # ========================================================
    # 3) Filter13 + Filter18 Rank3D
    # ========================================================

    print(
        "Replaying FILTER13 LIMIT20 + RANK3D..."
    )

    combined = replay_execution(
        source=limit20_source,
        rank3d=True,
        prices_return=price_returns,
    )

    # ========================================================
    # 4) Read already validated CURRENT / Rank3D baseline
    # ========================================================

    old = pd.read_csv(
        RANK_SUMMARY_PATH
    )

    current_row = (
        old[
            old[
                "scenario"
            ]
            == "BASELINE_1D"
        ]
        .iloc[0]
    )

    rank3d_row = (
        old[
            old[
                "scenario"
            ]
            == "PERSIST_3D"
        ]
        .iloc[0]
    )

    summary_rows = [
        {
            "scenario":
                "CURRENT",

            "annualized_turnover":
                current_row[
                    "annualized_turnover"
                ],

            "total_cost_pct":
                current_row[
                    "total_cost_pct"
                ],

            "gross_cagr":
                current_row[
                    "gross_cagr"
                ],

            "net_cagr":
                current_row[
                    "net_cagr"
                ],

            "net_mdd":
                current_row[
                    "net_mdd"
                ],

            "net_volatility":
                current_row[
                    "net_volatility"
                ],

            "net_sharpe":
                current_row[
                    "net_sharpe"
                ],
        },

        summarize(
            "FILTER13_LIMIT20_ONLY",
            filter13_only,
        ),

        {
            "scenario":
                "FILTER18_RANK3D_ONLY",

            "annualized_turnover":
                rank3d_row[
                    "annualized_turnover"
                ],

            "total_cost_pct":
                rank3d_row[
                    "total_cost_pct"
                ],

            "gross_cagr":
                rank3d_row[
                    "gross_cagr"
                ],

            "net_cagr":
                rank3d_row[
                    "net_cagr"
                ],

            "net_mdd":
                rank3d_row[
                    "net_mdd"
                ],

            "net_volatility":
                rank3d_row[
                    "net_volatility"
                ],

            "net_sharpe":
                rank3d_row[
                    "net_sharpe"
                ],
        },

        summarize(
            "FILTER13_LIMIT20_PLUS_RANK3D",
            combined,
        ),
    ]

    summary = pd.DataFrame(
        summary_rows
    )

    # ========================================================
    # Deltas vs current
    # ========================================================

    current = (
        summary[
            summary[
                "scenario"
            ]
            == "CURRENT"
        ]
        .iloc[0]
    )

    for metric in [
        "annualized_turnover",
        "total_cost_pct",
        "gross_cagr",
        "net_cagr",
        "net_mdd",
        "net_volatility",
        "net_sharpe",
    ]:

        summary[
            f"{metric}_delta_vs_current"
        ] = (
            summary[
                metric
            ]
            - current[
                metric
            ]
        )

    # ========================================================
    # Interaction check
    # ========================================================

    row13 = (
        summary[
            summary[
                "scenario"
            ]
            == "FILTER13_LIMIT20_ONLY"
        ]
        .iloc[0]
    )

    row18 = (
        summary[
            summary[
                "scenario"
            ]
            == "FILTER18_RANK3D_ONLY"
        ]
        .iloc[0]
    )

    combo = (
        summary[
            summary[
                "scenario"
            ]
            == "FILTER13_LIMIT20_PLUS_RANK3D"
        ]
        .iloc[0]
    )

    expected_additive_net_cagr = (
        current[
            "net_cagr"
        ]
        +
        (
            row13[
                "net_cagr"
            ]
            - current[
                "net_cagr"
            ]
        )
        +
        (
            row18[
                "net_cagr"
            ]
            - current[
                "net_cagr"
            ]
        )
    )

    interaction_net_cagr = (
        combo[
            "net_cagr"
        ]
        - expected_additive_net_cagr
    )

    expected_additive_sharpe = (
        current[
            "net_sharpe"
        ]
        +
        (
            row13[
                "net_sharpe"
            ]
            - current[
                "net_sharpe"
            ]
        )
        +
        (
            row18[
                "net_sharpe"
            ]
            - current[
                "net_sharpe"
            ]
        )
    )

    interaction_sharpe = (
        combo[
            "net_sharpe"
        ]
        - expected_additive_sharpe
    )

    # ========================================================
    # Save
    # ========================================================

    limit20_detail = (
        limit20_source.copy()
    )

    limit20_detail[
        "scenario"
    ] = (
        "LIMIT20_SOURCE"
    )

    filter13_only_save = (
        filter13_only.copy()
    )

    filter13_only_save[
        "scenario"
    ] = (
        "FILTER13_LIMIT20_ONLY"
    )

    combined_save = (
        combined.copy()
    )

    combined_save[
        "scenario"
    ] = (
        "FILTER13_LIMIT20_PLUS_RANK3D"
    )

    detail = pd.concat(
        [
            limit20_detail,
            filter13_only_save,
            combined_save,
        ],
        ignore_index=True,
        sort=False,
    )

    detail.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Final report
    # ========================================================

    lines = []

    lines.append(
        "=" * 125
    )

    lines.append(
        "FINAL FILTER13 + FILTER18 "
        "PRODUCTION CANDIDATE VALIDATION"
    )

    lines.append(
        "=" * 125
    )

    lines.append("")

    lines.append(
        "Candidates:"
    )

    lines.append(
        "- Filter13: Macro–Phase combined-cut LIMIT20"
    )

    lines.append(
        "- Filter18: Rank Persistence 3D"
    )

    lines.append(
        "- Filter15: unchanged"
    )

    lines.append(
        "- Macro persistence: rejected / not used"
    )

    lines.append("")

    display_cols = [
        "scenario",
        "annualized_turnover",
        "total_cost_pct",
        "gross_cagr",
        "net_cagr",
        "net_mdd",
        "net_volatility",
        "net_sharpe",
        "net_cagr_delta_vs_current",
        "net_mdd_delta_vs_current",
        "net_sharpe_delta_vs_current",
    ]

    lines.append(
        summary[
            display_cols
        ].to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "INTERACTION CHECK"
    )

    lines.append(
        "-----------------"
    )

    lines.append(
        f"Combined Net CAGR interaction : "
        f"{interaction_net_cagr:+.4f}%p"
    )

    lines.append(
        f"Combined Sharpe interaction   : "
        f"{interaction_sharpe:+.4f}"
    )

    lines.append("")

    lines.append(
        "FINAL PRODUCTION DECISION RULE"
    )

    lines.append(
        "------------------------------"
    )

    lines.append(
        "PASS combined candidate if:"
    )

    lines.append(
        "1. Combined net CAGR > CURRENT."
    )

    lines.append(
        "2. Combined net Sharpe > CURRENT."
    )

    lines.append(
        "3. Turnover remains materially below CURRENT."
    )

    lines.append(
        "4. MDD does not introduce unacceptable risk."
    )

    lines.append(
        "5. Filter13 + Filter18 interaction is not strongly destructive."
    )

    lines.append(
        "6. Deleveraging safety path remains unblocked."
    )

    lines.append("")

    lines.append(
        "No Production code was modified by this audit."
    )

    report = "\n".join(
        lines
    )

    TEXT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print()
    print(
        report
    )

    print()
    print(
        "Saved:"
    )

    print(
        DETAIL_PATH
    )

    print(
        SUMMARY_PATH
    )

    print(
        TEXT_PATH
    )


if __name__ == "__main__":
    main()