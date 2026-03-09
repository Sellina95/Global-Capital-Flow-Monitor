# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-03-10

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.136  (-0.89% vs 4.173)
- **달러 인덱스**: 98.726  (-0.62% vs 99.345)
- **WTI 유가**: 86.640  (-15.65% vs 102.720)
- **변동성 지수 (VIX)**: 25.500  (-19.74% vs 31.770)
- **원/달러 환율**: 1466.290  (-1.26% vs 1485.010)

---

## 🚨 Regime Change Monitor (always-on)
- **Status:** ✅ DETECTED
- **Prev → Current:** RISK-OFF (긴축/불안·리스크 회피) → RISK-ON (완화 기대·리스크 선호)
- **File:** `insights/risk_alerts.txt` ✅ created
- **Email:** ❌ not sent (RESEND env missing (RESEND_API_KEY/RESEND_FROM/RESEND_TO))

---

## 🧾 Executive Summary (3 Lines)
- 현재 시장은 단기 리스크 선호가 회복되는 국면이며, 구조는 완화 기조.
- 유동성 여건이 개선되며 리스크 자산에 우호적이다.
- 전략적으로는 노출 확대가 가능하나, 규율 기반으로 70% 내에서 단계적으로 접근한다.

## 🧭 So What? (Decision Layer)
- **Risk Stance:** **INCREASE** *(target exposure: 70%)*
- **Context:** phase=RISK-ON (완화 기대·리스크 선호) / liquidity=UP-HIGH / credit_calm=True / geo=NORMAL

## 🗺️ Scenario Framework (Base / Bull / Bear)

### 🔹 Base Case
- 조건: 유동성 혼조 + 크레딧 안정 유지 / 변동성 급등 없이 박스권 장세 지속
- 전략: 노출 70% 유지, 퀄리티 중심 선별적 접근

### 🔼 Bull Case
- 조건: NET_LIQ 회복 (dir=UP & level=MID 이상) / 크레딧 스프레드 추가 축소
- 전략: 노출 단계적 확대, 성장/리스크 자산 베타 확장

### 🔻 Bear Case
- 조건: HY OAS > 4% 상회 또는 급등 / VIX 22 이상 또는 급등 전환
- 전략: 노출 35% 이하 축소, 방어/현금 비중 확대

## 🔗 Transmission Map (Macro → Industry → Company)
- **1-Line Conclusion:** 성장/고베타 우위 + 베타 확장 가능 → **High operating leverage / cyclicals / growth optionality** 선호

- **Policy → Valuation:** 할인율↓(멀티플 확장) → 성장/고베타 우위
- **Liquidity → Risk Budget:** 유동성 공급(리스크 허용↑) → 베타 확장 가능
- **Credit → Balance Sheet:** 크레딧 안정 → 시스템 리스크 제한

- **Sector/Company Shortcut:** Cyclicals/Tech(상황에 따라) + Small/Mid beta

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 25.50 → **High (Risk-off bias)**
- **핵심 조합(전일 대비 방향):** US10Y(↓) / DXY(↓) / VIX(↓)
- **판정:** **RISK-ON (완화 기대·리스크 선호)**
- **근거:** 금리↓ + 달러↓ + VIX↓ → 위험자산 선호/유동성 기대

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↓) / DXY(↓) / VIX(↓)
- **현실(FCI):** level=EASY (완화) / dir(→) | as of: 2026-03-06 (FRED last available)
- **유인(Real Rates):** level=NEUTRAL (중립) / dir(↑) | as of: 2026-03-06 (FRED last available)
- **판정:** **LIQUIDITY EXPANDING (Expectation-led) (기대 주도 확대)**
- **근거:** 기대는 완화 쪽, FCI/실질금리는 중립 이상 → 랠리 지속 가능성은 ‘열려있음’
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↓) / DXY(↓) / VIX(↓)
- **Policy Bias: EASING (완화) (STRONG, score=-2.5) | REAL_RATEΔ -0.020 / FCIΔ +0.000 / DXYΔ -0.619 / US10YΔ -0.037**
- **Expectations: dict received.**

- **판정:** **POLICY EASING (reinforced) (강화)**
- **근거:** 구조(REAL/FCI/DXY/US10Y)와 가격신호가 모두 EASING로 정렬 → 신호 신뢰도 상승
- **한줄요약 ~~** 구조=EASING (완화) & 가격=POLICY EASING (완화) 정렬 → 최종 POLICY EASING (reinforced) (강화)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-03-04 (FRED latest)
- **NET_LIQ level:** 5796840.1
- **TGA level:** 832053.0
- **RRP level:** 0.877
- **방향(전일 대비):** TGA(↓) / RRP(↓) / NET_LIQ(↑)
- **판정:** **LIQUIDITY SUPPORTIVE (완만한 유동성 우호)**
- **근거:** Net Liquidity↑ → 시장 내 달러 여력 개선
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-03-06 (FRED latest)
- **HY_OAS level:** 3.13% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↑) / +4.33%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↑) / LQD(↑)
- **HYG:** today 80.170 / prev 79.690 / pct 0.60%
- **LQD:** today 110.820 / prev 110.160 / pct 0.60%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, -0.89%)** → 완화 기대 강화
- DXY **(Strong, -0.62%)** → 달러 약세/리스크 선호
- WTI **(Strong, -15.65%)** → 물가 부담 완화
- VIX **(Strong, -19.74%)** → 심리 개선/리스크온
- 원/달러(USDKRW) **(Strong, -1.26%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Clear, +0.60%)** → 크레딧 위험선호↑
- LQD (IG Bond ETF) **(Clear, +0.60%)** → 우량채 강세(리스크오프 성향)

### 🧩 6) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함

- **금리 하락(US10Y↓)** → 달러 약세(DXY↓) / 할인율 부담 완화 / 위험자산 선호↑ 경향
- **변동성 하락(VIX↓)** → 심리 개선 / 위험자산 수요 회복 가능
- **유가 하락(WTI↓)** → 물가 부담 완화 / 긴축 압력 완화 가능

### ⚠ 6.5) Correlation Break Monitor

No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
- DEBUG: pct XLK=1.7991123472162127, XLF=-0.47458545623462756, XLE=-0.441930354160623, XLRE=0.20983948209057865
No significant sector-level correlation break detected.

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 하락(VIX↓)** → 심리 안정: 리스크 수용 여력 개선
- **금리 하락(US10Y↓)** → 완화 기대/할인율 부담 완화 가능
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 하락(WTI↓)** → 물가 부담 완화 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **-0.47**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.35 / defined weight: 1.35)*
- **3D Avg Score:** +0.72
- **Geo Momentum:** -1.19 *(Status: FALLING)*
- **Top Drivers:**
  - USDCNH: z_used=-1.61 (z1d=-3.17, z5d=+0.73, raw_w=0.18, norm_w=0.13) → contrib=-0.21
  - VIX: z_used=-1.38 (z1d=-2.46, z5d=+0.24, raw_w=0.18, norm_w=0.13) → contrib=-0.18
  - WTI: z_used=-1.98 (z1d=-4.27, z5d=+1.46, raw_w=0.10, norm_w=0.07) → contrib=-0.15
  - KR10Y_SPREAD: z_used=+1.38 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=+0.08
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, CN10Y_SPREAD, IL10Y_SPREAD, TR10Y_SPREAD

**So What?**
- 지정학 스트레스는 여전히 정상 범위에 있지만 최근 압력이 완화되고 있는 중입니다. 경계 유지.
- **Country ETF Crash?** Yes (EEM, EMB, EWJ, FXI, GLD, SPY)
- **Extreme Country Risk:** EEM, EMB, EWJ, FXI, GLD, SPY

### 💸 8) Incentive Filter
- **질문:** 누가 이득을 보고 있는가?
- **핵심 신호:** US10Y(↓) / DXY(↓) / WTI(↓)
- **이득을 보는 주체:**
  - Long-duration growth (discount-rate relief)
  - EM assets / risk trades
  - Energy consumers
- **손해를 보는 주체:**
  - USD strength trades
  - Energy producers

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** US10Y(↓) / DXY(↓) / WTI(↓) / VIX(↓)
- **판정:** **금리 하락(US10Y↓) + 달러 약세(DXY↓) + 유가 하락(WTI↓) + 변동성 완화(VIX↓)**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Strong) / WTI(Strong) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.136), DXY(98.726), VIX(25.50)

### 🏗️ 12) Structural Filter
- **질문:** 이 변화가 글로벌 구조(달러 패권/성장/에너지)에 어떤 힌트를 주는가?
- **핵심 신호:** US10Y(↓) / DXY(↓) / VIX(↓) / WTI(↓)
- **판정:** **NEUTRAL**
- **근거:** 패권/구조 신호가 뚜렷하지 않음

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: EASING (완화) (STRONG, score=-2.5) | REAL_RATEΔ -0.020 / FCIΔ +0.000 / DXYΔ -0.619 / US10YΔ -0.037
- **Sentiment (Fear&Greed):** 22.115565993419327 (FEAR)
- **Credit Calm (HY OAS<4):** True
- **Liquidity (NET_LIQ):** dir=UP / level=HIGH
- **Phase:** RISK-ON (완화 기대·리스크 선호)

- **🎯 Final Risk Action:** **INCREASE**
- **Risk Budget (0~100):** **70**
- **Narrative:** 구조=EASING / 심리=FEAR / 유동성=증가/높음 / 크레딧=안정 → Phase=RISK-ON (완화 기대·리스크 선호)

### ⚠ 14) Divergence Monitor
- **정의:** 구조(정책)와 가격(시장 국면)의 충돌 여부 감지
- **추가 이유:** 구조-가격 충돌은 국면 전환의 초기 신호가 될 수 있음

- **Structure:** EASING
- **Price Regime:** RISK-ON
- **Status:** **ALIGNED**
- **해석:** 구조와 가격 신호가 대체로 정렬

### 🎯 15) Volatility-Controlled Exposure (v2)
- **정의:** Risk Budget을 실제 익스포저로 변환 (Pro Version)
- **추가 이유:** 변동성·스트레스·국면을 모두 반영한 실전형 리스크 제어

- **Risk Budget:** 70
- **Phase Cap:** 85
- **VIX Level:** 25.50 (HIGH)
- **VIX Change (%):** -19.74%
- **Final Multiplier:** 0.84x

- **📊 Recommended Exposure:** **67%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **GROWTH TILT**
- **Duration Tilt:** **LONG DURATION FAVORED**
- **Cyclical vs Defensive:** **CYCLICAL FAVORED**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** LONG DURATION FAVORED
- **Inflation Factor:** DISINFLATION
- **USD Factor:** USD EASING
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v2)
- **정의:** Macro + Style/Factor/FINAL_STATE 종합 섹터 기울기 판단 (rule-based scoring)
- **추가 이유:** 리포트의 최종 output(포지셔닝)이 비어있지 않도록, 최소 OW/UW를 항상 생성

- **Context:** phase=RISK-ON (완화 기대·리스크 선호) / liquidity=UP-HIGH / structure=EASING / credit_calm=True
- **Overweight:** **Technology, Industrials, Financials**
- **Underweight:** **Consumer Staples**

- **Rationale (top drivers):**
  - OW Technology: +2: 유동성 공급 → 베타 확장 환경
  - OW Industrials: +2: 유동성 공급 → 경기순환(투자/생산) 우호
  - OW Financials: +1: 유동성 공급 → 리스크 선호 회복 구간 우호
  - UW Consumer Staples: -1: 유동성 공급 → 방어 섹터 상대매력 감소

### 🧬 19) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Preferred Company Traits:**

**Risk Control / Avoid:**
