# filters/strategist_filters.py

"""
Seyeon Strategist Filters
미국10Y, DXY, WTI, VIX, USDKRW 를 기반으로
전략적 시장 해석을 자동 생성하는 모듈.
"""

def build_strategist_commentary(market_data: dict) -> list:
    comments = []
    comments.append("## 🧭 Strategist Commentary (Seyeon’s Filters)\n")

    us10y = market_data["US10Y"]["today"]
    dxy = market_data["DXY"]["today"]
    wti = market_data["WTI"]["today"]
    vix = market_data["VIX"]["today"]
    usdkrw = market_data["USDKRW"]["today"]

    # ① 금리 해석
    if us10y < 4.0:
        comments.append("- **미국 10년물 금리 하락 → 위험자산 선호 증가 신호.**")
    elif us10y > 4.5:
        comments.append("- **미국 금리 상승 → 성장주·신흥국 부담. 자금 미국 회귀 가능성.**")
    else:
        comments.append("- **미국 금리 보합 → 대기 모드. FOMC/고용지표 대기장세.**")

    # ② DXY 해석
    if dxy < 100:
        comments.append("- **DXY 약세 → 신흥국 통화 강세 여지, 외국인 자금 유입 가능성.**")
    else:
        comments.append("- **DXY 강세 → 글로벌 긴축 영향, 위험회피 심리 확대.**")

    # ③ 유가(WTI)
    if wti < 70:
        comments.append("- **WTI 저유가 → 물가 부담 완화, 금리 동결/인하 분위기 강화.**")
    elif wti > 85:
        comments.append("- **WTI 고유가 → 인플레이션 압력 재부활, 금리 인하 지연 가능성.**")

    # ④ 변동성 (VIX)
    if vix < 17:
        comments.append("- **VIX 안정권 → 시장 전반적으로 긍정적 분위기.**")
    else:
        comments.append("- **VIX 상승 → 위험회피 심리 증가. 주식·코인 변동성 확대.**")

    # ⑤ 원·달러 환율
    if usdkrw < 1350:
        comments.append("- **원화 강세 → 외국인 매수 유입 가능성 높음 (주식시장 +).**")
    elif usdkrw > 1450:
        comments.append("- **원화 약세 → 외국인 매도, 수입물가 상승 부담.**")

    return comments
