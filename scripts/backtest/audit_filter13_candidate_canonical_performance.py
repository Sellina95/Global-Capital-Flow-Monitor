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

# 이미 오래 돌려서 만든 13→15→18 결과
INPUT_PATH = (
    RESULT_DIR
    / "filter13_candidate_current_pipeline_detail.csv"
)

# 직전 audit에서 이미 다운로드한 canonical ETF 가격
PRICE_PATH = (
    DATA_DIR
    / "sector_prices_filter13_candidate.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter13_candidate_canonical_performance_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_candidate_canonical_performance_summary.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter13_candidate_canonical_performance_summary.txt"
)


# ============================================================
# Exact performance.py contract
# ============================================================

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

COST_BPS_ONE_WAY = 5.0
TRADING_DAYS = 252

SCENARIO_ORDER = [
    "BASELINE_CURRENT",
    "LIMIT_15",
    "LIMIT_20",
    "LIMIT_25",
    "LIMIT_30",
]


# ============================================================
# Performance helpers
# Exact performance.py semantics
# ============================================================

def max_drawdown(
    returns: pd.Series,
) -> float:

    wealth = (
        1.0
        + returns.fillna(0.0)
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


def annualized_return(
    returns: pd.Series,
) -> float:

    clean = returns.dropna()

    if clean.empty:
        return float("nan")

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
        return float("nan")

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

    clean = returns.dropna()

    if len(clean) < 2:
        return float("nan")

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

    clean = returns.dropna()

    if len(clean) < 2:
        return float("nan")

    vol = clean.std(
        ddof=1
    )

    if vol == 0:
        return float("nan")

    return float(
        clean.mean()
        / vol
        * math.sqrt(
            TRADING_DAYS
        )
    )


# ============================================================
# CRITICAL:
#
# Filter18 weights are percentage points.
#
# performance.py does:
#
# float(weight) / 100.0
#
# NO heuristic.
# NO >1.5 test.
# ============================================================

def canonical_weight(
    value,
) -> float:

    x = pd.to_numeric(
        value,
        errors="coerce",
    )

    if pd.isna(x):
        return 0.0

    return (
        float(x)
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
            f"{PRICE_PATH}\n"
            "직전 P&L audit에서 만든 ETF 가격 파일이 없습니다."
        )

    # ========================================================
    # Load
    # ========================================================

    positions = pd.read_csv(
        INPUT_PATH
    )

    prices = pd.read_csv(
        PRICE_PATH
    )

    positions[
        "signal_date"
    ] = pd.to_datetime(
        positions[
            "signal_date"
        ],
        errors="coerce",
    )

    positions[
        "execution_date"
    ] = pd.to_datetime(
        positions[
            "execution_date"
        ],
        errors="coerce",
    )

    # ========================================================
    # Price frame
    # ========================================================

    date_col = None

    for candidate in [
        "execution_date",
        "date",
    ]:

        if candidate in prices.columns:

            date_col = candidate
            break

    if date_col is None:

        raise ValueError(
            "ETF price file에서 날짜 컬럼을 찾지 못했습니다."
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

    # performance.py:
    # returns = prices.pct_change(fill_method=None)
    returns = prices.pct_change(
        fill_method=None
    )

    # ========================================================
    # Weight contract
    # ========================================================

    weight_cols = [
        col
        for col in positions.columns
        if col.startswith(
            "weight__"
        )
    ]

    sector_weight_map = {}

    unmapped = []

    for col in weight_cols:

        sector = col.replace(
            "weight__",
            "",
            1,
        )

        ticker = (
            SECTOR_TO_ETF.get(
                sector
            )
        )

        if ticker is None:

            unmapped.append(
                sector
            )

        else:

            sector_weight_map[
                col
            ] = ticker

    print()
    print(
        "=" * 110
    )

    print(
        "FILTER13 CANDIDATE CANONICAL "
        "PERFORMANCE + COST AUDIT"
    )

    print(
        "=" * 110
    )

    print()

    print(
        f"Rows             : "
        f"{len(positions):,}"
    )

    print(
        f"Weight columns   : "
        f"{len(weight_cols)}"
    )

    print(
        f"Mapped sectors   : "
        f"{len(sector_weight_map)}"
    )

    print(
        f"One-way cost     : "
        f"{COST_BPS_ONE_WAY:.1f} bps"
    )

    print()

    print(
        "Weight contract  : "
        "Filter18 percentage points / 100"
    )

    if unmapped:

        raise RuntimeError(
            "Unmapped sectors:\n"
            + "\n".join(
                unmapped
            )
        )

    required_tickers = (
        set(
            sector_weight_map.values()
        )
        |
        {
            BENCHMARK
        }
    )

    missing_tickers = [
        ticker
        for ticker in required_tickers
        if ticker not in returns.columns
    ]

    if missing_tickers:

        raise RuntimeError(
            "Price file missing tickers:\n"
            f"{missing_tickers}"
        )

    # ========================================================
    # Scenario-by-scenario canonical performance
    # ========================================================

    processed = []

    for scenario in SCENARIO_ORDER:

        x = (
            positions[
                positions[
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

        if x.empty:
            continue

        # performance.py starts from zero risky weights.
        previous_weights = {
            ticker: 0.0
            for ticker in SECTOR_TO_ETF.values()
        }

        rows = []

        for _, position in x.iterrows():

            execution_date = pd.Timestamp(
                position[
                    "execution_date"
                ]
            )

            # -----------------------------------------------
            # Exact performance.py date convention
            # -----------------------------------------------

            if execution_date not in returns.index:

                rows.append(
                    {
                        "strategy_return_gross":
                            np.nan,

                        "strategy_return_net":
                            np.nan,

                        "benchmark_return":
                            np.nan,

                        "turnover":
                            np.nan,

                        "transaction_cost":
                            np.nan,

                        "canonical_allocated":
                            np.nan,

                        "status_perf":
                            "NO_PRICE",
                    }
                )

                continue

            # -----------------------------------------------
            # Exact target ETF weights
            # -----------------------------------------------

            target_weights = {
                ticker: 0.0
                for ticker in SECTOR_TO_ETF.values()
            }

            for weight_col, ticker in (
                sector_weight_map.items()
            ):

                target_weights[
                    ticker
                ] += canonical_weight(
                    position.get(
                        weight_col
                    )
                )

            allocated = float(
                sum(
                    target_weights.values()
                )
            )

            # -----------------------------------------------
            # Gross return
            # -----------------------------------------------

            gross_return = 0.0

            missing_price = False

            for ticker, weight in (
                target_weights.items()
            ):

                if weight == 0:
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

                    missing_price = True
                    continue

                gross_return += (
                    weight
                    * float(
                        ticker_return
                    )
                )

            # -----------------------------------------------
            # Exact performance.py turnover
            # -----------------------------------------------

            turnover = float(
                sum(
                    abs(
                        target_weights[
                            ticker
                        ]
                        -
                        previous_weights.get(
                            ticker,
                            0.0,
                        )
                    )
                    for ticker
                    in target_weights
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
            )

            benchmark_return = (
                returns.at[
                    execution_date,
                    BENCHMARK,
                ]
            )

            benchmark_return = (
                float(
                    benchmark_return
                )
                if pd.notna(
                    benchmark_return
                )
                else np.nan
            )

            rows.append(
                {
                    "strategy_return_gross":
                        gross_return,

                    "strategy_return_net":
                        net_return,

                    "benchmark_return":
                        benchmark_return,

                    "turnover":
                        turnover,

                    "transaction_cost":
                        transaction_cost,

                    "canonical_allocated":
                        allocated,

                    "status_perf":
                        (
                            "MISSING_PRICE"
                            if missing_price
                            else "OK"
                        ),
                }
            )

            previous_weights = (
                target_weights
            )

        perf_rows = pd.DataFrame(
            rows,
            index=x.index,
        )

        x = pd.concat(
            [
                x,
                perf_rows,
            ],
            axis=1,
        )

        processed.append(
            x
        )

    detail = pd.concat(
        processed,
        ignore_index=True,
        sort=False,
    )

    # ========================================================
    # Audit checks
    # ========================================================

    valid_rate = (
        detail[
            "strategy_return_net"
        ]
        .notna()
        .mean()
    )

    negative_turnover = int(
        (
            detail[
                "turnover"
            ]
            < 0
        ).sum()
    )

    negative_cost = int(
        (
            detail[
                "transaction_cost"
            ]
            < 0
        ).sum()
    )

    # Compare canonical reconstructed equity with Filter18
    # allocation captured from engine.
    captured_alloc = pd.to_numeric(
        detail[
            "allocated_equity_18"
        ],
        errors="coerce",
    )

    # captured Filter18 allocation is percentage points.
    reconstructed_alloc_pct = (
        detail[
            "canonical_allocated"
        ]
        * 100.0
    )

    detail[
        "allocation_reconstruction_error"
    ] = (
        reconstructed_alloc_pct
        - captured_alloc
    )

    allocation_error = (
        detail[
            "allocation_reconstruction_error"
        ]
        .abs()
    )

    allocation_fail_days = int(
        (
            allocation_error
            > 0.11
        ).sum()
    )

    print()
    print(
        "AUDIT CHECKS"
    )

    print(
        "------------"
    )

    print(
        f"Valid P&L rate             : "
        f"{valid_rate:.2%}"
    )

    print(
        f"Negative turnover days     : "
        f"{negative_turnover}"
    )

    print(
        f"Negative cost days         : "
        f"{negative_cost}"
    )

    print(
        f"Allocation reconstruction "
        f"fail days: "
        f"{allocation_fail_days:,}"
    )

    print(
        f"Max allocation abs error   : "
        f"{allocation_error.max():.6f}%p"
    )

    if (
        valid_rate < 0.95
        or negative_turnover > 0
        or negative_cost > 0
    ):

        raise RuntimeError(
            "Canonical performance audit gate failed."
        )

    # ========================================================
    # Summary
    # ========================================================

    summary_rows = []

    for scenario in SCENARIO_ORDER:

        x = detail[
            detail[
                "scenario"
            ]
            == scenario
        ].copy()

        if x.empty:
            continue

        gross = pd.to_numeric(
            x[
                "strategy_return_gross"
            ],
            errors="coerce",
        )

        net = pd.to_numeric(
            x[
                "strategy_return_net"
            ],
            errors="coerce",
        )

        summary_rows.append(
            {
                "scenario":
                    scenario,

                "days":
                    len(x),

                "avg_risk_budget_13":
                    pd.to_numeric(
                        x[
                            "risk_budget_13"
                        ],
                        errors="coerce",
                    ).mean(),

                "avg_exposure_15":
                    pd.to_numeric(
                        x[
                            "exposure_15"
                        ],
                        errors="coerce",
                    ).mean(),

                "avg_allocated_equity_18":
                    pd.to_numeric(
                        x[
                            "allocated_equity_18"
                        ],
                        errors="coerce",
                    ).mean(),

                # -------------------------------------------
                # Turnover
                # -------------------------------------------

                "avg_daily_turnover":
                    pd.to_numeric(
                        x[
                            "turnover"
                        ],
                        errors="coerce",
                    ).mean(),

                "annualized_turnover":
                    pd.to_numeric(
                        x[
                            "turnover"
                        ],
                        errors="coerce",
                    ).mean()
                    * TRADING_DAYS,

                "total_turnover":
                    pd.to_numeric(
                        x[
                            "turnover"
                        ],
                        errors="coerce",
                    ).sum(),

                # -------------------------------------------
                # Costs
                # -------------------------------------------

                "avg_daily_cost_bps":
                    pd.to_numeric(
                        x[
                            "transaction_cost"
                        ],
                        errors="coerce",
                    ).mean()
                    * 10000.0,

                "total_cost_pct":
                    pd.to_numeric(
                        x[
                            "transaction_cost"
                        ],
                        errors="coerce",
                    ).sum()
                    * 100.0,

                # -------------------------------------------
                # Gross performance
                # -------------------------------------------

                "gross_cagr":
                    annualized_return(
                        gross
                    )
                    * 100.0,

                "gross_mdd":
                    max_drawdown(
                        gross
                    )
                    * 100.0,

                "gross_volatility":
                    annualized_volatility(
                        gross
                    )
                    * 100.0,

                "gross_sharpe":
                    sharpe_ratio(
                        gross
                    ),

                # -------------------------------------------
                # Net performance
                # -------------------------------------------

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

    summary = pd.DataFrame(
        summary_rows
    )

    # ========================================================
    # Delta vs baseline
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
        "cagr_cost_drag"
    ] = (
        summary[
            "gross_cagr"
        ]
        - summary[
            "net_cagr"
        ]
    )

    # ========================================================
    # Exposure transmission
    # ========================================================

    summary[
        "restored_budget_13"
    ] = (
        summary[
            "avg_risk_budget_13"
        ]
        - baseline[
            "avg_risk_budget_13"
        ]
    )

    summary[
        "restored_exposure_15"
    ] = (
        summary[
            "avg_exposure_15"
        ]
        - baseline[
            "avg_exposure_15"
        ]
    )

    summary[
        "restored_allocated_18"
    ] = (
        summary[
            "avg_allocated_equity_18"
        ]
        - baseline[
            "avg_allocated_equity_18"
        ]
    )

    summary[
        "survival_13_to_15"
    ] = np.where(
        summary[
            "restored_budget_13"
        ].abs()
        > 1e-9,

        summary[
            "restored_exposure_15"
        ]
        /
        summary[
            "restored_budget_13"
        ],

        np.nan,
    )

    summary[
        "survival_15_to_18"
    ] = np.where(
        summary[
            "restored_exposure_15"
        ].abs()
        > 1e-9,

        summary[
            "restored_allocated_18"
        ]
        /
        summary[
            "restored_exposure_15"
        ],

        np.nan,
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
        "FILTER13 CANDIDATE — CANONICAL "
        "PERFORMANCE / TURNOVER / COST AUDIT"
    )

    lines.append(
        "=" * 125
    )

    lines.append("")

    lines.append(
        "Performance contract:"
    )

    lines.append(
        "- Same sector → ETF mapping as performance.py"
    )

    lines.append(
        "- Same execution_date return convention"
    )

    lines.append(
        "- Filter18 weights ALWAYS divided by 100"
    )

    lines.append(
        f"- One-way transaction cost = "
        f"{COST_BPS_ONE_WAY:.1f} bps"
    )

    lines.append("")

    lines.append(
        f"Valid P&L coverage: "
        f"{valid_rate:.2%}"
    )

    lines.append("")

    display_cols = [
        "scenario",

        "annualized_turnover",
        "total_cost_pct",

        "gross_cagr",
        "net_cagr",
        "cagr_cost_drag",

        "net_mdd",
        "net_volatility",
        "net_sharpe",

        "net_cagr_delta",
        "net_mdd_delta",
        "net_sharpe_delta",

        "survival_13_to_15",
        "survival_15_to_18",
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
        "FINAL GATE:"
    )

    lines.append(
        "- Candidate must retain net CAGR / Sharpe improvement."
    )

    lines.append(
        "- Turnover increase must be economically reasonable."
    )

    lines.append(
        "- MDD trade-off must remain acceptable."
    )

    lines.append(
        "- Improvement should remain broad across 15/20/25/30."
    )

    lines.append(
        "- Do not select a parameter solely for the highest return."
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