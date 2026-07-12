"""
Filter 15 Brake Strength Counterfactual Audit
==============================================

Question
--------
Filter 15 generally applied brakes in the correct direction.
But was the amount of exposure reduction too large?

Counterfactual scenarios
------------------------
1. Baseline
2. Volatility brake 50% weaker
3. Positioning brake 50% weaker
4. Credit brake 50% weaker
5. Volatility + Positioning + Credit brakes 50% weaker

Hard Deadman is NEVER relaxed.

Method
------
For each date:

    counterfactual exposure
    = actual Filter 15 exposure
    + restored fraction of the selected brake reduction

The restored exposure cannot exceed Filter 13 Risk Budget.

The production engine and existing backtest outputs are never modified.

Important
---------
Mechanical brake reductions are used only on replay exact-match dates.
On non-matching dates, the original exposure remains unchanged.

Outputs
-------
data/backtest/results/filter15_brake_strength_daily.csv
data/backtest/results/filter15_brake_strength_summary.csv
data/backtest/results/filter15_brake_strength_audit.txt
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

REPLAY_PATH = (
    RESULT_DIR
    / "filter15_mechanical_replay_daily.csv"
)

POSITIONS_PATH = (
    RESULT_DIR
    / "daily_positions.csv"
)

MASTER_PANEL_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

DAILY_OUT = (
    RESULT_DIR
    / "filter15_brake_strength_daily.csv"
)

SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_brake_strength_summary.csv"
)

TEXT_OUT = (
    RESULT_DIR
    / "filter15_brake_strength_audit.txt"
)


# ============================================================
# Configuration
# ============================================================

RELAXATION_RATE = 0.50
REPLAY_TOLERANCE = 1e-9
TRADING_DAYS = 252

SCENARIOS: dict[str, tuple[str, ...]] = {
    "baseline": (),
    "volatility_50pct_weaker": (
        "volatility_reduction",
    ),
    "positioning_50pct_weaker": (
        "positioning_reduction",
    ),
    "credit_50pct_weaker": (
        "credit_reduction",
    ),
    "all_soft_brakes_50pct_weaker": (
        "volatility_reduction",
        "positioning_reduction",
        "credit_reduction",
    ),
}


# ============================================================
# Helpers
# ============================================================

def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def find_date_column(
    columns: Iterable[str],
) -> str | None:
    allowed = {
        "date",
        "signal_date",
        "execution_date",
        "datetime",
        "timestamp",
    }

    for column in columns:
        if str(column).lower() in allowed:
            return str(column)

    return None


def find_spy_column(
    columns: Iterable[str],
) -> str | None:
    lookup = {
        str(column).lower(): str(column)
        for column in columns
    }

    for candidate in (
        "SPY",
        "SPY_Close",
        "SPY_ADJ_CLOSE",
        "spy_close",
        "spy_adj_close",
    ):
        match = lookup.get(candidate.lower())

        if match is not None:
            return match

    for column in columns:
        lowered = str(column).lower()

        if (
            "spy" in lowered
            and any(
                token in lowered
                for token in (
                    "close",
                    "price",
                    "adj",
                )
            )
        ):
            return str(column)

    return None


def calculate_cagr(
    daily_returns: pd.Series,
) -> float:
    returns = numeric(
        daily_returns
    ).dropna()

    if returns.empty:
        return float("nan")

    wealth = float(
        (1.0 + returns).prod()
    )

    years = len(returns) / TRADING_DAYS

    if wealth <= 0 or years <= 0:
        return float("nan")

    return wealth ** (1.0 / years) - 1.0


def calculate_mdd(
    daily_returns: pd.Series,
) -> float:
    returns = numeric(
        daily_returns
    ).fillna(0.0)

    equity = (
        1.0 + returns
    ).cumprod()

    running_peak = equity.cummax()

    drawdown = (
        equity / running_peak - 1.0
    )

    return float(drawdown.min())


def calculate_volatility(
    daily_returns: pd.Series,
) -> float:
    returns = numeric(
        daily_returns
    ).dropna()

    if len(returns) < 2:
        return float("nan")

    return float(
        returns.std(ddof=1)
        * np.sqrt(TRADING_DAYS)
    )


def calculate_sharpe(
    daily_returns: pd.Series,
) -> float:
    returns = numeric(
        daily_returns
    ).dropna()

    if len(returns) < 2:
        return float("nan")

    std = float(
        returns.std(ddof=1)
    )

    if std <= 1e-12:
        return float("nan")

    return float(
        returns.mean()
        / std
        * np.sqrt(TRADING_DAYS)
    )


def calculate_calmar(
    cagr: float,
    mdd: float,
) -> float:
    if (
        not np.isfinite(cagr)
        or not np.isfinite(mdd)
        or abs(mdd) <= 1e-12
    ):
        return float("nan")

    return float(
        cagr / abs(mdd)
    )


# ============================================================
# Load data
# ============================================================

def load_replay() -> pd.DataFrame:
    if not REPLAY_PATH.exists():
        raise FileNotFoundError(
            f"Replay file not found:\n{REPLAY_PATH}"
        )

    replay = pd.read_csv(
        REPLAY_PATH
    )

    required = {
        "signal_date",
        "risk_budget_13",
        "existing_exposure_15",
        "replay_error",
        "volatility_reduction",
        "positioning_reduction",
        "credit_reduction",
        "deadman_reduction",
    }

    missing = sorted(
        required - set(replay.columns)
    )

    if missing:
        raise ValueError(
            f"Replay file missing columns: {missing}"
        )

    replay["signal_date"] = pd.to_datetime(
        replay["signal_date"],
        errors="coerce",
    )

    for column in required - {"signal_date"}:
        replay[column] = numeric(
            replay[column]
        )

    replay = (
        replay.dropna(
            subset=[
                "signal_date",
                "risk_budget_13",
                "existing_exposure_15",
                "replay_error",
            ]
        )
        .sort_values("signal_date")
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    replay["replay_exact_match"] = (
        replay["replay_error"].abs()
        <= REPLAY_TOLERANCE
    )

    return replay


def load_execution_dates() -> pd.DataFrame:
    if not POSITIONS_PATH.exists():
        return pd.DataFrame(
            columns=[
                "signal_date",
                "execution_date",
            ]
        )

    positions = pd.read_csv(
        POSITIONS_PATH
    )

    if "signal_date" not in positions.columns:
        return pd.DataFrame(
            columns=[
                "signal_date",
                "execution_date",
            ]
        )

    positions["signal_date"] = pd.to_datetime(
        positions["signal_date"],
        errors="coerce",
    )

    if "execution_date" in positions.columns:
        positions["execution_date"] = pd.to_datetime(
            positions["execution_date"],
            errors="coerce",
        )
    else:
        positions["execution_date"] = pd.NaT

    return (
        positions[
            [
                "signal_date",
                "execution_date",
            ]
        ]
        .dropna(
            subset=["signal_date"]
        )
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
    )


def load_spy() -> pd.DataFrame:
    if not MASTER_PANEL_PATH.exists():
        raise FileNotFoundError(
            MASTER_PANEL_PATH
        )

    panel = pd.read_csv(
        MASTER_PANEL_PATH
    )

    date_column = find_date_column(
        panel.columns
    )

    spy_column = find_spy_column(
        panel.columns
    )

    if date_column is None:
        raise ValueError(
            "No date column found in master_panel.csv"
        )

    if spy_column is None:
        raise ValueError(
            "No SPY price column found in master_panel.csv"
        )

    spy = panel[
        [
            date_column,
            spy_column,
        ]
    ].copy()

    spy.columns = [
        "market_date",
        "spy_close",
    ]

    spy["market_date"] = pd.to_datetime(
        spy["market_date"],
        errors="coerce",
    )

    spy["spy_close"] = numeric(
        spy["spy_close"]
    )

    spy = (
        spy.dropna(
            subset=[
                "market_date",
                "spy_close",
            ]
        )
        .sort_values("market_date")
        .drop_duplicates(
            "market_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    # Return earned from market_date to the following trading date.
    spy["spy_next_return"] = (
        spy["spy_close"]
        .shift(-1)
        / spy["spy_close"]
        - 1.0
    )

    spy["next_market_date"] = (
        spy["market_date"]
        .shift(-1)
    )

    return spy


# ============================================================
# Return alignment
# ============================================================

def attach_realized_returns(
    replay: pd.DataFrame,
    execution_dates: pd.DataFrame,
    spy: pd.DataFrame,
) -> pd.DataFrame:
    result = replay.merge(
        execution_dates,
        on="signal_date",
        how="left",
        validate="one_to_one",
    )

    # A signal should earn the following trading session's return.
    signal_returns = spy[
        [
            "market_date",
            "next_market_date",
            "spy_next_return",
        ]
    ].rename(
        columns={
            "market_date": "signal_date",
            "next_market_date": (
                "derived_execution_date"
            ),
        }
    )

    result = result.merge(
        signal_returns,
        on="signal_date",
        how="left",
        validate="one_to_one",
    )

    result["effective_execution_date"] = (
        result["execution_date"]
        .combine_first(
            result["derived_execution_date"]
        )
    )

    return result


# ============================================================
# Scenario construction
# ============================================================

def build_scenario_exposures(
    df: pd.DataFrame,
) -> pd.DataFrame:
    result = df.copy()

    baseline = numeric(
        result["existing_exposure_15"]
    ).clip(
        lower=0.0,
        upper=100.0,
    )

    result["exposure_baseline"] = baseline

    for scenario, brake_columns in SCENARIOS.items():
        exposure_column = (
            f"exposure_{scenario}"
        )

        if scenario == "baseline":
            result[exposure_column] = baseline
            continue

        restored = pd.Series(
            0.0,
            index=result.index,
            dtype=float,
        )

        for brake_column in brake_columns:
            restored = (
                restored
                + numeric(
                    result[brake_column]
                ).fillna(0.0)
                * RELAXATION_RATE
            )

        # Mechanical attribution is trusted only on exact-match days.
        restored = restored.where(
            result["replay_exact_match"],
            0.0,
        )

        counterfactual = (
            baseline + restored
        )

        # Never exceed the original Filter 13 Risk Budget.
        counterfactual = np.minimum(
            counterfactual,
            result["risk_budget_13"],
        )

        # Hard Deadman remains untouched.
        hard_deadman_active = (
            result["deadman_reduction"]
            > 1e-10
        )

        counterfactual = counterfactual.where(
            ~hard_deadman_active,
            baseline,
        )

        result[exposure_column] = (
            numeric(counterfactual)
            .clip(
                lower=0.0,
                upper=100.0,
            )
        )

    return result


def build_scenario_returns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    result = df.copy()

    for scenario in SCENARIOS:
        exposure_column = (
            f"exposure_{scenario}"
        )

        return_column = (
            f"return_{scenario}"
        )

        result[return_column] = (
            result[exposure_column]
            / 100.0
            * result["spy_next_return"]
        )

        result[
            f"equity_{scenario}"
        ] = (
            1.0
            + result[return_column].fillna(0.0)
        ).cumprod()

    return result


# ============================================================
# Summary
# ============================================================

def build_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    baseline_cagr = calculate_cagr(
        df["return_baseline"]
    )

    baseline_mdd = calculate_mdd(
        df["return_baseline"]
    )

    baseline_sharpe = calculate_sharpe(
        df["return_baseline"]
    )

    baseline_calmar = calculate_calmar(
        baseline_cagr,
        baseline_mdd,
    )

    for scenario in SCENARIOS:
        exposure_column = (
            f"exposure_{scenario}"
        )

        return_column = (
            f"return_{scenario}"
        )

        cagr = calculate_cagr(
            df[return_column]
        )

        mdd = calculate_mdd(
            df[return_column]
        )

        volatility = calculate_volatility(
            df[return_column]
        )

        sharpe = calculate_sharpe(
            df[return_column]
        )

        calmar = calculate_calmar(
            cagr,
            mdd,
        )

        average_exposure = float(
            df[exposure_column].mean()
        )

        rows.append({
            "scenario": scenario,
            "average_exposure": (
                average_exposure
            ),
            "cagr": cagr,
            "mdd": mdd,
            "annualized_volatility": (
                volatility
            ),
            "sharpe": sharpe,
            "calmar": calmar,
            "cagr_change_vs_baseline": (
                cagr - baseline_cagr
            ),
            "mdd_change_vs_baseline": (
                mdd - baseline_mdd
            ),
            "sharpe_change_vs_baseline": (
                sharpe - baseline_sharpe
            ),
            "calmar_change_vs_baseline": (
                calmar - baseline_calmar
            ),
            "average_exposure_change": (
                average_exposure
                - float(
                    df[
                        "exposure_baseline"
                    ].mean()
                )
            ),
        })

    return pd.DataFrame(rows)


def classify_scenario(
    row: pd.Series,
) -> str:
    if row["scenario"] == "baseline":
        return "BASELINE"

    cagr_gain = row[
        "cagr_change_vs_baseline"
    ]

    mdd_change = row[
        "mdd_change_vs_baseline"
    ]

    sharpe_change = row[
        "sharpe_change_vs_baseline"
    ]

    calmar_change = row[
        "calmar_change_vs_baseline"
    ]

    # mdd_change is negative when drawdown became worse.
    if (
        cagr_gain >= 0.005
        and mdd_change >= -0.03
        and (
            sharpe_change > 0
            or calmar_change > 0
        )
    ):
        return "BRAKE_LIKELY_TOO_STRONG"

    if (
        cagr_gain <= 0.001
        and mdd_change < -0.03
    ):
        return "CURRENT_BRAKE_JUSTIFIED"

    if (
        cagr_gain > 0
        and (
            sharpe_change > 0
            or calmar_change > 0
        )
    ):
        return "MILD_OVERBRAKING_EVIDENCE"

    return "MIXED_OR_INCONCLUSIVE"


def make_text_summary(
    daily: pd.DataFrame,
    summary: pd.DataFrame,
) -> str:
    evaluated = summary.copy()

    evaluated["verdict"] = (
        evaluated.apply(
            classify_scenario,
            axis=1,
        )
    )

    lines = [
        "=" * 96,
        "FILTER 15 BRAKE STRENGTH COUNTERFACTUAL AUDIT",
        "=" * 96,
        "",
        "Research question",
        "-----------------",
        (
            "Were Volatility, Positioning, and Credit brakes "
            "directionally correct but mechanically too strong?"
        ),
        "",
        "Method",
        "------",
        (
            "Restore 50% of each selected soft-brake reduction "
            "on replay exact-match dates."
        ),
        (
            "Hard Deadman remains unchanged in every scenario."
        ),
        (
            "Counterfactual exposure cannot exceed Filter 13 "
            "Risk Budget."
        ),
        "",
        "Data",
        "----",
        (
            f"Period                 : "
            f"{daily['signal_date'].min().date()} ~ "
            f"{daily['signal_date'].max().date()}"
        ),
        (
            f"Observations           : "
            f"{len(daily):,}"
        ),
        (
            f"Replay exact-match days: "
            f"{int(daily['replay_exact_match'].sum()):,} / "
            f"{len(daily):,}"
        ),
        (
            f"Relaxation rate        : "
            f"{RELAXATION_RATE:.0%}"
        ),
        "",
        "Results",
        "-------",
    ]

    for _, row in evaluated.iterrows():
        lines.extend([
            "",
            str(row["scenario"]).upper(),
            (
                f"  Average exposure : "
                f"{row['average_exposure']:.2f}% "
                f"({row['average_exposure_change']:+.2f}%p)"
            ),
            (
                f"  CAGR             : "
                f"{row['cagr']:.2%} "
                f"({row['cagr_change_vs_baseline']:+.2%})"
            ),
            (
                f"  MDD              : "
                f"{row['mdd']:.2%} "
                f"({row['mdd_change_vs_baseline']:+.2%})"
            ),
            (
                f"  Volatility       : "
                f"{row['annualized_volatility']:.2%}"
            ),
            (
                f"  Sharpe           : "
                f"{row['sharpe']:.3f} "
                f"({row['sharpe_change_vs_baseline']:+.3f})"
            ),
            (
                f"  Calmar           : "
                f"{row['calmar']:.3f} "
                f"({row['calmar_change_vs_baseline']:+.3f})"
            ),
            (
                f"  Verdict          : "
                f"{row['verdict']}"
            ),
        ])

    lines.extend([
        "",
        "Decision framework",
        "------------------",
        (
            "CAGR rises materially while MDD deteriorates only "
            "modestly and Sharpe/Calmar improves:"
        ),
        "  -> the selected brake was probably too strong.",
        "",
        (
            "CAGR barely improves while MDD and risk-adjusted "
            "metrics deteriorate materially:"
        ),
        "  -> the existing brake strength is justified.",
        "",
        "Important limitation",
        "--------------------",
        (
            "This is an exposure-strength counterfactual using SPY "
            "as the common equity return proxy."
        ),
        (
            "It isolates the economic effect of giving back exposure; "
            "it does not alter sector-selection decisions."
        ),
        "",
        "No production code, thresholds, or existing results were modified.",
        "=" * 96,
    ])

    return "\n".join(lines)


# ============================================================
# Main
# ============================================================

def main() -> None:
    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    replay = load_replay()
    execution_dates = load_execution_dates()
    spy = load_spy()

    daily = attach_realized_returns(
        replay,
        execution_dates,
        spy,
    )

    daily = daily.dropna(
        subset=["spy_next_return"]
    ).copy()

    daily = build_scenario_exposures(
        daily
    )

    daily = build_scenario_returns(
        daily
    )

    summary = build_summary(
        daily
    )

    summary["verdict"] = (
        summary.apply(
            classify_scenario,
            axis=1,
        )
    )

    text_summary = make_text_summary(
        daily,
        summary,
    )

    daily.to_csv(
        DAILY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        SUMMARY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    TEXT_OUT.write_text(
        text_summary,
        encoding="utf-8",
    )

    print(text_summary)

    print()
    print("Saved outputs")
    print("-------------")
    print(DAILY_OUT)
    print(SUMMARY_OUT)
    print(TEXT_OUT)


if __name__ == "__main__":
    main()