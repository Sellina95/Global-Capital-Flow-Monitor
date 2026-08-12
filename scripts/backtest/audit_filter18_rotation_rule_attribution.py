from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# Path bootstrap
# ============================================================

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


import filters.strategist_filters as sf
import scripts.backtest.run_backtest as rb


# ============================================================
# Paths
# ============================================================

DATA_DIR = ROOT / "data" / "backtest"
RESULT_DIR = DATA_DIR / "results"

PANEL_PATH = (
    DATA_DIR
    / "master_panel.csv"
)

EXECUTED_TURNOVER_PATH = (
    RESULT_DIR
    / "filter18_rebalance_threshold_replay_detail.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter18_rotation_rule_attribution_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter18_rotation_rule_attribution_summary.csv"
)

EVENT_PATH = (
    RESULT_DIR
    / "filter18_rotation_rule_attribution_events.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter18_rotation_rule_attribution_summary.txt"
)


SCENARIO = "BASELINE_CURRENT"


# ============================================================
# Helpers
# ============================================================

def safe_float(
    x,
    default=np.nan,
):
    try:
        value = float(x)

        if pd.isna(value):
            return default

        return value

    except Exception:
        return default


def stable_json(
    value,
) -> str:

    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )
    except Exception:
        return str(value)


def rank_signature(
    score: dict[str, Any],
) -> str:
    """
    Positive-score sector ranking signature.
    """

    rows = []

    for sector, value in (
        score or {}
    ).items():

        number = safe_float(
            value
        )

        if (
            pd.notna(number)
            and number > 0
        ):
            rows.append(
                (
                    str(sector),
                    float(number),
                )
            )

    rows.sort(
        key=lambda x: (
            -x[1],
            x[0],
        )
    )

    return "|".join(
        sector
        for sector, _
        in rows
    )


def score_vector_distance(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
) -> float:

    if previous is None:
        return np.nan

    names = (
        set(
            current or {}
        )
        |
        set(
            previous or {}
        )
    )

    total = 0.0

    for sector in names:

        a = safe_float(
            (current or {}).get(
                sector,
                0.0,
            ),
            default=0.0,
        )

        b = safe_float(
            (previous or {}).get(
                sector,
                0.0,
            ),
            default=0.0,
        )

        total += abs(
            a - b
        )

    return float(
        total
    )


def cap_signature(
    cap_applied,
) -> str:

    if not isinstance(
        cap_applied,
        list,
    ):
        return ""

    normalized = []

    for row in cap_applied:

        if not isinstance(
            row,
            dict,
        ):
            continue

        normalized.append(
            (
                str(
                    row.get(
                        "sector",
                        "",
                    )
                ),
                safe_float(
                    row.get(
                        "cap"
                    ),
                    default=np.nan,
                ),
                str(
                    row.get(
                        "reason",
                        "REGIME_CAP",
                    )
                ),
            )
        )

    normalized.sort()

    return "|".join(
        f"{sector}:{cap}:{reason}"
        for sector, cap, reason
        in normalized
    )


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

    if not PANEL_PATH.exists():
        raise FileNotFoundError(
            PANEL_PATH
        )

    if not EXECUTED_TURNOVER_PATH.exists():
        raise FileNotFoundError(
            EXECUTED_TURNOVER_PATH
        )

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    executed = pd.read_csv(
        EXECUTED_TURNOVER_PATH
    )

    executed[
        "signal_date"
    ] = pd.to_datetime(
        executed[
            "signal_date"
        ],
        errors="coerce",
    )

    executed[
        "execution_date"
    ] = pd.to_datetime(
        executed[
            "execution_date"
        ],
        errors="coerce",
    )

    executed = (
        executed[
            executed[
                "scenario"
            ]
            == SCENARIO
        ]
        .copy()
        .sort_values(
            "execution_date"
        )
    )

    # ========================================================
    # Execution rows
    # ========================================================

    mask = (
        panel[
            "execution_date"
        ].notna()
        &
        pd.to_numeric(
            panel[
                "SPY"
            ],
            errors="coerce",
        ).notna()
    )

    indices = (
        panel.index[
            mask
        ].tolist()
    )

    print()
    print(
        "=" * 110
    )

    print(
        "FILTER18 ROTATION RULE ATTRIBUTION"
    )

    print(
        "=" * 110
    )

    print()

    print(
        f"Execution rows : "
        f"{len(indices):,}"
    )

    print(
        "Source         : current branch / "
        "actual Filter18 build_tactical_allocation call"
    )

    # ========================================================
    # Sequential engine state
    # ========================================================

    previous_exposure = 50.0

    flow_memory: dict[
        str,
        Any,
    ] = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    rows = []

    previous_score = None

    previous_rank_signature = None
    previous_macro_profile = None
    previous_participation_mode = None
    previous_cap_signature = None
    previous_residual_action = None

    # ========================================================
    # Loop
    # ========================================================

    for count, idx in enumerate(
        indices,
        start=1,
    ):

        market_data = (
            rb.build_market_data(
                panel=panel,
                row_index=idx,
                previous_exposure=(
                    previous_exposure
                ),
            )
        )

        flow_memory = (
            rb.prepare_filter13_execution_state(
                market_data=market_data,
                panel=panel,
                row_index=idx,
                previous_flow_memory=(
                    flow_memory
                ),
            )
        )

        captured: dict[
            str,
            Any,
        ] = {}

        original_builder = (
            sf.build_tactical_allocation
        )

        def capture_builder(
            *args,
            **kwargs,
        ):

            # -----------------------------------------------
            # Capture exact inputs supplied by Filter18
            # -----------------------------------------------

            score = (
                kwargs.get(
                    "score"
                )
                or (
                    args[0]
                    if len(args) > 0
                    else {}
                )
                or {}
            )

            ow_sorted = (
                kwargs.get(
                    "ow_sorted"
                )
                or (
                    args[1]
                    if len(args) > 1
                    else []
                )
                or []
            )

            divergence_flags = (
                kwargs.get(
                    "divergence_flags"
                )
                or (
                    args[2]
                    if len(args) > 2
                    else {}
                )
                or {}
            )

            total_exposure = (
                kwargs.get(
                    "total_exposure"
                )
                if "total_exposure"
                in kwargs
                else (
                    args[3]
                    if len(args) > 3
                    else np.nan
                )
            )

            deleveraging_required = (
                kwargs.get(
                    "deleveraging_required",
                    False,
                )
            )

            macro_profile = str(
                kwargs.get(
                    "macro_profile",
                    "BALANCED",
                )
                or "BALANCED"
            ).upper()

            market_quality_context = (
                kwargs.get(
                    "market_quality_context",
                    {}
                )
                or {}
            )

            sector_classification = (
                kwargs.get(
                    "sector_classification",
                    {}
                )
                or {}
            )

            # -----------------------------------------------
            # Call exact Production allocator
            # -----------------------------------------------

            result = original_builder(
                *args,
                **kwargs,
            )

            captured[
                "score"
            ] = dict(
                score
            )

            captured[
                "ow_sorted"
            ] = list(
                ow_sorted
            )

            captured[
                "divergence_flags"
            ] = dict(
                divergence_flags
            )

            captured[
                "sector_classification"
            ] = dict(
                sector_classification
            )

            captured[
                "total_exposure"
            ] = safe_float(
                total_exposure
            )

            captured[
                "deleveraging_required"
            ] = bool(
                deleveraging_required
            )

            captured[
                "macro_profile_input"
            ] = macro_profile

            captured[
                "market_quality_context"
            ] = dict(
                market_quality_context
            )

            captured[
                "allocation_result"
            ] = result

            return result

        sf.build_tactical_allocation = (
            capture_builder
        )

        try:

            rb.disable_live_side_effects(
                previous_exposure
            )

            rb.neutralize_all_side_effects(
                previous_exposure
            )

            with contextlib.redirect_stdout(
                io.StringIO()
            ):

                sf.narrative_engine_filter(
                    market_data
                )

                # Historical VIX_Z None protection.
                cross = (
                    market_data.get(
                        "CROSS_ASSET_TAPE",
                        {},
                    )
                    or {}
                )

                if not isinstance(
                    cross,
                    dict,
                ):
                    cross = {}

                vix_z = safe_float(
                    cross.get(
                        "VIX_Z"
                    ),
                    default=0.0,
                )

                cross[
                    "VIX_Z"
                ] = vix_z

                market_data[
                    "CROSS_ASSET_TAPE"
                ] = cross

                sf.volatility_controlled_exposure_filter(
                    market_data
                )

                sf.sector_allocation_filter(
                    market_data
                )

        finally:

            sf.build_tactical_allocation = (
                original_builder
            )

        # ====================================================
        # Captured allocator metadata
        # ====================================================

        if not captured:

            raise RuntimeError(
                "build_tactical_allocation was not captured."
            )

        score = (
            captured.get(
                "score",
                {}
            )
            or {}
        )

        allocation_result = (
            captured.get(
                "allocation_result",
                {}
            )
            or {}
        )

        market_quality_context = (
            captured.get(
                "market_quality_context",
                {}
            )
            or {}
        )

        current_rank_signature = (
            rank_signature(
                score
            )
        )

        current_macro_profile = str(
            allocation_result.get(
                "macro_profile",
                captured.get(
                    "macro_profile_input",
                    "BALANCED",
                ),
            )
            or "BALANCED"
        ).upper()

        current_participation_mode = str(
            allocation_result.get(
                "participation_mode",
                "BALANCED",
            )
            or "BALANCED"
        ).upper()

        current_cap_signature = (
            cap_signature(
                allocation_result.get(
                    "cap_applied",
                    [],
                )
            )
        )

        current_residual_action = str(
            allocation_result.get(
                "residual_reallocation_action",
                "UNKNOWN",
            )
            or "UNKNOWN"
        )

        # ====================================================
        # Daily state transitions
        # ====================================================

        score_distance = (
            score_vector_distance(
                score,
                previous_score,
            )
        )

        rank_changed = (
            previous_rank_signature
            is not None
            and current_rank_signature
            != previous_rank_signature
        )

        macro_profile_changed = (
            previous_macro_profile
            is not None
            and current_macro_profile
            != previous_macro_profile
        )

        participation_mode_changed = (
            previous_participation_mode
            is not None
            and current_participation_mode
            != previous_participation_mode
        )

        cap_signature_changed = (
            previous_cap_signature
            is not None
            and current_cap_signature
            != previous_cap_signature
        )

        residual_action_changed = (
            previous_residual_action
            is not None
            and current_residual_action
            != previous_residual_action
        )

        cap_count = len(
            allocation_result.get(
                "cap_applied",
                []
            )
            or []
        )

        weights = (
            allocation_result.get(
                "weights",
                {}
            )
            or {}
        )

        positive_sector_count = sum(
            1
            for value
            in score.values()
            if (
                pd.notna(
                    safe_float(
                        value
                    )
                )
                and safe_float(
                    value
                ) > 0
            )
        )

        row = {
            "signal_date":
                panel.iloc[
                    idx
                ][
                    "signal_date"
                ],

            "execution_date":
                panel.iloc[
                    idx
                ][
                    "execution_date"
                ],

            "risk_budget_13":
                market_data.get(
                    "RISK_BUDGET"
                ),

            "exposure_15":
                market_data.get(
                    "RECOMMENDED_EXPOSURE"
                ),

            "total_exposure_input_18":
                captured.get(
                    "total_exposure"
                ),

            "macro_profile":
                current_macro_profile,

            "participation_mode":
                current_participation_mode,

            "participation_quality":
                allocation_result.get(
                    "participation_quality",
                    "",
                ),

            "participation_signal":
                market_quality_context.get(
                    "participation_signal",
                    "",
                ),

            "leadership_state":
                market_quality_context.get(
                    "leadership_state",
                    "",
                ),

            "positioning_state":
                market_quality_context.get(
                    "positioning_state",
                    "",
                ),

            "vol_structure":
                market_quality_context.get(
                    "vol_structure",
                    "",
                ),

            "residual_action":
                current_residual_action,

            "cap_count":
                cap_count,

            "cap_signature":
                current_cap_signature,

            "rank_signature":
                current_rank_signature,

            "positive_sector_count":
                positive_sector_count,

            "score_vector_distance":
                score_distance,

            "rank_changed":
                rank_changed,

            "macro_profile_changed":
                macro_profile_changed,

            "participation_mode_changed":
                participation_mode_changed,

            "cap_signature_changed":
                cap_signature_changed,

            "residual_action_changed":
                residual_action_changed,

            "deleveraging_required":
                captured.get(
                    "deleveraging_required",
                    False,
                ),

            "target_allocated_equity":
                allocation_result.get(
                    "allocated_equity",
                    np.nan,
                ),

            "target_cash_weight":
                allocation_result.get(
                    "cash_weight",
                    np.nan,
                ),

            "score_json":
                stable_json(
                    score
                ),

            "cap_json":
                stable_json(
                    allocation_result.get(
                        "cap_applied",
                        [],
                    )
                ),
        }

        rows.append(
            row
        )

        # ====================================================
        # Update state
        # ====================================================

        previous_score = dict(
            score
        )

        previous_rank_signature = (
            current_rank_signature
        )

        previous_macro_profile = (
            current_macro_profile
        )

        previous_participation_mode = (
            current_participation_mode
        )

        previous_cap_signature = (
            current_cap_signature
        )

        previous_residual_action = (
            current_residual_action
        )

        exposure = market_data.get(
            "RECOMMENDED_EXPOSURE"
        )

        if (
            exposure is not None
            and pd.notna(
                exposure
            )
        ):

            previous_exposure = float(
                exposure
            )

        if count % 500 == 0:

            print(
                f"[ATTRIBUTION] "
                f"{count:,}/{len(indices):,}"
            )

    # ========================================================
    # Build frame
    # ========================================================

    df = pd.DataFrame(
        rows
    )

    for col in [
        "signal_date",
        "execution_date",
    ]:

        df[
            col
        ] = pd.to_datetime(
            df[
                col
            ],
            errors="coerce",
        )

    # ========================================================
    # Merge Production-equivalent executed turnover
    # ========================================================

    turnover_cols = [
        "signal_date",
        "execution_date",
        "executed_turnover",
        "target_turnover",
        "hold_count",
        "small_adjust_count",
        "rebalance_count",
    ]

    missing_turnover = [
        col
        for col in turnover_cols
        if col not in executed.columns
    ]

    if missing_turnover:

        raise ValueError(
            "Executed-turnover detail missing columns:\n"
            f"{missing_turnover}"
        )

    df = df.merge(
        executed[
            turnover_cols
        ],
        on=[
            "signal_date",
            "execution_date",
        ],
        how="inner",
    )

    if df.empty:

        raise RuntimeError(
            "No overlap with executed turnover replay."
        )

    # ========================================================
    # Event attribution
    # ========================================================

    events = {
        "RANK_CHANGED":
            "rank_changed",

        "MACRO_PROFILE_CHANGED":
            "macro_profile_changed",

        "PARTICIPATION_MODE_CHANGED":
            "participation_mode_changed",

        "CAP_SIGNATURE_CHANGED":
            "cap_signature_changed",

        "RESIDUAL_ACTION_CHANGED":
            "residual_action_changed",

        "DELEVERAGING_REQUIRED":
            "deleveraging_required",
    }

    total_turnover = (
        df[
            "executed_turnover"
        ].sum()
    )

    event_rows = []

    for event_name, col in (
        events.items()
    ):

        flag = (
            df[
                col
            ]
            .fillna(
                False
            )
            .astype(
                bool
            )
        )

        event_turnover = (
            df.loc[
                flag,
                "executed_turnover",
            ].sum()
        )

        non_event_turnover = (
            df.loc[
                ~flag,
                "executed_turnover",
            ].sum()
        )

        event_rows.append(
            {
                "event":
                    event_name,

                "event_days":
                    int(
                        flag.sum()
                    ),

                "event_day_rate":
                    float(
                        flag.mean()
                    ),

                "avg_turnover_event":
                    df.loc[
                        flag,
                        "executed_turnover",
                    ].mean(),

                "avg_turnover_no_event":
                    df.loc[
                        ~flag,
                        "executed_turnover",
                    ].mean(),

                "turnover_ratio_event_vs_no_event":
                    (
                        df.loc[
                            flag,
                            "executed_turnover",
                        ].mean()
                        /
                        df.loc[
                            ~flag,
                            "executed_turnover",
                        ].mean()
                        if (
                            (~flag).sum() > 0
                            and df.loc[
                                ~flag,
                                "executed_turnover",
                            ].mean() > 0
                        )
                        else np.nan
                    ),

                "turnover_on_event_days":
                    event_turnover,

                "share_of_total_turnover_on_event_days":
                    (
                        event_turnover
                        / total_turnover
                        if total_turnover > 0
                        else np.nan
                    ),
            }
        )

    event_summary = (
        pd.DataFrame(
            event_rows
        )
        .sort_values(
            [
                "turnover_ratio_event_vs_no_event",
                "share_of_total_turnover_on_event_days",
            ],
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # Continuous correlations
    # ========================================================

    corr_score_distance = safe_corr(
        df[
            "score_vector_distance"
        ],
        df[
            "executed_turnover"
        ],
    )

    corr_cap_count = safe_corr(
        df[
            "cap_count"
        ],
        df[
            "executed_turnover"
        ],
    )

    corr_positive_count = safe_corr(
        df[
            "positive_sector_count"
        ],
        df[
            "executed_turnover"
        ],
    )

    # ========================================================
    # State summaries
    # ========================================================

    macro_summary = (
        df.groupby(
            "macro_profile",
            dropna=False,
        )
        .agg(
            days=(
                "executed_turnover",
                "size",
            ),

            avg_turnover=(
                "executed_turnover",
                "mean",
            ),

            total_turnover=(
                "executed_turnover",
                "sum",
            ),

            avg_rebalance_count=(
                "rebalance_count",
                "mean",
            ),

            avg_small_adjust_count=(
                "small_adjust_count",
                "mean",
            ),
        )
        .reset_index()
    )

    macro_summary[
        "turnover_share"
    ] = (
        macro_summary[
            "total_turnover"
        ]
        / total_turnover
    )

    participation_summary = (
        df.groupby(
            "participation_mode",
            dropna=False,
        )
        .agg(
            days=(
                "executed_turnover",
                "size",
            ),

            avg_turnover=(
                "executed_turnover",
                "mean",
            ),

            total_turnover=(
                "executed_turnover",
                "sum",
            ),

            avg_rebalance_count=(
                "rebalance_count",
                "mean",
            ),
        )
        .reset_index()
    )

    participation_summary[
        "turnover_share"
    ] = (
        participation_summary[
            "total_turnover"
        ]
        / total_turnover
    )

    # ========================================================
    # Top days
    # ========================================================

    top_days = (
        df[
            [
                "signal_date",
                "execution_date",
                "executed_turnover",
                "target_turnover",

                "score_vector_distance",
                "rank_changed",

                "macro_profile",
                "macro_profile_changed",

                "participation_mode",
                "participation_mode_changed",

                "cap_count",
                "cap_signature_changed",

                "residual_action",
                "residual_action_changed",

                "deleveraging_required",

                "rebalance_count",
                "small_adjust_count",
                "hold_count",
            ]
        ]
        .sort_values(
            "executed_turnover",
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
    # Main summary
    # ========================================================

    summary = pd.DataFrame(
        [
            {
                "rows":
                    len(df),

                "annualized_executed_turnover":
                    df[
                        "executed_turnover"
                    ].mean()
                    * 252.0,

                "corr_score_distance_turnover":
                    corr_score_distance,

                "corr_cap_count_turnover":
                    corr_cap_count,

                "corr_positive_sector_count_turnover":
                    corr_positive_count,

                "rank_change_rate":
                    df[
                        "rank_changed"
                    ].mean(),

                "macro_profile_change_rate":
                    df[
                        "macro_profile_changed"
                    ].mean(),

                "participation_mode_change_rate":
                    df[
                        "participation_mode_changed"
                    ].mean(),

                "cap_signature_change_rate":
                    df[
                        "cap_signature_changed"
                    ].mean(),

                "residual_action_change_rate":
                    df[
                        "residual_action_changed"
                    ].mean(),
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

    event_summary.to_csv(
        EVENT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # Extra state tables
    macro_path = (
        RESULT_DIR
        / "filter18_rotation_rule_macro_summary.csv"
    )

    participation_path = (
        RESULT_DIR
        / "filter18_rotation_rule_participation_summary.csv"
    )

    top_path = (
        RESULT_DIR
        / "filter18_rotation_rule_top_days.csv"
    )

    macro_summary.to_csv(
        macro_path,
        index=False,
        encoding="utf-8-sig",
    )

    participation_summary.to_csv(
        participation_path,
        index=False,
        encoding="utf-8-sig",
    )

    top_days.to_csv(
        top_path,
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
        "FILTER18 ROTATION RULE ATTRIBUTION"
    )

    lines.append(
        "=" * 125
    )

    lines.append("")

    lines.append(
        f"Rows                         : "
        f"{len(df):,}"
    )

    lines.append(
        f"Executed annualized turnover : "
        f"{df['executed_turnover'].mean() * 252:.2f}x"
    )

    lines.append("")

    lines.append(
        "CONTINUOUS DRIVERS"
    )

    lines.append(
        "------------------"
    )

    lines.append(
        f"Corr turnover vs score-vector change : "
        f"{corr_score_distance:.3f}"
    )

    lines.append(
        f"Corr turnover vs cap count           : "
        f"{corr_cap_count:.3f}"
    )

    lines.append(
        f"Corr turnover vs positive-sector cnt : "
        f"{corr_positive_count:.3f}"
    )

    lines.append("")

    lines.append(
        "STATE-CHANGE ATTRIBUTION"
    )

    lines.append(
        "------------------------"
    )

    lines.append(
        event_summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "MACRO PROFILE"
    )

    lines.append(
        "-------------"
    )

    lines.append(
        macro_summary.sort_values(
            "total_turnover",
            ascending=False,
        ).to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "PARTICIPATION MODE"
    )

    lines.append(
        "------------------"
    )

    lines.append(
        participation_summary.sort_values(
            "total_turnover",
            ascending=False,
        ).to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "Interpretation:"
    )

    lines.append(
        "- High score-distance correlation / rank-change turnover "
        "→ ranking/score instability."
    )

    lines.append(
        "- High macro-profile change turnover ratio "
        "→ regime switching."
    )

    lines.append(
        "- High participation-mode change turnover ratio "
        "→ participation policy switching."
    )

    lines.append(
        "- High cap-signature change turnover ratio "
        "→ cap switching."
    )

    lines.append(
        "- High residual-action change turnover ratio "
        "→ residual redistribution instability."
    )

    lines.append(
        "- This is provenance/event attribution, not yet a causal "
        "counterfactual. Production remains unchanged."
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

    for path in [
        DETAIL_PATH,
        SUMMARY_PATH,
        EVENT_PATH,
        macro_path,
        participation_path,
        top_path,
        TEXT_PATH,
    ]:
        print(
            path
        )


if __name__ == "__main__":
    main()