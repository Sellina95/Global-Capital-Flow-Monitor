# filters/growth_sustainability.py

from typing import Any, Dict, Optional


def _to_float(value, default: Optional[float] = None) -> Optional[float]:
    """
    market_data 값이 숫자/문자/dict 어떤 형태여도 안전하게 float 변환.
    데이터가 없으면 None 반환.
    """
    if value is None:
        return default

    if isinstance(value, dict):
        for key in ["value", "latest", "close", "price", "current"]:
            if key in value:
                return _to_float(value.get(key), default)
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_interpretation(label: str, demand: int, financing: int, energy: int, policy: int) -> str:
    if label == "DURABLE_GROWTH":
        return (
            "Growth structure looks durable: demand, financing, and policy conditions "
            "are broadly supportive."
        )

    if label == "FRAGILE_EXPANSION":
        if financing > 0 and demand <= 0:
            return (
                "Expansion is supported more by financing conditions than by strong real demand. "
                "Growth can continue, but durability is limited."
            )
        return (
            "Expansion remains possible, but the growth structure is not yet broad or durable. "
            "Monitor demand confirmation."
        )

    if label == "LATE_CYCLE_STRAIN":
        return (
            "Growth momentum is weakening and the cycle is showing strain. "
            "Financing, demand, or policy support is not strong enough."
        )

    return (
        "Structural stress is elevated. Growth support is weak while macro burdens are rising."
    )

def growth_sustainability_filter(market_data: Dict[str, Any]) -> str:
    """
    12.5) Growth Sustainability Filter [SHADOW]
    - 출력 전용
    - Final Exposure / Phase / Sector Allocation 영향 없음
    - 기존 market_data 구조를 건드리지 않고, 필요한 FRED 값은 파일에서 직접 참조
    """

    # 1) Macro price inputs
    us10y = _to_float(market_data.get("GROWTH_US10Y"))
    oil = _to_float(market_data.get("GROWTH_WTI"))
    dxy = _to_float(market_data.get("GROWTH_DXY"))

    # 2) FRED inputs: read directly without modifying market_data
    real_yield = None
    curve = None
    fred_asof = "missing"

    try:
        fred_df = pd.read_csv("data/fred_macro_sctorallo.csv")

        if "date" in fred_df.columns and not fred_df.empty:
            fred_df["date"] = pd.to_datetime(fred_df["date"])
            fred_df = fred_df.sort_values("date")

            target_date = pd.to_datetime(
                market_data.get("date")
                or market_data.get("_DATA_ASOF")
                or market_data.get("_GROWTH_ASOF")
                or fred_df["date"].max()
            )

            fred_valid = fred_df[fred_df["date"] <= target_date]

            if not fred_valid.empty:
                fred_row = fred_valid.iloc[-1]
                fred_asof = pd.to_datetime(fred_row["date"]).strftime("%Y-%m-%d")

                real_yield = _to_float(
                    fred_row.get("DFII10")
                    if pd.notna(fred_row.get("DFII10", None))
                    else fred_row.get("REAL_RATE")
                )

                curve = _to_float(fred_row.get("T10Y2Y"))

    except Exception as e:
        fred_asof = f"error: {e}"

    liquidity_dir = (
        market_data.get("liquidity_dir")
        or market_data.get("NET_LIQ_DIR")
        or "UNKNOWN"
    )
    credit_calm = market_data.get("credit_calm", None)
    drift_label = market_data.get("drift_label", "UNKNOWN")

    demand = 0
    financing = 0
    energy = 0
    policy = 0

    # 1) Demand Proxy
    if drift_label in ["DISINFLATION_RISK_ON", "EARLY_RISK_ON", "RISK_ON"]:
        demand += 2
    elif drift_label in ["GROWTH_SCARE", "OIL_SHOCK", "RISK_OFF"]:
        demand -= 2

    if dxy is not None:
        if dxy < 103:
            demand += 1
        elif dxy > 106:
            demand -= 1

    # 2) Financing Engine
    if us10y is not None:
        if us10y < 4.5:
            financing += 1
        else:
            financing -= 1

    if real_yield is not None:
        if real_yield < 2.0:
            financing += 1
        else:
            financing -= 1

    if credit_calm is True:
        financing += 2
    elif credit_calm is False:
        financing -= 2

    # 3) Energy Burden
    if oil is not None:
        if oil < 85:
            energy += 2
        elif oil >= 95:
            energy -= 2
        elif oil >= 85:
            energy -= 1

    # 4) Policy Capacity
    if liquidity_dir == "UP":
        policy += 2
    elif liquidity_dir == "DOWN":
        policy -= 2

    if curve is not None:
        if curve > 0:
            policy += 1
        else:
            policy -= 1

    total = demand + financing + energy + policy

    input_summary = (
        f"US10Y={us10y if us10y is not None else 'missing'}, "
        f"RealYield={real_yield if real_yield is not None else 'missing'}, "
        f"T10Y2Y={curve if curve is not None else 'missing'}, "
        f"WTI={oil if oil is not None else 'missing'}, "
        f"DXY={dxy if dxy is not None else 'missing'}, "
        f"LiquidityDir={liquidity_dir}, "
        f"CreditCalm={credit_calm}, "
        f"DriftLabel={drift_label}, "
        f"FredAsof={fred_asof}"
    )

    if total >= 5:
        label = "DURABLE_GROWTH"
    elif total >= 1:
        label = "FRAGILE_EXPANSION"
    elif total >= -2:
        label = "LATE_CYCLE_STRAIN"
    else:
        label = "STRUCTURAL_STRESS"

    interpretation = _build_interpretation(label, demand, financing, energy, policy)

    report = f"""
### 12.5) Growth Sustainability Filter [SHADOW]
- **Score:** {total}
- **Label:** {label}
- **Demand Proxy:** {demand}
- **Financing:** {financing}
- **Energy Burden:** {energy}
- **Policy Capacity:** {policy}
- **Strategic Interpretation:** {interpretation}
- **Input Check:** {input_summary}

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.
"""

    return report

### 12.5) Growth Sustainability Filter [SHADOW]
- **Score:** {total}
- **Label:** {label}
- **Demand Proxy:** {demand}
- **Financing:** {financing}
- **Energy Burden:** {energy}
- **Policy Capacity:** {policy}
- **Strategic Interpretation:** {interpretation}
- **Input Check:** {input_summary}

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.
"""

    return report