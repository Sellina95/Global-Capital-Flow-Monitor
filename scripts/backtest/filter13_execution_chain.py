from __future__ import annotations

from typing import Any

import contextlib
import io
import pandas as pd
from filters.leadership_breadth import leadership_breadth_filter

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
# Historical / PIT Liquidity Level Producer
# ============================================================

def build_historical_liquidity_level_contract(
    market_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Production attach_liquidity_layer()의 NET_LIQ level contract를
    historical PIT 데이터로 재현한다.

    중요:
    - market_data["NET_LIQ"]["history"]는 market_data_builder가
      현재 row_index까지만 생성한 history다.
    - 미래 데이터는 절대 사용하지 않는다.
    - Production과 동일한 percentile bucket semantics를 사용한다.
    """

    net = market_data.get("NET_LIQ", {}) or {}

    if not isinstance(net, dict):
        net = {}

    def _float_or_none(value):
        try:
            if value is None or pd.isna(value):
                return None
            return float(value)
        except Exception:
            return None

    net_today = _float_or_none(
        net.get("today")
    )

    net_prev = _float_or_none(
        net.get("prev")
    )

    if net_today is None or net_prev is None:
        net_dir = "N/A"
    elif net_today > net_prev:
        net_dir = "UP"
    elif net_today < net_prev:
        net_dir = "DOWN"
    else:
        net_dir = "FLAT"

    history = pd.to_numeric(
        pd.Series(
            net.get("history", [])
        ),
        errors="coerce",
    ).dropna()

    level_bucket = "N/A"

    if (
        net_today is not None
        and not history.empty
    ):
        if len(history) >= 20:
            pct_rank = float(
                (history <= net_today).mean()
            )
        else:
            vmin = float(history.min())
            vmax = float(history.max())

            if vmax == vmin:
                pct_rank = 0.5
            else:
                pct_rank = (
                    net_today - vmin
                ) / (
                    vmax - vmin
                )

        if pct_rank < 0.33:
            level_bucket = "LOW"
        elif pct_rank < 0.66:
            level_bucket = "MID"
        else:
            level_bucket = "HIGH"

    net = dict(net)

    net["dir"] = net_dir
    net["level_bucket"] = level_bucket

    market_data["NET_LIQ"] = net
    market_data["NET_LIQ_DIR"] = net_dir
    market_data[
        "NET_LIQ_LEVEL_BUCKET"
    ] = level_bucket

    # Audit metadata
    market_data[
        "_NET_LIQ_LEVEL_SOURCE"
    ] = "HISTORICAL_PIT_HISTORY"

    market_data[
        "_NET_LIQ_LEVEL_HISTORY_COUNT"
    ] = int(len(history))

    return market_data

def build_historical_pos_slope(
    market_data: dict[str, Any],
    panel: pd.DataFrame,
    row_index: int,
) -> dict[str, Any]:
    """
    Historical/PIT equivalent of Production get_recent_pos_slope().

    Production:
        last 3 non-null SP500_POS_Z observations
        slope = (latest - third_latest) / 2

    Backtest:
        master_panel의 positioning__SP500_POS_Z를 사용한다.
        현재 row_index까지의 데이터만 사용하므로
        미래 데이터는 포함하지 않는다.
    """

    # master_panel의 실제 positioning column
    pos_col = "positioning__SP500_POS_Z"

    # Column 자체가 없는 경우에만 Production-style fallback
    if pos_col not in panel.columns:
        market_data["POS_SLOPE"] = 0.0
        market_data["_POS_SLOPE_SOURCE"] = "MISSING_COLUMN_FALLBACK"
        return market_data

    # 현재 historical 시점까지만 사용 (PIT)
    history = pd.to_numeric(
        panel.loc[:row_index, pos_col],
        errors="coerce",
    ).dropna()

    # Production get_recent_pos_slope()와 동일하게
    # 최근 최대 3개 observation 사용
    vals = history.tail(3).tolist()

    if len(vals) >= 3:
        slope = float(
            (vals[-1] - vals[-3]) / 2.0
        )
    elif len(vals) == 2:
        slope = float(
            vals[-1] - vals[-2]
        )
    else:
        slope = 0.0

    market_data["POS_SLOPE"] = slope

    # Audit metadata
    market_data["_POS_SLOPE_SOURCE"] = (
        "HISTORICAL_PIT_POSITIONING_SP500_POS_Z"
    )

    market_data["_POS_SLOPE_HISTORY_COUNT"] = int(
        len(history)
    )

    return market_data


def build_historical_cross_asset_pct_history(
    market_data: dict[str, Any],
    panel: pd.DataFrame,
    row_index: int,
) -> dict[str, Any]:
    """
    Historical/PIT history contract for Production
    build_cross_asset_tape().

    Production _compute_zscore_strength() expects percentage-change
    histories for US10Y, DXY, VIX, and WTI.

    Only observations available through row_index are used.
    """

    assets = ("US10Y", "DXY", "VIX", "WTI")

    for asset in assets:
        history_key = f"{asset}_PCT_HISTORY"

        if asset not in panel.columns:
            market_data[history_key] = []
            continue

        levels = pd.to_numeric(
            panel.loc[:row_index, asset],
            errors="coerce",
        )

        pct_history = (
            levels.pct_change(fill_method=None)
            .mul(100.0)
            .dropna()
            .tolist()
        )

        market_data[history_key] = pct_history

    market_data["_CROSS_ASSET_HISTORY_SOURCE"] = (
        "HISTORICAL_PIT_MASTER_PANEL"
    )

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
    # Historical/PIT Liquidity Level Contract
    #
    # Production attach_liquidity_layer() creates this
    # before the downstream Filter13 generator chain.
    # --------------------------------------------------

    build_historical_liquidity_level_contract(
        market_data
    )
    build_historical_pos_slope(
        market_data=market_data,
        panel=panel,
        row_index=row_index,
    )

    build_historical_cross_asset_pct_history(
        market_data=market_data,
        panel=panel,
        row_index=row_index,
    )
    # --------------------------------------------------
    # Historical/PIT Leadership Breadth Contract
    #
    # Production:
    # attach_leadership_layer()
    #     -> leadership_breadth_filter()
    #
    # Backtest:
    # master_panel의 현재 row와 직전 row만 사용해
    # 동일 LEAD_* contract를 만든 뒤
    # Production scoring function을 그대로 실행한다.
    # --------------------------------------------------

    leadership_mapping = {
        "QQQ": "LEAD_QQQ",
        "SPY": "LEAD_SPY",
        "SMH": "LEAD_SMH",
        "SOXX": "LEAD_SOXX",
        "IWM": "LEAD_IWM",
        "XLK": "LEAD_XLK",
        "XLF": "LEAD_XLF",
        "XLI": "LEAD_XLI",
        "XLY": "LEAD_XLY",
    }

    current_row = panel.iloc[row_index]
    previous_row = (
        panel.iloc[row_index - 1]
        if row_index > 0
        else None
    )

    for source_col, target_key in leadership_mapping.items():

        current_value = (
            current_row.get(source_col)
            if source_col in panel.columns
            else None
        )

        previous_value = (
            previous_row.get(source_col)
            if (
                previous_row is not None
                and source_col in panel.columns
            )
            else None
        )

        market_data[target_key] = (
            float(current_value)
            if pd.notna(current_value)
            else 0.0
        )

        market_data[f"{target_key}_PREV"] = (
            float(previous_value)
            if pd.notna(previous_value)
            else 0.0
        )

    market_data["_LEADERSHIP_SOURCE"] = (
        "HISTORICAL_PIT_MASTER_PANEL"
    )

    with contextlib.redirect_stdout(io.StringIO()):
        leadership_breadth_filter(market_data)
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