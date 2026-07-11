from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


PREFIXES = (
    "positioning__",
    "sentiment__",
    "country_etf__",
    "sovereign_yields__",
    "sovereign_spreads__",
    "credit__",
    "liquidity__",
    "fred_sector__",
    "fred_extras__",
)

CORE_SERIES = [
    "US10Y",
    "DXY",
    "WTI",
    "VIX",
    "USDKRW",
    "HYG",
    "LQD",
    "SPY",
    "QQQ",
    "IWM",
    "RSP",
    "XLK",
    "XLF",
    "XLE",
    "XLI",
    "XLY",
    "XLV",
    "XLU",
    "XLRE",
    "SMH",
    "SOXX",
    "EEM",
    "EMB",
    "GOLD",
    "VIX3M",
]


def clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None

    if isinstance(value, np.generic):
        return value.item()

    return value


def strip_prefix(column: str) -> tuple[str | None, str]:
    for prefix in PREFIXES:
        if column.startswith(prefix):
            return prefix[:-2], column[len(prefix):]

    return None, column


def build_series_snapshot(
    panel: pd.DataFrame,
    row_index: int,
    column: str,
    lookback: int = 252,
) -> dict[str, Any]:
    if column not in panel.columns:
        return {
            "today": None,
            "pct_change": None,
            "history": [],
        }

    start = max(0, row_index - lookback + 1)

    values = pd.to_numeric(
        panel.loc[start:row_index, column],
        errors="coerce",
    ).dropna()

    if values.empty:
        return {
            "today": None,
            "pct_change": None,
            "history": [],
        }

    today = float(values.iloc[-1])

    pct_change = None
    if len(values) >= 2 and float(values.iloc[-2]) != 0:
        pct_change = (
            float(values.iloc[-1]) / float(values.iloc[-2]) - 1.0
        ) * 100.0

    return {
        "today": today,
        "pct_change": pct_change,
        "history": values.astype(float).tolist(),
    }


def build_market_data(
    panel: pd.DataFrame,
    row_index: int,
    previous_exposure: float | None = None,
) -> dict[str, Any]:
    row = panel.iloc[row_index]

    market_data: dict[str, Any] = {
        "DATE": str(pd.to_datetime(row["signal_date"]).date()),
        "SIGNAL_DATE": str(pd.to_datetime(row["signal_date"]).date()),
        "EXECUTION_DATE": (
            str(pd.to_datetime(row["execution_date"]).date())
            if pd.notna(row.get("execution_date"))
            else None
        ),
        "PREV_EXPOSURE": previous_exposure,
    }

    namespaces: dict[str, dict[str, Any]] = {}

    for column, raw_value in row.items():
        value = clean_value(raw_value)

        namespace, key = strip_prefix(column)

        if namespace is None:
            market_data[key] = value
        else:
            namespaces.setdefault(namespace, {})[key] = value

            # 기존 필터 호환을 위해 top-level에도 노출
            if key not in market_data or market_data[key] is None:
                market_data[key] = value

    market_data["NAMESPACES"] = namespaces

    series_map = {
        key: build_series_snapshot(panel, row_index, key)
        for key in CORE_SERIES
        if key in panel.columns
    }

    market_data["SERIES"] = series_map

    # 운영 strategist_filters 호환:
    # 핵심 시장 변수는 단순 float가 아니라
    # {"today", "pct_change", "history"} 구조로 전달한다.
    market_data["RAW_VALUES"] = {
        key: clean_value(row.get(key))
        for key in CORE_SERIES
        if key in row.index
    }

    for key, snapshot in series_map.items():
        market_data[key] = snapshot

    # 운영 필터 호환:
    # 파생/거시 데이터의 숫자 컬럼을 모두
    # {"today", "pct_change", "history"} 시계열 구조로 자동 변환
    series_namespaces = {
        "liquidity",
        "credit",
        "fred_sector",
        "fred_extras",
        "sovereign_yields",
        "sovereign_spreads",
    }

    for namespace in series_namespaces:
        namespace_values = namespaces.get(namespace, {})
        prefix = f"{namespace}__"

        for key in namespace_values:
            source_col = f"{prefix}{key}"

            if source_col not in panel.columns:
                continue

            numeric = pd.to_numeric(
                panel.loc[:row_index, source_col],
                errors="coerce",
            )

            if numeric.notna().sum() == 0:
                continue

            market_data[key] = build_series_snapshot(
                panel,
                row_index,
                source_col,
            )

    # 필터에서 흔히 참조하는 포지셔닝 값
    positioning = namespaces.get("positioning", {})
    for key in (
        "SP500_POS_Z",
        "US10Y_POS_Z",
        "DXY_POS_Z",
        "DEALER_GAMMA_BIAS",
        "CTA_MOMENTUM_SCORE",
        "GAMMA_FETCH_OK",
        "CTA_FETCH_OK",
    ):
        if key in positioning:
            market_data[key] = positioning[key]

    # Credit: 운영 필터가 HY_OAS를 시계열 dict로 기대함
    credit = namespaces.get("credit", {})
    credit_col = "credit__HY_OAS"

    if credit_col in panel.columns:
        market_data["HY_OAS"] = build_series_snapshot(
            panel,
            row_index,
            credit_col,
        )
    elif "HY_OAS" in credit:
        market_data["HY_OAS"] = {
            "today": credit["HY_OAS"],
            "pct_change": None,
            "history": [],
        }

    # Sentiment compatibility
    sentiment = namespaces.get("sentiment", {})
    sentiment_value = sentiment.get("sentiment_proxy")

    market_data["SENTIMENT"] = {
        "fear_greed": sentiment_value,
        "source": sentiment.get("used", "backtest_proxy"),
        "as_of": market_data["SIGNAL_DATE"],
    }

    return market_data
