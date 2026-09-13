# Public Historical Report Reliability Contract V1

## Authority boundary

- The dated `reports/daily_report_YYYY-MM-DD.md` file is the authoritative publication snapshot for its report date.
- A same-date `reports/engine_diagnostics_YYYY-MM-DD.md` file is an additional authoritative diagnostics snapshot when it exists.
- The public renderer may format persisted values. It must not recalculate Production decisions, infer absent fields, or manufacture replacements for missing values.
- This contract does not modify F13, F15, F18, F19, historical source data, portfolio state, or frozen research evidence.

## Schema routing

- `PM_V2_COMPLETE` reports use the strict structured PM renderer.
- Pre-contract `LEGACY_BASIC`, `LEGACY_ENGINE`, and the dated transitional allowlist use a lossless archival renderer.
- The archival renderer exposes the persisted source byte-for-byte in an escaped HTML snapshot with a SHA-256 identity.
- A new report dated on or after 2026-09-07 must satisfy `PM_V2_COMPLETE`. A new partial or unknown schema fails the gate.
- Missing diagnostics never create a diagnostics page or link. Missing historical metadata is stated as not recorded; it is not inferred.

## CI acceptance checks

`scripts/audit_public_historical_reliability.py` machine-enumerates the full persisted report population and validates:

1. calendar population identity and same-date report routing;
2. report/page existence and stale unbacked page rejection;
3. report date and data-as-of clock consistency;
4. schema classification and historical rendering route;
5. byte-exact legacy source rendering and diagnostics-source rendering;
6. strict PM V2 displayed-field reconciliation;
7. F13/F15/F18 report-to-diagnostics consistency and allocation identities;
8. F19 ETF/action/classification/divergence rendering;
9. parser-created unavailable states and unsupported renderer fallbacks;
10. new-schema drift after the strict-contract start date.

Both the daily report workflow and the Pages deployment workflow run the audit and regression tests before publication can proceed.

## Closure evidence (2026-09-13 population)

- Pre-fix baseline: **FAIL**, 14,879 failed assertions.
- Calendar dates: **246**.
- Daily report pages: **246**.
- Same-date diagnostics sources: **11**.
- Schema population: 50 legacy basic, 185 legacy engine, 5 transitional PM V2, 6 complete PM V2.
- Post-fix reconciliation: **90,515 checks, 0 failures**.
- Lossless archival routes: **240 reports**.
- Strict structured routes: **6 reports**.
- Source-recorded `N/A`/`nan` tokens preserved without invention: **307**.
- Reports whose old persisted contract did not record data-as-of: **77**.
- Reports without a separate diagnostics artifact, now left without a fabricated diagnostics page: **235**.

The machine-readable current-population result is stored in `artifacts/public_historical_reliability_audit_v1.json`.
