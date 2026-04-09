import os
import time
import requests
import yfinance as yf
import sys

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
    print(f"🚀 [{time.strftime('%Y-%m-%d %H:%M:%S')}] Monitoring Start...")
    tickers = {"VIX": "^VIX", "WTI": "CL=F", "DXY": "DX-Y.NYB"}
    summary_lines = []
    alert_detected = False

    for name, ticker in tickers.items():
        try:
            # 데이터를 가져온 후 인덱스를 단순화합니다.
            df = yf.download(ticker, period="1d", interval="1m", progress=False)
            if df.empty or len(df) < 5:
                summary_lines.append(f"- {name}: Data insufficient")
                continue
            
            # 🚨 핵심 수정: 어떤 구조로 들어오든 '최근 값' 딱 하나만 추출합니다.
            # .values.flatten()을 사용해 1차원 배열로 만든 뒤 마지막 값을 가져옵니다.
            prices = df['Close'].values.flatten()
            curr_price = float(prices[-1])
            prev_price = float(prices[-5]) # 5분 전
            
            change = (curr_price - prev_price) / prev_price * 100
            
            line = f"- {name}: {curr_price:.2f} ({change:+.2f}%)"
            summary_lines.append(line)
            print(line)

            # 테스트용 임계치 0.01 (성공 확인 후 높이세요!)
            if abs(change) >= 0.01: 
                alert_detected = True
        except Exception as e:
            # 에러 발생 시 로그를 아주 상세하게 찍습니다.
            print(f"❌ {name} 감시 중 에러 발생: {str(e)}")
            summary_lines.append(f"- {name}: Error ({str(e)})")

    # 이메일 본문 구성
    full_body = "Strategic Early Warning System - Status Report\n\n"
    full_body += "\n".join(summary_lines)
    full_body += f"\n\nChecked at: {time.strftime('%Y-%m-%d %H:%M:%S')}"

    if alert_detected:
        subject = f"🚨 [SEW Alert] Market Status ({time.strftime('%H:%M')})"
        ok, note = send_sew_email(subject, full_body)
        print(f"📧 Email Sent Result: {note}")
    else:
        print("✅ No significant anomaly detected.")

if __name__ == "__main__":
    check_market_anomaly()
