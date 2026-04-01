# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-04-02
**Data as of:** 2026-04-02

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.319  (+0.19% vs 4.311)
- **달러 인덱스**: 99.552  (-0.31% vs 99.857)
- **WTI 유가**: 98.910  (-3.15% vs 102.130)
- **변동성 지수 (VIX)**: 24.540  (-2.81% vs 25.250)
- **원/달러 환율**: 1513.080  (+0.59% vs 1504.170)

---

## 🚨 Regime Change Monitor (always-on)
- **Status:** ✅ DETECTED
- **Prev → Current:** RISK-OFF (긴축/불안·리스크 회피) → RISK-ON (부분 정렬)
- **File:** `insights/risk_alerts.txt` ✅ created
- **Email:** ✅ sent (sent)

---

Some commentary here
## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 24.54 → **High (Risk-off bias)**
- **핵심 조합(전일 대비 방향):** US10Y(↑) / DXY(↓) / VIX(↓)
- **판정:** **RISK-ON (부분 정렬)**
- **근거:** VIX↓ + (금리↓ 또는 달러↓) → 리스크 선호가 서서히 강화

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↑) / DXY(↓) / VIX(↓)
- **현실(FCI):** level=EASY (완화) / dir(↑) | as of: 2026-03-27 (FRED last available)
- **유인(Real Rates):** level=RESTRICTIVE (유인↓) / dir(↑) | as of: 2026-03-31 (FRED last available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↑) / DXY(↓) / VIX(↓)
- **Policy Bias: MIXED (혼조) (WEAK, score=-0.5) | REAL_RATEΔ -0.040 / FCIΔ +0.020 / DXYΔ -0.305 / US10YΔ +0.008**
- **Expectations: dict received.**

- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리/달러/변동성 신호가 완전히 정렬되지 않음
- **한줄요약 ~~** 구조=MIXED (혼조)(WEAK)는 참고, 가격=POLICY MIXED (정책 신호 혼조) 중심 → 최종 POLICY MIXED (정책 신호 혼조)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-03-25 (FRED latest)
- **NET_LIQ level:** 5783083.2
- **TGA level:** 874077.0
- **RRP level:** 0.777
- **방향(전일 대비):** TGA(↑) / RRP(↑) / NET_LIQ(↓)
- **판정:** **LIQUIDITY DRAINING (유동성 흡수)**
- **근거:** Net Liquidity↓ → 시장 내 달러 여력 축소 가능
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-03-31 (FRED latest)
- **HY_OAS level:** 3.28% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↓) / -5.20%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 좁혀지는 중 → 공포 온도 완화
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(↓)
- **HYG:** today 79.370 / prev 79.560 / pct -0.24%
- **LQD:** today 108.660 / prev 108.990 / pct -0.30%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, +0.19%)** → 완화 기대 약화/금리 부담
- DXY **(Clear, -0.31%)** → 달러 약세/리스크 선호
- WTI **(Strong, -3.15%)** → 물가 부담 완화
- VIX **(Strong, -2.81%)** → 심리 개선/리스크온
- 원/달러(USDKRW) **(Strong, +0.59%)** → 원화 약세/수급 부담
- HYG (High Yield ETF) **(Mild, -0.24%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Mild, -0.30%)** → 우량채 약세(리스크온 성향)

### 🧩 6) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함

- **금리 상승(US10Y↑)** → 달러 강세(DXY↑) / 위험자산 할인율 부담 / 성장주 변동성↑ 경향
- **변동성 하락(VIX↓)** → 심리 개선 / 위험자산 수요 회복 가능
- **유가 하락(WTI↓)** → 물가 부담 완화 / 긴축 압력 완화 가능

### ⚠ 6.5) Correlation Break Monitor

Correlation Break Detected:
- US10Y ↑ but Technology ↑ (QQQ/XLK)
- US10Y ↑ but SPY ↑
- USDKRW ↑ (KRW↓) but VIX ↓

So What?
- 할인율 역풍에도 기술이 강함 → 성장 내러티브/강한 매수세가 금리 부담을 상쇄
- 금리 역풍에도 시장이 상승 → ‘성장/실적/유동성 기대’가 금리보다 우위일 수 있음
- 원화 약세에도 변동성은 눌림 → 수급 요인/국지적 FX 스트레스 가능 (공격적 숏 보류)
- 결론: **공식이 깨진 구간** → 방향 베팅보다 **사이징 보수적 + 퀄리티/리더 중심**

### ⚠ 6.6) Sector Correlation Break Monitor
- DEBUG: pct XLK=1.51242276744617, XLF=0.14178589495371358, XLE=-3.738160567374897, XLRE=0.29389891379700167
Correlation Break Detected:
- US10Y ↑ but XLRE ↑ (Real Estate)
- US10Y ↑ but XLK ↑ (Tech)

So What?
- 금리 역풍에도 리츠 강세 → 배당/수급 요인이 금리 부담을 상쇄 (숏 신중)
- 할인율 역풍에도 기술 강세 → 성장 내러티브/매수세 우위 (고밸류 숏 신중)
- 결론: **섹터 ‘공식’이 깨진 구간** → 방향 베팅보다 **사이징 축소 + 리더 중심**

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 하락(VIX↓)** → 심리 안정: 리스크 수용 여력 개선
- **금리 상승(US10Y↑)** → 할인율 부담/유동성 압박 가능
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 하락(WTI↓)** → 물가 부담 완화 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **-0.28**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** -0.18
- **Geo Momentum:** -0.10 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Israel_2023
- **Cosine Similarity Score:** 0.142
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Israel_2023: 0.142
  - Red_Sea: 0.023
  - Ukraine_2022: -0.059
- **Top Drivers:**
  - VIX: z_used=-1.13 (z1d=-0.44, z5d=-2.16, raw_w=0.18, norm_w=0.14) → contrib=-0.16
  - USDCNH: z_used=-0.64 (z1d=-0.38, z5d=-1.03, raw_w=0.18, norm_w=0.14) → contrib=-0.09
  - GOLD: z_used=+0.84 (z1d=+0.67, z5d=+1.10, raw_w=0.12, norm_w=0.09) → contrib=+0.08
  - WTI: z_used=-0.92 (z1d=-1.06, z5d=-0.71, raw_w=0.10, norm_w=0.08) → contrib=-0.07
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Israel_2023** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (GLD)
- **Extreme Country Risk:** GLD

### 💸 8) Incentive Filter
- **질문:** 누가 이득을 보고 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↓) / WTI(↓)
- **이득을 보는 주체:**
  - Banks/Financials (higher rates)
  - EM assets / risk trades
  - Energy consumers
- **손해를 보는 주체:**
  - Long-duration growth (discount-rate pressure)
  - USD strength trades
  - Energy producers

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** US10Y(↑) / DXY(↓) / WTI(↓) / VIX(↓)
- **판정:** **금리 상승(US10Y↑) + 달러 약세(DXY↓) + 유가 하락(WTI↓) + 변동성 완화(VIX↓)**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Clear) / WTI(Strong) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.319), DXY(99.552), VIX(24.54)

### 🏗️ 12) Structural Filter (v2)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↓) / GOLD(↑) / VIX(↓) / WTI(↓)
- **판정:** **ENERGY-DRIVEN STAGFLATION (에너지 주도 스태그)**
- **근거:** 긴축적인 실질금리(2.0%) 환경에서도 고유가가 유지됨. 이는 공급망의 구조적 압박을 의미

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: MIXED (혼조) (WEAK, score=-0.5) | REAL_RATEΔ -0.040 / FCIΔ +0.020 / DXYΔ -0.305 / US10YΔ +0.008 (스태그플레이션)
- **Sentiment (Fear&Greed):** 40.004610403472114 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** DOWN (MID)
- **Phase:** RISK-ON (부분 정렬) (Cap: 30)
- **[SPECIAL ALERT]**: **⚠️ 에너지 비용 전이** (Structural Cap: 40)

- **🎯 Final Risk Action:** **REDUCE**
- **Risk Budget (0~100):** **30**
- **Narrative:** 구조=MIXED(스태그플레이션) / 심리=NEUTRAL / 유동성=감소/중간 / 크레딧=안정 → Phase=RISK-ON (부분 정렬)

### ⚠ 14) Divergence Monitor
- **정의:** 구조(정책)와 가격(시장 국면)의 충돌 여부 감지
- **추가 이유:** 구조-가격 충돌은 국면 전환의 초기 신호가 될 수 있음

- **Structure:** MIXED
- **Price Regime:** RISK-ON
- **Status:** **ALIGNED**
- **해석:** 구조와 가격 신호가 대체로 정렬

### 🎯 15) Volatility-Controlled Exposure (v2)
- **정의:** Risk Budget을 실제 익스포저로 변환 (Pro Version)
- **추가 이유:** 변동성·스트레스·국면을 모두 반영한 실전형 리스크 제어

- **Risk Budget:** 30
- **Phase Cap:** 85
- **VIX Level:** 24.54 (HIGH)
- **VIX Change (%):** -2.81%
- **Final Multiplier:** 0.80x

- **📊 Recommended Exposure:** **28%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **VALUE TILT**
- **Duration Tilt:** **SHORT DURATION FAVORED**
- **Cyclical vs Defensive:** **DEFENSIVE FAVORED**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** SHORT DURATION FAVORED
- **Inflation Factor:** NEUTRAL
- **USD Factor:** USD EASING
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.2)

**Context:** phase=RISK-ON (부분 정렬) / T10Y2Y=0.52 (MODERATE STEEP) / VIX=25.25 (VOLATILITY ELEVATED) / liquidity=DOWN-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE

**Overweight:** Consumer Staples, Utilities, Health Care, Financials, Industrials

**Underweight:** Technology, Real Estate, Consumer Discretionary

**Scoreboard:**
- Consumer Staples: +5  (+2 VOL, +3 LIQ, = +5)
- Utilities: +4  (+3 VOL, +1 LIQ, = +4)
- Health Care: +3  (+3 LIQ, = +3)
- Financials: +2  (+2 CURVE, = +2)
- Industrials: +2  (+1 CURVE, +1 PHASE, = +2)
- Consumer Discretionary: -1  (-1 LIQ, = -1)
- Real Estate: -2  (-2 LIQ, = -2)
- Technology: -5  (-3 VOL, -3 LIQ, +1 PHASE, = -5)

**Rationale (top drivers):**
- OW Consumer Staples: +2: VOLATILITY ELEVATED → 필수소비 선호 (absolute mode: VIX 25.2)
- OW Consumer Staples: +3: 유동성 긴축 → 방어적 필수소비 선호
- OW Utilities: +3: VOLATILITY ELEVATED → 방어주 우위 (absolute mode: VIX 25.2)
- OW Utilities: +1: 유동성 긴축 → 방어주 버퍼
- OW Health Care: +3: 유동성 긴축 → 안정적 현금흐름 선호
- OW Financials: +2: 완만한 스티프닝(0.52) → 예대마진 개선
- UW Technology: +1: RISK-ON → 성장주 미세 가점
- UW Technology: -3: VOLATILITY ELEVATED → 위험자산 회피 (absolute mode: VIX 25.2)


---

### 🧬 19) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Preferred Company Traits:**
- High Free Cash Flow generators
- Net cash or low leverage balance sheets
- Stable margins / pricing power
- Low to mid beta exposure
- RAROC-friendly profile

**Risk Control / Avoid:**
- Negative FCF / cash-burn models
- High leverage / refinancing-dependent names
- Long-duration, high-multiple growth

## 🧭 So What? (Decision Layer)
- **Risk Stance:** **REDUCE** *(target exposure: 30%)*
- **Context:** phase=RISK-ON (부분 정렬) / liquidity=DOWN-MID / credit_calm=True / geo=NORMAL

## 🗺️ Scenario Framework (Base / Bull / Bear)

### 🔹 Base Case
- 조건: 유동성 혼조 + 크레딧 안정 유지 / 변동성 급등 없이 박스권 장세 지속
- 전략: 노출 30% 유지, 퀄리티 중심 선별적 접근

### 🔼 Bull Case
- 조건: NET_LIQ 회복 (dir=UP & level=MID 이상) / 크레딧 스프레드 추가 축소
- 전략: 노출 단계적 확대, 성장/리스크 자산 베타 확장

### 🔻 Bear Case
- 조건: HY OAS > 4% 상회 또는 급등 / VIX 22 이상 또는 급등 전환
- 전략: 노출 35% 이하 축소, 방어/현금 비중 확대

## 🔗 Transmission Map (Macro → Industry → Company)
- **1-Line Conclusion:** 퀄리티 중심 차별화 + 고베타/레버리지 제한 → **High FCF / Low leverage / pricing power** 선호

- **Policy → Valuation:** 할인율 방향성 불명확 → 퀄리티 중심 차별화
- **Liquidity → Risk Budget:** 유동성 흡수(리스크 허용↓) → 고베타/레버리지 제한
- **Credit → Balance Sheet:** 크레딧 안정 → 시스템 리스크 제한

- **Sector/Company Shortcut:** Defensive(Staples/Utilities/Healthcare) + Mega-cap quality

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -1.125553087582153
- **Z-Score (5d):** -0.27094572415262175

### EEM
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.4632793517021279
- **Z-Score (5d):** -0.14430742182060774

### EIS
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.2942146372947476
- **Z-Score (5d):** -0.6143700282885403

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.10099464104614363
- **Z-Score (5d):** -0.5863816538505023

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.4838046592612248
- **Z-Score (5d):** 0.5626332650513497

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.5762217923554426
- **Z-Score (5d):** -0.1593320994177461

### GLD
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 0.6082411804821091
- **Z-Score (5d):** 0.8252027093133838

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.9157132687291649
- **Z-Score (5d):** 0.21190208778632655

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.6981231095354877
- **Z-Score (5d):** -0.29064307546720186
