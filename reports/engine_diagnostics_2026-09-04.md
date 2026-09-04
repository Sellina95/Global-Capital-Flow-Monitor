# ENGINE DIAGNOSTICS
**Date:** 2026-09-04
**Data as of:** 2026-09-03

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: ✅ STABLE**
> **판단 요약: 구조-가격-수급 정렬 / 실시간 이상징후 없음 / 데드맨 정상**
### 🎯 Exposure Framework
- **Base Exposure (전략 기준): 80%**
- **Final Exposure (실행 기준): 80%**

- **Portfolio Stance:** INCREASE / 80%

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
  - Leadership Breadth → **MEGA_CAP_SQUEEZE_RISK** (Leadership is heavily concentrated in mega-cap/AI-related names, increasing squeeze and reversal risk.)
  - Positioning Stress → **STABLE_BUT_CROWDED** (Positioning is becoming crowded, but market structure remains stable.)

## 🎯 Final Decision (War Room Override)
- **Final Action:** **INCREASE**
- **Final Exposure:** **80%**
- **Base Context:** phase=RISK-ON / LIQUIDITY / narrative=INCREASE / base_exposure=80%
- **SEW:** STABLE / NORMAL
- **Divergence:** ALIGNED / **STAY (포지션 유지)**
- **Drift:** ⚡ STRUCTURAL DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK / score=7
- **Flow:** ⚡ BUILDING / score=6
- **Gamma:** 🟡 POSITIVE-TRANSITION
- **Tactical Action:** HOLD / NONE / LOW
- **Positioning:** pos_z=1.79
- **Warning Score:** 0 (No warning)
- **Tactical Why:** No actionable alignment
- **Why:** SEW STABLE → 실시간 이상징후 없음 → Divergence ALIGNED → 구조·가격·수급 정렬 → Narrative Action=INCREASE 반영 → Tactical=HOLD / Flow=⚡ BUILDING(6) / Drift=⚡ STRUCTURAL DRIFT(7) / Gamma=🟡 POSITIVE-TRANSITION → Tactical HOLD/MONITOR → 최종판단 변경 없음

### 🚩 Market Regime Status
- **국면 전환 감지:** 🚨 **RISK-ON (부분 정렬)** → **RISK-ON / LIQUIDITY**
- **Structural Regime:** **POLICY_EASING**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.762  (-0.71% vs 4.796)
- **달러 인덱스**: 99.000  (-0.56% vs 99.560)
- **WTI 유가**: 91.300  (+0.32% vs 91.010)
- **변동성 지수 (VIX)**: 14.320 (-5.79% vs 15.200)
- **원/달러 환율**: 1358.390  (-1.05% vs 1372.860)

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 14.32 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(↓) / DXY(↓) / VIX(↓)
- **판정:** **RISK-ON / LIQUIDITY | Flow:  (Flow Weak)**
- **근거:** 금리↓ + 달러↓ + VIX↓ → 위험자산 선호/유동성 기대

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↓) / DXY(↓) / VIX(↓)
- **현실(FCI):** value=-0.558 / level=EASY (완화) / update=low-frequency | as of: 2026-09-04 (latest available)
- **유인(Real Rates):** value=2.450 / level=RESTRICTIVE (유인↓) / dir(→) | as of: 2026-09-04 (latest available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대는 완화지만 FCI 압박 또는 실질금리 유인↓ → 리스크자산 지속성 약화 리스크
- **Note:** FCI는 저빈도 금융환경 프록시로 level 중심 해석, Real Rates는 영업일 기준 변화 방향을 함께 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↓) / DXY(↓) / VIX(↓)
- **Policy Bias: EASING (완화) (MODERATE, score=-1.5) | REAL_RATEΔ +0.000 / FCI value=-0.558 (low-frequency) / DXYΔ -0.560 / US10YΔ -0.034**
- **Expectations: dict received.**

- **판정:** **POLICY EASING (완화)**
- **근거:** 금리↓ + 달러↓ (+VIX 안정) → 완화 쪽
- **한줄요약 ~~** 구조=EASING (완화)(MODERATE)는 참고, 가격=POLICY EASING (완화) 중심 → 최종 POLICY EASING (완화)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-09-02 (FRED latest)
- **NET_LIQ level:** 5769268.5
- **TGA level:** 967935.0
- **RRP level:** 0.525
- **방향(전일 대비):** TGA(↑) / RRP(↓) / NET_LIQ(↓)
- **판정:** **LIQUIDITY DRAINING (유동성 흡수)**
- **근거:** Net Liquidity↓ → 시장 내 달러 여력 축소 가능
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-09-02 (FRED latest)
- **HY_OAS level:** 2.66% → **COOL (낮은 공포)**
- **방향(전일 대비):** HY_OAS(↑) / +0.38%
- **판정:** **CREDIT CALM**
- **근거:** HY 스프레드 낮음 → 크레딧 스트레스 제한 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↑) / LQD(↑)
- **HYG:** today 79.210 / prev 79.110 / pct 0.13%
- **LQD:** today 105.500 / prev 105.350 / pct 0.14%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, -0.71%)** → 완화 기대 강화
- DXY **(Strong, -0.56%)** → 달러 약세/리스크 선호
- WTI **(Mild, +0.32%)** → 인플레 재자극 가능성
- VIX **(Strong, -5.79%)** → 심리 개선/리스크온
- 원/달러(USDKRW) **(Strong, -1.05%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Mild, +0.13%)** → 크레딧 위험선호↑
- LQD (IG Bond ETF) **(Mild, +0.14%)** → 우량채 강세(리스크오프 성향)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 하락(US10Y↓)** → 할인율 압박 완화 → 달러 약세(DXY↓) 유도: **위험자산(Growth/EM) 선호 심리 강화 및 유동성 환경 개선**
- **변동성 하락(VIX↓)** → 심리 개선(Risk-On): **자산군 전반의 위험 수용 여력(Risk Appetite) 회복 및 랠리 지속 가능성**
- **유가 상승(WTI↑)** → 기대 인플레이션 자극: **제조/운송업 비용 부담 가중 및 중앙은행의 긴축 유지 명분 강화**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### 🌊 Drift Monitor (v4)
- **정의:** 누적 흐름 + ATR 기반 강도 감지

- **SPY:** 🟢 UP | Short-term: SHORT DOWN | 1D=+1.04% / 5D=+0.26% | Strength: LOW
- **WTI:** 🟡 PULLBACK | Short-term: MIXED | 1D=-0.49% / 5D=+8.93% | Strength: MEDIUM
- **DXY:** 🟡 REBOUND | Short-term: SHORT UP | 1D=+0.08% / 5D=-0.62% | Strength: LOW
- **GOLD:** 🟢 UP | Short-term: SHORT DOWN | 1D=+0.44% / 5D=+0.75% | Strength: LOW

- **Drift Score:** 7
- **State:** **⚡ STRUCTURAL DRIFT**
- **Label:** NEUTRAL
- **SEW Combo Signal:** 🟢 EARLY FLOW WITHOUT SHOCK

- **Market Drift Summary:**
  - Equity (SPY): 🟢 UP / SHORT DOWN
  - Oil (WTI): 🟡 PULLBACK / MIXED
  - Dollar (DXY): 🟡 REBOUND / SHORT UP
  - Gold (GOLD): 🟢 UP / SHORT DOWN

- **Drivers:**
  - SPY positive drift
  - Sector breadth expanding
  - Strong SPY continuation
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
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **-0.28**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** -0.20
- **Geo Momentum:** -0.09 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Iran_Crisis_2020
- **Cosine Similarity Score:** 0.005
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Iran_Crisis_2020: 0.005
  - Red_Sea: -0.116
  - Ukraine_2022: -0.118
- **Top Drivers:**
  - KR10Y_SPREAD: z_used=-1.67 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.10
  - DE10Y_SPREAD: z_used=-1.67 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=-0.08
  - JP10Y_SPREAD: z_used=-1.67 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=-0.08
  - GOLD: z_used=+0.74 (z1d=+1.71, z5d=-0.71, raw_w=0.12, norm_w=0.09) → contrib=+0.07
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Iran_Crisis_2020** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** No (BND, EEM, EIS, EMB, EWJ, FXI, GLD, SPY, VXX)

### ⚡ 7.3) Pseudo Gamma Filter
- **정의:** 옵션 데이터 없이 시장의 감마 환경을 추론
- **주의:** Dealer Gamma Bias 숫자와 Pseudo Gamma State는 서로 다른 레이어

- **Pseudo Gamma State:** 🟡 POSITIVE-TRANSITION
- **Dealer Gamma Bias:** 0.71 (NEUTRAL / transition zone)
- **Bias:** VIX는 안정적이나 Drift가 형성 중
- **Strategy:** 초기 방향성 관찰 / 과도한 추격 금지

- **Drift Score:** 7 (⚡ STRUCTURAL DRIFT)
- **VIX:** 14.31999969482422
- **SEW:** STABLE / NORMAL

- **🚀 Combo Signal:** 🟢 EARLY FLOW WITHOUT SHOCK

### 🏦 Institutional Flow Engine (v2-minimal)
- **정의:** 기관성 자금이 뉴스 전에 남기는 흔적을 구조적으로 탐지

- **Raw Flow State:** **⚡ BUILDING**
- **Transition State:** **CONFIRMED_FLOW**
- **Flow Delta:** +0 (prev=6 → current=6)
- **Persistence Days:** 6
- **Transition Note:** 기관성 흐름이 높은 강도로 확인
- **Confidence:** **MEDIUM-HIGH**
- **Action Bias:** **WATCHLIST**

- **Drift:** ⚡ STRUCTURAL DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK
- **Gamma:** 🟡 POSITIVE-TRANSITION / 🟢 EARLY FLOW WITHOUT SHOCK
- **SEW:** STABLE / NORMAL
- **Positioning (POS_Z):** 1.79
- **Validation Score:** 3 (boost applied: +2)

- **Drivers:**
  - Drift strong
  - Gamma transition
  - No shock yet
  - Positioning somewhat stretched
  - Cross-asset risk participation
  - Leadership breadth expanding
  - Cyclical leadership over defensives

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(43.00bp) | 실질금리(2.45%) | DXY(99.00)
*(as of: RealRate: 2026-09-04 / FRED last available)*

❌ **자본이 탈출하는 곳 (Short Incentive):**
고금리(실질금리 2% 상회) 부담으로 인한 리스크 오프 신호

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** 금리↓ + 달러↓ + 유가↑ + VIX↓
- **최종 판정:** **금리·달러 안정에 따른 전형적인 '위험자산 선호(Risk-On)'**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Strong) / WTI(Mild) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.762), DXY(99.000), VIX(14.32)

### 🏗️ 12) Structural Filter (v3)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↓) / DXY(↓) / GOLD(↑) / VIX(↓) / WTI(↑)
- **Meaningful Move Check:** DXY=-0.5624724511108896 / GOLD=2.87200596006657 / US10Y=-0.7089224325336567 / VIX=-5.789474509759621 / WTI=0.31864730108809425
- **판정:** **NEUTRAL**
- **근거:** 글로벌 매크로 구조의 특이 신호가 감지되지 않음



### 12.5) Growth Sustainability Filter [SHADOW]
- **Score:** -1
- **Label:** LATE_CYCLE_STRAIN
- **Demand Proxy:** 1
- **Financing:** 0
- **Energy Burden:** -1
- **Policy Capacity:** -1
- **Strategic Interpretation:** Growth momentum is weakening and the cycle is showing strain. Financing, demand, or policy support is not strong enough.
- **Input Check:** US10Y=4.76200008392334, RealYield=2.45, T10Y2Y=0.43, WTI=91.3000030517578, DXY=99.0, LiquidityDir=DOWN, CreditCalm=True, HY_OAS=2.66, DriftLabel=NEUTRAL, FredAsof=2026-09-03

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.




### 12.8) Positioning Stress Filter [SHADOW]

- **Score:** 1
- **Label:** STABLE_BUT_CROWDED
- **Strategic Interpretation:** Positioning is becoming crowded, but market structure remains stable.

**Positioning Notes**
- Term Structure: VIX3M-VIX=3.10 → healthy contango / stable structure
- Short-Term Hedge: VIX9D/VIX=0.82 → calm front-end hedge
- Gamma Structure: Positive gamma mild
- Positioning: Elevated long positioning

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.



### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** 2
- **Label:** EARLY_ROTATION
- **Strategic Interpretation:** Participation is emerging, but confirmation remains limited.
- **Breadth / Participation:** -3
- **Breadth Note:** RSP-SPY return spread=-0.38%p → narrow cap-weight leadership
- **Nasdaq Breadth Note:** QQQE-QQQ return spread=-0.31%p → mega-cap concentrated Nasdaq rally
- **Positioning / Gamma:** 1
- **Credit Confirmation:** 2
- **Macro Participation:** 2

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.



### 12.7) Leadership Breadth Filter [SHADOW]
- **Score:** -3
- **Label:** MEGA_CAP_SQUEEZE_RISK
- **Strategic Interpretation:** Leadership is heavily concentrated in mega-cap/AI-related names, increasing squeeze and reversal risk.

**Leadership Notes**
- QQQ-SPY spread=0.14%p → neutral growth leadership
- SMH-QQQ spread=-0.80%p → AI/tech rally not semiconductor-broad
- SOXX-QQQ spread=-1.04%p → chip breadth lagging
- IWM-SPY spread=-0.65%p → small-cap lag, narrow leadership risk
- XLF-SPY spread=0.51%p → sector diffusion positive
- XLI-SPY spread=-0.02%p → sector diffusion neutral
- XLY-SPY spread=0.35%p → sector diffusion positive

📌 Shadow Note: This filter checks whether leadership is broadening beyond mega-cap tech/AI. No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.


### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: EASING (완화) (MODERATE, score=-1.5) | REAL_RATEΔ +0.000 / FCI value=-0.558 (low-frequency) / DXYΔ -0.560 / US10YΔ -0.034 (정상)
- **Sentiment (Fear&Greed):** 70.05044561439233 (GREED)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** DOWN (MID)
- **Structural Regime:** POLICY_EASING
- **Operational Phase:** RISK-ON / LIQUIDITY (Cap: 85)
- **Macro Tilt:** +5
- **Drift:** ⚡ STRUCTURAL DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK
- **Drift Score:** 7
- **Flow Score:** 6
- **Flow Continuity:** TRACE_BUILDING → ⚡ BUILDING (FLOW_PERSISTENCE, tilt=+1)
- **Flow Regime Tilt:** +3 / Flow-Gamma Tilt: +2

- **🎯 Final Risk Action:** **INCREASE**
- **Risk Budget (0~100):** **85**
- **Narrative:** 구조=EASING / 심리=GREED / 유동성=감소/중간 / 크레딧=안정 / 드리프트=⚡ STRUCTURAL DRIFT (NEUTRAL) / 수급=1.79 ⚠️ 수급 다소 과열 → Phase=RISK-ON / LIQUIDITY

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `EASING` | **Price(Regime):** `RISK-ON` | **Bucket:** `RISK-ON` | **VIX:** `14.32`
- **Positioning Data:** Z-Score: `1.79` (>2.2 시 Run) | Gamma: `0.71` (<0.5 시 Run) | CTA: `1.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v3.2)
- **정의:** 13번 Risk Budget 실행 브레이크 레이어
- **추가 이유:** 전략 판단(13) 이후 실제 진입 강도를 조절하기 위함

- **Base Risk Budget (13):** 85
- **VIX Level:** 14.32 (NORMAL) | **Change:** -5.79%
- **Positioning Layer:** ⚠️ Elevated Positioning Heat(1.79)
- **Brake Drivers:** ⚠️ Elevated Positioning Heat

- **📊 Recommended Exposure:** **80%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **GROWTH TILT**
- **Duration Tilt:** **LONG DURATION FAVORED**
- **Cyclical vs Defensive:** **CYCLICAL FAVORED**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** LONG DURATION FAVORED
- **Inflation Factor:** NEUTRAL
- **USD Factor:** USD EASING
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.3)

**Context:** phase=RISK-ON / LIQUIDITY / T10Y2Y=0.43 (MODERATE STEEP) / VIX=14.32 (VOLATILITY CALM) / liquidity=DOWN-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM

**Macro Profile:** DISINFLATION_RISK_ON
**Macro Inputs Debug:** phase=RISK-ON / LIQUIDITY / us10y_pct=-0.71% / dxy_pct=-0.56% / wti_pct=+0.32% / vix=14.32 / liq_easy=False / liq_tight=True / credit_calm=True / flow_score=6

**Flow Overlay:** flow_score=6 / flow_state=⚡ BUILDING / drift_label=NEUTRAL / gamma=🟡 POSITIVE-TRANSITION
**Flow Notes:** NEUTRAL + FLOW ACTIVE → XLK/XLI 소폭 가점 | Gamma POSITIVE → 리더 섹터 가점

**Overweight:** Financials, Consumer Staples, Health Care, Technology, Energy, Communication Services

**Underweight:** Industrials, Consumer Discretionary, Real Estate, Utilities

**Scoreboard:**
- Financials: +1.4  (+2 CURVE, +1 MOM, = +1.4)
- Consumer Staples: +1.2  (+2 LIQ, = +1.2)
- Health Care: +1.2  (+2 LIQ, = +1.2)
- Technology: +1.1  (+2 VOL, -2 LIQ, +1.5 PHASE, +1.5 FLOW, = +1.1)
- Energy: +0.6  (+2 MOM, = +0.6)
- Communication Services: +0.3  (+0.5 PHASE, = +0.3)
- Utilities: -0.3  (-1 VOL, +1 LIQ, -0.5 PHASE, = -0.3)
- Consumer Discretionary: -1.4  (+1 VOL, -1 LIQ, +1 PHASE, -1 MOM, = -1.4)
- Real Estate: -1.4  (-1.5 LIQ, -1 MOM, = -1.4)
- Industrials: -1.5  (+1 CURVE, +1 FLOW, -2 MOM, = -1.5)

**Rationale (Why the score exists: 섹터 점수의 핵심 드라이버)**
- OW Financials: FLOW_WEAK → 이론상 우호하나 실제 자금 유입 확인 부족
- OW Financials: +2: 완만한 스티프닝(0.43) → 예대마진 개선
- OW Financials: +1: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- OW Consumer Staples: FLOW_WEAK → 이론상 우호하나 실제 자금 유입 확인 부족
- OW Consumer Staples: +2: 유동성 긴축 → 방어적 필수소비 선호
- OW Health Care: FLOW_WEAK → 이론상 우호하나 실제 자금 유입 확인 부족
- OW Health Care: +2: 유동성 긴축 → 안정적 현금흐름 선호
- OW Technology: +2: VOLATILITY CALM → 성장주 베팅 유효 (absolute mode: VIX 14.3)
- OW Technology: +1.5: Disinflation Risk-On → 성장주/장기 듀레이션 우호
- UW Industrials: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Industrials: +1: 완만한 스티프닝(0.43) → 성장 기대 반영
- UW Industrials: +0.5: Flow Overlay → 경기민감 확인용 가점

**Regime Controller:**
- BALANCED (avg_divergence=-0.72, dispersion=1.19)
- Correlation Break: False / Type=NONE
- Interpretation: 디스인플레이션 리스크온 / 성장주·소비 베타 우호

**Divergence / Classification Monitor (Theory vs Flow alignment: 이론과 실제 자금흐름 정렬 여부)**
- Financials: FLOW_WEAK (theory=+2.0, flow=+0.7, final=+1.4)
- Consumer Staples: FLOW_WEAK (theory=+2.0, flow=+0.0, final=+1.2)
- Health Care: FLOW_WEAK (theory=+2.0, flow=+0.0, final=+1.2)
- Energy: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+1.4, final=+0.6)
- Materials: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Consumer Discretionary: THEORY_TRAP (theory=+1.0, flow=-0.7, final=-1.4)
- Real Estate: AVOID (theory=-1.5, flow=-0.7, final=-1.4)
- Industrials: THEORY_TRAP (theory=+1.0, flow=-1.1, final=-1.5)

### 💰 18.5) Tactical Asset Allocation (Execution Weight)
- **Strategic Exposure (15):** **80.0%** → **Regime Adjusted:** **80.0%**
- **Exposure Override:** BALANCED → Sector Weight Only (No Exposure Change)

| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |
| :--- | :---: | :---: | :---: | :--- |
| Financials | +1.4 | NEGATIVE_DIVERGENCE | **10.0%** | SMALL ADJUST |
| Consumer Staples | +1.2 | NEGATIVE_DIVERGENCE | **12.9%** | SMALL ADJUST |
| Health Care | +1.2 | NEGATIVE_DIVERGENCE | **12.9%** | SMALL ADJUST |
| Technology | +1.1 | ALIGNED | **10.0%** | NEW |
| Energy | +0.6 | POSITIVE_DIVERGENCE | **11.5%** | HOLD |
| Communication Services | +0.3 | ALIGNED | **5.9%** | NEW |
| **Cash & Hedge** | - | - | **36.8%** | DEFENSIVE |

- **Allocation Check:** Sector Weights + Cash = **100.0%**
- **Regime Cap Profile:** DISINFLATION_RISK_ON
- **Participation / Quality Cap Applied:**
  - Financials: 14.9% → 10.0% (-4.9%)
  - Technology: 20.3% → 10.0% (-10.3%)
  - Energy: 13.0% → 10.0% (-3.0%)
- **Strategic Cash (15):** 20.0%
- **Tactical Reserve (Cap / Unallocated):** 16.8%


**Deleveraging Priority Preview:**
- 기준: Divergence → Momentum → Score → Current Weight
1. Consumer Staples (priority_score=3.75, score=1.2, weight=12.9%, div=NEGATIVE_DIVERGENCE, mom=0)
2. Health Care (priority_score=3.75, score=1.2, weight=12.9%, div=NEGATIVE_DIVERGENCE, mom=0)
3. Financials (priority_score=2.31, score=1.38, weight=10.0%, div=NEGATIVE_DIVERGENCE, mom=1)
4. Communication Services (priority_score=-0.17, score=0.33, weight=5.9%, div=ALIGNED, mom=0)
5. Technology (priority_score=-0.56, score=1.13, weight=10.0%, div=ALIGNED, mom=0)

**Leveraging Priority Preview:**
- 기준: Score → Momentum → Positive Divergence
1. Energy (priority_score=4.63, score=0.63, weight=11.5%, div=POSITIVE_DIVERGENCE, mom=2)
2. Technology (priority_score=1.13, score=1.13, weight=10.0%, div=ALIGNED, mom=0)
3. Communication Services (priority_score=0.33, score=0.33, weight=5.9%, div=ALIGNED, mom=0)
4. Financials (priority_score=-0.12, score=1.38, weight=10.0%, div=NEGATIVE_DIVERGENCE, mom=1)
5. Consumer Staples (priority_score=-1.80, score=1.2, weight=12.9%, div=NEGATIVE_DIVERGENCE, mom=0)
- **Divergence Adjustment:** Financials, Consumer Staples, Health Care penalized in weight sizing

### 🧬 19) Execution Layer (ETF Mapping)

| Sector | ETF | Weight | Action | Divergence | Classification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| Financials | XLF | 10.0% | WATCHLIST_SMALL | NEGATIVE_DIVERGENCE | FLOW_WEAK |
| Consumer Staples | XLP | 12.9% | WATCHLIST_SMALL | NEGATIVE_DIVERGENCE | FLOW_WEAK |
| Health Care | XLV | 12.9% | WATCHLIST_SMALL | NEGATIVE_DIVERGENCE | FLOW_WEAK |
| Technology | XLK | 10.0% | ADD | ALIGNED | ALIGNED |
| Energy | XLE | 11.5% | TACTICAL_ONLY | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Communication Services | XLC | 5.9% | SMALL | ALIGNED | ALIGNED |


### 🧬 19.5) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Execution Notes:**
- Flow building → selective expansion allowed if risk controls remain stable.
- Positioning heat elevated → prefer rebalancing over fresh chasing.

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
- Crowded late-entry trades

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.602902822097724
- **Z-Score (5d):** -1.1147989701949161

### EEM
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.22291278047492227
- **Z-Score (5d):** -0.0967796048643486

### EIS
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.8663080938948262
- **Z-Score (5d):** 0.3485571032573052

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.9717516728958153
- **Z-Score (5d):** -0.4866325371960661

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.2429295687493807
- **Z-Score (5d):** 0.626418581139834

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.5515956610318279
- **Z-Score (5d):** 0.024654515642617246

### GLD
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.0326418658495846
- **Z-Score (5d):** -0.8293724826167875

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.17348182103568
- **Z-Score (5d):** -0.00824027237101326

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.5913860941716699
- **Z-Score (5d):** -0.05282146351126228
