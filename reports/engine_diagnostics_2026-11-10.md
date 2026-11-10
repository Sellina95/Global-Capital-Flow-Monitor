# ENGINE DIAGNOSTICS
**Date:** 2026-11-10
**Data as of:** 2026-11-09

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: ✅ STABLE**
> **판단 요약: 구조-가격-수급 정렬 / 실시간 이상징후 없음 / 데드맨 정상**
### 🎯 Exposure Framework
- **Base Exposure (전략 기준): 61%**
- **Final Exposure (실행 기준): 61%**

- **Portfolio Stance:** HOLD / 61%

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
  - Leadership Breadth → **BROAD_LEADERSHIP** (Leadership is broadening across sectors, confirming healthier market participation.)
  - Positioning Stress → **SQUEEZE_RISK** (Positioning is stretched and vulnerable to squeeze-driven reversals.)

## 🎯 Final Decision (War Room Override)
- **Final Action:** **HOLD**
- **Final Exposure:** **61%**
- **Base Context:** phase=TRANSITION / MIXED / narrative=HOLD / base_exposure=61%
- **SEW:** STABLE / NORMAL
- **Divergence:** ALIGNED / **STAY (포지션 유지)**
- **Drift:** 🔥 EXTREME DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK / score=8
- **Flow:** 🔥 BUILDING HARD / score=7
- **Gamma:** 🟡 TRANSITION
- **Tactical Action:** HOLD / NONE / LOW
- **Positioning:** pos_z=0.83
- **Warning Score:** 0 (No warning)
- **Tactical Why:** No actionable alignment
- **Why:** SEW STABLE → 실시간 이상징후 없음 → Divergence ALIGNED → 구조·가격·수급 정렬 → Narrative Action=HOLD 반영 → Tactical=HOLD / Flow=🔥 BUILDING HARD(7) / Drift=🔥 EXTREME DRIFT(8) / Gamma=🟡 TRANSITION → Tactical HOLD/MONITOR → 최종판단 변경 없음

### 🚩 Market Regime Status
- **국면 전환 감지:** 🚨 **TRANSITION / MIXED (전환·혼조)** → **TRANSITION / MIXED**
- **Structural Regime:** **UNKNOWN_TRANSITION**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.864  (+0.10% vs 4.859)
- **달러 인덱스**: 101.650  (-0.64% vs 102.300)
- **WTI 유가**: 86.850  (-4.38% vs 90.830)
- **변동성 지수 (VIX)**: 19.920 (-22.31% vs 25.640)
- **원/달러 환율**: 1362.700  (+0.47% vs 1356.340)

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 19.92 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(↑) / DXY(↓) / VIX(↓)
- **판정:** **TRANSITION / MIXED | Flow:  (Flow Weak)**
- **근거:** Macro Narrative=UNKNOWN_TRANSITION / Policy=MIXED / Credit=WATCH

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↑) / DXY(↓) / VIX(↓)
- **현실(FCI):** value=-0.459 / level=EASY (완화) / update=low-frequency | as of: 2026-11-10 (latest available)
- **유인(Real Rates):** value=2.630 / level=RESTRICTIVE (유인↓) / dir(→) | as of: 2026-11-10 (latest available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI는 저빈도 금융환경 프록시로 level 중심 해석, Real Rates는 영업일 기준 변화 방향을 함께 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↑) / DXY(↓) / VIX(↓)
- **Policy Bias: MIXED (혼조) (WEAK, score=-0.5) | REAL_RATEΔ +0.000 / FCI value=-0.459 (low-frequency) / DXYΔ -0.650 / US10YΔ +0.005**
- **Expectations: dict received.**

- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리/달러/변동성 신호가 완전히 정렬되지 않음
- **한줄요약 ~~** 구조=MIXED (혼조)(WEAK)는 참고, 가격=POLICY MIXED (정책 신호 혼조) 중심 → 최종 POLICY MIXED (정책 신호 혼조)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-11-04 (FRED latest)
- **NET_LIQ level:** 5790969.8
- **TGA level:** 957175.0
- **RRP level:** 0.225
- **방향(전일 대비):** TGA(↓) / RRP(↑) / NET_LIQ(↑)
- **판정:** **LIQUIDITY SUPPORTIVE (완만한 유동성 우호)**
- **근거:** Net Liquidity↑ → 시장 내 달러 여력 개선
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-11-06 (FRED latest)
- **HY_OAS level:** 3.42% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↓) / -1.72%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 좁혀지는 중 → 공포 온도 완화
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↑) / LQD(↑)
- **HYG:** today 77.510 / prev 77.230 / pct 0.36%
- **LQD:** today 104.670 / prev 104.530 / pct 0.13%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Clear, +0.10%)** → 완화 기대 약화/금리 부담
- DXY **(Strong, -0.64%)** → 달러 약세/리스크 선호
- WTI **(Strong, -4.38%)** → 물가 부담 완화
- VIX **(Strong, -22.31%)** → 심리 개선/리스크온
- 원/달러(USDKRW) **(Clear, +0.47%)** → 원화 약세/수급 부담
- HYG (High Yield ETF) **(Mild, +0.36%)** → 크레딧 위험선호↑
- LQD (IG Bond ETF) **(Mild, +0.13%)** → 우량채 강세(리스크오프 성향)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 상승(US10Y↑)** → 실질 금리 압박 → 달러 강세(DXY↑) 유도: **신흥국 자본 유출 및 고밸류 성장주 할인율 부담 증가**
- **변동성 하락(VIX↓)** → 심리 개선(Risk-On): **자산군 전반의 위험 수용 여력(Risk Appetite) 회복 및 랠리 지속 가능성**
- **유가 하락(WTI↓)** → 물가 부담 완화: **실질 구매력 회복 및 긴축 압력 완화(Dovish Tilt) 가능성 시사**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### 🌊 Drift Monitor (v4)
- **정의:** 누적 흐름 + ATR 기반 강도 감지

- **SPY:** 🟢 UP | Short-term: SHORT DOWN | 1D=+2.36% / 5D=+0.07% | Strength: LOW
- **WTI:** 🔴 DOWN | Short-term: MIXED | 1D=-1.75% / 5D=-11.20% | Strength: HIGH
- **DXY:** 🔴 DOWN | Short-term: SHORT DOWN | 1D=-0.10% / 5D=-0.31% | Strength: LOW
- **GOLD:** 🟢 UP | Short-term: SHORT DOWN | 1D=+0.21% / 5D=+4.64% | Strength: MEDIUM

- **Drift Score:** 8
- **State:** **🔥 EXTREME DRIFT**
- **Label:** NEUTRAL
- **SEW Combo Signal:** 🟢 EARLY FLOW WITHOUT SHOCK

- **Market Drift Summary:**
  - Equity (SPY): 🟢 UP / SHORT DOWN
  - Oil (WTI): 🔴 DOWN / MIXED
  - Dollar (DXY): 🔴 DOWN / SHORT DOWN
  - Gold (GOLD): 🟢 UP / SHORT DOWN

- **Drivers:**
  - SPY positive drift
  - Credit supports risk
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
- **금리 상승(US10Y↑)** → 할인율 부담/유동성 압박 가능
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 하락(WTI↓)** → 물가 부담 완화 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **-0.32**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** +0.59
- **Geo Momentum:** -0.91 *(Status: FALLING)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** China_Trade_2018
- **Cosine Similarity Score:** -0.134
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - China_Trade_2018: -0.134
  - Taiwan_Tension: -0.180
  - Israel_2023: -0.204
- **Top Drivers:**
  - VIX: z_used=-1.51 (z1d=-2.01, z5d=-0.77, raw_w=0.18, norm_w=0.14) → contrib=-0.21
  - EMB: z_used=-1.46 (z1d=+1.63, z5d=+1.19, raw_w=0.12, norm_w=0.09) → contrib=-0.13
  - WTI: z_used=-1.59 (z1d=-1.57, z5d=-1.61, raw_w=0.10, norm_w=0.08) → contrib=-0.12
  - GOLD: z_used=+1.14 (z1d=+0.81, z5d=+1.64, raw_w=0.12, norm_w=0.09) → contrib=+0.11
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스는 여전히 정상 범위에 있지만 최근 압력이 완화되고 있는 중입니다. 경계 유지.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **China_Trade_2018** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (GLD)
- **Extreme Country Risk:** GLD

### ⚡ 7.3) Pseudo Gamma Filter
- **정의:** 옵션 데이터 없이 시장의 감마 환경을 추론
- **주의:** Dealer Gamma Bias 숫자와 Pseudo Gamma State는 서로 다른 레이어

- **Pseudo Gamma State:** 🟡 TRANSITION
- **Dealer Gamma Bias:** 0.61 (NEUTRAL / transition zone)
- **Bias:** 초기 방향성 형성 / 감마 전환 구간
- **Strategy:** 포지션 확대 신중 / 초기 진입 구간

- **Drift Score:** 8 (🔥 EXTREME DRIFT)
- **VIX:** 19.920000076293945
- **SEW:** STABLE / NORMAL

- **🚀 Combo Signal:** 🟢 EARLY FLOW WITHOUT SHOCK

### 🏦 Institutional Flow Engine (v2-minimal)
- **정의:** 기관성 자금이 뉴스 전에 남기는 흔적을 구조적으로 탐지

- **Raw Flow State:** **🔥 BUILDING HARD**
- **Transition State:** **CONFIRMED_FLOW**
- **Flow Delta:** +0 (prev=7 → current=7)
- **Persistence Days:** 6
- **Transition Note:** 기관성 흐름이 높은 강도로 확인
- **Confidence:** **HIGH**
- **Action Bias:** **EARLY PREP**

- **Drift:** 🔥 EXTREME DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK
- **Gamma:** 🟡 TRANSITION / 🟢 EARLY FLOW WITHOUT SHOCK
- **SEW:** STABLE / NORMAL
- **Positioning (POS_Z):** 0.83
- **Validation Score:** 3 (boost applied: +2)

- **Drivers:**
  - Drift strong
  - Gamma transition
  - No shock yet
  - Cross-asset risk participation
  - Credit confirms risk appetite
  - Leadership breadth expanding

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(32.00bp) | 실질금리(2.63%) | DXY(101.65)
*(as of: RealRate: 2026-11-10 / FRED last available)*

❌ **자본이 탈출하는 곳 (Short Incentive):**
고금리(실질금리 2% 상회) 부담으로 인한 리스크 오프 신호

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** 금리↑ + 달러↓ + 유가↓ + VIX↓
- **최종 판정:** **매크로 지표 혼조 속 시장 심리 개선 주도**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Clear) / DXY(Strong) / WTI(Strong) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.864), DXY(101.650), VIX(19.92)

### 🏗️ 12) Structural Filter (v3)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↓) / GOLD(↑) / VIX(↓) / WTI(↓)
- **Meaningful Move Check:** DXY=-0.6353875918752843 / GOLD=0.9718054088512288 / US10Y=0.10289436904309317 / VIX=-22.308890208725245 / WTI=-4.381815784102335
- **판정:** **NEUTRAL**
- **근거:** 글로벌 매크로 구조의 특이 신호가 감지되지 않음



### 12.5) Growth Sustainability Filter [SHADOW]
- **Score:** 3
- **Label:** FRAGILE_EXPANSION
- **Demand Proxy:** 1
- **Financing:** 0
- **Energy Burden:** -1
- **Policy Capacity:** 3
- **Strategic Interpretation:** Expansion remains possible, but the growth structure is not yet broad or durable. Monitor demand confirmation.
- **Input Check:** US10Y=4.863999843597412, RealYield=2.63, T10Y2Y=0.32, WTI=86.8499984741211, DXY=101.6500015258789, LiquidityDir=UP, CreditCalm=True, HY_OAS=3.42, DriftLabel=NEUTRAL, FredAsof=2026-11-09

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.




### 12.8) Positioning Stress Filter [SHADOW]

- **Score:** 0
- **Label:** SQUEEZE_RISK
- **Strategic Interpretation:** Positioning is stretched and vulnerable to squeeze-driven reversals.

**Positioning Notes**
- Term Structure: VIX3M-VIX=0.93 → mild contango
- Short-Term Hedge: VIX9D/VIX=1.00 → neutral short-term hedge
- Gamma Structure: Positive gamma mild
- Positioning: Neutral positioning

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.



### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** 3
- **Label:** EARLY_ROTATION
- **Strategic Interpretation:** Participation is emerging, but confirmation remains limited.
- **Breadth / Participation:** -1
- **Breadth Note:** RSP-SPY return spread=-0.10%p → neutral breadth
- **Nasdaq Breadth Note:** QQQE-QQQ return spread=-0.39%p → mega-cap concentrated Nasdaq rally
- **Positioning / Gamma:** 0
- **Credit Confirmation:** 2
- **Macro Participation:** 2

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.



### 12.7) Leadership Breadth Filter [SHADOW]
- **Score:** 7
- **Label:** BROAD_LEADERSHIP
- **Strategic Interpretation:** Leadership is broadening across sectors, confirming healthier market participation.

**Leadership Notes**
- QQQ-SPY spread=1.18%p → growth leadership
- SMH-QQQ spread=1.51%p → semiconductor participation strong
- SOXX-QQQ spread=3.95%p → SOX proxy confirms chip breadth
- IWM-SPY spread=0.86%p → small-cap participation confirms broader risk-on
- XLF-SPY spread=-0.91%p → sector diffusion weak
- XLI-SPY spread=1.46%p → sector diffusion positive
- XLY-SPY spread=0.55%p → sector diffusion positive

📌 Shadow Note: This filter checks whether leadership is broadening beyond mega-cap tech/AI. No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.


### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: MIXED (혼조) (WEAK, score=-0.5) | REAL_RATEΔ +0.000 / FCI value=-0.459 (low-frequency) / DXYΔ -0.650 / US10YΔ +0.005 (정상)
- **Sentiment (Fear&Greed):** 33.02731229408654 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** UP (MID)
- **Structural Regime:** UNKNOWN_TRANSITION
- **Operational Phase:** TRANSITION / MIXED (Cap: 65)
- **Macro Tilt:** +0
- **Drift:** 🔥 EXTREME DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK
- **Drift Score:** 8
- **Flow Score:** 7
- **Flow Continuity:** CONFIRMED_FLOW → 🔥 BUILDING HARD (FLOW_PERSISTENCE, tilt=+1)
- **Flow Regime Tilt:** +4 / Flow-Gamma Tilt: +2

- **🎯 Final Risk Action:** **HOLD**
- **Risk Budget (0~100):** **65**
- **Narrative:** 구조=MIXED / 심리=NEUTRAL / 유동성=증가/중간 / 크레딧=안정 / 드리프트=🔥 EXTREME DRIFT (NEUTRAL) / 수급=0.83 → Phase=TRANSITION / MIXED

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `MIXED` | **Price(Regime):** `TRANSITION / MIXED` | **Bucket:** `MIXED` | **VIX:** `19.92`
- **Positioning Data:** Z-Score: `0.83` (>1.8 시 Run) | Gamma: `0.61` (<0.5 시 Run) | CTA: `0.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v3.2)
- **정의:** 13번 Risk Budget 실행 브레이크 레이어
- **추가 이유:** 전략 판단(13) 이후 실제 진입 강도를 조절하기 위함

- **Base Risk Budget (13):** 65
- **VIX Level:** 19.92 (NORMAL) | **Change:** -22.31%
- **Positioning Layer:** ⚠️ Bearish CTA(0.0)
- **Brake Drivers:** ⚠️ Bearish CTA

- **📊 Recommended Exposure:** **61%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **VALUE TILT**
- **Duration Tilt:** **SHORT DURATION FAVORED**
- **Cyclical vs Defensive:** **NEUTRAL**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** SHORT DURATION FAVORED
- **Inflation Factor:** NEUTRAL
- **USD Factor:** USD EASING
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.3)

**Context:** phase=TRANSITION / MIXED / T10Y2Y=0.32 (MODERATE STEEP) / VIX=19.92 (VOLATILITY NORMAL) / liquidity=UP-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM

**Macro Profile:** BALANCED
**Macro Inputs Debug:** phase=TRANSITION / MIXED / us10y_pct=+0.10% / dxy_pct=-0.64% / wti_pct=-4.38% / vix=19.92 / liq_easy=True / liq_tight=False / credit_calm=True / flow_score=7

**Flow Overlay:** flow_score=7 / flow_state=🔥 BUILDING HARD / drift_label=NEUTRAL / gamma=🟡 TRANSITION
**Flow Notes:** NEUTRAL + FLOW ACTIVE → XLK/XLI 소폭 가점 | Gamma TRANSITION → 초기 리더 소폭 가점

**Overweight:** Financials, Consumer Discretionary, Industrials, Consumer Staples, Health Care, Materials, Real Estate, Utilities

**Underweight:** Technology, Communication Services

**Scoreboard:**
- Financials: +2.2  (+1 LIQ, +2 CURVE, +2 MOM, = +2.2)
- Consumer Discretionary: +1.3  (+1.5 LIQ, +2 MOM, = +1.3)
- Industrials: +1.1  (+1.5 LIQ, +1 CURVE, +0.5 FLOW, = +1.1)
- Consumer Staples: +0.9  (+0.5 PHASE, +2 MOM, = +0.9)
- Health Care: +0.9  (+0.5 PHASE, +2 MOM, = +0.9)
- Materials: +0.8  (+2 MOM, = +0.8)
- Real Estate: +0.8  (+2 MOM, = +0.8)
- Utilities: +0.2  (-1 LIQ, +2 MOM, = +0.2)
- Communication Services: -0.3  (-1 MOM, = -0.3)
- Technology: -1.8  (+2 LIQ, +1 FLOW, -2 MOM, = -1.8)

**Rationale (Why the score exists: 섹터 점수의 핵심 드라이버)**
- OW Financials: +1: 유동성 완화 → 위험선호 회복
- OW Financials: +2: 완만한 스티프닝(0.32) → 예대마진 개선
- OW Consumer Discretionary: +1.5: 유동성 완화 → 소비 민감주 우호
- OW Consumer Discretionary: +2: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- OW Industrials: FLOW_WEAK → 이론상 우호하나 실제 자금 유입 확인 부족
- OW Industrials: +1.5: 유동성 완화 → 경기민감 회복
- OW Industrials: +1: 완만한 스티프닝(0.32) → 성장 기대 반영
- OW Consumer Staples: TACTICAL_MOMENTUM_ONLY → 거시 근거 약하지만 단기 리더십 존재
- OW Consumer Staples: +0.5: Balanced Macro Profile → 방어 보완
- OW Consumer Staples: +2: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- UW Technology: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Technology: +2: 유동성 완화 → 성장주/베타 우호
- UW Technology: +0.5: Flow Overlay → 초기 흐름에서 성장주 선행 반응

**Regime Controller:**
- DISLOCATION (avg_divergence=-0.08, dispersion=1.64)
- Correlation Break: False / Type=NONE
- Interpretation: 섹터별 괴리가 큰 불안정 장세 → 포지션 축소와 리더 섹터 검증 필요

**Divergence / Classification Monitor (Theory vs Flow alignment: 이론과 실제 자금흐름 정렬 여부)**
- Financials: HIGH_CONVICTION_ALIGNED (theory=+3.0, flow=+1.4, final=+2.2)
- Industrials: FLOW_WEAK (theory=+2.5, flow=+0.1, final=+1.1)
- Consumer Staples: TACTICAL_MOMENTUM_ONLY (theory=+0.5, flow=+1.4, final=+0.9)
- Health Care: TACTICAL_MOMENTUM_ONLY (theory=+0.5, flow=+1.4, final=+0.9)
- Materials: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+1.4, final=+0.8)
- Real Estate: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+1.4, final=+0.8)
- Energy: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Technology: THEORY_TRAP (theory=+2.0, flow=-1.1, final=-1.8)

### 💰 18.5) Tactical Asset Allocation (Execution Weight)
- **Strategic Exposure (15):** **61.0%** → **Regime Adjusted:** **61.0%**
- **Exposure Override:** DISLOCATION → Sector Weight Only (No Exposure Change)

| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |
| :--- | :---: | :---: | :---: | :--- |
| Financials | +2.2 | ALIGNED | **5.8%** | HOLD |
| Consumer Discretionary | +1.3 | ALIGNED | **1.4%** | HOLD |
| Consumer Staples | +0.9 | POSITIVE_DIVERGENCE | **4.3%** | HOLD |
| Health Care | +0.9 | POSITIVE_DIVERGENCE | **1.7%** | HOLD |
| Materials | +0.8 | POSITIVE_DIVERGENCE | **1.5%** | HOLD |
| Utilities | +0.2 | ALIGNED | **1.1%** | HOLD |
| **Cash & Hedge** | - | - | **81.9%** | DEFENSIVE |

- **Allocation Check:** Sector Weights + Cash = **100.0%**
- **Regime Cap Profile:** BALANCED
- **Participation / Quality Cap Applied:**
  - Financials: 18.2% → 10.0% (-8.2%)
- **Strategic Cash (15):** 39.0%
- **Tactical Reserve (Cap / Unallocated):** 42.9%


**Deleveraging Priority Preview:**
- 기준: Divergence → Momentum → Score → Current Weight
1. Communication Services (priority_score=0.48, score=-0.32, weight=0.8%, div=ALIGNED, mom=0)
2. Energy (priority_score=0.0, score=0.0, weight=1.5%, div=ALIGNED, mom=0)
3. Utilities (priority_score=-2.09, score=0.18, weight=1.1%, div=ALIGNED, mom=2)
4. Consumer Discretionary (priority_score=-2.65, score=1.3, weight=1.4%, div=ALIGNED, mom=2)
5. Consumer Staples (priority_score=-4.16, score=0.94, weight=4.3%, div=POSITIVE_DIVERGENCE, mom=2)

**Leveraging Priority Preview:**
- 기준: Score → Momentum → Positive Divergence
1. Financials (priority_score=7.25, score=2.25, weight=5.8%, div=ALIGNED, mom=2)
2. Consumer Staples (priority_score=4.94, score=0.94, weight=4.3%, div=POSITIVE_DIVERGENCE, mom=2)
3. Health Care (priority_score=4.94, score=0.94, weight=1.7%, div=POSITIVE_DIVERGENCE, mom=2)
4. Materials (priority_score=4.76, score=0.76, weight=1.5%, div=POSITIVE_DIVERGENCE, mom=2)
5. Consumer Discretionary (priority_score=4.30, score=1.3, weight=1.4%, div=ALIGNED, mom=2)
- **Divergence Adjustment:** Industrials penalized in weight sizing

### 🧬 19) Execution Layer (ETF Mapping)

| Sector | ETF | Weight | Action | Divergence | Classification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| Communication Services | XLC | 0.8% | MICRO | ALIGNED | ALIGNED |
| Consumer Discretionary | XLY | 1.4% | MICRO | ALIGNED | ALIGNED |
| Consumer Staples | XLP | 4.3% | TACTICAL_ONLY | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Energy | XLE | 1.5% | NO_ACTION | ALIGNED | NEUTRAL |
| Financials | XLF | 5.8% | ACCUMULATE | ALIGNED | HIGH_CONVICTION_ALIGNED |
| Health Care | XLV | 1.7% | TACTICAL_ONLY | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Materials | XLB | 1.5% | TACTICAL_ONLY | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Utilities | XLU | 1.1% | MICRO | ALIGNED | ALIGNED |


### 🧬 19.5) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Execution Notes:**
- Flow building → selective expansion allowed if risk controls remain stable.

**Preferred Company Traits:**
- High-conviction leaders with cross-asset confirmation

**Risk Control / Avoid:**
- Unscreened speculative exposure

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.15545493283969553
- **Z-Score (5d):** 0.6971549725778906

### EEM
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.9385800655095973
- **Z-Score (5d):** 0.24052465491575264

### EIS
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.6252395370137527
- **Z-Score (5d):** 0.5955197484755025

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.6564825722116923
- **Z-Score (5d):** 1.171174854108429

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 2.841355774674253
- **Z-Score (5d):** -0.4611265194353585

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.7217165946183245
- **Z-Score (5d):** 1.8356565077008271

### GLD
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 1.2691510075026204
- **Z-Score (5d):** 1.9655370809799517

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 2.624401374436739
- **Z-Score (5d):** 0.26841650448779397

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -2.6292034791974386
- **Z-Score (5d):** -0.2582782992711162
