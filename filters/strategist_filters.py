from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
from scripts.data_processing import download_all_etfs_and_save
from scripts.data_processing import load_etf_data_from_csv
from sklearn.metrics.pairwise import cosine_similarity

import numpy as np
from pathlib import Path

import pandas as pd
import math

# =========================
# Helpers
# =========================

def detect_flow_signal(market_data):

    sew = market_data.get("SEW_STATE", "NORMAL")
    drift_score = market_data.get("DRIFT_SCORE", 0)

    signal = "NONE"
    strength = 0

    # 🔥 1. Drift 먼저 (기관 축적 단계)
    if drift_score >= 3:
        signal = "FLOW_BUILDING"
        strength = 1

    # 🔥 2. Drift + SEW = 진짜 신호
    if drift_score >= 2 and sew in ["WATCH", "ALERT"]:
        signal = "PRE_SHOCK"
        strength = 2

    # 🔥 3. SEW만 단독
    if sew in ["ALERT", "DEADMAN"]:
        signal = "SHOCK"
        strength = 3

    market_data["FLOW_SIGNAL"] = signal
    market_data["FLOW_STRENGTH"] = strength

    return market_data
    
def classify_drift_label(drift: Dict[str, Any]) -> str:
    spy_1d = drift.get("SPY", {}).get("1D")
    wti_1d = drift.get("WTI", {}).get("1D")
    dxy_1d = drift.get("DXY", {}).get("1D")
    gold_1d = drift.get("GOLD", {}).get("1D")

    def up(x, thr=0.8):
        return x is not None and x > thr

    def down(x, thr=-0.8):
        return x is not None and x < thr

    # --------------------------------------------------
    # 1) DISINFLATION RISK-ON
    # 주식↑ / 유가↓ / 금↑(선택)
    # --------------------------------------------------
    if up(spy_1d) and down(wti_1d):
        return "DISINFLATION_RISK_ON"

    # --------------------------------------------------
    # 2) SYSTEMIC HEDGE
    # 금↑ / 달러↑ / 주식↓
    # --------------------------------------------------
    if up(gold_1d) and up(dxy_1d) and down(spy_1d):
        return "SYSTEMIC_HEDGE"

    # --------------------------------------------------
    # 3) OIL SHOCK
    # 유가↑↑ + 주식↓
    # --------------------------------------------------
    if up(wti_1d, 2.0) and down(spy_1d):
        return "OIL_SHOCK"

    # --------------------------------------------------
    # 4) TIGHTENING PRESSURE
    # 달러↑ + 주식↓
    # --------------------------------------------------
    if up(dxy_1d) and down(spy_1d):
        return "TIGHTENING_PRESSURE"

    # --------------------------------------------------
    # 5) DEFAULT
    # --------------------------------------------------
    return "MIXED"
    

def classify_drift_label(drift_inputs: Dict[str, Any]) -> str:
    """
    drift_inputs 예시:
    {
        "SPY": {"1D": ...},
        "WTI": {"1D": ...},
        "DXY": {"1D": ...},
        "GOLD": {"1D": ...},
    }
    """

    spy_1d = drift_inputs.get("SPY", {}).get("1D")
    wti_1d = drift_inputs.get("WTI", {}).get("1D")
    dxy_1d = drift_inputs.get("DXY", {}).get("1D")
    gold_1d = drift_inputs.get("GOLD", {}).get("1D")

    def up(x, thr=0.8):
        return x is not None and x > thr

    def down(x, thr=-0.8):
        return x is not None and x < thr

    # 1) 디스인플레이션 + 리스크온
    if up(spy_1d) and down(wti_1d):
        return "DISINFLATION_RISK_ON"

    # 2) 시스템 헤지
    if up(gold_1d) and up(dxy_1d) and down(spy_1d):
        return "SYSTEMIC_HEDGE"

    # 3) 오일 쇼크
    if up(wti_1d, 2.0) and down(spy_1d):
        return "OIL_SHOCK"

    # 4) 긴축 압력
    if up(dxy_1d) and down(spy_1d):
        return "TIGHTENING_PRESSURE"

    return "MIXED"


def drift_monitor_filter(market_data: Dict[str, Any]) -> str:
    """
    Drift Monitor v4 (visualized)
    - 기존 점수 계산 로직 유지
    - 출력만 방향 / 단기 정렬 / 강도 중심으로 개선
    """

    drift = market_data.get("DRIFT_DATA", {}) or {}

    def g(asset, key):
        try:
            return drift.get(asset, {}).get(key)
        except Exception:
            return None

    # -----------------------------
    # Score 계산 (기존 유지)
    # -----------------------------
    score = 0
    reasons = []

    # WTI (디스인플레이션 핵심)
    if g("WTI", "ret_1d") is not None and g("WTI", "ret_1d") <= -5:
        score += 1
        reasons.append("WTI 1D downside extension")

    # SPY 상승
    if g("SPY", "ret_1d") is not None and g("SPY", "ret_1d") >= 1:
        score += 1
        reasons.append("SPY 1D continuation")

    # GOLD 상승
    if g("GOLD", "ret_1d") is not None and g("GOLD", "ret_1d") >= 1:
        score += 1
        reasons.append("Gold strength")

    # DXY 약세
    if g("DXY", "ret_1d") is not None and g("DXY", "ret_1d") <= -0.2:
        score += 1
        reasons.append("DXY softening")

    # -----------------------------
    # ATR 기반 강화 (기존 유지)
    # -----------------------------
    if g("SPY", "norm_1d") is not None and abs(g("SPY", "norm_1d")) >= 1.5:
        score += 1
        reasons.append("SPY move > 1.5 ATR")

    if g("WTI", "norm_1d") is not None and abs(g("WTI", "norm_1d")) >= 2.0:
        score += 1
        reasons.append("WTI extreme ATR move")

    # -----------------------------
    # State 정의 (기존 유지)
    # -----------------------------
    if score >= 4:
        state = "🔥 STRONG TREND (방향성 자금 흐름 감지)"
    elif score >= 2:
        state = "⚡ TREND FORMING (초기 흐름 감지)"
    elif score == 1:
        state = "WEAK DRIFT (노이즈 가능)"
    else:
        state = "NO DRIFT"

    # -----------------------------
    # Label 정의 (기존 유지)
    # -----------------------------
    label = "NEUTRAL"

    spy = g("SPY", "ret_1d")
    wti = g("WTI", "ret_1d")
    dxy = g("DXY", "ret_1d")
    gold = g("GOLD", "ret_1d")

    if spy and wti and dxy:
        if spy > 0 and wti < 0 and dxy < 0:
            label = "DISINFLATION_RISK_ON"
        elif spy < 0 and wti > 0 and dxy > 0:
            label = "INFLATION_RISK_OFF"
        elif spy < 0 and wti < 0:
            label = "GROWTH_SCARE"
        elif spy > 0 and wti > 0:
            label = "REOPENING / DEMAND_BOOM"

    # -----------------------------
    # SEW 조합 신호 (기존 유지)
    # -----------------------------
    sew_status = str(market_data.get("SEW_STATUS", "N/A") or "N/A").upper()

    combo_signal = "NONE"

    if sew_status == "STABLE" and score >= 3:
        combo_signal = "🟢 EARLY FLOW WITHOUT SHOCK"
    elif sew_status in ["WATCH", "ALERT"] and score >= 3:
        combo_signal = "🟠 FLOW + SHOCK CONFLICT / EVENT RISK"
    elif sew_status in ["WATCH", "ALERT"] and score <= 1:
        combo_signal = "🔴 SHOCK WITHOUT DRIFT"

    # -----------------------------
    # 저장 (기존 유지)
    # -----------------------------
    market_data["DRIFT_SCORE"] = score
    market_data["DRIFT_STATE"] = state

    market_data["DRIFT"] = {
        "data": drift,
        "score": score,
        "state": state,
        "label": label,
        "combo_signal": combo_signal,
    }

    # -----------------------------
    # 시각화용 helper
    # -----------------------------
    def fmt(x):
        try:
            if x is None:
                return "N/A"
            return f"{float(x):+.2f}%"
        except Exception:
            return "N/A"

    def short_alignment(asset: str) -> str:
        vals = [
            g(asset, "ret_15m"),
            g(asset, "ret_30m"),
            g(asset, "ret_1h"),
            g(asset, "ret_4h"),
        ]
        vals = [v for v in vals if v is not None]

        if not vals:
            return "N/A"

        up = sum(1 for v in vals if v > 0)
        down = sum(1 for v in vals if v < 0)

        if up >= 3:
            return "SHORT UP"
        if down >= 3:
            return "SHORT DOWN"
        return "MIXED"

    def trend_direction(asset: str) -> str:
        d1 = g(asset, "ret_1d")
        d5 = g(asset, "ret_5d")

        if d1 is None or d5 is None:
            return "N/A"

        if d1 > 0 and d5 > 0:
            return "🟢 UP"
        if d1 < 0 and d5 < 0:
            return "🔴 DOWN"
        if d1 > 0 and d5 < 0:
            return "🟡 REBOUND"
        if d1 < 0 and d5 > 0:
            return "🟡 PULLBACK"
        return "⚪ SIDEWAYS"

    def strength_label(asset: str) -> str:
        d1 = g(asset, "ret_1d")
        d5 = g(asset, "ret_5d")

        vals = [abs(v) for v in [d1, d5] if v is not None]
        if not vals:
            return "N/A"

        strength = sum(vals) / len(vals)

        if strength >= 5:
            return "HIGH"
        if strength >= 2:
            return "MEDIUM"
        return "LOW"

    def asset_summary(asset: str) -> str:
        direction = trend_direction(asset)
        short = short_alignment(asset)
        strength = strength_label(asset)
        d1 = fmt(g(asset, "ret_1d"))
        d5 = fmt(g(asset, "ret_5d"))
        return f"- **{asset}:** {direction} | Short-term: {short} | 1D={d1} / 5D={d5} | Strength: {strength}"

    # -----------------------------
    # Output
    # -----------------------------
    lines = []
    lines.append("### 🌊 Drift Monitor (v4)")
    lines.append("- **정의:** 누적 흐름 + ATR 기반 강도 감지")
    lines.append("")

    for asset in ["SPY", "WTI", "DXY", "GOLD"]:
        lines.append(asset_summary(asset))

    lines.append("")
    lines.append(f"- **Drift Score:** {score}")
    lines.append(f"- **State:** **{state}**")
    lines.append(f"- **Label:** {label}")
    lines.append(f"- **SEW Combo Signal:** {combo_signal}")

    lines.append("")
    lines.append("- **Market Drift Summary:**")
    lines.append(f"  - Equity (SPY): {trend_direction('SPY')} / {short_alignment('SPY')}")
    lines.append(f"  - Oil (WTI): {trend_direction('WTI')} / {short_alignment('WTI')}")
    lines.append(f"  - Dollar (DXY): {trend_direction('DXY')} / {short_alignment('DXY')}")
    lines.append(f"  - Gold (GOLD): {trend_direction('GOLD')} / {short_alignment('GOLD')}")

    if reasons:
        lines.append("")
        lines.append("- **Drivers:**")
        for r in reasons:
            lines.append(f"  - {r}")

    return "\n".join(lines)
# -------------------------------------------------------------------
# 6.5) Correlation Break Monitor (stabilized v2.0)
# -------------------------------------------------------------------
def correlation_break_filter(market_data: Dict[str, Any]) -> str:
    state = correlation_break_state(market_data)

    lines = []
    lines.append("### ⚠ 6.5) Correlation Break Monitor")

    if market_data.get("_STALE"):
        lines.append("⚠ Market Closed / Stale Data → Correlation signals evaluated conservatively.")
        lines.append("")

    if state["break"]:
        lines.append("Correlation Break Detected:")
        for b in state["reasons"]:
            lines.append(f"- {b}")
        lines.append("")
        lines.append("So What?")
        lines.append("- 결론: **공식이 깨진 구간** → 방향 베팅보다 **사이징 보수적 + 퀄리티/리더 중심**")
    else:
        lines.append("No significant correlation break detected.")

    return "\n".join(lines)


def correlation_break_state(market_data: Dict[str, Any]) -> Dict[str, Any]:
    def pct(key: str) -> Optional[float]:
        v = market_data.get(key, {}) or {}
        x = v.get("pct_change")
        try:
            return None if x is None else float(x)
        except Exception:
            return None

    def signif(x: Optional[float], thr: float) -> bool:
        return (x is not None) and (abs(x) >= thr)

    us10y = pct("US10Y")
    dxy = pct("DXY")
    vix = pct("VIX")
    spy = pct("SPY")
    qqq = pct("QQQ")
    xlk = pct("XLK")

    # Tech proxy 우선순위: QQQ -> XLK
    tech = qqq if qqq is not None else xlk

    # --------------------------------------------------
    # 안정화 threshold
    # --------------------------------------------------
    THR_US10Y = 0.20   # 기존 0.10 → 상향
    THR_DXY = 0.20     # 기존 0.15 → 상향
    THR_VIX = 1.20     # 기존 1.00 → 상향
    THR_EQ = 0.35      # 기존 0.25 → 상향

    breaks = []
    score = 0

    # 금리와 주식/기술주의 비정상 동행
    if signif(us10y, THR_US10Y):
        if us10y > 0:
            if signif(tech, THR_EQ) and tech > 0:
                breaks.append("US10Y ↑ but Technology ↑")
                score += 1
            if signif(spy, THR_EQ) and spy > 0:
                breaks.append("US10Y ↑ but SPY ↑")
                score += 1

        elif us10y < 0:
            if signif(tech, THR_EQ) and tech < 0:
                breaks.append("US10Y ↓ but Technology ↓")
                score += 1
            if signif(spy, THR_EQ) and spy < 0:
                breaks.append("US10Y ↓ but SPY ↓")
                score += 1

    # VIX와 주식의 비정상 동행
    if signif(vix, THR_VIX) and vix > 0:
        if signif(spy, THR_EQ) and spy > 0:
            breaks.append("VIX ↑ but SPY ↑")
            score += 1
        if signif(tech, THR_EQ) and tech > 0:
            breaks.append("VIX ↑ but Technology ↑")
            score += 1

    # DXY와 SPY/Tech의 비정상 동행
    if signif(dxy, THR_DXY) and dxy > 0:
        if signif(spy, THR_EQ) and spy > 0:
            breaks.append("DXY ↑ but SPY ↑")
            score += 1
        if signif(tech, THR_EQ) and tech > 0:
            breaks.append("DXY ↑ but Technology ↑")
            score += 1

    return {
        "break": len(breaks) > 0,
        "score": score,
        "reasons": breaks,
    }


# -------------------------------------------------------------------
# 6.6) Sector Correlation Break Monitor (stabilized v2.0)
# -------------------------------------------------------------------
def sector_correlation_break_filter(market_data: Dict[str, Any]) -> str:
    state = sector_correlation_break_state(market_data)

    lines = []
    lines.append("### ⚠ 6.6) Sector Correlation Break Monitor")

    if market_data.get("_STALE"):
        lines.append("⚠ Market Closed / Stale Data → Sector signals evaluated conservatively.")
        lines.append("")

    if state["break"]:
        lines.append("Correlation Break Detected:")
        for b in state["reasons"]:
            lines.append(f"- {b}")
        lines.append("")
        lines.append("So What?")
        lines.append("- 결론: **섹터 ‘공식’이 깨진 구간** → 방향 베팅보다 **사이징 축소 + 리더 중심**")
    else:
        lines.append("No significant sector-level correlation break detected.")

    return "\n".join(lines)


def sector_correlation_break_state(market_data: Dict[str, Any]) -> Dict[str, Any]:
    def pct(key: str) -> Optional[float]:
        v = market_data.get(key, {}) or {}
        x = v.get("pct_change")
        try:
            return None if x is None else float(x)
        except Exception:
            return None

    def signif(x: Optional[float], thr: float) -> bool:
        return (x is not None) and (abs(x) >= thr)

    us10y = pct("US10Y")
    wti = pct("WTI")
    dxy = pct("DXY")
    vix = pct("VIX")

    xlk = pct("XLK")
    xlf = pct("XLF")
    xle = pct("XLE")
    xlre = pct("XLRE")

    # --------------------------------------------------
    # 안정화 threshold
    # --------------------------------------------------
    THR_US10Y = 0.20   # 금리 변화 의미 있게
    THR_WTI = 2.00     # 유가 이벤트성 움직임만 반영
    THR_DXY = 0.20
    THR_VIX = 1.20
    THR_SECTOR = 0.35  # 섹터는 0.35 이상일 때만 의미 부여

    breaks = []
    score = 0

    # 금리 상승인데 금융/리츠/기술주가 반대로 움직이는 경우
    if signif(us10y, THR_US10Y):
        if us10y > 0:
            if signif(xlf, THR_SECTOR) and xlf < 0:
                breaks.append("US10Y ↑ but XLF ↓")
                score += 1
            if signif(xlre, THR_SECTOR) and xlre > 0:
                breaks.append("US10Y ↑ but XLRE ↑")
                score += 1
            if signif(xlk, THR_SECTOR) and xlk > 0:
                breaks.append("US10Y ↑ but XLK ↑")
                score += 1

        elif us10y < 0:
            if signif(xlk, THR_SECTOR) and xlk < 0:
                breaks.append("US10Y ↓ but XLK ↓")
                score += 1
            if signif(xlf, THR_SECTOR) and xlf < 0:
                breaks.append("US10Y ↓ but XLF ↓")
                score += 1

    # 유가 상승인데 에너지 섹터 하락
    if signif(wti, THR_WTI) and wti > 0:
        if signif(xle, THR_SECTOR) and xle < 0:
            breaks.append("WTI ↑ but XLE ↓")
            score += 1

    # VIX 상승인데 금융 상승
    if signif(vix, THR_VIX) and vix > 0:
        if signif(xlf, THR_SECTOR) and xlf > 0:
            breaks.append("VIX ↑ but XLF ↑")
            score += 1

    # 달러 상승인데 기술 상승
    if signif(dxy, THR_DXY) and dxy > 0:
        if signif(xlk, THR_SECTOR) and xlk > 0:
            breaks.append("DXY ↑ but XLK ↑")
            score += 1

    return {
        "break": len(breaks) > 0,
        "score": score,
        "reasons": breaks,
    }

    
def _cumret_series_from_df(df: pd.DataFrame, col: str, days: int = 5) -> pd.Series:
    s = pd.to_numeric(df[col], errors="coerce")
    s = s.dropna()
    return s.pct_change(days) * 100.0
    
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

    def _valid(x):
        return x is not None and not pd.isna(x)

    us10y_dir = _sign_from(us10y)
    dxy_dir   = _sign_from(dxy)
    vix_dir   = _sign_from(vix)

    # Direction: for FCI/REAL_RATE, lower is better
    fci_raw_dir = _sign_from(fci)
    rr_raw_dir  = _sign_from(rr)
    fci_eff_dir = -fci_raw_dir if _valid(fci.get("today")) else 0
    rr_eff_dir  = -rr_raw_dir  if _valid(rr.get("today")) else 0

    def fci_level_label(x: Optional[float]) -> str:
        if x is None or pd.isna(x):
            return "N/A"
        if x <= -0.25:
            return "EASY (완화)"
        if x < 0.25:
            return "NEUTRAL (중립)"
        return "TIGHT (압박)"

    def rr_level_label(x: Optional[float]) -> str:
        if x is None or pd.isna(x):
            return "N/A"
        if x < 1.0:
            return "SUPPORTIVE (유인↑)"
        if x < 2.0:
            return "NEUTRAL (중립)"
        return "RESTRICTIVE (유인↓)"

    fci_level = fci_level_label(_to_float(fci.get("today")))
    rr_level  = rr_level_label(_to_float(rr.get("today")))

    exp_easing = (us10y_dir == -1 and dxy_dir == -1 and vix_dir in (-1, 0))
    exp_tight  = (us10y_dir == 1 and dxy_dir == 1)

    def level_score(label: str) -> int:
        if label in ("EASY (완화)", "SUPPORTIVE (유인↑)"):
            return 1
        if label in ("TIGHT (압박)", "RESTRICTIVE (유인↓)"):
            return -1
        return 0

    reality_score = level_score(fci_level)
    incentive_score = level_score(rr_level)

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

    if not _valid(fci.get("today")):
        lines.append("- **현실(FCI):** N/A (not available)")
    else:
        lines.append(
            f"- **현실(FCI):** level={fci_level} / dir({_dir_str(fci_eff_dir)})"
            + (f" | as of: {fci_asof} (FRED last available)" if fci_asof else "")
        )

    if not _valid(rr.get("today")):
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
    # dxy_dir = _sign_from(dxy) # 필요시 사용
    wti_dir = _sign_from(wti)
    vix_dir = _sign_from(vix)

    lines = []
    lines.append("### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)")
    lines.append("- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함")
    lines.append("")

    # 1. 금리-통화 연쇄 반응
    if us10y_dir == 1:
        lines.append("- **금리 상승(US10Y↑)** → 실질 금리 압박 → 달러 강세(DXY↑) 유도: **신흥국 자본 유출 및 고밸류 성장주 할인율 부담 증가**")
    elif us10y_dir == -1:
        lines.append("- **금리 하락(US10Y↓)** → 할인율 압박 완화 → 달러 약세(DXY↓) 유도: **위험자산(Growth/EM) 선호 심리 강화 및 유동성 환경 개선**")
    else:
        lines.append("- **금리 보합(US10Y→)** → 할인율 변수 제한: 시장은 정책 경로 재확인을 위한 대기 국면")

    # 2. 심리-수요 연쇄 반응
    if vix_dir == 1:
        lines.append("- **변동성 상승(VIX↑)** → 위험회피(Risk-Off) 강화: **안전 자산(Cash/USD) 선호도 급증 및 하이일드 스프레드 확대 압력**")
    elif vix_dir == -1:
        lines.append("- **변동성 하락(VIX↓)** → 심리 개선(Risk-On): **자산군 전반의 위험 수용 여력(Risk Appetite) 회복 및 랠리 지속 가능성**")
    else:
        lines.append("- **변동성 보합(VIX→)** → 심리 변화 제한: 현재의 추세가 관성적으로 유지되는 구간")

    # 3. 에너지-인플레 연쇄 반응
    if wti_dir == 1:
        lines.append("- **유가 상승(WTI↑)** → 기대 인플레이션 자극: **제조/운송업 비용 부담 가중 및 중앙은행의 긴축 유지 명분 강화**")
    elif wti_dir == -1:
        lines.append("- **유가 하락(WTI↓)** → 물가 부담 완화: **실질 구매력 회복 및 긴축 압력 완화(Dovish Tilt) 가능성 시사**")
    else:
        lines.append("- **유가 보합(WTI→)** → 물가 변수 제한: 에너지발 매크로 충격은 제한적인 국면")

    # 4. 연결 고리 (Check Point)
    lines.append("")
    lines.append("> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함")

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

# filters/strategist_filters.py (상수 구간)



# 급락 여부를 체크하는 함수
GEO_WINDOW = 60

def check_etf_crash(
    df: pd.DataFrame,
    etf_symbol: str,
    days: int = 5,
    threshold: float = 2.0,
) -> bool:
    """
    ETF별 '위험 방향'을 반영한 crash/stress 체크 함수.

    - 일반 risk asset (EEM, EMB, SPY, EIS, FXI, EWJ, BND 등):
        5일 누적수익률이 -threshold%보다 낮으면 급락/위험
    - safe haven / stress asset (GLD, VXX):
        5일 누적수익률이 +threshold%보다 높으면 stress 확대(위험)

    threshold는 절대값 기준 (기본 2.0%)
    """
    if etf_symbol not in df.columns:
        return False

    s = pd.to_numeric(df[etf_symbol], errors="coerce").dropna()
    if len(s) < days + 1:
        return False

    cum_ret = (
        (s.pct_change().add(1).rolling(window=days).apply(lambda x: x.prod(), raw=True) - 1)
        * 100
    )

    if cum_ret.dropna().empty:
        return False

    last_val = float(cum_ret.dropna().iloc[-1])

    # ✅ 방향성 정의
    upside_risk_assets = {"GLD", "VXX"}   # 상승이 stress / risk-off
    downside_risk_assets = {"EIS", "SPY", "EEM", "EMB", "FXI", "EWJ", "BND"}

    if etf_symbol in upside_risk_assets:
        if last_val > threshold:
            print(f"[INFO] {etf_symbol} stress spike detected: {last_val:.2f}% change")
            return True
        return False

    # default: 하락이 위험
    if etf_symbol in downside_risk_assets or True:
        if last_val < -threshold:
            print(f"[INFO] {etf_symbol} has crashed: {last_val:.2f}% change")
            return True

    return False


def attach_country_risk_layer(
    market_data: Dict[str, Any],
    df: pd.DataFrame,
    today_idx: int,
    window: int = GEO_WINDOW,
) -> Dict[str, Any]:
    """
    country_etf_data_combined.csv 에서 전체 국가 ETF 데이터를 읽어
    각 ETF별 급락 여부 / z-score를 계산
    """
    file_path = "data/country_etf_data_combined.csv"
    all_etf_data = load_etf_data_from_csv(file_path)

    if all_etf_data.empty:
        print("[ERROR] No combined ETF data found.")
        return market_data

    all_etf_data = all_etf_data.sort_index()

    country_etf_list = [
        "EIS",
        "SPY",
        "EEM",
        "EMB",
        "GLD",
        "VXX",
        "FXI",
        "EWJ",
        "BND",
    ]

    # ✅ 방향성 정의
    upside_risk_assets = {"GLD", "VXX"}  # 상승이 stress
    downside_risk_assets = {"EIS", "SPY", "EEM", "EMB", "FXI", "EWJ", "BND"}  # 하락이 stress

    for country_etf in country_etf_list:
        if country_etf not in all_etf_data.columns:
            print(f"[WARN] {country_etf} not found in combined ETF data.")
            continue

        etf_data = all_etf_data[[country_etf]].copy()
        etf_data[country_etf] = pd.to_numeric(etf_data[country_etf], errors="coerce")
        etf_data = etf_data.dropna()

        if etf_data.empty or len(etf_data) < 6:
            print(f"[WARN] Not enough data for {country_etf}")
            continue

        pct_1d = etf_data[country_etf].pct_change() * 100
        pct_5d = (
            (etf_data[country_etf].pct_change().add(1).rolling(window=5).apply(lambda x: x.prod(), raw=True) - 1)
            * 100
        )

        z_1d = _zscore_last(pct_1d, window)
        z_5d = _zscore_last(pct_5d, window)

        print(f"[INFO] {country_etf} z_1d: {z_1d}, z_5d: {z_5d}")

        country_risk = "NORMAL"

        # ✅ z_5d 방향성도 ETF별로 다르게 해석
        if z_5d is not None:
            if country_etf in upside_risk_assets and z_5d > 2:
                country_risk = "HIGH"
            elif country_etf in downside_risk_assets and z_5d < -2:
                country_risk = "HIGH"

        is_crash = check_etf_crash(etf_data, country_etf)
        if is_crash:
            country_risk = "EXTREME"

        market_data[f"COUNTRY_RISK_{country_etf}"] = {
            "country_etf": country_etf,
            "z_1d": z_1d,
            "z_5d": z_5d,
            "risk_level": country_risk,
            "crash": is_crash,
        }

    return market_data


            
# (key, weight, transform, mode)
# mode: "pct" | "level"
GEO_FACTORS = [
    # -----------------------
    # Market Reaction
    # -----------------------
    ("VIX",    0.18, "normal", "pct"),
    ("WTI",    0.10, "normal", "pct"),
    ("GOLD",   0.12, "normal", "pct"),
    ("USDCNH", 0.18, "normal", "pct"),

    # -----------------------
    # EM Stress
    # -----------------------
    ("EEM",    0.10, "inverse", "pct"),
    ("EMB",    0.12, "inverse", "pct"),
    ("USDMXN", 0.05, "normal",  "pct"),
    ("USDJPY", 0.05, "inverse", "pct"),

    # -----------------------
    # Supply Chain / Shipping
    # -----------------------
    ("SEA",    0.05, "inverse", "pct"),
    ("BDRY",   0.05, "normal",  "pct"),

    # -----------------------
    # Defense
    # -----------------------
    ("ITA",    0.03, "normal", "pct"),
    ("XAR",    0.02, "normal", "pct"),

    # -----------------------
    # ✅ Sovereign Spread (CDS proxy) — NEW
    # spread는 pct_change보다 레벨 자체가 의미있어서 level z-score
    # -----------------------
    ("KR10Y_SPREAD", 0.08, "normal", "level"),
    ("JP10Y_SPREAD", 0.06, "normal", "level"),
    ("DE10Y_SPREAD", 0.06, "normal", "level"),
    ("IL10Y_SPREAD", 0.05, "normal", "level"),
]

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


# Z-score 계산용 헬퍼 함수
def _zscore_last(s: pd.Series, window: int) -> Optional[float]:
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return None
    x = s.tail(window).dropna()
    if len(x) < 5:
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

    if market_data is None:
        market_data = {}

    df2 = df.iloc[: today_idx + 1].copy()

    # -----------------------
    # merge sovereign spreads
    # -----------------------
    try:
        sov = load_sovereign_spreads_df()

        if sov is not None and not sov.empty and "date" in sov.columns:

            sov2 = sov.copy()
            sov2["date"] = pd.to_datetime(sov2["date"], errors="coerce")
            sov2 = sov2.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")

            if "date" in df2.columns:
                df2["date"] = pd.to_datetime(df2["date"], errors="coerce")

            wanted_cols = ["date"]

            for c in [
                "KR10Y_SPREAD",
                "JP10Y_SPREAD",
                "DE10Y_SPREAD",
                "IL10Y_SPREAD",
            ]:
                if c in sov2.columns:
                    wanted_cols.append(c)

            if len(wanted_cols) > 1:
                df2 = pd.merge(df2, sov2[wanted_cols], on="date", how="left")

                for c in wanted_cols:
                    if c != "date":
                        df2[c] = pd.to_numeric(df2[c], errors="coerce").ffill()

                        # fallback → market_data
                        if pd.isna(df2[c].iloc[-1]):
                            if c in market_data:
                                df2.loc[df2.index[-1], c] = market_data.get(c)

    except Exception:
        pass

    # -----------------------
    # helpers
    # -----------------------
    def _zscore_last_level(series: pd.Series, win: int):
        s = pd.to_numeric(series, errors="coerce").dropna()

        if len(s) < max(10, min(win, 20)):
            return None

        tail = s.tail(win)
        mu = float(tail.mean())
        sd = float(tail.std(ddof=0))

        if sd == 0:
            return 0.0

        return float((tail.iloc[-1] - mu) / sd)

    def _series_level_from_df(df_, key):
        return pd.to_numeric(df_.get(key), errors="coerce")

    def _merge_spreads_for_hist(df_hist: pd.DataFrame) -> pd.DataFrame:
        """
        Geo momentum 계산용: 히스토리 slice에도 sovereign spreads 동일 방식으로 merge
        """
        out = df_hist.copy()

        try:
            sov_hist = load_sovereign_spreads_df()
            if sov_hist is not None and not sov_hist.empty and "date" in sov_hist.columns:
                sov_hist = sov_hist.copy()
                sov_hist["date"] = pd.to_datetime(sov_hist["date"], errors="coerce")
                sov_hist = (
                    sov_hist.dropna(subset=["date"])
                    .sort_values("date")
                    .drop_duplicates("date", keep="last")
                )

                if "date" in out.columns:
                    out["date"] = pd.to_datetime(out["date"], errors="coerce")

                wanted_cols = ["date"]
                for c in ["KR10Y_SPREAD", "JP10Y_SPREAD", "DE10Y_SPREAD", "IL10Y_SPREAD"]:
                    if c in sov_hist.columns:
                        wanted_cols.append(c)

                if len(wanted_cols) > 1:
                    out = pd.merge(out, sov_hist[wanted_cols], on="date", how="left")
                    for c in wanted_cols:
                        if c != "date":
                            out[c] = pd.to_numeric(out[c], errors="coerce").ffill()
        except Exception:
            pass

        return out

    def _compute_geo_score_only(df_input: pd.DataFrame) -> Optional[float]:
        """
        Momentum 계산용: score만 간단히 계산
        """
        local_usable_components = []

        for item in GEO_FACTORS:
            key = item[0]
            raw_weight = float(item[1])
            transform = item[2]
            mode = item[3] if len(item) >= 4 else None

            if mode is None:
                mode = "level" if key.endswith("_SPREAD") else "pct"

            if key not in df_input.columns:
                continue

            z = None
            z_1d = None
            z_5d = None

            if mode == "level":
                level_series = _series_level_from_df(df_input, key)
                z = _zscore_last_level(level_series, window)
            else:
                pct_1d = _pct_series_from_df(df_input, key)
                pct_5d = _cumret_series_from_df(df_input, key, days=5)

                z_1d = _zscore_last(pct_1d, window)
                z_5d = _zscore_last(pct_5d, window)

                if z_1d is None and z_5d is None:
                    z = None
                elif z_1d is None:
                    z = z_5d
                elif z_5d is None:
                    z = z_1d
                else:
                    z = 0.6 * float(z_1d) + 0.4 * float(z_5d)

            if z is None:
                continue

            z_used = -z if transform == "inverse" else z

            local_usable_components.append(
                {
                    "raw_weight": raw_weight,
                    "z_used": float(z_used),
                }
            )

        local_used_weight = sum(c["raw_weight"] for c in local_usable_components)
        if local_used_weight <= 0:
            return None

        local_score = 0.0
        for c in local_usable_components:
            norm_w = c["raw_weight"] / local_used_weight
            local_score += c["z_used"] * norm_w

        return float(local_score)

    # -----------------------
    # pass 1: collect usable factors
    # -----------------------
    usable_components = []
    missing = []

    total_defined_weight = sum(float(item[1]) for item in GEO_FACTORS)

    for item in GEO_FACTORS:
        key = item[0]
        raw_weight = float(item[1])
        transform = item[2]
        mode = item[3] if len(item) >= 4 else None

        if mode is None:
            mode = "level" if key.endswith("_SPREAD") else "pct"

        # -----------------------
        # fallback check
        # -----------------------
        if key not in df2.columns:
            if key in market_data:
                val = market_data.get(key)
                if val is not None:
                    df2.loc[df2.index[-1], key] = val
                else:
                    missing.append(key)
                    continue
            else:
                missing.append(key)
                continue

        # -----------------------
        # compute zscore
        # -----------------------
        z = None
        z_1d = None
        z_5d = None

        if mode == "level":
            level_series = _series_level_from_df(df2, key)
            z = _zscore_last_level(level_series, window)

        else:
            pct_1d = _pct_series_from_df(df2, key)
            pct_5d = _cumret_series_from_df(df2, key, days=5)

            z_1d = _zscore_last(pct_1d, window)
            z_5d = _zscore_last(pct_5d, window)

            if z_1d is None and z_5d is None:
                z = None
            elif z_1d is None:
                z = z_5d
            elif z_5d is None:
                z = z_1d
            else:
                z = 0.6 * float(z_1d) + 0.4 * float(z_5d)

        if z is None:
            missing.append(key)
            continue

        z_used = -z if transform == "inverse" else z

        usable_components.append(
            {
                "key": key,
                "raw_weight": raw_weight,
                "z": float(z),
                "z_1d": None if z_1d is None else float(z_1d),
                "z_5d": None if z_5d is None else float(z_5d),
                "z_used": float(z_used),
                "transform": transform,
                "mode": mode,
            }
        )

    # -----------------------
    # pass 2: dynamic re-weighting
    # -----------------------
    used_weight = sum(c["raw_weight"] for c in usable_components)
    coverage = (used_weight / total_defined_weight) if total_defined_weight > 0 else 0.0

    components = []
    score = None

    if used_weight > 0:
        score = 0.0

        for c in usable_components:
            normalized_weight = c["raw_weight"] / used_weight
            contrib = c["z_used"] * normalized_weight
            score += contrib

            components.append(
                {
                    "key": c["key"],
                    "weight": c["raw_weight"],
                    "normalized_weight": normalized_weight,
                    "z": c["z"],
                    "z_1d": c["z_1d"],
                    "z_5d": c["z_5d"],
                    "z_used": c["z_used"],
                    "contrib": contrib,
                    "transform": c["transform"],
                    "mode": c["mode"],
                }
            )

    # -----------------------
    # Geo Momentum
    # -----------------------
    geo_score_3d_avg = None
    geo_momentum = None
    geo_momentum_label = "N/A"

    try:
        recent_scores = []
        start_idx = max(0, today_idx - 2)  # 최근 3개 시점

        for idx in range(start_idx, today_idx + 1):
            df_hist = df.iloc[: idx + 1].copy()
            df_hist = _merge_spreads_for_hist(df_hist)

            s = _compute_geo_score_only(df_hist)
            if s is not None:
                recent_scores.append(float(s))

        if len(recent_scores) >= 2:
            geo_score_3d_avg = float(sum(recent_scores) / len(recent_scores))

            if score is not None:
                geo_momentum = float(score - geo_score_3d_avg)

                if geo_momentum >= 0.25:
                    geo_momentum_label = "RISING"
                elif geo_momentum <= -0.25:
                    geo_momentum_label = "FALLING"
                else:
                    geo_momentum_label = "FLAT"
    except Exception:
        pass

    # -----------------------
    # level label
    # -----------------------
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
        "total_defined_weight": total_defined_weight,
        "coverage": coverage,
        "missing": missing,
        "components": components,
        "score_3d_avg": geo_score_3d_avg,
        "momentum": geo_momentum,
        "momentum_label": geo_momentum_label,
    }

    return market_data

GEO_SIMILARITY_FEATURES = [
    "geo_score",
    "geo_momentum",
    "VIX",
    "WTI",
    "GOLD",
    "USDCNH",
    "EEM",
    "EMB",
    "BDRY",
    "ITA",
    "KR10Y_SPREAD",
    "IL10Y_SPREAD",
    "country_crash_count",
    "country_high_count",
]

GEO_EVENT_TEMPLATES = {
    "Ukraine_2022": {
        "geo_score": 2.4,
        "geo_momentum": 0.8,
        "VIX": 2.0,
        "WTI": 2.2,
        "GOLD": 1.4,
        "USDCNH": 1.0,
        "EEM": 1.3,
        "EMB": 1.1,
        "BDRY": 0.6,
        "ITA": 1.7,
        "KR10Y_SPREAD": 0.7,
        "IL10Y_SPREAD": 0.3,
        "country_crash_count": 1.0,
        "country_high_count": 2.0,
    },
    "Israel_2023": {
        "geo_score": 1.8,
        "geo_momentum": 0.5,
        "VIX": 1.1,
        "WTI": 1.0,
        "GOLD": 1.2,
        "USDCNH": 0.4,
        "EEM": 0.7,
        "EMB": 0.6,
        "BDRY": 0.2,
        "ITA": 2.0,
        "KR10Y_SPREAD": 0.2,
        "IL10Y_SPREAD": 1.8,
        "country_crash_count": 1.0,
        "country_high_count": 1.0,
    },
    "Taiwan_Tension": {
        "geo_score": 1.5,
        "geo_momentum": 0.6,
        "VIX": 0.9,
        "WTI": 0.4,
        "GOLD": 0.8,
        "USDCNH": 1.8,
        "EEM": 0.9,
        "EMB": 0.7,
        "BDRY": 0.4,
        "ITA": 0.5,
        "KR10Y_SPREAD": 0.4,
        "IL10Y_SPREAD": 0.0,
        "country_crash_count": 0.0,
        "country_high_count": 2.0,
    },
    "Red_Sea": {
        "geo_score": 1.6,
        "geo_momentum": 0.7,
        "VIX": 0.8,
        "WTI": 1.4,
        "GOLD": 0.7,
        "USDCNH": 0.3,
        "EEM": 0.4,
        "EMB": 0.4,
        "BDRY": 1.8,
        "ITA": 0.6,
        "KR10Y_SPREAD": 0.2,
        "IL10Y_SPREAD": 0.2,
        "country_crash_count": 0.0,
        "country_high_count": 1.0,
    },
    "China_Trade_2018": {
        "geo_score": 1.7,
        "geo_momentum": 0.5,
        "VIX": 1.2,
        "WTI": 0.6,
        "GOLD": 0.9,
        "USDCNH": 2.2,       # 위안화 변동성 극대화 (핵심 변수)
        "EEM": 1.8,          # 신흥국 자산 타격
        "EMB": 1.4,          # 신흥국 채권 스트레스
        "BDRY": 1.5,         # 글로벌 물동량 우려 (해운지수)
        "ITA": 0.4,
        "KR10Y_SPREAD": 1.2, # 한국 금리 스프레드 민감도 높음
        "IL10Y_SPREAD": 0.1,
        "country_crash_count": 1.0,
        "country_high_count": 2.0,
    },
    "Iran_Crisis_2020": {
        "geo_score": 2.1,
        "geo_momentum": 0.9,
        "VIX": 1.8,
        "WTI": 2.5,          # 유가 급등 (핵심 변수)
        "GOLD": 1.9,         # 안전자산 선호
        "USDCNH": 0.5,
        "EEM": 0.8,
        "EMB": 0.7,
        "BDRY": 0.3,
        "ITA": 1.5,          # 방산 섹터 반응
        "KR10Y_SPREAD": 0.3,
        "IL10Y_SPREAD": 0.2,
        "country_crash_count": 0.0,
        "country_high_count": 1.0,
    },

        
}


def _safe_float(x, default: float = 0.0) -> float:
    try:
        if x is None or pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def _extract_geo_component_map(market_data: Dict[str, Any]) -> Dict[str, float]:
    geo = market_data.get("GEO_EW", {}) or {}
    comps = geo.get("components", []) or []

    out = {}
    for c in comps:
        key = c.get("key")
        if key is None:
            continue
        out[key] = _safe_float(c.get("z_used"), 0.0)

    return out


def _extract_country_risk_counts(market_data: Dict[str, Any]) -> Tuple[int, int]:
    crash_count = 0
    high_count = 0

    for k, v in market_data.items():
        if not str(k).startswith("COUNTRY_RISK_"):
            continue

        item = v or {}

        if item.get("crash"):
            crash_count += 1

        risk_level = item.get("risk_level", "NORMAL")
        if risk_level in ["HIGH", "EXTREME"]:
            high_count += 1

    return crash_count, high_count


def build_current_geo_similarity_vector(market_data: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, float]]:
    geo = market_data.get("GEO_EW", {}) or {}
    comp_map = _extract_geo_component_map(market_data)
    crash_count, high_count = _extract_country_risk_counts(market_data)

    feature_map = {
        "geo_score": _safe_float(geo.get("score"), 0.0),
        "geo_momentum": _safe_float(geo.get("momentum"), 0.0),
        "VIX": _safe_float(comp_map.get("VIX"), 0.0),
        "WTI": _safe_float(comp_map.get("WTI"), 0.0),
        "GOLD": _safe_float(comp_map.get("GOLD"), 0.0),
        "USDCNH": _safe_float(comp_map.get("USDCNH"), 0.0),
        "EEM": _safe_float(comp_map.get("EEM"), 0.0),
        "EMB": _safe_float(comp_map.get("EMB"), 0.0),
        "BDRY": _safe_float(comp_map.get("BDRY"), 0.0),
        "ITA": _safe_float(comp_map.get("ITA"), 0.0),
        "KR10Y_SPREAD": _safe_float(comp_map.get("KR10Y_SPREAD"), 0.0),
        "IL10Y_SPREAD": _safe_float(comp_map.get("IL10Y_SPREAD"), 0.0),
        "country_crash_count": float(crash_count),
        "country_high_count": float(high_count),
    }

    current_vector = np.array(
        [feature_map[k] for k in GEO_SIMILARITY_FEATURES],
        dtype=float
    )

    return current_vector, feature_map


def calculate_cosine_similarity(current_vector: np.ndarray, historical_vectors: np.ndarray) -> np.ndarray:
    """
    현재 벡터와 과거 이벤트 벡터들 간 cosine similarity를 계산한다.
    """
    current_vector = np.asarray(current_vector, dtype=float).reshape(1, -1)
    historical_vectors = np.asarray(historical_vectors, dtype=float)

    if historical_vectors.ndim != 2:
        raise ValueError("historical_vectors must be a 2D array")

    if current_vector.shape[1] != historical_vectors.shape[1]:
        raise ValueError(
            f"Feature size mismatch: current_vector has {current_vector.shape[1]} features, "
            f"historical_vectors has {historical_vectors.shape[1]} features"
        )

    if np.isnan(current_vector).any():
        current_vector = np.nan_to_num(current_vector, nan=0.0)

    if np.isnan(historical_vectors).any():
        historical_vectors = np.nan_to_num(historical_vectors, nan=0.0)

    return cosine_similarity(current_vector, historical_vectors)[0]


def attach_geo_similarity_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    if market_data is None:
        market_data = {}

    geo = market_data.get("GEO_EW", {}) or {}

    if geo.get("score") is None:
        geo["cosine_similarity"] = {
            "score": None,
            "matched_event": None,
            "signal": "N/A",
            "all_scores": {},
            "feature_map": {},
        }
        market_data["GEO_EW"] = geo
        return market_data

    current_vector, feature_map = build_current_geo_similarity_vector(market_data)

    template_names = list(GEO_EVENT_TEMPLATES.keys())

    historical_vectors = np.array([
        [GEO_EVENT_TEMPLATES[name].get(k, 0.0) for k in GEO_SIMILARITY_FEATURES]
        for name in template_names
    ], dtype=float)

    similarities = calculate_cosine_similarity(current_vector, historical_vectors)

    score_map = {
        name: float(score)
        for name, score in zip(template_names, similarities)
    }

    best_idx = int(np.argmax(similarities))
    best_score = float(similarities[best_idx])
    best_match = template_names[best_idx]

    if best_score >= 0.90:
        signal = "EXTREME_MATCH"
    elif best_score >= 0.80:
        signal = "HIGH_MATCH"
    elif best_score >= 0.70:
        signal = "ELEVATED_MATCH"
    else:
        signal = "LOW_MATCH"

    geo["cosine_similarity"] = {
        "score": best_score,
        "matched_event": best_match,
        "signal": signal,
        "all_scores": score_map,
        "feature_map": feature_map,
    }

    market_data["GEO_EW"] = geo
    return market_data

def attach_drift_data_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Drift v3 (with ATR normalization)
    - 15m / 30m / 1H / 4H / 1D / 5D returns
    - ATR 기반 정규화 포함
    """

    import yfinance as yf
    import pandas as pd

    drift_tickers = {
        "SPY": "SPY",
        "WTI": "CL=F",
        "DXY": "DX-Y.NYB",
        "GOLD": "GC=F",
    
        # Credit / Risk participation
        "HYG": "HYG",
        "LQD": "LQD",
    
        # EM / China
        "EEM": "EEM",
        "FXI": "FXI",
    
        # Sector leadership
        "XLK": "XLK",
        "XLI": "XLI",
        "XLF": "XLF",
        "XLY": "XLY",
    
        # Defensive comparison
        "XLP": "XLP",
        "XLU": "XLU",

    }
    drift_data = {}

    # -----------------------------
    # Helpers
    # -----------------------------
    def safe_ret(curr, past):
        try:
            if curr is None or past is None or past == 0:
                return None
            return ((curr / past) - 1.0) * 100.0
        except Exception:
            return None

    def extract_close_series(df):
        if df is None or df.empty:
            return None

        try:
            if isinstance(df.columns, pd.MultiIndex):
                close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
                if not close_cols:
                    return None
                s = df[close_cols]
                if isinstance(s, pd.DataFrame):
                    s = s.squeeze()
            else:
                if "Close" not in df.columns:
                    return None
                s = df["Close"]

            if isinstance(s, pd.DataFrame):
                s = s.squeeze()

            s = pd.to_numeric(s, errors="coerce").dropna()
            if s.empty:
                return None

            return s
        except Exception:
            return None

    def calculate_atr(df, period=14):
        try:
            high = df["High"]
            low = df["Low"]
            close = df["Close"]

            tr1 = high - low
            tr2 = (high - close.shift(1)).abs()
            tr3 = (low - close.shift(1)).abs()

            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(period).mean()

            return atr
        except Exception:
            return None

    # -----------------------------
    # Main loop
    # -----------------------------
    for name, ticker in drift_tickers.items():
        try:
            intraday = yf.download(
                ticker,
                period="7d",
                interval="15m",
                progress=False,
                auto_adjust=False,
                threads=False,
            )

            daily = yf.download(
                ticker,
                period="3mo",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )

            intraday_close = extract_close_series(intraday)
            daily_close = extract_close_series(daily)

            if intraday_close is None or daily_close is None:
                drift_data[name] = {}
                continue

            curr = float(intraday_close.iloc[-1])

            # intraday
            m15 = float(intraday_close.iloc[-2]) if len(intraday_close) >= 2 else None
            m30 = float(intraday_close.iloc[-3]) if len(intraday_close) >= 3 else None
            h1 = float(intraday_close.iloc[-5]) if len(intraday_close) >= 5 else None
            h4 = float(intraday_close.iloc[-17]) if len(intraday_close) >= 17 else None

            # daily
            d1 = float(daily_close.iloc[-2]) if len(daily_close) >= 2 else None
            d5 = float(daily_close.iloc[-6]) if len(daily_close) >= 6 else None

            # ATR
            atr_series = calculate_atr(daily)
            atr_latest = float(atr_series.iloc[-1]) if atr_series is not None else None

            def norm(ret):
                try:
                    if ret is None or atr_latest is None or atr_latest == 0:
                        return None
                    return ret / atr_latest
                except Exception:
                    return None

            drift_data[name] = {
                "ret_15m": safe_ret(curr, m15),
                "ret_30m": safe_ret(curr, m30),
                "ret_1h": safe_ret(curr, h1),
                "ret_4h": safe_ret(curr, h4),
                "ret_1d": safe_ret(curr, d1),
                "ret_5d": safe_ret(curr, d5),
                "atr": atr_latest,
                "norm_1d": norm(safe_ret(curr, d1)),
                "norm_5d": norm(safe_ret(curr, d5)),
            }

        except Exception:
            drift_data[name] = {}

    market_data["DRIFT_DATA"] = drift_data
    
    print("[DRIFT_DATA KEYS]", sorted(drift_data.keys()))
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
    score_3d_avg = geo.get("score_3d_avg")
    momentum = geo.get("momentum")
    momentum_label = geo.get("momentum_label", "N/A")

    cosine_info = geo.get("cosine_similarity", {}) or {}
    cosine_score = cosine_info.get("score")
    cosine_match = cosine_info.get("matched_event")
    cosine_signal = cosine_info.get("signal")
    cosine_all = cosine_info.get("all_scores", {}) or {}

    # -----------------------
    # Friendly label mapping
    # -----------------------
    similarity_label_map = {
        "LOW_MATCH": "Weak Historical Match",
        "ELEVATED_MATCH": "Moderate Historical Match",
        "HIGH_MATCH": "Strong Historical Match",
        "EXTREME_MATCH": "Extreme Historical Match",
        "N/A": "N/A",
        None: "N/A",
    }
    cosine_signal_label = similarity_label_map.get(cosine_signal, str(cosine_signal))

    # -----------------------
    # Country ETF risk aggregation
    # -----------------------
    country_risk_keys = sorted([k for k in market_data.keys() if k.startswith("COUNTRY_RISK_")])

    crashed_etfs = []
    tracked_etfs = []
    high_risk_etfs = []
    extreme_risk_etfs = []

    for key in country_risk_keys:
        item = market_data.get(key, {}) or {}
        etf = item.get("country_etf", "UNKNOWN")
        tracked_etfs.append(etf)

        if item.get("crash"):
            crashed_etfs.append(etf)

        risk_level = item.get("risk_level", "NORMAL")
        if risk_level == "HIGH":
            high_risk_etfs.append(etf)
        elif risk_level == "EXTREME":
            extreme_risk_etfs.append(etf)

    lines = []
    lines.append("### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)")

    if market_data.get("_STALE"):
        lines.append("⚠ Market Closed / Stale Data → Price-based geo signals muted.")
        lines.append("")

    # -----------------------
    # insufficient data
    # -----------------------
    if score is None:
        lines.append("- **Status:** N/A (insufficient data)")
        lines.append(f"- **Missing/Skipped:** {', '.join(missing) if missing else 'None'}")
        lines.append("- **Sovereign Spread factors included:** None")
        lines.append("- **Cosine Similarity Score:** N/A")
        lines.append("- **So What?:** 데이터가 쌓이거나 지표가 추가되면 조기경보 점수를 계산합니다.")

        if tracked_etfs:
            if crashed_etfs:
                lines.append(f"- **Country ETF Crash?** Yes ({', '.join(crashed_etfs)})")
            else:
                lines.append(f"- **Country ETF Crash?** No ({', '.join(tracked_etfs)})")
        else:
            lines.append("- **Country ETF Crash?** N/A")
        return "\n".join(lines)

    # -----------------------
    # main score
    # -----------------------
    coverage = geo.get("coverage")
    used_weight = geo.get("used_weight")
    total_defined_weight = geo.get("total_defined_weight")

    lines.append(f"- **Geo Stress Score (z-composite):** **{score:+.2f}**  *(Level: {level})*")

    if coverage is not None:
        lines.append(
            f"- **Coverage:** {coverage:.0%} *(used weight: {used_weight:.2f} / defined weight: {total_defined_weight:.2f})*"
        )

    if score_3d_avg is not None:
        lines.append(f"- **3D Avg Score:** {score_3d_avg:+.2f}")

    if momentum is not None:
        lines.append(f"- **Geo Momentum:** {momentum:+.2f} *(Status: {momentum_label})*")

    # -----------------------
    # cosine similarity section
    # -----------------------
    if cosine_score is not None:
        lines.append("")
        lines.append("**Historical Pattern Match (Cosine Similarity):**")
        lines.append(f"- **Closest Historical Match:** {cosine_match}")
        lines.append(f"- **Cosine Similarity Score:** {cosine_score:.3f}")
        lines.append(f"- **Similarity Signal:** {cosine_signal_label}")

        top_similarity = sorted(cosine_all.items(), key=lambda x: x[1], reverse=True)[:3]
        if top_similarity:
            lines.append("- **Top Similarity Matches:**")
            for name, sc in top_similarity:
                lines.append(f"  - {name}: {sc:.3f}")
    else:
        lines.append("- **Cosine Similarity Score:** N/A")

    # -----------------------
    # top contributors
    # -----------------------
    comps_sorted = sorted(
        comps,
        key=lambda x: abs(float(x.get("contrib", 0.0))),
        reverse=True
    )

    top = comps_sorted[:4]

    lines.append("- **Top Drivers:**")
    for c in top:
        nw = c.get("normalized_weight", c.get("weight", 0.0))

        if c.get("mode") == "pct":
            z1 = c.get("z_1d")
            z5 = c.get("z_5d")
            z1_txt = "NA" if z1 is None else f"{z1:+.2f}"
            z5_txt = "NA" if z5 is None else f"{z5:+.2f}"

            lines.append(
                f"  - {c['key']}: z_used={c['z_used']:+.2f} "
                f"(z1d={z1_txt}, z5d={z5_txt}, raw_w={c['weight']:.2f}, norm_w={nw:.2f}) "
                f"→ contrib={c['contrib']:+.2f}"
            )
        else:
            lines.append(
                f"  - {c['key']}: z_used={c['z_used']:+.2f} "
                f"(mode=level, raw_w={c['weight']:.2f}, norm_w={nw:.2f}) → contrib={c['contrib']:+.2f}"
            )

    # -----------------------
    # always show missing line
    # -----------------------
    lines.append(f"- **Missing/Skipped:** {', '.join(missing) if missing else 'None'}")

    # -----------------------
    # sovereign spread check
    # -----------------------
    spread_comps = [
        c for c in comps
        if str(c.get("key", "")).endswith("_SPREAD")
    ]

    if spread_comps:
        spread_names = ", ".join([c["key"] for c in spread_comps])
        lines.append(f"- **Sovereign Spread factors included:** {spread_names}")
    else:
        lines.append("- **Sovereign Spread factors included:** None")

    # -----------------------
    # So What → Trade Information
    # -----------------------
    lines.append("")
    lines.append("**Trade Information:**")

    # 1) Geo stress regime interpretation
    if level == "NORMAL":
        if momentum_label == "RISING":
            lines.append("- 지정학 스트레스는 여전히 정상 범위에 있지만 최근 압력이 상승하고 있는 중입니다. 경계 강화 필요.")
        elif momentum_label == "FALLING":
            lines.append("- 지정학 스트레스는 여전히 정상 범위에 있지만 최근 압력이 완화되고 있는 중입니다. 경계 유지.")
        else:
            lines.append("- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.")

    elif level == "ELEVATED":
        if momentum_label == "RISING":
            lines.append("- 스트레스 ‘상승’ 구간: 리스크 상승 가속 → 헤지/사이징 축소 검토.")
        elif momentum_label == "FALLING":
            lines.append("- 스트레스 ‘상승’ 구간: 리스크는 여전히 높지만 단기 압력은 완화 중. 과잉 대응보다는 선별 대응이 필요.")
        else:
            lines.append("- 지정학 스트레스가 경계 구간(ELEVATED)에 머물고 있습니다. 기존 레짐은 유지하되 EM·원자재·중국 민감 익스포저는 보수적으로 점검할 필요가 있습니다.")

    elif level == "HIGH":
        if momentum_label == "RISING":
            lines.append("- 스트레스 ‘높음’ + 상승 중: 리스크 익스포저 축소와 헤지 강화가 우선입니다.")
        elif momentum_label == "FALLING":
            lines.append("- 스트레스 ‘높음’이지만 단기 과열은 일부 완화 중입니다. 다만 고베타·EM 노출은 여전히 점검이 필요합니다.")
        else:
            lines.append("- 스트레스 ‘높음’: EM/고베타/레버리지 노출 점검 및 방어적 대응이 필요합니다.")

    else:
        lines.append("- 스트레스 ‘극단’: 디레버리징 + 방어자산/헤지 우선, 갭리스크 대비(현금/단기).")

    # 2) Similarity interpretation
    if cosine_score is not None:
        if cosine_score >= 0.80:
            lines.append(
                f"- 과거 위기 패턴과의 유사도가 높습니다. 현재 시장은 **{cosine_match}** 유형의 지정학 리스크 재현 가능성을 시사하므로, 단기 risk-off 대응을 강화할 필요가 있습니다."
            )
        elif cosine_score >= 0.60:
            lines.append(
                f"- 과거 위기 패턴과 부분적으로 유사합니다. 현재 시장은 **{cosine_match}** 계열의 초기 징후를 일부 보이고 있어, 관련 자산군과 지역 노출을 점검할 필요가 있습니다."
            )
        else:
            lines.append(
                f"- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **{cosine_match}** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다."
            )

    # 3) Country ETF crash line
    if crashed_etfs:
        lines.append(f"- **Country ETF Crash?** Yes ({', '.join(crashed_etfs)})")
    elif tracked_etfs:
        lines.append(f"- **Country ETF Crash?** No ({', '.join(tracked_etfs)})")
    else:
        lines.append("- **Country ETF Crash?** N/A")

    if extreme_risk_etfs:
        lines.append(f"- **Extreme Country Risk:** {', '.join(extreme_risk_etfs)}")
    elif high_risk_etfs:
        lines.append(f"- **High Country Risk:** {', '.join(high_risk_etfs)}")

    return "\n".join(lines)

def pseudo_gamma_filter(market_data: Dict[str, Any]) -> str:
    """
    7.3) Pseudo Gamma Filter (v1)

    목적:
    - 옵션 데이터 없이 시장의 감마 상태 추론
    - Drift + VIX + SEW 기반 구조 판단

    Output:
    - POSITIVE / NEGATIVE / TRANSITION
    """

    drift_score = market_data.get("DRIFT_SCORE", 0)
    drift_state = market_data.get("DRIFT_STATE", "N/A")

    vix = market_data.get("VIX", {}) or {}
    vix_level = vix.get("today")

    sew_state = str(market_data.get("SEW_STATUS", "N/A") or "N/A").upper()
    sew_event_type = str(market_data.get("SEW_EVENT_TYPE", "N/A") or "N/A").upper()

    gamma_state = "UNKNOWN"
    gamma_bias = ""
    strategy = ""

    # -------------------------
    # 1️⃣ Positive Gamma
    # -------------------------
    if vix_level is not None and vix_level < 18:
        if drift_score <= 1:
            gamma_state = "🟢 POSITIVE GAMMA"
            gamma_bias = "Mean-reverting / 딜러가 변동성 흡수"
            strategy = "눌림 매수 / 추격 금지"

    # -------------------------
    # 2️⃣ Negative Gamma
    # -------------------------
    if vix_level is not None and vix_level >= 20:
        if drift_score >= 3:
            gamma_state = "🔴 NEGATIVE GAMMA"
            gamma_bias = "Trend acceleration / 변동성 확대"
            strategy = "추세 추종 / 빠른 대응"

    # -------------------------
    # 3️⃣ Transition Zone (핵심)
    # -------------------------
    if gamma_state == "UNKNOWN":
        if drift_score >= 2:
            gamma_state = "🟡 TRANSITION"
            gamma_bias = "초기 방향성 형성 / 감마 전환 구간"
            strategy = "포지션 확대 신중 / 초기 진입 구간"
        else:
            gamma_state = "🟢 POSITIVE GAMMA (WEAK)"
            gamma_bias = "안정적 시장"
            strategy = "과도한 베팅 금지"

    # -------------------------
    # 4️⃣ SEW 결합 (리얼 핵심)
    # -------------------------
    combo_signal = ""

    if sew_state in ["ALERT", "CRISIS"]:
        if "NEGATIVE" in gamma_state:
            combo_signal = "🚨 SHOCK + NEGATIVE GAMMA → 폭발 구간"
        else:
            combo_signal = "⚠️ SHOCK but gamma unclear"
    else:
        if "TRANSITION" in gamma_state:
            combo_signal = "🟢 EARLY FLOW WITHOUT SHOCK"
        elif "POSITIVE" in gamma_state:
            combo_signal = "🟢 STABLE FLOW"
        else:
            combo_signal = "🔴 TREND ACCELERATION"

    # -------------------------
    # Output
    # -------------------------
    lines = []
    lines.append("### ⚡ 7.3) Pseudo Gamma Filter")
    lines.append("- **정의:** 옵션 데이터 없이 시장의 감마 상태 추론")
    lines.append("")

    lines.append(f"- **Gamma State:** {gamma_state}")
    lines.append(f"- **Bias:** {gamma_bias}")
    lines.append(f"- **Strategy:** {strategy}")
    lines.append("")
    lines.append(f"- **Drift Score:** {drift_score} ({drift_state})")
    lines.append(f"- **VIX:** {vix_level}")
    lines.append(f"- **SEW:** {sew_state} / {sew_event_type}")
    lines.append("")
    lines.append(f"- **🚀 Combo Signal:** {combo_signal}")

    market_data["GAMMA_STATE"] = gamma_state
    market_data["GAMMA_COMBO"] = combo_signal

    return "\n".join(lines)

# =========================
# 8) Incentive Filter
# =========================
def incentive_filter(market_data: Dict[str, Any]) -> str:
    """
    8) Incentive Filter (Wall St. Logic)
    실질 금리와 장단기 금리차를 활용해 자본의 '진짜 의도'를 파악
    """
    if market_data is None:
        market_data = {}
        
    state = market_data.get("FINAL_STATE", {}) or {}

    def fetch_val(key: str, default: float) -> float:
        # 1. FINAL_STATE에서 먼저 확인
        val = state.get(key.upper()) or state.get(key.lower())
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, dict):
            val = val.get("today")

        # 2. market_data 루트에서 다시 확인 (fallback)
        if val is None:
            node = market_data.get(key.upper()) or market_data.get(key.lower())
            if isinstance(node, (int, float)):
                return float(node)
            if isinstance(node, dict):
                val = node.get("today")

        try:
            return float(val) if val is not None else default
        except Exception:
            return default

    # -------------------------
    # 1) 데이터 로드 및 단위 보정
    # -------------------------
    raw_t10y2y = state.get("T10Y2Y") 
    if not isinstance(raw_t10y2y, (int, float)):
        raw_t10y2y = fetch_val("T10Y2Y", 0.0)

    # bp 단위 보정
    t10y2y_bp = raw_t10y2y * 100 if abs(raw_t10y2y) < 5 else raw_t10y2y
    
    rr_val = fetch_val("DFII10", 0.0)
    dxy_val = fetch_val("DXY", 100.0)

    # 2번 필터 스타일의 날짜 정보 가져오기 (추가된 부분)
    rr_asof = market_data.get("_DFII10_ASOF")
    dxy_asof = market_data.get("_DXY_ASOF")

    # -------------------------
    # 2) 리포트 문구 생성
    # -------------------------
    lines = []
    lines.append("### 🎯 8) Incentive Filter (Wall St. Logic)")
    lines.append("")
    lines.append(f"**핵심 신호:** 장단기차({t10y2y_bp:.2f}bp) | 실질금리({rr_val:.2f}%) | DXY({dxy_val:.2f})")
    
    # 💡 [추가] 날짜 정보가 있으면 한 줄 넣어주기 (2번 필터와 통일감)
    as_of_list = []
    if rr_asof: as_of_list.append(f"RealRate: {rr_asof}")
    if dxy_asof: as_of_list.append(f"DXY: {dxy_asof}")
    if as_of_list:
        lines.append(f"*(as of: {', '.join(as_of_list)} / FRED last available)*")
    
    lines.append("")

    # -------------------------
    # 3) 자본 흐름 로직 (Wall St. Insight)
    # -------------------------
    if rr_val < 1.0:
        incentive_text = "✅ **자본이 쏠리는 곳 (Long Incentive):**\nGrowth/Quality (QUAL) - 유동성 환경 우호 및 저금리 수혜"
    elif rr_val >= 2.0:
        incentive_text = "❌ **자본이 탈출하는 곳 (Short Incentive):**\n고금리(실질금리 2% 상회) 부담으로 인한 리스크 오프 신호"
    else:
        incentive_text = "Neutral - 자본의 방향성이 탐색 구간에 있음 (실질금리 정상화 과정)"

    lines.append(incentive_text)
    lines.append("")
    lines.append("- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.")
    
    return "\n".join(lines)

# =========================
# 9) Cause Filter
def cause_filter(market_data: Dict[str, Any]) -> str:
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    wti = _get_series(market_data, "WTI")
    vix = _get_series(market_data, "VIX")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    wti_dir = _sign_from(wti)
    vix_dir = _sign_from(vix)

    # -------------------------
    # 1) 지표 조합 기반 Narrative 판정 로직
    # -------------------------
    narrative = ""
    
    # CASE A: 전형적인 골디락스 / 리스크온 (금리↓, 달러↓, 유가↓, VIX↓)
    if us10y_dir <= 0 and dxy_dir <= 0 and vix_dir == -1:
        narrative = "금리·달러 안정에 따른 전형적인 '위험자산 선호(Risk-On)'"
    
    # CASE B: 비용 압박 완화 (유가↓, 금리↓)
    elif wti_dir == -1 and us10y_dir <= 0:
        narrative = "인플레이션 압력 둔화 및 비용 감소형 안도 랠리"
        
    # CASE C: 긴축 우려 / 리스크오프 (금리↑, 달러↑, VIX↑)
    elif us10y_dir == 1 and dxy_dir == 1 and vix_dir == 1:
        narrative = "긴축 공포 및 달러 수급 경색에 따른 '위험회피(Risk-Off)'"
        
    # CASE D: 스태그플레이션 우려 (유가↑, 금리↑)
    elif wti_dir == 1 and us10y_dir == 1:
        narrative = "비용 상승형 물가 부담 및 경기 둔화 우려 반영"
        
    # CASE E: 단순 유동성/심리 장세
    elif vix_dir == -1:
        narrative = "매크로 지표 혼조 속 시장 심리 개선 주도"
    
    else:
        narrative = "복합적 요인에 의한 지표 혼조 및 방향성 탐색"

    # -------------------------
    # 2) 출력 정리
    # -------------------------
    parts = []
    if us10y_dir == 1: parts.append("금리↑")
    elif us10y_dir == -1: parts.append("금리↓")
    if dxy_dir == 1: parts.append("달러↑")
    elif dxy_dir == -1: parts.append("달러↓")
    if wti_dir == 1: parts.append("유가↑")
    elif wti_dir == -1: parts.append("유가↓")
    if vix_dir == 1: parts.append("VIX↑")
    elif vix_dir == -1: parts.append("VIX↓")

    raw_signals = " + ".join(parts) if parts else "신호 없음"

    lines = []
    lines.append("### 🔍 9) Cause Filter")
    lines.append("- **질문:** 무엇이 이 움직임을 만들었는가?")
    lines.append(f"- **핵심 신호:** {raw_signals}")
    lines.append(f"- **최종 판정:** **{narrative}**") # 핵심 서사 출력
    
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
    # 1. 데이터 추출
    us10y = _get_series(market_data, "US10Y")
    dxy = _get_series(market_data, "DXY")
    vix = _get_series(market_data, "VIX")
    wti = _get_series(market_data, "WTI")
    gold = _get_series(market_data, "GOLD")
    rr = _get_series(market_data, "REAL_RATE")

    us10y_dir = _sign_from(us10y)
    dxy_dir = _sign_from(dxy)
    vix_dir = _sign_from(vix)
    wti_dir = _sign_from(wti)
    gold_dir = _sign_from(gold)

    # 값 / 변화율 추출
    rr_val = _to_float(rr.get("today")) if rr else None
    wti_val = _to_float(wti.get("today")) if wti else None

    us10y_pct = _to_float(us10y.get("pct_change")) if us10y else None
    dxy_pct = _to_float(dxy.get("pct_change")) if dxy else None
    vix_pct = _to_float(vix.get("pct_change")) if vix else None
    wti_pct = _to_float(wti.get("pct_change")) if wti else None
    gold_pct = _to_float(gold.get("pct_change")) if gold else None

    # 2. 상태 초기화
    state = "NEUTRAL"
    rationale = "글로벌 매크로 구조의 특이 신호가 감지되지 않음"

    # ---------------------------------------------------------
    # [NEW] Deadband / Meaningful move thresholds
    # ---------------------------------------------------------
    TH_DXY = 0.20
    TH_GOLD = 0.50
    TH_VIX = 1.00
    TH_US10Y = 0.20
    TH_WTI = 2.00

    dxy_up_meaningful = dxy_pct is not None and dxy_pct >= TH_DXY
    gold_up_meaningful = gold_pct is not None and gold_pct >= TH_GOLD
    vix_up_meaningful = vix_pct is not None and vix_pct >= TH_VIX
    us10y_down_meaningful = us10y_pct is not None and us10y_pct <= -TH_US10Y
    us10y_up_meaningful = us10y_pct is not None and us10y_pct >= TH_US10Y
    wti_up_meaningful = wti_pct is not None and wti_pct >= TH_WTI
    wti_down_meaningful = wti_pct is not None and wti_pct <= -TH_WTI

    # ---------------------------------------------------------
    # [12번 필터 안정화 로직 - 우선순위 판정]
    # ---------------------------------------------------------

    # A) 시스템적 헤지
    # 기존: dxy_dir == 1 and gold_dir == 1
    # 문제: 미세한 + 부호만으로도 발동
    # 개선: 의미 있는 상승 + 보조 리스크 신호 1개 동반 시에만 발동
    if dxy_up_meaningful and gold_up_meaningful and (vix_up_meaningful or us10y_down_meaningful):
        state = "SYSTEMIC HEDGE (시스템적 위험 회피)"
        rationale = "달러와 금의 의미 있는 동반 상승이 확인되며, 보조 리스크 신호까지 동반됨"

    # B) 에너지 주도 스태그플레이션
    elif (
        wti_val is not None and rr_val is not None
        and wti_val > 90
        and rr_val >= 2.0
        and wti_up_meaningful
    ):
        state = "ENERGY-DRIVEN STAGFLATION (에너지 주도 스태그)"
        rationale = f"긴축적인 실질금리({rr_val}%) 환경에서도 고유가가 의미 있게 유지/상승. 공급 측 구조 압박 가능성"

    # C) 글로벌 긴축 구조
    elif us10y_up_meaningful and dxy_up_meaningful:
        state = "GLOBAL FINANCIAL TIGHTENING (글로벌 긴축 구조)"
        rationale = "금리↑ + 달러↑가 모두 의미 있는 수준으로 나타나 글로벌 자본 조달 비용 압박"

    # D) 비용 주도 구조
    elif wti_up_meaningful and us10y_dir <= 0:
        state = "COST-PUSH STRUCTURE (비용 주도 구조)"
        rationale = "경기 지지(금리 하락/보합)가 필요한 상황에서 유가가 의미 있게 상승해 실물 비용 부담을 가중"

    # E) 수요 둔화 우려
    elif wti_down_meaningful and vix_up_meaningful:
        state = "WEAK DEMAND + RISK-OFF (수요 둔화)"
        rationale = "유가 하락과 변동성 상승이 동시에 의미 있게 나타나 성장 둔화 우려를 반영"

    # ---------------------------------------------------------
    # 3. 리포트 조립
    # ---------------------------------------------------------
    lines = []
    lines.append("### 🏗️ 12) Structural Filter (v3)")
    lines.append("- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?")

    signals = [
        f"US10Y({_dir_str(us10y_dir)})",
        f"DXY({_dir_str(dxy_dir)})",
        f"GOLD({_dir_str(gold_dir)})",
        f"VIX({_dir_str(vix_dir)})",
        f"WTI({_dir_str(wti_dir)})",
    ]
    lines.append(f"- **핵심 신호:** {' / '.join(signals)}")
    lines.append(
        f"- **Meaningful Move Check:** "
        f"DXY={dxy_pct if dxy_pct is not None else 'N/A'} / "
        f"GOLD={gold_pct if gold_pct is not None else 'N/A'} / "
        f"US10Y={us10y_pct if us10y_pct is not None else 'N/A'} / "
        f"VIX={vix_pct if vix_pct is not None else 'N/A'} / "
        f"WTI={wti_pct if wti_pct is not None else 'N/A'}"
    )
    lines.append(f"- **판정:** **{state}**")
    lines.append(f"- **근거:** {rationale}")

    market_data["STRUCT_V2_STATE"] = state

    return "\n".join(lines)





    
from typing import Dict, Any, Optional

def narrative_engine_filter(market_data: Dict[str, Any]) -> str:
    """
    Narrative Engine v2.2 (Restored Original Format + Drift Add-on + Realistic Scoring)

    Structure + Sentiment + Credit + Liquidity + Phase
    + Drift (보조 가점만)
    → Final Risk Action + Risk Budget (0~100)

    원칙:
    - 기존 13번 양식 유지
    - FINAL_STATE 정상 저장
    - Drift는 메인 엔진이 아니라 보조 신호로만 반영
    - 점수는 기존보다 과도하게 85로 치우치지 않도록 보수화
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
    # --------------------------------------------------
    # 1️⃣ Pull Signals
    # --------------------------------------------------
    struct_v2 = str(market_data.get("STRUCT_V2_STATE", "NEUTRAL")).upper()
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
    
    pos_z = _to_float(market_data.get("SP500_POS_Z", 0.0))
    if pos_z is None:
        pos_z = 0.0
        # --------------------------------------------------
    # 1.5️⃣ Drift (보조 신호만)
    # --------------------------------------------------
    drift = market_data.get("DRIFT", {}) or {}
    drift_score = drift.get("score", market_data.get("DRIFT_SCORE", 0))
    try:
        drift_score = int(drift_score)
    except Exception:
        drift_score = 0

    drift_state = str(
        drift.get("state", market_data.get("DRIFT_STATE", "N/A")) or "N/A"
    )
    drift_label = str(drift.get("label", "N/A") or "N/A")
    drift_combo = str(drift.get("combo_signal", "NONE") or "NONE")

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
    if not mixed:
        if easing and not tightening:
            budget += 10
        elif tightening and not easing:
            budget -= 10

    # Credit tilt (보수화)
    if credit_calm is True:
        budget += 5
    elif credit_calm is False:
        budget -= 10

    # Liquidity tilt (보수화)
    if liq_dir_tag == "UP":
        budget += 5
    elif liq_dir_tag == "DOWN":
        budget -= 10

    if liq_level_bucket == "HIGH":
        budget += 5
    elif liq_level_bucket == "LOW":
        budget -= 5

    # --------------------------------------------------
    # 2.5️⃣ Structural v2 Penalty
    # --------------------------------------------------
    struct_v2_kr = "정상"
    struct_alert = ""
    v2_cap = 100

    if "SYSTEMIC" in struct_v2:
        budget -= 20
        struct_v2_kr = "시스템위기"
        struct_alert = "🚨 시스템 불신 감지"
        v2_cap = 30
    elif "STAGFLATION" in struct_v2:
        budget -= 15
        struct_v2_kr = "스태그플레이션"
        struct_alert = "⚠️ 에너지 비용 전이"
        v2_cap = 40

    # --------------------------------------------------
    # 2.7️⃣ Drift Adjustment (ADD ONLY)
    # --------------------------------------------------
    drift_tilt = 0
    if drift_score >= 4:
        drift_tilt = 5
    elif drift_score >= 2:
        drift_tilt = 3
    elif drift_score <= -2:
        drift_tilt = -5

    budget += drift_tilt
    
   # --------------------------------------------------
    # 2.7️⃣ Drift Adjustment (ADD ONLY)
    # --------------------------------------------------
    drift_tilt = 0
    if drift_score >= 4:
        drift_tilt = 5
    elif drift_score >= 2:
        drift_tilt = 3
    elif drift_score <= -2:
        drift_tilt = -5
    
    budget += drift_tilt
    
    # --------------------------------------------------
    # 2.75️⃣ Flow / Gamma Alignment Boost (ADD ONLY)
    # --------------------------------------------------
    flow = market_data.get("INSTITUTIONAL_FLOW", {}) or {}
    gamma_state = str(market_data.get("GAMMA_STATE", "N/A") or "N/A").upper()
    
    flow_score = flow.get("score", 0)
    try:
        flow_score = int(flow_score)
    except Exception:
        flow_score = 0
    
    flow_gamma_tilt = 0
    
    # 상승 초기 정렬: Drift + Flow + Gamma TRANSITION
    if drift_score >= 2 and flow_score >= 3 and "TRANSITION" in gamma_state:
        flow_gamma_tilt = 3
    
    # 더 강한 상승 압력: Drift + Flow 강하고 Gamma POSITIVE
    elif drift_score >= 3 and flow_score >= 4 and "POSITIVE" in gamma_state:
        flow_gamma_tilt = 5
    
    # 하락/충돌 상황은 아직 보수적으로 0 처리
    # (지금은 시스템 안정화가 우선이라 과한 감점 넣지 않음)
    
    budget += flow_gamma_tilt

    # --------------------------------------------------
    # 2.8️⃣ Positioning Penalty
    # --------------------------------------------------
    pos_alert = ""
    if pos_z >= 2.0:
        budget -= 8
        pos_alert = " ⚠️ 수급 과열 감지"
    elif pos_z >= 1.5:
        budget -= 4
        pos_alert = " ⚠️ 수급 다소 과열"

    # --------------------------------------------------
    # 3️⃣ Phase Cap
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

    if "SYSTEMIC" in struct_v2 or "STAGFLATION" in struct_v2:
        cap = min(cap, 30)

    final_cap = min(cap, v2_cap)
    budget = min(int(round(budget)), final_cap)
    budget = _clamp(budget, 0, 100)
    market_data["RISK_BUDGET"] = budget

    # --------------------------------------------------
    # 4️⃣ Final Action
    # --------------------------------------------------
    if budget >= 70:
        action = "INCREASE"
    elif budget <= 20:
        action = "STRONG REDUCE"
    elif budget <= 40:
        action = "REDUCE"
    else:
        action = "HOLD"

    # 포지셔닝 과열 시 액션 오버라이드
    if pos_z >= 2.0:
        if action == "INCREASE":
            action = "HOLD (POS_OVERHEATED)"
        elif action == "HOLD":
            action = "REDUCE (POS_OVERHEATED)"

    # --------------------------------------------------
    # 5️⃣ Narrative Line
    # --------------------------------------------------
    struct_tag = "MIXED"
    if not mixed:
        if easing and not tightening:
            struct_tag = "EASING"
        elif tightening and not easing:
            struct_tag = "TIGHTENING"

    struct_tag_final = f"{struct_tag}({struct_v2_kr})" if struct_v2_kr != "정상" else struct_tag

    credit_tag = "안정" if credit_calm is True else ("불안" if credit_calm is False else "N/A")
    liq_dir_kr = {"UP": "증가", "DOWN": "감소", "FLAT": "보합", "N/A": "N/A"}[liq_dir_tag]
    liq_lvl_kr = {"HIGH": "높음", "MID": "중간", "LOW": "낮음", "N/A": "N/A"}.get(liq_level_bucket, "N/A")
    liq_tag = f"{liq_dir_kr}/{liq_lvl_kr}"

    narrative = (
        f"구조={struct_tag_final} / 심리={sent_state} / 유동성={liq_tag} / "
        f"크레딧={credit_tag} / 드리프트={drift_state} ({drift_label}) / "
        f"수급={pos_z:.2f}{pos_alert} → Phase={phase}"
    )

    # --------------------------------------------------
    # --------------------------------------------------
    # 6.5️⃣ Final State Object
    # 기존 FINAL_STATE(FRED_EXTRA 등)를 보존하면서 13번 결과만 업데이트
    # --------------------------------------------------
    existing_final_state = market_data.get("FINAL_STATE", {}) or {}
    
    final_state = {
        **existing_final_state,
    
        "phase": phase,
        "phase_cap": cap,
        "risk_action": action,
        "risk_budget": budget,
    
        "structure_tag": struct_tag,
        "policy_bias_line": policy_bias_line,
    
        "sentiment_fear_greed": fear,
        "sentiment_state": sent_state,
    
        "credit_calm": credit_calm,
        "hy_oas_today": hy_oas_today,
    
        "liquidity_dir": liq_dir_tag,
        "liquidity_level_bucket": liq_level_bucket,
        "net_liq_pct_change": net_liq_pct,
    
        "pos_z": pos_z,
    
        "drift_score": drift_score,
        "drift_state": drift_state,
        "drift_label": drift_label,
        "drift_combo_signal": drift_combo,
        "drift_tilt": drift_tilt,
        "flow_gamma_tilt": flow_gamma_tilt,
    
        "narrative_line": narrative,
    }
    market_data["FINAL_STATE"] = final_state

    # --------------------------------------------------
    # 6️⃣ Output (원래 양식 복구)
    # --------------------------------------------------
    lines = []
    lines.append("### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)")
    lines.append("- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정")
    lines.append("- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문")
    lines.append("")
    lines.append(f"- **Structure Bias:** {policy_bias_line} ({struct_v2_kr})")
    lines.append(f"- **Sentiment (Fear&Greed):** {fear if fear is not None else 'N/A'} ({sent_state})")
    lines.append(f"- **Credit Calm:** {credit_calm}")
    lines.append(f"- **Liquidity (NET_LIQ):** {liq_dir_tag} ({liq_level_bucket})")
    lines.append(f"- **Phase:** {phase} (Cap: {cap})")

    if struct_alert:
        lines.append(f"- **[SPECIAL ALERT]**: **{struct_alert}** (Structural Cap: {v2_cap})")

    lines.append(f"- **Drift:** {drift_state} / {drift_label} / {drift_combo}")
    lines.append(f"- **Drift Score:** {drift_score}")
    lines.append("")
    lines.append(f"- **🎯 Final Risk Action:** **{action}**")
    lines.append(f"- **Risk Budget (0~100):** **{budget}**")
    lines.append(f"- **Narrative:** {narrative}")

    return "\n".join(lines)

    
def divergence_monitor_filter(market_data: Dict[str, Any]) -> str:
    """
    14) Divergence Monitor (Upgraded with Positioning Fragility Engine)
    
    [핵심 로직]
    - Macro(Structure) vs Price(Regime) 사이의 괴리 분석
    - Positioning(Z-Score, Gamma, CTA)의 '임계치'와 '충돌'을 통한 폭발 가능성 진단
    """

    # 1️⃣ 기초 데이터 로드
    policy_bias_line = str(market_data.get("POLICY_BIAS_LINE", ""))
    market_regime = str(market_data.get("MARKET_REGIME", "N/A")).upper()
    vix_series = _get_series(market_data, "VIX") or {}
    vix_value = float(vix_series.get("today", 20)) 

    # 2️⃣ 포지셔닝 데이터 추출
    pos_z = float(market_data.get("SP500_POS_Z", 0.0))
    gamma = float(market_data.get("DEALER_GAMMA_BIAS", 1.0)) 
    cta = float(market_data.get("CTA_MOMENTUM_SCORE", 0.0))

    # 3️⃣ Structure(정책) & Price(시장) 판별
    structure = "EASING" if "EASING" in policy_bias_line.upper() else \
                "TIGHTENING" if "TIGHTENING" in policy_bias_line.upper() else "MIXED"
    price = "RISK-ON" if "RISK-ON" in market_regime else \
            "RISK-OFF" if "RISK-OFF" in market_regime else "MIXED"

    # [고도화 로직 1: 국면별 가변 임계치]
    # 관망/긴축 국면에서는 1.8만 넘어도 예민하게 반응, 완화 국면에서는 2.2까지 허용
    threshold_z = 1.8 if price != "RISK-ON" or structure == "TIGHTENING" else 2.2

    # [고도화 로직 2: 수급 취약성(Fragility) 판정]
    # 기계(CTA)는 쏠렸는데 딜러(Gamma)가 받아줄 힘이 없는 'Run 준비' 상태
    is_fragile = (abs(cta) > 0.8 and gamma < 0.5)

    # 4️⃣ 판정 및 결과 조립
    status = "ALIGNED"
    explanation = "구조와 가격, 수급이 조화를 이루며 추세 유지 중"
    action_signal = "STAY (포지션 유지)"

    # CASE A: 정책 완화 vs 가격 하락 (Capitulation 체크)
    if structure == "EASING" and price == "RISK-OFF":
        if pos_z < -threshold_z and cta < -0.7:
            status = "🚀 CAPITULATION / GENERATIONAL BUY"
            explanation = f"정책 완화 속 항복 매물 발생(Z:{pos_z:.2f}). 기계적 매도 정점 국면."
            action_signal = "AGGRESSIVE ACCUMULATE (공격적 매수)"
        else:
            status = "BEAR TRAP / DISCOUNT"
            explanation = "유동성 구조는 우호적이나 일시적 수급 꼬임"
            action_signal = "ACCUMULATE (분할 매수)"

    # CASE B: 정책 긴축 vs 가격 상승 (Bull Trap 체크)
    elif structure == "TIGHTENING" and price == "RISK-ON":
        if pos_z > threshold_z or is_fragile:
            status = "🚨 EXTREME BULL TRAP / FRAGILITY"
            explanation = f"긴축 중 가격 과열. 특히 수급 취약성(Gamma:{gamma:.2f}) 감지됨. 폭락 전 마지막 불꽃."
            action_signal = "EXIT / PROTECT CAPITAL (RUN 액션 준비)"
        else:
            status = "BULL TRAP / OVERHEATED"
            explanation = "긴축 구조 속 가격 상승. 점진적 과열 국면"
            action_signal = "REDUCE RISK (익절 시작)"

    # CASE C: 추세 고갈 (Trend Exhaustion)
    elif abs(pos_z) > threshold_z:
        status = "⚡ TREND EXHAUSTION"
        explanation = f"추세와 정책은 일치하나 포지션 에너지 고갈(Z:{pos_z:.2f}). 반전 가능성 상존."
        action_signal = "MONITOR REVERSAL (RUN 액션 준비)"

    # 5️⃣ 리포트 텍스트 생성
    lines = []
    lines.append("### ⚠ 14) Divergence Monitor (Macro vs Positioning)")
    lines.append("- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단")
    lines.append("- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?")
    lines.append("")
    
    lines.append(f"- **Structure(3번):** `{structure}` | **Price(Regime):** `{price}` | **VIX:** `{vix_value:.2f}`")
    
    # 세연 님의 Run 가이드라인을 명시적으로 리포트에 포함
    pos_line = (
        f"- **Positioning Data:** "
        f"Z-Score: `{pos_z:.2f}` (>{threshold_z} 시 Run) | "
        f"Gamma: `{gamma:.2f}` (<0.5 시 Run) | "
        f"CTA: `{cta:.1f}` (추세 변곡점 확인)"
    )
    lines.append(pos_line)
    
    lines.append(f"- **Status:** **{status}** -> **해석:** {explanation}")
    lines.append(f"- **Action Signal:** 🚨 **{action_signal}**")

    return "\n".join(lines)
    #Build

def volatility_controlled_exposure_filter(market_data: Dict[str, Any]) -> str:
    """
    🎯 15) Volatility-Controlled Exposure (v2.6 - Dead Man's Switch Integrated)

    업그레이드:
    - [CRITICAL] Dead Man's Switch: POS_Z 과열 및 Slope 폭주 시 강제 0%
    - VIX 레벨 + 변화율 반영
    - Positioning Data (Gamma, CTA) 연동 가중치 적용
    - Exposure smoothing 및 Phase cap 적용
    """

    # ---------------------------
    # Helpers
    # ---------------------------
    def _to_float(x) -> Optional[float]:
        if x is None: return None
        if isinstance(x, (int, float)): return float(x)
        try:
            return float(str(x).replace(",", "").replace("%", "").strip())
        except Exception:
            return None

    def _clamp(x, lo=0, hi=100):
        return max(lo, min(int(round(x)), hi))

    # ---------------------------
    # Inputs
    # ---------------------------
    risk_budget = _to_float(market_data.get("RISK_BUDGET", 50)) or 50.0
    phase = str(market_data.get("MARKET_REGIME", "N/A")).upper()

    vix_series = market_data.get("VIX", {}) or {}
    vix_today = _to_float(vix_series.get("today"))
    vix_pct = _to_float(vix_series.get("pct_change"))

    # 14번 포지셔닝 데이터 + 기울기(Slope) 추출
    pos_z = _to_float(market_data.get("SP500_POS_Z", 0.0))
    
    pos_slope = _to_float(market_data.get("POS_SLOPE"))
    if pos_slope is None:
        pos_slope = get_recent_pos_slope("data/positioning_data.csv")
        market_data["POS_SLOPE"] = pos_slope
    
    gamma = _to_float(market_data.get("DEALER_GAMMA_BIAS", 1.0))
    cta = _to_float(market_data.get("CTA_MOMENTUM_SCORE", 1.0))
    
    # 🔍 DEBUG (여기 위치 정확함)
    print("[DEBUG][15 POSITIONING INPUT]")
    print(f"SP500_POS_Z={pos_z}")
    print(f"POS_SLOPE={pos_slope}")
    print(f"GAMMA={gamma}")
    print(f"CTA={cta}")
    
    prev_exposure = _to_float(market_data.get("PREV_EXPOSURE"))
    if prev_exposure is None:
        prev_exposure = risk_budget

    # ---------------------------
    # 0️⃣ [NEW] Dead Man's Switch (최우선 브레이크)
    # ---------------------------
    is_deadman_on = False  # 변수명 통일
    deadman_reason = ""
    
    # 1. POS_Z가 2.0을 넘으면 (과열/항복 극단)
    if abs(pos_z) > 2.0:
        is_deadman_on = True
        deadman_reason = f"POS_Z Extreme ({pos_z:.2f})"
    
    # 2. 기울기가 급격할 때 (폭주)
    if abs(pos_slope) > 0.5: 
        is_deadman_on = True
        deadman_reason = f"Aggressive Slope ({pos_slope:.2f})"

    # ---------------------------
    # 1️⃣ Phase Cap
    # ---------------------------
    cap = 100
    if "WAITING" in phase or "RANGE" in phase: cap = 60
    elif "TRANSITION" in phase or "MIXED" in phase: cap = 70
    elif "RISK-ON" in phase: cap = 85
    elif "RISK-OFF" in phase: cap = 35

    exposure = min(risk_budget, cap)

    # ---------------------------
    # 2️⃣ Multiplier: Volatility (VIX)
    # ---------------------------
    vol_state = "N/A"
    multiplier = 1.0

    if vix_today is not None:
        if vix_today < 14:
            vol_state = "LOW"; multiplier *= 1.05
        elif vix_today < 20:
            vol_state = "NORMAL"
        elif vix_today < 30:
            vol_state = "HIGH"; multiplier *= 0.80
        else:
            vol_state = "EXTREME"; multiplier *= 0.60

    if vix_pct is not None:
        if vix_pct > 5: multiplier *= 0.85  
        elif vix_pct < -5: multiplier *= 1.05 

    # ---------------------------
    # 3️⃣ Multiplier: Positioning (Gamma/CTA)
    # ---------------------------
    pos_multiplier = 1.0
    pos_notes = []

    if gamma < 0.5:
        pos_multiplier *= 0.85
        pos_notes.append(f"Low Gamma({gamma:.2f})")
    
    if cta <= 0:
        pos_multiplier *= 0.90
        pos_notes.append(f"Bearish CTA({cta:.1f})")

    multiplier *= pos_multiplier
    exposure *= multiplier

    # ---------------------------
    # 4️⃣ Guardrail & Smoothing
    # ---------------------------
    hy_oas = market_data.get("HY_OAS", {}) or {}
    hy_level = _to_float(hy_oas.get("today"))
    if hy_level is not None and hy_level > 5:
        exposure *= 0.75 

    if prev_exposure is not None:
        exposure = 0.7 * prev_exposure + 0.3 * exposure

    # 🚨 Dead Man's Switch 적용
    if is_deadman_on:
        exposure = 0 

    exposure = min(exposure, cap)
    exposure = _clamp(exposure)
    market_data["PREV_EXPOSURE"] = exposure

    # ---------------------------
    # Output 구성 (리포트 시각화)
    # ---------------------------
    vix_display = f"{vix_today:.2f}" if vix_today is not None else "N/A"
    vix_pct_display = f"{vix_pct:+.2f}%" if vix_pct is not None else "N/A"
    
    lines = []
    lines.append("### 🎯 15) Volatility-Controlled Exposure (v2.6)")
    lines.append("- **정의:** Risk Budget을 실제 익스포저로 변환 (Positions & Deadman Switch)")
    lines.append("- **추가 이유:** 수급 과열(POS_Z)이나 급격한 쏠림 발생 시 강제 시스템 셧다운")
    lines.append("")
    lines.append(f"- **Risk Budget:** {risk_budget:.0f} | **Phase Cap:** {cap}")
    lines.append(f"- **VIX Level:** {vix_display} ({vol_state}) | **Change:** {vix_pct_display}")
    
    # 🚨 데드맨 스위치 작동 여부에 따른 리포트 분기
    if is_deadman_on:
        lines.append(f"- **🚨 STATUS:** **DEAD MAN'S SWITCH ACTIVATED**")
        lines.append(f"- **Reason:** {deadman_reason}")  # 위에서 선언한 이름으로 수정
        lines.append(f"- **Action:** 포지션 진입 금지 및 기존 물량 청산 권고")
    else:
        lines.append(f"- **Final Multiplier:** {multiplier:.2f}x (Vol x Pos)")
        if pos_notes:
            lines.append(f"- **Positioning Brake:** 적용됨 | ⚠️ {', '.join(pos_notes)}")
        lines.append(f"- **Slope Intensity:** {pos_slope:.4f} (Stable)")

    lines.append("")
    lines.append(f"- **📊 Recommended Exposure:** **{exposure}%**")
    market_data["RECOMMENDED_EXPOSURE"] = exposure
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


def dynamic_vix_threshold(market_data: Dict[str, Any]) -> Tuple[int, str, str]:
    """
    VIX 동적 임계값 판단
    반환:
      (score, label, detail)
    """

    state = market_data.get("FINAL_STATE", {}) or {}

    def fetch_val(key: str, default: float) -> float:
        val = state.get(key.upper())
        if val is None:
            val = state.get(key.lower())
        if val is None:
            node = market_data.get(key.upper(), {})
            if isinstance(node, dict):
                val = node.get("today")
        try:
            return float(val) if val is not None else default
        except Exception:
            return default

    current_vix = fetch_val("VIX", 20.0)

    history = (
        market_data.get("_VIX_HISTORY")
        or market_data.get("VIX_HISTORY")
        or market_data.get("vix_history")
    )

    if isinstance(history, (list, tuple)):
        clean_hist = []
        for x in history:
            try:
                if x is not None:
                    clean_hist.append(float(x))
            except Exception:
                pass

        if len(clean_hist) >= 20:
            recent20 = clean_hist[-20:]
            avg20 = sum(recent20) / len(recent20)

            if avg20 > 0:
                ratio = current_vix / avg20

                if ratio >= 1.25:
                    return (3, "VOLATILITY SHOCK", f"dynamic mode: VIX {current_vix:.1f} / 20D avg {avg20:.1f} = {ratio:.2f}x")
                elif ratio >= 1.10:
                    return (2, "VOLATILITY ELEVATED", f"dynamic mode: VIX {current_vix:.1f} / 20D avg {avg20:.1f} = {ratio:.2f}x")
                elif ratio <= 0.85:
                    return (-2, "VOLATILITY CALM", f"dynamic mode: VIX {current_vix:.1f} / 20D avg {avg20:.1f} = {ratio:.2f}x")
                else:
                    return (0, "VOLATILITY NORMAL", f"dynamic mode: VIX {current_vix:.1f} / 20D avg {avg20:.1f} = {ratio:.2f}x")

    # fallback absolute mode
    if current_vix >= 30:
        return (3, "VOLATILITY SHOCK", f"absolute mode: VIX {current_vix:.1f}")
    elif current_vix >= 25:
        return (2, "VOLATILITY ELEVATED", f"absolute mode: VIX {current_vix:.1f}")
    elif current_vix <= 15:
        return (-2, "VOLATILITY CALM", f"absolute mode: VIX {current_vix:.1f}")
    else:
        return (0, "VOLATILITY NORMAL", f"absolute mode: VIX {current_vix:.1f}")

from typing import Dict, Any, List, Tuple, Optional


def dynamic_vix_threshold(market_data: Dict[str, Any]) -> Tuple[int, str, str]:
    """
    VIX 동적 임계값 판단
    반환:
      (score, label, detail)
    """

    state = market_data.get("FINAL_STATE", {}) or {}

    def fetch_val(key: str, default: float) -> float:
        val = state.get(key.upper())
        if val is None:
            val = state.get(key.lower())
        if val is None:
            node = market_data.get(key.upper(), {})
            if isinstance(node, dict):
                val = node.get("today")
        try:
            return float(val) if val is not None else default
        except Exception:
            return default

    current_vix = fetch_val("VIX", 20.0)

    history = (
        market_data.get("_VIX_HISTORY")
        or market_data.get("VIX_HISTORY")
        or market_data.get("vix_history")
    )

    if isinstance(history, (list, tuple)):
        clean_hist = []
        for x in history:
            try:
                if x is not None:
                    clean_hist.append(float(x))
            except Exception:
                pass

        if len(clean_hist) >= 20:
            recent20 = clean_hist[-20:]
            avg20 = sum(recent20) / len(recent20)

            if avg20 > 0:
                ratio = current_vix / avg20

                if ratio >= 1.25:
                    return (3, "VOLATILITY SHOCK", f"dynamic mode: VIX {current_vix:.1f} / 20D avg {avg20:.1f} = {ratio:.2f}x")
                elif ratio >= 1.10:
                    return (2, "VOLATILITY ELEVATED", f"dynamic mode: VIX {current_vix:.1f} / 20D avg {avg20:.1f} = {ratio:.2f}x")
                elif ratio <= 0.85:
                    return (-2, "VOLATILITY CALM", f"dynamic mode: VIX {current_vix:.1f} / 20D avg {avg20:.1f} = {ratio:.2f}x")
                else:
                    return (0, "VOLATILITY NORMAL", f"dynamic mode: VIX {current_vix:.1f} / 20D avg {avg20:.1f} = {ratio:.2f}x")

    # fallback absolute mode
    if current_vix >= 30:
        return (3, "VOLATILITY SHOCK", f"absolute mode: VIX {current_vix:.1f}")
    elif current_vix >= 25:
        return (2, "VOLATILITY ELEVATED", f"absolute mode: VIX {current_vix:.1f}")
    elif current_vix <= 15:
        return (-2, "VOLATILITY CALM", f"absolute mode: VIX {current_vix:.1f}")
    else:
        return (0, "VOLATILITY NORMAL", f"absolute mode: VIX {current_vix:.1f}")

def rank_deleveraging_priority(
    score: Dict[str, float],
    weights: Dict[str, float],
    divergence_flags: Dict[str, str],
    momentum_scores: Dict[str, float] = None,
) -> list:
    """
    Deleveraging Priority Engine v1
    - 노출도를 줄여야 할 때 어떤 섹터부터 줄일지 우선순위 산출
    - 아직 실제 weight를 깎지는 않고, '순위'만 만든다.
    """

    if momentum_scores is None:
        momentum_scores = {}

    priority_rows = []

    for sector, weight in weights.items():
        s_score = float(score.get(sector, 0.0))
        div_flag = divergence_flags.get(sector, "ALIGNED")

        # 기본 위험 점수
        risk_score = 0.0

        # 1) Divergence 우선
        if div_flag == "NEGATIVE_DIVERGENCE":
            risk_score += 4.0
        elif div_flag == "POSITIVE_DIVERGENCE":
            risk_score -= 1.0

        # 2) 낮은 score 우선 감축
        if s_score < 0:
            risk_score += 3.0
        elif s_score == 0:
            risk_score += 2.0
        elif s_score <= 1:
            risk_score += 1.0

        # 3) 고위험 섹터 가산
        if sector in ["Technology", "Consumer Discretionary", "Real Estate"]:
            risk_score += 1.0

        # 4) 방어 섹터는 감축 우선순위 낮춤
        if sector in ["Consumer Staples", "Health Care", "Utilities"]:
            risk_score -= 0.5

        # 5) 비중이 큰 섹터는 감축 후보
        if weight >= 20:
            risk_score += 1.0
        elif weight >= 10:
            risk_score += 0.5

        priority_rows.append({
            "sector": sector,
            "weight": weight,
            "score": s_score,
            "divergence": div_flag,
            "risk_score": round(risk_score, 2),
        })

    # risk_score 높은 순 = 먼저 줄일 대상
    priority_rows = sorted(
        priority_rows,
        key=lambda x: (-x["risk_score"], x["score"], -x["weight"])
    )

    return priority_rows

def build_tactical_allocation(
    score: Dict[str, float],
    ow_sorted: list,
    divergence_flags: Dict[str, str],
    total_exposure: float,
    deleveraging_required: bool = False,
) -> Dict[str, Any]:
    """
    18.5) Tactical Asset Allocation Builder
    - 양수 점수 섹터만 대상으로 비중 계산
    - Divergence 반영
    - Deleveraging 상황에서는 위험 섹터를 우선 축소
    - 총 노출도(total_exposure) 안에서 정규화
    """

    positive_scores = {s: score[s] for s in ow_sorted if score.get(s, 0) > 0}
    total_score_sum = sum(positive_scores.values())

    weights = {}

    if total_score_sum <= 0:
        return {
            "weights": {},
            "cash_weight": round(100.0 - total_exposure, 1),
            "total_score_sum": 0,
        }

    # 1) 기본 비중 계산
    for sector, s_score in positive_scores.items():
        weights[sector] = (s_score / total_score_sum) * total_exposure

    # 2) Divergence 반영
    for sector in list(weights.keys()):
        flag = divergence_flags.get(sector, "ALIGNED")

        if flag == "NEGATIVE_DIVERGENCE":
            weights[sector] *= 0.65
        elif flag == "POSITIVE_DIVERGENCE":
            weights[sector] *= 1.25

    # 3) 디레버리징 상황일 때 위험 섹터 추가 축소
    if deleveraging_required:
        for sector in list(weights.keys()):
            flag = divergence_flags.get(sector, "ALIGNED")
            sector_score = score.get(sector, 0)

            if flag == "NEGATIVE_DIVERGENCE":
                weights[sector] *= 0.50

            elif sector_score <= 1:
                weights[sector] *= 0.70

            elif sector in ["Technology", "Consumer Discretionary", "Communication Services", "Real Estate"]:
                weights[sector] *= 0.85

    # 4) 다시 total_exposure 안으로 정규화
    adjusted_sum = sum(weights.values())
    if adjusted_sum > 0:
        for sector in weights:
            weights[sector] = (weights[sector] / adjusted_sum) * total_exposure

    # 5) 반올림
    for sector in weights:
        weights[sector] = round(weights[sector], 1)

    cash_weight = round(100.0 - total_exposure, 1)

    return {
        "weights": weights,
        "cash_weight": cash_weight,
        "total_score_sum": total_score_sum,
    }

def sector_allocation_filter(market_data: Dict[str, Any]) -> str:
    """
    18) Sector Allocation Engine (v3.3)
    반영:
    1) Curve 구간 세분화
    2) Signal priority hierarchy
    3) Score 기반 정렬
    4) Financials cap
    5) rationale 중복 완화
    6) sector별 score breakdown 추가
    7) 🔥 Drift / Gamma / Institutional Flow overlay 추가
       - 기존 이론 로직은 유지
       - 실제 돈 흐름은 overlay 점수로만 반영
    """

    state = market_data.get("FINAL_STATE", {}) or {}

    def fetch_val(key: str, default: float) -> float:
        val = state.get(key.upper())
        if val is None:
            val = state.get(key.lower())

        if val is None:
            node = market_data.get(key.upper(), {})
            if isinstance(node, dict):
                val = node.get("today")

        try:
            return float(val) if val is not None else default
        except Exception:
            return default

    def fetch_state_str(key: str, default: str) -> str:
        val = state.get(key)
        if val is None:
            val = state.get(key.upper())
        if val is None:
            val = state.get(key.lower())
        return str(val if val is not None else default).upper()

    # -------------------------
    # 1) 핵심 변수
    # -------------------------
    t10y2y = fetch_val("T10Y2Y", 0.0)
    vix = fetch_val("VIX", 20.0)

    phase = fetch_state_str("phase", "N/A")
    liq_dir = fetch_state_str("liquidity_dir", "N/A")
    liq_lvl = fetch_state_str("liquidity_level_bucket", "N/A")
    credit_calm = state.get("credit_calm", None)

    # 🔥 Flow / Gamma / Drift overlay inputs
    inst_flow = market_data.get("INSTITUTIONAL_FLOW", {}) or {}
    flow_score = inst_flow.get("score", 0)
    try:
        flow_score = int(flow_score)
    except Exception:
        flow_score = 0

    flow_state = str(inst_flow.get("state", "N/A") or "N/A").upper()
    drift_label = str(
        inst_flow.get("drift_label")
        or state.get("drift_label")
        or market_data.get("DRIFT_LABEL")
        or "N/A"
    ).upper()
    gamma_state = str(
        inst_flow.get("gamma_state")
        or market_data.get("GAMMA_STATE")
        or "N/A"
    ).upper()

    vix_score, vix_label, vix_detail = dynamic_vix_threshold(market_data)

    # -------------------------
    # 2) Curve 구간 세분화
    # -------------------------
    if t10y2y < 0:
        curve_segment = "INVERTED"
    elif t10y2y < 0.25:
        curve_segment = "FLAT / FRAGILE"
    elif t10y2y < 0.75:
        curve_segment = "MODERATE STEEP"
    else:
        curve_segment = "STEEP / REFLATION"

    # -------------------------
    # 3) 우선순위
    # -------------------------
    PRIORITY = {
        "VOL": 7,
        "LIQ": 6,
        "CURVE": 5,
        "CREDIT": 4,
        "PHASE": 3,
        "FLOW": 2,   # 🔥 새로 추가
        "MOM": 1,
    }

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
    drivers = {s: [] for s in sectors}

    def add_score(sector: str, pts: float, why: str, bucket: str):
        if sector not in score:
            return
        score[sector] += pts
        drivers[sector].append({
            "pts": pts,
            "why": why,
            "bucket": bucket,
            "priority": PRIORITY[bucket],
        })

    # -------------------------
    # A) VOLATILITY
    # -------------------------
    if vix_score >= 3:
        add_score("Utilities", 4, f"{vix_label} → 최우선 피난처 ({vix_detail})", "VOL")
        add_score("Consumer Staples", 3, f"{vix_label} → 경기 비탄력적 섹터 선호 ({vix_detail})", "VOL")
        add_score("Health Care", 2, f"{vix_label} → 방어/현금흐름 선호 ({vix_detail})", "VOL")
        add_score("Technology", -4, f"{vix_label} → 고베타/멀티플 압박 ({vix_detail})", "VOL")
        add_score("Consumer Discretionary", -2, f"{vix_label} → 경기민감 소비 부담 ({vix_detail})", "VOL")
    elif vix_score == 2:
        add_score("Utilities", 3, f"{vix_label} → 방어주 우위 ({vix_detail})", "VOL")
        add_score("Consumer Staples", 2, f"{vix_label} → 필수소비 선호 ({vix_detail})", "VOL")
        add_score("Technology", -3, f"{vix_label} → 위험자산 회피 ({vix_detail})", "VOL")
    elif vix_score == -2:
        add_score("Technology", 2, f"{vix_label} → 성장주 베팅 유효 ({vix_detail})", "VOL")
        add_score("Consumer Discretionary", 1, f"{vix_label} → 경기민감 소비 회복 ({vix_detail})", "VOL")
        add_score("Utilities", -1, f"{vix_label} → 방어주 상대매력 둔화 ({vix_detail})", "VOL")

   
    # -------------------------
    # B) LIQUIDITY
    # -------------------------
    liq_tight = (liq_dir == "DOWN") or (liq_lvl == "LOW")
    liq_easy = (liq_dir == "UP") and (liq_lvl in ("MID", "HIGH"))

    # 🔧 v3.4: Liquidity는 중요하지만 단독으로 섹터를 지배하지 않도록 완화
    if liq_tight:
        add_score("Consumer Staples", 2, "유동성 긴축 → 방어적 필수소비 선호", "LIQ")
        add_score("Health Care", 2, "유동성 긴축 → 안정적 현금흐름 선호", "LIQ")
        add_score("Utilities", 1, "유동성 긴축 → 방어주 버퍼", "LIQ")
        add_score("Technology", -2, "유동성 긴축 → 고밸류에이션 부담", "LIQ")
        add_score("Real Estate", -1.5, "유동성 긴축 → 조달비용 상승 부담", "LIQ")
        add_score("Consumer Discretionary", -1, "유동성 긴축 → 경기민감 소비 부담", "LIQ")

    elif liq_easy:
        add_score("Technology", 2, "유동성 완화 → 성장주/베타 우호", "LIQ")
        add_score("Industrials", 1.5, "유동성 완화 → 경기민감 회복", "LIQ")
        add_score("Consumer Discretionary", 1.5, "유동성 완화 → 소비 민감주 우호", "LIQ")
        add_score("Financials", 1, "유동성 완화 → 위험선호 회복", "LIQ")
        add_score("Utilities", -1, "유동성 완화 → 방어주 상대매력 저하", "LIQ")


    # -------------------------
    # C) CURVE
    # -------------------------
    if curve_segment == "INVERTED":
        add_score("Financials", -3, f"수익률 곡선 역전({t10y2y:.2f}) → 은행 수익성 악화", "CURVE")
        add_score("Utilities", 2, "역전 커브 → 침체 방어주 선호", "CURVE")
        add_score("Consumer Staples", 1, "역전 커브 → 경기 방어 필요", "CURVE")

    elif curve_segment == "FLAT / FRAGILE":
        add_score("Health Care", 1, f"플랫 커브({t10y2y:.2f}) → 방어/퀄리티 선호", "CURVE")
        add_score("Consumer Staples", 1, f"플랫 커브({t10y2y:.2f}) → 경기 민감도 낮은 섹터 선호", "CURVE")

    elif curve_segment == "MODERATE STEEP":
        add_score("Financials", 2, f"완만한 스티프닝({t10y2y:.2f}) → 예대마진 개선", "CURVE")
        add_score("Industrials", 1, f"완만한 스티프닝({t10y2y:.2f}) → 성장 기대 반영", "CURVE")

    elif curve_segment == "STEEP / REFLATION":
        add_score("Financials", 3, f"가파른 스티프닝({t10y2y:.2f}) → 금융주 우호", "CURVE")
        add_score("Energy", 1, f"가파른 스티프닝({t10y2y:.2f}) → 리플레이션 민감 섹터", "CURVE")
        add_score("Materials", 1, f"가파른 스티프닝({t10y2y:.2f}) → 경기재개/실물 민감", "CURVE")

    # -------------------------
    # D) CREDIT
    # -------------------------
    if credit_calm is False:
        add_score("Financials", -2, "크레딧 리스크 감지 → 금융주 변동성 확대", "CREDIT")
        add_score("Real Estate", -3, "크레딧 리스크 감지 → 부동산 금융 위축", "CREDIT")
        add_score("Consumer Staples", 1, "크레딧 리스크 감지 → 방어주 선호", "CREDIT")
        add_score("Health Care", 1, "크레딧 리스크 감지 → 퀄리티 선호", "CREDIT")

    # -------------------------
    # E) PHASE
    # -------------------------
    if "RISK-OFF" in phase:
        add_score("Consumer Staples", 1, "RISK-OFF → 방어주 미세 가점", "PHASE")
        add_score("Health Care", 1, "RISK-OFF → 퀄리티 미세 가점", "PHASE")
        add_score("Technology", -1, "RISK-OFF → 성장주 미세 감점", "PHASE")

    elif "RISK-ON" in phase:
        add_score("Industrials", 1, "RISK-ON → 경기민감 미세 가점", "PHASE")
        add_score("Technology", 1, "RISK-ON → 성장주 미세 가점", "PHASE")

    elif "EVENT-WATCHING" in phase or "WAITING" in phase:
        add_score("Health Care", 1, f"{phase} → 관망 구간 방어/퀄리티 선호", "PHASE")
        add_score("Consumer Staples", 1, f"{phase} → 관망 구간 필수소비 선호", "PHASE")

    # -------------------------
    # F) REAL-TIME MOMENTUM (Relative Strength)
    # -------------------------
    ticker_map = {
        "Technology": "XLK",
        "Financials": "XLF",
        "Energy": "XLE",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Consumer Discretionary": "XLY",
        "Consumer Staples": "XLP",
        "Health Care": "XLV",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Communication Services": "XLC"
    }

    momentum_data = market_data.get("MOMENTUM_SCORES", {})

    for sector_name, ticker in ticker_map.items():
        m_score = momentum_data.get(ticker, 0)
        if m_score > 0:
            add_score(sector_name, m_score, "Relative Strength 강세 (vs SPY) → 자금 유입 확인", "MOM")
        elif m_score < 0:
            add_score(sector_name, m_score, "Relative Strength 약세 (vs SPY) → 소외 섹터", "MOM")

    # -------------------------
    # G) 🔥 FLOW / GAMMA / DRIFT OVERLAY (ADD ONLY)
    # -------------------------
    flow_overlay_notes: List[str] = []

    flow_active = flow_score >= 4
    gamma_transition = "TRANSITION" in gamma_state
    gamma_positive = "POSITIVE" in gamma_state

    # 1) 디스인플레이션 + 리스크온 초기
    if flow_active and drift_label == "DISINFLATION_RISK_ON":
        add_score("Technology", 1.5, "Flow Overlay → DISINFLATION_RISK_ON 수혜", "FLOW")
        add_score("Consumer Discretionary", 1.0, "Flow Overlay → 소비/성장 베타 우호", "FLOW")
        add_score("Communication Services", 0.5, "Flow Overlay → 성장/플랫폼 수혜", "FLOW")
        flow_overlay_notes.append("DISINFLATION_RISK_ON → XLK/XLY/XLC 가점")

    # 2) 오일 쇼크 / 원자재 압력
    elif flow_active and drift_label == "OIL_SHOCK":
        add_score("Energy", 1.5, "Flow Overlay → OIL_SHOCK 수혜", "FLOW")
        add_score("Materials", 1.0, "Flow Overlay → 원자재/실물 우호", "FLOW")
        add_score("Consumer Discretionary", -1.0, "Flow Overlay → 유가 쇼크 시 소비 부담", "FLOW")
        flow_overlay_notes.append("OIL_SHOCK → XLE/XLB 가점, XLY 감점")

    # 3) 중립이지만 초기 흐름이 형성되는 경우
    elif flow_active and drift_label == "NEUTRAL":
        add_score("Technology", 0.5, "Flow Overlay → 초기 흐름에서 성장주 선행 반응", "FLOW")
        add_score("Industrials", 0.5, "Flow Overlay → 경기민감 확인용 가점", "FLOW")
        flow_overlay_notes.append("NEUTRAL + FLOW ACTIVE → XLK/XLI 소폭 가점")

    # 4) Gamma 상태에 따른 집중도
    if flow_active and gamma_positive:
        add_score("Technology", 1.0, "Gamma Overlay → POSITIVE, 추세 지속 우호", "FLOW")
        add_score("Industrials", 0.5, "Gamma Overlay → 경기민감 추세 확인", "FLOW")
        flow_overlay_notes.append("Gamma POSITIVE → 리더 섹터 가점")
    elif flow_active and gamma_transition:
        add_score("Technology", 0.5, "Gamma Overlay → TRANSITION, 초기 리더 형성", "FLOW")
        flow_overlay_notes.append("Gamma TRANSITION → 초기 리더 소폭 가점")


    # -------------------------
    # H) Theory vs Flow Divergence Adjustment
    # -------------------------
    divergence_flags = {}

    for s in sectors:
        ticker = ticker_map.get(s)
        mom = momentum_data.get(ticker, 0) if ticker else 0
        theo = score[s]

        if theo >= 2 and mom < 0:
            score[s] -= 1
            divergence_flags[s] = "NEGATIVE_DIVERGENCE"
            drivers[s].append({
                "pts": -1,
                "why": "이론 대비 실제 자금 흐름 약세 → 포지션 보수화",
                "bucket": "MOM",
                "priority": PRIORITY["MOM"],
            })

        elif theo <= 0 and mom > 0:
            # 🔥 Positive Divergence는 관찰이 아니라 최소 실행 후보로 상향
            score[s] += 1
            divergence_flags[s] = "POSITIVE_DIVERGENCE"
            drivers[s].append({
                "pts": 1,
                "why": "이론 대비 실제 자금 유입 확인 → 최소 관찰 비중 후보로 상향",
                "bucket": "MOM",
                "priority": PRIORITY["MOM"],
            })


        else:
            divergence_flags[s] = "ALIGNED"
   
    # -------------------------
    # I) Conflict Resolver
    # -------------------------
    if vix >= 28 and liq_tight:
        if score["Technology"] > 0:
            score["Technology"] = 0
            drivers["Technology"].append({
                "pts": 0,
                "why": "Conflict Resolver → VIX 고점 + 유동성 긴축으로 성장주 긍정점수 제거",
                "bucket": "VOL",
                "priority": PRIORITY["VOL"],
            })

        if score["Real Estate"] > -1:
            add_score("Real Estate", -1, "Conflict Resolver → VIX 고점 + 유동성 긴축으로 RE 추가 감점", "VOL")

    if score["Financials"] > 0 and vix >= 30 and liq_tight:
        original = score["Financials"]
        score["Financials"] = min(score["Financials"], 1)
        if score["Financials"] != original:
            drivers["Financials"].append({
                "pts": score["Financials"] - original,
                "why": "Financials Cap → VIX 고점 + 유동성 긴축으로 금융주 상단 제한",
                "bucket": "VOL",
                "priority": PRIORITY["VOL"],
            })

    if score["Financials"] > 0 and (credit_calm is False):
        add_score("Financials", -1, "Conflict Resolver → 커브 우호보다 크레딧 리스크 우선", "CREDIT")

    if ("EVENT-WATCHING" in phase or "WAITING" in phase):
        if score["Industrials"] > 0:
            add_score("Industrials", -1, "Conflict Resolver → 이벤트 관망으로 경기민감 가점 일부 축소", "PHASE")
        if score["Energy"] > 0:
            add_score("Energy", -1, "Conflict Resolver → 이벤트 관망으로 리플레이션 베팅 일부 축소", "PHASE")

    # -------------------------
    # 5) Score 기반 정렬
    # -------------------------
    ow_sorted = sorted([s for s in sectors if score[s] > 0], key=lambda x: (-score[x], x))
    uw_sorted = sorted([s for s in sectors if score[s] < 0], key=lambda x: (score[x], x))

    for s in sectors:
        positive = [d for d in drivers[s] if d["pts"] > 0]
        negative = [d for d in drivers[s] if d["pts"] < 0]
        zeroish = [d for d in drivers[s] if d["pts"] == 0]

        positive = sorted(positive, key=lambda d: (-d["priority"], -abs(d["pts"]), d["why"]))
        negative = sorted(negative, key=lambda d: (-d["priority"], -abs(d["pts"]), d["why"]))
        zeroish = sorted(zeroish, key=lambda d: (-d["priority"], d["why"]))

        drivers[s] = positive + negative + zeroish

    def sector_breakdown(sector: str) -> str:
        bucket_sum = {}
        for d in drivers[sector]:
            bucket_sum[d["bucket"]] = bucket_sum.get(d["bucket"], 0) + d["pts"]

        ordered_buckets = ["VOL", "LIQ", "CURVE", "CREDIT", "PHASE", "FLOW", "MOM"]
        parts = []
        for b in ordered_buckets:
            if b in bucket_sum and bucket_sum[b] != 0:
                if float(bucket_sum[b]).is_integer():
                    parts.append(f"{int(bucket_sum[b]):+d} {b}")
                else:
                    parts.append(f"{bucket_sum[b]:+,.1f} {b}")
        if float(score[sector]).is_integer():
            parts.append(f"= {int(score[sector]):+d}")
        else:
            parts.append(f"= {score[sector]:+,.1f}")
        return ", ".join(parts)

    top_rationales: List[str] = []
    seen_text = set()

    for s in ow_sorted[:4] + uw_sorted[:4]:
        label = "OW" if score[s] > 0 else "UW"
        used_bucket = set()
        local_count = 0

        for d in drivers[s]:
            if d["bucket"] in used_bucket:
                continue

            pts_display = f"{int(d['pts']):+d}" if float(d["pts"]).is_integer() else f"{d['pts']:+.1f}"
            text = f"{label} {s}: {pts_display}: {d['why']}"
            if text in seen_text:
                continue

            seen_text.add(text)
            used_bucket.add(d["bucket"])
            top_rationales.append(text)
            local_count += 1

            if local_count >= 2:
                break

        if len(top_rationales) >= 8:
            break

    # -------------------------
    # 6) 출력
    # -------------------------
    lines: List[str] = []
    lines.append("### 🏭 18) Sector Allocation Engine (v3.3)")
    lines.append("")
    lines.append(
        f"**Context:** phase={phase} / "
        f"T10Y2Y={t10y2y:.2f} ({curve_segment}) / "
        f"VIX={vix:.2f} ({vix_label}) / "
        f"liquidity={liq_dir}-{liq_lvl} / "
        f"credit={credit_calm}"
    )
    lines.append("")
    lines.append("**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM")
    lines.append("")
    lines.append(
        f"**Flow Overlay:** flow_score={flow_score} / flow_state={flow_state} / "
        f"drift_label={drift_label} / gamma={gamma_state}"
    )
    if flow_overlay_notes:
        lines.append(f"**Flow Notes:** {' | '.join(flow_overlay_notes)}")
    lines.append("")
    lines.append(f"**Overweight:** {', '.join(ow_sorted) if ow_sorted else 'None'}")
    lines.append("")
    lines.append(f"**Underweight:** {', '.join(uw_sorted) if uw_sorted else 'None'}")
    lines.append("")
    lines.append("**Scoreboard:**")
    for s in sorted(sectors, key=lambda x: (-score[x], x)):
        if score[s] != 0:
            score_display = f"{int(score[s]):+d}" if float(score[s]).is_integer() else f"{score[s]:+.1f}"
            lines.append(f"- {s}: {score_display}  ({sector_breakdown(s)})")
    lines.append("")
    lines.append("**Rationale (top drivers):**")

    for r in top_rationales:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("**Divergence Monitor (Theory vs Flow):**")
    has_divergence = False
    for s in sorted(sectors, key=lambda x: (-score[x], x)):
        flag = divergence_flags.get(s, "ALIGNED")
        if flag != "ALIGNED":
            has_divergence = True
            lines.append(f"- {s}: {flag}")
    if not has_divergence:
        lines.append("- No major theory-vs-flow divergence detected.")

    # -------------------------
    # 18.5) Execution Weight Allocation Logic
    # -------------------------
    # -------------------------
    # 18.5) Execution Weight Allocation Logic
    # -------------------------
    final_exposure = float(market_data.get("RECOMMENDED_EXPOSURE", 50.0))
    prev_exposure = float(market_data.get("PREV_EXPOSURE", final_exposure))

    # 🔥 디레버리징 트리거
    deleveraging_required = final_exposure < prev_exposure


    
    corr_msg = correlation_break_filter(market_data)
    is_corr_break = bool(corr_msg)
    
    if is_corr_break:
        if "Technology" in score:
            score["Technology"] += 0.5
    
        for s in ["Industrials", "Consumer Discretionary"]:
            if s in score:
                score[s] -= 0.3
    
    # 🔧 score가 corr/divergence 조정 후 바뀌었으므로 정렬 재계산
    ow_sorted = sorted([s for s in sectors if score[s] > 0], key=lambda x: (-score[x], x))
    uw_sorted = sorted([s for s in sectors if score[s] < 0], key=lambda x: (score[x], x))

    alloc_result = build_tactical_allocation(
    score=score,
    ow_sorted=ow_sorted,
    divergence_flags=divergence_flags,
    total_exposure=final_exposure,
    deleveraging_required=deleveraging_required,  # 🔥 추가
    )
    
   

    weights = alloc_result["weights"]
    cash_weight = alloc_result["cash_weight"]
    total_score_sum = alloc_result["total_score_sum"]

    # 🔥 Deleveraging Priority Preview
    delev_priority = rank_deleveraging_priority(
    score=score,
    weights=weights,
    divergence_flags=divergence_flags,
    momentum_scores=momentum_data,
    )

    allocation_lines = []
    allocation_lines.append("### 💰 18.5) Tactical Asset Allocation (Execution Weight)")
    #allocation_lines.append(f"- **Total Target Exposure:** **{final_exposure}%** (from Filter 15)")
    allocation_lines.append(f"- **Strategic Exposure (15):** **{final_exposure}%**")
    allocation_lines.append(f"- **Execution Exposure (18.5):** **{total_exposure}%**")
    allocation_lines.append("")

    if total_score_sum > 0:
        allocation_lines.append("| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |")
        allocation_lines.append("| :--- | :---: | :---: | :---: | :--- |")

        for s in ow_sorted:
            if s not in weights:
                continue

            s_score = score[s]
            s_weight = weights[s]
            flag = divergence_flags.get(s, "ALIGNED")

            action = "STRONG BUY" if s_weight >= 20 else ("ACCUMULATE" if s_weight >= 10 else "HOLD")
            score_display = f"+{int(s_score)}" if float(s_score).is_integer() else f"{s_score:+.1f}"

            allocation_lines.append(
                f"| {s} | {score_display} | {flag} | **{s_weight:.1f}%** | {action} |"
            )

        total_allocated = round(sum(weights.values()) + cash_weight, 1)

        if total_allocated != 100:
            diff = 100 - total_allocated
            cash_weight += diff
        
        # 🔥 수정된 값 기준으로 다시 계산
        total_allocated = round(sum(weights.values()) + cash_weight, 1)
        
        # ✅ 이제 출력
        allocation_lines.append(f"| **Cash & Hedge** | - | - | **{cash_weight:.1f}%** | DEFENSIVE |")
        allocation_lines.append("")
        allocation_lines.append(f"- **Allocation Check:** Sector Weights + Cash = **{total_allocated:.1f}%**")
        allocation_lines.append("")
        allocation_lines.append("**Deleveraging Priority Preview:**")
        allocation_lines.append("- 기준: Divergence → Score → Risk Sector → Current Weight")
        
        for i, row in enumerate(delev_priority[:5], start=1):
            allocation_lines.append(
                f"{i}. {row['sector']} "
                f"(risk_score={row['risk_score']}, "
                f"score={row['score']}, "
                f"weight={row['weight']:.1f}%, "
                f"div={row['divergence']})"
            )
        
        penalized = [s for s in ow_sorted if divergence_flags.get(s) == "NEGATIVE_DIVERGENCE"]
        if penalized:
            allocation_lines.append(f"- **Divergence Adjustment:** {', '.join(penalized)} penalized in weight sizing")
    else:
        allocation_lines.append("⚠️ 양수 점수를 받은 섹터가 없습니다. 현금 비중을 확대하십시오.")

    lines.append("\n" + "\n".join(allocation_lines))

    # -------------------------
    # 19) Execution Layer (ETF Mapping)
    # -------------------------
    etf_plan = build_execution_etf_map(weights)

    # -------------------------
    # Portfolio Logging (Paper Trading)
    # -------------------------
    try:
        from portfolio.save_portfolio import save_paper_portfolio

        etf_weights = {item["etf"]: item["weight"] for item in etf_plan}

        save_paper_portfolio(
            weights=etf_weights,
            cash_weight=cash_weight,
            exposure=final_exposure
        )

    except Exception as e:
        print(f"⚠️ Portfolio save failed: {e}")

    lines.append("")
    lines.append("### 🧬 19) Execution Layer (ETF Mapping)")
    lines.append("")

    if etf_plan:
        lines.append("| Sector | ETF | Weight | Action |")
        lines.append("| :--- | :---: | :---: | :--- |")

        for item in etf_plan:
            lines.append(
                f"| {item['sector']} | {item['etf']} | {item['weight']}% | {item['action']} |"
            )
    else:
        lines.append("⚠️ 실행 가능한 ETF 매핑이 없습니다.")

    return "\n".join(lines)


def build_execution_etf_map(weights: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    19) Execution Layer (Phase 1)
    - 18.5에서 나온 sector weight를 실제 ETF 실행안으로 변환
    """

    sector_to_etf = {
        "Technology": "XLK",
        "Financials": "XLF",
        "Energy": "XLE",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Consumer Discretionary": "XLY",
        "Consumer Staples": "XLP",
        "Health Care": "XLV",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Communication Services": "XLC",
    }

    results: List[Dict[str, Any]] = []

    for sector, weight in weights.items():
        if weight <= 0:
            continue

        etf = sector_to_etf.get(sector)
        if not etf:
            continue

        if weight >= 20:
            action = "PRIMARY"
        elif weight >= 10:
            action = "ADD"
        else:
            action = "SMALL"

        results.append({
            "sector": sector,
            "etf": etf,
            "weight": round(weight, 1),
            "action": action,
        })

    return results

    

# filters/execution_layer.py
from typing import Dict, Any
from filters.executive_layer import execution_layer_filter

def executive_summary_filter(market_data: Dict[str, Any], debug: bool = False) -> str:
    result = execution_layer_filter(market_data, debug=debug)
    return result["report"]
    

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


    

def institutional_flow_engine_filter(market_data: Dict[str, Any]) -> str:
    """
    Institutional Flow Engine (v2-minimal)

    목적:
    - 기관성 자금 축적 흔적을 점수화
    - 뉴스/쇼크 이전의 방향성 흐름 탐지
    - 기존 로직 유지 + breadth / validation 최소 추가
    """

    drift = market_data.get("DRIFT", {}) or {}
    drift_score = drift.get("score", 0)
    drift_state = str(drift.get("state", "N/A") or "N/A")
    drift_label = str(drift.get("label", "N/A") or "N/A")
    combo_signal = str(drift.get("combo_signal", "NONE") or "NONE")

    gamma_state = str(market_data.get("GAMMA_STATE", "UNKNOWN") or "UNKNOWN")
    gamma_combo = str(market_data.get("GAMMA_COMBO", "NONE") or "NONE")

    sew_status = str(market_data.get("SEW_STATUS", "N/A") or "N/A").upper()
    sew_event_type = str(market_data.get("SEW_EVENT_TYPE", "N/A") or "N/A").upper()

    pos_z = market_data.get("SP500_POS_Z", 0.0)
    try:
        pos_z = float(pos_z)
    except Exception:
        pos_z = 0.0

    drift_data = market_data.get("DRIFT_DATA", {}) or {}

    def g(asset: str, key: str):
        try:
            return drift_data.get(asset, {}).get(key)
        except Exception:
            return None

    # -----------------------------
    # 기존 short-horizon inputs
    # -----------------------------
    spy_15m = g("SPY", "ret_15m")
    spy_30m = g("SPY", "ret_30m")
    wti_15m = g("WTI", "ret_15m")
    wti_30m = g("WTI", "ret_30m")
    gold_15m = g("GOLD", "ret_15m")
    gold_30m = g("GOLD", "ret_30m")
    dxy_15m = g("DXY", "ret_15m")
    dxy_30m = g("DXY", "ret_30m")

    flow_score = 0
    reasons = []

    # 1) Drift core
    if drift_score >= 4:
        flow_score += 3
        reasons.append("Drift strong")
    elif drift_score >= 3:
        flow_score += 2
        reasons.append("Drift building")
    elif drift_score >= 2:
        flow_score += 1
        reasons.append("Drift early")

    # 2) Label quality
    if drift_label in ["DISINFLATION_RISK_ON", "SYSTEMIC_HEDGE", "TIGHTENING_PRESSURE", "OIL_SHOCK"]:
        flow_score += 1
        reasons.append(f"Clear flow label: {drift_label}")

    # 3) Short-horizon pre-move cluster
    short_hits = 0

    if spy_15m is not None and spy_15m >= 0.25:
        short_hits += 1
    if spy_30m is not None and spy_30m >= 0.40:
        short_hits += 1

    if wti_15m is not None and abs(wti_15m) >= 0.60:
        short_hits += 1
    if wti_30m is not None and abs(wti_30m) >= 0.90:
        short_hits += 1

    if gold_15m is not None and abs(gold_15m) >= 0.30:
        short_hits += 1
    if gold_30m is not None and abs(gold_30m) >= 0.45:
        short_hits += 1

    if dxy_15m is not None and abs(dxy_15m) >= 0.10:
        short_hits += 1
    if dxy_30m is not None and abs(dxy_30m) >= 0.15:
        short_hits += 1

    if short_hits >= 3:
        flow_score += 2
        reasons.append("Short-horizon pre-move cluster")
    elif short_hits >= 2:
        flow_score += 1
        reasons.append("Short-horizon pre-move")

    # 4) Gamma context
    if "TRANSITION" in gamma_state:
        flow_score += 1
        reasons.append("Gamma transition")
    elif "NEGATIVE" in gamma_state:
        flow_score += 1
        reasons.append("Gamma acceleration regime")

    # 5) SEW relationship
    if sew_status == "STABLE":
        flow_score += 1
        reasons.append("No shock yet")
    elif sew_status in ["WATCH", "ALERT"]:
        flow_score -= 1
        reasons.append("Shock already leaking into tape")

    # 6) Positioning penalty
    if pos_z >= 2.0:
        flow_score -= 2
        reasons.append("Positioning overheated")
    elif pos_z >= 1.5:
        flow_score -= 1
        reasons.append("Positioning somewhat stretched")

    # --------------------------------------------------
    # 6.5) Validation Layer (NEW, minimal additive only)
    # --------------------------------------------------
    validation_score = 0

    hyg_1d = g("HYG", "ret_1d")
    lqd_1d = g("LQD", "ret_1d")
    eem_1d = g("EEM", "ret_1d")
    fxi_1d = g("FXI", "ret_1d")

    xlk_1d = g("XLK", "ret_1d")
    xli_1d = g("XLI", "ret_1d")
    xlf_1d = g("XLF", "ret_1d")
    xly_1d = g("XLY", "ret_1d")
    xlp_1d = g("XLP", "ret_1d")
    xlu_1d = g("XLU", "ret_1d")

    # 6.5-1) Cross-asset risk participation
    risk_participation_hits = 0

    if hyg_1d is not None and hyg_1d > 0:
        risk_participation_hits += 1
    if eem_1d is not None and eem_1d > 0:
        risk_participation_hits += 1
    if fxi_1d is not None and fxi_1d > 0:
        risk_participation_hits += 1

    if risk_participation_hits >= 2:
        validation_score += 1
        reasons.append("Cross-asset risk participation")

    # 6.5-2) Credit confirmation
    if hyg_1d is not None and lqd_1d is not None and hyg_1d >= lqd_1d:
        validation_score += 1
        reasons.append("Credit confirms risk appetite")

    # 6.5-3) Sector leadership breadth
    leadership_hits = 0
    for v in [xlk_1d, xli_1d, xlf_1d, xly_1d]:
        if v is not None and v > 0:
            leadership_hits += 1

    if leadership_hits >= 2:
        validation_score += 1
        reasons.append("Leadership breadth expanding")

    # 6.5-4) Cyclical vs defensive check
    defensive_weak = 0
    for v in [xlp_1d, xlu_1d]:
        if v is not None and v <= 0:
            defensive_weak += 1

    cyclical_strong = 0
    for v in [xli_1d, xly_1d, xlk_1d]:
        if v is not None and v > 0:
            cyclical_strong += 1

    if cyclical_strong >= 2 and defensive_weak >= 1:
        validation_score += 1
        reasons.append("Cyclical leadership over defensives")

    # Validation score는 최대 +2까지만 반영 (과적합 방지)
    validation_boost = min(validation_score, 2)
    flow_score += validation_boost

    # 7) Flow state
    if flow_score >= 7:
        flow_state = "🔥 BUILDING HARD"
        confidence = "HIGH"
        interpretation = "뉴스 전 방향성 자금 축적 가능성 높음"
        action_bias = "EARLY PREP"
    elif flow_score >= 5:
        flow_state = "⚡ BUILDING"
        confidence = "MEDIUM-HIGH"
        interpretation = "기관성 흐름 형성 가능성"
        action_bias = "WATCHLIST"
    elif flow_score >= 3:
        flow_state = "👀 EARLY TRACE"
        confidence = "MEDIUM"
        interpretation = "흔적은 있으나 확신은 이르다"
        action_bias = "MONITOR"
    else:
        flow_state = "NO CLEAR FLOW"
        confidence = "LOW"
        interpretation = "기관성 축적 흔적 불충분"
        action_bias = "IGNORE"

    market_data["INSTITUTIONAL_FLOW"] = {
        "score": flow_score,
        "state": flow_state,
        "confidence": confidence,
        "interpretation": interpretation,
        "action_bias": action_bias,
        "reasons": reasons,
        "drift_label": drift_label,
        "combo_signal": combo_signal,
        "gamma_state": gamma_state,
        "gamma_combo": gamma_combo,
        "sew_status": sew_status,
        "sew_event_type": sew_event_type,
        "validation_score": validation_score,
        "validation_boost": validation_boost,
    }

    print("[FLOW ENGINE FINAL]", market_data["INSTITUTIONAL_FLOW"])

    lines = []
    lines.append("### 🏦 Institutional Flow Engine (v2-minimal)")
    lines.append("- **정의:** 기관성 자금이 뉴스 전에 남기는 흔적을 구조적으로 탐지")
    lines.append("")
    lines.append(f"- **Flow Score:** {flow_score}")
    lines.append(f"- **Flow State:** **{flow_state}**")
    lines.append(f"- **Confidence:** **{confidence}**")
    lines.append(f"- **Interpretation:** {interpretation}")
    lines.append(f"- **Action Bias:** **{action_bias}**")
    lines.append("")
    lines.append(f"- **Drift:** {drift_state} / {drift_label} / {combo_signal}")
    lines.append(f"- **Gamma:** {gamma_state} / {gamma_combo}")
    lines.append(f"- **SEW:** {sew_status} / {sew_event_type}")
    lines.append(f"- **Positioning (POS_Z):** {pos_z}")
    lines.append(f"- **Validation Score:** {validation_score} (boost applied: +{validation_boost})")

    if reasons:
        lines.append("")
        lines.append("- **Drivers:**")
        for r in reasons:
            lines.append(f"  - {r}")

    return "\n".join(lines)


    
    # -------------------------
 


def final_action_engine(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Final Action Engine v3.3
    - FINAL_STATE + INSTITUTIONAL_FLOW + GAMMA + SEW 통합 판단
    - EARLY TRACE를 institutional exit로 오해하지 않도록 수정
    - Risk-On + Early Trace 구간은 REDUCE가 아니라 HOLD/MONITOR로 처리
    """

    final_state = market_data.get("FINAL_STATE", {}) or {}
    inst_flow = market_data.get("INSTITUTIONAL_FLOW", {}) or {}

    raw_phase = str(final_state.get("phase", "N/A") or "N/A")
    raw_gamma = str(market_data.get("GAMMA_STATE", "UNKNOWN") or "UNKNOWN")
    raw_sew = str(market_data.get("SEW_STATUS", "N/A") or "N/A")

    risk_budget = final_state.get("risk_budget", 50)
    flow_score = inst_flow.get("score", 0)
    flow_state = str(inst_flow.get("state", "N/A") or "N/A")
    pos_z = market_data.get("SP500_POS_Z", 0)

    try:
        pos_z = float(pos_z)
    except Exception:
        pos_z = 0.0

    try:
        risk_budget = int(risk_budget)
    except Exception:
        risk_budget = 50

    try:
        flow_score = int(flow_score)
    except Exception:
        flow_score = 0

    def normalize_text(x: str) -> str:
        x = str(x).upper().strip()
        x = x.replace("_", "-")
        x = x.replace("–", "-")
        x = x.replace("—", "-")
        return x

    phase_norm = normalize_text(raw_phase)
    gamma_norm = normalize_text(raw_gamma)
    sew_norm = normalize_text(raw_sew)
    flow_norm = normalize_text(flow_state)

    is_risk_on = "RISK-ON" in phase_norm or "RISK ON" in phase_norm
    is_risk_off = "RISK-OFF" in phase_norm or "RISK OFF" in phase_norm

    is_gamma_positive = "POSITIVE" in gamma_norm
    is_gamma_transition = "TRANSITION" in gamma_norm
    is_gamma_negative = "NEGATIVE" in gamma_norm

    is_sew_stable = "STABLE" in sew_norm
    is_sew_watch = "WATCH" in sew_norm
    is_sew_alert = "ALERT" in sew_norm
    is_sew_deadman = "DEADMAN" in sew_norm

    is_early_trace = (
        "EARLY" in flow_norm
        or "TRACE" in flow_norm
        or flow_score == 3
    )

    action = "HOLD"
    size = "NONE"
    confidence = "LOW"
    reason = []

    print("[DEBUG][ACTION ENGINE]")
    print(" raw_phase =", raw_phase)
    print(" raw_gamma =", raw_gamma)
    print(" raw_sew =", raw_sew)
    print(" phase_norm =", phase_norm)
    print(" gamma_norm =", gamma_norm)
    print(" sew_norm =", sew_norm)
    print(" flow_norm =", flow_norm)
    print(" is_risk_on =", is_risk_on)
    print(" risk_budget =", risk_budget)
    print(" flow_score =", flow_score)
    print(" flow_state =", flow_state)
    print(" is_early_trace =", is_early_trace)
    print(" pos_z =", pos_z)

    # 1) Shock 최우선
    if is_sew_alert or is_sew_deadman:
        action = "REDUCE"
        size = "RISK CUT"
        confidence = "HIGH"
        reason.append("SEW shock → emergency risk cut")

    # 2) 구조 붕괴 Exit
    elif is_gamma_negative and flow_score <= 4:
        action = "EXIT"
        size = "FULL"
        confidence = "HIGH"
        reason.append("Gamma breakdown + flow weakening")

    # 3) Risk-On but no confirmed flow
    elif is_risk_on and flow_score <= 2:
        action = "WAIT"
        size = "0%"
        confidence = "LOW"
        reason.append("Risk-On environment but institutional flow not confirmed")

    # 4) Risk-On early trace
    elif (
        is_risk_on
        and is_early_trace
        and (is_gamma_positive or is_gamma_transition)
        and (is_sew_stable or is_sew_watch)
    ):
        action = "HOLD"
        size = "MAINTAIN"
        confidence = "MEDIUM"
        reason.append("Early institutional trace → hold exposure, not exit")

    # 5) 강한 확신 구간
    elif (
        is_risk_on
        and flow_score >= 7
        and is_gamma_positive
        and (is_sew_stable or is_sew_watch)
    ):
        action = "ADD"
        size = "MEDIUM (30~60%)"
        confidence = "HIGH"
        reason.append("Flow strong + structure aligned")

    # 6) BUILDING 구간
    elif (
        is_risk_on
        and flow_score >= 6
        and (is_gamma_transition or is_gamma_positive)
        and is_sew_stable
    ):
        action = "ADD"
        size = "MEDIUM (20~40%)"
        confidence = "MEDIUM-HIGH"
        reason.append("Flow building confirmed + gamma turning + no shock")

    # 7) 초기 진입 구간
    elif (
        is_risk_on
        and flow_score >= 4
        and (is_gamma_transition or is_gamma_positive)
        and is_sew_stable
    ):
        action = "EARLY BUY"
        size = "SMALL (10~20%)"
        confidence = "MEDIUM"
        reason.append("Flow building + gamma turning + no shock")

    # 8) Risk-On인데 흐름 약함
    elif is_risk_on and flow_score < 4 and is_sew_stable:
        action = "WAIT"
        size = "0%"
        confidence = "LOW"
        reason.append("Good environment but no strong flow yet")

    # 9) Risk-Off 환경
    elif is_risk_off:
        action = "REDUCE"
        size = "DEFENSIVE"
        confidence = "MEDIUM"
        reason.append("Risk-off environment")

    # 10) 기본값
    else:
        action = "HOLD"
        size = "NONE"
        confidence = "LOW"
        reason.append("No actionable alignment")

    # 11) 과열 override
    if pos_z >= 2.2 and flow_score < 5:
        action = "REDUCE"
        size = "TAKE PROFIT"
        confidence = "MEDIUM"
        reason.append("Positioning overheat")

    return {
        "action": action,
        "size": size,
        "confidence": confidence,
        "reason": reason,
        "phase": raw_phase,
        "phase_norm": phase_norm,
        "risk_budget": risk_budget,
        "flow_score": flow_score,
        "flow_state": flow_state,
        "flow_norm": flow_norm,
        "gamma_state": raw_gamma,
        "gamma_norm": gamma_norm,
        "sew_status": raw_sew,
        "sew_norm": sew_norm,
        "pos_z": pos_z,
        "is_early_trace": is_early_trace,
    }

def build_strategist_commentary(market_data: Dict[str, Any]) -> str:
    sections = []

    # 1. 예시/테스트용 코드

    if market_data.get("some_key"):
        sections.append(str({"key": "value"}))

    # ---------------------------------------------------------
    # 2. [데이터 전처리] 필터 실행 전 FRED EXTRA를 FINAL_STATE에 주입
    # ---------------------------------------------------------
    if "_FRED_EXTRA" in market_data:
        fred_extra = market_data["_FRED_EXTRA"] or {}

        if "FINAL_STATE" not in market_data or market_data["FINAL_STATE"] is None:
            market_data["FINAL_STATE"] = {}

        final_state = market_data["FINAL_STATE"]

        # 숫자 default(0.0, 100.0) 절대 넣지 말고
        # 값이 실제로 있을 때만 덮어쓰기
        if fred_extra.get("T10Y2Y") is not None:
            final_state["T10Y2Y"] = fred_extra.get("T10Y2Y")

        if fred_extra.get("T10YIE") is not None:
            final_state["T10YIE"] = fred_extra.get("T10YIE")

        if fred_extra.get("VIX") is not None:
            final_state["VIX"] = fred_extra.get("VIX")

        if fred_extra.get("DFII10") is not None:
            final_state["DFII10"] = fred_extra.get("DFII10")

        if fred_extra.get("DXY") is not None:
            final_state["DXY"] = fred_extra.get("DXY")

        if fred_extra.get("DGS2") is not None:
            final_state["DGS2"] = fred_extra.get("DGS2")

        if fred_extra.get("FCI") is not None:
            final_state["FCI"] = fred_extra.get("FCI")

        if fred_extra.get("REAL_RATE") is not None:
            final_state["REAL_RATE"] = fred_extra.get("REAL_RATE")

        print(f"[DEBUG][PRE-FILTER] FINAL_STATE Prepared: {final_state}")

    # ---------------------------------------------------------
    # 3. [필터 호출 시작]
    # ---------------------------------------------------------
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
    sections.append(credit_stress_filter(market_data))
    sections.append("")
    sections.append(legacy_directional_filters(market_data))
    sections.append("")
    sections.append(cross_asset_filter(market_data))
    sections.append("")
    sections.append(drift_monitor_filter(market_data))
    sections.append("")
    sections.append(correlation_break_filter(market_data))
    sections.append("")
    sections.append(sector_correlation_break_filter(market_data))
    sections.append("")
    sections.append(risk_exposure_filter(market_data))
    sections.append("")
    sections.append(geopolitical_early_warning_filter(market_data))
    sections.append("")
    sections.append(pseudo_gamma_filter(market_data))
    sections.append("")
    sections.append(institutional_flow_engine_filter(market_data))
    sections.append("")
    # 8번 필터
    sections.append(incentive_filter(market_data))
    sections.append("")

    # 나머지 필터
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

    return "\n".join(sections)
