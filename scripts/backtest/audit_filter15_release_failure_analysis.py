"""
FILTER15 RELEASE FAILURE ANALYSIS

목적
----
검증된 Filter15 Deadman counterfactual 후보:

    HY_FALLING + VIX < 30

의 실패 원인을 분해한다.

핵심 질문
---------
1. Release timing 자체가 너무 빨랐는가?
2. Release timing은 합리적이었지만
   0 -> Filter13 full risk budget 복원이 너무 공격적이었는가?
3. 성공 episode와 실패 episode의 차이는 무엇인가?

검증 원칙
---------
- Production 코드 수정 금지
- 미래 데이터 backfill 금지
- Signal t -> Return t+1
- Counterfactual 결과만 사용
- 새로운 Production rule을 만들지 않음
- 현재 단계는 진단 / hypothesis generation 전용

입력
----
data/backtest/results/
    filter15_deadman_release_gate_counterfactual_daily.csv

data/backtest/results/
    filter15_deadman_release_gate_counterfactual_episodes.csv

출력
----
data/backtest/results/
    filter15_release_failure_analysis.csv

data/backtest/results/
    filter15_release_failure_summary.csv

data/backtest/results/
    filter15_release_failure_analysis.txt
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

DAILY_PATH = (
    RESULT_DIR
    / "filter15_deadman_release_gate_counterfactual_daily.csv"
)

EPISODE_PATH = (
    RESULT_DIR
    / "filter15_deadman_release_gate_counterfactual_episodes.csv"
)

OUT_DETAIL = (
    RESULT_DIR
    / "filter15_release_failure_analysis.csv"
)

OUT_SUMMARY = (
    RESULT_DIR
    / "filter15_release_failure_summary.csv"
)

OUT_TXT = (
    RESULT_DIR
    / "filter15_release_failure_analysis.txt"
)


# ============================================================
# Configuration
# ============================================================

TARGET_CANDIDATE = "HY_FALLING_VIX_LT_30"

# Release 이후 얼마 동안의 path를 관찰할 것인가.
# 이것은 미래 데이터를 release 결정에 사용하는 것이 아니라
# 사후 audit / failure attribution 용도다.
FORWARD_WINDOWS = (5, 10, 20)

# sizing diagnostic
#
# FULL:
#     기존 counterfactual과 동일.
#     Filter13 budget 100% 복원.
#
# HALF:
#     Filter13 budget의 50%만 복원.
#
# QUARTER:
#     Filter13 budget의 25%만 복원.
#
# 중요:
# 이것들은 Production 후보가 아니라
# timing vs sizing 문제를 식별하기 위한 진단 도구다.
SIZING_LEVELS = {
    "FULL": 1.00,
    "HALF": 0.50,
    "QUARTER": 0.25,
}


# ============================================================
# Helpers
# ============================================================

def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def compound_return(
    returns: pd.Series,
) -> float:

    x = numeric(
        returns
    ).fillna(0.0)

    if len(x) == 0:
        return np.nan

    return float(
        (1.0 + x).prod() - 1.0
    )


def max_drawdown(
    returns: pd.Series,
) -> float:

    x = numeric(
        returns
    ).fillna(0.0)

    if len(x) == 0:
        return np.nan

    wealth = (
        1.0 + x
    ).cumprod()

    peak = wealth.cummax()

    dd = (
        wealth
        / peak
        - 1.0
    )

    return float(
        dd.min()
    )


def safe_float(value):
    try:
        if pd.isna(value):
            return np.nan

        return float(value)

    except Exception:
        return np.nan


# ============================================================
# Load
# ============================================================

if not DAILY_PATH.exists():
    raise FileNotFoundError(
        f"Missing:\n{DAILY_PATH}\n\n"
        "Run "
        "audit_filter15_deadman_release_gate_counterfactual.py "
        "first."
    )

if not EPISODE_PATH.exists():
    raise FileNotFoundError(
        f"Missing:\n{EPISODE_PATH}"
    )


daily = pd.read_csv(
    DAILY_PATH
)

episodes = pd.read_csv(
    EPISODE_PATH
)


# ============================================================
# Contract
# ============================================================

required_daily = {
    "episode_id",
    "candidate",
    "signal_date",
    "HY_OAS",
    "VIX",
    "SPY",
    "hy_falling",
    "baseline_exposure_15",
    "counterfactual_exposure",
    "counterfactual_release_date",
    "spy_return",
}

missing_daily = sorted(
    required_daily
    - set(daily.columns)
)

if missing_daily:
    raise ValueError(
        "Missing daily columns:\n"
        + "\n".join(missing_daily)
    )


required_episode = {
    "episode_id",
    "candidate",
    "dominant_trigger",
    "start_signal_date",
    "production_end_signal_date",
    "counterfactual_release_date",
    "duration_rows",
    "rows_released_early",
    "incremental_return",
    "incremental_mdd",
}

missing_episode = sorted(
    required_episode
    - set(episodes.columns)
)

if missing_episode:
    raise ValueError(
        "Missing episode columns:\n"
        + "\n".join(missing_episode)
    )


# ============================================================
# Types
# ============================================================

for col in (
    "signal_date",
    "counterfactual_release_date",
):
    daily[col] = pd.to_datetime(
        daily[col],
        errors="coerce",
    )


for col in (
    "start_signal_date",
    "production_end_signal_date",
    "counterfactual_release_date",
):
    episodes[col] = pd.to_datetime(
        episodes[col],
        errors="coerce",
    )


for col in (
    "HY_OAS",
    "VIX",
    "SPY",
    "baseline_exposure_15",
    "counterfactual_exposure",
    "spy_return",
):
    daily[col] = numeric(
        daily[col]
    )


for col in (
    "duration_rows",
    "rows_released_early",
    "incremental_return",
    "incremental_mdd",
):
    episodes[col] = numeric(
        episodes[col]
    )


daily = (
    daily
    .sort_values(
        [
            "episode_id",
            "candidate",
            "signal_date",
        ]
    )
    .reset_index(drop=True)
)


# ============================================================
# Target candidate only
# ============================================================

d = daily[
    daily["candidate"]
    == TARGET_CANDIDATE
].copy()

e = episodes[
    episodes["candidate"]
    == TARGET_CANDIDATE
].copy()


if d.empty:
    raise ValueError(
        f"No daily rows for {TARGET_CANDIDATE}"
    )

if e.empty:
    raise ValueError(
        f"No episode rows for {TARGET_CANDIDATE}"
    )


# Only episodes where early release actually occurred.
released = e[
    e[
        "counterfactual_release_date"
    ].notna()
].copy()


# ============================================================
# Episode Analysis
# ============================================================

records = []


for _, ep in released.iterrows():

    episode_id = ep["episode_id"]

    release_date = ep[
        "counterfactual_release_date"
    ]

    block = d[
        d["episode_id"]
        == episode_id
    ].copy()

    block = (
        block
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    if block.empty:
        continue

    release_matches = block.index[
        block["signal_date"]
        == release_date
    ].tolist()

    if not release_matches:
        continue

    release_pos = int(
        release_matches[0]
    )

    release_row = block.iloc[
        release_pos
    ]

    # --------------------------------------------------------
    # Information known AT release
    # --------------------------------------------------------

    release_hy = safe_float(
        release_row["HY_OAS"]
    )

    release_vix = safe_float(
        release_row["VIX"]
    )

    release_spy = safe_float(
        release_row["SPY"]
    )

    release_baseline_exposure = safe_float(
        release_row[
            "baseline_exposure_15"
        ]
    )

    release_full_exposure = safe_float(
        release_row[
            "counterfactual_exposure"
        ]
    )

    # --------------------------------------------------------
    # Credit persistence diagnostics
    #
    # These use future rows ONLY for ex-post evaluation.
    # They are NOT used to determine the release date.
    # --------------------------------------------------------

    post = block.iloc[
        release_pos:
    ].copy()

    post["hy_change_from_release"] = (
        post["HY_OAS"]
        - release_hy
    )

    post["vix_change_from_release"] = (
        post["VIX"]
        - release_vix
    )

    post["spy_return_from_release"] = (
        post["SPY"]
        / release_spy
        - 1.0
    )

    # Did credit immediately re-widen?
    hy_rewiden_5 = np.nan
    hy_rewiden_10 = np.nan
    hy_rewiden_20 = np.nan

    vix_respike_5 = np.nan
    vix_respike_10 = np.nan
    vix_respike_20 = np.nan

    spy_forward_5 = np.nan
    spy_forward_10 = np.nan
    spy_forward_20 = np.nan

    spy_min_5 = np.nan
    spy_min_10 = np.nan
    spy_min_20 = np.nan

    window_results = {}

    for window in FORWARD_WINDOWS:

        future = post.iloc[
            : window + 1
        ].copy()

        if future.empty:
            continue

        # Credit:
        # positive means spread re-widened vs release.
        max_hy_rewiden = (
            future[
                "hy_change_from_release"
            ].max()
        )

        # Vol:
        # positive means VIX respiked.
        max_vix_respike = (
            future[
                "vix_change_from_release"
            ].max()
        )

        # Price path after release.
        final_spy_return = (
            future[
                "spy_return_from_release"
            ].iloc[-1]
        )

        min_spy_return = (
            future[
                "spy_return_from_release"
            ].min()
        )

        window_results[
            window
        ] = {
            "max_hy_rewiden":
                max_hy_rewiden,

            "max_vix_respike":
                max_vix_respike,

            "final_spy_return":
                final_spy_return,

            "min_spy_return":
                min_spy_return,
        }

    if 5 in window_results:
        hy_rewiden_5 = (
            window_results[5][
                "max_hy_rewiden"
            ]
        )
        vix_respike_5 = (
            window_results[5][
                "max_vix_respike"
            ]
        )
        spy_forward_5 = (
            window_results[5][
                "final_spy_return"
            ]
        )
        spy_min_5 = (
            window_results[5][
                "min_spy_return"
            ]
        )

    if 10 in window_results:
        hy_rewiden_10 = (
            window_results[10][
                "max_hy_rewiden"
            ]
        )
        vix_respike_10 = (
            window_results[10][
                "max_vix_respike"
            ]
        )
        spy_forward_10 = (
            window_results[10][
                "final_spy_return"
            ]
        )
        spy_min_10 = (
            window_results[10][
                "min_spy_return"
            ]
        )

    if 20 in window_results:
        hy_rewiden_20 = (
            window_results[20][
                "max_hy_rewiden"
            ]
        )
        vix_respike_20 = (
            window_results[20][
                "max_vix_respike"
            ]
        )
        spy_forward_20 = (
            window_results[20][
                "final_spy_return"
            ]
        )
        spy_min_20 = (
            window_results[20][
                "min_spy_return"
            ]
        )

    # --------------------------------------------------------
    # TIMING DIAGNOSTIC
    #
    # Definition for diagnosis only:
    #
    # If SPY falls materially AFTER release,
    # the release timing may have been premature.
    #
    # Threshold is NOT a proposed Production rule.
    # --------------------------------------------------------

    timing_warning = bool(
        pd.notna(spy_min_10)
        and spy_min_10 <= -0.05
    )

    severe_timing_warning = bool(
        pd.notna(spy_min_20)
        and spy_min_20 <= -0.10
    )

    # --------------------------------------------------------
    # SIZING DIAGNOSTIC
    #
    # Hold release DATE constant.
    #
    # Only change amount of Filter13 budget restored.
    #
    # This isolates sizing from timing.
    # --------------------------------------------------------

    sizing_results = {}

    for sizing_name, fraction in (
        SIZING_LEVELS.items()
    ):

        cf_exposure = (
            block[
                "baseline_exposure_15"
            ].copy()
        )

        release_mask = (
            block.index
            >= release_pos
        )

        # Original FULL counterfactual exposure is the
        # restored Filter13 budget generated in the prior audit.
        full_restored = (
            block.loc[
                release_mask,
                "counterfactual_exposure",
            ]
        )

        baseline = (
            block.loc[
                release_mask,
                "baseline_exposure_15",
            ]
        )

        # Fraction of the incremental restored exposure.
        #
        # HALF does NOT mean fixed 50% exposure.
        # It means halfway between baseline deadman exposure
        # and the FULL restored exposure.
        restored = (
            baseline
            + (
                full_restored
                - baseline
            )
            * fraction
        )

        cf_exposure.loc[
            release_mask
        ] = restored

        # Signal t -> next return
        executed = (
            cf_exposure
            .shift(1)
            .fillna(0.0)
            / 100.0
        )

        baseline_executed = (
            block[
                "baseline_exposure_15"
            ]
            .shift(1)
            .fillna(0.0)
            / 100.0
        )

        strategy_return = (
            executed
            * block[
                "spy_return"
            ].fillna(0.0)
        )

        baseline_return = (
            baseline_executed
            * block[
                "spy_return"
            ].fillna(0.0)
        )

        total_return = compound_return(
            strategy_return
        )

        baseline_total_return = (
            compound_return(
                baseline_return
            )
        )

        incremental_return = (
            total_return
            - baseline_total_return
        )

        mdd = max_drawdown(
            strategy_return
        )

        baseline_mdd = max_drawdown(
            baseline_return
        )

        incremental_mdd = (
            mdd
            - baseline_mdd
        )

        sizing_results[
            sizing_name
        ] = {
            "return":
                total_return,

            "incremental_return":
                incremental_return,

            "mdd":
                mdd,

            "incremental_mdd":
                incremental_mdd,
        }

    # --------------------------------------------------------
    # Diagnostic classification
    # --------------------------------------------------------

    full_inc_ret = (
        sizing_results[
            "FULL"
        ][
            "incremental_return"
        ]
    )

    full_inc_mdd = (
        sizing_results[
            "FULL"
        ][
            "incremental_mdd"
        ]
    )

    half_inc_ret = (
        sizing_results[
            "HALF"
        ][
            "incremental_return"
        ]
    )

    half_inc_mdd = (
        sizing_results[
            "HALF"
        ][
            "incremental_mdd"
        ]
    )

    quarter_inc_ret = (
        sizing_results[
            "QUARTER"
        ][
            "incremental_return"
        ]
    )

    quarter_inc_mdd = (
        sizing_results[
            "QUARTER"
        ][
            "incremental_mdd"
        ]
    )

    # --------------------------------------------------------
    # Classification is intentionally descriptive.
    # It is NOT a Production decision rule.
    # --------------------------------------------------------

    if severe_timing_warning:
        diagnosis = "LIKELY_TIMING_FAILURE"

    elif (
        timing_warning
        and full_inc_ret < 0
    ):
        diagnosis = "TIMING_RISK"

    elif (
        full_inc_mdd < -0.05
        and half_inc_mdd > full_inc_mdd
    ):
        diagnosis = "LIKELY_SIZING_FAILURE"

    elif (
        full_inc_ret > 0
        and full_inc_mdd > -0.03
    ):
        diagnosis = "SUCCESSFUL_RELEASE"

    elif full_inc_ret > 0:
        diagnosis = "POSITIVE_BUT_RISKY"

    else:
        diagnosis = "AMBIGUOUS_FAILURE"

    records.append(
        {
            "episode_id":
                episode_id,

            "dominant_trigger":
                ep[
                    "dominant_trigger"
                ],

            "start_signal_date":
                ep[
                    "start_signal_date"
                ],

            "production_end_signal_date":
                ep[
                    "production_end_signal_date"
                ],

            "release_date":
                release_date,

            "duration_rows":
                ep[
                    "duration_rows"
                ],

            "rows_released_early":
                ep[
                    "rows_released_early"
                ],

            # Release state
            "release_hy_oas":
                release_hy,

            "release_vix":
                release_vix,

            "release_spy":
                release_spy,

            "release_baseline_exposure":
                release_baseline_exposure,

            "release_full_exposure":
                release_full_exposure,

            # Forward diagnostics
            "hy_max_rewiden_5":
                hy_rewiden_5,

            "hy_max_rewiden_10":
                hy_rewiden_10,

            "hy_max_rewiden_20":
                hy_rewiden_20,

            "vix_max_respike_5":
                vix_respike_5,

            "vix_max_respike_10":
                vix_respike_10,

            "vix_max_respike_20":
                vix_respike_20,

            "spy_return_5":
                spy_forward_5,

            "spy_return_10":
                spy_forward_10,

            "spy_return_20":
                spy_forward_20,

            "spy_min_return_5":
                spy_min_5,

            "spy_min_return_10":
                spy_min_10,

            "spy_min_return_20":
                spy_min_20,

            # Timing
            "timing_warning":
                timing_warning,

            "severe_timing_warning":
                severe_timing_warning,

            # FULL
            "full_incremental_return":
                full_inc_ret,

            "full_incremental_mdd":
                full_inc_mdd,

            # HALF
            "half_incremental_return":
                half_inc_ret,

            "half_incremental_mdd":
                half_inc_mdd,

            # QUARTER
            "quarter_incremental_return":
                quarter_inc_ret,

            "quarter_incremental_mdd":
                quarter_inc_mdd,

            # Diagnosis
            "diagnosis":
                diagnosis,
        }
    )


detail = pd.DataFrame(
    records
)


if detail.empty:
    raise ValueError(
        "No released episodes analyzed."
    )


# ============================================================
# Summary by diagnosis
# ============================================================

summary = (
    detail
    .groupby(
        "diagnosis",
        dropna=False,
    )
    .agg(
        episodes=(
            "episode_id",
            "count",
        ),

        avg_rows_released_early=(
            "rows_released_early",
            "mean",
        ),

        avg_release_hy=(
            "release_hy_oas",
            "mean",
        ),

        avg_release_vix=(
            "release_vix",
            "mean",
        ),

        avg_spy_min_10=(
            "spy_min_return_10",
            "mean",
        ),

        avg_spy_min_20=(
            "spy_min_return_20",
            "mean",
        ),

        avg_hy_rewiden_10=(
            "hy_max_rewiden_10",
            "mean",
        ),

        avg_vix_respike_10=(
            "vix_max_respike_10",
            "mean",
        ),

        avg_full_incremental_return=(
            "full_incremental_return",
            "mean",
        ),

        avg_full_incremental_mdd=(
            "full_incremental_mdd",
            "mean",
        ),

        avg_half_incremental_return=(
            "half_incremental_return",
            "mean",
        ),

        avg_half_incremental_mdd=(
            "half_incremental_mdd",
            "mean",
        ),

        avg_quarter_incremental_return=(
            "quarter_incremental_return",
            "mean",
        ),

        avg_quarter_incremental_mdd=(
            "quarter_incremental_mdd",
            "mean",
        ),
    )
    .reset_index()
)


# ============================================================
# Overall sizing comparison
# ============================================================

sizing_summary = []

for name in (
    "full",
    "half",
    "quarter",
):

    ret_col = (
        f"{name}_incremental_return"
    )

    mdd_col = (
        f"{name}_incremental_mdd"
    )

    sizing_summary.append(
        {
            "sizing":
                name.upper(),

            "episodes":
                len(detail),

            "positive_episodes":
                int(
                    (
                        detail[ret_col]
                        > 0
                    ).sum()
                ),

            "negative_episodes":
                int(
                    (
                        detail[ret_col]
                        < 0
                    ).sum()
                ),

            "total_incremental_return":
                detail[
                    ret_col
                ].sum(),

            "avg_incremental_return":
                detail[
                    ret_col
                ].mean(),

            "avg_incremental_mdd":
                detail[
                    mdd_col
                ].mean(),

            "worst_incremental_mdd":
                detail[
                    mdd_col
                ].min(),
        }
    )


sizing_summary_df = pd.DataFrame(
    sizing_summary
)


# ============================================================
# Worst cases
# ============================================================

worst = (
    detail
    .sort_values(
        "full_incremental_mdd",
        ascending=True,
    )
    .head(10)
)


# ============================================================
# Save
# ============================================================

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

detail.to_csv(
    OUT_DETAIL,
    index=False,
)

summary.to_csv(
    OUT_SUMMARY,
    index=False,
)


# ============================================================
# Report
# ============================================================

lines = []

lines.append(
    "=" * 78
)

lines.append(
    "FILTER15 RELEASE FAILURE ANALYSIS"
)

lines.append(
    "=" * 78
)

lines.append("")

lines.append(
    f"Candidate              : {TARGET_CANDIDATE}"
)

lines.append(
    f"Released Episodes      : {len(detail)}"
)

lines.append(
    "Production Modified    : NO"
)

lines.append(
    "Future Data in Signal  : NO"
)

lines.append(
    "Execution              : SIGNAL t -> RETURN t+1"
)

lines.append("")

lines.append(
    "===== DIAGNOSIS COUNTS ====="
)

lines.append(
    detail[
        "diagnosis"
    ]
    .value_counts()
    .to_string()
)

lines.append("")

lines.append(
    "===== DIAGNOSIS SUMMARY ====="
)

lines.append(
    summary.to_string(
        index=False
    )
)

lines.append("")

lines.append(
    "===== SIZING DIAGNOSTIC ====="
)

lines.append(
    sizing_summary_df.to_string(
        index=False
    )
)

lines.append("")

lines.append(
    "===== WORST FULL-RELEASE CASES ====="
)

worst_cols = [
    "episode_id",
    "dominant_trigger",
    "release_date",
    "release_hy_oas",
    "release_vix",
    "rows_released_early",
    "spy_min_return_10",
    "spy_min_return_20",
    "hy_max_rewiden_10",
    "vix_max_respike_10",
    "full_incremental_return",
    "full_incremental_mdd",
    "half_incremental_mdd",
    "quarter_incremental_mdd",
    "diagnosis",
]

lines.append(
    worst[
        worst_cols
    ].to_string(
        index=False
    )
)

lines.append("")

lines.append(
    "=" * 78
)

lines.append(
    "기관 관점 해석 기준"
)

lines.append(
    "=" * 78
)

lines.append("")

lines.append(
    "1. Timing Failure:"
)

lines.append(
    "   Release 직후 시장이 다시 크게 하락한다면 "
    "confirmation 자체가 부족했을 가능성."
)

lines.append("")

lines.append(
    "2. Sizing Failure:"
)

lines.append(
    "   Release 시점은 유효하지만 FULL 복원에서만 "
    "큰 drawdown이 발생하고 HALF/QUARTER에서 "
    "위험이 크게 감소한다면 단계적 재위험화가 "
    "필요할 가능성."
)

lines.append("")

lines.append(
    "3. Persistence:"
)

lines.append(
    "   Release 이후 HY 재확대 또는 VIX 재급등이 "
    "실패 episode에 집중된다면 다음 연구에서 "
    "2~3일 confirmation/persistence를 검증할 근거가 됨."
)

lines.append("")

lines.append(
    "4. Production Decision:"
)

lines.append(
    "   본 Audit은 원인 식별용이며 Production "
    "변경을 승인하지 않음."
)

lines.append("")

lines.append(
    "NEXT GATE:"
)

lines.append(
    "Timing / Sizing / Persistence 중 실제 병목을 "
    "식별한 뒤 하나의 hypothesis만 별도 "
    "counterfactual로 검증."
)


text = "\n".join(
    lines
)


OUT_TXT.write_text(
    text,
    encoding="utf-8",
)


# ============================================================
# Console
# ============================================================

print()
print(text)
print()

print(
    f"Saved: {OUT_DETAIL}"
)

print(
    f"Saved: {OUT_SUMMARY}"
)

print(
    f"Saved: {OUT_TXT}"
)