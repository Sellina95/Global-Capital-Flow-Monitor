"""
Filter13 Audit - Phase 2
Historical Institutional Flow + T-1 PREV_FLOW Replay

목적
----
13번 Narrative Engine attribution 전에
Flow 관련 dependency를 PIT(Point-in-Time) 방식으로 검증한다.

원칙
----
- Production 코드 수정 금지
- insights/flow_state.json 사용 금지
- insights/sew_state.json 사용 금지
- 현재 날짜의 Flow는 현재 날짜 정보만으로 계산
- PREV_FLOW는 직전 거래일에 계산된 Flow만 사용
- Historical SEW unavailable -> 가점/감점 0
- 우선 2022년 첫 10거래일만 검증
"""

import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


from scripts.generate_report import (
    build_market_data,
    merge_sovereign_spreads_into_macro_df,
    attach_liquidity_layer,
    attach_credit_spread_layer,
    attach_fred_extras_layer,
    attach_sovereign_spread_layer,
    attach_sentiment_proxy_layer,
    attach_sector_momentum_layer,
    attach_drift_data_layer,
    attach_growth_sustainability_layer,
    attach_breadth_layer,
    attach_leadership_layer,
)

from filters.strategist_filters import (
    market_regime_filter,
    liquidity_filter,
    policy_filter_with_expectations,
    high_yield_spread_filter,
    credit_stress_filter,
    drift_monitor_filter,
    pseudo_gamma_filter,
    structural_filter,
)


OUTPUT_DIR = ROOT / "data" / "backtest" / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Historical data loaders
# ============================================================

def load_backtest_macro_df():

    path = ROOT / "data" / "backtest" / "macro_data.csv"

    print("[LOAD]", path)

    df = pd.read_csv(path)

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df = (
        df
        .sort_values("date")
        .reset_index(drop=True)
    )

    return df


def attach_positioning_layer_backtest(
    market_data: Dict[str, Any],
    df: pd.DataFrame,
    idx: int,
):

    path = (
        ROOT
        / "data"
        / "backtest"
        / "positioning_data.csv"
    )

    if not path.exists():
        return market_data

    pos_df = pd.read_csv(path)

    pos_df["date"] = pd.to_datetime(
        pos_df["date"],
        errors="coerce",
    )

    current_date = pd.to_datetime(
        df.iloc[idx]["date"]
    )

    hist = (
        pos_df[
            pos_df["date"] <= current_date
        ]
        .sort_values("date")
    )

    if hist.empty:
        return market_data

    latest = hist.iloc[-1]

    for col in [
        "SP500_POS_Z",
        "US10Y_POS_Z",
        "DXY_POS_Z",
        "DEALER_GAMMA_BIAS",
        "CTA_MOMENTUM_SCORE",
        "GAMMA_FETCH_OK",
        "CTA_FETCH_OK",
    ]:

        if col in latest.index:
            market_data[col] = latest.get(col)

    market_data["_POS_ASOF"] = (
        latest["date"]
        .strftime("%Y-%m-%d")
    )

    return market_data


# ============================================================
# Historical Institutional Flow
#
# Production institutional_flow_engine_filter의
# CURRENT FLOW scoring logic 복제.
#
# 의도적 차이:
# - load_previous_flow_state() 사용 안 함
# - current flow_state.json 사용 안 함
# - historical SEW unavailable -> neutral 0
# ============================================================

def historical_institutional_flow(
    market_data: Dict[str, Any],
) -> Dict[str, Any]:

    drift = market_data.get(
        "DRIFT",
        {},
    ) or {}

    drift_score = drift.get(
        "score",
        market_data.get(
            "DRIFT_SCORE",
            0,
        ),
    )

    try:
        drift_score = int(
            float(drift_score)
        )
    except Exception:
        drift_score = 0

    drift_label = str(
        drift.get(
            "label",
            "N/A",
        )
        or "N/A"
    )

    gamma_state = str(
        market_data.get(
            "GAMMA_STATE",
            "UNKNOWN",
        )
        or "UNKNOWN"
    ).upper()

    pos_z = market_data.get(
        "SP500_POS_Z",
        0.0,
    )

    try:
        pos_z = float(pos_z)

        if pd.isna(pos_z):
            pos_z = 0.0

    except Exception:
        pos_z = 0.0

    drift_data = market_data.get(
        "DRIFT_DATA",
        {},
    ) or {}

    def g(
        asset: str,
        key: str,
    ):

        try:

            value = (
                drift_data
                .get(asset, {})
                .get(key)
            )

            if value is None:
                return None

            value = float(value)

            if pd.isna(value):
                return None

            return value

        except Exception:
            return None

    flow_score = 0
    reasons = []

    # --------------------------------------------------------
    # 1. Drift core
    # Production 동일
    # --------------------------------------------------------

    if drift_score >= 4:

        flow_score += 3
        reasons.append(
            "Drift strong"
        )

    elif drift_score >= 3:

        flow_score += 2
        reasons.append(
            "Drift building"
        )

    elif drift_score >= 2:

        flow_score += 1
        reasons.append(
            "Drift early"
        )

    # --------------------------------------------------------
    # 2. Label quality
    # Production 동일
    # --------------------------------------------------------

    if drift_label in [
        "DISINFLATION_RISK_ON",
        "SYSTEMIC_HEDGE",
        "TIGHTENING_PRESSURE",
        "OIL_SHOCK",
    ]:

        flow_score += 1

        reasons.append(
            f"Clear flow label: "
            f"{drift_label}"
        )

    # --------------------------------------------------------
    # 3. Short-horizon cluster
    # Production 동일
    # --------------------------------------------------------

    spy_15m = g(
        "SPY",
        "ret_15m",
    )

    spy_30m = g(
        "SPY",
        "ret_30m",
    )

    wti_15m = g(
        "WTI",
        "ret_15m",
    )

    wti_30m = g(
        "WTI",
        "ret_30m",
    )

    gold_15m = g(
        "GOLD",
        "ret_15m",
    )

    gold_30m = g(
        "GOLD",
        "ret_30m",
    )

    dxy_15m = g(
        "DXY",
        "ret_15m",
    )

    dxy_30m = g(
        "DXY",
        "ret_30m",
    )

    short_hits = 0

    if (
        spy_15m is not None
        and spy_15m >= 0.25
    ):
        short_hits += 1

    if (
        spy_30m is not None
        and spy_30m >= 0.40
    ):
        short_hits += 1

    if (
        wti_15m is not None
        and abs(wti_15m) >= 0.60
    ):
        short_hits += 1

    if (
        wti_30m is not None
        and abs(wti_30m) >= 0.90
    ):
        short_hits += 1

    if (
        gold_15m is not None
        and abs(gold_15m) >= 0.30
    ):
        short_hits += 1

    if (
        gold_30m is not None
        and abs(gold_30m) >= 0.45
    ):
        short_hits += 1

    if (
        dxy_15m is not None
        and abs(dxy_15m) >= 0.10
    ):
        short_hits += 1

    if (
        dxy_30m is not None
        and abs(dxy_30m) >= 0.15
    ):
        short_hits += 1

    if short_hits >= 3:

        flow_score += 2

        reasons.append(
            "Short-horizon pre-move cluster"
        )

    elif short_hits >= 2:

        flow_score += 1

        reasons.append(
            "Short-horizon pre-move"
        )

    # --------------------------------------------------------
    # 4. Gamma context
    # Production 동일
    # --------------------------------------------------------

    if "TRANSITION" in gamma_state:

        flow_score += 1

        reasons.append(
            "Gamma transition"
        )

    elif "NEGATIVE" in gamma_state:

        flow_score += 1

        reasons.append(
            "Gamma acceleration regime"
        )

    # --------------------------------------------------------
    # 5. SEW
    #
    # Historical SEW source가 확인되지 않았으므로
    # 현재 insights/sew_state.json 사용 금지.
    #
    # STABLE +1 / WATCH-ALERT -1 모두 적용하지 않는다.
    # --------------------------------------------------------

    sew_status = (
        "HISTORICAL_UNAVAILABLE"
    )

    sew_event_type = (
        "HISTORICAL_UNAVAILABLE"
    )

    # --------------------------------------------------------
    # 6. Positioning
    # Production 동일
    # --------------------------------------------------------

    if pos_z >= 2.0:

        flow_score -= 2

        reasons.append(
            "Positioning overheated"
        )

    elif pos_z >= 1.5:

        flow_score -= 1

        reasons.append(
            "Positioning somewhat stretched"
        )

    # --------------------------------------------------------
    # 6.5 Validation
    # Production 동일
    # --------------------------------------------------------

    validation_score = 0

    hyg_1d = g(
        "HYG",
        "ret_1d",
    )

    lqd_1d = g(
        "LQD",
        "ret_1d",
    )

    eem_1d = g(
        "EEM",
        "ret_1d",
    )

    fxi_1d = g(
        "FXI",
        "ret_1d",
    )

    xlk_1d = g(
        "XLK",
        "ret_1d",
    )

    xli_1d = g(
        "XLI",
        "ret_1d",
    )

    xlf_1d = g(
        "XLF",
        "ret_1d",
    )

    xly_1d = g(
        "XLY",
        "ret_1d",
    )

    xlp_1d = g(
        "XLP",
        "ret_1d",
    )

    xlu_1d = g(
        "XLU",
        "ret_1d",
    )

    risk_participation_hits = 0

    if (
        hyg_1d is not None
        and hyg_1d > 0
    ):
        risk_participation_hits += 1

    if (
        eem_1d is not None
        and eem_1d > 0
    ):
        risk_participation_hits += 1

    if (
        fxi_1d is not None
        and fxi_1d > 0
    ):
        risk_participation_hits += 1

    if risk_participation_hits >= 2:

        validation_score += 1

        reasons.append(
            "Cross-asset risk participation"
        )

    if (
        hyg_1d is not None
        and lqd_1d is not None
        and hyg_1d >= lqd_1d
    ):

        validation_score += 1

        reasons.append(
            "Credit confirms risk appetite"
        )

    leadership_hits = 0

    for value in [
        xlk_1d,
        xli_1d,
        xlf_1d,
        xly_1d,
    ]:

        if (
            value is not None
            and value > 0
        ):
            leadership_hits += 1

    if leadership_hits >= 2:

        validation_score += 1

        reasons.append(
            "Leadership breadth expanding"
        )

    defensive_weak = 0

    for value in [
        xlp_1d,
        xlu_1d,
    ]:

        if (
            value is not None
            and value <= 0
        ):
            defensive_weak += 1

    cyclical_strong = 0

    for value in [
        xli_1d,
        xly_1d,
        xlk_1d,
    ]:

        if (
            value is not None
            and value > 0
        ):
            cyclical_strong += 1

    if (
        cyclical_strong >= 2
        and defensive_weak >= 1
    ):

        validation_score += 1

        reasons.append(
            "Cyclical leadership over defensives"
        )

    validation_boost = min(
        validation_score,
        2,
    )

    flow_score += validation_boost

    # --------------------------------------------------------
    # 7. Flow state
    # Production thresholds 동일
    # --------------------------------------------------------

    if flow_score >= 7:

        flow_state = (
            "🔥 BUILDING HARD"
        )

    elif flow_score >= 5:

        flow_state = (
            "⚡ BUILDING"
        )

    elif flow_score >= 3:

        flow_state = (
            "👀 EARLY TRACE"
        )

    elif flow_score >= 1:

        flow_state = (
            "🌱 LIGHT TRACE"
        )

    else:

        flow_state = (
            "NO CLEAR FLOW"
        )

    flow = {
        "score":
            int(flow_score),

        "state":
            flow_state,

        "reasons":
            reasons,

        "drift_label":
            drift_label,

        "gamma_state":
            gamma_state,

        "sew_status":
            sew_status,

        "sew_event_type":
            sew_event_type,

        "validation_score":
            validation_score,

        "validation_boost":
            validation_boost,
    }

    market_data[
        "INSTITUTIONAL_FLOW"
    ] = flow

    return flow


# ============================================================
# Main
# ============================================================

def main():

    df = load_backtest_macro_df()

    df = (
        merge_sovereign_spreads_into_macro_df(
            df
        )
    )

    dates = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    selected_indices = df.index[
        (dates >= pd.Timestamp(
            "2022-01-01"
        ))
        &
        (dates <= pd.Timestamp(
            "2022-06-30"
        ))
    ]

    # Phase 2 gate:
    # 첫 10거래일만 검증
    selected_indices = list(
        selected_indices
    )[:10]

    print(
        "[PHASE2] rows:",
        len(selected_indices),
    )

    rows = []

    # --------------------------------------------------------
    # 핵심:
    # 현재 JSON 파일이 아니라
    # 직전 loop의 Flow만 기억한다.
    # --------------------------------------------------------

    previous_flow = None

    for count, idx in enumerate(
        selected_indices,
        start=1,
    ):

        signal_date = pd.to_datetime(
            df.iloc[idx]["date"]
        )

        try:

            market_data = (
                build_market_data(
                    df,
                    idx,
                )
            )

            # -----------------------------------------------
            # Historical layers
            # -----------------------------------------------

            market_data = (
                attach_liquidity_layer(
                    market_data
                )
                or market_data
            )

            market_data = (
                attach_credit_spread_layer(
                    market_data
                )
                or market_data
            )

            market_data = (
                attach_fred_extras_layer(
                    market_data
                )
                or market_data
            )

            market_data = (
                attach_sovereign_spread_layer(
                    market_data
                )
                or market_data
            )

            market_data = (
                attach_positioning_layer_backtest(
                    market_data,
                    df,
                    idx,
                )
            )

            market_data = (
                attach_sentiment_proxy_layer(
                    market_data
                )
                or market_data
            )

            market_data = (
                attach_sector_momentum_layer(
                    market_data,
                    df,
                    idx,
                )
                or market_data
            )

            market_data = (
                attach_drift_data_layer(
                    market_data
                )
                or market_data
            )

            market_data = (
                attach_growth_sustainability_layer(
                    market_data,
                    df,
                    idx,
                )
                or market_data
            )

            market_data = (
                attach_breadth_layer(
                    market_data,
                    df,
                    idx,
                )
                or market_data
            )

            market_data = (
                attach_leadership_layer(
                    market_data,
                    df,
                    idx,
                )
                or market_data
            )

            # -----------------------------------------------
            # Production 상대 순서
            # -----------------------------------------------

            market_regime_filter(
                market_data
            )

            liquidity_filter(
                market_data
            )

            policy_filter_with_expectations(
                market_data
            )

            high_yield_spread_filter(
                market_data
            )

            credit_stress_filter(
                market_data
            )

            drift_monitor_filter(
                market_data
            )

            # Historical SEW를 현재 JSON에서 읽지 않는다.
            market_data[
                "SEW_STATUS"
            ] = "HISTORICAL_UNAVAILABLE"

            market_data[
                "SEW_EVENT_TYPE"
            ] = "HISTORICAL_UNAVAILABLE"

            pseudo_gamma_filter(
                market_data
            )

            # -----------------------------------------------
            # T-1 PREV FLOW 주입
            #
            # 반드시 CURRENT FLOW 계산 전에
            # 직전 거래일 결과만 넣는다.
            # -----------------------------------------------

            if previous_flow is None:

                prev_flow_score = 0

                prev_flow_state = "N/A"

            else:

                prev_flow_score = int(
                    previous_flow[
                        "score"
                    ]
                )

                prev_flow_state = str(
                    previous_flow[
                        "state"
                    ]
                )

            market_data[
                "PREV_FLOW_SCORE"
            ] = prev_flow_score

            market_data[
                "PREV_FLOW_STATE"
            ] = prev_flow_state

            # -----------------------------------------------
            # Current historical Flow
            # -----------------------------------------------

            current_flow = (
                historical_institutional_flow(
                    market_data
                )
            )

            structural_filter(
                market_data
            )

            # -----------------------------------------------
            # PIT validation
            # -----------------------------------------------

            if count == 1:

                pit_status = (
                    "FIRST_ROW"
                )

            else:

                expected_score = int(
                    rows[-1][
                        "current_flow_score"
                    ]
                )

                expected_state = str(
                    rows[-1][
                        "current_flow_state"
                    ]
                )

                if (
                    prev_flow_score
                    == expected_score
                    and
                    prev_flow_state
                    == expected_state
                ):

                    pit_status = "PASS"

                else:

                    pit_status = "FAIL"

            drift = market_data.get(
                "DRIFT",
                {},
            ) or {}

            row = {

                "date":
                    signal_date.strftime(
                        "%Y-%m-%d"
                    ),

                "drift_score":
                    drift.get(
                        "score",
                        market_data.get(
                            "DRIFT_SCORE"
                        ),
                    ),

                "gamma_state":
                    market_data.get(
                        "GAMMA_STATE"
                    ),

                "sew_status":
                    "HISTORICAL_UNAVAILABLE",

                "current_flow_score":
                    current_flow[
                        "score"
                    ],

                "current_flow_state":
                    current_flow[
                        "state"
                    ],

                "prev_flow_score":
                    prev_flow_score,

                "prev_flow_state":
                    prev_flow_state,

                "validation_score":
                    current_flow[
                        "validation_score"
                    ],

                "validation_boost":
                    current_flow[
                        "validation_boost"
                    ],

                "pit_status":
                    pit_status,
            }

            rows.append(row)

            # -----------------------------------------------
            # 오늘 결과를 저장.
            #
            # 다음 loop에서만 PREV가 된다.
            # -----------------------------------------------

            previous_flow = {
                "score":
                    current_flow[
                        "score"
                    ],

                "state":
                    current_flow[
                        "state"
                    ],
            }

            print(
                f"[PHASE2] "
                f"{count}/"
                f"{len(selected_indices)} "
                f"{signal_date.date()} "
                f"PREV="
                f"{prev_flow_score} "
                f"CURRENT="
                f"{current_flow['score']} "
                f"{pit_status}"
            )

        except Exception as exc:

            print(
                "[ERROR]",
                signal_date,
                repr(exc),
            )

            rows.append({

                "date":
                    signal_date.strftime(
                        "%Y-%m-%d"
                    ),

                "pit_status":
                    "ERROR",

                "error":
                    repr(exc),
            })

            # 오류가 난 날짜의 잘못된 값을
            # 다음 날짜 PREV로 넘기지 않는다.
            previous_flow = None

    # ========================================================
    # Save
    # ========================================================

    result = pd.DataFrame(
        rows
    )

    out = (
        OUTPUT_DIR
        / "filter13_flow_phase2_gate.csv"
    )

    result.to_csv(
        out,
        index=False,
        encoding="utf-8-sig"

        )

    print()
    print("[SAVED]", out)

    if "pit_status" in result.columns:
        print()
        print("[PIT STATUS]")
        print(
            result["pit_status"]
            .value_counts(dropna=False)
            .to_string()
        )

    failed = result[
        result["pit_status"] != "PASS"
    ]

    if not failed.empty:
        print()
        print("[FIRST FAILED ROWS]")

        cols = [
            c
            for c in (
                "date",
                "pit_status",
                "error",
            )
            if c in failed.columns
        ]

        print(
            failed[cols]
            .head(20)
            .to_string(index=False)
        )

    print()
    print("PHASE 2 COMPLETE.")


if __name__ == "__main__":
    main()