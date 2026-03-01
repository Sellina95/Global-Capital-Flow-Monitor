from typing import Dict, Any

def decision_layer_filter(market_data: Dict[str, Any]) -> str:
    """
    So What? Decision Layer (v1)
    Turns FINAL_STATE + style/factor outputs into actionable guidance.
    + GEO_EW overlay (Early Warning)
    """

    state = market_data.get("FINAL_STATE", {}) or {}

    phase = str(state.get("phase", "N/A"))
    action = str(state.get("risk_action", "HOLD"))
    budget = state.get("risk_budget", None)

    liq_dir = str(state.get("liquidity_dir", "N/A"))
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A"))
    credit_calm = state.get("credit_calm", None)

    # Optional if you later store them as keys
    style = market_data.get("STYLE_TILT", None)
    duration = market_data.get("DURATION_TILT", None)
    cyclical = market_data.get("CYCLICAL_TILT", None)

    exposure_txt = f"{budget}%" if isinstance(budget, int) else "중립"

    # --- stance adjustment (liquidity penalty)
    stance = action
    if action == "INCREASE" and (liq_dir == "DOWN" or liq_lvl == "LOW"):
        stance = "HOLD"

    # --- build Do / Don't / Triggers
    do, dont, triggers = [], [], []

    if stance == "INCREASE":
        do += ["노출을 단계적으로 확대하되, 퀄리티(현금흐름/재무안정) 중심으로 확대"]
        triggers += ["VIX 급등 또는 HY OAS 확대 시 즉시 방어"]
    elif stance == "REDUCE":
        do += ["현금/단기자산 비중 확대, 레버리지·저품질 크레딧 노출 축소"]
        triggers += ["크레딧 추가 악화 시 추가 디레버리징"]
    else:
        do += ["노출은 유지하되, 베타 확대보다 ‘선별적 포지셔닝(퀄리티)’ 유지"]
        triggers += ["NET_LIQ 추가 하락/LOW 고착 시 노출 축소 준비"]

    # Liquidity overlay
    if liq_dir == "DOWN" or liq_lvl == "LOW":
        dont += ["공격적 베타 확대", "장기듀레이션 성장주/레버리지 익스포저 확대"]
    else:
        dont += ["무분별한 테마 추격", "리스크 관리 없는 집중 포지션"]

    # Credit overlay
    if credit_calm is False:
        do += ["크레딧 스트레스 확인 시(우선순위 1) 방어 전환"]
        triggers += ["HY OAS 4% 상회 시 ‘Risk-Off 프로토콜’"]

    # -------------------------
    # ✅ GEO Early Warning overlay (NEW)
    # - market_data["GEO_EW"] created by attach_geopolitical_ew_layer
    # - This does NOT change FINAL_STATE logic; only adjusts stance + guidance
    # -------------------------
    geo = market_data.get("GEO_EW", {}) or {}
    geo_level = str(geo.get("level", "NORMAL")).upper()

    if geo_level == "ELEVATED":
        # if you wanted to increase, suppress to HOLD
        if stance == "INCREASE":
            stance = "HOLD"
        do.append("Geo EW Elevated → 지정학 리스크 헤어컷 적용 (베타 확대 자제)")
        triggers.append("Geo Score 추가 상승/확산 시 방어 전환")
    elif geo_level == "CRISIS":
        stance = "REDUCE"
        do.append("Geo EW Crisis → 지정학 스트레스 급등, 즉시 방어 모드")
        dont.append("공격적 베타 포지셔닝")
        triggers.append("Geo Score 정상화 확인 전까지 리스크 축소 유지")

    # Style hints (optional text)
    style_hint = []
    if style or duration or cyclical:
        if style:
            style_hint.append(f"Style={style}")
        if duration:
            style_hint.append(f"Duration={duration}")
        if cyclical:
            style_hint.append(f"Cyclical/Defensive={cyclical}")

    lines = []
    lines.append("## 🧭 So What? (Decision Layer)")
    lines.append(f"- **Risk Stance:** **{stance}** *(target exposure: {exposure_txt})*")
    lines.append(f"- **Context:** phase={phase} / liquidity={liq_dir}-{liq_lvl} / credit_calm={credit_calm} / geo={geo_level}")
    if style_hint:
        lines.append(f"- **Style Hints:** " + " / ".join(style_hint))
        lines.append(f"- **Do:** " + "; ".join(do))
        lines.append(f"- **Don't:** " + "; ".join(dont))
        lines.append(f"- **Triggers:** " + "; ".join(triggers))
    geo_overlay = market_data.get("GEO_OVERLAY", {}) or {}
    if geo_overlay and geo_overlay.get("budget_delta", 0) != 0:
        lines.append(f"- **Geo Overlay:** {geo_overlay.get('note')} → budget {geo_overlay.get('base_budget')}% → {geo_overlay.get('final_budget')}%")
    return "\n".join(lines)
