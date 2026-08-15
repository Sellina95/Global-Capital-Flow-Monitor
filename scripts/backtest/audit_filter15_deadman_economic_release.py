from __future__ import annotations

"""
FILTER15 DEADMAN ECONOMIC RELEASE TIMING AUDIT

Purpose
-------
Evaluate whether Hard Deadman episodes remained active after
the equity market had already begun to recover.

This is an observational audit only.

It does NOT:
- modify Production
- modify Filter15
- change HY_OAS thresholds
- introduce alternative release rules
- optimize parameters
- use future information in strategy execution

Inputs
------
data/backtest/results/filter15_deadman_episodes.csv
data/backtest/master_panel.csv

Outputs
-------
data/backtest/results/filter15_deadman_economic_release_daily.csv
data/backtest/results/filter15_deadman_economic_release_episodes.csv
data/backtest/results/filter15_deadman_economic_release_summary.csv
data/backtest/results/filter15_deadman_economic_release_audit.txt
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data" / "backtest"
RESULT_DIR = DATA_DIR / "results"

EPISODE_PATH = (
    RESULT_DIR
    / "filter15_deadman_episodes.csv"
)

PANEL_PATH = (
    DATA_DIR
    / "master_panel.csv"
)

DAILY_OUT = (
    RESULT_DIR
    / "filter15_deadman_economic_release_daily.csv"
)

EPISODE_OUT = (
    RESULT_DIR
    / "filter15_deadman_economic_release_episodes.csv"
)

SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_deadman_economic_release_summary.csv"
)

AUDIT_OUT = (
    RESULT_DIR
    / "filter15_deadman_economic_release_audit.txt"
)


# ============================================================
# Helpers
# ============================================================

def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def pct_return(
    current: float,
    reference: float,
) -> float:

    if (
        pd.isna(current)
        or pd.isna(reference)
        or reference == 0
    ):
        return np.nan

    return (
        float(current)
        / float(reference)
        - 1.0
    )


def safe_max(series: pd.Series) -> float:

    clean = numeric(series).dropna()

    if clean.empty:
        return np.nan

    return float(clean.max())


def safe_min(series: pd.Series) -> float:

    clean = numeric(series).dropna()

    if clean.empty:
        return np.nan

    return float(clean.min())


# ============================================================
# Load
# ============================================================

def load_data():

    if not EPISODE_PATH.exists():

        raise FileNotFoundError(
            "\nMissing Deadman episode audit:\n"
            f"{EPISODE_PATH}\n\n"
            "Run:\n"
            "python scripts/backtest/"
            "audit_filter15_deadman_episodes.py\n"
        )

    if not PANEL_PATH.exists():

        raise FileNotFoundError(
            "\nMissing master panel:\n"
            f"{PANEL_PATH}"
        )

    episodes = pd.read_csv(
        EPISODE_PATH
    )

    panel = pd.read_csv(
        PANEL_PATH
    )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    for col in [
        "start_signal_date",
        "end_signal_date",
        "next_signal_date",
    ]:

        if col in episodes.columns:

            episodes[col] = pd.to_datetime(
                episodes[col],
                errors="coerce",
            )

    required_panel = [
        "signal_date",
        "SPY",
    ]

    missing = [
        col
        for col in required_panel
        if col not in panel.columns
    ]

    if missing:

        raise ValueError(
            "master_panel.csv missing required columns: "
            f"{missing}"
        )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"],
        errors="coerce",
    )

    panel["SPY"] = numeric(
        panel["SPY"]
    )

    panel = (
        panel
        .dropna(
            subset=[
                "signal_date",
                "SPY",
            ]
        )
        .sort_values(
            "signal_date"
        )
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    return episodes, panel


# ============================================================
# Build Deadman Daily Panel
# ============================================================

def build_daily(
    episodes: pd.DataFrame,
    panel: pd.DataFrame,
) -> pd.DataFrame:

    rows = []

    spy_lookup = (
        panel
        .set_index("signal_date")["SPY"]
    )

    for _, ep in episodes.iterrows():

        episode_id = int(
            ep["episode_id"]
        )

        start_date = ep[
            "start_signal_date"
        ]

        end_date = ep[
            "end_signal_date"
        ]

        if (
            pd.isna(start_date)
            or pd.isna(end_date)
        ):
            continue

        sample = panel[
            (
                panel["signal_date"]
                >= start_date
            )
            &
            (
                panel["signal_date"]
                <= end_date
            )
        ].copy()

        if sample.empty:
            continue

        start_spy = float(
            sample.iloc[0]["SPY"]
        )

        # ----------------------------------------------------
        # Running information using ONLY information available
        # through each historical date.
        # ----------------------------------------------------

        sample["running_low_spy"] = (
            sample["SPY"]
            .cummin()
        )

        sample["return_from_episode_start"] = (
            sample["SPY"]
            / start_spy
            - 1.0
        )

        sample["recovery_from_running_low"] = (
            sample["SPY"]
            / sample["running_low_spy"]
            - 1.0
        )

        sample["new_episode_low"] = (
            sample["SPY"]
            <= sample["running_low_spy"]
        )

        # Prior rolling high, historical only.
        sample["prior_20d_high"] = (
            sample["SPY"]
            .shift(1)
            .rolling(
                20,
                min_periods=1,
            )
            .max()
        )

        sample["drawdown_from_prior_20d_high"] = (
            sample["SPY"]
            / sample["prior_20d_high"]
            - 1.0
        )

        # Historical moving averages.
        sample["spy_ma5"] = (
            sample["SPY"]
            .rolling(
                5,
                min_periods=5,
            )
            .mean()
        )

        sample["spy_ma20"] = (
            sample["SPY"]
            .rolling(
                20,
                min_periods=20,
            )
            .mean()
        )

        sample["above_ma5"] = (
            sample["SPY"]
            > sample["spy_ma5"]
        )

        sample["above_ma20"] = (
            sample["SPY"]
            > sample["spy_ma20"]
        )

        # ----------------------------------------------------
        # Observational recovery markers
        #
        # These are NOT proposed strategy rules.
        # They are descriptive thresholds only.
        # ----------------------------------------------------

        sample["recovered_5pct_from_low"] = (
            sample[
                "recovery_from_running_low"
            ]
            >= 0.05
        )

        sample["recovered_10pct_from_low"] = (
            sample[
                "recovery_from_running_low"
            ]
            >= 0.10
        )

        sample["recovered_15pct_from_low"] = (
            sample[
                "recovery_from_running_low"
            ]
            >= 0.15
        )

        for _, row in sample.iterrows():

            rows.append(
                {
                    "episode_id":
                        episode_id,

                    "signal_date":
                        row["signal_date"],

                    "SPY":
                        row["SPY"],

                    "episode_start_spy":
                        start_spy,

                    "running_low_spy":
                        row[
                            "running_low_spy"
                        ],

                    "return_from_episode_start":
                        row[
                            "return_from_episode_start"
                        ],

                    "recovery_from_running_low":
                        row[
                            "recovery_from_running_low"
                        ],

                    "drawdown_from_prior_20d_high":
                        row[
                            "drawdown_from_prior_20d_high"
                        ],

                    "above_ma5":
                        row[
                            "above_ma5"
                        ],

                    "above_ma20":
                        row[
                            "above_ma20"
                        ],

                    "recovered_5pct_from_low":
                        row[
                            "recovered_5pct_from_low"
                        ],

                    "recovered_10pct_from_low":
                        row[
                            "recovered_10pct_from_low"
                        ],

                    "recovered_15pct_from_low":
                        row[
                            "recovered_15pct_from_low"
                        ],

                    "dominant_trigger":
                        ep.get(
                            "dominant_trigger",
                            "",
                        ),

                    "max_hy_oas":
                        ep.get(
                            "max_hy_oas",
                            np.nan,
                        ),

                    "release_status":
                        ep.get(
                            "release_status",
                            "",
                        ),
                }
            )

    return pd.DataFrame(
        rows
    )


# ============================================================
# Episode Economic Analysis
# ============================================================

def first_true_date(
    sample: pd.DataFrame,
    column: str,
):

    hit = sample[
        sample[column].fillna(False)
    ]

    if hit.empty:
        return pd.NaT

    return hit.iloc[0][
        "signal_date"
    ]


def rows_after_date_until_end(
    sample: pd.DataFrame,
    date,
) -> int:

    if pd.isna(date):
        return 0

    return int(
        (
            sample["signal_date"]
            > date
        ).sum()
    )


def build_episode_analysis(
    episodes: pd.DataFrame,
    daily: pd.DataFrame,
    panel: pd.DataFrame,
) -> pd.DataFrame:

    output = []

    spy_lookup = (
        panel
        .set_index("signal_date")["SPY"]
    )

    for _, ep in episodes.iterrows():

        episode_id = int(
            ep["episode_id"]
        )

        sample = (
            daily[
                daily["episode_id"]
                == episode_id
            ]
            .sort_values(
                "signal_date"
            )
        )

        if sample.empty:
            continue

        start_date = ep[
            "start_signal_date"
        ]

        end_date = ep[
            "end_signal_date"
        ]

        next_date = ep.get(
            "next_signal_date",
            pd.NaT,
        )

        start_spy = float(
            sample.iloc[0]["SPY"]
        )

        end_spy = float(
            sample.iloc[-1]["SPY"]
        )

        low_spy = safe_min(
            sample["SPY"]
        )

        high_spy = safe_max(
            sample["SPY"]
        )

        low_rows = sample[
            sample["SPY"]
            == low_spy
        ]

        low_date = (
            low_rows.iloc[0][
                "signal_date"
            ]
            if not low_rows.empty
            else pd.NaT
        )

        # ----------------------------------------------------
        # First observable recovery dates
        # ----------------------------------------------------

        recovery_5_date = first_true_date(
            sample,
            "recovered_5pct_from_low",
        )

        recovery_10_date = first_true_date(
            sample,
            "recovered_10pct_from_low",
        )

        recovery_15_date = first_true_date(
            sample,
            "recovered_15pct_from_low",
        )

        above_ma20_date = first_true_date(
            sample,
            "above_ma20",
        )

        # ----------------------------------------------------
        # How long Deadman remained active after those
        # observable recovery milestones.
        # ----------------------------------------------------

        deadman_rows_after_5 = (
            rows_after_date_until_end(
                sample,
                recovery_5_date,
            )
        )

        deadman_rows_after_10 = (
            rows_after_date_until_end(
                sample,
                recovery_10_date,
            )
        )

        deadman_rows_after_15 = (
            rows_after_date_until_end(
                sample,
                recovery_15_date,
            )
        )

        deadman_rows_after_ma20 = (
            rows_after_date_until_end(
                sample,
                above_ma20_date,
            )
        )

        # ----------------------------------------------------
        # Market return while Deadman remained active
        # ----------------------------------------------------

        return_start_to_end = (
            pct_return(
                end_spy,
                start_spy,
            )
        )

        return_low_to_end = (
            pct_return(
                end_spy,
                low_spy,
            )
        )

        next_spy = np.nan

        if (
            pd.notna(next_date)
            and next_date
            in spy_lookup.index
        ):

            next_spy = float(
                spy_lookup.loc[
                    next_date
                ]
            )

        return_low_to_release = (
            pct_return(
                next_spy,
                low_spy,
            )
        )

        # ----------------------------------------------------
        # Observational late-release flags
        #
        # NOT strategy recommendations.
        # ----------------------------------------------------

        recovered_5_before_release = (
            pd.notna(
                recovery_5_date
            )
            and recovery_5_date
            < end_date
        )

        recovered_10_before_release = (
            pd.notna(
                recovery_10_date
            )
            and recovery_10_date
            < end_date
        )

        recovered_15_before_release = (
            pd.notna(
                recovery_15_date
            )
            and recovery_15_date
            < end_date
        )

        output.append(
            {
                "episode_id":
                    episode_id,

                "start_signal_date":
                    start_date,

                "end_signal_date":
                    end_date,

                "next_signal_date":
                    next_date,

                "duration_rows":
                    ep.get(
                        "duration_rows",
                        len(sample),
                    ),

                "dominant_trigger":
                    ep.get(
                        "dominant_trigger",
                        "",
                    ),

                "trigger_sequence":
                    ep.get(
                        "trigger_sequence",
                        "",
                    ),

                "start_spy":
                    start_spy,

                "episode_low_spy":
                    low_spy,

                "episode_low_date":
                    low_date,

                "end_spy":
                    end_spy,

                "next_spy":
                    next_spy,

                "return_start_to_end":
                    return_start_to_end,

                "return_low_to_end":
                    return_low_to_end,

                "return_low_to_release":
                    return_low_to_release,

                "recovery_5_date":
                    recovery_5_date,

                "recovery_10_date":
                    recovery_10_date,

                "recovery_15_date":
                    recovery_15_date,

                "above_ma20_date":
                    above_ma20_date,

                "deadman_rows_after_5pct_recovery":
                    deadman_rows_after_5,

                "deadman_rows_after_10pct_recovery":
                    deadman_rows_after_10,

                "deadman_rows_after_15pct_recovery":
                    deadman_rows_after_15,

                "deadman_rows_after_ma20":
                    deadman_rows_after_ma20,

                "recovered_5_before_release":
                    recovered_5_before_release,

                "recovered_10_before_release":
                    recovered_10_before_release,

                "recovered_15_before_release":
                    recovered_15_before_release,

                "max_hy_oas":
                    ep.get(
                        "max_hy_oas",
                        np.nan,
                    ),

                "next_risk_budget_13":
                    ep.get(
                        "next_risk_budget_13",
                        np.nan,
                    ),

                "next_exposure_15":
                    ep.get(
                        "next_exposure_15",
                        np.nan,
                    ),

                "release_status":
                    ep.get(
                        "release_status",
                        "",
                    ),
            }
        )

    return pd.DataFrame(
        output
    )


# ============================================================
# Summary
# ============================================================

def build_summary(
    ep: pd.DataFrame,
) -> pd.DataFrame:

    total = len(ep)

    rows = []

    def add_metric(
        metric,
        count,
        extra=np.nan,
    ):

        rows.append(
            {
                "metric":
                    metric,

                "count":
                    int(count),

                "pct_of_episodes":
                    (
                        float(count)
                        / total
                        * 100.0
                        if total
                        else 0.0
                    ),

                "value":
                    extra,
            }
        )

    add_metric(
        "TOTAL_EPISODES",
        total,
    )

    count_5 = int(
        ep[
            "recovered_5_before_release"
        ].sum()
    )

    count_10 = int(
        ep[
            "recovered_10_before_release"
        ].sum()
    )

    count_15 = int(
        ep[
            "recovered_15_before_release"
        ].sum()
    )

    add_metric(
        "RECOVERED_5PCT_BEFORE_RELEASE",
        count_5,
        ep[
            "deadman_rows_after_5pct_recovery"
        ].mean(),
    )

    add_metric(
        "RECOVERED_10PCT_BEFORE_RELEASE",
        count_10,
        ep[
            "deadman_rows_after_10pct_recovery"
        ].mean(),
    )

    add_metric(
        "RECOVERED_15PCT_BEFORE_RELEASE",
        count_15,
        ep[
            "deadman_rows_after_15pct_recovery"
        ].mean(),
    )

    add_metric(
        "HY_OAS_DOMINANT_EPISODES",
        int(
            (
                ep[
                    "dominant_trigger"
                ]
                == "HY_OAS_GE_6"
            ).sum()
        ),
    )

    rows.append(
        {
            "metric":
                "AVG_LOW_TO_END_RETURN",

            "count":
                total,

            "pct_of_episodes":
                100.0,

            "value":
                ep[
                    "return_low_to_end"
                ].mean(),
        }
    )

    rows.append(
        {
            "metric":
                "MEDIAN_LOW_TO_END_RETURN",

            "count":
                total,

            "pct_of_episodes":
                100.0,

            "value":
                ep[
                    "return_low_to_end"
                ].median(),
        }
    )

    rows.append(
        {
            "metric":
                "AVG_LOW_TO_RELEASE_RETURN",

            "count":
                int(
                    ep[
                        "return_low_to_release"
                    ].notna().sum()
                ),

            "pct_of_episodes":
                (
                    ep[
                        "return_low_to_release"
                    ]
                    .notna()
                    .mean()
                    * 100.0
                ),

            "value":
                ep[
                    "return_low_to_release"
                ].mean(),
        }
    )

    return pd.DataFrame(
        rows
    )


# ============================================================
# Main
# ============================================================

def main():

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    episodes, panel = load_data()

    daily = build_daily(
        episodes,
        panel,
    )

    ep = build_episode_analysis(
        episodes,
        daily,
        panel,
    )

    summary = build_summary(
        ep
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    expected_episodes = len(
        episodes
    )

    analyzed_episodes = len(
        ep
    )

    episode_reconciliation = (
        expected_episodes
        == analyzed_episodes
    )

    future_date_violation = False

    for _, row in ep.iterrows():

        end_date = row[
            "end_signal_date"
        ]

        for col in [
            "recovery_5_date",
            "recovery_10_date",
            "recovery_15_date",
            "above_ma20_date",
        ]:

            value = row[col]

            if (
                pd.notna(value)
                and value > end_date
            ):

                future_date_violation = True

    result = (
        "PASS"
        if (
            episode_reconciliation
            and not future_date_violation
        )
        else "FAIL"
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    daily.to_csv(
        DAILY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    ep.to_csv(
        EPISODE_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        SUMMARY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # Useful statistics
    # --------------------------------------------------------

    recovered_5 = int(
        ep[
            "recovered_5_before_release"
        ].sum()
    )

    recovered_10 = int(
        ep[
            "recovered_10_before_release"
        ].sum()
    )

    recovered_15 = int(
        ep[
            "recovered_15_before_release"
        ].sum()
    )

    hy_ep = ep[
        ep[
            "dominant_trigger"
        ]
        == "HY_OAS_GE_6"
    ]

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    lines = []

    lines.append(
        "# FILTER15 DEADMAN ECONOMIC RELEASE AUDIT"
    )

    lines.append("")

    lines.append(
        f"Episodes Expected      : {expected_episodes}"
    )

    lines.append(
        f"Episodes Analyzed      : {analyzed_episodes}"
    )

    lines.append(
        "Episode Reconciliation : "
        + (
            "PASS"
            if episode_reconciliation
            else "FAIL"
        )
    )

    lines.append(
        "Future-Date Violation  : "
        + (
            "YES"
            if future_date_violation
            else "NO"
        )
    )

    lines.append("")

    lines.append(
        f"5% Recovery Before Release  : {recovered_5}"
    )

    lines.append(
        f"10% Recovery Before Release : {recovered_10}"
    )

    lines.append(
        f"15% Recovery Before Release : {recovered_15}"
    )

    lines.append("")

    lines.append(
        "Average Low -> Deadman End Return: "
        f"{ep['return_low_to_end'].mean():.4%}"
    )

    lines.append(
        "Median Low -> Deadman End Return : "
        f"{ep['return_low_to_end'].median():.4%}"
    )

    lines.append(
        "Average Low -> Release Return    : "
        f"{ep['return_low_to_release'].mean():.4%}"
    )

    lines.append("")

    lines.append(
        f"HY_OAS Dominant Episodes: {len(hy_ep)}"
    )

    if len(hy_ep):

        lines.append(
            "HY_OAS Avg Low -> Deadman End: "
            f"{hy_ep['return_low_to_end'].mean():.4%}"
        )

        lines.append(
            "HY_OAS Median Low -> Deadman End: "
            f"{hy_ep['return_low_to_end'].median():.4%}"
        )

        lines.append(
            "HY_OAS Avg Deadman Rows After "
            "5% Recovery: "
            f"{hy_ep['deadman_rows_after_5pct_recovery'].mean():.2f}"
        )

        lines.append(
            "HY_OAS Avg Deadman Rows After "
            "10% Recovery: "
            f"{hy_ep['deadman_rows_after_10pct_recovery'].mean():.2f}"
        )

    lines.append("")

    lines.append(
        "Production source modified: NO"
    )

    lines.append(
        "Filter15 threshold modified: NO"
    )

    lines.append(
        "Counterfactual rule introduced: NO"
    )

    lines.append(
        "Future-data strategy backfill: NO"
    )

    lines.append("")

    lines.append(
        "IMPORTANT:"
    )

    lines.append(
        "5% / 10% / 15% recovery markers are "
        "descriptive audit markers only."
    )

    lines.append(
        "They are NOT proposed trading thresholds."
    )

    lines.append("")

    lines.append(
        f"RESULT: FILTER15 DEADMAN ECONOMIC RELEASE AUDIT {result}"
    )

    AUDIT_OUT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    # ========================================================
    # Console
    # ========================================================

    print(
        "\n"
        + "=" * 78
    )

    print(
        "FILTER15 DEADMAN ECONOMIC RELEASE TIMING AUDIT"
    )

    print(
        "=" * 78
    )

    print(
        f"\nEpisodes Expected : {expected_episodes}"
    )

    print(
        f"Episodes Analyzed : {analyzed_episodes}"
    )

    print(
        "Reconciliation    : "
        + (
            "PASS"
            if episode_reconciliation
            else "FAIL"
        )
    )

    print(
        "Future Violation  : "
        + (
            "YES"
            if future_date_violation
            else "NO"
        )
    )

    print(
        "\n===== RECOVERY BEFORE DEADMAN RELEASE ====="
    )

    print(
        f"5% recovery  : {recovered_5}"
    )

    print(
        f"10% recovery : {recovered_10}"
    )

    print(
        f"15% recovery : {recovered_15}"
    )

    print(
        "\n===== MARKET RECOVERY WHILE DEADMAN ACTIVE ====="
    )

    print(
        "Average Low -> Deadman End : "
        f"{ep['return_low_to_end'].mean():.2%}"
    )

    print(
        "Median Low -> Deadman End  : "
        f"{ep['return_low_to_end'].median():.2%}"
    )

    print(
        "Average Low -> Release     : "
        f"{ep['return_low_to_release'].mean():.2%}"
    )

    print(
        "\n===== HY_OAS DOMINANT EPISODES ====="
    )

    print(
        f"Episodes: {len(hy_ep)}"
    )

    if len(hy_ep):

        print(
            "Avg Low -> End: "
            f"{hy_ep['return_low_to_end'].mean():.2%}"
        )

        print(
            "Median Low -> End: "
            f"{hy_ep['return_low_to_end'].median():.2%}"
        )

        print(
            "Avg rows after 5% recovery: "
            f"{hy_ep['deadman_rows_after_5pct_recovery'].mean():.2f}"
        )

        print(
            "Avg rows after 10% recovery: "
            f"{hy_ep['deadman_rows_after_10pct_recovery'].mean():.2f}"
        )

    print(
        "\n===== LONGEST / LATEST RELEASE CASES ====="
    )

    display_cols = [
        "episode_id",
        "start_signal_date",
        "end_signal_date",
        "duration_rows",
        "dominant_trigger",
        "episode_low_date",
        "return_low_to_end",
        "recovery_5_date",
        "deadman_rows_after_5pct_recovery",
        "recovery_10_date",
        "deadman_rows_after_10pct_recovery",
        "next_exposure_15",
    ]

    print(
        ep.sort_values(
            [
                "deadman_rows_after_5pct_recovery",
                "duration_rows",
            ],
            ascending=False,
        )
        .head(20)[
            display_cols
        ]
        .to_string(
            index=False
        )
    )

    print(
        "\n"
        + "=" * 78
    )

    print(
        f"RESULT: FILTER15 DEADMAN ECONOMIC RELEASE AUDIT {result}"
    )

    print(
        "=" * 78
    )

    print(
        f"\nSaved: {DAILY_OUT}"
    )

    print(
        f"Saved: {EPISODE_OUT}"
    )

    print(
        f"Saved: {SUMMARY_OUT}"
    )

    print(
        f"Saved: {AUDIT_OUT}"
    )


if __name__ == "__main__":
    main()