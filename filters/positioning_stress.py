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


# 원인:
# report 블록 안에서 {term_note} / {front_note} / {gamma_note} / {positioning_note}
# 쓰는데 위에서 해당 변수 초기화가 누락됐거나
# 함수 들여쓰기 꼬여서 scope 밖.

# positioning_stress_filter 함수 시작부를 아래처럼 통째로 교체


def positioning_stress_filter(market_data: Dict[str, Any]) -> str:
    """
    12.8) Positioning Stress Filter [SHADOW]
    """

    vix = _to_float(market_data.get("VIX"))
    vix3m = _to_float(market_data.get("VIX3M"))
    vix9d = _to_float(market_data.get("VIX9D"))

    gamma = _to_float(market_data.get("DEALER_GAMMA_BIAS"))
    spx_pos = _to_float(market_data.get("SP500_POS_Z"))
    cta = _to_float(market_data.get("CTA_MOMENTUM_SCORE"))

    score = 0

    # 반드시 먼저 초기화
    term_note = "VIX3M data missing"
    front_note = "VIX9D data missing"
    gamma_note = "Neutral gamma"
    positioning_note = "Neutral positioning"

    # =========================================================
    # 1) VIX Term Structure (VIX3M vs VIX)
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
    # 2) Front-end hedge demand (VIX9D vs VIX)
    # =========================================================
    if vix > 0 and vix9d > 0:
        front_ratio = vix9d / vix

        if front_ratio < 0.95:
            score += 1
            front_note = f"VIX9D/VIX={front_ratio:.2f} → calm front-end hedge"
        elif front_ratio <= 1.05:
            front_note = f"VIX9D/VIX={front_ratio:.2f} → neutral short-term hedge"
        else:
            score -= 2
            front_note = f"VIX9D/VIX={front_ratio:.2f} → front-end panic hedge"

    # =========================================================
    # 3) Gamma
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
    # 4) Positioning
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

    if cta > 1:
        score -= 1
    elif cta < 0:
        score += 1

    # =========================================================
    # Label
    # =========================================================
    if score >= 4:
        label = "STRUCTURAL_RISK_ON"
    elif score >= 1:
        label = "STABLE_BUT_CROWDED"
    elif score >= -3:
        label = "SQUEEZE_RISK"
    else:
        label = "POSITIONING_STRESS_EVENT"

    report = f"""
### 12.8) Positioning Stress Filter [SHADOW]

- **Score:** {score}
- **Label:** {label}

**Positioning Notes**
- Term Structure: {term_note}
- Short-Term Hedge: {front_note}
- Gamma Structure: {gamma_note}
- Positioning: {positioning_note}

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure, Phase, or Allocation.
"""

    return report