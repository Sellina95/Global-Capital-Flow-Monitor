# filters/scenario_layer.py
from typing import Dict, Any


def scenario_generator_filter(market_data: Dict[str, Any]) -> str:
    """
    Scenario Generator v2
    - Strategic View (FINAL_STATE)와 Execution View (FINAL_DECISION)를 분리
    - 현재 실행 기준(Base Case)과 재확대 조건(Bull Case), 추가 방어 조건(Bear Case)을 함께 제시
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
        base_exposure = int(final_decision.get("base_exposure", strategic_budget if strategic_budget is not None else 50))
    except Exception:
        base_exposure = 50

    try:
        final_exposure = int(final_decision.get("exposure", base_exposure))
    except Exception:
        final_exposure = base_exposure

    sew_status = str(final_decision.get("sew_status", "N/A")).upper()
    sew_event = str(final_decision.get("sew_event", "N/A")).upper()
    div_status = str(final_decision.get("div_status", "N/A")).upper()

    # -------------------------
    # Warning score
    # -------------------------
    corr65_score = int(warn.get("corr65_score", 0) or 0)
    corr66_score = int(warn.get("corr66_score", 0) or 0)
    geo_level = str(warn.get("geo_level", "NORMAL")).upper()

    warning_score = corr65_score + corr66_score
    if geo_level == "ELEVATED":
        warning_score += 1
    elif geo_level == "CRISIS":
        warning_score += 2

    # -------------------------
    # Base Case
    # -------------------------
    base_conditions = []
    base_conditions.append(f"현재 Execution View={execution_action} 유지")
    base_conditions.append(f"SEW={sew_status} / Divergence={div_status}")
    if warning_score > 0:
        base_conditions.append(f"Warning Score {warning_score} 지속")
    else:
        base_conditions.append("추가 경고 신호 없음")

    if final_exposure < base_exposure:
        base_action = (
            f"실행 노출 {final_exposure}% 유지, 퀄리티 중심 선별적 접근 "
            f"(전략 기준 {base_exposure}% 대비 방어적 사이징)"
        )
    else:
        base_action = (
            f"실행 노출 {final_exposure}% 유지, 전략 기준과 실행 기준이 정렬된 상태에서 운용"
        )

    # -------------------------
    # Bull Case
    # -------------------------
    bull_conditions = []
    bull_conditions.append("Warning Score ≤ 1")
    bull_conditions.append("SEW: STABLE 유지")
    bull_conditions.append("Divergence: ALIGNED 유지")
    bull_conditions.append("NET_LIQ 우호 / 크레딧 안정 지속")

    if final_exposure < base_exposure:
        bull_action = (
            f"실행 노출 {final_exposure}% → {base_exposure}%로 복귀, "
            "성장/리스크 자산 베타 단계적 재확대"
        )
    else:
        bull_action = (
            f"실행 노출 {base_exposure}% 유지 또는 추가 확장 검토, "
            "성장/리스크 자산 베타 우호"
        )

    # -------------------------
    # Bear Case
    # -------------------------
    bear_conditions = []
    bear_conditions.append("SEW WATCH/ALERT/DEADMAN 재발")
    bear_conditions.append("HY OAS 4% 상회 또는 급등")
    bear_conditions.append("VIX 22 이상 또는 급등 전환")
    bear_conditions.append("상관관계 붕괴 심화 / Divergence 비정렬 전환")

    if final_exposure > 35:
        bear_action = (
            f"실행 노출 {final_exposure}%에서 추가 축소, "
            "방어/현금 비중 확대 및 고베타 자산 감축"
        )
    else:
        bear_action = (
            f"실행 노출 {final_exposure}% 이하 방어 유지, "
            "현금/방어자산 중심으로 생존 우선"
        )

    # -------------------------
    # Text assembly
    # -------------------------
    lines = []
    lines.append("## 🗺️ Scenario Framework (Base / Bull / Bear)")
    lines.append("")
    lines.append(
        f"- **Strategic View:** {strategic_action} ({base_exposure}%) | "
        f"**Execution View:** {execution_action} ({final_exposure}%)"
    )
    lines.append(
        f"- **Context:** phase={phase} / liquidity={liq_dir}-{liq_lvl} / "
        f"credit_calm={credit_calm} / geo={geo_level}"
    )
    lines.append("")

    lines.append("### 🔹 Base Case")
    lines.append("- 조건: " + " / ".join(base_conditions))
    lines.append("- 전략: " + base_action)
    lines.append("")

    lines.append("### 🔼 Bull Case")
    lines.append("- 조건: " + " / ".join(bull_conditions))
    lines.append("- 전략: " + bull_action)
    lines.append("")

    lines.append("### 🔻 Bear Case")
    lines.append("- 조건: " + " / ".join(bear_conditions))
    lines.append("- 전략: " + bear_action)

    return "\n".join(lines)
