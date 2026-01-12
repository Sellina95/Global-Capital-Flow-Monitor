# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-01-12

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.187  (+0.00% vs 4.187)
- **달러 인덱스**: 98.882  (+0.15% vs 98.738)
- **WTI 유가**: 59.650  (+4.56% vs 57.050)
- **변동성 지수 (VIX)**: 15.120  (+4.20% vs 14.510)
- **원/달러 환율**: 1466.040  (+1.34% vs 1446.670)

---

## 🚨 Regime Change Monitor (always-on)
- **Status:** ✅ DETECTED
- **Prev → Current:** RISK-ON (부분 정렬) → RISK-OFF (부분 정렬)
- **File:** `insights/risk_alerts.txt` ✅ created
- **Email:** ❌ not sent (RESEND env missing (RESEND_API_KEY/RESEND_FROM/RESEND_TO))

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 15.12 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(→) / DXY(↑) / VIX(↑)
- **판정:** **RISK-OFF (부분 정렬)**
- **근거:** VIX↑ + (금리↑ 또는 달러↑) → 불안/긴축 우려 확대

### 💧 2) Liquidity Filter
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **핵심 신호:** US10Y(→, Noise) / DXY(↑, Mild) / VIX(↑, Strong)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 유동성 신호가 한 방향으로 정렬되지 않음

### 🏛️ 3) Policy Filter
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?
- **추가 이유:** 정책 흐름과 반대로 움직이는 자산은 지속 가능성이 낮기 때문
- **핵심 신호:** US10Y(→) / DXY(↑) / VIX(↑)
- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리와 달러 신호가 일관되지 않음 / 정책 불확실성 확대(VIX↑)

### 📌 4) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Noise, +0.00%)** → 보합(관망)
- DXY **(Mild, +0.15%)** → 달러 강세/신흥국 부담
- WTI **(Strong, +4.56%)** → 인플레 재자극 가능성
- VIX **(Strong, +4.20%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Strong, +1.34%)** → 원화 약세/수급 부담

### 🧩 5) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지, 즉 연쇄효과를 파악하기 위함

- **금리 변화 없음(US10Y→)** → 달러와 유가는 큰 변화 없음
- **변동성 상승(VIX↑)** → **리스크 회피, 달러 강세(DXY↑)** 및 **유가 하락(WTI↓)**
- **유가 상승(WTI↑)** → **리스크 선호, 금리 인상(US10Y↑)**

### 🧩 6) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 상승(VIX↑)** → **리스크 증가**: 변동성이 커지면 시장 불안정성 증가
- **달러 강세(DXY↑)** → **리스크 증가**: 달러 강세는 글로벌 자산에 부담을 줄 수 있음
- **유가 상승(WTI↑)** → **리스크 증가**: 유가 급등은 인플레이션 압력과 경제적 부담 증가

### 💸 7) Incentive Filter
- **질문:** 누가 이득을 보고 있는가?
- **핵심 신호:** US10Y(→) / DXY(↑) / WTI(↑)
- **판정:** **Beneficiaries identified**
- **이득을 보는 주체:**
  - Importers (cheaper foreign goods)
  - Oil Producers (higher oil prices)
- **손해를 보는 주체:**
  - Consumers (higher loan costs)
  - Exporters (due to stronger USD)
  - Consumers (due to higher energy costs)

### 🔍 8) Cause Filter
- **질문:** 무엇이 이 시장 움직임을 일으켰는가?
- **핵심 신호:** US10Y(→) / DXY(↑) / WTI(↑) / VIX(↑)
- **판정:** **달러 강세(DXY 상승) 유가 상승(WTI 상승) 변동성 증가(VIX 상승) **
- **이유:** 직접적인 원인 파악

### 🔄 9) Direction Filter
- **질문:** 시장이 어느 방향으로, 얼마나 움직였는가?
- **핵심 신호:** US10Y(Noise, →) / DXY(Mild, ↑) / WTI(Strong, ↑) / VIX(Strong, ↑)
- **판정:** **SIGNIFICANT MOVEMENT (의미 있는 움직임)**
- **근거:** 유가나 변동성의 변화가 큰 경우

### ⏳ 10) Timing Filter
- **질문:** 시장 변화가 단기, 중기, 장기 관점에서 어떤 영향을 미치는지?
- **핵심 신호:** US10Y(0.00% short-term, 4.19% medium-term, 4.19% long-term) / DXY(0.15% short-term, 98.74% medium-term, 98.88% long-term) / VIX(4.20% short-term, 14.51% medium-term, 15.12% long-term)
- **판정:** **HIGH VOLATILITY (고변동성)**
- **근거:** 변동성이 지속적으로 확대되고 있으며, 시장의 불확실성이 커지고 있음

### 🏗️ 11) Structural Filter
- **질문:** 이 변화가 글로벌 경제 구조나 패권 구조와 어떻게 연결되는지?
- **핵심 신호:** US10Y(→) / DXY(↑) / VIX(↑) / WTI(↑)
- **판정:** **NEUTRAL**
- **근거:** 세계 경제 구조와의 상관관계가 명확하지 않음