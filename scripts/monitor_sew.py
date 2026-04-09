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
            # interval="1m"은 데이터가 불안정할 수 있어 넉넉히 가져옵니다.
            df = yf.download(ticker, period="1d", interval="1m", progress=False)
            if df.empty or len(df) < 5:
                summary_lines.append(f"- {name}: Data insufficient")
                continue
            
            # 🚨 수정된 핵심 포인트: iloc[-1] 뒤에 .values[0] 등을 써서 확실히 단일 값으로 추출
            # Multi-index 구조일 경우를 대비해 'Close' 열을 명확히 지정
            close_data = df['Close']
            
            # 데이터가 1차원 Series가 아닐 경우를 대비해 flatten 처리
            curr_price = float(close_data.iloc[-1])
            prev_price = float(close_data.iloc[-5]) # 5분 전
            
            change = (curr_price - prev_price) / prev_price * 100
            
            line = f"- {name}: {curr_price:.2f} ({change:+.2f}%)"
            summary_lines.append(line)
            print(line)

            # 테스트를 위해 임계치 0.01% 적용 (성공 확인 후 3.0으로 복구하세요!)
            if abs(change) >= 0.01: 
                alert_detected = True
        except Exception as e:
            summary_lines.append(f"- {name}: Error ({e})")
            print(f"❌ {name} 감시 중 에러: {e}")

    full_body = "Strategic Early Warning System - Status Report\n\n"
    full_body += "\n".join(summary_lines)
    full_body += f"\n\nChecked at (UTC): {time.strftime('%Y-%m-%d %H:%M:%S')}"

    if alert_detected:
        subject = f"🚨 [SEW Alert] Market Status ({time.strftime('%H:%M')})"
        ok, note = send_sew_email(subject, full_body)
        print(f"📧 Email Sent: {note}")
    else:
        print("✅ No significant anomaly.")

if __name__ == "__main__":
    check_market_anomaly()
