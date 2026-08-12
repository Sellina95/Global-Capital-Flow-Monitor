from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

INPUT_PATH = (
    RESULT_DIR
    / "filter13_candidate_current_pipeline_detail.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "portfolio_turnover_anatomy_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "portfolio_turnover_anatomy_summary.csv"
)

TOP_DAYS_PATH = (
    RESULT_DIR
    / "portfolio_turnover_anatomy_top_days.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "portfolio_turnover_anatomy_summary.txt"
)


TRADING_DAYS = 252

TINY_MOVE_THRESHOLD = 0.0025
# 0.25%p = 25 bps weight change


# ============================================================
# Helpers
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

    return float(x) / 100.0


def safe_corr(
    a: pd.Series,
    b: pd.Series,
) -> float:

    x = pd.to_numeric(
        a,
        errors="coerce",
    )

    y = pd.to_numeric(
        b,
        errors="coerce",
    )

    valid = (
        x.notna()
        & y.notna()
    )

    if valid.sum() < 3:
        return np.nan

    return float(
        x[valid].corr(
            y[valid]
        )
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            INPUT_PATH
        )

    df = pd.read_csv(
        INPUT_PATH
    )

    # ========================================================
    # Baseline only
    # ========================================================

    if "scenario" not in df.columns:
        raise ValueError(
            "scenario column missing."
        )

    df = (
        df[
            df[
                "scenario"
            ]
            == "BASELINE_CURRENT"
        ]
        .copy()
    )

    if df.empty:
        raise RuntimeError(
            "BASELINE_CURRENT rows not found."
        )

    # ========================================================
    # Dates
    # ========================================================

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

    df = (
        df
        .dropna(
            subset=[
                "execution_date"
            ]
        )
        .sort_values(
            "execution_date"
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # Weight columns
    # ========================================================

    weight_cols = [
        col
        for col in df.columns
        if col.startswith(
            "weight__"
        )
    ]

    if not weight_cols:
        raise RuntimeError(
            "weight__* columns not found."
        )

    print()
    print(
        "=" * 110
    )

    print(
        "PORTFOLIO TURNOVER ANATOMY AUDIT"
    )

    print(
        "=" * 110
    )

    print()
    print(
        f"Baseline rows  : {len(df):,}"
    )

    print(
        f"Weight columns : {len(weight_cols)}"
    )

    # ========================================================
    # Normalize weights
    # ========================================================

    norm_cols = []

    for col in weight_cols:

        norm_col = (
            "_w__"
            + col.replace(
                "weight__",
                "",
                1,
            )
        )

        df[
            norm_col
        ] = (
            df[
                col
            ]
            .apply(
                canonical_weight
            )
        )

        norm_cols.append(
            norm_col
        )

    # ========================================================
    # Canonical allocated equity
    # ========================================================

    df[
        "allocated_reconstructed"
    ] = (
        df[
            norm_cols
        ]
        .sum(
            axis=1
        )
    )

    captured_alloc = (
        pd.to_numeric(
            df[
                "allocated_equity_18"
            ],
            errors="coerce",
        )
        / 100.0
    )

    df[
        "allocation_error"
    ] = (
        df[
            "allocated_reconstructed"
        ]
        - captured_alloc
    )

    allocation_fail = int(
        (
            df[
                "allocation_error"
            ].abs()
            > 0.0011
        ).sum()
    )

    print()
    print(
        "ALLOCATION CONTRACT"
    )

    print(
        "-------------------"
    )

    print(
        f"Reconstruction fail days : "
        f"{allocation_fail:,}"
    )

    print(
        f"Max abs error            : "
        f"{df['allocation_error'].abs().max():.8f}"
    )

    if allocation_fail > 0:

        raise RuntimeError(
            "Filter18 allocation reconstruction failed."
        )

    # ========================================================
    # Daily turnover decomposition
    # ========================================================

    previous_weights = {
        col: 0.0
        for col in norm_cols
    }

    previous_allocated = 0.0

    turnover_list = []
    exposure_turnover_list = []
    rotation_turnover_list = []
    tiny_jitter_turnover_list = []
    large_move_turnover_list = []

    max_sector_change_list = []
    changed_sector_count_list = []
    tiny_change_count_list = []

    for _, row in df.iterrows():

        current_weights = {
            col: float(
                row[col]
            )
            for col in norm_cols
        }

        changes = {
            col: (
                current_weights[col]
                - previous_weights[col]
            )
            for col in norm_cols
        }

        abs_changes = {
            col: abs(
                changes[col]
            )
            for col in norm_cols
        }

        # ----------------------------------------------------
        # Exact canonical turnover
        # ----------------------------------------------------

        total_turnover = float(
            sum(
                abs_changes.values()
            )
        )

        current_allocated = float(
            sum(
                current_weights.values()
            )
        )

        # ----------------------------------------------------
        # Minimum turnover required purely from
        # gross exposure change
        # ----------------------------------------------------

        exposure_turnover = abs(
            current_allocated
            - previous_allocated
        )

        # ----------------------------------------------------
        # Residual turnover = sector reshuffling
        #
        # Since:
        # total L1 turnover >= absolute gross exposure change
        # ----------------------------------------------------

        rotation_turnover = max(
            total_turnover
            - exposure_turnover,
            0.0,
        )

        # ----------------------------------------------------
        # Tiny jitter
        # ----------------------------------------------------

        tiny_jitter_turnover = float(
            sum(
                change
                for change
                in abs_changes.values()
                if (
                    change > 0
                    and change
                    <= TINY_MOVE_THRESHOLD
                )
            )
        )

        large_move_turnover = max(
            total_turnover
            - tiny_jitter_turnover,
            0.0,
        )

        changed_sector_count = int(
            sum(
                1
                for change
                in abs_changes.values()
                if change > 1e-12
            )
        )

        tiny_change_count = int(
            sum(
                1
                for change
                in abs_changes.values()
                if (
                    change > 0
                    and change
                    <= TINY_MOVE_THRESHOLD
                )
            )
        )

        max_sector_change = (
            max(
                abs_changes.values()
            )
            if abs_changes
            else 0.0
        )

        turnover_list.append(
            total_turnover
        )

        exposure_turnover_list.append(
            exposure_turnover
        )

        rotation_turnover_list.append(
            rotation_turnover
        )

        tiny_jitter_turnover_list.append(
            tiny_jitter_turnover
        )

        large_move_turnover_list.append(
            large_move_turnover
        )

        max_sector_change_list.append(
            max_sector_change
        )

        changed_sector_count_list.append(
            changed_sector_count
        )

        tiny_change_count_list.append(
            tiny_change_count
        )

        previous_weights = (
            current_weights
        )

        previous_allocated = (
            current_allocated
        )

    # ========================================================
    # Attach turnover anatomy
    # ========================================================

    df[
        "turnover"
    ] = turnover_list

    df[
        "exposure_change_turnover"
    ] = exposure_turnover_list

    df[
        "sector_rotation_turnover"
    ] = rotation_turnover_list

    df[
        "tiny_jitter_turnover"
    ] = tiny_jitter_turnover_list

    df[
        "large_move_turnover"
    ] = large_move_turnover_list

    df[
        "max_sector_change"
    ] = max_sector_change_list

    df[
        "changed_sector_count"
    ] = changed_sector_count_list

    df[
        "tiny_change_count"
    ] = tiny_change_count_list

    # ========================================================
    # Upstream changes
    # ========================================================

    for col in [
        "risk_budget_13",
        "exposure_15",
        "allocated_equity_18",
    ]:

        numeric = pd.to_numeric(
            df[
                col
            ],
            errors="coerce",
        )

        df[
            f"{col}_change"
        ] = (
            numeric
            .diff()
        )

        df[
            f"{col}_abs_change"
        ] = (
            df[
                f"{col}_change"
            ]
            .abs()
        )

    # ========================================================
    # Turnover buckets
    # ========================================================

    df[
        "turnover_bucket"
    ] = pd.cut(
        df[
            "turnover"
        ],
        bins=[
            -np.inf,
            0.01,
            0.05,
            0.10,
            0.25,
            0.50,
            np.inf,
        ],
        labels=[
            "<=1%",
            "1-5%",
            "5-10%",
            "10-25%",
            "25-50%",
            ">50%",
        ],
    )

    # ========================================================
    # Summary stats
    # ========================================================

    total_turnover = float(
        df[
            "turnover"
        ].sum()
    )

    exposure_turnover_total = float(
        df[
            "exposure_change_turnover"
        ].sum()
    )

    rotation_turnover_total = float(
        df[
            "sector_rotation_turnover"
        ].sum()
    )

    tiny_turnover_total = float(
        df[
            "tiny_jitter_turnover"
        ].sum()
    )

    annualized_turnover = (
        df[
            "turnover"
        ].mean()
        * TRADING_DAYS
    )

    # ========================================================
    # Concentration
    # ========================================================

    sorted_turnover = (
        df[
            "turnover"
        ]
        .sort_values(
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    def top_share(
        fraction: float,
    ) -> float:

        if total_turnover <= 0:
            return np.nan

        n = max(
            1,
            int(
                np.ceil(
                    len(
                        sorted_turnover
                    )
                    * fraction
                )
            ),
        )

        return float(
            sorted_turnover
            .iloc[
                :n
            ]
            .sum()
            / total_turnover
        )

    top_1_share = top_share(
        0.01
    )

    top_5_share = top_share(
        0.05
    )

    top_10_share = top_share(
        0.10
    )

    # ========================================================
    # Correlations
    # ========================================================

    corr_13 = safe_corr(
        df[
            "turnover"
        ],
        df[
            "risk_budget_13_abs_change"
        ],
    )

    corr_15 = safe_corr(
        df[
            "turnover"
        ],
        df[
            "exposure_15_abs_change"
        ],
    )

    corr_18 = safe_corr(
        df[
            "turnover"
        ],
        df[
            "allocated_equity_18_abs_change"
        ],
    )

    # ========================================================
    # Bucket summary
    # ========================================================

    bucket_summary = (
        df.groupby(
            "turnover_bucket",
            observed=False,
        )
        .agg(
            days=(
                "turnover",
                "size",
            ),

            avg_turnover=(
                "turnover",
                "mean",
            ),

            total_turnover=(
                "turnover",
                "sum",
            ),

            avg_exposure_change_turnover=(
                "exposure_change_turnover",
                "mean",
            ),

            avg_sector_rotation_turnover=(
                "sector_rotation_turnover",
                "mean",
            ),

            avg_tiny_jitter_turnover=(
                "tiny_jitter_turnover",
                "mean",
            ),

            avg_abs_change_13=(
                "risk_budget_13_abs_change",
                "mean",
            ),

            avg_abs_change_15=(
                "exposure_15_abs_change",
                "mean",
            ),

            avg_abs_change_18=(
                "allocated_equity_18_abs_change",
                "mean",
            ),
        )
        .reset_index()
    )

    bucket_summary[
        "turnover_share"
    ] = np.where(
        total_turnover > 0,

        bucket_summary[
            "total_turnover"
        ]
        / total_turnover,

        np.nan,
    )

    # ========================================================
    # Top turnover days
    # ========================================================

    top_days = (
        df[
            [
                "signal_date",
                "execution_date",

                "risk_budget_13",
                "risk_budget_13_change",

                "exposure_15",
                "exposure_15_change",

                "allocated_equity_18",
                "allocated_equity_18_change",

                "turnover",
                "exposure_change_turnover",
                "sector_rotation_turnover",
                "tiny_jitter_turnover",

                "changed_sector_count",
                "max_sector_change",

                "deadman_reason",
                "brake_drivers",
            ]
        ]
        .sort_values(
            "turnover",
            ascending=False,
        )
        .head(
            50
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # Main summary
    # ========================================================

    summary = pd.DataFrame(
        [
            {
                "rows":
                    len(df),

                "avg_daily_turnover":
                    df[
                        "turnover"
                    ].mean(),

                "annualized_turnover":
                    annualized_turnover,

                "total_turnover":
                    total_turnover,

                "exposure_change_turnover_total":
                    exposure_turnover_total,

                "sector_rotation_turnover_total":
                    rotation_turnover_total,

                "exposure_change_share":
                    (
                        exposure_turnover_total
                        / total_turnover
                        if total_turnover > 0
                        else np.nan
                    ),

                "sector_rotation_share":
                    (
                        rotation_turnover_total
                        / total_turnover
                        if total_turnover > 0
                        else np.nan
                    ),

                "tiny_jitter_turnover_total":
                    tiny_turnover_total,

                "tiny_jitter_share":
                    (
                        tiny_turnover_total
                        / total_turnover
                        if total_turnover > 0
                        else np.nan
                    ),

                "median_daily_turnover":
                    df[
                        "turnover"
                    ].median(),

                "p90_daily_turnover":
                    df[
                        "turnover"
                    ].quantile(
                        0.90
                    ),

                "p95_daily_turnover":
                    df[
                        "turnover"
                    ].quantile(
                        0.95
                    ),

                "p99_daily_turnover":
                    df[
                        "turnover"
                    ].quantile(
                        0.99
                    ),

                "top_1pct_turnover_share":
                    top_1_share,

                "top_5pct_turnover_share":
                    top_5_share,

                "top_10pct_turnover_share":
                    top_10_share,

                "corr_turnover_abs_change_13":
                    corr_13,

                "corr_turnover_abs_change_15":
                    corr_15,

                "corr_turnover_abs_change_18":
                    corr_18,
            }
        ]
    )

    # ========================================================
    # Save
    # ========================================================

    df.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    top_days.to_csv(
        TOP_DAYS_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Report
    # ========================================================

    lines = []

    lines.append(
        "=" * 115
    )

    lines.append(
        "PORTFOLIO TURNOVER ANATOMY AUDIT"
    )

    lines.append(
        "=" * 115
    )

    lines.append("")

    lines.append(
        "Source:"
    )

    lines.append(
        "BASELINE_CURRENT from saved "
        "13→15→18 full-pipeline detail."
    )

    lines.append("")

    lines.append(
        f"Rows                 : "
        f"{len(df):,}"
    )

    lines.append(
        f"Annualized Turnover  : "
        f"{annualized_turnover:.2f}x"
    )

    lines.append("")

    lines.append(
        "TURNOVER DECOMPOSITION"
    )

    lines.append(
        "----------------------"
    )

    lines.append(
        f"Exposure-change share : "
        f"{(
            exposure_turnover_total
            / total_turnover
        ):.1%}"
    )

    lines.append(
        f"Sector-rotation share : "
        f"{(
            rotation_turnover_total
            / total_turnover
        ):.1%}"
    )

    lines.append(
        f"Tiny-jitter share     : "
        f"{(
            tiny_turnover_total
            / total_turnover
        ):.1%}"
    )

    lines.append("")

    lines.append(
        "TURNOVER DISTRIBUTION"
    )

    lines.append(
        "---------------------"
    )

    lines.append(
        f"Median daily turnover : "
        f"{df['turnover'].median():.2%}"
    )

    lines.append(
        f"P90 daily turnover    : "
        f"{df['turnover'].quantile(0.90):.2%}"
    )

    lines.append(
        f"P95 daily turnover    : "
        f"{df['turnover'].quantile(0.95):.2%}"
    )

    lines.append(
        f"P99 daily turnover    : "
        f"{df['turnover'].quantile(0.99):.2%}"
    )

    lines.append("")

    lines.append(
        "CONCENTRATION"
    )

    lines.append(
        "-------------"
    )

    lines.append(
        f"Top 1% days share     : "
        f"{top_1_share:.1%}"
    )

    lines.append(
        f"Top 5% days share     : "
        f"{top_5_share:.1%}"
    )

    lines.append(
        f"Top 10% days share    : "
        f"{top_10_share:.1%}"
    )

    lines.append("")

    lines.append(
        "UPSTREAM CORRELATION"
    )

    lines.append(
        "--------------------"
    )

    lines.append(
        f"Turnover vs |Δ13|     : "
        f"{corr_13:.3f}"
    )

    lines.append(
        f"Turnover vs |Δ15|     : "
        f"{corr_15:.3f}"
    )

    lines.append(
        f"Turnover vs |Δ18|     : "
        f"{corr_18:.3f}"
    )

    lines.append("")

    lines.append(
        "TURNOVER BUCKETS"
    )

    lines.append(
        "----------------"
    )

    lines.append(
        bucket_summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "Interpretation:"
    )

    lines.append(
        "- High exposure-change share → gross exposure "
        "adjustment is the dominant turnover source."
    )

    lines.append(
        "- High sector-rotation share → Filter18 allocation "
        "reshuffling is the dominant source."
    )

    lines.append(
        "- High tiny-jitter share → rebalance threshold / "
        "no-trade band should be investigated."
    )

    lines.append(
        "- Strong turnover correlation with |Δ15| → "
        "Filter15 exposure instability is likely driving trades."
    )

    lines.append(
        "- Strong turnover correlation with |Δ18| but weak |Δ15| "
        "→ sector allocator is likely the main culprit."
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
        TOP_DAYS_PATH
    )

    print(
        TEXT_PATH
    )


if __name__ == "__main__":
    main()