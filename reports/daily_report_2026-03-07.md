# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-03-07

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.133  (-0.31% vs 4.146)
- **달러 인덱스**: 98.855  (-0.21% vs 99.065)
- **WTI 유가**: 91.270  (+15.72% vs 78.870)
- **변동성 지수 (VIX)**: 29.490  (+24.17% vs 23.750)
- **원/달러 환율**: 1484.590  (+0.26% vs 1480.680)

---

## 🚨 Regime Change Monitor (always-on)
- **Status:** ✅ DETECTED
- **Prev → Current:** RISK-OFF (긴축/불안·리스크 회피) → TRANSITION / MIXED (전환·혼조)
- **File:** `insights/risk_alerts.txt` ✅ created
- **Email:** ❌ not sent (RESEND env missing (RESEND_API_KEY/RESEND_FROM/RESEND_TO))

---

## 🧾 Executive Summary (3 Lines)
- 현재 시장은 방향성이 제한된 혼합 국면이며, 구조 신호는 혼조.
- 유동성 여건이 개선되며 리스크 자산에 우호적이다.
- 전략적으로는 공격적 확대보다 50% 내외의 선별적 노출 유지가 적절하다.

## 🧭 So What? (Decision Layer)
- **Risk Stance:** **HOLD** *(target exposure: 50%)*
- **Context:** phase=TRANSITION / MIXED (전환·혼조) / liquidity=UP-HIGH / credit_calm=True / geo=ELEVATED
- **Geo Overlay:** GeoEW=ELEVATED overlay applied (-10% budget adj) → budget 60% → 50%

## 🗺️ Scenario Framework (Base / Bull / Bear)

### 🔹 Base Case
- 조건: 유동성 혼조 + 크레딧 안정 유지 / 변동성 급등 없이 박스권 장세 지속
- 전략: 노출 50% 유지, 퀄리티 중심 선별적 접근

### 🔼 Bull Case
- 조건: NET_LIQ 회복 (dir=UP & level=MID 이상) / 크레딧 스프레드 추가 축소
- 전략: 노출 단계적 확대, 성장/리스크 자산 베타 확장

### 🔻 Bear Case
- 조건: HY OAS > 4% 상회 또는 급등 / VIX 22 이상 또는 급등 전환
- 전략: 노출 35% 이하 축소, 방어/현금 비중 확대

## 🔗 Transmission Map (Macro → Industry → Company)
- **1-Line Conclusion:** 퀄리티 중심 차별화 + 베타 확장 가능 → **High operating leverage / cyclicals / growth optionality** 선호

- **Policy → Valuation:** 할인율 방향성 불명확 → 퀄리티 중심 차별화
- **Liquidity → Risk Budget:** 유동성 공급(리스크 허용↑) → 베타 확장 가능
- **Credit → Balance Sheet:** 크레딧 안정 → 시스템 리스크 제한

- **Sector/Company Shortcut:** Cyclicals/Tech(상황에 따라) + Small/Mid beta

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 29.49 → **High (Risk-off bias)**
- **핵심 조합(전일 대비 방향):** US10Y(↓) / DXY(↓) / VIX(↑)
- **판정:** **TRANSITION / MIXED (전환·혼조)**
- **근거:** 금리/달러/변동성 축이 한 방향으로 정렬되지 않음

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↓) / DXY(↓) / VIX(↑)
- **현실(FCI):** level=EASY (완화) / dir(→) | as of: 2026-03-05 (FRED last available)
- **유인(Real Rates):** level=NEUTRAL (중립) / dir(↓) | as of: 2026-03-05 (FRED last available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↓) / DXY(↓) / VIX(↑)
- **Policy Bias: MIXED (혼조) (WEAK, score=-0.5) | REAL_RATEΔ +0.020 / FCIΔ +0.000 / DXYΔ -0.210 / US10YΔ -0.013**
- **Expectations: dict received.**

- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리/달러/변동성 신호가 완전히 정렬되지 않음
- **한줄요약 ~~** 구조=MIXED (혼조)(WEAK)는 참고, 가격=POLICY MIXED (정책 신호 혼조) 중심 → 최종 POLICY MIXED (정책 신호 혼조)

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
- **Spread as of:** 2026-03-05 (FRED latest)
- **HY_OAS level:** 3.00% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↑) / +1.01%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(↓)
- **HYG:** today 79.690 / prev 80.080 / pct -0.49%
- **LQD:** today 110.160 / prev 110.530 / pct -0.33%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, -0.31%)** → 완화 기대 강화
- DXY **(Clear, -0.21%)** → 달러 약세/리스크 선호
- WTI **(Strong, +15.72%)** → 인플레 재자극 가능성
- VIX **(Strong, +24.17%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Clear, +0.26%)** → 원화 약세/수급 부담
- HYG (High Yield ETF) **(Clear, -0.49%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Mild, -0.33%)** → 우량채 약세(리스크온 성향)

### 🧩 6) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함

- **금리 하락(US10Y↓)** → 달러 약세(DXY↓) / 할인율 부담 완화 / 위험자산 선호↑ 경향
- **변동성 상승(VIX↑)** → 위험회피 강화 / 달러 선호↑ / 원자재·주식 부담 가능
- **유가 상승(WTI↑)** → 인플레 재자극 가능성 / 금리 상방 압력

### ⚠ 6.5) Correlation Break Monitor

Correlation Break Detected:
- US10Y ↓ but Technology ↓ (QQQ/XLK)

So What?
- 금리 완화에도 기술 약세 → 금리보다 실적/규제/리스크 요인이 우위 (퀄리티 중심)
- 결론: **공식이 깨진 구간** → 방향 베팅보다 **사이징 보수적 + 퀄리티/리더 중심**

### ⚠ 6.6) Sector Correlation Break Monitor
- DEBUG: pct XLK=-2.061634712974086, XLF=-1.2883073459096475, XLE=0.1593487133805438, XLRE=-1.038303556426229
Correlation Break Detected:
- US10Y ↓ but XLK ↓ (Tech)

So What?
- 금리 하락에도 기술 약세 → 금리보다 실적/성장 우려가 더 큼 (퀄리티만)
- 결론: **섹터 ‘공식’이 깨진 구간** → 방향 베팅보다 **사이징 축소 + 리더 중심**

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 상승(VIX↑)** → 변동성 확대: 포지션 축소/헤지 수요 증가 가능
- **금리 하락(US10Y↓)** → 완화 기대/할인율 부담 완화 가능
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **+1.05**  *(Level: ELEVATED)*
- **Top Drivers:**
  - VIX: z_used=+2.86 (w=0.18) → contrib=+0.52
  - WTI: z_used=+5.14 (w=0.10) → contrib=+0.51
  - EMB: z_used=+2.43 (w=0.12) → contrib=+0.29
  - BDRY: z_used=-3.32 (w=0.05) → contrib=-0.17
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, CN10Y_SPREAD, IL10Y_SPREAD, TR10Y_SPREAD

**So What?**
- 조기경보 ‘상승’ 구간: **사이징 보수적**, 이벤트 리스크(중동/중국/EM) 헤지 후보 점검.

### 💸 8) Incentive Filter
- **질문:** 누가 이득을 보고 있는가?
- **핵심 신호:** US10Y(↓) / DXY(↓) / WTI(↑)
- **이득을 보는 주체:**
  - Long-duration growth (discount-rate relief)
  - EM assets / risk trades
  - Energy producers
- **손해를 보는 주체:**
  - USD strength trades
  - Energy consumers

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** US10Y(↓) / DXY(↓) / WTI(↑) / VIX(↑)
- **판정:** **금리 하락(US10Y↓) + 달러 약세(DXY↓) + 유가 상승(WTI↑) + 변동성 확대(VIX↑)**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Clear) / WTI(Strong) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.133), DXY(98.855), VIX(29.49)

### 🏗️ 12) Structural Filter
- **질문:** 이 변화가 글로벌 구조(달러 패권/성장/에너지)에 어떤 힌트를 주는가?
- **핵심 신호:** US10Y(↓) / DXY(↓) / VIX(↑) / WTI(↑)
- **판정:** **NEUTRAL**
- **근거:** 패권/구조 신호가 뚜렷하지 않음

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: MIXED (혼조) (WEAK, score=-0.5) | REAL_RATEΔ +0.020 / FCIΔ +0.000 / DXYΔ -0.210 / US10YΔ -0.013
- **Sentiment (Fear&Greed):** 13.989604935808488 (FEAR)
- **Credit Calm (HY OAS<4):** True
- **Liquidity (NET_LIQ):** dir=UP / level=HIGH
- **Phase:** TRANSITION / MIXED (전환·혼조)

- **🎯 Final Risk Action:** **HOLD**
- **Risk Budget (0~100):** **60**
- **Narrative:** 구조=MIXED / 심리=FEAR / 유동성=증가/높음 / 크레딧=안정 → Phase=TRANSITION / MIXED (전환·혼조)

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

- **Risk Budget:** 60
- **Phase Cap:** 70
- **VIX Level:** 29.49 (HIGH)
- **VIX Change (%):** +24.17%
- **Final Multiplier:** 0.68x

- **📊 Recommended Exposure:** **54%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **NEUTRAL**
- **Duration Tilt:** **LONG DURATION FAVORED**
- **Cyclical vs Defensive:** **CYCLICAL (ENERGY) BIAS**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** LONG DURATION FAVORED
- **Inflation Factor:** NEUTRAL
- **USD Factor:** NEUTRAL
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v2)
- **정의:** Macro + Style/Factor/FINAL_STATE 종합 섹터 기울기 판단 (rule-based scoring)
- **추가 이유:** 리포트의 최종 output(포지셔닝)이 비어있지 않도록, 최소 OW/UW를 항상 생성

- **Context:** phase=TRANSITION / MIXED (전환·혼조) / liquidity=UP-HIGH / structure=MIXED / credit_calm=True
- **Overweight:** **Financials, Industrials, Technology**
- **Underweight:** **Utilities, Consumer Staples**

- **Rationale (top drivers):**
  - OW Financials: +1: 유동성 공급 → 리스크 선호 회복 구간 우호
  - OW Industrials: +2: 유동성 공급 → 경기순환(투자/생산) 우호
  - OW Technology: +2: 유동성 공급 → 베타 확장 환경
  - UW Utilities: -1: 유동성 공급 → 방어 섹터 상대매력 감소
  - UW Consumer Staples: -1: 유동성 공급 → 방어 섹터 상대매력 감소

### 🧬 19) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Preferred Company Traits:**

**Risk Control / Avoid:**
