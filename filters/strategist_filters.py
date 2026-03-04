from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import math

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


from typing import Dict, Any, Optional, List, Tuple

# -------------------------------------------------------------------
# 6.5) Correlation Break Monitor (v1.2)
# - Adds: TECH_PROXY + SPY (optional) based "Structural Break" signals
# - Still works when TECH_PROXY/SPY missing (falls back to credit/USD)
# - Assumes market_data is produced by build_market_data()
#   where each key looks like:
#     market_data["US10Y"] = {"today": float, "prev": float|None, "pct_change": float|None, ...}
# -------------------------------------------------------------------

from typing import Dict, Any, Optional

def correlation_break_filter(market_data: Dict[str, Any]) -> str:
    """
    Correlation Break Monitor (v2)
    Detects: "things that should move together but diverge" with thresholds
    - Uses QQQ (TECH_PROXY) and SPY if available
    - Falls back to XLK / credit / FX proxies
    - Avoids false positives on flat days (0.0 moves)
    """

    def pct(key: str) -> Optional[float]:
        v = market_data.get(key, {}) or {}
        x = v.get("pct_change")
        try:
            return None if x is None else float(x)
        except Exception:
            return None

    def signif(x: Optional[float], thr: float) -> bool:
        return (x is not None) and (abs(x) >= thr)

    # --- pull core pct changes ---
    us10y = pct("US10Y")
    dxy = pct("DXY")
    vix = pct("VIX")
    usdkrw = pct("USDKRW")
    hyg = pct("HYG")
    lqd = pct("LQD")

    # --- tech / broad equity proxies ---
    # Preferred: QQQ & SPY (from macro_data.csv)
    qqq = pct("QQQ")
    spy = pct("SPY")

    # Fallback for tech if QQQ missing
    xlk = pct("XLK")
    tech = qqq if qqq is not None else xlk  # tech proxy

    # liquidity dir (from liquidity layer)
    net_liq = market_data.get("NET_LIQ", {}) or {}
    net_liq_dir = str(net_liq.get("dir", "N/A")).upper()

    # --- thresholds (tune later, safe defaults now) ---
    # US10Y is in % change terms already (your build_market_data uses pct_change)
    THR_US10Y = 0.10     # 0.10% move 이상일 때만 "금리 의미있게 움직임"
    THR_DXY   = 0.15
    THR_VIX   = 1.00     # VIX는 잘 튀니 1% 이상만 의미
    THR_EQ    = 0.25     # QQQ/SPY/XLK 같은 ETF는 0.25% 이상만
    THR_FX    = 0.15
    THR_CREDIT= 0.20

    breaks = []
    interp = []

    # --- DEBUG line (원하면 유지, 싫으면 삭제) ---
    lines = []
    lines.append("### ⚠ 6.5) Correlation Break Monitor")
    if market_data.get("_STALE"):
        lines.append("⚠ Market Closed / Stale Data → Correlation signals muted.")
        lines.append("")
        lines.append(f"- DEBUG: US10Y={us10y}, TECH(qqq/xlk)={tech}, SPY={spy}")

    # If missing key proxies, note (but still run other checks)
    notes = []
    if tech is None:
        notes.append("TECH_PROXY(QQQ/XLK) not available")
    if spy is None:
        notes.append("SPY not available")
    if notes:
        lines.append(f"- **Note:** {', '.join(notes)} → using available proxies (credit/USD/FX).")
        lines.append("")

    # ------------------------------------------------------------
    # A) Rates vs Tech / Broad (대표 공식: 금리↑ => 기술/주식 부담)
    # ------------------------------------------------------------
    if signif(us10y, THR_US10Y):
        # 금리↑인데 기술↑ => "금리보다 성장 내러티브/매수세가 더 강함"
        if us10y > 0 and signif(tech, THR_EQ) and tech > 0:
            breaks.append("US10Y ↑ but Technology ↑ (QQQ/XLK)")
            interp.append("할인율 역풍에도 기술이 강함 → 성장 내러티브/강한 매수세가 금리 부담을 상쇄")
        # 금리↑인데 SPY↑ => 시장 전체가 금리 역풍을 무시
        if us10y > 0 and signif(spy, THR_EQ) and spy > 0:
            breaks.append("US10Y ↑ but SPY ↑")
            interp.append("금리 역풍에도 시장이 상승 → ‘성장/실적/유동성 기대’가 금리보다 우위일 수 있음")
        # 금리↓인데 기술↓ => 금리보다 ‘실적/리스크’가 더 중요
        if us10y < 0 and signif(tech, THR_EQ) and tech < 0:
            breaks.append("US10Y ↓ but Technology ↓ (QQQ/XLK)")
            interp.append("금리 완화에도 기술 약세 → 금리보다 실적/규제/리스크 요인이 우위 (퀄리티 중심)")

    # ------------------------------------------------------------
    # B) VIX vs Equity (대표 공식: VIX↑ => 주식↓)
    # ------------------------------------------------------------
    if signif(vix, THR_VIX):
        if vix > 0 and signif(spy, THR_EQ) and spy > 0:
            breaks.append("VIX ↑ but SPY ↑")
            interp.append("공포 신호에도 시장이 상승 → 옵션/헤지 포지션 꼬임, 숏이 위험해질 수 있음")
        if vix > 0 and signif(tech, THR_EQ) and tech > 0:
            breaks.append("VIX ↑ but Technology ↑ (QQQ/XLK)")
            interp.append("변동성 상승에도 기술이 강함 → 테마 주도/숏커버/수급 왜곡 가능")

    # ------------------------------------------------------------
    # C) Dollar vs Risk (대표 공식: 달러↑ => 위험자산 압박)
    # ------------------------------------------------------------
    if signif(dxy, THR_DXY):
        if dxy > 0 and signif(spy, THR_EQ) and spy > 0:
            breaks.append("DXY ↑ but SPY ↑")
            interp.append("달러 강세(리스크 압박)에도 시장 강함 → 강한 매수/테마 드라이브 가능 (숏 신중)")
        if dxy > 0 and signif(hyg, THR_CREDIT) and hyg > 0:
            breaks.append("DXY ↑ but HYG ↑")
            interp.append("달러 강세에도 하이일드 강세 → 리스크 선호가 버티는 국면 (포지션 꼬임 주의)")

    # ------------------------------------------------------------
    # D) KRW weakness vs VIX (국지적 FX 스트레스 vs 변동성)
    # ------------------------------------------------------------
    if signif(usdkrw, THR_FX) and usdkrw > 0:
        if vix is not None and vix < 0:
            breaks.append("USDKRW ↑ (KRW↓) but VIX ↓")
            interp.append("원화 약세에도 변동성은 눌림 → 수급 요인/국지적 FX 스트레스 가능 (공격적 숏 보류)")

    # ------------------------------------------------------------
    # E) Liquidity vs Credit proxy (NET_LIQ↓인데 위험크레딧 강함 등)
    # ------------------------------------------------------------
    if net_liq_dir == "DOWN":
        # HYG↑ & LQD↓ 조합은 애매하지만, ‘리스크 크레딧 선호’ 신호로 사용
        if signif(hyg, THR_CREDIT) and signif(lqd, THR_CREDIT) and hyg > 0 and lqd < 0:
            breaks.append("Liquidity ↓ but Credit Risk Appetite ↑ (HYG↑ / LQD↓)")
            interp.append("유동성 흡수에도 하이일드가 버팀 → 포지셔닝/리스크 선호가 생각보다 강할 수 있음")

    # -------------------------
    # Output
    # -------------------------
    if breaks:
        lines.append("")
        lines.append("Correlation Break Detected:")
        for b in breaks:
            lines.append(f"- {b}")
        lines.append("")
        lines.append("So What?")
        for i in interp[:6]:
            lines.append(f"- {i}")
        lines.append("- 결론: **공식이 깨진 구간** → 방향 베팅보다 **사이징 보수적 + 퀄리티/리더 중심**")
    else:
        lines.append("")
        lines.append("No significant correlation break detected.")

    return "\n".join(lines)

# -------------------------------------------------------------------
# 6.6) Sector Correlation Break Monitor (v1.1)
# - FIX: missing based on today's pct(None), not key existence
# - If one sector ETF missing, still runs other rules and prints result
# -------------------------------------------------------------------

def sector_correlation_break_filter(market_data: Dict[str, Any]) -> str:
    """
    Sector Correlation Break Monitor (v1.1)
    Detects: expected macro→sector relationships breaking.
    - Robust when some sector ETFs have missing today's values (pct_change=None).
    """

    def pct(key: str) -> Optional[float]:
        v = market_data.get(key, {}) or {}
        x = v.get("pct_change")
        try:
            return None if x is None else float(x)
        except Exception:
            return None

    us10y = pct("US10Y")
    wti = pct("WTI")
    dxy = pct("DXY")
    vix = pct("VIX")

    xlk = pct("XLK")    # Tech
    xlf = pct("XLF")    # Financials
    xle = pct("XLE")    # Energy
    xlre = pct("XLRE")  # Real Estate

    lines: List[str] = []
    lines.append("### ⚠ 6.6) Sector Correlation Break Monitor")
    lines.append(f"- DEBUG: pct XLK={xlk}, XLF={xlf}, XLE={xle}, XLRE={xlre}")
    
    if market_data.get("_STALE"):
        lines.append("⚠ Market Closed / Stale Data → Sector signals muted.")
        lines.append("")
    # ✅ FIX: "키"가 아니라 "오늘 pct 값(None)" 기준으로 missing 표시
    missing_today = [k for k, v in [("XLK", xlk), ("XLF", xlf), ("XLE", xle), ("XLRE", xlre)] if v is None]
    if missing_today:
        lines.append(f"- **Note:** sector ETFs missing today values: {', '.join(missing_today)}")
        lines.append("")  # 그래도 계속 진행 (없는 애 관련 rule만 스킵)

    breaks: List[str] = []
    so_what: List[str] = []

    # --- Rule 1: Rates ↑ should support Financials (often), hurt Real Estate/Tech duration ---
    if us10y is not None:
        if us10y > 0:
            if xlf is not None and xlf < 0:
                breaks.append("US10Y ↑ but XLF ↓ (Financials)")
                so_what.append("금리 상승에도 금융 약세 → NIM 기대보다 경기/신용 우려가 더 큼 (포지션 과신 금지)")
            if xlre is not None and xlre > 0:
                breaks.append("US10Y ↑ but XLRE ↑ (Real Estate)")
                so_what.append("금리 역풍에도 리츠 강세 → 배당/수급 요인이 금리 부담을 상쇄 (숏 신중)")
            if xlk is not None and xlk > 0:
                breaks.append("US10Y ↑ but XLK ↑ (Tech)")
                so_what.append("할인율 역풍에도 기술 강세 → 성장 내러티브/매수세 우위 (고밸류 숏 신중)")
        elif us10y < 0:
            # rates down usually helps duration; if Tech down anyway -> growth narrative weak / earnings risk
            if xlk is not None and xlk < 0:
                breaks.append("US10Y ↓ but XLK ↓ (Tech)")
                so_what.append("금리 하락에도 기술 약세 → 금리보다 실적/성장 우려가 더 큼 (퀄리티만)")

    # --- Rule 2: Oil ↑ should support Energy ---
    if wti is not None and wti > 0:
        if xle is not None and xle < 0:
            breaks.append("WTI ↑ but XLE ↓ (Energy)")
            so_what.append("유가 상승에도 에너지 약세 → 수요 둔화/정책 리스크가 더 큼 (에너지 비중 과신 금지)")

    # --- Rule 3: Risk-off (VIX ↑ or DXY ↑) usually pressures cyclicals / supports defensives ---
    if vix is not None and vix > 0:
        if xlf is not None and xlf > 0:
            breaks.append("VIX ↑ but XLF ↑ (Financials)")
            so_what.append("공포 신호에도 금융 강세 → 포지셔닝/수급 왜곡 가능 (추격매수보다 확인)")
    if dxy is not None and dxy > 0:
        if xlk is not None and xlk > 0:
            breaks.append("DXY ↑ but XLK ↑ (Tech)")
            so_what.append("달러 강세(리스크 압박)에도 기술 강세 → 강한 매수/테마 드라이브 가능 (숏 신중)")

    if breaks:
        lines.append("Correlation Break Detected:")
        for b in breaks:
            lines.append(f"- {b}")
        lines.append("")
        lines.append("So What?")
        for s in so_what[:6]:
            lines.append(f"- {s}")
        lines.append("- 결론: **섹터 ‘공식’이 깨진 구간** → 방향 베팅보다 **사이징 축소 + 리더 중심**")
    else:
        lines.append("No significant sector-level correlation break detected.")

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



# filters/strategist_filters.py (어딘가 상단 상수 구간)

# filters/strategist_filters.py (상단 상수 구간)

GEO_WINDOW = 60  # 60~90 중 선택(백필 히스토리 있으니 60 추천)

# (key, weight, transform)
# transform: "normal" | "inverse"
# - inverse 예: USDJPY는 USDJPY 하락(=JPY강세)=risk-off니까 inverse가 합리적
GEO_FACTORS = [
    # -----------------------
    # Market Reaction (confirmation)
    # -----------------------
    ("VIX",        0.18, "normal"),
    ("WTI",        0.10, "normal"),
    ("GOLD",       0.12, "normal"),
    ("USDCNH",     0.18, "normal"),

    # -----------------------
    # EM Stress (capital flight)
    # -----------------------
    ("EEM",        0.10, "inverse"),  # EEM 하락 = risk-off
    ("EMB",        0.12, "inverse"),  # EMB 하락 = risk-off
    ("USDMXN",     0.05, "normal"),   # USD/MXN 상승(페소 약세) = stress
    ("USDJPY",     0.05, "inverse"),  # USDJPY 하락(엔 강세)=risk-off

    # -----------------------
    # Supply Chain / Shipping proxy (early)
    # -----------------------
    ("SEA",        0.05, "inverse"),  # SEA 하락을 stress로 볼지(공급망 붕괴) 케이스가 있어 inverse로 시작
    ("BDRY",       0.05, "normal"),   # BDRY는 케이스별. v2에서는 일단 normal로 두고 관찰

    # -----------------------
    # Defense attention proxy (early)
    # -----------------------
    ("ITA",        0.03, "normal"),
    ("XAR",        0.02, "normal"),

    # -----------------------
    # Sovereign stress (CDS proxy via 10Y spread vs US)
    # - sovereign_spreads.csv에 컬럼이 존재해야 함
    # - key 이름은 "XX10Y_SPREAD" 규칙 (yield - US yield)
    # -----------------------
    ("KR10Y_SPREAD", 0.10, "normal"),
    ("JP10Y_SPREAD", 0.06, "normal"),
    ("CN10Y_SPREAD", 0.06, "normal"),
    ("IL10Y_SPREAD", 0.08, "normal"),
    ("TR10Y_SPREAD", 0.05, "normal"),
]

# score -> level 구간
GEO_THRESHOLDS = [
    ("NORMAL",   -0.75, 0.75),
    ("ELEVATED",  0.75, 1.50),
    ("HIGH",      1.50, 2.50),
    ("CONFLICT",  2.50, 99.0),
]

def _to_num(x) -> Optional[float]:
    v = pd.to_numeric(x, errors="coerce")
    return None if pd.isna(v) else float(v)


def _pct_series_from_df(df: pd.DataFrame, col: str) -> pd.Series:
    """
    df[col]에서 % 변화(전일 대비)를 시계열로 만듦.
    결측/스키마변경에도 견고하게.
    """
    s = pd.to_numeric(df[col], errors="coerce")
    s = s.dropna()
    # pct_change는 (t - t-1)/t-1 * 100
    return s.pct_change() * 100.0


def _zscore_last(s: pd.Series, window: int) -> Optional[float]:
    """
    Rolling z-score의 마지막 값을 반환.
    ✅ 핵심: 새로 추가된 컬럼(히스토리 짧음)도 계산되도록 최소 샘플 수를 허용.
    """
    if s is None:
        return None

    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return None

    # 최근 window만
    x = s.tail(window).dropna()
    if len(x) < 5:
        # ✅ 히스토리 너무 짧으면 아직은 스킵
        return None

    mu = float(x.mean())
    sd = float(x.std(ddof=0))

    last = float(x.iloc[-1])
    if sd == 0:
        return 0.0
    return (last - mu) / sd

from typing import Dict, Any, Optional, List, Tuple
import pandas as pd

def attach_geopolitical_ew_layer(
    market_data: Dict[str, Any],
    df: pd.DataFrame,
    today_idx: int,
    window: int = GEO_WINDOW,
) -> Dict[str, Any]:
    """
    GEO Early Warning composite score를 market_data["GEO_EW"]에 저장.
    - df 기반 rolling z-score
    - 없는 팩터는 스킵 (가중치 재정규화)
    - USDJPY는 inverse 처리 (USDJPY 하락 = risk-off)

    ✅ v2 업그레이드:
    - sovereign_spreads.csv를 df2에 merge해서 CDS proxy(국채 스프레드)를 GEO_FACTORS에 포함 가능
    - *_SPREAD 키는 pct_change가 아니라 "level z-score"로 처리 (스프레드는 레벨이 더 의미있음)
    """

    if market_data is None:
        market_data = {}

    # -----------------------------------------
    # 0) Build df2 (until today)
    # -----------------------------------------
    df2 = df.iloc[: today_idx + 1].copy()

    # -----------------------------------------
    # ✅ 0.5) Merge sovereign spreads into df2
    # -----------------------------------------
    try:
        sov = load_sovereign_spreads_df()  # <- 너가 이미 만들었다고 한 함수
        if sov is not None and not sov.empty and "date" in sov.columns:
            sov2 = sov.copy()
            sov2["date"] = pd.to_datetime(sov2["date"], errors="coerce")
            sov2 = sov2.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")

            # df2 date normalize
            if "date" in df2.columns:
                df2["date"] = pd.to_datetime(df2["date"], errors="coerce")

            # 필요한 컬럼만 합치기 (존재하는 것만)
            wanted_cols = ["date"]
            for c in ["KR10Y_SPREAD", "JP10Y_SPREAD", "CN10Y_SPREAD", "IL10Y_SPREAD", "TR10Y_SPREAD", "DE10Y_SPREAD", "GB10Y_SPREAD"]:
                if c in sov2.columns:
                    wanted_cols.append(c)

            if len(wanted_cols) > 1:
                df2 = pd.merge(df2, sov2[wanted_cols], on="date", how="left")
                # sovereign spread는 매일 안 나올 수 있으니 ffill로 정렬
                for c in wanted_cols:
                    if c != "date":
                        df2[c] = pd.to_numeric(df2[c], errors="coerce").ffill()
    except Exception:
        # merge 실패해도 GEO는 계속 돌아가야 함
        pass

    # -----------------------------------------
    # Helpers (local)
    # -----------------------------------------
    def _zscore_last_level(series: pd.Series, win: int) -> Optional[float]:
        s = pd.to_numeric(series, errors="coerce").dropna()
        if len(s) < max(10, min(win, 20)):
            return None
        tail = s.tail(win)
        mu = float(tail.mean())
        sd = float(tail.std(ddof=0))
        if sd == 0:
            return None
        return float((tail.iloc[-1] - mu) / sd)

    def _series_level_from_df(df_: pd.DataFrame, key: str) -> pd.Series:
        return pd.to_numeric(df_.get(key), errors="coerce")

    # -----------------------------------------
    # 1) Compute score
    # -----------------------------------------
    components: List[Dict[str, Any]] = []
    missing: List[str] = []

    raw_score = 0.0
    used_weight = 0.0

    # ✅ GEO_FACTORS 호환:
    # - 기존: (key, w, transform)
    # - 확장: (key, w, transform, mode) where mode in {"pct","level"}
    #   * mode 생략 시:
    #       - key가 *_SPREAD 이면 level
    #       - 그 외는 pct
    for item in GEO_FACTORS:
        if not isinstance(item, (list, tuple)) or len(item) < 3:
            continue

        key = item[0]
        w = item[1]
        transform = item[2]
        mode = None
        if len(item) >= 4:
            mode = item[3]

        if mode is None:
            mode = "level" if str(key).endswith("_SPREAD") else "pct"

        if key not in df2.columns:
            missing.append(key)
            continue

        # mode별 zscore 계산
        z = None
        if mode == "level":
            level_series = _series_level_from_df(df2, key)
            z = _zscore_last_level(level_series, window)
        else:
            pct = _pct_series_from_df(df2, key)  # 기존 너 프로젝트 함수 그대로 사용
            z = _zscore_last(pct, window)

        if z is None:
            missing.append(key)
            continue

        # transform
        z_used = -z if transform == "inverse" else z

        contrib = float(w) * float(z_used)
        raw_score += contrib
        used_weight += float(w)

        components.append({
            "key": key,
            "weight": float(w),
            "z": float(z),
            "z_used": float(z_used),
            "contrib": float(contrib),
            "transform": transform,
            "mode": mode,  # ✅ NEW: pct vs level
        })

    score = (raw_score / used_weight) if used_weight > 0 else None

    # level
    level = "N/A"
    if score is not None:
        for name, lo, hi in GEO_THRESHOLDS:
            if score >= lo and score < hi:
                level = name
                break

    market_data["GEO_EW"] = {
        "score": score,
        "level": level,
        "window": window,
        "used_weight": used_weight,
        "missing": missing,
        "components": components,
    }

    return market_data

def geopolitical_early_warning_filter(market_data: Dict[str, Any]) -> str:
    """
    리포트 출력용 문자열
    """
    geo = (market_data.get("GEO_EW") or {})
    score = geo.get("score")
    level = geo.get("level", "N/A")
    missing = geo.get("missing", [])
    comps = geo.get("components", [])

    lines = []
    lines.append("### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)")
    if market_data.get("_STALE"):
        lines.append("⚠ Market Closed / Stale Data → Price-based geo signals muted.")
        lines.append("")
    
    if score is None:
        lines.append("- **Status:** N/A (insufficient data)")
        if missing:
            lines.append(f"- **Missing/Insufficient:** {', '.join(missing)}")
        lines.append("- **So What?:** 데이터가 쌓이거나 지표가 추가되면 조기경보 점수를 계산합니다.")
        return "\n".join(lines)

    lines.append(f"- **Geo Stress Score (z-composite):** **{score:+.2f}**  *(Level: {level})*")

    # top contributors
    comps_sorted = sorted(comps, key=lambda x: abs(float(x.get("contrib", 0.0))), reverse=True)
    top = comps_sorted[:4]

    lines.append("- **Top Drivers:**")
    for c in top:
        lines.append(
            f"  - {c['key']}: z_used={c['z_used']:+.2f} (w={c['weight']:.2f}) → contrib={c['contrib']:+.2f}"
        )

    if missing:
        lines.append(f"- **Missing/Skipped:** {', '.join(missing)}")

    # So What template (level-based)
    lines.append("")
    lines.append("**So What?**")
    if level in ("NORMAL",):
        lines.append("- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.")
    elif level in ("ELEVATED",):
        lines.append("- 조기경보 ‘상승’ 구간: **사이징 보수적**, 이벤트 리스크(중동/중국/EM) 헤지 후보 점검.")
    elif level in ("HIGH",):
        lines.append("- 스트레스 ‘높음’: **리스크 익스포저 축소 준비**, EM/고베타/레버리지 노출 점검.")
    else:  # EXTREME
        lines.append("- 스트레스 ‘극단’: **디레버리징 + 방어자산/헤지 우선**, 갭리스크 대비(현금/단기)")

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


from typing import Dict, Any, Optional

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
    liq_level_bucket = str(
        net_liq.get("level_bucket") or market_data.get("NET_LIQ_LEVEL_BUCKET") or "N/A"
    ).upper()
    if liq_level_bucket not in ("HIGH", "MID", "LOW"):
        liq_level_bucket = "N/A"

    phase = market_data.get("MARKET_REGIME", "N/A")
    phase_upper = str(phase).upper()

    policy_upper = policy_bias_line.upper()
    mixed = "MIXED" in policy_upper
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
    # ✅ If explicitly mixed, don't apply easing/tightening tilt
    if not mixed:
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

    # ✅ FIX v1.1: If policy line explicitly says MIXED, force MIXED
    struct_tag = "MIXED"
    if not mixed:
        if easing and not tightening:
            struct_tag = "EASING"
        elif tightening and not easing:
            struct_tag = "TIGHTENING"

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
    # ... Narrative Engine이 FINAL_STATE를 market_data에 넣은 뒤

    
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
        mixed = "MIXED" in policy_upper
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

from typing import Dict, Any, List, Tuple, Optional

def sector_allocation_filter(market_data: Dict[str, Any]) -> str:
    """
    Sector Allocation Engine (v2)
    - FINAL_STATE(phase/structure/liquidity/credit) 기반으로
      Overweight/Underweight를 최소 1개 이상 생성
    - 결과는 market_data["SECTOR_TILT"]에 저장 (다른 레이어에서도 재사용 가능)

    섹터 기준: GICS 11
    Tech, Financials, Energy, Industrials, Materials,
    Consumer Discretionary, Consumer Staples,
    Health Care, Utilities, Real Estate, Communication Services
    """

    state = market_data.get("FINAL_STATE", {}) or {}

    phase = str(state.get("phase", "N/A")).upper()
    structure = str(state.get("structure_tag", "MIXED")).upper()  # EASING/TIGHTENING/MIXED
    liq_dir = str(state.get("liquidity_dir", "N/A")).upper()      # UP/DOWN/FLAT/N/A
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A")).upper()  # HIGH/MID/LOW/N/A
    credit_calm = state.get("credit_calm", None)                  # True/False/None

    # --------------------------------------------------
    # Scoring map (rule-based)
    # --------------------------------------------------
    sectors = [
        "Technology",
        "Financials",
        "Energy",
        "Industrials",
        "Materials",
        "Consumer Discretionary",
        "Consumer Staples",
        "Health Care",
        "Utilities",
        "Real Estate",
        "Communication Services",
    ]

    score = {s: 0 for s in sectors}
    reasons = {s: [] for s in sectors}

    def add(s: str, pts: int, why: str):
        score[s] += pts
        reasons[s].append(f"{'+' if pts>0 else ''}{pts}: {why}")

    # -------------------------
    # A) Liquidity rules (가장 중요)
    # -------------------------
    liq_tight = (liq_dir == "DOWN") or (liq_lvl == "LOW")
    liq_easy = (liq_dir == "UP") and (liq_lvl in ("MID", "HIGH"))

    if liq_tight:
        # Quality/Defensive 선호
        add("Consumer Staples", +3, "유동성 흡수 → 방어/필수소비 선호")
        add("Health Care", +3, "유동성 흡수 → 현금흐름 안정 섹터 선호")
        add("Utilities", +2, "유동성 흡수 → 방어적 수요(단, 금리 민감)")
        # High beta / long-duration 압박
        add("Technology", -3, "유동성 흡수 → 고베타/장기듀레이션 부담")
        add("Consumer Discretionary", -2, "유동성 흡수 → 경기민감 소비 압박")
        add("Real Estate", -2, "유동성 흡수 → 레버리지/금리 민감도 부담")
    elif liq_easy:
        # Cyclical/High beta 확장
        add("Technology", +2, "유동성 공급 → 베타 확장 환경")
        add("Consumer Discretionary", +2, "유동성 공급 → 경기민감 섹터 우호")
        add("Industrials", +2, "유동성 공급 → 경기순환(투자/생산) 우호")
        add("Financials", +1, "유동성 공급 → 리스크 선호 회복 구간 우호")
        # Defensive는 상대 약화
        add("Consumer Staples", -1, "유동성 공급 → 방어 섹터 상대매력 감소")
        add("Utilities", -1, "유동성 공급 → 방어 섹터 상대매력 감소")
    else:
        # Mixed liquidity -> barbell
        add("Health Care", +1, "유동성 혼조 → 퀄리티 선호 잔존")
        add("Consumer Staples", +1, "유동성 혼조 → 방어적 바벨 한 축")
        add("Industrials", +1, "유동성 혼조 → 선별적 경기순환")

    # -------------------------
    # B) Structure rules (금리/할인율)
    # -------------------------
    if structure == "TIGHTENING":
        # Long-duration 압박
        add("Technology", -2, "긴축 → 할인율↑ → 장기듀레이션 멀티플 압박")
        add("Communication Services", -1, "긴축 → 성장/멀티플 부담")
        add("Real Estate", -2, "긴축 → 금리 민감/레버리지 비용 부담")
        add("Utilities", -1, "긴축 → 채권 대체재 성격(듀레이션) 부담")
        # Value/Financials 상대 우위 가능
        add("Financials", +2, "긴축/고금리 → NIM/금리 환경 우호 가능")
        add("Energy", +1, "인플레/공급 변수 시 방어적 인플레 헤지 성격")
    elif structure == "EASING":
        add("Technology", +2, "완화 → 할인율↓ → 멀티플 확장 여지")
        add("Communication Services", +1, "완화 → 성장주 우호")
        add("Real Estate", +1, "완화 → 금리 민감 섹터 완화")
        add("Utilities", +1, "완화 → 배당/방어 매력 회복")
    else:
        # MIXED
        add("Financials", +1, "정책 혼조 → 가치/캐리 성격 일부 유지")
        add("Health Care", +1, "정책 혼조 → 퀄리티 선호")

    # -------------------------
    # C) Credit rules (스프레드/조달환경)
    # -------------------------
    if credit_calm is True:
        add("Industrials", +1, "크레딧 안정 → 경기순환/기업활동 리스크 완화")
        add("Materials", +1, "크레딧 안정 → 실물/투자 사이클 방어")
        add("Financials", +1, "크레딧 안정 → 금융 스트레스 제한")
    elif credit_calm is False:
        add("Financials", -2, "크레딧 불안 → 금융 스트레스/리스크 관리 우선")
        add("Real Estate", -2, "크레딧 불안 → 레버리지 민감 섹터 취약")
        add("Consumer Discretionary", -1, "크레딧 불안 → 소비/경기 민감 부담")
        add("Consumer Staples", +1, "크레딧 불안 → 방어 섹터 선호 강화")
        add("Health Care", +1, "크레딧 불안 → 방어/퀄리티 선호 강화")

    # -------------------------
    # D) Phase rules (risk-on/off flavor)
    # -------------------------
    if "RISK-OFF" in phase:
        add("Consumer Staples", +2, "리스크오프 → 방어 섹터 선호")
        add("Health Care", +2, "리스크오프 → 퀄리티 선호")
        add("Technology", -2, "리스크오프 → 고베타 부담")
        add("Consumer Discretionary", -2, "리스크오프 → 경기민감 부담")
    elif "RISK-ON" in phase:
        add("Industrials", +1, "리스크온 → 경기순환 선호")
        add("Financials", +1, "리스크온 → 위험선호 구간 우호")
        add("Technology", +1, "리스크온 → 성장/베타 회복")
    elif "EVENT" in phase or "WATCH" in phase:
        # 관망 구간은 extremes 줄이고 퀄리티로
        add("Health Care", +1, "이벤트 관망 → 방어/퀄리티 선호")
        add("Consumer Staples", +1, "이벤트 관망 → 변동성 낮은 섹터 선호")

    # --------------------------------------------------
    # Pick Over/Under (at least 1)
    # --------------------------------------------------
    ranked = sorted(sectors, key=lambda s: score[s], reverse=True)
    over = [s for s in ranked if score[s] > 0][:3]
    under = [s for s in reversed(ranked) if score[s] < 0][:3]

    # Safety: ensure not empty
    if not over:
        over = ranked[:2]
    if not under:
        under = list(reversed(ranked))[:2]

    # store for other layers
    market_data["SECTOR_TILT"] = {
        "overweight": over,
        "underweight": under,
        "scores": score,
        "context": {
            "phase": phase,
            "structure": structure,
            "liquidity": f"{liq_dir}-{liq_lvl}",
            "credit_calm": credit_calm,
        }
    }

    # --------------------------------------------------
    # Output block
    # --------------------------------------------------
    def fmt_list(xs: List[str]) -> str:
        return ", ".join(xs) if xs else "None"

    context_line = f"phase={phase or 'N/A'} / liquidity={liq_dir}-{liq_lvl} / structure={structure} / credit_calm={credit_calm}"

    lines = []
    lines.append("### 🏭 18) Sector Allocation Engine (v2)")
    lines.append("- **정의:** Macro + Style/Factor/FINAL_STATE 종합 섹터 기울기 판단 (rule-based scoring)")
    lines.append("- **추가 이유:** 리포트의 최종 output(포지셔닝)이 비어있지 않도록, 최소 OW/UW를 항상 생성")
    lines.append("")
    lines.append(f"- **Context:** {context_line}")
    lines.append(f"- **Overweight:** **{fmt_list(over)}**")
    lines.append(f"- **Underweight:** **{fmt_list(under)}**")
    lines.append("")

    # add brief rationale: top 1 reason per sector
    lines.append("- **Rationale (top drivers):**")
    for s in over:
        top = reasons[s][0] if reasons[s] else "rule-based tilt"
        lines.append(f"  - OW {s}: {top}")
    for s in under:
        top = reasons[s][0] if reasons[s] else "rule-based tilt"
        lines.append(f"  - UW {s}: {top}")

    return "\n".join(lines)


# filters/execution_layer.py
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

def execution_layer_filter(market_data: Dict[str, Any]) -> str:
    """
    Execution / Style Translation Layer (v1.1)

    목적:
    - 섹터(18) + FINAL_STATE(13) 기반으로 "구현용 기업 타입 체크리스트"를 출력
    - Risk stance / exposure 퍼센트 / HOLD 반복 금지 (Decision Layer 영역)
    """

    state = market_data.get("FINAL_STATE", {}) or {}

    structure = str(state.get("structure_tag", "MIXED")).upper()
    liq_dir = str(state.get("liquidity_dir", "N/A")).upper()
    liq_lvl = str(state.get("liquidity_level_bucket", "N/A")).upper()
    credit_calm = state.get("credit_calm", None)

    # (선택) 18번 결과가 market_data에 저장돼 있다면 가져오기
    # v2 섹터엔진에서 아래 키로 저장하도록 맞추면 좋음:
    # market_data["SECTOR_OW"] = [...]
    # market_data["SECTOR_UW"] = [...]
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

def apply_geo_overlay_to_final_state(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Geo EW를 FINAL_STATE 위에 'overlay'로 반영.

    - Narrative Engine이 만든 FINAL_STATE를 보수적으로 조정
    - risk_budget / risk_action 조정
    - 조정 내역을 market_data["GEO_OVERLAY"]에 기록
    """

    if market_data is None:
        return market_data

    state = market_data.get("FINAL_STATE", {}) or {}
    geo = market_data.get("GEO_EW", {}) or {}

    level = str(geo.get("level", "N/A")).upper()
    score = geo.get("score", None)

    # 주말 / 휴장 감지
    is_stale = bool(market_data.get("_STALE", False))

    base_budget = state.get("risk_budget", None)
    base_action = str(state.get("risk_action", "HOLD"))

    overlay = {
        "level": level,
        "score": score,
        "stale": is_stale,
        "base_budget": base_budget,
        "base_action": base_action,
        "budget_delta": 0,
        "final_budget": base_budget,
        "final_action": base_action,
        "note": "",
    }

    # -------------------------
    # Geo Penalty Rules
    # -------------------------
    penalty_map = {
        "NORMAL": 0,
        "ELEVATED": -10,
        "HIGH": -20,
        "CONFLICT": -25,
    }

    penalty = penalty_map.get(level, 0)

    # 주말이면 신호 반감
    if is_stale and penalty != 0:
        penalty = int(penalty / 2)

    # -------------------------
    # Budget Adjustment
    # -------------------------
    if isinstance(base_budget, int):

        new_budget = max(0, min(100, base_budget + penalty))

        overlay["budget_delta"] = penalty
        overlay["final_budget"] = new_budget

        state["risk_budget"] = new_budget

        # -------------------------
        # Action Conservative Shift
        # -------------------------
        if level in ("ELEVATED", "HIGH", "CONFLICT"):

            if base_action == "INCREASE":
                state["risk_action"] = "HOLD"
                overlay["final_action"] = "HOLD"

            elif base_action == "HOLD" and level in ("HIGH", "CONFLICT"):
                state["risk_action"] = "REDUCE"
                overlay["final_action"] = "REDUCE"

        overlay["note"] = f"GeoEW={level} overlay applied ({penalty}% budget adj)"

    else:

        overlay["note"] = (
            f"GeoEW={level} detected but base_budget not int → no budget change"
        )

    market_data["FINAL_STATE"] = state
    market_data["GEO_OVERLAY"] = overlay

    return market_data
    

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
    sections.append(correlation_break_filter(market_data))
    sections.append("")
    sections.append(sector_correlation_break_filter(market_data)) # ✅ 6.6 추가
    sections.append("")
    sections.append(risk_exposure_filter(market_data))
    sections.append("")
    sections.append(geopolitical_early_warning_filter(market_data))
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
    sections.append("")
    sections.append(execution_layer_filter(market_data))
    sections.append("")
    
    return "\n".join(sections)
