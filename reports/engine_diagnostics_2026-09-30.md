# ENGINE DIAGNOSTICS
**Date:** 2026-09-30
**Data as of:** 2026-09-29

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: ✅ STABLE**
> **판단 요약: 구조-가격-수급 정렬 / 실시간 이상징후 없음 / 데드맨 정상**
### 🎯 Exposure Framework
- **Base Exposure (전략 기준): 30%**
- **Final Exposure (실행 기준): 30%**

- **Portfolio Stance:** STRONG REDUCE / 30%

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
  - Flow Authenticity → **REAL_ACCUMULATION** (Institutional participation appears broad and persistent.)
  - Leadership Breadth → **BROAD_LEADERSHIP** (Leadership is broadening across sectors, confirming healthier market participation.)
  - Positioning Stress → **STABLE_BUT_CROWDED** (Positioning is becoming crowded, but market structure remains stable.)

## 🎯 Final Decision (War Room Override)
- **Final Action:** **STRONG REDUCE**
- **Final Exposure:** **30%**
- **Base Context:** phase=SOFT RISK-OFF / narrative=STRONG REDUCE / base_exposure=30%
- **SEW:** STABLE / NORMAL
- **Divergence:** ALIGNED / **STAY (포지션 유지)**
- **Drift:** 👀 EARLY DRIFT / NEUTRAL / NONE / score=2
- **Flow:** 👀 EARLY TRACE / score=4
- **Gamma:** 🟡 POSITIVE-TRANSITION
- **Tactical Action:** REDUCE / DEFENSIVE / MEDIUM
- **Positioning:** pos_z=1.53
- **Warning Score:** 0 (No warning)
- **Tactical Why:** Risk-off environment
- **Why:** SEW STABLE → 실시간 이상징후 없음 → Divergence ALIGNED → 구조·가격·수급 정렬 → Narrative Action=STRONG REDUCE 반영 → Tactical=REDUCE / Flow=👀 EARLY TRACE(4) / Drift=👀 EARLY DRIFT(2) / Gamma=🟡 POSITIVE-TRANSITION → Tactical REDUCE → 방어 기조 유지 / 총노출 추가 감산 없이 배분 보수화

### 🚩 Market Regime Status
- **국면 전환 감지:** 🚨 **SOFT RISK-OFF (경계 강화)** → **SOFT RISK-OFF**
- **Structural Regime:** **TIGHTENING_GROWTH_SCARE**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 5.255  (+0.29% vs 5.240)
- **달러 인덱스**: 101.370  (+0.17% vs 101.200)
- **WTI 유가**: 89.380  (-3.48% vs 92.600)
- **변동성 지수 (VIX)**: 16.040 (-0.19% vs 16.070)
- **원/달러 환율**: 1359.560  (+0.37% vs 1354.510)

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 16.04 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(↑) / DXY(↑) / VIX(↓)
- **판정:** **SOFT RISK-OFF | Flow:  (Flow Weak)**
- **근거:** Macro Narrative=TIGHTENING_GROWTH_SCARE / Policy=MIXED / Credit=WATCH

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↑) / DXY(↑) / VIX(↓)
- **현실(FCI):** value=-0.555 / level=EASY (완화) / update=low-frequency | as of: 2026-09-30 (latest available)
- **유인(Real Rates):** value=2.900 / level=RESTRICTIVE (유인↓) / dir(→) | as of: 2026-09-30 (latest available)
- **판정:** **LIQUIDITY TIGHTENING (유동성 축소)**
- **근거:** 금리↑+달러↑ + (FCI 압박 또는 실질금리 유인↓) → 리스크자산에 불리
- **Note:** FCI는 저빈도 금융환경 프록시로 level 중심 해석, Real Rates는 영업일 기준 변화 방향을 함께 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↑) / DXY(↑) / VIX(↓)
- **Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCI value=-0.555 (low-frequency) / DXYΔ +0.170 / US10YΔ +0.015**
- **Expectations: dict received.**

- **판정:** **POLICY TIGHTENING (긴축)**
- **근거:** 금리↑ + 달러↑ → 긴축 압력
- **한줄요약 ~~** 구조=TIGHTENING (긴축)(MODERATE)는 참고, 가격=POLICY TIGHTENING (긴축) 중심 → 최종 POLICY TIGHTENING (긴축)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-09-23 (FRED latest)
- **NET_LIQ level:** 5770619.5
- **TGA level:** 977084.0
- **RRP level:** 0.461
- **방향(전일 대비):** TGA(↑) / RRP(↓) / NET_LIQ(↓)
- **판정:** **LIQUIDITY DRAINING (유동성 흡수)**
- **근거:** Net Liquidity↓ → 시장 내 달러 여력 축소 가능
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-09-28 (FRED latest)
- **HY_OAS level:** 3.02% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↑) / +3.07%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(↓)
- **HYG:** today 77.360 / prev 77.540 / pct -0.23%
- **LQD:** today 102.410 / prev 102.470 / pct -0.06%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, +0.29%)** → 완화 기대 약화/금리 부담
- DXY **(Clear, +0.17%)** → 달러 강세/신흥국 부담
- WTI **(Strong, -3.48%)** → 물가 부담 완화
- VIX **(Noise, -0.19%)** → 심리 개선/리스크온
- 원/달러(USDKRW) **(Clear, +0.37%)** → 원화 약세/수급 부담
- HYG (High Yield ETF) **(Mild, -0.23%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Noise, -0.06%)** → 우량채 약세(리스크온 성향)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 상승(US10Y↑)** → 실질 금리 압박 → 달러 강세(DXY↑) 유도: **신흥국 자본 유출 및 고밸류 성장주 할인율 부담 증가**
- **변동성 하락(VIX↓)** → 심리 개선(Risk-On): **자산군 전반의 위험 수용 여력(Risk Appetite) 회복 및 랠리 지속 가능성**
- **유가 하락(WTI↓)** → 물가 부담 완화: **실질 구매력 회복 및 긴축 압력 완화(Dovish Tilt) 가능성 시사**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### 🌊 Drift Monitor (v4)
- **정의:** 누적 흐름 + ATR 기반 강도 감지

- **SPY:** 🔴 DOWN | Short-term: MIXED | 1D=-0.17% / 5D=-1.18% | Strength: LOW
- **WTI:** 🟡 REBOUND | Short-term: MIXED | 1D=+0.08% / 5D=-2.94% | Strength: LOW
- **DXY:** 🟡 PULLBACK | Short-term: SHORT DOWN | 1D=-0.12% / 5D=+0.15% | Strength: LOW
- **GOLD:** 🟡 REBOUND | Short-term: SHORT UP | 1D=+0.83% / 5D=-2.40% | Strength: LOW

- **Drift Score:** 2
- **State:** **👀 EARLY DRIFT**
- **Label:** NEUTRAL
- **SEW Combo Signal:** NONE

- **Market Drift Summary:**
  - Equity (SPY): 🔴 DOWN / MIXED
  - Oil (WTI): 🟡 REBOUND / MIXED
  - Dollar (DXY): 🟡 PULLBACK / SHORT DOWN
  - Gold (GOLD): 🟡 REBOUND / SHORT UP

- **Drivers:**
  - Sector breadth expanding
  - Dollar not restrictive

### ⚠ 6.5) Correlation Break Monitor
No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
No significant sector-level correlation break detected.

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 하락(VIX↓)** → 심리 안정: 리스크 수용 여력 개선
- **금리 상승(US10Y↑)** → 할인율 부담/유동성 압박 가능
- **달러 강세(DXY↑)** → 신흥국·원자재·원화 등 위험자산에 부담
- **유가 하락(WTI↓)** → 물가 부담 완화 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **-0.28**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** -0.32
- **Geo Momentum:** +0.04 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Taiwan_Tension
- **Cosine Similarity Score:** 0.362
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Taiwan_Tension: 0.362
  - China_Trade_2018: 0.311
  - Ukraine_2022: 0.260
- **Top Drivers:**
  - KR10Y_SPREAD: z_used=-2.66 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.16
  - DE10Y_SPREAD: z_used=-2.80 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=-0.13
  - JP10Y_SPREAD: z_used=-2.79 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=-0.13
  - USDMXN: z_used=+3.18 (z1d=+2.71, z5d=+3.89, raw_w=0.05, norm_w=0.04) → contrib=+0.12
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Taiwan_Tension** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (EEM, EIS, EMB, EWJ, FXI)
- **Extreme Country Risk:** EEM, EIS, EMB, EWJ, FXI

### ⚡ 7.3) Pseudo Gamma Filter
- **정의:** 옵션 데이터 없이 시장의 감마 환경을 추론
- **주의:** Dealer Gamma Bias 숫자와 Pseudo Gamma State는 서로 다른 레이어

- **Pseudo Gamma State:** 🟡 POSITIVE-TRANSITION
- **Dealer Gamma Bias:** 0.50 (NEUTRAL / transition zone)
- **Bias:** VIX는 안정적이나 Drift가 형성 중
- **Strategy:** 초기 방향성 관찰 / 과도한 추격 금지

- **Drift Score:** 2 (👀 EARLY DRIFT)
- **VIX:** 16.040000915527344
- **SEW:** STABLE / NORMAL

- **🚀 Combo Signal:** 🟢 EARLY FLOW WITHOUT SHOCK

### 🏦 Institutional Flow Engine (v2-minimal)
- **정의:** 기관성 자금이 뉴스 전에 남기는 흔적을 구조적으로 탐지

- **Raw Flow State:** **👀 EARLY TRACE**
- **Transition State:** **TRACE_BUILDING**
- **Flow Delta:** +1 (prev=3 → current=4)
- **Persistence Days:** 3
- **Transition Note:** 기관성 흐름이 전일 대비 강화
- **Confidence:** **MEDIUM**
- **Action Bias:** **MONITOR**

- **Drift:** 👀 EARLY DRIFT / NEUTRAL / NONE
- **Gamma:** 🟡 POSITIVE-TRANSITION / 🟢 EARLY FLOW WITHOUT SHOCK
- **SEW:** STABLE / NORMAL
- **Positioning (POS_Z):** 1.53
- **Validation Score:** 2 (boost applied: +2)

- **Drivers:**
  - Drift early
  - Gamma transition
  - No shock yet
  - Positioning somewhat stretched
  - Leadership breadth expanding
  - Cyclical leadership over defensives

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(37.00bp) | 실질금리(2.90%) | DXY(101.37)
*(as of: RealRate: 2026-09-30 / FRED last available)*

❌ **자본이 탈출하는 곳 (Short Incentive):**
고금리(실질금리 2% 상회) 부담으로 인한 리스크 오프 신호

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** 금리↑ + 달러↑ + 유가↓ + VIX↓
- **최종 판정:** **매크로 지표 혼조 속 시장 심리 개선 주도**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Clear) / WTI(Strong) / VIX(Noise)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(5.255), DXY(101.370), VIX(16.04)

### 🏗️ 12) Structural Filter (v3)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↑) / GOLD(↑) / VIX(↓) / WTI(↓)
- **Meaningful Move Check:** DXY=0.16798992437400134 / GOLD=0.2710942623906173 / US10Y=0.28626610644971423 / VIX=-0.18667566811800826 / WTI=-3.4773231898087107
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
- **Input Check:** US10Y=5.255000114440918, RealYield=2.9, T10Y2Y=0.37, WTI=89.37999725341797, DXY=101.37000274658205, LiquidityDir=DOWN, CreditCalm=True, HY_OAS=3.02, DriftLabel=NEUTRAL, FredAsof=2026-09-29

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.




### 12.8) Positioning Stress Filter [SHADOW]

- **Score:** 1
- **Label:** STABLE_BUT_CROWDED
- **Strategic Interpretation:** Positioning is becoming crowded, but market structure remains stable.

**Positioning Notes**
- Term Structure: VIX3M-VIX=2.05 → healthy contango / stable structure
- Short-Term Hedge: VIX9D/VIX=0.89 → calm front-end hedge
- Gamma Structure: Positive gamma mild
- Positioning: Elevated long positioning

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.



### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** 5
- **Label:** REAL_ACCUMULATION
- **Strategic Interpretation:** Institutional participation appears broad and persistent.
- **Breadth / Participation:** 0
- **Breadth Note:** RSP-SPY return spread=0.07%p → neutral breadth
- **Nasdaq Breadth Note:** QQQE-QQQ return spread=0.10%p → neutral Nasdaq breadth
- **Positioning / Gamma:** 1
- **Credit Confirmation:** 2
- **Macro Participation:** 2

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.



### 12.7) Leadership Breadth Filter [SHADOW]
- **Score:** 6
- **Label:** BROAD_LEADERSHIP
- **Strategic Interpretation:** Leadership is broadening across sectors, confirming healthier market participation.

**Leadership Notes**
- QQQ-SPY spread=0.37%p → growth leadership
- SMH-QQQ spread=0.96%p → semiconductor participation strong
- SOXX-QQQ spread=1.00%p → SOX proxy confirms chip breadth
- IWM-SPY spread=-0.18%p → small-cap participation neutral
- XLF-SPY spread=-0.15%p → sector diffusion neutral
- XLI-SPY spread=0.39%p → sector diffusion positive
- XLY-SPY spread=0.32%p → sector diffusion positive

📌 Shadow Note: This filter checks whether leadership is broadening beyond mega-cap tech/AI. No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.


### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCI value=-0.555 (low-frequency) / DXYΔ +0.170 / US10YΔ +0.015 (정상)
- **Sentiment (Fear&Greed):** 63.74216435069459 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** DOWN (MID)
- **Structural Regime:** TIGHTENING_GROWTH_SCARE
- **Operational Phase:** SOFT RISK-OFF (Cap: 50)
- **Macro Tilt:** -8
- **Drift:** 👀 EARLY DRIFT / NEUTRAL / NONE
- **Drift Score:** 2
- **Flow Score:** 4
- **Flow Continuity:** 👀 EARLY TRACE → 👀 EARLY TRACE (FLOW_PERSISTENCE, tilt=+1)
- **Flow Regime Tilt:** +3 / Flow-Gamma Tilt: +0

- **🎯 Final Risk Action:** **STRONG REDUCE**
- **Risk Budget (0~100):** **32**
- **Narrative:** 구조=TIGHTENING / 심리=NEUTRAL / 유동성=감소/중간 / 크레딧=안정 / 드리프트=👀 EARLY DRIFT (NEUTRAL) / 수급=1.53 ⚠️ 수급 다소 과열 → Phase=SOFT RISK-OFF

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `TIGHTENING` | **Price(Regime):** `SOFT RISK-OFF` | **Bucket:** `RISK-OFF` | **VIX:** `16.04`
- **Positioning Data:** Z-Score: `1.53` (>1.8 시 Run) | Gamma: `0.50` (<0.5 시 Run) | CTA: `1.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v3.2)
- **정의:** 13번 Risk Budget 실행 브레이크 레이어
- **추가 이유:** 전략 판단(13) 이후 실제 진입 강도를 조절하기 위함

- **Base Risk Budget (13):** 32
- **VIX Level:** 16.04 (NORMAL) | **Change:** -0.19%
- **Positioning Layer:** ⚠️ Positioning Heat(1.53)
- **Brake Drivers:** ⚠️ Positioning Heat

- **📊 Recommended Exposure:** **30%**

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

### 🏭 18) Sector Allocation Engine (v3.3)

**Context:** phase=SOFT RISK-OFF / T10Y2Y=0.37 (MODERATE STEEP) / VIX=16.04 (VOLATILITY NORMAL) / liquidity=DOWN-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM

**Macro Profile:** SOFT_RISK_OFF_DISINFLATION
**Macro Inputs Debug:** phase=SOFT RISK-OFF / us10y_pct=+0.29% / dxy_pct=+0.17% / wti_pct=-3.48% / vix=16.04 / liq_easy=False / liq_tight=True / credit_calm=True / flow_score=4

**Flow Overlay:** flow_score=4 / flow_state=👀 EARLY TRACE / drift_label=NEUTRAL / gamma=🟡 POSITIVE-TRANSITION
**Flow Notes:** NEUTRAL + FLOW ACTIVE → XLK/XLI 소폭 가점 | Gamma POSITIVE → 리더 섹터 가점

**Overweight:** Health Care, Energy

**Underweight:** Utilities, Financials, Consumer Discretionary, Real Estate, Consumer Staples, Materials, Industrials, Technology

**Scoreboard:**
- Health Care: +1.7  (+2 LIQ, +1.2 PHASE, +1 MOM, = +1.7)
- Energy: +0.4  (+1 MOM, = +0.4)
- Technology: -0.2  (-2 LIQ, +0.5 PHASE, +1.5 FLOW, +1 MOM, = -0.2)
- Industrials: -0.3  (+1 CURVE, -0.5 PHASE, +1 FLOW, -2 MOM, = -0.3)
- Materials: -0.6  (-2 MOM, = -0.6)
- Consumer Staples: -1.2  (+2 LIQ, +0.8 PHASE, -1 MOM, = -1.2)
- Consumer Discretionary: -1.7  (-1 LIQ, -0.5 PHASE, -2 MOM, = -1.7)
- Real Estate: -1.7  (-1.5 LIQ, -2 MOM, = -1.7)
- Financials: -1.9  (+2 CURVE, -2 MOM, = -1.9)
- Utilities: -2.4  (+1 LIQ, -2 MOM, = -2.4)

**Rationale (Why the score exists: 섹터 점수의 핵심 드라이버)**
- OW Health Care: FLOW_WEAK → 이론상 우호하나 실제 자금 유입 확인 부족
- OW Health Care: +2: 유동성 긴축 → 안정적 현금흐름 선호
- OW Health Care: +1.2: Soft Risk-Off Disinflation → 금리 안정/퀄리티 방어 우위
- OW Energy: TACTICAL_MOMENTUM_ONLY → 거시 근거 약하지만 단기 리더십 존재
- OW Energy: +1: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- UW Utilities: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Utilities: +1: 유동성 긴축 → 방어주 버퍼
- UW Utilities: -2: Relative Strength 약세 (vs SPY) → 소외 섹터
- UW Financials: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Financials: +2: 완만한 스티프닝(0.37) → 예대마진 개선
- UW Financials: -2: Relative Strength 약세 (vs SPY) → 소외 섹터
- UW Consumer Discretionary: -1: 유동성 긴축 → 경기민감 소비 부담
- UW Consumer Discretionary: -0.5: Soft Risk-Off Disinflation → 소비 베타는 일부 제한

**Regime Controller:**
- DISLOCATION (avg_divergence=-1.02, dispersion=1.82)
- Correlation Break: False / Type=NONE
- Interpretation: 섹터별 괴리가 큰 불안정 장세 → 포지션 축소와 리더 섹터 검증 필요

**Divergence / Classification Monitor (Theory vs Flow alignment: 이론과 실제 자금흐름 정렬 여부)**
- Health Care: FLOW_WEAK (theory=+3.2, flow=+0.7, final=+1.7)
- Energy: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+0.7, final=+0.4)
- Communication Services: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Consumer Staples: THEORY_TRAP (theory=+2.8, flow=-0.7, final=-1.2)
- Consumer Discretionary: AVOID (theory=-1.5, flow=-1.4, final=-1.7)
- Real Estate: AVOID (theory=-1.5, flow=-1.4, final=-1.7)
- Financials: THEORY_TRAP (theory=+2.0, flow=-1.4, final=-1.9)
- Utilities: THEORY_TRAP (theory=+1.0, flow=-1.4, final=-2.4)

### 💰 18.5) Tactical Asset Allocation (Execution Weight)
- **Strategic Exposure (15):** **30.0%** → **Regime Adjusted:** **30.0%**
- **Exposure Override:** DISLOCATION → Sector Weight Only (No Exposure Change)

| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |
| :--- | :---: | :---: | :---: | :--- |
| Health Care | +1.7 | NEGATIVE_DIVERGENCE | **18.0%** | HOLD |
| Energy | +0.4 | POSITIVE_DIVERGENCE | **7.4%** | NEW |
| **Cash & Hedge** | - | - | **69.5%** | DEFENSIVE |

- **Allocation Check:** Sector Weights + Cash = **100.0%**
- **Regime Cap Profile:** SOFT_RISK_OFF_DISINFLATION
- **Regime Cap Applied:** None
- **Strategic Cash (15):** 70.0%
- **Tactical Reserve (Cap / Unallocated):** -0.5%


**Deleveraging Priority Preview:**
- 기준: Divergence → Momentum → Score → Current Weight
1. Health Care (priority_score=3.32, score=1.71, weight=18.0%, div=NEGATIVE_DIVERGENCE, mom=1)
2. Technology (priority_score=0.24, score=-0.16, weight=5.1%, div=ALIGNED, mom=0)
3. Energy (priority_score=-3.19, score=0.38, weight=7.4%, div=POSITIVE_DIVERGENCE, mom=1)

**Leveraging Priority Preview:**
- 기준: Score → Momentum → Positive Divergence
1. Energy (priority_score=2.88, score=0.38, weight=7.4%, div=POSITIVE_DIVERGENCE, mom=1)
2. Health Care (priority_score=0.21, score=1.71, weight=18.0%, div=NEGATIVE_DIVERGENCE, mom=1)
3. Technology (priority_score=-0.16, score=-0.16, weight=5.1%, div=ALIGNED, mom=0)
- **Divergence Adjustment:** Health Care penalized in weight sizing

### 🧬 19) Execution Layer (ETF Mapping)

| Sector | ETF | Weight | Action | Divergence | Classification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| Health Care | XLV | 17.7% | DEFENSIVE_QUALITY | NEGATIVE_DIVERGENCE | FLOW_WEAK |
| Energy | XLE | 7.3% | TACTICAL_ONLY | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Technology | XLK | 5.0% | SMALL | ALIGNED | ALIGNED |


### 🧬 19.5) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Execution Notes:**
- Early flow trace → maintain leaders, wait for confirmation before broadening.
- Exposure below 45% → defensive execution; cash remains strategic asset.

**Preferred Company Traits:**
- High Free Cash Flow generators
- Net cash or low leverage balance sheets
- Stable margins / pricing power
- Low to mid beta exposure
- RAROC-friendly profile
- Cash flow visibility and earnings stability
- Leaders with improving breadth confirmation
- Smaller position sizes with strict risk budget discipline

**Risk Control / Avoid:**
- Negative FCF / cash-burn models
- High leverage / refinancing-dependent names
- Long-duration, high-multiple growth
- Rate-sensitive long-duration equities
- Broad beta expansion before confirmation

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** HIGH
- **Z-Score (1d):** -0.056926352388859104
- **Z-Score (5d):** -2.6834719517373227

### EEM
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 0.1922985554630534
- **Z-Score (5d):** -0.9425296226664576

### EIS
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 0.06263018262528708
- **Z-Score (5d):** -2.105535035940452

### EMB
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 0.025255135330763956
- **Z-Score (5d):** -3.119337612667687

### EWJ
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.27863655493612755
- **Z-Score (5d):** -1.1540929996969873

### FXI
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.9025853076655306
- **Z-Score (5d):** -1.5099106105628257

### GLD
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.8327360845903914
- **Z-Score (5d):** -1.4245704468480926

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.3135072363420677
- **Z-Score (5d):** -0.9628344762389504

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.11118399223844
- **Z-Score (5d):** 1.0175855540646743
