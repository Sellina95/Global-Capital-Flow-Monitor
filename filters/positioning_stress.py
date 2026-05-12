# filters/positioning_stress.py

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


def positioning_stress_filter(market_data: Dict[str, Any]) -> str:
    """
    12.8) Positioning Stress Filter [SHADOW]

    목적:
    - 현재 시장이 구조적 risk-on인지
    - 숏커버 / forced chase / panic unwind인지 추정
    - VIX term structure 기반
    - 출력 전용 (Final Exposure 영향 없음)
    """

    vix = _to_float(market_data.get("VIX"))
    vix3m = _to_float(market_data.get("VIX3M"))

    gamma = _to_float(market_data.get("DEALER_GAMMA_BIAS"))
    spx_pos = _to_float(market_data.get("SP500_POS_Z"))
    cta = _to_float(market_data.get("CTA_MOMENTUM_SCORE"))

    score = 0
    term_note = "VIX3M data missing"
    gamma_note = "Neutral gamma"
    positioning_note = "Neutral positioning"

    # =========================================================
    # 1) VIX Term Structure
    # =========================================================
    if vix > 0 and vix3m > 0:
        spread = vix3m - vix

        if spread > 2:
            score += 2
            term_note = f"VIX3M-VIX={spread:.2f} → healthy contango / stable structure"
        elif spread > 0:
            score += 1
            term_note = f"VIX3M-VIX={spread:.2f} → mild contango"
        elif spread > -2:
            score -= 1
            term_note = f"VIX3M-VIX={spread:.2f} → flattening / caution"
        else:
            score -= 3
            term_note = f"VIX3M-VIX={spread:.2f} → backwardation / stress event"

    # =========================================================
    # 2) Gamma squeeze risk
    # =========================================================
    if gamma > 1:
        score -= 2
        gamma_note = "Positive gamma extreme → dealer-supported squeeze risk"
    elif gamma > 0:
        score -= 1
        gamma_note = "Positive gamma mild"
    elif gamma < -1:
        score += 1
        gamma_note = "Negative gamma unwind risk but less artificial upside"

    # =========================================================
    # 3) Position overcrowding
    # =========================================================
    if spx_pos > 2:
        score -= 2
        positioning_note = "Crowded long positioning"
    elif spx_pos > 1:
        score -= 1
        positioning_note = "Elevated long positioning"
    elif spx_pos < -1:
        score += 1
        positioning_note = "Reset / under-owned market"

    # CTA trend participation
    if cta > 1:
        score -= 1
    elif cta < 0:
        score += 1

    # =========================================================
    # Label
    # =========================================================
    if score >= 3:
        label = "STRUCTURAL_RISK_ON"
    elif score >= 0:
        label = "STABLE_BUT_CROWDED"
    elif score >= -3:
        label = "SQUEEZE_RISK"
    else:
        label = "POSITIONING_STRESS_EVENT"

    report = f"""
### 12.8) Positioning Stress Filter [SHADOW]
- **Score:** {score}
- **Label:** {label}

### Positioning Notes
- **Term Structure:** {term_note}
- **Gamma Structure:** {gamma_note}
- **Positioning:** {positioning_note}

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure, Phase, or Allocation.
"""

    return report