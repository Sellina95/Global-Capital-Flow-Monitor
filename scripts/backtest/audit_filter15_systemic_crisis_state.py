"""
FILTER15 SYSTEMIC CRISIS STATE DIAGNOSTIC

목적
----
Filter15 Hard Deadman의 조기 Release 연구에서 확인된 핵심 문제:

    HY_FALLING + VIX < 30

은 다수 episode에서 유효했지만 2008 systemic crisis에서는
false stabilization을 recovery로 오인했다.

이번 Audit은 새로운 Release rule을 만들지 않는다.

핵심 질문
---------
1. 2008 TIMING_RISK와 SUCCESSFUL_RELEASE 당시 기존 Filter15 / Backtest
   데이터의 상태 차이가 무엇이었는가?

2. 단순 HY level / persistence / peak compression이 아닌
   systemic crisis state를 기존 데이터로 식별할 수 있는가?

3. Macro / Cross Asset / Volatility / Credit / Liquidity / Positioning /
   Equity trend 중 어떤 축이 2008을 정상 recovery와 구분하는가?

4. 기존 데이터만으로 CRISIS -> STABILIZING -> RECOVERY_CONFIRMED
   상태 구조를 만들 근거가 있는가?

원칙
----
- Production 수정 금지
- Filter15 수정 금지
- 새로운 지표 추가 금지
- 새로운 Release rule 적용 금지
- Threshold optimization 금지
- 미래 데이터 backfill 금지
- Release 시점까지 존재한 PIT 데이터만 사용
- 본 Audit은 descriptive diagnostic
- 결과 확인 전 state machine 설계 금지

입력
----
data/backtest/results/filter15_release_failure_analysis.csv

data/backtest/master_panel.csv

출력
----
data/backtest/results/filter15_systemic_crisis_state_episode.csv
data/backtest/results/filter15_systemic_crisis_state_numeric_summary.csv
data/backtest/results/filter15_systemic_crisis_state_categorical_summary.csv
data/backtest/results/filter15_systemic_crisis_state_audit.txt
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

FAILURE_PATH = (
    RESULT_DIR
    / "filter15_release_failure_analysis.csv"
)

PANEL_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

EPISODE_OUT = (
    RESULT_DIR
    / "filter15_systemic_crisis_state_episode.csv"
)

NUMERIC_OUT = (
    RESULT_DIR
    / "filter15_systemic_crisis_state_numeric_summary.csv"
)

CATEGORICAL_OUT = (
    RESULT_DIR
    / "filter15_systemic_crisis_state_categorical_summary.csv"
)

AUDIT_OUT = (
    RESULT_DIR
    / "filter15_systemic_crisis_state_audit.txt"
)


# ============================================================
# Helpers
# ============================================================

def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def first_existing_column(
    df: pd.DataFrame,
    candidates: tuple[str, ...],
) -> str | None:

    exact = {
        str(col).lower(): str(col)
        for col in df.columns
    }

    for candidate in candidates:

        found = exact.get(
            candidate.lower()
        )

        if found is not None:
            return found

    return None


def safe_mean(series: pd.Series) -> float:

    x = numeric(series).dropna()

    if x.empty:
        return np.nan

    return float(
        x.mean()
    )


def safe_median(series: pd.Series) -> float:

    x = numeric(series).dropna()

    if x.empty:
        return np.nan

    return float(
        x.median()
    )


def safe_min(series: pd.Series) -> float:

    x = numeric(series).dropna()

    if x.empty:
        return np.nan

    return float(
        x.min()
    )


def safe_max(series: pd.Series) -> float:

    x = numeric(series).dropna()

    if x.empty:
        return np.nan

    return float(
        x.max()
    )


def normalize_text(value) -> str:

    if pd.isna(value):
        return "MISSING"

    value = str(value).strip()

    if not value:
        return "MISSING"

    return value.upper()


# ============================================================
# Load release diagnosis
# ============================================================

if not FAILURE_PATH.exists():

    raise FileNotFoundError(
        f"\nRequired input not found:\n"
        f"{FAILURE_PATH}\n\n"
        "먼저 "
        "audit_filter15_release_failure_analysis.py "
        "를 실행해야 합니다."
    )


release = pd.read_csv(
    FAILURE_PATH
)


required_release = {
    "episode_id",
    "release_date",
    "release_hy_oas",
    "release_vix",
    "rows_released_early",
    "full_incremental_return",
    "full_incremental_mdd",
    "diagnosis",
}


missing_release = sorted(
    required_release
    - set(release.columns)
)


if missing_release:

    raise ValueError(
        "\nMissing release columns:\n"
        + "\n".join(
            missing_release
        )
    )


release["episode_id"] = numeric(
    release["episode_id"]
)


release["release_date"] = pd.to_datetime(
    release["release_date"],
    errors="coerce",
)


for col in (
    "release_hy_oas",
    "release_vix",
    "rows_released_early",
    "full_incremental_return",
    "full_incremental_mdd",
):

    release[col] = numeric(
        release[col]
    )


release = (
    release
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
# We primarily care about:
#
# SUCCESSFUL_RELEASE vs TIMING_RISK.
#
# AMBIGUOUS_FAILURE is retained as context but must NOT be
# silently treated as a clean failure class.
# ============================================================

release["comparison_class"] = (
    release["diagnosis"]
    .astype(str)
    .str.upper()
)


# ============================================================
# Load master panel
# ============================================================

if not PANEL_PATH.exists():

    raise FileNotFoundError(
        f"\nMaster panel not found:\n"
        f"{PANEL_PATH}"
    )


panel = pd.read_csv(
    PANEL_PATH
)


# ============================================================
# Resolve date
# ============================================================

date_col = first_existing_column(
    panel,
    (
        "signal_date",
        "date",
        "Date",
    ),
)


if date_col is None:

    raise ValueError(
        "\nNo signal/date column found in master_panel.csv"
    )


panel["_signal_date"] = pd.to_datetime(
    panel[date_col],
    errors="coerce",
)


panel = (
    panel
    .dropna(
        subset=[
            "_signal_date",
        ]
    )
    .sort_values(
        "_signal_date"
    )
    .drop_duplicates(
        "_signal_date",
        keep="last",
    )
    .reset_index(drop=True)
)


# ============================================================
# Candidate input map
#
# IMPORTANT:
# These are ONLY existing project fields.
# No external / new institutional indicator is added.
# ============================================================

candidate_map = {

    # --------------------------------------------------------
    # Market
    # --------------------------------------------------------

    "SPY": (
        "SPY",
        "spy",
    ),

    "VIX": (
        "VIX",
        "vix",
        "sentiment__vix",
    ),

    # --------------------------------------------------------
    # Credit
    # --------------------------------------------------------

    "HY_OAS": (
        "HY_OAS",
        "hy_oas",
        "credit__HY_OAS",
        "sentiment__hy_oas",
    ),

    # --------------------------------------------------------
    # Liquidity
    # --------------------------------------------------------

    "NET_LIQ": (
        "NET_LIQ",
        "net_liq",
        "liquidity__NET_LIQ",
    ),

    # --------------------------------------------------------
    # Positioning
    # --------------------------------------------------------

    "SP500_POS_Z": (
        "positioning__SP500_POS_Z",
        "SP500_POS_Z",
        "sp500_pos_z",
    ),

    "POS_SLOPE": (
        "positioning__POS_SLOPE",
        "POS_SLOPE",
        "pos_slope",
    ),

    "DEALER_GAMMA_BIAS": (
        "positioning__DEALER_GAMMA_BIAS",
        "DEALER_GAMMA_BIAS",
        "dealer_gamma_bias",
    ),

    "CTA_MOMENTUM_SCORE": (
        "positioning__CTA_MOMENTUM_SCORE",
        "CTA_MOMENTUM_SCORE",
        "cta_momentum_score",
    ),

    # --------------------------------------------------------
    # Breadth / flow
    # --------------------------------------------------------

    "LEADERSHIP_BREADTH_SCORE": (
        "LEADERSHIP_BREADTH_SCORE",
        "leadership_breadth_score",
    ),

    "INSTITUTIONAL_FLOW_SCORE": (
        "INSTITUTIONAL_FLOW.score",
        "institutional_flow__score",
        "INSTITUTIONAL_FLOW_SCORE",
        "institutional_flow_score",
    ),

    # --------------------------------------------------------
    # Cross asset
    # --------------------------------------------------------

    "VIX_Z": (
        "CROSS_ASSET_TAPE.VIX_Z",
        "cross_asset_tape__VIX_Z",
        "VIX_Z",
        "vix_z",
    ),
}


# ============================================================
# Resolve actual panel columns
# ============================================================

resolved = {}


for output_name, candidates in candidate_map.items():

    resolved[
        output_name
    ] = first_existing_column(
        panel,
        candidates,
    )


# ============================================================
# Categorical states
# ============================================================

categorical_map = {

    "MACRO_NARRATIVE": (
        "MACRO_NARRATIVE",
        "macro_narrative",
    ),

    "MARKET_REGIME": (
        "MARKET_REGIME",
        "market_regime",
    ),

    "STRUCT_V2_STATE": (
        "STRUCT_V2_STATE",
        "struct_v2_state",
    ),

    "GAMMA_STATE": (
        "GAMMA_STATE",
        "gamma_state",
    ),

    "POLICY_BIAS_LINE": (
        "POLICY_BIAS_LINE",
        "policy_bias_line",
    ),
}


resolved_categorical = {}


for output_name, candidates in categorical_map.items():

    resolved_categorical[
        output_name
    ] = first_existing_column(
        panel,
        candidates,
    )


# ============================================================
# Build release-date snapshot
# ============================================================

records = []


for _, row in release.iterrows():

    release_date = row[
        "release_date"
    ]

    # Exact PIT snapshot only.
    #
    # We DO NOT search forward.
    #
    # If exact signal date is unavailable, use latest row
    # <= release date only.
    eligible = panel[
        panel["_signal_date"]
        <= release_date
    ]


    if eligible.empty:

        snapshot = None

    else:

        snapshot = eligible.iloc[-1]


    record = {
        "episode_id":
            row["episode_id"],

        "diagnosis":
            row["diagnosis"],

        "comparison_class":
            row["comparison_class"],

        "release_date":
            release_date,

        "release_hy_oas":
            row["release_hy_oas"],

        "release_vix":
            row["release_vix"],

        "rows_released_early":
            row["rows_released_early"],

        "full_incremental_return":
            row["full_incremental_return"],

        "full_incremental_mdd":
            row["full_incremental_mdd"],
    }


    if snapshot is None:

        record[
            "snapshot_date"
        ] = pd.NaT

        record[
            "snapshot_lag_days"
        ] = np.nan

        for name in resolved:
            record[name] = np.nan

        for name in resolved_categorical:
            record[name] = "MISSING"

        records.append(
            record
        )

        continue


    snapshot_date = snapshot[
        "_signal_date"
    ]


    record[
        "snapshot_date"
    ] = snapshot_date


    record[
        "snapshot_lag_days"
    ] = (
        release_date
        - snapshot_date
    ).days


    # --------------------------------------------------------
    # Numeric fields
    # --------------------------------------------------------

    for name, actual_col in resolved.items():

        if actual_col is None:

            record[name] = np.nan

        else:

            record[name] = pd.to_numeric(
                snapshot[
                    actual_col
                ],
                errors="coerce",
            )


    # --------------------------------------------------------
    # Categorical fields
    # --------------------------------------------------------

    for (
        name,
        actual_col,
    ) in resolved_categorical.items():

        if actual_col is None:

            record[name] = "MISSING"

        else:

            record[name] = normalize_text(
                snapshot[
                    actual_col
                ]
            )


    records.append(
        record
    )


episode = pd.DataFrame(
    records
)


# ============================================================
# PIT audit
# ============================================================

episode[
    "future_snapshot_violation"
] = (
    episode[
        "snapshot_date"
    ]
    > episode[
        "release_date"
    ]
)


future_violations = int(
    episode[
        "future_snapshot_violation"
    ]
    .fillna(False)
    .sum()
)


# ============================================================
# Historical market-state features
#
# These use ONLY observations <= release date.
#
# They are not new data.
# They are transformations of existing SPY/VIX/HY series.
# ============================================================

panel["_SPY"] = (
    numeric(
        panel[
            resolved["SPY"]
        ]
    )
    if resolved["SPY"] is not None
    else np.nan
)


panel["_VIX"] = (
    numeric(
        panel[
            resolved["VIX"]
        ]
    )
    if resolved["VIX"] is not None
    else np.nan
)


panel["_HY"] = (
    numeric(
        panel[
            resolved["HY_OAS"]
        ]
    )
    if resolved["HY_OAS"] is not None
    else np.nan
)


# ============================================================
# Add trailing PIT diagnostics
# ============================================================

for idx, row in episode.iterrows():

    release_date = row[
        "release_date"
    ]

    history = panel[
        panel["_signal_date"]
        <= release_date
    ].copy()


    if history.empty:
        continue


    # --------------------------------------------------------
    # SPY drawdown from historical running peak
    # --------------------------------------------------------

    spy_history = (
        history[
            "_SPY"
        ]
        .dropna()
    )


    if not spy_history.empty:

        current_spy = float(
            spy_history.iloc[-1]
        )

        historical_peak = float(
            spy_history.max()
        )

        if historical_peak != 0:

            episode.loc[
                idx,
                "spy_drawdown_from_prior_peak",
            ] = (
                current_spy
                / historical_peak
                - 1.0
            )


        # 20-day return
        if len(spy_history) >= 21:

            previous = float(
                spy_history.iloc[-21]
            )

            if previous != 0:

                episode.loc[
                    idx,
                    "spy_return_20d",
                ] = (
                    current_spy
                    / previous
                    - 1.0
                )


        # 60-day return
        if len(spy_history) >= 61:

            previous = float(
                spy_history.iloc[-61]
            )

            if previous != 0:

                episode.loc[
                    idx,
                    "spy_return_60d",
                ] = (
                    current_spy
                    / previous
                    - 1.0
                )


    # --------------------------------------------------------
    # HY recent change
    # --------------------------------------------------------

    hy_history = (
        history[
            "_HY"
        ]
        .dropna()
    )


    if not hy_history.empty:

        current_hy = float(
            hy_history.iloc[-1]
        )


        if len(hy_history) >= 6:

            episode.loc[
                idx,
                "hy_change_5d",
            ] = (
                current_hy
                - float(
                    hy_history.iloc[-6]
                )
            )


        if len(hy_history) >= 21:

            episode.loc[
                idx,
                "hy_change_20d",
            ] = (
                current_hy
                - float(
                    hy_history.iloc[-21]
                )
            )


    # --------------------------------------------------------
    # VIX recent state
    # --------------------------------------------------------

    vix_history = (
        history[
            "_VIX"
        ]
        .dropna()
    )


    if not vix_history.empty:

        current_vix = float(
            vix_history.iloc[-1]
        )


        if len(vix_history) >= 6:

            episode.loc[
                idx,
                "vix_change_5d",
            ] = (
                current_vix
                - float(
                    vix_history.iloc[-6]
                )
            )


        if len(vix_history) >= 21:

            episode.loc[
                idx,
                "vix_change_20d",
            ] = (
                current_vix
                - float(
                    vix_history.iloc[-21]
                )
            )


# ============================================================
# Numeric comparison fields
# ============================================================

numeric_fields = [

    "release_hy_oas",
    "release_vix",
    "rows_released_early",

    "SPY",
    "VIX",
    "HY_OAS",
    "NET_LIQ",

    "SP500_POS_Z",
    "POS_SLOPE",
    "DEALER_GAMMA_BIAS",
    "CTA_MOMENTUM_SCORE",

    "LEADERSHIP_BREADTH_SCORE",
    "INSTITUTIONAL_FLOW_SCORE",
    "VIX_Z",

    "spy_drawdown_from_prior_peak",
    "spy_return_20d",
    "spy_return_60d",

    "hy_change_5d",
    "hy_change_20d",

    "vix_change_5d",
    "vix_change_20d",
]


numeric_fields = [
    col
    for col in numeric_fields
    if col in episode.columns
]


# ============================================================
# Numeric class summary
# ============================================================

numeric_records = []


classes = [
    "SUCCESSFUL_RELEASE",
    "TIMING_RISK",
    "AMBIGUOUS_FAILURE",
]


for field in numeric_fields:

    for class_name in classes:

        x = episode[
            episode[
                "comparison_class"
            ]
            == class_name
        ]


        if field not in x.columns:
            continue


        values = numeric(
            x[field]
        )


        numeric_records.append(
            {
                "field":
                    field,

                "comparison_class":
                    class_name,

                "episodes":
                    int(
                        values.notna().sum()
                    ),

                "mean":
                    safe_mean(
                        values
                    ),

                "median":
                    safe_median(
                        values
                    ),

                "min":
                    safe_min(
                        values
                    ),

                "max":
                    safe_max(
                        values
                    ),
            }
        )


numeric_summary = pd.DataFrame(
    numeric_records
)


# ============================================================
# Direct 2008 vs successful comparison
#
# Because TIMING_RISK currently contains ONE episode,
# this is descriptive only.
#
# We explicitly DO NOT perform significance testing.
# ============================================================

comparison_records = []


timing = episode[
    episode[
        "comparison_class"
    ]
    == "TIMING_RISK"
]


successful = episode[
    episode[
        "comparison_class"
    ]
    == "SUCCESSFUL_RELEASE"
]


for field in numeric_fields:

    timing_mean = safe_mean(
        timing[field]
    )

    success_mean = safe_mean(
        successful[field]
    )


    comparison_records.append(
        {
            "field":
                field,

            "timing_risk_value":
                timing_mean,

            "successful_mean":
                success_mean,

            "successful_median":
                safe_median(
                    successful[field]
                ),

            "difference_vs_success_mean":
                (
                    timing_mean
                    - success_mean
                    if (
                        pd.notna(
                            timing_mean
                        )
                        and pd.notna(
                            success_mean
                        )
                    )
                    else np.nan
                ),
        }
    )


direct_comparison = pd.DataFrame(
    comparison_records
)


# ============================================================
# Categorical summaries
# ============================================================

categorical_records = []


categorical_fields = [
    col
    for col in resolved_categorical
    if col in episode.columns
]


for field in categorical_fields:

    for class_name in classes:

        x = episode[
            episode[
                "comparison_class"
            ]
            == class_name
        ]


        counts = (
            x[field]
            .fillna(
                "MISSING"
            )
            .astype(str)
            .value_counts(
                dropna=False
            )
        )


        total = int(
            counts.sum()
        )


        for value, count in counts.items():

            categorical_records.append(
                {
                    "field":
                        field,

                    "comparison_class":
                        class_name,

                    "value":
                        value,

                    "count":
                        int(
                            count
                        ),

                    "pct":
                        (
                            float(
                                count
                                / total
                                * 100.0
                            )
                            if total
                            else np.nan
                        ),
                }
            )


categorical_summary = pd.DataFrame(
    categorical_records
)


# ============================================================
# 2008 snapshot
# ============================================================

episode1 = episode[
    episode[
        "episode_id"
    ]
    == 1
].copy()


# ============================================================
# Save
# ============================================================

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


episode.to_csv(
    EPISODE_OUT,
    index=False,
)


numeric_summary.to_csv(
    NUMERIC_OUT,
    index=False,
)


categorical_summary.to_csv(
    CATEGORICAL_OUT,
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
    "FILTER15 SYSTEMIC CRISIS STATE DIAGNOSTIC"
)

lines.append(
    "=" * 78
)

lines.append("")


lines.append(
    f"Release Episodes Analysed : {len(episode)}"
)

lines.append(
    f"Successful Releases       : {len(successful)}"
)

lines.append(
    f"Timing Risk Episodes      : {len(timing)}"
)

lines.append(
    "Production Modified       : NO"
)

lines.append(
    "New Indicators Added      : NO"
)

lines.append(
    "New Release Rule Applied  : NO"
)

lines.append(
    "Threshold Optimization    : NO"
)

lines.append(
    f"Future Snapshot Violations: {future_violations}"
)

lines.append("")


# ------------------------------------------------------------
# Column mapping audit
# ------------------------------------------------------------

lines.append(
    "===== MASTER PANEL FIELD MAPPING ====="
)


for name, actual in resolved.items():

    lines.append(
        f"{name:28s}: "
        f"{actual if actual is not None else 'NOT FOUND'}"
    )


for name, actual in resolved_categorical.items():

    lines.append(
        f"{name:28s}: "
        f"{actual if actual is not None else 'NOT FOUND'}"
    )


lines.append("")


# ------------------------------------------------------------
# Direct comparison
# ------------------------------------------------------------

lines.append(
    "===== TIMING RISK vs SUCCESSFUL RELEASE ====="
)


lines.append(
    direct_comparison.to_string(
        index=False
    )
)


lines.append("")


# ------------------------------------------------------------
# 2008
# ------------------------------------------------------------

lines.append(
    "===== EPISODE 1 / 2008 STATE SNAPSHOT ====="
)


if episode1.empty:

    lines.append(
        "Episode 1 not found."
    )

else:

    display_cols = [

        "episode_id",
        "release_date",
        "snapshot_date",
        "snapshot_lag_days",

        "release_hy_oas",
        "release_vix",

        "SPY",
        "VIX",
        "HY_OAS",
        "NET_LIQ",

        "SP500_POS_Z",
        "POS_SLOPE",
        "DEALER_GAMMA_BIAS",
        "CTA_MOMENTUM_SCORE",

        "LEADERSHIP_BREADTH_SCORE",
        "INSTITUTIONAL_FLOW_SCORE",
        "VIX_Z",

        "spy_drawdown_from_prior_peak",
        "spy_return_20d",
        "spy_return_60d",

        "hy_change_5d",
        "hy_change_20d",

        "vix_change_5d",
        "vix_change_20d",

        "MACRO_NARRATIVE",
        "MARKET_REGIME",
        "STRUCT_V2_STATE",
        "GAMMA_STATE",
        "POLICY_BIAS_LINE",

        "full_incremental_return",
        "full_incremental_mdd",
        "diagnosis",
    ]


    display_cols = [
        col
        for col in display_cols
        if col in episode1.columns
    ]


    lines.append(
        episode1[
            display_cols
        ].to_string(
            index=False
        )
    )


lines.append("")


# ------------------------------------------------------------
# Categorical state
# ------------------------------------------------------------

lines.append(
    "===== CATEGORICAL STATE SUMMARY ====="
)


if categorical_summary.empty:

    lines.append(
        "No categorical state fields available in master panel."
    )

else:

    lines.append(
        categorical_summary.to_string(
            index=False
        )
    )


lines.append("")


# ------------------------------------------------------------
# Research interpretation guardrails
# ------------------------------------------------------------

lines.append(
    "=" * 78
)

lines.append(
    "연구 해석 원칙"
)

lines.append(
    "=" * 78
)

lines.append("")


lines.append(
    "1. TIMING_RISK는 현재 2008 episode 1개뿐이므로 "
    "통계적 유의성 검정이나 threshold 최적화를 하지 않는다."
)

lines.append("")


lines.append(
    "2. 목적은 2008을 맞히는 숫자를 찾는 것이 아니라 "
    "systemic crisis와 정상 recovery 사이에 경제적으로 설명 가능한 "
    "state 차이가 존재하는지 확인하는 것이다."
)

lines.append("")


lines.append(
    "3. 한 변수 하나가 2008만 완벽히 분리한다고 바로 rule로 채택하지 않는다."
)

lines.append("")


lines.append(
    "4. Macro / Credit / Volatility / Equity Trend / Liquidity 등 "
    "여러 기존 축에서 같은 방향의 evidence가 나타나는지 확인한다."
)

lines.append("")


lines.append(
    "5. 기존 데이터로 state separation이 가능할 경우 다음 Gate에서 "
    "CRISIS -> STABILIZING -> RECOVERY_CONFIRMED state machine을 "
    "별도 counterfactual로 검증한다."
)

lines.append("")


lines.append(
    "6. 기존 데이터가 2008과 성공 recovery를 구분하지 못할 경우에만 "
    "missing information을 정의하고 새로운 지표 필요성을 검토한다."
)

lines.append("")


lines.append(
    "7. 이번 Audit만으로 Production Filter15를 수정하지 않는다."
)

lines.append("")


lines.append(
    "PRODUCTION DECISION: NO CHANGE"
)

lines.append(
    "NEXT GATE: 기존 데이터의 systemic-state separation 여부 판단"
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
    f"Saved: {NUMERIC_OUT}"
)

print(
    f"Saved: {CATEGORICAL_OUT}"
)

print(
    f"Saved: {AUDIT_OUT}"
)



