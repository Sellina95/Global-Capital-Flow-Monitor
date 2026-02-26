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
    # ✅ 방탄: market_data가 None으로 들어와도 죽지 않게
    if market_data is None:
        market_data = {}

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

    # ✅ ETF류(HYG/LQD 등)는 좀 더 넓게
    if key in ("HYG", "LQD"):
        if p < 0.10:
            return "Noise"
        if p < 0.40:
            return "Mild"
        if p < 0.90:
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
# 1) Regime
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

    # ✅ Phase/Regime를 다른 필터(Narrative Engine 등)에서 쓰도록 저장
    market_data["MARKET_REGIME"] = regime

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
# 2) Liquidity (rates/dollar/vix)
# =========================
def liquidity_filter(market_data: Dict[str, Any]) -> str:
    """
    Enhanced Liquidity Filter (Expectation + Reality + Incentive)
    - US10Y/DXY/VIX: 'market expectations' (price-based)
    - FCI: 'real-world pressure' (lower = easier)
    - REAL_RATE(TIPS): 'risk-taking incentive' (lower = easier)

    Output: no raw numbers, only direction + level labels.
    """

    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")

    fci = _get_series(market_data, "FCI")
    rr  = _get_series(market_data, "REAL_RATE")

    us10y_dir = _sign_from(us10y)
    dxy_dir   = _sign_from(dxy)
    vix_dir   = _sign_from(vix)

    # Direction: for FCI/REAL_RATE, lower is better (easier / more incentive)
    fci_raw_dir = _sign_from(fci)
    rr_raw_dir  = _sign_from(rr)
    fci_eff_dir = -fci_raw_dir if fci.get("today") is not None else 0
    rr_eff_dir  = -rr_raw_dir  if rr.get("today") is not None else 0

    # -------------------------
    # Level labels (no numbers)
    # -------------------------
    def fci_level_label(x: Optional[float]) -> str:
        """
        NFCI is often centered around 0:
        - below 0: easier-than-average conditions
        - above 0: tighter-than-average
        """
        if x is None:
            return "N/A"
        if x <= -0.25:
            return "EASY (완화)"
        if x < 0.25:
            return "NEUTRAL (중립)"
        return "TIGHT (압박)"

    def rr_level_label(x: Optional[float]) -> str:
        """
        10Y TIPS real yield rough bands (can be tuned):
        - < 1.0 : supportive for risk-taking
        - 1.0~2.0 : neutral-ish
        - > 2.0 : restrictive
        """
        if x is None:
            return "N/A"
        if x < 1.0:
            return "SUPPORTIVE (유인↑)"
        if x < 2.0:
            return "NEUTRAL (중립)"
        return "RESTRICTIVE (유인↓)"

    fci_level = fci_level_label(_to_float(fci.get("today")))
    rr_level  = rr_level_label(_to_float(rr.get("today")))

    # -------------------------
    # Expectation (price) signal
    # -------------------------
    exp_easing = (us10y_dir == -1 and dxy_dir == -1 and vix_dir in (-1, 0))
    exp_tight  = (us10y_dir == 1 and dxy_dir == 1)

    # -------------------------
    # Reality + Incentive states from levels
    # -------------------------
    # Map level labels to coarse score: +1 supportive / 0 neutral / -1 tight
    def level_score(label: str) -> int:
        if label in ("EASY (완화)", "SUPPORTIVE (유인↑)"):
            return 1
        if label in ("TIGHT (압박)", "RESTRICTIVE (유인↓)"):
            return -1
        return 0

    reality_score = level_score(fci_level)   # FCI
    incentive_score = level_score(rr_level)  # Real Rates

    # -------------------------
    # Final decision logic
    # -------------------------
    state = "LIQUIDITY MIXED / FRAGILE (혼조·취약)"
    rationale = "기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전"

    if exp_easing and reality_score == 1 and incentive_score == 1:
        state = "LIQUIDITY EXPANDING (Confirmed) (유동성 확대·확인)"
        rationale = "기대 완화 + FCI 완화 + 실질금리 유인↑ → ‘현실/유인’까지 동반"
    elif exp_easing and (reality_score >= 0 and incentive_score >= 0):
        state = "LIQUIDITY EXPANDING (Expectation-led) (기대 주도 확대)"
        rationale = "기대는 완화 쪽, FCI/실질금리는 중립 이상 → 랠리 지속 가능성은 ‘열려있음’"
    elif exp_easing and (reality_score == -1 or incentive_score == -1):
        state = "LIQUIDITY MIXED / FRAGILE (혼조·취약)"
        rationale = "기대는 완화지만 FCI 압박 또는 실질금리 유인↓ → 리스크자산 지속성 약화 리스크"
    elif exp_tight and (reality_score == -1 or incentive_score == -1):
        state = "LIQUIDITY TIGHTENING (유동성 축소)"
        rationale = "금리↑+달러↑ + (FCI 압박 또는 실질금리 유인↓) → 리스크자산에 불리"
    elif exp_tight and reality_score == 1 and incentive_score == 1:
        state = "LIQUIDITY MIXED / FRAGILE (혼조·취약)"
        rationale = "가격은 타이트하지만 FCI/유인은 완화 → ‘가격 신호의 과잉’ 가능"

    # as-of meta
    fci_asof = market_data.get("_FCI_ASOF")
    rr_asof  = market_data.get("_REAL_ASOF")

    lines = []
    lines.append("### 💧 2) Liquidity Filter (Enhanced)")
    lines.append("- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?")
    lines.append(
        "- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, "
        "FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다."
    )
    lines.append("")
    lines.append(
        f"- **기대(가격) 신호:** US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / VIX({_dir_str(vix_dir)})"
    )

    if fci.get("today") is None:
        lines.append("- **현실(FCI):** N/A (not available)")
    else:
        lines.append(
            f"- **현실(FCI):** level={fci_level} / dir({_dir_str(fci_eff_dir)})"
            + (f" | as of: {fci_asof} (FRED last available)" if fci_asof else "")
        )

    if rr.get("today") is None:
        lines.append("- **유인(Real Rates):** N/A (not available)")
    else:
        lines.append(
            f"- **유인(Real Rates):** level={rr_level} / dir({_dir_str(rr_eff_dir)})"
            + (f" | as of: {rr_asof} (FRED last available)" if rr_asof else "")
        )

    lines.append(f"- **판정:** **{state}**")
    lines.append(f"- **근거:** {rationale}")
    lines.append("- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함")
    return "\n".join(lines)


# =========================
# 3) Policy
# =========================
from typing import Dict, Any
def policy_filter_with_expectations(market_data: Dict[str, Any]) -> str:
    """
    Policy Filter upgraded with Macro-Δ structure engine.
    - Always works even when EXPECTATIONS is missing/unusable.
    - Uses REAL_RATE/FCI + DXY + US10Y to infer policy bias (structure).
    - Combines structure (bias) + price impulse (US10Y/DXY/VIX) into final regime.
    """

    # ---- helpers ----
    def _safe_get_series(key: str) -> Dict[str, Any]:
        s = _get_series(market_data, key) or {}
        return {
            "today": s.get("today"),
            "prev": s.get("prev"),
            "pct_change": s.get("pct_change"),
        }

    def _delta(s: Dict[str, Any]):
        t, p = s.get("today"), s.get("prev")
        if t is None or p is None:
            return None
        try:
            return float(t) - float(p)
        except Exception:
            return None

    def _dir_from_delta(d):
        if d is None:
            return 0
        return 1 if d > 0 else (-1 if d < 0 else 0)

    def _fmt_delta(d, digits=3):
        if d is None:
            return "N/A"
        return f"{d:+.{digits}f}"

    # ---- 1) pull series ----
    us10y = _safe_get_series("US10Y")
    dxy = _safe_get_series("DXY")
    vix = _safe_get_series("VIX")
    fci = _safe_get_series("FCI")
    real = _safe_get_series("REAL_RATE")

    us10y_d = _delta(us10y)
    dxy_d = _delta(dxy)
    vix_d = _delta(vix)  # (not used in structure score, but kept for display)
    fci_d = _delta(fci)
    real_d = _delta(real)

    # Price impulse (what market did) - uses pct_change sign from _sign_from()
    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    vix_dir = _sign_from(vix)

    # ---- 2) structure score (policy bias) ----
    # Convention: + direction = tighter / - direction = easier
    # Stronger weights: REAL_RATE, FCI, DXY. Weaker: US10Y (overlaps with REAL_RATE somewhat)
    score = 0.0
    components = []

    def add_component(name: str, d, w: float):
        nonlocal score
        if d is None:
            components.append(f"{name}Δ N/A")
            return
        direction = _dir_from_delta(d)  # + => tightening impulse, - => easing impulse
        score += w * direction
        components.append(f"{name}Δ {_fmt_delta(d)}")

    add_component("REAL_RATE", real_d, 1.0)   # real yield up = tighter
    add_component("FCI", fci_d, 1.0)          # conditions tighter = tighter
    add_component("DXY", dxy_d, 1.0)          # dollar stronger = tighter
    add_component("US10Y", us10y_d, 0.5)      # nominal up = tighter (weaker weight)

    # Bias buckets (structure)
    if score >= 2.5:
        bias = "TIGHTENING (긴축)"
        strength = "STRONG"
    elif score <= -2.5:
        bias = "EASING (완화)"
        strength = "STRONG"
    elif score >= 1.0:
        bias = "TIGHTENING (긴축)"
        strength = "MODERATE"
    elif score <= -1.0:
        bias = "EASING (완화)"
        strength = "MODERATE"
    else:
        bias = "MIXED (혼조)"
        strength = "WEAK"

    bias_line = f"Policy Bias: {bias} ({strength}, score={score:+.1f}) | " + " / ".join(components)
    market_data["POLICY_BIAS_LINE"] = bias_line

    # ---- 3) baseline regime from price action ----
    price_regime = "POLICY MIXED (정책 신호 혼조)"
    price_rationale = "금리/달러/변동성 신호가 완전히 정렬되지 않음"

    if us10y_dir == -1 and dxy_dir == -1 and vix_dir in (-1, 0):
        price_regime = "POLICY EASING (완화)"
        price_rationale = "금리↓ + 달러↓ (+VIX 안정) → 완화 쪽"
    elif us10y_dir == 1 and dxy_dir == 1:
        price_regime = "POLICY TIGHTENING (긴축)"
        price_rationale = "금리↑ + 달러↑ → 긴축 압력"

    # ---- 4) combine: structure vs price -> final regime ----
    # Simple decision rule:
    # - If structure is STRONG and conflicts with price -> structure-led
    # - If structure is STRONG and aligns -> reinforced
    # - Otherwise -> price-led (default)
    def _structure_label(bias_text: str) -> str:
        if "EASING" in bias_text:
            return "EASING"
        if "TIGHTENING" in bias_text:
            return "TIGHTENING"
        return "MIXED"

    def _price_label(regime_text: str) -> str:
        if "EASING" in regime_text:
            return "EASING"
        if "TIGHTENING" in regime_text:
            return "TIGHTENING"
        return "MIXED"

    s_lab = _structure_label(bias)
    p_lab = _price_label(price_regime)

    if strength == "STRONG" and s_lab != "MIXED" and p_lab != "MIXED" and s_lab != p_lab:
        regime = f"POLICY {s_lab} (structure-led) (구조 주도)"
        rationale = f"구조(REAL/FCI/DXY/US10Y)가 {s_lab} 방향으로 강함 → 가격신호({price_regime})는 확인/노이즈로 처리"
        one_liner = f"구조는 {bias}, 가격은 {price_regime} → 최종 POLICY {s_lab} (structure-led) (구조 주도)"
    elif strength == "STRONG" and s_lab != "MIXED" and s_lab == p_lab:
        regime = f"POLICY {s_lab} (reinforced) (강화)"
        rationale = f"구조(REAL/FCI/DXY/US10Y)와 가격신호가 모두 {s_lab}로 정렬 → 신호 신뢰도 상승"
        one_liner = f"구조={bias} & 가격={price_regime} 정렬 → 최종 POLICY {s_lab} (reinforced) (강화)"
    else:
        regime = price_regime
        rationale = price_rationale
        one_liner = f"구조={bias}({strength})는 참고, 가격={price_regime} 중심 → 최종 {regime}"

    # ---- 5) expectations (optional, display only for now) ----
    expectations_raw = market_data.get("EXPECTATIONS")
    if expectations_raw is None:
        exp_line = "Expectations: N/A (no data attached)"
    elif isinstance(expectations_raw, list):
        exp_line = f"Expectations: list received (len={len(expectations_raw)}), event-surprise layer not applied."
    elif isinstance(expectations_raw, dict):
        exp_line = "Expectations: dict received."
    else:
        exp_line = f"Expectations: unsupported type={type(expectations_raw).__name__}"

    # ---- 6) report ----
    lines = []
    lines.append("### 🏛️ 3) Policy Filter (with Expectations)")
    lines.append("- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?")
    lines.append("")
    lines.append(
        f"- **가격(현재) 신호:** US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / VIX({_dir_str(vix_dir)})"
    )
    lines.append(f"- **{bias_line}**")
    lines.append(f"- **{exp_line}**")
    lines.append("")
    lines.append(f"- **판정:** **{regime}**")
    lines.append(f"- **근거:** {rationale}")
    lines.append(f"- **한줄요약 ~~** {one_liner}")

    return "\n".join(lines)



# =========================
# 4) Fed Plumbing (TGA/RRP/Net Liquidity)
# =========================
def fed_plumbing_filter(market_data: Dict[str, Any]) -> str:
    tga = _get_series(market_data, "TGA")
    rrp = _get_series(market_data, "RRP")
    net = _get_series(market_data, "NET_LIQ")

    # ✅ generate_report.py: "_LIQ_ASOF"
    # ✅ legacy/other: "LIQUIDITY_ASOF"
    as_of = None
    raw_as_of = market_data.get("_LIQ_ASOF")

    if isinstance(raw_as_of, str) and raw_as_of.strip():
        as_of = raw_as_of.strip()

    if tga["today"] is None and rrp["today"] is None and net["today"] is None:
        lines = [
            "### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)",
            "- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?",
            "- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음",
            "- **Status:** Not ready (TGA/RRP/NET_LIQ not found in market_data)",
        ]
        return "\n".join(lines)

    tga_dir = _sign_from(tga)
    rrp_dir = _sign_from(rrp)
    net_dir = _sign_from(net)

    state = "LIQUIDITY NEUTRAL"
    rationale = "레벨/방향 혼조 또는 정보 제한"

    if net["today"] is not None:
        if net_dir == 1:
            state = "LIQUIDITY SUPPORTIVE (완만한 유동성 우호)"
            rationale = "Net Liquidity↑ → 시장 내 달러 여력 개선"
        elif net_dir == -1:
            state = "LIQUIDITY DRAINING (유동성 흡수)"
            rationale = "Net Liquidity↓ → 시장 내 달러 여력 축소 가능"

    lines = []
    lines.append("### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)")
    lines.append("- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?")
    lines.append("- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음")
    if as_of:
        lines.append(f"- **Liquidity as of:** {as_of} (FRED latest)")
    if net["today"] is not None:
        lines.append(f"- **NET_LIQ level:** {_fmt_num(net['today'], 1)}")
    if tga["today"] is not None:
        lines.append(f"- **TGA level:** {_fmt_num(tga['today'], 1)}")
    if rrp["today"] is not None:
        lines.append(f"- **RRP level:** {_fmt_num(rrp['today'], 3)}")

    lines.append(
        f"- **방향(전일 대비):** TGA({_dir_str(tga_dir)}) / RRP({_dir_str(rrp_dir)}) / NET_LIQ({_dir_str(net_dir)})"
    )
    lines.append(f"- **판정:** **{state}**")
    lines.append(f"- **근거:** {rationale}")
    lines.append("- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함")
    return "\n".join(lines)


# =========================
# 4.5) Credit Stress Filter (HYG vs LQD)
# =========================
def credit_stress_filter(market_data: Dict[str, Any]) -> str:
    """
    If HYG ↓ and LQD ↑ or → :
        Credit Stress ↑ (Risk-off warning)

    해석:
      - 하이일드(저신용) 채권이 약해지고,
      - IG(우량) 채권은 버티거나 강해지면,
      → 시장이 '위험을 감수할 이유가 없다'고 판단하며
        크레딧 리스크를 먼저 줄이는 신호로 해석
    """
    hyg = _get_series(market_data, "HYG")
    lqd = _get_series(market_data, "LQD")

    if hyg["today"] is None or lqd["today"] is None:
        lines = [
            "### 🧾 4.5) Credit Stress Filter (HYG vs LQD)",
            "- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?",
            "- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성",
            "- **Status:** Not ready (need HYG & LQD in market_data)",
        ]
        return "\n".join(lines)

    hyg_dir = _sign_from(hyg)
    lqd_dir = _sign_from(lqd)

    state = "CREDIT NEUTRAL"
    rationale = "HYG/LQD 방향성이 뚜렷하지 않음"

    # 핵심 룰
    if hyg_dir == -1 and lqd_dir in (0, 1):
        state = "CREDIT STRESS ↑ (Risk-off warning)"
        rationale = "하이일드 약세(HYG↓) + 우량채 방어(LQD→/↑) → 위험회피로 크레딧 프리미엄 재평가 가능"
    elif hyg_dir == 1 and lqd_dir in (0, -1):
        state = "CREDIT RISK-ON (risk appetite improving)"
        rationale = "하이일드 강세(HYG↑) + 우량채 약세/보합(LQD→/↓) → 위험선호 회복 가능"

    lines = []
    lines.append("### 🧾 4.5) Credit Stress Filter (HYG vs LQD)")
    lines.append("- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?")
    lines.append("- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성")
    lines.append(f"- **방향(전일 대비):** HYG({_dir_str(hyg_dir)}) / LQD({_dir_str(lqd_dir)})")
    lines.append(f"- **HYG:** today {_fmt_num(hyg['today'], 3)} / prev {_fmt_num(hyg['prev'], 3)} / pct {_fmt_num(hyg['pct_change'], 2)}%")
    lines.append(f"- **LQD:** today {_fmt_num(lqd['today'], 3)} / prev {_fmt_num(lqd['prev'], 3)} / pct {_fmt_num(lqd['pct_change'], 2)}%")
    lines.append(f"- **판정:** **{state}**")
    lines.append(f"- **근거:** {rationale}")
    return "\n".join(lines)

def high_yield_spread_filter(market_data: Dict[str, Any]) -> str:
    """
    4.2) High Yield Spread Filter (HY OAS)
    - HY OAS level = 크레딧 공포의 '온도'
    - Level이 높을수록: 디폴트/자금조달/리스크 프리미엄 스트레스 ↑
    """
    hy = _get_series(market_data, "HY_OAS")
    asof = market_data.get("_HY_ASOF")

    if hy.get("today") is None:
        lines = [
            "### 🌡️ 4.2) High Yield Spread Filter (HY OAS)",
            "- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?",
            "- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌",
            "- **Status:** Not ready (need HY_OAS in market_data)",
        ]
        return "\n".join(lines)

    level = float(hy["today"])
    d = _sign_from(hy)
    pct = hy.get("pct_change")
    pct_txt = f"{pct:+.2f}%" if pct is not None else "N/A"

    # ✅ 간단/실무형 레벨 구간 (퍼센트 단위)
    # (너 프로젝트에 맞춰 추후 조정 가능)
    if level < 3.0:
        temp = "COOL (낮은 공포)"
        base_state = "CREDIT CALM"
        base_reason = "HY 스프레드 낮음 → 크레딧 스트레스 제한"
    elif level < 4.0:
        temp = "WARM (경계)"
        base_state = "CREDIT WATCH"
        base_reason = "스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능"
    elif level < 6.0:
        temp = "HOT (스트레스)"
        base_state = "CREDIT STRESS"
        base_reason = "스프레드 의미 있게 높음 → 위험자산 변동성↑ 가능"
    else:
        temp = "BURNING (위기 수준)"
        base_state = "CREDIT CRISIS"
        base_reason = "스프레드 급등 구간 → 디폴트/유동성 경색 우려"

    # 방향까지 반영해 한 줄 더 “온도 해석”을 얹기
    if d == 1:
        nuance = "스프레드가 벌어지는 중 → 공포 온도 상승"
    elif d == -1:
        nuance = "스프레드가 좁혀지는 중 → 공포 온도 완화"
    else:
        nuance = "방향성 제한 → 레벨 중심 해석"

    lines = []
    lines.append("### 🌡️ 4.2) High Yield Spread Filter (HY OAS)")
    lines.append("- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?")
    lines.append("- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌")
    if asof:
        lines.append(f"- **Spread as of:** {asof} (FRED latest)")
    lines.append(f"- **HY_OAS level:** {_fmt_num(level, 2)}% → **{temp}**")
    lines.append(f"- **방향(전일 대비):** HY_OAS({_dir_str(d)}) / {pct_txt}")
    lines.append(f"- **판정:** **{base_state}**")
    lines.append(f"- **근거:** {base_reason} / {nuance}")
    lines.append("- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함")
    return "\n".join(lines)



# =========================
# 5) Directional signals (legacy)
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
    lines.append(line("HYG", "HYG (High Yield ETF)", "크레딧 위험선호↑", "크레딧 스트레스↑", "보합(크레딧 변화 제한)"))
    lines.append(line("LQD", "LQD (IG Bond ETF)", "우량채 강세(리스크오프 성향)", "우량채 약세(리스크온 성향)", "보합(방향성 제한)"))
    return "\n".join(lines)


# =========================
# 6) Cross-Asset Filter
# =========================
def cross_asset_filter(market_data: Dict[str, Any]) -> str:
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
    lines.append("- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함")
    lines.append("")

    if us10y_dir == 1:
        lines.append("- **금리 상승(US10Y↑)** → 달러 강세(DXY↑) / 위험자산 할인율 부담 / 성장주 변동성↑ 경향")
    elif us10y_dir == -1:
        lines.append("- **금리 하락(US10Y↓)** → 달러 약세(DXY↓) / 할인율 부담 완화 / 위험자산 선호↑ 경향")
    else:
        lines.append("- **금리 보합(US10Y→)** → 할인율 변수 제한")

    if vix_dir == 1:
        lines.append("- **변동성 상승(VIX↑)** → 위험회피 강화 / 달러 선호↑ / 원자재·주식 부담 가능")
    elif vix_dir == -1:
        lines.append("- **변동성 하락(VIX↓)** → 심리 개선 / 위험자산 수요 회복 가능")
    else:
        lines.append("- **변동성 보합(VIX→)** → 심리 변화 제한")

    if wti_dir == 1:
        lines.append("- **유가 상승(WTI↑)** → 인플레 재자극 가능성 / 금리 상방 압력")
    elif wti_dir == -1:
        lines.append("- **유가 하락(WTI↓)** → 물가 부담 완화 / 긴축 압력 완화 가능")
    else:
        lines.append("- **유가 보합(WTI→)** → 물가 변수 제한")

    return "\n".join(lines)


# =========================
# 7) Risk Exposure Filter
# =========================
def risk_exposure_filter(market_data: Dict[str, Any]) -> str:
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
        lines.append("- **VIX 상승(VIX↑)** → 변동성 확대: 포지션 축소/헤지 수요 증가 가능")
    elif vix_dir == -1:
        lines.append("- **VIX 하락(VIX↓)** → 심리 안정: 리스크 수용 여력 개선")
    else:
        lines.append("- **VIX 보합(VIX→)** → 심리 변화 제한")

    if us10y_dir == 1:
        lines.append("- **금리 상승(US10Y↑)** → 할인율 부담/유동성 압박 가능")
    elif us10y_dir == -1:
        lines.append("- **금리 하락(US10Y↓)** → 완화 기대/할인율 부담 완화 가능")
    else:
        lines.append("- **금리 보합(US10Y→)** → 금리 변수 제한")

    if dxy_dir == 1:
        lines.append("- **달러 강세(DXY↑)** → 신흥국·원자재·원화 등 위험자산에 부담")
    elif dxy_dir == -1:
        lines.append("- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능")
    else:
        lines.append("- **달러 보합(DXY→)** → 달러 변수 제한")

    if wti_dir == 1:
        lines.append("- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능")
    elif wti_dir == -1:
        lines.append("- **유가 하락(WTI↓)** → 물가 부담 완화 가능")
    else:
        lines.append("- **유가 보합(WTI→)** → 물가 변수 제한")

    return "\n".join(lines)


# =========================
# 8) Incentive Filter
# =========================
def incentive_filter(market_data: Dict[str, Any]) -> str:
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    wti = _get_series(market_data, "WTI")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    wti_dir = _sign_from(wti)

    winners = []
    losers = []

    if us10y_dir == 1:
        winners.append("Banks/Financials (higher rates)")
        losers.append("Long-duration growth (discount-rate pressure)")
    elif us10y_dir == -1:
        winners.append("Long-duration growth (discount-rate relief)")

    if dxy_dir == 1:
        winners.append("USD holders / US importers")
        losers.append("EM assets / USD debtors")
    elif dxy_dir == -1:
        winners.append("EM assets / risk trades")
        losers.append("USD strength trades")

    if wti_dir == 1:
        winners.append("Energy producers")
        losers.append("Energy consumers")
    elif wti_dir == -1:
        winners.append("Energy consumers")
        losers.append("Energy producers")

    lines = []
    lines.append("### 💸 8) Incentive Filter")
    lines.append("- **질문:** 누가 이득을 보고 있는가?")
    lines.append(f"- **핵심 신호:** US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / WTI({_dir_str(wti_dir)})")
    lines.append("- **이득을 보는 주체:**")
    lines.extend([f"  - {w}" for w in winners] if winners else ["  - None"])
    lines.append("- **손해를 보는 주체:**")
    lines.extend([f"  - {l}" for l in losers] if losers else ["  - None"])
    return "\n".join(lines)


# =========================
# 9) Cause Filter
# =========================
def cause_filter(market_data: Dict[str, Any]) -> str:
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
        parts.append("금리 상승(US10Y↑)")
    elif us10y_dir == -1:
        parts.append("금리 하락(US10Y↓)")

    if dxy_dir == 1:
        parts.append("달러 강세(DXY↑)")
    elif dxy_dir == -1:
        parts.append("달러 약세(DXY↓)")

    if wti_dir == 1:
        parts.append("유가 상승(WTI↑)")
    elif wti_dir == -1:
        parts.append("유가 하락(WTI↓)")

    if vix_dir == 1:
        parts.append("변동성 확대(VIX↑)")
    elif vix_dir == -1:
        parts.append("변동성 완화(VIX↓)")

    cause = " + ".join(parts) if parts else "원인 신호 뚜렷하지 않음"

    lines = []
    lines.append("### 🔍 9) Cause Filter")
    lines.append("- **질문:** 무엇이 이 움직임을 만들었는가?")
    lines.append(f"- **핵심 신호:** US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / WTI({_dir_str(wti_dir)}) / VIX({_dir_str(vix_dir)})")
    lines.append(f"- **판정:** **{cause}**")
    return "\n".join(lines)


# =========================
# 10) Direction Filter
# =========================
def direction_filter(market_data: Dict[str, Any]) -> str:
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    wti = _get_series(market_data, "WTI")
    vix = _get_series(market_data, "VIX")

    us10y_strength = _strength_label("US10Y", us10y.get("pct_change"))
    dxy_strength = _strength_label("DXY", dxy.get("pct_change"))
    wti_strength = _strength_label("WTI", wti.get("pct_change"))
    vix_strength = _strength_label("VIX", vix.get("pct_change"))

    lines = []
    lines.append("### 🔄 10) Direction Filter")
    lines.append("- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?")
    lines.append(
        f"- **강도:** US10Y({us10y_strength}) / DXY({dxy_strength}) / WTI({wti_strength}) / VIX({vix_strength})"
    )

    if "Strong" in (us10y_strength, dxy_strength, wti_strength, vix_strength) or "Clear" in (
        us10y_strength,
        dxy_strength,
        wti_strength,
        vix_strength,
    ):
        lines.append("- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**")
    else:
        lines.append("- **판정:** **MOSTLY NOISE (대부분 노이즈)**")

    return "\n".join(lines)


# =========================
# 11) Timing Filter
# =========================
def timing_filter(market_data: Dict[str, Any]) -> str:
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")

    lines = []
    lines.append("### ⏳ 11) Timing Filter")
    lines.append("- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?")
    lines.append("- **가이드:**")
    lines.append("  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼")
    lines.append("  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감")
    lines.append(
        f"- **Today snapshot:** US10Y({_fmt_num(us10y['today'], 3)}), DXY({_fmt_num(dxy['today'], 3)}), VIX({_fmt_num(vix['today'], 2)})"
    )
    return "\n".join(lines)


# =========================
# 12) Structural Filter
# =========================
def structural_filter(market_data: Dict[str, Any]) -> str:
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")
    wti = _get_series(market_data, "WTI")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    vix_dir = _sign_from(vix)
    wti_dir = _sign_from(wti)

    state = "NEUTRAL"
    rationale = "패권/구조 신호가 뚜렷하지 않음"

    if us10y_dir == 1 and dxy_dir == 1:
        state = "GLOBAL FINANCIAL TIGHTENING (글로벌 긴축 구조)"
        rationale = "금리↑ + 달러↑ 조합은 글로벌 자금조달 비용을 올려 신흥국/리스크자산에 부담"
    elif wti_dir == -1 and vix_dir == 1:
        state = "WEAK DEMAND + RISK-OFF (수요 둔화 + 위험회피)"
        rationale = "유가↓ + VIX↑는 성장 둔화 우려와 위험회피 심리 강화로 연결될 수 있음"

    lines = []
    lines.append("### 🏗️ 12) Structural Filter")
    lines.append("- **질문:** 이 변화가 글로벌 구조(달러 패권/성장/에너지)에 어떤 힌트를 주는가?")
    lines.append(
        f"- **핵심 신호:** US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / VIX({_dir_str(vix_dir)}) / WTI({_dir_str(wti_dir)})"
    )
    lines.append(f"- **판정:** **{state}**")
    lines.append(f"- **근거:** {rationale}")
    return "\n".join(lines)


def narrative_engine_filter(market_data: Dict[str, Any]) -> str:
    """
    Narrative Engine v2 (Phase-Respecting Risk Budget) — Liquidity upgraded

    Structure + Sentiment + Credit + Liquidity + Phase
    → Final Risk Action + Risk Budget (0~100)

    핵심 업그레이드:
    - Phase별 Risk Budget 상한(cap) 적용
    - Liquidity를 pct(방향) + level bucket(HIGH/MID/LOW) 2축으로 반영
      * attach_liquidity_layer에서 market_data["NET_LIQ"]["level_bucket"] 세팅된 것을 사용
    """

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _to_float(x) -> Optional[float]:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return float(x)
        try:
            return float(str(x).replace(",", "").replace("%", ""))
        except Exception:
            return None

    def _clamp(x: int, lo: int = 0, hi: int = 100) -> int:
        return max(lo, min(hi, int(x)))

    def _sentiment_state(fear: Optional[float]) -> str:
        if fear is None:
            return "N/A"
        if fear < 30:
            return "FEAR"
        if fear > 70:
            return "GREED"
        return "NEUTRAL"

    def _liq_dir_tag(pct: Optional[float]) -> str:
        if pct is None:
            return "N/A"
        if pct > 0:
            return "UP"
        if pct < 0:
            return "DOWN"
        return "FLAT"

    # --------------------------------------------------
    # 1️⃣ Pull Signals
    # --------------------------------------------------

    policy_bias_line = str(market_data.get("POLICY_BIAS_LINE", "") or "")

    sentiment = market_data.get("SENTIMENT", {}) or {}
    fear = _to_float(sentiment.get("fear_greed"))
    sent_state = _sentiment_state(fear)

    hy_oas = market_data.get("HY_OAS", {}) or {}
    hy_oas_today = _to_float(hy_oas.get("today"))
    credit_calm: Optional[bool] = None
    if hy_oas_today is not None:
        credit_calm = hy_oas_today < 4.0

    net_liq = market_data.get("NET_LIQ", {}) or {}
    net_liq_pct = _to_float(net_liq.get("pct_change"))
    liq_dir_tag = _liq_dir_tag(net_liq_pct)

    # NEW: level bucket (HIGH/MID/LOW) from attach_liquidity_layer
    liq_level_bucket = str(net_liq.get("level_bucket") or market_data.get("NET_LIQ_LEVEL_BUCKET") or "N/A").upper()
    if liq_level_bucket not in ("HIGH", "MID", "LOW"):
        liq_level_bucket = "N/A"

    phase = market_data.get("MARKET_REGIME", "N/A")
    phase_upper = str(phase).upper()

    policy_upper = policy_bias_line.upper()
    easing = "EASING" in policy_upper
    tightening = "TIGHTENING" in policy_upper

    # --------------------------------------------------
    # 2️⃣ Risk Budget Core
    # --------------------------------------------------

    # Base from sentiment
    if sent_state == "FEAR":
        budget = 35
    elif sent_state == "GREED":
        budget = 70
    elif sent_state == "NEUTRAL":
        budget = 55
    else:
        budget = 50

    # Structure tilt
    if easing and not tightening:
        budget += 10
    elif tightening and not easing:
        budget -= 10

    # Credit tilt
    if credit_calm is True:
        budget += 10
    elif credit_calm is False:
        budget -= 10

    # Liquidity tilt (Direction + Level)
    # Direction: UP +10 / DOWN -10 / FLAT 0 / N/A 0
    if liq_dir_tag == "UP":
        budget += 10
    elif liq_dir_tag == "DOWN":
        budget -= 10

    # Level bucket: HIGH +5 / LOW -5 / MID 0 / N/A 0
    if liq_level_bucket == "HIGH":
        budget += 5
    elif liq_level_bucket == "LOW":
        budget -= 5

    # --------------------------------------------------
    # 3️⃣ Phase Cap (핵심 업그레이드)
    # --------------------------------------------------

    cap = 100
    if phase_upper.startswith("WAITING") or "RANGE" in phase_upper:
        cap = 60
    elif phase_upper.startswith("TRANSITION") or "MIXED" in phase_upper:
        cap = 70
    elif phase_upper.startswith("RISK-ON"):
        cap = 85
    elif phase_upper.startswith("RISK-OFF"):
        cap = 35

    budget = min(int(round(budget)), cap)
    budget = _clamp(budget, 0, 100)

    # store for downstream filters (e.g., Volatility-Controlled Exposure)
    market_data["RISK_BUDGET"] = budget

    # --------------------------------------------------
    # 4️⃣ Final Action
    # --------------------------------------------------

    if budget >= 70:
        action = "INCREASE"
    elif budget <= 35:
        action = "REDUCE"
    else:
        action = "HOLD"

    # --------------------------------------------------
    # 5️⃣ Narrative Line
    # --------------------------------------------------

    struct_tag = "EASING" if easing else ("TIGHTENING" if tightening else "MIXED")
    credit_tag = "안정" if credit_calm is True else ("불안" if credit_calm is False else "N/A")

    # More Wall-Street-ish liquidity tag (two-axis)
    liq_dir_kr = {"UP": "증가", "DOWN": "감소", "FLAT": "보합", "N/A": "N/A"}[liq_dir_tag]
    liq_lvl_kr = {"HIGH": "높음", "MID": "중간", "LOW": "낮음", "N/A": "N/A"}.get(liq_level_bucket, "N/A")
    liq_tag = f"{liq_dir_kr}/{liq_lvl_kr}"

    narrative = (
        f"구조={struct_tag} / 심리={sent_state} / 유동성={liq_tag} / "
        f"크레딧={credit_tag} → Phase={phase}"
    )
        # --------------------------------------------------
    # 6.5️⃣ Final State Object (for Executive/Decision/Scenario layers)
    # --------------------------------------------------
    final_state = {
        "phase": phase,
        "phase_cap": cap,
        "risk_action": action,
        "risk_budget": budget,

        "structure_tag": struct_tag,           # EASING/TIGHTENING/MIXED
        "policy_bias_line": policy_bias_line,  # 원문 보존

        "sentiment_fear_greed": fear,
        "sentiment_state": sent_state,         # FEAR/NEUTRAL/GREED

        "credit_calm": credit_calm,            # True/False/None
        "hy_oas_today": hy_oas_today,

        "liquidity_dir": liq_dir_tag,          # UP/DOWN/FLAT/N/A
        "liquidity_level_bucket": liq_level_bucket,  # HIGH/MID/LOW/N/A
        "net_liq_pct_change": net_liq_pct,

        "narrative_line": narrative,
    }

    market_data["FINAL_STATE"] = final_state
    # --------------------------------------------------
    # 6️⃣ Output (기존 필터 스타일 통일)
    # --------------------------------------------------

    lines = []
    lines.append("### 🧠 13) Narrative Engine (v2 + Risk Budget)")
    lines.append("- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정")
    lines.append("- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문")
    lines.append("")
    lines.append(f"- **Structure Bias:** {policy_bias_line}")
    lines.append(f"- **Sentiment (Fear&Greed):** {fear if fear is not None else 'N/A'} ({sent_state})")
    lines.append(f"- **Credit Calm (HY OAS<4):** {credit_calm}")
    lines.append(f"- **Liquidity (NET_LIQ):** dir={liq_dir_tag} / level={liq_level_bucket}")
    lines.append(f"- **Phase:** {phase}")
    lines.append("")
    lines.append(f"- **🎯 Final Risk Action:** **{action}**")
    lines.append(f"- **Risk Budget (0~100):** **{budget}**")
    lines.append(f"- **Narrative:** {narrative}")


    return "\n".join(lines)
    
def divergence_monitor_filter(market_data: Dict[str, Any]) -> str:
    """
    Divergence Monitor
    Structure (Policy Bias) vs Price Regime (Market Regime)
    """

    policy_bias = str(market_data.get("POLICY_BIAS_LINE", ""))
    phase = str(market_data.get("MARKET_REGIME", "N/A"))

    policy_upper = policy_bias.upper()
    phase_upper = phase.upper()

    # ---------------------------
    # 1️⃣ Structure 판별
    # ---------------------------

    if "EASING" in policy_upper:
        structure = "EASING"
    elif "TIGHTENING" in policy_upper:
        structure = "TIGHTENING"
    else:
        structure = "MIXED"

    # ---------------------------
    # 2️⃣ Price Regime 판별
    # ---------------------------

    if phase_upper.startswith("RISK-ON"):
        price = "RISK-ON"
    elif phase_upper.startswith("RISK-OFF"):
        price = "RISK-OFF"
    elif phase_upper.startswith("WAITING") or "RANGE" in phase_upper:
        price = "WAITING"
    elif phase_upper.startswith("TRANSITION"):
        price = "TRANSITION"
    elif phase_upper.startswith("EVENT"):
        price = "MIXED"
    else:
        price = "MIXED"

    # ---------------------------
    # 3️⃣ Divergence 판단
    # ---------------------------

    status = "ALIGNED"
    explanation = "구조와 가격 신호가 대체로 정렬"

    if structure == "EASING" and price == "RISK-OFF":
        status = "DIVERGENCE"
        explanation = "구조는 완화인데 가격은 리스크오프 → 전환 가능성 탐지"

    elif structure == "TIGHTENING" and price == "RISK-ON":
        status = "DIVERGENCE"
        explanation = "구조는 긴축인데 가격은 리스크온 → 과열/되돌림 가능성"

    elif structure == "EASING" and price == "MIXED":
        status = "DELAYED RESPONSE"
        explanation = "구조는 완화이나 가격은 아직 명확히 반응하지 않음"

    elif structure == "TIGHTENING" and price == "MIXED":
        status = "DELAYED RESPONSE"
        explanation = "구조는 긴축이나 가격은 아직 명확히 반응하지 않음"

    elif price in ("WAITING", "TRANSITION"):
        status = "TRANSITION ZONE"
        explanation = "시장 방향 탐색 구간"

    # ---------------------------
    # 4️⃣ Output
    # ---------------------------

    lines = []
    lines.append("### ⚠ 14) Divergence Monitor")
    lines.append("- **정의:** 구조(정책)와 가격(시장 국면)의 충돌 여부 감지")
    lines.append("- **추가 이유:** 구조-가격 충돌은 국면 전환의 초기 신호가 될 수 있음")
    lines.append("")
    lines.append(f"- **Structure:** {structure}")
    lines.append(f"- **Price Regime:** {price}")
    lines.append(f"- **Status:** **{status}**")
    lines.append(f"- **해석:** {explanation}")

    return "\n".join(lines)
    
    #Build

def volatility_controlled_exposure_filter(market_data: Dict[str, Any]) -> str:
    """
    🎯 15) Volatility-Controlled Exposure (v2 - Pro)

    Risk Budget → 실제 익스포저 변환
    업그레이드:
    - VIX 레벨 + 변화율 반영
    - Phase cap 재적용
    - Exposure smoothing
    - Guardrail (리스크 자동 브레이크)
    """

    # ---------------------------
    # Helpers
    # ---------------------------
    def _to_float(x) -> Optional[float]:
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return float(x)
        try:
            return float(str(x).replace(",", "").replace("%", "").strip())
        except Exception:
            return None

    def _clamp(x, lo=0, hi=100):
        return max(lo, min(int(round(x)), hi))

    # ---------------------------
    # Inputs
    # ---------------------------
    risk_budget = _to_float(market_data.get("RISK_BUDGET", 50))
    if risk_budget is None:
        risk_budget = 50.0

    phase = str(market_data.get("MARKET_REGIME", "N/A")).upper()

    vix_series = market_data.get("VIX", {}) or {}
    vix_today = _to_float(vix_series.get("today"))
    vix_pct = _to_float(vix_series.get("pct_change"))

    prev_exposure = _to_float(market_data.get("PREV_EXPOSURE"))
    if prev_exposure is None:
        prev_exposure = risk_budget

    # ---------------------------
    # 1️⃣ Phase Cap
    # ---------------------------
    cap = 100
    if phase.startswith("WAITING") or "RANGE" in phase:
        cap = 60
    elif phase.startswith("TRANSITION") or "MIXED" in phase:
        cap = 70
    elif phase.startswith("RISK-ON"):
        cap = 85
    elif phase.startswith("RISK-OFF"):
        cap = 35

    exposure = min(risk_budget, cap)

    # ---------------------------
    # 2️⃣ VIX Level Adjustment
    # ---------------------------
    vol_state = "N/A"
    multiplier = 1.0

    if vix_today is not None:
        if vix_today < 14:
            vol_state = "LOW"
            multiplier *= 1.05
        elif vix_today < 20:
            vol_state = "NORMAL"
        elif vix_today < 30:
            vol_state = "HIGH"
            multiplier *= 0.80
        else:
            vol_state = "EXTREME"
            multiplier *= 0.60

    # ---------------------------
    # 3️⃣ VIX Momentum Adjustment
    # ---------------------------
    if vix_pct is not None:
        if vix_pct > 5:
            multiplier *= 0.85  # 급등 시 추가 감산
        elif vix_pct < -5:
            multiplier *= 1.05  # 급락 시 소폭 가산

    exposure *= multiplier

    # ---------------------------
    # 4️⃣ Guardrail (Stress Brake)
    # ---------------------------
    hy_oas = market_data.get("HY_OAS", {}) or {}
    hy_level = _to_float(hy_oas.get("today"))

    if hy_level is not None and hy_level > 5:
        exposure *= 0.75  # 크레딧 스트레스 발생 시 감산

    # ---------------------------
    # 5️⃣ Smoothing (급변 방지)
    # ---------------------------
    if prev_exposure is not None:
        exposure = 0.7 * prev_exposure + 0.3 * exposure

    exposure = min(exposure, cap)
    exposure = _clamp(exposure)

    # 저장 (다음날 smoothing용)
    market_data["PREV_EXPOSURE"] = exposure

    # ---------------------------
    # Output (기존 필터 스타일)
    # ---------------------------
    if vix_today is not None:
        vix_display = f"{vix_today:.2f}"
    else:
        vix_display = "N/A"

    if vix_pct is not None:
        vix_pct_display = f"{vix_pct:+.2f}%"
    else:
        vix_pct_display = "N/A"

    lines = []
    lines.append("### 🎯 15) Volatility-Controlled Exposure (v2)")
    lines.append("- **정의:** Risk Budget을 실제 익스포저로 변환 (Pro Version)")
    lines.append("- **추가 이유:** 변동성·스트레스·국면을 모두 반영한 실전형 리스크 제어")
    lines.append("")
    lines.append(f"- **Risk Budget:** {risk_budget:.0f}")
    lines.append(f"- **Phase Cap:** {cap}")
    lines.append(f"- **VIX Level:** {vix_display} ({vol_state})")
    lines.append(f"- **VIX Change (%):** {vix_pct_display}")
    lines.append(f"- **Final Multiplier:** {multiplier:.2f}x")
    lines.append("")
    lines.append(f"- **📊 Recommended Exposure:** **{exposure}%**")

    return "\n".join(lines)

def style_tilt_filter(market_data: Dict[str, Any]) -> str:
    """
    🎨 16) Style Tilt (v1.1)

    Improvements:
    - Duration: use US10Y delta (today-prev) if available
    - Cyclical/Defensive: use Exposure + Phase first, WTI as secondary
    """

    def _to_float(x):
        try:
            return float(str(x).replace(",", "").replace("%", ""))
        except:
            return None

    policy_bias = str(market_data.get("POLICY_BIAS_LINE", "")).upper()
    phase = str(market_data.get("MARKET_REGIME", "")).upper()

    # US10Y: prefer delta
    us10y = market_data.get("US10Y", {})
    us10y_today = _to_float(us10y.get("today"))
    us10y_prev = _to_float(us10y.get("prev"))
    us10y_delta = None
    if us10y_today is not None and us10y_prev is not None:
        us10y_delta = us10y_today - us10y_prev

    # WTI: optional secondary
    oil = market_data.get("WTI", {})
    oil_pct = _to_float(oil.get("pct_change"))

    # Exposure (from filter 15)
    exposure = _to_float(market_data.get("RECOMMENDED_EXPOSURE"))
    if exposure is None:
        exposure = _to_float(market_data.get("PREV_EXPOSURE"))

    easing = "EASING" in policy_bias
    tightening = "TIGHTENING" in policy_bias

    # 1) Growth vs Value
    style = "NEUTRAL"
    if easing and (us10y_delta is None or us10y_delta <= 0):
        style = "GROWTH TILT"
    elif tightening or (us10y_delta is not None and us10y_delta > 0):
        style = "VALUE TILT"

    # 2) Duration
    duration = "NEUTRAL"
    if us10y_delta is not None:
        if us10y_delta < 0:
            duration = "LONG DURATION FAVORED"
        elif us10y_delta > 0:
            duration = "SHORT DURATION FAVORED"

    # 3) Cyclical vs Defensive
    cyclical = "NEUTRAL"

    # primary: phase + exposure
    if phase.startswith("RISK-ON"):
        cyclical = "CYCLICAL FAVORED"
    elif phase.startswith("RISK-OFF"):
        cyclical = "DEFENSIVE FAVORED"
    elif phase.startswith("WAITING") or "RANGE" in phase or phase.startswith("EVENT"):
        cyclical = "DEFENSIVE / QUALITY BIAS"

    # secondary: exposure high => cyclicals, low => defensive
    if exposure is not None:
        if exposure >= 70:
            cyclical = "CYCLICAL FAVORED"
        elif exposure <= 35:
            cyclical = "DEFENSIVE FAVORED"

    # tertiary: oil impulse
    if oil_pct is not None and oil_pct > 1.0:
        cyclical = "CYCLICAL (ENERGY) BIAS"

    lines = []
    lines.append("### 🎨 16) Style Tilt (v1.1)")
    lines.append("- **정의:** Macro 구조 기반 스타일 기울기 판단")
    lines.append("- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분")
    lines.append("")
    lines.append(f"- **Growth vs Value:** **{style}**")
    lines.append(f"- **Duration Tilt:** **{duration}**")
    lines.append(f"- **Cyclical vs Defensive:** **{cyclical}**")
    return "\n".join(lines)


def factor_layer_filter(market_data: Dict[str, Any]) -> str:
    """
    🧩 17) Factor Layer (v1)

    정의: 시장을 움직이는 핵심 위험 요인 판별
    목적: 자금이 무엇에 민감하게 반응하는지 파악
    """

    def _to_float(x):
        try:
            return float(str(x).replace(",", "").replace("%", ""))
        except:
            return None

    # ---------------------------
    # Pull Data
    # ---------------------------

    us10y = market_data.get("US10Y", {})
    dxy = market_data.get("DXY", {})
    oil = market_data.get("WTI", {})
    hy = market_data.get("HY_OAS", {})

    us10y_today = _to_float(us10y.get("today"))
    us10y_prev = _to_float(us10y.get("prev"))
    us10y_delta = None
    if us10y_today is not None and us10y_prev is not None:
        us10y_delta = us10y_today - us10y_prev

    dxy_pct = _to_float(dxy.get("pct_change"))
    oil_pct = _to_float(oil.get("pct_change"))
    hy_level = _to_float(hy.get("today"))

    # ---------------------------
    # 1️⃣ Duration Factor
    # ---------------------------

    duration = "NEUTRAL"
    if us10y_delta is not None:
        if us10y_delta < 0:
            duration = "LONG DURATION FAVORED"
        elif us10y_delta > 0:
            duration = "SHORT DURATION FAVORED"

    # ---------------------------
    # 2️⃣ Inflation Factor
    # ---------------------------

    inflation = "NEUTRAL"
    if oil_pct is not None and us10y_delta is not None:
        if oil_pct > 1 and us10y_delta > 0:
            inflation = "INFLATION PRESSURE"
        elif oil_pct < -1 and us10y_delta < 0:
            inflation = "DISINFLATION"

    # ---------------------------
    # 3️⃣ USD Factor
    # ---------------------------

    usd = "NEUTRAL"
    if dxy_pct is not None:
        if dxy_pct > 0.3:
            usd = "USD TIGHTENING"
        elif dxy_pct < -0.3:
            usd = "USD EASING"

    # ---------------------------
    # 4️⃣ Credit Factor
    # ---------------------------

    credit = "NEUTRAL"
    if hy_level is not None:
        if hy_level < 4:
            credit = "CREDIT SUPPORTIVE"
        elif hy_level > 5:
            credit = "CREDIT STRESS"

    # ---------------------------
    # Output
    # ---------------------------

    lines = []
    lines.append("### 🧩 17) Factor Layer (v1)")
    lines.append("- **정의:** 시장을 움직이는 핵심 위험 요인 판별")
    lines.append("- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악")
    lines.append("")
    lines.append(f"- **Duration Factor:** {duration}")
    lines.append(f"- **Inflation Factor:** {inflation}")
    lines.append(f"- **USD Factor:** {usd}")
    lines.append(f"- **Credit Factor:** {credit}")

    return "\n".join(lines)    

def sector_allocation_filter(market_data: Dict[str, Any]) -> str:
    """
    🏭 18) Sector Allocation Engine (v1)

    정의: Macro + Style + Factor 종합 섹터 기울기 판단
    목적: 상대적 Overweight / Underweight 방향 제시
    """

    policy = str(market_data.get("POLICY_BIAS_LINE", "")).upper()
    phase = str(market_data.get("MARKET_REGIME", "")).upper()
    style_info = str(market_data.get("STYLE_TILT_OUTPUT", "")).upper()
    factor_info = str(market_data.get("FACTOR_LAYER_OUTPUT", "")).upper()

    overweight = []
    underweight = []

    easing = "EASING" in policy
    tightening = "TIGHTENING" in policy

    # ---------------------------
    # Growth vs Value
    # ---------------------------
    if "GROWTH TILT" in style_info:
        overweight += ["Technology", "Communication Services"]
    elif "VALUE TILT" in style_info:
        overweight += ["Financials", "Energy"]

    # ---------------------------
    # Cyclical vs Defensive
    # ---------------------------
    if "CYCLICAL" in style_info:
        overweight += ["Industrials", "Materials"]
    elif "DEFENSIVE" in style_info:
        overweight += ["Healthcare", "Consumer Staples", "Utilities"]

    # ---------------------------
    # Inflation Factor
    # ---------------------------
    if "INFLATION PRESSURE" in factor_info:
        overweight += ["Energy", "Materials"]
    elif "DISINFLATION" in factor_info:
        overweight += ["Technology"]

    # ---------------------------
    # Credit Stress
    # ---------------------------
    if "CREDIT STRESS" in factor_info:
        underweight += ["Financials", "Industrials"]
    elif "CREDIT SUPPORTIVE" in factor_info:
        overweight += ["Financials"]

    # 중복 제거
    overweight = list(set(overweight))
    underweight = list(set(underweight))

    lines = []
    lines.append("### 🏭 18) Sector Allocation Engine (v1)")
    lines.append("- **정의:** Macro + Style + Factor 종합 섹터 기울기 판단")
    lines.append("- **추가 이유:** 방향뿐 아니라 어느 산업에 기울어야 하는지 판단")
    lines.append("")
    lines.append(f"- **Overweight:** {', '.join(overweight) if overweight else 'None'}")
    lines.append(f"- **Underweight:** {', '.join(underweight) if underweight else 'None'}")

    return "\n".join(lines)


def build_strategist_commentary(market_data: Dict[str, Any]) -> str:
    sections = []
    sections.append("## 🧭 Strategist Commentary (Seyeon’s Filters)\n")
    sections.append(market_regime_filter(market_data))
    sections.append("")
    sections.append(liquidity_filter(market_data))
    sections.append("")
    sections.append(policy_filter_with_expectations(market_data))
    sections.append("")
    sections.append(fed_plumbing_filter(market_data))
    sections.append("")
    sections.append(high_yield_spread_filter(market_data))
    sections.append("")
    # ✅ 새 필터 끼워넣기 (Fed Plumbing 다음, Legacy 이전이 제일 자연스러움)
    sections.append(credit_stress_filter(market_data))
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
    sections.append(narrative_engine_filter(market_data))
    sections.append("")
    sections.append(divergence_monitor_filter(market_data))    
    sections.append("")
    sections.append(volatility_controlled_exposure_filter(market_data))
    sections.append("")    
    sections.append(style_tilt_filter(market_data))   
    sections.append("")    
    sections.append(factor_layer_filter(market_data))   
    sections.append("")      
    sections.append(sector_allocation_filter(market_data))  
    
    return "\n".join(sections)
