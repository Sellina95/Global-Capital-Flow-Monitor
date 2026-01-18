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
    Normalize input to dict with today/prev/pct_change/delta.
    market_data[key] can be:
      - float (today only)
      - dict: {"today": ..., "prev": ..., "pct_change": ...}
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

        return {"today": today, "prev": prev, "pct_change": pct, "delta": delta}

    today = _to_float(raw)
    return {"today": today, "prev": None, "pct_change": None, "delta": None}


def _sign_from(series: Dict[str, Any]) -> int:
    pct = _to_float(series.get("pct_change"))
    delta = _to_float(series.get("delta"))

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


def _dir_str(d: int) -> str:
    if d == 1:
        return "↑"
    if d == -1:
        return "↓"
    return "→"


def _fmt_num(x: Optional[float], nd: int = 3) -> str:
    if x is None:
        return "N/A"
    return f"{x:.{nd}f}"


def _strength_label(key: str, pct_change: Optional[float]) -> str:
    """
    Noise vs meaningful move heuristics (pct change 기준)
    """
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

    # Liquidity series는 “레벨/방향”이 더 중요해서 강도는 보수적으로
    if key in ("TGA", "RRP", "NET_LIQ", "WALCL"):
        if p < 0.10:
            return "Noise"
        if p < 0.30:
            return "Mild"
        if p < 0.80:
            return "Clear"
        return "Strong"

    if p < 0.10:
        return "Noise"
    if p < 0.30:
        return "Mild"
    if p < 0.80:
        return "Clear"
    return "Strong"


# =========================
# Regime: label + markdown
# =========================
def get_regime_label(market_data: Dict[str, Any]) -> str:
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    vix_dir = _sign_from(vix)

    combo = (us10y_dir, dxy_dir, vix_dir)

    regime = "TRANSITION / MIXED (전환·혼조)"

    if combo == (0, 0, 0):
        regime = "WAITING / RANGE (대기·박스권)"
    elif combo == (-1, -1, -1):
        regime = "RISK-ON (완화 기대·리스크 선호)"
    elif combo == (1, 1, 1):
        regime = "RISK-OFF (긴축/불안·리스크 회피)"
    elif vix_dir == 0 and (us10y_dir != 0 or dxy_dir != 0):
        regime = "EVENT-WATCHING (이벤트 관망)"
    elif us10y_dir == 1 and dxy_dir == 1 and vix_dir != -1:
        regime = "TIGHTENING BIAS (긴축 편향)"
    elif vix_dir == -1 and (dxy_dir == -1 or us10y_dir == -1):
        regime = "RISK-ON (부분 정렬)"
    elif vix_dir == 1 and (dxy_dir == 1 or us10y_dir == 1):
        regime = "RISK-OFF (부분 정렬)"

    return regime


def market_regime_filter(market_data: Dict[str, Any]) -> str:
    vix = _get_series(market_data, "VIX")
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")

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

    regime = get_regime_label(market_data)

    reason = "금리/달러/변동성 축이 한 방향으로 정렬되지 않음"
    if regime.startswith("WAITING"):
        reason = "핵심 축(금리/달러/변동성) 모두 보합 → 방향성 부재"
    elif regime.startswith("RISK-ON") and "부분" not in regime:
        reason = "금리↓ + 달러↓ + VIX↓ → 위험자산 선호/유동성 기대"
    elif regime.startswith("RISK-OFF") and "부분" not in regime:
        reason = "금리↑ + 달러↑ + VIX↑ → 안전자산/현금 선호 강화"
    elif regime.startswith("EVENT-WATCHING"):
        reason = "변동성은 눌려있지만 금리/달러가 움직임 → 데이터/이벤트 대기"
    elif regime.startswith("TIGHTENING"):
        reason = "금리↑ + 달러↑ → 글로벌 금융여건 타이트해질 가능성"
    elif "부분" in regime and regime.startswith("RISK-ON"):
        reason = "VIX↓ + (금리↓ 또는 달러↓) → 리스크 선호가 서서히 강화"
    elif "부분" in regime and regime.startswith("RISK-OFF"):
        reason = "VIX↑ + (금리↑ 또는 달러↑) → 불안/긴축 우려 확대"

    lines = []
    lines.append("### 🧩 1) Market Regime Filter")
    lines.append("- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*")
    lines.append("- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문")
    lines.append("")
    lines.append(f"- **VIX 레벨:** {_fmt_num(vix_today, 2)} → **{vix_level}**")
    lines.append(
        f"- **핵심 조합(전일 대비 방향):** "
        f"US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / VIX({_dir_str(vix_dir)})"
    )
    lines.append(f"- **판정:** **{regime}**")
    lines.append(f"- **근거:** {reason}")
    return "\n".join(lines)


# =========================
# Liquidity Filter (macro)
# =========================
def liquidity_filter(market_data: Dict[str, Any]) -> str:
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
    lines.append("### 💧 2) Liquidity Filter (Macro)")
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
# Fed Plumbing Filter (NEW)
# =========================
def fed_plumbing_filter(market_data: Dict[str, Any]) -> str:
    """
    Fed Plumbing Filter (TGA/RRP/NET_LIQ)
    목적: 달러가 '시장 안'에 남아있는지, '시장 밖'으로 빠져나가는지(흡수되는지) 확인.
    """
    tga = _get_series(market_data, "TGA")
    rrp = _get_series(market_data, "RRP")
    net = _get_series(market_data, "NET_LIQ")

    # data not ready (or not injected into market_data)
    if tga["today"] is None or rrp["today"] is None or net["today"] is None:
        return "\n".join([
            "### 🧰 3) Fed Plumbing Filter (TGA/RRP/Net Liquidity)",
            "- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?",
            "- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음",
            "- **Status:** Not enough liquidity history (need TGA/RRP/NET_LIQ in market_data)",
        ])

    tga_dir = _sign_from(tga)
    rrp_dir = _sign_from(rrp)
    net_dir = _sign_from(net)

    state = "LIQUIDITY NEUTRAL"
    rationale = "유동성 신호가 혼조"

    # 아주 단순하지만 실전에서 유용한 방향성 프레임
    if net_dir == 1 and tga_dir != 1 and rrp_dir != 1:
        state = "LIQUIDITY SUPPORTIVE (완만한 유동성 우호)"
        rationale = "Net Liquidity↑ → 시장 내 달러 여력 개선(리스크자산 방어력↑)"
    elif net_dir == -1 and (tga_dir == 1 or rrp_dir == 1):
        state = "LIQUIDITY DRAINING (유동성 흡수)"
        rationale = "TGA↑ 또는 RRP↑ 동반 Net Liquidity↓ → 시장에서 달러가 빠져나갈 가능성"

    lines = []
    lines.append("### 🧰 3) Fed Plumbing Filter (TGA/RRP/Net Liquidity)")
    lines.append("- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?")
    lines.append("- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음")
    lines.append(
        f"- **방향(전일 대비):** TGA({_dir_str(tga_dir)}) / RRP({_dir_str(rrp_dir)}) / NET_LIQ({_dir_str(net_dir)})"
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
    lines.append("### 🏛️ 4) Policy Filter")
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
# Legacy Directional Filters
# =========================
def legacy_directional_filters(market_data: Dict[str, Any]) -> str:
    def line(key: str, label: str, up: str, down: str, flat: str) -> str:
        s = _get_series(market_data, key)
        direction = _sign_from(s)
        pct = _to_float(s.get("pct_change"))
        strength = _strength_label(key, pct)

        if direction == 1:
            msg = up
        elif direction == -1:
            msg = down
        else:
            msg = flat

        pct_txt = f"{pct:+.2f}%" if pct is not None else "N/A"
        return f"- {label} **({strength}, {pct_txt})** → {msg}"

    lines = []
    lines.append("### 📌 5) Directional Signals (Legacy Filters)")
    lines.append("**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함")
    lines.append(line("US10Y", "미국 금리(US10Y)", "완화 기대 약화/금리 부담", "완화 기대 강화", "보합(관망)"))
    lines.append(line("DXY", "DXY", "달러 강세/신흥국 부담", "달러 약세/리스크 선호", "달러 보합(방향성 약함)"))
    lines.append(line("WTI", "WTI", "인플레 재자극 가능성", "물가 부담 완화", "유가 보합(물가 변수 제한)"))
    lines.append(line("VIX", "VIX", "심리 악화/리스크오프", "심리 개선/리스크온", "변동성 보합(심리 변화 제한)"))
    lines.append(line("USDKRW", "원/달러(USDKRW)", "원화 약세/수급 부담", "원화 강세/수급 개선", "환율 보합(수급 압력 제한)"))
    return "\n".join(lines)


def cross_asset_filter(market_data: Dict[str, Any]) -> str:
    """
    Cross-Asset Filter
    이 필터는 한 자산의 변화가 다른 자산군에 어떻게 전파되는지, 즉 연쇄효과를 분석합니다.
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    wti = _get_series(market_data, "WTI")
    vix = _get_series(market_data, "VIX")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    wti_dir = _sign_from(wti)
    vix_dir = _sign_from(vix)

    lines = []
    lines.append("### 🧩 6) Cross-Asset Filter (연쇄효과 분석)")
    lines.append("- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지, 즉 연쇄효과를 파악하기 위함")
    lines.append("")

    if us10y_dir == 1:
        lines.append("- **금리 상승(US10Y↑)** → **달러 강세(DXY↑)** 및 **유가 하락(WTI↓)** 경향")
    elif us10y_dir == -1:
        lines.append("- **금리 하락(US10Y↓)** → **달러 약세(DXY↓)** 및 **유가 상승(WTI↑)** 경향")
    else:
        lines.append("- **금리 변화 없음(US10Y→)** → 달러와 유가는 큰 변화 없음")

    if vix_dir == 1:
        lines.append("- **변동성 상승(VIX↑)** → **리스크 회피, 달러 강세(DXY↑)** 및 **유가 하락(WTI↓)**")
    elif vix_dir == -1:
        lines.append("- **변동성 하락(VIX↓)** → **리스크 선호, 달러 약세(DXY↓)** 및 **유가 상승(WTI↑)**")
    else:
        lines.append("- **변동성 변화 없음(VIX→)** → 달러와 유가는 큰 변화 없음")

    if wti_dir == 1:
        lines.append("- **유가 상승(WTI↑)** → **물가 재자극/금리 부담(US10Y↑) 가능성**")
    elif wti_dir == -1:
        lines.append("- **유가 하락(WTI↓)** → **물가 부담 완화/금리 부담↓(US10Y↓) 가능성**")
    else:
        lines.append("- **유가 변화 없음(WTI→)** → 금리는 큰 변화 없음")

    return "\n".join(lines)


def risk_exposure_filter(market_data: Dict[str, Any]) -> str:
    """
    Risk Exposure Filter
    숫자는 괜찮아 보일 수 있지만 그 뒤에 숨은 리스크를 식별합니다.
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    wti = _get_series(market_data, "WTI")
    vix = _get_series(market_data, "VIX")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    wti_dir = _sign_from(wti)
    vix_dir = _sign_from(vix)

    lines = []
    lines.append("### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)")
    lines.append("- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함")
    lines.append("")

    if vix_dir == 1:
        lines.append("- **VIX 상승(VIX↑)** → **리스크 증가**: 시장 불안/헤지 수요 확대")
    elif vix_dir == -1:
        lines.append("- **VIX 하락(VIX↓)** → **리스크 완화**: 시장 심리 개선")
    else:
        lines.append("- **VIX 보합(VIX→)** → 심리 변화 제한")

    if us10y_dir == 1:
        lines.append("- **금리 상승(US10Y↑)** → **리스크 증가**: 할인율↑/유동성 부담↑")
    elif us10y_dir == -1:
        lines.append("- **금리 하락(US10Y↓)** → **완화 기대** 또는 **경기 둔화 우려**(맥락 점검 필요)")
    else:
        lines.append("- **금리 보합(US10Y→)** → 금리 변수 중립")

    if dxy_dir == 1:
        lines.append("- **달러 강세(DXY↑)** → **리스크 증가**: 글로벌 금융여건 타이트, 신흥국 부담")
    elif dxy_dir == -1:
        lines.append("- **달러 약세(DXY↓)** → **리스크 완화**: 위험자산 선호 확대 가능")
    else:
        lines.append("- **달러 보합(DXY→)** → 달러 변수 중립")

    if wti_dir == 1:
        lines.append("- **유가 상승(WTI↑)** → **리스크 증가**: 인플레 재자극/마진 압박")
    elif wti_dir == -1:
        lines.append("- **유가 하락(WTI↓)** → **리스크 완화**(물가) 또는 **수요 둔화 신호**(경기) 점검")
    else:
        lines.append("- **유가 보합(WTI→)** → 물가 변수 제한")

    return "\n".join(lines)


def incentive_filter(market_data: Dict[str, Any]) -> str:
    """
    Incentive Filter
    누가 이득을 보는가? (승자/패자)
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    wti = _get_series(market_data, "WTI")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    wti_dir = _sign_from(wti)

    winners = []
    losers = []

    if us10y_dir == 1:
        winners.append("Banks/Financials (higher yields)")
    elif us10y_dir == -1:
        winners.append("Duration assets (growth/tech) if risk sentiment holds")

    if dxy_dir == 1:
        winners.append("USD cash / USD assets (strong dollar)")
        losers.append("EM assets / USD funding-sensitive borrowers")
    elif dxy_dir == -1:
        winners.append("EM risk / non-USD assets (weaker dollar)")

    if wti_dir == 1:
        winners.append("Oil producers / energy sector")
        losers.append("Energy consumers (cost pressure)")
    elif wti_dir == -1:
        winners.append("Energy consumers (cost relief)")
        losers.append("Oil producers (price pressure)")

    lines = []
    lines.append("### 💸 8) Incentive Filter")
    lines.append("- **질문:** 누가 이득을 보고 있는가?")
    lines.append(
        f"- **핵심 신호:** US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / WTI({_dir_str(wti_dir)})"
    )
    lines.append("- **이득:**")
    if winners:
        for w in winners:
            lines.append(f"  - {w}")
    else:
        lines.append("  - None")
    lines.append("- **손해:**")
    if losers:
        for l in losers:
            lines.append(f"  - {l}")
    else:
        lines.append("  - None")

    return "\n".join(lines)


def cause_filter(market_data: Dict[str, Any]) -> str:
    """
    Cause Filter
    무엇이 움직임을 만들었나? (신호 요약)
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    wti = _get_series(market_data, "WTI")
    vix = _get_series(market_data, "VIX")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    wti_dir = _sign_from(wti)
    vix_dir = _sign_from(vix)

    parts = []
    if us10y_dir == 1:
        parts.append("금리↑")
    elif us10y_dir == -1:
        parts.append("금리↓")

    if dxy_dir == 1:
        parts.append("달러↑")
    elif dxy_dir == -1:
        parts.append("달러↓")

    if wti_dir == 1:
        parts.append("유가↑")
    elif wti_dir == -1:
        parts.append("유가↓")

    if vix_dir == 1:
        parts.append("VIX↑")
    elif vix_dir == -1:
        parts.append("VIX↓")

    cause = " / ".join(parts) if parts else "원인 불명(보합/혼조)"

    lines = []
    lines.append("### 🔍 9) Cause Filter")
    lines.append("- **질문:** 무엇이 이 시장 움직임을 일으켰는가?")
    lines.append(
        f"- **핵심 신호:** US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / WTI({_dir_str(wti_dir)}) / VIX({_dir_str(vix_dir)})"
    )
    lines.append(f"- **판정:** **{cause}**")
    return "\n".join(lines)


def direction_filter(market_data: Dict[str, Any]) -> str:
    """
    Direction Filter
    노이즈인가, 의미있는 움직임인가?
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    wti = _get_series(market_data, "WTI")
    vix = _get_series(market_data, "VIX")

    us10y_strength = _strength_label("US10Y", us10y.get("pct_change"))
    dxy_strength = _strength_label("DXY", dxy.get("pct_change"))
    wti_strength = _strength_label("WTI", wti.get("pct_change"))
    vix_strength = _strength_label("VIX", vix.get("pct_change"))

    state = "NOISE / SMALL MOVE (노이즈 가능)"
    rationale = "핵심 지표 변동 폭이 작음"

    if us10y_strength in ("Clear", "Strong") or dxy_strength in ("Clear", "Strong"):
        state = "SIGNIFICANT MOVE (의미 있는 움직임)"
        rationale = "금리/달러 변동이 뚜렷함"
    elif wti_strength in ("Clear", "Strong") or vix_strength in ("Clear", "Strong"):
        state = "SIGNIFICANT MOVE (의미 있는 움직임)"
        rationale = "유가/VIX 변동이 뚜렷함"

    lines = []
    lines.append("### 🔄 10) Direction Filter")
    lines.append("- **질문:** 시장이 어느 방향으로, 얼마나 움직였는가?")
    lines.append(
        f"- **강도:** US10Y({us10y_strength}) / DXY({dxy_strength}) / WTI({wti_strength}) / VIX({vix_strength})"
    )
    lines.append(f"- **판정:** **{state}**")
    lines.append(f"- **근거:** {rationale}")
    return "\n".join(lines)


def timing_filter(market_data: Dict[str, Any]) -> str:
    """
    Timing Filter
    단기/중기/장기 중 어떤 프레임이 중요한가?
    (현재는 단순 표시용. 추후 rolling/MA로 확장 추천)
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")

    lines = []
    lines.append("### ⏳ 11) Timing Filter")
    lines.append("- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 영향이 큰가?")
    lines.append(
        f"- **단기 변화(pct):** US10Y({_fmt_num(us10y.get('pct_change'), 2)}%) / "
        f"DXY({_fmt_num(dxy.get('pct_change'), 2)}%) / "
        f"VIX({_fmt_num(vix.get('pct_change'), 2)}%)"
    )
    lines.append("- **메모:** 장기 프레임 분석은 추후 이동평균/추세선으로 확장 권장")
    return "\n".join(lines)


def structural_filter(market_data: Dict[str, Any]) -> str:
    """
    Structural Filter
    이 변화가 글로벌 구조(성장/패권/수요)와 어떻게 연결되는가?
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")
    wti = _get_series(market_data, "WTI")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    vix_dir = _sign_from(vix)
    wti_dir = _sign_from(wti)

    state = "NEUTRAL"
    rationale = "세계 경제 구조와의 연결이 뚜렷하지 않음"

    if us10y_dir == 1 and dxy_dir == 1:
        state = "GLOBAL TIGHTENING (글로벌 긴축 구조)"
        rationale = "금리↑ + 달러↑ → 신흥국/레버리지/리스크자산 부담 확대"
    elif wti_dir == -1 and vix_dir == 1:
        state = "WEAK DEMAND / RISK-OFF"
        rationale = "유가↓ + 변동성↑ → 수요 둔화 우려와 회피 심리 확대"

    lines = []
    lines.append("### 🏗️ 12) Structural Filter")
    lines.append("- **질문:** 이 변화가 글로벌 경제 구조/패권 구조와 어떻게 연결되는가?")
    lines.append(
        f"- **핵심 신호:** US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / VIX({_dir_str(vix_dir)}) / WTI({_dir_str(wti_dir)})"
    )
    lines.append(f"- **판정:** **{state}**")
    lines.append(f"- **근거:** {rationale}")
    return "\n".join(lines)


# =========================
# Build
# =========================
def build_strategist_commentary(market_data: Dict[str, Any]) -> str:
    sections = []
    sections.append("## 🧭 Strategist Commentary (Seyeon’s Filters)\n")
    sections.append(market_regime_filter(market_data))
    sections.append("")
    sections.append(liquidity_filter(market_data))
    sections.append("")
    sections.append(fed_plumbing_filter(market_data))  # ✅ NEW
    sections.append("")
    sections.append(policy_filter(market_data))
    sections.append("")
    sections.append(legacy_directional_filters(market_data))
    sections.append("")
    sections.append(cross_asset_filter(market_data))
    sections.append("")
    sections.append(risk_exposure_filter(market_data))
    sections.append("")
    sections.append(incentive_filter(market_data))
    sections.append("")
    sections.append(cause_filter(market_data))
    sections.append("")
    sections.append(direction_filter(market_data))
    sections.append("")
    sections.append(timing_filter(market_data))
    sections.append("")
    sections.append(structural_filter(market_data))
    return "\n".join(sections)
