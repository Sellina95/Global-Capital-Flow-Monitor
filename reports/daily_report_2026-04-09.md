# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-04-09
**Data as of:** 2026-04-09

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: ✅ STABLE (권장 노출도: 66%)**
> **구조적 수급(14번)과 실시간 발작(SEW), 15번 데드맨 로직을 통합하여 판단합니다.**

- **[14번 수급괴리]:** ✅ **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **[액션 시그널]:** 🚨 **STAY (포지션 유지)**
- **[실시간 보초병(SEW)]:**
  ✅ 지난 24시간 내 특이 수급 발작 없음 (15번 필터 통과)
- **[15번 데드맨]:** ✅ PASS (정상 범위 내)
### 🚩 Market Regime Status
- **현재 국면 유지:** ✅ **TRANSITION / MIXED (전환·혼조)**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.291  (+0.00% vs 4.291)
- **달러 인덱스**: 98.947  (-0.08% vs 99.030)
- **WTI 유가**: 99.360  (+5.24% vs 94.410)
- **변동성 지수 (VIX)**: 21.520  (+2.28% vs 21.040)
- **원/달러 환율**: 1480.130  (-1.27% vs 1499.130)

---

Some commentary here
## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 21.52 → **High (Risk-off bias)**
- **핵심 조합(전일 대비 방향):** US10Y(→) / DXY(↓) / VIX(↑)
- **판정:** **TRANSITION / MIXED (전환·혼조)**
- **근거:** 금리/달러/변동성 축이 한 방향으로 정렬되지 않음

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(→) / DXY(↓) / VIX(↑)
- **현실(FCI):** level=EASY (완화) / dir(→) | as of: 2026-04-09 (FRED last available)
- **유인(Real Rates):** level=NEUTRAL (중립) / dir(→) | as of: 2026-04-09 (FRED last available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(→) / DXY(↓) / VIX(↑)
- **Policy Bias: EASING (완화) (MODERATE, score=-1.0) | REAL_RATEΔ +0.000 / FCIΔ +0.000 / DXYΔ -0.083 / US10YΔ +0.000**
- **Expectations: dict received.**

- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리/달러/변동성 신호가 완전히 정렬되지 않음
- **한줄요약 ~~** 구조=EASING (완화)(MODERATE)는 참고, 가격=POLICY MIXED (정책 신호 혼조) 중심 → 최종 POLICY MIXED (정책 신호 혼조)

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
- **Spread as of:** 2026-04-07 (FRED latest)
- **HY_OAS level:** 3.12% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↑) / +2.30%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(→) / LQD(→)
- **HYG:** today 80.190 / prev 80.190 / pct 0.00%
- **LQD:** today 109.490 / prev 109.490 / pct 0.00%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Noise, +0.00%)** → 보합(관망)
- DXY **(Mild, -0.08%)** → 달러 약세/리스크 선호
- WTI **(Strong, +5.24%)** → 인플레 재자극 가능성
- VIX **(Clear, +2.28%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Strong, -1.27%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Noise, +0.00%)** → 보합(크레딧 변화 제한)
- LQD (IG Bond ETF) **(Noise, +0.00%)** → 보합(방향성 제한)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 보합(US10Y→)** → 할인율 변수 제한: 시장은 정책 경로 재확인을 위한 대기 국면
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
- **금리 보합(US10Y→)** → 금리 변수 제한
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **-0.39**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** -0.53
- **Geo Momentum:** +0.14 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Israel_2023
- **Cosine Similarity Score:** -0.162
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Israel_2023: -0.162
  - Red_Sea: -0.193
  - Iran_Crisis_2020: -0.197
- **Top Drivers:**
  - USDCNH: z_used=-1.39 (z1d=-1.09, z5d=-1.85, raw_w=0.18, norm_w=0.14) → contrib=-0.19
  - EMB: z_used=-0.74 (z1d=+0.04, z5d=+1.79, raw_w=0.12, norm_w=0.09) → contrib=-0.07
  - KR10Y_SPREAD: z_used=-1.00 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.06
  - VIX: z_used=-0.42 (z1d=+0.13, z5d=-1.26, raw_w=0.18, norm_w=0.14) → contrib=-0.06
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Israel_2023** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** No (BND, EEM, EIS, EMB, EWJ, FXI, GLD, SPY, VXX)

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(50.00bp) | 실질금리(1.96%) | DXY(98.95)
*(as of: RealRate: 2026-04-09 / FRED last available)*

Neutral - 자본의 방향성이 탐색 구간에 있음 (실질금리 정상화 과정)

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** US10Y(→) / DXY(↓) / WTI(↑) / VIX(↑)
- **판정:** **달러 약세(DXY↓) + 유가 상승(WTI↑) + 변동성 확대(VIX↑)**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Noise) / DXY(Mild) / WTI(Strong) / VIX(Clear)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.291), DXY(98.947), VIX(21.52)

### 🏗️ 12) Structural Filter (v2)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(→) / DXY(↓) / GOLD(↑) / VIX(↑) / WTI(↑)
- **판정:** **COST-PUSH STRUCTURE (비용 주도 구조)**
- **근거:** 경기 지지(금리 하락)가 필요한 상황에서 유가 상승은 실물 경제의 구조적 비용 부담을 가중시킴

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: EASING (완화) (MODERATE, score=-1.0) | REAL_RATEΔ +0.000 / FCIΔ +0.000 / DXYΔ -0.083 / US10YΔ +0.000 (정상)
- **Sentiment (Fear&Greed):** 49.62654387019943 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** UP (MID)
- **Phase:** TRANSITION / MIXED (전환·혼조) (Cap: 70)

- **🎯 Final Risk Action:** **INCREASE**
- **Risk Budget (0~100):** **70**
- **Narrative:** 구조=EASING / 심리=NEUTRAL / 유동성=증가/중간 / 크레딧=안정 / 수급=0.68 → Phase=TRANSITION / MIXED (전환·혼조)

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `EASING` | **Price(Regime):** `MIXED` | **VIX:** `21.52`
- **Positioning Data:** Z-Score: `0.68` (>1.8 시 Run) | Gamma: `1.00` (<0.5 시 Run) | CTA: `1.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v2.6)
- **정의:** Risk Budget을 실제 익스포저로 변환 (Positions & Deadman Switch)
- **추가 이유:** 수급 과열(POS_Z)이나 급격한 쏠림 발생 시 강제 시스템 셧다운

- **Risk Budget:** 70 | **Phase Cap:** 70
- **VIX Level:** 21.52 (HIGH) | **Change:** +2.28%
- **Final Multiplier:** 0.80x (Vol x Pos)
- **Slope Intensity:** 0.0000 (Stable)

- **📊 Recommended Exposure:** **66%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **GROWTH TILT**
- **Duration Tilt:** **NEUTRAL**
- **Cyclical vs Defensive:** **CYCLICAL (ENERGY) BIAS**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** NEUTRAL
- **Inflation Factor:** NEUTRAL
- **USD Factor:** NEUTRAL
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.2)

**Context:** phase=TRANSITION / MIXED (전환·혼조) / T10Y2Y=0.50 (MODERATE STEEP) / VIX=21.52 (VOLATILITY NORMAL) / liquidity=UP-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE

**Overweight:** Financials, Industrials, Consumer Discretionary, Technology

**Underweight:** Utilities

**Scoreboard:**
- Financials: +3  (+1 LIQ, +2 CURVE, = +3)
- Industrials: +3  (+2 LIQ, +1 CURVE, = +3)
- Consumer Discretionary: +2  (+2 LIQ, = +2)
- Technology: +2  (+2 LIQ, = +2)
- Utilities: -1  (-1 LIQ, = -1)

**Rationale (top drivers):**
- OW Financials: +1: 유동성 완화 → 위험선호 회복
- OW Financials: +2: 완만한 스티프닝(0.50) → 예대마진 개선
- OW Industrials: +2: 유동성 완화 → 경기민감 회복
- OW Industrials: +1: 완만한 스티프닝(0.50) → 성장 기대 반영
- OW Consumer Discretionary: +2: 유동성 완화 → 소비 민감주 우호
- OW Technology: +2: 유동성 완화 → 성장주/베타 우호
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
- **Risk Stance:** **INCREASE** *(target exposure: 70%)*
- **Context:** phase=TRANSITION / MIXED (전환·혼조) / liquidity=UP-MID / credit_calm=True / geo=NORMAL

## 🗺️ Scenario Framework (Base / Bull / Bear)

### 🔹 Base Case
- 조건: 유동성 혼조 + 크레딧 안정 유지 / 변동성 급등 없이 박스권 장세 지속
- 전략: 노출 70% 유지, 퀄리티 중심 선별적 접근

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


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.72192924906809
- **Z-Score (5d):** 0.8910062670649734

### EEM
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 3.0269033528757068
- **Z-Score (5d):** 2.0096445650624863

### EIS
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 2.0404349380548084
- **Z-Score (5d):** 1.7121296045588508

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 2.5634161431051106
- **Z-Score (5d):** 2.2217235313053916

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 2.670974576153745
- **Z-Score (5d):** 1.651313553147251

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.904020980364808
- **Z-Score (5d):** 0.8253604024435469

### GLD
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.19532882255793949
- **Z-Score (5d):** 0.07310670151601449

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 2.7010729112007996
- **Z-Score (5d):** 2.7465311782535893

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -2.0558069813985957
- **Z-Score (5d):** -2.114083308607435
