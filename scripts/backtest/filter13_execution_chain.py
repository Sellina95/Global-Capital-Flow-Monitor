from __future__ import annotations

from typing import Any

import pandas as pd

import filters.strategist_filters as sf


# ============================================================
# Historical / PIT DRIFT_DATA Producer
# ============================================================

DRIFT_COLUMN_CANDIDATES = {
    "SPY": ["SPY"],
    "RSP": ["RSP"],
    "QQQE": ["QQQE"],
    "WTI": ["WTI"],
    "DXY": ["DXY"],
    "GOLD": ["GOLD"],
    "HYG": ["HYG"],
    "LQD": ["LQD"],
    "EEM": ["EEM", "country_etf__EEM"],
    "FXI": ["FXI", "country_etf__FXI"],
    "XLK": ["XLK"],
    "XLI": ["XLI"],
    "XLF": ["XLF"],
    "XLY": ["XLY"],
    "XLP": ["XLP"],
    "XLU": ["XLU"],
}


def _resolve_drift_column(
    panel: pd.DataFrame,
    candidates: list[str],
) -> str | None:
    """
    DRIFT asset에 대응하는 실제 master_panel 컬럼을 찾는다.
    """
    for col in candidates:
        if col in panel.columns:
            return col

    return None


def _historical_return(
    panel: pd.DataFrame,
    row_index: int,
    column: str | None,
    periods: int,
) -> float:
    """
    현재 row_index 시점까지의 데이터만 이용해
    N거래일 수익률(%)을 계산한다.

    미래 row는 절대 참조하지 않는다.

    데이터가 없으면 0이 아니라 NaN 반환.
    NaN은 Production drift_monitor_filter에서
    '실제 0% 움직임'으로 오인되지 않도록 하기 위함.
    """

    if column is None:
        return float("nan")

    values = pd.to_numeric(
        panel.loc[:row_index, column],
        errors="coerce",
    ).dropna()

    if len(values) < periods + 1:
        return float("nan")

    current = float(values.iloc[-1])
    previous = float(values.iloc[-(periods + 1)])

    if previous == 0:
        return float("nan")

    return ((current / previous) - 1.0) * 100.0


def build_historical_drift_data(
    market_data: dict[str, Any],
    panel: pd.DataFrame,
    row_index: int,
) -> dict[str, Any]:
    """
    Backtest 전용 Historical/PIT DRIFT_DATA Producer.

    Production attach_drift_data_layer()의 출력 Contract를
    historical daily data로 가능한 범위까지 재현한다.

    원칙
    ----
    1. row_index 이후 데이터 사용 금지.
    2. 현재 yfinance/live fetch 사용 금지.
    3. 존재하지 않는 데이터는 0으로 대체하지 않는다.
    4. Historical intraday / OHLC가 없는 항목은 NaN 처리.
    5. Production drift_monitor_filter() 자체는 수정하지 않는다.

    현재 재현 가능
    --------------
    - ret_1d
    - ret_5d

    현재 재현 불가
    --------------
    - ret_15m
    - ret_30m
    - ret_1h
    - ret_4h
    - ATR
    - norm_1d
    - norm_5d
    """

    drift_data: dict[str, dict[str, float]] = {}
    missing_assets: list[str] = []

    for asset, candidates in DRIFT_COLUMN_CANDIDATES.items():
        column = _resolve_drift_column(
            panel,
            candidates,
        )

        if column is None:
            missing_assets.append(asset)

        ret_1d = _historical_return(
            panel=panel,
            row_index=row_index,
            column=column,
            periods=1,
        )

        ret_5d = _historical_return(
            panel=panel,
            row_index=row_index,
            column=column,
            periods=5,
        )

        drift_data[asset] = {
            # Historical intraday unavailable
            "ret_15m": float("nan"),
            "ret_30m": float("nan"),
            "ret_1h": float("nan"),
            "ret_4h": float("nan"),

            # Historical daily close based
            "ret_1d": ret_1d,
            "ret_5d": ret_5d,

            # Historical OHLC unavailable in current panel
            "atr": float("nan"),
            "norm_1d": float("nan"),
            "norm_5d": float("nan"),
        }

    market_data["DRIFT_DATA"] = drift_data

    # Audit metadata
    asof_col = (
        "signal_date"
        if "signal_date" in panel.columns
        else "date"
    )

    try:
        asof = pd.to_datetime(
            panel.iloc[row_index][asof_col]
        ).strftime("%Y-%m-%d")
    except Exception:
        asof = None

    market_data["_DRIFT_ASOF"] = asof
    market_data["_DRIFT_SOURCE"] = "HISTORICAL_PIT_DAILY"
    market_data["_DRIFT_MISSING_ASSETS"] = missing_assets
    market_data["_DRIFT_INTRADAY_AVAILABLE"] = False
    market_data["_DRIFT_ATR_AVAILABLE"] = False

    return market_data


# ============================================================
# Production Pre-Filter13 Execution Adapter
# ============================================================

def prepare_filter13_execution_state(
    market_data: dict[str, Any],
    panel: pd.DataFrame,
    row_index: int,
    previous_flow_memory: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Backtest Pre-Filter13 Execution Adapter.

    역할
    ----
    Production에서 Filter13 이전에 생성되는 state를
    동일한 Production 함수와 동일한 실행 순서로 재현한다.

    Historical Drift
    ----------------
    Production attach_drift_data_layer()는 현재 yfinance 데이터를
    사용하므로 historical backtest에서는 호출하지 않는다.

    대신 build_historical_drift_data()가 현재 row_index까지의
    PIT 데이터만 사용해 DRIFT_DATA Contract를 생성한다.

    Flow History
    ------------
    Production의 현재 insights/flow_state.json은 과거 Backtest에
    사용하지 않는다.

    대신 Backtest가 직전 날짜 historical flow memory를 전달한다.
    """

    previous_flow_memory = previous_flow_memory or {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    # --------------------------------------------------
    # Historical/PIT DRIFT_DATA
    # 반드시 drift_monitor_filter 이전에 생성
    # --------------------------------------------------

    build_historical_drift_data(
        market_data=market_data,
        panel=panel,
        row_index=row_index,
    )

    # --------------------------------------------------
    # Filter13이 직접 읽는 이전 Flow Contract
    # --------------------------------------------------

    market_data["PREV_FLOW_STATE"] = previous_flow_memory.get(
        "flow_state",
        "N/A",
    )

    market_data["PREV_FLOW_SCORE"] = previous_flow_memory.get(
        "flow_score",
        0,
    )

    # --------------------------------------------------
    # Historical SEW Contract
    #
    # SEW historical archive가 없으므로
    # 현재 insights/sew_state.json을 절대 사용하지 않는다.
    # --------------------------------------------------

    market_data["SEW_STATUS"] = "HISTORICAL_UNAVAILABLE"
    market_data["SEW_EVENT_TYPE"] = "HISTORICAL_UNAVAILABLE"

    # --------------------------------------------------
    # Production Pre-13 execution order
    # --------------------------------------------------

    sf.market_regime_filter(
        market_data
    )

    sf.policy_filter_with_expectations(
        market_data
    )

    sf.drift_monitor_filter(
        market_data
    )

    sf.pseudo_gamma_filter(
        market_data
    )

    # --------------------------------------------------
    # Historical Flow Loader Override
    #
    # Production IFE는 load_previous_flow_state()를 내부 호출한다.
    # Backtest에서는 현재 flow_state.json 대신
    # t-1 historical memory 사용.
    # --------------------------------------------------

    original_loader = sf.load_previous_flow_state

    try:
        sf.load_previous_flow_state = (
            lambda *args, **kwargs: dict(
                previous_flow_memory
            )
        )

        sf.institutional_flow_engine_filter(
            market_data
        )

    finally:
        sf.load_previous_flow_state = original_loader

    sf.structural_filter(
        market_data
    )

    # --------------------------------------------------
    # Next-day Flow Memory
    # --------------------------------------------------

    institutional_flow = (
        market_data.get(
            "INSTITUTIONAL_FLOW",
            {},
        )
        or {}
    )

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
            previous_flow_memory.get(
                "flow_state",
                "N/A",
            )
        ),
        prev_flow_score=int(
            previous_flow_memory.get(
                "flow_score",
                0,
            )
            or 0
        ),
        current_flow_state=str(
            current_flow_state
        ),
        current_flow_score=int(
            current_flow_score
            or 0
        ),
        prev_persistence_days=int(
            previous_flow_memory.get(
                "persistence_days",
                0,
            )
            or 0
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