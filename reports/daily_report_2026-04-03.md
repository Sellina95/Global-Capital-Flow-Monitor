# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-04-03
**Data as of:** 2026-04-02

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.351  (+0.74% vs 4.319)
- **달러 인덱스**: 100.119  (+0.47% vs 99.650)
- **WTI 유가**: 112.600  (+12.47% vs 100.120)
- **변동성 지수 (VIX)**: 27.490  (+12.02% vs 24.540)
- **원/달러 환율**: 1517.340  (+0.93% vs 1503.330)

---

## 🚨 Regime Change Monitor (always-on)
- **Status:** ❎ NOT DETECTED
- **Current Regime:** RISK-OFF (긴축/불안·리스크 회피)
- **File:** not created
- **Email:** not sent

---

Some commentary here
## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 27.49 → **High (Risk-off bias)**
- **핵심 조합(전일 대비 방향):** US10Y(↑) / DXY(↑) / VIX(↑)
- **판정:** **RISK-OFF (긴축/불안·리스크 회피)**
- **근거:** 금리↑ + 달러↑ + VIX↑ → 안전자산/현금 선호 강화

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↑) / DXY(↑) / VIX(↑)
- **현실(FCI):** level=EASY (완화) / dir(↑) | as of: 2026-03-27 (FRED last available)
- **유인(Real Rates):** level=RESTRICTIVE (유인↓) / dir(↑) | as of: 2026-03-31 (FRED last available)
- **판정:** **LIQUIDITY TIGHTENING (유동성 축소)**
- **근거:** 금리↑+달러↑ + (FCI 압박 또는 실질금리 유인↓) → 리스크자산에 불리
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↑) / DXY(↑) / VIX(↑)
- **Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ -0.040 / FCIΔ +0.020 / DXYΔ +0.469 / US10YΔ +0.032**
- **Expectations: dict received.**

- **판정:** **POLICY TIGHTENING (긴축)**
- **근거:** 금리↑ + 달러↑ → 긴축 압력
- **한줄요약 ~~** 구조=TIGHTENING (긴축)(MODERATE)는 참고, 가격=POLICY TIGHTENING (긴축) 중심 → 최종 POLICY TIGHTENING (긴축)

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
- **방향(전일 대비):** HYG(→) / LQD(→)
- **HYG:** today 79.370 / prev 79.370 / pct 0.00%
- **LQD:** today 108.660 / prev 108.660 / pct 0.00%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, +0.74%)** → 완화 기대 약화/금리 부담
- DXY **(Strong, +0.47%)** → 달러 강세/신흥국 부담
- WTI **(Strong, +12.47%)** → 인플레 재자극 가능성
- VIX **(Strong, +12.02%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Strong, +0.93%)** → 원화 약세/수급 부담
- HYG (High Yield ETF) **(Noise, +0.00%)** → 보합(크레딧 변화 제한)
- LQD (IG Bond ETF) **(Noise, +0.00%)** → 보합(방향성 제한)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 상승(US10Y↑)** → 실질 금리 압박 → 달러 강세(DXY↑) 유도: **신흥국 자본 유출 및 고밸류 성장주 할인율 부담 증가**
- **변동성 상승(VIX↑)** → 위험회피(Risk-Off) 강화: **안전 자산(Cash/USD) 선호도 급증 및 하이일드 스프레드 확대 압력**
- **유가 상승(WTI↑)** → 기대 인플레이션 자극: **제조/운송업 비용 부담 가중 및 중앙은행의 긴축 유지 명분 강화**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### ⚠ 6.5) Correlation Break Monitor

No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
- DEBUG: pct XLK=0.0, XLF=0.0, XLE=0.0, XLRE=0.0
No significant sector-level correlation break detected.

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 상승(VIX↑)** → 변동성 확대: 포지션 축소/헤지 수요 증가 가능
- **금리 상승(US10Y↑)** → 할인율 부담/유동성 압박 가능
- **달러 강세(DXY↑)** → 신흥국·원자재·원화 등 위험자산에 부담
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **+0.12**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** -0.07
- **Geo Momentum:** +0.19 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Ukraine_2022
- **Cosine Similarity Score:** 0.476
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Ukraine_2022: 0.476
  - Red_Sea: 0.436
  - Israel_2023: 0.361
- **Top Drivers:**
  - WTI: z_used=+2.26 (z1d=+2.68, z5d=+1.62, raw_w=0.10, norm_w=0.08) → contrib=+0.17
  - VIX: z_used=+0.49 (z1d=+1.15, z5d=-0.49, raw_w=0.18, norm_w=0.14) → contrib=+0.07
  - KR10Y_SPREAD: z_used=-1.00 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.06
  - DE10Y_SPREAD: z_used=+1.00 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=+0.05
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Ukraine_2022** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (GLD)
- **Extreme Country Risk:** GLD

### 💸 8) Incentive Filter
- **질문:** 누가 이득을 보고 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↑) / WTI(↑)
- **이득을 보는 주체:**
  - Banks/Financials (higher rates)
  - USD holders / US importers
  - Energy producers
- **손해를 보는 주체:**
  - Long-duration growth (discount-rate pressure)
  - EM assets / USD debtors
  - Energy consumers

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** US10Y(↑) / DXY(↑) / WTI(↑) / VIX(↑)
- **판정:** **금리 상승(US10Y↑) + 달러 강세(DXY↑) + 유가 상승(WTI↑) + 변동성 확대(VIX↑)**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Strong) / WTI(Strong) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.351), DXY(100.119), VIX(27.49)

### 🏗️ 12) Structural Filter (v2)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↑) / GOLD(↓) / VIX(↑) / WTI(↑)
- **판정:** **ENERGY-DRIVEN STAGFLATION (에너지 주도 스태그)**
- **근거:** 긴축적인 실질금리(2.0%) 환경에서도 고유가가 유지됨. 이는 공급망의 구조적 압박을 의미

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ -0.040 / FCIΔ +0.020 / DXYΔ +0.469 / US10YΔ +0.032 (스태그플레이션)
- **Sentiment (Fear&Greed):** 32.36493705369449 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** DOWN (MID)
- **Phase:** RISK-OFF (긴축/불안·리스크 회피) (Cap: 30)
- **[SPECIAL ALERT]**: **⚠️ 에너지 비용 전이** (Structural Cap: 40)

- **🎯 Final Risk Action:** **REDUCE**
- **Risk Budget (0~100):** **30**
- **Narrative:** 구조=TIGHTENING(스태그플레이션) / 심리=NEUTRAL / 유동성=감소/중간 / 크레딧=안정 → Phase=RISK-OFF (긴축/불안·리스크 회피)

### ⚠ 14) Divergence Monitor
- **정의:** 구조(정책)와 가격(시장 국면)의 충돌 여부 감지
- **추가 이유:** 구조-가격 충돌은 국면 전환의 초기 신호가 될 수 있음

- **Structure:** TIGHTENING
- **Price Regime:** RISK-OFF
- **Status:** **ALIGNED**
- **해석:** 구조와 가격 신호가 대체로 정렬

### 🎯 15) Volatility-Controlled Exposure (v2)
- **정의:** Risk Budget을 실제 익스포저로 변환 (Pro Version)
- **추가 이유:** 변동성·스트레스·국면을 모두 반영한 실전형 리스크 제어

- **Risk Budget:** 30
- **Phase Cap:** 35
- **VIX Level:** 27.49 (HIGH)
- **VIX Change (%):** +12.02%
- **Final Multiplier:** 0.68x

- **📊 Recommended Exposure:** **27%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **VALUE TILT**
- **Duration Tilt:** **SHORT DURATION FAVORED**
- **Cyclical vs Defensive:** **CYCLICAL (ENERGY) BIAS**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** SHORT DURATION FAVORED
- **Inflation Factor:** INFLATION PRESSURE
- **USD Factor:** USD TIGHTENING
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.2)

**Context:** phase=RISK-OFF (긴축/불안·리스크 회피) / T10Y2Y=0.00 (FLAT / FRAGILE) / VIX=20.00 (VOLATILITY NORMAL) / liquidity=DOWN-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE

**Overweight:** Consumer Staples, Health Care, Utilities

**Underweight:** Technology, Real Estate, Consumer Discretionary

**Scoreboard:**
- Consumer Staples: +5  (+3 LIQ, +1 CURVE, +1 PHASE, = +5)
- Health Care: +5  (+3 LIQ, +1 CURVE, +1 PHASE, = +5)
- Utilities: +1  (+1 LIQ, = +1)
- Consumer Discretionary: -1  (-1 LIQ, = -1)
- Real Estate: -2  (-2 LIQ, = -2)
- Technology: -4  (-3 LIQ, -1 PHASE, = -4)

**Rationale (top drivers):**
- OW Consumer Staples: +3: 유동성 긴축 → 방어적 필수소비 선호
- OW Consumer Staples: +1: 플랫 커브(0.00) → 경기 민감도 낮은 섹터 선호
- OW Health Care: +3: 유동성 긴축 → 안정적 현금흐름 선호
- OW Health Care: +1: 플랫 커브(0.00) → 방어/퀄리티 선호
- OW Utilities: +1: 유동성 긴축 → 방어주 버퍼
- UW Technology: -3: 유동성 긴축 → 고밸류에이션 부담
- UW Technology: -1: RISK-OFF → 성장주 미세 감점
- UW Real Estate: -2: 유동성 긴축 → 조달비용 상승 부담


---

### 🧬 19) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Preferred Company Traits:**
- High Free Cash Flow generators
- Net cash or low leverage balance sheets
- Stable margins / pricing power
- Low to mid beta exposure
- RAROC-friendly profile
- Cash flow visibility and earnings stability

**Risk Control / Avoid:**
- Negative FCF / cash-burn models
- High leverage / refinancing-dependent names
- Long-duration, high-multiple growth
- Rate-sensitive long-duration equities

## 🧭 So What? (Decision Layer)
- **Risk Stance:** **REDUCE** *(target exposure: 30%)*
- **Context:** phase=RISK-OFF (긴축/불안·리스크 회피) / liquidity=DOWN-MID / credit_calm=True / geo=NORMAL

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
- **1-Line Conclusion:** 장기듀레이션 성장주 불리 + 고베타/레버리지 제한 → **High FCF / Low leverage / pricing power** 선호

- **Policy → Valuation:** 할인율↑(멀티플 압박) → 장기듀레이션 성장주 불리
- **Liquidity → Risk Budget:** 유동성 흡수(리스크 허용↓) → 고베타/레버리지 제한
- **Credit → Balance Sheet:** 크레딧 안정 → 시스템 리스크 제한

- **Sector/Company Shortcut:** Defensive(Staples/Utilities/Healthcare) + Mega-cap quality

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.1612756341798267
- **Z-Score (5d):** 0.45667712252979653

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
- **Z-Score (1d):** 0.9841746283496073
- **Z-Score (5d):** 0.08268509475814964

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
