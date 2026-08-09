from __future__ import annotations

from typing import Any

import filters.strategist_filters as sf


def prepare_filter13_execution_state(
    market_data: dict[str, Any],
    previous_flow_memory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Backtest Pre-Filter13 Execution Adapter.

    역할
    ----
    Production에서 Filter13 이전에 생성되는 state를
    동일한 Production 함수와 동일한 실행 순서로 재현한다.

    Flow History
    ------------
    Production의 현재 insights/flow_state.json은 과거 Backtest에 사용하지 않는다.
    대신 Backtest가 직전 날짜의 historical flow memory를 전달한다.

    반환값
    ------
    다음 Backtest 날짜에 사용할 flow memory:
    {
        "flow_state": ...,
        "flow_score": ...,
        "persistence_days": ...,
    }
    """

    previous_flow_memory = previous_flow_memory or {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    # Filter13이 직접 읽는 이전 Flow Contract
    market_data["PREV_FLOW_STATE"] = previous_flow_memory.get(
        "flow_state",
        "N/A",
    )
    market_data["PREV_FLOW_SCORE"] = previous_flow_memory.get(
        "flow_score",
        0,
    )

    # --------------------------------------------------
    # Production Pre-13 execution order
    # --------------------------------------------------

    sf.market_regime_filter(market_data)

    sf.policy_filter_with_expectations(market_data)

    sf.drift_monitor_filter(market_data)

    sf.pseudo_gamma_filter(market_data)

    # --------------------------------------------------
    # Historical Flow Loader Override
    #
    # Production IFE는 load_previous_flow_state()를 내부 호출한다.
    # Backtest에서는 현재 flow_state.json 대신 t-1 historical memory 사용.
    # --------------------------------------------------

    original_loader = sf.load_previous_flow_state

    try:
        sf.load_previous_flow_state = lambda *args, **kwargs: dict(
            previous_flow_memory
        )

        sf.institutional_flow_engine_filter(market_data)

    finally:
        sf.load_previous_flow_state = original_loader

    sf.structural_filter(market_data)

    # --------------------------------------------------
    # Next-day Flow Memory
    #
    # INSTITUTIONAL_FLOW에는 raw current flow가 저장됨.
    # Production과 동일하게 transition 함수로 상태 전환을 계산해
    # 다음 날짜 memory를 만든다.
    # --------------------------------------------------

    institutional_flow = market_data.get("INSTITUTIONAL_FLOW", {}) or {}

    current_flow_state = institutional_flow.get(
        "state",
        "NO CLEAR FLOW",
    )
    current_flow_score = institutional_flow.get(
        "score",
        0,
    )

    transition_info = sf.classify_flow_transition(
        prev_flow_state=str(
            previous_flow_memory.get("flow_state", "N/A")
        ),
        prev_flow_score=int(
            previous_flow_memory.get("flow_score", 0) or 0
        ),
        current_flow_state=str(current_flow_state),
        current_flow_score=int(current_flow_score or 0),
        prev_persistence_days=int(
            previous_flow_memory.get("persistence_days", 0) or 0
        ),
    )

    return {
        "flow_state": transition_info.get(
            "flow_state",
            current_flow_state,
        ),
        "flow_score": transition_info.get(
            "flow_score",
            current_flow_score,
        ),
        "persistence_days": transition_info.get(
            "persistence_days",
            0,
        ),
    }
