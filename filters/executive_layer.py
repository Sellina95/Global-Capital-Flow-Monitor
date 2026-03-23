from typing import Dict, Any, List

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
    Execution / Style Translation Layer (v1.1)
    - 환경에 맞는 주식 선택 기준을 제공
    - RAROC 우수 종목을 우선 고려하는 로직 추가
    """
    state = market_data.get("FINAL_STATE", {}) or {}
    structure = str(state.get("structure_tag", "MIXED")).upper()
    liq_dir = str(state.get("liquidity_dir", "N/A")).upper()
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A")).upper()
    credit_calm = state.get("credit_calm", None)

    # (선택) 18번 결과가 market_data에 저장돼 있다면 가져오기
    sector_ow = market_data.get("SECTOR_OW", []) or []
    sector_uw = market_data.get("SECTOR_UW", []) or []

    preferred: List[str] = []
    avoid: List[str] = []

    # ---- Priority 1: Liquidity ----
    if liq_dir == "DOWN" or liq_lvl == "LOW":
        preferred += [
            "High Free Cash Flow generators",
            "Net cash or low leverage balance sheets",
            "Stable margins / pricing power",
            "Low to mid beta exposure",
            "High RAROC Focus",  # RAROC가 높은 종목 우선 고려
        ]
        avoid += [
            "Negative FCF / cash-burn models",
            "High leverage / refinancing-dependent names",
            "Long-duration, high-multiple growth",
        ]

    # ---- Priority 2: Structure ----
    if structure == "TIGHTENING":
        preferred.append("Cash flow visibility and earnings stability")
        avoid.append("Rate-sensitive long-duration equities")

    # ---- Priority 3: Credit ----
    if credit_calm is False:
        preferred.append("Strong liquidity buffers and defensive balance sheets")
        avoid.append("Highly levered capital structures")

    # ---- Priority 4: RAROC ----
    # RAROC가 높은 종목을 우선적으로 선택하는 로직 추가
    if "RAROC" in market_data and market_data["RAROC"] > 0.1:
        preferred.append("High RAROC Focus")  # RAROC가 0.1 이상인 기업 우선

    preferred = _uniq_keep_order(preferred)
    avoid = _uniq_keep_order(avoid)

    lines = []
    lines.append("### 🧬 19) Execution / Style Translation Layer")
    lines.append("- **Implementation Focus:** Environment-Aware Stock Types")
    lines.append("")
  
    # 섹터 연결(있으면)
    if sector_ow or sector_uw:
        if sector_ow:
            lines.append(f"- **Apply to Overweight Sectors:** {', '.join(sector_ow)}")
        if sector_uw:
            lines.append(f"- **Apply to Underweight Sectors:** {', '.join(sector_uw)}")
        lines.append("")

    lines.append("**Preferred Company Traits:**")
    for p in preferred:
        lines.append(f"- {p}")

    lines.append("")
    lines.append("**Risk Control / Avoid:**")
    for a in avoid:
        lines.append(f"- {a}")
        
    return "\n".join(lines)

def _uniq_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        if not x:
            continue
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out