

"""
Filter 15 Brake Attribution Audit
=================================

Research question
-----------------
Which signal family best explains the exposure reduction from
Filter 13 Risk Budget to Filter 15 Final Exposure?

Candidate families
------------------
- Positioning
- Volatility
- Credit
- Liquidity

Important
---------
This script does NOT change strategy thresholds.

This is a statistical/behavioral attribution audit.
It identifies which signal family explains Filter 15 reductions
after controlling for the other families.

It is not yet a mechanical code-path attribution unless Filter 15
already logs each individual multiplier/cap.

Inputs
------
data/backtest/results/exposure_reduction_daily.csv

Outputs
-------
data/backtest/results/filter15_brake_family_daily.csv
data/backtest/results/filter15_brake_attribution.csv
data/backtest/results/filter15_brake_by_year.csv
data/backtest/results/filter15_brake_audit_summary.txt
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

INPUT_PATH = RESULT_DIR / "exposure_reduction_daily.csv"

DAILY_OUT = RESULT_DIR / "filter15_brake_family_daily.csv"
ATTRIBUTION_OUT = RESULT_DIR / "filter15_brake_attribution.csv"
YEAR_OUT = RESULT_DIR / "filter15_brake_by_year.csv"
SUMMARY_OUT = RESULT_DIR / "filter15_brake_audit_summary.txt"


# ============================================================
# Candidate signal definitions
# ============================================================

FAMILY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "positioning": (
        "positioning__",
        "sp500_pos_z",
        "us10y_pos_z",
        "dxy_pos_z",
        "cta_momentum",
        "dealer_gamma",
        "gamma_bias",
        "positioning_state",
        "positioning_stress",
    ),
    "volatility": (
        "vix",
        "vix3m",
        "volatility",
        "vol_structure",
        "term_structure",
    ),
    "credit": (
        "hy_oas",
        "hyg_lqd",
        "credit__",
        "credit_spread",
        "spread",
        "hyg",
        "lqd",
    ),
    "liquidity": (
        "liquidity",
        "net_liq",
        "netliq",
        "walcl",
        "rrp",
        "tga",
        "reserves",
    ),
}

EXCLUDE_KEYWORDS = (
    "forward",
    "return",
    "exposure",
    "reduction",
    "retention",
    "allocated",
    "cash_weight",
    "signal_date",
    "execution_date",
)


# ============================================================
# Helpers
# ============================================================

def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def safe_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    valid = np.isfinite(y_true) & np.isfinite(y_pred)

    if valid.sum() < 30:
        return float("nan")

    y = y_true[valid]
    pred = y_pred[valid]

    denominator = np.sum((y - y.mean()) ** 2)

    if denominator <= 1e-12:
        return float("nan")

    return float(
        1.0 - np.sum((y - pred) ** 2) / denominator
    )


def standardize_frame(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=df.index)

    for column in df.columns:
        values = numeric(df[column])

        median = values.median()
        values = values.fillna(median)

        std = values.std(ddof=0)

        if not np.isfinite(std) or std <= 1e-12:
            continue

        result[column] = (values - values.mean()) / std

    return result


def ridge_fit_predict(
    x: np.ndarray,
    y: np.ndarray,
    alpha: float = 10.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Ridge regression implemented with NumPy.

    Returns
    -------
    beta
    fitted values
    """

    valid = (
        np.isfinite(y)
        & np.isfinite(x).all(axis=1)
    )

    if valid.sum() < max(50, x.shape[1] * 5):
        raise ValueError(
            "Not enough valid observations for ridge regression."
        )

    x_valid = x[valid]
    y_valid = y[valid]

    # Add intercept.
    design = np.column_stack(
        [
            np.ones(len(x_valid)),
            x_valid,
        ]
    )

    penalty = np.eye(design.shape[1])
    penalty[0, 0] = 0.0

    beta = np.linalg.solve(
        design.T @ design + alpha * penalty,
        design.T @ y_valid,
    )

    fitted_all = np.full(len(y), np.nan)

    full_design = np.column_stack(
        [
            np.ones(len(x)),
            x,
        ]
    )

    fitted_all[:] = full_design @ beta

    return beta, fitted_all


def discover_family_columns(
    columns: Iterable[str],
) -> dict[str, list[str]]:
    discovered: dict[str, list[str]] = {}

    for family, keywords in FAMILY_KEYWORDS.items():
        matches: list[str] = []

        for column in columns:
            lowered = column.lower()

            if any(excluded in lowered for excluded in EXCLUDE_KEYWORDS):
                continue

            if any(keyword in lowered for keyword in keywords):
                matches.append(column)

        discovered[family] = sorted(set(matches))

    return discovered


def make_family_score(
    standardized: pd.DataFrame,
    columns: list[str],
) -> pd.Series:
    """
    Build one composite signal per family.

    The direction is initially arbitrary. It is later aligned so that a
    positive family score corresponds to greater exposure reduction.
    """

    usable = [
        column
        for column in columns
        if column in standardized.columns
    ]

    if not usable:
        return pd.Series(
            np.nan,
            index=standardized.index,
            dtype=float,
        )

    return standardized[usable].mean(axis=1)


def align_family_direction(
    score: pd.Series,
    reduction: pd.Series,
) -> tuple[pd.Series, float]:
    pair = pd.concat(
        [
            numeric(score).rename("score"),
            numeric(reduction).rename("reduction"),
        ],
        axis=1,
    ).dropna()

    if len(pair) < 30:
        return score, float("nan")

    corr = pair["score"].corr(pair["reduction"])

    if pd.notna(corr) and corr < 0:
        return -score, float(-corr)

    return score, float(corr)


# ============================================================
# Load
# ============================================================

def load_data() -> pd.DataFrame:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_PATH}\n\n"
            "Run audit_exposure_reduction.py first."
        )

    df = pd.read_csv(INPUT_PATH)

    required = {
        "signal_date",
        "risk_budget_13",
        "exposure_15",
        "reduction_13_to_15",
    }

    missing = sorted(required - set(df.columns))

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )

    df["reduction_13_to_15"] = numeric(
        df["reduction_13_to_15"]
    ).clip(lower=0)

    df = (
        df.dropna(
            subset=[
                "signal_date",
                "reduction_13_to_15",
            ]
        )
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    return df


# ============================================================
# Build family dataset
# ============================================================

def build_family_dataset(
    df: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    dict[str, list[str]],
    dict[str, float],
]:
    family_columns = discover_family_columns(df.columns)

    all_signal_columns = sorted(
        {
            column
            for columns in family_columns.values()
            for column in columns
        }
    )

    if not all_signal_columns:
        raise ValueError(
            "No candidate Positioning, Volatility, Credit, or "
            "Liquidity columns were found in the input."
        )

    standardized = standardize_frame(
        df[all_signal_columns]
    )

    result = df[
        [
            "signal_date",
            "risk_budget_13",
            "exposure_15",
            "reduction_13_to_15",
        ]
    ].copy()

    raw_correlations: dict[str, float] = {}

    for family, columns in family_columns.items():
        score = make_family_score(
            standardized,
            columns,
        )

        aligned_score, correlation = align_family_direction(
            score,
            df["reduction_13_to_15"],
        )

        result[f"{family}_brake_score"] = aligned_score
        raw_correlations[family] = correlation

    return result, family_columns, raw_correlations


# ============================================================
# Attribution
# ============================================================

def run_attribution(
    family_df: pd.DataFrame,
    family_columns: dict[str, list[str]],
    raw_correlations: dict[str, float],
) -> tuple[pd.DataFrame, pd.DataFrame]:

    available_families = [
        family
        for family in FAMILY_KEYWORDS
        if family_df[f"{family}_brake_score"].notna().sum() >= 30
    ]

    if len(available_families) < 2:
        raise ValueError(
            "At least two signal families are required for "
            "multivariate attribution."
        )

    feature_columns = [
        f"{family}_brake_score"
        for family in available_families
    ]

    model_data = family_df[
        [
            "signal_date",
            "reduction_13_to_15",
            *feature_columns,
        ]
    ].copy()

    for column in feature_columns:
        model_data[column] = numeric(
            model_data[column]
        ).fillna(0.0)

    y = numeric(
        model_data["reduction_13_to_15"]
    ).to_numpy(dtype=float)

    x = model_data[
        feature_columns
    ].to_numpy(dtype=float)

    beta, fitted = ridge_fit_predict(
        x,
        y,
        alpha=10.0,
    )

    full_r2 = safe_r2(y, fitted)

    model_data["predicted_reduction"] = fitted
    model_data["residual_reduction"] = y - fitted

    # Daily contribution from each family.
    for index, family in enumerate(available_families):
        coefficient = beta[index + 1]

        contribution = (
            x[:, index] * coefficient
        )

        model_data[
            f"{family}_daily_contribution"
        ] = contribution

    attribution_rows: list[dict[str, object]] = []

    positive_contribution_totals: dict[str, float] = {}

    for family in available_families:
        contribution_column = (
            f"{family}_daily_contribution"
        )

        positive_total = float(
            model_data[contribution_column]
            .clip(lower=0)
            .sum()
        )

        positive_contribution_totals[family] = positive_total

    all_positive_total = sum(
        positive_contribution_totals.values()
    )

    for index, family in enumerate(available_families):
        reduced_features = [
            candidate
            for candidate in available_families
            if candidate != family
        ]

        reduced_columns = [
            f"{candidate}_brake_score"
            for candidate in reduced_features
        ]

        reduced_x = model_data[
            reduced_columns
        ].to_numpy(dtype=float)

        _, reduced_fitted = ridge_fit_predict(
            reduced_x,
            y,
            alpha=10.0,
        )

        reduced_r2 = safe_r2(
            y,
            reduced_fitted,
        )

        incremental_r2 = full_r2 - reduced_r2

        contribution_total = (
            positive_contribution_totals[family]
        )

        contribution_share = (
            contribution_total / all_positive_total
            if all_positive_total > 0
            else float("nan")
        )

        family_signal_columns = family_columns.get(
            family,
            [],
        )

        attribution_rows.append(
            {
                "family": family,
                "signal_column_count": len(
                    family_signal_columns
                ),
                "signal_columns": " | ".join(
                    family_signal_columns
                ),
                "raw_family_correlation": raw_correlations.get(
                    family,
                    float("nan"),
                ),
                "ridge_coefficient": float(
                    beta[index + 1]
                ),
                "full_model_r2": full_r2,
                "model_r2_without_family": reduced_r2,
                "incremental_r2": incremental_r2,
                "positive_daily_contribution_total": (
                    contribution_total
                ),
                "estimated_brake_share": contribution_share,
            }
        )

    attribution = pd.DataFrame(
        attribution_rows
    ).sort_values(
        [
            "incremental_r2",
            "estimated_brake_share",
        ],
        ascending=False,
    )

    return model_data, attribution


# ============================================================
# Annual attribution
# ============================================================

def build_year_attribution(
    daily: pd.DataFrame,
) -> pd.DataFrame:
    contribution_columns = [
        column
        for column in daily.columns
        if column.endswith("_daily_contribution")
    ]

    result = daily.copy()

    result["year"] = pd.to_datetime(
        result["signal_date"]
    ).dt.year

    aggregations: dict[str, tuple[str, str]] = {
        "observations": (
            "signal_date",
            "size",
        ),
        "actual_average_reduction": (
            "reduction_13_to_15",
            "mean",
        ),
        "actual_total_reduction": (
            "reduction_13_to_15",
            "sum",
        ),
        "predicted_average_reduction": (
            "predicted_reduction",
            "mean",
        ),
    }

    for column in contribution_columns:
        family = column.replace(
            "_daily_contribution",
            "",
        )

        aggregations[
            f"{family}_positive_contribution"
        ] = (
            column,
            lambda values: values.clip(lower=0).sum(),
        )

    annual = (
        result.groupby("year")
        .agg(**aggregations)
        .reset_index()
    )

    annual_contribution_columns = [
        column
        for column in annual.columns
        if column.endswith("_positive_contribution")
    ]

    annual["all_family_positive_contribution"] = annual[
        annual_contribution_columns
    ].sum(axis=1)

    for column in annual_contribution_columns:
        family = column.replace(
            "_positive_contribution",
            "",
        )

        annual[f"{family}_share"] = np.where(
            annual["all_family_positive_contribution"] > 0,
            annual[column]
            / annual["all_family_positive_contribution"],
            np.nan,
        )

    return annual


# ============================================================
# Summary
# ============================================================

def make_summary(
    df: pd.DataFrame,
    attribution: pd.DataFrame,
    family_columns: dict[str, list[str]],
) -> str:

    top = attribution.iloc[0]

    lines: list[str] = []

    for _, row in attribution.iterrows():
        lines.append(
            f"{row['family']:12s} | "
            f"incremental R²={row['incremental_r2']:8.4f} | "
            f"estimated brake share="
            f"{row['estimated_brake_share']:8.2%} | "
            f"raw corr="
            f"{row['raw_family_correlation']:8.4f}"
        )

    discovered_lines: list[str] = []

    for family, columns in family_columns.items():
        discovered_lines.append(
            f"{family:12s}: {len(columns):2d} columns"
        )

        for column in columns:
            discovered_lines.append(
                f"    - {column}"
            )

    if top["incremental_r2"] >= 0.10:
        verdict = (
            f"{str(top['family']).upper()} IS THE LEADING "
            "FILTER 15 BRAKE CANDIDATE.\n"
            "Removing this family causes the largest loss of "
            "explanatory power in the multivariate model."
        )
    elif top["incremental_r2"] >= 0.03:
        verdict = (
            f"{str(top['family']).upper()} IS THE LEADING "
            "CANDIDATE, BUT ATTRIBUTION IS MIXED.\n"
            "Multiple signal families appear to contribute to "
            "Filter 15 reductions."
        )
    else:
        verdict = (
            "NO SINGLE DOMINANT BRAKE FAMILY WAS ESTABLISHED.\n"
            "The Filter 15 reduction may be caused by interactions, "
            "caps, state persistence, or variables not logged here."
        )

    summary = f"""
============================================================
FILTER 15 BRAKE ATTRIBUTION AUDIT
============================================================

Period
------
{df['signal_date'].min().date()} ~ {df['signal_date'].max().date()}

Observations
------------
{len(df):,}

Average 13 -> 15 reduction
--------------------------
{df['reduction_13_to_15'].mean():.2f}%p

Multivariate family attribution
-------------------------------
{chr(10).join(lines)}

Preliminary verdict
-------------------
{verdict}

Interpretation
--------------
Incremental R² measures how much explanatory power is lost when
one signal family is removed while the other families remain.

Estimated brake share measures each family's positive modeled
contribution to Filter 15 exposure reduction.

This is stronger than simple correlation, but it is still
behavioral attribution rather than exact mechanical attribution.

Discovered signal columns
-------------------------
{chr(10).join(discovered_lines)}

Next decision
-------------
Audit the leading family for:

1. Reduction frequency
2. Episode persistence
3. Bull-market false braking
4. SPY forward returns after braking
5. Exact Filter 15 code-path and multiplier/cap application
============================================================
""".strip()

    return summary


# ============================================================
# Main
# ============================================================

def main() -> None:
    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_data()

    family_df, family_columns, raw_correlations = (
        build_family_dataset(df)
    )

    daily, attribution = run_attribution(
        family_df,
        family_columns,
        raw_correlations,
    )

    annual = build_year_attribution(
        daily
    )

    summary = make_summary(
        df,
        attribution,
        family_columns,
    )

    daily.to_csv(
        DAILY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    attribution.to_csv(
        ATTRIBUTION_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    annual.to_csv(
        YEAR_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    SUMMARY_OUT.write_text(
        summary,
        encoding="utf-8",
    )

    print(summary)

    print("\nSaved outputs")
    print("-------------")
    print(DAILY_OUT)
    print(ATTRIBUTION_OUT)
    print(YEAR_OUT)
    print(SUMMARY_OUT)


if __name__ == "__main__":
    main()