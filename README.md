# 🌍 Global Capital Flow Monitor
### Strategy & Capital Flow Research Initiative

Global Capital Flow Monitor is a macro-to-execution framework that converts:
Structure → Flow → Risk Budget → Tactical Allocation → ETF Execution.

It is designed not to predict markets,
but to systematically interpret capital flow and translate it into disciplined positioning.

---

# 🧠 Overview

**Global Capital Flow Monitor** is a rule-based macro strategy engine designed to interpret **cross-asset capital flow dynamics** and translate them into a structured daily strategist framework.

The system integrates multiple layers of global market structure:

- Interest Rate Structure  
- USD Liquidity Conditions  
- Volatility Regimes  
- Credit Market Stress  
- Policy Bias & Expectations  
- Factor Sensitivity  
- Style Rotation  
- Sector Allocation Logic  
- Execution Translation Layer  

The objective is not prediction.

The objective is:
- disciplined interpretation of market structure
- systematic risk budgeting
- tactical asset allocation
- execution translation

---

# 💡 Strategic Genesis

This project is not merely a coding exercise — it represents a synthesis of professional experience and macro-structural thinking.

### The "Plumbing" Perspective
My experience at **Bank of America (Global Markets Operations)** provided insight into the hidden mechanics of the financial system.

Markets do not move purely because of narratives — they move because **liquidity flows through specific pipes**:

- Treasury General Account (TGA)
- Reverse Repo Facility (RRP)
- Collateral chains
- Institutional funding channels

This project translates those **invisible liquidity mechanics into systematic signals.**

### Cross-Border Intelligence
Experience with **Industrial and Commercial Bank of China (ICBC)** exposed the structural interaction between **Western capital markets and Eastern financial systems**.

Combined with:

- English / Chinese financial literacy
- Computer Science background

the system is designed to interpret **multi-polar capital flow dynamics**.

### Algorithmic Discipline
Markets are complex, non-linear systems.

This framework removes emotional interpretation and replaces it with **rule-based macro structure analysis**.

---

# 🏗 Core Framework Philosophy

Markets move in hierarchical layers:

1. Structure (Policy & Liquidity)
2. Price Confirmation (Rates / USD / Volatility)
3. Credit Conditions
4. Drift Detection
5. Institutional Flow Detection
6. Risk Budget Construction
7. Divergence / Fragility Monitoring
8. Volatility-Controlled Exposure
9. Tactical Sector Allocation
10. ETF Execution Mapping
11. Execution / Style Translation

This engine replicates that hierarchy using rule-based macro logic.

It separates:

- Structural bias
- Price reaction
- Liquidity plumbing
- Risk appetite
- Capital positioning
- Execution interpretation

---

# ⚙️ System Architecture
Drift Monitor
↓
Institutional Flow Engine
↓
Narrative Engine
↓
Divergence Monitor
↓
Volatility-Controlled Exposure
↓
Sector Allocation Engine
↓
Tactical Allocation Builder
↓
ETF Execution Layer
↓
Execution / Style Translation Layer

Each filter operates independently but feeds into a structured **daily strategist report.**

---

# 📂 Project Structure
.github/                CI automation workflows
data/                   Raw & processed macro datasets
filters/                Core strategist filter engine
insights/               Regime change logs & risk alerts
reports/                Daily generated macro reports
scripts/                Data pipeline & report generation

fetch_macro_data.py     Macro data fetch module
requirements.txt        Dependencies
README.md
Daily strategist outputs are automatically generated and stored in:
/reports

These outputs represent **interpreted capital flow narratives**, not raw data dumps.

---

# 🧠 Implemented Strategy Layers (19 Filters)

## Core Macro Structure
1. Market Regime Detection  
2. Liquidity Structure (Enhanced)  
3. Policy Bias Analysis  

4. Fed Plumbing (TGA / RRP / Net Liquidity)  
4.2 High Yield Spread (HY OAS)  
4.5 Credit Stress (HYG vs LQD)

---

## Cross-Asset & Risk Mapping

6. Cross-Asset Interaction  
6.5 Correlation Break Monitor (Macro-Level)  
6.6 Sector Correlation Break Monitor  

7. Risk Exposure Filter  
7.2 Geopolitical Early Warning System (Geo Stress Composite)  
7.5 Institutional Flow Architecture (Core Flow Engine)  

8. Incentive Mapping  
9. Cause Filter  
10. Noise vs Signal Filter  
11. Timing Framework  
12. Structural Interpretation  
---

## Narrative & Allocation Engine

13. Narrative Engine (Risk Budget Core)
14. Divergence / Fragility Monitor
15. Volatility-Controlled Exposure & Dead Man's Switch

16. Style Tilt
17. Factor Layer
18. Sector Allocation Engine

18.5 Tactical Asset Allocation Builder
19 ETF Execution Layer
19.5 Execution / Style Translation Layer

---

# 🏦 Institutional Flow Architecture (Filter 7.5 / Core Flow Engine)

The Institutional Flow Engine is designed to detect whether capital is beginning to reposition before narrative consensus forms.

Unlike price-only systems, this layer evaluates whether institutional behavior is leaving structural footprints through:

### Core Inputs
- Drift Score (multi-day directional persistence)
- Cross-Asset Validation
- Gamma Context (dealer positioning environment)
- SEW Stability (shock filtering)
- Positioning Stress (POS_Z)
- Day-over-Day Flow Continuity

### Flow Classification
- NO CLEAR FLOW
- EARLY TRACE
- FLOW BUILDING
- CONFIRMED FLOW

### Purpose
This engine answers:

“Is this merely price movement —
or is capital actually beginning to move?”

### Strategic Use
Flow signals do not replace macro regime.

They modify conviction.

Examples:
- Risk-Off + No Flow → Defensive
- Risk-Off + Flow Improving → Defensive but selective
- Transition + Flow Building → Early positioning
- Risk-On + Confirmed Flow → Expansion bias

### Philosophy
Price can bounce.

Flow sustains.

This layer exists to distinguish noise from institutional intent.

---

# 🛰️ Geopolitical Early Warning System (Filter 7.2)

The **Geopolitical Early Warning Monitor** detects market stress associated with geopolitical disruptions.

Unlike simple news-driven models, the system observes **cross-asset market reactions** across multiple domains.

### Market Reaction Layer

- VIX (volatility shock)
- WTI (energy supply risk)
- GOLD (safe haven demand)
- USDCNH (China capital flow proxy)

### Emerging Market Stress Layer

- EEM
- EMB
- USDMXN
- USDJPY

### Supply Chain / Shipping Signals

- SEA (shipping companies)
- BDRY (dry bulk freight index)

### Defense Sector Reaction

- ITA (US Aerospace & Defense ETF)
- XAR (Defense equal-weight ETF)

### Sovereign Stress Proxy

Bond spread differentials used as **CDS proxies**:

- KR10Y Spread
- JP10Y Spread
- CN10Y Spread
- IL10Y Spread
- TR10Y Spread

These indicators collectively produce a **Geo Stress Score (z-score composite)**.

### System Output

Geo Stress Score
↓
Stress Level Classification
(CALM / WATCH / ELEVATED / HIGH)
↓
Top Contributing Factors
↓
Strategic Interpretation

### Example Event Backtest

Tested on major geopolitical shocks:

- 2022 Russia invasion of Ukraine
- 2023 Gaza war outbreak
- 2024 Red Sea shipping disruptions

The system identifies:

- dominant cross-asset reactions
- stress propagation channels
- sovereign spread responses

---

# 📊 Sample Daily Output Snapshot

### Executive Summary (3 Lines)

Risk Budget: 45
Final Exposure: 40
Core Position: XLK (DEFENSIVE_PRIMARY)
Cash Buffer: 60
Flow State: NO CLEAR FLOW

Sector Tilt:
Core Position:
Technology (XLK) as defensive primary
Selective Financials / Industrials
Elevated Cash Buffer

Underweight:
Energy / Real Estate / Utilities

Execution Focus:
High Free Cash Flow
Low Leverage
Defensive Bias

Scenario Framework:
Base: Liquidity mixed
Bull: Liquidity recovery
Bear: Credit stress breakout

This output is **not a trading signal**.

It is a **structured macro interpretation and risk allocation framework.**

---

# 🎯 Strategic Differentiation
The Global Capital Flow Monitor is not a conventional collection of technical indicators; it is a disciplined capital flow hierarchy model designed to navigate market complexity through structural rigor and real-time execution.

1. Execution-Layer Intelligence
Real-time Market "Scream" Detection: Most systems react to official data releases. This engine captures the exact moment when the market starts to "scream"—detecting information leakage and price reflexivity via real-time rolling z-scores (2-Sigma) across cross-asset correlations before macro updates.

Mechanical Fail-Safe (Dead Man’s Switch): To ensure algorithmic sustainability, the system implements a Fail-Safe Shutdown Protocol (Filter 15.0). If liquidity velocity (Slope) or positioning extremes (POS_Z) exceed safety thresholds, the system automatically triggers a Dead Man’s Switch, mandating a 0% exposure to preserve capital during tail-risk events.

Event-Driven Workflow: Integrated with the Resend API, the system bridges the gap between analysis and action by dispatching instant strategist alerts the moment a regime transition or liquidity spike is detected.

2. Structural & Liquidity Plumbing
Policy vs. Price Reaction: Explicitly separates structural policy shifts from noise-driven price reactions, ensuring the strategy remains anchored in "what the Fed does" rather than "what the market hopes."

Fed Plumbing Integration: Direct modeling of the financial system’s "pipes"—including the Treasury General Account (TGA), Reverse Repo Facility (RRP), and Net Liquidity—to track the actual movement of institutional funds.

3. Risk & Allocation Hierarchy
Macro-to-Execution Translation: A rigorous top-down framework that flows from Macro Regimes → Style Factors → Sector Allocation → Company Traits, ensuring that every position is a direct translation of a macro-structural view.

Quantified Risk Budgeting: Replaces subjective "conviction" with a volatility-adjusted exposure framework, calculating risk budgets based on real-time stress levels and regime-specific caps.

Scenario-Driven Framing: Moves beyond binary predictions by utilizing a dynamic scenario engine, allowing the strategist to prepare for Base, Bull, and Bear cases simultaneously within a structured transmission map.

4. Adaptive Market Monitoring
Correlation Break Detection: Monitors the breakdown of historical relationships between assets (e.g., Rates vs. Tech, USD vs. Emerging Markets) to identify regime shifts before they become consensus.

Geopolitical Stress Mapping: Translates vague geopolitical fears into quantified Geo Stress Scores through pattern matching and sovereign spread differentials.

5. Institutional Flow Architecture:
Captures early-stage institutional repositioning before narrative consensus through drift persistence, cross-asset validation, gamma structure, and flow continuity.

This system does not stop at interpretation —
it translates macro structure into:
Risk Budget → Tactical Allocation → ETF Execution → Style Translation.

---

# 🧪 Intended Use Cases

- Macro research portfolio
- Cross-asset regime monitoring
- Risk management experimentation
- Asset allocation framework development
- Strategy / research interview demonstration

---

# 🔭 Ongoing Development

Planned upgrades include:

- Event-driven Cause Filter (Economic Calendar Integration)
- Structural Trend Overlay (PMI / 200DMA)
- Cross-Asset Divergence Intensity Index
- Allocation backtesting module
- Paper Portfolio Performance Tracking
- Flow Regime Persistence Scoring
- Sector-to-ETF Rotation Backtesting

---

# 📜 Strategic Philosophy

> "Capital flows reflect incentives.  
> Incentives reflect structure.  
> Structure reflects the architecture of the global system."

In a world overwhelmed by information, the greatest asset is **not data — but interpretation.**

Understanding capital flow is ultimately a way of understanding how humanity allocates:

- risk
- trust
- belief

This monitor represents a long-term commitment to decoding that language.

It is designed to preserve **sovereignty over decision-making in an era of engineered narratives.**

---

**Strategy & Capital Flow Research Initiative**

Developed by a strategist who believes in:

- the power of logic  
- the depth of macro history  
- the resilience of the human spirit
