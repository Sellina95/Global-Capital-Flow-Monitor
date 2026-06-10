def generate_pm_final_brief(market_data):

    lines = []
    final_state = market_data.get("FINAL_STATE", {}) or {}
    final_decision = market_data.get("FINAL_DECISION", {}) or {}
    final_action = market_data.get("FINAL_ACTION", {}) or {}
    credit_calm = final_state.get("credit_calm", False)
    geo_level = market_data.get("WARNING_SIGNALS", {}).get("geo_level", "NORMAL")

    phase = final_state.get("phase", "N/A")
    structure = final_state.get("structure_tag", "N/A")

    flow_state = final_state.get("flow_state", "N/A")
    drift_state = final_state.get("drift_state", "N/A")

    liquidity_dir = final_state.get("liquidity_dir", "N/A")
    pos_z = final_state.get("pos_z", 0)

    exposure = final_decision.get("exposure", "N/A")
    action = final_decision.get("action", "N/A")

    macro_narrative = final_state.get("macro_narrative", "N/A")

    cross_asset = final_state.get("cross_asset_tape", {}) or {}

    us10y_dir = cross_asset.get("US10Y_DIR", 0)
    dxy_dir = cross_asset.get("DXY_DIR", 0)
    vix_dir = cross_asset.get("VIX_DIR", 0)
    wti_dir = cross_asset.get("WTI_DIR", 0)

    thesis = ""

    if liquidity_dir == "DOWN" and pos_z >= 1.5:

        thesis = (
            "Liquidity is tightening while positioning remains crowded. "
            "Maintain defensive exposure and avoid marginal risk expansion."
        )

    elif "TRACE" in str(flow_state).upper():

        thesis = (
            "Participation is emerging but remains unconfirmed. "
            "Stay selective and focus on capital preservation."
        )

    else:

        thesis = (
            "Market conditions remain balanced. "
            "Monitor liquidity, participation, and risk signals."
        )

    lines.append("🏦 GLOBAL MACRO DAILY — PM FINAL BRIEF")
    lines.append("")

    # Rally Confidence Assessment

    rally_score = 0

    # 12.6
    flow_label = market_data.get("FLOW_AUTHENTICITY_LABEL", "")

    # 12.5
    growth_label = market_data.get("GROWTH_SUSTAINABILITY_LABEL", "")

    # 12.7
    leadership_label = market_data.get("LEADERSHIP_BREADTH_LABEL", "")

    # 12.8
    positioning_label = (
        market_data.get("POSITIONING_STRESS_LABEL")
        or market_data.get("POSITIONING_LABEL")
        or market_data.get("POSITIONING_STATE")
        or ""
    )

    if flow_label == "REAL_ACCUMULATION":
        rally_score += 1

    if growth_label == "STRUCTURAL_STRESS":
        rally_score -= 1

    if leadership_label == "BROAD_LEADERSHIP":
        rally_score += 1
    elif leadership_label == "MEGA_CAP_SQUEEZE_RISK":
        rally_score -= 1

    if positioning_label == "SQUEEZE_RISK":
        rally_score -= 1

    if rally_score >= 1:
        rally_confidence = "HIGH"
    elif rally_score == 0:
        rally_confidence = "MEDIUM"
    else:
        rally_confidence = "LOW"

    lines.append("🧭 1. Executive Summary")

    summary = (
        f"Markets are operating in a {phase} regime as liquidity conditions remain "
        f"{liquidity_dir.lower()} and volatility pressures have increased. "
        f"Participation remains {flow_state}, while positioning risk sits at {pos_z:.1f}. "
        f"Maintain disciplined exposure and avoid adding marginal risk."
    )

    lines.append(summary)

    if rally_confidence == "HIGH":
        confidence_display = "🟢 HIGH"
    elif rally_confidence == "MEDIUM":
        confidence_display = "🟡 MEDIUM"
    else:
        confidence_display = "🔴 LOW"

    lines.append(f"Rally Confidence: {confidence_display}")

    rally_message_map = {
        "LOW": (
            "Participation is improving, but liquidity remains tight and positioning risk is elevated. "
            "Treat the rally as low-confidence until flow persistence and leadership quality improve."
        ),
        "MEDIUM": (
            "Participation is emerging, but confirmation remains limited. "
            "Wait for stronger breadth and persistence before increasing risk exposure."
        ),
        "HIGH": (
            "Participation and leadership support trend continuation. "
            "Risk exposure may be maintained, subject to volatility and positioning controls."
        ),
    }

    lines.append(rally_message_map.get(rally_confidence, rally_message_map["MEDIUM"]))



    lines.append("")

    lines.append("🌍 2. Macro Regime")

    lines.append(f"Liquidity: {'🔻 Tightening' if liquidity_dir=='DOWN' else '🟢 Improving'}")
    lines.append(
        f"Flow: {'🟡 Early Trace' if 'TRACE' in flow_state else flow_state}"
    )
    lines.append(
        f"Volatility: {'🔺 Rising' if 'RISK' in phase.upper() else '🟢 Stable'}"
    )
    lines.append(f"Structure: {structure}")

    credit_calm = final_state.get("credit_calm")
    lines.append("")
    lines.append("⚠️ 3. Key Macro Conflict")

    if liquidity_dir == "DOWN" and credit_calm:

        lines.append("")
        lines.append("1) Liquidity vs Credit")
        lines.append("• Liquidity: Tightening")
        lines.append("• Credit: Stable")

        lines.append("Interpretation:")
        lines.append(
            "Liquidity conditions are deteriorating, "
            "but credit markets have not yet confirmed stress."
        )

        lines.append(
            "Early-stage fragility signal rather than crisis."
        )
    if pos_z >= 1.5:

        lines.append("")
        lines.append("2) Positioning Crowding")
        lines.append(f"• POS_Z = {pos_z:.2f}")

        lines.append("Interpretation:")
        lines.append(
            "Positioning remains elevated. "
            "Main risk is an air-pocket correction rather than structural collapse."
        )
    lines.append("")
    lines.append("📊 4. Cross Asset Summary")

    equity_status = "🔴 Weakening" if vix_dir > 0 else "🟢 Stable"
    bond_status = "🟡 Neutral"
    usd_status = "🔺 Stronger" if dxy_dir > 0 else "🔻 Weaker"
    oil_status = "🔺 Rising" if wti_dir > 0 else "🔻 Falling"
    vol_status = "🔺 Rising" if vix_dir > 0 else "🟢 Stable"

    lines.append(f"Equities: {equity_status}")
    lines.append(f"Bonds: {bond_status}")
    lines.append(f"USD: {usd_status}")
    lines.append(f"Oil: {oil_status}")
    lines.append(f"Volatility: {vol_status}")

    lines.append("")
    lines.append("Interpretation:")
   

    if dxy_dir > 0 and vix_dir > 0 and us10y_dir > 0:
        lines.append(
            "Rates, dollar, and volatility are rising together, signaling broad financial-condition tightening."
        )
        lines.append(
            "Risk assets should be treated cautiously unless credit and breadth strongly confirm participation."
        )

    elif dxy_dir > 0 and vix_dir > 0:
        lines.append(
            "A stronger dollar and rising volatility are tightening risk appetite."
        )
        lines.append(
            "This favors defensive exposure and discourages aggressive risk expansion."
        )

    elif dxy_dir < 0 and vix_dir < 0 and us10y_dir <= 0:
        lines.append(
            "A weaker dollar and lower volatility are easing financial conditions."
        )
        lines.append(
            "This supports risk assets, provided breadth and credit remain stable."
        )

    elif dxy_dir < 0 and vix_dir < 0 and us10y_dir > 0:
        lines.append(
            "Dollar weakness and lower volatility are providing temporary breathing room for equities."
        )
        lines.append(
            "However, rising yields limit the quality of the risk-on signal."
        )

    elif us10y_dir > 0 and wti_dir > 0:
        lines.append(
            "Rising yields and oil prices point to reflation pressure."
        )
        lines.append(
            "This can support cyclicals in the short run but keeps inflation and duration risk elevated."
        )

    elif us10y_dir < 0 and wti_dir < 0:
        lines.append(
            "Falling yields and oil prices suggest growth-scare or disinflation pressure."
        )
        lines.append(
            "Defensive assets may outperform unless risk participation broadens."
        )

    elif dxy_dir > 0 and wti_dir < 0:
        lines.append(
            "Dollar strength and falling oil suggest global demand caution."
        )
        lines.append(
            "This is more consistent with defensive risk posture than broad risk expansion."
        )

    elif dxy_dir < 0 and wti_dir > 0:
        lines.append(
            "Dollar weakness and rising oil indicate reflationary risk appetite."
        )
        lines.append(
            "Monitor whether equity leadership broadens beyond narrow growth exposure."
        )

    elif vix_dir > 0:
        lines.append(
            "Volatility is rising, indicating weaker risk appetite."
        )
        lines.append(
            "Avoid chasing rallies until volatility pressure stabilizes."
        )

    elif vix_dir < 0:
        lines.append(
            "Volatility is easing, improving tactical risk conditions."
        )
        lines.append(
            "Confirmation still depends on liquidity, credit, and market breadth."
        )

    else:
        lines.append(
            "Cross-asset signals remain mixed and do not provide a clear directional confirmation."
        )

    
    lines.append("")
    lines.append("🧠 5. Market Interpretation")

    lines.append(
        f"Current market is best described as '{macro_narrative}'."
    )

    lines.append(
        "Liquidity is slowing, but systemic stress remains contained."
    )

    lines.append(
        "Credit markets remain stable, although participation quality requires monitoring."
    )

    lines.append("")
    lines.append("⚠️ 6. Risk Matrix")
    liq_risk = "🔴 Elevated" if liquidity_dir == "DOWN" else "🟢 Low"
    if pos_z >= 1.5:
        pos_risk = "🔴 Elevated"
    elif pos_z >= 1.0:
        pos_risk = "🟡 Moderate"
    else:
        pos_risk = "🟢 Low"

    credit_risk = "🟢 Low" if credit_calm else "🔴 Elevated"

    if geo_level in ["ELEVATED", "HIGH"]:
        geo_risk = "🟡 Elevated"
    else:
        geo_risk = "🟢 Low"

    inflation_risk = "🟡 Moderate" #fred 복구직전

    lines.append(f"Inflation Risk      {inflation_risk}")
    lines.append(f"Liquidity Risk      {liq_risk}")
    lines.append(f"Positioning Risk    {pos_risk}")
    lines.append(f"Credit Risk         {credit_risk}")
    lines.append(f"Geopolitical Risk   {geo_risk}")

    lines.append("")
    lines.append("🏭 7. Sector Implication")

    if action == "STRONG REDUCE" or "RISK-OFF" in str(phase).upper():
        lines.append("🟢 Preferred:")
        lines.append("- Health Care")
        lines.append("- Consumer Staples")
        lines.append("- Utilities")
        lines.append("")
        lines.append("🔴 Avoid:")
        lines.append("- High-beta cyclicals")
        lines.append("- Crowded growth leadership")
        lines.append("- Rate-sensitive long-duration equities")
    else:
        lines.append("🟢 Preferred:")
        lines.append("- Quality leaders")
        lines.append("- Confirmed relative-strength sectors")
        lines.append("")
        lines.append("🔴 Avoid:")
        lines.append("- Weak breadth / theory-only sector bets")
    
    lines.append("")
    lines.append("🎯 8. Tactical Recommendation")

    final_action_size = final_action.get("size", "N/A")
    final_action_confidence = final_action.get("confidence", "N/A")
    final_action_reasons = final_action.get("reason", [])

    lines.append(f"Recommendation: {action} / {final_action_size}")
    lines.append(f"Confidence: {final_action_confidence}")

    if final_action_reasons:
        lines.append("Rationale:")
        for reason in final_action_reasons:
            lines.append(f"- {reason}")

    lines.append(
        "Maintain defensive discipline, avoid aggressive risk expansion, "
        "and prioritize cash plus resilient sectors."
    )

    lines.append("")

    lines.append("📈 9. Internal Rotation Monitor")
    rsp = market_data.get("BREADTH_RSP")
    rsp_prev = market_data.get("BREADTH_RSP_PREV")

    spy = market_data.get("BREADTH_SPY")
    spy_prev = market_data.get("BREADTH_SPY_PREV")

    rsp_prev2 = market_data.get("BREADTH_RSP_PREV2")
    spy_prev2 = market_data.get("BREADTH_SPY_PREV2")

    qqqe = market_data.get("BREADTH_QQQE")
    qqqe_prev = market_data.get("BREADTH_QQQE_PREV")

    qqq = market_data.get("BREADTH_QQQ")
    qqq_prev = market_data.get("BREADTH_QQQ_PREV")

    qqqe_prev2 = market_data.get("BREADTH_QQQE_PREV2")
    qqq_prev2 = market_data.get("BREADTH_QQQ_PREV2")

    smh = market_data.get("LEAD_SMH")
    smh_prev = market_data.get("LEAD_SMH_PREV")
    smh_prev2 = market_data.get("LEAD_SMH_PREV2")

    iwm = market_data.get("LEAD_IWM")
    iwm_prev = market_data.get("LEAD_IWM_PREV")
    iwm_prev2 = market_data.get("LEAD_IWM_PREV2")


    rsp_rel = (
        ((rsp / rsp_prev) - 1)
        -
        ((spy / spy_prev) - 1)
    )

    qqqe_rel = (
        ((qqqe / qqqe_prev) - 1)
        -
        ((qqq / qqq_prev) - 1)
    )


    smh_rel = (
        ((smh / smh_prev) - 1)
        -
        ((spy / spy_prev) - 1)
    )

    iwm_rel = (
        ((iwm / iwm_prev) - 1)
        -
        ((spy / spy_prev) - 1)
    )
    rsp_rel_yesterday = (
        ((rsp_prev / rsp_prev2) - 1)
        -
        ((spy_prev / spy_prev2) - 1)
    )

    qqqe_rel_yesterday = (
        ((qqqe_prev / qqqe_prev2) - 1)
        -
        ((qqq_prev / qqq_prev2) - 1)
    )

    smh_rel_yesterday = (
        ((smh_prev / smh_prev2) - 1)
        -
        ((spy_prev / spy_prev2) - 1)
    )

    iwm_rel_yesterday = (
        ((iwm_prev / iwm_prev2) - 1)
        -
        ((spy_prev / spy_prev2) - 1)
    )

    def append_rotation_line(label, today, yesterday):
        change = today - yesterday
        lines.append(f"{label}")
        lines.append(f"Yesterday: {yesterday:+.2%}")
        lines.append(f"Today: {today:+.2%}")
        lines.append(f"Change: {change:+.2%}")
        lines.append("")

    append_rotation_line("RSP vs SPY", rsp_rel, rsp_rel_yesterday)
    append_rotation_line("QQQE vs QQQ", qqqe_rel, qqqe_rel_yesterday)
    append_rotation_line("SMH vs SPY", smh_rel, smh_rel_yesterday)
    append_rotation_line("IWM vs SPY", iwm_rel, iwm_rel_yesterday)

   
    lines.append("")
    lines.append("Interpretation:")

    # Threshold 변수화 (유지보수 용이성)
    SMH_STRONG_LEADERSHIP = 3.0

    if rsp_rel > 0 and qqqe_rel > 0 and smh_rel > SMH_STRONG_LEADERSHIP and iwm_rel > 0:
        lines.append("Participation is broadening across equal-weight, semiconductor, and small-cap segments.")
        lines.append("This is consistent with healthy risk expansion and improving market breadth.")

    elif rsp_rel > 0 and qqqe_rel > 0 and smh_rel > 0:
        lines.append("Participation is broadening while semiconductor leadership remains supportive.")
        lines.append("Market participation appears healthier than a pure mega-cap driven rally.")

    elif rsp_rel > 0 and qqqe_rel > 0 and smh_rel <= 0:
        lines.append("Breadth improved, but semiconductor leadership remains weak.")
        lines.append("Rotation is expanding beyond AI leadership.")

    # 💡 6월 8일 같은 'AI 독주/나머지 소외' 장세를 완벽히 포착하는 구간
    elif rsp_rel <= 0 and qqqe_rel <= 0 and smh_rel > SMH_STRONG_LEADERSHIP:
        lines.append("Broad participation weakened while semiconductor leadership became dominant.")
        lines.append("Current strength appears concentrated in AI-linked leadership.")
        lines.append("Rally quality should be treated cautiously.")

    elif rsp_rel <= 0 and qqqe_rel <= 0 and smh_rel > 0:
        lines.append("Leadership narrowed back toward mega-cap and semiconductor exposure.")
        lines.append("Participation remains weak outside leadership groups.")

    elif rsp_rel <= 0 and qqqe_rel <= 0 and smh_rel <= 0:
        lines.append("Leadership narrowed and participation weakened simultaneously.")
        lines.append("Market internals remain fragile.")

    elif rsp_rel > 0 and qqqe_rel <= 0:
        lines.append("S&P participation improved while Nasdaq breadth weakened.")
        lines.append("Rotation appears uneven across sectors.")

    elif rsp_rel <= 0 and qqqe_rel > 0:
        lines.append("Nasdaq participation improved while broader market breadth lagged.")
        lines.append("Leadership remains concentrated in growth-oriented segments.")

    else:
        lines.append("Internal rotation remains mixed and inconclusive.")

    lines.append("")
    lines.append("🏁 10. Final PM View")
    lines.append(
        f"Action: {action}"
    )

    lines.append(
        f"Exposure: {exposure}%"
    )

    lines.append(
        f"Bias: {phase}"
    )

    lines.append(
        "Key focus: monitor liquidity, participation quality, and positioning risk."
    )

    return "\n".join(lines)