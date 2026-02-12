# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-02-12

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.172  (+0.00% vs 4.172)
- **달러 인덱스**: 96.961  (+0.06% vs 96.907)
- **WTI 유가**: 64.440  (-0.69% vs 64.890)
- **변동성 지수 (VIX)**: 17.400  (-1.42% vs 17.650)
- **원/달러 환율**: 1439.450  (-0.42% vs 1445.480)

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

- **VIX 레벨:** 17.40 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(→) / DXY(↑) / VIX(↓)
- **판정:** **TRANSITION / MIXED (전환·혼조)**
- **근거:** 금리/달러/변동성 축이 한 방향으로 정렬되지 않음

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(→) / DXY(↑) / VIX(↓)
- **현실(FCI):** level=EASY (완화) / dir(→) | as of: 2026-02-06 (FRED last available)
- **유인(Real Rates):** level=NEUTRAL (중립) / dir(→) | as of: 2026-02-06 (FRED last available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?
- **추가 이유:** 정책 흐름과 반대로 움직이는 자산은 지속 가능성이 낮기 때문
- **핵심 신호:** US10Y(→) / DXY(↑) / VIX(↓)
- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리와 달러 신호가 일관되지 않음 / 정책 신호 신뢰도 개선(VIX↓)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-02-04 (FRED latest)
- **NET_LIQ level:** 5697133.6
- **TGA level:** 908773.0
- **RRP level:** 2.414
- **방향(전일 대비):** TGA(↓) / RRP(↑) / NET_LIQ(↑)
- **판정:** **LIQUIDITY SUPPORTIVE (완만한 유동성 우호)**
- **근거:** Net Liquidity↑ → 시장 내 달러 여력 개선
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-02-10 (FRED latest)
- **HY_OAS level:** 2.86% → **COOL (낮은 공포)**
- **방향(전일 대비):** HY_OAS(↑) / +0.70%
- **판정:** **CREDIT CALM**
- **근거:** HY 스프레드 낮음 → 크레딧 스트레스 제한 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(→) / LQD(→)
- **HYG:** today 80.830 / prev 80.830 / pct 0.00%
- **LQD:** today 110.700 / prev 110.700 / pct 0.00%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Noise, +0.00%)** → 보합(관망)
- DXY **(Mild, +0.06%)** → 달러 강세/신흥국 부담
- WTI **(Clear, -0.69%)** → 물가 부담 완화
- VIX **(Clear, -1.42%)** → 심리 개선/리스크온
- 원/달러(USDKRW) **(Clear, -0.42%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Noise, +0.00%)** → 보합(크레딧 변화 제한)
- LQD (IG Bond ETF) **(Noise, +0.00%)** → 보합(방향성 제한)

### 🧩 6) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함

- **금리 보합(US10Y→)** → 할인율 변수 제한
- **변동성 하락(VIX↓)** → 심리 개선 / 위험자산 수요 회복 가능
- **유가 하락(WTI↓)** → 물가 부담 완화 / 긴축 압력 완화 가능

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 하락(VIX↓)** → 심리 안정: 리스크 수용 여력 개선
- **금리 보합(US10Y→)** → 금리 변수 제한
- **달러 강세(DXY↑)** → 신흥국·원자재·원화 등 위험자산에 부담
- **유가 하락(WTI↓)** → 물가 부담 완화 가능

### 💸 8) Incentive Filter
- **질문:** 누가 이득을 보고 있는가?
- **핵심 신호:** US10Y(→) / DXY(↑) / WTI(↓)
- **이득을 보는 주체:**
  - USD holders / US importers
  - Energy consumers
- **손해를 보는 주체:**
  - EM assets / USD debtors
  - Energy producers

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** US10Y(→) / DXY(↑) / WTI(↓) / VIX(↓)
- **판정:** **달러 강세(DXY↑) + 유가 하락(WTI↓) + 변동성 완화(VIX↓)**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Noise) / DXY(Mild) / WTI(Clear) / VIX(Clear)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.172), DXY(96.961), VIX(17.40)

### 🏗️ 12) Structural Filter
- **질문:** 이 변화가 글로벌 구조(달러 패권/성장/에너지)에 어떤 힌트를 주는가?
- **핵심 신호:** US10Y(→) / DXY(↑) / VIX(↓) / WTI(↓)
- **판정:** **NEUTRAL**
- **근거:** 패권/구조 신호가 뚜렷하지 않음