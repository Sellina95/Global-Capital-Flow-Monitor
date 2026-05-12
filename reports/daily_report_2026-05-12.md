# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-05-12
**Data as of:** 2026-05-11

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: 🚨 ALERT**
> **판단 요약: 데드맨 스위치 발동 / 자산 보호 모드 강제 전환**

### 🕓 Intraday Historical Trigger Log
- [2026-05-12 13:33:46] ALERT | SEW=DEADMAN | EVENT=NORMAL | credit=UNKNOWN(N/A) | flow=NO_FLOW_BASE -> EARLY_TRACE | flow_delta=2 | persistence=1 | flow_alert=CHANGE | Exp=0% | 🚨 HARD DEADMAN: Real-time Cross-Asset Shock (spike=0, extreme=4) | spike=0 extreme=4 | corr_break=NO | email=YES | z={'SPY': -3.756308203533061, 'QQQ': -4.028312090631426, 'VIX': 0.9970386843272325, 'DXY': 4.188004497055036, 'WTI': 4.1997373223694705}
👉 해석: 오늘 장중 HARD DEADMAN 이벤트가 발생했으며, 현재도 자산 보호 모드가 유지 중입니다.

### 🎯 Exposure Framework
- **Base Exposure (전략 기준): 50%**
- **Final Exposure (실행 기준): 0%**

- **Portfolio Stance:** EXIT / 0%

- **[14번 구조·수급 괴리]:** 🚨 **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
### 🟢 Current SEW Status
- **SEW:** DEADMAN | 🚨 HARD DEADMAN 발동 (익스포저 0% / 자산 보호 모드)
- **Event Type:** NORMAL → 정상 상태 / 구조적 리스크 없음
- **Spike Monitor:** Spike 0 / Extreme 4
- **Current Reason:** 🚨 HARD DEADMAN: Real-time Cross-Asset Shock (spike=0, extreme=4)

- **[15번 데드맨]:** 🚨 ACTIVATED
- **[14번 수급 시그널]:** 🚨 **STAY (포지션 유지)**

### 📌 Interpretation
- 금일 시장은 **EVENT-WATCHING (이벤트 관망) 환경**입니다.
- 기관성 자금 흐름은 아직 뚜렷하지 않아, 공격적 확장에는 신중함이 필요합니다.
- 드리프트 강도는 아직 약해 추세 신뢰도는 제한적입니다.
- 따라서 **현 수준에서 포지션 유지 및 관망 전략이 적절**합니다.

### 🎯 Final Action Engine(Raw Signal)
- **Action:** HOLD
- **Size:** NONE
- **Confidence:** LOW
- **Reason:**
  - No actionable alignment

## 🎯 Final Decision (War Room Override)
- **Final Action:** **EXIT**
- **Final Exposure:** **0%**
- **Base Context:** phase=EVENT-WATCHING (이벤트 관망) / narrative=HOLD / base_exposure=50%
- **SEW:** DEADMAN / NORMAL
- **Divergence:** ALIGNED / **STAY (포지션 유지)**
- **Drift:** NO DRIFT / INFLATION_RISK_OFF / NONE / score=0
- **Flow:** NO CLEAR FLOW / score=1
- **Gamma:** 🟢 POSITIVE GAMMA (WEAK)
- **Tactical Action:** HOLD / NONE / LOW
- **Positioning:** pos_z=0.00
- **Warning Score:** 2 (6.6 섹터 상관관계 붕괴)
- **Tactical Why:** No actionable alignment
- **Why:** SEW DEADMAN 발동 → 즉시 EXIT / 익스포저 0% → 상위 레이어(SEW/Divergence)가 Narrative보다 우선 → Warning Score 2 → 익스포저 15% haircut → Tactical=HOLD / Flow=NO CLEAR FLOW(1) / Drift=NO DRIFT(0) / Gamma=🟢 POSITIVE GAMMA (WEAK) → Tactical HOLD/MONITOR → 최종판단 변경 없음

### 🚩 Market Regime Status
- **현재 국면 유지:** ✅ **EVENT-WATCHING (이벤트 관망)**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.410  (+1.05% vs 4.364)
- **달러 인덱스**: 97.940  (+0.10% vs 97.840)
- **WTI 유가**: 98.070  (+2.78% vs 95.420)
- **변동성 지수 (VIX)**: 18.380
- **원/달러 환율**: 1460.550  (+0.40% vs 1454.790)

---

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 18.38 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(↑) / DXY(↑) / VIX(→)
- **판정:** **EVENT-WATCHING (이벤트 관망) (Flow Weak)**
- **근거:** 변동성은 눌려있지만 금리/달러가 움직임 → 데이터/이벤트 대기

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↑) / DXY(↑) / VIX(→)
- **현실(FCI):** level=EASY (완화) / dir(→) | as of: 2026-05-12 (FRED last available)
- **유인(Real Rates):** level=NEUTRAL (중립) / dir(→) | as of: 2026-05-12 (FRED last available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↑) / DXY(↑) / VIX(→)
- **Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCIΔ +0.000 / DXYΔ +0.100 / US10YΔ +0.046**
- **Expectations: dict received.**

- **판정:** **POLICY TIGHTENING (긴축)**
- **근거:** 금리↑ + 달러↑ → 긴축 압력
- **한줄요약 ~~** 구조=TIGHTENING (긴축)(MODERATE)는 참고, 가격=POLICY TIGHTENING (긴축) 중심 → 최종 POLICY TIGHTENING (긴축)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-05-06 (FRED latest)
- **NET_LIQ level:** 5831742.4
- **TGA level:** 877761.0
- **RRP level:** 1.633
- **방향(전일 대비):** TGA(↓) / RRP(↑) / NET_LIQ(↑)
- **판정:** **LIQUIDITY SUPPORTIVE (완만한 유동성 우호)**
- **근거:** Net Liquidity↑ → 시장 내 달러 여력 개선
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-05-08 (FRED latest)
- **HY_OAS level:** 2.81% → **COOL (낮은 공포)**
- **방향(전일 대비):** HY_OAS(↑) / +0.72%
- **판정:** **CREDIT CALM**
- **근거:** HY 스프레드 낮음 → 크레딧 스트레스 제한 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(↓)
- **HYG:** today 79.980 / prev 80.140 / pct -0.20%
- **LQD:** today 108.930 / prev 109.200 / pct -0.25%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, +1.05%)** → 완화 기대 약화/금리 부담
- DXY **(Mild, +0.10%)** → 달러 강세/신흥국 부담
- WTI **(Strong, +2.78%)** → 인플레 재자극 가능성
- VIX **(N/A, N/A)** → 변동성 보합(심리 변화 제한)
- 원/달러(USDKRW) **(Clear, +0.40%)** → 원화 약세/수급 부담
- HYG (High Yield ETF) **(Mild, -0.20%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Mild, -0.25%)** → 우량채 약세(리스크온 성향)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 상승(US10Y↑)** → 실질 금리 압박 → 달러 강세(DXY↑) 유도: **신흥국 자본 유출 및 고밸류 성장주 할인율 부담 증가**
- **변동성 보합(VIX→)** → 심리 변화 제한: 현재의 추세가 관성적으로 유지되는 구간
- **유가 상승(WTI↑)** → 기대 인플레이션 자극: **제조/운송업 비용 부담 가중 및 중앙은행의 긴축 유지 명분 강화**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### 🌊 Drift Monitor (v4)
- **정의:** 누적 흐름 + ATR 기반 강도 감지

- **SPY:** 🟡 PULLBACK | Short-term: SHORT DOWN | 1D=-0.41% / 5D=+1.73% | Strength: LOW
- **WTI:** 🟡 REBOUND | Short-term: MIXED | 1D=+3.34% / 5D=-0.90% | Strength: MEDIUM
- **DXY:** 🟡 REBOUND | Short-term: SHORT UP | 1D=+0.38% / 5D=-0.17% | Strength: LOW
- **GOLD:** 🟡 PULLBACK | Short-term: SHORT DOWN | 1D=-0.36% / 5D=+3.20% | Strength: LOW

- **Drift Score:** 0
- **State:** **NO DRIFT**
- **Label:** INFLATION_RISK_OFF
- **SEW Combo Signal:** NONE

- **Market Drift Summary:**
  - Equity (SPY): 🟡 PULLBACK / SHORT DOWN
  - Oil (WTI): 🟡 REBOUND / MIXED
  - Dollar (DXY): 🟡 REBOUND / SHORT UP
  - Gold (GOLD): 🟡 PULLBACK / SHORT DOWN

### ⚠ 6.5) Correlation Break Monitor
⚠ Market Closed / Stale Data → Correlation signals evaluated conservatively.

No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
⚠ Market Closed / Stale Data → Sector signals evaluated conservatively.

Correlation Break Detected:
- US10Y ↑ but XLRE ↑
- US10Y ↑ but XLK ↑

So What?
- 결론: **섹터 ‘공식’이 깨진 구간** → 방향 베팅보다 **사이징 축소 + 리더 중심**

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 보합(VIX→)** → 심리 변화 제한
- **금리 상승(US10Y↑)** → 할인율 부담/유동성 압박 가능
- **달러 강세(DXY↑)** → 신흥국·원자재·원화 등 위험자산에 부담
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
⚠ Market Closed / Stale Data → Price-based geo signals muted.

- **Geo Stress Score (z-composite):** **-0.10**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** -0.27
- **Geo Momentum:** +0.17 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Red_Sea
- **Cosine Similarity Score:** 0.404
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Red_Sea: 0.404
  - Ukraine_2022: 0.309
  - China_Trade_2018: 0.247
- **Top Drivers:**
  - VIX: z_used=+0.53 (z1d=+0.87, z5d=+0.01, raw_w=0.18, norm_w=0.14) → contrib=+0.07
  - KR10Y_SPREAD: z_used=-1.02 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.06
  - BDRY: z_used=+1.38 (z1d=+1.59, z5d=+1.08, raw_w=0.05, norm_w=0.04) → contrib=+0.05
  - DE10Y_SPREAD: z_used=-1.02 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=-0.05
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Red_Sea** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (GLD)
- **Extreme Country Risk:** GLD

### ⚡ 7.3) Pseudo Gamma Filter
- **정의:** 옵션 데이터 없이 시장의 감마 환경을 추론
- **주의:** Dealer Gamma Bias 숫자와 Pseudo Gamma State는 서로 다른 레이어

- **Pseudo Gamma State:** 🟢 POSITIVE GAMMA (WEAK)
- **Dealer Gamma Bias:** 1.00 (NEUTRAL / transition zone)
- **Bias:** 안정적 시장
- **Strategy:** 과도한 베팅 금지

- **Drift Score:** 0 (NO DRIFT)
- **VIX:** 18.3799991607666
- **SEW:** DEADMAN / NORMAL

- **🚀 Combo Signal:** ⚠️ SHOCK but gamma not fully negative

### 🏦 Institutional Flow Engine (v2-minimal)
- **정의:** 기관성 자금이 뉴스 전에 남기는 흔적을 구조적으로 탐지

- **Raw Flow State:** **NO CLEAR FLOW**
- **Transition State:** **NO CLEAR FLOW**
- **Flow Delta:** -1 (prev=2 → current=1)
- **Persistence Days:** 0
- **Transition Note:** 기관성 흐름 상태 유지
- **Confidence:** **LOW**
- **Action Bias:** **IGNORE**

- **Drift:** NO DRIFT / INFLATION_RISK_OFF / NONE
- **Gamma:** 🟢 POSITIVE GAMMA (WEAK) / ⚠️ SHOCK but gamma not fully negative
- **SEW:** DEADMAN / NORMAL
- **Positioning (POS_Z):** 0.0
- **Validation Score:** 1 (boost applied: +1)

- **Drivers:**
  - Credit confirms risk appetite

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(47.00bp) | 실질금리(1.93%) | DXY(97.94)
*(as of: RealRate: 2026-05-12 / FRED last available)*

Neutral - 자본의 방향성이 탐색 구간에 있음 (실질금리 정상화 과정)

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** 금리↑ + 달러↑ + 유가↑
- **최종 판정:** **비용 상승형 물가 부담 및 경기 둔화 우려 반영**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Mild) / WTI(Strong) / VIX(N/A)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.410), DXY(97.940), VIX(18.38)

### 🏗️ 12) Structural Filter (v3)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↑) / GOLD(↓) / VIX(→) / WTI(↑)
- **Meaningful Move Check:** DXY=0.10221392810588373 / GOLD=-0.03600769143322094 / US10Y=1.0540789519547211 / VIX=N/A / WTI=2.77719720889844
- **판정:** **NEUTRAL**
- **근거:** 글로벌 매크로 구조의 특이 신호가 감지되지 않음


### 12.5) Growth Sustainability Filter [SHADOW]
- **Score:** 2
- **Label:** FRAGILE_EXPANSION
- **Demand Proxy:** 0
- **Financing:** 2
- **Energy Burden:** 0
- **Policy Capacity:** 0

📌 Shadow Note: This filter is observation-only and does not affect Final Exposure, Phase, or Sector Allocation.



### 12.8) Positioning Stress Filter [SHADOW]

- **Score:** 0
- **Label:** SQUEEZE_RISK

**Positioning Notes**
- Term Structure: VIX3M data missing
- Short-Term Hedge: VIX9D data missing
- Gamma Structure: Neutral gamma
- Positioning: Neutral positioning

📌 Shadow Note: This filter estimates whether current market behavior reflects structural participation or unstable positioning stress (squeeze / unwind / panic). No impact on Final Exposure, Phase, or Allocation.



### 12.6) Flow Authenticity Filter [SHADOW]
- **Score:** 2
- **Label:** EARLY_ROTATION
- **Breadth / Participation:** -2
- **Breadth Note:** XLK only leadership → narrow rally
- **Nasdaq Breadth Note:** QQQE/QQQ return data missing
- **Positioning / Gamma:** 0
- **Credit Confirmation:** 2
- **Macro Participation:** 2

📌 Shadow Note: This filter estimates whether upside is driven by real accumulation or short-covering. No impact on Final Exposure, Phase, or Allocation.



### 12.7) Leadership Breadth Filter [SHADOW]
- **Score:** 0
- **Label:** CONCENTRATED_LEADERSHIP

**Leadership Notes**
- QQQ/SPY return data missing
- SMH/QQQ return data missing
- SOXX/QQQ return data missing
- IWM/SPY return data missing
- XLF/SPY return data missing
- XLI/SPY return data missing
- XLY/SPY return data missing

📌 Shadow Note: This filter checks whether leadership is broadening beyond mega-cap tech/AI. No impact on Final Exposure, Phase, or Allocation.


### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCIΔ +0.000 / DXYΔ +0.100 / US10YΔ +0.046 (정상)
- **Sentiment (Fear&Greed):** 57.14214693894362 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** UP (MID)
- **Phase:** EVENT-WATCHING (이벤트 관망) (Cap: 100)
- **Drift:** NO DRIFT / INFLATION_RISK_OFF / NONE
- **Drift Score:** 0
- **Flow Score:** 1
- **Flow Continuity:** EARLY_TRACE → NO CLEAR FLOW (N/A, tilt=+0)
- **Flow Regime Tilt:** +0 / Flow-Gamma Tilt: +0

- **🎯 Final Risk Action:** **HOLD**
- **Risk Budget (0~100):** **55**
- **Narrative:** 구조=TIGHTENING / 심리=NEUTRAL / 유동성=증가/중간 / 크레딧=안정 / 드리프트=NO DRIFT (INFLATION_RISK_OFF) / 수급=0.00 → Phase=EVENT-WATCHING (이벤트 관망)

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `TIGHTENING` | **Price(Regime):** `EVENT-WATCHING` | **Bucket:** `MIXED` | **VIX:** `18.38`
- **Positioning Data:** Z-Score: `0.00` (>1.8 시 Run) | Gamma: `1.00` (<0.5 시 Run) | CTA: `0.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v3.2)
- **정의:** 13번 Risk Budget 실행 브레이크 레이어
- **추가 이유:** 전략 판단(13) 이후 실제 진입 강도를 조절하기 위함

- **Base Risk Budget (13):** 55
- **VIX Level:** 18.38 (NORMAL) | **Change:** N/A
- **Final Multiplier:** 0.90x (VIX x Positioning x Confidence)
- **Confidence Level:** LOW (flow_score=1)
- **Slope Intensity:** 0.0000
- **Brake Drivers:** ⚠️ Low Confidence

- **📊 Recommended Exposure:** **50%**

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

**Context:** phase=EVENT-WATCHING (이벤트 관망) / T10Y2Y=0.47 (MODERATE STEEP) / VIX=18.38 (VOLATILITY NORMAL) / liquidity=UP-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM

**Macro Profile:** STAGFLATION_STRESS
**Macro Inputs Debug:** phase=EVENT-WATCHING (이벤트 관망) / us10y_pct=+1.05% / dxy_pct=+0.10% / wti_pct=+2.78% / vix=18.38 / liq_easy=True / liq_tight=False / credit_calm=True / flow_score=1

**Flow Overlay:** flow_score=1 / flow_state=NO CLEAR FLOW / drift_label=INFLATION_RISK_OFF / gamma=🟢 POSITIVE GAMMA (WEAK)

**Overweight:** Technology, Consumer Discretionary, Materials

**Underweight:** Energy, Financials, Real Estate, Utilities, Industrials

**Scoreboard:**
- Technology: +1.0  (+2 LIQ, -1 PHASE, +2 MOM, = +1.0)
- Consumer Discretionary: +0.4  (+1.5 LIQ, -0.5 PHASE, = +0.4)
- Materials: +0.2  (+0.5 PHASE, = +0.2)
- Industrials: -0.0  (+1.5 LIQ, +1 CURVE, -1 PHASE, = -0.0)
- Utilities: -0.8  (-1 LIQ, -1 PHASE, = -0.8)
- Real Estate: -1.0  (-1 PHASE, -1 MOM, = -1.0)
- Financials: -1.3  (+1 LIQ, +2 CURVE, -2 MOM, = -1.3)
- Energy: -1.9  (+1.5 PHASE, -2 MOM, = -1.9)

**Rationale (Why the score exists: 섹터 점수의 핵심 드라이버)**
- OW Technology: +2: 유동성 완화 → 성장주/베타 우호
- OW Technology: +2: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- OW Consumer Discretionary: +1.5: 유동성 완화 → 소비 민감주 우호
- OW Consumer Discretionary: -0.5: Stagflation Stress → 소비 여력 압박
- OW Materials: +0.5: Stagflation Stress → 원자재 민감 섹터 일부 우호
- UW Energy: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Energy: +1.5: Stagflation Stress → 유가/인플레 압력 수혜
- UW Energy: -2: Relative Strength 약세 (vs SPY) → 소외 섹터
- UW Financials: THEORY_TRAP → 거시/이론 우호 대비 실제 자금흐름 및 상대강도 약세
- UW Financials: +1: 유동성 완화 → 위험선호 회복
- UW Financials: +2: 완만한 스티프닝(0.47) → 예대마진 개선
- UW Real Estate: -1: Stagflation Stress → 조달비용 부담
- UW Real Estate: -1: Relative Strength 약세 (vs SPY) → 소외 섹터

**Regime Controller:**
- DISLOCATION (avg_divergence=-0.78, dispersion=1.73)
Correlation Break: True / Leader=UNKNOWN
- Interpretation: 섹터별 괴리가 큰 불안정 장세 → 포지션 축소와 리더 섹터 검증 필요
- Correlation Break: True / Leader=UNKNOWN

**Divergence / Classification Monitor (Theory vs Flow alignment: 이론과 실제 자금흐름 정렬 여부)**
- Communication Services: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Consumer Staples: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Health Care: NEUTRAL (theory=+0.0, flow=+0.0, final=+0.0)
- Industrials: FLOW_WEAK (theory=+2.5, flow=+0.0, final=-0.0)
- Real Estate: AVOID (theory=-1.0, flow=-0.7, final=-1.0)
- Financials: THEORY_TRAP (theory=+3.0, flow=-1.4, final=-1.3)
- Energy: THEORY_TRAP (theory=+1.5, flow=-1.4, final=-1.9)

### 💰 18.5) Tactical Asset Allocation (Execution Weight)
- **Strategic Exposure (15):** **50.0%** → **Regime Adjusted:** **42.5%**
- **Exposure Override:** DISLOCATION → 섹터 괴리 확대, 총노출 15% 축소

| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |
| :--- | :---: | :---: | :---: | :--- |
| Technology | +1.5 | ALIGNED | **12.0%** | HOLD |
| Materials | +0.2 | ALIGNED | **4.7%** | HOLD |
| Consumer Discretionary | +0.1 | ALIGNED | **1.4%** | HOLD |
| **Cash & Hedge** | - | - | **81.9%** | DEFENSIVE |

- **Allocation Check:** Sector Weights + Cash = **100.0%**
- **Regime Cap Profile:** STAGFLATION_STRESS
- **Regime Cap Applied:**
  - Technology: 34.9% → 12.0% (-22.9%)


**Deleveraging Priority Preview:**
- 기준: Divergence → Momentum → Score → Current Weight
1. Consumer Discretionary (priority_score=-0.05, score=0.10999999999999999, weight=1.4%, div=ALIGNED, mom=0)
2. Materials (priority_score=-0.1, score=0.21, weight=4.7%, div=ALIGNED, mom=0)
3. Technology (priority_score=-1.84, score=1.47, weight=12.0%, div=ALIGNED, mom=2)

**Leveraging Priority Preview:**
- 기준: Score → Momentum → Positive Divergence
1. Technology (priority_score=4.47, score=1.47, weight=12.0%, div=ALIGNED, mom=2)
2. Materials (priority_score=0.21, score=0.21, weight=4.7%, div=ALIGNED, mom=0)
3. Consumer Discretionary (priority_score=0.11, score=0.10999999999999999, weight=1.4%, div=ALIGNED, mom=0)

### 🧬 19) Execution Layer (ETF Mapping)

| Sector | ETF | Weight | Action | Divergence | Classification |
| :--- | :---: | :---: | :--- | :--- | :--- |
| Technology | XLK | 12.0% | ADD | ALIGNED | ALIGNED |
| Materials | XLB | 4.7% | SMALL | ALIGNED | ALIGNED |
| Consumer Discretionary | XLY | 1.4% | MICRO | ALIGNED | ALIGNED |


### 🧬 19.5) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Execution Notes:**
- Flow weak → avoid chasing; keep only proven leaders.

**Preferred Company Traits:**
- Cash flow visibility and earnings stability
- Market leaders with confirmed relative strength

**Risk Control / Avoid:**
- Rate-sensitive long-duration equities
- Flow-weak cyclicals and theory-only sector bets

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.8310832350336235
- **Z-Score (5d):** -0.05157991563370826

### EEM
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -1.3742949714776753
- **Z-Score (5d):** 0.11035519186423431

### EIS
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.43024256923559134
- **Z-Score (5d):** 0.41721354770652547

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.6247473702408144
- **Z-Score (5d):** 0.12340216644454328

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.13786720634266403
- **Z-Score (5d):** 1.0539760445699289

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.007048241655164147
- **Z-Score (5d):** 1.2130664272871252

### GLD
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.4597687221997055
- **Z-Score (5d):** 0.8005747251358315

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.5764500311002168
- **Z-Score (5d):** 0.5390171554594162

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.05750592110359534
- **Z-Score (5d):** -0.1271105988808705
