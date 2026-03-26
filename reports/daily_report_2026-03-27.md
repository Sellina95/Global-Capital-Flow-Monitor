# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-03-27
**Data as of:** 2026-03-27

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.416  (+1.28% vs 4.360)
- **달러 인덱스**: 99.865  (+0.07% vs 99.797)
- **WTI 유가**: 93.220  (+0.34% vs 92.900)
- **변동성 지수 (VIX)**: 27.440  (+4.10% vs 26.360)
- **원/달러 환율**: 1507.470  (+0.15% vs 1505.280)

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

- **VIX 레벨:** 27.44 → **High (Risk-off bias)**
- **핵심 조합(전일 대비 방향):** US10Y(↑) / DXY(↑) / VIX(↑)
- **판정:** **RISK-OFF (긴축/불안·리스크 회피)**
- **근거:** 금리↑ + 달러↑ + VIX↑ → 안전자산/현금 선호 강화

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↑) / DXY(↑) / VIX(↑)
- **현실(FCI):** level=EASY (완화) / dir(↑) | as of: 2026-03-20 (FRED last available)
- **유인(Real Rates):** level=RESTRICTIVE (유인↓) / dir(↑) | as of: 2026-03-25 (FRED last available)
- **판정:** **LIQUIDITY TIGHTENING (유동성 축소)**
- **근거:** 금리↑+달러↑ + (FCI 압박 또는 실질금리 유인↓) → 리스크자산에 불리
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↑) / DXY(↑) / VIX(↑)
- **Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ -0.040 / FCIΔ +0.039 / DXYΔ +0.068 / US10YΔ +0.056**
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
- **Spread as of:** 2026-03-25 (FRED latest)
- **HY_OAS level:** 3.17% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↓) / -0.63%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 좁혀지는 중 → 공포 온도 완화
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(↓)
- **HYG:** today 78.920 / prev 79.275 / pct -0.45%
- **LQD:** today 107.880 / prev 108.490 / pct -0.56%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, +1.28%)** → 완화 기대 약화/금리 부담
- DXY **(Mild, +0.07%)** → 달러 강세/신흥국 부담
- WTI **(Mild, +0.34%)** → 인플레 재자극 가능성
- VIX **(Strong, +4.10%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Mild, +0.15%)** → 원화 약세/수급 부담
- HYG (High Yield ETF) **(Clear, -0.45%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Clear, -0.56%)** → 우량채 약세(리스크온 성향)

### 🧩 6) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함

- **금리 상승(US10Y↑)** → 달러 강세(DXY↑) / 위험자산 할인율 부담 / 성장주 변동성↑ 경향
- **변동성 상승(VIX↑)** → 위험회피 강화 / 달러 선호↑ / 원자재·주식 부담 가능
- **유가 상승(WTI↑)** → 인플레 재자극 가능성 / 금리 상방 압력

### ⚠ 6.5) Correlation Break Monitor

No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
- DEBUG: pct XLK=-2.1490315216080718, XLF=-0.7185498451729493, XLE=0.7038800198096997, XLRE=-0.5553461125772119
Correlation Break Detected:
- US10Y ↑ but XLF ↓ (Financials)

So What?
- 금리 상승에도 금융 약세 → NIM 기대보다 경기/신용 우려가 더 큼 (포지션 과신 금지)
- 결론: **섹터 ‘공식’이 깨진 구간** → 방향 베팅보다 **사이징 축소 + 리더 중심**

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 상승(VIX↑)** → 변동성 확대: 포지션 축소/헤지 수요 증가 가능
- **금리 상승(US10Y↑)** → 할인율 부담/유동성 압박 가능
- **달러 강세(DXY↑)** → 신흥국·원자재·원화 등 위험자산에 부담
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **+0.33**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** +0.14
- **Geo Momentum:** +0.19 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Taiwan_Tension
- **Cosine Similarity Score:** 0.482
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Taiwan_Tension: 0.482
  - Ukraine_2022: 0.428
  - Israel_2023: 0.336
- **Top Drivers:**
  - EMB: z_used=+1.59 (z1d=-2.28, z5d=-0.57, raw_w=0.12, norm_w=0.09) → contrib=+0.15
  - EEM: z_used=+1.20 (z1d=-1.24, z5d=-1.15, raw_w=0.10, norm_w=0.08) → contrib=+0.09
  - USDCNH: z_used=+0.64 (z1d=+0.05, z5d=+1.51, raw_w=0.18, norm_w=0.14) → contrib=+0.09
  - KR10Y_SPREAD: z_used=-1.00 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.06
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Taiwan_Tension** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (EEM, EIS, FXI, VXX)
- **Extreme Country Risk:** EEM, EIS, FXI, VXX

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
- **강도:** US10Y(Strong) / DXY(Mild) / WTI(Mild) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.416), DXY(99.865), VIX(27.44)

### 🏗️ 12) Structural Filter
- **질문:** 이 변화가 글로벌 구조(달러 패권/성장/에너지)에 어떤 힌트를 주는가?
- **핵심 신호:** US10Y(↑) / DXY(↑) / VIX(↑) / WTI(↑)
- **판정:** **GLOBAL FINANCIAL TIGHTENING (글로벌 긴축 구조)**
- **근거:** 금리↑ + 달러↑ 조합은 글로벌 자금조달 비용을 올려 신흥국/리스크자산에 부담

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ -0.040 / FCIΔ +0.039 / DXYΔ +0.068 / US10YΔ +0.056
- **Sentiment (Fear&Greed):** 31.26502886667732 (NEUTRAL)
- **Credit Calm (HY OAS<4):** True
- **Liquidity (NET_LIQ):** dir=DOWN / level=MID
- **Phase:** RISK-OFF (긴축/불안·리스크 회피)

- **🎯 Final Risk Action:** **REDUCE**
- **Risk Budget (0~100):** **35**
- **Narrative:** 구조=TIGHTENING / 심리=NEUTRAL / 유동성=감소/중간 / 크레딧=안정 → Phase=RISK-OFF (긴축/불안·리스크 회피)

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

- **Risk Budget:** 35
- **Phase Cap:** 35
- **VIX Level:** 27.44 (HIGH)
- **VIX Change (%):** +4.10%
- **Final Multiplier:** 0.80x

- **📊 Recommended Exposure:** **33%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **VALUE TILT**
- **Duration Tilt:** **SHORT DURATION FAVORED**
- **Cyclical vs Defensive:** **DEFENSIVE FAVORED**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** SHORT DURATION FAVORED
- **Inflation Factor:** NEUTRAL
- **USD Factor:** NEUTRAL
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v2)

**Context:** phase=RISK-OFF (긴축/불안·리스크 회피) / T10Y2Y=0.00 / VIX=27.44 / credit=True

**Overweight:** Consumer Staples, Health Care, Utilities
**Underweight:** Technology, Real Estate

**Rationale (top drivers):**
- UW Technology: -3: 유동성 긴축 → 고밸류에이션 부담
- UW Technology: -3: VIX 27.4 → 위험자산 회피
- OW Consumer Staples: +3: 유동성 긴축 → 방어적 필수소비 선호
- OW Consumer Staples: +2: VIX 27.4 → 경기 비탄력적 섹터 선호
- OW Health Care: +3: 유동성 긴축 → 안정적 현금흐름 선호
- OW Utilities: +3: 시장 공포 확산(VIX 27.4) → 최우선 피난처


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
- **Risk Stance:** **REDUCE** *(target exposure: 35%)*
- **Context:** phase=RISK-OFF (긴축/불안·리스크 회피) / liquidity=DOWN-MID / credit_calm=True / geo=NORMAL

## 🗺️ Scenario Framework (Base / Bull / Bear)

### 🔹 Base Case
- 조건: 유동성 혼조 + 크레딧 안정 유지 / 변동성 급등 없이 박스권 장세 지속
- 전략: 노출 35% 유지, 퀄리티 중심 선별적 접근

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
- **Z-Score (1d):** -2.272447062398424
- **Z-Score (5d):** -1.8413675794468776

### EEM
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -2.1611014101367605
- **Z-Score (5d):** -1.3357550218209582

### EIS
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -1.2948193374984127
- **Z-Score (5d):** -1.4651557527491885

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -2.369791755245505
- **Z-Score (5d):** -1.5319364803257993

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -1.6424703047035605
- **Z-Score (5d):** -0.595191418246228

### FXI
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -2.034518565464422
- **Z-Score (5d):** -1.0541600342222224

### GLD
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -1.482688386416877
- **Z-Score (5d):** -1.1057196830542604

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -2.1340592175403987
- **Z-Score (5d):** -1.356325886729923

### VXX
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 1.4145717043117143
- **Z-Score (5d):** 1.100598525219013
