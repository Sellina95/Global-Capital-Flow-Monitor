import os
import time
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional, List

# ---------------------------
# 1. 통합 데이터(CSV) 로드 함수 (진짜 데이터 엔진)
# ---------------------------
def load_war_room_context(csv_path: str = "data/market_data_history.csv"):
    if not os.path.exists(csv_path):
        return None
    try:
        df = pd.read_csv(csv_path)
        # 가장 최신(오늘 아침) 데이터 1줄을 사전형태로 반환
        return df.tail(1).to_dict('records')[0] 
    except Exception:
        return None

def get_recent_pos_slope(csv_path: str, column_name='SP500_POS_Z'):
    try:
        if not os.path.exists(csv_path): return 0.0
        df = pd.read_csv(csv_path)
        valid_data = df[column_name].dropna().tail(3).tolist()
        if len(valid_data) >= 3:
            return (valid_data[-1] - valid_data[-3]) / 2
        elif len(valid_data) == 2:
            return valid_data[-1] - valid_data[-2]
    except: return 0.0
    return 0.0

# ---------------------------
# 2. 6.5 & 6.6 상관관계 붕괴 필터 (세연 님 오리지널 로직 보존)
# ---------------------------
def correlation_break_filter(market_data: Dict[str, Any]) -> str:
    def pct(key: str) -> Optional[float]:
        v = market_data.get(key, {}) or {}
        x = v.get("pct_change")
        try: return None if x is None else float(x)
        except: return None

    def signif(x: Optional[float], thr: float) -> bool:
        return (x is not None) and (abs(x) >= thr)

    us10y, dxy, vix = pct("US10Y"), pct("DXY"), pct("VIX")
    qqq, spy, xlk = pct("QQQ"), pct("SPY"), pct("XLK")
    tech = qqq if qqq is not None else xlk

    THR_US10Y, THR_DXY, THR_VIX, THR_EQ = 0.10, 0.15, 1.00, 0.25
    breaks, interp = [], []

    # A) Rates vs Tech/Broad
    if signif(us10y, THR_US10Y):
        if us10y > 0 and signif(tech, THR_EQ) and tech > 0:
            breaks.append("US10Y ↑ but Technology ↑"); interp.append("할인율 역풍에도 기술 강세 → 성장 내러티브 우위")
        if us10y > 0 and signif(spy, THR_EQ) and spy > 0:
            breaks.append("US10Y ↑ but SPY ↑"); interp.append("시장이 금리 역풍을 무시 중")
    
    # B) VIX vs Equity
    if signif(vix, THR_VIX) and vix > 0 and signif(spy, THR_EQ) and spy > 0:
        breaks.append("VIX ↑ but SPY ↑"); interp.append("공포 신호에도 상승 → 숏 스퀴즈/포지션 꼬임 가능성")

    if not breaks: return ""
    
    res = ["\n### ⚠ 6.5) Correlation Break Detected:"]
    for b in breaks: res.append(f"- {b}")
    res.append(f"\n💡 So What?\n- {interp[0]}")
    return "\n".join(res)

# ---------------------------
# 3. 15번 필터: Volatility-Controlled Exposure (진짜 데이터 연동)
# ---------------------------
def volatility_controlled_exposure_filter(market_data: Dict[str, Any], context: Dict[str, Any]) -> (int, str):
    risk_budget = float(context.get("RISK_BUDGET", 85)) # CSV에서 로드
    phase = str(context.get("MARKET_REGIME", "RISK-ON")).upper() # CSV에서 로드
    pos_z = float(context.get("SP500_POS_Z", 0.0)) # CSV에서 로드
    
    vix_today = market_data.get("VIX", {}).get("current")
    pos_slope = float(market_data.get("POS_SLOPE", 0.0))
    is_spiking = market_data.get("IS_SPIKING", False)

    is_deadman_on = False
    reason = ""
    if is_spiking:
        is_deadman_on = True; reason = "Real-time Vol Spike Detected"
    elif abs(pos_z) > 2.0:
        is_deadman_on = True; reason = f"POS_Z Extreme ({pos_z:.2f})"
    elif abs(pos_slope) > 0.5:
        is_deadman_on = True; reason = f"Aggressive Slope ({pos_slope:.2f})"

    if is_deadman_on:
        return 0, f"🚨 DEAD MAN'S SWITCH: {reason}"

    cap = 85 if "RISK-ON" in phase else 35
    exposure = min(risk_budget, cap)
    if vix_today and vix_today > 25: exposure *= 0.8
    
    return int(exposure), "Normal Operation"

# ---------------------------
# 4. 메인 감시 및 이메일 로직
# ---------------------------
def check_market_anomaly():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    csv_path = "data/market_data_history.csv"
    context = load_war_room_context(csv_path) or {} # 진짜 데이터 가져오기
    
    tickers = {"VIX": "^VIX", "WTI": "CL=F", "DXY": "DX-Y.NYB", "US10Y": "^TNX", "NQ": "NQ=F", "SPY": "SPY", "QQQ": "QQQ"}
    
    market_snap = {}
    summary_lines = []
    is_spiking = False
    
    print(f"🚀 [{now_str}] 통합 상황실 가동 (Data: {context.get('date', 'N/A')})")

    for name, ticker in tickers.items():
        try:
            df = yf.download(ticker, period="1d", interval="1m", progress=False)
            if df.empty: continue
            prices = df['Close'].values.flatten()
            curr = float(prices[-1])
            prev = float(prices[-5]) if len(prices) > 5 else prices[0]
            change = (curr - prev) / prev * 100
            
            market_snap[name] = {"current": curr, "pct_change": change}
            icon = "🔺" if change > 0 else "🔻"
            summary_lines.append(f"{icon} {name}: {curr:.2f} ({change:+.2f}%)")
            
            if abs(change) >= 2.0: is_spiking = True
        except: continue

    # 추가 데이터 구성
    market_snap["IS_SPIKING"] = is_spiking
    market_snap["POS_SLOPE"] = get_recent_pos_slope(csv_path)

    # 필터 판정
    corr_msg = correlation_break_filter(market_snap)
    recommended_exp, status_msg = volatility_controlled_exposure_filter(market_snap, context)

    # 알람 실행 (스파이크 발생 OR 데드맨 가동 OR 상관관계 붕괴)
    if is_spiking or recommended_exp == 0 or corr_msg:
        subject = f"🚨 [Emergency] {status_msg if recommended_exp == 0 else 'Market Anomaly Detected'}"
        body = f"""
[Digital War Room - Real-time Status]

세연 전략가님, 시스템이 자산 보호를 위해 긴급 조치를 검토 중입니다.

─────────────────────────────────────────
📢 실시간 요약 (Exposure: {recommended_exp}%)
─────────────────────────────────────────
- 일시: {now_str}
- 시스템 상태: {status_msg}
- 아침 데이터 기준: {context.get('date', 'Unknown')}
- POS_Z: {context.get('SP500_POS_Z', 'N/A')}

📊 자산별 변동률 (5분 기준)
{chr(10).join(summary_lines)}
{corr_msg}

─────────────────────────────────────────
🧠 전략적 가이드
─────────────────────────────────────────
💡 권장 익스포저가 {recommended_exp}%로 산출되었습니다.
💡 {'즉시 포지션을 동결하거나 축소하십시오.' if recommended_exp == 0 else '상관관계 붕괴 및 가격 스파이크를 주의 깊게 관찰하십시오.'}
─────────────────────────────────────────
        """
        # 로그 저장
        os.makedirs("insights", exist_ok=True)
        with open("insights/alerts.log", "a", encoding="utf-8") as f:
            f.write(f"[{now_str}] Exp:{recommended_exp}% | {status_msg} | {corr_msg[:30]}...\n")

        # 이메일 발송 (환경변수 체크)
        api_key = os.getenv("RESEND_API_KEY")
        if api_key:
            requests.post("https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"from": os.getenv("RESEND_FROM"), "to": [os.getenv("RESEND_TO")], "subject": subject, "text": body})
        print(f"📧 알림 발송 완료: {status_msg}")

if __name__ == "__main__":
    check_market_anomaly()
