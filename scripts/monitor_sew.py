import os
import time
import requests
import yfinance as yf
import sys
from datetime import datetime

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
            timeout=20,
        )
        return (True, "sent") if 200 <= r.status_code < 300 else (False, f"HTTP {r.status_code}")
    except Exception as e:
        return False, str(e)

def check_market_anomaly():
    # 시간 설정 (KST 기준은 UTC+9지만, 일단 깃허브 시간 기준으로 표시)
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"🚀 [{now_str}] Strategic Early Warning Monitoring...")
    
    tickers = {"VIX(변동성)": "^VIX", "WTI(원유)": "CL=F", "DXY(달러인덱스)": "DX-Y.NYB"}
    summary_lines = []
    alert_assets = []
    threshold = 2.0 # 세연 님이 설정하신 2.0% 임계치

    for name, ticker in tickers.items():
        try:
            df = yf.download(ticker, period="1d", interval="1m", progress=False)
            if df.empty or len(df) < 5:
                continue
            
            prices = df['Close'].values.flatten()
            curr_price = float(prices[-1])
            prev_price = float(prices[-5])
            change = (curr_price - prev_price) / prev_price * 100
            
            status_icon = "🔺" if change > 0 else "🔻"
            line = f"{status_icon} {name}: {curr_price:.2f} ({change:+.2f}%)"
            summary_lines.append(line)
            
            if abs(change) >= threshold:
                alert_assets.append(f"{name}({change:+.2f}%)")
        except Exception as e:
            summary_lines.append(f"❌ {name}: 데이터 수집 에러")

    if alert_assets:
        # 🚨 이메일 제목: 어떤 자산이 튀었는지 바로 알 수 있게
        subject = f"🚨 [SEW Alert] {', '.join(alert_assets)} 수급 발작 포착!"
        
        # 📝 이메일 본문: 전략적 가독성 높이기
        body = f"""
[Strategic Early Warning System - Briefing]

세연 전략가님, 실시간 시장 감시 엔진이 '비정상적 수급 쏠림'을 감지했습니다.

📍 감지 시각: {now_str} (UTC)
📍 감지 대상: {', '.join(alert_assets)}

-----------------------------------------
📊 현재 시장 주요 지표 현황 (5분 변동률)
-----------------------------------------
{chr(10).join(summary_lines)}

-----------------------------------------
💡 전략적 가이드라인
1. 현재 'EVENT-WATCHING' 국면이므로 작은 수급 이탈이 패닉 셀로 이어질 수 있습니다.
2. 14번(유동성 가드레일) 및 15번(리스크 오프 필터) 수치를 즉시 점검하십시오.
3. 해당 자산의 급변이 단순 기술적 반등인지, 매크로 펀더멘털의 균열인지 파악이 필요합니다.

※ 본 메일은 설정하신 임계치({threshold}%) 초과 시에만 자동 발송됩니다.
-----------------------------------------
        """
        ok, note = send_sew_email(subject, body)
        print(f"📧 상세 브리핑 발송 완료: {note}")
    else:
        print("✅ 이상 징후 없음. 평온한 시장입니다.")

if __name__ == "__main__":
    check_market_anomaly()
