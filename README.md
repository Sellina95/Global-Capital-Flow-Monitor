# 🌍 Global Capital Flow Monitor

> **A strategist‑oriented macro & capital‑flow monitoring system**
> combining **quant signals** with **human strategic filters**.

---

## 🔍 What is this project?

**Global Capital Flow Monitor** is a personal research & automation project designed to:

* Track **global capital flow** through core macro indicators
* Detect **market regime shifts** (risk‑on / risk‑off / transition)
* Translate raw data into **strategist‑level interpretation**, not just numbers

This is **not a trading bot** and **not a pure quant model**.

It is a **strategy thinking framework** that sits between:

* Quantitative signals (rates, FX, volatility)
* Macro / policy context
* Human judgment & scenario awareness

---

## 🧠 Why this matters (for recruiters & reviewers)

Most dashboards answer:

> *“What moved today?”*

This project answers:

> **“Why does this move matter *now*, under this regime?”**

Key differentiators:

* ✅ **Regime‑aware interpretation** (same signal ≠ same meaning)
* ✅ **Liquidity & policy filters** layered on top of raw data
* ✅ Daily automation via **GitHub Actions**
* ✅ Clear separation between *signal*, *filter*, and *judgment*

This reflects how **global strategists**, **macro researchers**, and **investment committees** actually think.

---

## 📊 Core Indicators Monitored

* **US 10Y Treasury Yield (US10Y)** – global discount rate
* **DXY (US Dollar Index)** – global funding & risk barometer
* **WTI Crude Oil** – inflation & real‑economy pressure
* **VIX** – market stress & risk perception
* **USD/KRW** – EM capital flow & dollar liquidity proxy

---

## 🧭 Strategist Filter Framework (Core Design)

Daily reports are built using layered filters:

### 🧩 1) Market Regime Filter

**Purpose:** Identify *what kind of market we are in*

* Risk‑On / Risk‑Off
* Transition / Mixed
* Event‑watching / Range

> Same data behaves differently depending on regime.

---

### 💧 2) Liquidity Filter

**Question:** *Is fresh money entering the system or drying up?*

Uses:

* US10Y direction
* DXY pressure
* VIX behavior

Outputs:

* Liquidity expansion
* Liquidity tightening
* Mixed / fragile liquidity

---

### 🏛️ 3) Policy Filter

**Question:** *Is policy acting as a tailwind or a headwind?*

Rationale:

* Markets cannot sustainably move **against policy gravity**

Detects:

* Easing bias
* Tightening bias
* Policy uncertainty / mixed signals

---

### 📌 4) Directional Signals (Legacy Filters)

**Purpose:** Provide *asset‑level directional context*

Includes:

* Direction (up / down / flat)
* **Signal strength** classification:

  * Noise
  * Mild
  * Clear
  * Strong

> Added to prevent over‑interpreting small daily noise.

---

## 📁 Project Structure

```text
Global-Capital-Flow-Monitor/
│
├── data/
│   └── macro_data.csv        # Auto‑updated macro time series
│
├── scripts/
│   ├── fetch_macro_data.py   # Fetch & append daily macro data
│   ├── generate_report.py    # Build daily strategist report
│   ├── summarize_macro.py    # Optional summary helpers
│   ├── visualize_macro.py    # Charts & visuals
│   └── risk_alerts.py        # Risk‑signal experiments
│
├── filters/
│   └── strategist_filters.py # Core strategist logic (regime, liquidity, policy)
│
├── reports/
│   └── daily_report_YYYY-MM-DD.md
│
├── .github/workflows/
│   └── daily-macro.yml       # GitHub Actions automation
│
└── README.md
```

---

## ⚙️ Automation

* Runs **daily via GitHub Actions**
* Automatically:

  1. Updates macro data
  2. Generates strategist report
  3. Commits results back to repository

This ensures:

* No manual execution
* Time‑consistent analysis
* Reproducible daily history

---

## 🎯 Who this project is for

This project reflects skills relevant to:

* Global Strategy / Macro Research
* Asset Management (Multi‑asset, Global)
* Global Markets / Sales / Structuring support
* Strategy & Research roles bridging data and narrative

---

## 🧩 Philosophy

> **Numbers don’t move markets. Interpretation does.**

This project is an experiment in:

* Turning data into *decision‑ready insight*
* Making strategy thinking explicit and structured
* Building a personal, evolving strategist toolkit

---

📌 *This repository is actively evolving.*
Future extensions may include:

* Cross‑asset correlation filters
* Event‑risk scoring
* Scenario‑based summaries

---

**Author:** Seyeon Kim
**Focus:** Global strategy · macro · capital flows



