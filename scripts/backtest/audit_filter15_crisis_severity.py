from __future__ import annotations

"""
FILTER15 CRISIS SEVERITY / LEVEL-vs-DIRECTION AUDIT

목적
----
Deadman 이후 조기 recovery 후보가 발생할 때,

1) 위험 지표의 방향(Direction)은 개선되고 있지만
2) 절대 위험 수준(Level)은 여전히 crisis 상태인지

를 분리해서 진단한다.

특히 2008 Timing Risk와 Successful Release를 비교하여
단순 HY falling / VIX falling이 false stabilization을
만드는 구조적 원인인지 확인한다.

원칙
----
- Production 수정 금지
- 미래 데이터 사용 금지
- 새 지표 추가 금지
- Missing-data gate 금지
- 새로운 threshold optimization 금지
- 기존 Production 경계만 사용
"""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

INPUT_PATH = (
    RESULT_DIR
    / "filter15_common_data_recovery_state_episode.csv"
)

EPISODE_OUT = (
    RESULT_DIR
    / "filter15_crisis_severity_episode.csv"
)

SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_crisis_severity_summary.csv"
)

AUDIT_OUT = (
    RESULT_DIR
    / "filter15_crisis_severity_audit.txt"
)


# ============================================================
# Helpers
# ============================================================

def num(df: pd.DataFrame, col: str) -> pd.Series:
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


def pct_true(series: pd.Series) -> float:
    if len(series) == 0:
        return np.nan

    return float(
        series.fillna(False)
        .astype(bool)
        .mean()
        * 100.0
    )


def safe_mean(series: pd.Series) -> float:
    x = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if x.empty:
        return np.nan

    return float(x.mean())


def safe_median(series: pd.Series) -> float:
    x = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if x.empty:
        return np.nan

    return float(x.median())


# ============================================================
# Load
# ============================================================

def load_data() -> pd.DataFrame:

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"\nMissing input:\n{INPUT_PATH}\n\n"
            "먼저 "
            "audit_filter15_common_data_recovery_state.py "
            "를 실행하세요."
        )

    df = pd.read_csv(INPUT_PATH)

    required = [
        "episode_id",
        "release_date",
        "diagnosis",
        "common_hy",
        "common_hy_change",
        "common_vix",
        "common_vix_change",
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
# Severity classification
# ============================================================

def build_severity_features(
    df: pd.DataFrame,
) -> pd.DataFrame:

    out = df.copy()

    hy = num(out, "common_hy")
    hy_change = num(
        out,
        "common_hy_change",
    )

    vix = num(out, "common_vix")
    vix_change = num(
        out,
        "common_vix_change",
    )

    # --------------------------------------------------------
    # CREDIT LEVEL
    #
    # 기존 Production Filter15 경계 그대로 사용.
    #
    # HY >= 6.0 : Credit Crisis / Hard Deadman
    # HY >= 5.0 : Credit Stress
    # HY >= 4.0 : Mild Credit Stress
    # --------------------------------------------------------

    out["credit_level_state"] = "CALM"

    out.loc[
        hy >= 4.0,
        "credit_level_state",
    ] = "MILD_STRESS"

    out.loc[
        hy >= 5.0,
        "credit_level_state",
    ] = "STRESS"

    out.loc[
        hy >= 6.0,
        "credit_level_state",
    ] = "CRISIS"

    # --------------------------------------------------------
    # CREDIT DIRECTION
    # --------------------------------------------------------

    out["credit_direction"] = "FLAT"

    out.loc[
        hy_change < 0,
        "credit_direction",
    ] = "IMPROVING"

    out.loc[
        hy_change > 0,
        "credit_direction",
    ] = "DETERIORATING"

    # --------------------------------------------------------
    # VIX LEVEL
    #
    # 기존 Production Filter15 경계.
    #
    # <14 LOW
    # <20 NORMAL
    # <30 STRESS
    # >=30 PANIC
    # --------------------------------------------------------

    out["vix_level_state"] = "LOW"

    out.loc[
        vix >= 14,
        "vix_level_state",
    ] = "NORMAL"

    out.loc[
        vix >= 20,
        "vix_level_state",
    ] = "STRESS"

    out.loc[
        vix >= 30,
        "vix_level_state",
    ] = "PANIC"

    # --------------------------------------------------------
    # VIX DIRECTION
    # --------------------------------------------------------

    out["vix_direction"] = "FLAT"

    out.loc[
        vix_change < 0,
        "vix_direction",
    ] = "IMPROVING"

    out.loc[
        vix_change > 0,
        "vix_direction",
    ] = "DETERIORATING"

    # --------------------------------------------------------
    # Level / Direction conflict
    #
    # 핵심 연구 대상:
    #
    # 방향은 좋아지고 있지만 절대 수준은 여전히 위험한가?
    # --------------------------------------------------------

    out["credit_improving"] = (
        hy_change < 0
    )

    out["vix_improving"] = (
        vix_change < 0
    )

    out["credit_still_crisis"] = (
        hy >= 6.0
    )

    out["credit_still_stress"] = (
        hy >= 5.0
    )

    out["vix_still_stress"] = (
        vix >= 20
    )

    out["vix_still_panic"] = (
        vix >= 30
    )

    # --------------------------------------------------------
    # False stabilization candidates
    # --------------------------------------------------------

    out[
        "credit_direction_level_conflict"
    ] = (
        out["credit_improving"]
        &
        out["credit_still_crisis"]
    )

    out[
        "vix_direction_level_conflict"
    ] = (
        out["vix_improving"]
        &
        out["vix_still_stress"]
    )

    out[
        "dual_direction_improvement"
    ] = (
        out["credit_improving"]
        &
        out["vix_improving"]
    )

    out[
        "dual_improvement_but_crisis_level"
    ] = (
        out["dual_direction_improvement"]
        &
        (
            out["credit_still_crisis"]
            |
            out["vix_still_panic"]
        )
    )

    # --------------------------------------------------------
    # Research state
    #
    # 이것은 Production rule이 아니다.
    # 기존 threshold의 의미를 이용한 diagnostic label.
    # --------------------------------------------------------

    out["severity_state_hint"] = (
        "UNRESOLVED"
    )

    # Direction조차 안 좋아짐
    unresolved = ~(
        out["dual_direction_improvement"]
    )

    out.loc[
        unresolved,
        "severity_state_hint",
    ] = "CRISIS_OR_UNSTABLE"

    # 방향은 개선됐지만 level이 crisis
    out.loc[
        out[
            "dual_improvement_but_crisis_level"
        ],
        "severity_state_hint",
    ] = "EARLY_STABILIZATION"

    # 방향 개선 + hard crisis level 해제
    recovering = (
        out["dual_direction_improvement"]
        &
        ~out["credit_still_crisis"]
        &
        ~out["vix_still_panic"]
    )

    out.loc[
        recovering,
        "severity_state_hint",
    ] = "LEVEL_NORMALIZING"

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

    features = [
        "credit_improving",
        "vix_improving",

        "credit_still_crisis",
        "credit_still_stress",

        "vix_still_stress",
        "vix_still_panic",

        "credit_direction_level_conflict",
        "vix_direction_level_conflict",

        "dual_direction_improvement",
        "dual_improvement_but_crisis_level",
    ]

    rows = []

    for feature in features:

        row = {
            "feature": feature,
        }

        for group_name in groups:

            group = df[
                df["diagnosis"]
                == group_name
            ]

            row[
                f"{group_name}_pct"
            ] = pct_true(
                group[feature]
            )

        timing = row.get(
            "TIMING_RISK_pct",
            np.nan,
        )

        success = row.get(
            "SUCCESSFUL_RELEASE_pct",
            np.nan,
        )

        if (
            pd.notna(timing)
            and pd.notna(success)
        ):
            row[
                "timing_minus_success"
            ] = timing - success
        else:
            row[
                "timing_minus_success"
            ] = np.nan

        rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# Numeric comparison
# ============================================================

def build_numeric_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    groups = [
        "TIMING_RISK",
        "SUCCESSFUL_RELEASE",
        "AMBIGUOUS_FAILURE",
    ]

    features = [
        "common_hy",
        "common_hy_change",
        "common_vix",
        "common_vix_change",
    ]

    rows = []

    for feature in features:

        row = {
            "feature": feature,
        }

        for group_name in groups:

            group = df[
                df["diagnosis"]
                == group_name
            ]

            row[
                f"{group_name}_mean"
            ] = safe_mean(
                group[feature]
            )

            row[
                f"{group_name}_median"
            ] = safe_median(
                group[feature]
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

    df = build_severity_features(
        raw
    )

    summary = build_summary(
        df
    )

    numeric_summary = (
        build_numeric_summary(df)
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    df.to_csv(
        EPISODE_OUT,
        index=False,
    )

    summary.to_csv(
        SUMMARY_OUT,
        index=False,
    )

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

    # --------------------------------------------------------
    # State distribution
    # --------------------------------------------------------

    state_summary = (
        df.groupby(
            [
                "diagnosis",
                "severity_state_hint",
            ],
            dropna=False,
        )
        .size()
        .reset_index(
            name="episodes"
        )
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    display_cols = [
        "episode_id",
        "release_date",
        "diagnosis",

        "common_hy",
        "common_hy_change",
        "credit_level_state",
        "credit_direction",

        "common_vix",
        "common_vix_change",
        "vix_level_state",
        "vix_direction",

        "credit_direction_level_conflict",
        "vix_direction_level_conflict",
        "dual_direction_improvement",
        "dual_improvement_but_crisis_level",

        "severity_state_hint",

        "full_incremental_return",
        "full_incremental_mdd",
    ]

    display_cols = [
        col
        for col in display_cols
        if col in df.columns
    ]

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    lines = []

    lines.append("=" * 78)
    lines.append(
        "FILTER15 CRISIS SEVERITY / LEVEL-vs-DIRECTION AUDIT"
    )
    lines.append("=" * 78)

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
        "Threshold Optimization: NO"
    )
    lines.append(
        "Threshold Source      : EXISTING FILTER15 PRODUCTION BOUNDARIES"
    )

    lines.append("")

    # --------------------------------------------------------
    # 2008
    # --------------------------------------------------------

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
                display_cols
            ].to_string(
                index=False
            )
        )

    lines.append("")

    # --------------------------------------------------------
    # Successful
    # --------------------------------------------------------

    lines.append(
        "===== SUCCESSFUL RELEASES ====="
    )

    if successful.empty:
        lines.append(
            "No successful episodes."
        )
    else:
        lines.append(
            successful[
                display_cols
            ].to_string(
                index=False
            )
        )

    lines.append("")

    # --------------------------------------------------------
    # Separation
    # --------------------------------------------------------

    lines.append(
        "===== LEVEL-vs-DIRECTION SEPARATION ====="
    )

    lines.append(
        summary.to_string(
            index=False
        )
    )

    lines.append("")

    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    lines.append(
        "===== NUMERIC COMPARISON ====="
    )

    lines.append(
        numeric_summary.to_string(
            index=False
        )
    )

    lines.append("")

    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    lines.append(
        "===== SEVERITY STATE DISTRIBUTION ====="
    )

    lines.append(
        state_summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append("=" * 78)
    lines.append("해석 원칙")
    lines.append("=" * 78)

    lines.append("")

    lines.append(
        "1. Direction improvement는 crisis 종료와 동일하지 않다."
    )

    lines.append("")

    lines.append(
        "2. HY가 하락 중이어도 HY >= 6이면 Production 정의상 "
        "Credit Crisis level은 아직 유지된다."
    )

    lines.append("")

    lines.append(
        "3. VIX가 하락 중이어도 절대 level이 높다면 "
        "시장 stress가 완전히 정상화되었다고 볼 수 없다."
    )

    lines.append("")

    lines.append(
        "4. EARLY_STABILIZATION은 recovery 실패 판정이 아니라 "
        "'방향은 개선됐지만 crisis severity가 남아 있음'을 뜻한다."
    )

    lines.append("")

    lines.append(
        "5. 이 Audit에서 2008 Timing Risk가 EARLY_STABILIZATION에 "
        "위치하고 성공 recovery가 LEVEL_NORMALIZING에 집중되는지 확인한다."
    )

    lines.append("")

    lines.append(
        "6. separation이 확인되지 않으면 새로운 숫자를 최적화하지 않고 "
        "crisis persistence / regime history로 연구 범위를 이동한다."
    )

    lines.append("")

    lines.append(
        "PRODUCTION DECISION: NO CHANGE"
    )

    lines.append(
        "NEXT GATE: "
        "CRISIS -> STABILIZING -> RECOVERY_CONFIRMED "
        "STATE-MACHINE ELIGIBILITY"
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