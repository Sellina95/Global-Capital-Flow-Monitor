# ENGINE DIAGNOSTICS
**Date:** 2026-11-11
**Data as of:** 2026-11-10

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: ✅ STABLE**
> **판단 요약: 구조-가격-수급 정렬 / 실시간 이상징후 없음 / 데드맨 정상**
### 🎯 Exposure Framework
- **Base Exposure (전략 기준): 45%**
- **Final Exposure (실행 기준): 45%**

- **Portfolio Stance:** REDUCE / 45%

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
  - Flow Authenticity → **REAL_ACCUMULATION** (Institutional participation appears broad and persistent.)
  - Leadership Breadth → **CONCENTRATED_LEADERSHIP** (Leadership remains concentrated, with limited confirmation beyond key growth or mega-cap areas.)
  - Positioning Stress → **SQUEEZE_RISK** (Positioning is stretched and vulnerable to squeeze-driven reversals.)

## 🎯 Final Decision (War Room Override)
- **Final Action:** **REDUCE**
- **Final Exposure:** **45%**
- **Base Context:** phase=SOFT RISK-OFF / narrative=REDUCE / base_exposure=45%
- **SEW:** STABLE / NORMAL
- **Divergence:** ALIGNED / **STAY (포지션 유지)**
- **Drift:** 👀 EARLY DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK / score=3
- **Flow:** ⚡ BUILDING / score=6
- **Gamma:** 🟡 TRANSITION
- **Tactical Action:** REDUCE / DEFENSIVE / MEDIUM
- **Positioning:** pos_z=0.82
- **Warning Score:** 0 (No warning)
- **Tactical Why:** Risk-off environment
- **Why:** SEW STABLE → 실시간 이상징후 없음 → Divergence ALIGNED → 구조·가격·수급 정렬 → Narrative Action=REDUCE 반영 → Tactical=REDUCE / Flow=⚡ BUILDING(6) / Drift=👀 EARLY DRIFT(3) / Gamma=🟡 TRANSITION → Tactical REDUCE → 방어 기조 유지 / 총노출 추가 감산 없이 배분 보수화

### 🚩 Market Regime Status
- **국면 전환 감지:** 🚨 **RISK-ON (부분 정렬)** → **SOFT RISK-OFF**
- **Structural Regime:** **TIGHTENING_GROWTH_SCARE**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.983  (+2.45% vs 4.864)
- **달러 인덱스**: 102.230  (+0.57% vs 101.650)
- **WTI 유가**: 86.040  (-0.93% vs 86.850)
- **변동성 지수 (VIX)**: 19.460 (-2.31% vs 19.920)
- **원/달러 환율**: 1343.840  (-1.38% vs 1362.700)

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 19.46 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(↑) / DXY(↑) / VIX(↓)
- **판정:** **SOFT RISK-OFF | Flow:  (Flow Weak)**
- **근거:** Macro Narrative=TIGHTENING_GROWTH_SCARE / Policy=MIXED / Credit=WATCH

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↑) / DXY(↑) / VIX(↓)
- **현실(FCI):** value=-0.459 / level=EASY (완화) / update=low-frequency | as of: 2026-11-11 (latest available)
- **유인(Real Rates):** value=2.660 / level=RESTRICTIVE (유인↓) / dir(→) | as of: 2026-11-11 (latest available)
- **판정:** **LIQUIDITY TIGHTENING (유동성 축소)**
- **근거:** 금리↑+달러↑ + (FCI 압박 또는 실질금리 유인↓) → 리스크자산에 불리
- **Note:** FCI는 저빈도 금융환경 프록시로 level 중심 해석, Real Rates는 영업일 기준 변화 방향을 함께 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↑) / DXY(↑) / VIX(↓)
- **Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCI value=-0.459 (low-frequency) / DXYΔ +0.580 / US10YΔ +0.119**
- **Expectations: dict received.**

- **판정:** **POLICY TIGHTENING (긴축)**
- **근거:** 금리↑ + 달러↑ → 긴축 압력
- **한줄요약 ~~** 구조=TIGHTENING (긴축)(MODERATE)는 참고, 가격=POLICY TIGHTENING (긴축) 중심 → 최종 POLICY TIGHTENING (긴축)

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
- **Spread as of:** 2026-11-09 (FRED latest)
- **HY_OAS level:** 3.34% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↓) / -2.34%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 좁혀지는 중 → 공포 온도 완화
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(↓)
- **HYG:** today 77.180 / prev 77.510 / pct -0.43%
- **LQD:** today 103.880 / prev 104.670 / pct -0.75%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, +2.45%)** → 완화 기대 약화/금리 부담
- DXY **(Strong, +0.57%)** → 달러 강세/신흥국 부담
- WTI **(Clear, -0.93%)** → 물가 부담 완화
- VIX **(Clear, -2.31%)** → 심리 개선/리스크온
- 원/달러(USDKRW) **(Strong, -1.38%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Clear, -0.43%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Clear, -0.75%)** → 우량채 약세(리스크온 성향)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 상승(US10Y↑)** → 실질 금리 압박 → 달러 강세(DXY↑) 유도: **신흥국 자본 유출 및 고밸류 성장주 할인율 부담 증가**
- **변동성 하락(VIX↓)** → 심리 개선(Risk-On): **자산군 전반의 위험 수용 여력(Risk Appetite) 회복 및 랠리 지속 가능성**
- **유가 하락(WTI↓)** → 물가 부담 완화: **실질 구매력 회복 및 긴축 압력 완화(Dovish Tilt) 가능성 시사**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### 🌊 Drift Monitor (v4)
- **정의:** 누적 흐름 + ATR 기반 강도 감지

- **SPY:** 🔴 DOWN | Short-term: SHORT UP | 1D=-0.37% / 5D=-0.58% | Strength: LOW
- **WTI:** 🟡 REBOUND | Short-term: SHORT DOWN | 1D=+0.19% / 5D=-2.18% | Strength: LOW
- **DXY:** 🟢 UP | Short-term: SHORT UP | 1D=+0.12% / 5D=+0.83% | Strength: LOW
- **GOLD:** 🟡 REBOUND | Short-term: SHORT UP | 1D=+1.00% / 5D=-0.06% | Strength: LOW

- **Drift Score:** 3
- **State:** **👀 EARLY DRIFT**
- **Label:** NEUTRAL
- **SEW Combo Signal:** 🟢 EARLY FLOW WITHOUT SHOCK

- **Market Drift Summary:**
  - Equity (SPY): 🔴 DOWN / SHORT UP
  - Oil (WTI): 🟡 REBOUND / SHORT DOWN
  - Dollar (DXY): 🟢 UP / SHORT UP
  - Gold (GOLD): 🟡 REBOUND / SHORT UP

- **Drivers:**
  - Credit supports risk
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
- **Geo Stress Score (z-composite):** **+0.22**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** +0.19
- **Geo Momentum:** +0.03 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** China_Trade_2018
- **Cosine Similarity Score:** 0.541
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - China_Trade_2018: 0.541
  - Taiwan_Tension: 0.400
  - Red_Sea: 0.203
- **Top Drivers:**
  - USDCNH: z_used=+0.92 (z1d=-0.36, z5d=+2.84, raw_w=0.18, norm_w=0.14) → contrib=+0.13
  - VIX: z_used=-0.50 (z1d=-0.28, z5d=-0.82, raw_w=0.18, norm_w=0.14) → contrib=-0.07
  - WTI: z_used=-0.86 (z1d=-0.35, z5d=-1.61, raw_w=0.10, norm_w=0.08) → contrib=-0.07
  - SEA: z_used=+1.31 (z1d=-0.92, z5d=-1.90, raw_w=0.05, norm_w=0.04) → contrib=+0.05
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **China_Trade_2018** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (EWJ, GLD)
- **Extreme Country Risk:** EWJ, GLD

### ⚡ 7.3) Pseudo Gamma Filter
- **정의:** 옵션 데이터 없이 시장의 감마 환경을 추론
- **주의:** Dealer Gamma Bias 숫자와 Pseudo Gamma State는 서로 다른 레이어

- **Pseudo Gamma State:** 🟡 TRANSITION
- **Dealer Gamma Bias:** 0.61 (NEUTRAL / transition zone)
- **Bias:** 초기 방향성 형성 / 감마 전환 구간
- **Strategy:** 포지션 확대 신중 / 초기 진입 구간

- **Drift Score:** 3 (👀 EARLY DRIFT)
- **VIX:** 19.459999084472656
- **SEW:** STABLE / NORMAL

- **🚀 Combo Signal:** 🟢 EARLY FLOW WITHOUT SHOCK

### 🏦 Institutional Flow Engine (v2-minimal)
- **정의:** 기관성 자금이 뉴스 전에 남기는 흔적을 구조적으로 탐지

- **Raw Flow State:** **⚡ BUILDING**
- **Transition State:** **FLOW_FADE**
- **Flow Delta:** -1 (prev=7 → current=6)
- **Persistence Days:** 5
- **Transition Note:** 기관성 흐름은 남아 있으나 강도 약화
- **Confidence:** **MEDIUM-HIGH**
- **Action Bias:** **WATCHLIST**

- **Drift:** 👀 EARLY DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK
- **Gamma:** 🟡 TRANSITION / 🟢 EARLY FLOW WITHOUT SHOCK
- **SEW:** STABLE / NORMAL
- **Positioning (POS_Z):** 0.82
- **Validation Score:** 2 (boost applied: +2)

- **Drivers:**
  - Drift building
  - Gamma transition
  - No shock yet
  - Credit confirms risk appetite
  - Leadership breadth expanding

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(25.00bp) | 실질금리(2.66%) | DXY(102.23)
*(as of: RealRate: 2026-11-11 / FRED last available)*

❌ **자본이 탈출하는 곳 (Short Incentive):**
고금리(실질금리 2% 상회) 부담으로 인한 리스크 오프 신호

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** 금리↑ + 달러↑ + 유가↓ + VIX↓
- **최종 판정:** **매크로 지표 혼조 속 시장 심리 개선 주도**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Strong) / WTI(Clear) / VIX(Clear)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.983), DXY(102.230), VIX(19.46)

### 🏗️ 12) Structural Filter (v3)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↑) / GOLD(↓) / VIX(↓) / WTI(↓)
- **Meaningful Move Check:** DXY=0.5705871346268754 / GOLD=-2.0488528090442335 / US10Y=2.446545268601772 / VIX=-2.3092419179692634 / WTI=-0.9326396923715629
- **판정:** **GLOBAL FINANCIAL TIGHTENING (글로벌 긴축 구조)**
- **근거:** 금리↑ + 달러↑가 모두 의미 있는 수준으로 나타나 글로벌 자본 조달 비용 압박



### 12.5) Growth Sustainability Filter [SHADOW]
- **Score:** 3
- **Label:** FRAGILE_EXPANSION
- **Demand Proxy:** 1
- **Financing:** 0
- **Energy Burden:** -1
- **Policy Capacity:** 3
- **Strategic Interpretation:** Expansion remains possible, but the growth structure is not yet broad or durable. Monitor demand confirmation.
- **Input Check:** US10Y=4.982999801635742, RealYield=2.66, T10Y2Y=0.25, WTI=86.04000091552734, DXY=102.2300033569336, LiquidityDir=UP, CreditCalm=True, HY_OAS=3.34, DriftLabel=NEUTRAL, FredAsof=2026-11-10

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.




### 12.8) Positioning Stress Filter [SHADOW]

- **Score:** 0
- **Label:** SQUEEZE_RISK
- **Strategic Interpretation:** Positioning is stretched and vulnerable to squeeze-driven reversals.

**Positioning Notes**
- Term Structure: VIX3M-VIX=1.18 → mild contango
- Short-Term Hedge: VIX9D/VIX=0.95 → neutral short-term hedge
- Gamma Structure: Positive gamma mild
- Positioning: Neutral positioning

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.



### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** 7
- **Label:** REAL_ACCUMULATION
- **Strategic Interpretation:** Institutional participation appears broad and persistent.
- **Breadth / Participation:** 3
- **Breadth Note:** RSP-SPY return spread=0.34%p → broad participation
- **Nasdaq Breadth Note:** QQQE-QQQ return spread=0.31%p → broad Nasdaq participation
- **Positioning / Gamma:** 0
- **Credit Confirmation:** 2
- **Macro Participation:** 2

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.



### 12.7) Leadership Breadth Filter [SHADOW]
- **Score:** 0
- **Label:** CONCENTRATED_LEADERSHIP
- **Strategic Interpretation:** Leadership remains concentrated, with limited confirmation beyond key growth or mega-cap areas.

**Leadership Notes**
- QQQ-SPY spread=-0.31%p → growth leadership weak
- SMH-QQQ spread=-0.10%p → semiconductor participation neutral
- SOXX-QQQ spread=0.56%p → SOX proxy confirms chip breadth
- IWM-SPY spread=-0.32%p → small-cap lag, narrow leadership risk
- XLF-SPY spread=0.89%p → sector diffusion positive
- XLI-SPY spread=0.27%p → sector diffusion neutral
- XLY-SPY spread=0.40%p → sector diffusion positive

📌 Shadow Note: This filter checks whether leadership is broadening beyond mega-cap tech/AI. No impact on Final Exposure or Phase, but used as context for Sector Allocation risk controls.


### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCI value=-0.459 (low-frequency) / DXYΔ +0.580 / US10YΔ +0.119 (정상)
- **Sentiment (Fear&Greed):** 36.8975848680945 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** UP (MID)
- **Structural Regime:** TIGHTENING_GROWTH_SCARE
- **Operational Phase:** SOFT RISK-OFF (Cap: 50)
- **Macro Tilt:** -8
- **Drift:** 👀 EARLY DRIFT / NEUTRAL / 🟢 EARLY FLOW WITHOUT SHOCK
- **Drift Score:** 3
- **Flow Score:** 6
- **Flow Continuity:** CONFIRMED_FLOW → ⚡ BUILDING (FLOW_PERSISTENCE, tilt=+1)
- **Flow Regime Tilt:** +4 / Flow-Gamma Tilt: +2

- **🎯 Final Risk Action:** **REDUCE**
- **Risk Budget (0~100):** **50**
- **Narrative:** 구조=TIGHTENING / 심리=NEUTRAL / 유동성=증가/중간 / 크레딧=안정 / 드리프트=👀 EARLY DRIFT (NEUTRAL) / 수급=0.82 → Phase=SOFT RISK-OFF

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `TIGHTENING` | **Price(Regime):** `SOFT RISK-OFF` | **Bucket:** `RISK-OFF` | **VIX:** `19.46`
- **Positioning Data:** Z-Score: `0.82` (>1.8 시 Run) | Gamma: `0.61` (<0.5 시 Run) | CTA: `0.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v3.2)
- **정의:** 13번 Risk Budget 실행 브레이크 레이어
- **추가 이유:** 전략 판단(13) 이후 실제 진입 강도를 조절하기 위함

- **Base Risk Budget (13):** 50
- **VIX Level:** 19.46 (NORMAL) | **Change:** -2.31%
- **Positioning Layer:** ⚠️ Bearish CTA(0.0)
- **Brake Drivers:** ⚠️ Bearish CTA

- **📊 Recommended Exposure:** **45%**

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

**Context:** phase=SOFT RISK-OFF / T10Y2Y=0.25 (MODERATE STEEP) / VIX=19.46 (VOLATILITY NORMAL) / liquidity=UP-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM

**Macro Profile:** SOFT_RISK_OFF_DISINFLATION
**Macro Inputs Debug:** phase=SOFT RISK-OFF / us10y_pct=+2.45% / dxy_pct=+0.57% / wti_pct=-0.93% / vix=19.46 / liq_easy=True / liq_tight=False / credit_calm=True / flow_score=6

**Flow Overlay:** flow_score=6 / flow_state=⚡ BUILDING / drift_label=NEUTRAL / gamma=🟡 TRANSITION
**Flow Notes:** NEUTRAL + FLOW ACTIVE → XLK/XLI 소폭 가점 | Gamma TRANSITION → 초기 리더 소폭 가점

**Overweight:** Financials, Health Care, Consumer Discretionary, Consumer Staples, Industrials, Materials, Real Estate, Utilities

**Underweight:** Technology, Energy

**Scoreboard:**
- Financials: +2.2  (+1 LIQ, +2 CURVE, +2 MOM, = +2.2)
- Health Care: +1.2  (+1.2 PHASE, +2 MOM, = +1.2)
- Consumer Discretionary: +1.1  (+1.5 LIQ, -0.5 PHASE, +2 MOM, = +1.1)
- Consumer Staples: +1.0  (+0.8 PHASE, +2 MOM, = +1.0)
- Industrials: +0.9  (+1.5 LIQ, +1 CURVE, -0.5 PHASE, +0.5 FLOW, = +0.9)
- Materials: +0.8  (+2 MOM, = +0.8)
- Real Estate: +0.8  (+2 MOM, = +0.8)
- Utilities: +0.2  (-1 LIQ, +2 MOM, = +0.2)
- Energy: -0.3  (-1 MOM, = -0.3)
- Technology: -1.6  (+2 LIQ, +0.5 PHASE, +1 FLOW, -2 MOM, = -1.6)

**Rationale (Why the score exists: 섹터 점수의 핵심 드라이버)**
- OW Financials: +1: 유동성 완화 → 위험선호 회복
- OW Financials: +2: 완만한 스티프닝(0.25) → 예대마진 개선
- OW Health Care: +1.2: Soft Risk-Off Disinflation → 금리 안정/퀄리티 방어 우위
- OW Health Care: +2: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- OW Consumer Discretionary: +1.5: 유동성 완화 → 소비 민감주 우호
- OW Consumer Discretionary: +2: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- OW Consumer Staples: TACTICAL_MOMENTUM_ONLY → 거시 근거 약하지만 단기 리더십 존재
- OW Consumer Staples: +0.8: Soft Risk-Off Disinflation → 필수소비 방어 보완
- OW Consumer Staples: +2: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- UW Technology: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Technology: +2: 유동성 완화 → 성장주/베타 우호
- UW Technology: +0.5: Soft Risk-Off Disinflation → 금리 안정으로 리더 섹터 일부 유지

**Regime Controller:**
- DISLOCATION (avg_divergence=-0.12, dispersion=1.64)
- Correlation Break: False / Type=NONE
- Interpretation: 섹터별 괴리가 큰 불안정 장세 → 포지션 축소와 리더 섹터 검증 필요

**Divergence / Classification Monitor (Theory vs Flow alignment: 이론과 실제 자금흐름 정렬 여부)**
- Financials: HIGH_CONVICTION_ALIGNED (theory=+3.0, flow=+1.4, final=+2.2)
- Consumer Staples: TACTICAL_MOMENTUM_ONLY (theory=+0.8, flow=+1.4, final=+1.0)
- Industrials: FLOW_WEAK (theory=+2.0, flow=+0.1, final=+0.9)
- Materials: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+1.4, final=+0.8)
- Real Estate: TACTICAL_MOMENTUM_ONLY (theory=+0.0, flow=+1.4, final=+0.8)
- Communication Services: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Technology: THEORY_TRAP (theory=+2.5, flow=-1.1, final=-1.6)

### 💰 18.5) Tactical Asset Allocation (Execution Weight)
- **Strategic Exposure (15):** **45.0%** → **Regime Adjusted:** **45.0%**
- **Exposure Override:** DISLOCATION → Sector Weight Only (No Exposure Change)

| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |
| :--- | :---: | :---: | :---: | :--- |
| Financials | +2.2 | ALIGNED | **5.8%** | HOLD |
| Health Care | +1.2 | ALIGNED | **1.7%** | HOLD |
| Consumer Discretionary | +1.1 | ALIGNED | **1.4%** | HOLD |
| Consumer Staples | +1.0 | POSITIVE_DIVERGENCE | **4.3%** | HOLD |
| Materials | +0.8 | POSITIVE_DIVERGENCE | **1.5%** | HOLD |
| Utilities | +0.2 | ALIGNED | **1.1%** | HOLD |
| **Cash & Hedge** | - | - | **81.9%** | DEFENSIVE |

- **Allocation Check:** Sector Weights + Cash = **100.0%**
- **Regime Cap Profile:** SOFT_RISK_OFF_DISINFLATION
- **Participation / Quality Cap Applied:**
  - Financials: 14.1% → 5.0% (-9.1%)
  - Consumer Discretionary: 5.9% → 5.0% (-0.9%)
- **Strategic Cash (15):** 55.0%
- **Tactical Reserve (Cap / Unallocated):** 26.9%


**Deleveraging Priority Preview:**
- 기준: Divergence → Momentum → Score → Current Weight
1. Energy (priority_score=0.48, score=-0.32, weight=1.5%, div=ALIGNED, mom=0)
2. Communication Services (priority_score=0.0, score=0.0, weight=0.8%, div=ALIGNED, mom=0)
3. Utilities (priority_score=-2.09, score=0.18, weight=1.1%, div=ALIGNED, mom=2)
4. Consumer Discretionary (priority_score=-2.54, score=1.08, weight=1.4%, div=ALIGNED, mom=2)
5. Health Care (priority_score=-2.58, score=1.17, weight=1.7%, div=ALIGNED, mom=2)

**Leveraging Priority Preview:**
- 기준: Score → Momentum → Positive Divergence
1. Financials (priority_score=7.25, score=2.25, weight=5.8%, div=ALIGNED, mom=2)
2. Consumer Staples (priority_score=5.04, score=1.04, weight=4.3%, div=POSITIVE_DIVERGENCE, mom=2)
3. Materials (priority_score=4.76, score=0.76, weight=1.5%, div=POSITIVE_DIVERGENCE, mom=2)
4. Health Care (priority_score=4.17, score=1.17, weight=1.7%, div=ALIGNED, mom=2)
5. Consumer Discretionary (priority_score=4.08, score=1.08, weight=1.4%, div=ALIGNED, mom=2)
- **Divergence Adjustment:** Industrials penalized in weight sizing

### 🧬 19) Execution Layer (ETF Mapping)

| Sector | ETF | Weight | Action | Divergence | Classification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| Communication Services | XLC | 0.8% | NO_ACTION | ALIGNED | NEUTRAL |
| Consumer Discretionary | XLY | 1.4% | MICRO | ALIGNED | ALIGNED |
| Consumer Staples | XLP | 4.3% | DEFENSIVE_BUFFER | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Energy | XLE | 1.5% | MICRO | ALIGNED | ALIGNED |
| Financials | XLF | 5.8% | ACCUMULATE | ALIGNED | HIGH_CONVICTION_ALIGNED |
| Health Care | XLV | 1.7% | DEFENSIVE_QUALITY | ALIGNED | ALIGNED |
| Materials | XLB | 1.5% | TACTICAL_ONLY | POSITIVE_DIVERGENCE | TACTICAL_MOMENTUM_ONLY |
| Utilities | XLU | 1.1% | MICRO | ALIGNED | ALIGNED |


### 🧬 19.5) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Execution Notes:**
- Flow building → selective expansion allowed if risk controls remain stable.

**Preferred Company Traits:**
- Cash flow visibility and earnings stability
- High-conviction leaders with cross-asset confirmation

**Risk Control / Avoid:**
- Rate-sensitive long-duration equities

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -2.201040078450755
- **Z-Score (5d):** -0.10814447970835402

### EEM
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.3827285146724672
- **Z-Score (5d):** -0.02419030467958128

### EIS
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.3354126631466807
- **Z-Score (5d):** 0.5983177384709804

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -1.423691291019235
- **Z-Score (5d):** 0.7761130755944566

### EWJ
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.7993830922632944
- **Z-Score (5d):** -0.892538071945407

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.6071179634858216
- **Z-Score (5d):** 1.5057557128489063

### GLD
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -1.6099180390967522
- **Z-Score (5d):** 1.185639760182711

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.3559951020804091
- **Z-Score (5d):** -0.26317835982576676

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.10627286461352747
- **Z-Score (5d):** 0.014385506608069728
