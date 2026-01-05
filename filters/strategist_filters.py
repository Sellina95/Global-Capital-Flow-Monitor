from __future__ import annotations
from typing import Any, Dict, Optional


# =========================
# Helpers
# =========================
def _to_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _get_series(market_data: Dict[str, Any], key: str) -> Dict[str, Any]:
    """
    market_data[key] can be:
      - float (today only)
      - dict: {"today": ..., "prev": ..., "pct_change": ...}
      - dict: {"value": ..., "prev": ...} etc.
    Normalize to dict with today/prev/pct_change/delta.
    """
    raw = market_data.get(key)

    if isinstance(raw, dict):
        today = _to_float(raw.get("today", raw.get("value", raw.get("current"))))
        prev = _to_float(raw.get("prev", raw.get("previous")))
        pct = _to_float(raw.get("pct_change", raw.get("pct", raw.get("change_pct"))))

        delta = None
        if today is not None and prev is not None:
            delta = today - prev
            if pct is None and prev != 0:
                pct = (delta / prev) * 100.0

        return {
            "today": today,
            "prev": prev,
            "pct_change": pct,  # percent, not decimal
            "delta": delta,
        }

    today = _to_float(raw)
    return {"today": today, "prev": None, "pct_change": None, "delta": None}


def _sign_from(series: Dict[str, Any]) -> int:
    pct = series.get("pct_change")
    delta = series.get("delta")

    pct = _to_float(pct)
    delta = _to_float(delta)

    if pct is not None:
        if pct > 0:
            return 1
        if pct < 0:
            return -1
        return 0

    if delta is not None:
        if delta > 0:
            return 1
        if delta < 0:
            return -1
        return 0

    return 0


def _strength_label(key: str, pct_change: Optional[float]) -> str:
    if pct_change is None:
        return "N/A"
    p = abs(pct_change)

    if key in ("US10Y",):
        if p < 0.02:
            return "Noise"
        if p < 0.07:
            return "Mild"
        if p < 0.15:
            return "Clear"
        return "Strong"

    if key in ("DXY",):
        if p < 0.05:
            return "Noise"
        if p < 0.15:
            return "Mild"
        if p < 0.35:
            return "Clear"
        return "Strong"

    if key in ("WTI",):
        if p < 0.15:
            return "Noise"
        if p < 0.60:
            return "Mild"
        if p < 1.30:
            return "Clear"
        return "Strong"

    if key in ("VIX",):
        if p < 0.40:
            return "Noise"
        if p < 1.20:
            return "Mild"
        if p < 2.50:
            return "Clear"
        return "Strong"

    if key in ("USDKRW",):
        if p < 0.05:
            return "Noise"
        if p < 0.20:
            return "Mild"
        if p < 0.50:
            return "Clear"
        return "Strong"

    if p < 0.10:
        return "Noise"
    if p < 0.30:
        return "Mild"
    if p < 0.80:
        return "Clear"
    return "Strong"


def _fmt_num(x: Optional[float], nd: int = 3) -> str:
    if x is None:
        return "N/A"
    return f"{x:.{nd}f}"


# =========================
# v0.2-1 Market Regime Filter
# =========================
def market_regime_filter(market_data: Dict[str, Any]) -> str:
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")

    vix_today = vix["today"]
    vix_level = "N/A"
    if vix_today is not None:
        if vix_today < 14:
            vix_level = "Low (Risk-on bias)"
        elif vix_today < 20:
            vix_level = "Mid (Neutral/Mixed)"
        else:
            vix_level = "High (Risk-off bias)"

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    vix_dir = _sign_from(vix)

    combo = (us10y_dir, dxy_dir, vix_dir)

    regime = "TRANSITION / MIXED (전환·혼조)"
    reason = "금리/달러/변동성 축이 한 방향으로 정렬되지 않음"

    if combo == (0, 0, 0):
        regime = "WAITING / RANGE (대기·박스권)"
        reason = "핵심 축(금리/달러/변동성) 모두 보합 → 방향성 부재"
    elif combo == (-1, -1, -1):
        regime = "RISK-ON (완화 기대·리스크 선호)"
        reason = "금리↓ + 달러↓ + VIX↓ → 위험자산 선호/유동성 기대"
    elif combo == (1, 1, 1):
        regime = "RISK-OFF (긴축/불안·리스크 회피)"
        reason = "금리↑ + 달러↑ + VIX↑ → 안전자산/현금 선호 강화"
    elif vix_dir == 0 and (us10y_dir != 0 or dxy_dir != 0):
        regime = "EVENT-WATCHING (이벤트 관망)"
        reason = "변동성은 눌려있지만 금리/달러가 움직임 → 데이터/이벤트 대기"
    elif us10y_dir == 1 and dxy_dir == 1 and vix_dir != -1:
        regime = "TIGHTENING BIAS (긴축 편향)"
        reason = "금리↑ + 달러↑ → 글로벌 금융여건 타이트해질 가능성"
    elif vix_dir == -1 and (dxy_dir == -1 or us10y_dir == -1):
        regime = "RISK-ON (부분 정렬)"
        reason = "VIX↓ + (금리↓ 또는 달러↓) → 리스크 선호가 서서히 강화"
    elif vix_dir == 1 and (dxy_dir == 1 or us10y_dir == 1):
        regime = "RISK-OFF (부분 정렬)"
        reason = "VIX↑ + (금리↑ 또는 달러↑) → 불안/긴축 우려 확대"

    lines = []
    lines.append("### 🧩 1) Market Regime Filter")
    lines.append("- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*")
    lines.append("- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문")
    lines.append("")
    lines.append(f"- **VIX 레벨:** {_fmt_num(vix_today, 2)} → **{vix_level}**")
    lines.append(
        f"- **핵심 조합(전일 대비 방향):** "
        f"US10Y({ _dir_str(us10y_dir) }) / DXY({ _dir_str(dxy_dir) }) / VIX({ _dir_str(vix_dir) })"
    )
    lines.append(f"- **판정:** **{regime}**")
    lines.append(f"- **근거:** {reason}")
    return "\n".join(lines)


# =========================
#  Liquidity Filter
# =========================
def liquidity_filter(market_data: Dict[str, Any]) -> str:
    """
    Liquidity Filter (v0.3-1)
    Answers: Is liquidity expanding, tightening, or mixed?
    Uses US10Y, DXY, VIX with noise-aware logic.
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    vix_dir = _sign_from(vix)

    us10y_str = _strength_label("US10Y", us10y.get("pct_change"))
    dxy_str = _strength_label("DXY", dxy.get("pct_change"))
    vix_str = _strength_label("VIX", vix.get("pct_change"))

    def eff_dir(d, strength):
        return 0 if strength == "Noise" else d

    u = eff_dir(us10y_dir, us10y_str)
    d = eff_dir(dxy_dir, dxy_str)
    v = eff_dir(vix_dir, vix_str)

    state = "LIQUIDITY MIXED / FRAGILE (혼조·취약)"
    rationale = "유동성 신호가 한 방향으로 정렬되지 않음"

    if u == -1 and d == -1 and v in (-1, 0):
        state = "LIQUIDITY EXPANDING (유동성 확대)"
        rationale = "금리↓ + 달러↓ (±VIX↓) → 금융여건 완화"

    elif u == 1 and d == 1:
        state = "LIQUIDITY TIGHTENING (유동성 축소)"
        rationale = "금리↑ + 달러↑ → 글로벌 금융여건 타이트"

    lines = []
    lines.append("### 💧 2) Liquidity Filter")
    lines.append("- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?")
    lines.append(
        f"- **핵심 신호:** US10Y({_dir_str(us10y_dir)}, {us10y_str}) / "
        f"DXY({_dir_str(dxy_dir)}, {dxy_str}) / "
        f"VIX({_dir_str(vix_dir)}, {vix_str})"
    )
    lines.append(f"- **판정:** **{state}**")
    lines.append(f"- **근거:** {rationale}")

    return "\n".join(lines)


# =========================
# Policy Filter
# =========================
def policy_filter(market_data: Dict[str, Any]) -> str:
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    vix_dir = _sign_from(vix)

    regime = "POLICY MIXED (정책 신호 혼조)"
    reason = "금리와 달러 신호가 일관되지 않음"

    if us10y_dir == -1 and dxy_dir == -1:
        regime = "POLICY EASING (완화 기대)"
        reason = "금리↓ + 달러↓ → 통화환경 완화 기대 확대"
    elif us10y_dir == 1 and dxy_dir == 1:
        regime = "POLICY TIGHTENING (긴축 압력)"
        reason = "금리↑ + 달러↑ → 정책 긴축 압력 강화"
    elif us10y_dir == 0 and dxy_dir == 0:
        regime = "POLICY NEUTRAL (정책 공백)"
        reason = "정책 방향성 명확하지 않음"

    vix_note = ""
    if vix_dir == 1:
        vix_note = " / 정책 불확실성 확대(VIX↑)"
    elif vix_dir == -1:
        vix_note = " / 정책 신호 신뢰도 개선(VIX↓)"

    lines = []
    lines.append("### 🏛️ 3) Policy Filter")
    lines.append("- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?")
    lines.append("- **추가 이유:** 정책 흐름과 반대로 움직이는 자산은 지속 가능성이 낮기 때문")
    lines.append(
        f"- **핵심 신호:** US10Y({_dir_str(us10y_dir)}) / "
        f"DXY({_dir_str(dxy_dir)}) / VIX({_dir_str(vix_dir)})"
    )
    lines.append(f"- **판정:** **{regime}**")
    lines.append(f"- **근거:** {reason}{vix_note}")

    return "\n".join(lines)


# =========================
# Build
# =========================
def build_strategist_commentary(market_data: Dict[str, Any]) -> str:
    """
    Strategist Commentary – Seyeon’s Filters (v0.2)
    """
    sections = []
    sections.append("## 🧭 Strategist Commentary (Seyeon’s Filters)\n")
    sections.append(market_regime_filter(market_data))
    sections.append("")
    sections.append(liquidity_filter(market_data))
    sections.append("")
    sections.append(policy_filter(market_data))
    sections.append("")
    sections.append(legacy_directional_filters(market_data))
    return "\n".join(sections)
