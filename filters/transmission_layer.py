# filters/transmission_layer.py
from typing import Dict, Any

def transmission_layer_filter(market_data: Dict[str, Any]) -> str:
    """
    Transmission Layer v1.2
    Macro → Factor → Industry → Company Type 연결을
    '1줄 결론 + 근거' 형태로 압축.
    """

    state = market_data.get("FINAL_STATE", {}) or {}

    struct = str(state.get("structure_tag", "MIXED"))
    liq_dir = str(state.get("liquidity_dir", "N/A"))
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A"))
    credit_calm = state.get("credit_calm", None)

    # ----- Core conclusion tags -----
    # Policy/valuation implication
    if struct == "TIGHTENING":
        policy_imp = "할인율↑(멀티플 압박)"
        equity_bias = "장기듀레이션 성장주 불리"
    elif struct == "EASING":
        policy_imp = "할인율↓(멀티플 확장)"
        equity_bias = "성장/고베타 우위"
    else:
        policy_imp = "할인율 방향성 불명확"
        equity_bias = "퀄리티 중심 차별화"

    # Liquidity implication
    if liq_dir == "DOWN" or liq_lvl == "LOW":
        liq_imp = "유동성 흡수(리스크 허용↓)"
        beta_bias = "고베타/레버리지 제한"
        company_pref = "High FCF / Low leverage / pricing power"
        sector_hint = "Defensive(Staples/Utilities/Healthcare) + Mega-cap quality"
    elif liq_dir == "UP" and liq_lvl in ("MID", "HIGH"):
        liq_imp = "유동성 공급(리스크 허용↑)"
        beta_bias = "베타 확장 가능"
        company_pref = "High operating leverage / cyclicals / growth optionality"
        sector_hint = "Cyclicals/Tech(상황에 따라) + Small/Mid beta"
    else:
        liq_imp = "유동성 혼조"
        beta_bias = "베타 중립"
        company_pref = "퀄리티 + 리스크 관리형 포지셔닝"
        sector_hint = "Balanced / barbell"

    # Credit implication
    if credit_calm is False:
        credit_imp = "크레딧 스트레스↑(조달비용↑)"
        credit_bias = "고부채/하이일드 취약"
    elif credit_calm is True:
        credit_imp = "크레딧 안정"
        credit_bias = "시스템 리스크 제한"
    else:
        credit_imp = "크레딧 혼조"
        credit_bias = "추가 확인 필요"

    # ----- Output -----
    lines = []
    lines.append("## 🔗 Transmission Map (Macro → Industry → Company)")
    lines.append(f"- **1-Line Conclusion:** {equity_bias} + {beta_bias} → **{company_pref}** 선호")
    lines.append("")
    lines.append(f"- **Policy → Valuation:** {policy_imp} → {equity_bias}")
    lines.append(f"- **Liquidity → Risk Budget:** {liq_imp} → {beta_bias}")
    lines.append(f"- **Credit → Balance Sheet:** {credit_imp} → {credit_bias}")
    lines.append("")
    lines.append(f"- **Sector/Company Shortcut:** {sector_hint}")

    return "\n".join(lines)
