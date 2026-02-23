# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-02-24

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.029  (-1.39% vs 4.086)
- **달러 인덱스**: 97.725  (-0.07% vs 97.789)
- **WTI 유가**: 66.290  (-0.29% vs 66.480)
- **변동성 지수 (VIX)**: 21.010  (+10.06% vs 19.090)
- **원/달러 환율**: 1443.030  (-0.11% vs 1444.670)

---

## 🚨 Regime Change Monitor (always-on)
- **Status:** ✅ DETECTED
- **Prev → Current:** RISK-OFF (긴축/불안·리스크 회피) → TRANSITION / MIXED (전환·혼조)
- **File:** `insights/risk_alerts.txt` ✅ created
- **Email:** ❌ not sent (RESEND env missing (RESEND_API_KEY/RESEND_FROM/RESEND_TO))

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 21.01 → **High (Risk-off bias)**
- **핵심 조합(전일 대비 방향):** US10Y(↓) / DXY(↓) / VIX(↑)
- **판정:** **TRANSITION / MIXED (전환·혼조)**
- **근거:** 금리/달러/변동성 축이 한 방향으로 정렬되지 않음

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↓) / DXY(↓) / VIX(↑)
- **현실(FCI):** level=EASY (완화) / dir(→) | as of: 2026-02-20 (FRED last available)
- **유인(Real Rates):** level=NEUTRAL (중립) / dir(↓) | as of: 2026-02-20 (FRED last available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↓) / DXY(↓) / VIX(↑)
- **Policy Bias: MIXED (혼조) (WEAK, score=-0.5) | REAL_RATEΔ +0.010 / FCIΔ +0.000 / DXYΔ -0.064 / US10YΔ -0.057**
- **Expectations: dict received.**

- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리/달러/변동성 신호가 완전히 정렬되지 않음
- **한줄요약 ~~** 구조=MIXED (혼조)(WEAK)는 참고, 가격=POLICY MIXED (정책 신호 혼조) 중심 → 최종 POLICY MIXED (정책 신호 혼조)

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
- **Spread as of:** 2026-02-20 (FRED latest)
- **HY_OAS level:** 2.86% → **COOL (낮은 공포)**
- **방향(전일 대비):** HY_OAS(↓) / -0.69%
- **판정:** **CREDIT CALM**
- **근거:** HY 스프레드 낮음 → 크레딧 스트레스 제한 / 스프레드가 좁혀지는 중 → 공포 온도 완화
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(↑)
- **HYG:** today 80.870 / prev 81.000 / pct -0.16%
- **LQD:** today 111.710 / prev 111.590 / pct 0.11%
- **판정:** **CREDIT STRESS ↑ (Risk-off warning)**
- **근거:** 하이일드 약세(HYG↓) + 우량채 방어(LQD→/↑) → 위험회피로 크레딧 프리미엄 재평가 가능

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, -1.39%)** → 완화 기대 강화
- DXY **(Mild, -0.07%)** → 달러 약세/리스크 선호
- WTI **(Mild, -0.29%)** → 물가 부담 완화
- VIX **(Strong, +10.06%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Mild, -0.11%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Mild, -0.16%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Mild, +0.11%)** → 우량채 강세(리스크오프 성향)

### 🧩 6) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함

- **금리 하락(US10Y↓)** → 달러 약세(DXY↓) / 할인율 부담 완화 / 위험자산 선호↑ 경향
- **변동성 상승(VIX↑)** → 위험회피 강화 / 달러 선호↑ / 원자재·주식 부담 가능
- **유가 하락(WTI↓)** → 물가 부담 완화 / 긴축 압력 완화 가능

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 상승(VIX↑)** → 변동성 확대: 포지션 축소/헤지 수요 증가 가능
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
- **핵심 신호:** US10Y(↓) / DXY(↓) / WTI(↓) / VIX(↑)
- **판정:** **금리 하락(US10Y↓) + 달러 약세(DXY↓) + 유가 하락(WTI↓) + 변동성 확대(VIX↑)**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Mild) / WTI(Mild) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.029), DXY(97.725), VIX(21.01)

### 🏗️ 12) Structural Filter
- **질문:** 이 변화가 글로벌 구조(달러 패권/성장/에너지)에 어떤 힌트를 주는가?
- **핵심 신호:** US10Y(↓) / DXY(↓) / VIX(↑) / WTI(↓)
- **판정:** **WEAK DEMAND + RISK-OFF (수요 둔화 + 위험회피)**
- **근거:** 유가↓ + VIX↑는 성장 둔화 우려와 위험회피 심리 강화로 연결될 수 있음

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: MIXED (혼조) (WEAK, score=-0.5) | REAL_RATEΔ +0.010 / FCIΔ +0.000 / DXYΔ -0.064 / US10YΔ -0.057
- **Sentiment (Fear&Greed):** 35.0 (NEUTRAL)
- **Credit Calm (HY OAS<4):** True
- **Liquidity Supportive (NET_LIQ pct>0):** False
- **Phase:** TRANSITION / MIXED (전환·혼조)

- **🎯 Final Risk Action:** **HOLD**
- **Risk Budget (0~100):** **55**
- **Narrative:** 구조=MIXED / 심리=NEUTRAL / 유동성=비우호 / 크레딧=안정 → Phase=TRANSITION / MIXED (전환·혼조)

### ⚠ 14) Divergence Monitor
- **정의:** 구조(정책)와 가격(시장 국면)의 충돌 여부 감지
- **추가 이유:** 구조-가격 충돌은 국면 전환의 초기 신호가 될 수 있음

- **Structure:** MIXED
- **Price Regime:** TRANSITION
- **Status:** **TRANSITION ZONE**
- **해석:** 시장 방향 탐색 구간

### 🎯 15) Volatility-Controlled Exposure (v2)
- **정의:** Risk Budget을 실제 익스포저로 변환 (Pro Version)
- **추가 이유:** 변동성·스트레스·국면을 모두 반영한 실전형 리스크 제어

- **Risk Budget:** 55
- **Phase Cap:** 70
- **VIX Level:** 21.01 (HIGH)
- **VIX Change (%):** +10.06%
- **Final Multiplier:** 0.68x

- **📊 Recommended Exposure:** **50%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **NEUTRAL**
- **Duration Tilt:** **LONG DURATION FAVORED**
- **Cyclical vs Defensive:** **NEUTRAL**

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