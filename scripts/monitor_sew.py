import os
import json
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional


# ---------------------------
# 1. 통합 데이터(CSV) 로드 함수
# ---------------------------
def load_war_room_context(csv_path: str = "data/market_data_history.csv"):
    if not os.path.exists(csv_path):
        return None
    try:
        df = pd.read_csv(csv_path)
        return df.tail(1).to_dict("records")[0]
    except Exception:
        return None


def get_recent_pos_slope(csv_path: str, column_name: str = "SP500_POS_Z") -> float:
    try:
        if not os.path.exists(csv_path):
            return 0.0
        df = pd.read_csv(csv_path)
        valid_data = df[column_name].dropna().tail(3).tolist()
        if len(valid_data) >= 3:
            return float((valid_data[-1] - valid_data[-3]) / 2)
        elif len(valid_data) == 2:
            return float(valid_data[-1] - valid_data[-2])
    except Exception:
        return 0.0
    return 0.0


# ---------------------------
# 2. 실시간 z-score 계산 함수
# ---------------------------
def compute_zscore(prices: np.ndarray, window: int = 20) -> float:
    try:
        series = pd.Series(prices, dtype="float64")
        rets = series.pct_change() * 100.0
        rets = rets.dropna()

        if len(rets) < window + 1:
            return 0.0

        recent = rets.tail(window)
        mu = recent.mean()
        sigma = recent.std()

        if sigma == 0 or pd.isna(sigma):
            return 0.0

        return float((rets.iloc[-1] - mu) / sigma)
    except Exception:
        return 0.0


def classify_spike_state(z: float) -> str:
    az = abs(z)
    if az >= 3.5:
        return "EXTREME"
    elif az >= 2.5:
        return "ALERT"
    elif az >= 1.8:
        return "WATCH"
    return "NORMAL"


# ---------------------------
# 3. 6.5 상관관계 붕괴 필터
# ---------------------------
def correlation_break_filter(market_data: Dict[str, Any]) -> str:
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
    qqq = pct("QQQ")
    spy = pct("SPY")
    xlk = pct("XLK")
    tech = qqq if qqq is not None else xlk

    THR_US10Y, THR_DXY, THR_VIX, THR_EQ = 0.10, 0.15, 1.00, 0.25
    breaks, interp = [], []

    if signif(us10y, THR_US10Y):
        if us10y > 0 and signif(tech, THR_EQ) and tech > 0:
            breaks.append("US10Y ↑ but Technology ↑")
            interp.append("할인율 역풍에도 기술 강세 → 성장 내러티브 우위")
        if us10y > 0 and signif(spy, THR_EQ) and spy > 0:
            breaks.append("US10Y ↑ but SPY ↑")
            interp.append("시장이 금리 역풍을 무시 중")

    if signif(vix, THR_VIX) and vix > 0 and signif(spy, THR_EQ) and spy > 0:
        breaks.append("VIX ↑ but SPY ↑")
        interp.append("공포 신호에도 상승 → 숏 스퀴즈/포지션 꼬임 가능성")

    if not breaks:
        return ""

    res = ["### ⚠ 6.5) Correlation Break Detected:"]
    for b in breaks:
        res.append(f"- {b}")
    res.append(f"💡 So What? - {interp[0]}")
    return "\n".join(res)


# ---------------------------
# 4. 15번 필터: SEW 실시간용 Volatility-Controlled Exposure
# 주의:
# - 이 함수는 monitor_sew.py 전용 실시간 안전장치
# - Daily Report의 15번 v3.0과는 별도
# ---------------------------
def volatility_controlled_exposure_filter(
    market_data: Dict[str, Any], context: Dict[str, Any]
) -> tuple[int, str]:
    risk_budget = float(context.get("RISK_BUDGET", 85))
    phase = str(context.get("MARKET_REGIME", "RISK-ON")).upper()
    pos_z = float(context.get("SP500_POS_Z", 0.0))

    vix_today = market_data.get("VIX", {}).get("current")
    pos_slope = float(market_data.get("POS_SLOPE", 0.0))
    is_spiking = market_data.get("IS_SPIKING", False)

    is_deadman_on = False
    reason = ""

    if is_spiking:
        is_deadman_on = True
        reason = "Real-time Vol Spike Detected"
    elif abs(pos_z) > 2.0:
        is_deadman_on = True
        reason = f"POS_Z Extreme ({pos_z:.2f})"
    elif abs(pos_slope) > 0.5:
        is_deadman_on = True
        reason = f"Aggressive Slope ({pos_slope:.2f})"

    if is_deadman_on:
        return 0, f"🚨 DEAD MAN'S SWITCH: {reason}"

    cap = 85 if "RISK-ON" in phase else 35
    exposure = min(risk_budget, cap)

    if vix_today and vix_today > 25:
        exposure *= 0.8

    return int(exposure), "Normal Operation"


# ---------------------------
# 5. Event Signature 분류
# ---------------------------
def detect_event_signature(
    z_map: Dict[str, float],
    context: Dict[str, Any],
    market_snap: Dict[str, Any],
) -> str:
    """
    가격 + 포지셔닝 결합형 이벤트 해석
    """

    spy_z = float(z_map.get("SPY", 0.0) or 0.0)
    qqq_z = float(z_map.get("QQQ", 0.0) or 0.0)
    vix_z = float(z_map.get("VIX", 0.0) or 0.0)
    dxy_z = float(z_map.get("DXY", 0.0) or 0.0)
    wti_z = float(z_map.get("WTI", 0.0) or 0.0)

    pos_z = float(context.get("SP500_POS_Z", 0.0) or 0.0)
    gamma_bias = float(context.get("DEALER_GAMMA_BIAS", 1.0) or 1.0)
    cta_score = float(context.get("CTA_MOMENTUM_SCORE", 0.0) or 0.0)
    pos_slope = float(market_snap.get("POS_SLOPE", 0.0) or 0.0)

    if spy_z < -2.5 and vix_z > 2.5:
        if pos_z > 1.8 or abs(pos_slope) > 0.5:
            return "LIQUIDATION_SHOCK"
        return "RISK_OFF_SHOCK"

    if qqq_z < -2.5 and vix_z > 2.0:
        if cta_score >= 1.0 or pos_z > 1.5:
            return "TECH_DELEVERAGING"
        return "TECH_STRESS"

    if wti_z < -2.5 and dxy_z > 2.0:
        if pos_z > 1.8 or abs(pos_slope) > 0.5:
            return "MACRO_UNWIND"
        return "MACRO_FLOW_DISLOCATION"

    if spy_z > 2.5 and vix_z < -2.0:
        if gamma_bias < 0.5:
            return "VOL_CRUSH_SQUEEZE"
        return "RISK_ON_SQUEEZE"

    if pos_z > 2.2 and abs(pos_slope) > 0.5:
        return "POSITION_UNWIND_RISK"

    return "NORMAL"


# ---------------------------
# 6. 야후 데이터 다운로드 헬퍼
# ---------------------------
def download_intraday_prices(
    ticker: str,
    period: str = "5d",
    interval: str = "5m",
) -> Optional[np.ndarray]:
    try:
        df = yf.download(
            ticker,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False,
            threads=False,
        )

        if df is None or df.empty or "Close" not in df.columns:
            return None

        close_series = df["Close"]
        if isinstance(close_series, pd.DataFrame):
            close_series = close_series.squeeze()

        close_series = pd.to_numeric(close_series, errors="coerce").dropna()
        if close_series.empty:
            return None

        return close_series.values.astype(float)

    except Exception:
        return None


# ---------------------------
# 7. SEW 상태 저장 함수
# ---------------------------
def save_sew_state(
    filepath: str,
    timestamp: str,
    sew_status: str,
    event_type: str,
    spike_count: int,
    extreme_count: int,
    recommended_exposure: int,
    deadman: bool,
    summary: str,
    deadman_reason: str,
    z_map: Dict[str, float],
    market_snap: Dict[str, Any],
):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    assets = {}
    for name, z in z_map.items():
        assets[name] = {
            "zscore": round(float(z), 2),
            "state": market_snap.get(name, {}).get("spike_state", "N/A"),
            "pct_change": round(float(market_snap.get(name, {}).get("pct_change", 0.0)), 2),
        }

    payload = {
        "timestamp": timestamp,
        "status": sew_status,
        "event_type": event_type,
        "spike_count": spike_count,
        "extreme_count": extreme_count,
        "recommended_exposure": recommended_exposure,
        "deadman": deadman,
        "summary": summary,
        "deadman_reason": deadman_reason,
        "assets": assets,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# ---------------------------
# 7.5 Institutional Flow 상태 저장/비교 함수
# ---------------------------
def load_previous_flow_state(filepath: str = "insights/flow_state.json") -> Dict[str, Any]:
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_flow_state(
    current_state: str,
    current_score: int,
    timestamp: str,
    transition_info: Dict[str, Any] = None,
    filepath: str = "insights/flow_state.json",
) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    transition_info = transition_info or {}

    payload = {
        "timestamp": timestamp,
        "flow_state": transition_info.get("flow_state", current_state),
        "flow_score": transition_info.get("flow_score", current_score),
        "prev_flow_state": transition_info.get("prev_flow_state", "N/A"),
        "prev_flow_score": transition_info.get("prev_flow_score", 0),
        "flow_delta": transition_info.get("flow_delta", 0),
        "persistence_days": transition_info.get("persistence_days", 0),
        "transition": transition_info.get("transition", "N/A"),
        "transition_note": transition_info.get("transition_note", "N/A"),
        "raw_flow_state": current_state,
        "raw_flow_score": current_score,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def classify_flow_transition(
    prev_flow_state: str,
    prev_flow_score: int,
    current_flow_state: str,
    current_flow_score: int,
    prev_persistence_days: int = 0,
) -> Dict[str, Any]:
    """
    Flow Persistence Layer (v2.5)

    목적:
    - 단순 현재 flow_state가 아니라
      이전 상태 대비 흐름이 강화/약화/붕괴/유지되는지 판정
    """

    prev_state = str(prev_flow_state or "N/A").upper()
    current_state = str(current_flow_state or "N/A").upper()

    flow_delta = int(current_flow_score) - int(prev_flow_score)

    transition_state = current_flow_state
    transition_note = "현재 flow 상태 기준 유지"
    persistence_days = 0

    # 1) 이전에 흔적이 있었는데 오늘 완전히 사라짐
    if prev_flow_score >= 2 and current_flow_score == 0:
        transition_state = "FLOW_BREAK"
        transition_note = "전일 형성되던 기관성 흐름이 유지되지 못하고 소멸"
        persistence_days = 0

    # 2) 이전보다 약해짐
    elif prev_flow_score >= 3 and 0 < current_flow_score < prev_flow_score:
        transition_state = "FLOW_FADE"
        transition_note = "기관성 흐름은 남아 있으나 강도 약화"
        persistence_days = max(0, prev_persistence_days - 1)

    # 3) 초기 흔적 발생
    elif prev_flow_score < 2 and current_flow_score >= 2:
        transition_state = "EARLY_TRACE"
        transition_note = "기관성 흐름 초기 흔적 발생"
        persistence_days = 1

    # 4) 흐름 강화
    elif current_flow_score > prev_flow_score and current_flow_score >= 3:
        transition_state = "TRACE_BUILDING"
        transition_note = "기관성 흐름이 전일 대비 강화"
        persistence_days = prev_persistence_days + 1

    # 5) 강한 흐름 확인
    elif current_flow_score >= 5:
        transition_state = "CONFIRMED_FLOW"
        transition_note = "기관성 흐름이 높은 강도로 확인"
        persistence_days = prev_persistence_days + 1

    # 6) 계속 없음
    elif current_flow_score < 2 and prev_flow_score < 2:
        transition_state = "NO_FLOW_BASE"
        transition_note = "기관성 흐름 부재 상태 지속"
        persistence_days = 0

    # 7) 그 외 유지
    else:
        transition_state = current_flow_state
        transition_note = "기관성 흐름 상태 유지"
        persistence_days = prev_persistence_days if current_flow_score >= 2 else 0

    return {
        "flow_state": transition_state,
        "flow_score": current_flow_score,
        "prev_flow_state": prev_flow_state,
        "prev_flow_score": prev_flow_score,
        "flow_delta": flow_delta,
        "persistence_days": persistence_days,
        "transition": f"{prev_flow_state} -> {transition_state}",
        "transition_note": transition_note,
    }


def extract_current_flow_from_context(context: Dict[str, Any]) -> tuple[str, int]:
    """
    market_data_history.csv의 컬럼명이 바뀌어도 최대한 안전하게 읽는다.
    없으면 NO CLEAR FLOW / 0으로 처리.
    """
    current_flow_state = str(
        context.get("flow_state")
        or context.get("FLOW_STATE")
        or context.get("institutional_flow_state")
        or context.get("INSTITUTIONAL_FLOW_STATE")
        or context.get("flow")
        or context.get("FLOW")
        or "NO CLEAR FLOW"
    ).upper()

    try:
        current_flow_score = int(float(
            context.get("flow_score")
            or context.get("FLOW_SCORE")
            or context.get("institutional_flow_score")
            or context.get("INSTITUTIONAL_FLOW_SCORE")
            or 0
        ))
    except Exception:
        current_flow_score = 0

    return current_flow_state, current_flow_score


def evaluate_flow_change(
    prev_flow_state: str,
    current_flow_state: str,
) -> tuple[bool, str, str]:
    """
    이전 flow_state와 현재 flow_state를 비교해 알림 여부/레벨/메시지 산출
    """
    prev_flow_state = str(prev_flow_state or "N/A").upper()
    current_flow_state = str(current_flow_state or "NO CLEAR FLOW").upper()

    if prev_flow_state == "N/A":
        return False, "NONE", ""

    if current_flow_state == prev_flow_state:
        return False, "NONE", ""

    if prev_flow_state == "NO CLEAR FLOW" and current_flow_state in ["EARLY TRACE", "CONFIRMED FLOW"]:
        return (
            True,
            "UPGRADE",
            f"Institutional flow upgraded: {prev_flow_state} → {current_flow_state}",
        )

    if prev_flow_state == "EARLY TRACE" and current_flow_state == "CONFIRMED FLOW":
        return (
            True,
            "CONFIRMATION",
            f"Institutional flow confirmed: {prev_flow_state} → {current_flow_state}",
        )

    if current_flow_state == "NO CLEAR FLOW":
        return (
            True,
            "FADE",
            f"Institutional flow faded: {prev_flow_state} → {current_flow_state}",
        )

    return (
        True,
        "CHANGE",
        f"Institutional flow changed: {prev_flow_state} → {current_flow_state}",
    )


# ---------------------------
# 8. 메인 감시 및 이메일 로직
# ---------------------------
def check_market_anomaly():
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    csv_path = "data/market_data_history.csv"
    context = load_war_room_context(csv_path) or {}

    tickers = {
        "SPY": "SPY",
        "QQQ": "QQQ",
        "VIX": "^VIX",
        "DXY": "UUP",
        "WTI": "USO",
    }

    market_snap: Dict[str, Any] = {}
    summary_lines = []
    z_map: Dict[str, float] = {}

    spike_count = 0
    extreme_count = 0
    is_spiking = False

    print(f"🚀 [{now_str}] 통합 상황실 가동 (Data: {context.get('date', 'N/A')})")

    for name, ticker in tickers.items():
        try:
            print(f"🔍 {name} 데이터 수집 시도... ({ticker})")
            prices = download_intraday_prices(ticker, period="5d", interval="5m")

            if prices is None or len(prices) < 2:
                print(f"⚠️ {name} 데이터 부족 또는 수집 실패")
                continue

            curr = float(prices[-1])

            if len(prices) >= 6:
                prev = float(prices[-5])
            elif len(prices) >= 2:
                prev = float(prices[-2])
            else:
                prev = curr

            change = 0.0 if prev == 0 else ((curr - prev) / prev) * 100.0

            z = compute_zscore(prices)
            state = classify_spike_state(z)

            if state == "EXTREME":
                extreme_count += 1
            elif state == "ALERT":
                spike_count += 1

            market_snap[name] = {
                "current": curr,
                "pct_change": change,
                "zscore": z,
                "spike_state": state,
            }
            z_map[name] = z

            icon = "🔺" if change > 0 else ("🔻" if change < 0 else "⏸")
            summary_lines.append(
                f"{icon} {name}: {curr:.2f} ({change:+.2f}%) | z={z:+.2f} [{state}]"
            )

            print(
                f"✅ {name} 수집 성공 | len={len(prices)} | "
                f"curr={curr:.2f} | change={change:+.2f}% | z={z:+.2f}"
            )

        except Exception as e:
            print(f"❌ {name} 오류: {e}")
            continue

    if extreme_count >= 1:
        is_spiking = True
    elif spike_count >= 2:
        is_spiking = True

    event_type = detect_event_signature(z_map, context, market_snap)

    # ---------------------------
    # Institutional Flow Change Monitor
    # ---------------------------
    current_flow_state, current_flow_score = extract_current_flow_from_context(context)

    prev_flow = load_previous_flow_state()
    prev_flow_state = str(prev_flow.get("flow_state", "N/A") or "N/A").upper()
    try:
        prev_flow_score = int(float(prev_flow.get("flow_score", 0) or 0))
    except Exception:
        prev_flow_score = 0

    prev_persistence_days = int(prev_flow.get("persistence_days", 0) or 0)

    transition_info = classify_flow_transition(
        prev_flow_state=prev_flow_state,
        prev_flow_score=prev_flow_score,
        current_flow_state=current_flow_state,
        current_flow_score=current_flow_score,
        prev_persistence_days=prev_persistence_days,
    )
    
    flow_change_alert, flow_alert_level, flow_alert_msg = evaluate_flow_change(
        prev_flow_state=prev_flow_state,
        current_flow_state=transition_info.get("flow_state", current_flow_state),
    )
    transition_state = str(transition_info.get("flow_state", current_flow_state) or "").upper()
    flow_delta = int(transition_info.get("flow_delta", 0) or 0)
    
    if transition_state == "FLOW_BREAK":
        flow_change_alert = True
        flow_alert_level = "FLOW_BREAK"
        flow_alert_msg = "전일 형성되던 기관성 흐름이 유지되지 못하고 소멸되었습니다."
    
    elif transition_state == "FLOW_FADE":
        flow_change_alert = True
        flow_alert_level = "FLOW_FADE"
        flow_alert_msg = "기관성 흐름은 남아 있으나 강도가 약화되었습니다."
    
    elif transition_state == "TRACE_BUILDING":
        flow_change_alert = True
        flow_alert_level = "TRACE_BUILDING"
        flow_alert_msg = "기관성 흐름이 전일 대비 강화되고 있습니다."
    
    elif transition_state == "CONFIRMED_FLOW":
        flow_change_alert = True
        flow_alert_level = "CONFIRMED_FLOW"
        flow_alert_msg = "기관성 흐름이 높은 강도로 확인되었습니다."
    
    save_flow_state(
        current_state=current_flow_state,
        current_score=current_flow_score,
        timestamp=now_str,
        transition_info=transition_info,
    )

    print(
        f"[FLOW MONITOR] prev={prev_flow_state}({prev_flow_score}) "
        f"current={current_flow_state}({current_flow_score}) "
        f"alert={flow_alert_level}"
    )

    market_snap["IS_SPIKING"] = is_spiking
    market_snap["POS_SLOPE"] = get_recent_pos_slope(csv_path)
    market_snap["EVENT_TYPE"] = event_type
    market_snap["Z_MAP"] = z_map

    corr_msg = correlation_break_filter(market_snap)
    recommended_exp, status_msg = volatility_controlled_exposure_filter(market_snap, context)

    # ---------------------------
    # SEW 상태 판단
    # ---------------------------
    deadman = (recommended_exp == 0)

    if deadman:
        sew_status = "DEADMAN"
        sew_summary = "🚨 데드맨 스위치 발동 (익스포저 0% / 자산 보호 모드)"
    elif extreme_count >= 1:
        sew_status = "ALERT"
        sew_summary = "🚨 실시간 발작 감지 (EXTREME z-score 발생 / 즉시 모니터링 필요)"
    elif spike_count >= 2:
        sew_status = "WATCH"
        sew_summary = "⚠️ 다중 자산 경미한 이상반응 감지 (ALERT 2건 이상)"
    else:
        sew_status = "STABLE"
        sew_summary = f"✅ 이상징후 없음 ({len(z_map)}개 자산 정상 범위 / z-score 발작 없음)"

    # ---------------------------
    # SEW 상태 파일 저장
    # ---------------------------
    save_sew_state(
        filepath="insights/sew_state.json",
        timestamp=now_str,
        sew_status=sew_status,
        event_type=event_type,
        spike_count=spike_count,
        extreme_count=extreme_count,
        recommended_exposure=recommended_exp,
        deadman=deadman,
        summary=sew_summary,
        deadman_reason=status_msg,
        z_map=z_map,
        market_snap=market_snap,
    )

    # ---------------------------
    # 실전용 발송 조건
    # ---------------------------
    should_alert = (
        sew_status in ["WATCH", "ALERT", "DEADMAN"]
        or event_type in [
            "LIQUIDATION_SHOCK",
            "MACRO_UNWIND",
            "TECH_DELEVERAGING",
            "POSITION_UNWIND_RISK",
            "RISK_OFF_SHOCK",
            "MACRO_FLOW_DISLOCATION",
            "TECH_STRESS",
            "VOL_CRUSH_SQUEEZE",
            "RISK_ON_SQUEEZE",
        ]
        or recommended_exp == 0
        or bool(corr_msg)
        or flow_change_alert
    )

    os.makedirs("insights", exist_ok=True)

    if should_alert:
        subject = f"🚨 [SEW] {sew_status} | {event_type} | Flow {flow_alert_level} | Exp {recommended_exp}%"

        body = f"""
[Digital War Room - Real-time Status]

현재 마켓에서 이상징후 또는 기관성 흐름 변화가 감지되었습니다.

─────────────────────────────────────────
📢 실시간 요약 (Exposure: {recommended_exp}%)
─────────────────────────────────────────
- 일시: {now_str}
- 시스템 상태: {status_msg}
- SEW Status: {sew_status}
- Event Type: {event_type}
- Deadman Reason: {status_msg if recommended_exp == 0 else 'N/A'}
- 아침 데이터 기준: {context.get('date', 'Unknown')}

─────────────────────────────────────────
🏦 Institutional Flow Monitor
─────────────────────────────────────────
- Raw Flow State: {current_flow_state} (prev: {prev_flow_state})
- Raw Flow Score: {current_flow_score} (prev: {prev_flow_score})
- Transition State: {transition_info.get('flow_state', current_flow_state)}
- Flow Delta: {transition_info.get('flow_delta', 0)}
- Persistence Days: {transition_info.get('persistence_days', 0)}
- Transition Note: {transition_info.get('transition_note', 'N/A')}
- Flow Alert: {flow_alert_msg if flow_change_alert else 'N/A'}

─────────────────────────────────────────
📌 Positioning / Spike
─────────────────────────────────────────
- POS_Z: {context.get('SP500_POS_Z', 'N/A')}
- POS_SLOPE: {market_snap.get('POS_SLOPE', 0.0):+.2f}
- Spike Count: {spike_count}
- Extreme Count: {extreme_count}

📊 자산별 변동률 (5분 기준)
{chr(10).join(summary_lines) if summary_lines else 'No intraday asset summary available.'}

{corr_msg if corr_msg else 'No correlation break message.'}

─────────────────────────────────────────
🧠 전략적 가이드
─────────────────────────────────────────
💡 권장 익스포저가 {recommended_exp}%로 산출되었습니다.
💡 {'즉시 포지션을 동결하거나 축소하십시오.' if recommended_exp == 0 else '가격/포지셔닝/상관관계/기관흐름 변화를 주의 깊게 관찰하십시오.'}
─────────────────────────────────────────
        """.strip()

        with open("insights/alerts.log", "a", encoding="utf-8") as f:
            f.write(
                f"[{now_str}] ALERT | "
                f"SEW={sew_status} | "
                f"EVENT={event_type} | "
                f"flow={transition_info.get('transition', f'{prev_flow_state}->{current_flow_state}')} | "
                f"flow_delta={transition_info.get('flow_delta', 0)} | "
                f"persistence={transition_info.get('persistence_days', 0)} | "
                f"flow_alert={flow_alert_level} | "
                f"Exp={recommended_exp}% | "
                f"{status_msg} | "
                f"spike={spike_count} extreme={extreme_count} | "
                f"corr_break={'YES' if bool(corr_msg) else 'NO'} | "
                f"z={z_map}\n"
            )

        api_key = os.getenv("RESEND_API_KEY")
        resend_from = os.getenv("RESEND_FROM")
        resend_to = os.getenv("RESEND_TO")

        print(
            f"DEBUG: should_alert={should_alert}, "
            f"recommended_exp={recommended_exp}, "
            f"event_type={event_type}, "
            f"sew_status={sew_status}, "
            f"flow={prev_flow_state}->{current_flow_state}, "
            f"flow_alert={flow_alert_level}, "
            f"corr_msg_exists={bool(corr_msg)}, "
            f"z_map={z_map}"
        )
        print(f"DEBUG: RESEND_FROM={resend_from}, RESEND_TO={resend_to}")

        email_sent = False

        if api_key and resend_from and resend_to:
            try:
                resp = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": resend_from,
                        "to": [resend_to],
                        "subject": subject,
                        "text": body,
                    },
                    timeout=15,
                )
                print(f"✅ Resend status: {resp.status_code}")
                print(f"✅ Resend response: {resp.text}")

                if resp.status_code in [200, 201]:
                    email_sent = True
                else:
                    print("❌ 이메일 API 호출은 되었지만 성공 응답이 아닙니다.")

            except Exception as e:
                print(f"❌ 이메일 발송 실패: {e}")
        else:
            print("❌ RESEND_API_KEY / RESEND_FROM / RESEND_TO 환경변수 확인 필요")

        if email_sent:
            print(f"📧 실전 알림 발송 완료: {sew_status} | {event_type} | {flow_alert_level}")
        else:
            print(f"⚠️ 실전 알림 미발송: {sew_status} | {event_type} | {flow_alert_level}")

    else:
        with open("insights/alerts.log", "a", encoding="utf-8") as f:
            f.write(
                f"[{now_str}] NO_ALERT | "
                f"SEW={sew_status} | "
                f"EVENT={event_type} | "
                f"flow={prev_flow_state}->{current_flow_state} | "
                f"flow_alert={flow_alert_level} | "
                f"Exp={recommended_exp}% | "
                f"spike={spike_count} extreme={extreme_count} | "
                f"corr_break={'YES' if bool(corr_msg) else 'NO'} | "
                f"z={z_map}\n"
            )

        print("✅ 특이사항 없음. 정상 모니터링 종료.")


if __name__ == "__main__":
    check_market_anomaly()
