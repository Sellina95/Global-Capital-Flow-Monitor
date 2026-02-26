# filters/transmission_layer.py
from typing import Dict, Any

def transmission_layer_filter(market_data: Dict[str, Any]) -> str:
    """
    Transmission Layer v1
    Macro → Factor → Industry → Company Type 연결 설명
    """

    state = market_data.get("FINAL_STATE", {}) or {}

    struct = str(state.get("structure_tag", "MIXED"))
    liq_dir = str(state.get("liquidity_dir", "N/A"))
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A"))
    credit_calm = state.get("credit_calm", None)

    lines = []
    lines.append("## 🔗 Transmission Map (Macro → Industry → Company)")
    lines.append("")

    # -----------------------------
    # 1️⃣ Structure → Valuation Path
    # -----------------------------
    if struct == "TIGHTENING":
        lines.append("- 금리·정책 긴축 기조")
        lines.append("  → 할인율 상승")
        lines.append("  → 장기 현금흐름(Duration 긴) 기업 멀티플 압박")
        lines.append("  → 고밸류 성장주/Tech/SaaS 상대적 부담")
        lines.append("")
    elif struct == "EASING":
        lines.append("- 정책 완화 기조")
        lines.append("  → 할인율 하락")
        lines.append("  → 멀티플 확장")
        lines.append("  → Growth/High Beta/소형주 상대적 우위")
        lines.append("")
    else:
        lines.append("- 정책 혼조(Mixed)")
        lines.append("  → 할인율 방향성 불명확")
        lines.append("  → 멀티플 확장 제한적")
        lines.append("  → 퀄리티/현금흐름 중심 차별화 장세")
        lines.append("")

    # -----------------------------
    # 2️⃣ Liquidity → Beta Path
    # -----------------------------
    if liq_dir == "DOWN" or liq_lvl == "LOW":
        lines.append("- 유동성 흡수(달러 체력 약화)")
        lines.append("  → 리스크 허용 축소")
        lines.append("  → 고베타·레버리지 기업 압박")
        lines.append("  → Defensive/현금흐름 안정 기업 선호")
        lines.append("")
    elif liq_dir == "UP":
        lines.append("- 유동성 공급 확대")
        lines.append("  → 리스크 허용 확대")
        lines.append("  → Cyclical/High Beta 확장")
        lines.append("")
    else:
        lines.append("- 유동성 혼조")
        lines.append("  → 베타 플레이 제한적")
        lines.append("")

    # -----------------------------
    # 3️⃣ Credit → Balance Sheet Path
    # -----------------------------
    if credit_calm is False:
        lines.append("- 크레딧 스트레스 확대")
        lines.append("  → 자금조달 비용 상승")
        lines.append("  → 고부채 기업/은행/하이일드 취약")
        lines.append("")
    elif credit_calm is True:
        lines.append("- 크레딧 안정")
        lines.append("  → 시스템 리스크 낮음")
        lines.append("  → 디레버리징 압력 제한적")
        lines.append("")
    else:
        lines.append("- 크레딧 신호 불명확")
        lines.append("")

    return "\n".join(lines)
