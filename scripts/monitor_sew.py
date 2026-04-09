import os
import time
import requests
import yfinance as yf
import sys

# 1. 이메일 발송 함수 (아까 찾은 보물 같은 '팔')
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

# 2. 핵심 감시 로직 (이름을 'check_market_anomaly'로 통일했습니다!)
def check_market_anomaly():
    print(f"🚀 [{time.strftime('%Y-%m-%d %H:%M:%S')}] Strategic Early Warning 감시 시작...")
    
    # 감시 자산: VIX, 유가, 달러인덱스
    tickers = {"VIX": "^VIX", "WTI": "CL=F", "DXY": "DX-Y.NYB"}
    
    for name, ticker in tickers.items():
        try:
            # 최근 데이터 가져오기
            df = yf.download(ticker, period="1d", interval="1m", progress=False)
            if df.empty or len(df) < 5: 
                print(f"⚠️ {name}: 데이터가 부족합니다.")
                continue
            
            curr_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-5]) # 5분 전
            change = (curr_price - prev_price) / prev_price * 100
            
            print(f"📊 {name}: {curr_price:.2f} (5분 변동: {change:+.2f}%)")

            # 🚨 임계치 설정: 3% 이상 급변 시 알림 (테스트를 위해 낮추려면 0.5 등으로 수정 가능)
            if abs(change) >= 3.0:
                subject = f"🚨 [SEW Alert] {name} 이상 징후 포착!"
                body = (
                    f"세연 전략가님, 실시간 감시 엔진이 수급 발작을 감지했습니다.\n\n"
                    f"- 자산: {name}\n"
                    f"- 현재가: {curr_price:.2f}\n"
                    f"- 5분 변동률: {change:+.2f}%\n\n"
                    f"즉시 14, 15번 포지셔닝 필터를 확인하세요!"
                )
                ok, note = send_sew_email(subject, body)
                print(f"📧 이메일 발송: {note}")
        except Exception as e:
            print(f"❌ {name} 감시 중 에러: {e}")

# 3. 메인 실행부
if __name__ == "__main__":
    # GitHub Actions 전용 (--once 옵션이 있을 때)
    if "--once" in sys.argv:
        check_market_anomaly()
    # 로컬 서버용 (무한 루프)
    else:
        while True:
            check_market_anomaly()
            print("💤 5분간 대기 후 다시 감시합니다...")
            time.sleep(300)
