# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-04-24
**Data as of:** 2026-04-24

## ⚡ Strategic War Room (통합 대응)
> **시스템 상태: ✅ STABLE**
> **판단 요약: 구조-가격-수급 정렬 / 실시간 이상징후 없음 / 데드맨 정상**
### 🎯 Exposure Framework
- **Base Exposure (전략 기준): 35%**
- **Final Exposure (실행 기준): 27%**

- **Portfolio Stance:** REDUCE / 27%

- **[14번 구조·수급 괴리]:** ✅ **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **[실시간 보초병(SEW)]:** STABLE | ✅ 이상징후 없음 (5개 자산 정상 범위 / z-score 발작 없음)
- **[SEW Event Type]:** NORMAL
  → 해석: 정상 상태 / 구조적 리스크 없음
- **[SEW Spike Monitor]:** Spike 0 / Extreme 0
- **[15번 데드맨]:** ✅ PASS
- **[14번 수급 시그널]:** 🚨 **STAY (포지션 유지)**

### 📌 Interpretation
- 금일 시장은 **RISK-OFF (긴축/불안·리스크 회피) 환경**이며 유동성과 정책은 완화적 상태
- 그러나 **기관 자금 유입은 아직 확신 단계에 도달하지 못한 초기 흐름 구간**
- 감마 구조는 안정적이나, **드리프트 강도가 약해 추세 신뢰도는 제한적**
- 따라서 **신규 진입보다는 기존 포지션 관리 및 일부 리스크 축소가 우선**

### 🎯 Final Action Engine(Raw Signal)
- **Action:** REDUCE
- **Size:** DEFENSIVE
- **Confidence:** MEDIUM
- **Reason:**
  - Risk-off environment

## 🎯 Final Decision (War Room Override)
- **Final Action:** **REDUCE**
- **Final Exposure:** **27%**
- **Base Context:** phase=RISK-OFF (긴축/불안·리스크 회피) / narrative=REDUCE / base_exposure=35%
- **SEW:** STABLE / NORMAL
- **Divergence:** ALIGNED / **STAY (포지션 유지)**
- **Drift:** NO DRIFT / INFLATION_RISK_OFF / NONE / score=0
- **Flow:** NO CLEAR FLOW / score=2
- **Gamma:** 🟢 POSITIVE GAMMA (WEAK)
- **Tactical Action:** REDUCE / DEFENSIVE / MEDIUM
- **Positioning:** pos_z=1.50
- **Warning Score:** 2 (6.6 섹터 상관관계 붕괴)
- **Tactical Why:** Risk-off environment
- **Why:** SEW STABLE → 실시간 이상징후 없음 → Divergence ALIGNED → 구조·가격·수급 정렬 → Narrative Action=REDUCE 반영 → Warning Score 2 → 익스포저 15% haircut → Tactical=REDUCE / Flow=NO CLEAR FLOW(2) / Drift=NO DRIFT(0) / Gamma=🟢 POSITIVE GAMMA (WEAK) → Tactical REDUCE → 방어 기조 유지 / 익스포저 5% 추가 축소

### 🚩 Market Regime Status
- **국면 전환 감지:** 🚨 **TRANSITION / MIXED (전환·혼조)** → **RISK-OFF (긴축/불안·리스크 회피)**

---

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.323  (+0.68% vs 4.294)
- **달러 인덱스**: 98.876  (+0.29% vs 98.590)
- **WTI 유가**: 96.660  (+3.98% vs 92.960)
- **변동성 지수 (VIX)**: 19.310  (+2.06% vs 18.920)
- **원/달러 환율**: 1482.280  (-0.24% vs 1485.800)

---

---

## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 19.31 → **Mid (Neutral/Mixed)**
- **핵심 조합(전일 대비 방향):** US10Y(↑) / DXY(↑) / VIX(↑)
- **판정:** **RISK-OFF (긴축/불안·리스크 회피)**
- **근거:** 금리↑ + 달러↑ + VIX↑ → 안전자산/현금 선호 강화

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(↑) / DXY(↑) / VIX(↑)
- **현실(FCI):** level=EASY (완화) / dir(→) | as of: 2026-04-24 (FRED last available)
- **유인(Real Rates):** level=NEUTRAL (중립) / dir(→) | as of: 2026-04-24 (FRED last available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(↑) / DXY(↑) / VIX(↑)
- **Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCIΔ +0.000 / DXYΔ +0.286 / US10YΔ +0.029**
- **Expectations: dict received.**

- **판정:** **POLICY TIGHTENING (긴축)**
- **근거:** 금리↑ + 달러↑ → 긴축 압력
- **한줄요약 ~~** 구조=TIGHTENING (긴축)(MODERATE)는 참고, 가격=POLICY TIGHTENING (긴축) 중심 → 최종 POLICY TIGHTENING (긴축)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-04-22 (FRED latest)
- **NET_LIQ level:** 5701450.5
- **TGA level:** 1005968.0
- **RRP level:** 0.538
- **방향(전일 대비):** TGA(↑) / RRP(↑) / NET_LIQ(↓)
- **판정:** **LIQUIDITY DRAINING (유동성 흡수)**
- **근거:** Net Liquidity↓ → 시장 내 달러 여력 축소 가능
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-04-22 (FRED latest)
- **HY_OAS level:** 2.84% → **COOL (낮은 공포)**
- **방향(전일 대비):** HY_OAS(↓) / -0.35%
- **판정:** **CREDIT CALM**
- **근거:** HY 스프레드 낮음 → 크레딧 스트레스 제한 / 스프레드가 좁혀지는 중 → 공포 온도 완화
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(↓) / LQD(↓)
- **HYG:** today 80.370 / prev 80.500 / pct -0.16%
- **LQD:** today 109.520 / prev 109.820 / pct -0.27%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Strong, +0.68%)** → 완화 기대 약화/금리 부담
- DXY **(Clear, +0.29%)** → 달러 강세/신흥국 부담
- WTI **(Strong, +3.98%)** → 인플레 재자극 가능성
- VIX **(Clear, +2.06%)** → 심리 악화/리스크오프
- 원/달러(USDKRW) **(Clear, -0.24%)** → 원화 강세/수급 개선
- HYG (High Yield ETF) **(Mild, -0.16%)** → 크레딧 스트레스↑
- LQD (IG Bond ETF) **(Mild, -0.27%)** → 우량채 약세(리스크온 성향)

### 🧩 6) Cross-Asset Filter (자산군 연쇄 반응 분석)
- **추가 이유:** 단일 지표의 노이즈를 제거하고, 매크로 충격이 자산군 전반으로 확산되는 **전이 경로(Transmission Path)**를 파악하기 위함

- **금리 상승(US10Y↑)** → 실질 금리 압박 → 달러 강세(DXY↑) 유도: **신흥국 자본 유출 및 고밸류 성장주 할인율 부담 증가**
- **변동성 상승(VIX↑)** → 위험회피(Risk-Off) 강화: **안전 자산(Cash/USD) 선호도 급증 및 하이일드 스프레드 확대 압력**
- **유가 상승(WTI↑)** → 기대 인플레이션 자극: **제조/운송업 비용 부담 가중 및 중앙은행의 긴축 유지 명분 강화**

> **[Strategic Note]:** 위 연쇄 반응이 역사적 상관관계에서 벗어날 경우, **6.5) Correlation Break Monitor**를 통해 국면 전환 여부를 정밀 판별함

### 🌊 Drift Monitor (v4)
- **정의:** 누적 흐름 + ATR 기반 강도 감지

- **SPY:** 🟡 PULLBACK | Short-term: SHORT UP | 1D=-0.39% / 5D=+0.97% | Strength: LOW
- **WTI:** 🟢 UP | Short-term: SHORT DOWN | 1D=+0.85% / 5D=+15.28% | Strength: HIGH
- **DXY:** 🟢 UP | Short-term: SHORT UP | 1D=+0.07% / 5D=+0.79% | Strength: LOW
- **GOLD:** 🔴 DOWN | Short-term: SHORT DOWN | 1D=-0.40% / 5D=-3.52% | Strength: LOW

- **Drift Score:** 0
- **State:** **NO DRIFT**
- **Label:** INFLATION_RISK_OFF
- **SEW Combo Signal:** NONE

- **Market Drift Summary:**
  - Equity (SPY): 🟡 PULLBACK / SHORT UP
  - Oil (WTI): 🟢 UP / SHORT DOWN
  - Dollar (DXY): 🟢 UP / SHORT UP
  - Gold (GOLD): 🔴 DOWN / SHORT DOWN

### ⚠ 6.5) Correlation Break Monitor
No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
Correlation Break Detected:
- US10Y ↑ but XLF ↓
- US10Y ↑ but XLRE ↑

So What?
- 결론: **섹터 ‘공식’이 깨진 구간** → 방향 베팅보다 **사이징 축소 + 리더 중심**

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 상승(VIX↑)** → 변동성 확대: 포지션 축소/헤지 수요 증가 가능
- **금리 상승(US10Y↑)** → 할인율 부담/유동성 압박 가능
- **달러 강세(DXY↑)** → 신흥국·원자재·원화 등 위험자산에 부담
- **유가 상승(WTI↑)** → 인플레 압력/실질소득 부담 가능

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
- **Geo Stress Score (z-composite):** **+0.23**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** +0.04
- **Geo Momentum:** +0.19 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** China_Trade_2018
- **Cosine Similarity Score:** 0.652
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - China_Trade_2018: 0.652
  - Taiwan_Tension: 0.615
  - Ukraine_2022: 0.458
- **Top Drivers:**
  - USDCNH: z_used=+1.07 (z1d=+1.05, z5d=+1.10, raw_w=0.18, norm_w=0.14) → contrib=+0.15
  - EMB: z_used=+0.56 (z1d=-0.93, z5d=+0.00, raw_w=0.12, norm_w=0.09) → contrib=+0.05
  - EEM: z_used=+0.65 (z1d=-0.94, z5d=-0.21, raw_w=0.10, norm_w=0.08) → contrib=+0.05
  - VIX: z_used=+0.25 (z1d=+0.17, z5d=+0.38, raw_w=0.18, norm_w=0.14) → contrib=+0.03
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 과거 위기 패턴과 부분적으로 유사합니다. 현재 시장은 **China_Trade_2018** 계열의 초기 징후를 일부 보이고 있어, 관련 자산군과 지역 노출을 점검할 필요가 있습니다.
- **Country ETF Crash?** Yes (EWJ)
- **Extreme Country Risk:** EWJ

### ⚡ 7.3) Pseudo Gamma Filter
- **정의:** 옵션 데이터 없이 시장의 감마 상태 추론

- **Gamma State:** 🟢 POSITIVE GAMMA (WEAK)
- **Bias:** 안정적 시장
- **Strategy:** 과도한 베팅 금지

- **Drift Score:** 0 (NO DRIFT)
- **VIX:** 19.309999465942383
- **SEW:** STABLE / NORMAL

- **🚀 Combo Signal:** 🟢 STABLE FLOW

### 🏦 Institutional Flow Engine (v2-minimal)
- **정의:** 기관성 자금이 뉴스 전에 남기는 흔적을 구조적으로 탐지

- **Flow Score:** 2
- **Flow State:** **NO CLEAR FLOW**
- **Confidence:** **LOW**
- **Interpretation:** 기관성 축적 흔적 불충분
- **Action Bias:** **IGNORE**

- **Drift:** NO DRIFT / INFLATION_RISK_OFF / NONE
- **Gamma:** 🟢 POSITIVE GAMMA (WEAK) / 🟢 STABLE FLOW
- **SEW:** STABLE / NORMAL
- **Positioning (POS_Z):** 1.5
- **Validation Score:** 1 (boost applied: +1)

- **Drivers:**
  - Short-horizon pre-move
  - No shock yet
  - Positioning somewhat stretched
  - Credit confirms risk appetite

### 🎯 8) Incentive Filter (Wall St. Logic)

**핵심 신호:** 장단기차(51.00bp) | 실질금리(1.92%) | DXY(98.88)
*(as of: RealRate: 2026-04-24 / FRED last available)*

Neutral - 자본의 방향성이 탐색 구간에 있음 (실질금리 정상화 과정)

- **Note:** 실질금리와 달러는 자본의 '기회비용'을 결정하는 핵심 유인책입니다.

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** 금리↑ + 달러↑ + 유가↑ + VIX↑
- **최종 판정:** **긴축 공포 및 달러 수급 경색에 따른 '위험회피(Risk-Off)'**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Strong) / DXY(Clear) / WTI(Strong) / VIX(Clear)
- **판정:** **SIGNIFICANT MOVE (의미 있는 변화)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.323), DXY(98.876), VIX(19.31)

### 🏗️ 12) Structural Filter (v3)
- **질문:** 글로벌 화폐 가치와 에너지 패권 등 '판'의 변화가 있는가?
- **핵심 신호:** US10Y(↑) / DXY(↑) / GOLD(↓) / VIX(↑) / WTI(↑)
- **Meaningful Move Check:** DXY=0.2900934409336726 / GOLD=-1.007928057316429 / US10Y=0.6753564146644189 / VIX=2.0613075479692635 / WTI=3.9802115039550814
- **판정:** **GLOBAL FINANCIAL TIGHTENING (글로벌 긴축 구조)**
- **근거:** 금리↑ + 달러↑가 모두 의미 있는 수준으로 나타나 글로벌 자본 조달 비용 압박

### 🧠 13) Narrative Engine (v2 + Risk Budget + Drift)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: TIGHTENING (긴축) (MODERATE, score=+1.5) | REAL_RATEΔ +0.000 / FCIΔ +0.000 / DXYΔ +0.286 / US10YΔ +0.029 (정상)
- **Sentiment (Fear&Greed):** 59.56760726839175 (NEUTRAL)
- **Credit Calm:** True
- **Liquidity (NET_LIQ):** DOWN (MID)
- **Phase:** RISK-OFF (긴축/불안·리스크 회피) (Cap: 35)
- **Drift:** NO DRIFT / INFLATION_RISK_OFF / NONE
- **Drift Score:** 0

- **🎯 Final Risk Action:** **REDUCE**
- **Risk Budget (0~100):** **35**
- **Narrative:** 구조=TIGHTENING / 심리=NEUTRAL / 유동성=감소/중간 / 크레딧=안정 / 드리프트=NO DRIFT (INFLATION_RISK_OFF) / 수급=1.50 ⚠️ 수급 다소 과열 → Phase=RISK-OFF (긴축/불안·리스크 회피)

### ⚠ 14) Divergence Monitor (Macro vs Positioning)
- **추가이유:** 시장 가격과 정책 사이의 괴리 및 수급의 '질'을 파악하여 폭발적 반전 가능성 진단
- **핵심질문:** 정책은 이런데 주가는 왜 반대로 가지?(Anomaly) 그 뒤에 숨은 수급 주체(CTA, Dealer)들은 지금 어떤 상태인가?

- **Structure(3번):** `TIGHTENING` | **Price(Regime):** `RISK-OFF` | **VIX:** `19.31`
- **Positioning Data:** Z-Score: `1.50` (>1.8 시 Run) | Gamma: `2.27` (<0.5 시 Run) | CTA: `1.0` (추세 변곡점 확인)
- **Status:** **ALIGNED** -> **해석:** 구조와 가격, 수급이 조화를 이루며 추세 유지 중
- **Action Signal:** 🚨 **STAY (포지션 유지)**

### 🎯 15) Volatility-Controlled Exposure (v2.6)
- **정의:** Risk Budget을 실제 익스포저로 변환 (Positions & Deadman Switch)
- **추가 이유:** 수급 과열(POS_Z)이나 급격한 쏠림 발생 시 강제 시스템 셧다운

- **Risk Budget:** 35 | **Phase Cap:** 35
- **VIX Level:** 19.31 (NORMAL) | **Change:** +2.06%
- **Final Multiplier:** 1.00x (Vol x Pos)
- **Slope Intensity:** 0.0000 (Stable)

- **📊 Recommended Exposure:** **35%**

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

**Context:** phase=RISK-OFF (긴축/불안·리스크 회피) / T10Y2Y=0.51 (MODERATE STEEP) / VIX=19.31 (VOLATILITY NORMAL) / liquidity=DOWN-MID / credit=True

**Signal Priority:** VOL > LIQ > CURVE > CREDIT > PHASE > FLOW > MOM

**Flow Overlay:** flow_score=2 / flow_state=NO CLEAR FLOW / drift_label=INFLATION_RISK_OFF / gamma=🟢 POSITIVE GAMMA (WEAK)

**Overweight:** Consumer Staples, Health Care, Financials, Industrials, Utilities

**Underweight:** Technology, Consumer Discretionary, Energy, Real Estate

**Scoreboard:**
- Consumer Staples: +4  (+3 LIQ, +1 PHASE, = +4)
- Health Care: +4  (+3 LIQ, +1 PHASE, = +4)
- Financials: +1  (+2 CURVE, -1 MOM, = +1)
- Industrials: +1  (+1 CURVE, = +1)
- Utilities: +1  (+1 LIQ, = +1)
- Consumer Discretionary: -1  (-1 LIQ, = -1)
- Energy: -1  (-1 MOM, = -1)
- Real Estate: -1  (-2 LIQ, +1 MOM, = -1)
- Technology: -2  (-3 LIQ, -1 PHASE, +2 MOM, = -2)

**Rationale (top drivers):**
- OW Consumer Staples: +3: 유동성 긴축 → 방어적 필수소비 선호
- OW Consumer Staples: +1: RISK-OFF → 방어주 미세 가점
- OW Health Care: +3: 유동성 긴축 → 안정적 현금흐름 선호
- OW Health Care: +1: RISK-OFF → 퀄리티 미세 가점
- OW Financials: +2: 완만한 스티프닝(0.51) → 예대마진 개선
- OW Financials: -1: Relative Strength 약세 (vs SPY) → 소외 섹터
- OW Industrials: +1: 완만한 스티프닝(0.51) → 성장 기대 반영
- UW Technology: +2: Relative Strength 강세 (vs SPY) → 자금 유입 확인
- UW Technology: -3: 유동성 긴축 → 고밸류에이션 부담

**Divergence Monitor (Theory vs Flow):**
- Real Estate: POSITIVE_DIVERGENCE
- Technology: POSITIVE_DIVERGENCE

### 💰 18.5) Tactical Asset Allocation (Execution Weight)
- **Total Target Exposure:** **35.0%** (from Filter 15)

| Sector | Score | Divergence | **Weight in Portfolio** | **Action** |
| :--- | :---: | :---: | :---: | :--- |
| Consumer Staples | +4 | ALIGNED | **13.1%** | ACCUMULATE |
| Health Care | +4 | ALIGNED | **13.1%** | ACCUMULATE |
| Financials | +1 | ALIGNED | **3.3%** | HOLD |
| Industrials | +0.7 | ALIGNED | **2.3%** | HOLD |
| Utilities | +1 | ALIGNED | **3.3%** | HOLD |
| **Cash & Hedge** | - | - | **64.9%** | DEFENSIVE |

- **Allocation Check:** Sector Weights + Cash = **100.0%**

### 🧬 19) Execution Layer (ETF Mapping)

| Sector | ETF | Weight | Action |
| :--- | :---: | :---: | :--- |
| Consumer Staples | XLP | 13.1% | ADD |
| Health Care | XLV | 13.1% | ADD |
| Financials | XLF | 3.3% | SMALL |
| Industrials | XLI | 2.3% | SMALL |
| Utilities | XLU | 3.3% | SMALL |


### 🧬 19.5) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Preferred Company Traits:**
- High Free Cash Flow generators
- Net cash or low leverage balance sheets
- Stable margins / pricing power
- Low to mid beta exposure
- RAROC-friendly profile
- Cash flow visibility and earnings stability

**Risk Control / Avoid:**
- Negative FCF / cash-burn models
- High leverage / refinancing-dependent names
- Long-duration, high-multiple growth
- Rate-sensitive long-duration equities

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.6874239429137498
- **Z-Score (5d):** -0.19442920472854525

### EEM
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.9447328496456631
- **Z-Score (5d):** -0.20960226904626034

### EIS
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.018099115775402685
- **Z-Score (5d):** 0.06977531056869712

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.992760203308429
- **Z-Score (5d):** -0.1100446566932307

### EWJ
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -0.490206261355641
- **Z-Score (5d):** -0.8765332782163968

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.905861424019054
- **Z-Score (5d):** -0.5648981625434227

### GLD
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.3234137601425192
- **Z-Score (5d):** -0.34560019942436543

### SPY
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.44776866442781743
- **Z-Score (5d):** 0.33725837200442044

### VXX
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.09301301925608915
- **Z-Score (5d):** -0.061599687709342
