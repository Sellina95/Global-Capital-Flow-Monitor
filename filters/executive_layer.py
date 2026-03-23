# filters/executive_layer.py
from typing import Dict, Any



def calculate_raroc(risk_adjusted_return: float, capital: float) -> float:
    """
    RAROC (Risk-Adjusted Return on Capital) 계산
    - risk_adjusted_return: 위험 조정된 수익률
    - capital: 자본 (리스크 자본)
    
    RAROC = risk_adjusted_return / capital
    """
    if capital == 0:  # 자본이 0일 때 RAROC 계산 방지
        return 0
    return risk_adjusted_return / capital
    
def executive_summary_filter(market_data: Dict[str, Any]) -> str:
    """
    Executive Compression (3 lines)
    Uses market_data["FINAL_STATE"] produced by narrative_engine_filter.
    """

    state = market_data.get("FINAL_STATE", {}) or {}
    print("[DEBUG][EXEC] structure_tag=", state.get("structure_tag"), "| policy_bias_line=", state.get("policy_bias_line"))

    phase = str(state.get("phase", "N/A"))
    structure = str(state.get("structure_tag", "MIXED"))
    liq_dir = str(state.get("liquidity_dir", "N/A"))
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A"))
    credit_calm = state.get("credit_calm", None)
    risk_budget = state.get("risk_budget", None)
    risk_action = str(state.get("risk_action", "HOLD"))

    # 1) Line 1: phase + structure
    phase_line = (
        "단기 리스크 선호가 회복되는 국면"
        if "RISK-ON" in phase.upper()
        else "리스크 회피가 우세한 국면"
        if "RISK-OFF" in phase.upper()
        else "방향성이 제한된 혼합 국면"
    )

    struct_line = (
        "구조는 완화 기조"
        if structure == "EASING"
        else "구조는 긴축 기조"
        if structure == "TIGHTENING"
        else "구조 신호는 혼조"
    )

    # 2) Line 2: liquidity/credit risk
    if liq_dir == "DOWN" or liq_lvl == "LOW":
        line2 = "유동성은 약화(흡수) 국면으로 상방 동력을 제한할 수 있다."
    elif liq_dir == "UP" and liq_lvl in ("MID", "HIGH"):
        line2 = "유동성 여건이 개선되며 리스크 자산에 우호적이다."
    else:
        # if liquidity ambiguous, use credit when available
        if credit_calm is True:
            line2 = "크레딧은 안정적이어서 급격한 리스크오프 신호는 제한적이다."
        elif credit_calm is False:
            line2 = "크레딧 스트레스가 높아 리스크 관리 우선순위가 상승했다."
        else:
            line2 = "유동성·크레딧 신호가 혼조로, 추세 확인이 필요하다."

    # 3) Line 3: action guidance
    budget_txt = f"{risk_budget}%" if isinstance(risk_budget, int) else "중립 수준"

    if risk_action == "INCREASE":
        line3 = f"전략적으로는 노출 확대가 가능하나, 규율 기반으로 {budget_txt} 내에서 단계적으로 접근한다."
    elif risk_action == "REDUCE":
        line3 = f"전략적으로는 노출 축소가 필요하며, {budget_txt} 이하로 리스크를 재조정한다."
    else:
        line3 = f"전략적으로는 공격적 확대보다 {budget_txt} 내외의 선별적 노출 유지가 적절하다."

    line1 = f"현재 시장은 {phase_line}이며, {struct_line}."

    # store for later layers if needed
    market_data["EXEC_SUMMARY_LINES"] = [line1, line2, line3]

    lines = []
    lines.append("## 🧾 Executive Summary (3 Lines)")
    lines.append(f"- {line1}")
    lines.append(f"- {line2}")
    lines.append(f"- {line3}")
    return "\n".join(lines)
