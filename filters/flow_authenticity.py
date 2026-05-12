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

    breadth_note = "Sector proxy used"
    nasdaq_breadth_note = "QQQE/QQQ data missing"

    # A) Broad market breadth: RSP/SPY
    if spy > 0 and rsp > 0:
        rsp_spy_ratio = rsp / spy

        if rsp_spy_ratio >= 0.99:
            breadth += 2
            breadth_note = f"RSP/SPY={rsp_spy_ratio:.3f} → broad participation"
        elif rsp_spy_ratio >= 0.96:
            breadth_note = f"RSP/SPY={rsp_spy_ratio:.3f} → neutral breadth"
        else:
            breadth -= 2
            breadth_note = f"RSP/SPY={rsp_spy_ratio:.3f} → narrow cap-weight leadership"
    else:
        if xlk > 0 and (xlf > 0 or xli > 0):
            breadth += 2
            breadth_note = "XLK + XLF/XLI participation → broader rotation"
        elif xlk > 0 and xlf <= 0 and xli <= 0:
            breadth -= 2
            breadth_note = "XLK only leadership → narrow rally"
        else:
            breadth_note = "No clear breadth confirmation"

    # B) Nasdaq breadth: QQQE/QQQ
    if qqq > 0 and qqqe > 0:
        qqqe_qqq_ratio = qqqe / qqq

        if qqqe_qqq_ratio >= 0.99:
            breadth += 1
            nasdaq_breadth_note = (
                f"QQQE/QQQ={qqqe_qqq_ratio:.3f} → broad Nasdaq participation"
            )
        elif qqqe_qqq_ratio >= 0.96:
            nasdaq_breadth_note = (
                f"QQQE/QQQ={qqqe_qqq_ratio:.3f} → neutral Nasdaq breadth"
            )
        else:
            breadth -= 1
            nasdaq_breadth_note = (
                f"QQQE/QQQ={qqqe_qqq_ratio:.3f} → mega-cap concentrated Nasdaq rally"
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