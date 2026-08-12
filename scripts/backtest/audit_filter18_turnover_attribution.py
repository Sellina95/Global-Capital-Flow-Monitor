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

PIPELINE_PATH = (
    RESULT_DIR
    / "filter13_candidate_current_pipeline_detail.csv"
)

TURNOVER_PATH = (
    RESULT_DIR
    / "portfolio_turnover_anatomy_detail.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter18_turnover_attribution_detail.csv"
)

SECTOR_SUMMARY_PATH = (
    RESULT_DIR
    / "filter18_turnover_attribution_sector_summary.csv"
)

EVENT_SUMMARY_PATH = (
    RESULT_DIR
    / "filter18_turnover_attribution_event_summary.csv"
)

TOP_DAYS_PATH = (
    RESULT_DIR
    / "filter18_turnover_attribution_top_days.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter18_turnover_attribution_summary.txt"
)


# ============================================================
# Contract
# ============================================================

SCENARIO = "BASELINE_CURRENT"

TINY = 1e-12

LOW_EXPOSURE_CHANGE = 0.02
# 2%p 이하 gross exposure 변화인데
# sector rotation이 크면 "allocation reshuffle" 후보

HIGH_ROTATION = 0.20
# 20% 이상 sector rotation


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
    x: pd.Series,
    y: pd.Series,
) -> float:

    a = pd.to_numeric(
        x,
        errors="coerce",
    )

    b = pd.to_numeric(
        y,
        errors="coerce",
    )

    valid = (
        a.notna()
        & b.notna()
    )

    if valid.sum() < 3:
        return np.nan

    return float(
        a[valid].corr(
            b[valid]
        )
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    if not PIPELINE_PATH.exists():
        raise FileNotFoundError(
            PIPELINE_PATH
        )

    if not TURNOVER_PATH.exists():
        raise FileNotFoundError(
            TURNOVER_PATH
        )

    pipeline = pd.read_csv(
        PIPELINE_PATH
    )

    turnover = pd.read_csv(
        TURNOVER_PATH
    )

    # ========================================================
    # Baseline only
    # ========================================================

    pipeline = (
        pipeline[
            pipeline[
                "scenario"
            ]
            == SCENARIO
        ]
        .copy()
    )

    if pipeline.empty:
        raise RuntimeError(
            f"{SCENARIO} not found."
        )

    # ========================================================
    # Dates
    # ========================================================

    for df in (
        pipeline,
        turnover,
    ):

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

    # ========================================================
    # Weight columns
    # ========================================================

    weight_cols = [
        col
        for col in pipeline.columns
        if col.startswith(
            "weight__"
        )
    ]

    if not weight_cols:
        raise RuntimeError(
            "Filter18 weight columns not found."
        )

    print()
    print(
        "=" * 110
    )

    print(
        "FILTER18 TURNOVER ATTRIBUTION AUDIT"
    )

    print(
        "=" * 110
    )

    print()
    print(
        f"Baseline rows : {len(pipeline):,}"
    )

    print(
        f"Sector count  : {len(weight_cols)}"
    )

    # ========================================================
    # Normalize weights
    # ========================================================

    sector_norm_cols = {}

    for col in weight_cols:

        sector = col.replace(
            "weight__",
            "",
            1,
        )

        norm_col = (
            "_w__"
            + sector
        )

        pipeline[
            norm_col
        ] = (
            pipeline[
                col
            ]
            .apply(
                canonical_weight
            )
        )

        sector_norm_cols[
            sector
        ] = norm_col

    # ========================================================
    # Daily sector weight changes
    # ========================================================

    sector_change_cols = {}
    sector_abs_change_cols = {}

    for sector, norm_col in (
        sector_norm_cols.items()
    ):

        change_col = (
            "_dw__"
            + sector
        )

        abs_col = (
            "_absdw__"
            + sector
        )

        pipeline[
            change_col
        ] = (
            pipeline[
                norm_col
            ]
            .diff()
            .fillna(
                pipeline[
                    norm_col
                ]
            )
        )

        pipeline[
            abs_col
        ] = (
            pipeline[
                change_col
            ]
            .abs()
        )

        sector_change_cols[
            sector
        ] = change_col

        sector_abs_change_cols[
            sector
        ] = abs_col

    # ========================================================
    # Reconstructed turnover
    # ========================================================

    abs_change_cols = list(
        sector_abs_change_cols.values()
    )

    pipeline[
        "turnover_reconstructed"
    ] = (
        pipeline[
            abs_change_cols
        ]
        .sum(
            axis=1
        )
    )

    # ========================================================
    # Merge turnover anatomy
    # ========================================================

    needed_turnover_cols = [
        "signal_date",
        "execution_date",
        "turnover",
        "exposure_change_turnover",
        "sector_rotation_turnover",
        "tiny_jitter_turnover",
        "risk_budget_13_abs_change",
        "exposure_15_abs_change",
        "allocated_equity_18_abs_change",
    ]

    missing_turnover_cols = [
        c
        for c in needed_turnover_cols
        if c not in turnover.columns
    ]

    if missing_turnover_cols:

        raise ValueError(
            "Turnover anatomy missing columns:\n"
            f"{missing_turnover_cols}"
        )

    df = pipeline.merge(
        turnover[
            needed_turnover_cols
        ],
        on=[
            "signal_date",
            "execution_date",
        ],
        how="left",
    )

    # ========================================================
    # Parity
    # ========================================================

    df[
        "turnover_error"
    ] = (
        df[
            "turnover_reconstructed"
        ]
        -
        df[
            "turnover"
        ]
    )

    turnover_fail = int(
        (
            df[
                "turnover_error"
            ]
            .abs()
            > 1e-9
        ).sum()
    )

    max_turnover_error = (
        df[
            "turnover_error"
        ]
        .abs()
        .max()
    )

    print()
    print(
        "TURNOVER PARITY"
    )

    print(
        "---------------"
    )

    print(
        f"Fail days    : "
        f"{turnover_fail:,}"
    )

    print(
        f"Max abs error: "
        f"{max_turnover_error:.10f}"
    )

    if turnover_fail > 0:

        raise RuntimeError(
            "Turnover reconstruction parity failed."
        )

    # ========================================================
    # Per-sector contribution
    # ========================================================

    sector_rows = []

    total_turnover = (
        df[
            "turnover"
        ].sum()
    )

    for sector, abs_col in (
        sector_abs_change_cols.items()
    ):

        total_sector_turnover = (
            df[
                abs_col
            ].sum()
        )

        sector_rows.append(
            {
                "sector":
                    sector,

                "total_abs_weight_change":
                    total_sector_turnover,

                "turnover_share":
                    (
                        total_sector_turnover
                        / total_turnover
                        if total_turnover > 0
                        else np.nan
                    ),

                "avg_daily_abs_change":
                    df[
                        abs_col
                    ].mean(),

                "median_daily_abs_change":
                    df[
                        abs_col
                    ].median(),

                "p95_abs_change":
                    df[
                        abs_col
                    ].quantile(
                        0.95
                    ),

                "change_days":
                    int(
                        (
                            df[
                                abs_col
                            ]
                            > TINY
                        ).sum()
                    ),

                "large_change_days_gt5pct":
                    int(
                        (
                            df[
                                abs_col
                            ]
                            >= 0.05
                        ).sum()
                    ),
            }
        )

    sector_summary = (
        pd.DataFrame(
            sector_rows
        )
        .sort_values(
            "turnover_share",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # Buy / sell legs
    # ========================================================

    buy_cols = []
    sell_cols = []

    for sector, change_col in (
        sector_change_cols.items()
    ):

        buy_col = (
            "_buy__"
            + sector
        )

        sell_col = (
            "_sell__"
            + sector
        )

        df[
            buy_col
        ] = (
            df[
                change_col
            ]
            .clip(
                lower=0.0
            )
        )

        df[
            sell_col
        ] = (
            -df[
                change_col
            ]
        ).clip(
            lower=0.0
        )

        buy_cols.append(
            buy_col
        )

        sell_cols.append(
            sell_col
        )

    df[
        "total_buys"
    ] = (
        df[
            buy_cols
        ]
        .sum(
            axis=1
        )
    )

    df[
        "total_sells"
    ] = (
        df[
            sell_cols
        ]
        .sum(
            axis=1
        )
    )

    # ========================================================
    # Rotation classification
    # ========================================================

    df[
        "low_exposure_change"
    ] = (
        df[
            "allocated_equity_18_abs_change"
        ]
        <= (
            LOW_EXPOSURE_CHANGE
            * 100.0
        )
    )

    df[
        "high_rotation"
    ] = (
        df[
            "sector_rotation_turnover"
        ]
        >= HIGH_ROTATION
    )

    df[
        "pure_rotation_candidate"
    ] = (
        df[
            "low_exposure_change"
        ]
        &
        df[
            "high_rotation"
        ]
    )

    # ========================================================
    # Breadth of rotation
    # ========================================================

    df[
        "sector_change_count"
    ] = (
        df[
            abs_change_cols
        ]
        .gt(
            TINY
        )
        .sum(
            axis=1
        )
    )

    df[
        "sector_large_change_count"
    ] = (
        df[
            abs_change_cols
        ]
        .ge(
            0.05
        )
        .sum(
            axis=1
        )
    )

    # ========================================================
    # Dominant sector
    # ========================================================

    dominant_sectors = []
    dominant_changes = []

    for _, row in df.iterrows():

        values = {
            sector:
                float(
                    row[
                        abs_col
                    ]
                )

            for sector, abs_col
            in sector_abs_change_cols.items()
        }

        if not values:

            dominant_sectors.append(
                ""
            )

            dominant_changes.append(
                0.0
            )

            continue

        sector = max(
            values,
            key=values.get,
        )

        dominant_sectors.append(
            sector
        )

        dominant_changes.append(
            values[
                sector
            ]
        )

    df[
        "dominant_turnover_sector"
    ] = dominant_sectors

    df[
        "dominant_sector_abs_change"
    ] = dominant_changes

    # ========================================================
    # Event groups
    # ========================================================

    conditions = [
        df[
            "sector_rotation_turnover"
        ]
        > df[
            "exposure_change_turnover"
        ],

        df[
            "sector_rotation_turnover"
        ]
        < df[
            "exposure_change_turnover"
        ],
    ]

    choices = [
        "ROTATION_DOMINANT",
        "EXPOSURE_DOMINANT",
    ]

    df[
        "turnover_driver"
    ] = np.select(
        conditions,
        choices,
        default="BALANCED",
    )

    event_summary = (
        df.groupby(
            "turnover_driver"
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

            avg_sector_rotation=(
                "sector_rotation_turnover",
                "mean",
            ),

            avg_exposure_change=(
                "exposure_change_turnover",
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

            avg_sector_change_count=(
                "sector_change_count",
                "mean",
            ),

            pure_rotation_days=(
                "pure_rotation_candidate",
                "sum",
            ),
        )
        .reset_index()
    )

    event_summary[
        "turnover_share"
    ] = np.where(
        total_turnover > 0,

        event_summary[
            "total_turnover"
        ]
        / total_turnover,

        np.nan,
    )

    # ========================================================
    # Correlation by sector
    # ========================================================

    sector_corr_rows = []

    for sector, abs_col in (
        sector_abs_change_cols.items()
    ):

        sector_corr_rows.append(
            {
                "sector":
                    sector,

                "corr_with_total_turnover":
                    safe_corr(
                        df[
                            abs_col
                        ],
                        df[
                            "turnover"
                        ],
                    ),

                "corr_with_rotation_turnover":
                    safe_corr(
                        df[
                            abs_col
                        ],
                        df[
                            "sector_rotation_turnover"
                        ],
                    ),
            }
        )

    sector_corr = pd.DataFrame(
        sector_corr_rows
    )

    sector_summary = (
        sector_summary.merge(
            sector_corr,
            on="sector",
            how="left",
        )
    )

    # ========================================================
    # Top days
    # ========================================================

    top_cols = [
        "signal_date",
        "execution_date",

        "risk_budget_13",
        "exposure_15",
        "allocated_equity_18",

        "turnover",
        "exposure_change_turnover",
        "sector_rotation_turnover",

        "turnover_driver",
        "pure_rotation_candidate",

        "sector_change_count",
        "sector_large_change_count",

        "dominant_turnover_sector",
        "dominant_sector_abs_change",

        "deadman_reason",
        "brake_drivers",
    ]

    top_days = (
        df[
            top_cols
        ]
        .sort_values(
            "turnover",
            ascending=False,
        )
        .head(
            100
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # Overall diagnostics
    # ========================================================

    rotation_dominant_days = int(
        (
            df[
                "turnover_driver"
            ]
            == "ROTATION_DOMINANT"
        ).sum()
    )

    rotation_dominant_turnover_share = (
        df.loc[
            df[
                "turnover_driver"
            ]
            == "ROTATION_DOMINANT",
            "turnover",
        ].sum()
        / total_turnover
        if total_turnover > 0
        else np.nan
    )

    pure_rotation_days = int(
        df[
            "pure_rotation_candidate"
        ].sum()
    )

    pure_rotation_turnover_share = (
        df.loc[
            df[
                "pure_rotation_candidate"
            ],
            "turnover",
        ].sum()
        / total_turnover
        if total_turnover > 0
        else np.nan
    )

    corr_rotation_15 = safe_corr(
        df[
            "sector_rotation_turnover"
        ],
        df[
            "exposure_15_abs_change"
        ],
    )

    corr_rotation_18 = safe_corr(
        df[
            "sector_rotation_turnover"
        ],
        df[
            "allocated_equity_18_abs_change"
        ],
    )

    # ========================================================
    # Save
    # ========================================================

    df.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    sector_summary.to_csv(
        SECTOR_SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    event_summary.to_csv(
        EVENT_SUMMARY_PATH,
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
        "=" * 120
    )

    lines.append(
        "FILTER18 TURNOVER ATTRIBUTION AUDIT"
    )

    lines.append(
        "=" * 120
    )

    lines.append("")

    lines.append(
        "TURNOVER PARITY"
    )

    lines.append(
        "---------------"
    )

    lines.append(
        f"Fail days        : "
        f"{turnover_fail}"
    )

    lines.append(
        f"Max abs error    : "
        f"{max_turnover_error:.10f}"
    )

    lines.append("")

    lines.append(
        "ROTATION DIAGNOSTICS"
    )

    lines.append(
        "--------------------"
    )

    lines.append(
        f"Rotation-dominant days            : "
        f"{rotation_dominant_days:,}"
    )

    lines.append(
        f"Rotation-dominant turnover share  : "
        f"{rotation_dominant_turnover_share:.1%}"
    )

    lines.append(
        f"Pure-rotation candidate days      : "
        f"{pure_rotation_days:,}"
    )

    lines.append(
        f"Pure-rotation turnover share      : "
        f"{pure_rotation_turnover_share:.1%}"
    )

    lines.append(
        f"Corr rotation turnover vs |Δ15|   : "
        f"{corr_rotation_15:.3f}"
    )

    lines.append(
        f"Corr rotation turnover vs |Δ18|   : "
        f"{corr_rotation_18:.3f}"
    )

    lines.append("")

    lines.append(
        "SECTOR TURNOVER CONTRIBUTION"
    )

    lines.append(
        "----------------------------"
    )

    lines.append(
        sector_summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "EVENT GROUPS"
    )

    lines.append(
        "------------"
    )

    lines.append(
        event_summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "Interpretation:"
    )

    lines.append(
        "- A few sectors dominating turnover → "
        "sector-specific ranking/cap rules should be inspected."
    )

    lines.append(
        "- Broad sector participation with high rotation "
        "and low gross-exposure change → "
        "Filter18 allocation reshuffling is likely structural."
    )

    lines.append(
        "- High pure-rotation turnover share → "
        "rank persistence / hysteresis / rebalance threshold "
        "becomes a strong production candidate."
    )

    lines.append(
        "- If rotation turnover rises mainly when Filter15 changes, "
        "Filter18 may be reacting mechanically to upstream exposure."
    )

    lines.append(
        "- If rotation remains high despite small |Δ15|, "
        "Filter18 itself is the primary source."
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
        SECTOR_SUMMARY_PATH
    )

    print(
        EVENT_SUMMARY_PATH
    )

    print(
        TOP_DAYS_PATH
    )

    print(
        TEXT_PATH
    )


if __name__ == "__main__":
    main()