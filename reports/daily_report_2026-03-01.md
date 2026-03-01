# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-03-01

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 3.962  (+0.00% vs 3.962)
- **달러 인덱스**: 97.610  (+0.00% vs 97.610)
- **WTI 유가**: 67.020  (+0.00% vs 67.020)
- **변동성 지수 (VIX)**: 19.860  (+0.00% vs 19.860)
- **원/달러 환율**: 1439.230  (+0.00% vs 1439.230)

---

## 🚨 Regime Change Monitor (always-on)
- **Status:** ✅ DETECTED
- **Prev → Current:** RISK-OFF (긴축/불안·리스크 회피) → WAITING / RANGE (대기·박스권)
- **File:** `insights/risk_alerts.txt` ✅ created
- **Email:** ❌ not sent (RESEND env missing (RESEND_API_KEY/RESEND_FROM/RESEND_TO))

---

## 🧾 Executive Summary (3 Lines)
- 현재 시장은 방향성이 제한된 혼합 국면이며, 구조는 완화 기조.
- 유동성 여건이 개선되며 리스크 자산에 우호적이다.
- 전략적으로는 공격적 확대보다 60% 내외의 선별적 노출 유지가 적절하다.

## 🧭 So What? (Decision Layer)
- **Risk Stance:** **HOLD** *(target exposure: 60%)*
- **Context:** phase=WAITING / RANGE (대기·박스권) / liquidity=UP-MID / credit_calm=True
- **Do:** 노출은 유지하되, 베타 확대보다 ‘선별적 포지셔닝(퀄리티)’ 유지
- **Don't:** 무분별한 테마 추격; 리스크 관리 없는 집중 포지션
- **Triggers:** NET_LIQ 추가 하락/LOW 고착 시 노출 축소 준비

## 🗺️ Scenario Framework (Base / Bull / Bear)

### 🔹 Base Case
- 조건: 유동성 혼조 + 크레딧 안정 유지 / 변동성 급등 없이 박스권 장세 지속
- 전략: 노출 60% 유지, 퀄리티 중심 선별적 접근

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

- **VIX 레벨:** 19.86 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(→) / DXY(→) / VIX(→)
- **판정:** **WAITING / RANGE (대기·박스권)**
- **근거:** 핵심 축(금리/달러/변동성) 모두 보합 → 방향성 부재

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(→) / DXY(→) / VIX(→)
- **현실(FCI):** level=EASY (완화) / dir(→) | as of: 2026-02-26 (FRED last available)
- **유인(Real Rates):** level=NEUTRAL (중립) / dir(↑) | as of: 2026-02-26 (FRED last available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(→) / DXY(→) / VIX(→)
- **Policy Bias: EASING (완화) (MODERATE, score=-1.0) | REAL_RATEΔ -0.030 / FCIΔ +0.000 / DXYΔ +0.000 / US10YΔ +0.000**
- **Expectations: dict received.**

- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리/달러/변동성 신호가 완전히 정렬되지 않음
- **한줄요약 ~~** 구조=EASING (완화)(MODERATE)는 참고, 가격=POLICY MIXED (정책 신호 혼조) 중심 → 최종 POLICY MIXED (정책 신호 혼조)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-02-25 (FRED latest)
- **NET_LIQ level:** 5726183.8
- **TGA level:** 887612.0
- **RRP level:** 1.159
- **방향(전일 대비):** TGA(↓) / RRP(↑) / NET_LIQ(↑)
- **판정:** **LIQUIDITY SUPPORTIVE (완만한 유동성 우호)**
- **근거:** Net Liquidity↑ → 시장 내 달러 여력 개선
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-02-26 (FRED latest)
- **HY_OAS level:** 2.98% → **COOL (낮은 공포)**
- **방향(전일 대비):** HY_OAS(↑) / +1.36%
- **판정:** **CREDIT CALM**
- **근거:** HY 스프레드 낮음 → 크레딧 스트레스 제한 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(→) / LQD(→)
- **HYG:** today 80.720 / prev 80.720 / pct 0.00%
- **LQD:** today 111.680 / prev 111.680 / pct 0.00%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Noise, +0.00%)** → 보합(관망)
- DXY **(Noise, +0.00%)** → 달러 보합(방향성 약함)
- WTI **(Noise, +0.00%)** → 유가 보합(물가 변수 제한)
- VIX **(Noise, +0.00%)** → 변동성 보합(심리 변화 제한)
- 원/달러(USDKRW) **(Noise, +0.00%)** → 환율 보합(수급 압력 제한)
- HYG (High Yield ETF) **(Noise, +0.00%)** → 보합(크레딧 변화 제한)
- LQD (IG Bond ETF) **(Noise, +0.00%)** → 보합(방향성 제한)

### 🧩 6) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함

- **금리 보합(US10Y→)** → 할인율 변수 제한
- **변동성 보합(VIX→)** → 심리 변화 제한
- **유가 보합(WTI→)** → 물가 변수 제한

### ⚠ 6.5) Correlation Break Monitor
- DEBUG: US10Y=0.0, TECH=None, SPY=None

- **Note:** TECH_PROXY not available, SPY not available → using available proxies (credit/USD/FX).

No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
No significant sector-level correlation break detected.

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 보합(VIX→)** → 심리 변화 제한
- **금리 보합(US10Y→)** → 금리 변수 제한
- **달러 보합(DXY→)** → 달러 변수 제한
- **유가 보합(WTI→)** → 물가 변수 제한

### 💸 8) Incentive Filter
- **질문:** 누가 이득을 보고 있는가?
- **핵심 신호:** US10Y(→) / DXY(→) / WTI(→)
- **이득을 보는 주체:**
  - None
- **손해를 보는 주체:**
  - None

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** US10Y(→) / DXY(→) / WTI(→) / VIX(→)
- **판정:** **원인 신호 뚜렷하지 않음**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Noise) / DXY(Noise) / WTI(Noise) / VIX(Noise)
- **판정:** **MOSTLY NOISE (대부분 노이즈)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(3.962), DXY(97.610), VIX(19.86)

### 🏗️ 12) Structural Filter
- **질문:** 이 변화가 글로벌 구조(달러 패권/성장/에너지)에 어떤 힌트를 주는가?
- **핵심 신호:** US10Y(→) / DXY(→) / VIX(→) / WTI(→)
- **판정:** **NEUTRAL**
- **근거:** 패권/구조 신호가 뚜렷하지 않음

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: EASING (완화) (MODERATE, score=-1.0) | REAL_RATEΔ -0.030 / FCIΔ +0.000 / DXYΔ +0.000 / US10YΔ +0.000
- **Sentiment (Fear&Greed):** 50.0 (NEUTRAL)
- **Credit Calm (HY OAS<4):** True
- **Liquidity (NET_LIQ):** dir=UP / level=MID
- **Phase:** WAITING / RANGE (대기·박스권)

- **🎯 Final Risk Action:** **HOLD**
- **Risk Budget (0~100):** **60**
- **Narrative:** 구조=EASING / 심리=NEUTRAL / 유동성=증가/중간 / 크레딧=안정 → Phase=WAITING / RANGE (대기·박스권)

### ⚠ 14) Divergence Monitor
- **정의:** 구조(정책)와 가격(시장 국면)의 충돌 여부 감지
- **추가 이유:** 구조-가격 충돌은 국면 전환의 초기 신호가 될 수 있음

- **Structure:** EASING
- **Price Regime:** WAITING
- **Status:** **TRANSITION ZONE**
- **해석:** 시장 방향 탐색 구간

### 🎯 15) Volatility-Controlled Exposure (v2)
- **정의:** Risk Budget을 실제 익스포저로 변환 (Pro Version)
- **추가 이유:** 변동성·스트레스·국면을 모두 반영한 실전형 리스크 제어

- **Risk Budget:** 60
- **Phase Cap:** 60
- **VIX Level:** 19.86 (NORMAL)
- **VIX Change (%):** +0.00%
- **Final Multiplier:** 1.00x

- **📊 Recommended Exposure:** **60%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **GROWTH TILT**
- **Duration Tilt:** **NEUTRAL**
- **Cyclical vs Defensive:** **DEFENSIVE / QUALITY BIAS**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** NEUTRAL
- **Inflation Factor:** NEUTRAL
- **USD Factor:** NEUTRAL
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v2)
- **정의:** Macro + Style/Factor/FINAL_STATE 종합 섹터 기울기 판단 (rule-based scoring)
- **추가 이유:** 리포트의 최종 output(포지셔닝)이 비어있지 않도록, 최소 OW/UW를 항상 생성

- **Context:** phase=WAITING / RANGE (대기·박스권) / liquidity=UP-MID / structure=EASING / credit_calm=True
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
