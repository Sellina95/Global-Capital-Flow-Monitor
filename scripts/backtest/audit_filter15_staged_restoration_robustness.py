from __future__ import annotations

"""
FILTER15 STAGED RESTORATION ROBUSTNESS AUDIT

목적
----
이미 완료된 staged restoration counterfactual의 결과가

1) 특정 crisis / 특정 episode 하나에 의존하는가?
2) 여러 시기에서 방향성이 유지되는가?
3) RAMP_3가 STATIC_FULL 대비 episode-level로 일관되게 개선되는가?
4) 2008 episode를 제거해도 결론이 유지되는가?

를 검증한다.

중요
----
이번 Audit은 새로운 전략을 만들지 않는다.
기존 결과 artifact를 재분석하는 robustness gate다.

입력
----
filter15_staged_restoration_episodes.csv

기존 path:
- STATIC_FULL
- RAMP_2
- RAMP_3

원칙
----
- Production 수정 금지
- 새로운 indicator 없음
- 새로운 threshold 없음
- 미래 데이터 없음
- parameter optimization 없음
- 기존 counterfactual 결과만 재분석
"""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

INPUT_PATH = (
    RESULT_DIR
    / "filter15_staged_restoration_episodes.csv"
)

OUT_EPISODE = (
    RESULT_DIR
    / "filter15_staged_restoration_robustness_episode.csv"
)

OUT_ERA = (
    RESULT_DIR
    / "filter15_staged_restoration_robustness_era.csv"
)

OUT_LOO = (
    RESULT_DIR
    / "filter15_staged_restoration_robustness_leave_one_out.csv"
)

OUT_SUMMARY = (
    RESULT_DIR
    / "filter15_staged_restoration_robustness_summary.csv"
)

OUT_TXT = (
    RESULT_DIR
    / "filter15_staged_restoration_robustness_audit.txt"
)


PATHS = [
    "STATIC_FULL",
    "RAMP_2",
    "RAMP_3",
]


# ============================================================
# Helpers
# ============================================================

def num(series):
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def pct(x):
    if pd.isna(x):
        return "NaN"
    return f"{100.0 * float(x):.3f}%"


# ============================================================
# Load
# ============================================================

def load_data():

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"\n필요한 staged restoration 결과가 없습니다:\n"
            f"{INPUT_PATH}\n\n"
            "먼저 아래를 실행하세요:\n"
            "python scripts/backtest/"
            "audit_filter15_staged_restoration_path.py"
        )

    df = pd.read_csv(
        INPUT_PATH
    )

    required = [
        "episode_id",
        "diagnosis",
        "release_date",
        "rows_released_early",
        "candidate_exposure",
        "path",
        "total_return",
        "mdd",
        "invested_days",
        "full_days",
        "rebrake_days",
        "avg_exposure",
    ]

    missing = [
        c
        for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            "\nStaged restoration artifact contract 오류.\n"
            f"Missing columns: {missing}"
        )

    df["release_date"] = pd.to_datetime(
        df["release_date"],
        errors="coerce",
    )

    numeric_cols = [
        "episode_id",
        "rows_released_early",
        "candidate_exposure",
        "total_return",
        "mdd",
        "invested_days",
        "full_days",
        "rebrake_days",
        "avg_exposure",
    ]

    for col in numeric_cols:
        df[col] = num(df[col])

    df["path"] = (
        df["path"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["diagnosis"] = (
        df["diagnosis"]
        .fillna("UNKNOWN")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    unknown_paths = sorted(
        set(df["path"].dropna())
        - set(PATHS)
    )

    if unknown_paths:
        raise ValueError(
            f"예상하지 못한 path가 있습니다: {unknown_paths}"
        )

    # 각 episode마다 세 path가 모두 있어야 한다.
    counts = (
        df.groupby("episode_id")["path"]
        .nunique()
    )

    bad = counts[
        counts != len(PATHS)
    ]

    if not bad.empty:
        raise ValueError(
            "\nEpisode별 path contract가 깨졌습니다.\n"
            f"{bad.to_string()}"
        )

    return (
        df
        .sort_values(
            ["episode_id", "path"]
        )
        .reset_index(drop=True)
    )


# ============================================================
# Episode Pairwise Comparison
# ============================================================

def build_episode_comparison(df):

    value_cols = [
        "total_return",
        "mdd",
        "avg_exposure",
        "invested_days",
        "full_days",
        "rebrake_days",
    ]

    pivot = df.pivot(
        index=[
            "episode_id",
            "diagnosis",
            "release_date",
            "rows_released_early",
            "candidate_exposure",
        ],
        columns="path",
        values=value_cols,
    )

    pivot.columns = [
        f"{metric}__{path}"
        for metric, path in pivot.columns
    ]

    pivot = (
        pivot
        .reset_index()
        .sort_values("episode_id")
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # RAMP_2 vs STATIC
    # --------------------------------------------------------

    pivot["return_delta_ramp2_vs_static"] = (
        pivot["total_return__RAMP_2"]
        - pivot["total_return__STATIC_FULL"]
    )

    # MDD는 덜 음수일수록 개선.
    pivot["mdd_improvement_ramp2_vs_static"] = (
        pivot["mdd__RAMP_2"]
        - pivot["mdd__STATIC_FULL"]
    )

    # --------------------------------------------------------
    # RAMP_3 vs STATIC
    # --------------------------------------------------------

    pivot["return_delta_ramp3_vs_static"] = (
        pivot["total_return__RAMP_3"]
        - pivot["total_return__STATIC_FULL"]
    )

    pivot["mdd_improvement_ramp3_vs_static"] = (
        pivot["mdd__RAMP_3"]
        - pivot["mdd__STATIC_FULL"]
    )

    # --------------------------------------------------------
    # RAMP_3 vs RAMP_2
    # --------------------------------------------------------

    pivot["return_delta_ramp3_vs_ramp2"] = (
        pivot["total_return__RAMP_3"]
        - pivot["total_return__RAMP_2"]
    )

    pivot["mdd_improvement_ramp3_vs_ramp2"] = (
        pivot["mdd__RAMP_3"]
        - pivot["mdd__RAMP_2"]
    )

    # --------------------------------------------------------
    # Episode-level wins
    # --------------------------------------------------------

    pivot["ramp3_return_win_vs_static"] = (
        pivot["return_delta_ramp3_vs_static"]
        > 0
    )

    pivot["ramp3_mdd_win_vs_static"] = (
        pivot["mdd_improvement_ramp3_vs_static"]
        > 0
    )

    pivot["ramp3_joint_win_vs_static"] = (
        pivot["ramp3_return_win_vs_static"]
        &
        pivot["ramp3_mdd_win_vs_static"]
    )

    pivot["ramp3_return_loss_vs_static"] = (
        pivot["return_delta_ramp3_vs_static"]
        < 0
    )

    # 연도
    pivot["year"] = (
        pivot["release_date"].dt.year
    )

    return pivot


# ============================================================
# Era Robustness
# ============================================================

def assign_era(year):

    if pd.isna(year):
        return "UNKNOWN"

    year = int(year)

    if year <= 2010:
        return "2008-2010"

    if year <= 2013:
        return "2011-2013"

    if year <= 2016:
        return "2014-2016"

    if year <= 2019:
        return "2017-2019"

    if year <= 2021:
        return "2020-2021"

    if year <= 2023:
        return "2022-2023"

    return "2024+"


def build_era_summary(ep):

    x = ep.copy()

    x["era"] = (
        x["year"]
        .apply(assign_era)
    )

    rows = []

    for era, g in x.groupby(
        "era",
        sort=False,
    ):

        rows.append(
            {
                "era":
                    era,

                "episodes":
                    len(g),

                "static_total_return":
                    float(
                        g[
                            "total_return__STATIC_FULL"
                        ].sum()
                    ),

                "ramp2_total_return":
                    float(
                        g[
                            "total_return__RAMP_2"
                        ].sum()
                    ),

                "ramp3_total_return":
                    float(
                        g[
                            "total_return__RAMP_3"
                        ].sum()
                    ),

                "ramp3_return_delta_vs_static":
                    float(
                        g[
                            "return_delta_ramp3_vs_static"
                        ].sum()
                    ),

                "static_worst_mdd":
                    float(
                        g[
                            "mdd__STATIC_FULL"
                        ].min()
                    ),

                "ramp2_worst_mdd":
                    float(
                        g[
                            "mdd__RAMP_2"
                        ].min()
                    ),

                "ramp3_worst_mdd":
                    float(
                        g[
                            "mdd__RAMP_3"
                        ].min()
                    ),

                "ramp3_return_win_rate":
                    float(
                        g[
                            "ramp3_return_win_vs_static"
                        ].mean()
                    ),

                "ramp3_mdd_win_rate":
                    float(
                        g[
                            "ramp3_mdd_win_vs_static"
                        ].mean()
                    ),

                "ramp3_joint_win_rate":
                    float(
                        g[
                            "ramp3_joint_win_vs_static"
                        ].mean()
                    ),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# Leave-One-Episode-Out
# ============================================================

def build_leave_one_out(ep):

    rows = []

    episode_ids = (
        ep["episode_id"]
        .dropna()
        .unique()
    )

    for episode_id in episode_ids:

        g = ep[
            ep["episode_id"]
            != episode_id
        ].copy()

        removed = ep[
            ep["episode_id"]
            == episode_id
        ].iloc[0]

        static_total = float(
            g[
                "total_return__STATIC_FULL"
            ].sum()
        )

        ramp2_total = float(
            g[
                "total_return__RAMP_2"
            ].sum()
        )

        ramp3_total = float(
            g[
                "total_return__RAMP_3"
            ].sum()
        )

        static_worst = float(
            g[
                "mdd__STATIC_FULL"
            ].min()
        )

        ramp3_worst = float(
            g[
                "mdd__RAMP_3"
            ].min()
        )

        rows.append(
            {
                "removed_episode_id":
                    episode_id,

                "removed_release_date":
                    removed["release_date"],

                "removed_diagnosis":
                    removed["diagnosis"],

                "remaining_episodes":
                    len(g),

                "static_total_return":
                    static_total,

                "ramp2_total_return":
                    ramp2_total,

                "ramp3_total_return":
                    ramp3_total,

                "ramp3_delta_vs_static":
                    ramp3_total
                    - static_total,

                "static_worst_mdd":
                    static_worst,

                "ramp3_worst_mdd":
                    ramp3_worst,

                "ramp3_worst_mdd_improvement":
                    ramp3_worst
                    - static_worst,

                "ramp3_still_return_better":
                    ramp3_total
                    > static_total,

                "ramp3_still_mdd_better":
                    ramp3_worst
                    > static_worst,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# Overall Summary
# ============================================================

def build_summary(ep, loo):

    rows = []

    for path in PATHS:

        returns = ep[
            f"total_return__{path}"
        ]

        mdds = ep[
            f"mdd__{path}"
        ]

        rows.append(
            {
                "path":
                    path,

                "episodes":
                    len(ep),

                "positive_episodes":
                    int(
                        (returns > 0).sum()
                    ),

                "negative_episodes":
                    int(
                        (returns < 0).sum()
                    ),

                "total_episode_return":
                    float(
                        returns.sum()
                    ),

                "avg_episode_return":
                    float(
                        returns.mean()
                    ),

                "median_episode_return":
                    float(
                        returns.median()
                    ),

                "avg_mdd":
                    float(
                        mdds.mean()
                    ),

                "worst_mdd":
                    float(
                        mdds.min()
                    ),
            }
        )

    summary = pd.DataFrame(rows)

    # 추가 robustness metrics를 RAMP_3 행에만 기록
    mask = (
        summary["path"]
        == "RAMP_3"
    )

    summary.loc[
        mask,
        "return_win_rate_vs_static"
    ] = float(
        ep[
            "ramp3_return_win_vs_static"
        ].mean()
    )

    summary.loc[
        mask,
        "mdd_win_rate_vs_static"
    ] = float(
        ep[
            "ramp3_mdd_win_vs_static"
        ].mean()
    )

    summary.loc[
        mask,
        "joint_win_rate_vs_static"
    ] = float(
        ep[
            "ramp3_joint_win_vs_static"
        ].mean()
    )

    summary.loc[
        mask,
        "loo_return_pass_rate"
    ] = float(
        loo[
            "ramp3_still_return_better"
        ].mean()
    )

    summary.loc[
        mask,
        "loo_mdd_pass_rate"
    ] = float(
        loo[
            "ramp3_still_mdd_better"
        ].mean()
    )

    return summary


# ============================================================
# 2008 Exclusion
# ============================================================

def build_2008_exclusion(ep):

    # 기존 결과에서 timing-risk episode가 2008 episode 1이었지만,
    # ID를 하드코딩하지 않고 release year로 식별한다.
    without_2008 = ep[
        ep["year"] != 2008
    ].copy()

    if without_2008.empty:
        return None

    result = {
        "episodes":
            len(without_2008),

        "static_total_return":
            float(
                without_2008[
                    "total_return__STATIC_FULL"
                ].sum()
            ),

        "ramp2_total_return":
            float(
                without_2008[
                    "total_return__RAMP_2"
                ].sum()
            ),

        "ramp3_total_return":
            float(
                without_2008[
                    "total_return__RAMP_3"
                ].sum()
            ),

        "static_worst_mdd":
            float(
                without_2008[
                    "mdd__STATIC_FULL"
                ].min()
            ),

        "ramp3_worst_mdd":
            float(
                without_2008[
                    "mdd__RAMP_3"
                ].min()
            ),
    }

    result[
        "ramp3_return_delta_vs_static"
    ] = (
        result["ramp3_total_return"]
        - result["static_total_return"]
    )

    result[
        "ramp3_mdd_improvement"
    ] = (
        result["ramp3_worst_mdd"]
        - result["static_worst_mdd"]
    )

    return result


# ============================================================
# Diagnosis Robustness
# ============================================================

def build_diagnosis_summary(ep):

    rows = []

    for diagnosis, g in ep.groupby(
        "diagnosis"
    ):

        rows.append(
            {
                "diagnosis":
                    diagnosis,

                "episodes":
                    len(g),

                "static_total_return":
                    float(
                        g[
                            "total_return__STATIC_FULL"
                        ].sum()
                    ),

                "ramp3_total_return":
                    float(
                        g[
                            "total_return__RAMP_3"
                        ].sum()
                    ),

                "ramp3_delta":
                    float(
                        g[
                            "return_delta_ramp3_vs_static"
                        ].sum()
                    ),

                "static_worst_mdd":
                    float(
                        g[
                            "mdd__STATIC_FULL"
                        ].min()
                    ),

                "ramp3_worst_mdd":
                    float(
                        g[
                            "mdd__RAMP_3"
                        ].min()
                    ),

                "return_win_rate":
                    float(
                        g[
                            "ramp3_return_win_vs_static"
                        ].mean()
                    ),

                "mdd_win_rate":
                    float(
                        g[
                            "ramp3_mdd_win_vs_static"
                        ].mean()
                    ),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# Main
# ============================================================

def main():

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw = load_data()

    episode = (
        build_episode_comparison(
            raw
        )
    )

    era = build_era_summary(
        episode
    )

    loo = build_leave_one_out(
        episode
    )

    summary = build_summary(
        episode,
        loo,
    )

    diagnosis = (
        build_diagnosis_summary(
            episode
        )
    )

    exclusion = (
        build_2008_exclusion(
            episode
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    episode.to_csv(
        OUT_EPISODE,
        index=False,
    )

    era.to_csv(
        OUT_ERA,
        index=False,
    )

    loo.to_csv(
        OUT_LOO,
        index=False,
    )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
    )

    # --------------------------------------------------------
    # Robustness diagnostics
    # --------------------------------------------------------

    ramp3_return_win_rate = float(
        episode[
            "ramp3_return_win_vs_static"
        ].mean()
    )

    ramp3_mdd_win_rate = float(
        episode[
            "ramp3_mdd_win_vs_static"
        ].mean()
    )

    ramp3_joint_win_rate = float(
        episode[
            "ramp3_joint_win_vs_static"
        ].mean()
    )

    loo_return_pass = float(
        loo[
            "ramp3_still_return_better"
        ].mean()
    )

    loo_mdd_pass = float(
        loo[
            "ramp3_still_mdd_better"
        ].mean()
    )

    worst_return_delta = float(
        episode[
            "return_delta_ramp3_vs_static"
        ].min()
    )

    best_return_delta = float(
        episode[
            "return_delta_ramp3_vs_static"
        ].max()
    )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    lines = []

    lines.append(
        "=" * 78
    )

    lines.append(
        "FILTER15 STAGED RESTORATION ROBUSTNESS AUDIT"
    )

    lines.append(
        "=" * 78
    )

    lines.append("")

    lines.append(
        f"Episodes                    : {len(episode)}"
    )

    lines.append(
        "Compared                    : STATIC_FULL / RAMP_2 / RAMP_3"
    )

    lines.append(
        "Primary Candidate           : RAMP_3"
    )

    lines.append(
        "Production Modified         : NO"
    )

    lines.append(
        "New Indicator               : NO"
    )

    lines.append(
        "New Threshold               : NO"
    )

    lines.append(
        "Parameter Optimization      : NO"
    )

    lines.append(
        "Future Data Added           : NO"
    )

    lines.append("")

    lines.append(
        "===== OVERALL ====="
    )

    lines.append(
        summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "===== RAMP_3 EPISODE-LEVEL ROBUSTNESS ====="
    )

    lines.append(
        f"Return Win Rate vs STATIC : "
        f"{ramp3_return_win_rate:.2%}"
    )

    lines.append(
        f"MDD Win Rate vs STATIC    : "
        f"{ramp3_mdd_win_rate:.2%}"
    )

    lines.append(
        f"Joint Win Rate            : "
        f"{ramp3_joint_win_rate:.2%}"
    )

    lines.append(
        f"Worst Return Delta        : "
        f"{pct(worst_return_delta)}"
    )

    lines.append(
        f"Best Return Delta         : "
        f"{pct(best_return_delta)}"
    )

    lines.append("")

    lines.append(
        "===== LEAVE-ONE-EPISODE-OUT ====="
    )

    lines.append(
        f"Return Conclusion Survives : "
        f"{loo_return_pass:.2%}"
    )

    lines.append(
        f"MDD Conclusion Survives    : "
        f"{loo_mdd_pass:.2%}"
    )

    lines.append("")

    lines.append(
        "===== ERA ROBUSTNESS ====="
    )

    lines.append(
        era.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "===== DIAGNOSIS ROBUSTNESS ====="
    )

    lines.append(
        diagnosis.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "===== EXCLUDING 2008 ====="
    )

    if exclusion is None:

        lines.append(
            "2008 exclusion result unavailable."
        )

    else:

        lines.append(
            f"Episodes             : "
            f"{exclusion['episodes']}"
        )

        lines.append(
            f"STATIC Total Return  : "
            f"{pct(exclusion['static_total_return'])}"
        )

        lines.append(
            f"RAMP_2 Total Return  : "
            f"{pct(exclusion['ramp2_total_return'])}"
        )

        lines.append(
            f"RAMP_3 Total Return  : "
            f"{pct(exclusion['ramp3_total_return'])}"
        )

        lines.append(
            f"RAMP_3 Return Delta  : "
            f"{pct(exclusion['ramp3_return_delta_vs_static'])}"
        )

        lines.append(
            f"STATIC Worst MDD     : "
            f"{pct(exclusion['static_worst_mdd'])}"
        )

        lines.append(
            f"RAMP_3 Worst MDD     : "
            f"{pct(exclusion['ramp3_worst_mdd'])}"
        )

        lines.append(
            f"MDD Improvement      : "
            f"{pct(exclusion['ramp3_mdd_improvement'])}"
        )

    lines.append("")

    lines.append(
        "===== WORST RAMP_3 TRADE-OFF EPISODES ====="
    )

    worst = (
        episode
        .sort_values(
            "return_delta_ramp3_vs_static",
            ascending=True,
        )
        .head(10)
    )

    worst_cols = [
        "episode_id",
        "release_date",
        "diagnosis",
        "total_return__STATIC_FULL",
        "total_return__RAMP_3",
        "return_delta_ramp3_vs_static",
        "mdd__STATIC_FULL",
        "mdd__RAMP_3",
        "mdd_improvement_ramp3_vs_static",
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
        "판정 원칙"
    )

    lines.append(
        "=" * 78
    )

    lines.append("")

    lines.append(
        "1. 2008을 제거해도 RAMP_3의 방향성이 유지되어야 한다."
    )

    lines.append("")

    lines.append(
        "2. Leave-One-Episode-Out에서 특정 episode 하나를 제거했을 때 "
        "결론이 뒤집히면 robustness가 부족하다."
    )

    lines.append("")

    lines.append(
        "3. 전체 평균만 보지 않고 episode별 return/MDD win rate를 함께 본다."
    )

    lines.append("")

    lines.append(
        "4. 일부 정상 recovery에서 수익을 희생하는 것은 가능하지만 "
        "손실이 소수 episode에 과도하게 집중되는지 확인한다."
    )

    lines.append("")

    lines.append(
        "5. 이번 Audit에서는 25/50/100 parameter를 변경하지 않는다. "
        "Sensitivity는 별도 Gate다."
    )

    lines.append("")

    lines.append(
        "6. Robustness를 통과해도 Production 변경은 아직 승인하지 않는다."
    )

    lines.append("")

    lines.append(
        "PRODUCTION DECISION: NO CHANGE"
    )

    lines.append(
        "NEXT GATE: PARAMETER SENSITIVITY"
    )

    text = "\n".join(
        lines
    )

    OUT_TXT.write_text(
        text,
        encoding="utf-8",
    )

    print()
    print(text)
    print()

    print(
        f"Saved: {OUT_EPISODE}"
    )

    print(
        f"Saved: {OUT_ERA}"
    )

    print(
        f"Saved: {OUT_LOO}"
    )

    print(
        f"Saved: {OUT_SUMMARY}"
    )

    print(
        f"Saved: {OUT_TXT}"
    )


if __name__ == "__main__":
    main()