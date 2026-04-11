from typing import Dict, Any


def decision_layer_filter(market_data: Dict[str, Any]) -> str:
    """
    So What? Decision Layer (v2)
    Turns FINAL_STATE + style/factor outputs into actionable guidance.
    + GEO_EW overlay
    + WARNING_SIGNALS overlay (6.5 / 6.6 / 7.2)
    """

    state = market_data.get("FINAL_STATE", {}) or {}

    phase = str(state.get("phase", "N/A"))
    action = str(state.get("risk_action", "HOLD")).upper()
    budget = state.get("risk_budget", None)

    liq_dir = str(state.get("liquidity_dir", "N/A")).upper()
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A")).upper()
    credit_calm = state.get("credit_calm", None)

    style = market_data.get("STYLE_TILT", None)
    duration = market_data.get("DURATION_TILT", None)
    cyclical = market_data.get("CYCLICAL_TILT", None)

    exposure_txt = f"{budget}%" if isinstance(budget, int) else "중립"

    stance = action

    if action == "INCREASE" and (liq_dir == "DOWN" or liq_lvl == "LOW"):
        stance = "HOLD"

    do, dont, triggers = [], [], []

    if stance == "INCREASE":
        do += ["노출을 단계적으로 확대하되, 퀄리티(현금흐름/재무안정) 중심으로 확대"]
        triggers += ["VIX 급등 또는 HY OAS 확대 시 즉시 방어"]
    elif stance == "REDUCE":
        do += ["현금/단기자산 비중 확대, 레버리지·저품질 크레딧 노출 축소"]
        triggers += ["크레딧 추가 악화 시 추가 디레버리징"]
    else:
        do += ["노출은 유지하되, 베타 확대보다 선별적 포지셔닝(퀄리티) 유지"]
        triggers += ["NET_LIQ 추가 하락/LOW 고착 시 노출 축소 준비"]

    if liq_dir == "DOWN" or liq_lvl == "LOW":
        dont += ["공격적 베타 확대", "장기듀레이션 성장주/레버리지 익스포저 확대"]
    else:
        dont += ["무분별한 테마 추격", "리스크 관리 없는 집중 포지션"]

    if credit_calm is False:
        do += ["크레딧 스트레스 확인 시(우선순위 1) 방어 전환"]
        triggers += ["HY OAS 4% 상회 시 Risk-Off 프로토콜"]

    # GEO overlay
    geo = market_data.get("GEO_EW", {}) or {}
    geo_level = str(geo.get("level", "NORMAL")).upper()

    if geo_level == "ELEVATED":
        if stance == "INCREASE":
            stance = "HOLD"
        do.append("Geo EW Elevated → 지정학 리스크 헤어컷 적용 (베타 확대 자제)")
        triggers.append("Geo Score 추가 상승/확산 시 방어 전환")
    elif geo_level == "CRISIS":
        stance = "REDUCE"
        do.append("Geo EW Crisis → 지정학 스트레스 급등, 즉시 방어 모드")
        dont.append("공격적 베타 포지셔닝")
        triggers.append("Geo Score 정상화 확인 전까지 리스크 축소 유지")

    # WARNING SIGNALS overlay
    warn = market_data.get("WARNING_SIGNALS", {}) or {}
    corr65_score = int(warn.get("corr65_score", 0) or 0)
    corr66_score = int(warn.get("corr66_score", 0) or 0)
    warn_geo_level = str(warn.get("geo_level", geo_level)).upper()

    warning_score = 0
    warning_notes = []

    warning_score += corr65_score
    warning_score += corr66_score

    if warn.get("corr65_break"):
        warning_notes.append("6.5 상관관계 붕괴")
    if warn.get("corr66_break"):
        warning_notes.append("6.6 섹터 상관관계 붕괴")

    if warn_geo_level == "ELEVATED":
        warning_score += 1
        warning_notes.append("7.2 지정학 경계(ELEVATED)")
    elif warn_geo_level == "CRISIS":
        warning_score += 2
        warning_notes.append("7.2 지정학 위기(CRISIS)")

    if warning_score >= 3:
        if stance == "INCREASE":
            stance = "HOLD"
        elif stance == "HOLD":
            stance = "REDUCE"
        do.append("Warning Score 3+ → 공격적 확장 금지, 익스포저 대폭 축소 고려")
        dont.append("공격적 베타 확대")
        triggers.append("경고 신호 해소 전까지 방어적 운용 유지")
    elif warning_score == 2:
        if stance == "INCREASE":
            stance = "HOLD"
        do.append("Warning Score 2 → 확신도 하락, 익스포저 10~15% 헤어컷 고려")
        triggers.append("상관관계 붕괴 지속 시 추가 축소 검토")
    elif warning_score == 1:
        do.append("Warning Score 1 → 경미한 이상신호, 포지션은 유지하되 모니터링 강화")

    style_hint = []
    if style:
        style_hint.append(f"Style={style}")
    if duration:
        style_hint.append(f"Duration={duration}")
    if cyclical:
        style_hint.append(f"Cyclical/Defensive={cyclical}")

    lines = []
    lines.append("## 🧭 So What? (Decision Layer)")
    lines.append(f"- **Risk Stance:** **{stance}** *(target exposure: {exposure_txt})*")
    lines.append(f"- **Context:** phase={phase} / liquidity={liq_dir}-{liq_lvl} / credit_calm={credit_calm} / geo={warn_geo_level}")

    if warning_score > 0:
        lines.append(f"- **Warning Score:** {warning_score} ({', '.join(warning_notes)})")
    else:
        lines.append("- **Warning Score:** 0 (No warning)")

    if style_hint:
        lines.append("- **Style Hints:** " + " / ".join(style_hint))

    lines.append("- **Do:** " + "; ".join(do))
    lines.append("- **Don't:** " + "; ".join(dont))
    lines.append("- **Triggers:** " + "; ".join(triggers))

    geo_overlay = market_data.get("GEO_OVERLAY", {}) or {}
    if geo_overlay and geo_overlay.get("budget_delta", 0) != 0:
        lines.append(
            f"- **Geo Overlay:** {geo_overlay.get('note')} → "
            f"budget {geo_overlay.get('base_budget')}% → {geo_overlay.get('final_budget')}%"
        )

    return "\n".join(lines)


def war_room_final_decision_filter(market_data: Dict[str, Any]) -> str:
    """
    Final Decision Layer (War Room Override)

    Priority:
    1) SEW
    2) Divergence
    3) Narrative / FINAL_STATE
    4) Warning Score (6.5 / 6.6 / 7.2)
    5) Exposure sizing
    """

    state = market_data.get("FINAL_STATE", {}) or {}
    sew = market_data.get("SEW_STATE", {}) or {}
    div = market_data.get("DIVERGENCE_STATE", {}) or {}
    warn = market_data.get("WARNING_SIGNALS", {}) or {}

    narrative_action = str(state.get("risk_action", "HOLD")).upper()
    risk_budget = int(state.get("risk_budget", 50)) if state.get("risk_budget") is not None else 50
    phase = str(state.get("phase", "N/A"))

    sew_status = str(sew.get("status", "N/A")).upper()
    sew_event = str(sew.get("event_type", "N/A")).upper()

    div_status = str(div.get("status", "N/A")).upper()
    div_action = str(div.get("action", "HOLD")).upper()

    base_exposure = market_data.get("RECOMMENDED_EXPOSURE", risk_budget)
    try:
        base_exposure = int(base_exposure)
    except Exception:
        base_exposure = risk_budget

        final_action = narrative_action
    final_exposure = base_exposure
    reason_chain = []

    # -------------------------
    # 1) SEW override
    # -------------------------
    if sew_status == "DEADMAN":
        final_action = "EXIT"
        final_exposure = 0
        reason_chain.append("SEW DEADMAN 발동 → 즉시 EXIT / 익스포저 0%")

    elif sew_status == "ALERT":
        final_action = "REDUCE"
        final_exposure = int(base_exposure * 0.7)
        reason_chain.append("SEW ALERT → 실시간 발작 감지, 익스포저 30% 축소")

    elif sew_status == "WATCH":
        if narrative_action == "INCREASE":
            final_action = "HOLD"
            final_exposure = base_exposure
            reason_chain.append("SEW WATCH → 증가 보류, HOLD 유지")
        else:
            final_action = narrative_action
            final_exposure = base_exposure
            reason_chain.append("SEW WATCH → 모니터링 강화, 기존 전략 유지")

    else:
        reason_chain.append("SEW STABLE → 실시간 이상징후 없음")

    # -------------------------
    # 1.5) Event Type Override
    # -------------------------
    if sew_status != "DEADMAN":  # DEADMAN은 최우선
        if sew_event == "LIQUIDATION_SHOCK":
            final_action = "EXIT"
            final_exposure = 0
            reason_chain.append("Event: LIQUIDATION_SHOCK → 강제 청산 흐름 → 즉시 EXIT")

        elif sew_event == "MACRO_UNWIND":
            final_action = "REDUCE"
            final_exposure = int(final_exposure * 0.6)
            reason_chain.append("Event: MACRO_UNWIND → 자금 언와인딩 → 익스포저 축소")

        elif sew_event == "TECH_DELEVERAGING":
            if final_action == "INCREASE":
                final_action = "HOLD"
            final_exposure = int(final_exposure * 0.75)
            reason_chain.append("Event: TECH_DELEVERAGING → 기술주 디레버리징 → 보수적 대응")

        elif sew_event == "POSITION_UNWIND_RISK":
            if final_action == "INCREASE":
                final_action = "HOLD"
            reason_chain.append("Event: POSITION_UNWIND_RISK → 포지션 과열 → 증가 억제")

        elif sew_event == "VOL_CRUSH_SQUEEZE":
            reason_chain.append("Event: VOL_CRUSH_SQUEEZE → 변동성 압축 상승 → 추격 주의")

        elif sew_event == "RISK_ON_SQUEEZE":
            reason_chain.append("Event: RISK_ON_SQUEEZE → 상승 압력 강화 (단, 과열 주의)")
            
    # 2) Divergence override
    if sew_status not in ["DEADMAN", "ALERT"]:
        if div_status != "ALIGNED":
            if final_action == "INCREASE":
                final_action = "HOLD"
                final_exposure = int(base_exposure * 0.8)
                reason_chain.append("Divergence 비정렬 → INCREASE 억제, HOLD로 하향")
            elif final_action == "HOLD":
                final_action = "REDUCE"
                final_exposure = int(base_exposure * 0.8)
                reason_chain.append("Divergence 비정렬 → HOLD에서 REDUCE로 전환")
            else:
                reason_chain.append("Divergence 비정렬 → 방어적 태도 유지")
        else:
            reason_chain.append("Divergence ALIGNED → 구조·가격·수급 정렬")

    # 3) Narrative confirmation
    if sew_status == "STABLE" and div_status == "ALIGNED":
        reason_chain.append(f"Narrative Action={narrative_action} 반영")
    else:
        reason_chain.append("상위 레이어(SEW/Divergence)가 Narrative보다 우선")

    # 4) Warning signals
    corr65_score = int(warn.get("corr65_score", 0) or 0)
    corr66_score = int(warn.get("corr66_score", 0) or 0)
    geo_level = str(warn.get("geo_level", "NORMAL")).upper()

    warning_score = corr65_score + corr66_score
    warning_notes = []

    if warn.get("corr65_break"):
        warning_notes.append("6.5 상관관계 붕괴")
    if warn.get("corr66_break"):
        warning_notes.append("6.6 섹터 상관관계 붕괴")

    if geo_level == "ELEVATED":
        warning_score += 1
        warning_notes.append("7.2 지정학 경계(ELEVATED)")
    elif geo_level == "CRISIS":
        warning_score += 2
        warning_notes.append("7.2 지정학 위기(CRISIS)")

    if warning_score >= 3:
        if final_action == "INCREASE":
            final_action = "HOLD"
        elif final_action == "HOLD":
            final_action = "REDUCE"
        final_exposure = int(final_exposure * 0.75)
        reason_chain.append("Warning Score 3+ → 공격적 확장 금지 / 익스포저 25% haircut")
    elif warning_score == 2:
        final_exposure = int(final_exposure * 0.85)
        reason_chain.append("Warning Score 2 → 익스포저 15% haircut")
    elif warning_score == 1:
        reason_chain.append("Warning Score 1 → 경미한 이상신호, 모니터링 강화")

    final_exposure = max(0, min(100, final_exposure))

    lines = []
    lines.append("## 🎯 Final Decision (War Room Override)")
    lines.append(f"- **Final Action:** **{final_action}**")
    lines.append(f"- **Final Exposure:** **{final_exposure}%**")
    lines.append(f"- **Base Context:** phase={phase} / narrative={narrative_action} / base_exposure={base_exposure}%")
    lines.append(f"- **SEW:** {sew_status} / {sew_event}")
    lines.append(f"- **Divergence:** {div_status} / {div_action}")
    lines.append(f"- **Warning Score:** {warning_score} ({', '.join(warning_notes) if warning_notes else 'No warning'})")
    lines.append(f"- **Why:** " + " → ".join(reason_chain))

    return "\n".join(lines)
