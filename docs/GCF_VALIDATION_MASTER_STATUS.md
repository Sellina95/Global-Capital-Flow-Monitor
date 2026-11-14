# GCF Validation Master Status

Purpose:

This file is the single master record for GCF topology reconstruction,
validation findings, evidence locations, and later remediation decisions.

Do not change Production logic merely because a finding exists.

Workflow:

DISCOVER
→ RECORD
→ VERIFY
→ CLASSIFY
→ FIX / KEEP / DOCUMENT / DEFER

---

# MASTER STATUS

| Phase | Scope | Status |
|---|---|---|
| Phase 0 | Core Execution Contract Closure | CLOSED |
| Phase 1 | Temporal Integrity / Data Provenance | CLOSED |
| Phase 2 | Decision & Report Semantic Integrity | CLOSED |
| Phase 3 | F18 Allocation Lineage | CLOSED |
| Phase 4 | Model Semantics / Signal Redundancy | CLOSED |

---

# PHASE 0 — Core Execution Contract Closure

## Goal

Verify that the core Production decision chain can be reproduced and
that persistent state required by the decision path survives across runs.

## Core Topology

Historical / Production Inputs
→ F13 Risk Budget
→ F15 Exposure
→ F18 Allocation
→ Cash / ETF Mapping

## Completed

- Production ↔ Backtest execution contract reviewed.
- Core F13 / F15 / F18 decision path reconstructed.
- F18 Rank3D persistence transport audited.
- `filter18_rank_state.json` is saved and restored across runs.
- F18 allocation logic itself was not changed during state-transport work.
- Consumed F18 state is observable in Run Manifest.

## Key Evidence

- `data/filter18_rank_state.json`
- Run Manifest F18 state metadata
- Commit:
  `bce176bf Persist Filter18 Rank3D state across production runs`

## Status

CLOSED

## Remaining note

Scheduled Production cross-run evidence may still be retained as
operational confirmation, but the transport contract itself is closed.

---

# PHASE 1 — Temporal Integrity / Data Provenance

## Goal

Determine what information was actually available to Production
at decision time.

## Core Topology

Production Input
→ Observation Clock
→ Retrieval / Availability Clock
→ State Clock
→ Run Manifest
→ Cross-Clock Audit

## Completed

- Production decision inputs inventoried as I01–I35.
- Observation dates attached where available.
- Retrieval timestamps recorded where relevant.
- Persistent state timestamps recorded.
- FRED observation-date lineage added.
- Positioning observation dates added.
- Positioning source tickers added.
- Positioning retrieval timestamp added.
- Live Drift bar/retrieval clocks added.
- Flow / SEW / F15 state freshness tracked.
- F18 consumed state tracked.
- Sovereign observation dates tracked.
- Breadth / Leadership clocks tracked.
- Core market clocks tracked.
- HYG/LQD daily vs live clocks separated.
- Cross-Clock Audit classifier added.
- Semantic clock policy added.
- `NO_CLOCK = 0`.
- Final local Cross-Clock result:
  `OVERALL = PASS`
- Final unresolved temporal warnings:
  `NONE`

## Key Evidence

- `docs/GCF_PRODUCTION_DECISION_INPUT_CLOCK_AUDIT_2026-10-08.md`
- `insights/run_manifest_*.json`
- Commit:
  `ec982fd8 Close production temporal integrity audit`

## Important Clock Semantics Identified

### Positioning

Latest positioning data may legitimately be newer than canonical
daily market `data_as_of`.

Recorded provenance now includes:

- observation date
- source ticker
- retrieval timestamp

### Previous Portfolio State

Previous portfolio state is an internal run-state clock,
not a market observation clock.

It is valid when:

previous_portfolio_date < report_date

even if it is newer than the last market `data_as_of`.

## Status

CLOSED

---

# PHASE 2 — Decision & Report Semantic Integrity

## Goal

Verify that every published decision number has:

- one canonical producer
- one defined meaning
- one runtime position
- one timestamp/state context
- clearly identified downstream consumers

## Confirmed Runtime Decision Chain

generate_daily_report()
→ build_strategist_commentary()
→ F13 narrative_engine_filter()
→ RISK_BUDGET
→ F15 volatility_controlled_exposure_filter()
→ RECOMMENDED_EXPOSURE
→ apply_geo_overlay_to_final_state()
→ RECOMMENDED_EXPOSURE may be constrained
→ F18 sector_allocation_filter()
→ Portfolio Allocation
→ final_action_engine()
→ FINAL_ACTION

## Confirmed Fields

### RISK_BUDGET

Producer:
`filters/strategist_filters.py::narrative_engine_filter`

Write:
`market_data["RISK_BUDGET"]`

Primary consumer:
F15

Meaning:
F13 strategic risk budget before F15 execution/risk compression.

Status:
PRODUCER IDENTIFIED

---

### RECOMMENDED_EXPOSURE

Initial producer:
`filters/strategist_filters.py::volatility_controlled_exposure_filter`

Write:
`market_data["RECOMMENDED_EXPOSURE"]`

Downstream consumer:
F18

Mutation point:
`apply_geo_overlay_to_final_state()`

Potential semantic states:

1. raw F15 exposure
2. post-Geo constrained exposure

Status:
OPEN — SEMANTIC REVIEW REQUIRED

---

### FINAL_ACTION

Producer:
`final_action_engine()`

Runtime position:
after F13 / F15 / Geo / F18 path

Stored as:
`market_data["FINAL_ACTION"]`

Status:
PRODUCER IDENTIFIED, DOWNSTREAM SEMANTICS STILL UNDER REVIEW

---

## Finding P2-001 — F15 vs SEW Exposure Engine Duplication

Observed:

Daily Production path:
`filters/strategist_filters.py::volatility_controlled_exposure_filter`

SEW path:
`scripts/monitor_sew.py::volatility_controlled_exposure_filter`

Questions:

- Are these intentionally different horizons?
- Which one is portfolio authority?
- Can SEW mutate Production exposure?
- Are both presented under the same semantic label?

Potential risk:

- authority ambiguity
- semantic drift
- duplicate exposure definitions

Status:
COMPLETED

Resolution:
- F15 is the sole Production portfolio exposure-control authority.
- SEW is alert/evidence-only and has no executable portfolio-action authority.
- F15 exposure-control state is separated from `SEW_STATUS` via `FILTER15_EXPOSURE_CONTROL_STATUS`.
- Resolved by commits `03a647ce` and `398e5c71`.

Decision:
RESOLVED — F15 is the sole exposure authority; SEW is alert/evidence-only.

---

## Finding P2-002 — RECOMMENDED_EXPOSURE Mutation

Observed:

F15
→ writes `RECOMMENDED_EXPOSURE`

Geo overlay
→ may modify `RECOMMENDED_EXPOSURE`

F18
→ consumes the resulting value

Question:

Does the report clearly distinguish:

- raw F15 exposure
- post-Geo exposure

Potential risk:

A value may be presented as “F15 Exposure”
even though it has already been changed by Geo.

Status:
COMPLETED

Resolution:
- F15 raw authority output is preserved explicitly as `F15_RECOMMENDED_EXPOSURE`.
- Geo pre/post-constraint exposure is preserved as `GEO_BASE_F15_EXPOSURE` and `GEO_ADJUSTED_EXPOSURE`.
- F18 records its actual upstream executable input as `F18_CONSUMED_EXPOSURE`.
- `RECOMMENDED_EXPOSURE` remains the backward-compatible executable field to avoid unnecessary Production consumer migration.
- `BASE_RECOMMENDED_EXPOSURE` is retained for compatibility but is explicitly documented as the exposure entering the F18 regime controller, not raw F15 exposure.
- Geo behavior and SEW non-authority are protected by `tests/test_exposure_lineage.py` (3 regression tests PASS).

Decision:
RESOLVED — exposure calculation behavior is unchanged; F15 → Geo → F18 lineage is now explicitly observable.

---

## Phase 2 Audit Queue

- POS_Z duplicate/conflicting presentation
- F15 raw vs post-Geo exposure naming
- F15 vs SEW authority boundary
- FINAL_ACTION lineage
- liquidity label conflicts
- flow state persistence semantics
- missing → 0 / neutral fallback semantics
- report text vs structured Production state

## Status

IN PROGRESS

---

# PHASE 3 — F18 Allocation Lineage

## Goal

Explain why every final portfolio weight exists.

## Target Topology

Raw Sector Score
→ Macro Adjustment
→ Rank
→ Persistence
→ Eligibility
→ Cap / Constraint
→ Normalized Weight
→ Exposure Reconciliation
→ ETF Weight

## Questions To Resolve

- Why is each sector OW / UW / zero?
- At what exact transformation did a sector become zero?
- Which constraint changed the weight?
- Does Rank3D persistence affect eligibility exactly as intended?
- Is F18 total exposure reconciled exactly to upstream exposure?
- Are ETF mappings historically eligible?
- Any future membership / inception leakage?

## Evidence To Record

- canonical producer for each intermediate F18 field
- pre/post rank
- persistence state
- eligibility
- cap
- normalized weight
- final ETF weight
- previous vs current allocation

## Findings

None recorded yet.

## Status

NOT STARTED

---

# PHASE 4 — Model Semantics / Signal Redundancy

## Goal

Verify that each major signal has a distinct economic role
and that duplicated information is understood.

## Areas To Audit

### Proxy terminology

Examples:

- Dealer Gamma Bias
- Gamma proxy
- positioning proxy
- liquidity labels

Questions:

- What does the signal actually measure?
- Is its name stronger than the underlying data supports?
- Should it be labelled as a proxy/context signal?

### Signal redundancy

Example:

VIX
→ Regime
→ F15 risk control
→ Flow
→ Gamma-related context

Question:

Is the same underlying information penalizing risk multiple times?

### Missing-value semantics

Audit:

- missing → 0
- missing → neutral
- previous value reuse
- fallback states

Question:

Does fallback behavior have economic meaning,
or merely keep the code running?

### Duplicate engines / functions

Record duplicated implementations that may create semantic drift.

Do not clean them merely for code style.
Only classify them after runtime authority is proven.

## Findings

None formally classified yet.

## Status

NOT STARTED

---

# FINDING DECISION REGISTER

Use only these final classifications:

- KEEP
- FIX
- DOCUMENT
- DEFER

| ID | Phase | Finding | Status | Final Decision |
|---|---|---|---|---|
| P2-001 | 2 | F15 vs SEW exposure engine duplication | COMPLETED | F15 = exposure authority; SEW = alert/evidence only |
| P2-002 | 2 | RECOMMENDED_EXPOSURE mutation / lineage ambiguity | COMPLETED | F15 raw → Geo adjusted → F18 consumed lineage explicit |

---

# FINAL JUNIOR-READY TARGET

Core target:

Phase 0 CLOSED
→ Phase 1 CLOSED
→ Phase 2 CLOSED
→ Phase 3 CLOSED
→ Phase 4 CLOSED

At that point the system should be able to answer:

1. What data entered the system?
2. When was that data actually available?
3. What signal/state did it create?
4. Who produced each decision number?
5. How did F13 become F15 exposure?
6. How did exposure become F18 allocation?
7. Why does each final portfolio weight exist?
8. What economic role does each major signal serve?
9. Are signals duplicated or double-counted?
10. Which known issues must be fixed, documented, kept, or deferred?

---

# RULE

This document is the master audit record.

Detailed evidence files remain as supporting evidence.

Do not fix findings during discovery unless a separate remediation
decision has been made and recorded here.

---

## Phase 2 Update — P2-001 Authority Review

### P2-001 — F15 vs SEW Exposure Engine Duplication

Final runtime contract:

- F15 is the sole Production portfolio exposure-control authority.
- SEW is an intraday anomaly monitor and alert/evidence-only layer.
- SEW does not directly set portfolio exposure.
- SEW does not directly force Final Action portfolio changes.
- SEW does not qualify Geo transmission for executable exposure reduction.
- Institutional Flow may still use SEW as observational/context evidence.
- F15 exposure-control status is stored separately in
  `FILTER15_EXPOSURE_CONTROL_STATUS`.

Regression protection:

- `tests/test_exposure_lineage.py` verifies that SEW alone cannot confirm
  Geo transmission or reduce executable exposure.

Status:

COMPLETED

Decision:

RESOLVED — F15 is the sole exposure authority; SEW is alert/evidence-only.

Implementation:

- `03a647ce` — Make SEW intraday monitor alert-only
- `398e5c71` — Separate SEW alerts from portfolio action authority
- `a85fae57` — Remove SEW from Geo exposure authority

---

## Finding P2-003 — SEW_STATUS Semantic Collision

Status:

COMPLETED

Original finding:

Production previously overloaded `SEW_STATUS` with two incompatible
semantic contracts:

- SEW intraday anomaly / shock state
- F15 portfolio exposure-control state

This could cause downstream consumers to interpret an F15 state as
the original SEW monitor state.

Resolution:

Production authority is now explicitly separated:

- `SEW_STATUS` = SEW intraday anomaly / shock state only.
- `FILTER15_EXPOSURE_CONTROL_STATUS` = F15 portfolio exposure-control state only.
- PM Final Brief reads the dedicated F15 control-status field.
- Geo no longer uses SEW as portfolio exposure authority or as a
  transmission qualifier for exposure reduction.

Historical reconstruction was also corrected:

- historical SEW values are not reconstructed as `f15.exposure_control`.
- historical SEW values are not reconstructed as
  `constraint.exposure_control`.
- where no canonical historical F15 control-state evidence exists,
  F15 exposure control remains `UNAVAILABLE` rather than being inferred
  from a different signal.

Regression protection:

- `tests/test_sew_f15_semantic_separation.py`: 3 / 3 PASS.
- `tests/test_exposure_lineage.py`: 3 / 3 PASS.
- Python compile check: PASS.
- `git diff --check`: PASS.

Canonical semantic contract:

SEW
→ intraday anomaly / shock observation
→ alert / contextual evidence
→ no F15 semantic substitution

F15
→ portfolio exposure-control authority
→ dedicated `FILTER15_EXPOSURE_CONTROL_STATUS`

Decision:

RESOLVED — SEW and F15 now retain separate runtime and historical
semantic identities. Missing historical F15 state is represented as
unavailable rather than reconstructed from SEW.


### P2-002 Runtime Lineage Conclusion

Finding:

`RECOMMENDED_EXPOSURE` changes semantic meaning during the same
Production runtime.

Observed lineage:

F15
→ writes `market_data["RECOMMENDED_EXPOSURE"]`

Geo Overlay
→ reads the F15 value as base exposure
→ may overwrite the same `RECOMMENDED_EXPOSURE` key

F18
→ reads the resulting `RECOMMENDED_EXPOSURE`

Therefore F18 consumes:

`post-Geo executable exposure`

not necessarily:

`raw F15 exposure`

Additional semantic mismatch:

`generate_report.py` contains the comment:

`F15 structured output is authoritative`

but the value read at that point may already be the
post-Geo constrained value.

Also:

`BASE_RECOMMENDED_EXPOSURE`

is assigned only after Geo execution when F18 starts.

Therefore this field is not guaranteed to represent
the original raw F15 exposure.

Potential impact:

- raw F15 output is not preserved as a distinct canonical field
- post-Geo exposure can be labelled or interpreted as F15 output
- report / manifest lineage may obscure which layer changed exposure
- audit reconstruction of F15 → Geo → F18 can become ambiguous

Runtime decision behavior:

No evidence yet that the numerical portfolio calculation itself is wrong.

The issue is semantic lineage / observability.

Classification:

FIX

Required remediation design:

Preserve distinct canonical states, conceptually:

- raw F15 exposure
- post-Geo executable exposure
- F18 consumed exposure

Do not implement remediation yet.


## Finding P2-004 — Missing Positioning Is Converted To Neutral

Observed canonical positioning path:

`fetch_positioning_data.py`
→ computes `SP500_POS_Z`
→ writes `positioning_data.csv`
→ `generate_report.py::attach_positioning_layer`
→ `market_data["SP500_POS_Z"]`
→ F13 / F15 / downstream consumers

No conflicting Production POS_Z producer was identified in this audit.

However, missing-data semantics are unsafe.

Observed behavior:

1. If all positioning source tickers fail:

`get_reliable_z_score()`
returns:

`0.0, None, None`

2. If positioning data is unavailable in Production:

`attach_positioning_layer()`

uses:

`SP500_POS_Z = 0.0`

3. F13 then interprets the value numerically.

A value of 0.0 receives no positioning penalty.

4. F15 also interprets the same value numerically as neutral positioning.

Therefore two different states are currently indistinguishable:

A. genuinely neutral positioning (`POS_Z ≈ 0`)

B. positioning unavailable / failed retrieval

Potential impact:

Missing positioning evidence can silently become a neutral market signal.

This can suppress positioning-related risk penalties without explicitly
telling downstream decision engines that the input is unavailable.

Classification:

FIX

Required remediation design:

Preserve missingness separately from economic neutrality.

Conceptually distinguish:

- valid POS_Z = 0.0
- POS_Z unavailable
- source/retrieval failure

Downstream F13/F15 fallback policy must then be explicitly defined.

Do not implement remediation during Phase 2 discovery.


---

## Finding P2-005 — Flow `persistence_days` Is Run Persistence, Not Calendar-Day Persistence

Observed:

`classify_flow_transition()` receives the previous persisted counter and
updates it using arithmetic such as:

`prev_persistence_days + 1`

or:

`prev_persistence_days - 1`

No elapsed-date or calendar-day calculation is performed.

The state is saved after each SEW monitor execution.

Therefore:

`persistence_days`

currently represents persistence across qualifying monitor runs,
not verified calendar-day persistence.

Potential impact:

If SEW executes multiple times within one day, the field name can
overstate the duration of institutional flow persistence.

Classification:

FIX

Required remediation design:

Either:

1. rename the field to accurately represent run persistence,

or

2. implement true date-based persistence.

Do not remediate during topology discovery.

---

## Finding P2-006 — Core Decision Missing-Value Defaults

Observed core decision fallbacks include:

- `SP500_POS_Z` missing → `0.0`
- `POS_SLOPE` missing → `0.0`
- `DEALER_GAMMA_BIAS` missing → `1.0`
- `CTA_MOMENTUM_SCORE` missing → default numeric state
- `RISK_BUDGET` missing → `50`

These fallbacks allow the decision chain to continue,
but some numeric defaults can be indistinguishable from genuine
economic observations.

Potential risk:

DATA UNAVAILABLE

can become semantically equivalent to:

ECONOMICALLY NEUTRAL / DEFAULT STATE

without an explicit missingness flag.

P2-004 already confirms this problem for Positioning.

P2-006 generalizes the issue to other core decision inputs.

Classification:

FIX / POLICY REQUIRED

Required remediation design:

For every core decision input define explicitly:

- valid observation
- unavailable observation
- fallback behavior
- whether fallback is neutral, conservative, stale reuse, or fail-closed

Do not implement remediation during topology discovery.

---

## Liquidity Semantic Audit Conclusion

Observed canonical structure:

`NET_LIQ`
→ direction (`UP / DOWN / FLAT`)
→ level bucket (`HIGH / MID / LOW`)

Production stores these concepts separately as:

- `liquidity_dir`
- `liquidity_level_bucket`
- `NET_LIQ_DIR`
- `NET_LIQ_LEVEL_BUCKET`

PM presentation also distinguishes:

- Liquidity direction
- Liquidity Level
- Dollar Liquidity
- Fed Plumbing momentum

No material authority or semantic collision was identified.

Classification:

KEEP

---

## FINAL_ACTION Lineage Conclusion

Observed runtime:

F13
→ F15
→ Geo
→ F18
→ `final_action_engine()`
→ `FINAL_ACTION`
→ `war_room_final_decision_filter()`
→ `FINAL_DECISION`

`final_action_engine()` consumes:

- FINAL_STATE / phase
- institutional flow
- gamma
- positioning
- risk budget
- `SEW_STATUS`

Historical audit conclusion:

P2-003 originally had downstream decision relevance because
`FINAL_ACTION` consumed the overloaded `SEW_STATUS` field.

At discovery time, `FINAL_ACTION` expected SEW semantics such as:

- STABLE
- WATCH
- ALERT
- DEADMAN

while the same flat key could already contain F15 exposure-control
status.

Current remediation status:

RESOLVED

- SEW and F15 now use separate semantic fields.
- direct SEW portfolio-action gates were removed from Final Action.
- SEW no longer substitutes for F15 exposure-control authority.
- no separate FINAL_ACTION authority conflict remains.

Classification:

DOCUMENT — historical finding resolved through P2-001 / P2-003 remediation.

---

# PHASE 2 — AUDIT CONCLUSION

Phase 2 topology / semantic discovery is complete.

## Findings

P2-001 — F15 vs SEW exposure engine duplication
Decision: RESOLVED / COMPLETED

P2-002 — RECOMMENDED_EXPOSURE pre/post Geo semantic mutation
Decision: RESOLVED / COMPLETED

P2-003 — SEW_STATUS semantic collision
Decision: RESOLVED / COMPLETED

P2-004 — Missing Positioning converted to neutral
Decision: FIX

P2-005 — Flow persistence_days is run-count semantics
Decision: FIX

P2-006 — Core decision missing-value fallback policy
Decision: FIX / POLICY REQUIRED

Liquidity semantic audit
Decision: KEEP

FINAL_ACTION lineage
Decision: DOCUMENT — P2-003 dependency resolved

## Phase Status

AUDIT CLOSED

REMEDIATION PENDING

No Production decision logic was changed during Phase 2 discovery.

Next:

PHASE 3 — F18 Allocation Lineage


---

# PHASE 3 — F18 ALLOCATION LINEAGE

## Confirmed Runtime Lineage

Production F18 allocation path:

`RECOMMENDED_EXPOSURE`
→ sector final scores
→ positive-score allocation universe
→ classification / divergence adjustment
→ score-proportional initial weights
→ deleveraging logic
→ regime caps
→ participation-quality caps
→ residual reallocation
→ exposure compression
→ rounding
→ Rank3D persistence
→ rebalance threshold
→ execution ceiling reconciliation
→ sector-to-ETF mapping
→ paper portfolio persistence

Confirmed controls:

- only positive-score sectors enter the normal allocation universe
- classification and divergence modify effective allocation scores
- deleveraging uses explicit priority logic
- macro-profile sector caps are applied
- participation-quality caps are applied
- Rank3D suppresses unconfirmed rank changes
- deleveraging bypasses Rank3D persistence
- 2% / 5% rebalance thresholds operate downstream
- final execution weights cannot exceed the current exposure ceiling
- sector weights map deterministically to sector ETFs
- Rank3D state commits only after successful portfolio persistence

---

## Finding P3-001 — Residual Reallocation Can Breach Previously Evaluated Sector Caps

Observed order:

1. regime caps are applied
2. participation-quality caps are applied
3. residual capital may be redistributed to eligible sectors
4. exposure compression is applied only if total sector exposure exceeds the total exposure ceiling
5. weights are rounded and returned

No sector-cap validation is performed after residual redistribution.

Important consequence:

A sector that was below its cap during the original cap check may receive
additional residual allocation and subsequently exceed that cap.

Example semantic path:

`Technology = 17%`
→ Technology cap = `18%`
→ no cap action
→ residual reallocation adds `3%`
→ Technology becomes `20%`

If total sector exposure remains within the portfolio exposure ceiling,
the later exposure-compression step does not necessarily reduce the
sector back to its 18% cap.

Therefore the portfolio-level exposure ceiling remains protected,
but the intended sector-level concentration cap can be violated.

Classification:

FIX

Required remediation design:

After residual redistribution, revalidate all applicable:

- regime caps
- participation-quality caps

Any excess must either:

- return to cash, or
- be redistributed only to sectors with remaining eligible capacity.

Do not implement remediation during topology discovery.

---

## Phase 3 Audit Conclusion

F18 allocation lineage is now reconstructed through:

score
→ eligibility
→ sizing
→ caps
→ residual policy
→ Rank3D
→ rebalance threshold
→ execution ceiling
→ ETF mapping
→ persisted portfolio

The final execution ceiling reconciliation is structurally sound and
prevents stale Rank3D weights from exceeding the current portfolio
exposure ceiling.

One material allocation-lineage issue was identified:

P3-001 — residual reallocation can breach sector caps.

Phase 3 topology discovery is complete.

Status:

AUDIT CLOSED

REMEDIATION PENDING

Next:

PHASE 4 — Model Semantics / Signal Redundancy


---

# PHASE 4 — MODEL SEMANTICS / SIGNAL REDUNDANCY

## Finding P4-001 — Institutional Flow Family Is Additive Across Multiple F13 Paths

Observed F13 flow-related contributions include:

1. Flow / Gamma Alignment Boost

`budget += flow_gamma_tilt`

2. Flow Continuity Tilt

`budget += flow_continuity_tilt`

3. Flow Regime Modifier

`budget += flow_regime_tilt`

All three depend materially on the same current institutional flow state
or `flow_score`.

The concepts are not identical:

- flow/gamma alignment measures cross-signal confirmation
- flow continuity measures persistence/change
- flow regime tilt measures current flow strength

However, they can activate simultaneously and add independently to the
same Risk Budget.

Therefore a single strong institutional-flow episode can influence F13
through multiple additive paths.

Potential impact:

Correlated evidence may receive more effective weight than intended.

Classification:

FIX / POLICY REVIEW

Required remediation design:

Define an explicit flow-family aggregation policy.

Possible approaches include:

- family-level contribution cap
- hierarchical flow score
- mutually exclusive modifiers
- explicit evidence-independence justification

Do not change Production logic during topology discovery.

---

## Finding P4-002 — REAL_RATE and US10Y Carry Partially Overlapping Rate Information

Observed structure score:

- REAL_RATE weight = 1.0
- DXY weight = 1.0
- US10Y weight = 0.5

The Production comment explicitly states that US10Y overlaps with
REAL_RATE somewhat and therefore receives a weaker weight.

This is not currently classified as a direct implementation bug.

Nominal 10Y yield and real yield contain distinct information,
but both can represent the same broad tightening/easing impulse.

Classification:

DOCUMENT / POLICY REVIEW

Required follow-up:

During model review, verify whether the current 1.0 / 0.5 weighting
provides intended incremental information rather than duplicated rate
exposure.

---

## Finding P4-003 — FCI Comment / Runtime Scoring Mismatch

Observed structure-score comment describes:

`REAL_RATE, FCI, DXY`

as stronger-weight components.

Actual additive score currently uses:

- REAL_RATE
- DXY
- US10Y

FCI is read and displayed as a low-frequency value but is not added to
the structure score in this runtime path.

Therefore documentation/comment semantics do not exactly match the
implemented score.

Classification:

DOCUMENT

No evidence from this audit establishes that FCI should be added to the
Production score.

The correct remediation is first to align documentation with actual
intended model authority, not to automatically change scoring logic.

---

## Signal-Family Review Conclusions

### Positioning / Gamma / CTA

No direct duplicate producer was identified.

The system distinguishes:

- `SP500_POS_Z` — positioning state
- `DEALER_GAMMA_BIAS` — positioning-layer gamma proxy
- `GAMMA_STATE` — Drift / VIX / SEW-based pseudo gamma regime
- `CTA_MOMENTUM_SCORE` — momentum / trend-following context

Classification:

KEEP / DOCUMENT

These signals can be correlated but are not semantically identical.

### Cross-Layer Signal Reuse

The same market variables may appear in F13, F15 and F18.

Signal reuse across layers is not automatically double counting because
the layers have different responsibilities:

F13
→ strategic risk budget

F15
→ exposure control

F18
→ sector allocation

The material concern is additive reuse of the same economic evidence
inside one decision authority without an explicit family-level contract.

---

# PHASE 4 — AUDIT CONCLUSION

Phase 4 semantic / redundancy discovery is complete.

Material findings:

P4-001 — Institutional Flow family additive overlap
Decision: FIX / POLICY REVIEW

P4-002 — REAL_RATE / US10Y partial rate overlap
Decision: DOCUMENT / POLICY REVIEW

P4-003 — FCI comment / runtime scoring mismatch
Decision: DOCUMENT

Positioning / Gamma / CTA semantic separation
Decision: KEEP / DOCUMENT

No Production decision logic was changed during Phase 4 discovery.

Status:

AUDIT CLOSED

REMEDIATION PENDING

