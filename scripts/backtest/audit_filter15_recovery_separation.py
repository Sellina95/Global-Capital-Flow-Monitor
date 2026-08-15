from __future__ import annotations

"""
FILTER15 RECOVERY SEPARATION AUDIT

목적
----
Deadman 이후:

    CRISIS
        ->
    STABILIZING
        ->
    RECOVERY_CONFIRMED

를 구분할 수 있는 기존 데이터 축이 무엇인지 진단한다.

중요:
- 새로운 release rule을 만들지 않는다.
- threshold optimization을 하지 않는다.
- Production을 수정하지 않는다.
- 2008 한 episode에 맞춘 과적합을 하지 않는다.
- 기존 execution-state snapshot만 사용한다.

Input
-----
data/backtest/results/
filter15_systemic_crisis_execution_state.csv

Output
------
data/backtest/results/
filter15_recovery_separation_episode.csv

data/backtest/results/
filter15_recovery_separation_summary.csv

data/backtest/results/
filter15_recovery_separation_audit.txt
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
    / "filter15_systemic_crisis_execution_state.csv"
)

EPISODE_OUT = (
    RESULT_DIR
    / "filter15_recovery_separation_episode.csv"
)

SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_recovery_separation_summary.csv"
)

AUDIT_OUT = (
    RESULT_DIR
    / "filter15_recovery_separation_audit.txt"
)


# ============================================================
# Helpers
# ============================================================

def numeric(
    df: pd.DataFrame,
    column: str,
) -> pd.Series:

    if column not in df.columns:
        return pd.Series(
            np.nan,
            index=df.index,
            dtype=float,
        )

    return pd.to_numeric(
        df[column],
        errors="coerce",
    )


def available_numeric(
    df: pd.DataFrame,
    column: str,
) -> pd.Series:

    return numeric(
        df,
        column,
    ).notna()


def available_text(
    df: pd.DataFrame,
    column: str,
) -> pd.Series:

    if column not in df.columns:
        return pd.Series(
            False,
            index=df.index,
            dtype=bool,
        )

    value = (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    missing_tokens = {
        "",
        "N/A",
        "NA",
        "NAN",
        "NONE",
        "NULL",
        "MISSING",
        "NOT_FOUND",
    }

    return ~value.isin(
        missing_tokens
    )


def safe_mean(
    series: pd.Series,
) -> float:

    x = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if x.empty:
        return np.nan

    return float(
        x.mean()
    )


def safe_median(
    series: pd.Series,
) -> float:

    x = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if x.empty:
        return np.nan

    return float(
        x.median()
    )


def pct_true(
    series: pd.Series,
) -> float:

    if len(series) == 0:
        return np.nan

    return float(
        pd.Series(series)
        .fillna(False)
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
            "\nRequired input not found:\n"
            f"{INPUT_PATH}\n\n"
            "먼저 "
            "audit_filter15_systemic_crisis_execution_state.py "
            "를 실행하세요."
        )

    df = pd.read_csv(
        INPUT_PATH
    )

    required = {
        "episode_id",
        "release_date",
        "diagnosis",
    }

    missing = sorted(
        required
        - set(df.columns)
    )

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

    return (
        df
        .sort_values(
            [
                "release_date",
                "episode_id",
            ]
        )
        .reset_index(drop=True)
    )


# ============================================================
# Build diagnostic features
# ============================================================

def build_features(
    df: pd.DataFrame,
) -> pd.DataFrame:

    out = df.copy()

    # --------------------------------------------------------
    # Raw numeric states
    # --------------------------------------------------------

    out["diag_hy"] = numeric(
        out,
        "HY_OAS",
    )

    out["diag_hy_change"] = numeric(
        out,
        "HY_OAS_PCT_CHANGE",
    )

    out["diag_vix"] = numeric(
        out,
        "VIX_TODAY",
    )

    out["diag_vix_change"] = numeric(
        out,
        "VIX_PCT_CHANGE",
    )

    out["diag_vix_z"] = numeric(
        out,
        "VIX_Z",
    )

    out["diag_pos_z"] = numeric(
        out,
        "SP500_POS_Z",
    )

    out["diag_pos_slope"] = numeric(
        out,
        "POS_SLOPE",
    )

    out["diag_gamma"] = numeric(
        out,
        "DEALER_GAMMA_BIAS",
    )

    out["diag_cta"] = numeric(
        out,
        "CTA_MOMENTUM_SCORE",
    )

    out["diag_net_liq"] = numeric(
        out,
        "NET_LIQ",
    )

    out["diag_flow"] = numeric(
        out,
        "INSTITUTIONAL_FLOW_SCORE",
    )

    out["diag_prev_flow"] = numeric(
        out,
        "PREV_FLOW_SCORE",
    )

    out["diag_leadership"] = numeric(
        out,
        "LEADERSHIP_BREADTH_SCORE",
    )

    out["diag_us10y_z"] = numeric(
        out,
        "CROSS_ASSET_US10Y_Z",
    )

    out["diag_dxy_z"] = numeric(
        out,
        "CROSS_ASSET_DXY_Z",
    )

    out["diag_wti_z"] = numeric(
        out,
        "CROSS_ASSET_WTI_Z",
    )

    # --------------------------------------------------------
    # Data availability
    #
    # 이것 자체를 release rule로 쓰는 것이 아니다.
    # 회복 판단 당시 confirmation breadth가 얼마나 존재했는지
    # 진단하기 위한 feature다.
    # --------------------------------------------------------

    out["has_vix_z"] = available_numeric(
        out,
        "VIX_Z",
    )

    out["has_positioning"] = available_numeric(
        out,
        "SP500_POS_Z",
    )

    out["has_pos_slope"] = available_numeric(
        out,
        "POS_SLOPE",
    )

    out["has_net_liq"] = available_numeric(
        out,
        "NET_LIQ",
    )

    out["has_flow"] = available_numeric(
        out,
        "INSTITUTIONAL_FLOW_SCORE",
    )

    out["has_leadership"] = available_numeric(
        out,
        "LEADERSHIP_BREADTH_SCORE",
    )

    out["has_us10y_z"] = available_numeric(
        out,
        "CROSS_ASSET_US10Y_Z",
    )

    out["has_dxy_z"] = available_numeric(
        out,
        "CROSS_ASSET_DXY_Z",
    )

    out["has_wti_z"] = available_numeric(
        out,
        "CROSS_ASSET_WTI_Z",
    )

    out["has_macro"] = available_text(
        out,
        "MACRO_NARRATIVE",
    )

    out["has_market_regime"] = available_text(
        out,
        "MARKET_REGIME",
    )

    out["has_struct"] = available_text(
        out,
        "STRUCT_V2_STATE",
    )

    out["has_gamma_state"] = available_text(
        out,
        "GAMMA_STATE",
    )

    out["has_policy"] = available_text(
        out,
        "POLICY_BIAS_LINE",
    )

    out["has_flow_state"] = available_text(
        out,
        "INSTITUTIONAL_FLOW_STATE",
    )

    # --------------------------------------------------------
    # Confirmation breadth
    # --------------------------------------------------------

    confirmation_columns = [
        "has_vix_z",
        "has_positioning",
        "has_pos_slope",
        "has_net_liq",
        "has_flow",
        "has_leadership",
        "has_us10y_z",
        "has_dxy_z",
        "has_wti_z",
        "has_macro",
        "has_market_regime",
        "has_struct",
        "has_gamma_state",
        "has_policy",
        "has_flow_state",
    ]

    out[
        "confirmation_available_count"
    ] = (
        out[
            confirmation_columns
        ]
        .astype(int)
        .sum(axis=1)
    )

    out[
        "confirmation_available_pct"
    ] = (
        out[
            "confirmation_available_count"
        ]
        / len(confirmation_columns)
        * 100.0
    )

    # --------------------------------------------------------
    # Directional evidence
    #
    # 중요:
    # 이것은 candidate release rule이 아니다.
    #
    # 단순히 기존 state 중 몇 개가
    # "stabilization 방향"을 가리키는지 비교한다.
    # --------------------------------------------------------

    out["evidence_hy_falling"] = (
        out["diag_hy_change"] < 0
    )

    out["evidence_vix_falling"] = (
        out["diag_vix_change"] < 0
    )

    out["evidence_vix_below_panic"] = (
        out["diag_vix"] < 30
    )

    out["evidence_vix_z_nonpositive"] = (
        out["diag_vix_z"] <= 0
    )

    out["evidence_positioning_not_extreme"] = (
        out["diag_pos_z"].abs() < 2
    )

    out["evidence_positioning_not_accelerating"] = (
        out["diag_pos_slope"].abs() <= 0.5
    )

    out["evidence_gamma_not_negative_proxy"] = (
        out["diag_gamma"] >= 0.5
    )

    out["evidence_cta_not_bearish"] = (
        out["diag_cta"] > 0
    )

    out["evidence_flow_positive"] = (
        out["diag_flow"] > 0
    )

    out["evidence_flow_persistent"] = (
        (
            out["diag_flow"] > 0
        )
        & (
            out["diag_prev_flow"] > 0
        )
    )

    out["evidence_leadership_present"] = (
        out["diag_leadership"] >= 2
    )

    # --------------------------------------------------------
    # Evidence count
    #
    # Missing data는 evidence로 인정하지 않는다.
    # --------------------------------------------------------

    evidence_columns = [
        "evidence_hy_falling",
        "evidence_vix_falling",
        "evidence_vix_below_panic",
        "evidence_vix_z_nonpositive",
        "evidence_positioning_not_extreme",
        "evidence_positioning_not_accelerating",
        "evidence_gamma_not_negative_proxy",
        "evidence_cta_not_bearish",
        "evidence_flow_positive",
        "evidence_flow_persistent",
        "evidence_leadership_present",
    ]

    for column in evidence_columns:

        out[column] = (
            out[column]
            .fillna(False)
            .astype(bool)
        )

    out[
        "stabilization_evidence_count"
    ] = (
        out[
            evidence_columns
        ]
        .astype(int)
        .sum(axis=1)
    )

    return out


# ============================================================
# Group comparison
# ============================================================

def build_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    numeric_fields = [
        "diag_hy",
        "diag_hy_change",
        "diag_vix",
        "diag_vix_change",
        "diag_vix_z",
        "diag_pos_z",
        "diag_pos_slope",
        "diag_gamma",
        "diag_cta",
        "diag_net_liq",
        "diag_flow",
        "diag_prev_flow",
        "diag_leadership",
        "diag_us10y_z",
        "diag_dxy_z",
        "diag_wti_z",
        "confirmation_available_count",
        "confirmation_available_pct",
        "stabilization_evidence_count",
    ]

    boolean_fields = [
        "has_vix_z",
        "has_positioning",
        "has_pos_slope",
        "has_net_liq",
        "has_flow",
        "has_leadership",
        "has_us10y_z",
        "has_dxy_z",
        "has_wti_z",
        "evidence_hy_falling",
        "evidence_vix_falling",
        "evidence_vix_below_panic",
        "evidence_vix_z_nonpositive",
        "evidence_positioning_not_extreme",
        "evidence_positioning_not_accelerating",
        "evidence_gamma_not_negative_proxy",
        "evidence_cta_not_bearish",
        "evidence_flow_positive",
        "evidence_flow_persistent",
        "evidence_leadership_present",
    ]

    groups = {
        "TIMING_RISK":
            df[
                df["diagnosis"]
                == "TIMING_RISK"
            ],

        "SUCCESSFUL_RELEASE":
            df[
                df["diagnosis"]
                == "SUCCESSFUL_RELEASE"
            ],

        "AMBIGUOUS_FAILURE":
            df[
                df["diagnosis"]
                == "AMBIGUOUS_FAILURE"
            ],
    }

    rows = []

    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    for field in numeric_fields:

        row = {
            "feature": field,
            "feature_type": "NUMERIC",
        }

        for name, group in groups.items():

            row[
                f"{name}_mean"
            ] = safe_mean(
                group[field]
            )

            row[
                f"{name}_median"
            ] = safe_median(
                group[field]
            )

        timing = row[
            "TIMING_RISK_mean"
        ]

        success = row[
            "SUCCESSFUL_RELEASE_mean"
        ]

        row[
            "timing_minus_success"
        ] = (
            timing - success
            if (
                pd.notna(timing)
                and pd.notna(success)
            )
            else np.nan
        )

        rows.append(row)

    # --------------------------------------------------------
    # Boolean
    # --------------------------------------------------------

    for field in boolean_fields:

        row = {
            "feature": field,
            "feature_type": "BOOLEAN_PCT_TRUE",
        }

        for name, group in groups.items():

            row[
                f"{name}_mean"
            ] = pct_true(
                group[field]
            )

            row[
                f"{name}_median"
            ] = np.nan

        timing = row[
            "TIMING_RISK_mean"
        ]

        success = row[
            "SUCCESSFUL_RELEASE_mean"
        ]

        row[
            "timing_minus_success"
        ] = (
            timing - success
            if (
                pd.notna(timing)
                and pd.notna(success)
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
    # Group frames
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
    # 2008 display
    # ========================================================

    display_columns = [
        "episode_id",
        "release_date",
        "diagnosis",

        "HY_OAS",
        "HY_OAS_PCT_CHANGE",

        "VIX_TODAY",
        "VIX_PCT_CHANGE",
        "VIX_Z",

        "SP500_POS_Z",
        "POS_SLOPE",

        "DEALER_GAMMA_BIAS",
        "CTA_MOMENTUM_SCORE",

        "INSTITUTIONAL_FLOW_SCORE",
        "PREV_FLOW_SCORE",

        "LEADERSHIP_BREADTH_SCORE",

        "confirmation_available_count",
        "confirmation_available_pct",

        "stabilization_evidence_count",

        "full_incremental_return",
        "full_incremental_mdd",
    ]

    display_columns = [
        column
        for column in display_columns
        if column in df.columns
    ]

    # ========================================================
    # Largest raw differences
    #
    # 이것도 selection이지 optimization이 아니다.
    # 절대값 차이가 큰 feature를 보여줄 뿐이다.
    # ========================================================

    ranked = (
        summary
        .dropna(
            subset=[
                "timing_minus_success"
            ]
        )
        .assign(
            abs_difference=lambda x:
                x[
                    "timing_minus_success"
                ].abs()
        )
        .sort_values(
            "abs_difference",
            ascending=False,
        )
    )

    # ========================================================
    # Audit
    # ========================================================

    lines = []

    lines.append(
        "=" * 78
    )

    lines.append(
        "FILTER15 RECOVERY SEPARATION AUDIT"
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
        "Release Rule Modified : NO"
    )

    lines.append(
        "Threshold Optimization: NO"
    )

    lines.append("")

    lines.append(
        "===== TIMING RISK / 2008 ====="
    )

    if timing.empty:

        lines.append(
            "No TIMING_RISK episode found."
        )

    else:

        lines.append(
            timing[
                display_columns
            ].to_string(
                index=False
            )
        )

    lines.append("")

    lines.append(
        "===== SUCCESSFUL RELEASE AVERAGES ====="
    )

    successful_fields = [
        "diag_hy",
        "diag_hy_change",
        "diag_vix",
        "diag_vix_change",
        "diag_vix_z",
        "diag_pos_z",
        "diag_pos_slope",
        "diag_cta",
        "diag_flow",
        "diag_prev_flow",
        "diag_leadership",
        "confirmation_available_count",
        "confirmation_available_pct",
        "stabilization_evidence_count",
    ]

    success_table = []

    for field in successful_fields:

        success_table.append(
            {
                "feature": field,
                "mean":
                    safe_mean(
                        successful[field]
                    ),
                "median":
                    safe_median(
                        successful[field]
                    ),
            }
        )

    lines.append(
        pd.DataFrame(
            success_table
        ).to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "===== LARGEST TIMING-vs-SUCCESS DIFFERENCES ====="
    )

    lines.append(
        ranked[
            [
                "feature",
                "feature_type",
                "TIMING_RISK_mean",
                "SUCCESSFUL_RELEASE_mean",
                "timing_minus_success",
            ]
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "===== FULL FEATURE SUMMARY ====="
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
        "1. TIMING_RISK는 1개 episode뿐이므로 "
        "2008에 맞는 숫자 threshold를 만들지 않는다."
    )

    lines.append("")

    lines.append(
        "2. 이번 단계의 목적은 어떤 독립 축이 "
        "성공 recovery와 실패 recovery를 구분할 가능성이 있는지 "
        "후보를 좁히는 것이다."
    )

    lines.append("")

    lines.append(
        "3. 단일 지표보다 Credit / Volatility / Financial Conditions / "
        "Flow / Leadership / Positioning / Liquidity의 "
        "복수 확인 구조를 우선 검토한다."
    )

    lines.append("")

    lines.append(
        "4. confirmation_available_count는 데이터가 많다는 이유만으로 "
        "release를 허용하기 위한 점수가 아니다. "
        "회복 판단 당시 정보 품질을 진단하기 위한 값이다."
    )

    lines.append("")

    lines.append(
        "5. 이번 결과에서 의미 있는 separation 후보가 발견되면 "
        "그 다음에만 CRISIS -> STABILIZING -> RECOVERY_CONFIRMED "
        "research state-machine을 정의한다."
    )

    lines.append("")

    lines.append(
        "6. state-machine 정의 후에도 바로 Production에 넣지 않고 "
        "별도 point-in-time counterfactual과 out-of-sample 검증을 거친다."
    )

    lines.append("")

    lines.append(
        "PRODUCTION DECISION: NO CHANGE"
    )

    lines.append(
        "NEXT GATE: RECOVERY STATE HYPOTHESIS"
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