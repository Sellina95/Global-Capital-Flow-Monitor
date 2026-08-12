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

INPUT_PATH = (
    RESULT_DIR
    / "filter13_candidate_current_pipeline_detail.csv"
)

PRICE_PATH = (
    DATA_DIR
    / "sector_prices_filter13_candidate.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter18_rebalance_threshold_replay_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter18_rebalance_threshold_replay_summary.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter18_rebalance_threshold_replay_summary.txt"
)


# ============================================================
# Production contract
# ============================================================

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

BENCHMARK = "SPY"

SCENARIO_ORDER = [
    "BASELINE_CURRENT",
    "LIMIT_15",
    "LIMIT_20",
    "LIMIT_25",
    "LIMIT_30",
]


# ============================================================
# Performance helpers
# ============================================================

def annualized_return(returns: pd.Series) -> float:

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
# Exact production threshold semantics
# ============================================================

def apply_threshold_exact(
    target_weights: dict[str, float],
    previous_weights: dict[str, float],
) -> tuple[
    dict[str, float],
    dict[str, str],
]:

    adjusted = {}
    actions = {}

    # Production function iterates only sectors currently
    # present in target weights.
    for sector, target_w in target_weights.items():

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

        if (
            abs_diff
            < HOLD_THRESHOLD
        ):

            adjusted[
                sector
            ] = prev_w

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


# ============================================================
# Main
# ============================================================

def main() -> None:

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            INPUT_PATH
        )

    if not PRICE_PATH.exists():
        raise FileNotFoundError(
            PRICE_PATH
        )

    raw = pd.read_csv(
        INPUT_PATH
    )

    prices = pd.read_csv(
        PRICE_PATH
    )

    raw[
        "execution_date"
    ] = pd.to_datetime(
        raw[
            "execution_date"
        ],
        errors="coerce",
    )

    raw[
        "signal_date"
    ] = pd.to_datetime(
        raw[
            "signal_date"
        ],
        errors="coerce",
    )

    # ========================================================
    # Price frame
    # ========================================================

    date_col = (
        "execution_date"
        if "execution_date"
        in prices.columns
        else "date"
    )

    prices[
        date_col
    ] = pd.to_datetime(
        prices[
            date_col
        ],
        errors="coerce",
    )

    prices = (
        prices
        .dropna(
            subset=[
                date_col
            ]
        )
        .set_index(
            date_col
        )
        .sort_index()
    )

    returns = prices.pct_change(
        fill_method=None
    )

    # ========================================================
    # Weight universe
    # ========================================================

    weight_cols = [
        col
        for col in raw.columns
        if col.startswith(
            "weight__"
        )
    ]

    sectors = [
        col.replace(
            "weight__",
            "",
            1,
        )
        for col
        in weight_cols
    ]

    print()
    print(
        "=" * 115
    )

    print(
        "FILTER18 PRODUCTION REBALANCE "
        "THRESHOLD SEQUENTIAL REPLAY"
    )

    print(
        "=" * 115
    )

    print()

    print(
        f"Rows                  : "
        f"{len(raw):,}"
    )

    print(
        f"Sector columns        : "
        f"{len(weight_cols)}"
    )

    print(
        f"Production thresholds : "
        f"HOLD < {HOLD_THRESHOLD:.1f}%p / "
        f"REBALANCE >= {REBALANCE_THRESHOLD:.1f}%p"
    )

    # ========================================================
    # Scenario replay
    # ========================================================

    all_rows = []

    summary_rows = []

    for scenario in SCENARIO_ORDER:

        df = (
            raw[
                raw[
                    "scenario"
                ]
                == scenario
            ]
            .copy()
            .sort_values(
                "execution_date"
            )
            .reset_index(
                drop=True
            )
        )

        if df.empty:
            continue

        # Historical sequential state:
        # yesterday's EXECUTED sector weights.
        previous_executed = {}

        target_previous = {}

        replay_rows = []

        for _, row in df.iterrows():

            # ------------------------------------------------
            # Target weights captured by backtest builder
            # ------------------------------------------------

            target_weights = {}

            for col in weight_cols:

                sector = col.replace(
                    "weight__",
                    "",
                    1,
                )

                value = pd.to_numeric(
                    row.get(
                        col
                    ),
                    errors="coerce",
                )

                if pd.notna(
                    value
                ):

                    target_weights[
                        sector
                    ] = float(
                        value
                    )

            # ------------------------------------------------
            # Target turnover:
            # what previous audits measured
            # ------------------------------------------------

            target_turnover = (
                calculate_turnover(
                    current=target_weights,
                    previous=target_previous,
                    universe=sectors,
                )
            )

            # ------------------------------------------------
            # Production-equivalent sequential threshold
            # ------------------------------------------------

            executed_weights, actions = (
                apply_threshold_exact(
                    target_weights=target_weights,
                    previous_weights=(
                        previous_executed
                    ),
                )
            )

            executed_turnover = (
                calculate_turnover(
                    current=executed_weights,
                    previous=previous_executed,
                    universe=sectors,
                )
            )

            # ------------------------------------------------
            # Action counts
            # ------------------------------------------------

            hold_count = sum(
                1
                for value in actions.values()
                if value == "HOLD"
            )

            small_adjust_count = sum(
                1
                for value in actions.values()
                if value == "SMALL ADJUST"
            )

            rebalance_count = sum(
                1
                for value in actions.values()
                if value == "REBALANCE"
            )

            new_count = sum(
                1
                for value in actions.values()
                if value == "NEW"
            )

            # ------------------------------------------------
            # P&L
            # ------------------------------------------------

            execution_date = row[
                "execution_date"
            ]

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

                    r = returns.at[
                        execution_date,
                        ticker,
                    ]

                    if pd.isna(r):
                        continue

                    gross_return += (
                        float(
                            weight_pct
                        )
                        / 100.0
                        * float(r)
                    )

            transaction_cost = (
                executed_turnover
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

            result = {
                "scenario":
                    scenario,

                "signal_date":
                    row[
                        "signal_date"
                    ],

                "execution_date":
                    execution_date,

                "risk_budget_13":
                    row[
                        "risk_budget_13"
                    ],

                "exposure_15":
                    row[
                        "exposure_15"
                    ],

                "target_turnover":
                    target_turnover,

                "executed_turnover":
                    executed_turnover,

                "turnover_reduction":
                    (
                        target_turnover
                        - executed_turnover
                    ),

                "hold_count":
                    hold_count,

                "small_adjust_count":
                    small_adjust_count,

                "rebalance_count":
                    rebalance_count,

                "new_count":
                    new_count,

                "executed_allocated_equity":
                    sum(
                        executed_weights.values()
                    ),

                "executed_cash_weight":
                    100.0
                    - sum(
                        executed_weights.values()
                    ),

                "transaction_cost":
                    transaction_cost,

                "strategy_return_gross":
                    gross_return,

                "strategy_return_net":
                    net_return,
            }

            for sector in sectors:

                result[
                    f"target__{sector}"
                ] = (
                    target_weights.get(
                        sector,
                        0.0,
                    )
                )

                result[
                    f"executed__{sector}"
                ] = (
                    executed_weights.get(
                        sector,
                        0.0,
                    )
                )

                result[
                    f"action__{sector}"
                ] = (
                    actions.get(
                        sector,
                        "REMOVED",
                    )
                )

            replay_rows.append(
                result
            )

            target_previous = (
                target_weights
            )

            previous_executed = (
                executed_weights
            )

        replay = pd.DataFrame(
            replay_rows
        )

        all_rows.append(
            replay
        )

        # ====================================================
        # Scenario summary
        # ====================================================

        gross = pd.to_numeric(
            replay[
                "strategy_return_gross"
            ],
            errors="coerce",
        )

        net = pd.to_numeric(
            replay[
                "strategy_return_net"
            ],
            errors="coerce",
        )

        target_ann_turnover = (
            replay[
                "target_turnover"
            ].mean()
            * TRADING_DAYS
        )

        executed_ann_turnover = (
            replay[
                "executed_turnover"
            ].mean()
            * TRADING_DAYS
        )

        reduction_rate = (
            1.0
            - (
                executed_ann_turnover
                / target_ann_turnover
            )
            if target_ann_turnover > 0
            else np.nan
        )

        summary_rows.append(
            {
                "scenario":
                    scenario,

                "days":
                    len(
                        replay
                    ),

                "target_annualized_turnover":
                    target_ann_turnover,

                "executed_annualized_turnover":
                    executed_ann_turnover,

                "turnover_reduction_rate":
                    reduction_rate,

                "avg_hold_count":
                    replay[
                        "hold_count"
                    ].mean(),

                "avg_small_adjust_count":
                    replay[
                        "small_adjust_count"
                    ].mean(),

                "avg_rebalance_count":
                    replay[
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

                "total_cost_pct":
                    replay[
                        "transaction_cost"
                    ].sum()
                    * 100.0,
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
    # Baseline deltas
    # ========================================================

    baseline = (
        summary[
            summary[
                "scenario"
            ]
            == "BASELINE_CURRENT"
        ]
        .iloc[0]
    )

    for metric in [
        "executed_annualized_turnover",
        "net_cagr",
        "net_mdd",
        "net_volatility",
        "net_sharpe",
        "total_cost_pct",
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
        "FILTER18 PRODUCTION REBALANCE "
        "THRESHOLD SEQUENTIAL REPLAY"
    )

    lines.append(
        "=" * 125
    )

    lines.append("")

    lines.append(
        "Important:"
    )

    lines.append(
        "Target weights = build_tactical_allocation output."
    )

    lines.append(
        "Executed weights = target weights after exact "
        "Production apply_rebalance_threshold semantics."
    )

    lines.append("")

    display_cols = [
        "scenario",

        "target_annualized_turnover",
        "executed_annualized_turnover",
        "turnover_reduction_rate",

        "avg_hold_count",
        "avg_small_adjust_count",
        "avg_rebalance_count",

        "gross_cagr",
        "net_cagr",
        "net_mdd",
        "net_sharpe",

        "total_cost_pct",
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
        "Decision:"
    )

    lines.append(
        "- If executed turnover is materially below target turnover, "
        "previous turnover audits were measuring target churn rather "
        "than Production execution churn."
    )

    lines.append(
        "- Only executed turnover should be used for subsequent "
        "Filter18 attribution and cost analysis."
    )

    lines.append(
        "- Production code remains unchanged."
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