# filters/flow_authenticity.py

from typing import Any, Dict


def _to_float(value, default=0.0):
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


def flow_authenticity_filter(market_data: Dict[str, Any]) -> str:
    """
    12.6) Flow Authenticity Filter [SHADOW]
    목적:
    - 새 자금 유입 vs 숏커버 / squeeze 가능성 추정
    - 출력 전용 (Final Exposure 영향 없음)
    """

    # Existing project-compatible proxies
    spx_pos = _to_float(market_data.get("SP500_POS_Z"))
    gamma = _to_float(market_data.get("DEALER_GAMMA_BIAS"))
    cta = _to_float(market_data.get("CTA_MOMENTUM_SCORE"))
    vix = _to_float(market_data.get("VIX"))
    dxy = _to_float(market_data.get("DXY"))

    # Optional / existing booleans
    credit_calm = market_data.get("credit_calm", True)

    # Sector participation proxy
    momentum_scores = market_data.get("MOMENTUM_SCORES", {}) or {}

    xlk = momentum_scores.get("XLK", 0)
    xlf = momentum_scores.get("XLF", 0)
    xli = momentum_scores.get("XLI", 0)

    breadth = 0
    positioning = 0
    credit = 0
    sector = 0

    # 1) Breadth / concentration proxy
    # XLK only = narrow
    # XLK + XLF/XLI = broader
    if xlk > 0 and (xlf > 0 or xli > 0):
        breadth += 2
    elif xlk > 0 and xlf <= 0 and xli <= 0:
        breadth -= 2

    # 2) Positioning / squeeze risk
    if spx_pos > 2:
        positioning -= 2  # crowded
    elif spx_pos < 0:
        positioning += 1  # reset potential

    if gamma > 1:
        positioning -= 1  # squeeze / dealer support only
    elif gamma < 0:
        positioning += 1

    if cta > 0:
        positioning += 1

    # 3) Credit confirmation
    if credit_calm:
        credit += 2
    else:
        credit -= 2

    # 4) Macro participation proxy
    if vix < 18:
        sector += 1
    if dxy < 103:
        sector += 1
    elif dxy > 106:
        sector -= 1

    total = breadth + positioning + credit + sector

    if total >= 4:
        label = "REAL_ACCUMULATION"
    elif total >= 1:
        label = "EARLY_ROTATION"
    elif total >= -2:
        label = "SHORT_COVERING"
    else:
        label = "SQUEEZE_FADE_RISK"

    report = f"""
### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** {total}
- **Label:** {label}
- **Breadth / Participation:** {breadth}
- **Positioning / Gamma:** {positioning}
- **Credit Confirmation:** {credit}
- **Macro Participation:** {sector}

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.
"""

    return report