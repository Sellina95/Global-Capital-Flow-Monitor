import yfinance as yf
import pandas as pd
import numpy as np
import os
from datetime import datetime

def get_reliable_z_score(ticker_list, period="1y"):
    for ticker in ticker_list:
        try:
            hist = yf.Ticker(ticker).history(period=period)
            if not hist.empty and len(hist) > 20:
                close = hist["Close"].dropna()
                z_score = (close.iloc[-1] - close.mean()) / close.std()
                print(f"   ✅ 데이터 수집 성공: {ticker}")
                return round(z_score, 2)
        except Exception as e:
            print(f"   ⚠️ {ticker} 시도 실패: {e}")
            continue
    return 0.0

def _load_last_positioning_row(output_path: str):
    """
    기존 CSV에서 마지막 정상 행을 읽어옴.
    """
    if not os.path.exists(output_path):
        return None
    try:
        df = pd.read_csv(output_path)
        if df.empty:
            return None
        return df.iloc[-1].to_dict()
    except Exception as e:
        print(f"   ⚠️ 이전 positioning row 로드 실패: {e}")
        return None

def fetch_positioning_center():
    print("🚀 [포지셔닝 관제 센터 2.0] 가동: 데이터 수집 및 Z-Score 분석 시작...")

    output_path = "data/positioning_data.csv"
    last_row = _load_last_positioning_row(output_path)

    results = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "GAMMA_FETCH_OK": 0,
        "CTA_FETCH_OK": 0,
    }

    # --- [1] CFTC/선물 포지션 Proxy ---
    tickers_priority = {
        "SP500_POS": ["ES=F", "SPY", "VOO"],
        "US10Y_POS": ["ZN=F", "^TNX", "TLT"],
        "DXY_POS": ["DX-Y.NYB", "DX=F", "UUP"],
    }

    for name, t_list in tickers_priority.items():
        print(f"🔎 {name} 분석 중...")
        results[f"{name}_Z"] = get_reliable_z_score(t_list)

    # --- [2] Dealer Gamma Exposure ---
    try:
        spy = yf.Ticker("SPY")
        vix_hist = yf.Ticker("^VIX").history(period="5d")
        vix_current = vix_hist["Close"].iloc[-1] if not vix_hist.empty else 20.0

        expirations = spy.options[:2]
        if len(expirations) == 0:
            raise ValueError("SPY option expirations is empty")

        total_call_oi = 0
        total_put_oi = 0

        for date in expirations:
            opt = spy.option_chain(date)

            if "openInterest" not in opt.calls.columns or "openInterest" not in opt.puts.columns:
                raise ValueError(f"openInterest column missing for expiration {date}")

            total_call_oi += opt.calls["openInterest"].fillna(0).sum()
            total_put_oi += opt.puts["openInterest"].fillna(0).sum()

        if total_call_oi == 0:
            raise ValueError("total_call_oi is 0")

        pcr = total_put_oi / total_call_oi
        gamma_proxy = round(pcr * (20 / vix_current), 2)

        results["DEALER_GAMMA_BIAS"] = gamma_proxy
        results["GAMMA_FETCH_OK"] = 1

    except Exception as e:
        print(f"   ❌ Dealer Gamma 분석 실패: {e}")

        # 실패 시 이전 정상값 유지
        prev_gamma = None
        if last_row is not None:
            try:
                prev_gamma = float(last_row.get("DEALER_GAMMA_BIAS"))
            except Exception:
                prev_gamma = None

        if prev_gamma is not None:
            print(f"   ⚠️ 이전 gamma 값 유지: {prev_gamma}")
            results["DEALER_GAMMA_BIAS"] = prev_gamma
        else:
            print("   ⚠️ 이전 gamma 값 없음 → 중립값 1.0 사용")
            results["DEALER_GAMMA_BIAS"] = 1.0

    # --- [3] CTA Momentum ---
    try:
        spy_hist = yf.Ticker("SPY").history(period="1y")
        if not spy_hist.empty:
            close = spy_hist["Close"].dropna()
            ma50 = close.rolling(50).mean().iloc[-1]
            ma200 = close.rolling(200).mean().iloc[-1]
            current = close.iloc[-1]

            cta_score = 0.0
            if current > ma50:
                cta_score += 0.5
            if current > ma200:
                cta_score += 0.5
            if current < ma50:
                cta_score -= 0.5
            if current < ma200:
                cta_score -= 0.5

            results["CTA_MOMENTUM_SCORE"] = cta_score
            results["CTA_FETCH_OK"] = 1
        else:
            raise ValueError("SPY history empty")

    except Exception as e:
        print(f"   ❌ CTA 분석 실패: {e}")

        prev_cta = None
        if last_row is not None:
            try:
                prev_cta = float(last_row.get("CTA_MOMENTUM_SCORE"))
            except Exception:
                prev_cta = None

        if prev_cta is not None:
            print(f"   ⚠️ 이전 CTA 값 유지: {prev_cta}")
            results["CTA_MOMENTUM_SCORE"] = prev_cta
        else:
            print("   ⚠️ 이전 CTA 값 없음 → 0.0 사용")
            results["CTA_MOMENTUM_SCORE"] = 0.0

    # --- [4] 저장 ---
    df = pd.DataFrame([results])

    if not os.path.exists("data"):
        os.makedirs("data")

    try:
        if not os.path.exists(output_path):
            df.to_csv(output_path, index=False)
        else:
            df.to_csv(output_path, mode="a", header=False, index=False)
        print(f"✅ 포지셔닝 업데이트 완료! (Path: {output_path})")
    except Exception as e:
        print(f"❌ CSV 저장 실패: {e}")

    print(f"📊 최종 데이터 스냅샷: {results}")
    return results

if __name__ == "__main__":
    fetch_positioning_center()