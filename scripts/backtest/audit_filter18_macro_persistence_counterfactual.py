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

# Target weights
REPLAY_PATH = (
    RESULT_DIR
    / "filter18_rebalance_threshold_replay_detail.csv"
)

# Rank / Macro / Deleveraging provenance
ATTR_PATH = (
    RESULT_DIR
    / "filter18_rotation_rule_attribution_detail.csv"
)

# Canonical ETF prices
PRICE_PATH = (
    DATA_DIR
    / "sector_prices_filter13_candidate.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter18_macro_persistence_counterfactual_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter18_macro_persistence_counterfactual_summary.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter18_macro_persistence_counterfactual_summary.txt"
)


# ============================================================
# Research contract
# ============================================================

SCENARIO_SOURCE = "BASELINE_CURRENT"

# Rank persistence already validated.
RANK_PERSISTENCE_DAYS = 3

MACRO_WINDOWS = [
    1,
    2,
    3,
    5,
]

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

    if years <= 0 or total <= 0:
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
        * math.sqrt(TRADING_DAYS)
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

    std = clean.std(ddof=1)

    if std == 0:
        return np.nan

    return float(
        clean.mean()
        / std
        * math.sqrt(TRADING_DAYS)
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

    return float(
        (
            wealth
            / peak
            - 1.0
        ).min()
    )


# ============================================================
# Exact Production threshold
# ============================================================

def apply_rebalance_threshold_exact(
    target_weights: dict[str, float],
    previous_weights: dict[str, float],
) -> tuple[
    dict[str, float],
    dict[str, str],
]:

    adjusted = {}
    actions = {}

    for sector, target_w in (
        target_weights.items()
    ):

        prev_w = previous_weights.get(
            sector
        )

        if prev_w is None:

            adjusted[
                sector
            ] = target_w

            actions[
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

        if abs_diff < HOLD_THRESHOLD:

            adjusted[
                sector
            ] = prev_w

            actions[
                sector
            ] = "HOLD"

        elif abs_diff < REBALANCE_THRESHOLD:

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
            for sector
            in universe
        )
        / 100.0
    )


# ============================================================
# Reconstruct original target dict
# ============================================================

def reconstruct_source_target(
    row: pd.Series,
    sectors: list[str],
) -> dict[str, float]:

    result = {}

    for sector in sectors:

        action = str(
            row.get(
                f"action__{sector}",
                "REMOVED",
            )
        ).upper()

        if action == "REMOVED":
            continue

        value = pd.to_numeric(
            row.get(
                f"target__{sector}"
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

    for frame in [
        replay,
        attr,
    ]:

        frame[
            "signal_date"
        ] = pd.to_datetime(
            frame[
                "signal_date"
            ],
            errors="coerce",
        )

        frame[
            "execution_date"
        ] = pd.to_datetime(
            frame[
                "execution_date"
            ],
            errors="coerce",
        )

    # ========================================================
    # Merge provenance
    # ========================================================

    required_attr = [
        "signal_date",
        "execution_date",
        "rank_signature",
        "macro_profile",
        "deleveraging_required",
    ]

    missing_attr = [
        col
        for col in required_attr
        if col not in attr.columns
    ]

    if missing_attr:

        raise ValueError(
            "Attribution file missing:\n"
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
            "Replay / attribution overlap empty."
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

        price_date_col = "date"

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
    # Header
    # ========================================================

    print()
    print(
        "=" * 120
    )

    print(
        "FILTER18 MACRO PROFILE PERSISTENCE COUNTERFACTUAL"
    )

    print(
        "=" * 120
    )

    print()

    print(
        f"Rows                    : "
        f"{len(df):,}"
    )

    print(
        f"Rank persistence fixed  : "
        f"{RANK_PERSISTENCE_DAYS}D"
    )

    print(
        f"Macro windows           : "
        f"{MACRO_WINDOWS}"
    )

    print()

    print(
        "Safety override:"
    )

    print(
        "DELEVERAGING_REQUIRED bypasses both "
        "rank and macro persistence."
    )

    # ========================================================
    # Scenario loop
    # ========================================================

    all_rows = []

    summary_rows = []

    for macro_days in MACRO_WINDOWS:

        scenario = (
            "RANK3D_ONLY"
            if macro_days == 1
            else (
                f"RANK3D_MACRO{macro_days}D"
            )
        )

        # ----------------------------------------------------
        # Sequential execution state
        # ----------------------------------------------------

        previous_executed = {}

        # Accepted state
        accepted_rank = None
        accepted_macro = None
        accepted_target = {}

        # Pending rank state
        pending_rank = None
        pending_rank_count = 0

        # Pending macro state
        pending_macro = None
        pending_macro_count = 0

        suppressed_rank_days = 0
        suppressed_macro_days = 0

        rank_confirmation_days = 0
        macro_confirmation_days = 0

        forced_deleveraging_days = 0

        rows = []

        for _, row in df.iterrows():

            current_rank = str(
                row.get(
                    "rank_signature",
                    "",
                )
                or ""
            )

            current_macro = str(
                row.get(
                    "macro_profile",
                    "BALANCED",
                )
                or "BALANCED"
            ).upper()

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
            # Initial observation
            # =================================================

            if accepted_rank is None:

                accepted_rank = current_rank
                accepted_macro = current_macro

                accepted_target = dict(
                    source_target
                )

                target_for_execution = dict(
                    source_target
                )

                rank_action = (
                    "INITIAL_ACCEPT"
                )

                macro_action = (
                    "INITIAL_ACCEPT"
                )

            # =================================================
            # Safety override
            # =================================================

            elif deleveraging_required:

                forced_deleveraging_days += 1

                accepted_rank = current_rank
                accepted_macro = current_macro

                accepted_target = dict(
                    source_target
                )

                pending_rank = None
                pending_rank_count = 0

                pending_macro = None
                pending_macro_count = 0

                target_for_execution = dict(
                    source_target
                )

                rank_action = (
                    "FORCED_DELEVERAGE_ACCEPT"
                )

                macro_action = (
                    "FORCED_DELEVERAGE_ACCEPT"
                )

            else:

                # =================================================
                # Rank persistence
                # =================================================

                rank_confirmed = False

                if current_rank == accepted_rank:

                    pending_rank = None
                    pending_rank_count = 0

                    rank_confirmed = True

                    rank_action = (
                        "ACCEPTED_RANK"
                    )

                else:

                    if pending_rank == current_rank:

                        pending_rank_count += 1

                    else:

                        pending_rank = current_rank
                        pending_rank_count = 1

                    if (
                        pending_rank_count
                        >= RANK_PERSISTENCE_DAYS
                    ):

                        accepted_rank = (
                            current_rank
                        )

                        pending_rank = None
                        pending_rank_count = 0

                        rank_confirmed = True

                        rank_confirmation_days += 1

                        rank_action = (
                            "RANK_CONFIRMED"
                        )

                    else:

                        rank_confirmed = False

                        suppressed_rank_days += 1

                        rank_action = (
                            "RANK_CHANGE_SUPPRESSED"
                        )

                # =================================================
                # Macro persistence
                # =================================================

                macro_confirmed = False

                if macro_days == 1:

                    accepted_macro = (
                        current_macro
                    )

                    pending_macro = None
                    pending_macro_count = 0

                    macro_confirmed = True

                    macro_action = (
                        "IMMEDIATE_ACCEPT"
                    )

                elif (
                    current_macro
                    == accepted_macro
                ):

                    pending_macro = None
                    pending_macro_count = 0

                    macro_confirmed = True

                    macro_action = (
                        "ACCEPTED_MACRO"
                    )

                else:

                    if (
                        pending_macro
                        == current_macro
                    ):

                        pending_macro_count += 1

                    else:

                        pending_macro = (
                            current_macro
                        )

                        pending_macro_count = 1

                    if (
                        pending_macro_count
                        >= macro_days
                    ):

                        accepted_macro = (
                            current_macro
                        )

                        pending_macro = None
                        pending_macro_count = 0

                        macro_confirmed = True

                        macro_confirmation_days += 1

                        macro_action = (
                            "MACRO_CONFIRMED"
                        )

                    else:

                        macro_confirmed = False

                        suppressed_macro_days += 1

                        macro_action = (
                            "MACRO_CHANGE_SUPPRESSED"
                        )

                # =================================================
                # Target acceptance
                #
                # We only accept today's target if BOTH
                # persistence gates permit it.
                #
                # This is an operational counterfactual,
                # not a pure causal decomposition.
                # =================================================

                if (
                    rank_confirmed
                    and macro_confirmed
                ):

                    accepted_target = dict(
                        source_target
                    )

                    target_for_execution = dict(
                        source_target
                    )

                else:

                    target_for_execution = dict(
                        accepted_target
                    )

            # =================================================
            # Production execution semantics
            # =================================================

            if deleveraging_required:

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
                    current=executed_weights,
                    previous=previous_executed,
                    universe=sectors,
                )
            )

            # =================================================
            # Performance
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
                for action in actions.values()
                if action == "HOLD"
            )

            small_adjust_count = sum(
                1
                for action in actions.values()
                if action == "SMALL ADJUST"
            )

            rebalance_count = sum(
                1
                for action in actions.values()
                if action == "REBALANCE"
            )

            result = {
                "scenario":
                    scenario,

                "macro_persistence_days":
                    macro_days,

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

                "rank_action":
                    rank_action,

                "current_macro":
                    current_macro,

                "accepted_macro":
                    accepted_macro,

                "macro_action":
                    macro_action,

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

            rows.append(
                result
            )

            previous_executed = dict(
                executed_weights
            )

        # ====================================================
        # Scenario results
        # ====================================================

        replay_scenario = pd.DataFrame(
            rows
        )

        all_rows.append(
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

                "macro_persistence_days":
                    macro_days,

                "days":
                    len(
                        replay_scenario
                    ),

                "annualized_turnover":
                    ann_turnover,

                "total_cost_pct":
                    total_cost_pct,

                "suppressed_rank_days":
                    suppressed_rank_days,

                "rank_confirmation_days":
                    rank_confirmation_days,

                "suppressed_macro_days":
                    suppressed_macro_days,

                "macro_confirmation_days":
                    macro_confirmation_days,

                "forced_deleveraging_days":
                    forced_deleveraging_days,

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
        all_rows,
        ignore_index=True,
        sort=False,
    )

    summary = pd.DataFrame(
        summary_rows
    )

    # ========================================================
    # Baseline = Rank 3D only
    # ========================================================

    baseline = (
        summary[
            summary[
                "scenario"
            ]
            == "RANK3D_ONLY"
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
        "incremental_turnover_reduction"
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
        "FILTER18 MACRO PROFILE PERSISTENCE COUNTERFACTUAL"
    )

    lines.append(
        "=" * 125
    )

    lines.append("")

    lines.append(
        f"Rank persistence fixed at "
        f"{RANK_PERSISTENCE_DAYS}D."
    )

    lines.append(
        "Macro persistence is tested only for "
        "incremental value after Rank 3D."
    )

    lines.append("")

    lines.append(
        "Risk safety:"
    )

    lines.append(
        "DELEVERAGING_REQUIRED bypasses all persistence gates."
    )

    lines.append("")

    display_cols = [
        "scenario",
        "macro_persistence_days",

        "annualized_turnover",
        "incremental_turnover_reduction",
        "total_cost_pct",

        "suppressed_macro_days",
        "macro_confirmation_days",
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
        "1. Compare all scenarios against RANK3D_ONLY."
    )

    lines.append(
        "2. Macro persistence should deliver meaningful "
        "incremental turnover/cost reduction."
    )

    lines.append(
        "3. Net CAGR / Sharpe must not deteriorate materially."
    )

    lines.append(
        "4. MDD must remain acceptable."
    )

    lines.append(
        "5. If incremental benefit is small, do NOT add "
        "another Production state machine."
    )

    lines.append(
        "6. Prefer the simpler Rank Persistence-only design "
        "when performance is economically equivalent."
    )

    lines.append(
        "7. Production code remains unchanged."
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