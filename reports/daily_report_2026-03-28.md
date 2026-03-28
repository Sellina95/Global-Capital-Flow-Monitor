# 🌍 Global Capital Flow – Daily Brief
**Date:** 2026-03-28
**Data as of:** 2026-03-28

## 📊 Daily Macro Signals

- **미국 10년물 금리**: 4.440  (+0.00% vs 4.440)
- **달러 인덱스**: 100.150  (+0.00% vs 100.150)
- **WTI 유가**: 99.640  (+0.00% vs 99.640)
- **변동성 지수 (VIX)**: 31.050  (+0.00% vs 31.050)
- **원/달러 환율**: 1508.360  (+0.00% vs 1508.360)

---

## 🚨 Regime Change Monitor (always-on)
- **Status:** ✅ DETECTED
- **Prev → Current:** RISK-OFF (긴축/불안·리스크 회피) → WAITING / RANGE (대기·박스권)
- **File:** `insights/risk_alerts.txt` ✅ created
- **Email:** ❌ not sent (RESEND env missing (RESEND_API_KEY/RESEND_FROM/RESEND_TO))

---

Some commentary here
## 🧭 Strategist Commentary (Seyeon’s Filters)

### 🧩 1) Market Regime Filter
- **정의:** 지금 어떤 장(場)인지 판단하는 *시장 국면 필터*
- **추가 이유:** 같은 지표도 ‘국면’에 따라 의미가 완전히 달라지기 때문

- **VIX 레벨:** 31.05 → **High (Risk-off bias)**
- **핵심 조합(전일 대비 방향):** US10Y(→) / DXY(→) / VIX(→)
- **판정:** **WAITING / RANGE (대기·박스권)**
- **근거:** 핵심 축(금리/달러/변동성) 모두 보합 → 방향성 부재

### 💧 2) Liquidity Filter (Enhanced)
- **질문:** 시장에 새 돈이 들어오는가, 말라가는가?
- **추가 이유:** US10Y/DXY/VIX는 ‘시장의 기대’를 보여주고, FCI는 ‘현실의 압박’을, Real Rates는 ‘위험을 감수할 유인’을 보여준다.

- **기대(가격) 신호:** US10Y(→) / DXY(→) / VIX(→)
- **현실(FCI):** level=EASY (완화) / dir(↑) | as of: 2026-03-20 (FRED last available)
- **유인(Real Rates):** level=RESTRICTIVE (유인↓) / dir(↓) | as of: 2026-03-26 (FRED last available)
- **판정:** **LIQUIDITY MIXED / FRAGILE (혼조·취약)**
- **근거:** 기대(가격)와 현실(FCI)/유인(실질금리) 정렬이 불완전
- **Note:** FCI/Real Rates는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🏛️ 3) Policy Filter (with Expectations)
- **질문:** 중앙은행·정책 환경은 완화인가, 긴축인가?

- **가격(현재) 신호:** US10Y(→) / DXY(→) / VIX(→)
- **Policy Bias: TIGHTENING (긴축) (MODERATE, score=+2.0) | REAL_RATEΔ +0.060 / FCIΔ +0.039 / DXYΔ +0.000 / US10YΔ +0.000**
- **Expectations: dict received.**

- **판정:** **POLICY MIXED (정책 신호 혼조)**
- **근거:** 금리/달러/변동성 신호가 완전히 정렬되지 않음
- **한줄요약 ~~** 구조=TIGHTENING (긴축)(MODERATE)는 참고, 가격=POLICY MIXED (정책 신호 혼조) 중심 → 최종 POLICY MIXED (정책 신호 혼조)

### 🧰 4) Fed Plumbing Filter (TGA/RRP/Net Liquidity)
- **질문:** 시장의 ‘달러 체력’은 늘고 있나, 줄고 있나?
- **추가 이유:** 금리·달러가 안정적이어도 유동성이 빠지면 리스크 자산은 쉽게 흔들릴 수 있음
- **Liquidity as of:** 2026-03-25 (FRED latest)
- **NET_LIQ level:** 5783083.2
- **TGA level:** 874077.0
- **RRP level:** 0.777
- **방향(전일 대비):** TGA(↑) / RRP(↑) / NET_LIQ(↓)
- **판정:** **LIQUIDITY DRAINING (유동성 흡수)**
- **근거:** Net Liquidity↓ → 시장 내 달러 여력 축소 가능
- **Note:** TGA/RRP/WALCL은 매일 갱신되지 않을 수 있어, 리포트에는 ‘최근 available 값’을 반영함

### 🌡️ 4.2) High Yield Spread Filter (HY OAS)
- **질문:** 시장 공포의 ‘온도’는 올라가고 있나, 내려가고 있나?
- **추가 이유:** HYG/LQD가 ‘방향’이라면, HY Spread는 ‘강도(얼마나 무서워하는지)’를 보여줌
- **Spread as of:** 2026-03-26 (FRED latest)
- **HY_OAS level:** 3.21% → **WARM (경계)**
- **방향(전일 대비):** HY_OAS(↑) / +1.26%
- **판정:** **CREDIT WATCH**
- **근거:** 스프레드 상승 구간 진입 → 리스크 프리미엄 확대 가능 / 스프레드가 벌어지는 중 → 공포 온도 상승
- **Note:** HY OAS는 매일 갱신되지 않을 수 있어, ‘최근 available 값’을 반영함

### 🧾 4.5) Credit Stress Filter (HYG vs LQD)
- **질문:** 크레딧 시장이 먼저 ‘리스크오프’를 말하고 있는가?
- **추가 이유:** HYG가 LQD보다 약해지면, 시장이 ‘위험을 감수할 이유가 없다’고 판단하기 시작했을 가능성
- **방향(전일 대비):** HYG(→) / LQD(→)
- **HYG:** today 78.720 / prev 78.720 / pct 0.00%
- **LQD:** today 107.620 / prev 107.620 / pct 0.00%
- **판정:** **CREDIT NEUTRAL**
- **근거:** HYG/LQD 방향성이 뚜렷하지 않음

### 📌 5) Directional Signals (Legacy Filters)
**추가 이유:** 개별 자산의 단기 방향성과 노이즈 강도를 구분해 과도한 해석을 방지하기 위함
- 미국 금리(US10Y) **(Noise, +0.00%)** → 보합(관망)
- DXY **(Noise, +0.00%)** → 달러 보합(방향성 약함)
- WTI **(Noise, +0.00%)** → 유가 보합(물가 변수 제한)
- VIX **(Noise, +0.00%)** → 변동성 보합(심리 변화 제한)
- 원/달러(USDKRW) **(Noise, +0.00%)** → 환율 보합(수급 압력 제한)
- HYG (High Yield ETF) **(Noise, +0.00%)** → 보합(크레딧 변화 제한)
- LQD (IG Bond ETF) **(Noise, +0.00%)** → 보합(방향성 제한)

### 🧩 6) Cross-Asset Filter (연쇄효과 분석)
- **추가 이유:** 한 지표의 변화가 다른 자산군에 어떻게 전파되는지 파악하기 위함

- **금리 보합(US10Y→)** → 할인율 변수 제한
- **변동성 보합(VIX→)** → 심리 변화 제한
- **유가 보합(WTI→)** → 물가 변수 제한

### ⚠ 6.5) Correlation Break Monitor
⚠ Market Closed / Stale Data → Correlation signals muted.

- DEBUG: US10Y=0.0, TECH(qqq/xlk)=0.0, SPY=0.0

No significant correlation break detected.

### ⚠ 6.6) Sector Correlation Break Monitor
- DEBUG: pct XLK=0.0, XLF=0.0, XLE=0.0, XLRE=0.0
⚠ Market Closed / Stale Data → Sector signals muted.

No significant sector-level correlation break detected.

### 🧩 7) Risk Exposure Filter (숨은 리스크 분석)
- **추가 이유:** 숫자는 괜찮아 보여도 그 뒤에 숨은 리스크를 식별하기 위함

- **VIX 보합(VIX→)** → 심리 변화 제한
- **금리 보합(US10Y→)** → 금리 변수 제한
- **달러 보합(DXY→)** → 달러 변수 제한
- **유가 보합(WTI→)** → 물가 변수 제한

### 🛰️ 7.2) Geopolitical Early Warning Monitor (FX/Commodities Composite)
⚠ Market Closed / Stale Data → Price-based geo signals muted.

- **Geo Stress Score (z-composite):** **+0.23**  *(Level: NORMAL)*
- **Coverage:** 100% *(used weight: 1.30 / defined weight: 1.30)*
- **3D Avg Score:** +0.38
- **Geo Momentum:** -0.14 *(Status: FLAT)*

**Historical Pattern Match (Cosine Similarity):**
- **Closest Historical Match:** Taiwan_Tension
- **Cosine Similarity Score:** 0.490
- **Similarity Signal:** Weak Historical Match
- **Top Similarity Matches:**
  - Taiwan_Tension: 0.490
  - Ukraine_2022: 0.448
  - Israel_2023: 0.363
- **Top Drivers:**
  - USDCNH: z_used=+0.72 (z1d=+0.08, z5d=+1.68, raw_w=0.18, norm_w=0.14) → contrib=+0.10
  - KR10Y_SPREAD: z_used=-1.00 (mode=level, raw_w=0.08, norm_w=0.06) → contrib=-0.06
  - DE10Y_SPREAD: z_used=+1.00 (mode=level, raw_w=0.06, norm_w=0.05) → contrib=+0.05
  - VIX: z_used=+0.30 (z1d=-0.18, z5d=+1.03, raw_w=0.18, norm_w=0.14) → contrib=+0.04
- **Missing/Skipped:** None
- **Sovereign Spread factors included:** KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD

**Trade Information:**
- 지정학 스트레스 프록시가 평온. 기존 매크로 레짐/리스크 예산 신호를 우선.
- 역사적 위기 패턴 유사도는 낮습니다. 현재는 **Taiwan_Tension** 유형과 가장 가깝지만, 전면적 지정학 쇼크보다는 제한적·국지적 리스크 모니터링 구간으로 해석됩니다.
- **Country ETF Crash?** Yes (EIS, SPY, VXX)
- **Extreme Country Risk:** EIS, SPY, VXX

### 💸 8) Incentive Filter
- **질문:** 누가 이득을 보고 있는가?
- **핵심 신호:** US10Y(→) / DXY(→) / WTI(→)
- **이득을 보는 주체:**
  - None
- **손해를 보는 주체:**
  - None

### 🔍 9) Cause Filter
- **질문:** 무엇이 이 움직임을 만들었는가?
- **핵심 신호:** US10Y(→) / DXY(→) / WTI(→) / VIX(→)
- **판정:** **원인 신호 뚜렷하지 않음**

### 🔄 10) Direction Filter
- **질문:** 오늘 움직임은 ‘노이즈’인가 ‘의미 있는 변화’인가?
- **강도:** US10Y(Noise) / DXY(Noise) / WTI(Noise) / VIX(Noise)
- **판정:** **MOSTLY NOISE (대부분 노이즈)**

### ⏳ 11) Timing Filter
- **질문:** 이 신호는 단기/중기/장기 중 어디에 더 중요하게 작용하는가?
- **가이드:**
  - 금리/달러의 ‘레벨’ 변화는 중기(수 주~수개월) 영향이 더 큼
  - VIX 급등/급락은 단기(수 일~수 주) 심리 변화에 민감
- **Today snapshot:** US10Y(4.440), DXY(100.150), VIX(31.05)

### 🏗️ 12) Structural Filter
- **질문:** 이 변화가 글로벌 구조(달러 패권/성장/에너지)에 어떤 힌트를 주는가?
- **핵심 신호:** US10Y(→) / DXY(→) / VIX(→) / WTI(→)
- **판정:** **NEUTRAL**
- **근거:** 패권/구조 신호가 뚜렷하지 않음

### 🧠 13) Narrative Engine (v2 + Risk Budget)
- **정의:** 구조·심리·크레딧·유동성·국면을 통합해 오늘의 리스크 액션을 결정
- **추가 이유:** 지표는 많지만 전략가는 결국 ‘리스크를 늘릴지/줄일지/유지할지’를 판단해야 하기 때문

- **Structure Bias:** Policy Bias: TIGHTENING (긴축) (MODERATE, score=+2.0) | REAL_RATEΔ +0.060 / FCIΔ +0.039 / DXYΔ +0.000 / US10YΔ +0.000
- **Sentiment (Fear&Greed):** 23.525678574596 (FEAR)
- **Credit Calm (HY OAS<4):** True
- **Liquidity (NET_LIQ):** dir=DOWN / level=MID
- **Phase:** WAITING / RANGE (대기·박스권)

- **🎯 Final Risk Action:** **REDUCE**
- **Risk Budget (0~100):** **25**
- **Narrative:** 구조=TIGHTENING / 심리=FEAR / 유동성=감소/중간 / 크레딧=안정 → Phase=WAITING / RANGE (대기·박스권)

### ⚠ 14) Divergence Monitor
- **정의:** 구조(정책)와 가격(시장 국면)의 충돌 여부 감지
- **추가 이유:** 구조-가격 충돌은 국면 전환의 초기 신호가 될 수 있음

- **Structure:** TIGHTENING
- **Price Regime:** WAITING
- **Status:** **TRANSITION ZONE**
- **해석:** 시장 방향 탐색 구간

### 🎯 15) Volatility-Controlled Exposure (v2)
- **정의:** Risk Budget을 실제 익스포저로 변환 (Pro Version)
- **추가 이유:** 변동성·스트레스·국면을 모두 반영한 실전형 리스크 제어

- **Risk Budget:** 25
- **Phase Cap:** 60
- **VIX Level:** 31.05 (EXTREME)
- **VIX Change (%):** +0.00%
- **Final Multiplier:** 0.60x

- **📊 Recommended Exposure:** **22%**

### 🎨 16) Style Tilt (v1.1)
- **정의:** Macro 구조 기반 스타일 기울기 판단
- **추가 이유:** 같은 Risk-On이라도 어떤 유형의 자산이 유리한지 구분

- **Growth vs Value:** **VALUE TILT**
- **Duration Tilt:** **NEUTRAL**
- **Cyclical vs Defensive:** **DEFENSIVE FAVORED**

### 🧩 17) Factor Layer (v1)
- **정의:** 시장을 움직이는 핵심 위험 요인 판별
- **추가 이유:** 자금이 무엇에 민감하게 반응하는지 파악

- **Duration Factor:** NEUTRAL
- **Inflation Factor:** NEUTRAL
- **USD Factor:** NEUTRAL
- **Credit Factor:** CREDIT SUPPORTIVE

### 🏭 18) Sector Allocation Engine (v2)

**Context:** phase=WAITING / RANGE (대기·박스권) / T10Y2Y=0.56 / VIX=27.44

**Overweight:** Consumer Staples, Health Care, Utilities, Financials
**Underweight:** Technology, Real Estate

**Rationale (top drivers):**
- UW Technology: -3: 유동성 긴축 → 고밸류에이션 부담
- UW Technology: -3: VIX 27.4 → 위험자산 회피
- OW Financials: +2: 수익률 곡선 가파름(0.56) → 예대마진 개선
- OW Consumer Staples: +3: 유동성 긴축 → 방어적 필수소비 선호
- OW Consumer Staples: +2: VIX 27.4 → 경기 비탄력적 섹터 선호
- OW Health Care: +3: 유동성 긴축 → 안정적 현금흐름 선호


---

### 🧬 19) Execution / Style Translation Layer
- **Implementation Focus:** Environment-Aware Stock Types

**Preferred Company Traits:**
- High Free Cash Flow generators
- Net cash or low leverage balance sheets
- Stable margins / pricing power
- Low to mid beta exposure
- High RAROC Focus
- Cash flow visibility and earnings stability

**Risk Control / Avoid:**
- Negative FCF / cash-burn models
- High leverage / refinancing-dependent names
- Long-duration, high-multiple growth
- Rate-sensitive long-duration equities

## 🧭 So What? (Decision Layer)
- **Risk Stance:** **REDUCE** *(target exposure: 25%)*
- **Context:** phase=WAITING / RANGE (대기·박스권) / liquidity=DOWN-MID / credit_calm=True / geo=NORMAL

## 🗺️ Scenario Framework (Base / Bull / Bear)

### 🔹 Base Case
- 조건: 유동성 혼조 + 크레딧 안정 유지 / 변동성 급등 없이 박스권 장세 지속
- 전략: 노출 25% 유지, 퀄리티 중심 선별적 접근

### 🔼 Bull Case
- 조건: NET_LIQ 회복 (dir=UP & level=MID 이상) / 크레딧 스프레드 추가 축소
- 전략: 노출 단계적 확대, 성장/리스크 자산 베타 확장

### 🔻 Bear Case
- 조건: HY OAS > 4% 상회 또는 급등 / VIX 22 이상 또는 급등 전환
- 전략: 노출 35% 이하 축소, 방어/현금 비중 확대

## 🔗 Transmission Map (Macro → Industry → Company)
- **1-Line Conclusion:** 장기듀레이션 성장주 불리 + 고베타/레버리지 제한 → **High FCF / Low leverage / pricing power** 선호

- **Policy → Valuation:** 할인율↑(멀티플 압박) → 장기듀레이션 성장주 불리
- **Liquidity → Risk Budget:** 유동성 흡수(리스크 허용↓) → 고베타/레버리지 제한
- **Credit → Balance Sheet:** 크레딧 안정 → 시스템 리스크 제한

- **Sector/Company Shortcut:** Defensive(Staples/Utilities/Healthcare) + Mega-cap quality

---


---

## 🌐 Country ETF Risk Monitor

### BND
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 0.061336324160422735
- **Z-Score (5d):** -0.07580858704598166

### EEM
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.32036175262903366
- **Z-Score (5d):** -0.36102924293464467

### EIS
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -2.8613351789170385
- **Z-Score (5d):** -1.989935862240425

### EMB
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -1.1832064530902695
- **Z-Score (5d):** -0.062083725331717826

### EWJ
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -1.0412074293788547
- **Z-Score (5d):** 0.005950000660952742

### FXI
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** -0.04725567663956673
- **Z-Score (5d):** -0.0636955447223752

### GLD
- **Crash?** False
- **Risk Level:** NORMAL
- **Z-Score (1d):** 1.3105741554405599
- **Z-Score (5d):** 0.0292063613339626

### SPY
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** -1.934197405728403
- **Z-Score (5d):** -1.5312685669147317

### VXX
- **Crash?** True
- **Risk Level:** EXTREME
- **Z-Score (1d):** 1.5105119198840158
- **Z-Score (5d):** 1.2600938041636112
