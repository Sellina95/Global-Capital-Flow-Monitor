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


def _ret(today: float, prev: float) -> float:
    if today > 0 and prev > 0:
        return (today / prev) - 1
    return 0.0


def leadership_breadth_filter(market_data: Dict[str, Any]) -> str:
    """
    12.7) Leadership Breadth Filter [SHADOW]
    목적:
    - 랠리가 mega-cap / AI / semiconductor 중심인지
    - 아니면 broad risk-on으로 확산되는지 판단
    - 출력 전용
    """

    qqq = _to_float(market_data.get("LEAD_QQQ"))
    spy = _to_float(market_data.get("LEAD_SPY"))
    smh = _to_float(market_data.get("LEAD_SMH"))
    soxx = _to_float(market_data.get("LEAD_SOXX"))
    iwm = _to_float(market_data.get("LEAD_IWM"))

    qqq_prev = _to_float(market_data.get("LEAD_QQQ_PREV"))
    spy_prev = _to_float(market_data.get("LEAD_SPY_PREV"))
    smh_prev = _to_float(market_data.get("LEAD_SMH_PREV"))
    soxx_prev = _to_float(market_data.get("LEAD_SOXX_PREV"))
    iwm_prev = _to_float(market_data.get("LEAD_IWM_PREV"))

    qqq_ret = _ret(qqq, qqq_prev)
    spy_ret = _ret(spy, spy_prev)
    smh_ret = _ret(smh, smh_prev)
    soxx_ret = _ret(soxx, soxx_prev)
    iwm_ret = _ret(iwm, iwm_prev)

    score = 0
    notes = []

    # 1) QQQ vs SPY
    if qqq > 0 and spy > 0 and qqq_prev > 0 and spy_prev > 0:
        qqq_spy_spread = qqq_ret - spy_ret

        if qqq_spy_spread >= 0.003:
            score += 1
            notes.append(f"QQQ-SPY spread={qqq_spy_spread*100:.2f}%p → growth leadership")
        elif qqq_spy_spread <= -0.003:
            score -= 1
            notes.append(f"QQQ-SPY spread={qqq_spy_spread*100:.2f}%p → growth leadership weak")
        else:
            notes.append(f"QQQ-SPY spread={qqq_spy_spread*100:.2f}%p → neutral growth leadership")
    else:
        notes.append("QQQ/SPY return data missing")

    # 2) SMH vs QQQ
    if smh > 0 and qqq > 0 and smh_prev > 0 and qqq_prev > 0:
        smh_qqq_spread = smh_ret - qqq_ret

        if smh_qqq_spread >= 0.003:
            score += 2
            notes.append(f"SMH-QQQ spread={smh_qqq_spread*100:.2f}%p → semiconductor participation strong")
        elif smh_qqq_spread <= -0.003:
            score -= 2
            notes.append(f"SMH-QQQ spread={smh_qqq_spread*100:.2f}%p → AI/tech rally not semiconductor-broad")
        else:
            notes.append(f"SMH-QQQ spread={smh_qqq_spread*100:.2f}%p → semiconductor participation neutral")
    else:
        notes.append("SMH/QQQ return data missing")

    # 3) SOXX confirmation
    if soxx > 0 and qqq > 0 and soxx_prev > 0 and qqq_prev > 0:
        soxx_qqq_spread = soxx_ret - qqq_ret

        if soxx_qqq_spread >= 0.003:
            score += 1
            notes.append(f"SOXX-QQQ spread={soxx_qqq_spread*100:.2f}%p → SOX proxy confirms chip breadth")
        elif soxx_qqq_spread <= -0.003:
            score -= 1
            notes.append(f"SOXX-QQQ spread={soxx_qqq_spread*100:.2f}%p → chip breadth lagging")
        else:
            notes.append(f"SOXX-QQQ spread={soxx_qqq_spread*100:.2f}%p → chip breadth neutral")
    else:
        notes.append("SOXX/QQQ return data missing")

    # 4) Small-cap participation
    if iwm > 0 and spy > 0 and iwm_prev > 0 and spy_prev > 0:
        iwm_spy_spread = iwm_ret - spy_ret

        if iwm_spy_spread >= 0.003:
            score += 2
            notes.append(f"IWM-SPY spread={iwm_spy_spread*100:.2f}%p → small-cap participation confirms broader risk-on")
        elif iwm_spy_spread <= -0.003:
            score -= 2
            notes.append(f"IWM-SPY spread={iwm_spy_spread*100:.2f}%p → small-cap lag, narrow leadership risk")
        else:
            notes.append(f"IWM-SPY spread={iwm_spy_spread*100:.2f}%p → small-cap participation neutral")
    else:
        notes.append("IWM/SPY return data missing")

    # 5) Cyclical / Sector diffusion: XLF, XLI, XLY vs SPY
    xlf = _to_float(market_data.get("LEAD_XLF"))
    xli = _to_float(market_data.get("LEAD_XLI"))
    xly = _to_float(market_data.get("LEAD_XLY"))

    xlf_prev = _to_float(market_data.get("LEAD_XLF_PREV"))
    xli_prev = _to_float(market_data.get("LEAD_XLI_PREV"))
    xly_prev = _to_float(market_data.get("LEAD_XLY_PREV"))

    diffusion_score = 0
    diffusion_notes = []

    for name, today, prev in [
        ("XLF", xlf, xlf_prev),
        ("XLI", xli, xli_prev),
        ("XLY", xly, xly_prev),
    ]:
        if today > 0 and prev > 0 and spy > 0 and spy_prev > 0:
            sector_ret = _ret(today, prev)
            spy_ret_for_sector = _ret(spy, spy_prev)
            spread = sector_ret - spy_ret_for_sector

            if spread >= 0.003:
                diffusion_score += 1
                diffusion_notes.append(
                    f"{name}-SPY spread={spread*100:.2f}%p → sector diffusion positive"
                )
            elif spread <= -0.003:
                diffusion_score -= 1
                diffusion_notes.append(
                    f"{name}-SPY spread={spread*100:.2f}%p → sector diffusion weak"
                )
            else:
                diffusion_notes.append(
                    f"{name}-SPY spread={spread*100:.2f}%p → sector diffusion neutral"
                )
        else:
            diffusion_notes.append(f"{name}/SPY return data missing")

    score += diffusion_score
    notes.extend(diffusion_notes)

    if score >= 4:
        label = "BROAD_LEADERSHIP"
    elif score >= 1:
        label = "SELECTIVE_EXPANSION"
    elif score >= -2:
        label = "CONCENTRATED_LEADERSHIP"
    else:
        label = "MEGA_CAP_SQUEEZE_RISK"
    
    market_data["LEADERSHIP_BREADTH_SCORE"] = score
    market_data["LEADERSHIP_BREADTH_LABEL"] = label

    # 18.0 Sector Allocation용 normalized leadership outputs
    if label == "BROAD_LEADERSHIP":
        leadership_state = "BROAD"
        breadth_score_18 = 2
        leader_type = "BROAD_MARKET"
        participation_signal = "CONFIRMED"

    elif label == "SELECTIVE_EXPANSION":
        leadership_state = "MODERATE"
        breadth_score_18 = 1
        leader_type = "SEMIS_LED"
        participation_signal = "PARTIAL"

    elif label == "CONCENTRATED_LEADERSHIP":
        leadership_state = "NARROW"
        breadth_score_18 = 0
        leader_type = "MEGACAP_TECH"
        participation_signal = "WEAK"

    else:  # MEGA_CAP_SQUEEZE_RISK
        leadership_state = "MEGACAP_ONLY"
        breadth_score_18 = -1
        leader_type = "MEGACAP_TECH"
        participation_signal = "WEAK"

    market_data["LEADERSHIP_STATE"] = leadership_state
    market_data["BREADTH_SCORE_18"] = breadth_score_18
    market_data["LEADER_TYPE"] = leader_type
    market_data["PARTICIPATION_SIGNAL"] = participation_signal

    print(
        "[DEBUG][LEADERSHIP_18]",
        market_data.get("LEADERSHIP_STATE"),
        market_data.get("BREADTH_SCORE_18"),
        market_data.get("LEADER_TYPE"),
        market_data.get("PARTICIPATION_SIGNAL"),
    )
    
    
    notes_text = "\n".join([f"- {n}" for n in notes])
    
    

    report = f"""
### 12.7) Leadership Breadth Filter [SHADOW]
- **Score:** {score}
- **Label:** {label}

**Leadership Notes**
{notes_text}

📌 Shadow Note: This filter checks whether leadership is broadening beyond mega-cap tech/AI. No impact on Final Exposure, Phase, or Allocation.
"""

    return report
