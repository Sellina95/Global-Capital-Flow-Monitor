# ENGINE DIAGNOSTICS
**Date:** 2026-11-18
**Data as of:** 2026-11-17

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: 🚨 ALERT**
> **판단 요약: 데드맨 스위치 발동 / 자산 보호 모드 강제 전환**

### 🕓 Intraday Historical Trigger Log
- [2026-11-18 17:24:36 KST] ALERT | SEW=DEADMAN | EVENT=NORMAL | credit=CREDIT_WATCH(3.34%) | flow=👀 EARLY TRACE -> FLOW_FADE | flow_delta=-2 | persistence=0 | flow_alert=FLOW_FADE | PortfolioAction=NONE | Cross-Asset Shock spike=3, extreme=0 | spike=3 extreme=0 | corr_break=NO | email=YES | z={'SPY': 3.2579850215754926, 'QQQ': 3.493567620741734, 'VIX': -0.3437928937965383, 'DXY': 2.798880985722186, 'WTI': 0.11695251850019434}
👉 해석: 오늘 장중 HARD DEADMAN 이벤트가 발생했으며, 현재도 자산 보호 모드가 유지 중입니다.

### 🎯 Exposure Framework
- **Base Exposure (전략 기준): 30%**
- **Final Exposure (실행 기준): 0%**

- **Portfolio Stance:** EXIT / 0%

- **[14번 구조·수급 괴리]:** 🚨 **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
### 🟢 Current SEW Status
- **SEW:** DEADMAN | 🚨 SEW HARD DEADMAN — 장중 실시간 이상징후 감지. 평소 시장 범위를 벗어난 움직임이 관측되고 있습니다. 금일 시장 변동성과 포지션 리스크에 주의하십시오. SEW는 총노출을 직접 변경하지 않습니다.
- **Event Type:** NORMAL → 정상 상태 / 구조적 리스크 없음
- **Spike Monitor:** Spike 3 / Extreme 0
- **Current Reason:** Cross-Asset Shock spike=3, extreme=0

- **[15번 데드맨]:** 🚨 ACTIVATED
- **[14번 수급 시그널]:** 🚨 **STAY (포지션 유지)**

### 🔬 Structural Layer (12.5~12.8)
- **Structural Layer:**
  - Growth Sustainability → **FRAGILE_EXPANSION** (Expansion remains possible, but the growth structure is not yet broad or durable. Monitor demand confirmation.)
  - Flow Authenticity → **EARLY_ROTATION** (Participation is emerging, but confirmation remains limited.)
  - Leadership Breadth → **SELECTIVE_EXPANSION** (Leadership is improving selectively, but broad market confirmation remains incomplete.)
  - Positioning Stress → **SQUEEZE_RISK** (Positioning is stretched and vulnerable to squeeze-driven reversals.)

## 🎯 Final Decision (War Room Override)
- **Final Action:** **EXIT**
- **Final Exposure:** **0%**
- **Base Context:** phase=TRANSITION / MIXED / narrative=HOLD / base_exposure=30%
- **SEW:** DEADMAN / NORMAL
- **Divergence:** ALIGNED / **STAY (포지션 유지)**
- **Drift:** 👀 EARLY DRIFT / NEUTRAL / NONE / score=3
- **Flow:** 👀 EARLY TRACE / score=3
- **Gamma:** 🔴 NEGATIVE GAMMA
- **Tactical Action:** HOLD / NONE / LOW
- **Positioning:** pos_z=0.30
- **Warning Score:** 4 (6.5 상관관계 붕괴, 6.6 섹터 상관관계 붕괴)
- **Tactical Why:** No actionable alignment
- **Why:** SEW DEADMAN 발동 → 즉시 EXIT / 익스포저 0% → 상위 레이어(SEW/Divergence)가 Narrative보다 우선 → Warning Score 3+ → 공격적 확장 금지 / 총노출 추가 감산 없이 방어적 배분 → Tactical=HOLD / Flow=👀 EARLY TRACE(3) / Drift=👀 EARLY DRIFT(3) / Gamma=🔴 NEGATIVE GAMMA → Tactical HOLD/MONITOR → 최종판단 변경 없음

### 🚩 Market Regime Status
- **국면 전환 감지:** 🚨 **RISK-OFF (부분 정렬)** → **TRANSITION / MIXED**
- **Structural Regime:** **UNKNOWN_TRANSITION**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 5.103  (-0.35% vs 5.121)
- **달러 인덱스**: 103.490  (-0.06% vs 103.550)
- **WTI 유가**: 86.010  (+0.34% vs 85.720)
- **변동성 지수 (VIX)**: 25.460 (+11.13% vs 22.910)
- **원/달러 환율**: 1335.670  (+0.18% vs 1333.250)

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 25.46 → **High (Risk-off bias)**
- **핵심 조합(전일 대비 방향):** US10Y(↓) / DXY(↓) / VIX(↑)
- **판정:** **TRANSITION / MIXED | Flow:  (Flow Weak)**
- **근거:** Macro Narrative=UNKNOWN_TRANSITION / Policy=MIXED / Credit=WATCH

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↓) / DXY(↓) / VIX(↑)
- **현실(FCI):** value=-0.462 / level=EASY (완화) / update=low-frequency | as of: 2026-11-18 (latest available)
- **유인(Real Rates):** value=2.920 / level=RESTRICTIVE (유인↓) / dir(→) | as of: 2026-11-18 (latest available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI는 저빈도 금융환경 프록시로 level 중심 해석, Real Rates는 영업일 기준 변화 방향을 함께 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↓) / DXY(↓) / VIX(↑)
- **Policy Bias: EASING (완화) (MODERATE, score=-1.5) | REAL_RATEΔ +0.000 / FCI value=-0.462 (low-frequency) / DXYΔ -0.060 / US10YΔ -0.018**
- **Expectations: dict received.**

- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리/달러/변동성 신호가 완전히 정렬되지 않음
- **한줄요약 ~~** 구조=EASING (완화)(MODERATE)는 참고, 가격=POLICY MIXED (정책 신호 혼조) 중심 → 최종 POLICY MIXED (정책 신호 혼조)

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
- **Spread as of:** 2026-11-16 (FRED latest)
- **HY_OAS level:** 3.34% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↑) / +3.41%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(↓)
- **HYG:** today 76.630 / prev 76.730 / pct -0.13%
- **LQD:** today 102.740 / prev 102.800 / pct -0.06%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, -0.35%)** → 완화 기대 강화
- DXY **(Mild, -0.06%)** → 달러 약세/리스크 선호
- WTI **(Mild, +0.34%)** → 인플레 재자극 가능성
- VIX **(Strong, +11.13%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Mild, +0.18%)** → 원화 약세/수급 부담
- HYG (High Yield ETF) **(Mild, -0.13%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Noise, -0.06%)** → 우량채 약세(리스크온 성향)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 하락(US10Y↓)** → 할인율 압박 완화 → 달러 약세(DXY↓) 유도: **위험자산(Growth/EM) 선호 심리 강화 및 유동성 환경 개선**
- **변동성 상승(VIX↑)** → 위험회피(Risk-Off) 강화: **안전 자산(Cash/USD) 선호도 급증 및 하이일드 스프레드 확대 압력**
- **유가 상승(WTI↑)** → 기대 인플레이션 자극: **제조/운송업 비용 부담 가중 및 중앙은행의 긴축 유지 명분 강화**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### 🌊 Drift Monitor (v4)
- **정의:** 누적 흐름 + ATR 기반 강도 감지

- **SPY:** 🔴 DOWN | Short-term: SHORT UP | 1D=-1.02% / 5D=-2.34% | Strength: LOW
- **WTI:** 🔴 DOWN | Short-term: MIXED | 1D=-2.03% / 5D=-2.62% | Strength: MEDIUM
- **DXY:** 🟢 UP | Short-term: SHORT UP | 1D=+0.27% / 5D=+0.83% | Strength: LOW
- **GOLD:** 🔴 DOWN | Short-term: SHORT DOWN | 1D=-2.57% / 5D=-5.89% | Strength: MEDIUM

- **Drift Score:** 3
- **State:** **👀 EARLY DRIFT**
- **Label:** NEUTRAL
- **SEW Combo Signal:** NONE

- **Market Drift Summary:**
  - Equity (SPY): 🔴 DOWN / SHORT UP
  - Oil (WTI): 🔴 DOWN / MIXED
  - Dollar (DXY): 🟢 UP / SHORT UP
  - Gold (GOLD): 🔴 DOWN / SHORT DOWN

- **Drivers:**
  - Defensives lagging
  - Dollar not restrictive
  - Gold event move

### ⚠ 6.5) Correlation Break Monitor
Correlation Break Detected:
- US10Y ↓ but Technology ↓
- US10Y ↓ but SPY ↓

So What?
- 결론: **공식이 깨진 구간** → 총노출 추가 감산보다 **추격 자제 + 퀄리티/리더 중심 배분**

### ⚠ 6.6) Sector Correlation Break Monitor
Correlation Break Detected:
- US10Y ↓ but XLK ↓
- US10Y ↓ but XLF ↓

So What?
- 결론: **섹터 ‘공식’이 깨진 구간** → 총노출 추가 감산보다 **섹터 배분 보수화 + 리더 중심**

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 상승(VIX↑)** → 변동성 확대: 포지션 축소/헤지 수요 증가 가능
- **금리 하락(US10Y↓)** → 완화 기대/할인율 부담 완화 가능
- **달러 약세(DXY↓)** → 위험자산 선호/신흥국 부담 완화 가능
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **+0.00**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** -0.12
- **Geo Momentum:** +0.12 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Ukraine_2022
- **Cosine Similarity Score:** 0.444
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Ukraine_2022: 0.444
  - China_Trade_2018: 0.441
  - Taiwan_Tension: 0.392
- **Top Drivers:**
  - VIX: z_used=+1.24 (z1d=+0.81, z5d=+1.88, raw_w=0.18, norm_w=0.14) → contrib=+0.17
  - USDCNH: z_used=-0.75 (z1d=-1.04, z5d=-0.32, raw_w=0.18, norm_w=0.14) → contrib=-0.10
  - EEM: z_used=+0.78 (z1d=-0.54, z5d=-1.14, raw_w=0.10, norm_w=0.08) → contrib=+0.06
  - KR10Y_SPREAD: z_used=-0.85 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.05
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Ukraine_2022** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (EEM, EIS, FXI, SPY, VXX)
- **Extreme Country Risk:** EEM, EIS, FXI, SPY, VXX

### ⚡ 7.3) Pseudo Gamma Filter
- **정의:** 옵션 데이터 없이 시장의 감마 환경을 추론
- **주의:** Dealer Gamma Bias 숫자와 Pseudo Gamma State는 서로 다른 레이어

- **Pseudo Gamma State:** 🔴 NEGATIVE GAMMA
- **Dealer Gamma Bias:** 0.96 (NEUTRAL / transition zone)
- **Bias:** Trend acceleration / 변동성 확대
- **Strategy:** 추세 추종 / 빠른 대응

- **Drift Score:** 3 (👀 EARLY DRIFT)
- **VIX:** 25.459999084472656
- **SEW:** DEADMAN / NORMAL

- **🚀 Combo Signal:** 🚨 SHOCK + NEGATIVE GAMMA → 폭발 구간

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
- **Gamma:** 🔴 NEGATIVE GAMMA / 🚨 SHOCK + NEGATIVE GAMMA → 폭발 구간
- **SEW:** DEADMAN / NORMAL
- **Positioning (POS_Z):** 0.3
- **Validation Score:** 0 (boost applied: +0)

- **Drivers:**
  - Drift building
  - Gamma acceleration regime

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(30.00bp) | 실질금리(2.92%) | DXY(103.49)
*(as of: RealRate: 2026-11-18 / FRED last available)*

❌ **자본이 탈출하는 곳 (Short Incentive):**
고금리(실질금리 2% 상회) 부담으로 인한 리스크 오프 신호

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** 금리↓ + 달러↓ + 유가↑ + VIX↑
- **최종 판정:** **복합적 요인에 의한 지표 혼조 및 방향성 탐색**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Mild) / WTI(Mild) / VIX(Strong)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(5.103), DXY(103.490), VIX(25.46)

### 🏗️ 12) Structural Filter (v3)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↓) / DXY(↓) / GOLD(↑) / VIX(↑) / WTI(↑)
- **Meaningful Move Check:** DXY=-0.05794803111525609 / GOLD=0.2906813177232027 / US10Y=-0.351487008491538 / VIX=11.130507437993685 / WTI=0.33831184250765345
- **판정:** **NEUTRAL**
- **근거:** 글로벌 매크로 구조의 특이 신호가 감지되지 않음



### 12.5) Growth Sustainability Filter [SHADOW]
- **Score:** 2
- **Label:** FRAGILE_EXPANSION
- **Demand Proxy:** 0
- **Financing:** 0
- **Energy Burden:** -1
- **Policy Capacity:** 3
- **Strategic Interpretation:** Expansion remains possible, but the growth structure is not yet broad or durable. Monitor demand confirmation.
- **Input Check:** US10Y=5.103000164031982, RealYield=2.92, T10Y2Y=0.3, WTI=86.01000213623047, DXY=103.48999786376953, LiquidityDir=UP, CreditCalm=True, HY_OAS=3.34, DriftLabel=NEUTRAL, FredAsof=2026-11-17

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.




### 12.8) Positioning Stress Filter [SHADOW]

- **Score:** -2
- **Label:** SQUEEZE_RISK
- **Strategic Interpretation:** Positioning is stretched and vulnerable to squeeze-driven reversals.

**Positioning Notes**
- Term Structure: VIX3M-VIX=-0.48 → flattening / caution
- Short-Term Hedge: VIX9D/VIX=1.05 → neutral short-term hedge
- Gamma Structure: Positive gamma mild
- Positioning: Neutral positioning

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.



### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** 1
- **Label:** EARLY_ROTATION
- **Strategic Interpretation:** Participation is emerging, but confirmation remains limited.
- **Breadth / Participation:** -3
- **Breadth Note:** RSP-SPY return spread=-0.43%p → narrow cap-weight leadership
- **Nasdaq Breadth Note:** QQQE-QQQ return spread=-0.54%p → mega-cap concentrated Nasdaq rally
- **Positioning / Gamma:** 0
- **Credit Confirmation:** 2
- **Macro Participation:** 2

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.



### 12.7) Leadership Breadth Filter [SHADOW]
- **Score:** 1
- **Label:** SELECTIVE_EXPANSION
- **Strategic Interpretation:** Leadership is improving selectively, but broad market confirmation remains incomplete.

**Leadership Notes**
- QQQ-SPY spread=0.29%p → neutral growth leadership
- SMH-QQQ spread=0.34%p → semiconductor participation strong
- SOXX-QQQ spread=0.90%p → SOX proxy confirms chip breadth
- IWM-SPY spread=-0.41%p → small-cap lag, narrow leadership risk
- XLF-SPY spread=-0.89%p → sector diffusion weak
- XLI-SPY spread=0.47%p → sector diffusion positive
- XLY-SPY spread=0.13%p → sector diffusion neutral

📌 Shadow Note: This filter checks whether leadership is broadening beyond mega-cap tech/AI. No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.


### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: EASING (완화) (MODERATE, score=-1.5) | REAL_RATEΔ +0.000 / FCI value=-0.462 (low-frequency) / DXYΔ -0.060 / US10YΔ -0.018 (정상)
- **Sentiment (Fear&Greed):** 14.076589349687673 (FEAR)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** UP (MID)
- **Structural Regime:** UNKNOWN_TRANSITION
- **Operational Phase:** TRANSITION / MIXED (Cap: 65)
- **Macro Tilt:** +0
- **Drift:** 👀 EARLY DRIFT / NEUTRAL / NONE
- **Drift Score:** 3
- **Flow Score:** 3
- **Flow Continuity:** FLOW_FADE → 👀 EARLY TRACE (N/A, tilt=+0)
- **Flow Regime Tilt:** +2 / Flow-Gamma Tilt: +0

- **🎯 Final Risk Action:** **HOLD**
- **Risk Budget (0~100):** **58**
- **Narrative:** 구조=EASING / 심리=FEAR / 유동성=증가/중간 / 크레딧=안정 / 드리프트=👀 EARLY DRIFT (NEUTRAL) / 수급=0.30 → Phase=TRANSITION / MIXED

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `EASING` | **Price(Regime):** `TRANSITION / MIXED` | **Bucket:** `MIXED` | **VIX:** `25.46`
- **Positioning Data:** Z-Score: `0.30` (>1.8 시 Run) | Gamma: `0.96` (<0.5 시 Run) | CTA: `0.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v3.2)
- **정의:** 13번 Risk Budget 실행 브레이크 레이어
- **추가 이유:** 전략 판단(13) 이후 실제 진입 강도를 조절하기 위함

- **Base Risk Budget (13):** 58
- **VIX Level:** 25.46 (STRESS) | **Change:** +11.13%
- **Positioning Layer:** ⚠️ Bearish CTA(0.0)
- **Brake Drivers:** ⚠️ High VIX, VIX Spike, VIX Convexity Shock, Bearish CTA

- **📊 Recommended Exposure:** **30%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **GROWTH TILT**
- **Duration Tilt:** **LONG DURATION FAVORED**
- **Cyclical vs Defensive:** **DEFENSIVE FAVORED**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** LONG DURATION FAVORED
- **Inflation Factor:** NEUTRAL
- **USD Factor:** NEUTRAL
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v3.3)

**Context:** phase=TRANSITION / MIXED / T10Y2Y=0.30 (MODERATE STEEP) / VIX=25.46 (VOLATILITY ELEVATED) / liquidity=UP-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM

**Macro Profile:** BALANCED
**Macro Inputs Debug:** phase=TRANSITION / MIXED / us10y_pct=-0.35% / dxy_pct=-0.06% / wti_pct=+0.34% / vix=25.46 / liq_easy=True / liq_tight=False / credit_calm=True / flow_score=3

**Flow Overlay:** flow_score=3 / flow_state=👀 EARLY TRACE / drift_label=NEUTRAL / gamma=🔴 NEGATIVE GAMMA

**Overweight:** Consumer Staples, Financials, Utilities, Industrials, Health Care, Consumer Discretionary, Materials, Real Estate

**Underweight:** Technology, Communication Services

**Scoreboard:**
- Consumer Staples: +2.5  (+2 VOL, +0.5 PHASE, +2 MOM, = +2.5)
- Financials: +2.5  (+1 LIQ, +2 CURVE, +2 MOM, = +2.5)
- Utilities: +2.2  (+3 VOL, -1 LIQ, +2 MOM, = +2.2)
- Industrials: +1.4  (+1.5 LIQ, +1 CURVE, = +1.4)
- Health Care: +1.1  (+0.5 PHASE, +2 MOM, = +1.1)
- Consumer Discretionary: +1.1  (+1.5 LIQ, +1 MOM, = +1.1)
- Materials: +0.3  (+1 MOM, = +0.3)
- Real Estate: +0.3  (+1 MOM, = +0.3)
- Communication Services: -0.3  (= -0.3)
- Technology: -1.9  (-3 VOL, +2 LIQ, -2 MOM, = -1.9)

**Rationale (Why the score exists: 섹터 점수의 핵심 드라이버)**
- OW Consumer Staples: +2: VOLATILITY ELEVATED → 필수소비 선호 (absolute mode: VIX 25.5)
- OW Consumer Staples: +0.5: Balanced Macro Profile → 방어 보완
- OW Financials: +1: 유동성 완화 → 위험선호 회복
- OW Financials: +2: 완만한 스티프닝(0.30) → 예대마진 개선
- OW Utilities: +3: VOLATILITY ELEVATED → 방어주 우위 (absolute mode: VIX 25.5)
- OW Utilities: +2: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- OW Industrials: FLOW_WEAK → 이론상 우호하나 실제 자금 유입 확인 부족
- OW Industrials: +1.5: 유동성 완화 → 경기민감 회복
- OW Industrials: +1: 완만한 스티프닝(0.30) → 성장 기대 반영
- UW Technology: +2: 유동성 완화 → 성장주/베타 우호
- UW Technology: -3: VOLATILITY ELEVATED → 위험자산 회피 (absolute mode: VIX 25.5)

**Regime Controller:**
- BALANCED (avg_divergence=-0.43, dispersion=1.00)
- Correlation Break: True / Type=GROWTH_FAILED_ON_RATE_RELIEF
- Break Reasons: US10Y ↓ but Technology ↓ | US10Y ↓ but SPY ↓ | US10Y ↓ but XLK ↓ | US10Y ↓ but XLF ↓
- Interpretation: 균형 장세 / 강한 방향성보다 선별적 배분 필요

**Divergence / Classification Monitor (Theory vs Flow alignment: 이론과 실제 자금흐름 정렬 여부)**
- Consumer Staples: HIGH_CONVICTION_ALIGNED (theory=+2.5, flow=+1.4, final=+2.5)
- Financials: HIGH_CONVICTION_ALIGNED (theory=+3.0, flow=+1.4, final=+2.5)
- Utilities: HIGH_CONVICTION_ALIGNED (theory=+2.0, flow=+1.4, final=+2.2)
- Industrials: FLOW_WEAK (theory=+2.5, flow=+0.0, final=+1.4)
- Health Care: TACTICAL_MOMENTUM_ONLY (theory=+0.5, flow=+1.4, final=+1.1)
- Materials: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+0.7, final=+0.3)
- Real Estate: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+0.7, final=+0.3)
- Energy: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Communication Services: NEUTRAL (theory=+0.0, flow=+0.0, final=-0.3)
- Technology: AVOID (theory=-1.0, flow=-1.4, final=-1.9)

### 💰 18.5) Tactical Asset Allocation (Execution Weight)
- **Strategic Exposure (15):** **30.0%** → **Regime Adjusted:** **30.0%**
- **Exposure Override:** BALANCED → Sector Weight Only (No Exposure Change)

| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |
| :--- | :---: | :---: | :---: | :--- |
| Consumer Staples | +2.5 | ALIGNED | **4.3%** | HOLD |
| Financials | +2.5 | ALIGNED | **5.8%** | HOLD |
| Utilities | +2.2 | ALIGNED | **1.1%** | HOLD |
| Health Care | +1.1 | POSITIVE_DIVERGENCE | **1.7%** | HOLD |
| Consumer Discretionary | +1.1 | ALIGNED | **1.4%** | HOLD |
| Materials | +0.3 | POSITIVE_DIVERGENCE | **1.5%** | HOLD |
| **Cash & Hedge** | - | - | **81.9%** | DEFENSIVE |

- **Allocation Check:** Sector Weights + Cash = **100.0%**
- **Regime Cap Profile:** BALANCED
- **Regime Cap Applied:** None
- **Strategic Cash (15):** 70.0%
- **Tactical Reserve (Cap / Unallocated):** 11.9%


**Deleveraging Priority Preview:**
- 기준: Divergence → Momentum → Score → Current Weight
1. Communication Services (priority_score=0.45, score=-0.3, weight=0.8%, div=ALIGNED, mom=0)
2. Energy (priority_score=0.0, score=0.0, weight=1.5%, div=ALIGNED, mom=0)
3. Consumer Discretionary (priority_score=-1.55, score=1.1, weight=1.4%, div=ALIGNED, mom=1)
4. Materials (priority_score=-3.14, score=0.28, weight=1.5%, div=POSITIVE_DIVERGENCE, mom=1)
5. Health Care (priority_score=-4.55, score=1.11, weight=1.7%, div=POSITIVE_DIVERGENCE, mom=2)

**Leveraging Priority Preview:**
- 기준: Score → Momentum → Positive Divergence
1. Consumer Staples (priority_score=7.47, score=2.47, weight=4.3%, div=ALIGNED, mom=2)
2. Financials (priority_score=7.47, score=2.47, weight=5.8%, div=ALIGNED, mom=2)
3. Utilities (priority_score=7.18, score=2.18, weight=1.1%, div=ALIGNED, mom=2)
4. Health Care (priority_score=5.11, score=1.11, weight=1.7%, div=POSITIVE_DIVERGENCE, mom=2)
5. Materials (priority_score=2.78, score=0.28, weight=1.5%, div=POSITIVE_DIVERGENCE, mom=1)
- **Divergence Adjustment:** Industrials penalized in weight sizing

### 🧬 19) Execution Layer (ETF Mapping)

| Sector | ETF | Weight | Action | Divergence | Classification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| Communication Services | XLC | 0.8% | NO_ACTION | ALIGNED | NEUTRAL |
| Consumer Discretionary | XLY | 1.4% | MICRO | ALIGNED | ALIGNED |
| Consumer Staples | XLP | 4.3% | ACCUMULATE | ALIGNED | HIGH_CONVICTION_ALIGNED |
| Energy | XLE | 1.5% | NO_ACTION | ALIGNED | NEUTRAL |
| Financials | XLF | 5.8% | ACCUMULATE | ALIGNED | HIGH_CONVICTION_ALIGNED |
| Health Care | XLV | 1.7% | TACTICAL_ONLY | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Materials | XLB | 1.5% | TACTICAL_ONLY | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Utilities | XLU | 1.1% | MICRO | ALIGNED | HIGH_CONVICTION_ALIGNED |


### 🧬 19.5) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Execution Notes:**
- Early flow trace → maintain leaders, wait for confirmation before broadening.
- Exposure below 45% → defensive execution; cash remains strategic asset.

**Preferred Company Traits:**
- Leaders with improving breadth confirmation
- Smaller position sizes with strict risk budget discipline

**Risk Control / Avoid:**
- Broad beta expansion before confirmation

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.48654392257734563
- **Z-Score (5d):** -0.6926941467037918

### EEM
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.543343385384211
- **Z-Score (5d):** -1.137121583081548

### EIS
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 0.13559601783493078
- **Z-Score (5d):** -1.2421660216855794

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.12405922016029289
- **Z-Score (5d):** -1.2571294251286675

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.8905391828085127
- **Z-Score (5d):** -0.7728299225769135

### FXI
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -1.04188126650796
- **Z-Score (5d):** -1.5109041355296775

### GLD
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.12088040370374319
- **Z-Score (5d):** -1.2018947755876557

### SPY
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.9916143732209239
- **Z-Score (5d):** -1.581268227535752

### VXX
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 1.348143761605328
- **Z-Score (5d):** 2.5557624101144687
