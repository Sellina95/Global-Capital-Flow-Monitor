# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-02-25

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.052  (-0.05% vs 4.054)
- **달러 인덱스**: 97.851  (-0.03% vs 97.882)
- **WTI 유가**: 65.470  (-0.94% vs 66.090)
- **변동성 지수 (VIX)**: 18.680  (-2.05% vs 19.070)
- **원/달러 환율**: 1427.000  (-0.07% vs 1428.010)

---

## 🚨 Regime Change Monitor (always-on)
- **Status:** ✅ DETECTED
- **Prev → Current:** RISK-OFF (긴축/불안·리스크 회피) → RISK-ON (완화 기대·리스크 선호)
- **File:** `insights/risk_alerts.txt` ✅ created
- **Email:** ❌ not sent (RESEND env missing (RESEND_API_KEY/RESEND_FROM/RESEND_TO))

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 18.68 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(↓) / DXY(↓) / VIX(↓)
- **판정:** **RISK-ON (완화 기대·리스크 선호)**
- **근거:** 금리↓ + 달러↓ + VIX↓ → 위험자산 선호/유동성 기대

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↓) / DXY(↓) / VIX(↓)
- **현실(FCI):** level=EASY (완화) / dir(→) | as of: 2026-02-23 (FRED last available)
- **유인(Real Rates):** level=NEUTRAL (중립) / dir(↑) | as of: 2026-02-23 (FRED last available)
- **판정:** **LIQUIDITY EXPANDING (Expectation-led) (기대 주도 확대)**
- **근거:** 기대는 완화 쪽, FCI/실질금리는 중립 이상 → 랠리 지속 가능성은 ‘열려있음’
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↓) / DXY(↓) / VIX(↓)
- **Policy Bias: EASING (완화) (STRONG, score=-2.5) | REAL_RATEΔ -0.030 / FCIΔ +0.000 / DXYΔ -0.031 / US10YΔ -0.002**
- **Expectations: dict received.**

- **판정:** **POLICY EASING (reinforced) (강화)**
- **근거:** 구조(REAL/FCI/DXY/US10Y)와 가격신호가 모두 EASING로 정렬 → 신호 신뢰도 상승
- **한줄요약 ~~** 구조=EASING (완화) & 가격=POLICY EASING (완화) 정렬 → 최종 POLICY EASING (reinforced) (강화)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-02-18 (FRED latest)
- **NET_LIQ level:** 5700667.1
- **TGA level:** 912727.0
- **RRP level:** 0.856
- **방향(전일 대비):** TGA(↓) / RRP(↓) / NET_LIQ(↓)
- **판정:** **LIQUIDITY DRAINING (유동성 흡수)**
- **근거:** Net Liquidity↓ → 시장 내 달러 여력 축소 가능
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-02-23 (FRED latest)
- **HY_OAS level:** 2.95% → **COOL (낮은 공포)**
- **방향(전일 대비):** HY_OAS(↑) / +3.15%
- **판정:** **CREDIT CALM**
- **근거:** HY 스프레드 낮음 → 크레딧 스트레스 제한 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↑) / LQD(↓)
- **HYG:** today 80.875 / prev 80.810 / pct 0.08%
- **LQD:** today 111.665 / prev 111.680 / pct -0.01%
- **판정:** **CREDIT RISK-ON (risk appetite improving)**
- **근거:** 하이일드 강세(HYG↑) + 우량채 약세/보합(LQD→/↓) → 위험선호 회복 가능

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Mild, -0.05%)** → 완화 기대 강화
- DXY **(Noise, -0.03%)** → 달러 약세/리스크 선호
- WTI **(Clear, -0.94%)** → 물가 부담 완화
- VIX **(Clear, -2.05%)** → 심리 개선/리스크온
- 원/달러(USDKRW) **(Mild, -0.07%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Noise, +0.08%)** → 크레딧 위험선호↑
- LQD (IG Bond ETF) **(Noise, -0.01%)** → 우량채 약세(리스크온 성향)

### 🧩 6) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함

- **금리 하락(US10Y↓)** → 달러 약세(DXY↓) / 할인율 부담 완화 / 위험자산 선호↑ 경향
- **변동성 하락(VIX↓)** → 심리 개선 / 위험자산 수요 회복 가능
- **유가 하락(WTI↓)** → 물가 부담 완화 / 긴축 압력 완화 가능

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 하락(VIX↓)** → 심리 안정: 리스크 수용 여력 개선
- **금리 하락(US10Y↓)** → 완화 기대/할인율 부담 완화 가능
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 하락(WTI↓)** → 물가 부담 완화 가능

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
- **강도:** US10Y(Mild) / DXY(Noise) / WTI(Clear) / VIX(Clear)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.052), DXY(97.851), VIX(18.68)

### 🏗️ 12) Structural Filter
- **질문:** 이 변화가 글로벌 구조(달러 패권/성장/에너지)에 어떤 힌트를 주는가?
- **핵심 신호:** US10Y(↓) / DXY(↓) / VIX(↓) / WTI(↓)
- **판정:** **NEUTRAL**
- **근거:** 패권/구조 신호가 뚜렷하지 않음

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: EASING (완화) (STRONG, score=-2.5) | REAL_RATEΔ -0.030 / FCIΔ +0.000 / DXYΔ -0.031 / US10YΔ -0.002
- **Sentiment (Fear&Greed):** 50.0 (NEUTRAL)
- **Credit Calm (HY OAS<4):** True
- **Liquidity (NET_LIQ):** dir=DOWN / level=LOW
- **Phase:** RISK-ON (완화 기대·리스크 선호)

- **🎯 Final Risk Action:** **HOLD**
- **Risk Budget (0~100):** **60**
- **Narrative:** 구조=EASING / 심리=NEUTRAL / 유동성=감소/낮음 / 크레딧=안정 → Phase=RISK-ON (완화 기대·리스크 선호)

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

- **Risk Budget:** 60
- **Phase Cap:** 85
- **VIX Level:** 18.68 (NORMAL)
- **VIX Change (%):** -2.05%
- **Final Multiplier:** 1.00x

- **📊 Recommended Exposure:** **60%**

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
- **Inflation Factor:** NEUTRAL
- **USD Factor:** NEUTRAL
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v1)
- **정의:** Macro + Style + Factor 종합 섹터 기울기 판단
- **추가 이유:** 방향뿐 아니라 어느 산업에 기울어야 하는지 판단

- **Overweight:** None
- **Underweight:** None