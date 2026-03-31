from typing import Dict, Any, List

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

def executive_summary_filter(market_data: Dict[str, Any]) -> str:
    """
    Execution / Style Translation Layer
    - 환경에 맞는 주식/ETF 선택 기준 제시
    - 실제 RAROC 계산이 아니라, RAROC-friendly 스타일 선호 기준을 출력
    """
    state = market_data.get("FINAL_STATE", {}) or {}
    structure = str(state.get("structure_tag", "MIXED")).upper()
    liq_dir = str(state.get("liquidity_dir", "N/A")).upper()
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A")).upper()
    credit_calm = state.get("credit_calm", None)

    sector_ow = market_data.get("SECTOR_OW", []) or []
    sector_uw = market_data.get("SECTOR_UW", []) or []

    preferred: List[str] = []
    avoid: List[str] = []

    # Priority 1: Liquidity
    if liq_dir == "DOWN" or liq_lvl == "LOW":
        preferred += [
            "High Free Cash Flow generators",
            "Net cash or low leverage balance sheets",
            "Stable margins / pricing power",
            "Low to mid beta exposure",
            "RAROC-friendly profile",
        ]
        avoid += [
            "Negative FCF / cash-burn models",
            "High leverage / refinancing-dependent names",
            "Long-duration, high-multiple growth",
        ]

    # Priority 2: Structure
    if structure == "TIGHTENING":
        preferred.append("Cash flow visibility and earnings stability")
        avoid.append("Rate-sensitive long-duration equities")

    # Priority 3: Credit
    if credit_calm is False:
        preferred.append("Strong liquidity buffers and defensive balance sheets")
        avoid.append("Highly levered capital structures")

    preferred = _uniq_keep_order(preferred)
    avoid = _uniq_keep_order(avoid)

    lines = []
    lines.append("### 🧬 19) Execution / Style Translation Layer")
    lines.append("- **Implementation Focus:** Environment-Aware Stock Types")
    lines.append("")

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