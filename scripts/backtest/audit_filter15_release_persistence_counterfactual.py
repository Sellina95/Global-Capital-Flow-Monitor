"""
FILTER15 RELEASE PERSISTENCE COUNTERFACTUAL

목적
----
기존 Filter15 Hard Deadman release 후보:

    HY_FALLING + VIX < 30

에서 발생한 false stabilization 문제를 검증한다.

비교 대상
---------
1. PERSIST_1
   HY_FALLING + VIX < 30
   현재 후보와 동일.

2. PERSIST_2
   위 조건이 2거래일 연속 확인된 경우 release.

3. PERSIST_3
   위 조건이 3거래일 연속 확인된 경우 release.

핵심 연구 질문
-------------
- Persistence confirmation이 2008형 premature release를 막는가?
- 성공했던 recovery episode를 얼마나 보존하는가?
- Total incremental return은 어떻게 변하는가?
- Worst incremental MDD가 개선되는가?
- Confirmation 때문에 정상 recovery를 지나치게 늦게 잡지는 않는가?

검증 원칙
---------
- Production 코드 수정 금지
- Production Filter15 수정 금지
- 미래 데이터 backfill 금지
- signal t -> return t+1
- Exposure sizing은 FULL 유지
- Persistence만 독립적으로 변경
- 결과는 research counterfactual이며 Production 승인 아님

입력
----
data/backtest/results/
    filter15_deadman_release_gate_counterfactual_daily.csv

출력
----
data/backtest/results/
    filter15_release_persistence_daily.csv

data/backtest/results/
    filter15_release_persistence_episodes.csv

data/backtest/results/
    filter15_release_persistence_summary.csv

data/backtest/results/
    filter15_release_persistence_audit.txt
"""

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

INPUT_PATH = (
    RESULT_DIR
    / "filter15_deadman_release_gate_counterfactual_daily.csv"
)

DAILY_OUT = (
    RESULT_DIR
    / "filter15_release_persistence_daily.csv"
)

EPISODE_OUT = (
    RESULT_DIR
    / "filter15_release_persistence_episodes.csv"
)

SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_release_persistence_summary.csv"
)

AUDIT_OUT = (
    RESULT_DIR
    / "filter15_release_persistence_audit.txt"
)


# ============================================================
# Configuration
# ============================================================

SOURCE_CANDIDATE = "HY_FALLING_VIX_LT_30"

PERSISTENCE_WINDOWS = {
    "PERSIST_1": 1,
    "PERSIST_2": 2,
    "PERSIST_3": 3,
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

    drawdown = (
        wealth / peak
        - 1.0
    )

    return float(
        drawdown.min()
    )


def consecutive_true(
    condition: pd.Series,
) -> pd.Series:
    """
    현재 행까지 condition이 몇 거래일 연속 True인지 계산.

    미래 데이터 사용 없음.

    예:
        False -> 0
        True  -> 1
        True  -> 2
        True  -> 3
        False -> 0
    """

    condition = (
        condition
        .fillna(False)
        .astype(bool)
    )

    groups = (
        (~condition)
        .cumsum()
    )

    streak = (
        condition
        .groupby(groups)
        .cumsum()
    )

    return streak.astype(int)


# ============================================================
# Load
# ============================================================

if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"\nInput not found:\n{INPUT_PATH}\n\n"
        "먼저 "
        "audit_filter15_deadman_release_gate_counterfactual.py "
        "를 실행해야 합니다."
    )


df = pd.read_csv(
    INPUT_PATH
)


# ============================================================
# Contract validation
# ============================================================

required = {
    "episode_id",
    "candidate",
    "signal_date",
    "HY_OAS",
    "VIX",
    "SPY",
    "hy_falling",
    "baseline_exposure_15",
    "counterfactual_exposure",
    "spy_return",
}

missing = sorted(
    required
    - set(df.columns)
)

if missing:
    raise ValueError(
        "\nMissing required columns:\n"
        + "\n".join(missing)
    )


# ============================================================
# Types
# ============================================================

df["signal_date"] = pd.to_datetime(
    df["signal_date"],
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
    df[col] = numeric(
        df[col]
    )


# Robust boolean conversion.

if df["hy_falling"].dtype == bool:

    df["hy_falling_bool"] = (
        df["hy_falling"]
    )

else:

    df["hy_falling_bool"] = (
        df["hy_falling"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(
            [
                "true",
                "1",
                "yes",
            ]
        )
    )


# ============================================================
# Target candidate only
# ============================================================

df = df[
    df["candidate"]
    == SOURCE_CANDIDATE
].copy()


if df.empty:
    raise ValueError(
        f"\nNo rows found for candidate: "
        f"{SOURCE_CANDIDATE}"
    )


df = (
    df
    .dropna(
        subset=[
            "episode_id",
            "signal_date",
        ]
    )
    .sort_values(
        [
            "episode_id",
            "signal_date",
        ]
    )
    .reset_index(drop=True)
)


# ============================================================
# IMPORTANT:
#
# Base release condition is reconstructed using ONLY
# information available on signal_date.
#
# No future persistence information is used.
# ============================================================

df["base_release_condition"] = (
    df["hy_falling_bool"]
    & df["VIX"].notna()
    & (
        df["VIX"]
        < 30.0
    )
)


# ============================================================
# Calculate persistence INSIDE each Deadman episode
# ============================================================

df["release_condition_streak"] = (
    df
    .groupby(
        "episode_id",
        group_keys=False,
    )[
        "base_release_condition"
    ]
    .transform(
        consecutive_true
    )
)


# ============================================================
# Run persistence counterfactual
# ============================================================

daily_records = []
episode_records = []


episode_ids = (
    df["episode_id"]
    .dropna()
    .unique()
)


for episode_id in episode_ids:

    block = df[
        df["episode_id"]
        == episode_id
    ].copy()

    block = (
        block
        .sort_values(
            "signal_date"
        )
        .reset_index(drop=True)
    )

    if block.empty:
        continue

    # Production baseline:
    # Deadman exposure remains whatever the validated
    # baseline Filter15 produced.
    baseline_exposure = (
        block[
            "baseline_exposure_15"
        ]
        .copy()
    )

    # FULL restored exposure from the previously validated
    # release counterfactual.
    #
    # We are deliberately NOT changing sizing here.
    full_restored_exposure = (
        block[
            "counterfactual_exposure"
        ]
        .copy()
    )

    # --------------------------------------------------------
    # Each persistence hypothesis
    # --------------------------------------------------------

    for (
        persistence_name,
        required_days,
    ) in PERSISTENCE_WINDOWS.items():

        eligible = (
            block[
                "release_condition_streak"
            ]
            >= required_days
        )

        eligible_positions = (
            block.index[
                eligible
            ]
            .tolist()
        )

        if eligible_positions:

            release_pos = int(
                eligible_positions[0]
            )

            release_date = (
                block.loc[
                    release_pos,
                    "signal_date",
                ]
            )

        else:

            release_pos = None
            release_date = pd.NaT

        # ----------------------------------------------------
        # Counterfactual exposure
        # ----------------------------------------------------

        cf_exposure = (
            baseline_exposure
            .copy()
        )

        if release_pos is not None:

            # From confirmed release onward, use the exact
            # FULL restored exposure from the validated
            # original counterfactual.
            cf_exposure.iloc[
                release_pos:
            ] = (
                full_restored_exposure
                .iloc[
                    release_pos:
                ]
                .values
            )

        # ----------------------------------------------------
        # Execution:
        #
        # signal t determines exposure for next return.
        # ----------------------------------------------------

        baseline_executed = (
            baseline_exposure
            .shift(1)
            .fillna(0.0)
            / 100.0
        )

        cf_executed = (
            cf_exposure
            .shift(1)
            .fillna(0.0)
            / 100.0
        )

        asset_return = (
            block[
                "spy_return"
            ]
            .fillna(0.0)
        )

        baseline_return = (
            baseline_executed
            * asset_return
        )

        cf_return = (
            cf_executed
            * asset_return
        )

        incremental_daily_return = (
            cf_return
            - baseline_return
        )

        # ----------------------------------------------------
        # Episode metrics
        # ----------------------------------------------------

        baseline_total_return = (
            compound_return(
                baseline_return
            )
        )

        cf_total_return = (
            compound_return(
                cf_return
            )
        )

        incremental_return = (
            cf_total_return
            - baseline_total_return
        )

        baseline_mdd = (
            max_drawdown(
                baseline_return
            )
        )

        cf_mdd = (
            max_drawdown(
                cf_return
            )
        )

        incremental_mdd = (
            cf_mdd
            - baseline_mdd
        )

        # ----------------------------------------------------
        # Release timing
        # ----------------------------------------------------

        if release_pos is not None:

            rows_released_early = (
                len(block)
                - release_pos
            )

            release_hy = (
                block.loc[
                    release_pos,
                    "HY_OAS",
                ]
            )

            release_vix = (
                block.loc[
                    release_pos,
                    "VIX",
                ]
            )

            release_streak = (
                block.loc[
                    release_pos,
                    "release_condition_streak",
                ]
            )

        else:

            rows_released_early = 0
            release_hy = np.nan
            release_vix = np.nan
            release_streak = 0

        # ----------------------------------------------------
        # Daily output
        # ----------------------------------------------------

        for i in block.index:

            daily_records.append(
                {
                    "episode_id":
                        episode_id,

                    "persistence":
                        persistence_name,

                    "required_days":
                        required_days,

                    "signal_date":
                        block.loc[
                            i,
                            "signal_date",
                        ],

                    "HY_OAS":
                        block.loc[
                            i,
                            "HY_OAS",
                        ],

                    "VIX":
                        block.loc[
                            i,
                            "VIX",
                        ],

                    "SPY":
                        block.loc[
                            i,
                            "SPY",
                        ],

                    "hy_falling":
                        block.loc[
                            i,
                            "hy_falling_bool",
                        ],

                    "base_release_condition":
                        block.loc[
                            i,
                            "base_release_condition",
                        ],

                    "release_condition_streak":
                        block.loc[
                            i,
                            "release_condition_streak",
                        ],

                    "release_date":
                        release_date,

                    "released":
                        bool(
                            release_pos is not None
                            and i >= release_pos
                        ),

                    "baseline_exposure_15":
                        baseline_exposure.iloc[i],

                    "counterfactual_exposure":
                        cf_exposure.iloc[i],

                    "spy_return":
                        asset_return.iloc[i],

                    "baseline_strategy_return":
                        baseline_return.iloc[i],

                    "counterfactual_strategy_return":
                        cf_return.iloc[i],

                    "incremental_daily_return":
                        incremental_daily_return.iloc[i],
                }
            )

        # ----------------------------------------------------
        # Episode output
        # ----------------------------------------------------

        episode_records.append(
            {
                "episode_id":
                    episode_id,

                "persistence":
                    persistence_name,

                "required_days":
                    required_days,

                "release_date":
                    release_date,

                "released":
                    release_pos is not None,

                "release_hy_oas":
                    release_hy,

                "release_vix":
                    release_vix,

                "release_streak":
                    release_streak,

                "rows_released_early":
                    rows_released_early,

                "baseline_total_return":
                    baseline_total_return,

                "counterfactual_total_return":
                    cf_total_return,

                "incremental_return":
                    incremental_return,

                "baseline_mdd":
                    baseline_mdd,

                "counterfactual_mdd":
                    cf_mdd,

                "incremental_mdd":
                    incremental_mdd,
            }
        )


# ============================================================
# DataFrames
# ============================================================

daily_out = pd.DataFrame(
    daily_records
)

episodes_out = pd.DataFrame(
    episode_records
)


if episodes_out.empty:
    raise ValueError(
        "No persistence episodes generated."
    )


# ============================================================
# Summary
# ============================================================

summary_records = []


for persistence_name in (
    PERSISTENCE_WINDOWS.keys()
):

    x = episodes_out[
        episodes_out[
            "persistence"
        ]
        == persistence_name
    ].copy()

    released = x[
        x["released"]
    ].copy()

    positive = int(
        (
            released[
                "incremental_return"
            ]
            > 0
        ).sum()
    )

    negative = int(
        (
            released[
                "incremental_return"
            ]
            < 0
        ).sum()
    )

    flat = int(
        (
            released[
                "incremental_return"
            ]
            == 0
        ).sum()
    )

    summary_records.append(
        {
            "persistence":
                persistence_name,

            "required_days":
                PERSISTENCE_WINDOWS[
                    persistence_name
                ],

            "total_episodes":
                len(x),

            "released_episodes":
                len(released),

            "not_released_episodes":
                int(
                    len(x)
                    - len(released)
                ),

            "positive_episodes":
                positive,

            "negative_episodes":
                negative,

            "flat_episodes":
                flat,

            "avg_rows_released_early":
                (
                    released[
                        "rows_released_early"
                    ].mean()
                    if len(released)
                    else np.nan
                ),

            "median_rows_released_early":
                (
                    released[
                        "rows_released_early"
                    ].median()
                    if len(released)
                    else np.nan
                ),

            "total_incremental_return":
                released[
                    "incremental_return"
                ].sum(),

            "avg_incremental_return":
                (
                    released[
                        "incremental_return"
                    ].mean()
                    if len(released)
                    else np.nan
                ),

            "avg_incremental_mdd":
                (
                    released[
                        "incremental_mdd"
                    ].mean()
                    if len(released)
                    else np.nan
                ),

            "worst_incremental_mdd":
                (
                    released[
                        "incremental_mdd"
                    ].min()
                    if len(released)
                    else np.nan
                ),
        }
    )


summary = pd.DataFrame(
    summary_records
)


# ============================================================
# Compare release dates episode by episode
# ============================================================

release_compare = (
    episodes_out
    .pivot(
        index="episode_id",
        columns="persistence",
        values="release_date",
    )
    .reset_index()
)


for col in (
    "PERSIST_1",
    "PERSIST_2",
    "PERSIST_3",
):
    if col in release_compare.columns:
        release_compare[col] = pd.to_datetime(
            release_compare[col],
            errors="coerce",
        )


if (
    "PERSIST_1" in release_compare.columns
    and "PERSIST_2" in release_compare.columns
):

    release_compare[
        "persist2_delay_calendar_days"
    ] = (
        release_compare[
            "PERSIST_2"
        ]
        - release_compare[
            "PERSIST_1"
        ]
    ).dt.days


if (
    "PERSIST_1" in release_compare.columns
    and "PERSIST_3" in release_compare.columns
):

    release_compare[
        "persist3_delay_calendar_days"
    ] = (
        release_compare[
            "PERSIST_3"
        ]
        - release_compare[
            "PERSIST_1"
        ]
    ).dt.days


# ============================================================
# 2008 Episode / Episode 1 diagnostic
# ============================================================

episode1 = episodes_out[
    episodes_out[
        "episode_id"
    ]
    == 1
].copy()


# ============================================================
# Worst cases
# ============================================================

worst_cases = (
    episodes_out[
        episodes_out[
            "released"
        ]
    ]
    .sort_values(
        "incremental_mdd",
        ascending=True,
    )
    .head(15)
)


# ============================================================
# Save CSVs
# ============================================================

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


daily_out.to_csv(
    DAILY_OUT,
    index=False,
)

episodes_out.to_csv(
    EPISODE_OUT,
    index=False,
)

summary.to_csv(
    SUMMARY_OUT,
    index=False,
)


# ============================================================
# Audit report
# ============================================================

lines = []

lines.append(
    "=" * 78
)

lines.append(
    "FILTER15 RELEASE PERSISTENCE COUNTERFACTUAL"
)

lines.append(
    "=" * 78
)

lines.append("")

lines.append(
    f"Source Candidate       : {SOURCE_CANDIDATE}"
)

lines.append(
    f"Deadman Episodes       : {len(episode_ids)}"
)

lines.append(
    "Production Modified    : NO"
)

lines.append(
    "Future-data Backfill   : NO"
)

lines.append(
    "Exposure Sizing        : FULL / UNCHANGED"
)

lines.append(
    "Execution              : SIGNAL t -> RETURN t+1"
)

lines.append("")

lines.append(
    "===== PERSISTENCE SUMMARY ====="
)

lines.append(
    summary.to_string(
        index=False
    )
)

lines.append("")

lines.append(
    "===== EPISODE 1 / 2008 DIAGNOSTIC ====="
)

if episode1.empty:

    lines.append(
        "Episode 1 not found."
    )

else:

    episode1_cols = [
        "episode_id",
        "persistence",
        "required_days",
        "release_date",
        "released",
        "release_hy_oas",
        "release_vix",
        "rows_released_early",
        "incremental_return",
        "incremental_mdd",
    ]

    lines.append(
        episode1[
            episode1_cols
        ].to_string(
            index=False
        )
    )


lines.append("")

lines.append(
    "===== WORST RELEASE CASES ====="
)

worst_cols = [
    "episode_id",
    "persistence",
    "release_date",
    "release_hy_oas",
    "release_vix",
    "rows_released_early",
    "incremental_return",
    "incremental_mdd",
]

lines.append(
    worst_cases[
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
    "기관 관점 검증 질문"
)

lines.append(
    "=" * 78
)

lines.append("")

lines.append(
    "1. PERSIST_2 또는 PERSIST_3가 2008년 false stabilization을 "
    "제거하거나 충분히 지연시키는가?"
)

lines.append("")

lines.append(
    "2. Worst incremental MDD가 의미 있게 개선되는가?"
)

lines.append("")

lines.append(
    "3. 기존 PERSIST_1에서 성공했던 recovery episode를 "
    "얼마나 유지하는가?"
)

lines.append("")

lines.append(
    "4. Confirmation을 기다리느라 정상적인 recovery의 "
    "초기 수익을 지나치게 포기하지 않는가?"
)

lines.append("")

lines.append(
    "5. Persistence만으로 tail problem이 해결된다면 "
    "다음 단계에서 staged re-risking을 별도로 검증한다."
)

lines.append("")

lines.append(
    "6. Persistence로도 2008형 failure가 남는다면 "
    "단순 confirmation 문제가 아니라 crisis severity / "
    "regime-state 문제를 별도로 검증한다."
)

lines.append("")

lines.append(
    "PRODUCTION DECISION: NO CHANGE"
)

lines.append(
    "본 결과는 Research Counterfactual이며 "
    "Production 변경 승인이 아니다."
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
    f"Saved: {DAILY_OUT}"
)

print(
    f"Saved: {EPISODE_OUT}"
)

print(
    f"Saved: {SUMMARY_OUT}"
)

print(
    f"Saved: {AUDIT_OUT}"
)
