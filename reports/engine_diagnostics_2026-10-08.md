# ENGINE DIAGNOSTICS
**Date:** 2026-10-08
**Data as of:** 2026-10-07

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: ✅ STABLE**
> **판단 요약: 구조-가격-수급 정렬 / 실시간 이상징후 없음 / 데드맨 정상**
### 🎯 Exposure Framework
- **Base Exposure (전략 기준): 42%**
- **Final Exposure (실행 기준): 42%**

- **Portfolio Stance:** REDUCE / 42%

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
  - Leadership Breadth → **MEGA_CAP_SQUEEZE_RISK** (Leadership is heavily concentrated in mega-cap/AI-related names, increasing squeeze and reversal risk.)
  - Positioning Stress → **SQUEEZE_RISK** (Positioning is stretched and vulnerable to squeeze-driven reversals.)

## 🎯 Final Decision (War Room Override)
- **Final Action:** **REDUCE**
- **Final Exposure:** **42%**
- **Base Context:** phase=SOFT RISK-OFF / narrative=REDUCE / base_exposure=42%
- **SEW:** STABLE / NORMAL
- **Divergence:** ALIGNED / **STAY (포지션 유지)**
- **Drift:** WEAK DRIFT (노이즈 가능) / NEUTRAL / NONE / score=1
- **Flow:** NO CLEAR FLOW / score=0
- **Gamma:** 🟢 POSITIVE GAMMA
- **Tactical Action:** REDUCE / DEFENSIVE / MEDIUM
- **Positioning:** pos_z=1.64
- **Warning Score:** 0 (No warning)
- **Tactical Why:** Risk-off environment
- **Why:** SEW STABLE → 실시간 이상징후 없음 → Divergence ALIGNED → 구조·가격·수급 정렬 → Narrative Action=REDUCE 반영 → Tactical=REDUCE / Flow=NO CLEAR FLOW(0) / Drift=WEAK DRIFT (노이즈 가능)(1) / Gamma=🟢 POSITIVE GAMMA → Tactical REDUCE → 방어 기조 유지 / 총노출 추가 감산 없이 배분 보수화

### 🚩 Market Regime Status
- **국면 전환 감지:** 🚨 **RISK-ON (완화 기대·리스크 선호)** → **SOFT RISK-OFF**
- **Structural Regime:** **TIGHTENING_GROWTH_SCARE**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 5.277  (+0.15% vs 5.269)
- **달러 인덱스**: 102.240  (+0.40% vs 101.830)
- **WTI 유가**: 88.280  (-1.30% vs 89.440)
- **변동성 지수 (VIX)**: 15.080 (+0.47% vs 15.010)
- **원/달러 환율**: 1339.740  (-0.30% vs 1343.750)

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 15.08 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(↑) / DXY(↑) / VIX(↑)
- **판정:** **SOFT RISK-OFF | Flow:  (Flow Weak)**
- **근거:** Macro Narrative=TIGHTENING_GROWTH_SCARE / Policy=MIXED / Credit=WATCH

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↑) / DXY(↑) / VIX(↑)
- **현실(FCI):** value=-0.494 / level=EASY (완화) / update=low-frequency | as of: 2026-10-08 (latest available)
- **유인(Real Rates):** value=2.910 / level=RESTRICTIVE (유인↓) / dir(→) | as of: 2026-10-08 (latest available)
- **판정:** **LIQUIDITY TIGHTENING (유동성 축소)**
- **근거:** 금리↑+달러↑ + (FCI 압박 또는 실질금리 유인↓) → 리스크자산에 불리
- **Note:** FCI는 저빈도 금융환경 프록시로 level 중심 해석, Real Rates는 영업일 기준 변화 방향을 함께 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↑) / DXY(↑) / VIX(↑)
- **Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCI value=-0.494 (low-frequency) / DXYΔ +0.410 / US10YΔ +0.008**
- **Expectations: dict received.**

- **판정:** **POLICY TIGHTENING (긴축)**
- **근거:** 금리↑ + 달러↑ → 긴축 압력
- **한줄요약 ~~** 구조=TIGHTENING (긴축)(MODERATE)는 참고, 가격=POLICY TIGHTENING (긴축) 중심 → 최종 POLICY TIGHTENING (긴축)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-09-30 (FRED latest)
- **NET_LIQ level:** 5794345.5
- **TGA level:** 948674.0
- **RRP level:** 11.539
- **방향(전일 대비):** TGA(↓) / RRP(↑) / NET_LIQ(↑)
- **판정:** **LIQUIDITY SUPPORTIVE (완만한 유동성 우호)**
- **근거:** Net Liquidity↑ → 시장 내 달러 여력 개선
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-10-06 (FRED latest)
- **HY_OAS level:** 3.03% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↓) / -2.88%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 좁혀지는 중 → 공포 온도 완화
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(↓)
- **HYG:** today 77.180 / prev 77.270 / pct -0.12%
- **LQD:** today 102.100 / prev 102.140 / pct -0.04%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, +0.15%)** → 완화 기대 약화/금리 부담
- DXY **(Strong, +0.40%)** → 달러 강세/신흥국 부담
- WTI **(Clear, -1.30%)** → 물가 부담 완화
- VIX **(Mild, +0.47%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Clear, -0.30%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Mild, -0.12%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Noise, -0.04%)** → 우량채 약세(리스크온 성향)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 상승(US10Y↑)** → 실질 금리 압박 → 달러 강세(DXY↑) 유도: **신흥국 자본 유출 및 고밸류 성장주 할인율 부담 증가**
- **변동성 상승(VIX↑)** → 위험회피(Risk-Off) 강화: **안전 자산(Cash/USD) 선호도 급증 및 하이일드 스프레드 확대 압력**
- **유가 하락(WTI↓)** → 물가 부담 완화: **실질 구매력 회복 및 긴축 압력 완화(Dovish Tilt) 가능성 시사**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### 🌊 Drift Monitor (v4)
- **정의:** 누적 흐름 + ATR 기반 강도 감지

- **SPY:** 🟡 PULLBACK | Short-term: MIXED | 1D=-0.25% / 5D=+1.90% | Strength: LOW
- **WTI:** 🟡 REBOUND | Short-term: SHORT UP | 1D=+3.42% / 5D=-1.69% | Strength: MEDIUM
- **DXY:** 🟢 UP | Short-term: SHORT UP | 1D=+0.12% / 5D=+0.26% | Strength: LOW
- **GOLD:** 🟡 REBOUND | Short-term: SHORT DOWN | 1D=+0.08% / 5D=-1.39% | Strength: LOW

- **Drift Score:** 1
- **State:** **WEAK DRIFT (노이즈 가능)**
- **Label:** NEUTRAL
- **SEW Combo Signal:** NONE

- **Market Drift Summary:**
  - Equity (SPY): 🟡 PULLBACK / MIXED
  - Oil (WTI): 🟡 REBOUND / SHORT UP
  - Dollar (DXY): 🟢 UP / SHORT UP
  - Gold (GOLD): 🟡 REBOUND / SHORT DOWN

- **Drivers:**
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
- **유가 하락(WTI↓)** → 물가 부담 완화 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **-0.50**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** -0.57
- **Geo Momentum:** +0.07 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Taiwan_Tension
- **Cosine Similarity Score:** 0.044
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Taiwan_Tension: 0.044
  - China_Trade_2018: 0.039
  - Red_Sea: -0.120
- **Top Drivers:**
  - KR10Y_SPREAD: z_used=-1.95 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.12
  - DE10Y_SPREAD: z_used=-1.98 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=-0.09
  - JP10Y_SPREAD: z_used=-1.98 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=-0.09
  - IL10Y_SPREAD: z_used=-1.96 (mode=level, raw_w=0.05, norm_w=0.04) → contrib=-0.08
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Taiwan_Tension** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (EIS)
- **Extreme Country Risk:** EIS

### ⚡ 7.3) Pseudo Gamma Filter
- **정의:** 옵션 데이터 없이 시장의 감마 환경을 추론
- **주의:** Dealer Gamma Bias 숫자와 Pseudo Gamma State는 서로 다른 레이어

- **Pseudo Gamma State:** 🟢 POSITIVE GAMMA
- **Dealer Gamma Bias:** 1.53 (STABILIZING / dealer gamma proxy supportive)
- **Bias:** Mean-reverting / 딜러가 변동성 흡수
- **Strategy:** 눌림 매수 / 추격 금지

- **Drift Score:** 1 (WEAK DRIFT (노이즈 가능))
- **VIX:** 15.079999923706056
- **SEW:** STABLE / NORMAL

- **🚀 Combo Signal:** 🟢 STABLE FLOW

### 🏦 Institutional Flow Engine (v2-minimal)
- **정의:** 기관성 자금이 뉴스 전에 남기는 흔적을 구조적으로 탐지

- **Raw Flow State:** **NO CLEAR FLOW**
- **Transition State:** **FLOW_BREAK**
- **Flow Delta:** -6 (prev=6 → current=0)
- **Persistence Days:** 0
- **Transition Note:** 전일 형성되던 기관성 흐름이 유지되지 못하고 소멸
- **Confidence:** **LOW**
- **Action Bias:** **IGNORE**

- **Drift:** WEAK DRIFT (노이즈 가능) / NEUTRAL / NONE
- **Gamma:** 🟢 POSITIVE GAMMA / 🟢 STABLE FLOW
- **SEW:** STABLE / NORMAL
- **Positioning (POS_Z):** 1.64
- **Validation Score:** 0 (boost applied: +0)

- **Drivers:**
  - No shock yet
  - Positioning somewhat stretched

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(51.00bp) | 실질금리(2.91%) | DXY(102.24)
*(as of: RealRate: 2026-10-08 / FRED last available)*

❌ **자본이 탈출하는 곳 (Short Incentive):**
고금리(실질금리 2% 상회) 부담으로 인한 리스크 오프 신호

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** 금리↑ + 달러↑ + 유가↓ + VIX↑
- **최종 판정:** **긴축 공포 및 달러 수급 경색에 따른 '위험회피(Risk-Off)'**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Strong) / WTI(Clear) / VIX(Mild)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(5.277), DXY(102.240), VIX(15.08)

### 🏗️ 12) Structural Filter (v3)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↑) / GOLD(↓) / VIX(↑) / WTI(↓)
- **Meaningful Move Check:** DXY=0.40262793414760495 / GOLD=-1.1081631979546556 / US10Y=0.15182951076274454 / VIX=0.46635372256376795 / WTI=-1.2969629141829622
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
- **Input Check:** US10Y=5.276999950408936, RealYield=2.91, T10Y2Y=0.51, WTI=88.27999877929688, DXY=102.23999786376952, LiquidityDir=UP, CreditCalm=True, HY_OAS=3.03, DriftLabel=NEUTRAL, FredAsof=2026-10-07

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.




### 12.8) Positioning Stress Filter [SHADOW]

- **Score:** 0
- **Label:** SQUEEZE_RISK
- **Strategic Interpretation:** Positioning is stretched and vulnerable to squeeze-driven reversals.

**Positioning Notes**
- Term Structure: VIX3M-VIX=2.64 → healthy contango / stable structure
- Short-Term Hedge: VIX9D/VIX=0.78 → calm front-end hedge
- Gamma Structure: Positive gamma extreme → dealer-supported squeeze risk
- Positioning: Elevated long positioning

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.



### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** 1
- **Label:** EARLY_ROTATION
- **Strategic Interpretation:** Participation is emerging, but confirmation remains limited.
- **Breadth / Participation:** -3
- **Breadth Note:** RSP-SPY return spread=-0.57%p → narrow cap-weight leadership
- **Nasdaq Breadth Note:** QQQE-QQQ return spread=-0.64%p → mega-cap concentrated Nasdaq rally
- **Positioning / Gamma:** 0
- **Credit Confirmation:** 2
- **Macro Participation:** 2

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.



### 12.7) Leadership Breadth Filter [SHADOW]
- **Score:** -6
- **Label:** MEGA_CAP_SQUEEZE_RISK
- **Strategic Interpretation:** Leadership is heavily concentrated in mega-cap/AI-related names, increasing squeeze and reversal risk.

**Leadership Notes**
- QQQ-SPY spread=-0.01%p → neutral growth leadership
- SMH-QQQ spread=-0.93%p → AI/tech rally not semiconductor-broad
- SOXX-QQQ spread=-0.87%p → chip breadth lagging
- IWM-SPY spread=-1.05%p → small-cap lag, narrow leadership risk
- XLF-SPY spread=-0.24%p → sector diffusion neutral
- XLI-SPY spread=-1.94%p → sector diffusion weak
- XLY-SPY spread=-0.08%p → sector diffusion neutral

📌 Shadow Note: This filter checks whether leadership is broadening beyond mega-cap tech/AI. No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.


### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCI value=-0.494 (low-frequency) / DXYΔ +0.410 / US10YΔ +0.008 (정상)
- **Sentiment (Fear&Greed):** 68.78608136385444 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** UP (MID)
- **Structural Regime:** TIGHTENING_GROWTH_SCARE
- **Operational Phase:** SOFT RISK-OFF (Cap: 45)
- **Macro Tilt:** -8
- **Drift:** WEAK DRIFT (노이즈 가능) / NEUTRAL / NONE
- **Drift Score:** 1
- **Flow Score:** 0
- **Flow Continuity:** CONFIRMED_FLOW → NO CLEAR FLOW (N/A, tilt=+0)
- **Flow Regime Tilt:** +0 / Flow-Gamma Tilt: +0

- **🎯 Final Risk Action:** **REDUCE**
- **Risk Budget (0~100):** **43**
- **Narrative:** 구조=TIGHTENING / 심리=NEUTRAL / 유동성=증가/중간 / 크레딧=안정 / 드리프트=WEAK DRIFT (노이즈 가능) (NEUTRAL) / 수급=1.64 ⚠️ 수급 다소 과열 → Phase=SOFT RISK-OFF

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `TIGHTENING` | **Price(Regime):** `SOFT RISK-OFF` | **Bucket:** `RISK-OFF` | **VIX:** `15.08`
- **Positioning Data:** Z-Score: `1.64` (>1.8 시 Run) | Gamma: `1.53` (<0.5 시 Run) | CTA: `1.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v3.2)
- **정의:** 13번 Risk Budget 실행 브레이크 레이어
- **추가 이유:** 전략 판단(13) 이후 실제 진입 강도를 조절하기 위함

- **Base Risk Budget (13):** 43
- **VIX Level:** 15.08 (NORMAL) | **Change:** +0.47%
- **Positioning Layer:** ⚠️ Positioning Heat(1.64), Positive Gamma(1.53)
- **Brake Drivers:** ⚠️ Positioning Heat

- **📊 Recommended Exposure:** **42%**

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
- **USD Factor:** USD TIGHTENING
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.3)

**Context:** phase=SOFT RISK-OFF / T10Y2Y=0.51 (MODERATE STEEP) / VIX=15.08 (VOLATILITY NORMAL) / liquidity=UP-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM

**Macro Profile:** SOFT_RISK_OFF_DISINFLATION
**Macro Inputs Debug:** phase=SOFT RISK-OFF / us10y_pct=+0.15% / dxy_pct=+0.40% / wti_pct=-1.30% / vix=15.08 / liq_easy=True / liq_tight=False / credit_calm=True / flow_score=0

**Flow Overlay:** flow_score=0 / flow_state=NO CLEAR FLOW / drift_label=NEUTRAL / gamma=🟢 POSITIVE GAMMA

**Overweight:** Technology, Health Care, Consumer Staples

**Underweight:** Consumer Discretionary, Utilities, Industrials, Materials, Real Estate, Financials, Communication Services

**Scoreboard:**
- Technology: +2.5  (+2 LIQ, +0.5 PHASE, +2 MOM, = +2.5)
- Health Care: +0.9  (+1.2 PHASE, = +0.9)
- Consumer Staples: +0.4  (+0.8 PHASE, -1 MOM, = +0.4)
- Communication Services: -0.2  (-1 MOM, = -0.2)
- Financials: -0.3  (+1 LIQ, +2 CURVE, -2 MOM, = -0.3)
- Materials: -0.3  (-2 MOM, = -0.3)
- Real Estate: -0.3  (-2 MOM, = -0.3)
- Industrials: -1.0  (+1.5 LIQ, +1 CURVE, -0.5 PHASE, -2 MOM, = -1.0)
- Utilities: -1.6  (-1 LIQ, -2 MOM, = -1.6)
- Consumer Discretionary: -1.6  (+1.5 LIQ, -0.5 PHASE, -1 MOM, = -1.6)

**Rationale (Why the score exists: 섹터 점수의 핵심 드라이버)**
- OW Technology: +2: 유동성 완화 → 성장주/베타 우호
- OW Technology: +0.5: Soft Risk-Off Disinflation → 금리 안정으로 리더 섹터 일부 유지
- OW Health Care: +1.2: Soft Risk-Off Disinflation → 금리 안정/퀄리티 방어 우위
- OW Consumer Staples: +0.8: Soft Risk-Off Disinflation → 필수소비 방어 보완
- OW Consumer Staples: -1: Relative Strength 약세 (vs SPY) → 소외 섹터
- UW Consumer Discretionary: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Consumer Discretionary: +1.5: 유동성 완화 → 소비 민감주 우호
- UW Consumer Discretionary: -0.5: Soft Risk-Off Disinflation → 소비 베타는 일부 제한
- UW Utilities: -1: 유동성 완화 → 방어주 상대매력 저하
- UW Utilities: -2: Relative Strength 약세 (vs SPY) → 소외 섹터
- UW Industrials: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Industrials: +1.5: 유동성 완화 → 경기민감 회복
- UW Industrials: +1: 완만한 스티프닝(0.51) → 성장 기대 반영

**Regime Controller:**
- THEORY_MARKET (avg_divergence=-1.56, dispersion=1.22)
- Correlation Break: False / Type=NONE
- Interpretation: 거시/이론 조건이 자금흐름보다 우세한 장세 → 보수적 해석과 방어적 배분 필요

**Divergence / Classification Monitor (Theory vs Flow alignment: 이론과 실제 자금흐름 정렬 여부)**
- Technology: HIGH_CONVICTION_ALIGNED (theory=+2.5, flow=+1.4, final=+2.5)
- Energy: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Financials: THEORY_TRAP (theory=+3.0, flow=-1.4, final=-0.3)
- Industrials: THEORY_TRAP (theory=+2.0, flow=-1.4, final=-1.0)
- Utilities: AVOID (theory=-1.0, flow=-1.4, final=-1.6)
- Consumer Discretionary: THEORY_TRAP (theory=+1.0, flow=-0.7, final=-1.6)

### 💰 18.5) Tactical Asset Allocation (Execution Weight)
- **Strategic Exposure (15):** **42.0%** → **Regime Adjusted:** **42.0%**
- **Exposure Override:** THEORY_MARKET → Sector Weight Only (No Exposure Change)

| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |
| :--- | :---: | :---: | :---: | :--- |
| Technology | +2.5 | ALIGNED | **0.0%** | NEW |
| Health Care | +0.9 | ALIGNED | **8.9%** | NEW |
| Consumer Staples | +0.4 | ALIGNED | **4.3%** | NEW |
| **Cash & Hedge** | - | - | **86.8%** | DEFENSIVE |

- **Allocation Check:** Sector Weights + Cash = **100.0%**
- **Regime Cap Profile:** SOFT_RISK_OFF_DISINFLATION
- **Participation / Quality Cap Applied:**
  - Technology: 28.8% → 28.0% (-0.8%)
  - Technology: 28.0% → 0.0% (-28.0%)
- **Strategic Cash (15):** 58.0%
- **Tactical Reserve (Cap / Unallocated):** 28.8%


**Deleveraging Priority Preview:**
- 기준: Divergence → Momentum → Score → Current Weight
1. Consumer Staples (priority_score=1.28, score=0.43, weight=4.3%, div=ALIGNED, mom=-1)
2. Health Care (priority_score=0.23, score=0.9, weight=8.9%, div=ALIGNED, mom=0)
3. Technology (priority_score=-8.0, score=2.52, weight=0.0%, div=ALIGNED, mom=2)

**Leveraging Priority Preview:**
- 기준: Score → Momentum → Positive Divergence
1. Technology (priority_score=7.52, score=2.52, weight=0.0%, div=ALIGNED, mom=2)
2. Health Care (priority_score=0.90, score=0.9, weight=8.9%, div=ALIGNED, mom=0)
3. Consumer Staples (priority_score=0.43, score=0.43, weight=4.3%, div=ALIGNED, mom=-1)

### 🧬 19) Execution Layer (ETF Mapping)

| Sector | ETF | Weight | Action | Divergence | Classification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| Health Care | XLV | 8.9% | DEFENSIVE_QUALITY | ALIGNED | ALIGNED |
| Consumer Staples | XLP | 4.3% | DEFENSIVE_BUFFER | ALIGNED | ALIGNED |


### 🧬 19.5) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Execution Notes:**
- Flow weak → avoid chasing; keep only proven leaders.
- Exposure below 45% → defensive execution; cash remains strategic asset.

**Preferred Company Traits:**
- Cash flow visibility and earnings stability
- Market leaders with confirmed relative strength
- Smaller position sizes with strict risk budget discipline

**Risk Control / Avoid:**
- Rate-sensitive long-duration equities
- Flow-weak cyclicals and theory-only sector bets

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.062142997350074516
- **Z-Score (5d):** 0.7105804213130105

### EEM
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.9740880148527876
- **Z-Score (5d):** 0.23739135237116513

### EIS
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -1.4067503969518471
- **Z-Score (5d):** -1.3979867916221873

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.3400857059039304
- **Z-Score (5d):** 0.9644857907588315

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.8847163586108342
- **Z-Score (5d):** 0.1787714398441854

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.937138569600652
- **Z-Score (5d):** -0.7991266123445876

### GLD
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -1.1164312607859979
- **Z-Score (5d):** -0.45632631902030796

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.43681818523813315
- **Z-Score (5d):** 1.062180153344359

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.5471691905686724
- **Z-Score (5d):** -0.6190072989078114
