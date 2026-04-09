import os
import time
import requests
import yfinance as yf

# 1. 방금 찾은 그 '팔' (이메일 함수) 이식
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
        return (True, "sent") if 200 <= r.status_code < 300 else (False, f"Error: {r.status_code}")
    except Exception as e:
        return False, str(e)

# 2. 5분 단위 실시간 감시 로직
def run_strategic_early_warning():
    print("🚀 Strategic Early Warning System 가동 중...")
    
    # 우리가 감시할 '이상 징후' 리스트 (VIX, 유가 등)
    tickers = {"VIX": "^VIX", "WTI": "CL=F"}
    
    while True:
        try:
            # 데이터 가져오기 (최근 15분)
            for name, ticker in tickers.items():
                df = yf.download(ticker, period="1d", interval="1m", progress=False)
                if len(df) < 5: continue
                
                curr_price = df['Close'].iloc[-1]
                prev_price = df['Close'].iloc[-5] # 5분 전 가격
                change = (curr_price - prev_price) / prev_price * 100
                
                print(f"[{time.strftime('%H:%M:%S')}] {name}: {curr_price:.2f} ({change:+.2f}%)")

                # 🚨 이상 징후 판단: 5분 만에 3% 이상 급변할 때 (세연 님이 원하는 수치로 조정 가능)
                if abs(change) >= 3.0:
                    subject = f"🚨 [SEW Alert] {name} Unusual Movement Detected!"
                    body = (
                        f"세연 전략가님, 시장에 이상 수급이 포착되었습니다.\n\n"
                        f"- 자산: {name}\n"
                        f"- 현재가: {curr_price:.2f}\n"
                        f"- 5분 변동률: {change:.2f}%\n\n"
                        f"14, 15번 필터를 점검하고 리스 가드레일을 확인하세요!"
                    )
                    ok, note = send_sew_email(subject, body)
                    print(f"📧 알림 발송 결과: {note}")

        except Exception as e:
            print(f"⚠️ 에러 발생: {e}")
            
        time.sleep(300) # 5분 대기

if __name__ == "__main__":
    run_strategic_early_warning()
