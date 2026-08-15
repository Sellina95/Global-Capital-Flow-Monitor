from __future__ import annotations

"""
FILTER15 COMMON-DATA RECOVERY STATE HYPOTHESIS AUDIT

목적
----
Deadman 이후 recovery 판단에 사용할 수 있는 후보 중에서
2008 Timing Risk episode와 이후 Successful Release에
공통으로 실제 관측 가능한 데이터만 사용해 진단한다.

핵심 원칙
---------
1. Production 수정 금지
2. 미래 데이터 사용 금지
3. 새로운 데이터 추가 금지
4. 2008 warm-up 결측을 release 차단 조건으로 사용 금지
5. threshold optimization 금지
6. 아직 실제 release rule을 만들지 않음
7. CRISIS -> STABILIZING -> RECOVERY_CONFIRMED
   state-machine 설계 전 마지막 common-data screening

Input
-----
filter15_recovery_separation_episode.csv

Output
------
filter15_common_data_recovery_state_episode.csv
filter15_common_data_recovery_state_summary.csv
filter15_common_data_recovery_state_audit.txt
"""

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
    / "filter15_recovery_separation_episode.csv"
)

EPISODE_OUT = (
    RESULT_DIR
    / "filter15_common_data_recovery_state_episode.csv"
)

SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_common_data_recovery_state_summary.csv"
)

AUDIT_OUT = (
    RESULT_DIR
    / "filter15_common_data_recovery_state_audit.txt"
)


# ============================================================
# Helpers
# ============================================================

def num(
    df: pd.DataFrame,
    col: str,
) -> pd.Series:

    if col not in df.columns:
        return pd.Series(
            np.nan,
            index=df.index,
            dtype=float,
        )

    return pd.to_numeric(
        df[col],
        errors="coerce",
    )


def txt(
    df: pd.DataFrame,
    col: str,
) -> pd.Series:

    if col not in df.columns:
        return pd.Series(
            "MISSING",
            index=df.index,
            dtype=str,
        )

    return (
        df[col]
        .fillna("MISSING")
        .astype(str)
        .str.strip()
        .str.upper()
    )


def safe_mean(
    x: pd.Series,
) -> float:

    x = pd.to_numeric(
        x,
        errors="coerce",
    ).dropna()

    if x.empty:
        return np.nan

    return float(x.mean())


def safe_median(
    x: pd.Series,
) -> float:

    x = pd.to_numeric(
        x,
        errors="coerce",
    ).dropna()

    if x.empty:
        return np.nan

    return float(x.median())


def pct_true(
    x: pd.Series,
) -> float:

    if len(x) == 0:
        return np.nan

    return float(
        x.fillna(False)
        .astype(bool)
        .mean()
        * 100.0
    )


# ============================================================
# Load
# ============================================================

def load_data() -> pd.DataFrame:

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "\nRequired input missing:\n"
            f"{INPUT_PATH}\n\n"
            "먼저 audit_filter15_recovery_separation.py를 "
            "실행하세요."
        )

    df = pd.read_csv(
        INPUT_PATH
    )

    required = [
        "episode_id",
        "release_date",
        "diagnosis",
    ]

    missing = [
        col
        for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df["release_date"] = pd.to_datetime(
        df["release_date"],
        errors="coerce",
    )

    df["diagnosis"] = (
        df["diagnosis"]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
    )

    return df


# ============================================================
# Identify genuinely common data
# ============================================================

def identify_common_fields(
    df: pd.DataFrame,
) -> tuple[list[str], pd.DataFrame]:

    """
    TIMING_RISK + SUCCESSFUL_RELEASE 양쪽에서
    모두 관측 가능한 numeric field만 common field로 인정.

    중요한 점:
    2008에서 missing인 데이터는 여기서 자동 제외된다.
    """

    candidate_fields = [
        "HY_OAS",
        "HY_OAS_PCT_CHANGE",

        "VIX_TODAY",
        "VIX_PCT_CHANGE",

        "POS_SLOPE",

        "DEALER_GAMMA_BIAS",
        "CTA_MOMENTUM_SCORE",

        "INSTITUTIONAL_FLOW_SCORE",
        "PREV_FLOW_SCORE",

        "LEADERSHIP_BREADTH_SCORE",

        "RISK_BUDGET",
    ]

    candidate_fields = [
        field
        for field in candidate_fields
        if field in df.columns
    ]

    timing = df[
        df["diagnosis"]
        == "TIMING_RISK"
    ]

    successful = df[
        df["diagnosis"]
        == "SUCCESSFUL_RELEASE"
    ]

    rows = []
    common = []

    for field in candidate_fields:

        timing_values = pd.to_numeric(
            timing[field],
            errors="coerce",
        )

        success_values = pd.to_numeric(
            successful[field],
            errors="coerce",
        )

        timing_available = (
            len(timing) > 0
            and timing_values.notna().all()
        )

        success_available = (
            len(successful) > 0
            and success_values.notna().all()
        )

        is_common = bool(
            timing_available
            and success_available
        )

        if is_common:
            common.append(field)

        rows.append(
            {
                "field": field,
                "timing_available":
                    timing_available,
                "successful_available":
                    success_available,
                "common_usable":
                    is_common,
            }
        )

    return (
        common,
        pd.DataFrame(rows),
    )


# ============================================================
# Build common-data evidence
# ============================================================

def build_features(
    df: pd.DataFrame,
) -> pd.DataFrame:

    out = df.copy()

    # --------------------------------------------------------
    # Raw common observations
    # --------------------------------------------------------

    out["common_hy"] = num(
        out,
        "HY_OAS",
    )

    out["common_hy_change"] = num(
        out,
        "HY_OAS_PCT_CHANGE",
    )

    out["common_vix"] = num(
        out,
        "VIX_TODAY",
    )

    out["common_vix_change"] = num(
        out,
        "VIX_PCT_CHANGE",
    )

    out["common_pos_slope"] = num(
        out,
        "POS_SLOPE",
    )

    out["common_gamma"] = num(
        out,
        "DEALER_GAMMA_BIAS",
    )

    out["common_cta"] = num(
        out,
        "CTA_MOMENTUM_SCORE",
    )

    out["common_flow"] = num(
        out,
        "INSTITUTIONAL_FLOW_SCORE",
    )

    out["common_prev_flow"] = num(
        out,
        "PREV_FLOW_SCORE",
    )

    out["common_leadership"] = num(
        out,
        "LEADERSHIP_BREADTH_SCORE",
    )

    out["common_risk_budget"] = num(
        out,
        "RISK_BUDGET",
    )

    # --------------------------------------------------------
    # Directional recovery evidence
    #
    # 여기 있는 threshold는 새로운 최적화 숫자가 아니다.
    #
    # 이미 Production / 기존 audit에서 의미가 정의되어 있는
    # 방향성 또는 기존 경계만 사용한다.
    # --------------------------------------------------------

    out["common_hy_improving"] = (
        out["common_hy_change"] < 0
    )

    out["common_vix_improving"] = (
        out["common_vix_change"] < 0
    )

    # 기존 Filter15 panic boundary
    out["common_vix_below_panic"] = (
        out["common_vix"] < 30
    )

    # 기존 positioning slope risk boundary
    out["common_pos_slope_stable"] = (
        out["common_pos_slope"].abs()
        <= 0.5
    )

    # 기존 gamma neutral threshold
    out["common_gamma_nonnegative"] = (
        out["common_gamma"]
        >= 0.5
    )

    # 기존 CTA 의미
    out["common_cta_positive"] = (
        out["common_cta"]
        > 0
    )

    out["common_flow_positive"] = (
        out["common_flow"]
        > 0
    )

    out["common_flow_persistent"] = (
        (out["common_flow"] > 0)
        &
        (out["common_prev_flow"] > 0)
    )

    # Leadership score 2 이상은
    # 기존 separation audit의 진단 기준 유지
    out["common_leadership_present"] = (
        out["common_leadership"]
        >= 2
    )

    # --------------------------------------------------------
    # Evidence groups
    #
    # 단순 총점만 보지 않고 서로 다른 경제 축으로 나눈다.
    # --------------------------------------------------------

    # Credit stabilization
    out["credit_recovery_evidence"] = (
        out["common_hy_improving"]
    )

    # Volatility stabilization
    out["vol_recovery_evidence"] = (
        out["common_vix_improving"]
        &
        out["common_vix_below_panic"]
    )

    # Position / market mechanics
    out["market_mechanics_evidence"] = (
        out["common_pos_slope_stable"]
        &
        out["common_gamma_nonnegative"]
    )

    # Institutional participation
    out["flow_recovery_evidence"] = (
        out["common_flow_positive"]
        &
        out["common_flow_persistent"]
    )

    # Participation / leadership
    out["leadership_recovery_evidence"] = (
        out["common_leadership_present"]
    )

    # CTA is kept separately because 2008 and many
    # successful recoveries may both be neutral.
    out["cta_recovery_evidence"] = (
        out["common_cta_positive"]
    )

    evidence_axes = [
        "credit_recovery_evidence",
        "vol_recovery_evidence",
        "market_mechanics_evidence",
        "flow_recovery_evidence",
        "leadership_recovery_evidence",
        "cta_recovery_evidence",
    ]

    for col in evidence_axes:
        out[col] = (
            out[col]
            .fillna(False)
            .astype(bool)
        )

    out[
        "common_recovery_axes_count"
    ] = (
        out[evidence_axes]
        .astype(int)
        .sum(axis=1)
    )

    # --------------------------------------------------------
    # Diagnostic labels
    #
    # 중요:
    # 이건 Production state가 아니다.
    # threshold optimization도 아니다.
    #
    # 상태 설계 가능성을 보기 위한 연구용 label.
    # --------------------------------------------------------

    out["research_state_hint"] = "CRISIS_OR_UNCONFIRMED"

    # 최소한 Credit + Volatility가 개선되면
    # stabilization 가능성으로만 분류.
    stabilizing = (
        out["credit_recovery_evidence"]
        &
        out["vol_recovery_evidence"]
    )

    out.loc[
        stabilizing,
        "research_state_hint",
    ] = "STABILIZING"

    # RECOVERY_CONFIRMED는 아직 만들지 않는다.
    #
    # 이유:
    # TIMING_RISK가 1개뿐이므로
    # axes_count >= N 같은 숫자를 여기서 고르면
    # 2008 최적화가 되기 때문.
    #
    # 이번 Audit은 STABILIZING까지의 구조와
    # 각 독립 축의 separation만 확인한다.

    return out


# ============================================================
# Summary
# ============================================================

def build_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    groups = [
        "TIMING_RISK",
        "SUCCESSFUL_RELEASE",
        "AMBIGUOUS_FAILURE",
    ]

    numeric_fields = [
        "common_hy",
        "common_hy_change",

        "common_vix",
        "common_vix_change",

        "common_pos_slope",
        "common_gamma",
        "common_cta",

        "common_flow",
        "common_prev_flow",

        "common_leadership",
        "common_risk_budget",

        "common_recovery_axes_count",
    ]

    boolean_fields = [
        "common_hy_improving",
        "common_vix_improving",
        "common_vix_below_panic",
        "common_pos_slope_stable",
        "common_gamma_nonnegative",
        "common_cta_positive",
        "common_flow_positive",
        "common_flow_persistent",
        "common_leadership_present",

        "credit_recovery_evidence",
        "vol_recovery_evidence",
        "market_mechanics_evidence",
        "flow_recovery_evidence",
        "leadership_recovery_evidence",
        "cta_recovery_evidence",
    ]

    rows = []

    for field in numeric_fields:

        row = {
            "feature": field,
            "type": "NUMERIC",
        }

        for group_name in groups:

            group = df[
                df["diagnosis"]
                == group_name
            ]

            row[
                f"{group_name}_mean"
            ] = safe_mean(
                group[field]
            )

            row[
                f"{group_name}_median"
            ] = safe_median(
                group[field]
            )

        timing_value = row.get(
            "TIMING_RISK_mean",
            np.nan,
        )

        success_value = row.get(
            "SUCCESSFUL_RELEASE_mean",
            np.nan,
        )

        row[
            "timing_minus_success"
        ] = (
            timing_value
            - success_value
            if (
                pd.notna(timing_value)
                and pd.notna(success_value)
            )
            else np.nan
        )

        rows.append(row)

    for field in boolean_fields:

        row = {
            "feature": field,
            "type": "BOOLEAN_PCT_TRUE",
        }

        for group_name in groups:

            group = df[
                df["diagnosis"]
                == group_name
            ]

            row[
                f"{group_name}_mean"
            ] = pct_true(
                group[field]
            )

            row[
                f"{group_name}_median"
            ] = np.nan

        timing_value = row.get(
            "TIMING_RISK_mean",
            np.nan,
        )

        success_value = row.get(
            "SUCCESSFUL_RELEASE_mean",
            np.nan,
        )

        row[
            "timing_minus_success"
        ] = (
            timing_value
            - success_value
            if (
                pd.notna(timing_value)
                and pd.notna(success_value)
            )
            else np.nan
        )

        rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# Main
# ============================================================

def main() -> None:

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw = load_data()

    common_fields, availability = (
        identify_common_fields(
            raw
        )
    )

    df = build_features(
        raw
    )

    summary = build_summary(
        df
    )

    # ========================================================
    # Save
    # ========================================================

    df.to_csv(
        EPISODE_OUT,
        index=False,
    )

    summary.to_csv(
        SUMMARY_OUT,
        index=False,
    )

    # ========================================================
    # Groups
    # ========================================================

    timing = df[
        df["diagnosis"]
        == "TIMING_RISK"
    ]

    successful = df[
        df["diagnosis"]
        == "SUCCESSFUL_RELEASE"
    ]

    ambiguous = df[
        df["diagnosis"]
        == "AMBIGUOUS_FAILURE"
    ]

    # ========================================================
    # Axis comparison
    # ========================================================

    axes = [
        "credit_recovery_evidence",
        "vol_recovery_evidence",
        "market_mechanics_evidence",
        "flow_recovery_evidence",
        "leadership_recovery_evidence",
        "cta_recovery_evidence",
    ]

    axis_rows = []

    for axis in axes:

        axis_rows.append(
            {
                "axis": axis,

                "timing_risk_pct":
                    pct_true(
                        timing[axis]
                    ),

                "successful_pct":
                    pct_true(
                        successful[axis]
                    ),

                "ambiguous_pct":
                    pct_true(
                        ambiguous[axis]
                    ),
            }
        )

    axis_table = pd.DataFrame(
        axis_rows
    )

    axis_table[
        "success_minus_timing"
    ] = (
        axis_table[
            "successful_pct"
        ]
        -
        axis_table[
            "timing_risk_pct"
        ]
    )

    axis_table = axis_table.sort_values(
        "success_minus_timing",
        ascending=False,
    )

    # ========================================================
    # State hint
    # ========================================================

    state_table = (
        df.groupby(
            [
                "diagnosis",
                "research_state_hint",
            ],
            dropna=False,
        )
        .size()
        .reset_index(
            name="episodes"
        )
    )

    # ========================================================
    # 2008 row
    # ========================================================

    timing_display = [
        "episode_id",
        "release_date",
        "diagnosis",

        "common_hy",
        "common_hy_change",

        "common_vix",
        "common_vix_change",

        "common_pos_slope",
        "common_gamma",
        "common_cta",

        "common_flow",
        "common_prev_flow",
        "common_leadership",

        "credit_recovery_evidence",
        "vol_recovery_evidence",
        "market_mechanics_evidence",
        "flow_recovery_evidence",
        "leadership_recovery_evidence",
        "cta_recovery_evidence",

        "common_recovery_axes_count",

        "research_state_hint",

        "full_incremental_return",
        "full_incremental_mdd",
    ]

    timing_display = [
        col
        for col in timing_display
        if col in timing.columns
    ]

    # ========================================================
    # Audit report
    # ========================================================

    lines = []

    lines.append(
        "=" * 78
    )

    lines.append(
        "FILTER15 COMMON-DATA RECOVERY STATE HYPOTHESIS AUDIT"
    )

    lines.append(
        "=" * 78
    )

    lines.append("")

    lines.append(
        f"Episodes              : {len(df)}"
    )

    lines.append(
        f"Successful Releases   : {len(successful)}"
    )

    lines.append(
        f"Timing Risk           : {len(timing)}"
    )

    lines.append(
        f"Ambiguous Failures    : {len(ambiguous)}"
    )

    lines.append("")

    lines.append(
        "Production Modified   : NO"
    )

    lines.append(
        "Future-data Backfill  : NO"
    )

    lines.append(
        "New Indicator         : NO"
    )

    lines.append(
        "Missing-data Gate     : NO"
    )

    lines.append(
        "Threshold Optimization: NO"
    )

    lines.append("")

    # ========================================================
    # Common fields
    # ========================================================

    lines.append(
        "===== COMMON-DATA AVAILABILITY ====="
    )

    lines.append(
        availability.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "Common usable fields:"
    )

    for field in common_fields:
        lines.append(
            f"- {field}"
        )

    lines.append("")

    # ========================================================
    # Timing Risk
    # ========================================================

    lines.append(
        "===== TIMING RISK / 2008 ====="
    )

    if timing.empty:
        lines.append(
            "No TIMING_RISK episode."
        )
    else:
        lines.append(
            timing[
                timing_display
            ].to_string(
                index=False
            )
        )

    lines.append("")

    # ========================================================
    # Axis separation
    # ========================================================

    lines.append(
        "===== RECOVERY AXIS SEPARATION ====="
    )

    lines.append(
        axis_table.to_string(
            index=False
        )
    )

    lines.append("")

    # ========================================================
    # State hint
    # ========================================================

    lines.append(
        "===== RESEARCH STATE HINT ====="
    )

    lines.append(
        state_table.to_string(
            index=False
        )
    )

    lines.append("")

    # ========================================================
    # Full summary
    # ========================================================

    lines.append(
        "===== COMMON-DATA FEATURE SUMMARY ====="
    )

    lines.append(
        summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "=" * 78
    )

    lines.append(
        "해석 원칙"
    )

    lines.append(
        "=" * 78
    )

    lines.append("")

    lines.append(
        "1. 2008에서 결측인 VIX_Z / SP500_POS_Z / "
        "NET_LIQ / Cross-Asset Z는 recovery gate에 사용하지 않는다."
    )

    lines.append("")

    lines.append(
        "2. HY 하락과 VIX 하락은 stabilization을 의미할 수 있지만 "
        "그 자체가 exposure 복원 승인을 의미하지 않는다."
    )

    lines.append("")

    lines.append(
        "3. Recovery는 Credit / Volatility / Market Mechanics / "
        "Flow / Leadership / CTA의 독립 축으로 평가한다."
    )

    lines.append("")

    lines.append(
        "4. 이번 Audit의 research_state_hint는 "
        "STABILIZING 가능성을 확인하기 위한 진단 label이며 "
        "Production state가 아니다."
    )

    lines.append("")

    lines.append(
        "5. RECOVERY_CONFIRMED threshold는 이번 단계에서 만들지 않는다. "
        "TIMING_RISK가 1개뿐이므로 axes_count 숫자를 고르면 "
        "2008 과적합 위험이 있다."
    )

    lines.append("")

    lines.append(
        "6. 여러 독립 축에서 반복적으로 separation이 확인될 경우에만 "
        "다음 단계에서 state-machine counterfactual을 만든다."
    )

    lines.append("")

    lines.append(
        "PRODUCTION DECISION: NO CHANGE"
    )

    lines.append(
        "NEXT GATE: STATE-MACHINE COUNTERFACTUAL DESIGN"
    )

    audit_text = "\n".join(
        lines
    )

    AUDIT_OUT.write_text(
        audit_text,
        encoding="utf-8",
    )

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
        f"Saved: {AUDIT_OUT}"
    )


if __name__ == "__main__":
    main()