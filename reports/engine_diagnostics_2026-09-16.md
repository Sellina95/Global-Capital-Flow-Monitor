# ENGINE DIAGNOSTICS
**Date:** 2026-09-16
**Data as of:** 2026-09-15

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: ✅ STABLE**
> **판단 요약: 구조-가격-수급 정렬 / 실시간 이상징후 없음 / 데드맨 정상**
### 🎯 Exposure Framework
- **Base Exposure (전략 기준): 32%**
- **Final Exposure (실행 기준): 32%**

- **Portfolio Stance:** REDUCE / 32%

- **[14번 구조·수급 괴리]:** ✅ **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
### 🟢 Current SEW Status
- **SEW:** STABLE | ✅ 이상징후 없음 (5개 자산 정상 범위 / z-score 발작 없음)
- **Event Type:** NORMAL → 정상 상태 / 구조적 리스크 없음
- **Spike Monitor:** Spike 0 / Extreme 0

- **[15번 Hard Deadman]:** ✅ PASS
- **[14번 수급 시그널]:** 🚨 **STAY (포지션 유지)**

### 🔬 Structural Layer (12.5~12.8)
- **Structural Layer:**
  - Growth Sustainability → **FRAGILE_EXPANSION** (Expansion remains possible, but the growth structure is not yet broad or durable. Monitor demand confirmation.)
  - Flow Authenticity → **EARLY_ROTATION** (Participation is emerging, but confirmation remains limited.)
  - Leadership Breadth → **CONCENTRATED_LEADERSHIP** (Leadership remains concentrated, with limited confirmation beyond key growth or mega-cap areas.)
  - Positioning Stress → **SQUEEZE_RISK** (Positioning is stretched and vulnerable to squeeze-driven reversals.)

## 🎯 Final Decision (War Room Override)
- **Final Action:** **REDUCE**
- **Final Exposure:** **32%**
- **Base Context:** phase=EVENT-WATCHING / INFLATION / narrative=REDUCE / base_exposure=32%
- **SEW:** STABLE / NORMAL
- **Divergence:** ALIGNED / **STAY (포지션 유지)**
- **Drift:** 👀 EARLY DRIFT / NEUTRAL / NONE / score=2
- **Flow:** 👀 EARLY TRACE / score=3
- **Gamma:** 🟡 POSITIVE-TRANSITION
- **Tactical Action:** HOLD / NONE / LOW
- **Positioning:** pos_z=1.48
- **Warning Score:** 0 (No warning)
- **Tactical Why:** No actionable alignment
- **Why:** SEW STABLE → 실시간 이상징후 없음 → Divergence ALIGNED → 구조·가격·수급 정렬 → Narrative Action=REDUCE 반영 → Tactical=HOLD / Flow=👀 EARLY TRACE(3) / Drift=👀 EARLY DRIFT(2) / Gamma=🟡 POSITIVE-TRANSITION → Tactical HOLD/MONITOR → 최종판단 변경 없음

### 🚩 Market Regime Status
- **국면 전환 감지:** 🚨 **SOFT RISK-OFF (부분 경계)** → **EVENT-WATCHING / INFLATION**
- **Structural Regime:** **INFLATION_PRESSURE**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.996  (+0.71% vs 4.961)
- **달러 인덱스**: 99.650  (+0.19% vs 99.460)
- **WTI 유가**: 105.830  (+4.38% vs 101.390)
- **변동성 지수 (VIX)**: 17.200 (+0.58% vs 17.100)
- **원/달러 환율**: 1345.610  (+0.07% vs 1344.640)

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 17.20 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(↑) / DXY(↑) / VIX(↑)
- **판정:** **EVENT-WATCHING / INFLATION | Flow:  (Flow Weak)**
- **근거:** 변동성은 눌려있지만 금리/달러가 움직임 → 데이터/이벤트 대기

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↑) / DXY(↑) / VIX(↑)
- **현실(FCI):** value=-0.564 / level=EASY (완화) / update=low-frequency | as of: 2026-09-16 (latest available)
- **유인(Real Rates):** value=2.600 / level=RESTRICTIVE (유인↓) / dir(→) | as of: 2026-09-16 (latest available)
- **판정:** **LIQUIDITY TIGHTENING (유동성 축소)**
- **근거:** 금리↑+달러↑ + (FCI 압박 또는 실질금리 유인↓) → 리스크자산에 불리
- **Note:** FCI는 저빈도 금융환경 프록시로 level 중심 해석, Real Rates는 영업일 기준 변화 방향을 함께 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↑) / DXY(↑) / VIX(↑)
- **Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCI value=-0.564 (low-frequency) / DXYΔ +0.190 / US10YΔ +0.035**
- **Expectations: dict received.**

- **판정:** **POLICY TIGHTENING (긴축)**
- **근거:** 금리↑ + 달러↑ → 긴축 압력
- **한줄요약 ~~** 구조=TIGHTENING (긴축)(MODERATE)는 참고, 가격=POLICY TIGHTENING (긴축) 중심 → 최종 POLICY TIGHTENING (긴축)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-09-09 (FRED latest)
- **NET_LIQ level:** 5857283.6
- **TGA level:** 883335.0
- **RRP level:** 0.432
- **방향(전일 대비):** TGA(↓) / RRP(↓) / NET_LIQ(↑)
- **판정:** **LIQUIDITY SUPPORTIVE (완만한 유동성 우호)**
- **근거:** Net Liquidity↑ → 시장 내 달러 여력 개선
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-09-14 (FRED latest)
- **HY_OAS level:** 2.71% → **COOL (낮은 공포)**
- **방향(전일 대비):** HY_OAS(↑) / +2.26%
- **판정:** **CREDIT CALM**
- **근거:** HY 스프레드 낮음 → 크레딧 스트레스 제한 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(↓)
- **HYG:** today 78.380 / prev 78.530 / pct -0.19%
- **LQD:** today 104.280 / prev 104.300 / pct -0.02%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, +0.71%)** → 완화 기대 약화/금리 부담
- DXY **(Clear, +0.19%)** → 달러 강세/신흥국 부담
- WTI **(Strong, +4.38%)** → 인플레 재자극 가능성
- VIX **(Mild, +0.58%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Mild, +0.07%)** → 원화 약세/수급 부담
- HYG (High Yield ETF) **(Mild, -0.19%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Noise, -0.02%)** → 우량채 약세(리스크온 성향)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 상승(US10Y↑)** → 실질 금리 압박 → 달러 강세(DXY↑) 유도: **신흥국 자본 유출 및 고밸류 성장주 할인율 부담 증가**
- **변동성 상승(VIX↑)** → 위험회피(Risk-Off) 강화: **안전 자산(Cash/USD) 선호도 급증 및 하이일드 스프레드 확대 압력**
- **유가 상승(WTI↑)** → 기대 인플레이션 자극: **제조/운송업 비용 부담 가중 및 중앙은행의 긴축 유지 명분 강화**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### 🌊 Drift Monitor (v4)
- **정의:** 누적 흐름 + ATR 기반 강도 감지

- **SPY:** 🔴 DOWN | Short-term: SHORT UP | 1D=-0.45% / 5D=-1.11% | Strength: LOW
- **WTI:** 🟡 PULLBACK | Short-term: SHORT UP | 1D=-0.96% / 5D=+9.12% | Strength: HIGH
- **DXY:** 🟡 PULLBACK | Short-term: SHORT DOWN | 1D=-0.05% / 5D=+0.84% | Strength: LOW
- **GOLD:** 🟡 REBOUND | Short-term: SHORT UP | 1D=+0.79% / 5D=-2.10% | Strength: LOW

- **Drift Score:** 2
- **State:** **👀 EARLY DRIFT**
- **Label:** NEUTRAL
- **SEW Combo Signal:** NONE

- **Market Drift Summary:**
  - Equity (SPY): 🔴 DOWN / SHORT UP
  - Oil (WTI): 🟡 PULLBACK / SHORT UP
  - Dollar (DXY): 🟡 PULLBACK / SHORT DOWN
  - Gold (GOLD): 🟡 REBOUND / SHORT UP

- **Drivers:**
  - Defensives lagging
  - Dollar not restrictive

### ⚠ 6.5) Correlation Break Monitor
No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
No significant sector-level correlation break detected.

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 상승(VIX↑)** → 변동성 확대: 포지션 축소/헤지 수요 증가 가능
- **금리 상승(US10Y↑)** → 할인율 부담/유동성 압박 가능
- **달러 강세(DXY↑)** → 신흥국·원자재·원화 등 위험자산에 부담
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **-0.22**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** -0.38
- **Geo Momentum:** +0.17 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Taiwan_Tension
- **Cosine Similarity Score:** 0.366
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Taiwan_Tension: 0.366
  - Ukraine_2022: 0.310
  - China_Trade_2018: 0.295
- **Top Drivers:**
  - KR10Y_SPREAD: z_used=-2.58 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.16
  - DE10Y_SPREAD: z_used=-2.75 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=-0.13
  - JP10Y_SPREAD: z_used=-2.63 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=-0.12
  - EMB: z_used=+1.27 (z1d=-0.59, z5d=-2.30, raw_w=0.12, norm_w=0.09) → contrib=+0.12
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Taiwan_Tension** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (EEM, EIS)
- **Extreme Country Risk:** EEM, EIS

### ⚡ 7.3) Pseudo Gamma Filter
- **정의:** 옵션 데이터 없이 시장의 감마 환경을 추론
- **주의:** Dealer Gamma Bias 숫자와 Pseudo Gamma State는 서로 다른 레이어

- **Pseudo Gamma State:** 🟡 POSITIVE-TRANSITION
- **Dealer Gamma Bias:** 0.70 (NEUTRAL / transition zone)
- **Bias:** VIX는 안정적이나 Drift가 형성 중
- **Strategy:** 초기 방향성 관찰 / 과도한 추격 금지

- **Drift Score:** 2 (👀 EARLY DRIFT)
- **VIX:** 17.200000762939453
- **SEW:** STABLE / NORMAL

- **🚀 Combo Signal:** 🟢 EARLY FLOW WITHOUT SHOCK

### 🏦 Institutional Flow Engine (v2-minimal)
- **정의:** 기관성 자금이 뉴스 전에 남기는 흔적을 구조적으로 탐지

- **Raw Flow State:** **👀 EARLY TRACE**
- **Transition State:** **EARLY_TRACE**
- **Flow Delta:** +2 (prev=1 → current=3)
- **Persistence Days:** 1
- **Transition Note:** 기관성 흐름 초기 흔적 발생
- **Confidence:** **MEDIUM**
- **Action Bias:** **MONITOR**

- **Drift:** 👀 EARLY DRIFT / NEUTRAL / NONE
- **Gamma:** 🟡 POSITIVE-TRANSITION / 🟢 EARLY FLOW WITHOUT SHOCK
- **SEW:** STABLE / NORMAL
- **Positioning (POS_Z):** 1.48
- **Validation Score:** 0 (boost applied: +0)

- **Drivers:**
  - Drift early
  - Gamma transition
  - No shock yet

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(33.00bp) | 실질금리(2.60%) | DXY(99.65)
*(as of: RealRate: 2026-09-16 / FRED last available)*

❌ **자본이 탈출하는 곳 (Short Incentive):**
고금리(실질금리 2% 상회) 부담으로 인한 리스크 오프 신호

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** 금리↑ + 달러↑ + 유가↑ + VIX↑
- **최종 판정:** **긴축 공포 및 달러 수급 경색에 따른 '위험회피(Risk-Off)'**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Clear) / WTI(Strong) / VIX(Mild)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.996), DXY(99.650), VIX(17.20)

### 🏗️ 12) Structural Filter (v3)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↑) / GOLD(↓) / VIX(↑) / WTI(↑)
- **Meaningful Move Check:** DXY=0.19103402690048135 / GOLD=-0.43889101507053263 / US10Y=0.7054998519315365 / VIX=0.5847975394087778 / WTI=4.379132526022625
- **판정:** **ENERGY-DRIVEN STAGFLATION (에너지 주도 스태그)**
- **근거:** 긴축적인 실질금리(2.6%) 환경에서도 고유가가 의미 있게 유지/상승. 공급 측 구조 압박 가능성



### 12.5) Growth Sustainability Filter [SHADOW]
- **Score:** 2
- **Label:** FRAGILE_EXPANSION
- **Demand Proxy:** 1
- **Financing:** 0
- **Energy Burden:** -2
- **Policy Capacity:** 3
- **Strategic Interpretation:** Expansion remains possible, but the growth structure is not yet broad or durable. Monitor demand confirmation.
- **Input Check:** US10Y=4.995999813079834, RealYield=2.6, T10Y2Y=0.33, WTI=105.83000183105467, DXY=99.6500015258789, LiquidityDir=UP, CreditCalm=True, HY_OAS=2.71, DriftLabel=NEUTRAL, FredAsof=2026-09-15

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.




### 12.8) Positioning Stress Filter [SHADOW]

- **Score:** 0
- **Label:** SQUEEZE_RISK
- **Strategic Interpretation:** Positioning is stretched and vulnerable to squeeze-driven reversals.

**Positioning Notes**
- Term Structure: VIX3M-VIX=2.16 → healthy contango / stable structure
- Short-Term Hedge: VIX9D/VIX=1.00 → neutral short-term hedge
- Gamma Structure: Positive gamma mild
- Positioning: Elevated long positioning

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.



### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** 3
- **Label:** EARLY_ROTATION
- **Strategic Interpretation:** Participation is emerging, but confirmation remains limited.
- **Breadth / Participation:** -1
- **Breadth Note:** RSP-SPY return spread=-0.03%p → neutral breadth
- **Nasdaq Breadth Note:** QQQE-QQQ return spread=-0.40%p → mega-cap concentrated Nasdaq rally
- **Positioning / Gamma:** 0
- **Credit Confirmation:** 2
- **Macro Participation:** 2

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.



### 12.7) Leadership Breadth Filter [SHADOW]
- **Score:** 0
- **Label:** CONCENTRATED_LEADERSHIP
- **Strategic Interpretation:** Leadership remains concentrated, with limited confirmation beyond key growth or mega-cap areas.

**Leadership Notes**
- QQQ-SPY spread=-0.20%p → neutral growth leadership
- SMH-QQQ spread=0.77%p → semiconductor participation strong
- SOXX-QQQ spread=0.95%p → SOX proxy confirms chip breadth
- IWM-SPY spread=-0.50%p → small-cap lag, narrow leadership risk
- XLF-SPY spread=0.14%p → sector diffusion neutral
- XLI-SPY spread=-0.18%p → sector diffusion neutral
- XLY-SPY spread=-1.29%p → sector diffusion weak

📌 Shadow Note: This filter checks whether leadership is broadening beyond mega-cap tech/AI. No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.


### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCI value=-0.564 (low-frequency) / DXYΔ +0.190 / US10YΔ +0.035 (스태그플레이션)
- **Sentiment (Fear&Greed):** 58.54023163124992 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** UP (MID)
- **Structural Regime:** INFLATION_PRESSURE
- **Operational Phase:** EVENT-WATCHING / INFLATION (Cap: 100)
- **Macro Tilt:** -6
- **[SPECIAL ALERT]**: **⚠️ 에너지 비용 전이** (Structural Cap: 40)
- **Drift:** 👀 EARLY DRIFT / NEUTRAL / NONE
- **Drift Score:** 2
- **Flow Score:** 3
- **Flow Continuity:** NO_FLOW_BASE → 👀 EARLY TRACE (N/A, tilt=+0)
- **Flow Regime Tilt:** +2 / Flow-Gamma Tilt: +0

- **🎯 Final Risk Action:** **REDUCE**
- **Risk Budget (0~100):** **36**
- **Narrative:** 구조=TIGHTENING(스태그플레이션) / 심리=NEUTRAL / 유동성=증가/중간 / 크레딧=안정 / 드리프트=👀 EARLY DRIFT (NEUTRAL) / 수급=1.48 → Phase=EVENT-WATCHING / INFLATION

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `TIGHTENING` | **Price(Regime):** `EVENT-WATCHING` | **Bucket:** `MIXED` | **VIX:** `17.20`
- **Positioning Data:** Z-Score: `1.48` (>1.8 시 Run) | Gamma: `0.70` (<0.5 시 Run) | CTA: `0.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v3.2)
- **정의:** 13번 Risk Budget 실행 브레이크 레이어
- **추가 이유:** 전략 판단(13) 이후 실제 진입 강도를 조절하기 위함

- **Base Risk Budget (13):** 36
- **VIX Level:** 17.20 (NORMAL) | **Change:** +0.58%
- **Positioning Layer:** ⚠️ Bearish CTA(0.0)
- **Brake Drivers:** ⚠️ Bearish CTA

- **📊 Recommended Exposure:** **32%**

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
- **USD Factor:** NEUTRAL
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.3)

**Context:** phase=EVENT-WATCHING / INFLATION / T10Y2Y=0.33 (MODERATE STEEP) / VIX=17.20 (VOLATILITY NORMAL) / liquidity=UP-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM

**Macro Profile:** EVENT_TRANSITION
**Macro Inputs Debug:** phase=EVENT-WATCHING / INFLATION / us10y_pct=+0.71% / dxy_pct=+0.19% / wti_pct=+4.38% / vix=17.20 / liq_easy=True / liq_tight=False / credit_calm=True / flow_score=3

**Flow Overlay:** flow_score=3 / flow_state=👀 EARLY TRACE / drift_label=NEUTRAL / gamma=🟡 POSITIVE-TRANSITION

**Overweight:** Financials, Consumer Staples, Health Care

**Underweight:** Consumer Discretionary, Technology, Industrials, Utilities, Energy, Real Estate

**Scoreboard:**
- Financials: +2.1  (+1 LIQ, +2 CURVE, +1 MOM, = +2.1)
- Consumer Staples: +0.7  (+1 PHASE, = +0.7)
- Health Care: +0.7  (+1 PHASE, = +0.7)
- Real Estate: -0.2  (-1 MOM, = -0.2)
- Energy: -0.4  (-1 PHASE, +2 MOM, = -0.4)
- Utilities: -0.7  (-1 LIQ, = -0.7)
- Industrials: -1.0  (+1.5 LIQ, +1 CURVE, -0.5 PHASE, -2 MOM, = -1.0)
- Consumer Discretionary: -1.1  (+1.5 LIQ, -1 MOM, = -1.1)
- Technology: -1.1  (+2 LIQ, -0.5 PHASE, -1 MOM, = -1.1)

**Rationale (Why the score exists: 섹터 점수의 핵심 드라이버)**
- OW Financials: FLOW_WEAK → 이론상 우호하나 실제 자금 유입 확인 부족
- OW Financials: +1: 유동성 완화 → 위험선호 회복
- OW Financials: +2: 완만한 스티프닝(0.33) → 예대마진 개선
- OW Consumer Staples: +1: EVENT-WATCHING / INFLATION → 관망 구간 필수소비 선호
- OW Health Care: +1: EVENT-WATCHING / INFLATION → 관망 구간 방어/퀄리티 선호
- UW Consumer Discretionary: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Consumer Discretionary: +1.5: 유동성 완화 → 소비 민감주 우호
- UW Consumer Discretionary: -1: Relative Strength 약세 (vs SPY) → 소외 섹터
- UW Technology: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Technology: +2: 유동성 완화 → 성장주/베타 우호
- UW Technology: -0.5: EVENT-WATCHING / INFLATION → 이벤트 전 성장주 베타 일부 제한
- UW Industrials: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Industrials: +1.5: 유동성 완화 → 경기민감 회복
- UW Industrials: +1: 완만한 스티프닝(0.33) → 성장 기대 반영

**Regime Controller:**
- BALANCED (avg_divergence=-0.95, dispersion=1.42)
- Correlation Break: False / Type=NONE
- Interpretation: 균형 장세 / 강한 방향성보다 선별적 배분 필요

**Divergence / Classification Monitor (Theory vs Flow alignment: 이론과 실제 자금흐름 정렬 여부)**
- Financials: FLOW_WEAK (theory=+3.0, flow=+0.7, final=+2.1)
- Communication Services: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Materials: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Energy: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+1.4, final=-0.4)
- Industrials: THEORY_TRAP (theory=+2.0, flow=-1.4, final=-1.0)
- Consumer Discretionary: THEORY_TRAP (theory=+1.5, flow=-0.7, final=-1.1)
- Technology: THEORY_TRAP (theory=+1.5, flow=-0.7, final=-1.1)

### 💰 18.5) Tactical Asset Allocation (Execution Weight)
- **Strategic Exposure (15):** **32.0%** → **Regime Adjusted:** **32.0%**
- **Exposure Override:** BALANCED → Sector Weight Only (No Exposure Change)

| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |
| :--- | :---: | :---: | :---: | :--- |
| Financials | +2.1 | NEGATIVE_DIVERGENCE | **5.0%** | DELEVERAGE |
| Consumer Staples | +0.7 | ALIGNED | **8.7%** | DELEVERAGE |
| Health Care | +0.7 | ALIGNED | **13.2%** | DELEVERAGE |
| **Cash & Hedge** | - | - | **73.1%** | DEFENSIVE |

- **Allocation Check:** Sector Weights + Cash = **100.0%**
- **Regime Cap Profile:** EVENT_TRANSITION
- **Participation / Quality Cap Applied:**
  - Financials: 10.2% → 5.0% (-5.2%)
- **Strategic Cash (15):** 68.0%
- **Tactical Reserve (Cap / Unallocated):** 5.1%


**Deleveraging Priority Preview:**
- 기준: Divergence → Momentum → Score → Current Weight
1. Financials (priority_score=1.0, score=2.12, weight=5.0%, div=NEGATIVE_DIVERGENCE, mom=1)
2. Health Care (priority_score=0.31, score=0.65, weight=13.2%, div=ALIGNED, mom=0)
3. Consumer Staples (priority_score=-0.33, score=0.65, weight=8.7%, div=ALIGNED, mom=0)

**Leveraging Priority Preview:**
- 기준: Score → Momentum → Positive Divergence
1. Consumer Staples (priority_score=0.65, score=0.65, weight=8.7%, div=ALIGNED, mom=0)
2. Health Care (priority_score=0.65, score=0.65, weight=13.2%, div=ALIGNED, mom=0)
3. Financials (priority_score=0.62, score=2.12, weight=5.0%, div=NEGATIVE_DIVERGENCE, mom=1)
- **Divergence Adjustment:** Financials penalized in weight sizing

### 🧬 19) Execution Layer (ETF Mapping)

| Sector | ETF | Weight | Action | Divergence | Classification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| Financials | XLF | 5.0% | WATCHLIST_SMALL | NEGATIVE_DIVERGENCE | FLOW_WEAK |
| Consumer Staples | XLP | 8.7% | SMALL | ALIGNED | ALIGNED |
| Health Care | XLV | 13.2% | ADD | ALIGNED | ALIGNED |


### 🧬 19.5) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Execution Notes:**
- Early flow trace → maintain leaders, wait for confirmation before broadening.
- Exposure below 45% → defensive execution; cash remains strategic asset.

**Preferred Company Traits:**
- Cash flow visibility and earnings stability
- Leaders with improving breadth confirmation
- Smaller position sizes with strict risk budget discipline

**Risk Control / Avoid:**
- Rate-sensitive long-duration equities
- Broad beta expansion before confirmation

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** HIGH
- **Z-Score (1d):** 0.02092751950351292
- **Z-Score (5d):** -2.02249276043061

### EEM
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.14150719978694096
- **Z-Score (5d):** -1.5204551395732986

### EIS
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.24851009145233563
- **Z-Score (5d):** -0.951614913950523

### EMB
- **Crash?** False
- **Risk Level:** HIGH
- **Z-Score (1d):** -0.6686114064326141
- **Z-Score (5d):** -2.4454931558693627

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.5099800103535355
- **Z-Score (5d):** -0.5599450267704558

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -1.183283661993732
- **Z-Score (5d):** -0.5741839489945088

### GLD
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.1879706443817186
- **Z-Score (5d):** -0.44881263911320773

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.675464571601341
- **Z-Score (5d):** -0.8111066699710712

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.20151250274617427
- **Z-Score (5d):** 0.8311643370234919
