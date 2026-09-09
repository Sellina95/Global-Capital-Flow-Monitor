# ENGINE DIAGNOSTICS
**Date:** 2026-09-09
**Data as of:** 2026-09-08

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: ✅ STABLE**
> **판단 요약: 구조-가격-수급 정렬 / 실시간 이상징후 없음 / 데드맨 정상**
### 🎯 Exposure Framework
- **Base Exposure (전략 기준): 40%**
- **Final Exposure (실행 기준): 40%**

- **Portfolio Stance:** REDUCE / 40%

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
  - Leadership Breadth → **SELECTIVE_EXPANSION** (Leadership is improving selectively, but broad market confirmation remains incomplete.)
  - Positioning Stress → **STABLE_BUT_CROWDED** (Positioning is becoming crowded, but market structure remains stable.)

## 🎯 Final Decision (War Room Override)
- **Final Action:** **REDUCE**
- **Final Exposure:** **40%**
- **Base Context:** phase=RISK-ON / REFLATION / narrative=REDUCE / base_exposure=40%
- **SEW:** STABLE / NORMAL
- **Divergence:** ALIGNED / **STAY (포지션 유지)**
- **Drift:** WEAK DRIFT (노이즈 가능) / NEUTRAL / NONE / score=1
- **Flow:** NO CLEAR FLOW / score=0
- **Gamma:** 🟢 POSITIVE GAMMA
- **Tactical Action:** WAIT / 0% / LOW
- **Positioning:** pos_z=1.57
- **Warning Score:** 1 (6.6 섹터 상관관계 붕괴)
- **Tactical Why:** Risk-On environment but institutional flow not confirmed
- **Why:** SEW STABLE → 실시간 이상징후 없음 → Divergence ALIGNED → 구조·가격·수급 정렬 → Narrative Action=REDUCE 반영 → Warning Score 1 → 경미한 이상신호, 모니터링 강화 → Tactical=WAIT / Flow=NO CLEAR FLOW(0) / Drift=WEAK DRIFT (노이즈 가능)(1) / Gamma=🟢 POSITIVE GAMMA → Tactical HOLD/MONITOR → 최종판단 변경 없음

### 🚩 Market Regime Status
- **국면 전환 감지:** 🚨 **SOFT RISK-OFF (경계 강화)** → **RISK-ON / REFLATION**
- **Structural Regime:** **REFLATION**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.806  (+0.46% vs 4.784)
- **달러 인덱스**: 98.840  (-0.32% vs 99.160)
- **WTI 유가**: 93.030  (+1.69% vs 91.480)
- **변동성 지수 (VIX)**: 15.720 (+8.19% vs 14.530)
- **원/달러 환율**: 1343.570  (-0.87% vs 1355.410)

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 15.72 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(↑) / DXY(↓) / VIX(↑)
- **판정:** **RISK-ON / REFLATION | Flow:  (Flow Weak)**
- **근거:** 금리↓ + 달러↓ + VIX↓ → 위험자산 선호/유동성 기대

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↑) / DXY(↓) / VIX(↑)
- **현실(FCI):** value=-0.558 / level=EASY (완화) / update=low-frequency | as of: 2026-09-09 (latest available)
- **유인(Real Rates):** value=2.430 / level=RESTRICTIVE (유인↓) / dir(→) | as of: 2026-09-09 (latest available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI는 저빈도 금융환경 프록시로 level 중심 해석, Real Rates는 영업일 기준 변화 방향을 함께 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↑) / DXY(↓) / VIX(↑)
- **Policy Bias: MIXED (혼조) (WEAK, score=-0.5) | REAL_RATEΔ +0.000 / FCI value=-0.558 (low-frequency) / DXYΔ -0.320 / US10YΔ +0.022**
- **Expectations: dict received.**

- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리/달러/변동성 신호가 완전히 정렬되지 않음
- **한줄요약 ~~** 구조=MIXED (혼조)(WEAK)는 참고, 가격=POLICY MIXED (정책 신호 혼조) 중심 → 최종 POLICY MIXED (정책 신호 혼조)

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
- **Spread as of:** 2026-09-07 (FRED latest)
- **HY_OAS level:** 2.68% → **COOL (낮은 공포)**
- **방향(전일 대비):** HY_OAS(→) / +0.00%
- **판정:** **CREDIT CALM**
- **근거:** HY 스프레드 낮음 → 크레딧 스트레스 제한 / 방향성 제한 → 레벨 중심 해석
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(→)
- **HYG:** today 79.120 / prev 79.160 / pct -0.05%
- **LQD:** today 105.480 / prev 105.480 / pct 0.00%
- **판정:** **CREDIT STRESS ↑ (Risk-off warning)**
- **근거:** 하이일드 약세(HYG↓) + 우량채 방어(LQD→/↑) → 위험회피로 크레딧 프리미엄 재평가 가능

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, +0.46%)** → 완화 기대 약화/금리 부담
- DXY **(Clear, -0.32%)** → 달러 약세/리스크 선호
- WTI **(Strong, +1.69%)** → 인플레 재자극 가능성
- VIX **(Strong, +8.19%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Strong, -0.87%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Noise, -0.05%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Noise, +0.00%)** → 보합(방향성 제한)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 상승(US10Y↑)** → 실질 금리 압박 → 달러 강세(DXY↑) 유도: **신흥국 자본 유출 및 고밸류 성장주 할인율 부담 증가**
- **변동성 상승(VIX↑)** → 위험회피(Risk-Off) 강화: **안전 자산(Cash/USD) 선호도 급증 및 하이일드 스프레드 확대 압력**
- **유가 상승(WTI↑)** → 기대 인플레이션 자극: **제조/운송업 비용 부담 가중 및 중앙은행의 긴축 유지 명분 강화**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### 🌊 Drift Monitor (v4)
- **정의:** 누적 흐름 + ATR 기반 강도 감지

- **SPY:** 🔴 DOWN | Short-term: SHORT DOWN | 1D=-0.55% / 5D=-0.14% | Strength: LOW
- **WTI:** 🟢 UP | Short-term: SHORT DOWN | 1D=+0.97% / 5D=+4.11% | Strength: MEDIUM
- **DXY:** 🔴 DOWN | Short-term: SHORT DOWN | 1D=-0.12% / 5D=-0.95% | Strength: LOW
- **GOLD:** 🟢 UP | Short-term: SHORT UP | 1D=+0.84% / 5D=+1.91% | Strength: LOW

- **Drift Score:** 1
- **State:** **WEAK DRIFT (노이즈 가능)**
- **Label:** NEUTRAL
- **SEW Combo Signal:** NONE

- **Market Drift Summary:**
  - Equity (SPY): 🔴 DOWN / SHORT DOWN
  - Oil (WTI): 🟢 UP / SHORT DOWN
  - Dollar (DXY): 🔴 DOWN / SHORT DOWN
  - Gold (GOLD): 🟢 UP / SHORT UP

- **Drivers:**
  - Dollar not restrictive

### ⚠ 6.5) Correlation Break Monitor
No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
Correlation Break Detected:
- US10Y ↑ but XLF ↓

So What?
- 결론: **섹터 ‘공식’이 깨진 구간** → 총노출 추가 감산보다 **섹터 배분 보수화 + 리더 중심**

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 상승(VIX↑)** → 변동성 확대: 포지션 축소/헤지 수요 증가 가능
- **금리 상승(US10Y↑)** → 할인율 부담/유동성 압박 가능
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **-0.18**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** -0.21
- **Geo Momentum:** +0.04 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Iran_Crisis_2020
- **Cosine Similarity Score:** 0.000
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Iran_Crisis_2020: 0.000
  - Red_Sea: -0.069
  - Ukraine_2022: -0.085
- **Top Drivers:**
  - USDCNH: z_used=-1.09 (z1d=-1.27, z5d=-0.82, raw_w=0.18, norm_w=0.14) → contrib=-0.15
  - VIX: z_used=+1.04 (z1d=+1.26, z5d=+0.70, raw_w=0.18, norm_w=0.14) → contrib=+0.14
  - USDJPY: z_used=+2.45 (z1d=-2.08, z5d=-3.01, raw_w=0.05, norm_w=0.04) → contrib=+0.09
  - KR10Y_SPREAD: z_used=-1.48 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.09
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Iran_Crisis_2020** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** No (BND, EEM, EIS, EMB, EWJ, FXI, GLD, SPY, VXX)

### ⚡ 7.3) Pseudo Gamma Filter
- **정의:** 옵션 데이터 없이 시장의 감마 환경을 추론
- **주의:** Dealer Gamma Bias 숫자와 Pseudo Gamma State는 서로 다른 레이어

- **Pseudo Gamma State:** 🟢 POSITIVE GAMMA
- **Dealer Gamma Bias:** 0.91 (NEUTRAL / transition zone)
- **Bias:** Mean-reverting / 딜러가 변동성 흡수
- **Strategy:** 눌림 매수 / 추격 금지

- **Drift Score:** 1 (WEAK DRIFT (노이즈 가능))
- **VIX:** 15.720000267028809
- **SEW:** STABLE / NORMAL

- **🚀 Combo Signal:** 🟢 STABLE FLOW

### 🏦 Institutional Flow Engine (v2-minimal)
- **정의:** 기관성 자금이 뉴스 전에 남기는 흔적을 구조적으로 탐지

- **Raw Flow State:** **NO CLEAR FLOW**
- **Transition State:** **FLOW_BREAK**
- **Flow Delta:** -4 (prev=4 → current=0)
- **Persistence Days:** 0
- **Transition Note:** 전일 형성되던 기관성 흐름이 유지되지 못하고 소멸
- **Confidence:** **LOW**
- **Action Bias:** **IGNORE**

- **Drift:** WEAK DRIFT (노이즈 가능) / NEUTRAL / NONE
- **Gamma:** 🟢 POSITIVE GAMMA / 🟢 STABLE FLOW
- **SEW:** STABLE / NORMAL
- **Positioning (POS_Z):** 1.57
- **Validation Score:** 0 (boost applied: +0)

- **Drivers:**
  - No shock yet
  - Positioning somewhat stretched

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(41.00bp) | 실질금리(2.43%) | DXY(98.84)
*(as of: RealRate: 2026-09-09 / FRED last available)*

❌ **자본이 탈출하는 곳 (Short Incentive):**
고금리(실질금리 2% 상회) 부담으로 인한 리스크 오프 신호

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** 금리↑ + 달러↓ + 유가↑ + VIX↑
- **최종 판정:** **비용 상승형 물가 부담 및 경기 둔화 우려 반영**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Clear) / WTI(Strong) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.806), DXY(98.840), VIX(15.72)

### 🏗️ 12) Structural Filter (v3)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↓) / GOLD(↓) / VIX(↑) / WTI(↑)
- **Meaningful Move Check:** DXY=-0.3227181448169207 / GOLD=-0.8104181662061036 / US10Y=0.4598727670061374 / VIX=8.189955649877206 / WTI=1.694354356673514
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
- **Input Check:** US10Y=4.806000232696533, RealYield=2.43, T10Y2Y=0.41, WTI=93.02999877929688, DXY=98.83999633789062, LiquidityDir=DOWN, CreditCalm=True, HY_OAS=2.68, DriftLabel=NEUTRAL, FredAsof=2026-09-08

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.




### 12.8) Positioning Stress Filter [SHADOW]

- **Score:** 1
- **Label:** STABLE_BUT_CROWDED
- **Strategic Interpretation:** Positioning is becoming crowded, but market structure remains stable.

**Positioning Notes**
- Term Structure: VIX3M-VIX=2.67 → healthy contango / stable structure
- Short-Term Hedge: VIX9D/VIX=0.94 → calm front-end hedge
- Gamma Structure: Positive gamma mild
- Positioning: Elevated long positioning

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.



### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** 2
- **Label:** EARLY_ROTATION
- **Strategic Interpretation:** Participation is emerging, but confirmation remains limited.
- **Breadth / Participation:** -3
- **Breadth Note:** RSP-SPY return spread=-0.49%p → narrow cap-weight leadership
- **Nasdaq Breadth Note:** QQQE-QQQ return spread=-0.72%p → mega-cap concentrated Nasdaq rally
- **Positioning / Gamma:** 1
- **Credit Confirmation:** 2
- **Macro Participation:** 2

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.



### 12.7) Leadership Breadth Filter [SHADOW]
- **Score:** 3
- **Label:** SELECTIVE_EXPANSION
- **Strategic Interpretation:** Leadership is improving selectively, but broad market confirmation remains incomplete.

**Leadership Notes**
- QQQ-SPY spread=0.47%p → growth leadership
- SMH-QQQ spread=1.27%p → semiconductor participation strong
- SOXX-QQQ spread=1.73%p → SOX proxy confirms chip breadth
- IWM-SPY spread=0.10%p → small-cap participation neutral
- XLF-SPY spread=-0.83%p → sector diffusion weak
- XLI-SPY spread=0.06%p → sector diffusion neutral
- XLY-SPY spread=-0.25%p → sector diffusion neutral

📌 Shadow Note: This filter checks whether leadership is broadening beyond mega-cap tech/AI. No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.


### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: MIXED (혼조) (WEAK, score=-0.5) | REAL_RATEΔ +0.000 / FCI value=-0.558 (low-frequency) / DXYΔ -0.320 / US10YΔ +0.022 (정상)
- **Sentiment (Fear&Greed):** 64.65275107934299 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** DOWN (MID)
- **Structural Regime:** REFLATION
- **Operational Phase:** RISK-ON / REFLATION (Cap: 85)
- **Macro Tilt:** +6
- **Drift:** WEAK DRIFT (노이즈 가능) / NEUTRAL / NONE
- **Drift Score:** 1
- **Flow Score:** 0
- **Flow Continuity:** 👀 EARLY TRACE → NO CLEAR FLOW (FLOW_FADE, tilt=-3)
- **Flow Regime Tilt:** +0 / Flow-Gamma Tilt: +0

- **🎯 Final Risk Action:** **REDUCE**
- **Risk Budget (0~100):** **49**
- **Narrative:** 구조=MIXED / 심리=NEUTRAL / 유동성=감소/중간 / 크레딧=안정 / 드리프트=WEAK DRIFT (노이즈 가능) (NEUTRAL) / 수급=1.57 ⚠️ 수급 다소 과열 → Phase=RISK-ON / REFLATION

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `MIXED` | **Price(Regime):** `RISK-ON` | **Bucket:** `RISK-ON` | **VIX:** `15.72`
- **Positioning Data:** Z-Score: `1.57` (>2.2 시 Run) | Gamma: `0.91` (<0.5 시 Run) | CTA: `1.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v3.2)
- **정의:** 13번 Risk Budget 실행 브레이크 레이어
- **추가 이유:** 전략 판단(13) 이후 실제 진입 강도를 조절하기 위함

- **Base Risk Budget (13):** 49
- **VIX Level:** 15.72 (NORMAL) | **Change:** +8.19%
- **Positioning Layer:** ⚠️ Positioning Heat(1.57)
- **Brake Drivers:** ⚠️ VIX Spike, Positioning Heat

- **📊 Recommended Exposure:** **40%**

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
- **USD Factor:** USD EASING
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.3)

**Context:** phase=RISK-ON / REFLATION / T10Y2Y=0.41 (MODERATE STEEP) / VIX=15.72 (VOLATILITY NORMAL) / liquidity=DOWN-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM

**Macro Profile:** DISINFLATION_RISK_ON
**Macro Inputs Debug:** phase=RISK-ON / REFLATION / us10y_pct=+0.46% / dxy_pct=-0.32% / wti_pct=+1.69% / vix=15.72 / liq_easy=False / liq_tight=True / credit_calm=True / flow_score=0

**Flow Overlay:** flow_score=0 / flow_state=NO CLEAR FLOW / drift_label=NEUTRAL / gamma=🟢 POSITIVE GAMMA

**Overweight:** Consumer Staples, Health Care, Energy, Financials, Communication Services, Utilities

**Underweight:** Industrials, Real Estate, Technology, Consumer Discretionary

**Scoreboard:**
- Consumer Staples: +1.1  (+2 LIQ, = +1.1)
- Health Care: +1.1  (+2 LIQ, = +1.1)
- Energy: +0.6  (+2 MOM, = +0.6)
- Financials: +0.4  (+2 CURVE, +1 MOM, = +0.4)
- Communication Services: +0.3  (+0.5 PHASE, = +0.3)
- Utilities: +0.3  (+1 LIQ, -0.5 PHASE, = +0.3)
- Consumer Discretionary: -0.2  (-1 LIQ, +1 PHASE, -1 MOM, = -0.2)
- Technology: -0.3  (-2 LIQ, +1.5 PHASE, = -0.3)
- Industrials: -1.3  (+1 CURVE, -1 MOM, = -1.3)
- Real Estate: -1.3  (-1.5 LIQ, -1 MOM, = -1.3)

**Rationale (Why the score exists: 섹터 점수의 핵심 드라이버)**
- OW Consumer Staples: FLOW_WEAK → 이론상 우호하나 실제 자금 유입 확인 부족
- OW Consumer Staples: +2: 유동성 긴축 → 방어적 필수소비 선호
- OW Health Care: FLOW_WEAK → 이론상 우호하나 실제 자금 유입 확인 부족
- OW Health Care: +2: 유동성 긴축 → 안정적 현금흐름 선호
- OW Energy: TACTICAL_MOMENTUM_ONLY → 거시 근거 약하지만 단기 리더십 존재
- OW Energy: +2: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- OW Financials: FLOW_WEAK → 이론상 우호하나 실제 자금 유입 확인 부족
- OW Financials: +2: 완만한 스티프닝(0.41) → 예대마진 개선
- OW Financials: +1: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- UW Industrials: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Industrials: +1: 완만한 스티프닝(0.41) → 성장 기대 반영
- UW Industrials: -1: Relative Strength 약세 (vs SPY) → 소외 섹터

**Regime Controller:**
- BALANCED (avg_divergence=-0.55, dispersion=1.09)
- Correlation Break: True / Type=XLF_BETRAYAL
- Break Reasons: US10Y ↑ but XLF ↓
- Interpretation: 디스인플레이션 리스크온 / 성장주·소비 베타 우호

**Divergence / Classification Monitor (Theory vs Flow alignment: 이론과 실제 자금흐름 정렬 여부)**
- Consumer Staples: FLOW_WEAK (theory=+2.0, flow=+0.0, final=+1.1)
- Health Care: FLOW_WEAK (theory=+2.0, flow=+0.0, final=+1.1)
- Energy: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+1.4, final=+0.6)
- Financials: FLOW_WEAK (theory=+2.0, flow=+0.7, final=+0.4)
- Materials: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Industrials: THEORY_TRAP (theory=+1.0, flow=-0.7, final=-1.3)
- Real Estate: AVOID (theory=-1.5, flow=-0.7, final=-1.3)

### 💰 18.5) Tactical Asset Allocation (Execution Weight)
- **Strategic Exposure (15):** **40.0%** → **Regime Adjusted:** **40.0%**
- **Exposure Override:** BALANCED → Sector Weight Only (No Exposure Change)

| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |
| :--- | :---: | :---: | :---: | :--- |
| Consumer Staples | +1.1 | NEGATIVE_DIVERGENCE | **8.3%** | SMALL ADJUST |
| Health Care | +1.1 | NEGATIVE_DIVERGENCE | **8.3%** | SMALL ADJUST |
| Energy | +0.6 | POSITIVE_DIVERGENCE | **8.4%** | NEW |
| Financials | +0.4 | NEGATIVE_DIVERGENCE | **3.0%** | HOLD |
| Communication Services | +0.3 | ALIGNED | **3.9%** | NEW |
| Utilities | +0.3 | ALIGNED | **3.9%** | NEW |
| **Cash & Hedge** | - | - | **60.8%** | DEFENSIVE |

- **Allocation Check:** Sector Weights + Cash = **100.0%**
- **Regime Cap Profile:** DISINFLATION_RISK_ON
- **Regime Cap Applied:** None
- **Strategic Cash (15):** 60.0%
- **Tactical Reserve (Cap / Unallocated):** 0.8%


**Deleveraging Priority Preview:**
- 기준: Divergence → Momentum → Score → Current Weight
1. Consumer Staples (priority_score=3.87, score=1.08, weight=8.3%, div=NEGATIVE_DIVERGENCE, mom=0)
2. Health Care (priority_score=3.87, score=1.08, weight=8.3%, div=NEGATIVE_DIVERGENCE, mom=0)
3. Financials (priority_score=2.78, score=0.44, weight=3.0%, div=NEGATIVE_DIVERGENCE, mom=1)
4. Technology (priority_score=0.45, score=-0.3, weight=3.4%, div=ALIGNED, mom=0)
5. Communication Services (priority_score=-0.15, score=0.3, weight=3.9%, div=ALIGNED, mom=0)

**Leveraging Priority Preview:**
- 기준: Score → Momentum → Positive Divergence
1. Energy (priority_score=4.57, score=0.57, weight=8.4%, div=POSITIVE_DIVERGENCE, mom=2)
2. Communication Services (priority_score=0.30, score=0.3, weight=3.9%, div=ALIGNED, mom=0)
3. Utilities (priority_score=0.30, score=0.3, weight=3.9%, div=ALIGNED, mom=0)
4. Technology (priority_score=-0.30, score=-0.3, weight=3.4%, div=ALIGNED, mom=0)
5. Financials (priority_score=-1.06, score=0.44, weight=3.0%, div=NEGATIVE_DIVERGENCE, mom=1)
- **Divergence Adjustment:** Consumer Staples, Health Care, Financials penalized in weight sizing

### 🧬 19) Execution Layer (ETF Mapping)

| Sector | ETF | Weight | Action | Divergence | Classification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| Consumer Staples | XLP | 8.3% | WATCHLIST_SMALL | NEGATIVE_DIVERGENCE | FLOW_WEAK |
| Health Care | XLV | 8.3% | WATCHLIST_SMALL | NEGATIVE_DIVERGENCE | FLOW_WEAK |
| Energy | XLE | 8.4% | TACTICAL_ONLY | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Financials | XLF | 3.0% | WATCHLIST_SMALL | NEGATIVE_DIVERGENCE | FLOW_WEAK |
| Communication Services | XLC | 3.9% | SMALL | ALIGNED | ALIGNED |
| Utilities | XLU | 3.9% | SMALL | ALIGNED | ALIGNED |
| Technology | XLK | 3.4% | SMALL | ALIGNED | ALIGNED |


### 🧬 19.5) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Execution Notes:**
- Flow weak → avoid chasing; keep only proven leaders.
- Exposure below 45% → defensive execution; cash remains strategic asset.

**Preferred Company Traits:**
- High Free Cash Flow generators
- Net cash or low leverage balance sheets
- Stable margins / pricing power
- Low to mid beta exposure
- RAROC-friendly profile
- Market leaders with confirmed relative strength
- Smaller position sizes with strict risk budget discipline

**Risk Control / Avoid:**
- Negative FCF / cash-burn models
- High leverage / refinancing-dependent names
- Long-duration, high-multiple growth
- Flow-weak cyclicals and theory-only sector bets

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.2956272504368013
- **Z-Score (5d):** -0.23429201697523713

### EEM
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.07582370811416975
- **Z-Score (5d):** 0.7488812658469218

### EIS
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.5285782862478107
- **Z-Score (5d):** 0.8905008341166809

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.3504831265929749
- **Z-Score (5d):** 0.01515119618785523

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.32618653443699336
- **Z-Score (5d):** 0.5823421463322429

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -2.1160950729160395
- **Z-Score (5d):** -0.41975145459601776

### GLD
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -1.1413767173862688
- **Z-Score (5d):** -0.7131618138532613

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.8064098152894332
- **Z-Score (5d):** -0.32818480709717635

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.7724633130174257
- **Z-Score (5d):** 0.6277192200460833
