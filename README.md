# 🌍 Global Capital Flow Monitor

### Macro Research · Capital Flow · Risk Budgeting · Portfolio Allocation

**Global Capital Flow Monitor** is an independent research framework designed to translate global macro structure and cross-asset capital flows into systematic portfolio decisions.

The core transmission chain is:

**Macro Structure  
→ Capital Flow  
→ Risk Budget  
→ Volatility-Controlled Exposure  
→ Tactical Allocation  
→ ETF Execution**

The objective is not to predict markets.

The objective is to build a disciplined framework for interpreting market structure, controlling risk, and translating macro information into portfolio decisions.

> **Research project — not investment advice.**

---

# 📌 Current Research Status

The project has evolved from a daily macro monitoring engine into a historical research and validation framework.

### Production / Strategy Architecture

Implemented components include:

- Macro regime classification
- Liquidity structure
- Credit stress monitoring
- Cross-asset confirmation
- Institutional flow detection
- Positioning and gamma context
- Risk budgeting
- Volatility-controlled exposure
- Sector allocation
- Tactical portfolio construction
- ETF execution translation

---

### Historical Validation Framework

The research environment now includes:

- Historical backtesting
- Point-in-time input validation
- Production ↔ Backtest parity testing
- Execution-chain audits
- Filter-level attribution
- Counterfactual testing
- Causal propagation analysis
- Portfolio allocation diagnostics

Research and production logic are intentionally separated.

Historical validation is designed to answer not only:

> **“Did the strategy perform?”**

but also:

> **“Did the historical simulation use the information and decision process that would actually have been available at the time?”**

---

# 🧪 Current Research — Macro Regime V4

Macro Regime V4 is currently under causal validation.

The research sequence is:

**Macro V4  
→ Portfolio Regime  
→ Filter 13 Risk Budget  
→ Filter 15 Exposure  
→ Filter 18 Allocation**

Current validation principles:

- Portfolio mapping was frozen before performance evaluation
- Mapping selection did not use returns, PnL, CAGR, or Sharpe
- No performance-based parameter tuning is used during causal validation
- Production filters remain unchanged during counterfactual testing
- Historical propagation is tested through the existing portfolio engine

The objective of this stage is to determine whether changes in macro classification propagate through the portfolio architecture for structurally explainable reasons.

**Causal attribution remains in progress.**

Performance evaluation is intentionally deferred until the causal and execution contracts are closed.

---

# 🏗 System Architecture

The framework follows a hierarchical market interpretation process.

```text
Macro Structure
        ↓
Liquidity & Credit Conditions
        ↓
Cross-Asset Confirmation
        ↓
Institutional Flow
        ↓
Macro / Market Regime
        ↓
Risk Budget
        ↓
Volatility-Controlled Exposure
        ↓
Sector & Factor Interpretation
        ↓
Tactical Allocation
        ↓
ETF Execution
```

This hierarchy separates:

- structural macro information
- market price reaction
- liquidity conditions
- credit conditions
- positioning
- capital flow
- portfolio risk
- execution

The purpose is to prevent a single indicator or narrative from directly determining portfolio exposure.

---

# 🔬 Research & Validation Philosophy

A major focus of the project is **decision-process integrity**.

Backtest results are not treated as valid simply because a historical equity curve looks attractive.

Before performance evaluation, the research process checks:

### 1. Input Contract

What information does each strategy component actually consume?

Examples include:

- rates
- USD
- volatility
- oil
- credit spreads
- liquidity
- positioning
- institutional flow
- market regime

---

### 2. Point-in-Time Integrity

Historical simulations should use information that would have been available at the relevant decision date.

The research process therefore considers:

- historical availability
- execution timing
- signal date vs. execution date
- lag structure
- state carried from previous observations

This is designed to reduce look-ahead bias and future-data leakage.

---

### 3. Production ↔ Backtest Parity

Where possible, historical testing reuses the same decision logic used by the production research engine.

Parity audits test whether:

```text
Historical Inputs
        ↓
Production Logic
        ↓
Backtest Replay
```

produce equivalent intermediate decisions.

This prevents a backtest from silently becoming a different strategy from the live research system.

---

### 4. Causal Attribution

When a model component changes, the research process traces where the change propagates.

For example:

```text
Macro Classification Change
        ↓
Portfolio Regime
        ↓
Risk Budget
        ↓
Exposure
        ↓
Sector Allocation
        ↓
Executed Equity Allocation
```

The goal is to distinguish genuine causal transmission from unexplained downstream differences.

---

### 5. Performance Comes Last

Returns, PnL, CAGR, Sharpe, and other performance statistics are intentionally separated from model-selection stages when necessary.

The principle is:

> **Understand why the system behaves differently before asking whether the difference made more money.**

This reduces the risk of selecting rules simply because they improve historical performance.

---

# 🧠 Core Strategy Layers

## Macro Structure

The system monitors structural and market-based macro information including:

- Interest-rate structure
- USD conditions
- Volatility
- Credit spreads
- Liquidity
- Inflation-related signals
- Cross-asset price behavior

These inputs contribute to the system's macro and market regime interpretation.

---

## Liquidity Plumbing

The framework incorporates financial-system liquidity indicators including:

- Treasury General Account (TGA)
- Reverse Repo Facility (RRP)
- Federal Reserve balance sheet
- Net Liquidity

The purpose is to evaluate changes in the liquidity environment rather than relying solely on asset-price momentum.

---

## Credit

Credit conditions provide an important confirmation layer.

Inputs include:

- High Yield OAS
- HYG
- LQD
- credit-spread behavior

Credit is used as a risk-transmission signal rather than as a standalone trading rule.

---

# 🏦 Institutional Flow Architecture

The Institutional Flow Engine attempts to distinguish short-term price movement from more persistent capital repositioning.

Inputs include:

- multi-day drift
- cross-asset confirmation
- dealer gamma context
- positioning stress
- flow continuity
- participation behavior

Conceptually:

```text
Price Movement
        ↓
Cross-Asset Confirmation
        ↓
Persistence
        ↓
Positioning / Gamma Context
        ↓
Flow Classification
```

Possible flow states include:

- NO CLEAR FLOW
- EARLY TRACE
- FLOW BUILDING
- CONFIRMED FLOW

Flow signals modify portfolio conviction rather than independently determining the macro regime.

---

# 🧭 Risk Budget — Filter 13

Filter 13 converts the broader market interpretation into a portfolio **Risk Budget**.

The purpose is to answer:

> **How much risk should the system be willing to take under the current environment?**

Inputs may include:

- macro regime
- liquidity
- credit
- structural conditions
- institutional flow
- positioning
- event risk

The resulting risk budget becomes an upstream constraint for portfolio exposure.

---

# ⚠️ Volatility-Controlled Exposure — Filter 15

Filter 15 converts the Risk Budget into an executable exposure recommendation.

It evaluates risk conditions including:

- volatility
- credit stress
- positioning
- dealer gamma
- institutional flow
- market participation

The purpose is not to generate alpha independently.

It acts as a **risk-control layer between strategic conviction and portfolio allocation.**

---

# 📊 Sector Allocation — Filter 18

Filter 18 translates the allowed portfolio exposure into sector-level allocation.

The process incorporates:

- sector scores
- relative strength
- flow information
- macro profile
- market quality
- sector classification
- portfolio persistence rules

The resulting allocation is reconciled against the exposure permitted by the upstream risk framework before ETF execution.

---

# 🔄 Stateful Portfolio Logic

Not every portfolio decision is determined solely by today's signal.

The framework also contains stateful mechanisms designed to reduce unnecessary portfolio churn.

These include persistence and rebalance logic that can preserve previously accepted portfolio states until sufficient evidence exists for a transition.

Because stateful logic can create downstream path dependence, historical validation explicitly audits these state transitions.

---

# 🛰️ Geopolitical Early Warning Monitor

The geopolitical monitoring layer evaluates cross-asset reactions associated with geopolitical stress.

Observed markets include:

### Market Reaction

- VIX
- WTI
- Gold
- FX stress indicators

### Emerging Markets

- EEM
- EMB
- selected FX pairs

### Supply Chain / Shipping

- shipping-related market indicators

### Defense

- aerospace and defense ETFs

The objective is not to predict geopolitical events.

It is to measure how geopolitical stress is being transmitted through financial markets.

---

# 📊 Daily Strategist Output

The system produces a structured daily market interpretation containing elements such as:

```text
Macro Regime
Liquidity Conditions
Institutional Flow
Credit Conditions
Positioning Risk
Risk Budget
Final Exposure
Sector Allocation
Cash Allocation
Execution Mapping
```

The daily output represents a **structured research interpretation**, not a trading signal.

---

# 📂 Repository Structure

```text
.github/        CI / automation workflows

data/           Historical and processed market data

filters/        Core strategist and portfolio logic

insights/       Regime and risk diagnostics

portfolio/      Portfolio state and execution utilities

reports/        Generated strategist reports

scripts/
    backtest/   Historical replay, parity and audit framework
```

Research artifacts and diagnostic outputs are generated separately from production strategy logic.

---

# 🧰 Research Stack

The project is primarily built with:

- Python
- pandas
- rule-based decision systems
- historical market datasets
- Git / GitHub
- automated research pipelines

The emphasis is on **transparent and auditable decision logic** rather than black-box prediction.

---

# 💡 Project Origin

The project combines three areas of experience and interest:

### Global Markets Operations

Experience in global markets operations provided exposure to the operational infrastructure behind institutional financial markets.

This created an interest in understanding not only where asset prices move, but how liquidity, settlement, funding, and institutional positioning interact beneath market narratives.

### Computer Science

A Computer Science background provides the technical foundation for converting market hypotheses into reproducible systems and validation pipelines.

### Cross-Border Markets

Experience across Korean, U.S., and Chinese financial environments contributed to an interest in global capital allocation and cross-border financial transmission.

The project is therefore designed around a central question:

> **Where is global capital moving, why is it moving, and how should portfolio risk respond?**

---

# 🎯 Research Objectives

Global Capital Flow Monitor is being developed as a long-term research project in:

- Global Macro
- Quantitative Research
- Cross-Asset Strategy
- Portfolio Risk
- Capital Flow Analysis
- Tactical Asset Allocation

The project is also an exercise in learning how institutional investment systems separate:

**hypothesis → implementation → validation → risk control → execution**

---

# 🔭 Ongoing Development

Current and future research areas include:

- Macro Regime V4 causal validation
- Macro-to-portfolio propagation attribution
- Point-in-time historical data auditing
- Portfolio state and persistence attribution
- Capital availability vs. capital rotation research
- AI infrastructure capital-flow monitoring
- Sector and factor transmission analysis
- Execution and portfolio diagnostics

Research features are promoted only after their behavior and implementation contracts are validated.

---

# 📜 Research Philosophy

> **Capital flows reflect incentives.  
> Incentives reflect structure.  
> Structure shapes risk.**

Markets contain more information than any single narrative can capture.

The purpose of this project is therefore not to build a machine that claims to know the future.

It is to build a system that asks better questions, applies consistent decision rules, and makes the path from information to portfolio risk auditable.

---

### Strategy & Capital Flow Research Initiative

**Independent research project. Not investment advice.**