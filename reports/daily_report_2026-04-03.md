# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-04-03
**Data as of:** 2026-04-03

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.313  (-0.87% vs 4.351)
- **달러 인덱스**: 100.017  (-0.10% vs 100.119)
- **WTI 유가**: 112.060  (-0.48% vs 112.600)
- **변동성 지수 (VIX)**: 23.870  (-13.17% vs 27.490)
- **원/달러 환율**: 1509.860  (-0.49% vs 1517.340)

---

## 🚨 Regime Change Monitor (always-on)
- **Status:** ✅ DETECTED
- **Prev → Current:** RISK-OFF (긴축/불안·리스크 회피) → RISK-ON (완화 기대·리스크 선호)
- **File:** `insights/risk_alerts.txt` ✅ created
- **Email:** ✅ sent (sent)

---

Some commentary here
## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 23.87 → **High (Risk-off bias)**
- **핵심 조합(전일 대비 방향):** US10Y(↓) / DXY(↓) / VIX(↓)
- **판정:** **RISK-ON (완화 기대·리스크 선호)**
- **근거:** 금리↓ + 달러↓ + VIX↓ → 위험자산 선호/유동성 기대

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↓) / DXY(↓) / VIX(↓)
- **현실(FCI):** level=EASY (완화) / dir(↑) | as of: 2026-03-27 (FRED last available)
- **유인(Real Rates):** level=RESTRICTIVE (유인↓) / dir(↓) | as of: 2026-04-01 (FRED last available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대는 완화지만 FCI 압박 또는 실질금리 유인↓ → 리스크자산 지속성 약화 리스크
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↓) / DXY(↓) / VIX(↓)
- **Policy Bias: MIXED (혼조) (WEAK, score=+0.5) | REAL_RATEΔ +0.020 / FCIΔ +0.020 / DXYΔ -0.102 / US10YΔ -0.038**
- **Expectations: dict received.**

- **판정:** **POLICY EASING (완화)**
- **근거:** 금리↓ + 달러↓ (+VIX 안정) → 완화 쪽
- **한줄요약 ~~** 구조=MIXED (혼조)(WEAK)는 참고, 가격=POLICY EASING (완화) 중심 → 최종 POLICY EASING (완화)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-04-01 (FRED latest)
- **NET_LIQ level:** 5827623.9
- **TGA level:** 847718.0
- **RRP level:** 2.107
- **방향(전일 대비):** TGA(↓) / RRP(↑) / NET_LIQ(↑)
- **판정:** **LIQUIDITY SUPPORTIVE (완만한 유동성 우호)**
- **근거:** Net Liquidity↑ → 시장 내 달러 여력 개선
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-04-01 (FRED latest)
- **HY_OAS level:** 3.16% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↓) / -3.66%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 좁혀지는 중 → 공포 온도 완화
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↑) / LQD(↑)
- **HYG:** today 79.560 / prev 79.370 / pct 0.24%
- **LQD:** today 109.120 / prev 108.660 / pct 0.42%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, -0.87%)** → 완화 기대 강화
- DXY **(Mild, -0.10%)** → 달러 약세/리스크 선호
- WTI **(Mild, -0.48%)** → 물가 부담 완화
- VIX **(Strong, -13.17%)** → 심리 개선/리스크온
- 원/달러(USDKRW) **(Clear, -0.49%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Mild, +0.24%)** → 크레딧 위험선호↑
- LQD (IG Bond ETF) **(Clear, +0.42%)** → 우량채 강세(리스크오프 성향)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 하락(US10Y↓)** → 할인율 압박 완화 → 달러 약세(DXY↓) 유도: **위험자산(Growth/EM) 선호 심리 강화 및 유동성 환경 개선**
- **변동성 하락(VIX↓)** → 심리 개선(Risk-On): **자산군 전반의 위험 수용 여력(Risk Appetite) 회복 및 랠리 지속 가능성**
- **유가 하락(WTI↓)** → 물가 부담 완화: **실질 구매력 회복 및 긴축 압력 완화(Dovish Tilt) 가능성 시사**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### ⚠ 6.5) Correlation Break Monitor

No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
- DEBUG: pct XLK=0.8005350246373281, XLF=0.18203914864043713, XLE=0.47481562404745775, XLRE=1.6117212090736324
No significant sector-level correlation break detected.

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 하락(VIX↓)** → 심리 안정: 리스크 수용 여력 개선
- **금리 하락(US10Y↓)** → 완화 기대/할인율 부담 완화 가능
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 하락(WTI↓)** → 물가 부담 완화 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **-0.37**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** -0.09
- **Geo Momentum:** -0.28 *(Status: FALLING)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Israel_2023
- **Cosine Similarity Score:** -0.057
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Israel_2023: -0.057
  - Red_Sea: -0.069
  - Taiwan_Tension: -0.138
- **Top Drivers:**
  - VIX: z_used=-1.84 (z1d=-1.53, z5d=-2.30, raw_w=0.18, norm_w=0.14) → contrib=-0.25
  - EMB: z_used=-0.89 (z1d=+0.34, z5d=+1.71, raw_w=0.12, norm_w=0.09) → contrib=-0.08
  - USDCNH: z_used=-0.45 (z1d=-0.33, z5d=-0.63, raw_w=0.18, norm_w=0.14) → contrib=-0.06
  - KR10Y_SPREAD: z_used=-1.00 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.06
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스는 여전히 정상 범위에 있지만 최근 압력이 완화되고 있는 중입니다. 경계 유지.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Israel_2023** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (GLD)
- **Extreme Country Risk:** GLD

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
- **강도:** US10Y(Strong) / DXY(Mild) / WTI(Mild) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.313), DXY(100.017), VIX(23.87)

### 🏗️ 12) Structural Filter (v2)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↓) / DXY(↓) / GOLD(↑) / VIX(↓) / WTI(↓)
- **판정:** **ENERGY-DRIVEN STAGFLATION (에너지 주도 스태그)**
- **근거:** 긴축적인 실질금리(2.02%) 환경에서도 고유가가 유지됨. 이는 공급망의 구조적 압박을 의미

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: MIXED (혼조) (WEAK, score=+0.5) | REAL_RATEΔ +0.020 / FCIΔ +0.020 / DXYΔ -0.102 / US10YΔ -0.038 (스태그플레이션)
- **Sentiment (Fear&Greed):** 40.172407627318975 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** UP (MID)
- **Phase:** RISK-ON (완화 기대·리스크 선호) (Cap: 30)
- **[SPECIAL ALERT]**: **⚠️ 에너지 비용 전이** (Structural Cap: 40)

- **🎯 Final Risk Action:** **REDUCE**
- **Risk Budget (0~100):** **30**
- **Narrative:** 구조=MIXED(스태그플레이션) / 심리=NEUTRAL / 유동성=증가/중간 / 크레딧=안정 → Phase=RISK-ON (완화 기대·리스크 선호)

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
- **VIX Level:** 23.87 (HIGH)
- **VIX Change (%):** -13.17%
- **Final Multiplier:** 0.84x

- **📊 Recommended Exposure:** **29%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **NEUTRAL**
- **Duration Tilt:** **LONG DURATION FAVORED**
- **Cyclical vs Defensive:** **DEFENSIVE FAVORED**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** LONG DURATION FAVORED
- **Inflation Factor:** NEUTRAL
- **USD Factor:** NEUTRAL
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.2)

**Context:** phase=RISK-ON (완화 기대·리스크 선호) / T10Y2Y=0.52 (MODERATE STEEP) / VIX=24.54 (VOLATILITY NORMAL) / liquidity=UP-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE

**Overweight:** Industrials, Financials, Technology, Consumer Discretionary

**Underweight:** Utilities

**Scoreboard:**
- Industrials: +4  (+2 LIQ, +1 CURVE, +1 PHASE, = +4)
- Financials: +3  (+1 LIQ, +2 CURVE, = +3)
- Technology: +3  (+2 LIQ, +1 PHASE, = +3)
- Consumer Discretionary: +2  (+2 LIQ, = +2)
- Utilities: -1  (-1 LIQ, = -1)

**Rationale (top drivers):**
- OW Industrials: +2: 유동성 완화 → 경기민감 회복
- OW Industrials: +1: 완만한 스티프닝(0.52) → 성장 기대 반영
- OW Financials: +1: 유동성 완화 → 위험선호 회복
- OW Financials: +2: 완만한 스티프닝(0.52) → 예대마진 개선
- OW Technology: +2: 유동성 완화 → 성장주/베타 우호
- OW Technology: +1: RISK-ON → 성장주 미세 가점
- OW Consumer Discretionary: +2: 유동성 완화 → 소비 민감주 우호
- UW Utilities: -1: 유동성 완화 → 방어주 상대매력 저하


---

### 🧬 19) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Preferred Company Traits:**
- Balanced quality exposure
- Selective sector-neutral positioning

**Risk Control / Avoid:**
- Unscreened speculative exposure

## 🧭 So What? (Decision Layer)
- **Risk Stance:** **REDUCE** *(target exposure: 30%)*
- **Context:** phase=RISK-ON (완화 기대·리스크 선호) / liquidity=UP-MID / credit_calm=True / geo=NORMAL

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
- **1-Line Conclusion:** 퀄리티 중심 차별화 + 베타 확장 가능 → **High operating leverage / cyclicals / growth optionality** 선호

- **Policy → Valuation:** 할인율 방향성 불명확 → 퀄리티 중심 차별화
- **Liquidity → Risk Budget:** 유동성 공급(리스크 허용↑) → 베타 확장 가능
- **Credit → Balance Sheet:** 크레딧 안정 → 시스템 리스크 제한

- **Sector/Company Shortcut:** Cyclicals/Tech(상황에 따라) + Small/Mid beta

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.8308411581771605
- **Z-Score (5d):** 2.093152295009902

### EEM
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.6841970754157566
- **Z-Score (5d):** 0.6507684275440477

### EIS
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.3754373559874648
- **Z-Score (5d):** -0.2718252716628387

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.3076039785146895
- **Z-Score (5d):** 1.642055263486481

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.903095974307816
- **Z-Score (5d):** 0.8929660696328626

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.13850539868585948
- **Z-Score (5d):** 1.0493691165467434

### GLD
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.765013741187367
- **Z-Score (5d):** 1.1630529279220787

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.1899228277830461
- **Z-Score (5d):** 1.7280075959239154

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.1439613098937333
- **Z-Score (5d):** -1.4574567473881597
