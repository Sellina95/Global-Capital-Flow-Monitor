from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data" / "backtest"
RESULT_DIR = DATA_DIR / "results"

# Target weights + previous threshold replay
REPLAY_PATH = (
    RESULT_DIR
    / "filter18_rebalance_threshold_replay_detail.csv"
)

# Rank signature + deleveraging_required
ATTR_PATH = (
    RESULT_DIR
    / "filter18_rotation_rule_attribution_detail.csv"
)

# Canonical ETF prices already downloaded
PRICE_PATH = (
    DATA_DIR
    / "sector_prices_filter13_candidate.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter18_rank_persistence_counterfactual_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter18_rank_persistence_counterfactual_summary.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter18_rank_persistence_counterfactual_summary.txt"
)


# ============================================================
# Production contract
# ============================================================

HOLD_THRESHOLD = 2.0
REBALANCE_THRESHOLD = 5.0

COST_BPS_ONE_WAY = 5.0
TRADING_DAYS = 252

SCENARIO_SOURCE = "BASELINE_CURRENT"

PERSISTENCE_WINDOWS = [
    1,
    2,
    3,
    5,
]


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

BENCHMARK = "SPY"


# ============================================================
# Performance helpers
# ============================================================

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
        (1.0 + clean).prod()
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
        total ** (1.0 / years)
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
        clean.std(ddof=1)
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
        + clean.fillna(0.0)
    ).cumprod()

    peak = wealth.cummax()

    drawdown = (
        wealth
        / peak
        - 1.0
    )

    return float(
        drawdown.min()
    )


# ============================================================
# Exact Production rebalance threshold
# ============================================================

def apply_rebalance_threshold_exact(
    target_weights: dict[str, float],
    previous_weights: dict[str, float],
) -> tuple[
    dict[str, float],
    dict[str, str],
]:

    adjusted_weights = {}
    rebalance_actions = {}

    for sector, target_w in (
        target_weights.items()
    ):

        prev_w = (
            previous_weights.get(
                sector
            )
        )

        if prev_w is None:

            adjusted_weights[
                sector
            ] = target_w

            rebalance_actions[
                sector
            ] = "NEW"

            continue

        diff = (
            target_w
            - prev_w
        )

        abs_diff = abs(
            diff
        )

        if (
            abs_diff
            < HOLD_THRESHOLD
        ):

            adjusted_weights[
                sector
            ] = prev_w

            rebalance_actions[
                sector
            ] = "HOLD"

        elif (
            abs_diff
            < REBALANCE_THRESHOLD
        ):

            adjusted_weights[
                sector
            ] = target_w

            rebalance_actions[
                sector
            ] = "SMALL ADJUST"

        else:

            adjusted_weights[
                sector
            ] = target_w

            rebalance_actions[
                sector
            ] = "REBALANCE"

    adjusted_weights = {
        sector:
            round(
                weight,
                1,
            )

        for sector, weight
        in adjusted_weights.items()
    }

    return (
        adjusted_weights,
        rebalance_actions,
    )


# ============================================================
# Turnover
# ============================================================

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
            for sector in universe
        )
        / 100.0
    )


# ============================================================
# Reconstruct source target weights
#
# target__sector is 0 even when sector was absent.
# action__sector == REMOVED tells us it was NOT present
# in original target dict.
# ============================================================

def reconstruct_source_target(
    row: pd.Series,
    sectors: list[str],
) -> dict[str, float]:

    result = {}

    for sector in sectors:

        action_col = (
            f"action__{sector}"
        )

        target_col = (
            f"target__{sector}"
        )

        action = str(
            row.get(
                action_col,
                "REMOVED",
            )
        ).upper()

        if action == "REMOVED":
            continue

        value = pd.to_numeric(
            row.get(
                target_col
            ),
            errors="coerce",
        )

        if pd.isna(value):
            continue

        result[
            sector
        ] = float(
            value
        )

    return result


# ============================================================
# Main
# ============================================================

def main() -> None:

    for path in [
        REPLAY_PATH,
        ATTR_PATH,
        PRICE_PATH,
    ]:

        if not path.exists():
            raise FileNotFoundError(
                path
            )

    # ========================================================
    # Load
    # ========================================================

    replay = pd.read_csv(
        REPLAY_PATH
    )

    attr = pd.read_csv(
        ATTR_PATH
    )

    prices = pd.read_csv(
        PRICE_PATH
    )

    replay = (
        replay[
            replay[
                "scenario"
            ]
            == SCENARIO_SOURCE
        ]
        .copy()
    )

    for df in [
        replay,
        attr,
    ]:

        df[
            "signal_date"
        ] = pd.to_datetime(
            df[
                "signal_date"
            ],
            errors="coerce",
        )

        df[
            "execution_date"
        ] = pd.to_datetime(
            df[
                "execution_date"
            ],
            errors="coerce",
        )

    # ========================================================
    # Merge rank / deleveraging provenance
    # ========================================================

    required_attr = [
        "signal_date",
        "execution_date",
        "rank_signature",
        "deleveraging_required",
    ]

    missing_attr = [
        col
        for col in required_attr
        if col not in attr.columns
    ]

    if missing_attr:

        raise ValueError(
            "Attribution detail missing:\n"
            f"{missing_attr}"
        )

    df = replay.merge(
        attr[
            required_attr
        ],
        on=[
            "signal_date",
            "execution_date",
        ],
        how="inner",
    )

    df = (
        df
        .sort_values(
            "execution_date"
        )
        .reset_index(
            drop=True
        )
    )

    if df.empty:

        raise RuntimeError(
            "Replay / attribution overlap is empty."
        )

    # ========================================================
    # Sector universe
    # ========================================================

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

    print()
    print(
        "=" * 120
    )

    print(
        "FILTER18 RANK PERSISTENCE COUNTERFACTUAL"
    )

    print(
        "=" * 120
    )

    print()

    print(
        f"Rows                : "
        f"{len(df):,}"
    )

    print(
        f"Sector count        : "
        f"{len(sectors)}"
    )

    print(
        f"Persistence windows : "
        f"{PERSISTENCE_WINDOWS}"
    )

    print()

    print(
        "Production safety rule:"
    )

    print(
        "DELEVERAGING_REQUIRED always bypasses "
        "rank persistence and rebalance threshold."
    )

    # ========================================================
    # Price frame
    # ========================================================

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
            "ETF price date column missing."
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

    returns = prices.pct_change(
        fill_method=None
    )

    # ========================================================
    # Scenario replay
    # ========================================================

    all_scenario_rows = []

    summary_rows = []

    for persistence_days in (
        PERSISTENCE_WINDOWS
    ):

        scenario = (
            "BASELINE_1D"
            if persistence_days == 1
            else f"PERSIST_{persistence_days}D"
        )

        # ----------------------------------------------------
        # Sequential state
        # ----------------------------------------------------

        previous_executed = {}

        accepted_rank = None
        accepted_target = {}

        pending_rank = None
        pending_count = 0

        rows = []

        suppressed_days = 0
        confirmation_days = 0
        forced_deleveraging_days = 0

        for _, row in df.iterrows():

            current_rank = str(
                row.get(
                    "rank_signature",
                    "",
                )
                or ""
            )

            source_target = (
                reconstruct_source_target(
                    row,
                    sectors,
                )
            )

            deleveraging_required = bool(
                row.get(
                    "deleveraging_required",
                    False,
                )
            )

            # =================================================
            # First observation
            # =================================================

            if accepted_rank is None:

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

                persistence_action = (
                    "INITIAL_ACCEPT"
                )

            # =================================================
            # Risk override:
            # deleveraging must NEVER be delayed
            # =================================================

            elif deleveraging_required:

                forced_deleveraging_days += 1

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

                persistence_action = (
                    "FORCED_DELEVERAGE_ACCEPT"
                )

            # =================================================
            # Baseline 1D:
            # accept every current ranking immediately
            # =================================================

            elif persistence_days == 1:

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

                persistence_action = (
                    "IMMEDIATE_ACCEPT"
                )

            # =================================================
            # Same rank as accepted
            #
            # IMPORTANT:
            # Weight changes caused by macro/caps/etc are still
            # allowed when rank itself has not changed.
            # =================================================

            elif current_rank == accepted_rank:

                accepted_target = dict(
                    source_target
                )

                pending_rank = None
                pending_count = 0

                target_for_execution = dict(
                    source_target
                )

                persistence_action = (
                    "ACCEPTED_RANK_UPDATE"
                )

            # =================================================
            # New ranking candidate
            # =================================================

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

                # ---------------------------------------------
                # Confirmation
                # ---------------------------------------------

                if (
                    pending_count
                    >= persistence_days
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

                    persistence_action = (
                        "RANK_CONFIRMED"
                    )

                    confirmation_days += 1

                # ---------------------------------------------
                # Not confirmed yet:
                # maintain previously accepted target
                # ---------------------------------------------

                else:

                    target_for_execution = dict(
                        accepted_target
                    )

                    persistence_action = (
                        "RANK_CHANGE_SUPPRESSED"
                    )

                    suppressed_days += 1

            # =================================================
            # Production execution
            # =================================================

            if deleveraging_required:

                # Production bypasses threshold entirely.
                executed_weights = {
                    sector:
                        round(
                            weight,
                            1,
                        )

                    for sector, weight
                    in target_for_execution.items()
                }

                actions = {
                    sector:
                        "DELEVERAGE"

                    for sector
                    in executed_weights
                }

            else:

                executed_weights, actions = (
                    apply_rebalance_threshold_exact(
                        target_weights=(
                            target_for_execution
                        ),
                        previous_weights=(
                            previous_executed
                        ),
                    )
                )

            # =================================================
            # Turnover
            # =================================================

            turnover = (
                calculate_turnover(
                    current=(
                        executed_weights
                    ),
                    previous=(
                        previous_executed
                    ),
                    universe=sectors,
                )
            )

            # =================================================
            # P&L
            # =================================================

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
                in returns.index
            ):

                gross_return = 0.0

                for sector, weight_pct in (
                    executed_weights.items()
                ):

                    ticker = (
                        SECTOR_TO_ETF.get(
                            sector
                        )
                    )

                    if (
                        ticker is None
                        or ticker
                        not in returns.columns
                    ):
                        continue

                    ticker_return = (
                        returns.at[
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

            # =================================================
            # Action counts
            # =================================================

            hold_count = sum(
                1
                for action
                in actions.values()
                if action == "HOLD"
            )

            small_adjust_count = sum(
                1
                for action
                in actions.values()
                if action == "SMALL ADJUST"
            )

            rebalance_count = sum(
                1
                for action
                in actions.values()
                if action == "REBALANCE"
            )

            result = {
                "scenario":
                    scenario,

                "persistence_days":
                    persistence_days,

                "signal_date":
                    row[
                        "signal_date"
                    ],

                "execution_date":
                    execution_date,

                "current_rank":
                    current_rank,

                "accepted_rank":
                    accepted_rank,

                "pending_rank":
                    pending_rank,

                "pending_count":
                    pending_count,

                "persistence_action":
                    persistence_action,

                "deleveraging_required":
                    deleveraging_required,

                "turnover":
                    turnover,

                "transaction_cost":
                    transaction_cost,

                "strategy_return_gross":
                    gross_return,

                "strategy_return_net":
                    net_return,

                "hold_count":
                    hold_count,

                "small_adjust_count":
                    small_adjust_count,

                "rebalance_count":
                    rebalance_count,

                "executed_allocated_equity":
                    sum(
                        executed_weights.values()
                    ),

                "executed_cash_weight":
                    (
                        100.0
                        - sum(
                            executed_weights.values()
                        )
                    ),
            }

            for sector in sectors:

                result[
                    f"executed__{sector}"
                ] = (
                    executed_weights.get(
                        sector,
                        0.0,
                    )
                )

            rows.append(
                result
            )

            previous_executed = dict(
                executed_weights
            )

        # ====================================================
        # Scenario frame
        # ====================================================

        replay_scenario = (
            pd.DataFrame(
                rows
            )
        )

        all_scenario_rows.append(
            replay_scenario
        )

        gross = pd.to_numeric(
            replay_scenario[
                "strategy_return_gross"
            ],
            errors="coerce",
        )

        net = pd.to_numeric(
            replay_scenario[
                "strategy_return_net"
            ],
            errors="coerce",
        )

        ann_turnover = (
            replay_scenario[
                "turnover"
            ].mean()
            * TRADING_DAYS
        )

        total_cost_pct = (
            replay_scenario[
                "transaction_cost"
            ].sum()
            * 100.0
        )

        summary_rows.append(
            {
                "scenario":
                    scenario,

                "persistence_days":
                    persistence_days,

                "days":
                    len(
                        replay_scenario
                    ),

                "annualized_turnover":
                    ann_turnover,

                "total_cost_pct":
                    total_cost_pct,

                "avg_hold_count":
                    replay_scenario[
                        "hold_count"
                    ].mean(),

                "avg_small_adjust_count":
                    replay_scenario[
                        "small_adjust_count"
                    ].mean(),

                "avg_rebalance_count":
                    replay_scenario[
                        "rebalance_count"
                    ].mean(),

                "suppressed_rank_days":
                    suppressed_days,

                "rank_confirmation_days":
                    confirmation_days,

                "forced_deleveraging_days":
                    forced_deleveraging_days,

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
        )

    # ========================================================
    # Combine
    # ========================================================

    detail = pd.concat(
        all_scenario_rows,
        ignore_index=True,
        sort=False,
    )

    summary = pd.DataFrame(
        summary_rows
    )

    # ========================================================
    # Baseline comparison
    # ========================================================

    baseline = (
        summary[
            summary[
                "scenario"
            ]
            == "BASELINE_1D"
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
            f"{metric}_delta"
        ] = (
            summary[
                metric
            ]
            - baseline[
                metric
            ]
        )

    summary[
        "turnover_reduction_rate"
    ] = (
        1.0
        -
        (
            summary[
                "annualized_turnover"
            ]
            /
            baseline[
                "annualized_turnover"
            ]
        )
    )

    # ========================================================
    # Compare corrected baseline to OLD threshold replay
    #
    # This quantifies prior semantic error from applying
    # threshold on deleveraging days.
    # ========================================================

    old_baseline_turnover = (
        pd.to_numeric(
            df[
                "executed_turnover"
            ],
            errors="coerce",
        )
        .mean()
        * TRADING_DAYS
    )

    corrected_baseline_turnover = float(
        baseline[
            "annualized_turnover"
        ]
    )

    old_vs_corrected_delta = (
        corrected_baseline_turnover
        - old_baseline_turnover
    )

    # ========================================================
    # Save
    # ========================================================

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
    # Report
    # ========================================================

    lines = []

    lines.append(
        "=" * 125
    )

    lines.append(
        "FILTER18 RANK PERSISTENCE COUNTERFACTUAL"
    )

    lines.append(
        "=" * 125
    )

    lines.append("")

    lines.append(
        "Production semantics:"
    )

    lines.append(
        "- Normal days: apply exact 2%p / 5%p rebalance threshold."
    )

    lines.append(
        "- Deleveraging days: BYPASS threshold exactly as Production."
    )

    lines.append(
        "- Rank persistence NEVER blocks deleveraging."
    )

    lines.append("")

    lines.append(
        f"Old threshold replay turnover : "
        f"{old_baseline_turnover:.2f}x"
    )

    lines.append(
        f"Corrected baseline turnover   : "
        f"{corrected_baseline_turnover:.2f}x"
    )

    lines.append(
        f"Correction delta              : "
        f"{old_vs_corrected_delta:+.2f}x"
    )

    lines.append("")

    display_cols = [
        "scenario",
        "persistence_days",

        "annualized_turnover",
        "turnover_reduction_rate",
        "total_cost_pct",

        "suppressed_rank_days",
        "rank_confirmation_days",
        "forced_deleveraging_days",

        "gross_cagr",
        "net_cagr",
        "net_mdd",
        "net_volatility",
        "net_sharpe",

        "net_cagr_delta",
        "net_mdd_delta",
        "net_sharpe_delta",
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
        "Decision Rules:"
    )

    lines.append(
        "1. Persistence must materially reduce executed turnover."
    )

    lines.append(
        "2. Net CAGR / Sharpe must not deteriorate materially."
    )

    lines.append(
        "3. MDD must remain acceptable."
    )

    lines.append(
        "4. Prefer a broad 2D/3D/5D plateau, not one magic parameter."
    )

    lines.append(
        "5. Deleveraging safety override must remain untouched."
    )

    lines.append(
        "6. This is a research counterfactual only. "
        "Production code remains unchanged."
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