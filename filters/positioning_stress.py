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
    vix9d = _to_float(market_data.get("VIX9D"))

    gamma = _to_float(market_data.get("DEALER_GAMMA_BIAS"))
    spx_pos = _to_float(market_data.get("SP500_POS_Z"))
    cta = _to_float(market_data.get("CTA_MOMENTUM_SCORE"))

    score = 0
    notes = []

    # =========================================================
    # 1) VIX Term Structure: VIX vs VIX3M
    # =========================================================
    if vix > 0 and vix3m > 0:
        vix_vix3m_ratio = vix / vix3m
        spread = vix3m - vix

        if vix_vix3m_ratio < 0.95:
            score += 2
            notes.append(
                f"Term Structure: VIX/VIX3M={vix_vix3m_ratio:.2f}, "
                f"spread={spread:.2f} → healthy contango"
            )
        elif vix_vix3m_ratio <= 1.05:
            notes.append(
                f"Term Structure: VIX/VIX3M={vix_vix3m_ratio:.2f}, "
                f"spread={spread:.2f} → neutral / flattening"
            )
        else:
            score -= 2
            notes.append(
                f"Term Structure: VIX/VIX3M={vix_vix3m_ratio:.2f}, "
                f"spread={spread:.2f} → backwardation stress"
            )
    else:
        notes.append("Term Structure: VIX3M data missing")

    # =========================================================
    # 2) Short-Term Event Hedge: VIX9D vs VIX
    # =========================================================
    if vix9d > 0 and vix > 0:
        vix9d_ratio = vix9d / vix

        if vix9d_ratio > 1.05:
            score -= 2
            notes.append(
                f"Short-Term Hedge: VIX9D/VIX={vix9d_ratio:.2f} → event hedge spike"
            )
        elif vix9d_ratio < 0.95:
            score += 1
            notes.append(
                f"Short-Term Hedge: VIX9D/VIX={vix9d_ratio:.2f} → calm front-end"
            )
        else:
            notes.append(
                f"Short-Term Hedge: VIX9D/VIX={vix9d_ratio:.2f} → neutral"
            )
    else:
        notes.append("Short-Term Hedge: VIX9D data missing")

    # =========================================================
    # 3) Gamma squeeze risk
    # =========================================================
    if gamma > 1:
        score -= 2
        notes.append("Gamma Structure: Positive gamma extreme → dealer-supported squeeze risk")
    elif gamma > 0:
        score -= 1
        notes.append("Gamma Structure: Positive gamma mild")
    elif gamma < -1:
        score += 1
        notes.append("Gamma Structure: Negative gamma unwind risk but less artificial upside")
    else:
        notes.append("Gamma Structure: Neutral gamma")

    # =========================================================
    # 4) Position overcrowding
    # =========================================================
    if spx_pos > 2:
        score -= 2
        notes.append("Positioning: Crowded long positioning")
    elif spx_pos > 1:
        score -= 1
        notes.append("Positioning: Elevated long positioning")
    elif spx_pos < -1:
        score += 1
        notes.append("Positioning: Reset / under-owned market")
    else:
        notes.append("Positioning: Neutral positioning")

    # =========================================================
    # 5) CTA trend participation
    # =========================================================
    if cta > 1:
        score -= 1
        notes.append("CTA: Trend following crowded / chase risk")
    elif cta < 0:
        score += 1
        notes.append("CTA: Trend reset / less crowded")
    else:
        notes.append("CTA: Neutral trend participation")

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

    notes_text = "\n".join([f"- {n}" for n in notes])
    # 원인:
    # report = f""" ... """ 블록이 닫히기 전에
    # 📌 라인이 문자열 밖으로 튀어나왔거나
    # 따옴표 종료 위치가 꼬인 상태.
    
    # 해결:
    # 아래처럼 report 전체를 하나의 triple quote 안에 넣으면 됨.
    
    
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
       