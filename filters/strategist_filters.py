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
    Upgraded Policy Filter with:
      1) Price-based policy regime (US10Y/DXY/VIX)
      2) Expectation vs Actual 'surprise' (if available)
      3) Policy Bias line (REAL_RATE + DXY + FCI) using 2-out-of-3 rule

    EXPECTATIONS can be:
      - dict: {"US10Y": x, "DXY": x, "VIX": x}  (direct forecasts)
      - list[dict]: economic calendar events from Investing.com (usually no direct forecasts for US10Y/DXY/VIX)
    """

    expectations_raw = market_data.get("EXPECTATIONS")

    def _to_float_maybe(x):
        if x is None:
            return None
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip()
        if not s or s in ("N/A", "-", "—"):
            return None
        s = s.replace(",", "").replace("%", "")
        try:
            return float(s)
        except Exception:
            return None

    # If your codebase does NOT have _dir_str, uncomment this fallback.
    # def _dir_str(d: int) -> str:
    #     return "↑" if d == 1 else ("↓" if d == -1 else "→")

    # 1) Normalize expectations into a dict (exp)
    exp: Dict[str, float] = {}
    exp_note = None

    if isinstance(expectations_raw, dict):
        exp = {k: _to_float_maybe(v) for k, v in expectations_raw.items()}
    elif isinstance(expectations_raw, list):
        # Investing economic calendar events -> typically no direct US10Y/DXY/VIX forecasts
        exp_note = f"EXPECTATIONS is a list (len={len(expectations_raw)}); no direct US10Y/DXY/VIX forecast keys found."
        exp = {}
    else:
        exp = {}

    # 2) Get actual series values
    us10y = _get_series(market_data, "US10Y")
    dxy   = _get_series(market_data, "DXY")
    vix   = _get_series(market_data, "VIX")

    def surprise_check(actual, expected):
        a = _to_float_maybe(actual)
        e = _to_float_maybe(expected)
        if a is None or e is None:
            return None
        return a - e

    us10y_s = surprise_check(us10y.get("today"), exp.get("US10Y"))
    dxy_s   = surprise_check(dxy.get("today"), exp.get("DXY"))
    vix_s   = surprise_check(vix.get("today"), exp.get("VIX"))

    # 3) Base policy signal (fallback) using direction only
    us10y_dir = _sign_from(us10y)
    dxy_dir   = _sign_from(dxy)
    vix_dir   = _sign_from(vix)

    base_regime = "POLICY MIXED (정책 신호 혼조)"
    base_reason = "금리/달러/변동성 신호가 완전히 정렬되지 않음"

    if us10y_dir == -1 and dxy_dir == -1 and vix_dir in (-1, 0):
        base_regime = "POLICY EASING (완화)"
        base_reason = "금리↓ + 달러↓ (+VIX 안정) → 완화 쪽"
    elif us10y_dir == 1 and dxy_dir == 1:
        base_regime = "POLICY TIGHTENING (긴축)"
        base_reason = "금리↑ + 달러↑ → 긴축 압력"

    # 4) If we have usable surprises, upgrade judgment
    has_surprise = (us10y_s is not None) or (dxy_s is not None) or (vix_s is not None)
    all_three    = (us10y_s is not None) and (dxy_s is not None) and (vix_s is not None)

    regime = base_regime
    rationale = base_reason

    if all_three:
        # Example logic: if US10Y surprise is negative -> easing surprise, else tightening
        regime = "POLICY EASING (Surprise-led) (서프라이즈: 완화)" if us10y_s < 0 else "POLICY TIGHTENING (Surprise-led) (서프라이즈: 긴축)"
        rationale = "기대 대비 실제(US10Y/DXY/VIX) 서프라이즈가 정책 체감 방향을 강화"
    elif has_surprise:
        rationale = "일부만 서프라이즈 계산 가능 → 기본 가격 신호 기반으로 유지"

    # -------------------------
    # 5) Policy Bias (Simple): REAL_RATE + DXY + FCI (2-out-of-3 rule)
    # -------------------------
    rr  = _get_series(market_data, "REAL_RATE")
    fci = _get_series(market_data, "FCI")

    rr_dir = _sign_from(rr)
    dxy_dir_for_bias = dxy_dir  # already computed

    # FCI is "tighter" when higher; for policy "easing-ness" we invert
    fci_raw_dir = _sign_from(fci)
    fci_dir = (-fci_raw_dir) if fci.get("today") is not None else 0  # invert only when we have data

    def _dir_kr(x: int) -> str:
        return "↑" if x == 1 else ("↓" if x == -1 else "→")

    up_cnt = sum(1 for x in (rr_dir, dxy_dir_for_bias, fci_dir) if x == 1)
    dn_cnt = sum(1 for x in (rr_dir, dxy_dir_for_bias, fci_dir) if x == -1)

    if up_cnt >= 2:
        policy_bias = "MODERATE TIGHTENING (긴축 우세)"
    elif dn_cnt >= 2:
        policy_bias = "SOFT EASING (완화 우세)"
    else:
        policy_bias = "MIXED (혼조)"

    bias_line = f"Policy Bias: {policy_bias} (Real rates {_dir_kr(rr_dir)} / DXY {_dir_kr(dxy_dir_for_bias)} / FCI {_dir_kr(fci_dir)})"

    # 6) Build report lines
    lines = []
    lines.append("### 🏛️ 3) Policy Filter (with Expectations)")
    lines.append("- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?")
    lines.append("- **추가 이유:** 정책 흐름과 반대로 움직이는 자산은 지속 가능성이 낮기 때문")
    lines.append("")
    lines.append(f"- **가격(현재) 신호:** US10Y({_dir_str(us10y_dir)}) / DXY({_dir_str(dxy_dir)}) / VIX({_dir_str(vix_dir)})")
    lines.append(f"- **{bias_line}**")

    # Expectations summary (no early return; always graceful)
    if expectations_raw is None:
        lines.append("- **Expectations:** N/A (no data attached)")
    elif isinstance(expectations_raw, list):
        lines.append(f"- **Expectations:** received economic-calendar events (len={len(expectations_raw)}), but no direct US10Y/DXY/VIX forecasts.")
        if exp_note:
            lines.append(f"  - Note: {exp_note}")
    elif isinstance(expectations_raw, dict):
        lines.append("- **Expectations:** dict received.")
    else:
        lines.append(f"- **Expectations:** unsupported type: {type(expectations_raw).__name__}")

    def fmt_surprise(x):
        if x is None:
            return "N/A"
        return f"{_fmt_num(x, 2)} (actual - expected)"

    lines.append("- **Expectations Check (Surprises):**")
    lines.append(f"  - **US10Y Surprise:** {fmt_surprise(us10y_s)}")
    lines.append(f"  - **DXY Surprise:** {fmt_surprise(dxy_s)}")
    lines.append(f"  - **VIX Surprise:** {fmt_surprise(vix_s)}")

    lines.append(f"- **판정:** **{regime}**")
    lines.append(f"- **근거:** {rationale}")

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
    return "\n".join(sections)
