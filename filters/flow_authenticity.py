# filters/flow_authenticity.py

from typing import Any, Dict


def _to_float(value, default=0.0):
    if value is None:
        return default

    if isinstance(value, dict):
        for key in ["value", "latest", "close", "price", "current"]:
            if key in value:
                return _to_float(value.get(key), default)
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _ret(today: float, prev: float) -> float:
    if today > 0 and prev > 0:
        return (today / prev) - 1
    return 0.0


def flow_authenticity_filter(market_data: Dict[str, Any]) -> str:
    """
    12.6) Flow Authenticity Filter [SHADOW]
    목적:
    - 새 자금 유입 vs 숏커버 / squeeze 가능성 추정
    - 출력 전용 (Final Exposure 영향 없음)
    """

    spx_pos = _to_float(market_data.get("SP500_POS_Z"))
    gamma = _to_float(market_data.get("DEALER_GAMMA_BIAS"))
    cta = _to_float(market_data.get("CTA_MOMENTUM_SCORE"))
    vix = _to_float(market_data.get("VIX"))
    dxy = _to_float(market_data.get("DXY"))

    credit_calm = market_data.get("credit_calm", True)

    momentum_scores = market_data.get("MOMENTUM_SCORES", {}) or {}
    xlk = _to_float(momentum_scores.get("XLK"))
    xlf = _to_float(momentum_scores.get("XLF"))
    xli = _to_float(momentum_scores.get("XLI"))

    breadth = 0
    positioning = 0
    credit = 0
    sector = 0

    spy = _to_float(market_data.get("BREADTH_SPY"))
    rsp = _to_float(market_data.get("BREADTH_RSP"))
    qqq = _to_float(market_data.get("BREADTH_QQQ"))
    qqqe = _to_float(market_data.get("BREADTH_QQQE"))

    spy_prev = _to_float(market_data.get("BREADTH_SPY_PREV"))
    rsp_prev = _to_float(market_data.get("BREADTH_RSP_PREV"))
    qqq_prev = _to_float(market_data.get("BREADTH_QQQ_PREV"))
    qqqe_prev = _to_float(market_data.get("BREADTH_QQQE_PREV"))

    breadth_note = "Sector proxy used"
    nasdaq_breadth_note = "QQQE/QQQ return data missing"

    # A) Broad market breadth: RSP return vs SPY return
    if spy > 0 and rsp > 0 and spy_prev > 0 and rsp_prev > 0:
        spy_ret = _ret(spy, spy_prev)
        rsp_ret = _ret(rsp, rsp_prev)
        spread = rsp_ret - spy_ret

        if spread >= 0.002:
            breadth += 2
            breadth_note = f"RSP-SPY return spread={spread*100:.2f}%p → broad participation"
        elif spread >= -0.003:
            breadth_note = f"RSP-SPY return spread={spread*100:.2f}%p → neutral breadth"
        else:
            breadth -= 2
            breadth_note = f"RSP-SPY return spread={spread*100:.2f}%p → narrow cap-weight leadership"
    else:
        if xlk > 0 and (xlf > 0 or xli > 0):
            breadth += 2
            breadth_note = "XLK + XLF/XLI participation → broader rotation"
        elif xlk > 0 and xlf <= 0 and xli <= 0:
            breadth -= 2
            breadth_note = "XLK only leadership → narrow rally"
        else:
            breadth_note = "No clear breadth confirmation"

    # B) Nasdaq breadth: QQQE return vs QQQ return
    if qqq > 0 and qqqe > 0 and qqq_prev > 0 and qqqe_prev > 0:
        qqq_ret = _ret(qqq, qqq_prev)
        qqqe_ret = _ret(qqqe, qqqe_prev)
        nasdaq_spread = qqqe_ret - qqq_ret

        if nasdaq_spread >= 0.002:
            breadth += 1
            nasdaq_breadth_note = (
                f"QQQE-QQQ return spread={nasdaq_spread*100:.2f}%p → broad Nasdaq participation"
            )
        elif nasdaq_spread >= -0.003:
            nasdaq_breadth_note = (
                f"QQQE-QQQ return spread={nasdaq_spread*100:.2f}%p → neutral Nasdaq breadth"
            )
        else:
            breadth -= 1
            nasdaq_breadth_note = (
                f"QQQE-QQQ return spread={nasdaq_spread*100:.2f}%p → mega-cap concentrated Nasdaq rally"
            )

    # 2) Positioning / squeeze risk
    if spx_pos > 2:
        positioning -= 2
    elif spx_pos < 0:
        positioning += 1

    if gamma > 1:
        positioning -= 1
    elif gamma < 0:
        positioning += 1

    if cta > 0:
        positioning += 1

    # 3) Credit confirmation
    if credit_calm:
        credit += 2
    else:
        credit -= 2

    # 4) Macro participation proxy
    if vix < 18:
        sector += 1

    if dxy < 103:
        sector += 1
    elif dxy > 106:
        sector -= 1

    total = breadth + positioning + credit + sector

    if total >= 4:
        label = "REAL_ACCUMULATION"
    elif total >= 1:
        label = "EARLY_ROTATION"
    elif total >= -2:
        label = "SHORT_COVERING"
    else:
        label = "SQUEEZE_FADE_RISK"

    report = f"""
### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** {total}
- **Label:** {label}
- **Breadth / Participation:** {breadth}
- **Breadth Note:** {breadth_note}
- **Nasdaq Breadth Note:** {nasdaq_breadth_note}
- **Positioning / Gamma:** {positioning}
- **Credit Confirmation:** {credit}
- **Macro Participation:** {sector}

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.
"""

    return report