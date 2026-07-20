"""
Filter13 Budget Attribution - FINAL PIT AUDIT

목적
----
13번 Narrative Engine이 Risk Budget을 어디에서 얼마나 변경했는지
historical Point-in-Time 방식으로 attribution한다.

검증된 기반
-----------
Phase 1:
- audit_filter13_budget_attribution_v2.py
- Historical PIT dependency harness

Phase 2:
- audit_filter13_flow_phase2.py
- Historical Institutional Flow
- T-1 PREV_FLOW replay

원칙
----
- Production 코드 수정 금지
- 미래 데이터 사용 금지
- insights/flow_state.json 사용 금지
- insights/sew_state.json 사용 금지
- Historical SEW unavailable -> neutral 0
- PREV_FLOW는 직전 거래일 계산값만 사용
- 우선 2022년 첫 10거래일만 검증
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "backtest"))

DATA_DIR = ROOT / "data" / "backtest"
OUTPUT_DIR = DATA_DIR / "results"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Verified Phase 1 infrastructure
# ============================================================

from audit_filter13_budget_attribution_v2 import (
    load_backtest_macro_df,
    attach_positioning_layer_backtest,
    attach_pit_external_layers,
)


# ============================================================
# Verified Phase 2 historical flow
# ============================================================

from audit_filter13_flow_phase2 import (
    historical_institutional_flow,
)


# ============================================================
# Existing production infrastructure
# ============================================================

from scripts.generate_report import (
    build_market_data,
    merge_sovereign_spreads_into_macro_df,
    attach_geopolitical_ew_layer,
    attach_country_risk_layer,
    attach_sector_momentum_layer,
    attach_geo_similarity_layer,
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


# ============================================================
# Helpers
# ============================================================

def _to_float(
    value: Any,
) -> Optional[float]:

    if value is None:
        return None

    if isinstance(
        value,
        (int, float),
    ):
        try:
            value = float(value)

            if pd.isna(value):
                return None

            return value

        except Exception:
            return None

    try:

        value = float(
            str(value)
            .replace(",", "")
            .replace("%", "")
        )

        if pd.isna(value):
            return None

        return value

    except Exception:
        return None


def _clamp(
    value: int,
    lo: int = 0,
    hi: int = 100,
) -> int:

    return max(
        lo,
        min(
            hi,
            int(value),
        ),
    )


def _sentiment_state(
    fear: Optional[float],
) -> str:

    if fear is None:
        return "N/A"

    if fear < 30:
        return "FEAR"

    if fear > 70:
        return "GREED"

    return "NEUTRAL"


def _liq_dir_tag(
    pct: Optional[float],
) -> str:

    if pct is None:
        return "N/A"

    if pct > 0:
        return "UP"

    if pct < 0:
        return "DOWN"

    return "FLAT"


# ============================================================
# Filter13 Budget Attribution
#
# strategist_filters.py narrative_engine_filter()
# Budget calculation logic only.
#
# Production 함수는 호출하지 않는다.
# 이유:
# - FINAL_STATE 등 side effect 방지
# - 각 단계별 attribution을 정확히 기록하기 위함
# ============================================================

def calculate_filter13_budget_attribution(
    market_data: Dict[str, Any],
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # Pull signals
    # --------------------------------------------------------

    struct_v2 = str(
        market_data.get(
            "STRUCT_V2_STATE",
            "NEUTRAL",
        )
        or "NEUTRAL"
    ).upper()

    policy_bias_line = str(
        market_data.get(
            "POLICY_BIAS_LINE",
            "",
        )
        or ""
    )

    sentiment = (
        market_data.get(
            "SENTIMENT",
            {},
        )
        or {}
    )

    fear = _to_float(
        sentiment.get(
            "fear_greed"
        )
    )

    sent_state = (
        _sentiment_state(
            fear
        )
    )

    hy_oas = (
        market_data.get(
            "HY_OAS",
            {},
        )
        or {}
    )

    if isinstance(
        hy_oas,
        dict,
    ):
        hy_oas_today = _to_float(
            hy_oas.get(
                "today"
            )
        )
    else:
        hy_oas_today = _to_float(
            hy_oas
        )

    credit_calm = None

    if hy_oas_today is not None:
        credit_calm = (
            hy_oas_today < 4.0
        )

    net_liq = (
        market_data.get(
            "NET_LIQ",
            {},
        )
        or {}
    )

    if isinstance(
        net_liq,
        dict,
    ):
        net_liq_pct = _to_float(
            net_liq.get(
                "pct_change"
            )
        )
    else:
        net_liq_pct = None

    liq_dir_tag = (
        _liq_dir_tag(
            net_liq_pct
        )
    )

    liq_level_bucket = str(
        (
            net_liq.get(
                "level_bucket"
            )
            if isinstance(
                net_liq,
                dict,
            )
            else None
        )
        or market_data.get(
            "NET_LIQ_LEVEL_BUCKET"
        )
        or "N/A"
    ).upper()

    if liq_level_bucket not in (
        "HIGH",
        "MID",
        "LOW",
    ):
        liq_level_bucket = "N/A"

    phase = market_data.get(
        "MARKET_REGIME",
        "N/A",
    )

    phase_upper = str(
        phase
    ).upper()

    macro_narrative = str(
        market_data.get(
            "MACRO_NARRATIVE",
            "N/A",
        )
        or "N/A"
    ).upper()

    policy_upper = (
        policy_bias_line.upper()
    )

    mixed = (
        "MIXED"
        in policy_upper
    )

    easing = (
        "EASING"
        in policy_upper
    )

    tightening = (
        "TIGHTENING"
        in policy_upper
    )

    pos_z = _to_float(
        market_data.get(
            "SP500_POS_Z",
            0.0,
        )
    )

    if pos_z is None:
        pos_z = 0.0

    drift = (
        market_data.get(
            "DRIFT",
            {},
        )
        or {}
    )

    drift_score = (
        drift.get(
            "score",
            market_data.get(
                "DRIFT_SCORE",
                0,
            ),
        )
        if isinstance(
            drift,
            dict,
        )
        else market_data.get(
            "DRIFT_SCORE",
            0,
        )
    )

    try:
        drift_score = int(
            float(drift_score)
        )
    except Exception:
        drift_score = 0

    flow = (
        market_data.get(
            "INSTITUTIONAL_FLOW",
            {},
        )
        or {}
    )

    flow_score = (
        flow.get(
            "score",
            0,
        )
        if isinstance(
            flow,
            dict,
        )
        else 0
    )

    try:
        flow_score = int(
            float(flow_score)
        )
    except Exception:
        flow_score = 0

    gamma_state = str(
        market_data.get(
            "GAMMA_STATE",
            "N/A",
        )
        or "N/A"
    ).upper()

    prev_flow_state = str(
        market_data.get(
            "PREV_FLOW_STATE",
            "N/A",
        )
        or "N/A"
    ).upper()

    prev_flow_score = _to_float(
        market_data.get(
            "PREV_FLOW_SCORE",
            0,
        )
    )

    if prev_flow_score is None:
        prev_flow_score = 0.0

    # ========================================================
    # 1. Base Budget
    # ========================================================

    if sent_state == "FEAR":
        budget = 35

    elif sent_state == "GREED":
        budget = 70

    elif sent_state == "NEUTRAL":
        budget = 55

    else:
        budget = 50

    base_budget = budget

    # ========================================================
    # 2. Structure
    # ========================================================

    before = budget

    if not mixed:

        if (
            easing
            and not tightening
        ):
            budget += 10

        elif (
            tightening
            and not easing
        ):
            budget -= 10

    structure_delta = (
        budget - before
    )

    # ========================================================
    # 3. Credit
    # ========================================================

    before = budget

    if credit_calm is True:
        budget += 5

    elif credit_calm is False:
        budget -= 10

    credit_delta = (
        budget - before
    )

    # ========================================================
    # 4. Liquidity
    # ========================================================

    before = budget

    if liq_dir_tag == "UP":
        budget += 5

    elif liq_dir_tag == "DOWN":
        budget -= 10

    if liq_level_bucket == "HIGH":
        budget += 5

    elif liq_level_bucket == "LOW":
        budget -= 5

    liquidity_delta = (
        budget - before
    )

    # ========================================================
    # 5. Structural v2
    # ========================================================

    before = budget

    v2_cap = 100

    vix_block = (
        market_data.get(
            "VIX",
            {},
        )
        or {}
    )

    if isinstance(
        vix_block,
        dict,
    ):

        vix_today = _to_float(
            vix_block.get(
                "today"
            )
        )

        vix_pct = _to_float(
            vix_block.get(
                "pct_change"
            )
        )

    else:

        vix_today = None
        vix_pct = None

    credit_stress = (
        credit_calm is False
    )

    liq_stress = (
        liq_dir_tag == "DOWN"
        and
        liq_level_bucket == "LOW"
    )

    vol_stress = (
        (
            vix_today is not None
            and
            vix_today >= 25
        )
        or
        (
            vix_pct is not None
            and
            vix_pct >= 25
        )
    )

    systemic_confirmed = (
        "SYSTEMIC" in struct_v2
        and
        (
            credit_stress
            or liq_stress
            or vol_stress
        )
    )

    systemic_watch = (
        "SYSTEMIC" in struct_v2
        and
        not systemic_confirmed
    )

    if systemic_confirmed:

        budget -= 20
        v2_cap = 30

    elif systemic_watch:

        budget -= 4
        v2_cap = 70

    elif "STAGFLATION" in struct_v2:

        budget -= 15
        v2_cap = 40

    structural_v2_delta = (
        budget - before
    )

    # ========================================================
    # 6. Drift
    # ========================================================

    before = budget

    drift_tilt = 0

    if drift_score >= 6:
        drift_tilt = 3

    elif drift_score >= 3:
        drift_tilt = 1

    elif drift_score <= -3:
        drift_tilt = -3

    budget += drift_tilt

    drift_delta = (
        budget - before
    )

    # ========================================================
    # 7. Flow Gamma
    # ========================================================

    before = budget

    flow_gamma_tilt = 0

    if (
        drift_score >= 3
        and
        flow_score >= 3
        and
        "TRANSITION"
        in gamma_state
    ):

        flow_gamma_tilt = 2

    elif (
        drift_score >= 5
        and
        flow_score >= 4
        and
        "POSITIVE"
        in gamma_state
    ):

        flow_gamma_tilt = 4

    budget += flow_gamma_tilt

    flow_gamma_delta = (
        budget - before
    )

    # ========================================================
    # 8. Flow Continuity
    # ========================================================

    before = budget

    flow_continuity_tilt = 0

    if (
        "NO CLEAR FLOW"
        in prev_flow_state
        and
        flow_score >= 3
    ):

        flow_continuity_tilt = 2

    elif (
        "EARLY TRACE"
        in prev_flow_state
        and
        flow_score >= 5
    ):

        flow_continuity_tilt = 3

    elif (
        (
            "EARLY TRACE"
            in prev_flow_state
            or
            "BUILDING"
            in prev_flow_state
        )
        and
        flow_score <= 2
    ):

        flow_continuity_tilt = -3

    elif (
        prev_flow_score >= 3
        and
        flow_score >= 3
    ):

        flow_continuity_tilt = 1

    budget += (
        flow_continuity_tilt
    )

    flow_continuity_delta = (
        budget - before
    )

    # ========================================================
    # 9. Flow Regime
    # ========================================================

    before = budget

    flow_regime_tilt = 0

    if flow_score >= 7:
        flow_regime_tilt = 4

    elif flow_score >= 5:
        flow_regime_tilt = 3

    elif flow_score >= 3:
        flow_regime_tilt = 2

    elif flow_score >= 1:
        flow_regime_tilt = 1

    if (
        "SOFT RISK-OFF"
        in phase_upper
        and
        flow_score >= 3
    ):

        flow_regime_tilt += 1

    if (
        (
            "EVENT-WATCHING"
            in phase_upper
            or
            "WAITING"
            in phase_upper
        )
        and
        flow_score >= 5
    ):

        flow_regime_tilt += 2

    budget += flow_regime_tilt

    flow_regime_delta = (
        budget - before
    )

    # ========================================================
    # 10. Macro
    # ========================================================

    before = budget

    macro_tilt = 0

    if "GOLDILOCKS" in phase_upper:
        macro_tilt += 8

    elif "REFLATION" in phase_upper:
        macro_tilt += 6

    elif "LIQUIDITY" in phase_upper:
        macro_tilt += 5

    elif (
        "TIGHTENING_GROWTH_SCARE"
        in macro_narrative
    ):
        macro_tilt -= 8

    elif "STAGFLATION" in phase_upper:
        macro_tilt -= 12

    elif (
        "INFLATION SHOCK"
        in phase_upper
    ):
        macro_tilt -= 12

    elif "INFLATION" in phase_upper:
        macro_tilt -= 6

    elif (
        "HARD RISK-OFF"
        in phase_upper
    ):
        macro_tilt -= 20

    budget += macro_tilt

    macro_delta = (
        budget - before
    )

    # ========================================================
    # 11. Positioning
    # ========================================================

    before = budget

    if pos_z >= 2.0:
        budget -= 8

    elif pos_z >= 1.5:
        budget -= 4

    positioning_delta = (
        budget - before
    )

    # ========================================================
    # 12. Event Floor
    #
    # Floor는 감산이 아니라 budget을 올릴 수도 있으므로
    # delta 그대로 기록.
    # ========================================================

    before = budget

    if (
        (
            "EVENT-WATCHING"
            in phase_upper
            or
            "WAITING"
            in phase_upper
        )
        and
        credit_calm is True
    ):

        budget = max(
            budget,
            25,
        )

    event_floor_delta = (
        budget - before
    )

    pre_cap_budget = budget

    # ========================================================
    # 13. Phase Cap
    # ========================================================

    cap = 100

    if (
        phase_upper.startswith(
            "WAITING"
        )
        or
        "RANGE"
        in phase_upper
    ):

        cap = 60

    elif phase_upper.startswith(
        "HARD RISK-OFF"
    ):

        cap = 20

    elif phase_upper.startswith(
        "SOFT RISK-OFF"
    ):

        cap = (
            50
            if flow_score >= 3
            else 45
        )

    elif "RISK-OFF" in phase_upper:

        cap = 35

    elif (
        "MIXED / FRAGILE"
        in phase_upper
    ):

        cap = 55

    elif (
        phase_upper.startswith(
            "TRANSITION"
        )
        or
        "MIXED"
        in phase_upper
    ):

        cap = 65

    elif phase_upper.startswith(
        "RISK-ON"
    ):

        cap = 85

    if (
        "SYSTEMIC"
        in struct_v2
        or
        "STAGFLATION"
        in struct_v2
    ):

        cap = min(
            cap,
            30,
        )

    # Phase cap의 실제 효과를 별도 계산
    phase_cap_effect = (
        min(
            int(round(budget)),
            cap,
        )
        -
        int(round(budget))
    )

    # ========================================================
    # 14. Final Cap
    # ========================================================

    final_cap = min(
        cap,
        v2_cap,
    )

    rounded_pre_cap = int(
        round(
            budget
        )
    )

    final_cap_effect = (
        min(
            rounded_pre_cap,
            final_cap,
        )
        -
        min(
            rounded_pre_cap,
            cap,
        )
    )

    # ========================================================
    # 15. Final Budget
    # ========================================================

    final_budget = min(
        rounded_pre_cap,
        final_cap,
    )

    final_budget = _clamp(
        final_budget,
        0,
        100,
    )

    # ========================================================
    # Output
    # ========================================================

    return {

        # Raw dependencies
        "sentiment_fear_greed":
            fear,

        "sentiment_state":
            sent_state,

        "policy_bias_line":
            policy_bias_line,

        "hy_oas_today":
            hy_oas_today,

        "net_liq_pct_change":
            net_liq_pct,

        "net_liq_level_bucket":
            liq_level_bucket,

        "struct_v2_state":
            struct_v2,

        "drift_score":
            drift_score,

        "gamma_state":
            gamma_state,

        "flow_score":
            flow_score,

        "prev_flow_score":
            prev_flow_score,

        "prev_flow_state":
            prev_flow_state,

        "macro_narrative":
            macro_narrative,

        "market_regime":
            phase,

        "sp500_pos_z":
            pos_z,

        # Attribution
        "base_budget":
            base_budget,

        "structure_delta":
            structure_delta,

        "credit_delta":
            credit_delta,

        "liquidity_delta":
            liquidity_delta,

        "structural_v2_delta":
            structural_v2_delta,

        "drift_delta":
            drift_delta,

        "flow_gamma_delta":
            flow_gamma_delta,

        "flow_continuity_delta":
            flow_continuity_delta,

        "flow_regime_delta":
            flow_regime_delta,

        "macro_delta":
            macro_delta,

        "positioning_delta":
            positioning_delta,

        "event_floor_delta":
            event_floor_delta,

        "pre_cap_budget":
            pre_cap_budget,

        "phase_cap":
            cap,

        "phase_cap_effect":
            phase_cap_effect,

        "v2_cap":
            v2_cap,

        "final_cap":
            final_cap,

        "final_cap_effect":
            final_cap_effect,

        "final_budget":
            final_budget,
    }


# ============================================================
# Main
# ============================================================

def main() -> None:

    df = (
        load_backtest_macro_df()
    )

    df = (
        merge_sovereign_spreads_into_macro_df(
            df
        )
    )

    dates = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    selected_indices = list(
        df.index[
            (
                dates
                >= pd.Timestamp(
                    "2022-01-01"
                )
            )
            &
            (
                dates
                <= pd.Timestamp(
                    "2022-01-31"
                )
            )
        ]
    )

    # --------------------------------------------------------
    # Gate run:
    # 먼저 10거래일만.
    # 이게 PASS한 뒤 전체 2022 H1로 확장한다.
    # --------------------------------------------------------

    selected_indices = list(selected_indices)

    print(
        "[FINAL AUDIT] rows:",
        len(selected_indices),
    )

    rows = []

    previous_flow = None

    for count, idx in enumerate(
        selected_indices,
        start=1,
    ):

        signal_date = pd.to_datetime(
            df.iloc[idx]["date"]
        )

        try:

            # =================================================
            # 1. Historical base
            # =================================================

            market_data = (
                build_market_data(
                    df,
                    idx,
                )
            )

            # =================================================
            # 2. VERIFIED PHASE 1 PIT EXTERNAL DATA
            #
            # 중요:
            # attach_liquidity_layer 등을 직접 호출하지 않는다.
            #
            # 이 함수가 signal_date cutoff를 적용해서
            # HY OAS / Liquidity / FRED / Sovereign /
            # Sentiment의 최신값 유입을 차단한다.
            # =================================================

            market_data = (
                attach_pit_external_layers(
                    market_data,
                    signal_date,
                )
            )

            # =================================================
            # 3. Historical positioning
            # =================================================

            market_data = (
                attach_positioning_layer_backtest(
                    market_data,
                    df,
                    idx,
                )
            )

            # =================================================
            # 4. Historical derived layers
            # =================================================

            market_data = (
                attach_geopolitical_ew_layer(
                    market_data,
                    df,
                    idx,
                )
                or market_data
            )

            market_data = (
                attach_country_risk_layer(
                    market_data,
                    df,
                    idx,
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
                attach_geo_similarity_layer(
                    market_data
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

            # =================================================
            # 5. Dependency producers
            # =================================================

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

            # Historical SEW:
            # current JSON 사용 금지
            market_data[
                "SEW_STATUS"
            ] = (
                "HISTORICAL_UNAVAILABLE"
            )

            market_data[
                "SEW_EVENT_TYPE"
            ] = (
                "HISTORICAL_UNAVAILABLE"
            )

            pseudo_gamma_filter(
                market_data
            )

            # =================================================
            # 6. T-1 PREV FLOW
            # =================================================

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

            # =================================================
            # 7. Historical Current Flow
            # =================================================

            current_flow = (
                historical_institutional_flow(
                    market_data
                )
            )

            # =================================================
            # 8. Structural state
            # =================================================

            structural_filter(
                market_data
            )

            # =================================================
            # 9. Budget Attribution
            # =================================================

            attribution = (
                calculate_filter13_budget_attribution(
                    market_data
                )
            )

            # =================================================
            # 10. PIT sanity
            # =================================================

            if count == 1:

                pit_status = (
                    "FIRST_ROW"
                )

            else:

                expected_prev = (
                    rows[-1][
                        "flow_score"
                    ]
                )

                if (
                    int(
                        prev_flow_score
                    )
                    ==
                    int(
                        expected_prev
                    )
                ):

                    pit_status = "PASS"

                else:

                    pit_status = "FAIL"

            row = {

                "date":
                    signal_date.strftime(
                        "%Y-%m-%d"
                    ),

                "pit_status":
                    pit_status,

                "_liq_asof":
                    market_data.get(
                        "_LIQ_ASOF"
                    ),

                "_hy_asof":
                    market_data.get(
                        "_HY_ASOF"
                    ),

                "_fred_asof":
                    market_data.get(
                        "_FRED_ASOF"
                    ),

                "_sov_asof":
                    market_data.get(
                        "_SOV_ASOF"
                    ),

                "_sentiment_asof":
                    (
                        market_data
                        .get(
                            "SENTIMENT",
                            {},
                        )
                        .get(
                            "as_of"
                        )
                        if isinstance(
                            market_data.get(
                                "SENTIMENT"
                            ),
                            dict,
                        )
                        else None
                    ),

                "_pos_asof":
                    market_data.get(
                        "_POS_ASOF"
                    ),

                **attribution,
            }

            rows.append(
                row
            )

            # =================================================
            # 11. Save current flow for T+1
            # =================================================

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
                "[FINAL AUDIT]",
                f"{count}/"
                f"{len(selected_indices)}",
                signal_date.date(),
                f"PREV={prev_flow_score}",
                f"FLOW="
                f"{current_flow['score']}",
                f"BASE="
                f"{attribution['base_budget']}",
                f"FINAL="
                f"{attribution['final_budget']}",
                pit_status,
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

            # 잘못된 날짜 결과는
            # 다음 거래일 PREV로 넘기지 않는다.
            previous_flow = None

    # ========================================================
    # Save daily
    # ========================================================

    result = pd.DataFrame(
        rows
    )

    daily_out = (
        OUTPUT_DIR
        / "filter13_budget_attribution_final_daily.csv"
    )

    result.to_csv(
        daily_out,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        "[SAVED]",
        daily_out,
    )

    # ========================================================
    # Summary
    # ========================================================

    attribution_cols = [

        "structure_delta",
        "credit_delta",
        "liquidity_delta",
        "structural_v2_delta",
        "drift_delta",
        "flow_gamma_delta",
        "flow_continuity_delta",
        "flow_regime_delta",
        "macro_delta",
        "positioning_delta",
        "event_floor_delta",
        "phase_cap_effect",
        "final_cap_effect",
    ]

    valid_cols = [

        col

        for col
        in attribution_cols

        if col
        in result.columns
    ]

    summary_rows = []

    for col in valid_cols:

        series = pd.to_numeric(
            result[col],
            errors="coerce",
        )

        summary_rows.append({

            "component":
                col,

            "avg_effect":
                series.mean(),

            "total_effect":
                series.sum(),

            "negative_days":
                int(
                    (
                        series < 0
                    ).sum()
                ),

            "positive_days":
                int(
                    (
                        series > 0
                    ).sum()
                ),

            "zero_days":
                int(
                    (
                        series == 0
                    ).sum()
                ),

            "avg_negative_effect":
                (
                    series[
                        series < 0
                    ].mean()
                    if (
                        series < 0
                    ).any()
                    else 0.0
                ),
        })

    summary = pd.DataFrame(
        summary_rows
    )

    if not summary.empty:

        summary = (
            summary
            .sort_values(
                "total_effect",
                ascending=True,
            )
            .reset_index(
                drop=True
            )
        )

    summary_out = (
        OUTPUT_DIR
        / "filter13_budget_attribution_final_summary.csv"
    )

    summary.to_csv(
        summary_out,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "[SAVED]",
        summary_out,
    )

    # ========================================================
    # Human-readable summary
    # ========================================================

    txt_out = (
        OUTPUT_DIR
        / "filter13_budget_attribution_final_summary.txt"
    )

    with open(
        txt_out,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            "FILTER13 BUDGET ATTRIBUTION "
            "FINAL AUDIT\n"
        )

        f.write(
            "=" * 70
            + "\n\n"
        )

        f.write(
            f"Rows: "
            f"{len(result)}\n"
        )

        if (
            "final_budget"
            in result.columns
        ):

            final_series = (
                pd.to_numeric(
                    result[
                        "final_budget"
                    ],
                    errors="coerce",
                )
            )

            f.write(
                "Average Final Budget: "
                f"{final_series.mean():.2f}\n"
            )

        if (
            "base_budget"
            in result.columns
        ):

            base_series = (
                pd.to_numeric(
                    result[
                        "base_budget"
                    ],
                    errors="coerce",
                )
            )

            f.write(
                "Average Base Budget: "
                f"{base_series.mean():.2f}\n"
            )

        f.write(
            "\nCOMPONENT ATTRIBUTION\n"
        )

        f.write(
            "-" * 70
            + "\n"
        )

        if not summary.empty:

            f.write(
                summary.to_string(
                    index=False
                )
            )

            f.write("\n")

    print(
        "[SAVED]",
        txt_out,
    )

    print()

    if (
        "pit_status"
        in result.columns
    ):

        print(
            "[PIT STATUS]"
        )

        print(
            result[
                "pit_status"
            ]
            .value_counts(
                dropna=False
            )
            .to_string()
        )

    print()
    print(
        "FINAL FILTER13 "
        "ATTRIBUTION GATE COMPLETE."
    )

    print(
        "Do not expand beyond "
        "10 trading days until "
        "the output is reviewed."
    )


if __name__ == "__main__":
    main()