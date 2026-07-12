"""
Exposure Reduction Attribution Audit
====================================

Research question
-----------------
Why did average equity exposure fall from Filter 13 Risk Budget
to Filter 15 Final Exposure?

This script does NOT modify thresholds or strategy logic.

Inputs
------
data/backtest/results/daily_positions.csv
data/backtest/master_panel.csv  (optional but strongly recommended)

Outputs
-------
data/backtest/results/exposure_reduction_daily.csv
data/backtest/results/exposure_reduction_by_year.csv
data/backtest/results/exposure_reduction_by_macro.csv
data/backtest/results/exposure_reduction_by_sew.csv
data/backtest/results/exposure_reduction_signal_diagnostics.csv
data/backtest/results/exposure_reduction_audit_summary.txt
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

DATA_DIR = ROOT / "data" / "backtest"
RESULT_DIR = DATA_DIR / "results"

POSITIONS_PATH = RESULT_DIR / "daily_positions.csv"
MASTER_PANEL_PATH = DATA_DIR / "master_panel.csv"

DAILY_OUT = RESULT_DIR / "exposure_reduction_daily.csv"
YEAR_OUT = RESULT_DIR / "exposure_reduction_by_year.csv"
MACRO_OUT = RESULT_DIR / "exposure_reduction_by_macro.csv"
SEW_OUT = RESULT_DIR / "exposure_reduction_by_sew.csv"
SIGNAL_OUT = RESULT_DIR / "exposure_reduction_signal_diagnostics.csv"
SUMMARY_OUT = RESULT_DIR / "exposure_reduction_audit_summary.txt"


# ============================================================
# Configuration
# ============================================================

REQUIRED_POSITION_COLUMNS = {
    "signal_date",
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
}

# Candidate master-panel columns are discovered by keyword.
# This avoids hard-coding one exact column name.
SIGNAL_KEYWORDS = {
    "positioning": (
        "pos_z",
        "position",
        "cta",
        "gamma",
    ),
    "liquidity": (
        "liquidity",
        "net_liq",
        "rrp",
        "tga",
    ),
    "credit": (
        "hy_oas",
        "hyg",
        "lqd",
        "credit",
        "spread",
    ),
    "volatility": (
        "vix",
        "volatility",
        "vol_",
    ),
    "rates": (
        "real_rate",
        "dgs2",
        "dfii10",
        "t10y2y",
        "yield",
    ),
}


# ============================================================
# Helpers
# ============================================================

def validate_columns(
    df: pd.DataFrame,
    required: Iterable[str],
    dataset_name: str,
) -> None:
    missing = sorted(set(required) - set(df.columns))

    if missing:
        raise ValueError(
            f"{dataset_name} is missing required columns: {missing}\n"
            f"Available columns:\n{list(df.columns)}"
        )


def numeric_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def safe_mean(series: pd.Series) -> float:
    values = numeric_series(series).dropna()

    if values.empty:
        return float("nan")

    return float(values.mean())


def safe_median(series: pd.Series) -> float:
    values = numeric_series(series).dropna()

    if values.empty:
        return float("nan")

    return float(values.median())


def safe_corr(left: pd.Series, right: pd.Series) -> float:
    pair = pd.concat(
        [
            numeric_series(left),
            numeric_series(right),
        ],
        axis=1,
    ).dropna()

    if len(pair) < 20:
        return float("nan")

    if pair.iloc[:, 0].nunique() < 2:
        return float("nan")

    if pair.iloc[:, 1].nunique() < 2:
        return float("nan")

    return float(pair.iloc[:, 0].corr(pair.iloc[:, 1]))


def identify_signal_columns(
    columns: Iterable[str],
) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}

    for family, keywords in SIGNAL_KEYWORDS.items():
        matches = []

        for column in columns:
            lowered = column.lower()

            if any(keyword in lowered for keyword in keywords):
                matches.append(column)

        found[family] = sorted(set(matches))

    return found


def contiguous_episode_lengths(active: pd.Series) -> pd.Series:
    """
    Return the episode length assigned to every active row.

    Example:
        False, True, True, False, True
        -> NaN, 2, 2, NaN, 1
    """

    active = active.fillna(False).astype(bool)
    group_id = active.ne(active.shift()).cumsum()

    lengths = active.groupby(group_id).transform("sum")

    return lengths.where(active, np.nan)


def build_group_summary(
    df: pd.DataFrame,
    group_column: str,
) -> pd.DataFrame:
    grouped = (
        df.groupby(group_column, dropna=False)
        .agg(
            observations=("signal_date", "size"),
            average_risk_budget_13=("risk_budget_13", "mean"),
            average_exposure_15=("exposure_15", "mean"),
            average_allocated_equity_18=("allocated_equity_18", "mean"),
            average_reduction_13_to_15=("reduction_13_to_15", "mean"),
            median_reduction_13_to_15=("reduction_13_to_15", "median"),
            total_reduction_13_to_15=("reduction_13_to_15", "sum"),
            reduction_days=("is_reduced_13_to_15", "sum"),
            zero_exposure_days=("is_zero_exposure_15", "sum"),
            average_retention_ratio=("retention_ratio_15_vs_13", "mean"),
            maximum_reduction=("reduction_13_to_15", "max"),
        )
        .reset_index()
    )

    grouped["reduction_day_share"] = (
        grouped["reduction_days"] / grouped["observations"]
    )

    grouped["zero_exposure_day_share"] = (
        grouped["zero_exposure_days"] / grouped["observations"]
    )

    return grouped.sort_values(
        "total_reduction_13_to_15",
        ascending=False,
    )


# ============================================================
# Load positions
# ============================================================

def load_positions() -> pd.DataFrame:
    if not POSITIONS_PATH.exists():
        raise FileNotFoundError(
            f"Daily position file not found:\n{POSITIONS_PATH}"
        )

    df = pd.read_csv(POSITIONS_PATH)

    validate_columns(
        df,
        REQUIRED_POSITION_COLUMNS,
        "daily_positions.csv",
    )

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )

    if "execution_date" in df.columns:
        df["execution_date"] = pd.to_datetime(
            df["execution_date"],
            errors="coerce",
        )

    for column in (
        "risk_budget_13",
        "exposure_15",
        "allocated_equity_18",
        "cash_weight",
    ):
        if column in df.columns:
            df[column] = numeric_series(df[column])

    df = (
        df.dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .drop_duplicates("signal_date", keep="last")
        .reset_index(drop=True)
    )

    valid_status = df.get(
        "status",
        pd.Series("OK", index=df.index),
    ).fillna("UNKNOWN")

    valid_error = df.get(
        "error",
        pd.Series("", index=df.index),
    ).fillna("").astype(str)

    valid_mask = (
        valid_status.eq("OK")
        & valid_error.str.strip().eq("")
        & df["risk_budget_13"].notna()
        & df["exposure_15"].notna()
        & df["allocated_equity_18"].notna()
    )

    excluded = int((~valid_mask).sum())

    if excluded:
        print(
            f"WARNING: excluding {excluded:,} rows with "
            "non-OK status, error, or missing exposure data."
        )

    return df.loc[valid_mask].copy()


# ============================================================
# Merge master panel
# ============================================================

def merge_master_panel(
    positions: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, list[str]]]:

    if not MASTER_PANEL_PATH.exists():
        print(
            "WARNING: master_panel.csv not found.\n"
            "Stage attribution will run, but signal diagnostics "
            "will be skipped."
        )

        return positions, {}

    panel = pd.read_csv(MASTER_PANEL_PATH)

    date_column = next(
        (
            column
            for column in panel.columns
            if column.lower() in {
                "date",
                "signal_date",
                "datetime",
            }
        ),
        None,
    )

    if date_column is None:
        raise ValueError(
            "master_panel.csv does not contain a date column."
        )

    panel = panel.rename(columns={date_column: "panel_date"})

    panel["panel_date"] = pd.to_datetime(
        panel["panel_date"],
        errors="coerce",
    )

    panel = (
        panel.dropna(subset=["panel_date"])
        .sort_values("panel_date")
        .drop_duplicates("panel_date", keep="last")
    )

    signal_families = identify_signal_columns(panel.columns)

    selected_signals = sorted(
        {
            column
            for columns in signal_families.values()
            for column in columns
            if column != "panel_date"
        }
    )

    merged = positions.merge(
        panel[["panel_date", *selected_signals]],
        left_on="signal_date",
        right_on="panel_date",
        how="left",
        validate="one_to_one",
    )

    merged = merged.drop(columns=["panel_date"])

    return merged, signal_families


# ============================================================
# Daily attribution
# ============================================================

def calculate_daily_attribution(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    result["reduction_13_to_15"] = (
        result["risk_budget_13"] - result["exposure_15"]
    )

    result["reduction_15_to_18"] = (
        result["exposure_15"] - result["allocated_equity_18"]
    )

    result["total_reduction_13_to_18"] = (
        result["risk_budget_13"]
        - result["allocated_equity_18"]
    )

    result["is_reduced_13_to_15"] = (
        result["reduction_13_to_15"] > 1e-9
    )

    result["is_reduced_15_to_18"] = (
        result["reduction_15_to_18"] > 1e-9
    )

    result["is_zero_exposure_15"] = (
        result["exposure_15"] <= 1e-9
    )

    result["retention_ratio_15_vs_13"] = np.where(
        result["risk_budget_13"] > 0,
        result["exposure_15"] / result["risk_budget_13"],
        np.nan,
    )

    result["retention_ratio_18_vs_15"] = np.where(
        result["exposure_15"] > 0,
        result["allocated_equity_18"] / result["exposure_15"],
        np.nan,
    )

    result["year"] = result["signal_date"].dt.year
    result["month"] = result["signal_date"].dt.to_period("M").astype(str)

    result["reduction_episode_length"] = contiguous_episode_lengths(
        result["is_reduced_13_to_15"]
    )

    result["zero_exposure_episode_length"] = contiguous_episode_lengths(
        result["is_zero_exposure_15"]
    )

    return result


# ============================================================
# Signal diagnostics
# ============================================================

def build_signal_diagnostics(
    df: pd.DataFrame,
    signal_families: dict[str, list[str]],
) -> pd.DataFrame:

    rows: list[dict[str, object]] = []

    for family, columns in signal_families.items():
        for column in columns:
            values = numeric_series(df[column])

            if values.notna().sum() < 20:
                continue

            reduced_mask = df["is_reduced_13_to_15"]
            normal_mask = ~reduced_mask

            rows.append(
                {
                    "signal_family": family,
                    "signal_column": column,
                    "observations": int(values.notna().sum()),
                    "missing_share": float(values.isna().mean()),
                    "mean_all": safe_mean(values),
                    "mean_on_reduction_days": safe_mean(
                        values[reduced_mask]
                    ),
                    "mean_on_non_reduction_days": safe_mean(
                        values[normal_mask]
                    ),
                    "median_on_reduction_days": safe_median(
                        values[reduced_mask]
                    ),
                    "median_on_non_reduction_days": safe_median(
                        values[normal_mask]
                    ),
                    "correlation_with_reduction": safe_corr(
                        values,
                        df["reduction_13_to_15"],
                    ),
                    "correlation_with_exposure_15": safe_corr(
                        values,
                        df["exposure_15"],
                    ),
                    "correlation_with_retention_ratio": safe_corr(
                        values,
                        df["retention_ratio_15_vs_13"],
                    ),
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "signal_family",
                "signal_column",
                "observations",
                "missing_share",
                "mean_all",
                "mean_on_reduction_days",
                "mean_on_non_reduction_days",
                "median_on_reduction_days",
                "median_on_non_reduction_days",
                "correlation_with_reduction",
                "correlation_with_exposure_15",
                "correlation_with_retention_ratio",
            ]
        )

    diagnostics = pd.DataFrame(rows)

    diagnostics["absolute_reduction_correlation"] = (
        diagnostics["correlation_with_reduction"].abs()
    )

    return diagnostics.sort_values(
        [
            "absolute_reduction_correlation",
            "observations",
        ],
        ascending=[False, False],
    )


# ============================================================
# Summary
# ============================================================

def make_summary(
    df: pd.DataFrame,
    signal_diagnostics: pd.DataFrame,
) -> str:

    avg_13 = safe_mean(df["risk_budget_13"])
    avg_15 = safe_mean(df["exposure_15"])
    avg_18 = safe_mean(df["allocated_equity_18"])

    reduction_13_15 = avg_13 - avg_15
    reduction_15_18 = avg_15 - avg_18
    total_reduction = avg_13 - avg_18

    if total_reduction > 0:
        share_13_15 = reduction_13_15 / total_reduction
        share_15_18 = reduction_15_18 / total_reduction
    else:
        share_13_15 = float("nan")
        share_15_18 = float("nan")

    reduction_days = int(df["is_reduced_13_to_15"].sum())
    reduction_day_share = float(
        df["is_reduced_13_to_15"].mean()
    )

    zero_days = int(df["is_zero_exposure_15"].sum())
    zero_day_share = float(
        df["is_zero_exposure_15"].mean()
    )

    max_reduction_episode = safe_mean(
        pd.Series(
            [
                df["reduction_episode_length"].max()
            ]
        )
    )

    median_reduction_episode = safe_median(
        df.loc[
            df["is_reduced_13_to_15"],
            "reduction_episode_length",
        ]
    )

    # Preliminary verdict: only identifies which stage is material.
    # It does NOT yet say whether the reduction was economically correct.
    if reduction_13_15 > 10 and share_13_15 >= 0.75:
        stage_verdict = (
            "FILTER 15 IS THE PRIMARY EXPOSURE BOTTLENECK.\n"
            "Most of the reduction from Risk Budget to allocated equity "
            "occurred between Filter 13 and Filter 15."
        )
    elif reduction_15_18 > reduction_13_15:
        stage_verdict = (
            "FILTER 18 IS THE LARGER EXPOSURE BOTTLENECK.\n"
            "More exposure was removed after Filter 15."
        )
    else:
        stage_verdict = (
            "EXPOSURE REDUCTION IS DISTRIBUTED ACROSS MULTIPLE STAGES.\n"
            "A single dominant stage was not established."
        )

    signal_text = "No master-panel signal diagnostics available."

    if not signal_diagnostics.empty:
        top = signal_diagnostics.head(10)

        lines = []

        for _, row in top.iterrows():
            corr = row["correlation_with_reduction"]

            lines.append(
                f"- {row['signal_family']:12s} | "
                f"{row['signal_column']} | "
                f"corr(reduction)={corr:.4f}"
            )

        signal_text = "\n".join(lines)

    summary = f"""
============================================================
EXPOSURE REDUCTION ATTRIBUTION AUDIT
============================================================

Period
------
{df['signal_date'].min().date()} ~ {df['signal_date'].max().date()}

Observations
------------
{len(df):,}

Average exposure by stage
-------------------------
Filter 13 Risk Budget       : {avg_13:8.2f}%
Filter 15 Final Exposure    : {avg_15:8.2f}%
Filter 18 Allocated Equity  : {avg_18:8.2f}%

Average exposure reduction
--------------------------
Filter 13 -> Filter 15      : {reduction_13_15:8.2f}%p
Filter 15 -> Filter 18      : {reduction_15_18:8.2f}%p
Filter 13 -> Filter 18      : {total_reduction:8.2f}%p

Share of total reduction
------------------------
Filter 13 -> Filter 15      : {share_13_15:8.2%}
Filter 15 -> Filter 18      : {share_15_18:8.2%}

Frequency and persistence
-------------------------
13 -> 15 reduction days     : {reduction_days:,}
Reduction-day share         : {reduction_day_share:8.2%}
Zero-exposure days at 15    : {zero_days:,}
Zero-exposure-day share     : {zero_day_share:8.2%}
Median reduction episode    : {median_reduction_episode:8.1f} days
Longest reduction episode   : {max_reduction_episode:8.1f} days

Preliminary stage verdict
-------------------------
{stage_verdict}

Important limitation
--------------------
This audit establishes WHERE exposure was removed.
It does not yet establish whether each reduction was correct.

The next audit must test the highest-ranked candidate signal
against subsequent market returns and regime context.

Top candidate signals associated with 13 -> 15 reduction
----------------------------------------------------------
{signal_text}
============================================================
""".strip()

    return summary


# ============================================================
# Main
# ============================================================

def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    positions = load_positions()

    merged, signal_families = merge_master_panel(positions)

    audit = calculate_daily_attribution(merged)

    by_year = build_group_summary(audit, "year")

    if "macro_profile" in audit.columns:
        by_macro = build_group_summary(
            audit,
            "macro_profile",
        )
    else:
        by_macro = pd.DataFrame()

    if "sew_status" in audit.columns:
        by_sew = build_group_summary(
            audit,
            "sew_status",
        )
    else:
        by_sew = pd.DataFrame()

    signal_diagnostics = build_signal_diagnostics(
        audit,
        signal_families,
    )

    summary = make_summary(
        audit,
        signal_diagnostics,
    )

    audit.to_csv(
        DAILY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    by_year.to_csv(
        YEAR_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    if not by_macro.empty:
        by_macro.to_csv(
            MACRO_OUT,
            index=False,
            encoding="utf-8-sig",
        )

    if not by_sew.empty:
        by_sew.to_csv(
            SEW_OUT,
            index=False,
            encoding="utf-8-sig",
        )

    signal_diagnostics.to_csv(
        SIGNAL_OUT,
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
    print(YEAR_OUT)

    if not by_macro.empty:
        print(MACRO_OUT)

    if not by_sew.empty:
        print(SEW_OUT)

    print(SIGNAL_OUT)
    print(SUMMARY_OUT)


if __name__ == "__main__":
    main()