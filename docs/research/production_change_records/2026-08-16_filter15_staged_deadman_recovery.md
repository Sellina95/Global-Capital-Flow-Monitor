# Research-to-Production Change Record #002

**Date:** 2026-08-16  
**System:** Global Capital Flow Monitor  
**Component:** Filter15 — Volatility-Controlled Exposure  
**Change:** Staged Deadman Recovery / Re-Risking  
**Research Branch:** `institutional-backtest-v1`  
**Production Branch:** `main`  
**Decision:** APPROVED FOR PRODUCTION

---

## 1. Problem

Filter15 contains a Hard Deadman mechanism that forces exposure to 0% during severe market stress.

The Hard Deadman trigger itself was not identified as the primary problem.

The research issue was the recovery path after a Deadman event.

The previous structure could restore the normally calculated Filter15 exposure too quickly after the system exited the defensive state. This created false-recovery risk: market conditions could temporarily improve, trigger re-entry, and then deteriorate again before the recovery became durable.

The objective was therefore:

> Preserve the existing Hard Deadman protection while improving the path by which risk is restored after a crisis state.

The research objective was not to maximize backtest returns or remove defensive controls.

---

## 2. Research Hypothesis

Instead of immediately restoring full normally calculated Filter15 exposure after a Deadman episode, restore exposure progressively when observable recovery conditions persist.

Candidate recovery signal:

`HY_FALLING_VIX_LT_30`

Defined as:

- current HY OAS below the prior observable HY OAS level, and
- current VIX below 30.

No future observations are required by the rule.

---

## 3. Production Recovery Structure

The approved state-machine structure is:

`HARD DEADMAN`

↓

`0% EXPOSURE`

↓

`RECOVERY SIGNAL`

↓

`25% OF CURRENT FILTER15 BASELINE`

↓

`50% OF CURRENT FILTER15 BASELINE`

↓

`NORMAL FILTER15 EXPOSURE`

The percentages are applied to the current daily Filter15 exposure baseline rather than to a fixed historical release-day exposure.

This distinction was explicitly corrected during the canonical research rebuild.

---

## 4. Re-Brake Safety Constraint

Recovery is conditional.

If the recovery candidate breaks before staged recovery is completed:

> Exposure returns immediately to 0%.

The system therefore follows:

`DEADMAN -> RECOVERY -> STAGED RE-RISKING -> NORMAL`

but can transition:

`RECOVERY -> RE-BRAKE -> 0%`

when recovery evidence deteriorates.

This prevents staged re-risking from becoming an unconditional time-based ramp.

---

## 5. Controls Not Changed

The following existing Production behavior was intentionally preserved:

- Filter13 Risk Budget logic,
- Hard Deadman trigger,
- existing VIX controls,
- positioning controls,
- Gamma controls,
- CTA controls,
- existing credit brakes,
- normal Filter15 exposure calculation,
- existing Deadman thresholds.

No new market indicator was introduced.

The modification is limited to the post-Deadman recovery path and the state required to operate that path across daily Production runs.

---

## 6. Persistent State

Staged recovery requires the Production system to remember the previous execution state.

A dedicated Filter15 persistent state contract was therefore added through:

`insights/filter15_state.json`

The state includes the information required to maintain recovery continuity across runs, including:

- previous Deadman state,
- recovery-active state,
- recovery streak,
- recovery-completed state,
- previous HY OAS,
- latest Filter15 status,
- latest recommended exposure.

State loading occurs before Filter15 execution through the Production report chain.

Updated state is saved after Filter15 execution.

---

## 7. Recovery-Completion Guard

During implementation review, a state-machine risk was identified:

A recovery sequence that had already completed could incorrectly re-enter Stage 1 within the same Deadman episode.

A dedicated completion state was therefore added:

`FILTER15_RECOVERY_COMPLETED`

Its purpose is to distinguish:

- recovery currently in progress,
- recovery already completed,
- a genuinely new Deadman/recovery episode.

This prevents completed recovery from repeatedly restarting the 25% stage.

---

## 8. Research Sequence

The Filter15 release investigation included:

1. existing Production parity and attribution review,
2. Hard Deadman episode audit,
3. release-failure diagnosis,
4. recovery candidate analysis,
5. persistence counterfactual,
6. staged re-risking counterfactual,
7. parameter sensitivity,
8. canonical daily-baseline correction,
9. robustness analysis,
10. Production state-contract inspection,
11. minimal Production implementation candidate,
12. durable state wiring,
13. actual-source / state-machine implementation review.

The research process intentionally separated:

- crisis detection,
- recovery detection,
- exposure restoration,
- Production state persistence.

---

## 9. Parameter-Control Decision

Multiple neighboring staged paths were investigated during research.

The research gate approved the staged restoration structure rather than selecting a path solely because it generated the highest historical return.

The Production candidate uses:

`25% -> 50% -> 100%`

The decision was not treated as a return-maximization exercise.

No new threshold was selected through unconstrained parameter optimization.

---

## 10. Corrected Canonical Contract

An earlier staged-restoration research artifact used a fixed release exposure.

That contract was not sufficiently aligned with the intended Production behavior because Production recalculates Filter15 exposure daily.

The canonical contract was therefore rebuilt using the current daily Filter15 baseline.

Corrected contract:

`DAILY BASELINE x 25% / 50% / 100%`

Calendar rows without an executable Filter15 row were skipped rather than forward-filled.

Results:

| Check | Result |
|---|---:|
| Episodes | 25 |
| Completed Episodes | 12 |
| Calendar Rows Skipped | 37 |
| Exposure Formula Max Error | 0.000000000000 |
| Completion Violations | 0 |
| Contract | PASS |

The earlier fixed-release-exposure economics were superseded for the Production decision.

---

## 11. Corrected Robustness Results

Corrected daily-baseline robustness results:

| Metric | Result |
|---|---:|
| Episodes | 25 |
| Recovery Completed | 12 |
| Recovery Incomplete | 13 |
| Positive Episodes | 16 |
| Negative Episodes | 9 |
| Total Episode Return | +4.382% |
| Average Episode Return | +0.175% |
| Median Episode Return | +0.031% |
| Worst Episode Return | -1.331% |
| Worst MDD | -7.498% |

Excluding the 2008 / Episode 1 tail event:

| Metric | Result |
|---|---:|
| Episodes | 24 |
| Total Episode Return | +5.713% |
| Average Episode Return | +0.238% |
| Worst MDD | -1.411% |
| Direction Positive | True |

Leave-one-episode-out conclusion survival:

**100%**

Positive-era rate:

**80%**

Robustness status:

**PASS_WITH_TAIL_WARNING**

---

## 12. Tail-Risk Warning

The research result is not interpreted as evidence that staged recovery eliminates crisis risk.

Episode 1 / 2008 remained the dominant historical tail observation.

Worst corrected MDD:

**-7.498%**

This tail was retained in the decision record rather than removed through parameter optimization.

The Production decision therefore reflects:

> improved recovery structure with known residual tail risk,

not:

> elimination of recovery risk.

---

## 13. Research Decision

The final research conclusion was:

**STAGED RE-RISKING STRUCTURE APPROVED FOR IMPLEMENTATION**

with the following constraints:

- retain Hard Deadman,
- use the validated recovery candidate,
- restore exposure progressively,
- immediately re-brake when recovery breaks,
- maintain durable state across Production runs,
- do not introduce additional indicators,
- do not optimize the recovery path solely for historical return.

---

## 14. Research-to-Production Promotion

Branch governance was preserved.

### Research / Validation

`institutional-backtest-v1`

Research commit:

`d865292f research: add Filter15 staged deadman recovery state`

The research branch contains the supporting audits, counterfactuals, robustness work, canonical reconstruction, and implementation candidates.

### Production

`main`

Production commit:

`75f5762e prod: add staged Filter15 deadman recovery`

Only the minimal runtime files were promoted:

- `filters/strategist_filters.py`
- `scripts/generate_report.py`

The research branch was NOT merged wholesale into Production.

---

## 15. Production Behavior After Promotion

Production Filter15 now follows the conceptual sequence:

`Filter13 Risk Budget`

↓

`Normal Filter15 Risk Controls`

↓

`Hard Deadman`

↓

`0%`

↓

`HY OAS Falling + VIX < 30`

↓

`Recovery Stage 1 — 25%`

↓

`Recovery Stage 2 — 50%`

↓

`Recovery Complete`

↓

`Normal Filter15 Exposure`

If the recovery condition breaks before completion:

`RECOVERY -> RE-BRAKE -> 0%`

Recovery state is persisted between Production executions.

---

## 16. Audit-Control Lessons

This investigation produced several control lessons.

### Daily baseline matters

A staged multiplier must be evaluated against the exposure actually recalculated on each historical signal date.

A fixed release-day exposure can create a research contract that differs from Production semantics.

### State is part of strategy logic

For path-dependent risk controls, persistent state is not merely an implementation detail.

Recovery-active, recovery-streak, and recovery-completed semantics are part of the strategy contract and must be audited explicitly.

### Research artifacts are not automatically canonical

Previously generated result files were not treated as authoritative when their execution semantics differed from the intended Production contract.

### Structural approval is different from parameter optimization

The research evidence supported staged restoration as a risk-control structure.

It was not used as permission to search historical data for the highest-return recovery percentages.

---

## 17. Research-to-Production Control Framework

The Filter15 change followed the control sequence:

**Production Behavior Identification**

↓

**Deadman Episode Audit**

↓

**Failure Diagnosis**

↓

**Recovery Hypothesis**

↓

**Counterfactual Testing**

↓

**Persistence Testing**

↓

**Staged Restoration Testing**

↓

**Parameter Sensitivity**

↓

**Canonical Daily-Baseline Reconstruction**

↓

**Robustness / Tail Review**

↓

**Production State Contract**

↓

**Minimal Runtime Patch**

↓

**Research Branch Commit**

↓

**Minimal Production Promotion**

This maintains the separation between research evidence and Production runtime code.

---

## Final Decision Record

**Filter15 Staged Deadman Recovery: PRODUCTION APPROVED**

Production commit:

`75f5762e`

Research commit:

`d865292f`

The existing Hard Deadman remains in place.

The approved change modifies only the post-Deadman risk-restoration path by introducing stateful staged re-risking and immediate re-braking when recovery evidence fails.

**FILTER15 RELEASE-LOGIC PROJECT: CLOSED**
