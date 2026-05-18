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
    """

    us10y = _to_float(market_data.get("US10Y"))
    real_yield = _to_float(market_data.get("DFII10") or market_data.get("REAL_RATE"))
    curve = _to_float(market_data.get("T10Y2Y"))
    oil = _to_float(market_data.get("WTI"))
    dxy = _to_float(market_data.get("DXY"))

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

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.
"""

    return report