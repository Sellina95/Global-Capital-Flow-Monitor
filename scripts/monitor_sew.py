import os
import time
import requests
import yfinance as yf
from datetime import datetime

def send_sew_email(subject, body):
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM")
    to_email = os.getenv("RESEND_TO")
    if not api_key or not from_email or not to_email: return False, "ENV Missing"
    try:
        r = requests.post("https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": from_email, "to": [to_email], "subject": subject, "text": body}, timeout=20)
        return (True, "sent") if 200 <= r.status_code < 300 else (False, f"HTTP {r.status_code}")
    except Exception as e: return False, str(e)

def check_market_anomaly():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 1. 감시 자산 확장 (데이터 정교화)
    tickers = {
        "VIX(공포지수)": "^VIX",
        "WTI(원유)": "CL=F",
        "DXY(달러)": "DX-Y.NYB",
        "TNX(10년물금리)": "^TNX", # 국채 금리 추가
        "NQ(나스닥선물)": "NQ=F"    # 나스닥 선물 추가
    }
    
    summary_lines = []
    alert_assets = []
    threshold = 2.0 
    anomaly_count = 0

    print(f"🚀 [{now_str}] 통합 상황실 가동...")

    for name, ticker in tickers.items():
        try:
            df = yf.download(ticker, period="1d", interval="1m", progress=False)
            if df.empty: continue
            prices = df['Close'].values.flatten()
            curr = float(prices[-1])
            prev = float(prices[-5])
            change = (curr - prev) / prev * 100
            
            icon = "🔺" if change > 0 else "🔻"
            line = f"{icon} {name}: {curr:.2f} ({change:+.2f}%)"
            summary_lines.append(line)
            
            if abs(change) >= threshold:
                alert_assets.append(f"{name}({change:+.2f}%)")
                anomaly_count += 1
        except:
            summary_lines.append(f"❌ {name}: 수집 실패")

    # 2. 통합 리포트 본문 구성
    if alert_assets:
        subject = f"🚨 [상황실] {', '.join(alert_assets)} 15번 필터 수급 발작 포착!"
        
        body = f"""
[Digital War Room - Real-time Status]

세연 전략가님, 시스템이 '15번 수급 쏠림 필터'에서 이상 징후를 감지했습니다.

─────────────────────────────────────────
📢 실시간 요약 (Status: 🚨 DETECTED)
─────────────────────────────────────────
- 일시: {now_str} (UTC)
- 탐지된 이상 징후: {anomaly_count}건 발생
- 주요 타격 자산: {', '.join(alert_assets)}

📊 자산별 실시간 수치 (5분 변동률)
{chr(10).join(summary_lines)}

─────────────────────────────────────────
🧠 전략적 가이드 (14/15번 필터 체크)
─────────────────────────────────────────
✅ [15번 필터] 수급 쏠림 : {anomaly_count}건 포착 (대응 요망)
💡 현재 {', '.join(alert_assets)}의 변동성이 임계치({threshold}%)를 초과했습니다.
💡 이는 단순 노이즈가 아닌 '수급의 방향성 전환'일 확률이 높습니다.

✅ [14번 필터] 유동성 가드레일 : EVENT-WATCHING 국면
💡 유동성이 극도로 민감한 구간이므로, 위 자산의 움직임이 
   포트폴리오 전체 리스크(Beta)에 미치는 영향을 즉시 확인하십시오.

─────────────────────────────────────────
Log: ✅ {anomaly_count} Anomaly Detected / Email sent to {os.getenv("RESEND_TO")}
        """
        ok, note = send_sew_email(subject, body)
        print(f"📧 통합 리포트 발송: {note}")
    else:
        print(f"✅ [{now_str}] 이상 없음. 15번 필터 통과.")

if __name__ == "__main__":
    check_market_anomaly()
