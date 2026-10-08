# Global-Capital-Flow-Monitor — Production Decision Input Inventory / Clock Registry Audit

Audit date: 2026-10-08 KST  
Mode: **READ-ONLY**  
Production baseline: **`main@c14c72e1b15bb6a87cb7d5520e482cb258962f78`**  
Target repository: `/private/tmp/gcf-main` (detached read-only audit worktree)  
Target repository changes: **none**

## 0. Scope, evidence standard, and verdict preview

The audited runtime root is exactly:

```text
.github/workflows/daily-macro.yml
→ scripts/generate_report.py::generate_daily_report()
→ filters/strategist_filters.py::build_strategist_commentary()
→ F13 narrative_engine_filter()
→ F15 volatility_controlled_exposure_filter()
→ apply_geo_overlay_to_final_state()
→ F18 sector_allocation_filter()
→ final allocation / report
```

This inventory follows actual callers, readers, writers, dictionary keys, and default branches. Names, comments, and files that are not reachable from this path are not treated as Production decision inputs.

Evidence labels:

- **VERIFIED**: caller→callee, reader/writer, or key flow is present in the audited commit.
- **UNKNOWN**: repository code does not preserve enough metadata to prove the fact.
- **SHADOW / REPORT ONLY / NON-PRODUCTION / ORPHAN**: present in the workflow or repository but not consumed by the F13→F15→F18 decision chain.

Preview: the decision-input set is statically inventoryable, but its clocks are not yet gate-ready. `data_as_of_date` is a local variable rather than a run-wide input contract; several authoritative loaders independently select their latest row; daily forward-fill often replaces the true source observation date with the run date; intraday/state inputs have separate clocks; and F18 Rank3D state is not transported across clean GitHub runners.

## 1. Proven Production runtime path

| Stage | Proven call / side effect | Evidence |
|---|---|---|
| Schedule | Daily at 01:00 UTC; manual dispatch also permitted | `.github/workflows/daily-macro.yml:3-7` |
| Producers | Macro, liquidity, credit, FRED, country ETF, sovereign, sentiment, positioning; then SEW monitor | `.github/workflows/daily-macro.yml:76-207` |
| Root selector | Loads macro file, merges sovereign spreads, chooses last row with at least 4/5 core values, blocks same-KST-day row, computes `data_as_of_date`, applies macro-only stale guard | `scripts/generate_report.py:2605-2659` |
| Attach phase | Liquidity → positioning slope → credit → FRED → sovereign → expectations → geo/country/sector/sentiment/live drift/growth/breadth/leadership/vol structure/positioning | `scripts/generate_report.py:2683-2713` |
| State injection | SEW, previous flow, F15 recovery state | `scripts/generate_report.py:2760-2830` |
| Ordered filters | Pre-filters, F13, F14, F15, geo constraint, F16/F17, F18 | `filters/strategist_filters.py:8584-8700` |
| State/output | Saves F15 state using `data_as_of_date`; F18 saves portfolio/trades and attempts Rank3D state | `scripts/generate_report.py:2833-2859`; `filters/strategist_filters.py:7702-7777` |
| Transport | Commits `data/*.csv` and `insights/*.json`, but not `data/*.json` | `.github/workflows/daily-macro.yml:344-370` |

### Actual clock topology

```text
Canonical macro clock
  data_as_of_date = selected macro_data.csv row (2026-10-07 in audited commit)
  ├─ core market, breadth, leadership, sector momentum
  └─ only family with an explicit stale stop

Independent observation/latest clocks
  ├─ liquidity latest valid NET_LIQ row
  ├─ HY OAS latest valid row
  ├─ FRED sctorallo latest calendar row (forward-filled)
  ├─ sovereign latest-any row (forward-filled upstream)
  └─ country ETF last file row

Execution/retrieval-day clocks
  ├─ positioning row stamped KST run date
  ├─ live drift downloads during report generation
  ├─ SEW/flow state timestamp from 10-minute monitor
  ├─ F18 Rank3D uses KST execution date
  └─ portfolio/trade log uses KST execution date

State clocks
  ├─ F15 state timestamp = prior canonical data_as_of_date
  ├─ flow/SEW timestamp = monitor wall clock
  └─ F18 last_processed_date = report execution date, but file is not transported
```

## 2. Production Decision Input Inventory

The inventory is split into two matched tables for readability. `ID` is the join key. “Retrieval/update” means a field persisted with the input, not merely a timestamp visible in an external service.

### 2A. Source, loader, key, and clock metadata

| ID | Input name | Type | Source / upstream producer | Actual loader / producer | Actual `market_data` or state key | Observation/source date present? | Retrieval/update timestamp present? | Production as-of actually used |
|---|---|---|---|---|---|---|---|---|
| I01 | Canonical macro row / `data_as_of_date` | Derived clock | `data/macro_data.csv`; `fetch_macro_data.py::fetch_macro_data` | `load_macro_df` → `_find_effective_market_idx` | local `data_as_of_date`; **not stored in `market_data`** | Yes: `date` | No | selected row date after KST-today exclusion and market-calendar stale guard |
| I02 | US10Y, DXY, WTI, VIX | Raw→derived series | Yahoo: `^TNX`, `DX-Y.NYB`/fallbacks, `CL=F`, `^VIX`; US10Y FRED fallback; CBOE vol fallback upstream | `build_market_data`; histories built in same function | `US10Y`, `DXY`, `WTI`, `VIX`; `*_PCT_HISTORY` | One shared macro row date; no per-field date | No | canonical selected row; previous value is last earlier non-null row |
| I03 | GOLD, USDCNH, USDJPY, USDMXN, SEA, BDRY, ITA, XAR, EEM, EMB | Raw→derived geo inputs | Yahoo via `fetch_macro_data.py` | `build_market_data` → `attach_geopolitical_ew_layer` | same names, `{today,prev,pct_change}` | Shared macro row date only | No | canonical row/history slice through `today_idx` |
| I04 | HYG / LQD daily price | Raw→derived credit/risk participation | Yahoo → `macro_data.csv` | `build_market_data`; also independently downloaded by live drift | `HYG`, `LQD`; live `DRIFT_DATA.HYG/LQD` | Macro date for daily family; live download index is discarded | No persisted retrieval time | canonical row for daily filters; latest live bar for flow validation |
| I05 | SPY, QQQ, XLK, XLF, XLE, XLRE daily correlation inputs | Raw→derived | Yahoo → `macro_data.csv` | `build_market_data` → correlation state functions | same names, `pct_change` | Shared macro row date | No | canonical row |
| I06 | Breadth prices SPY/RSP/QQQ/QQQE | Raw→derived | Yahoo → `macro_data.csv` | `attach_breadth_layer` | `BREADTH_*`, `_PREV`, `_PREV2`, `_BREADTH_ASOF` | Yes: `_BREADTH_ASOF` = canonical row | No | exactly `today_idx`, `today_idx-1/-2` |
| I07 | Leadership prices QQQ/SPY/SMH/SOXX/IWM/XLK/XLF/XLI/XLY | Raw→derived | Yahoo → `macro_data.csv` | `attach_leadership_layer` | `LEAD_*`, `_PREV`, `_PREV2`, `_LEADERSHIP_ASOF` | Yes: `_LEADERSHIP_ASOF` | No | canonical row and two prior rows |
| I08 | 11-sector relative momentum | Derived | Sector ETF and SPY history in `macro_data.csv` | `attach_sector_momentum_layer` | `MOMENTUM_SCORES[XLK…XLC]` | No dedicated field; inherits macro history | No | 20/60-row lookbacks ending at canonical row |
| I09 | VIX3M / VIX9D term structure | Raw→derived | Yahoo/CBOE upstream → `macro_data.csv` | `attach_volatility_structure_layer` | `VIX3M`, `VIX9D` | No dedicated field; inherits canonical row | No | canonical row |
| I10 | FCI, REAL_RATE, T10Y2Y | Raw→derived | FRED `NFCI`, `DFII10`, `T10Y2Y` → `fred_macro_sctorallo.csv`; Treasury HTML fallback for missing treasury fields | `load_fred_extras_df` → `attach_fred_extras_layer`; T10Y2Y also reloaded by `load_fred_data_from_csv` | `FCI`, `REAL_RATE`, `T10Y2Y`; `_FCI_ASOF`, `_REAL_ASOF`, `_T10Y2Y_ASOF`; `_FRED_EXTRA.T10Y2Y` | A `date` exists, but is a daily forward-filled calendar row, not necessarily source observation date | No; Treasury fallback records literal `TREASURY_FALLBACK`, not a date | latest valid row in whole file, unconstrained by `data_as_of_date`; `_FRED_EXTRA` uses file `iloc[-1]` |
| I11 | T10YIE, DFII10, DGS2 and FRED VIX copy | Raw/preserved context | FRED `T10YIE`, `DFII10`, `DGS2`, `VIXCLS` → same file | `attach_fred_extras_layer`; `_FRED_EXTRA` injection | same names; per-key `_ASOF`; `FINAL_STATE` preserves T10YIE/DFII10; DGS2 not injected by `_FRED_EXTRA` | Same synthetic daily row issue | No | latest file values; no cap to canonical date |
| I12 | TGA, RRP, WALCL, NET_LIQ | Raw→derived | FRED `WTREGEN`, `RRPONTSYD`, `WALCL` → `liquidity_data.csv`; NET_LIQ computed upstream | `load_liquidity_df` → `attach_liquidity_layer` | `TGA`, `RRP`, `NET_LIQ`, `NET_LIQ_DIR`, `NET_LIQ_LEVEL_BUCKET`, `LIQUIDITY_MOMENTUM`, `_LIQ_ASOF` | File `date`; `_LIQ_ASOF` is latest valid **NET_LIQ** row, not per-component date | No | latest valid NET_LIQ row across whole file; TGA/RRP taken from that row |
| I13 | HY OAS | Raw→derived | FRED `BAMLH0A0HYM2` → `credit_spread_data.csv` | `load_credit_spread_df` → `attach_credit_spread_layer` | `HY_OAS`, `_HY_ASOF`; status derived inside `CROSS_ASSET_TAPE` | Yes: last valid HY row | No | latest valid HY row in whole file, unconstrained by canonical date |
| I14 | Sentiment proxy | Derived persisted | `fetch_sentiment_proxy.py`: VIX z + HY OAS z + HYG/LQD z → `sentiment_proxy.csv` | `attach_sentiment_proxy_layer` | `SENTIMENT.fear_greed/source/as_of` | Yes: row `date` | No | file `iloc[-1]`, unconstrained by canonical date |
| I15 | SP500/US10Y/DXY positioning z | Derived persisted | Yahoo 1y close proxies (`ES=F/SPY/VOO`, `ZN=F/^TNX/TLT`, `DX-Y.NYB/DX=F/UUP`) | `fetch_positioning_center` → `load_positioning_df` → `attach_positioning_layer` | `SP500_POS_Z`, `US10Y_POS_Z`, `DXY_POS_Z`, `_POS_ASOF` | `date` is KST run date, not underlying last market observation | No separate timestamp | latest file row |
| I16 | Dealer gamma bias proxy | Derived persisted | SPY first two option expiries OI + latest VIX; prior snapshot fallback | same positioning producer/loader | `DEALER_GAMMA_BIAS`; producer has `GAMMA_FETCH_OK`, but loader does not inject it | Only positioning run date | No | latest row; may contain previous gamma relabeled with current run date |
| I17 | CTA momentum score | Derived persisted | SPY 1y close vs 50/200DMA; prior snapshot fallback | same positioning producer/loader | `CTA_MOMENTUM_SCORE`; `CTA_FETCH_OK` is not injected | Only positioning run date | No | latest row; may contain previous CTA relabeled with current run date |
| I18 | Positioning slope | Derived | last 2–3 `SP500_POS_Z` snapshots | `get_recent_pos_slope` | `POS_SLOPE` | No dedicated date; inherits snapshots | No | last 2–3 non-null rows, no canonical cap |
| I19 | Live drift tape | Raw→derived intraday | Yahoo 15m/7d and daily/3mo for SPY, CL, DXY, gold, HYG/LQD, EEM/FXI, sectors | `attach_drift_data_layer` → `drift_monitor_filter` | `DRIFT_DATA`, then `DRIFT`, `DRIFT_SCORE`, `DRIFT_STATE` | Source indexes exist only transiently; discarded from `market_data` | No | latest returned bars at report runtime |
| I20 | Pseudo gamma regime | Derived | VIX + drift score + SEW + dealer-gamma proxy | `pseudo_gamma_filter` | `GAMMA_STATE`, `GAMMA_COMBO`, `DEALER_GAMMA_NOTE` | No independent date | No | mixed clocks of I02/I16/I19/I23 |
| I21 | Current institutional flow | Derived | drift, pseudo gamma, SEW, positioning, live HYG/LQD/EEM/FXI/sector validation | `institutional_flow_engine_filter` | `INSTITUTIONAL_FLOW.*` | No independent source date | No | recomputed during daily report from mixed clocks |
| I22 | Previous flow state | Persisted state | `insights/flow_state.json`, written by 10-minute `monitor_sew.py` | `get_flow_state`; flow engine separately calls `load_previous_flow_state` | `FLOW_STATE`, `PREV_FLOW_STATE`, `PREV_FLOW_SCORE`, `PREV_FLOW_TIMESTAMP`; file also has `persistence_days` | `timestamp` exists | Yes: KST wall-clock timestamp | latest committed monitor state; no age check |
| I23 | SEW state | Persisted intraday state | `insights/sew_state.json`, written by `monitor_sew.py` | `get_sew_state` | `SEW_STATE`, `SEW_STATUS`, `SEW_EVENT_TYPE` | `timestamp` exists in file but is **not copied into `SEW_STATE`** | Yes in file | latest state; no age check |
| I24 | Filter15 recovery state | Persisted state | `insights/filter15_state.json`, daily writer | `get_filter15_state` / `save_filter15_state` | `FILTER15_PREV_DEADMAN`, `RECOVERY_*`, `FILTER15_PREV_HY_OAS` | `timestamp` exists and is prior canonical date | Yes, date only | latest file; no age/order validation |
| I25 | Filter18 Rank3D state | Persisted state, deployment-broken | `data/filter18_rank_state.json` | `load_filter18_rank_state` / `save_filter18_rank_state` | accepted/pending rank, count, target weights, `last_processed_date` | `last_processed_date` = KST execution date | No timestamp beyond date | file if present; in audited `main` it is absent and workflow does not stage `data/*.json` |
| I26 | Previous portfolio exposure/weights | Persisted state | `data/paper_portfolio_log.csv` | `load_previous_exposure`, `load_previous_weights` | local `prev_exposure`, `prev_etf_weights` | `date` = KST execution date | No | latest row excluding current KST date |
| I27 | Country ETF prices | Raw persisted | Yahoo EIS/SPY/EEM/EMB/GLD/VXX/FXI/EWJ/BND → `country_etf_data_combined.csv` | root precheck + `attach_country_risk_layer` | `COUNTRY_RISK_*` | `Date` exists | No | **entire file and its final row**, not sliced to canonical date |
| I28 | Sovereign yields/spreads | Raw→derived persisted | FRED country yields → `sovereign_yields.csv` → calendar/ffill spreads | `load_sovereign_spreads_df`; merge and `attach_sovereign_spread_layer` | `*_Y`, `*_SPREAD`, `_SOV_ASOF` | File date; upstream daily calendar/ffill obscures component observation date | No | latest valid per-column row in whole file; merge path ffill to macro dates |
| I29 | Geo EW score | Derived | I03 + I27 + I28 | `attach_geopolitical_ew_layer` | `GEO_EW.score/level/momentum/components` | No independent date | No | macro history ends at canonical date, but sovereign and country loaders have independent latest behavior |
| I30 | Post-F15 geo exposure constraint | Derived | F15 exposure + GEO_EW + transmission signals + `_STALE` | `apply_geo_overlay_to_final_state` | updates `RECOMMENDED_EXPOSURE`; writes `GEO_OVERLAY` | No | No | same run; mixed-source decision |
| I31 | Cross-asset tape / macro narrative / market regime | Derived | core macro histories + HY OAS | `build_cross_asset_tape` → `interpret_macro_narrative` → `map_to_portfolio_regime` → `market_regime_filter` | `CROSS_ASSET_TAPE`, `MACRO_NARRATIVE`, `MARKET_REGIME` | No independent date | No | mixed I02/I13; executed before current flow engine |
| I32 | Policy bias line | Derived | US10Y, DXY, VIX, REAL_RATE, FCI | `policy_filter_with_expectations` | `POLICY_BIAS_LINE` | No independent date | No | mixed canonical and latest-FRED clocks |
| I33 | Structural v2 state | Derived | US10Y, DXY, VIX, WTI, GOLD, REAL_RATE | `structural_filter` | `STRUCT_V2_STATE` | No independent date | No | mixed canonical and latest-FRED clocks |
| I34 | Leadership / positioning participation context | Derived | I06/I07/I09/I15-I17 | `leadership_breadth_filter`; `positioning_stress_filter`; `classify_participation_quality` | `LEADERSHIP_STATE`, `BREADTH_SCORE_18`, `PARTICIPATION_SIGNAL`, `POSITIONING_STATE`, `POSITIONING_SCORE_18`, `GAMMA_SIGNAL`, `VOL_STRUCTURE` | No independent date | No | mixed canonical and positioning-run clocks |
| I35 | F13 risk budget / F15 exposure | Derived decision state | outputs of prior rows | `narrative_engine_filter`; `volatility_controlled_exposure_filter` | `FINAL_STATE`, `RISK_BUDGET`, `RECOMMENDED_EXPOSURE` | No run-manifest date inside object | No | current mixed-clock run |
| S01 | Expectations | Raw live / report-only | Live FRED CPI/PCE/unemployment/payrolls/FEDFUNDS/T10YIE | `fetch_expectation_data` → `attach_expectation_layer` | `EXPECTATIONS`, `_EXP_ASOF` | Per-series `asof` and max `_EXP_ASOF` | No | latest live; **policy logic only displays receipt, does not apply it** |
| S02 | Growth sustainability | Derived shadow | macro + FRED file direct read | `growth_sustainability_filter` | report text only | `_GROWTH_ASOF`; FRED lookup capped to it | No | report-only; no F13/F15/F18 effect |
| S03 | PM 1-day sector snapshot | Derived display | macro sector prices | `attach_pm_sector_snapshot` | `PM_SECTOR_SNAPSHOT` | inherits canonical row | No | report-only |
| S04 | SPY/QQQ/TLT options GEX shadow | Raw/derived shadow | Yahoo/CBOE option chains → JSON | `fetch_spy_gex_shadow.py`; site reader only | no decision `market_data` key | Report-date contract in JSON | snapshot metadata varies; not audited as decision clock | UI only; no decision consumer |
| N01 | `fred_macro_extras.csv` duplicate | Raw NON-PRODUCTION | FRED NFCI/DFII10 | `fetch_fred_macro_extras.py` | none in Production decision loader | `date` exists but no ffill | No | workflow writes it, but generator reads `fred_macro_sctorallo.csv` instead |
| S05 | ACM term premium; CPI/PCE/GDP event context | Raw/report-only | NY Fed / web event sources | attached after all decision logic | `ACM_TERM_PREMIUM`, `*_EVENT_CONTEXT` | varies | varies/UNKNOWN | report only |

### 2B. Missing behavior, consumer, impact, authority, evidence, and clock class

| ID | Missing-data behavior | Consumer | Decision impact | Production authority? | Code evidence | Clock risk |
|---|---|---|---|---|---|---|
| I01 | Macro file/valid date absence: **STOP/exception**. If 4/5 core unavailable, falls back to any-core row; stale macro date: **STOP** | pre-filter | direct | YES, root clock | `generate_report.py:908-1003,2422-2454,2619-2647` | STRICT DAILY |
| I02 | Missing cell omitted; downstream helpers usually neutral/UNKNOWN; US10Y upstream may use FRED fallback | F13, F15, F18, pre-filter | direct | YES | `generate_report.py:1738-1806`; `strategist_filters.py:449-541,3859-4433,4621-5027,5904-6209` | STRICT DAILY |
| I03 | Missing component skipped; geo weights renormalize over available inputs; structural missing becomes neutral | F13 structural; geo post-F15 | direct/indirect | YES | `strategist_filters.py:2372-2729,3739-3850` | STRICT DAILY |
| I04 | Daily missing omitted; live failure gives `{}` and silently continues | pre-filter / current flow | indirect | YES | `strategist_filters.py:2990-3155,8083-8267` | STRICT DAILY + INTRADAY |
| I05 | Missing returns become `None`; correlation rule silently does not trigger | F18 correlation control | indirect | YES | `strategist_filters.py:906-979,1008-1105,6519-6550` | STRICT DAILY |
| I06 | Missing values become **0.0** for today/prev/prev2 | flow-authenticity, leadership context, F18 | indirect/direct | YES | `generate_report.py:1076-1136`; `flow_authenticity.py:28-141` | STRICT DAILY |
| I07 | Missing values become **0.0** | F15 leadership offset; F18 participation | direct | YES | `generate_report.py:1153-1214`; `leadership_breadth.py:26-213`; `strategist_filters.py:4831-4843` | STRICT DAILY |
| I08 | Missing ticker/lookback/benchmark becomes **0 score** | F18 | direct | YES | `generate_report.py:1331-1400`; `strategist_filters.py:6281-6304` | STRICT DAILY |
| I09 | Missing becomes **0.0**; downstream maps missing term structure to `COMPRESSION` | F18 participation | direct | YES | `generate_report.py:1295-1328`; `positioning_stress.py:30-216` | STRICT DAILY |
| I10 | Missing uses Treasury fallback where available; FCI has no Treasury fallback and remains absent; silent continuation | F13 policy; F18 curve | direct | YES | `generate_report.py:1515-1623,2738-2755`; `treasury_fallback.py:16-57` | LAGGED / RELEASE-SCHEDULED |
| I11 | Attach skips/uses fallback; `_FRED_EXTRA` converts missing T10Y2Y/T10YIE/DFII10 to **0.0** | preserved F13 state / report; T10Y2Y overlaps I10 | mostly display, T10Y2Y direct | PARTIAL | `generate_report.py:1664-1695,2738-2749`; `strategist_filters.py:8593-8629` | LAGGED / RELEASE-SCHEDULED |
| I12 | Empty/missing → `None` and `N/A`; silently continues | F13; F18 through FINAL_STATE; pre-filter | direct | YES | `generate_report.py:1810-2090`; `strategist_filters.py:3926-3934,4002-4011,6040-6042` | LAGGED / RELEASE-SCHEDULED |
| I13 | Empty/missing → `_HY_ASOF=None`, no HY key; downstream credit becomes UNKNOWN/neutral; silently continues | F13, F15, F18 | direct | YES | `generate_report.py:2093-2139`; `strategist_filters.py:473-497,3920-3924,4678-4680` | LAGGED / RELEASE-SCHEDULED |
| I14 | Missing/file error → no `SENTIMENT`; F13 uses base **50** (`N/A`) | F13 | direct | YES | `generate_report.py:2266-2299`; `strategist_filters.py:3916-3918,3979-3987` | STRICT DAILY |
| I15 | Empty/missing → z scores **0.0 neutral** | F13, current flow, F15, F18 | direct | YES | `generate_report.py:2219-2261`; `strategist_filters.py:3956-3958,4660-4662,8105-8109` | INTRADAY / run-date proxy |
| I16 | Producer failure → previous value, else **1.0 neutral**; loader defaults 1.0; success flag not consumed | pseudo gamma, F15, F18 | direct | YES | `fetch_positioning_data.py:228-321`; `generate_report.py:2228-2259`; `strategist_filters.py:4670-4672` | STATEFUL + INTRADAY |
| I17 | Producer failure → previous value, else **0.0**; F15 missing then defaults **1.0** | F15, F18 | direct | YES | `fetch_positioning_data.py:323-375`; `strategist_filters.py:4674-4676`; `positioning_stress.py:55-57` | STATEFUL + INTRADAY |
| I18 | Missing/error → **0.0** | F15 | direct | YES | `fetch_positioning_data.py:64-85`; `generate_report.py:2687-2690`; `strategist_filters.py:4664-4668` | STATEFUL |
| I19 | Per-ticker failure → empty dict; filter converts many missing 1D returns to **0** | drift, current flow, F13/F18 | direct/indirect | YES | `strategist_filters.py:2990-3155,586-774,8083-8267` | INTRADAY |
| I20 | Missing inputs become UNKNOWN/defaults and continue | current flow, F13, F18 | indirect | YES | `strategist_filters.py:3393-3509` | UNKNOWN (mixed clock) |
| I21 | Missing components default mostly to 0/N/A; silently continues | F13, F15, F18 | direct | YES | `strategist_filters.py:8083-8334` | UNKNOWN (mixed clock) |
| I22 | Missing/corrupt → `N/A`, score **0**, timestamp None; no freshness rejection | current flow transition; F13 continuity | direct | YES | `generate_report.py:754-778,2788-2793`; `strategist_filters.py:8301-8317` | STATEFUL |
| I23 | Missing/corrupt → N/A/false/zero; no freshness rejection | pseudo gamma, current flow, geo transmission | indirect/direct | YES | `generate_report.py:869-903,2760-2782`; `strategist_filters.py:3430-3502,8102-8103` | INTRADAY + STATEFUL |
| I24 | Missing/corrupt → safe defaults; recovery state resets; no freshness rejection | F15 | direct | YES | `generate_report.py:781-866,2795-2841`; `strategist_filters.py:4885-4976` | STATEFUL |
| I25 | Missing/corrupt → default empty state → `INITIAL_ACCEPT`; save failure only logs warning | F18 | direct | **YES in code, not durable in deployed workflow** | `save_portfolio.py:269-404`; `strategist_filters.py:6960-7243,7754-7774`; workflow `349-356` | STATEFUL |
| I26 | Missing/corrupt → previous exposure **50.0**, weights `{}` | F18 deleveraging/rebalance/trades | direct | YES | `save_portfolio.py:184-267`; `strategist_filters.py:6885-6892,7270-7280` | STATEFUL |
| I27 | File missing triggers download; empty file causes report **STOP**. Individual missing ETFs are skipped | precondition; geo post-F15/report | indirect/direct | YES | `generate_report.py:2589-2600`; `strategist_filters.py:2204-2284` | STRICT DAILY but uncapped latest |
| I28 | Missing file/column returns empty; geo/spread attachment silently skips; ffill uses prior values | geo post-F15 | indirect/direct | YES | `generate_report.py:2318-2420`; `strategist_filters.py:2372-2477` | LAGGED / RELEASE-SCHEDULED |
| I29 | Missing components skipped and weights renormalized; exceptions broadly swallowed | geo post-F15 | indirect/direct | YES | `strategist_filters.py:2372-2729` | UNKNOWN (mixed clock) |
| I30 | If no transmission signal, WATCH_ONLY; missing exposure does nothing | final exposure before F18 | direct | YES | `strategist_filters.py:7942-8078` | UNKNOWN (mixed clock) |
| I31 | Missing HY → UNKNOWN; insufficient histories → z UNKNOWN; other missing directions become neutral | F13, F15, F18 | direct | YES | `strategist_filters.py:304-541,1391-1444` | UNKNOWN (mixed daily/release) |
| I32 | Missing FCI/real deltas contribute nothing; expectations do not affect rule | F13 | direct | YES | `strategist_filters.py:1615-1786` | UNKNOWN (mixed daily/release) |
| I33 | Missing values simply prevent triggers; neutral state | F13 | direct | YES | `strategist_filters.py:3739-3850` | UNKNOWN (mixed daily/release) |
| I34 | Missing breadth/vol/positioning has numeric defaults that map to valid-looking states | F15/F18 | direct | YES | `leadership_breadth.py:26-213`; `positioning_stress.py:30-216`; `participation_quality.py:85-143` | UNKNOWN (mixed daily/run-date) |
| I35 | F15 missing F13 budget → **50**; F18 missing exposure → **50** | F15/F18/final allocation | direct | YES | `strategist_filters.py:4652-4654,6861-6881` | UNKNOWN (run composite) |
| S01 | Fetch error records `_EXP_ERROR`; silently continues | policy report only | display only | SHADOW / REPORT ONLY | `generate_report.py:2142-2217`; `strategist_filters.py:1760-1769` | LAGGED / RELEASE-SCHEDULED |
| S02 | Exceptions become “missing/error” in report | report only | display only | SHADOW | `growth_sustainability.py:55-204` | LAGGED / RELEASE-SCHEDULED |
| S03 | Missing → empty list | PM report | display only | SHADOW | `generate_report.py:1402-1501` | STRICT DAILY |
| S04 | Workflow is `continue-on-error`; no engine reader | Pages UI | display only | SHADOW / NON-PRODUCTION DECISION | workflow `176-198`; `build_pm_site.py:1695-1790` | INTRADAY snapshot |
| N01 | Producer keeps old file or empty skeleton; no decision reader | none | none | NON-PRODUCTION duplicate | `fetch_fred_macro_extras.py:98-179`; decision loader `generate_report.py:1005-1021` points elsewhere | LAGGED / RELEASE-SCHEDULED |
| S05 | Fetch failures are handled by adapters; attached after decisions | PM report | display only | REPORT ONLY | `generate_report.py:3023-3055` | UNKNOWN |

## 3. Exact F13 → F15 → F18 consumer map

### F13 — `narrative_engine_filter`

Directly reads:

- `STRUCT_V2_STATE`, `POLICY_BIAS_LINE`
- `SENTIMENT.fear_greed`
- `HY_OAS.today`
- `NET_LIQ.pct_change/level_bucket`
- `MARKET_REGIME`, `MACRO_NARRATIVE`, `CROSS_ASSET_TAPE`
- `SP500_POS_Z`
- `VIX.today/pct_change`
- `DRIFT` / fallback `DRIFT_SCORE`, `DRIFT_STATE`
- `INSTITUTIONAL_FLOW.score/state/confidence`
- `GAMMA_STATE`
- `PREV_FLOW_STATE`, `PREV_FLOW_SCORE`

It writes `RISK_BUDGET` and `FINAL_STATE` at `strategist_filters.py:4310-4408`. The direct reads and fallbacks are at `3913-3973`, `4021-4049`, and `4088-4168`.

### F15 — `volatility_controlled_exposure_filter`

Directly reads:

- F13 `RISK_BUDGET`
- macro `VIX.today/pct_change`
- positioning `SP500_POS_Z`, `POS_SLOPE`, `DEALER_GAMMA_BIAS`, `CTA_MOMENTUM_SCORE`
- `HY_OAS.today/pct_change`
- `INSTITUTIONAL_FLOW.score`
- `MACRO_NARRATIVE`, `CROSS_ASSET_TAPE.VIX_Z`
- `LEADERSHIP_BREADTH_SCORE`
- F15 persistent recovery keys

It writes `RECOMMENDED_EXPOSURE` and overwrites `SEW_STATUS` with the F15 status at `strategist_filters.py:4965-4976`. This is important: the original intraday SEW status has already been replaced before the geo constraint runs.

### Post-F15 geo constraint

`apply_geo_overlay_to_final_state` may reduce `RECOMMENDED_EXPOSURE` before F18. However, actual runtime transmission checks are narrower than they look:

- `float(market_data.get("VIX"))` receives a dict and fails, so the VIX transmission branch is normally unavailable (`7968-7975`).
- `HY_OAS_STATUS` is stored inside `CROSS_ASSET_TAPE`, not as a flat key or `FINAL_STATE.HY_OAS_STATUS`, so this branch is normally unavailable (`7980-7986`).
- `FLOW_SIGNAL` is written only by statically uncalled `detect_flow_signal`, so this branch is normally absent (`7988-7990`; writer `231-257`).
- `SEW_STATUS` was overwritten by F15 to `NORMAL`, `HARD_DEADMAN`, etc.; it no longer carries original `WATCH/ALERT/DEADMAN` semantics (`7992-7998` vs F15 `4967-4969`).
- The live drift label is therefore the clearly reachable transmission confirmation path (`8000-8007`).

This does not make country/sovereign data non-production: they still determine `GEO_EW.level`, which sets the penalty magnitude if a reachable transmission signal exists.

### F18 — `sector_allocation_filter`

Directly consumes:

- F13 `FINAL_STATE.phase/liquidity_dir/liquidity_level_bucket/credit_calm`
- T10Y2Y, VIX, US10Y/DXY/WTI changes
- current institutional flow / drift label / gamma state
- 11-sector `MOMENTUM_SCORES`
- correlation-break inputs from macro daily returns
- leadership/positioning participation context
- post-geo `RECOMMENDED_EXPOSURE`
- prior portfolio exposure/weights
- Rank3D persisted state

Core reads are at `strategist_filters.py:5919-6065,6281-6342,6519-6550,6861-6958,6960-7243`. Execution ceiling and final ETF mapping are at `7454-7700`.

## 4. Production Clock Registry V0

| Clock class | Inputs | Registry rule actually observable today |
|---|---|---|
| STRICT DAILY | I01-I09, I14, I27, S03 | Expected to align to a market date. Only I01 has a validation stop. I06/I07 explicitly carry canonical-row tags. Other families inherit or independently choose a last row. |
| LAGGED / RELEASE-SCHEDULED | I10-I13, I28, S01, S02, N01 | FRED/sovereign/liquidity/credit series can lag and be revised. Production does not retain vintage or availability time. Daily skeleton/ffill frequently makes the visible row date later than the true observation date. |
| INTRADAY | I19, parts of I04/I15-I17, I23, S04 | Values can be later than the canonical close. Live drift discards bar timestamps; positioning stamps run date; SEW preserves a wall-clock timestamp but daily engine does not validate it. |
| STATEFUL | I16-I18, I22-I26 | Previous values affect decisions. F15 and flow states persist; F18 Rank3D is coded but not transported; portfolio state uses KST execution date. |
| UNKNOWN | I20-I21, I29-I35, S05 | Derived objects mix multiple clocks and carry no authoritative composite as-of or provenance manifest. |

### Audited-commit clock snapshot

Canonical `data_as_of_date` from the current Production data is **2026-10-07**. The actual committed inputs show:

| Family | File max date / timestamp | Latest valid value date visible in file | Relation to canonical clock |
|---|---|---|---|
| macro core/breadth/leadership/sectors | 2026-10-07 | all inspected macro columns 2026-10-07 | aligned |
| liquidity | file calendar to 2026-10-08 | NET_LIQ/TGA/WALCL 2026-09-30; RRP 2026-10-07 | lagged; `_LIQ_ASOF` becomes 2026-09-30 and hides newer RRP clock |
| HY OAS | file calendar to 2026-10-08 | 2026-10-06 | lagged |
| FRED `sctorallo` | 2026-10-08 | all fields non-null at 2026-10-08 because of `ffill()` | **future row vs canonical; true source dates lost** |
| positioning | 2026-10-08 | 2026-10-08 run-date row | future/run-date clock vs canonical |
| sentiment | 2026-10-07 | 2026-10-07 | aligned |
| sovereign spreads | 2026-10-08 | most fields non-null at 2026-10-08 through upstream ffill | future/synthetic row vs canonical |
| country ETF | 2026-10-07 | 2026-10-07 | aligned in this snapshot, but loader is uncapped |
| SEW | `2026-10-08 16:13:21 KST` | same | intraday, later than canonical |
| flow | `2026-10-08 16:13:21 KST` | state `CONFIRMED_FLOW`, `persistence_days=8` | intraday/stateful, later than canonical |
| F15 state | timestamp `2026-10-07` | previous HY 3.03 | aligned to prior canonical date, but not freshness-checked |
| F18 Rank3D | file absent | none | state clock unavailable in deployed clean-run model |
| paper portfolio | latest row 2026-10-08 | 2026-10-08 execution snapshot | execution-day clock, not canonical market date |

## 5. Cross-Clock Risk Register

### P0

| Risk | Proof | Decision consequence |
|---|---|---|
| Auxiliary latest rows are not capped at `data_as_of_date` | FRED uses `valid_df.iloc[-1]` and `_FRED_EXTRA` uses `df.iloc[-1]`; HY, liquidity, sovereign, positioning, sentiment, and country ETF loaders likewise select their own latest rows. Current run combines canonical 2026-10-07 with FRED/positioning/sovereign 2026-10-08 rows. | A decision labeled “Data as of 2026-10-07” can consume information from a later execution date. |
| FRED/sovereign forward-fill destroys true observation-date semantics | `fred_data_fetcher.py:34-53` creates daily rows through today and forward-fills every series. Sovereign producers create daily calendars and ffill before spread calculation. | A future-looking validation gate cannot distinguish a genuine 2026-10-08 release from an older weekly/monthly observation copied into a 2026-10-08 row. |
| F18 Rank3D state clock is not durable | State path is `data/filter18_rank_state.json`; current `main` has no file; workflow stages `data/*.csv`, not `data/*.json`. | Every clean runner can re-enter initial state. The intended 3-trading-day clock is not the deployed clock. |

### P1

| Risk | Proof | Decision consequence |
|---|---|---|
| Canonical clock is not propagated into the decision object | `data_as_of_date` remains local; no `_DATA_ASOF` assignment exists. | Loaders/filters cannot enforce a common clock contract even if they expose `_ASOF` fields. |
| Live drift has no retained source or retrieval timestamp | Yahoo indexes are used to compute returns, then discarded from `DRIFT_DATA`. | The same canonical daily input can produce different F13/F18 decisions on rerun; exact replay is impossible. |
| Positioning `date` conflates retrieval date and observation date | Producer stamps `datetime.now()` while underlying closes/options may be from different market times; failed gamma/CTA can reuse prior values under the new date. | Stale prior data can appear current and pass any date-only gate. |
| State freshness is unchecked | Flow, SEW, and F15 readers expose timestamps/defaults but reject neither old nor future state. | Old intraday or recovery state can directly affect F13/F15. |
| Flow “persistence_days” is an intraday-run counter | 10-minute monitor writes/updates flow state; daily flow engine reads it. | The label “days” is not a trading-day clock and can advance many times in one day. |
| F18 uses KST execution date, not canonical market date | `today_rank_date = Timestamp.now(Asia/Seoul)`; paper portfolio also uses execution date. | Same market observation run on different KST dates can advance Rank3D/portfolio state differently. |
| Per-component dates are collapsed | `_LIQ_ASOF` tracks NET_LIQ only; `_SOV_ASOF` tracks latest-any row; file-level FRED date is synthetic. | A family-level clock can mask component-level lag or future rows. |
| Geo overlay mixes clocks and loses original SEW semantics | Country/sovereign/macro/live drift are mixed; F15 overwrites `SEW_STATUS` before overlay. | The executable post-F15 constraint is not reproducible from a single as-of and does not consume all apparent transmission signals as intended. |

### P2

| Risk | Proof | Decision consequence |
|---|---|---|
| Macro row validity is 4-of-5, not per-field clock completeness | `_find_effective_market_idx` accepts four core columns. | One missing core field can silently become neutral/absent while the date is accepted. |
| Country ETF last row is uncapped | `attach_country_risk_layer` ignores `today_idx` and uses the whole file. | It is aligned today but can run ahead of canonical macro data on another day. |
| Expectations have clocks but are non-decision today | `_EXP_ASOF` exists; policy filter displays receipt only. | No current decision risk, but promoting this layer without a gate would add mixed monthly/daily clocks. |
| Duplicate FRED outputs obscure authority | Workflow writes both `fred_macro_extras.csv` and `fred_macro_sctorallo.csv`; Production reads only the latter. | Operators may validate the wrong file or assume a clock safeguard that is not authoritative. |
| Missing values become valid-looking states | Breadth/leadership/VIX term structure use zeros; positioning uses neutral/prior; F18 has default context states. | Clock absence is not distinguishable from a genuine neutral observation. |

## 6. Hidden-clock and missing-data findings

### Verified latest-row patterns

- Macro selector: last row meeting 4/5 core validity (`generate_report.py:2419-2454`).
- FRED extras: per-series `valid_df.iloc[-1]` (`1569-1580`) and second load `df_fred_extra.iloc[-1]` (`2738-2749`).
- Liquidity: `valid_liq_df.iloc[-1]` (`1876-1903`).
- HY OAS: `valid_df.iloc[-1]` (`2118-2128`).
- Positioning: `pos_df.iloc[-1]` (`2244-2245`).
- Sentiment: `df.iloc[-1]` (`2288-2298`).
- Sovereign: latest-any and per-column last valid rows (`2376-2394`).
- Country ETF: calculations run on the full sorted file; latest z/crash is based on its tail (`strategist_filters.py:2214-2276`).
- Live drift: latest 15m/daily close (`3113-3127`).
- Previous portfolio: latest row excluding current KST date (`save_portfolio.py:184-267`).

### Verified silent neutral/zero/previous-value behavior

- Breadth and leadership missing observations → `0.0`.
- VIX3M/VIX9D missing → `0.0`; positioning layer then maps missing term structure to `COMPRESSION`.
- Sector momentum missing/lookback failure → score 0.
- Positioning z missing → 0.0.
- Dealer gamma/CTA fetch failure → previous value; if no previous value → 1.0/0.0.
- Live drift per-ticker failure → `{}`; many downstream reads become 0.
- Flow/SEW missing state → N/A/0/false.
- F15 state missing/corrupt → default non-recovery state.
- F18 state missing/corrupt → empty state and initial accept.
- Previous portfolio missing → exposure 50 and empty weights.

## 7. ORPHAN / SHADOW / NON-PRODUCTION classification

| Item | Classification | Reason |
|---|---|---|
| SPY/QQQ/TLT options GEX JSON | SHADOW | Workflow produces it, Pages reads it, no F13/F15/F18 reader exists. |
| `fred_macro_extras.csv` | NON-PRODUCTION duplicate | Workflow producer exists; authoritative loaders read `fred_macro_sctorallo.csv`. |
| Expectations | SHADOW / REPORT ONLY | Attached before filters, but policy explicitly applies no event-surprise logic. |
| Growth sustainability | SHADOW / REPORT ONLY | Function states and code path show no mutation consumed by F13/F15/F18. |
| PM sector snapshot | SHADOW / DISPLAY ONLY | Attached from the same macro data, explicitly not consumed by allocation. |
| ACM term premium | REPORT ONLY | Attached after all decision logic. |
| CPI/PCE/GDP event context | REPORT ONLY | Attached after all decision logic. |
| `data/filter18_rank_state.json` | ORPHANED DEPLOYMENT STATE | Has real F18 reader/writer, but is absent and not transported by workflow staging. It is not logically orphaned; it is operationally orphaned. |
| Macro V4/backtest artifacts | NON-PRODUCTION | No call from the audited daily root. |

## 8. Coverage Check

Coverage was checked in four directions:

1. **Forward from workflow:** every producer invoked before `generate_report.py` was mapped to an engine reader or classified SHADOW/NON-PRODUCTION.
2. **Forward from generator:** every `attach_*`, state reader, and precondition called by `generate_daily_report` was traced to its produced keys and consumers.
3. **Backward from decisions:** direct `market_data.get` / subscript reads in F13, F15, geo overlay, F18, and F18 helper calls were traced back to a writer/default/source.
4. **Persistence reverse check:** every F15/F18/portfolio/flow/SEW state reader was matched to its writer and workflow transport rule.

### Coverage matrix

| Decision stage | Direct input families covered | Unresolved source lineage |
|---|---|---|
| F13 | structure, policy, sentiment, credit, liquidity, regime/tape, VIX, positioning, drift, current/previous flow, pseudo gamma | none statically; true external publication/retrieval timestamps remain UNKNOWN |
| F15 | F13 budget, VIX, positioning/slope/gamma/CTA, HY OAS, flow, macro narrative/tape, leadership, F15 state | none statically; positioning observation time and state freshness remain UNKNOWN |
| Geo constraint | F15 exposure, Geo EW, stale flag, VIX/HY/flow/SEW/drift transmission | all readers found; several apparent transmission branches are not reachable with their expected semantics |
| F18 | phase/liquidity/credit, curve/VIX/core returns, flow/drift/gamma, momentum, correlation, participation, exposure, prior portfolio, Rank3D | none statically; deployed Rank3D state itself is absent |
| Final/report | F13/F15/F18 outputs, final action/decision, display-only enrichments | external report-only retrieval metadata varies and is not decision-critical |

**Coverage conclusion:** the static Production decision-input inventory is sufficiently complete for the audited commit. The remaining UNKNOWNs concern temporal provenance and actual external responses, not unidentified code-level input families.

## 9. Verdict

### Is the Production decision input inventory sufficiently complete?

**Yes for static code and repository lineage, with a clear boundary.** Every reachable raw, derived, and persisted input to F13→F15→geo→F18 has been mapped, and workflow-produced non-consumers were classified. It is **not** a complete runtime replay manifest because the repository does not retain live API payloads, retrieval times, true FRED publication/vintage dates, or live drift bar timestamps.

### Is the system ready to design a cross-clock validation gate?

**Ready to define the gate contract, but not ready to enforce a correctness gate against current fields.** A safe design can now specify required metadata and clock classes. Enforcement should be postponed until observation date, available-at/publication time, retrieval time, fallback/stale flag, and canonical run date are separately representable. Today, forward-filled dates and run-date stamps would cause both false passes and false failures.

### Are there UNKNOWN inputs that require gate design to be postponed?

**Yes.** The blocking UNKNOWNs are:

- true source observation/publication/vintage dates behind forward-filled FRED and sovereign rows;
- live drift bar as-of and retrieval timestamp after aggregation;
- actual underlying observation dates for positioning proxies and reused gamma/CTA values;
- freshness/ordering contract for SEW, flow, and F15 state;
- any external restoration mechanism for F18 Rank3D state (none exists in repository workflows);
- actual external API responses/fallback branches used in a given Actions run.

These UNKNOWNs do not prevent writing a registry schema; they prevent treating current `date` fields as a reliable enforcement basis.

### First three clock risks to fix

1. **Separate and preserve `observation_date`, `available_at/publication_time`, and `retrieved_at` for every authoritative input; stop using forward-filled calendar dates as source dates.** This is the prerequisite for all other clock validation.
2. **Propagate one canonical `data_as_of_date` into the decision object and cap/validate every authoritative loader against it, with explicit exemptions for named intraday overlays.** The current latest-row behavior demonstrably mixes 2026-10-07 and 2026-10-08.
3. **Make state clocks explicit and durable: validate SEW/flow/F15 freshness and order, use the canonical trading date for Rank3D advancement, and restore durable transport for `filter18_rank_state.json`.** Without this, repeated or clean-run executions do not share the intended state timeline.

## 10. Final concise answer

GCF Production does not currently have one decision clock. It has a guarded macro close clock, multiple independent latest-observation clocks, live intraday clocks, and several state clocks. F13 consumes macro/FRED/liquidity/credit/sentiment/positioning/live-flow mixtures; F15 adds persisted recovery state; geo may constrain the F15 output; F18 adds sector, participation, portfolio, and Rank3D state. The static input inventory is complete enough to define Clock Registry V0, but a validation gate should remain non-enforcing until temporal provenance is preserved. The most urgent problems are uncapped auxiliary latest rows, synthetic forward-filled source dates, and non-durable/unvalidated state clocks.
