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

    lines.append("🧭 1. Executive Summary")

    summary = (
        f"Markets are operating in a {phase} regime as liquidity conditions remain "
        f"{liquidity_dir.lower()} and volatility pressures have increased. "
        f"Participation remains {flow_state}, while positioning risk sits at {pos_z:.1f}. "
        f"Maintain disciplined exposure and avoid adding marginal risk."
    )

    lines.append(summary)
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

    if dxy_dir > 0 and vix_dir > 0:

        lines.append(
            "A stronger dollar and rising volatility continue to tighten financial conditions."
        )

    if wti_dir < 0:

        lines.append(
            "Falling oil prices partially offset inflation pressure."
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