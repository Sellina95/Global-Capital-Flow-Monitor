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
# Liquidity Filter
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

def fed_plumbing_filter(market_data: Dict[str, Any]) -> str:
    """
    Fed Plumbing Filter (TGA/RRP/NET_LIQ)
    목적: 유동성(달러)이 '시장 안'에 남아있는지, '시장 밖'으로 빠져나가고 있는지 확인
    """
    tga = _get_series(market_data, "TGA")
    rrp = _get_series(market_data, "RRP")
    net = _get_series(market_data, "NET_LIQ")

    # 데이터 없으면 섹션만 표시
    if tga["today"] is None or rrp["today"] is None or net["today"] is None:
        return "\n".join([
            "### 🧰 5) Fed Plumbing Filter (TGA/RRP/Net Liquidity)",
            "- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?",
            "- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음",
            "- **Status:** Not enough liquidity history (need TGA/RRP/NET_LIQ)",
        ])

    tga_dir = _sign_from(tga)
    rrp_dir = _sign_from(rrp)
    net_dir = _sign_from(net)

    # 해석 로직(간단하지만 방향성 핵심)
    state = "LIQUIDITY NEUTRAL"
    rationale = "유동성 신호가 혼조"
    if net_dir == 1 and tga_dir != 1 and rrp_dir != 1:
        state = "LIQUIDITY SUPPORTIVE (완만한 유동성 우호)"
        rationale = "Net Liquidity↑ (시장 내 달러 여력 개선) → 리스크자산 방어력 상승"
    elif net_dir == -1 and (tga_dir == 1 or rrp_dir == 1):
        state = "LIQUIDITY DRAINING (유동성 흡수)"
        rationale = "TGA↑ 또는 RRP↑와 함께 Net Liquidity↓ → 시장에서 달러가 빠져나갈 가능성"

    lines = []
    lines.append("### 🧰 5) Fed Plumbing Filter (TGA/RRP/Net Liquidity)")
    lines.append("- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?")
    lines.append("- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음")
    lines.append(
        f"- **방향(전일 대비):** TGA({_dir_str(tga_dir)}) / RRP({_dir_str(rrp_dir)}) / NET_LIQ({_dir_str(net_dir)})"
    )
    lines.append(f"- **판정:** **{state}**")
    lines.append(f"- **근거:** {rationale}")
    return "\n".join(lines)


def liquidity_plumbing_filter(market_data: Dict[str, Any]) -> str:
    tga = _get_series(market_data, "TGA")
    rrp = _get_series(market_data, "RRP")
    net = _get_series(market_data, "NET_LIQ")

    tga_dir = _sign_from(tga)
    rrp_dir = _sign_from(rrp)
    net_dir = _sign_from(net)

    # 해석: TGA↓ = 정부 지출로 시중 유동성 ↑ / RRP↓ = 잠긴 돈이 시장으로
    score = 0
    score += (1 if tga_dir == -1 else (-1 if tga_dir == 1 else 0))
    score += (1 if rrp_dir == -1 else (-1 if rrp_dir == 1 else 0))
    score += (1 if net_dir == 1 else (-1 if net_dir == -1 else 0))

    state = "PLUMBING MIXED (유동성 배관 혼조)"
    rationale = "TGA/RRP/Net Liquidity 신호가 엇갈림"

    if score >= 2:
        state = "PLUMBING SUPPORTIVE (유동성 우호)"
        rationale = "TGA↓/RRP↓/Net↑ 중 다수가 ‘시장으로 돈이 나오는’ 방향"
    elif score <= -2:
        state = "PLUMBING TIGHTENING (유동성 압박)"
        rationale = "TGA↑/RRP↑/Net↓ 중 다수가 ‘시장 유동성 흡수’ 방향"

    lines = []
    lines.append("### 🧰 2-2) Liquidity Plumbing (TGA/RRP)")
    lines.append("- **질문:** ‘연준-재무부 배관’에서 돈이 시장으로 나오고 있는가?")
    lines.append(
        f"- **핵심 신호:** TGA({_dir_str(tga_dir)}) / RRP({_dir_str(rrp_dir)}) / NET_LIQ({_dir_str(net_dir)})"
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
    lines.append("### 📌 4) Directional Signals (Legacy Filters)")
    lines.append("**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함")
    lines.append(line("US10Y", "미국 금리(US10Y)", "완화 기대 약화/금리 부담", "완화 기대 강화", "보합(관망)"))
    lines.append(line("DXY", "DXY", "달러 강세/신흥국 부담", "달러 약세/리스크 선호", "달러 보합(방향성 약함)"))
    lines.append(line("WTI", "WTI", "인플레 재자극 가능성", "물가 부담 완화", "유가 보합(물가 변수 제한)"))
    lines.append(line("VIX", "VIX", "심리 악화/리스크오프", "심리 개선/리스크온", "변동성 보합(심리 변화 제한)"))
    lines.append(line("USDKRW", "원/달러(USDKRW)", "원화 약세/수급 부담", "원화 강세/수급 개선", "환율 보합(수급 압력 제한)"))
    return "\n".join(lines)


def cross_asset_filter(market_data: Dict[str, Any]) -> str:
    """
    Cross-Asset Filter (v0.3-2)
    이 필터는 한 자산의 변화가 다른 자산군에 어떻게 전파되는지, 즉 연쇄효과를 분석합니다.
    """

    # Get data for key market indicators
    us10y = _get_series(market_data, "US10Y")  # 미국 10년물 금리
    dxy = _get_series(market_data, "DXY")  # 달러 인덱스
    wti = _get_series(market_data, "WTI")  # WTI 유가
    vix = _get_series(market_data, "VIX")  # 변동성 지수

    # Calculate direction signs for each asset
    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    wti_dir = _sign_from(wti)
    vix_dir = _sign_from(vix)

    # Generate cross-asset relationship commentary
    lines = []
    lines.append("### 🧩 5) Cross-Asset Filter (연쇄효과 분석)")
    lines.append("- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지, 즉 연쇄효과를 파악하기 위함")
    lines.append("")

    # 분석: 금리가 오르면, 달러는 어떻게 움직이는가?
    if us10y_dir == 1:
        lines.append("- **금리 상승(US10Y↑)** → **달러 강세(DXY↑)** 및 **유가 하락(WTI↓)** 경향")
    elif us10y_dir == -1:
        lines.append("- **금리 하락(US10Y↓)** → **달러 약세(DXY↓)** 및 **유가 상승(WTI↑)** 경향")
    else:
        lines.append("- **금리 변화 없음(US10Y→)** → 달러와 유가는 큰 변화 없음")

    # 분석: 변동성 지수 (VIX) 변화
    if vix_dir == 1:
        lines.append("- **변동성 상승(VIX↑)** → **리스크 회피, 달러 강세(DXY↑)** 및 **유가 하락(WTI↓)**")
    elif vix_dir == -1:
        lines.append("- **변동성 하락(VIX↓)** → **리스크 선호, 달러 약세(DXY↓)** 및 **유가 상승(WTI↑)**")
    else:
        lines.append("- **변동성 변화 없음(VIX→)** → 달러와 유가는 큰 변화 없음")

    # 분석: 유가(WTI)와 금리(US10Y) 간 관계
    if wti_dir == 1:
        lines.append("- **유가 상승(WTI↑)** → **리스크 선호, 금리 인상(US10Y↑)**")
    elif wti_dir == -1:
        lines.append("- **유가 하락(WTI↓)** → **리스크 회피, 금리 인하(US10Y↓)**")
    else:
        lines.append("- **유가 변화 없음(WTI→)** → 금리는 큰 변화 없음")

    return "\n".join(lines)
def risk_exposure_filter(market_data: Dict[str, Any]) -> str:
    """
    Risk Exposure Filter (v0.3-3)
    이 필터는 숫자는 괜찮아 보일 수 있지만 그 뒤에 숨은 리스크를 식별하는 역할을 합니다.
    """

    # Get data for key market indicators
    us10y = _get_series(market_data, "US10Y")  # 미국 10년물 금리
    dxy = _get_series(market_data, "DXY")  # 달러 인덱스
    wti = _get_series(market_data, "WTI")  # WTI 유가
    vix = _get_series(market_data, "VIX")  # 변동성 지수

    # Calculate direction signs for each asset
    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    wti_dir = _sign_from(wti)
    vix_dir = _sign_from(vix)

    # Generate risk exposure commentary
    lines = []
    lines.append("### 🧩 6) Risk Exposure Filter (숨은 리스크 분석)")
    lines.append("- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함")
    lines.append("")

    # 분석: VIX (변동성 지수) 높으면 리스크 상승
    if vix_dir == 1:
        lines.append("- **VIX 상승(VIX↑)** → **리스크 증가**: 변동성이 커지면 시장 불안정성 증가")
    else:
        lines.append("- **VIX 하락(VIX↓)** → **리스크 감소**: 불안정성이 줄어들고 상대적 안정성 증가")

    # 분석: 금리(US10Y) 상승하면 유동성 위기
    if us10y_dir == 1:
        lines.append("- **금리 상승(US10Y↑)** → **리스크 증가**: 금리 상승은 유동성 축소와 부담 증가")
    elif us10y_dir == -1:
        lines.append("- **금리 하락(US10Y↓)** → **리스크 증가**: 금리 하락은 경기 둔화 및 저금리 상황 지속")

    # 분석: 달러 강세(DXY↑)가 리스크를 확대하는 경우
    if dxy_dir == 1:
        lines.append("- **달러 강세(DXY↑)** → **리스크 증가**: 달러 강세는 글로벌 자산에 부담을 줄 수 있음")
    elif dxy_dir == -1:
        lines.append("- **달러 약세(DXY↓)** → **리스크 완화**: 달러 약세는 신흥국 자산 선호 증가 가능성")

    # 분석: 유가(WTI) 급등은 물가 압박
    if wti_dir == 1:
        lines.append("- **유가 상승(WTI↑)** → **리스크 증가**: 유가 급등은 인플레이션 압력과 경제적 부담 증가")
    elif wti_dir == -1:
        lines.append("- **유가 하락(WTI↓)** → **리스크 감소**: 유가 하락은 경기 둔화 우려 완화")

    return "\n".join(lines)

def incentive_filter(market_data: Dict[str, Any]) -> str:
    """
    Incentive Filter (v0.3-3)
    Answers: Who benefits from the market movement? 
    Analyzes key assets (US10Y, DXY, WTI) and identifies winners and losers.
    **추가 이유:** 이 결정/변화로 가장 크게 혜택을 보는 집단은 누구인지 파악하기 위함
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    wti = _get_series(market_data, "WTI")

    # Direction signs
    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    wti_dir = _sign_from(wti)

    # Winners and losers
    winners = []
    losers = []

    # If US10Y is up → Interest rates rise, banks benefit
    if us10y_dir == 1:
        winners.append("Banks/Financial Institutions (due to higher interest rates)")
    else:
        losers.append("Consumers (higher loan costs)")

    # If DXY is up → Dollar strengthens, exporters lose, importers gain
    if dxy_dir == 1:
        losers.append("Exporters (due to stronger USD)")
        winners.append("Importers (cheaper foreign goods)")
    else:
        winners.append("Exporters (weaker USD helps exports)")

    # If WTI is up → Oil prices rise, oil producers benefit
    if wti_dir == 1:
        winners.append("Oil Producers (higher oil prices)")
        losers.append("Consumers (due to higher energy costs)")
    else:
        winners.append("Consumers (lower energy prices)")
        losers.append("Oil Producers (lower oil prices)")

    # If all indicators are in a risk-off direction
    if not winners:
        incentive_status = "Risk-off: No clear beneficiaries"
    else:
        incentive_status = "Beneficiaries identified"

    # Generating the output
    lines = []
    lines.append("### 💸 7) Incentive Filter")
    lines.append("- **질문:** 누가 이득을 보고 있는가?")
    lines.append(f"- **핵심 신호:** US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / WTI({_dir_str(wti_dir)})")
    lines.append(f"- **판정:** **{incentive_status}**")
    lines.append("- **이득을 보는 주체:**")
    if winners:
        for winner in winners:
            lines.append(f"  - {winner}")
    else:
        lines.append("  - None")
    lines.append("- **손해를 보는 주체:**")
    if losers:
        for loser in losers:
            lines.append(f"  - {loser}")
    else:
        lines.append("  - None")

    return "\n".join(lines)

def cause_filter(market_data: Dict[str, Any]) -> str:
    """
    Cause Filter (v0.3-4)
    Answers: What caused the market movement?
    Analyzes key factors like US10Y, DXY, and WTI to identify the main causes of the market movement.
    **추가 이유:** 이 움직임이 나온 직접 이유를 파악하기 위함
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    wti = _get_series(market_data, "WTI")
    vix = _get_series(market_data, "VIX")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    wti_dir = _sign_from(wti)
    vix_dir = _sign_from(vix)

    # Determining the cause of the movement
    cause = ""
    if us10y_dir == 1:
        cause += "금리 상승(US10Y 상승) "
    elif us10y_dir == -1:
        cause += "금리 하락(US10Y 하락) "

    if dxy_dir == 1:
        cause += "달러 강세(DXY 상승) "
    elif dxy_dir == -1:
        cause += "달러 약세(DXY 하락) "

    if wti_dir == 1:
        cause += "유가 상승(WTI 상승) "
    elif wti_dir == -1:
        cause += "유가 하락(WTI 하락) "

    if vix_dir == 1:
        cause += "변동성 증가(VIX 상승) "
    elif vix_dir == -1:
        cause += "변동성 감소(VIX 하락) "

    # Final statement for the cause
    if cause == "":
        cause = "원인 불명"
    
    lines = []
    lines.append("### 🔍 8) Cause Filter")
    lines.append("- **질문:** 무엇이 이 시장 움직임을 일으켰는가?")
    lines.append(f"- **핵심 신호:** US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / WTI({_dir_str(wti_dir)}) / VIX({_dir_str(vix_dir)})")
    lines.append(f"- **판정:** **{cause}**")
    lines.append("- **이유:** 직접적인 원인 파악")

    return "\n".join(lines)

def direction_filter(market_data: Dict[str, Any]) -> str:
    """
    Direction Filter (v0.3-5)
    Answers: How much has the market moved? 
    Analyzes key assets and their movement to determine if it's noise or meaningful movement.
    **추가 이유:** 숫자가 어느 방향으로, 얼마나 움직였는가 즉 변화폭이 작은 ‘노이즈’야, 인지 '의미 있는 움직임' 인지를 파악하기위함
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    wti = _get_series(market_data, "WTI")
    vix = _get_series(market_data, "VIX")

    # Calculate the direction and strength of each asset
    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    wti_dir = _sign_from(wti)
    vix_dir = _sign_from(vix)

    # Calculate strength labels based on pct_change
    us10y_strength = _strength_label("US10Y", us10y.get("pct_change"))
    dxy_strength = _strength_label("DXY", dxy.get("pct_change"))
    wti_strength = _strength_label("WTI", wti.get("pct_change"))
    vix_strength = _strength_label("VIX", vix.get("pct_change"))

    # Combine the information into a narrative
    direction_info = f"US10Y({us10y_strength}, {_dir_str(us10y_dir)}) / DXY({dxy_strength}, {_dir_str(dxy_dir)}) / " \
                     f"WTI({wti_strength}, {_dir_str(wti_dir)}) / VIX({vix_strength}, {_dir_str(vix_dir)})"

    # Default state
    state = "NO MOVEMENT"
    rationale = "변화가 미미한 '노이즈' 또는 '의미 있는 변화'인지 분석 중"

    # Identify meaningful movements
    if us10y_strength in ["Clear", "Strong"] or dxy_strength in ["Clear", "Strong"]:
        state = "SIGNIFICANT MOVEMENT (의미 있는 움직임)"
        rationale = "금리나 달러의 변동이 크고 뚜렷함"
    elif wti_strength in ["Clear", "Strong"] or vix_strength in ["Clear", "Strong"]:
        state = "SIGNIFICANT MOVEMENT (의미 있는 움직임)"
        rationale = "유가나 변동성의 변화가 큰 경우"
    
    lines = []
    lines.append("### 🔄 9) Direction Filter")
    lines.append("- **질문:** 시장이 어느 방향으로, 얼마나 움직였는가?")
    lines.append(f"- **핵심 신호:** {direction_info}")
    lines.append(f"- **판정:** **{state}**")
    lines.append(f"- **근거:** {rationale}")



    return "\n".join(lines)

def timing_filter(market_data: Dict[str, Any]) -> str:
    """
    Timing Filter (v0.3-6)
    Answers: When is the key signal most important? 
    Analyzes short-term, medium-term, and long-term trends.
    **추가 이유:** 시장 변화가 단기, 중기, 장기 관점에서 어떤 영향을 미치는지 파악하기 위해
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")

    # Extracting short-term, medium-term, and long-term trends
    short_term_us10y = us10y["pct_change"]
    medium_term_us10y = us10y["prev"]
    long_term_us10y = us10y["today"]

    short_term_dxy = dxy["pct_change"]
    medium_term_dxy = dxy["prev"]
    long_term_dxy = dxy["today"]

    short_term_vix = vix["pct_change"]
    medium_term_vix = vix["prev"]
    long_term_vix = vix["today"]

    # Default state
    state = "NO SIGNIFICANT MOVEMENT"
    rationale = "단기, 중기, 장기적으로 시장 변화가 균일하게 발생하고 있음"

    # Define thresholds for different timeframes
    if short_term_us10y > 0.02 and medium_term_us10y > 0.05 and long_term_us10y > 0.1:
        state = "LONG-TERM RISK TREND (장기적 위험 신호)"
        rationale = "금리가 계속해서 상승하고 있으며, 장기적인 리스크가 확대되고 있음"
    
    elif short_term_dxy < -0.03 and medium_term_dxy < -0.07 and long_term_dxy < -0.1:
        state = "DOLLAR WEAKNESS TREND (달러 약세)"
        rationale = "달러가 약세를 지속하고 있어, 리스크 선호가 높아지고 있음"

    elif short_term_vix > 1.2 and medium_term_vix > 1.5 and long_term_vix > 2.0:
        state = "HIGH VOLATILITY (고변동성)"
        rationale = "변동성이 지속적으로 확대되고 있으며, 시장의 불확실성이 커지고 있음"

    lines = []
    lines.append("### ⏳ 10) Timing Filter")
    lines.append("- **질문:** 시장 변화가 단기, 중기, 장기 관점에서 어떤 영향을 미치는지?")
    lines.append(f"- **핵심 신호:** US10Y({short_term_us10y:.2f}% short-term, {medium_term_us10y:.2f}% medium-term, {long_term_us10y:.2f}% long-term) / "
                 f"DXY({short_term_dxy:.2f}% short-term, {medium_term_dxy:.2f}% medium-term, {long_term_dxy:.2f}% long-term) / "
                 f"VIX({short_term_vix:.2f}% short-term, {medium_term_vix:.2f}% medium-term, {long_term_vix:.2f}% long-term)")
    lines.append(f"- **판정:** **{state}**")
    lines.append(f"- **근거:** {rationale}")

    return "\n".join(lines)

def structural_filter(market_data: Dict[str, Any]) -> str:
    """
    Structural Filter (v0.3-8)
    Answers: How does this change connect to the global economic structure or power dynamics?
    **추가 이유:** 시장 변화가 글로벌 경제 구조나 패권 구조와 어떻게 연결되는지 파악하기 위해
    """
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")
    wti = _get_series(market_data, "WTI")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    vix_dir = _sign_from(vix)
    wti_dir = _sign_from(wti)

    # Default state
    state = "NEUTRAL"
    rationale = "세계 경제 구조와의 상관관계가 명확하지 않음"

    # Structural impact example
    if us10y_dir == 1 and dxy_dir == 1:
        state = "TIGHTENING GLOBAL STRUCTURE (글로벌 긴축)"
        rationale = "금리 상승과 달러 강세는 글로벌 금융 긴축을 예고하며, 신흥국 및 자산 시장에 큰 영향을 미침"

    elif wti_dir == -1 and vix_dir == 1:
        state = "WEAK GLOBAL DEMAND / RISK-OFF (세계 수요 약화 / 리스크 회피)"
        rationale = "유가 하락과 변동성 확대는 세계 경제 성장 둔화와 리스크 회피 성향을 강화함"

    lines = []
    lines.append("### 🏗️ 11) Structural Filter")
    lines.append("- **질문:** 이 변화가 글로벌 경제 구조나 패권 구조와 어떻게 연결되는지?")
    lines.append(
        f"- **핵심 신호:** US10Y({_dir_str(us10y_dir)}) / "
        f"DXY({_dir_str(dxy_dir)}) / VIX({_dir_str(vix_dir)}) / "
        f"WTI({_dir_str(wti_dir)})"
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
    sections.append("")
    sections.append(liquidity_filter(market_data))
    sections.append("")
    sections.append(liquidity_plumbing_filter(market_data))
    sections.append("")
    sections.append(policy_filter(market_data))

    return "\n".join(sections)
