# Filter18 Execution Capital Ceiling — Production Change Record

**Date:** 2026-08-16
**Status:** CLOSED
**Component:** Filter18 Sector Allocation / Execution Boundary

## Problem

Filter13 → Filter15에서 결정된 최종 허용 총노출보다
Filter18의 실제 ETF 섹터 배분 합계가 커지는 경우가 발견되었다.

원인은 Rank Persistence 3D가 이전에 승인된 sector composition과 함께
과거 absolute weights를 유지하면서, 현재 더 낮아진 exposure ceiling을
초과할 수 있었기 때문이다.

## Fix

`FILTER18_EXECUTION_CEILING_RECONCILIATION_V1`을
Filter18 / Rank Persistence 결정 이후,
`build_execution_etf_map()` 직전에 추가하였다.

최종 실행 계약:

Filter13 Risk Budget
→ Filter15 Exposure Control
→ Filter18 Sector Allocation
→ Rank Persistence 3D
→ Capital Ceiling Reconciliation
→ ETF Execution
→ Portfolio Persistence

Invariant:

Actual ETF Sector Exposure
<= Filter18 Allowed Exposure
<= Filter15 Exposure

현재 허용 exposure를 초과하는 경우 sector의 상대적 구성을 유지하면서
비례 축소하고, 0.1% execution rounding 이후 발생할 수 있는 residual
초과분도 제거한다.

## Logic Preservation

다음 로직은 변경하지 않았다.

- Filter13
- Filter15
- Filter18 sector ranking
- Rank Persistence confirmation logic
- build_tactical_allocation()
- build_execution_etf_map()

새로운 indicator 또는 parameter optimization도 추가하지 않았다.

## Full-History Validation

Executable PIT rows: 4,645

Pre-patch:
- Ceiling breaches: 293
- Max breach: +5.1%p

Post-patch:
- Execution errors: 0
- Ceiling breaches: 0
- Filter18 > Filter15: 0
- Negative tactical reserve: 0
- Max sector over allowed: 0.0
- Max capital error: 0.0

## Behavioral Regression

- Upstream 13/15/18 changes: 0
- Corrected breach rows: 293 / 293
- New breaches: 0
- Normal-date capital changes: 0
- Wrong-direction corrections: 0

Behavior classes:

- UNCHANGED_NORMAL: 4,352
- EXPECTED_BREACH_CORRECTION: 293

따라서 기존 정상 날짜의 행동은 유지하면서
capital-contract violation만 제거되었다.

## Governance

Research branch:
`institutional-backtest-v1`

Research validation commit:
`a2991871be79a8911efb530ce64f7b4133f06e39`

Production branch:
`main`

Production commit:
`809b5c975bec3cbb9f4e4749ad4c38e3c496eb2f`

Production promotion scope:
`filters/strategist_filters.py`

Research audit scripts와 intermediate artifacts는 Production으로
승격하지 않았다.

## Final Decision

Research Validation: PASS
Behavioral Regression: PASS
Production Promotion: PASS

Pre-patch breaches: 293
Post-patch breaches: 0
Normal rows changed: 0

**STATUS: CLOSED**
