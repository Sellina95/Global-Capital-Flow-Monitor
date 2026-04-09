import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

def get_reliable_z_score(ticker_list, period="1y"):
    """
    FALLBACK 로직: 리스트 내 티커들을 순차적으로 시도하여 
    유효한 데이터가 나오면 Z-Score를 계산합니다.
    """
    for ticker in ticker_list:
        try:
            hist = yf.Ticker(ticker).history(period=period)
            if not hist.empty and len(hist) > 20:
                close = hist['Close'].dropna()
                z_score = (close.iloc[-1] - close.mean()) / close.std()
                print(f"   ✅ 데이터 수집 성공: {ticker}")
                return round(z_score, 2)
        except Exception as e:
            print(f"   ⚠️ {ticker} 시도 실패: {e}")
            continue
    return 0.0 # 모든 티커 실패 시 기본값

def fetch_positioning_center():
    print("🚀 [포지셔닝 관제 센터 2.0] 가동: 데이터 수집 및 Z-Score 분석 시작...")
    results = {'date': datetime.now().strftime('%Y-%m-%d')}

    # --- [1] CFTC/선물 포지션 Proxy (Fallback 시스템 적용) ---
    # 메인 코드의 FALLBACK_TICKERS 우선순위를 반영하여 데이터 안정성 확보
    tickers_priority = {
        "SP500_POS": ["ES=F", "SPY", "VOO"],
        "US10Y_POS": ["ZN=F", "^TNX", "TLT"],
        "DXY_POS": ["DX-Y.NYB", "DX=F", "UUP"] # 0.0 저주 탈출용
    }

    for name, t_list in tickers_priority.items():
        print(f"🔎 {name} 분석 중...")
        results[f"{name}_Z"] = get_reliable_z_score(t_list)

    # --- [2] Dealer Gamma Exposure 고도화 (VIX 가중치 반영) ---
    # 단순히 비율만 보는 게 아니라 시장의 공포(VIX) 대비 옵션 방어력을 계산합니다.
    try:
        spy = yf.Ticker("SPY")
        # VIX 현재가 가져오기 (감마 보정용)
        vix_hist = yf.Ticker("^VIX").history(period="5d")
        vix_current = vix_hist['Close'].iloc[-1] if not vix_hist.empty else 20.0
        
        expirations = spy.options[:2]  # 가장 영향력 큰 근월물 2개 대상
        total_call_oi = 0
        total_put_oi = 0
        
        for date in expirations:
            opt = spy.option_chain(date)
            total_call_oi += opt.calls['openInterest'].sum()
            total_put_oi += opt.put['openInterest'].sum()
        
        # 기본 PCR (Put-Call Ratio)
        pcr = total_put_oi / total_call_oi
        
        # 💡 Gamma Bias 고도화: VIX가 낮을수록(평온) 감마가 시장을 잘 받쳐준다고 해석
        # VIX 20을 기준으로 가중치 부여 (값이 낮을수록 과열/상방쏠림)
        gamma_proxy = round(pcr * (20 / vix_current), 2)
        results['DEALER_GAMMA_BIAS'] = gamma_proxy
    except Exception as e:
        print(f"   ❌ Dealer Gamma 분석 실패: {e}")
        results['DEALER_GAMMA_BIAS'] = 1.0

    # --- [3] CTA Momentum (Trend Following) ---
    try:
        spy_hist = yf.Ticker("SPY").history(period="1y")
        if not spy_hist.empty:
            ma50 = spy_hist['Close'].rolling(50).mean().iloc[-1]
            ma200 = spy_hist['Close'].rolling(200).mean().iloc[-1]
            current = spy_hist['Close'].iloc[-1]
            
            cta_score = 0
            if current > ma50: cta_score += 0.5
            if current > ma200: cta_score += 0.5
            if current < ma50: cta_score -= 0.5
            if current < ma200: cta_score -= 0.5
            results['CTA_MOMENTUM_SCORE'] = cta_score
        else:
            results['CTA_MOMENTUM_SCORE'] = 0.0
    except:
        results['CTA_MOMENTUM_SCORE'] = 0.0

    # --- [4] 데이터 저장 및 CSV 적재 ---
    df = pd.DataFrame([results])
    output_path = "data/positioning_data.csv"
    
    if not os.path.exists('data'): os.makedirs('data')
    
    try:
        if not os.path.exists(output_path):
            df.to_csv(output_path, index=False)
        else:
            # 중복 날짜 방지 (선택 사항: 하루에 여러 번 돌려도 마지막 기록만 남기고 싶을 때)
            df.to_csv(output_path, mode='a', header=False, index=False)
        print(f"✅ 포지셔닝 업데이트 완료! (Path: {output_path})")
    except Exception as e:
        print(f"❌ CSV 저장 실패: {e}")
    
    print(f"📊 최종 데이터 스냅샷: {results}")
    return results

if __name__ == "__main__":
    fetch_positioning_center()
