# GCF Historical PM V2 Reconstruction V1

## Boundary

This contract adds a truth-preserving PM V2 presentation layer over the public historical surface. It does not replace or weaken `GCF_PUBLIC_HISTORICAL_REPORT_RELIABILITY_V1`. Every pre-PM-V2 page retains the exact persisted report bytes and SHA-256 used by that contract.

Authority order:

1. **A — historically reconstructable:** persisted `Data as of` exactly equals a `signal_date` in the frozen canonical PIT F13 → F15 → F18 parity artifact.
2. **B — persisted historical source:** the same-date report contains an explicit, semantically compatible labelled value.
3. **C — not legitimately reconstructable:** neither authority exists. The value is exactly `Unavailable`, with reason and source identity.

Nearest-date, current-date, interpolated, inferred, neutral, zero, and arbitrary default backfills are prohibited.

An A replay value and an explicitly persisted publication value are different kinds of truth: the former is a current-equivalent canonical reconstruction; the latter records what the historical publication actually said. If they differ, the PM V2 cockpit labels and displays both values and retains the lossless source. A difference must never be silently collapsed into either authority.

## Runtime and data lineage

Live: `generate_daily_report` → market-data adapters/normalizers → `build_strategist_commentary` → Production F13 → F15 → F18 → F19/final decision → `generate_pm_final_brief` → persisted PM V2 Markdown → `build_pm_site.build`.

Validated history: canonical PIT panel → `build_market_data` → `prepare_filter13_execution_state` → `prepare_historical_execution_contract` → Production F13 → F15 with isolated historical state → F18 allocation capture → frozen 4,645-row parity artifact.

Publication: persisted report date/data-as-of → exact-clock frozen parity lookup → explicit-only persisted parser → A/B/C record → PM V2 adapter → current renderer → provenance panel plus lossless original source.

The renderer never runs Production decision logic. Research treatment outputs are evidence only and never publication authority.

## Inventory and evidence

The inventory contains the 62 scalar fields read by the PM V2 renderer: top decision, F13/F15/F18 path, executive view, market state, cross-asset tape, leadership coverage, allocation context, active constraints, and final rationale. Variable sector allocation and F19 rows receive row-level provenance checks.

Frozen evidence is reused byte-for-byte: the 4,645-row F13/F15/F18 parity file and summary, canonical panel identity/provenance, canonical authority chain, G4 state/clock integrity, validated intervention population, and Claim 5 causal propagation manifests. Production code, thresholds, state semantics, and canonical authority are unchanged.

Exactly 88 of 246 reports have persisted data-as-of clocks matching the frozen canonical signal dates. Only those reports can receive A fields. Missing clocks and post-panel dates remain B/C and are never mapped to a nearby row.

## Gate

The audit fails on population/routing/schema mismatch, report/data clock failure, absent or changed provenance, A without exact frozen identity, B without same-date identity, hidden A-versus-persisted differences, any C value other than `Unavailable`, F13/F15/F18 capital inconsistency, F18 sector reconciliation failure, F19 display mismatch, renderer defaults, current PM V2 regression, or any V1 reliability regression.
