# filters/scenario_layer.py
from typing import Dict, Any

def scenario_generator_filter(market_data: Dict[str, Any]) -> str:
    """
    Scenario Generator v1
    Uses FINAL_STATE + key signals to construct Base/Bull/Bear frameworks.
    """

    state = market_data.get("FINAL_STATE", {}) or {}

    phase = str(state.get("phase", "N/A"))
    budget = state.get("risk_budget", None)
    action = str(state.get("risk_action", "HOLD"))
    liq_dir = str(state.get("liquidity_dir", "N/A"))
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A"))
    credit_calm = state.get("credit_calm", None)

    exposure_txt = f"{budget}%" if isinstance(budget, int) else "중립"

    # -------------------------
    # Base Case
    # -------------------------
    base = []
    base.append("유동성 혼조 + 크레딧 안정 유지")
    base.append("변동성 급등 없이 박스권 장세 지속")
    base_action = f"노출 {exposure_txt} 유지, 퀄리티 중심 선별적 접근"

    # -------------------------
    # Bull Case
    # -------------------------
    bull = []
    bull.append("NET_LIQ 회복 (dir=UP & level=MID 이상)")
    bull.append("크레딧 스프레드 추가 축소")
    bull_action = "노출 단계적 확대, 성장/리스크 자산 베타 확장"

    # -------------------------
    # Bear Case
    # -------------------------
    bear = []
    bear.append("HY OAS > 4% 상회 또는 급등")
    bear.append("VIX 22 이상 또는 급등 전환")
    bear_action = "노출 35% 이하 축소, 방어/현금 비중 확대"

    lines = []
    lines.append("## 🗺️ Scenario Framework (Base / Bull / Bear)")
    lines.append("")
    lines.append("### 🔹 Base Case")
    lines.append("- 조건: " + " / ".join(base))
    lines.append("- 전략: " + base_action)
    lines.append("")
    lines.append("### 🔼 Bull Case")
    lines.append("- 조건: " + " / ".join(bull))
    lines.append("- 전략: " + bull_action)
    lines.append("")
    lines.append("### 🔻 Bear Case")
    lines.append("- 조건: " + " / ".join(bear))
    lines.append("- 전략: " + bear_action)

    return "\n".join(lines)
