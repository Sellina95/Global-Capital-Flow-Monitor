import time
import yfinance as yf
# 세연 님이 이미 만든 알림 함수가 있다면 임포트
# from utils.email_helper import send_strategic_alert 

def check_market_anomaly():
    # 1. 실시간 데이터 가져오기 (VIX, WTI, DXY)
    tickers = ["^VIX", "CL=F", "DX-Y.NYB"]
    data = yf.download(tickers, period="1d", interval="1m")
    
    # 2. 최근 5분 변동폭 계산 (예: VIX)
    vix_latest = data['Close']['^VIX'].iloc[-1]
    vix_5min_ago = data['Close']['^VIX'].iloc[-5]
    vix_change = (vix_latest - vix_5min_ago) / vix_5min_ago * 100

    print(f"[{time.strftime('%H:%M:%S')}] VIX 5min Change: {vix_change:.2f}%")

    # 3. 이상 징후 판단 (Threshold: 3% 급등 시)
    if abs(vix_change) > 3.0:
        print("🚨 Strategic Anomaly Detected!")
        # 여기서 이메일 발송 함수 호출!
        # send_strategic_alert(reason=f"VIX Sudden Spike: {vix_change:.2f}%")

# 무한 루프: 5분마다 실행
while True:
    try:
        check_market_anomaly()
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(300) # 300초(5분) 대기
