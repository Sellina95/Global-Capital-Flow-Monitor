"""
Filter 15 Pre/Post Brake Event Study
====================================

Research question
-----------------
Were positive returns after Filter 15 brakes genuine false brakes,
or merely rebounds following prior market declines?

This audit examines:

- SPY return before each brake episode:
    -5D, -20D, -60D

- SPY return after each brake episode:
    +5D, +20D, +60D

Only episode-start events from the prior False Brake Audit are used.

Production strategy code is not modified.

Inputs
------
data/backtest/results/filter15_false_brake_events.csv
data/backtest/master_panel.csv

Outputs
-------
data/backtest/results/filter15_pre_post_events.csv
data/backtest/results/filter15_pre_post_summary.csv
data/backtest/results/filter15_pre_post_by_family.csv
data/backtest/results/filter15_pre_post_event_study.txt
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

EVENTS_PATH = (
    RESULT_DIR
    / "filter15_false_brake_events.csv"
)

MASTER_PANEL_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

EVENTS_OUT = (
    RESULT_DIR
    / "filter15_pre_post_events.csv"
)

SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_pre_post_summary.csv"
)

FAMILY_OUT = (
    RESULT_DIR
    / "filter15_pre_post_by_family.csv"
)

TEXT_OUT = (
    RESULT_DIR
    / "filter15_pre_post_event_study.txt"
)


WINDOWS = (5, 20, 60)


# ============================================================
# Helpers
# ============================================================

def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def find_date_column(df: pd.DataFrame) -> str:
    candidates = {
        "date",
        "signal_date",
        "execution_date",
        "datetime",
        "timestamp",
    }

    for column in df.columns:
        if str(column).lower() in candidates:
            return str(column)

    raise ValueError(
        "No usable date column found."
    )


def find_spy_column(df: pd.DataFrame) -> str:
    exact_candidates = (
        "SPY",
        "spy",
        "SPY_Close",
        "spy_close",
        "SPY_ADJ_CLOSE",
        "spy_adj_close",
    )

    lookup = {
        str(column).lower(): str(column)
        for column in df.columns
    }

    for candidate in exact_candidates:
        match = lookup.get(candidate.lower())

        if match is not None:
            return match

    for column in df.columns:
        lowered = str(column).lower()

        if (
            "spy" in lowered
            and any(
                term in lowered
                for term in (
                    "close",
                    "price",
                    "adj",
                )
            )
        ):
            return str(column)

    raise ValueError(
        "No usable SPY price column found."
    )


def safe_mean(series: pd.Series) -> float:
    values = numeric(series).dropna()

    if values.empty:
        return float("nan")

    return float(values.mean())


def safe_median(series: pd.Series) -> float:
    values = numeric(series).dropna()

    if values.empty:
        return float("nan")

    return float(values.median())


def safe_share(mask: pd.Series) -> float:
    values = mask.dropna()

    if values.empty:
        return float("nan")

    return float(values.mean())


# ============================================================
# Load data
# ============================================================

def load_episode_events() -> pd.DataFrame:
    if not EVENTS_PATH.exists():
        raise FileNotFoundError(
            f"Event file not found:\n{EVENTS_PATH}\n\n"
            "Run audit_filter15_false_brakes.py first."
        )

    events = pd.read_csv(EVENTS_PATH)

    required = {
        "signal_date",
        "brake_family",
        "episode_start",
        "brake_reduction",
        "brake_fraction",
    }

    missing = sorted(
        required - set(events.columns)
    )

    if missing:
        raise ValueError(
            f"Event file is missing columns: {missing}"
        )

    events["signal_date"] = pd.to_datetime(
        events["signal_date"],
        errors="coerce",
    )

    events["episode_start"] = (
        events["episode_start"]
        .astype(str)
        .str.lower()
        .isin(
            {
                "true",
                "1",
                "yes",
            }
        )
    )

    events["brake_reduction"] = numeric(
        events["brake_reduction"]
    )

    events["brake_fraction"] = numeric(
        events["brake_fraction"]
    )

    events = events.loc[
        events["episode_start"]
    ].copy()

    events = (
        events.dropna(
            subset=[
                "signal_date",
                "brake_family",
            ]
        )
        .sort_values(
            [
                "signal_date",
                "brake_family",
            ]
        )
        .reset_index(drop=True)
    )

    return events


def load_spy() -> pd.DataFrame:
    if not MASTER_PANEL_PATH.exists():
        raise FileNotFoundError(
            MASTER_PANEL_PATH
        )

    panel = pd.read_csv(
        MASTER_PANEL_PATH
    )

    date_column = find_date_column(panel)
    spy_column = find_spy_column(panel)

    spy = panel[
        [
            date_column,
            spy_column,
        ]
    ].copy()

    spy.columns = [
        "signal_date",
        "spy_close",
    ]

    spy["signal_date"] = pd.to_datetime(
        spy["signal_date"],
        errors="coerce",
    )

    spy["spy_close"] = numeric(
        spy["spy_close"]
    )

    spy = (
        spy.dropna(
            subset=[
                "signal_date",
                "spy_close",
            ]
        )
        .sort_values("signal_date")
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    return spy


# ============================================================
# Return calculations
# ============================================================

def add_pre_post_returns(
    spy: pd.DataFrame,
) -> pd.DataFrame:
    result = spy.copy()

    for window in WINDOWS:
        result[f"spy_pre_{window}d"] = (
            result["spy_close"]
            / result["spy_close"].shift(window)
            - 1.0
        )

        result[f"spy_post_{window}d"] = (
            result["spy_close"].shift(-window)
            / result["spy_close"]
            - 1.0
        )

    # Drawdown from trailing 20-day high at the brake date.
    trailing_high_20 = (
        result["spy_close"]
        .rolling(
            window=20,
            min_periods=5,
        )
        .max()
    )

    result["drawdown_from_20d_high"] = (
        result["spy_close"]
        / trailing_high_20
        - 1.0
    )

    trailing_high_60 = (
        result["spy_close"]
        .rolling(
            window=60,
            min_periods=20,
        )
        .max()
    )

    result["drawdown_from_60d_high"] = (
        result["spy_close"]
        / trailing_high_60
        - 1.0
    )

    return result


# ============================================================
# Event classification
# ============================================================

def classify_event(row: pd.Series) -> str:
    pre_20 = row.get(
        "spy_pre_20d",
        np.nan,
    )

    post_20 = row.get(
        "spy_post_20d",
        np.nan,
    )

    post_60 = row.get(
        "spy_post_60d",
        np.nan,
    )

    drawdown_20 = row.get(
        "drawdown_from_20d_high",
        np.nan,
    )

    if (
        pd.notna(pre_20)
        and pd.notna(post_20)
        and pre_20 <= -0.05
        and post_20 > 0
    ):
        return "POST_SELLOFF_REBOUND"

    if (
        pd.notna(drawdown_20)
        and pd.notna(post_20)
        and drawdown_20 <= -0.05
        and post_20 > 0
    ):
        return "POST_DRAWDOWN_REBOUND"

    if (
        pd.notna(post_20)
        and post_20 < -0.01
    ):
        return "PROTECTIVE_BRAKE"

    if (
        pd.notna(post_60)
        and post_60 < 0
    ):
        return "PROTECTIVE_BRAKE"

    if (
        pd.notna(pre_20)
        and pd.notna(post_20)
        and pre_20 > -0.02
        and post_20 >= 0.015
    ):
        return "LIKELY_FALSE_BRAKE"

    return "MIXED_OR_INCONCLUSIVE"


def calculate_event_costs(
    events: pd.DataFrame,
) -> pd.DataFrame:
    result = events.copy()

    for window in WINDOWS:
        result[
            f"estimated_missed_return_{window}d"
        ] = (
            result["brake_fraction"]
            * result[f"spy_post_{window}d"]
        )

        result[
            f"estimated_protection_{window}d"
        ] = (
            result["brake_fraction"]
            * -result[
                f"spy_post_{window}d"
            ].clip(upper=0)
        )

    return result


# ============================================================
# Summaries
# ============================================================

def build_family_summary(
    events: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for family, group in events.groupby(
        "brake_family"
    ):
        row: dict[str, object] = {
            "brake_family": family,
            "episodes": len(group),
            "average_brake_reduction": safe_mean(
                group["brake_reduction"]
            ),
            "median_brake_reduction": safe_median(
                group["brake_reduction"]
            ),
            "average_brake_fraction": safe_mean(
                group["brake_fraction"]
            ),
            "pre20_negative_share": safe_share(
                group["spy_pre_20d"] < 0
            ),
            "pre20_selloff_share": safe_share(
                group["spy_pre_20d"] <= -0.05
            ),
            "post20_positive_share": safe_share(
                group["spy_post_20d"] > 0
            ),
            "post20_negative_share": safe_share(
                group["spy_post_20d"] < 0
            ),
        }

        for window in WINDOWS:
            row[
                f"avg_spy_pre_{window}d"
            ] = safe_mean(
                group[f"spy_pre_{window}d"]
            )

            row[
                f"median_spy_pre_{window}d"
            ] = safe_median(
                group[f"spy_pre_{window}d"]
            )

            row[
                f"avg_spy_post_{window}d"
            ] = safe_mean(
                group[f"spy_post_{window}d"]
            )

            row[
                f"median_spy_post_{window}d"
            ] = safe_median(
                group[f"spy_post_{window}d"]
            )

            row[
                f"avg_missed_return_{window}d"
            ] = safe_mean(
                group[
                    f"estimated_missed_return_{window}d"
                ]
            )

            row[
                f"avg_protection_{window}d"
            ] = safe_mean(
                group[
                    f"estimated_protection_{window}d"
                ]
            )

        classification_counts = (
            group["event_classification"]
            .value_counts(
                normalize=True
            )
        )

        for classification in (
            "LIKELY_FALSE_BRAKE",
            "PROTECTIVE_BRAKE",
            "POST_SELLOFF_REBOUND",
            "POST_DRAWDOWN_REBOUND",
            "MIXED_OR_INCONCLUSIVE",
        ):
            row[
                f"{classification.lower()}_share"
            ] = float(
                classification_counts.get(
                    classification,
                    0.0,
                )
            )

        rows.append(row)

    return (
        pd.DataFrame(rows)
        .sort_values(
            "likely_false_brake_share",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def build_classification_summary(
    events: pd.DataFrame,
) -> pd.DataFrame:
    return (
        events.groupby(
            [
                "brake_family",
                "event_classification",
            ],
            dropna=False,
        )
        .agg(
            episodes=(
                "signal_date",
                "size",
            ),
            average_brake_reduction=(
                "brake_reduction",
                "mean",
            ),
            average_pre_20d=(
                "spy_pre_20d",
                "mean",
            ),
            average_post_20d=(
                "spy_post_20d",
                "mean",
            ),
            average_post_60d=(
                "spy_post_60d",
                "mean",
            ),
            average_missed_return_20d=(
                "estimated_missed_return_20d",
                "mean",
            ),
            average_protection_20d=(
                "estimated_protection_20d",
                "mean",
            ),
        )
        .reset_index()
        .sort_values(
            [
                "brake_family",
                "episodes",
            ],
            ascending=[
                True,
                False,
            ],
        )
    )


# ============================================================
# Verdict
# ============================================================

def family_verdict(
    row: pd.Series,
) -> str:
    false_share = row.get(
        "likely_false_brake_share",
        0.0,
    )

    protective_share = row.get(
        "protective_brake_share",
        0.0,
    )

    rebound_share = (
        row.get(
            "post_selloff_rebound_share",
            0.0,
        )
        + row.get(
            "post_drawdown_rebound_share",
            0.0,
        )
    )

    post_20 = row.get(
        "avg_spy_post_20d",
        np.nan,
    )

    if (
        false_share >= 0.30
        and false_share > protective_share
    ):
        return "STRUCTURAL_FALSE_BRAKE_CANDIDATE"

    if (
        protective_share >= 0.30
        and protective_share > false_share
    ):
        return "PREDOMINANTLY_PROTECTIVE"

    if rebound_share >= 0.30:
        return "REBOUND_CONTAMINATED"

    if (
        pd.notna(post_20)
        and post_20 > 0
    ):
        return "MIXED_WITH_UPSIDE_COST"

    return "MIXED_OR_INCONCLUSIVE"


def make_text_summary(
    events: pd.DataFrame,
    family_summary: pd.DataFrame,
) -> str:
    summary = family_summary.copy()

    summary["verdict"] = summary.apply(
        family_verdict,
        axis=1,
    )

    lines = [
        "=" * 88,
        "FILTER 15 PRE/POST BRAKE EVENT STUDY",
        "=" * 88,
        "",
        "Research question",
        "-----------------",
        (
            "Were positive returns after Filter 15 brakes genuine "
            "false brakes, or rebounds after prior selloffs?"
        ),
        "",
        "Period",
        "------",
        (
            f"{events['signal_date'].min().date()} ~ "
            f"{events['signal_date'].max().date()}"
        ),
        "",
        "Episode-start events",
        "--------------------",
        f"{len(events):,}",
        "",
        "Family results",
        "--------------",
    ]

    for _, row in summary.iterrows():
        rebound_share = (
            row[
                "post_selloff_rebound_share"
            ]
            + row[
                "post_drawdown_rebound_share"
            ]
        )

        lines.extend([
            "",
            str(
                row["brake_family"]
            ).upper(),
            (
                f"  Episodes                  : "
                f"{int(row['episodes']):,}"
            ),
            (
                f"  Average brake             : "
                f"{row['average_brake_reduction']:.2f}%p"
            ),
            (
                f"  SPY pre 20D               : "
                f"{row['avg_spy_pre_20d']:.2%}"
            ),
            (
                f"  SPY post 20D              : "
                f"{row['avg_spy_post_20d']:.2%}"
            ),
            (
                f"  SPY post 60D              : "
                f"{row['avg_spy_post_60d']:.2%}"
            ),
            (
                f"  Prior selloff share       : "
                f"{row['pre20_selloff_share']:.2%}"
            ),
            (
                f"  Rebound-contaminated share: "
                f"{rebound_share:.2%}"
            ),
            (
                f"  Likely false-brake share  : "
                f"{row['likely_false_brake_share']:.2%}"
            ),
            (
                f"  Protective-brake share    : "
                f"{row['protective_brake_share']:.2%}"
            ),
            (
                f"  Avg missed return 20D     : "
                f"{row['avg_missed_return_20d']:.2%}"
            ),
            (
                f"  Avg protection 20D        : "
                f"{row['avg_protection_20d']:.2%}"
            ),
            (
                f"  Verdict                    : "
                f"{row['verdict']}"
            ),
        ])

    lines.extend([
        "",
        "Classification rules",
        "--------------------",
        (
            "POST_SELLOFF_REBOUND: SPY had fallen at least 5% over "
            "the prior 20 trading days and subsequently recovered."
        ),
        (
            "PROTECTIVE_BRAKE: SPY fell materially after the brake."
        ),
        (
            "LIKELY_FALSE_BRAKE: there was no meaningful prior "
            "selloff, but SPY gained at least 1.5% over the next "
            "20 trading days."
        ),
        "",
        "Decision rule",
        "-------------",
        (
            "A family should only be considered an alpha-destroying "
            "candidate if its likely-false-brake share is materially "
            "larger than its protective share after rebound events "
            "are separated."
        ),
        "",
        "No thresholds or production strategy code were modified.",
        "=" * 88,
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

    events = load_episode_events()

    spy = load_spy()

    spy = add_pre_post_returns(
        spy
    )

    merged = events.merge(
        spy,
        on="signal_date",
        how="left",
        validate="many_to_one",
    )

    required_return_columns = [
        "spy_pre_20d",
        "spy_post_20d",
    ]

    merged = merged.dropna(
        subset=required_return_columns
    ).copy()

    merged = calculate_event_costs(
        merged
    )

    merged["event_classification"] = (
        merged.apply(
            classify_event,
            axis=1,
        )
    )

    family_summary = build_family_summary(
        merged
    )

    classification_summary = (
        build_classification_summary(
            merged
        )
    )

    text_summary = make_text_summary(
        merged,
        family_summary,
    )

    merged.to_csv(
        EVENTS_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    classification_summary.to_csv(
        SUMMARY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    family_summary.to_csv(
        FAMILY_OUT,
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
    print(EVENTS_OUT)
    print(SUMMARY_OUT)
    print(FAMILY_OUT)
    print(TEXT_OUT)


if __name__ == "__main__":
    main()