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
                close = hist["Close"].dropna()
                z_score = (close.iloc[-1] - close.mean()) / close.std()
                print(f"   ✅ 데이터 수집 성공: {ticker}")
                return round(z_score, 2)
            else:
                print(f"   ⚠️ {ticker}: 데이터 부족 또는 empty")
        except Exception as e:
            print(f"   ⚠️ {ticker} 시도 실패: {e}")
            continue

    print("   ❌ 모든 fallback ticker 실패 → 0.0 반환")
    return 0.0


def _load_last_positioning_row(output_path: str):
    """
    기존 CSV에서 마지막 정상 행을 읽어옵니다.
    """
    if not os.path.exists(output_path):
        return None

    try:
        df = pd.read_csv(output_path)
        if df.empty:
            return None

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

        if df.empty:
            return None

        return df.iloc[-1].to_dict()

    except Exception as e:
        print(f"   ⚠️ 이전 positioning row 로드 실패: {e}")
        return None


def _save_positioning_snapshot(results: dict, output_path: str):
    """
    날짜 기준으로 같은 날짜 행은 덮어쓰고,
    최종적으로 날짜당 1행만 유지하도록 저장합니다.
    """
    new_df = pd.DataFrame([results])

    # 컬럼 순서 고정
    ordered_cols = [
        "date",
        "SP500_POS_Z",
        "US10Y_POS_Z",
        "DXY_POS_Z",
        "DEALER_GAMMA_BIAS",
        "CTA_MOMENTUM_SCORE",
        "GAMMA_FETCH_OK",
        "CTA_FETCH_OK",
    ]

    for col in ordered_cols:
        if col not in new_df.columns:
            new_df[col] = np.nan

    new_df = new_df[ordered_cols]

    if not os.path.exists(output_path):
        new_df.to_csv(output_path, index=False)
        print(f"✅ 새 positioning_data.csv 생성 완료 ({output_path})")
        return

    try:
        existing = pd.read_csv(output_path)

        # 컬럼 불일치 보정
        for col in ordered_cols:
            if col not in existing.columns:
                existing[col] = np.nan

        existing = existing[ordered_cols]

        # date 정리
        existing["date"] = pd.to_datetime(existing["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        new_df["date"] = pd.to_datetime(new_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")

        target_date = new_df.iloc[0]["date"]

        # 같은 날짜 기존 행 제거
        existing = existing[existing["date"] != target_date]

        # 새 데이터 추가
        updated = pd.concat([existing, new_df], ignore_index=True)

        # 날짜 정렬
        updated["date"] = pd.to_datetime(updated["date"], errors="coerce")
        updated = updated.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        updated["date"] = updated["date"].dt.strftime("%Y-%m-%d")

        updated.to_csv(output_path, index=False)
        print(f"✅ 날짜 기준 overwrite 저장 완료 ({output_path})")

    except Exception as e:
        print(f"❌ CSV 저장 실패: {e}")


def fetch_positioning_center():
    print("🚀 [포지셔닝 관제 센터 2.0] 가동: 데이터 수집 및 Z-Score 분석 시작...")

    output_path = "data/positioning_data.csv"

    if not os.path.exists("data"):
        os.makedirs("data")

    last_row = _load_last_positioning_row(output_path)

    results = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "GAMMA_FETCH_OK": 0,
        "CTA_FETCH_OK": 0,
    }

    # --- [1] CFTC/선물 포지션 Proxy (Fallback 시스템 적용) ---
    tickers_priority = {
        "SP500_POS": ["ES=F", "SPY", "VOO"],
        "US10Y_POS": ["ZN=F", "^TNX", "TLT"],
        "DXY_POS": ["DX-Y.NYB", "DX=F", "UUP"],
    }

    for name, t_list in tickers_priority.items():
        print(f"\n🔎 {name} 분석 중...")
        results[f"{name}_Z"] = get_reliable_z_score(t_list)

    # --- [2] Dealer Gamma Exposure ---
    print("\n🔎 DEALER_GAMMA_BIAS 분석 중...")
    try:
        spy = yf.Ticker("SPY")

        vix_hist = yf.Ticker("^VIX").history(period="5d")
        vix_current = vix_hist["Close"].iloc[-1] if not vix_hist.empty else 20.0
        print(f"   vix_current = {vix_current}")

        expirations = spy.options[:2]
        print(f"   expirations = {expirations}")

        if len(expirations) == 0:
            raise ValueError("SPY option expirations is empty")

        total_call_oi = 0
        total_put_oi = 0

        for date in expirations:
            print(f"   📅 option chain fetch: {date}")
            opt = spy.option_chain(date)

            if "openInterest" not in opt.calls.columns or "openInterest" not in opt.puts.columns:
                raise ValueError(f"openInterest column missing for expiration {date}")

            call_oi = opt.calls["openInterest"].fillna(0).sum()
            put_oi = opt.puts["openInterest"].fillna(0).sum()

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

        results["DEALER_GAMMA_BIAS"] = gamma_proxy
        results["GAMMA_FETCH_OK"] = 1

    except Exception as e:
        print(f"   ❌ Dealer Gamma 분석 실패: {e}")

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

    # --- [3] CTA Momentum (Trend Following) ---
    print("\n🔎 CTA_MOMENTUM_SCORE 분석 중...")
    try:
        spy_hist = yf.Ticker("SPY").history(period="1y")
        print(f"   SPY rows: {len(spy_hist)}")

        if spy_hist.empty:
            raise ValueError("SPY history empty")

        close = spy_hist["Close"].dropna()
        current = close.iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1]

        print(f"   current = {current:.4f}")
        print(f"   ma50    = {ma50:.4f}")
        print(f"   ma200   = {ma200:.4f}")

        cta_score = 0.0
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

        results["CTA_MOMENTUM_SCORE"] = cta_score
        results["CTA_FETCH_OK"] = 1

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
    _save_positioning_snapshot(results, output_path)

    print(f"\n📊 최종 데이터 스냅샷: {results}")
    return results


if __name__ == "__main__":
    fetch_positioning_center()