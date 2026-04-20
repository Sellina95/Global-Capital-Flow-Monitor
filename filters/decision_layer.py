from typing import Dict, Any


def decision_layer_filter(market_data: Dict[str, Any]) -> str:
    """
    So What? Decision Layer (v3)
    - Strategic View (FINAL_STATE)와 Execution View (FINAL_DECISION)를 분리해서 보여줌
    - War Room 최종 판단을 보고서 하단 So What에 일관되게 반영
    """

    state = market_data.get("FINAL_STATE", {}) or {}
    final_decision = market_data.get("FINAL_DECISION", {}) or {}
    warn = market_data.get("WARNING_SIGNALS", {}) or {}

    # -------------------------
    # Strategic layer (Base)
    # -------------------------
    phase = str(state.get("phase", "N/A"))
    strategic_action = str(state.get("risk_action", "HOLD")).upper()
    strategic_budget = state.get("risk_budget", None)

    liq_dir = str(state.get("liquidity_dir", "N/A")).upper()
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A")).upper()
    credit_calm = state.get("credit_calm", None)

    # -------------------------
    # Execution layer (Final)
    # -------------------------
    execution_action = str(final_decision.get("action", strategic_action)).upper()

    try:
        base_exposure = int(
            final_decision.get(
                "base_exposure",
                strategic_budget if strategic_budget is not None else 50,
            )
        )
    except Exception:
        base_exposure = 50

    try:
        final_exposure = int(final_decision.get("exposure", base_exposure))
    except Exception:
        final_exposure = base_exposure

    sew_status = str(final_decision.get("sew_status", "N/A")).upper()
    sew_event = str(final_decision.get("sew_event", "N/A")).upper()

    div_status = str(final_decision.get("div_status", "N/A")).upper()
    div_action = str(final_decision.get("div_action", "HOLD")).upper()

    # -------------------------
    # Style / Factor hints
    # -------------------------
    style = market_data.get("STYLE_TILT", None)
    duration = market_data.get("DURATION_TILT", None)
    cyclical = market_data.get("CYCLICAL_TILT", None)

    style_hint = []
    if style:
        style_hint.append(f"Style={style}")
    if duration:
        style_hint.append(f"Duration={duration}")
    if cyclical:
        style_hint.append(f"Cyclical/Defensive={cyclical}")

    # -------------------------
    # Warning score
    # -------------------------
    corr65_score = int(warn.get("corr65_score", 0) or 0)
    corr66_score = int(warn.get("corr66_score", 0) or 0)
    warn_geo_level = str(warn.get("geo_level", "NORMAL")).upper()

    warning_score = corr65_score + corr66_score
    warning_notes = []

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

    # -------------------------
    # Actionable guidance
    # -------------------------
    do, dont, triggers = [], [], []

    # execution_action 기준으로 작성
    if execution_action == "INCREASE":
        do.append("전략·실행 판단이 모두 확장 쪽에 정렬된 상태로, 베타를 단계적으로 확대")
        do.append("퀄리티(현금흐름/재무안정) 중심으로 리스크 자산 비중 확대")
        triggers.append("VIX 급등 또는 HY OAS 확대 시 즉시 방어")
        dont.append("무분별한 테마 추격")
        dont.append("리스크 관리 없는 집중 포지션")

    elif execution_action == "REDUCE":
        do.append("실행 레이어 기준 방어 우선, 현금/단기자산 비중 확대")
        do.append("레버리지·저품질 크레딧·고베타 익스포저 축소")
        triggers.append("SEW 안정화 / Warning 정상화 확인 전까지 방어적 운용 유지")
        dont.append("공격적 베타 확대")
        dont.append("고변동성 자산 비중 확대")

    else:  # HOLD
        if final_exposure < base_exposure:
            do.append("구조적으로는 확대 가능하나, 현재는 리스크 오버라이드 반영으로 사이징 축소 유지")
            do.append("퀄리티 중심 선별적 포지셔닝 유지")
            triggers.append("Warning Score 정상화 / SEW 안정 / Divergence ALIGNED 유지 시 확대 재개 검토")
            dont.append("경고 신호 해소 전 무리한 베타 확대")
            dont.append("테마성 추격 매수")
        else:
            do.append("노출은 유지하되, 베타 확대보다 선별적 포지셔닝(퀄리티) 유지")
            triggers.append("NET_LIQ 추가 하락/LOW 고착 시 노출 축소 준비")
            dont.append("무분별한 테마 추격")
            dont.append("리스크 관리 없는 집중 포지션")

    if credit_calm is False:
        do.append("크레딧 스트레스 확인 시 방어 전환 우선")
        triggers.append("HY OAS 4% 상회 시 Risk-Off 프로토콜")

    if sew_status in ["WATCH", "ALERT", "DEADMAN"]:
        triggers.append(f"SEW {sew_status} 해소 여부 확인 필요")

    if div_status != "ALIGNED":
        triggers.append("Divergence 비정렬 해소 전까지 공격적 확장 보류")

    # -------------------------
    # Text assembly
    # -------------------------
    lines = []
    lines.append("## 🧭 So What? (Decision Layer)")
    lines.append(f"- **Strategic View:** **{strategic_action}** *(base exposure: {base_exposure}%)*")
    lines.append(f"- **Execution View:** **{execution_action}** *(final exposure: {final_exposure}%)*")
    lines.append(f"- **Context:** phase={phase} / liquidity={liq_dir}-{liq_lvl} / credit_calm={credit_calm} / geo={warn_geo_level}")
    lines.append(f"- **SEW / Divergence:** {sew_status} / {sew_event} | {div_status} / {div_action}")

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
    Final Decision Layer (War Room Override) - Unified Final

    Priority:
    1) SEW
    2) Event Type
    3) Divergence
    4) Narrative / FINAL_STATE
    5) Warning Score (6.5 / 6.6 / 7.2)
    6) Tactical Overlay (Drift / Flow / Gamma / Final Action Engine)
    7) Recovery / Exposure sizing
    """

    state = market_data.get("FINAL_STATE", {}) or {}
    sew = market_data.get("SEW_STATE", {}) or {}
    div = market_data.get("DIVERGENCE_STATE", {}) or {}
    warn = market_data.get("WARNING_SIGNALS", {}) or {}

    drift = market_data.get("DRIFT", {}) or {}
    inst_flow = market_data.get("INSTITUTIONAL_FLOW", {}) or {}

    # -------------------------
    # Base / Narrative
    # -------------------------
    narrative_action = str(state.get("risk_action", "HOLD")).upper()
    risk_budget = int(state.get("risk_budget", 50)) if state.get("risk_budget") is not None else 50
    phase = str(state.get("phase", "N/A"))

    # -------------------------
    # SEW / Divergence
    # -------------------------
    sew_status = str(sew.get("status", "N/A")).upper()
    sew_event = str(sew.get("event_type", "N/A")).upper()

    div_status = str(div.get("status", "N/A")).upper()
    div_action = str(div.get("action", "HOLD")).upper()

    # -------------------------
    # Tactical inputs
    # -------------------------
    drift_state = str(drift.get("state", market_data.get("DRIFT_STATE", "N/A")) or "N/A")
    drift_label = str(drift.get("label", "N/A") or "N/A")
    drift_combo = str(drift.get("combo_signal", "NONE") or "NONE")
    try:
        drift_score = int(drift.get("score", market_data.get("DRIFT_SCORE", 0)) or 0)
    except Exception:
        drift_score = 0

    try:
        flow_score = int(inst_flow.get("score", 0) or 0)
    except Exception:
        flow_score = 0
    flow_state = str(inst_flow.get("state", "N/A") or "N/A")

    gamma_state = str(market_data.get("GAMMA_STATE", "N/A") or "N/A")
    pos_z = market_data.get("SP500_POS_Z", 0)
    try:
        pos_z = float(pos_z)
    except Exception:
        pos_z = 0.0

    # Final Action Engine 결과는 generate_report.py에서 먼저 계산한 값을 사용
    tactical = market_data.get("FINAL_ACTION", {}) or {}
    tactical_action = str(tactical.get("action", "HOLD") or "HOLD").upper()
    tactical_size = str(tactical.get("size", "NONE") or "NONE")
    tactical_confidence = str(tactical.get("confidence", "LOW") or "LOW")
    tactical_reasons = tactical.get("reason", []) or []

    # -------------------------
    # Exposure base
    # -------------------------
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
    if sew_status != "DEADMAN":
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

    # -------------------------
    # 2) Divergence override
    # -------------------------
    if sew_status not in ["DEADMAN", "ALERT"]:
        if div_status != "ALIGNED":
            if final_action == "INCREASE":
                final_action = "HOLD"
                final_exposure = int(final_exposure * 0.8)
                reason_chain.append("Divergence 비정렬 → INCREASE 억제, HOLD로 하향")
            elif final_action == "HOLD":
                final_action = "REDUCE"
                final_exposure = int(final_exposure * 0.8)
                reason_chain.append("Divergence 비정렬 → HOLD에서 REDUCE로 전환")
            else:
                reason_chain.append("Divergence 비정렬 → 방어적 태도 유지")
        else:
            reason_chain.append("Divergence ALIGNED → 구조·가격·수급 정렬")

    # -------------------------
    # 3) Narrative confirmation
    # -------------------------
    if sew_status == "STABLE" and div_status == "ALIGNED":
        reason_chain.append(f"Narrative Action={narrative_action} 반영")
    else:
        reason_chain.append("상위 레이어(SEW/Divergence)가 Narrative보다 우선")

    # -------------------------
    # 4) Warning signals
    # -------------------------
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

    # -------------------------
    # 5) Tactical Overlay (NEW, additive only)
    # - 새 점수체계 없이 최종판단에 보조 반영
    # -------------------------
    reason_chain.append(
        f"Tactical={tactical_action} / Flow={flow_state}({flow_score}) / Drift={drift_state}({drift_score}) / Gamma={gamma_state}"
    )

    # REDUCE / EXIT는 최종판단을 보수적으로 끌어내리는 역할만 수행
    if tactical_action == "EXIT":
        final_action = "EXIT"
        final_exposure = 0
        reason_chain.append("Tactical EXIT → 최종 EXIT 우선")

    elif tactical_action == "REDUCE":
        if final_action == "INCREASE":
            final_action = "HOLD"
            final_exposure = int(final_exposure * 0.9)
            reason_chain.append("Tactical REDUCE → INCREASE 억제 / 익스포저 10% 축소")
        elif final_action == "HOLD":
            final_action = "REDUCE"
            final_exposure = int(final_exposure * 0.9)
            reason_chain.append("Tactical REDUCE → HOLD에서 REDUCE 전환 / 익스포저 10% 축소")
        else:
            final_exposure = int(final_exposure * 0.95)
            reason_chain.append("Tactical REDUCE → 방어 기조 유지 / 익스포저 5% 추가 축소")

    # ADD / EARLY BUY는 상위 리스크가 조용할 때만 보조적으로 허용
    elif tactical_action in ["ADD", "EARLY BUY"]:
        if sew_status == "STABLE" and div_status == "ALIGNED" and warning_score <= 1:
            reason_chain.append(f"Tactical {tactical_action} → 상위 리스크 안정 구간, 확장 신호 확인")
        else:
            reason_chain.append(f"Tactical {tactical_action} → 상위 리스크 조건 미충족, 최종판단에는 보수 반영")

    else:
        reason_chain.append("Tactical HOLD/MONITOR → 최종판단 변경 없음")

    # -------------------------
    # 6) Recovery Engine v1 (Phased Recovery)
    # -------------------------
    if (
        warning_score <= 1
        and sew_status == "STABLE"
        and div_status == "ALIGNED"
        and tactical_action not in ["REDUCE", "EXIT"]
    ):
        if final_exposure < base_exposure:
            gap = base_exposure - final_exposure
            recovery_step = max(5, int(gap * 0.5))

            final_exposure = min(
                base_exposure,
                final_exposure + recovery_step
            )

            reason_chain.append(
                f"Recovery Engine → 조건 충족, 익스포저 단계적 복귀 (+{recovery_step}%)"
            )

    # -------------------------
    # 6.5) Recovery Debug
    # -------------------------
    market_data["RECOVERY_DEBUG"] = {
        "sew_ok": sew_status == "STABLE",
        "div_ok": div_status == "ALIGNED",
        "warning_ok": warning_score <= 1,
        "base_exposure": base_exposure,
        "final_exposure_before_clamp": final_exposure,
    }

    final_exposure = max(0, min(100, final_exposure))

    lines = []
    lines.append("## 🎯 Final Decision (War Room Override)")
    lines.append(f"- **Final Action:** **{final_action}**")
    lines.append(f"- **Final Exposure:** **{final_exposure}%**")
    lines.append(f"- **Base Context:** phase={phase} / narrative={narrative_action} / base_exposure={base_exposure}%")
    lines.append(f"- **SEW:** {sew_status} / {sew_event}")
    lines.append(f"- **Divergence:** {div_status} / {div_action}")
    lines.append(f"- **Drift:** {drift_state} / {drift_label} / {drift_combo} / score={drift_score}")
    lines.append(f"- **Flow:** {flow_state} / score={flow_score}")
    lines.append(f"- **Gamma:** {gamma_state}")
    lines.append(f"- **Tactical Action:** {tactical_action} / {tactical_size} / {tactical_confidence}")
    lines.append(f"- **Positioning:** pos_z={pos_z:.2f}")
    lines.append(f"- **Warning Score:** {warning_score} ({', '.join(warning_notes) if warning_notes else 'No warning'})")

    if tactical_reasons:
        lines.append(f"- **Tactical Why:** {' / '.join(tactical_reasons)}")

    lines.append(f"- **Why:** " + " → ".join(reason_chain))

    market_data["FINAL_DECISION"] = {
        "action": final_action,
        "exposure": final_exposure,
        "base_exposure": base_exposure,
        "warning_score": warning_score,
        "warning_notes": warning_notes,
        "sew_status": sew_status,
        "sew_event": sew_event,
        "div_status": div_status,
        "div_action": div_action,
        "phase": phase,
        "narrative_action": narrative_action,
        "reason_chain": reason_chain,
        "drift_score": drift_score,
        "drift_state": drift_state,
        "drift_label": drift_label,
        "flow_score": flow_score,
        "flow_state": flow_state,
        "gamma_state": gamma_state,
        "tactical_action": tactical_action,
        "tactical_size": tactical_size,
        "tactical_confidence": tactical_confidence,
        "tactical_reasons": tactical_reasons,
        "pos_z": pos_z,
    }

    return "\n".join(lines)
