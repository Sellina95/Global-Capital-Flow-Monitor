from __future__ import annotations

"""
FILTER15 STAGED RE-RISKING COUNTERFACTUAL

목적
----
Deadman 이후 recovery candidate가 발생했을 때
Production처럼 즉시 정상 exposure를 복원하는 대신,
초기 exposure sizing을 줄이면 false recovery tail risk를
얼마나 줄일 수 있는지 검증한다.

비교
----
FULL    : Production recovery exposure 100%
HALF    : Production recovery exposure 50%
QUARTER : Production recovery exposure 25%

중요
----
이번 단계에서는 새로운 release threshold를 만들지 않는다.
기존 HY_FALLING_VIX_LT_30 candidate의 release date를 그대로 사용한다.

각 candidate release 이후 Production deadman이 실제로 끝나는 날까지
counterfactual sizing을 적용한다.

원칙
----
- Production 수정 금지
- 미래 데이터로 signal 생성 금지
- signal t -> return t+1
- 기존 release candidate 그대로 사용
- 새로운 indicator 없음
- threshold optimization 없음
- sizing effect만 분리
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

PARITY_PATH = (
    RESULT_DIR
    / "filter15_exact_parity_daily.csv"
)

EPISODE_PATH = (
    RESULT_DIR
    / "filter15_release_failure_analysis.csv"
)

OUT_DAILY = (
    RESULT_DIR
    / "filter15_staged_rerisk_daily.csv"
)

OUT_EPISODES = (
    RESULT_DIR
    / "filter15_staged_rerisk_episodes.csv"
)

OUT_SUMMARY = (
    RESULT_DIR
    / "filter15_staged_rerisk_summary.csv"
)

OUT_TXT = (
    RESULT_DIR
    / "filter15_staged_rerisk_audit.txt"
)


SIZINGS = {
    "FULL": 1.00,
    "HALF": 0.50,
    "QUARTER": 0.25,
}


# ============================================================
# Helpers
# ============================================================

def numeric(series):
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def first_existing(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:

    for col in candidates:
        if col in df.columns:
            return col

    return None


def compounded_return(
    returns: pd.Series,
) -> float:

    r = numeric(
        returns
    ).fillna(0.0)

    if r.empty:
        return 0.0

    return float(
        (1.0 + r).prod() - 1.0
    )


def max_drawdown(
    returns: pd.Series,
) -> float:

    r = numeric(
        returns
    ).fillna(0.0)

    if r.empty:
        return 0.0

    wealth = (
        1.0 + r
    ).cumprod()

    peak = wealth.cummax()

    dd = (
        wealth / peak
    ) - 1.0

    return float(
        dd.min()
    )


# ============================================================
# Load Master Panel
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
    ]

    missing = [
        col
        for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            "master_panel missing: "
            + str(missing)
        )

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )

    df["execution_date"] = pd.to_datetime(
        df["execution_date"],
        errors="coerce",
    )

    df["SPY"] = numeric(
        df["SPY"]
    )

    df = (
        df
        .dropna(
            subset=["signal_date"]
        )
        .sort_values("signal_date")
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # IMPORTANT
    #
    # signal t에서 정한 exposure는 다음 거래일 수익률에 적용.
    #
    # 따라서 signal row t에서 필요한 return은
    # SPY(t+1) / SPY(t) - 1
    #
    # shift(-1)은 성과 측정용일 뿐,
    # signal 생성에는 사용하지 않는다.
    # --------------------------------------------------------

    df["spy_return_t1"] = (
        df["SPY"].shift(-1)
        / df["SPY"]
        - 1.0
    )

    return df


# ============================================================
# Load Filter15 Exact Parity
# ============================================================

def load_parity():

    if not PARITY_PATH.exists():
        raise FileNotFoundError(
            PARITY_PATH
        )

    df = pd.read_csv(
        PARITY_PATH
    )

    if "signal_date" not in df.columns:
        raise ValueError(
            "Parity file missing signal_date"
        )

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )

    exposure_col = first_existing(
        df,
        [
            "actual_exposure_15",
            "exposure_15",
            "recommended_exposure",
        ],
    )

    deadman_col = first_existing(
        df,
        [
            "hard_deadman",
            "oracle_hard_deadman",
        ],
    )

    if exposure_col is None:
        raise ValueError(
            "Filter15 production exposure column not found."
        )

    df["_production_exposure"] = numeric(
        df[exposure_col]
    )

    if deadman_col is not None:

        raw = df[
            deadman_col
        ]

        if raw.dtype == bool:

            df["_hard_deadman"] = raw

        else:

            df["_hard_deadman"] = (
                raw
                .fillna(False)
                .astype(str)
                .str.upper()
                .isin(
                    [
                        "TRUE",
                        "1",
                        "YES",
                    ]
                )
            )

        deadman_source = (
            f"PARITY:{deadman_col}"
        )

    else:

        # Production exposure가 0이라는 이유만으로
        # hard deadman이라고 추론하면 안 되므로
        # fallback하지 않는다.
        raise ValueError(
            "Exact parity file에 hard_deadman 상태가 없습니다.\n"
            "0 exposure를 deadman으로 임의 해석하지 않습니다."
        )

    keep = [
        "signal_date",
        "_production_exposure",
        "_hard_deadman",
    ]

    return (
        df[keep]
        .dropna(
            subset=["signal_date"]
        )
        .drop_duplicates(
            "signal_date",
            keep="last",
        ),
        exposure_col,
        deadman_source,
    )


# ============================================================
# Load Previously Validated Release Candidates
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
        col
        for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            "release failure file missing: "
            + str(missing)
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

    df["rows_released_early"] = numeric(
        df["rows_released_early"]
    )

    # Candidate가 실제 release된 episode만 사용.
    df = df[
        df["release_date"].notna()
        & (
            df["rows_released_early"]
            > 0
        )
    ].copy()

    return df


# ============================================================
# Build Combined Daily Panel
# ============================================================

def build_panel(
    master,
    parity,
):

    df = master.merge(
        parity,
        on="signal_date",
        how="left",
        validate="one_to_one",
    )

    return df


# ============================================================
# Counterfactual Episode
# ============================================================

def simulate_episode(
    panel: pd.DataFrame,
    episode: pd.Series,
):

    release_date = (
        episode["release_date"]
    )

    rows_early = int(
        episode[
            "rows_released_early"
        ]
    )

    # --------------------------------------------------------
    # release_date부터 Production release 직전까지가
    # 기존 candidate가 "일찍 풀려고 했던 구간".
    #
    # 기존 failure analysis가 계산한 rows_released_early를
    # 그대로 사용한다.
    #
    # 새로운 종료 조건을 만들지 않는다.
    # --------------------------------------------------------

    start_matches = panel.index[
        panel["signal_date"]
        == release_date
    ].tolist()

    if not start_matches:
        raise ValueError(
            f"release_date missing from panel: "
            f"{release_date.date()}"
        )

    start_idx = start_matches[0]

    end_idx = (
        start_idx
        + rows_early
        - 1
    )

    if end_idx >= len(panel):
        end_idx = len(panel) - 1

    window = (
        panel
        .loc[
            start_idx:end_idx
        ]
        .copy()
    )

    if window.empty:
        return [], []

    daily_rows = []
    episode_rows = []

    # --------------------------------------------------------
    # Baseline
    #
    # Production deadman exposure는 이 구간에서 0이어야 하는 게
    # 원래 counterfactual 정의.
    #
    # 하지만 무조건 가정하지 않고 실제 값을 기록한다.
    # --------------------------------------------------------

    baseline_returns = (
        numeric(
            window[
                "_production_exposure"
            ]
        )
        / 100.0
        * numeric(
            window[
                "spy_return_t1"
            ]
        )
    )

    baseline_total = compounded_return(
        baseline_returns
    )

    baseline_mdd = max_drawdown(
        baseline_returns
    )

    # --------------------------------------------------------
    # Sizing variants
    # --------------------------------------------------------

    for sizing_name, multiplier in SIZINGS.items():

        # Counterfactual은 "정상 Filter15 exposure의 multiplier"
        # 를 적용한다.
        #
        # release failure analysis에서 FULL/HALF/QUARTER가
        # 의미했던 sizing decomposition을 그대로 유지한다.
        #
        # Production exposure가 deadman으로 0인 구간이므로
        # episode 파일에 저장된 release candidate exposure를
        # 우선 찾는다.
        candidate_exposure = None

        for candidate_col in [
            "release_exposure",
            "candidate_exposure",
            "next_exposure_15",
            "release_exposure_15",
        ]:

            if candidate_col in episode.index:

                value = pd.to_numeric(
                    episode[
                        candidate_col
                    ],
                    errors="coerce",
                )

                if pd.notna(value):
                    candidate_exposure = float(
                        value
                    )
                    break

        # ----------------------------------------------------
        # 기존 episode artifact에 candidate exposure가 없으면
        # release 당시 Filter13 budget을 사용하지 않는다.
        #
        # Filter13 budget != Filter15 exposure이므로
        # 서로 대체하면 attribution contract가 깨진다.
        # ----------------------------------------------------

        if candidate_exposure is None:

            # 이미 failure analysis에 full incremental return이
            # 존재하므로, daily exposure를 임의 재구성하지 않고
            # episode-level scaling으로 계산한다.

            full_return = pd.to_numeric(
                episode.get(
                    "full_incremental_return",
                    np.nan,
                ),
                errors="coerce",
            )

            full_mdd = pd.to_numeric(
                episode.get(
                    "full_incremental_mdd",
                    np.nan,
                ),
                errors="coerce",
            )

            if pd.isna(full_return):
                raise ValueError(
                    "Candidate exposure와 "
                    "full_incremental_return 둘 다 없습니다."
                )

            # ------------------------------------------------
            # Return은 정확한 linear scaling이 아니므로
            # FULL artifact를 단순 곱해서 새로운 '정확한'
            # return이라고 주장하면 안 된다.
            #
            # 따라서 이 fallback에서는 이전 failure analysis에
            # 이미 검증된 HALF/QUARTER artifact가 있으면 그것을 사용.
            # ------------------------------------------------

            artifact_return_col = {
                "FULL":
                    "full_incremental_return",

                "HALF":
                    "half_incremental_return",

                "QUARTER":
                    "quarter_incremental_return",
            }[
                sizing_name
            ]

            artifact_mdd_col = {
                "FULL":
                    "full_incremental_mdd",

                "HALF":
                    "half_incremental_mdd",

                "QUARTER":
                    "quarter_incremental_mdd",
            }[
                sizing_name
            ]

            cf_return = pd.to_numeric(
                episode.get(
                    artifact_return_col,
                    np.nan,
                ),
                errors="coerce",
            )

            cf_mdd = pd.to_numeric(
                episode.get(
                    artifact_mdd_col,
                    np.nan,
                ),
                errors="coerce",
            )

            if pd.isna(cf_return):
                raise ValueError(
                    f"{artifact_return_col} missing."
                )

            episode_rows.append(
                {
                    "episode_id":
                        episode["episode_id"],

                    "diagnosis":
                        episode["diagnosis"],

                    "release_date":
                        release_date,

                    "rows_released_early":
                        rows_early,

                    "sizing":
                        sizing_name,

                    "multiplier":
                        multiplier,

                    "measurement_source":
                        "VALIDATED_FAILURE_ANALYSIS_ARTIFACT",

                    "baseline_return":
                        baseline_total,

                    "baseline_mdd":
                        baseline_mdd,

                    "incremental_return":
                        float(cf_return),

                    "incremental_mdd":
                        float(cf_mdd)
                        if pd.notna(cf_mdd)
                        else np.nan,
                }
            )

            continue

        # ----------------------------------------------------
        # Exact daily sizing path
        # ----------------------------------------------------

        cf_exposure = (
            candidate_exposure
            * multiplier
        )

        cf_returns = (
            cf_exposure
            / 100.0
            * numeric(
                window[
                    "spy_return_t1"
                ]
            )
        )

        cf_total = compounded_return(
            cf_returns
        )

        cf_mdd = max_drawdown(
            cf_returns
        )

        incremental = (
            cf_total
            - baseline_total
        )

        for idx, (_, day) in enumerate(
            window.iterrows()
        ):

            daily_rows.append(
                {
                    "episode_id":
                        episode["episode_id"],

                    "diagnosis":
                        episode["diagnosis"],

                    "sizing":
                        sizing_name,

                    "signal_date":
                        day["signal_date"],

                    "execution_date":
                        day["execution_date"],

                    "day_number":
                        idx + 1,

                    "production_exposure":
                        day[
                            "_production_exposure"
                        ],

                    "counterfactual_exposure":
                        cf_exposure,

                    "spy_return_t1":
                        day[
                            "spy_return_t1"
                        ],

                    "counterfactual_return":
                        (
                            cf_exposure
                            / 100.0
                            * day[
                                "spy_return_t1"
                            ]
                        ),
                }
            )

        episode_rows.append(
            {
                "episode_id":
                    episode["episode_id"],

                "diagnosis":
                    episode["diagnosis"],

                "release_date":
                    release_date,

                "rows_released_early":
                    rows_early,

                "sizing":
                    sizing_name,

                "multiplier":
                    multiplier,

                "measurement_source":
                    "DAILY_RECONSTRUCTION",

                "candidate_exposure":
                    candidate_exposure,

                "baseline_return":
                    baseline_total,

                "baseline_mdd":
                    baseline_mdd,

                "counterfactual_return":
                    cf_total,

                "counterfactual_mdd":
                    cf_mdd,

                "incremental_return":
                    incremental,

                "incremental_mdd":
                    cf_mdd,
            }
        )

    return daily_rows, episode_rows


# ============================================================
# Summary
# ============================================================

def build_summary(
    episodes: pd.DataFrame,
):

    rows = []

    for sizing_name in SIZINGS:

        g = episodes[
            episodes["sizing"]
            == sizing_name
        ].copy()

        inc_ret = numeric(
            g["incremental_return"]
        )

        inc_mdd = numeric(
            g["incremental_mdd"]
        )

        rows.append(
            {
                "sizing":
                    sizing_name,

                "multiplier":
                    SIZINGS[
                        sizing_name
                    ],

                "episodes":
                    len(g),

                "positive_episodes":
                    int(
                        (inc_ret > 0).sum()
                    ),

                "negative_episodes":
                    int(
                        (inc_ret < 0).sum()
                    ),

                "flat_episodes":
                    int(
                        (inc_ret == 0).sum()
                    ),

                "total_incremental_return":
                    float(
                        inc_ret.sum()
                    ),

                "avg_incremental_return":
                    float(
                        inc_ret.mean()
                    ),

                "median_incremental_return":
                    float(
                        inc_ret.median()
                    ),

                "avg_incremental_mdd":
                    float(
                        inc_mdd.mean()
                    ),

                "worst_incremental_mdd":
                    float(
                        inc_mdd.min()
                    ),

                "avg_rows_at_reduced_risk":
                    float(
                        numeric(
                            g[
                                "rows_released_early"
                            ]
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

    parity, exposure_col, deadman_source = (
        load_parity()
    )

    episodes = load_episodes()

    panel = build_panel(
        master,
        parity,
    )

    all_daily = []
    all_episodes = []

    for _, episode in episodes.iterrows():

        daily_rows, episode_rows = (
            simulate_episode(
                panel,
                episode,
            )
        )

        all_daily.extend(
            daily_rows
        )

        all_episodes.extend(
            episode_rows
        )

    daily_df = pd.DataFrame(
        all_daily
    )

    episode_df = pd.DataFrame(
        all_episodes
    )

    if episode_df.empty:
        raise ValueError(
            "No counterfactual episodes produced."
        )

    summary_df = build_summary(
        episode_df
    )

    daily_df.to_csv(
        OUT_DAILY,
        index=False,
    )

    episode_df.to_csv(
        OUT_EPISODES,
        index=False,
    )

    summary_df.to_csv(
        OUT_SUMMARY,
        index=False,
    )

    # --------------------------------------------------------
    # 2008 / Timing Risk
    # --------------------------------------------------------

    timing = episode_df[
        episode_df["diagnosis"]
        == "TIMING_RISK"
    ]

    # --------------------------------------------------------
    # Worst cases
    # --------------------------------------------------------

    worst = (
        episode_df
        .sort_values(
            "incremental_mdd",
            ascending=True,
        )
        .head(15)
    )

    lines = []

    lines.append(
        "=" * 78
    )

    lines.append(
        "FILTER15 STAGED RE-RISKING COUNTERFACTUAL"
    )

    lines.append(
        "=" * 78
    )

    lines.append("")

    lines.append(
        "Research Question:"
    )

    lines.append(
        "Deadman 이후 즉시 FULL exposure로 복원하지 않고 "
        "초기 sizing을 낮추면 false-recovery tail risk를 "
        "줄이면서 recovery upside를 유지할 수 있는가?"
    )

    lines.append("")

    lines.append(
        f"Release Episodes       : {episodes['episode_id'].nunique()}"
    )

    lines.append(
        f"Production Exposure Col: {exposure_col}"
    )

    lines.append(
        f"Deadman Source         : {deadman_source}"
    )

    lines.append(
        "Release Candidate      : HY_FALLING_VIX_LT_30"
    )

    lines.append(
        "Execution              : SIGNAL t -> RETURN t+1"
    )

    lines.append(
        "Production Modified    : NO"
    )

    lines.append(
        "Future Data in Signal  : NO"
    )

    lines.append(
        "New Indicator          : NO"
    )

    lines.append(
        "New Release Threshold  : NO"
    )

    lines.append(
        "Sizing Tested          : FULL / HALF / QUARTER"
    )

    lines.append("")

    lines.append(
        "===== SIZING SUMMARY ====="
    )

    lines.append(
        summary_df.to_string(
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
            "sizing",
            "multiplier",
            "incremental_return",
            "incremental_mdd",
            "measurement_source",
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
        "===== WORST CASES ====="
    )

    worst_cols = [
        "episode_id",
        "diagnosis",
        "release_date",
        "rows_released_early",
        "sizing",
        "incremental_return",
        "incremental_mdd",
        "measurement_source",
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
        "판정 기준"
    )

    lines.append(
        "=" * 78
    )

    lines.append("")

    lines.append(
        "1. HALF/QUARTER가 2008형 false recovery의 "
        "worst MDD를 의미 있게 줄이는지 확인한다."
    )

    lines.append("")

    lines.append(
        "2. Tail risk 감소의 대가로 successful recovery의 "
        "incremental return을 얼마나 포기하는지 확인한다."
    )

    lines.append("")

    lines.append(
        "3. 가장 높은 평균 수익률을 자동으로 선택하지 않는다."
    )

    lines.append("")

    lines.append(
        "4. 기관 관점에서는 tail-loss 감소, recovery participation, "
        "rule simplicity와 robustness를 함께 평가한다."
    )

    lines.append("")

    lines.append(
        "5. 이번 결과만으로 25%/50% sizing을 Production에 "
        "채택하지 않는다."
    )

    lines.append("")

    lines.append(
        "6. 유효한 sizing이 확인되면 다음 Gate에서 "
        "단계적 exposure restoration path를 검증한다."
    )

    lines.append("")

    lines.append(
        "PRODUCTION DECISION: NO CHANGE"
    )

    lines.append(
        "NEXT GATE: STAGED RESTORATION PATH"
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
        f"Saved: {OUT_EPISODES}"
    )

    print(
        f"Saved: {OUT_SUMMARY}"
    )

    print(
        f"Saved: {OUT_TXT}"
    )


if __name__ == "__main__":
    main()