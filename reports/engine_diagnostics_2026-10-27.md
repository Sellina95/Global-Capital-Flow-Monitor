# ENGINE DIAGNOSTICS
**Date:** 2026-10-27
**Data as of:** 2026-10-26

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: ✅ STABLE**
> **판단 요약: 구조-가격-수급 정렬 / 실시간 이상징후 없음 / 데드맨 정상**
### 🎯 Exposure Framework
- **Base Exposure (전략 기준): 48%**
- **Final Exposure (실행 기준): 48%**

- **Portfolio Stance:** HOLD / 48%

- **[14번 구조·수급 괴리]:** ✅ **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
### 🟢 Current SEW Status
- **SEW:** STABLE | ✅ 이상징후 없음 (5개 자산 정상 범위 / z-score 발작 없음)
- **Event Type:** NORMAL → 정상 상태 / 구조적 리스크 없음
- **Spike Monitor:** Spike 0 / Extreme 0

- **[15번 Hard Deadman]:** ✅ PASS
- **[14번 수급 시그널]:** 🚨 **STAY (포지션 유지)**

### 🔬 Structural Layer (12.5~12.8)
- **Structural Layer:**
  - Growth Sustainability → **LATE_CYCLE_STRAIN** (Growth momentum is weakening and the cycle is showing strain. Financing, demand, or policy support is not strong enough.)
  - Flow Authenticity → **EARLY_ROTATION** (Participation is emerging, but confirmation remains limited.)
  - Leadership Breadth → **BROAD_LEADERSHIP** (Leadership is broadening across sectors, confirming healthier market participation.)
  - Positioning Stress → **SQUEEZE_RISK** (Positioning is stretched and vulnerable to squeeze-driven reversals.)

## 🎯 Final Decision (War Room Override)
- **Final Action:** **HOLD**
- **Final Exposure:** **48%**
- **Base Context:** phase=TRANSITION / MIXED / narrative=HOLD / base_exposure=48%
- **SEW:** STABLE / NORMAL
- **Divergence:** ALIGNED / **STAY (포지션 유지)**
- **Drift:** ⚡ STRUCTURAL DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK / score=6
- **Flow:** 🔥 BUILDING HARD / score=7
- **Gamma:** 🟡 TRANSITION
- **Tactical Action:** HOLD / NONE / LOW
- **Positioning:** pos_z=1.21
- **Warning Score:** 0 (No warning)
- **Tactical Why:** No actionable alignment
- **Why:** SEW STABLE → 실시간 이상징후 없음 → Divergence ALIGNED → 구조·가격·수급 정렬 → Narrative Action=HOLD 반영 → Tactical=HOLD / Flow=🔥 BUILDING HARD(7) / Drift=⚡ STRUCTURAL DRIFT(6) / Gamma=🟡 TRANSITION → Tactical HOLD/MONITOR → 최종판단 변경 없음

### 🚩 Market Regime Status
- **국면 전환 감지:** 🚨 **SOFT RISK-OFF (경계 강화)** → **TRANSITION / MIXED**
- **Structural Regime:** **UNKNOWN_TRANSITION**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.986  (-0.04% vs 4.988)
- **달러 인덱스**: 101.960  (+0.15% vs 101.810)
- **WTI 유가**: 101.760  (-1.46% vs 103.270)
- **변동성 지수 (VIX)**: 18.390 (-5.45% vs 19.450)
- **원/달러 환율**: 1321.760  (-0.32% vs 1325.990)

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 18.39 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(↓) / DXY(↑) / VIX(↓)
- **판정:** **TRANSITION / MIXED | Flow:  (Flow Weak)**
- **근거:** Macro Narrative=UNKNOWN_TRANSITION / Policy=MIXED / Credit=WATCH

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↓) / DXY(↑) / VIX(↓)
- **현실(FCI):** value=-0.496 / level=EASY (완화) / update=low-frequency | as of: 2026-10-27 (latest available)
- **유인(Real Rates):** value=2.660 / level=RESTRICTIVE (유인↓) / dir(→) | as of: 2026-10-27 (latest available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI는 저빈도 금융환경 프록시로 level 중심 해석, Real Rates는 영업일 기준 변화 방향을 함께 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↓) / DXY(↑) / VIX(↓)
- **Policy Bias: MIXED (혼조) (WEAK, score=+0.5) | REAL_RATEΔ +0.000 / FCI value=-0.496 (low-frequency) / DXYΔ +0.150 / US10YΔ -0.002**
- **Expectations: dict received.**

- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리/달러/변동성 신호가 완전히 정렬되지 않음
- **한줄요약 ~~** 구조=MIXED (혼조)(WEAK)는 참고, 가격=POLICY MIXED (정책 신호 혼조) 중심 → 최종 POLICY MIXED (정책 신호 혼조)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-10-21 (FRED latest)
- **NET_LIQ level:** 5801601.8
- **TGA level:** 952002.0
- **RRP level:** 0.237
- **방향(전일 대비):** TGA(↑) / RRP(↑) / NET_LIQ(↓)
- **판정:** **LIQUIDITY DRAINING (유동성 흡수)**
- **근거:** Net Liquidity↓ → 시장 내 달러 여력 축소 가능
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-10-23 (FRED latest)
- **HY_OAS level:** 3.38% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↓) / -0.59%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 좁혀지는 중 → 공포 온도 완화
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↑) / LQD(↑)
- **HYG:** today 77.200 / prev 77.050 / pct 0.19%
- **LQD:** today 104.020 / prev 103.850 / pct 0.16%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Mild, -0.04%)** → 완화 기대 강화
- DXY **(Mild, +0.15%)** → 달러 강세/신흥국 부담
- WTI **(Strong, -1.46%)** → 물가 부담 완화
- VIX **(Strong, -5.45%)** → 심리 개선/리스크온
- 원/달러(USDKRW) **(Clear, -0.32%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Mild, +0.19%)** → 크레딧 위험선호↑
- LQD (IG Bond ETF) **(Mild, +0.16%)** → 우량채 강세(리스크오프 성향)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 하락(US10Y↓)** → 할인율 압박 완화 → 달러 약세(DXY↓) 유도: **위험자산(Growth/EM) 선호 심리 강화 및 유동성 환경 개선**
- **변동성 하락(VIX↓)** → 심리 개선(Risk-On): **자산군 전반의 위험 수용 여력(Risk Appetite) 회복 및 랠리 지속 가능성**
- **유가 하락(WTI↓)** → 물가 부담 완화: **실질 구매력 회복 및 긴축 압력 완화(Dovish Tilt) 가능성 시사**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### 🌊 Drift Monitor (v4)
- **정의:** 누적 흐름 + ATR 기반 강도 감지

- **SPY:** 🟡 REBOUND | Short-term: MIXED | 1D=+0.69% / 5D=-0.16% | Strength: LOW
- **WTI:** 🔴 DOWN | Short-term: SHORT UP | 1D=-0.85% / 5D=-0.87% | Strength: LOW
- **DXY:** 🟢 UP | Short-term: SHORT UP | 1D=+0.13% / 5D=+0.36% | Strength: LOW
- **GOLD:** 🔴 DOWN | Short-term: SHORT DOWN | 1D=-0.43% / 5D=-2.93% | Strength: LOW

- **Drift Score:** 6
- **State:** **⚡ STRUCTURAL DRIFT**
- **Label:** NEUTRAL
- **SEW Combo Signal:** 🟢 EARLY FLOW WITHOUT SHOCK

- **Market Drift Summary:**
  - Equity (SPY): 🟡 REBOUND / MIXED
  - Oil (WTI): 🔴 DOWN / SHORT UP
  - Dollar (DXY): 🟢 UP / SHORT UP
  - Gold (GOLD): 🔴 DOWN / SHORT DOWN

- **Drivers:**
  - SPY positive drift
  - Credit supports risk
  - Sector breadth expanding
  - Broad cyclical leadership
  - Dollar not restrictive

### ⚠ 6.5) Correlation Break Monitor
No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
No significant sector-level correlation break detected.

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 하락(VIX↓)** → 심리 안정: 리스크 수용 여력 개선
- **금리 하락(US10Y↓)** → 완화 기대/할인율 부담 완화 가능
- **달러 강세(DXY↑)** → 신흥국·원자재·원화 등 위험자산에 부담
- **유가 하락(WTI↓)** → 물가 부담 완화 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **-0.14**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** +0.05
- **Geo Momentum:** -0.19 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Israel_2023
- **Cosine Similarity Score:** 0.372
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Israel_2023: 0.372
  - Ukraine_2022: 0.321
  - Taiwan_Tension: 0.314
- **Top Drivers:**
  - VIX: z_used=-0.61 (z1d=-0.96, z5d=-0.08, raw_w=0.18, norm_w=0.14) → contrib=-0.08
  - WTI: z_used=-0.63 (z1d=-0.68, z5d=-0.57, raw_w=0.10, norm_w=0.08) → contrib=-0.05
  - ITA: z_used=+1.56 (z1d=+2.35, z5d=+0.38, raw_w=0.03, norm_w=0.02) → contrib=+0.04
  - SEA: z_used=-0.93 (z1d=+0.98, z5d=+0.84, raw_w=0.05, norm_w=0.04) → contrib=-0.04
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Israel_2023** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (EEM, FXI, VXX)
- **Extreme Country Risk:** EEM, FXI, VXX

### ⚡ 7.3) Pseudo Gamma Filter
- **정의:** 옵션 데이터 없이 시장의 감마 환경을 추론
- **주의:** Dealer Gamma Bias 숫자와 Pseudo Gamma State는 서로 다른 레이어

- **Pseudo Gamma State:** 🟡 TRANSITION
- **Dealer Gamma Bias:** 0.40 (RUN RISK / dealer gamma proxy weak)
- **Bias:** 초기 방향성 형성 / 감마 전환 구간
- **Strategy:** 포지션 확대 신중 / 초기 진입 구간

- **Drift Score:** 6 (⚡ STRUCTURAL DRIFT)
- **VIX:** 18.389999389648438
- **SEW:** STABLE / NORMAL

- **🚀 Combo Signal:** 🟢 EARLY FLOW WITHOUT SHOCK

### 🏦 Institutional Flow Engine (v2-minimal)
- **정의:** 기관성 자금이 뉴스 전에 남기는 흔적을 구조적으로 탐지

- **Raw Flow State:** **🔥 BUILDING HARD**
- **Transition State:** **TRACE_BUILDING**
- **Flow Delta:** +2 (prev=5 → current=7)
- **Persistence Days:** 4
- **Transition Note:** 기관성 흐름이 전일 대비 강화
- **Confidence:** **HIGH**
- **Action Bias:** **EARLY PREP**

- **Drift:** ⚡ STRUCTURAL DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK
- **Gamma:** 🟡 TRANSITION / 🟢 EARLY FLOW WITHOUT SHOCK
- **SEW:** STABLE / NORMAL
- **Positioning (POS_Z):** 1.21
- **Validation Score:** 4 (boost applied: +2)

- **Drivers:**
  - Drift strong
  - Gamma transition
  - No shock yet
  - Cross-asset risk participation
  - Credit confirms risk appetite
  - Leadership breadth expanding
  - Cyclical leadership over defensives

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(32.00bp) | 실질금리(2.66%) | DXY(101.96)
*(as of: RealRate: 2026-10-27 / FRED last available)*

❌ **자본이 탈출하는 곳 (Short Incentive):**
고금리(실질금리 2% 상회) 부담으로 인한 리스크 오프 신호

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** 금리↓ + 달러↑ + 유가↓ + VIX↓
- **최종 판정:** **인플레이션 압력 둔화 및 비용 감소형 안도 랠리**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Mild) / DXY(Mild) / WTI(Strong) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.986), DXY(101.960), VIX(18.39)

### 🏗️ 12) Structural Filter (v3)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↓) / DXY(↑) / GOLD(↑) / VIX(↓) / WTI(↓)
- **Meaningful Move Check:** DXY=0.14733477013647633 / GOLD=0.7609970494064519 / US10Y=-0.040093325484193344 / VIX=-5.449878312142642 / WTI=-1.4621812297089092
- **판정:** **NEUTRAL**
- **근거:** 글로벌 매크로 구조의 특이 신호가 감지되지 않음



### 12.5) Growth Sustainability Filter [SHADOW]
- **Score:** -2
- **Label:** LATE_CYCLE_STRAIN
- **Demand Proxy:** 1
- **Financing:** 0
- **Energy Burden:** -2
- **Policy Capacity:** -1
- **Strategic Interpretation:** Growth momentum is weakening and the cycle is showing strain. Financing, demand, or policy support is not strong enough.
- **Input Check:** US10Y=4.986000061035156, RealYield=2.66, T10Y2Y=0.32, WTI=101.76000213623047, DXY=101.95999908447266, LiquidityDir=DOWN, CreditCalm=True, HY_OAS=3.38, DriftLabel=NEUTRAL, FredAsof=2026-10-26

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.




### 12.8) Positioning Stress Filter [SHADOW]

- **Score:** -1
- **Label:** SQUEEZE_RISK
- **Strategic Interpretation:** Positioning is stretched and vulnerable to squeeze-driven reversals.

**Positioning Notes**
- Term Structure: VIX3M-VIX=1.55 → mild contango
- Short-Term Hedge: VIX9D/VIX=0.97 → neutral short-term hedge
- Gamma Structure: Positive gamma mild
- Positioning: Elevated long positioning

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.



### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** 1
- **Label:** EARLY_ROTATION
- **Strategic Interpretation:** Participation is emerging, but confirmation remains limited.
- **Breadth / Participation:** -3
- **Breadth Note:** RSP-SPY return spread=-0.36%p → narrow cap-weight leadership
- **Nasdaq Breadth Note:** QQQE-QQQ return spread=-0.35%p → mega-cap concentrated Nasdaq rally
- **Positioning / Gamma:** 0
- **Credit Confirmation:** 2
- **Macro Participation:** 2

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.



### 12.7) Leadership Breadth Filter [SHADOW]
- **Score:** 5
- **Label:** BROAD_LEADERSHIP
- **Strategic Interpretation:** Leadership is broadening across sectors, confirming healthier market participation.

**Leadership Notes**
- QQQ-SPY spread=0.40%p → growth leadership
- SMH-QQQ spread=1.63%p → semiconductor participation strong
- SOXX-QQQ spread=1.74%p → SOX proxy confirms chip breadth
- IWM-SPY spread=-0.26%p → small-cap participation neutral
- XLF-SPY spread=-0.50%p → sector diffusion weak
- XLI-SPY spread=0.71%p → sector diffusion positive
- XLY-SPY spread=0.32%p → sector diffusion positive

📌 Shadow Note: This filter checks whether leadership is broadening beyond mega-cap tech/AI. No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.


### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: MIXED (혼조) (WEAK, score=+0.5) | REAL_RATEΔ +0.000 / FCI value=-0.496 (low-frequency) / DXYΔ +0.150 / US10YΔ -0.002 (정상)
- **Sentiment (Fear&Greed):** 37.83146747101575 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** DOWN (MID)
- **Structural Regime:** UNKNOWN_TRANSITION
- **Operational Phase:** TRANSITION / MIXED (Cap: 65)
- **Macro Tilt:** +0
- **Drift:** ⚡ STRUCTURAL DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK
- **Drift Score:** 6
- **Flow Score:** 7
- **Flow Continuity:** CONFIRMED_FLOW → 🔥 BUILDING HARD (FLOW_PERSISTENCE, tilt=+1)
- **Flow Regime Tilt:** +4 / Flow-Gamma Tilt: +2

- **🎯 Final Risk Action:** **HOLD**
- **Risk Budget (0~100):** **60**
- **Narrative:** 구조=MIXED / 심리=NEUTRAL / 유동성=감소/중간 / 크레딧=안정 / 드리프트=⚡ STRUCTURAL DRIFT (NEUTRAL) / 수급=1.21 → Phase=TRANSITION / MIXED

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `MIXED` | **Price(Regime):** `TRANSITION / MIXED` | **Bucket:** `MIXED` | **VIX:** `18.39`
- **Positioning Data:** Z-Score: `1.21` (>1.8 시 Run) | Gamma: `0.40` (<0.5 시 Run) | CTA: `0.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v3.2)
- **정의:** 13번 Risk Budget 실행 브레이크 레이어
- **추가 이유:** 전략 판단(13) 이후 실제 진입 강도를 조절하기 위함

- **Base Risk Budget (13):** 60
- **VIX Level:** 18.39 (NORMAL) | **Change:** -5.45%
- **Positioning Layer:** ⚠️ Negative Gamma(0.40), Bearish CTA(0.0)
- **Brake Drivers:** ⚠️ Negative Gamma, Bearish CTA

- **📊 Recommended Exposure:** **48%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **NEUTRAL**
- **Duration Tilt:** **LONG DURATION FAVORED**
- **Cyclical vs Defensive:** **NEUTRAL**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** LONG DURATION FAVORED
- **Inflation Factor:** DISINFLATION
- **USD Factor:** NEUTRAL
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.3)

**Context:** phase=TRANSITION / MIXED / T10Y2Y=0.32 (MODERATE STEEP) / VIX=18.39 (VOLATILITY NORMAL) / liquidity=DOWN-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM

**Macro Profile:** GROWTH_SCARE
**Macro Inputs Debug:** phase=TRANSITION / MIXED / us10y_pct=-0.04% / dxy_pct=+0.15% / wti_pct=-1.46% / vix=18.39 / liq_easy=False / liq_tight=True / credit_calm=True / flow_score=7

**Flow Overlay:** flow_score=7 / flow_state=🔥 BUILDING HARD / drift_label=NEUTRAL / gamma=🟡 TRANSITION
**Flow Notes:** NEUTRAL + FLOW ACTIVE → XLK/XLI 소폭 가점 | Gamma TRANSITION → 초기 리더 소폭 가점

**Overweight:** Health Care, Consumer Staples, Utilities, Energy, Financials, Materials

**Underweight:** Technology, Real Estate, Communication Services, Consumer Discretionary, Industrials

**Scoreboard:**
- Health Care: +2.5  (+2 LIQ, +1.5 PHASE, +2 MOM, = +2.5)
- Consumer Staples: +1.9  (+2 LIQ, +1.5 PHASE, +1 MOM, = +1.9)
- Utilities: +1.0  (+1 LIQ, +0.5 PHASE, +1 MOM, = +1.0)
- Energy: +0.8  (+2 MOM, = +0.8)
- Financials: +0.7  (+2 CURVE, -0.5 PHASE, = +0.7)
- Materials: +0.4  (+1 MOM, = +0.4)
- Industrials: -0.0  (+1 CURVE, -0.5 PHASE, +0.5 FLOW, -1 MOM, = -0.0)
- Consumer Discretionary: -0.4  (-1 LIQ, -0.5 PHASE, +1 MOM, = -0.4)
- Communication Services: -0.6  (-2 MOM, = -0.6)
- Real Estate: -0.7  (-1.5 LIQ, = -0.7)
- Technology: -0.8  (-2 LIQ, +1 FLOW, = -0.8)

**Rationale (Why the score exists: 섹터 점수의 핵심 드라이버)**
- OW Health Care: +2: 유동성 긴축 → 안정적 현금흐름 선호
- OW Health Care: +1.5: Growth Scare → 퀄리티/방어 선호
- OW Consumer Staples: FLOW_WEAK → 이론상 우호하나 실제 자금 유입 확인 부족
- OW Consumer Staples: +2: 유동성 긴축 → 방어적 필수소비 선호
- OW Consumer Staples: +1.5: Growth Scare → 경기방어 필수소비 선호
- OW Utilities: +1: 유동성 긴축 → 방어주 버퍼
- OW Utilities: +0.5: Growth Scare → 금리 하락 시 방어주 일부 우호
- OW Energy: TACTICAL_MOMENTUM_ONLY → 거시 근거 약하지만 단기 리더십 존재
- OW Energy: +2: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- UW Technology: +0.5: Flow Overlay → 초기 흐름에서 성장주 선행 반응
- UW Technology: -2: 유동성 긴축 → 고밸류에이션 부담
- UW Real Estate: -1.5: 유동성 긴축 → 조달비용 상승 부담

**Regime Controller:**
- DISLOCATION (avg_divergence=-0.14, dispersion=1.73)
- Correlation Break: False / Type=NONE
- Interpretation: 섹터별 괴리가 큰 불안정 장세 → 포지션 축소와 리더 섹터 검증 필요

**Divergence / Classification Monitor (Theory vs Flow alignment: 이론과 실제 자금흐름 정렬 여부)**
- Health Care: HIGH_CONVICTION_ALIGNED (theory=+3.5, flow=+1.4, final=+2.5)
- Consumer Staples: FLOW_WEAK (theory=+3.5, flow=+0.7, final=+1.9)
- Energy: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+1.4, final=+0.8)
- Materials: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+0.7, final=+0.4)

### 💰 18.5) Tactical Asset Allocation (Execution Weight)
- **Strategic Exposure (15):** **48.0%** → **Regime Adjusted:** **48.0%**
- **Exposure Override:** DISLOCATION → Sector Weight Only (No Exposure Change)

| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |
| :--- | :---: | :---: | :---: | :--- |
| Health Care | +2.5 | ALIGNED | **5.1%** | HOLD |
| Consumer Staples | +1.9 | NEGATIVE_DIVERGENCE | **5.0%** | HOLD |
| Utilities | +1.0 | ALIGNED | **1.1%** | HOLD |
| Energy | +0.8 | POSITIVE_DIVERGENCE | **3.2%** | HOLD |
| Materials | +0.4 | POSITIVE_DIVERGENCE | **1.6%** | HOLD |
| **Cash & Hedge** | - | - | **84.0%** | DEFENSIVE |

- **Allocation Check:** Sector Weights + Cash = **100.0%**
- **Regime Cap Profile:** GROWTH_SCARE
- **Regime Cap Applied:** None
- **Strategic Cash (15):** 52.0%
- **Tactical Reserve (Cap / Unallocated):** 32.0%


**Deleveraging Priority Preview:**
- 기준: Divergence → Momentum → Score → Current Weight
1. Consumer Staples (priority_score=2.33, score=1.87, weight=5.0%, div=NEGATIVE_DIVERGENCE, mom=1)
2. Utilities (priority_score=-1.5, score=0.99, weight=1.1%, div=ALIGNED, mom=1)
3. Materials (priority_score=-3.19, score=0.38, weight=1.6%, div=POSITIVE_DIVERGENCE, mom=1)
4. Energy (priority_score=-4.38, score=0.76, weight=3.2%, div=POSITIVE_DIVERGENCE, mom=2)
5. Health Care (priority_score=-7.71, score=2.48, weight=5.1%, div=ALIGNED, mom=2)

**Leveraging Priority Preview:**
- 기준: Score → Momentum → Positive Divergence
1. Health Care (priority_score=7.48, score=2.48, weight=5.1%, div=ALIGNED, mom=2)
2. Energy (priority_score=4.76, score=0.76, weight=3.2%, div=POSITIVE_DIVERGENCE, mom=2)
3. Materials (priority_score=2.88, score=0.38, weight=1.6%, div=POSITIVE_DIVERGENCE, mom=1)
4. Utilities (priority_score=2.49, score=0.99, weight=1.1%, div=ALIGNED, mom=1)
5. Consumer Staples (priority_score=0.37, score=1.87, weight=5.0%, div=NEGATIVE_DIVERGENCE, mom=1)
- **Divergence Adjustment:** Consumer Staples penalized in weight sizing

### 🧬 19) Execution Layer (ETF Mapping)

| Sector | ETF | Weight | Action | Divergence | Classification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| Consumer Staples | XLP | 5.0% | WATCHLIST_SMALL | NEGATIVE_DIVERGENCE | FLOW_WEAK |
| Energy | XLE | 3.2% | TACTICAL_ONLY | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Health Care | XLV | 5.1% | ACCUMULATE | ALIGNED | HIGH_CONVICTION_ALIGNED |
| Materials | XLB | 1.6% | TACTICAL_ONLY | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Utilities | XLU | 1.1% | MICRO | ALIGNED | ALIGNED |


### 🧬 19.5) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Execution Notes:**
- Flow building → selective expansion allowed if risk controls remain stable.

**Preferred Company Traits:**
- High Free Cash Flow generators
- Net cash or low leverage balance sheets
- Stable margins / pricing power
- Low to mid beta exposure
- RAROC-friendly profile
- High-conviction leaders with cross-asset confirmation

**Risk Control / Avoid:**
- Negative FCF / cash-burn models
- High leverage / refinancing-dependent names
- Long-duration, high-multiple growth

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.3463447586331755
- **Z-Score (5d):** 1.6706545281238365

### EEM
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.20013173364080503
- **Z-Score (5d):** -0.8543354618106035

### EIS
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.5475055994299967
- **Z-Score (5d):** 0.8449931418368413

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.3514163985694314
- **Z-Score (5d):** 0.723742808940317

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.15223590034055107
- **Z-Score (5d):** -0.4947385667440386

### FXI
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 0.778684656402322
- **Z-Score (5d):** -1.1912054380641626

### GLD
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.22417088401676682
- **Z-Score (5d):** -0.9576773683933053

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.0272211874642492
- **Z-Score (5d):** -0.3136299406836279

### VXX
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.8885847900392904
- **Z-Score (5d):** 1.2127203171382543
