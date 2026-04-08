#CTA 포지션, CFTC선물포지션, 옵션 감마 구조,Dealer Gamma Exposure 를 관리하는 파일
import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

def get_z_score(series):
    return (series.iloc[-1] - series.mean()) / series.std()

def fetch_positioning_center():
    print("🚀 포지셔닝 관제 센터 가동: 데이터 수집 시작...")
    results = {'date': datetime.now().strftime('%Y-%m-%d')}

    # --- [1] CFTC/선물 포지션 Proxy (Price-Volume Momentum) ---
    # 실제 CFTC 배포 전까지는 선물 가격의 이동평균 괴리도로 '쏠림'을 추정합니다.
    tickers = {"ES=F": "SP500_POS", "ZN=F": "US10Y_POS", "DX=F": "DXY_POS"}
    for symbol, name in tickers.items():
        try:
            hist = yf.Ticker(symbol).history(period="1y")
            results[f"{name}_Z"] = round(get_z_score(hist['Close']), 2)
        except:
            results[f"{name}_Z"] = 0.0

    # --- [2] Dealer Gamma Exposure 추정 (Simple Proxy) ---
    # SPY 옵션의 Call/Put Open Interest 비율을 통해 시장의 '쿠션' 혹은 '폭탄' 여부를 판단합니다.
    try:
        spy = yf.Ticker("SPY")
        expirations = spy.options[:3]  # 가까운 3개 만기일 대상
        total_call_oi = 0
        total_put_oi = 0
        
        for date in expirations:
            opt = spy.option_chain(date)
            total_call_oi += opt.calls['openInterest'].sum()
            total_put_oi += opt.put['openInterest'].sum()
        
        # PCR(Put-Call Ratio) 기반 감마 바이어스 (낮을수록 강세 쏠림/과열)
        pcr = total_put_oi / total_call_oi
        results['DEALER_GAMMA_BIAS'] = round(pcr, 2)
    except:
        results['DEALER_GAMMA_BIAS'] = 1.0

    # --- [3] CTA Momentum (Trend Following) ---
    # 주요 지수가 단기MA > 장기MA 인지 확인하여 CTA들의 '기계적 매수' 여부를 판단합니다.
    try:
        spy_hist = yf.Ticker("SPY").history(period="1y")
        ma50 = spy_hist['Close'].rolling(50).mean().iloc[-1]
        ma200 = spy_hist['Close'].rolling(200).mean().iloc[-1]
        current = spy_hist['Close'].iloc[-1]
        
        # CTA Score: 1.0 (Full Bull), -1.0 (Full Bear)
        cta_score = 0
        if current > ma50: cta_score += 0.5
        if current > ma200: cta_score += 0.5
        if current < ma50: cta_score -= 0.5
        if current < ma200: cta_score -= 0.5
        results['CTA_MOMENTUM_SCORE'] = cta_score
    except:
        results['CTA_MOMENTUM_SCORE'] = 0.0

    # --- [4] 데이터 저장 ---
    df = pd.DataFrame([results])
    output_path = "data/positioning_data.csv"
    
    if not os.path.exists('data'): os.makedirs('data')
    
    if not os.path.exists(output_path):
        df.to_csv(output_path, index=False)
    else:
        df.to_csv(output_path, mode='a', header=False, index=False)
    
    print(f"✅ 포지셔닝 업데이트 완료: {results}")
    return results

if __name__ == "__main__":
    fetch_positioning_center()
