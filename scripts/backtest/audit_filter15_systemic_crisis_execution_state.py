from __future__ import annotations

"""
FILTER15 SYSTEMIC CRISIS EXECUTION-STATE AUDIT

목적
----
기존 systemic crisis audit의 문제를 수정한다.

기존 문제:
    master_panel.csv를 직접 읽었기 때문에
    Production execution 과정에서 생성되는 아래 state가 누락됨.

    - MACRO_NARRATIVE
    - MARKET_REGIME
    - CROSS_ASSET_TAPE
    - POS_SLOPE
    - INSTITUTIONAL_FLOW
    - LEADERSHIP_BREADTH_SCORE
    - STRUCT_V2_STATE
    - GAMMA_STATE
    - POLICY_BIAS_LINE

이번 Audit:
    Exact Parity Audit과 동일한 historical PIT execution chain을
    전체 기간 순차 실행한다.

실행 순서
---------
1. build_market_data()
2. prepare_filter13_execution_state()
3. Production narrative_engine_filter()
4. Filter15 직전 완성 market_data snapshot 저장
5. 기존 release episode와 결합
6. TIMING_RISK vs SUCCESSFUL_RELEASE 비교

원칙
----
- Production 수정 금지
- 미래 데이터 사용 금지
- master_panel state 직접 사용 금지
- Production generator 재구현 금지
- threshold optimization 금지
- release rule 변경 금지
- 진단 전용
"""

from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# Paths / Imports
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT))


import filters.strategist_filters as sf

from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)


PANEL_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

RELEASE_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter15_release_failure_analysis.csv"
)

RESULT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

SNAPSHOT_OUT = (
    RESULT_DIR
    / "filter15_systemic_crisis_execution_state.csv"
)

SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_systemic_crisis_execution_state_summary.csv"
)

AUDIT_OUT = (
    RESULT_DIR
    / "filter15_systemic_crisis_execution_state_audit.txt"
)


# ============================================================
# Helpers
# ============================================================

def to_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    try:
        return float(
            str(value)
            .replace(",", "")
            .replace("%", "")
            .strip()
        )
    except Exception:
        return None


def nested_float(
    obj: Any,
    key: str,
) -> float | None:
    if not isinstance(obj, dict):
        return None

    return to_float(
        obj.get(key)
    )


def nested_text(
    obj: Any,
    key: str,
) -> str:
    if not isinstance(obj, dict):
        return "MISSING"

    value = obj.get(key)

    if value is None:
        return "MISSING"

    text = str(value).strip()

    return (
        text
        if text
        else "MISSING"
    )


def text_value(
    value: Any,
) -> str:
    if value is None:
        return "MISSING"

    try:
        if pd.isna(value):
            return "MISSING"
    except Exception:
        pass

    text = str(value).strip()

    return (
        text
        if text
        else "MISSING"
    )


def mean_or_nan(
    series: pd.Series,
) -> float:
    values = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if values.empty:
        return np.nan

    return float(
        values.mean()
    )


def median_or_nan(
    series: pd.Series,
) -> float:
    values = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if values.empty:
        return np.nan

    return float(
        values.median()
    )


# ============================================================
# Capture actual Filter15 input state
# ============================================================

def capture_filter15_state(
    market_data: dict[str, Any],
) -> dict[str, Any]:

    vix = (
        market_data.get("VIX", {})
        or {}
    )

    hy = (
        market_data.get("HY_OAS", {})
        or {}
    )

    net_liq = (
        market_data.get("NET_LIQ", {})
        or {}
    )

    flow = (
        market_data.get(
            "INSTITUTIONAL_FLOW",
            {},
        )
        or {}
    )

    tape = (
        market_data.get(
            "CROSS_ASSET_TAPE",
            {},
        )
        or {}
    )

    return {
        # ----------------------------------------------------
        # Filter13 output
        # ----------------------------------------------------
        "RISK_BUDGET":
            to_float(
                market_data.get(
                    "RISK_BUDGET"
                )
            ),

        # ----------------------------------------------------
        # Volatility
        # ----------------------------------------------------
        "VIX_TODAY":
            nested_float(
                vix,
                "today",
            ),

        "VIX_PCT_CHANGE":
            nested_float(
                vix,
                "pct_change",
            ),

        "VIX_Z":
            nested_float(
                tape,
                "VIX_Z",
            ),

        # ----------------------------------------------------
        # Credit
        # ----------------------------------------------------
        "HY_OAS":
            nested_float(
                hy,
                "today",
            ),

        "HY_OAS_PCT_CHANGE":
            nested_float(
                hy,
                "pct_change",
            ),

        "HY_OAS_STATUS":
            text_value(
                market_data.get(
                    "HY_OAS_STATUS"
                )
            ),

        # ----------------------------------------------------
        # Positioning
        # ----------------------------------------------------
        "SP500_POS_Z":
            to_float(
                market_data.get(
                    "SP500_POS_Z"
                )
            ),

        "POS_SLOPE":
            to_float(
                market_data.get(
                    "POS_SLOPE"
                )
            ),

        "DEALER_GAMMA_BIAS":
            to_float(
                market_data.get(
                    "DEALER_GAMMA_BIAS"
                )
            ),

        "CTA_MOMENTUM_SCORE":
            to_float(
                market_data.get(
                    "CTA_MOMENTUM_SCORE"
                )
            ),

        # ----------------------------------------------------
        # Liquidity
        # ----------------------------------------------------
        "NET_LIQ":
            nested_float(
                net_liq,
                "today",
            ),

        "NET_LIQ_DIR":
            text_value(
                market_data.get(
                    "NET_LIQ_DIR"
                )
            ),

        "NET_LIQ_LEVEL_BUCKET":
            text_value(
                market_data.get(
                    "NET_LIQ_LEVEL_BUCKET"
                )
            ),

        # ----------------------------------------------------
        # Macro / regime
        # ----------------------------------------------------
        "MACRO_NARRATIVE":
            text_value(
                market_data.get(
                    "MACRO_NARRATIVE"
                )
            ),

        "MARKET_REGIME":
            text_value(
                market_data.get(
                    "MARKET_REGIME"
                )
            ),

        "STRUCT_V2_STATE":
            text_value(
                market_data.get(
                    "STRUCT_V2_STATE"
                )
            ),

        "GAMMA_STATE":
            text_value(
                market_data.get(
                    "GAMMA_STATE"
                )
            ),

        "POLICY_BIAS_LINE":
            text_value(
                market_data.get(
                    "POLICY_BIAS_LINE"
                )
            ),

        # ----------------------------------------------------
        # Flow
        # ----------------------------------------------------
        "INSTITUTIONAL_FLOW_STATE":
            nested_text(
                flow,
                "state",
            ),

        "INSTITUTIONAL_FLOW_SCORE":
            nested_float(
                flow,
                "score",
            ),

        "PREV_FLOW_STATE":
            text_value(
                market_data.get(
                    "PREV_FLOW_STATE"
                )
            ),

        "PREV_FLOW_SCORE":
            to_float(
                market_data.get(
                    "PREV_FLOW_SCORE"
                )
            ),

        # ----------------------------------------------------
        # Leadership
        # ----------------------------------------------------
        "LEADERSHIP_BREADTH_SCORE":
            to_float(
                market_data.get(
                    "LEADERSHIP_BREADTH_SCORE"
                )
            ),

        # ----------------------------------------------------
        # Cross asset
        # ----------------------------------------------------
        "CROSS_ASSET_US10Y_Z":
            nested_float(
                tape,
                "US10Y_Z",
            ),

        "CROSS_ASSET_DXY_Z":
            nested_float(
                tape,
                "DXY_Z",
            ),

        "CROSS_ASSET_WTI_Z":
            nested_float(
                tape,
                "WTI_Z",
            ),

        # ----------------------------------------------------
        # PIT provenance
        # ----------------------------------------------------
        "POS_SLOPE_SOURCE":
            text_value(
                market_data.get(
                    "_POS_SLOPE_SOURCE"
                )
            ),

        "CROSS_ASSET_HISTORY_SOURCE":
            text_value(
                market_data.get(
                    "_CROSS_ASSET_HISTORY_SOURCE"
                )
            ),

        "NET_LIQ_LEVEL_SOURCE":
            text_value(
                market_data.get(
                    "_NET_LIQ_LEVEL_SOURCE"
                )
            ),
    }


# ============================================================
# Main
# ============================================================

def main() -> None:

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not PANEL_PATH.exists():
        raise FileNotFoundError(
            PANEL_PATH
        )

    if not RELEASE_PATH.exists():
        raise FileNotFoundError(
            "\nRelease analysis not found:\n"
            f"{RELEASE_PATH}\n\n"
            "먼저 audit_filter15_release_failure_analysis.py를 "
            "실행해야 합니다."
        )

    # ========================================================
    # Load panel
    # ========================================================

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    panel = (
        panel
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    # ========================================================
    # Load release episodes
    # ========================================================

    release = pd.read_csv(
        RELEASE_PATH
    )

    release["release_date"] = pd.to_datetime(
        release["release_date"],
        errors="coerce",
    )

    release = release.dropna(
        subset=[
            "release_date",
        ]
    ).copy()

    release_dates = set(
        release[
            "release_date"
        ]
        .dt.normalize()
        .tolist()
    )

    # ========================================================
    # Sequential PIT execution
    #
    # IMPORTANT:
    # Flow memory 때문에 release date만 골라 실행하면 안 된다.
    # 전체 기간을 처음부터 순차 실행해야 한다.
    # ========================================================

    previous_flow_memory = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    snapshots: list[
        dict[str, Any]
    ] = []

    total = len(panel)

    errors = 0

    for row_index in range(total):

        row = panel.iloc[
            row_index
        ]

        signal_date = pd.to_datetime(
            row["signal_date"]
        )

        execution_date = pd.to_datetime(
            row["execution_date"],
            errors="coerce",
        )

        try:
            # =================================================
            # 1. Historical PIT raw market_data
            # =================================================

            market_data = build_market_data(
                panel,
                row_index,
            )

            # =================================================
            # 2. Exact validated Production pre-13 chain
            # =================================================

            previous_flow_memory = (
                prepare_filter13_execution_state(
                    market_data=market_data,
                    panel=panel,
                    row_index=row_index,
                    previous_flow_memory=(
                        previous_flow_memory
                    ),
                )
            )

            # =================================================
            # 3. Actual Production Filter13
            #
            # Filter15 receives RISK_BUDGET after this.
            # =================================================

            sf.narrative_engine_filter(
                market_data
            )

            # =================================================
            # 4. Capture ONLY release dates
            #
            # Snapshot is BEFORE Production Filter15.
            # Therefore this is exactly the state Filter15 sees.
            # =================================================

            if (
                signal_date.normalize()
                in release_dates
            ):

                snapshot = (
                    capture_filter15_state(
                        market_data
                    )
                )

                snapshot[
                    "signal_date"
                ] = signal_date

                snapshot[
                    "execution_date"
                ] = execution_date

                snapshots.append(
                    snapshot
                )

        except Exception as exc:

            errors += 1

            if (
                signal_date.normalize()
                in release_dates
            ):
                snapshots.append(
                    {
                        "signal_date":
                            signal_date,

                        "execution_date":
                            execution_date,

                        "EXECUTION_ERROR":
                            repr(exc),
                    }
                )

        if (
            (row_index + 1) % 250 == 0
            or row_index + 1 == total
        ):
            print(
                f"Processed "
                f"{row_index + 1}/"
                f"{total}"
            )

    # ========================================================
    # Build snapshot frame
    # ========================================================

    state = pd.DataFrame(
        snapshots
    )

    state["signal_date"] = pd.to_datetime(
        state["signal_date"],
        errors="coerce",
    )

    # ========================================================
    # Merge with release diagnosis
    # ========================================================

    merged = release.merge(
        state,
        left_on="release_date",
        right_on="signal_date",
        how="left",
        validate="many_to_one",
    )

    # ========================================================
    # Snapshot integrity
    # ========================================================

    merged[
        "snapshot_found"
    ] = (
        merged[
            "signal_date"
        ].notna()
    )

    snapshot_missing = int(
        (~merged["snapshot_found"]).sum()
    )

    # ========================================================
    # Core comparison groups
    # ========================================================

    diagnosis = (
        merged[
            "diagnosis"
        ]
        .astype(str)
        .str.upper()
    )

    successful = merged[
        diagnosis
        == "SUCCESSFUL_RELEASE"
    ].copy()

    timing = merged[
        diagnosis
        == "TIMING_RISK"
    ].copy()

    ambiguous = merged[
        diagnosis
        == "AMBIGUOUS_FAILURE"
    ].copy()

    # ========================================================
    # Numeric comparison
    # ========================================================

    numeric_fields = [
        "RISK_BUDGET",

        "VIX_TODAY",
        "VIX_PCT_CHANGE",
        "VIX_Z",

        "HY_OAS",
        "HY_OAS_PCT_CHANGE",

        "SP500_POS_Z",
        "POS_SLOPE",
        "DEALER_GAMMA_BIAS",
        "CTA_MOMENTUM_SCORE",

        "NET_LIQ",

        "INSTITUTIONAL_FLOW_SCORE",
        "PREV_FLOW_SCORE",

        "LEADERSHIP_BREADTH_SCORE",

        "CROSS_ASSET_US10Y_Z",
        "CROSS_ASSET_DXY_Z",
        "CROSS_ASSET_WTI_Z",
    ]

    numeric_fields = [
        field
        for field in numeric_fields
        if field in merged.columns
    ]

    summary_rows = []

    for field in numeric_fields:

        timing_value = (
            mean_or_nan(
                timing[field]
            )
        )

        success_mean = (
            mean_or_nan(
                successful[field]
            )
        )

        success_median = (
            median_or_nan(
                successful[field]
            )
        )

        ambiguous_mean = (
            mean_or_nan(
                ambiguous[field]
            )
        )

        summary_rows.append(
            {
                "field":
                    field,

                "timing_risk_value":
                    timing_value,

                "successful_mean":
                    success_mean,

                "successful_median":
                    success_median,

                "ambiguous_mean":
                    ambiguous_mean,

                "timing_minus_success_mean":
                    (
                        timing_value
                        - success_mean
                        if (
                            pd.notna(
                                timing_value
                            )
                            and pd.notna(
                                success_mean
                            )
                        )
                        else np.nan
                    ),
            }
        )

    summary = pd.DataFrame(
        summary_rows
    )

    # ========================================================
    # Save CSV
    # ========================================================

    merged.to_csv(
        SNAPSHOT_OUT,
        index=False,
    )

    summary.to_csv(
        SUMMARY_OUT,
        index=False,
    )

    # ========================================================
    # State availability
    # ========================================================

    important_state_fields = [
        "MACRO_NARRATIVE",
        "MARKET_REGIME",
        "STRUCT_V2_STATE",
        "GAMMA_STATE",
        "POLICY_BIAS_LINE",

        "VIX_Z",

        "POS_SLOPE",

        "INSTITUTIONAL_FLOW_STATE",
        "INSTITUTIONAL_FLOW_SCORE",

        "LEADERSHIP_BREADTH_SCORE",
    ]

    availability_lines = []

    for field in important_state_fields:

        if field not in merged.columns:

            availability_lines.append(
                f"{field:30s}: COLUMN_MISSING"
            )

            continue

        series = merged[field]

        if series.dtype == object:

            available = (
                series
                .fillna("MISSING")
                .astype(str)
                .ne("MISSING")
                .sum()
            )

        else:

            available = (
                pd.to_numeric(
                    series,
                    errors="coerce",
                )
                .notna()
                .sum()
            )

        availability_lines.append(
            f"{field:30s}: "
            f"{int(available)}/{len(merged)}"
        )

    # ========================================================
    # Episode 1 / 2008
    # ========================================================

    episode1 = merged[
        pd.to_numeric(
            merged["episode_id"],
            errors="coerce",
        )
        == 1
    ].copy()

    episode1_fields = [
        "episode_id",
        "release_date",
        "execution_date",
        "diagnosis",

        "RISK_BUDGET",

        "VIX_TODAY",
        "VIX_PCT_CHANGE",
        "VIX_Z",

        "HY_OAS",
        "HY_OAS_PCT_CHANGE",
        "HY_OAS_STATUS",

        "SP500_POS_Z",
        "POS_SLOPE",

        "DEALER_GAMMA_BIAS",
        "CTA_MOMENTUM_SCORE",

        "NET_LIQ",
        "NET_LIQ_DIR",
        "NET_LIQ_LEVEL_BUCKET",

        "MACRO_NARRATIVE",
        "MARKET_REGIME",
        "STRUCT_V2_STATE",
        "GAMMA_STATE",
        "POLICY_BIAS_LINE",

        "INSTITUTIONAL_FLOW_STATE",
        "INSTITUTIONAL_FLOW_SCORE",
        "PREV_FLOW_STATE",
        "PREV_FLOW_SCORE",

        "LEADERSHIP_BREADTH_SCORE",

        "CROSS_ASSET_US10Y_Z",
        "CROSS_ASSET_DXY_Z",
        "CROSS_ASSET_WTI_Z",

        "POS_SLOPE_SOURCE",
        "CROSS_ASSET_HISTORY_SOURCE",
        "NET_LIQ_LEVEL_SOURCE",

        "full_incremental_return",
        "full_incremental_mdd",
    ]

    episode1_fields = [
        field
        for field in episode1_fields
        if field in episode1.columns
    ]

    # ========================================================
    # Categorical comparison
    # ========================================================

    categorical_fields = [
        "MACRO_NARRATIVE",
        "MARKET_REGIME",
        "STRUCT_V2_STATE",
        "GAMMA_STATE",
        "POLICY_BIAS_LINE",

        "NET_LIQ_DIR",
        "NET_LIQ_LEVEL_BUCKET",

        "INSTITUTIONAL_FLOW_STATE",
        "PREV_FLOW_STATE",
    ]

    categorical_lines = []

    for field in categorical_fields:

        if field not in merged.columns:
            continue

        categorical_lines.append(
            f"\n--- {field} ---"
        )

        table = (
            merged
            .assign(
                _diagnosis=(
                    merged["diagnosis"]
                    .astype(str)
                    .str.upper()
                )
            )
            .groupby(
                [
                    "_diagnosis",
                    field,
                ],
                dropna=False,
            )
            .size()
            .reset_index(
                name="episodes"
            )
        )

        categorical_lines.append(
            table.to_string(
                index=False
            )
        )

    # ========================================================
    # Audit report
    # ========================================================

    lines = []

    lines.append(
        "=" * 78
    )

    lines.append(
        "FILTER15 SYSTEMIC CRISIS EXECUTION-STATE AUDIT"
    )

    lines.append(
        "=" * 78
    )

    lines.append("")

    lines.append(
        f"Release Episodes Analysed : {len(merged)}"
    )

    lines.append(
        f"Successful Releases       : {len(successful)}"
    )

    lines.append(
        f"Timing Risk Episodes      : {len(timing)}"
    )

    lines.append(
        f"Ambiguous Failures        : {len(ambiguous)}"
    )

    lines.append(
        f"Snapshots Missing         : {snapshot_missing}"
    )

    lines.append(
        f"Execution Errors          : {errors}"
    )

    lines.append("")

    lines.append(
        "Production Modified       : NO"
    )

    lines.append(
        "Future-data Backfill      : NO"
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

    lines.append("")

    lines.append(
        "Execution Source:"
    )

    lines.append(
        "build_market_data"
    )

    lines.append(
        "-> prepare_filter13_execution_state"
    )

    lines.append(
        "-> Production narrative_engine_filter"
    )

    lines.append(
        "-> Filter15 pre-execution market_data snapshot"
    )

    lines.append("")

    lines.append(
        "===== STATE AVAILABILITY ====="
    )

    lines.extend(
        availability_lines
    )

    lines.append("")

    lines.append(
        "===== TIMING RISK vs SUCCESSFUL RELEASE ====="
    )

    lines.append(
        summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "===== EPISODE 1 / 2008 EXECUTION STATE ====="
    )

    if episode1.empty:

        lines.append(
            "Episode 1 not found."
        )

    else:

        lines.append(
            episode1[
                episode1_fields
            ].to_string(
                index=False
            )
        )

    lines.append("")

    lines.append(
        "===== CATEGORICAL STATE COMPARISON ====="
    )

    if categorical_lines:

        lines.extend(
            categorical_lines
        )

    else:

        lines.append(
            "No categorical state available."
        )

    lines.append("")

    lines.append(
        "=" * 78
    )

    lines.append(
        "판단 원칙"
    )

    lines.append(
        "=" * 78
    )

    lines.append("")

    lines.append(
        "1. 이번 결과는 master_panel의 raw state가 아니라 "
        "검증된 historical Production execution chain이 "
        "Filter15 직전에 생성한 실제 market_data를 사용한다."
    )

    lines.append("")

    lines.append(
        "2. TIMING_RISK가 1개뿐이므로 2008을 맞히는 "
        "단일 threshold를 최적화하지 않는다."
    )

    lines.append("")

    lines.append(
        "3. Credit / Volatility / Macro / Cross Asset / Flow / "
        "Liquidity가 같은 방향으로 systemic stress를 보여주는지 본다."
    )

    lines.append("")

    lines.append(
        "4. 여러 독립 축에서 2008과 성공 recovery가 분리될 경우에만 "
        "CRISIS -> STABILIZING -> RECOVERY_CONFIRMED "
        "state-machine hypothesis로 이동한다."
    )

    lines.append("")

    lines.append(
        "5. 기존 execution state로 분리가 불가능한 경우에만 "
        "새로운 데이터 필요성을 검토한다."
    )

    lines.append("")

    lines.append(
        "6. 이번 결과만으로 Production Filter15를 수정하지 않는다."
    )

    lines.append("")

    lines.append(
        "PRODUCTION DECISION: NO CHANGE"
    )

    lines.append(
        "NEXT GATE: SYSTEMIC STATE SEPARATION REVIEW"
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
        f"Saved: {SNAPSHOT_OUT}"
    )

    print(
        f"Saved: {SUMMARY_OUT}"
    )

    print(
        f"Saved: {AUDIT_OUT}"
    )


if __name__ == "__main__":
    main()