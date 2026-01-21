# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-01-21

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.295  (+0.00% vs 4.295)
- **달러 인덱스**: 98.605  (-0.03% vs 98.635)
- **WTI 유가**: 59.650  (+0.10% vs 59.590)
- **변동성 지수 (VIX)**: 19.330  (+0.47% vs 19.240)
- **원/달러 환율**: 1469.190  (+0.02% vs 1468.940)

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

- **VIX 레벨:** 19.33 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(→) / DXY(↓) / VIX(↑)
- **판정:** **TRANSITION / MIXED (전환·혼조)**
- **근거:** 금리/달러/변동성 축이 한 방향으로 정렬되지 않음

### 💧 2) Liquidity Filter
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **핵심 신호:** US10Y(→, Noise) / DXY(↓, Noise) / VIX(↑, Mild)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 유동성 신호가 한 방향으로 정렬되지 않음

### 🏛️ 3) Policy Filter
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?
- **추가 이유:** 정책 흐름과 반대로 움직이는 자산은 지속 가능성이 낮기 때문
- **핵심 신호:** US10Y(→) / DXY(↓) / VIX(↑)
- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리와 달러 신호가 일관되지 않음 / 정책 불확실성 확대(VIX↑)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-01-14 (FRED latest)
- **NET_LIQ level:** 5802521.8
- **TGA level:** 779175.0
- **RRP level:** 3.223
- **방향(전일 대비):** TGA(→) / RRP(→) / NET_LIQ(→)
- **판정:** **LIQUIDITY NEUTRAL**
- **근거:** 레벨/방향 혼조 또는 정보 제한
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-01-19 (FRED latest)
- **HY_OAS level:** 2.65% → **COOL (낮은 공포)**
- **방향(전일 대비):** HY_OAS(→) / N/A
- **판정:** **CREDIT CALM**
- **근거:** HY 스프레드 낮음 → 크레딧 스트레스 제한 / 방향성 제한 → 레벨 중심 해석
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(→) / LQD(→)
- **HYG:** today 80.880 / prev 80.880 / pct 0.00%
- **LQD:** today 109.900 / prev 109.900 / pct 0.00%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Noise, +0.00%)** → 보합(관망)
- DXY **(Noise, -0.03%)** → 달러 약세/리스크 선호
- WTI **(Noise, +0.10%)** → 인플레 재자극 가능성
- VIX **(Mild, +0.47%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Noise, +0.02%)** → 원화 약세/수급 부담
- HYG (High Yield ETF) **(Noise, +0.00%)** → 보합(크레딧 변화 제한)
- LQD (IG Bond ETF) **(Noise, +0.00%)** → 보합(방향성 제한)

### 🧩 6) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함

- **금리 보합(US10Y→)** → 할인율 변수 제한
- **변동성 상승(VIX↑)** → 위험회피 강화 / 달러 선호↑ / 원자재·주식 부담 가능
- **유가 상승(WTI↑)** → 인플레 재자극 가능성 / 금리 상방 압력

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 상승(VIX↑)** → 변동성 확대: 포지션 축소/헤지 수요 증가 가능
- **금리 보합(US10Y→)** → 금리 변수 제한
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 💸 8) Incentive Filter
- **질문:** 누가 이득을 보고 있는가?
- **핵심 신호:** US10Y(→) / DXY(↓) / WTI(↑)
- **이득을 보는 주체:**
  - EM assets / risk trades
  - Energy producers
- **손해를 보는 주체:**
  - USD strength trades
  - Energy consumers

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** US10Y(→) / DXY(↓) / WTI(↑) / VIX(↑)
- **판정:** **달러 약세(DXY↓) + 유가 상승(WTI↑) + 변동성 확대(VIX↑)**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Noise) / DXY(Noise) / WTI(Noise) / VIX(Mild)
- **판정:** **MOSTLY NOISE (대부분 노이즈)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.295), DXY(98.605), VIX(19.33)

### 🏗️ 12) Structural Filter
- **질문:** 이 변화가 글로벌 구조(달러 패권/성장/에너지)에 어떤 힌트를 주는가?
- **핵심 신호:** US10Y(→) / DXY(↓) / VIX(↑) / WTI(↑)
- **판정:** **NEUTRAL**
- **근거:** 패권/구조 신호가 뚜렷하지 않음