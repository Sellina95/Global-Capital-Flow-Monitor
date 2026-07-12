"""
Filter 15 False Brake Audit
===========================

Research question
-----------------
After Filter 15 reduced equity exposure because of:

- volatility
- positioning
- credit
- deadman

what happened to SPY over the following:

- 5 trading days
- 20 trading days
- 60 trading days?

Important
---------
Only dates where the independent Filter 15 replay exactly matched the
stored exposure_15 are used.

Production strategy code is never modified.

Inputs
------
data/backtest/results/filter15_mechanical_replay_daily.csv

SPY price is automatically searched in:
- data/backtest/master_panel.csv
- data/country_etf_data_combined.csv
- data/SPY_data.csv
- data/spy_data.csv

Outputs
-------
data/backtest/results/filter15_false_brake_events.csv
data/backtest/results/filter15_false_brake_summary.csv
data/backtest/results/filter15_false_brake_by_year.csv
data/backtest/results/filter15_false_brake_audit.txt
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

SPY_CANDIDATE_PATHS = [
    ROOT / "data" / "backtest" / "master_panel.csv",
    ROOT / "data" / "country_etf_data_combined.csv",
    ROOT / "data" / "SPY_data.csv",
    ROOT / "data" / "spy_data.csv",
]

EVENTS_OUT = (
    RESULT_DIR
    / "filter15_false_brake_events.csv"
)

SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_false_brake_summary.csv"
)

YEAR_OUT = (
    RESULT_DIR
    / "filter15_false_brake_by_year.csv"
)

TEXT_OUT = (
    RESULT_DIR
    / "filter15_false_brake_audit.txt"
)


BRAKE_COLUMNS = {
    "deadman": "deadman_reduction",
    "volatility": "volatility_reduction",
    "positioning": "positioning_reduction",
    "credit": "credit_reduction",
}

FORWARD_WINDOWS = (5, 20, 60)

EXACT_MATCH_TOLERANCE = 1e-9
BRAKE_TOLERANCE = 1e-10


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
    candidates = {
        "date",
        "signal_date",
        "execution_date",
        "datetime",
        "timestamp",
    }

    for column in columns:
        if str(column).lower() in candidates:
            return str(column)

    return None


def find_spy_column(
    columns: Iterable[str],
) -> str | None:
    """
    Find a wide-format SPY price column.
    """

    exact_priority = [
        "SPY",
        "spy",
        "SPY_Close",
        "spy_close",
        "SPY_ADJ_CLOSE",
        "spy_adj_close",
        "SPY_Adj Close",
        "spy_adj close",
    ]

    lookup = {
        str(column).lower(): str(column)
        for column in columns
    }

    for candidate in exact_priority:
        match = lookup.get(candidate.lower())

        if match:
            return match

    for column in columns:
        lowered = str(column).lower()

        if "spy" in lowered and any(
            term in lowered
            for term in (
                "close",
                "price",
                "adj",
            )
        ):
            return str(column)

    return None


def load_spy_from_wide(
    path: Path,
) -> pd.DataFrame | None:
    df = pd.read_csv(path)

    date_column = find_date_column(df.columns)
    spy_column = find_spy_column(df.columns)

    if date_column is None or spy_column is None:
        return None

    result = df[
        [
            date_column,
            spy_column,
        ]
    ].copy()

    result.columns = [
        "signal_date",
        "spy_close",
    ]

    return result


def load_spy_from_long(
    path: Path,
) -> pd.DataFrame | None:
    """
    Supports long-format data such as:

    Date, Ticker, Close

    or

    signal_date, ticker, adjusted_close
    """

    df = pd.read_csv(path)

    date_column = find_date_column(df.columns)

    if date_column is None:
        return None

    ticker_column = next(
        (
            column
            for column in df.columns
            if str(column).lower() in {
                "ticker",
                "symbol",
                "asset",
            }
        ),
        None,
    )

    if ticker_column is None:
        return None

    price_column = next(
        (
            column
            for column in df.columns
            if str(column).lower() in {
                "adj close",
                "adj_close",
                "adjusted_close",
                "close",
                "price",
            }
        ),
        None,
    )

    if price_column is None:
        return None

    ticker = (
        df[ticker_column]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    result = df.loc[
        ticker.eq("SPY"),
        [
            date_column,
            price_column,
        ],
    ].copy()

    if result.empty:
        return None

    result.columns = [
        "signal_date",
        "spy_close",
    ]

    return result


def load_spy_price() -> tuple[pd.DataFrame, Path]:
    for path in SPY_CANDIDATE_PATHS:
        if not path.exists():
            continue

        try:
            spy = load_spy_from_wide(path)

            if spy is None:
                spy = load_spy_from_long(path)

            if spy is None or spy.empty:
                continue

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

            if len(spy) >= 100:
                return spy, path

        except Exception as exc:
            print(
                f"WARNING: unable to use {path}: {exc}"
            )

    raise FileNotFoundError(
        "Could not locate a usable SPY price series.\n"
        "Checked:\n"
        + "\n".join(
            str(path)
            for path in SPY_CANDIDATE_PATHS
        )
    )


def safe_weighted_mean(
    values: pd.Series,
    weights: pd.Series,
) -> float:
    pair = pd.concat(
        [
            numeric(values).rename("value"),
            numeric(weights).rename("weight"),
        ],
        axis=1,
    ).dropna()

    pair = pair.loc[
        pair["weight"] > 0
    ]

    if pair.empty:
        return float("nan")

    return float(
        np.average(
            pair["value"],
            weights=pair["weight"],
        )
    )


# ============================================================
# Load replay
# ============================================================

def load_replay() -> pd.DataFrame:
    if not REPLAY_PATH.exists():
        raise FileNotFoundError(
            f"Replay file not found:\n{REPLAY_PATH}\n\n"
            "Run audit_filter15_mechanical_replay.py first."
        )

    df = pd.read_csv(REPLAY_PATH)

    required = {
        "signal_date",
        "risk_budget_13",
        "existing_exposure_15",
        "replay_error",
        *BRAKE_COLUMNS.values(),
    }

    missing = sorted(
        required - set(df.columns)
    )

    if missing:
        raise ValueError(
            f"Replay file is missing columns: {missing}"
        )

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )

    numeric_columns = [
        "risk_budget_13",
        "existing_exposure_15",
        "replay_error",
        *BRAKE_COLUMNS.values(),
    ]

    for column in numeric_columns:
        df[column] = numeric(df[column])

    df = (
        df.dropna(
            subset=[
                "signal_date",
                "risk_budget_13",
                "existing_exposure_15",
                "replay_error",
            ]
        )
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    # Use only dates where the independent replay matched exactly.
    df["replay_exact_match"] = (
        df["replay_error"].abs()
        <= EXACT_MATCH_TOLERANCE
    )

    return df


# ============================================================
# Forward returns
# ============================================================

def calculate_forward_returns(
    spy: pd.DataFrame,
) -> pd.DataFrame:
    result = spy.copy()

    for window in FORWARD_WINDOWS:
        result[f"spy_forward_{window}d"] = (
            result["spy_close"]
            .shift(-window)
            / result["spy_close"]
            - 1.0
        )

    return result


# ============================================================
# Event construction
# ============================================================

def build_brake_events(
    replay: pd.DataFrame,
    spy: pd.DataFrame,
) -> pd.DataFrame:
    merged = replay.merge(
        spy,
        on="signal_date",
        how="left",
        validate="one_to_one",
    )

    events: list[pd.DataFrame] = []

    for family, reduction_column in BRAKE_COLUMNS.items():
        active = (
            merged[reduction_column]
            > BRAKE_TOLERANCE
        )

        # Episode start prevents a 200-day continuous brake from
        # being counted as 200 independent signals.
        previous_active = active.shift(
            fill_value=False
        )

        episode_start = (
            active
            & ~previous_active
        )

        family_events = merged.loc[
            active
            & merged["replay_exact_match"]
            & merged["spy_close"].notna()
        ].copy()

        if family_events.empty:
            continue

        family_events["brake_family"] = family
        family_events["brake_reduction"] = (
            family_events[reduction_column]
        )

        family_events["brake_fraction"] = np.where(
            family_events["risk_budget_13"] > 0,
            family_events["brake_reduction"]
            / family_events["risk_budget_13"],
            np.nan,
        )

        family_events["episode_start"] = (
            episode_start.loc[
                family_events.index
            ].to_numpy()
        )

        family_events["year"] = (
            family_events["signal_date"].dt.year
        )

        for window in FORWARD_WINDOWS:
            forward_column = (
                f"spy_forward_{window}d"
            )

            # Positive value = return that was partly missed because
            # exposure was reduced.
            family_events[
                f"opportunity_cost_{window}d"
            ] = (
                family_events["brake_fraction"]
                * family_events[forward_column]
            )

            family_events[
                f"protection_value_{window}d"
            ] = (
                family_events["brake_fraction"]
                * -family_events[
                    forward_column
                ].clip(upper=0)
            )

        keep_columns = [
            "signal_date",
            "year",
            "brake_family",
            "episode_start",
            "risk_budget_13",
            "existing_exposure_15",
            "brake_reduction",
            "brake_fraction",
            "spy_close",
            "replay_exact_match",
        ]

        for window in FORWARD_WINDOWS:
            keep_columns.extend([
                f"spy_forward_{window}d",
                f"opportunity_cost_{window}d",
                f"protection_value_{window}d",
            ])

        events.append(
            family_events[keep_columns]
        )

    if not events:
        raise ValueError(
            "No exact-match brake events were found."
        )

    return (
        pd.concat(
            events,
            ignore_index=True,
        )
        .sort_values(
            [
                "signal_date",
                "brake_family",
            ]
        )
        .reset_index(drop=True)
    )


# ============================================================
# Summary
# ============================================================

def summarize_events(
    events: pd.DataFrame,
    *,
    episode_starts_only: bool,
) -> pd.DataFrame:
    sample = events.copy()

    if episode_starts_only:
        sample = sample.loc[
            sample["episode_start"]
        ].copy()

    rows: list[dict[str, object]] = []

    for family, group in sample.groupby(
        "brake_family"
    ):
        row: dict[str, object] = {
            "sample": (
                "episode_starts"
                if episode_starts_only
                else "all_brake_days"
            ),
            "brake_family": family,
            "observations": len(group),
            "average_brake_reduction": float(
                group["brake_reduction"].mean()
            ),
            "median_brake_reduction": float(
                group["brake_reduction"].median()
            ),
            "average_brake_fraction": float(
                group["brake_fraction"].mean()
            ),
        }

        for window in FORWARD_WINDOWS:
            forward = group[
                f"spy_forward_{window}d"
            ].dropna()

            row[
                f"avg_spy_forward_{window}d"
            ] = float(
                forward.mean()
            ) if not forward.empty else np.nan

            row[
                f"median_spy_forward_{window}d"
            ] = float(
                forward.median()
            ) if not forward.empty else np.nan

            row[
                f"positive_forward_share_{window}d"
            ] = float(
                (forward > 0).mean()
            ) if not forward.empty else np.nan

            row[
                f"negative_forward_share_{window}d"
            ] = float(
                (forward < 0).mean()
            ) if not forward.empty else np.nan

            row[
                f"weighted_spy_forward_{window}d"
            ] = safe_weighted_mean(
                group[f"spy_forward_{window}d"],
                group["brake_reduction"],
            )

            row[
                f"avg_opportunity_cost_{window}d"
            ] = float(
                group[
                    f"opportunity_cost_{window}d"
                ].mean()
            )

            row[
                f"avg_protection_value_{window}d"
            ] = float(
                group[
                    f"protection_value_{window}d"
                ].mean()
            )

        rows.append(row)

    return pd.DataFrame(rows)


def summarize_by_year(
    events: pd.DataFrame,
) -> pd.DataFrame:
    episode_events = events.loc[
        events["episode_start"]
    ].copy()

    rows: list[dict[str, object]] = []

    for (
        year,
        family,
    ), group in episode_events.groupby(
        [
            "year",
            "brake_family",
        ]
    ):
        row: dict[str, object] = {
            "year": year,
            "brake_family": family,
            "episode_count": len(group),
            "average_brake_reduction": (
                group["brake_reduction"].mean()
            ),
        }

        for window in FORWARD_WINDOWS:
            row[
                f"avg_spy_forward_{window}d"
            ] = group[
                f"spy_forward_{window}d"
            ].mean()

            row[
                f"positive_forward_share_{window}d"
            ] = (
                group[
                    f"spy_forward_{window}d"
                ]
                > 0
            ).mean()

        rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# Verdict
# ============================================================

def classify_family(
    row: pd.Series,
) -> str:
    """
    Preliminary classification based primarily on episode starts.

    This is not a threshold optimization.
    """

    forward_20 = row.get(
        "avg_spy_forward_20d",
        np.nan,
    )

    positive_share = row.get(
        "positive_forward_share_20d",
        np.nan,
    )

    forward_60 = row.get(
        "avg_spy_forward_60d",
        np.nan,
    )

    if (
        pd.notna(forward_20)
        and pd.notna(positive_share)
        and forward_20 > 0.015
        and positive_share >= 0.60
    ):
        return "LIKELY_FALSE_BRAKE"

    if (
        pd.notna(forward_20)
        and pd.notna(forward_60)
        and forward_20 < -0.01
        and forward_60 <= 0
    ):
        return "LIKELY_PROTECTIVE"

    return "MIXED_OR_INCONCLUSIVE"


def make_text_summary(
    replay: pd.DataFrame,
    spy: pd.DataFrame,
    summary: pd.DataFrame,
    spy_source: Path,
) -> str:
    episode_summary = summary.loc[
        summary["sample"].eq(
            "episode_starts"
        )
    ].copy()

    episode_summary["verdict"] = (
        episode_summary.apply(
            classify_family,
            axis=1,
        )
    )

    lines = [
        "=" * 84,
        "FILTER 15 FALSE BRAKE AUDIT",
        "=" * 84,
        "",
        "Research question",
        "-----------------",
        (
            "Did Filter 15 brakes protect against subsequent market "
            "declines, or did they suppress exposure before market gains?"
        ),
        "",
        "Data",
        "----",
        (
            f"Replay period     : "
            f"{replay['signal_date'].min().date()} ~ "
            f"{replay['signal_date'].max().date()}"
        ),
        (
            f"Replay exact days: "
            f"{int(replay['replay_exact_match'].sum()):,} / "
            f"{len(replay):,}"
        ),
        (
            f"SPY period        : "
            f"{spy['signal_date'].min().date()} ~ "
            f"{spy['signal_date'].max().date()}"
        ),
        f"SPY source        : {spy_source}",
        "",
        "Episode-start results",
        "---------------------",
    ]

    for _, row in episode_summary.iterrows():
        lines.extend([
            "",
            f"{str(row['brake_family']).upper()}",
            (
                f"  Episodes                 : "
                f"{int(row['observations']):,}"
            ),
            (
                f"  Average brake            : "
                f"{row['average_brake_reduction']:.2f}%p"
            ),
            (
                f"  SPY forward 5D           : "
                f"{row['avg_spy_forward_5d']:.2%}"
            ),
            (
                f"  SPY forward 20D          : "
                f"{row['avg_spy_forward_20d']:.2%}"
            ),
            (
                f"  SPY forward 60D          : "
                f"{row['avg_spy_forward_60d']:.2%}"
            ),
            (
                f"  Positive 20D share       : "
                f"{row['positive_forward_share_20d']:.2%}"
            ),
            (
                f"  Weighted SPY forward 20D : "
                f"{row['weighted_spy_forward_20d']:.2%}"
            ),
            (
                f"  Avg opportunity cost 20D : "
                f"{row['avg_opportunity_cost_20d']:.2%}"
            ),
            (
                f"  Avg protection value 20D : "
                f"{row['avg_protection_value_20d']:.2%}"
            ),
            f"  Preliminary verdict      : {row['verdict']}",
        ])

    lines.extend([
        "",
        "Interpretation",
        "--------------",
        (
            "Positive forward returns after a brake indicate missed "
            "upside and possible false braking."
        ),
        (
            "Negative forward returns indicate that the brake provided "
            "downside protection."
        ),
        (
            "Episode-start results are the primary evidence because "
            "continuous brake periods must not be treated as hundreds "
            "of independent signals."
        ),
        "",
        "Important limitation",
        "--------------------",
        (
            "This audit evaluates whether a brake was directionally "
            "useful. It does not yet optimize thresholds or modify "
            "strategy logic."
        ),
        "",
        "Original strategy code was not modified.",
        "=" * 84,
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

    spy, spy_source = load_spy_price()

    spy = calculate_forward_returns(spy)

    events = build_brake_events(
        replay,
        spy,
    )

    all_days_summary = summarize_events(
        events,
        episode_starts_only=False,
    )

    episode_summary = summarize_events(
        events,
        episode_starts_only=True,
    )

    summary = pd.concat(
        [
            all_days_summary,
            episode_summary,
        ],
        ignore_index=True,
    )

    summary["verdict"] = summary.apply(
        classify_family,
        axis=1,
    )

    by_year = summarize_by_year(events)

    text_summary = make_text_summary(
        replay,
        spy,
        summary,
        spy_source,
    )

    events.to_csv(
        EVENTS_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        SUMMARY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    by_year.to_csv(
        YEAR_OUT,
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
    print(YEAR_OUT)
    print(TEXT_OUT)


if __name__ == "__main__":
    main()