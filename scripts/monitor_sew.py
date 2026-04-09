import os
import time
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

# ---------------------------
# 1. Slope(기울기) 계산 함수 (데이터 누락 방어 로직 포함)
# ---------------------------
def get_recent_pos_slope(csv_path: str, column_name='SP500_POS_Z'):
    try:
        if not os.path.exists(csv_path):
            return 0.0
        
        df = pd.read_csv(csv_path)
        # 데이터가 있는(NaN이 아닌) 행만 추출 (4/8일 누락 등 대응)
        valid_data = df[column_name].dropna().tail(3).tolist()
        
        if len(valid_data) >= 3:
            # (오늘 값 - 2일 전 값) / 2 -> 하루 평균 변화량(기울기)
            slope = (valid_data[-1] - valid_data[-3]) / 2
            return slope
        elif len(valid_data) == 2:
            return valid_data[-1] - valid_data[-2]
    except Exception as e:
        print(f"❌ Slope 계산 중 오류: {e}")
    return 0.0

# ---------------------------
# 2. 15번 필터: Volatility-Controlled Exposure (v2.6)
# ---------------------------
def volatility_controlled_exposure_filter(market_data: Dict[str, Any]) -> (int, str):
    risk_budget = float(market_data.get("RISK_BUDGET", 50))
    phase = str(market_data.get("MARKET_REGIME", "N/A")).upper()
    vix_today = market_data.get("VIX_TODAY")
    pos_z = float(market_data.get("SP500_POS_Z", 0.0))
    pos_slope = float(market_data.get("POS_SLOPE", 0.0))
    is_spiking = market_data.get("IS_SPIKING", False)

    # Dead Man's Switch 판단
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

    # 기본 Cap 및 계산 (단순화 버전)
    cap = 85 if "RISK-ON" in phase else 35
    exposure = min(risk_budget, cap)
    if vix_today and vix_today > 25: exposure *= 0.8
    
    return int(exposure), "Normal Operation"

# ---------------------------
# 3. 이메일 발송 함수
# ---------------------------
def send_sew_email(subject, body):
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM")
    to_email = os.getenv("RESEND_TO")
    if not api_key or not from_email or not to_email: 
        return False, "ENV Missing"
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": from_email, "to": [to_email], "subject": subject, "text": body}, 
            timeout=20
        )
        return (True, "sent") if 200 <= r.status_code < 300 else (False, f"HTTP {r.status_code}")
    except Exception as e: 
        return False, str(e)

# ---------------------------
# 4. 메인 감시 함수
# ---------------------------
def check_market_anomaly():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    csv_path = "market_data_history.csv" # 세연 님의 데이터 파일 경로
    
    tickers = {
        "VIX(공포지수)": "^VIX",
        "WTI(원유)": "CL=F",
        "DXY(달러)": "DX-Y.NYB",
        "TNX(10년물금리)": "^TNX",
        "NQ(나스닥선물)": "NQ=F"
    }
    
    summary_lines = []
    alert_assets = []
    threshold = 2.0 
    is_spiking = False

    print(f"🚀 [{now_str}] 통합 상황실 가동...")

    current_vix = None
    for name, ticker in tickers.items():
        try:
            df = yf.download(ticker, period="1d", interval="1m", progress=False)
            if df.empty: continue
            prices = df['Close'].values.flatten()
            curr = float(prices[-1])
            prev = float(prices[-5]) if len(prices) > 5 else prices[0]
            change = (curr - prev) / prev * 100
            
            if "^VIX" in ticker: current_vix = curr

            icon = "🔺" if change > 0 else "🔻"
            summary_lines.append(f"{icon} {name}: {curr:.2f} ({change:+.2f}%)")
            
            if abs(change) >= threshold:
                alert_assets.append(f"{name}({change:+.2f}%)")
                is_spiking = True
        except Exception as e:
            summary_lines.append(f"❌ {name}: 수집 실패")

    # 5. 15번 필터 연동 (Slope 계산 및 데드맨 판단)
    pos_slope = get_recent_pos_slope(csv_path)
    
    # 임시 market_data 구성 (실제 환경에 맞게 조정 필요)
    market_data_snapshot = {
        "RISK_BUDGET": 85,
        "MARKET_REGIME": "RISK-ON", # 예시
        "VIX_TODAY": current_vix,
        "SP500_POS_Z": 0.72, # 예시 (실제로는 CSV에서 가져옴)
        "POS_SLOPE": pos_slope,
        "IS_SPIKING": is_spiking
    }

    recommended_exp, status_msg = volatility_controlled_exposure_filter(market_data_snapshot)

    # 6. 이상 징후 혹은 데드맨 스위치 작동 시 알림
    if is_spiking or recommended_exp == 0:
        subject = f"🚨 [Emergency] {status_msg if recommended_exp == 0 else 'Market Spike Detected'}"
        body = f"""
[Digital War Room - Real-time Status]

세연 전략가님, 시스템이 자산 보호를 위해 긴급 조치를 검토 중입니다.

─────────────────────────────────────────
📢 실시간 요약 (Exposure: {recommended_exp}%)
─────────────────────────────────────────
- 일시: {now_str}
- 시스템 상태: {status_msg}
- 기울기(Slope): {pos_slope:.4f}

📊 자산별 변동률 (5분 기준)
{chr(10).join(summary_lines)}

─────────────────────────────────────────
🧠 전략적 가이드
─────────────────────────────────────────
💡 권장 익스포저가 {recommended_exp}%로 산출되었습니다. 
💡 {'즉시 포지션을 동결하거나 축소하십시오.' if recommended_exp == 0 else '주의 깊게 관찰하십시오.'}
─────────────────────────────────────────
        """
        ok, note = send_sew_email(subject, body)
        print(f"📧 알림 발송 완료: {note}")

if __name__ == "__main__":
    check_market_anomaly()
