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


def execution_layer_filter(market_data: Dict[str, Any], debug: bool = False) -> Dict[str, Any]:
    """
    Execution / Style Translation Layer (v1.2)

    목적:
    - 1~18번 필터에서 정리된 시장 상태를 바탕으로
      실행 가능한 스타일 / 기업 타입 / ETF 해석용 태그를 생성
    - 리포트용 텍스트 + 후속 로직용 구조화 데이터 동시 반환
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
    style_tags: List[str] = []

    if debug:
        print(
            f"[DEBUG] structure={structure}, "
            f"liquidity_dir={liq_dir}, liquidity_level={liq_lvl}, "
            f"credit_calm={credit_calm}"
        )

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
        style_tags += [
            "defensive",
            "quality",
            "low_beta",
            "cashflow_strength",
            "balance_sheet_strength",
            "raroc_friendly",
        ]

    # Priority 2: Structure
    if structure == "TIGHTENING":
        preferred.append("Cash flow visibility and earnings stability")
        avoid.append("Rate-sensitive long-duration equities")
        style_tags += [
            "earnings_stability",
            "duration_aware",
        ]

    # Priority 3: Credit
    if credit_calm is False:
        preferred.append("Strong liquidity buffers and defensive balance sheets")
        avoid.append("Highly levered capital structures")
        style_tags += [
            "credit_defense",
            "liquidity_buffer",
        ]

    # fallback
    if not preferred:
        preferred = [
            "Balanced quality exposure",
            "Selective sector-neutral positioning",
        ]

    if not avoid:
        avoid = [
            "Unscreened speculative exposure",
        ]

    preferred = _uniq_keep_order(preferred)
    avoid = _uniq_keep_order(avoid)
    style_tags = _uniq_keep_order(style_tags)

    lines: List[str] = []
    lines.append("### 🧬 19.5) Execution / Style Translation Layer")
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

    report_text = "\n".join(lines)

    return {
        "report": report_text,
        "preferred_traits": preferred,
        "avoid_traits": avoid,
        "sector_ow": sector_ow,
        "sector_uw": sector_uw,
        "style_tags": style_tags,
    }


def executive_summary_filter(market_data: Dict[str, Any], debug: bool = False) -> str:
    """
    Wrapper:
    - generate_report.py 등 기존 코드와 호환되도록
      summary text만 반환
    """
    result = execution_layer_filter(market_data, debug=debug)
    return result["report"]
