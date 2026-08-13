# Research-to-Production Change Record #001

**Date:** 2026-08-13  
**System:** Global Capital Flow Monitor  
**Component:** Filter18 — Sector Allocation  
**Change:** 3-Day Rank Persistence  
**Research Branch:** `institutional-backtest-v1`  
**Production Branch:** `main`  
**Decision:** APPROVED FOR PRODUCTION

---

## 1. Problem

Filter18 reacts to changes in daily sector rankings.

Audit work identified that short-lived changes in sector rank could trigger unnecessary portfolio rotation, increasing turnover and transaction costs even when the underlying change did not persist.

The objective was therefore not to increase trading activity or optimize gross returns, but to determine whether temporary ranking noise could be filtered without weakening the system's defensive behavior.

---

## 2. Research Hypothesis

Require a changed sector ranking to persist for three trading days before accepting the new ranking.

Expected effect:

- reduce unnecessary sector rotation,
- reduce turnover,
- reduce transaction-cost drag,
- preserve economically meaningful allocation changes.

This rule must never delay required deleveraging.

---

## 3. Safety Constraint

### Deleveraging Bypass

Rank persistence is a turnover-control mechanism, not a risk-control mechanism.

Therefore:

> If deleveraging is required, the persistence rule is bypassed and the defensive target is accepted immediately.

This constraint prevents the 3-day confirmation rule from delaying risk reduction.

---

## 4. State-Machine Design

Production Rank3D maintains persistent state including:

- accepted rank,
- accepted target weights,
- pending rank,
- pending confirmation count,
- last processed date,
- last output target weights,
- last action.

Same-day reruns do not increment the confirmation counter.

State updates are persisted separately through the portfolio persistence layer.

---

## 5. State-Machine Validation

The following behaviors were explicitly tested:

- `INITIAL_ACCEPT`
- Day-1 rank-change suppression
- same-day rerun idempotency
- Day-2 suppression
- Day-3 confirmation
- immediate deleveraging bypass

Result:

**FILTER18 RANK3D STATE MACHINE CONTRACT: PASS**

---

## 6. Research-to-Production Semantic Parity

Validation period:

**4,645 trading days**

Exact semantic replay results:

| Check | Result |
|---|---:|
| Executed-weight fail days | 0 |
| Max weight absolute error | 0.0000000000 |
| Accepted-rank fail days | 0 |
| Pending-rank fail days | 0 |
| Pending-count fail days | 0 |
| Action fail days | 0 |

**FINAL STATUS: PASS**

The patched Production state-machine behavior therefore matched the validated research Rank3D behavior date-by-date over the tested history.

---

## 7. Economic Validation

Comparison:

| Metric | Baseline 1D | Persist 3D |
|---|---:|---:|
| Annualized Turnover | 50.5381 | 22.7054 |
| Total Cost (%) | 46.5773 | 20.9260 |
| Gross CAGR (%) | 2.5808 | 2.0223 |
| Net CAGR (%) | 0.0214 | 0.8707 |
| Net MDD (%) | -12.9379 | -8.9189 |
| Net Volatility (%) | 4.4105 | 3.4744 |
| Net Sharpe | 0.0269 | 0.2669 |

Observed changes:

- Turnover reduction: **55.07%**
- Net CAGR change: **+0.8493%p**
- Net Sharpe change: **+0.2400**
- Net MDD change: **+4.0190%p**

Gross CAGR decreased, but the reduction in turnover and transaction-cost drag produced materially better net results.

The change was therefore evaluated on implementation economics rather than gross backtest performance alone.

---

## 8. Production Gates

| Gate | Status |
|---|---|
| Canonical Filter13 parity | PASS |
| Filter18 source parity | PASS |
| Filter18 semantic parity | PASS |
| Turnover reduction | PASS |
| Net CAGR improvement | PASS |
| Net Sharpe improvement | PASS |
| MDD not worse | PASS |

**FINAL PRODUCTION GATE: PASS**

---

## 9. Decision

### APPROVED

**Filter18 Rank Persistence 3D**

### NOT CHANGED

**Filter13 — CURRENT / NO CHANGE**

The investigated Macro–Phase interaction modification was not promoted to Production.

**Filter15 — CURRENT / NO CHANGE**

No Filter15 production modification was included in this release.

### REJECTED

**Macro Persistence — NOT USED**

Research candidates were not automatically promoted simply because they were tested.

Only the Filter18 change that passed the required validation gates was approved.

---

## 10. Production Promotion

Branch governance:

### Research / Validation

`institutional-backtest-v1`

Contains:

- backtests,
- audits,
- counterfactual research,
- parity tests,
- sensitivity analysis,
- validation artifacts.

### Production

`main`

Contains only validated runtime changes required by the live system.

The complete research branch was NOT merged into Production.

Only the validated Filter18 runtime implementation was promoted to `main`.

Production runtime files modified:

- `filters/strategist_filters.py`
- `portfolio/save_portfolio.py`

Production commit:

`587bf878 feat: add Filter18 3D rank persistence`

---

## 11. Audit-Control Lesson

During the broader Filter13 investigation, an earlier candidate comparison was found to rely on a non-canonical historical attribution lineage.

Rather than continuing to optimize against that result, the research process was stopped and the baseline was rebuilt from:

- current `master_panel.csv`,
- current pre-Filter13 Production execution chain,
- current Production `narrative_engine_filter`,
- same-frame runtime-variable capture.

The rebuilt canonical Filter13 baseline achieved zero same-frame parity failures.

This established an important control principle for future research:

> Candidate performance must never be evaluated before the Production source lineage and baseline parity are independently verified.

Historical result files are therefore not treated as authoritative simply because they already exist.

---

## 12. Research-to-Production Control Framework

This change establishes the following promotion sequence for future strategy modifications:

**Problem Identification**

↓

**Canonical Production Baseline**

↓

**Source / Data Lineage Verification**

↓

**Research Hypothesis**

↓

**Counterfactual Test**

↓

**Safety Constraint Validation**

↓

**Semantic / Execution Parity**

↓

**Economic Validation After Costs**

↓

**Production Gate**

↓

**Minimal Production Promotion**

↓

**Post-Patch Audit**

This process separates research performance from production reliability and creates an auditable decision trail for strategy changes.

---

## Final Decision Record

**Filter18 Rank Persistence 3D: PRODUCTION APPROVED**

The change was promoted because it reduced implementation friction while preserving the system's risk controls and passed exact historical semantic-parity validation.

This is the first formally documented Research-to-Production promotion in the Global Capital Flow Monitor project.
