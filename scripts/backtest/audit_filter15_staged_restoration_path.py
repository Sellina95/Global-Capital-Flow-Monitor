from __future__ import annotations

"""
FILTER15 STAGED RESTORATION PATH COUNTERFACTUAL

연구 질문
---------
Deadman 이후 recovery candidate가 발생했을 때:

A. 즉시 FULL 복원
B. 2단계 복원
C. 3단계 복원

중 어느 방식이 정상 recovery 참여를 지나치게 희생하지 않으면서
false recovery의 tail risk를 줄이는가?

State Machine
-------------
STATIC_FULL
    candidate -> 100%

RAMP_2
    candidate day 1 -> 50%
    candidate가 다음 거래일까지 유지 -> 100%
    candidate 깨짐 -> 0%

RAMP_3
    candidate day 1 -> 25%
    candidate 2일 연속 -> 50%
    candidate 3일 연속 -> 100%
    candidate 깨짐 -> 0%

주의
----
여기서 25/50/100 및 50/100은 Production parameter가 아니다.
단순하고 해석 가능한 research counterfactual이다.

Release Candidate
-----------------
기존 연구에서 사용한:

    HY_FALLING_VIX_LT_30

즉:
    HY OAS가 전일보다 하락
    AND
    VIX < 30

새 release indicator나 새로운 threshold를 추가하지 않는다.

원칙
----
- Production 수정 금지
- master_panel PIT data만 사용
- signal t -> return t+1
- 미래 데이터 backfill 금지
- parameter optimization 금지
- 기존 candidate 정의 유지
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

MASTER_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

EPISODE_PATH = (
    RESULT_DIR
    / "filter15_release_failure_analysis.csv"
)

OUT_DAILY = (
    RESULT_DIR
    / "filter15_staged_restoration_daily.csv"
)

OUT_EPISODE = (
    RESULT_DIR
    / "filter15_staged_restoration_episodes.csv"
)

OUT_SUMMARY = (
    RESULT_DIR
    / "filter15_staged_restoration_summary.csv"
)

OUT_TXT = (
    RESULT_DIR
    / "filter15_staged_restoration_audit.txt"
)


PATHS = {
    "STATIC_FULL": [1.00],
    "RAMP_2": [0.50, 1.00],
    "RAMP_3": [0.25, 0.50, 1.00],
}


# ============================================================
# Helpers
# ============================================================

def num(x):
    return pd.to_numeric(
        x,
        errors="coerce",
    )


def compounded_return(
    returns: pd.Series,
) -> float:

    r = num(returns).fillna(0.0)

    if r.empty:
        return 0.0

    return float(
        (1.0 + r).prod() - 1.0
    )


def max_drawdown(
    returns: pd.Series,
) -> float:

    r = num(returns).fillna(0.0)

    if r.empty:
        return 0.0

    wealth = (
        1.0 + r
    ).cumprod()

    peak = wealth.cummax()

    dd = (
        wealth / peak
        - 1.0
    )

    return float(dd.min())


# ============================================================
# Master Panel
# ============================================================

def load_master():

    if not MASTER_PATH.exists():
        raise FileNotFoundError(
            MASTER_PATH
        )

    df = pd.read_csv(
        MASTER_PATH
    )

    required = [
        "signal_date",
        "execution_date",
        "SPY",
        "VIX",
        "credit__HY_OAS",
    ]

    missing = [
        c
        for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"master_panel missing columns: {missing}"
        )

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )

    df["execution_date"] = pd.to_datetime(
        df["execution_date"],
        errors="coerce",
    )

    for col in [
        "SPY",
        "VIX",
        "credit__HY_OAS",
    ]:
        df[col] = num(df[col])

    df = (
        df
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Signal t -> Return t+1
    #
    # 미래 수익률은 평가에만 사용.
    # candidate 생성에는 절대 사용하지 않음.
    # --------------------------------------------------------

    df["spy_return_t1"] = (
        df["SPY"].shift(-1)
        / df["SPY"]
        - 1.0
    )

    # --------------------------------------------------------
    # Existing recovery candidate
    #
    # HY_FALLING_VIX_LT_30
    #
    # 현재와 과거 정보만 사용.
    # --------------------------------------------------------

    df["hy_change_1d"] = (
        df["credit__HY_OAS"].diff()
    )

    df["release_candidate"] = (
        (df["hy_change_1d"] < 0)
        &
        (df["VIX"] < 30.0)
    )

    return df


# ============================================================
# Episodes
# ============================================================

def load_episodes():

    if not EPISODE_PATH.exists():
        raise FileNotFoundError(
            f"{EPISODE_PATH}\n"
            "먼저 release failure analysis를 실행하세요."
        )

    df = pd.read_csv(
        EPISODE_PATH
    )

    required = [
        "episode_id",
        "release_date",
        "rows_released_early",
        "diagnosis",
    ]

    missing = [
        c
        for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"episode file missing columns: {missing}"
        )

    df["release_date"] = pd.to_datetime(
        df["release_date"],
        errors="coerce",
    )

    df["rows_released_early"] = num(
        df["rows_released_early"]
    )

    df["diagnosis"] = (
        df["diagnosis"]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
    )

    # 실제 조기 release candidate가 있었던 episode만
    df = df[
        df["release_date"].notna()
        &
        (df["rows_released_early"] > 0)
    ].copy()

    return df


# ============================================================
# Exposure Base
# ============================================================

def resolve_candidate_exposure(
    episode: pd.Series,
) -> float:

    """
    이전 연구 artifact에서 release 당시의
    Filter15 candidate exposure를 찾는다.

    Filter13 risk budget으로 대체하지 않는다.
    """

    candidates = [
        "release_full_exposure",
    ]

    for col in candidates:

        if col not in episode.index:
            continue

        value = num(
            pd.Series(
                [episode[col]]
            )
        ).iloc[0]

        if pd.notna(value):
            return float(value)

    raise ValueError(
        "\nRelease episode artifact에 candidate Filter15 exposure가 없습니다.\n"
        "Filter13 budget을 대신 사용하면 contract가 깨지므로 중단합니다.\n\n"
        f"Episode: {episode.get('episode_id')}\n"
        "필요 후보 컬럼:\n"
        + "\n".join(
            f"- {x}"
            for x in candidates
        )
    )


# ============================================================
# State Machine
# ============================================================

def simulate_path(
    window: pd.DataFrame,
    candidate_exposure: float,
    path_name: str,
):

    stages = PATHS[path_name]

    stage_index = 0
    consecutive_candidate = 0

    rows = []

    for _, day in window.iterrows():

        candidate = bool(
            day["release_candidate"]
        )

        # ----------------------------------------------------
        # Re-brake
        #
        # candidate가 깨지는 순간 exposure = 0.
        # confirmation streak도 reset.
        # ----------------------------------------------------

        if not candidate:

            consecutive_candidate = 0
            stage_index = 0
            multiplier = 0.0
            state = "RE_BRAKE"

        else:

            consecutive_candidate += 1

            # -----------------------------------------------
            # STATIC_FULL
            # -----------------------------------------------

            if path_name == "STATIC_FULL":

                multiplier = 1.0
                state = "FULL"

            # -----------------------------------------------
            # RAMP
            #
            # candidate가 연속 유지될 때만 다음 단계로 이동.
            # 미래를 미리 보지 않는다.
            # -----------------------------------------------

            else:

                stage_index = min(
                    consecutive_candidate - 1,
                    len(stages) - 1,
                )

                multiplier = (
                    stages[stage_index]
                )

                if multiplier >= 1.0:
                    state = "FULL"
                else:
                    state = (
                        f"RAMP_{int(multiplier * 100)}"
                    )

        exposure = (
            candidate_exposure
            * multiplier
        )

        market_return = day[
            "spy_return_t1"
        ]

        if pd.isna(market_return):
            strategy_return = np.nan
        else:
            strategy_return = (
                exposure
                / 100.0
                * market_return
            )

        rows.append(
            {
                "signal_date":
                    day["signal_date"],

                "execution_date":
                    day["execution_date"],

                "path":
                    path_name,

                "candidate":
                    candidate,

                "candidate_streak":
                    consecutive_candidate,

                "state":
                    state,

                "multiplier":
                    multiplier,

                "candidate_exposure":
                    candidate_exposure,

                "counterfactual_exposure":
                    exposure,

                "spy_return_t1":
                    market_return,

                "counterfactual_return":
                    strategy_return,
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# Episode Simulation
# ============================================================

def simulate_episode(
    master: pd.DataFrame,
    episode: pd.Series,
):

    release_date = episode[
        "release_date"
    ]

    rows_early = int(
        episode[
            "rows_released_early"
        ]
    )

    matches = master.index[
        master["signal_date"]
        == release_date
    ].tolist()

    if not matches:
        raise ValueError(
            f"release_date missing from master panel: "
            f"{release_date.date()}"
        )

    start = matches[0]

    end = min(
        start + rows_early - 1,
        len(master) - 1,
    )

    window = (
        master
        .loc[start:end]
        .copy()
    )

    candidate_exposure = (
        resolve_candidate_exposure(
            episode
        )
    )

    daily_outputs = []
    episode_outputs = []

    for path_name in PATHS:

        sim = simulate_path(
            window=window,
            candidate_exposure=candidate_exposure,
            path_name=path_name,
        )

        sim.insert(
            0,
            "episode_id",
            episode["episode_id"],
        )

        sim.insert(
            1,
            "diagnosis",
            episode["diagnosis"],
        )

        daily_outputs.append(
            sim
        )

        returns = sim[
            "counterfactual_return"
        ]

        total_return = (
            compounded_return(
                returns
            )
        )

        mdd = max_drawdown(
            returns
        )

        invested_days = int(
            (
                sim[
                    "counterfactual_exposure"
                ]
                > 0
            ).sum()
        )

        full_days = int(
            (
                sim["multiplier"]
                >= 1.0
            ).sum()
        )

        rebrake_days = int(
            (
                sim["state"]
                == "RE_BRAKE"
            ).sum()
        )

        avg_exposure = float(
            sim[
                "counterfactual_exposure"
            ].mean()
        )

        episode_outputs.append(
            {
                "episode_id":
                    episode["episode_id"],

                "diagnosis":
                    episode["diagnosis"],

                "release_date":
                    release_date,

                "rows_released_early":
                    rows_early,

                "candidate_exposure":
                    candidate_exposure,

                "path":
                    path_name,

                "total_return":
                    total_return,

                "mdd":
                    mdd,

                "invested_days":
                    invested_days,

                "full_days":
                    full_days,

                "rebrake_days":
                    rebrake_days,

                "avg_exposure":
                    avg_exposure,
            }
        )

    return (
        pd.concat(
            daily_outputs,
            ignore_index=True,
        ),
        pd.DataFrame(
            episode_outputs
        ),
    )


# ============================================================
# Summary
# ============================================================

def build_summary(
    episode_df: pd.DataFrame,
):

    rows = []

    for path_name in PATHS:

        g = episode_df[
            episode_df["path"]
            == path_name
        ]

        r = num(
            g["total_return"]
        )

        mdd = num(
            g["mdd"]
        )

        rows.append(
            {
                "path":
                    path_name,

                "episodes":
                    len(g),

                "positive_episodes":
                    int((r > 0).sum()),

                "negative_episodes":
                    int((r < 0).sum()),

                "flat_episodes":
                    int((r == 0).sum()),

                "total_episode_return":
                    float(r.sum()),

                "avg_episode_return":
                    float(r.mean()),

                "median_episode_return":
                    float(r.median()),

                "avg_mdd":
                    float(mdd.mean()),

                "worst_mdd":
                    float(mdd.min()),

                "avg_exposure":
                    float(
                        num(
                            g["avg_exposure"]
                        ).mean()
                    ),

                "avg_invested_days":
                    float(
                        num(
                            g["invested_days"]
                        ).mean()
                    ),

                "avg_full_days":
                    float(
                        num(
                            g["full_days"]
                        ).mean()
                    ),

                "avg_rebrake_days":
                    float(
                        num(
                            g["rebrake_days"]
                        ).mean()
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

    master = load_master()
    episodes = load_episodes()

    daily_frames = []
    episode_frames = []

    for _, episode in episodes.iterrows():

        daily, episode_result = (
            simulate_episode(
                master,
                episode,
            )
        )

        daily_frames.append(
            daily
        )

        episode_frames.append(
            episode_result
        )

    daily_df = pd.concat(
        daily_frames,
        ignore_index=True,
    )

    episode_df = pd.concat(
        episode_frames,
        ignore_index=True,
    )

    summary_df = build_summary(
        episode_df
    )

    daily_df.to_csv(
        OUT_DAILY,
        index=False,
    )

    episode_df.to_csv(
        OUT_EPISODE,
        index=False,
    )

    summary_df.to_csv(
        OUT_SUMMARY,
        index=False,
    )

    # ========================================================
    # 2008 timing-risk comparison
    # ========================================================

    timing = episode_df[
        episode_df["diagnosis"]
        == "TIMING_RISK"
    ]

    successful = episode_df[
        episode_df["diagnosis"]
        == "SUCCESSFUL_RELEASE"
    ]

    # Successful recovery only summary
    success_summary = (
        successful
        .groupby("path")
        .agg(
            episodes=(
                "episode_id",
                "count",
            ),
            avg_return=(
                "total_return",
                "mean",
            ),
            median_return=(
                "total_return",
                "median",
            ),
            avg_mdd=(
                "mdd",
                "mean",
            ),
            worst_mdd=(
                "mdd",
                "min",
            ),
            avg_exposure=(
                "avg_exposure",
                "mean",
            ),
        )
        .reset_index()
    )

    # ========================================================
    # Report
    # ========================================================

    lines = []

    lines.append(
        "=" * 78
    )

    lines.append(
        "FILTER15 STAGED RESTORATION PATH AUDIT"
    )

    lines.append(
        "=" * 78
    )

    lines.append("")

    lines.append(
        f"Release Episodes      : {episodes['episode_id'].nunique()}"
    )

    lines.append(
        "Candidate             : HY_FALLING_VIX_LT_30"
    )

    lines.append(
        "Paths                 : STATIC_FULL / RAMP_2 / RAMP_3"
    )

    lines.append(
        "Re-brake              : candidate breaks -> 0%"
    )

    lines.append(
        "Execution             : SIGNAL t -> RETURN t+1"
    )

    lines.append(
        "PIT Source            : master_panel.csv"
    )

    lines.append(
        "Production Modified   : NO"
    )

    lines.append(
        "Future Data in Signal : NO"
    )

    lines.append(
        "New Indicator         : NO"
    )

    lines.append(
        "Threshold Optimization: NO"
    )

    lines.append("")

    lines.append(
        "===== ALL EPISODES ====="
    )

    lines.append(
        summary_df.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "===== SUCCESSFUL RECOVERY ONLY ====="
    )

    lines.append(
        success_summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "===== TIMING RISK / 2008 ====="
    )

    if timing.empty:

        lines.append(
            "No TIMING_RISK episode."
        )

    else:

        timing_cols = [
            "episode_id",
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

        lines.append(
            timing[
                timing_cols
            ].to_string(
                index=False
            )
        )

    lines.append("")

    lines.append(
        "=" * 78
    )

    lines.append(
        "판정 질문"
    )

    lines.append(
        "=" * 78
    )

    lines.append("")

    lines.append(
        "1. RAMP_2/RAMP_3가 STATIC_FULL 대비 2008 MDD를 "
        "실질적으로 줄이는가?"
    )

    lines.append("")

    lines.append(
        "2. successful recovery에서는 STATIC_FULL의 upside를 "
        "대부분 유지하는가?"
    )

    lines.append("")

    lines.append(
        "3. re-brake가 false stabilization에서 실제로 작동하는가?"
    )

    lines.append("")

    lines.append(
        "4. RAMP_3가 RAMP_2보다 복잡성 증가에 상응하는 "
        "추가적인 tail protection을 제공하는가?"
    )

    lines.append("")

    lines.append(
        "5. 단 하나의 2008 episode에 최적화된 결과라면 "
        "Production 후보로 승격하지 않는다."
    )

    lines.append("")

    lines.append(
        "6. 가장 단순한 robust path를 우선한다."
    )

    lines.append("")

    lines.append(
        "PRODUCTION DECISION: NO CHANGE"
    )

    lines.append(
        "NEXT GATE: ROBUSTNESS / EPISODE-LEVEL VALIDATION"
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
        f"Saved: {OUT_DAILY}"
    )

    print(
        f"Saved: {OUT_EPISODE}"
    )

    print(
        f"Saved: {OUT_SUMMARY}"
    )

    print(
        f"Saved: {OUT_TXT}"
    )


if __name__ == "__main__":
    main()