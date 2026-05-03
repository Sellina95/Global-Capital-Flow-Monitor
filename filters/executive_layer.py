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
    Execution / Style Translation Layer (v1.3)

    목적:
    - 1~18.5번 필터에서 정리된 시장 상태를 바탕으로
      실행 가능한 스타일 / 기업 타입 / ETF 해석용 태그를 생성
    - Flow / Positioning / Exposure 문맥까지 반영
    """

    state = market_data.get("FINAL_STATE", {}) or {}

    structure = str(state.get("structure_tag", "MIXED")).upper()
    liq_dir = str(state.get("liquidity_dir", "N/A")).upper()
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A")).upper()
    credit_calm = state.get("credit_calm", None)

    flow_score = state.get("flow_score", 0)
    try:
        flow_score = int(flow_score)
    except Exception:
        flow_score = 0

    flow_state = str(state.get("flow_state", "N/A") or "N/A").upper()
    pos_z = state.get("pos_z", market_data.get("SP500_POS_Z", 0.0))
    try:
        pos_z = float(pos_z)
    except Exception:
        pos_z = 0.0

    recommended_exposure = market_data.get("RECOMMENDED_EXPOSURE", None)
    try:
        recommended_exposure = float(recommended_exposure)
    except Exception:
        recommended_exposure = None

    sector_ow = market_data.get("SECTOR_OW", []) or []
    sector_uw = market_data.get("SECTOR_UW", []) or []

    preferred: List[str] = []
    avoid: List[str] = []
    style_tags: List[str] = []
    execution_notes: List[str] = []

    if debug:
        print(
            f"[DEBUG] structure={structure}, "
            f"liquidity_dir={liq_dir}, liquidity_level={liq_lvl}, "
            f"credit_calm={credit_calm}, flow_score={flow_score}, "
            f"flow_state={flow_state}, pos_z={pos_z}, "
            f"recommended_exposure={recommended_exposure}"
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

    # Priority 4: Flow confidence
    if flow_score <= 2:
        execution_notes.append("Flow weak → avoid chasing; keep only proven leaders.")
        preferred.append("Market leaders with confirmed relative strength")
        avoid.append("Flow-weak cyclicals and theory-only sector bets")
        style_tags += ["flow_selective", "leader_only"]

    elif flow_score <= 4:
        execution_notes.append("Early flow trace → maintain leaders, wait for confirmation before broadening.")
        preferred.append("Leaders with improving breadth confirmation")
        avoid.append("Broad beta expansion before confirmation")
        style_tags += ["early_flow", "selective_beta"]

    else:
        execution_notes.append("Flow building → selective expansion allowed if risk controls remain stable.")
        preferred.append("High-conviction leaders with cross-asset confirmation")
        style_tags += ["flow_building", "selective_expansion"]

    # Priority 5: Positioning heat
    if pos_z >= 1.7:
        execution_notes.append("Positioning heat elevated → prefer rebalancing over fresh chasing.")
        avoid.append("Crowded late-entry trades")
        style_tags += ["positioning_heat", "no_chase"]

    # Priority 6: Exposure regime
    if recommended_exposure is not None and recommended_exposure < 45:
        execution_notes.append("Exposure below 45% → defensive execution; cash remains strategic asset.")
        preferred.append("Smaller position sizes with strict risk budget discipline")
        style_tags += ["defensive_execution", "cash_buffer"]

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
    execution_notes = _uniq_keep_order(execution_notes)

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

    if execution_notes:
        lines.append("**Execution Notes:**")
        for n in execution_notes:
            lines.append(f"- {n}")
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
        "execution_notes": execution_notes,
    }

def executive_summary_filter(market_data: Dict[str, Any], debug: bool = False) -> str:
    """
    Wrapper:
    - generate_report.py 등 기존 코드와 호환되도록
      summary text만 반환
    """
    result = execution_layer_filter(market_data, debug=debug)
    return result["report"]
