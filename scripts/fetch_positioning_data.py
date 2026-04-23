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
                print(f"      last={close.iloc[-1]:.4f}, mean={close.mean():.4f}, std={close.std():.4f}, z={z_score:.4f}")
                return round(z_score, 2)
            else:
                print(f"   ⚠️ {ticker}: 데이터 부족 또는 empty")
        except Exception as e:
            print(f"   ⚠️ {ticker} 시도 실패: {e}")
            continue
    print("   ❌ 모든 fallback ticker 실패 → 0.0 반환")
    return 0.0

def fetch_positioning_center():
    print("🚀 [포지셔닝 관제 센터 2.0] 가동: 데이터 수집 및 Z-Score 분석 시작...")
    results = {'date': datetime.now().strftime('%Y-%m-%d')}

    # --- [1] CFTC/선물 포지션 Proxy (Fallback 시스템 적용) ---
    tickers_priority = {
        "SP500_POS": ["ES=F", "SPY", "VOO"],
        "US10Y_POS": ["ZN=F", "^TNX", "TLT"],
        "DXY_POS": ["DX-Y.NYB", "DX=F", "UUP"]
    }

    for name, t_list in tickers_priority.items():
        print(f"\n🔎 {name} 분석 중...")
        results[f"{name}_Z"] = get_reliable_z_score(t_list)

    # --- [2] Dealer Gamma Exposure 고도화 (VIX 가중치 반영) ---
    print("\n🔎 DEALER_GAMMA_BIAS 분석 중...")
    try:
        spy = yf.Ticker("SPY")

        # VIX 현재가 가져오기
        vix_hist = yf.Ticker("^VIX").history(period="5d")
        print(f"   VIX rows: {len(vix_hist)}")
        if not vix_hist.empty:
            print(f"   VIX tail:\n{vix_hist[['Close']].tail()}")
        vix_current = vix_hist['Close'].iloc[-1] if not vix_hist.empty else 20.0
        print(f"   vix_current = {vix_current}")

        # 옵션 만기일
        expirations = spy.options[:2]
        print(f"   expirations = {expirations}")

        total_call_oi = 0
        total_put_oi = 0

        if len(expirations) == 0:
            raise ValueError("SPY option expirations is empty")

        for date in expirations:
            print(f"   📅 option chain fetch: {date}")
            opt = spy.option_chain(date)

            call_cols = list(opt.calls.columns)
            put_cols = list(opt.puts.columns)
            print(f"      calls rows={len(opt.calls)}, puts rows={len(opt.puts)}")
            print(f"      calls cols={call_cols}")
            print(f"      puts cols={put_cols}")

            if 'openInterest' not in opt.calls.columns or 'openInterest' not in opt.puts.columns:
                raise ValueError(f"openInterest column missing for expiration {date}")

            call_oi = opt.calls['openInterest'].fillna(0).sum()
            put_oi = opt.puts['openInterest'].fillna(0).sum()

            print(f"      call_oi={call_oi}, put_oi={put_oi}")

            total_call_oi += call_oi
            total_put_oi += put_oi

        print(f"   total_call_oi = {total_call_oi}")
        print(f"   total_put_oi = {total_put_oi}")

        if total_call_oi == 0:
            raise ValueError("total_call_oi is 0, cannot compute PCR")

        pcr = total_put_oi / total_call_oi
        gamma_proxy = round(pcr * (20 / vix_current), 2)

        print(f"   pcr = {pcr:.6f}")
        print(f"   gamma_proxy = {gamma_proxy}")

        results['DEALER_GAMMA_BIAS'] = gamma_proxy

    except Exception as e:
        print(f"   ❌ Dealer Gamma 분석 실패: {e}")
        print("   ⚠️ fallback value 1.0 저장")
        results['DEALER_GAMMA_BIAS'] = 1.0

    # --- [3] CTA Momentum (Trend Following) ---
    print("\n🔎 CTA_MOMENTUM_SCORE 분석 중...")
    try:
        spy_hist = yf.Ticker("SPY").history(period="1y")
        print(f"   SPY rows: {len(spy_hist)}")

        if not spy_hist.empty:
            close = spy_hist['Close'].dropna()
            print(f"   latest closes:\n{close.tail()}")

            ma50 = close.rolling(50).mean().iloc[-1]
            ma200 = close.rolling(200).mean().iloc[-1]
            current = close.iloc[-1]

            print(f"   current = {current:.4f}")
            print(f"   ma50    = {ma50:.4f}")
            print(f"   ma200   = {ma200:.4f}")

            cta_score = 0
            if current > ma50:
                cta_score += 0.5
                print("   +0.5 : current > ma50")
            if current > ma200:
                cta_score += 0.5
                print("   +0.5 : current > ma200")
            if current < ma50:
                cta_score -= 0.5
                print("   -0.5 : current < ma50")
            if current < ma200:
                cta_score -= 0.5
                print("   -0.5 : current < ma200")

            print(f"   cta_score = {cta_score}")
            results['CTA_MOMENTUM_SCORE'] = cta_score
        else:
            print("   ⚠️ SPY history empty → CTA 0.0")
            results['CTA_MOMENTUM_SCORE'] = 0.0

    except Exception as e:
        print(f"   ❌ CTA 분석 실패: {e}")
        results['CTA_MOMENTUM_SCORE'] = 0.0

    # --- [4] 데이터 저장 및 CSV 적재 ---
    df = pd.DataFrame([results])
    output_path = "data/positioning_data.csv"

    if not os.path.exists('data'):
        os.makedirs('data')

    try:
        if not os.path.exists(output_path):
            df.to_csv(output_path, index=False)
            print(f"\n✅ 새 CSV 생성 완료: {output_path}")
        else:
            df.to_csv(output_path, mode='a', header=False, index=False)
            print(f"\n✅ 기존 CSV append 완료: {output_path}")
    except Exception as e:
        print(f"❌ CSV 저장 실패: {e}")

    print(f"\n📊 최종 데이터 스냅샷: {results}")
    return results

if __name__ == "__main__":
    fetch_positioning_center()