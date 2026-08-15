"""
FILTER15 CRISIS SEVERITY / REGIME TRANSITION AUDIT

목적
----
Filter15 Hard Deadman의 조기 Release 후보

    HY_FALLING + VIX < 30

가 일부 episode에서는 유효하지만 2008년 같은 structural crisis에서는
premature release를 발생시키는 이유를 진단한다.

이번 Audit은 새로운 release rule을 적용하지 않는다.

연구 질문
---------
1. 성공한 release와 실패한 release의 절대 HY OAS 수준은 다른가?
2. Release 당시 HY가 여전히 production crisis threshold(>= 6.0)에 있었는가?
3. Crisis peak 대비 HY가 얼마나 정상화된 뒤 release 되었는가?
4. HY < 6.0 복귀 시점은 candidate release보다 얼마나 늦는가?
5. HY absolute level, peak compression, VIX 중 무엇이 false stabilization과
   더 강하게 연결되는가?
6. 2008 episode는 다른 episode와 구조적으로 어떻게 다른가?

원칙
----
- Production 수정 금지
- Filter15 수정 금지
- 새로운 threshold 최적화 금지
- 미래 데이터를 release signal 생성에 사용하지 않음
- 본 파일은 descriptive / diagnostic audit
- 기존 validated counterfactual 결과만 분석
- Production 변경 승인용이 아님

입력
----
data/backtest/results/filter15_release_failure_analysis.csv

가능하면 추가 context:
data/backtest/results/filter15_deadman_episodes.csv

출력
----
data/backtest/results/filter15_crisis_severity_episode.csv
data/backtest/results/filter15_crisis_severity_summary.csv
data/backtest/results/filter15_crisis_severity_threshold_buckets.csv
data/backtest/results/filter15_crisis_severity_transition_audit.txt
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

FAILURE_PATH = (
    RESULT_DIR
    / "filter15_release_failure_analysis.csv"
)

DEADMAN_EPISODES_PATH = (
    RESULT_DIR
    / "filter15_deadman_episodes.csv"
)

EPISODE_OUT = (
    RESULT_DIR
    / "filter15_crisis_severity_episode.csv"
)

SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_crisis_severity_summary.csv"
)

BUCKET_OUT = (
    RESULT_DIR
    / "filter15_crisis_severity_threshold_buckets.csv"
)

AUDIT_OUT = (
    RESULT_DIR
    / "filter15_crisis_severity_transition_audit.txt"
)


# ============================================================
# Constants
# ============================================================

# Production Filter15 Hard Deadman threshold.
# This is NOT a newly optimized research threshold.
PRODUCTION_HY_CRISIS_THRESHOLD = 6.0


# Diagnostic buckets only.
# These are descriptive buckets, NOT candidate trading rules.
HY_BUCKETS = [
    -np.inf,
    4.0,
    5.0,
    6.0,
    7.0,
    8.0,
    np.inf,
]

HY_BUCKET_LABELS = [
    "<4",
    "4-5",
    "5-6",
    "6-7",
    "7-8",
    ">=8",
]


# ============================================================
# Helpers
# ============================================================

def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def safe_mean(series: pd.Series) -> float:
    x = numeric(series).dropna()

    if x.empty:
        return np.nan

    return float(x.mean())


def safe_median(series: pd.Series) -> float:
    x = numeric(series).dropna()

    if x.empty:
        return np.nan

    return float(x.median())


def pct_true(series: pd.Series) -> float:
    if len(series) == 0:
        return np.nan

    x = (
        series
        .fillna(False)
        .astype(bool)
    )

    return float(
        x.mean() * 100.0
    )


# ============================================================
# Load failure analysis
# ============================================================

if not FAILURE_PATH.exists():
    raise FileNotFoundError(
        f"\nRequired input not found:\n"
        f"{FAILURE_PATH}\n\n"
        "먼저 audit_filter15_release_failure_analysis.py "
        "를 실행해야 합니다."
    )


df = pd.read_csv(
    FAILURE_PATH
)


# ============================================================
# Required contract
# ============================================================

required = {
    "episode_id",
    "dominant_trigger",
    "release_date",
    "release_hy_oas",
    "release_vix",
    "rows_released_early",
    "full_incremental_return",
    "full_incremental_mdd",
    "diagnosis",
}

missing = sorted(
    required - set(df.columns)
)

if missing:
    raise ValueError(
        "\nMissing required columns in "
        "filter15_release_failure_analysis.csv:\n"
        + "\n".join(missing)
        + "\n\nAvailable columns:\n"
        + "\n".join(df.columns.astype(str))
    )


# ============================================================
# Types
# ============================================================

df["episode_id"] = numeric(
    df["episode_id"]
)

df["release_date"] = pd.to_datetime(
    df["release_date"],
    errors="coerce",
)

for col in (
    "release_hy_oas",
    "release_vix",
    "rows_released_early",
    "full_incremental_return",
    "full_incremental_mdd",
):
    df[col] = numeric(
        df[col]
    )


df = (
    df
    .dropna(
        subset=[
            "episode_id",
            "release_date",
        ]
    )
    .sort_values(
        [
            "episode_id",
            "release_date",
        ]
    )
    .reset_index(drop=True)
)


# ============================================================
# Optional Deadman episode context
# ============================================================

episode_context = None

if DEADMAN_EPISODES_PATH.exists():

    episode_context = pd.read_csv(
        DEADMAN_EPISODES_PATH
    )

    if "episode_id" in episode_context.columns:

        episode_context["episode_id"] = numeric(
            episode_context["episode_id"]
        )

        context_columns = [
            "episode_id",
        ]

        optional_columns = [
            "start_signal_date",
            "end_signal_date",
            "duration_rows",
            "max_hy_oas",
            "max_vix",
            "dominant_trigger",
            "next_signal_date",
            "next_risk_budget_13",
            "next_exposure_15",
            "release_status",
        ]

        for col in optional_columns:
            if col in episode_context.columns:
                context_columns.append(col)

        episode_context = (
            episode_context[
                context_columns
            ]
            .drop_duplicates(
                "episode_id",
                keep="last",
            )
        )

        # Avoid duplicate dominant_trigger.
        if (
            "dominant_trigger"
            in episode_context.columns
            and "dominant_trigger"
            in df.columns
        ):
            episode_context = (
                episode_context.rename(
                    columns={
                        "dominant_trigger":
                            "deadman_dominant_trigger"
                    }
                )
            )

        df = df.merge(
            episode_context,
            on="episode_id",
            how="left",
        )


# ============================================================
# Core severity diagnostics
# ============================================================

# Was release attempted while HY was STILL in the exact
# production Hard Deadman crisis zone?
df["release_inside_hy_crisis"] = (
    df["release_hy_oas"]
    >= PRODUCTION_HY_CRISIS_THRESHOLD
)


# Distance from production crisis boundary.
#
# Positive:
#   still ABOVE crisis threshold
#
# Negative:
#   already BELOW crisis threshold
df["hy_distance_from_crisis_threshold"] = (
    df["release_hy_oas"]
    - PRODUCTION_HY_CRISIS_THRESHOLD
)


# Descriptive HY bucket.
df["release_hy_bucket"] = pd.cut(
    df["release_hy_oas"],
    bins=HY_BUCKETS,
    labels=HY_BUCKET_LABELS,
    right=False,
)


# ============================================================
# Peak normalization diagnostics
# ============================================================

if "max_hy_oas" in df.columns:

    df["max_hy_oas"] = numeric(
        df["max_hy_oas"]
    )

    # Absolute compression from episode peak.
    #
    # Example:
    # peak = 10
    # release = 7
    # compression = 3
    df["hy_peak_compression_abs"] = (
        df["max_hy_oas"]
        - df["release_hy_oas"]
    )

    # Fraction of peak spread that has compressed.
    #
    # This is descriptive only.
    df["hy_peak_compression_pct"] = np.where(
        df["max_hy_oas"] > 0,
        (
            df["max_hy_oas"]
            - df["release_hy_oas"]
        )
        / df["max_hy_oas"],
        np.nan,
    )

else:

    df["max_hy_oas"] = np.nan
    df["hy_peak_compression_abs"] = np.nan
    df["hy_peak_compression_pct"] = np.nan


# ============================================================
# Outcome flags
# ============================================================

df["positive_incremental_return"] = (
    df["full_incremental_return"]
    > 0
)

df["negative_incremental_return"] = (
    df["full_incremental_return"]
    < 0
)


# Severe tail loss diagnostic.
#
# IMPORTANT:
# This is NOT a trading threshold.
# It is only used to identify materially bad historical
# counterfactual outcomes.
df["tail_mdd_gt_5pct"] = (
    df["full_incremental_mdd"]
    <= -0.05
)

df["tail_mdd_gt_10pct"] = (
    df["full_incremental_mdd"]
    <= -0.10
)


# ============================================================
# Diagnosis-level summary
# ============================================================

summary_records = []


for diagnosis, x in df.groupby(
    "diagnosis",
    dropna=False,
):

    summary_records.append(
        {
            "diagnosis":
                diagnosis,

            "episodes":
                len(x),

            "avg_release_hy":
                safe_mean(
                    x["release_hy_oas"]
                ),

            "median_release_hy":
                safe_median(
                    x["release_hy_oas"]
                ),

            "avg_release_vix":
                safe_mean(
                    x["release_vix"]
                ),

            "median_release_vix":
                safe_median(
                    x["release_vix"]
                ),

            "pct_release_inside_hy_crisis":
                pct_true(
                    x[
                        "release_inside_hy_crisis"
                    ]
                ),

            "avg_hy_distance_from_6":
                safe_mean(
                    x[
                        "hy_distance_from_crisis_threshold"
                    ]
                ),

            "avg_peak_hy":
                safe_mean(
                    x["max_hy_oas"]
                ),

            "avg_peak_compression_abs":
                safe_mean(
                    x[
                        "hy_peak_compression_abs"
                    ]
                ),

            "avg_peak_compression_pct":
                safe_mean(
                    x[
                        "hy_peak_compression_pct"
                    ]
                ),

            "avg_rows_released_early":
                safe_mean(
                    x[
                        "rows_released_early"
                    ]
                ),

            "avg_incremental_return":
                safe_mean(
                    x[
                        "full_incremental_return"
                    ]
                ),

            "avg_incremental_mdd":
                safe_mean(
                    x[
                        "full_incremental_mdd"
                    ]
                ),

            "worst_incremental_mdd":
                (
                    float(
                        x[
                            "full_incremental_mdd"
                        ].min()
                    )
                    if x[
                        "full_incremental_mdd"
                    ].notna().any()
                    else np.nan
                ),

            "tail_mdd_gt_5pct_count":
                int(
                    x[
                        "tail_mdd_gt_5pct"
                    ].sum()
                ),

            "tail_mdd_gt_10pct_count":
                int(
                    x[
                        "tail_mdd_gt_10pct"
                    ].sum()
                ),
        }
    )


summary = pd.DataFrame(
    summary_records
)


# ============================================================
# HY severity bucket summary
# ============================================================

bucket_records = []


for bucket in HY_BUCKET_LABELS:

    x = df[
        df["release_hy_bucket"].astype(str)
        == bucket
    ].copy()

    if x.empty:
        continue

    bucket_records.append(
        {
            "release_hy_bucket":
                bucket,

            "episodes":
                len(x),

            "positive_episodes":
                int(
                    x[
                        "positive_incremental_return"
                    ].sum()
                ),

            "negative_episodes":
                int(
                    x[
                        "negative_incremental_return"
                    ].sum()
                ),

            "successful_release":
                int(
                    (
                        x["diagnosis"]
                        == "SUCCESSFUL_RELEASE"
                    ).sum()
                ),

            "ambiguous_failure":
                int(
                    (
                        x["diagnosis"]
                        == "AMBIGUOUS_FAILURE"
                    ).sum()
                ),

            "timing_risk":
                int(
                    (
                        x["diagnosis"]
                        == "TIMING_RISK"
                    ).sum()
                ),

            "avg_release_hy":
                safe_mean(
                    x["release_hy_oas"]
                ),

            "avg_release_vix":
                safe_mean(
                    x["release_vix"]
                ),

            "avg_rows_released_early":
                safe_mean(
                    x[
                        "rows_released_early"
                    ]
                ),

            "avg_incremental_return":
                safe_mean(
                    x[
                        "full_incremental_return"
                    ]
                ),

            "avg_incremental_mdd":
                safe_mean(
                    x[
                        "full_incremental_mdd"
                    ]
                ),

            "worst_incremental_mdd":
                (
                    float(
                        x[
                            "full_incremental_mdd"
                        ].min()
                    )
                    if x[
                        "full_incremental_mdd"
                    ].notna().any()
                    else np.nan
                ),

            "tail_mdd_gt_5pct_count":
                int(
                    x[
                        "tail_mdd_gt_5pct"
                    ].sum()
                ),

            "tail_mdd_gt_10pct_count":
                int(
                    x[
                        "tail_mdd_gt_10pct"
                    ].sum()
                ),
        }
    )


bucket_summary = pd.DataFrame(
    bucket_records
)


# ============================================================
# Crisis-zone vs non-crisis-zone comparison
# ============================================================

zone_records = []


for inside_crisis, x in df.groupby(
    "release_inside_hy_crisis",
    dropna=False,
):

    zone_name = (
        "HY_GE_6_CRISIS_ZONE"
        if bool(inside_crisis)
        else "HY_LT_6_OUTSIDE_CRISIS"
    )

    zone_records.append(
        {
            "zone":
                zone_name,

            "episodes":
                len(x),

            "successful_release":
                int(
                    (
                        x["diagnosis"]
                        == "SUCCESSFUL_RELEASE"
                    ).sum()
                ),

            "ambiguous_failure":
                int(
                    (
                        x["diagnosis"]
                        == "AMBIGUOUS_FAILURE"
                    ).sum()
                ),

            "timing_risk":
                int(
                    (
                        x["diagnosis"]
                        == "TIMING_RISK"
                    ).sum()
                ),

            "positive_episodes":
                int(
                    x[
                        "positive_incremental_return"
                    ].sum()
                ),

            "negative_episodes":
                int(
                    x[
                        "negative_incremental_return"
                    ].sum()
                ),

            "avg_release_hy":
                safe_mean(
                    x["release_hy_oas"]
                ),

            "avg_release_vix":
                safe_mean(
                    x["release_vix"]
                ),

            "avg_incremental_return":
                safe_mean(
                    x[
                        "full_incremental_return"
                    ]
                ),

            "avg_incremental_mdd":
                safe_mean(
                    x[
                        "full_incremental_mdd"
                    ]
                ),

            "worst_incremental_mdd":
                (
                    float(
                        x[
                            "full_incremental_mdd"
                        ].min()
                    )
                    if x[
                        "full_incremental_mdd"
                    ].notna().any()
                    else np.nan
                ),
        }
    )


zone_summary = pd.DataFrame(
    zone_records
)


# ============================================================
# 2008 / Episode 1
# ============================================================

episode1 = df[
    df["episode_id"]
    == 1
].copy()


# ============================================================
# Worst cases
# ============================================================

worst = (
    df
    .sort_values(
        "full_incremental_mdd",
        ascending=True,
    )
    .head(15)
)


# ============================================================
# Save CSV
# ============================================================

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


df.to_csv(
    EPISODE_OUT,
    index=False,
)

summary.to_csv(
    SUMMARY_OUT,
    index=False,
)

bucket_summary.to_csv(
    BUCKET_OUT,
    index=False,
)


# ============================================================
# Audit text
# ============================================================

lines = []

lines.append(
    "=" * 78
)

lines.append(
    "FILTER15 CRISIS SEVERITY / REGIME TRANSITION AUDIT"
)

lines.append(
    "=" * 78
)

lines.append("")

lines.append(
    f"Release Episodes Analysed : {len(df)}"
)

lines.append(
    f"Production HY Crisis Level: "
    f"{PRODUCTION_HY_CRISIS_THRESHOLD:.2f}"
)

lines.append(
    "Production Modified       : NO"
)

lines.append(
    "New Release Rule Applied  : NO"
)

lines.append(
    "Threshold Optimization    : NO"
)

lines.append(
    "Purpose                   : DIAGNOSTIC ONLY"
)

lines.append("")


# ------------------------------------------------------------
# Diagnosis
# ------------------------------------------------------------

lines.append(
    "===== DIAGNOSIS SEVERITY SUMMARY ====="
)

lines.append(
    summary.to_string(
        index=False
    )
)

lines.append("")


# ------------------------------------------------------------
# Crisis zone
# ------------------------------------------------------------

lines.append(
    "===== PRODUCTION CRISIS-ZONE COMPARISON ====="
)

lines.append(
    zone_summary.to_string(
        index=False
    )
)

lines.append("")


# ------------------------------------------------------------
# Buckets
# ------------------------------------------------------------

lines.append(
    "===== RELEASE HY LEVEL BUCKETS ====="
)

lines.append(
    bucket_summary.to_string(
        index=False
    )
)

lines.append("")


# ------------------------------------------------------------
# Episode 1
# ------------------------------------------------------------

lines.append(
    "===== EPISODE 1 / 2008 ====="
)

if episode1.empty:

    lines.append(
        "Episode 1 not found."
    )

else:

    episode1_cols = [
        "episode_id",
        "release_date",
        "release_hy_oas",
        "release_vix",
        "release_inside_hy_crisis",
        "hy_distance_from_crisis_threshold",
        "max_hy_oas",
        "hy_peak_compression_abs",
        "hy_peak_compression_pct",
        "rows_released_early",
        "full_incremental_return",
        "full_incremental_mdd",
        "diagnosis",
    ]

    episode1_cols = [
        col
        for col in episode1_cols
        if col in episode1.columns
    ]

    lines.append(
        episode1[
            episode1_cols
        ].to_string(
            index=False
        )
    )


lines.append("")


# ------------------------------------------------------------
# Worst cases
# ------------------------------------------------------------

lines.append(
    "===== WORST RELEASE CASES ====="
)

worst_cols = [
    "episode_id",
    "dominant_trigger",
    "release_date",
    "release_hy_oas",
    "release_vix",
    "release_inside_hy_crisis",
    "max_hy_oas",
    "hy_peak_compression_abs",
    "hy_peak_compression_pct",
    "rows_released_early",
    "full_incremental_return",
    "full_incremental_mdd",
    "diagnosis",
]

worst_cols = [
    col
    for col in worst_cols
    if col in worst.columns
]

lines.append(
    worst[
        worst_cols
    ].to_string(
        index=False
    )
)

lines.append("")


# ------------------------------------------------------------
# Research interpretation
# ------------------------------------------------------------

lines.append(
    "=" * 78
)

lines.append(
    "다음 Gate 판단 기준"
)

lines.append(
    "=" * 78
)

lines.append("")

lines.append(
    "1. TIMING_RISK가 HY >= 6 crisis zone에 집중되는지 확인."
)

lines.append("")

lines.append(
    "2. 성공적인 Release도 HY >= 6에서 많이 발생한다면 "
    "'HY < 6' 단일 threshold를 바로 Release rule로 사용하면 안 됨."
)

lines.append("")

lines.append(
    "3. 성공/실패가 absolute HY level보다 peak 대비 compression에서 "
    "더 잘 분리된다면 relative normalization hypothesis를 다음에 검증."
)

lines.append("")

lines.append(
    "4. Absolute level과 peak compression 모두 분리가 약하면 "
    "credit 하나의 threshold 문제가 아니라 CRISIS -> STABILIZING -> "
    "RECOVERY_CONFIRMED 상태 전환 구조를 연구."
)

lines.append("")

lines.append(
    "5. 2008 하나 때문에 전체 threshold를 과도하게 보수화하지 말 것. "
    "Tail protection과 정상 recovery opportunity cost를 함께 평가해야 함."
)

lines.append("")

lines.append(
    "6. 이번 결과만으로 Production Filter15를 수정하지 않음."
)

lines.append("")

lines.append(
    "PRODUCTION DECISION: NO CHANGE"
)

lines.append(
    "NEXT: 결과를 보고 absolute severity / relative normalization / "
    "state transition 중 하나만 다음 counterfactual hypothesis로 선택."
)


audit_text = "\n".join(
    lines
)


AUDIT_OUT.write_text(
    audit_text,
    encoding="utf-8",
)


# ============================================================
# Console
# ============================================================

print()
print(audit_text)
print()

print(
    f"Saved: {EPISODE_OUT}"
)

print(
    f"Saved: {SUMMARY_OUT}"
)

print(
    f"Saved: {BUCKET_OUT}"
)

print(
    f"Saved: {AUDIT_OUT}"
)