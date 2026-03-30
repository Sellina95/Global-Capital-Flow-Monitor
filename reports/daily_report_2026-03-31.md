# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-03-31
**Data as of:** 2026-03-31

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.330  (+0.00% vs 4.330)
- **달러 인덱스**: 100.521  (-0.00% vs 100.525)
- **WTI 유가**: 102.140  (+0.02% vs 102.120)
- **변동성 지수 (VIX)**: 29.750  (+0.00% vs 29.750)
- **원/달러 환율**: 1518.680  (+0.05% vs 1517.880)

---

## 🚨 Regime Change Monitor (always-on)
- **Status:** ✅ DETECTED
- **Prev → Current:** RISK-OFF (긴축/불안·리스크 회피) → EVENT-WATCHING (이벤트 관망)
- **File:** `insights/risk_alerts.txt` ✅ created
- **Email:** ✅ sent (sent)

---

Some commentary here
## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 29.75 → **High (Risk-off bias)**
- **핵심 조합(전일 대비 방향):** US10Y(→) / DXY(↓) / VIX(→)
- **판정:** **EVENT-WATCHING (이벤트 관망)**
- **근거:** 변동성은 눌려있지만 금리/달러가 움직임 → 데이터/이벤트 대기

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(→) / DXY(↓) / VIX(→)
- **현실(FCI):** level=EASY (완화) / dir(↑) | as of: 2026-03-20 (FRED last available)
- **유인(Real Rates):** level=RESTRICTIVE (유인↓) / dir(↓) | as of: 2026-03-26 (FRED last available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(→) / DXY(↓) / VIX(→)
- **Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.0) | REAL_RATEΔ +0.060 / FCIΔ +0.039 / DXYΔ -0.004 / US10YΔ +0.000**
- **Expectations: dict received.**

- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리/달러/변동성 신호가 완전히 정렬되지 않음
- **한줄요약 ~~** 구조=TIGHTENING (긴축)(MODERATE)는 참고, 가격=POLICY MIXED (정책 신호 혼조) 중심 → 최종 POLICY MIXED (정책 신호 혼조)

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
- **Spread as of:** 2026-03-27 (FRED latest)
- **HY_OAS level:** 3.42% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↑) / +6.54%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(→) / LQD(→)
- **HYG:** today 79.015 / prev 79.015 / pct 0.00%
- **LQD:** today 108.465 / prev 108.465 / pct 0.00%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Noise, +0.00%)** → 보합(관망)
- DXY **(Noise, -0.00%)** → 달러 약세/리스크 선호
- WTI **(Noise, +0.02%)** → 인플레 재자극 가능성
- VIX **(Noise, +0.00%)** → 변동성 보합(심리 변화 제한)
- 원/달러(USDKRW) **(Mild, +0.05%)** → 원화 약세/수급 부담
- HYG (High Yield ETF) **(Noise, +0.00%)** → 보합(크레딧 변화 제한)
- LQD (IG Bond ETF) **(Noise, +0.00%)** → 보합(방향성 제한)

### 🧩 6) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함

- **금리 보합(US10Y→)** → 할인율 변수 제한
- **변동성 보합(VIX→)** → 심리 변화 제한
- **유가 상승(WTI↑)** → 인플레 재자극 가능성 / 금리 상방 압력

### ⚠ 6.5) Correlation Break Monitor

No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
- DEBUG: pct XLK=-0.00388849549485788, XLF=0.0, XLE=0.02387677446880553, XLRE=0.01232064410444612
No significant sector-level correlation break detected.

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 보합(VIX→)** → 심리 변화 제한
- **금리 보합(US10Y→)** → 금리 변수 제한
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **+0.15**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** +0.25
- **Geo Momentum:** -0.09 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Taiwan_Tension
- **Cosine Similarity Score:** 0.428
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Taiwan_Tension: 0.428
  - Ukraine_2022: 0.390
  - Israel_2023: 0.328
- **Top Drivers:**
  - USDCNH: z_used=+0.69 (z1d=+0.08, z5d=+1.60, raw_w=0.18, norm_w=0.14) → contrib=+0.10
  - KR10Y_SPREAD: z_used=-1.00 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.06
  - DE10Y_SPREAD: z_used=+1.00 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=+0.05
  - EEM: z_used=+0.34 (z1d=+0.01, z5d=-0.87, raw_w=0.10, norm_w=0.08) → contrib=+0.03
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Taiwan_Tension** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (EEM, EIS, GLD, SPY, VXX)
- **Extreme Country Risk:** EEM, EIS, GLD, SPY, VXX

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
- **핵심 신호:** US10Y(→) / DXY(↓) / WTI(↑) / VIX(→)
- **판정:** **달러 약세(DXY↓) + 유가 상승(WTI↑)**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Noise) / DXY(Noise) / WTI(Noise) / VIX(Noise)
- **판정:** **MOSTLY NOISE (대부분 노이즈)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.330), DXY(100.521), VIX(29.75)

### 🏗️ 12) Structural Filter (v2)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(→) / DXY(↓) / GOLD(↑) / VIX(→) / WTI(↑)
- **판정:** **ENERGY-DRIVEN STAGFLATION (에너지 주도 스태그)**
- **근거:** 긴축적인 실질금리(2.08%) 환경에서도 고유가가 유지됨. 이는 공급망의 구조적 압박을 의미

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.0) | REAL_RATEΔ +0.060 / FCIΔ +0.039 / DXYΔ -0.004 / US10YΔ +0.000 (스태그플레이션)
- **Sentiment (Fear&Greed):** 24.62722529300201 (FEAR)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** DOWN (MID)
- **Phase:** EVENT-WATCHING (이벤트 관망) (Cap: 30)
- **[SPECIAL ALERT]**: **⚠️ 에너지 비용 전이** (Structural Cap: 40)

- **🎯 Final Risk Action:** **STRONG REDUCE**
- **Risk Budget (0~100):** **10**
- **Narrative:** 구조=TIGHTENING(스태그플레이션) / 심리=FEAR / 유동성=감소/중간 / 크레딧=안정 → Phase=EVENT-WATCHING (이벤트 관망)

### ⚠ 14) Divergence Monitor
- **정의:** 구조(정책)와 가격(시장 국면)의 충돌 여부 감지
- **추가 이유:** 구조-가격 충돌은 국면 전환의 초기 신호가 될 수 있음

- **Structure:** TIGHTENING
- **Price Regime:** MIXED
- **Status:** **DELAYED RESPONSE**
- **해석:** 구조는 긴축이나 가격은 아직 명확히 반응하지 않음

### 🎯 15) Volatility-Controlled Exposure (v2)
- **정의:** Risk Budget을 실제 익스포저로 변환 (Pro Version)
- **추가 이유:** 변동성·스트레스·국면을 모두 반영한 실전형 리스크 제어

- **Risk Budget:** 10
- **Phase Cap:** 100
- **VIX Level:** 29.75 (HIGH)
- **VIX Change (%):** +0.00%
- **Final Multiplier:** 0.80x

- **📊 Recommended Exposure:** **9%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **VALUE TILT**
- **Duration Tilt:** **NEUTRAL**
- **Cyclical vs Defensive:** **DEFENSIVE FAVORED**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** NEUTRAL
- **Inflation Factor:** NEUTRAL
- **USD Factor:** NEUTRAL
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.2)

**Context:** phase=EVENT-WATCHING (이벤트 관망) / T10Y2Y=0.56 (MODERATE STEEP) / VIX=31.05 (VOLATILITY SHOCK) / liquidity=DOWN-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE

**Overweight:** Consumer Staples, Health Care, Utilities, Financials

**Underweight:** Technology, Consumer Discretionary, Real Estate

**Scoreboard:**
- Consumer Staples: +7  (+3 VOL, +3 LIQ, +1 PHASE, = +7)
- Health Care: +6  (+2 VOL, +3 LIQ, +1 PHASE, = +6)
- Utilities: +5  (+4 VOL, +1 LIQ, = +5)
- Financials: +1  (-1 VOL, +2 CURVE, = +1)
- Real Estate: -2  (-2 LIQ, = -2)
- Consumer Discretionary: -3  (-2 VOL, -1 LIQ, = -3)
- Technology: -7  (-4 VOL, -3 LIQ, = -7)

**Rationale (top drivers):**
- OW Consumer Staples: +3: VOLATILITY SHOCK → 경기 비탄력적 섹터 선호 (absolute mode: VIX 31.1)
- OW Consumer Staples: +3: 유동성 긴축 → 방어적 필수소비 선호
- OW Health Care: +2: VOLATILITY SHOCK → 방어/현금흐름 선호 (absolute mode: VIX 31.1)
- OW Health Care: +3: 유동성 긴축 → 안정적 현금흐름 선호
- OW Utilities: +4: VOLATILITY SHOCK → 최우선 피난처 (absolute mode: VIX 31.1)
- OW Utilities: +1: 유동성 긴축 → 방어주 버퍼
- OW Financials: +2: 완만한 스티프닝(0.56) → 예대마진 개선
- OW Financials: -1: Financials Cap → VIX 고점 + 유동성 긴축으로 금융주 상단 제한


---

### 🧬 19) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Preferred Company Traits:**
- High Free Cash Flow generators
- Net cash or low leverage balance sheets
- Stable margins / pricing power
- Low to mid beta exposure
- High RAROC Focus
- Cash flow visibility and earnings stability

**Risk Control / Avoid:**
- Negative FCF / cash-burn models
- High leverage / refinancing-dependent names
- Long-duration, high-multiple growth
- Rate-sensitive long-duration equities

## 🧭 So What? (Decision Layer)
- **Risk Stance:** **STRONG REDUCE** *(target exposure: 10%)*
- **Context:** phase=EVENT-WATCHING (이벤트 관망) / liquidity=DOWN-MID / credit_calm=True / geo=NORMAL

## 🗺️ Scenario Framework (Base / Bull / Bear)

### 🔹 Base Case
- 조건: 유동성 혼조 + 크레딧 안정 유지 / 변동성 급등 없이 박스권 장세 지속
- 전략: 노출 10% 유지, 퀄리티 중심 선별적 접근

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
- **Z-Score (1d):** 2.36284377213785
- **Z-Score (5d):** 0.431595643062618

### EEM
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.15187629407001582
- **Z-Score (5d):** -1.3299672098458308

### EIS
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -1.6620041676080037
- **Z-Score (5d):** -2.650146838715638

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.8892723472280663
- **Z-Score (5d):** -0.9381612430941189

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.7019658096952164
- **Z-Score (5d):** -0.5342556745608111

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.7271772190639516
- **Z-Score (5d):** 0.029485589526380782

### GLD
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 0.18195950884549897
- **Z-Score (5d):** 0.5350348803581406

### SPY
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 0.5520129883190679
- **Z-Score (5d):** -2.0235700473044544

### VXX
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.6562964883684885
- **Z-Score (5d):** 1.6660953763182096
