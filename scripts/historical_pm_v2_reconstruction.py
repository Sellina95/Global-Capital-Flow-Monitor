from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
PARITY_PATH = ROOT / "data/backtest/results/final_13_15_18_parity_closeout/final_13_15_18_parity_daily.csv"
CONTRACT_ID = "GCF_HISTORICAL_PM_V2_RECONSTRUCTION_V1"
UNAVAILABLE = "Unavailable"


@dataclass(frozen=True)
class FieldSpec:
    key: str
    section: str
    label: str
    aliases: tuple[str, ...] = ()


# Every scalar field read by the current PM V2 renderer. Variable sector and
# F19 rows are inventoried separately in each reconstruction record.
FIELD_SPECS = (
    FieldSpec("decision.action", "top", "PORTFOLIO STANCE", ("Final Action", "Action", "Risk Stance")),
    FieldSpec("decision.regime", "top", "REGIME", ("Operational Phase", "Current Regime", "Phase")),
    FieldSpec("decision.conviction", "top", "CONVICTION", ("Confidence",)),
    FieldSpec("f13.risk_budget", "DECISION PATH", "Strategic Risk Budget", ("Risk Budget (0~100)",)),
    FieldSpec("f15.recommended_exposure", "DECISION PATH", "Recommended Exposure", ("📊 Recommended Exposure",)),
    FieldSpec("f18.exposure_ceiling", "DECISION PATH", "Exposure Ceiling"),
    FieldSpec("f18.allocated_equity", "DECISION PATH", "Allocated Equity"),
    FieldSpec("f18.tactical_reserve", "DECISION PATH", "Tactical Reserve", ("Tactical Reserve (Cap / Unallocated)",)),
    FieldSpec("f18.cash", "DECISION PATH", "Cash"),
    FieldSpec("f15.exposure_control", "DECISION PATH", "Exposure Control"),
    FieldSpec("f18.macro_allocation", "DECISION PATH", "Macro Allocation", ("Macro Profile",)),
    FieldSpec("executive.macro_narrative", "EXECUTIVE VIEW", "Macro Narrative"),
    FieldSpec("executive.tactical_signal", "EXECUTIVE VIEW", "Tactical Signal", ("Tactical Action",)),
    FieldSpec("market.macro_narrative", "MARKET STATE", "Macro Narrative"),
    FieldSpec("market.policy_bias", "MARKET STATE", "Policy Bias"),
    FieldSpec("market.financial_conditions", "MARKET STATE", "Financial Conditions", ("현실(FCI)",)),
    FieldSpec("market.real_rate", "MARKET STATE", "Real Rate", ("유인(Real Rates)",)),
    FieldSpec("market.liquidity", "MARKET STATE", "Liquidity"),
    FieldSpec("market.liquidity_level", "MARKET STATE", "Liquidity Level", ("NET_LIQ level",)),
    FieldSpec("market.dollar_liquidity", "MARKET STATE", "Dollar Liquidity"),
    FieldSpec("market.fed_plumbing", "MARKET STATE", "Fed Plumbing"),
    FieldSpec("market.structure", "MARKET STATE", "Structure"),
    FieldSpec("market.growth", "MARKET STATE", "Growth Sustainability"),
    FieldSpec("market.flow", "MARKET STATE", "Institutional Flow", ("Flow",)),
    FieldSpec("market.flow_authenticity", "MARKET STATE", "Flow Authenticity"),
    FieldSpec("market.participation_quality", "MARKET STATE", "Participation Quality"),
    FieldSpec("market.participation_mode", "MARKET STATE", "Participation Mode"),
    FieldSpec("market.leadership", "MARKET STATE", "Leadership"),
    FieldSpec("market.positioning", "MARKET STATE", "Positioning"),
    FieldSpec("market.dealer_gamma", "MARKET STATE", "Dealer Gamma", ("Gamma",)),
    FieldSpec("market.squeeze_risk", "MARKET STATE", "Squeeze Risk"),
    FieldSpec("market.vol_structure", "MARKET STATE", "Vol Structure"),
    FieldSpec("market.positioning_z", "MARKET STATE", "Positioning Z", ("POS_Z",)),
    FieldSpec("market.credit", "MARKET STATE", "Credit"),
    FieldSpec("market.credit_structure", "MARKET STATE", "Credit Structure"),
    FieldSpec("market.drift", "MARKET STATE", "Drift"),
    FieldSpec("cross.us10y", "CROSS-ASSET CONFIRMATION", "US10Y Yield", ("미국 10년물 금리",)),
    FieldSpec("cross.usd", "CROSS-ASSET CONFIRMATION", "USD", ("달러 인덱스",)),
    FieldSpec("cross.oil", "CROSS-ASSET CONFIRMATION", "Oil", ("WTI 유가",)),
    FieldSpec("cross.vix", "CROSS-ASSET CONFIRMATION", "Volatility", ("변동성 지수 (VIX)", "VIX Level")),
    FieldSpec("cross.hy_oas", "CROSS-ASSET CONFIRMATION", "HY OAS", ("HY_OAS level",)),
    FieldSpec("leadership.coverage", "LEADERSHIP & PARTICIPATION", "Coverage"),
    FieldSpec("allocation.growth_value", "ALLOCATION CONTEXT", "Growth vs Value"),
    FieldSpec("allocation.duration_tilt", "ALLOCATION CONTEXT", "Duration Tilt"),
    FieldSpec("allocation.cyclical_defensive", "ALLOCATION CONTEXT", "Cyclical Defensive"),
    FieldSpec("allocation.duration_factor", "ALLOCATION CONTEXT", "Duration Factor"),
    FieldSpec("allocation.inflation_factor", "ALLOCATION CONTEXT", "Inflation Factor"),
    FieldSpec("allocation.usd_factor", "ALLOCATION CONTEXT", "USD Factor"),
    FieldSpec("allocation.credit_factor", "ALLOCATION CONTEXT", "Credit Factor"),
    FieldSpec("f18.regime_controller", "ALLOCATION CONTEXT", "Regime Controller"),
    FieldSpec("f18.exposure_override", "ALLOCATION CONTEXT", "Exposure Override"),
    FieldSpec("constraint.exposure_control", "ACTIVE CONSTRAINTS", "Exposure Control"),
    FieldSpec("constraint.squeeze_risk", "ACTIVE CONSTRAINTS", "Squeeze Risk"),
    FieldSpec("constraint.vol_structure", "ACTIVE CONSTRAINTS", "Vol Structure"),
    FieldSpec("constraint.correlation_break", "ACTIVE CONSTRAINTS", "Correlation Break"),
    FieldSpec("constraint.sector_corr_break", "ACTIVE CONSTRAINTS", "Sector Corr Break"),
    FieldSpec("constraint.rank_control", "ACTIVE CONSTRAINTS", "Rank Control"),
    FieldSpec("constraint.geopolitical", "ACTIVE CONSTRAINTS", "Geopolitical"),
    FieldSpec("rationale.decision", "DECISION RATIONALE", "Decision", ("Final Action", "Action")),
    FieldSpec("rationale.exposure", "DECISION RATIONALE", "Exposure Ceiling", ("Final Exposure",)),
    FieldSpec("rationale.tactical_signal", "DECISION RATIONALE", "Tactical Signal", ("Tactical Action",)),
    FieldSpec("rationale.conviction", "DECISION RATIONALE", "Conviction", ("Confidence",)),
)

COMPATIBLE_SECTIONS = {
    "f18.exposure_ceiling": ("PORTFOLIO ALLOCATION", "DECISION RATIONALE"),
    "f18.allocated_equity": ("PORTFOLIO ALLOCATION",),
    "f18.tactical_reserve": ("PORTFOLIO ALLOCATION",),
    "f18.cash": ("PORTFOLIO ALLOCATION",),
    "rationale.exposure": ("PORTFOLIO ALLOCATION",),
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _clean(value: str) -> str:
    value = value.strip().replace("**", "").replace("*", "").strip("` ")
    return re.sub(r"\s+", " ", value)


def _metadata(text: str, label: str) -> str:
    match = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$", text, re.MULTILINE)
    return _clean(match.group(1)) if match else ""


def _section(text: str, title: str) -> str:
    match = re.search(rf"^\d+\.\s+{re.escape(title)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    tail = text[match.end():]
    following = re.search(r"^\d+\.\s+[A-Z][A-Z &\-]+\s*$", tail, re.MULTILINE)
    return tail[:following.start()].strip() if following else tail.strip()


def _explicit_label(text: str, label: str) -> str:
    # Only literal labelled lines are accepted. Prose and unlabeled numeric
    # guesses never become historical state.
    decorated = rf"\**{re.escape(label)}\**"
    patterns = (
        rf"(?im)^\s*(?:[-*•]\s*)?{decorated}\s*:\s*\**(.+?)\**\s*$",
        rf"(?im)^\s*(?:[-*•]\s*)?{decorated}[ \t]+\**(.+?)\**\s*$",
        rf"(?im)^\s*{re.escape(label)}\s*$\n\s*\**(.+?)\**\s*$",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = _clean(match.group(1))
            if value:
                return value
    return ""


def _persisted_value(text: str, spec: FieldSpec) -> tuple[str, str] | None:
    labels = (spec.label,) + spec.aliases
    if spec.section == "top":
        for label in labels:
            value = _explicit_label(text, label)
            if value:
                return value, label
    else:
        block = _section(text, spec.section)
        if block:
            for label in labels:
                value = _explicit_label(block, label)
                if value:
                    return value, label
        for section_name in COMPATIBLE_SECTIONS.get(spec.key, ()):
            compatible = _section(text, section_name)
            if compatible:
                value = _explicit_label(compatible, spec.label)
                if value:
                    return value, spec.label
        # Outside a PM V2 section, only declared legacy aliases are allowed.
        # Reusing generic primary labels such as Cash or Positioning across an
        # entire legacy document silently changes their meaning.
        for label in spec.aliases:
            value = _explicit_label(text, label)
            if value:
                return value, label
    return None


def load_parity() -> tuple[dict[str, dict[str, str]], str]:
    raw = PARITY_PATH.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    with PARITY_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = {row["signal_date"]: row for row in csv.DictReader(handle)}
    return rows, digest


def _pct(value: str) -> str:
    return f"{float(value):.1f}%"


def _canonical_values(row: dict[str, str]) -> dict[str, object]:
    values: dict[str, object] = {
        "f13.risk_budget": _pct(row["risk_budget_13"]),
        "f15.recommended_exposure": _pct(row["exposure_15"]),
        "f18.exposure_ceiling": _pct(row["exposure_15"]),
        "f18.allocated_equity": _pct(row["allocated_equity_18"]),
        "f18.tactical_reserve": _pct(row["tactical_reserve"]),
        "f18.cash": _pct(row["cash_weight"]),
        "f15.exposure_control": row["sew_status"] or UNAVAILABLE,
        "f18.macro_allocation": row["macro_profile"] or UNAVAILABLE,
        "executive.macro_narrative": row["macro_narrative"] or UNAVAILABLE,
        "market.macro_narrative": row["macro_narrative"] or UNAVAILABLE,
        "cross.vix": f'{float(row["vix_today"]):.2f}',
        "cross.hy_oas": f'{float(row["hy_oas_today"]):.2f}%',
    }
    weights = json.loads(row["weights_json"])
    values["sector_weights"] = {
        name: _pct(str(weight)) for name, weight in weights.items() if float(weight) > 0
    }
    return values


def source_schema(text: str) -> str:
    required = ("DECISION PATH", "EXECUTIVE VIEW", "MARKET STATE", "CROSS-ASSET CONFIRMATION",
                "LEADERSHIP & PARTICIPATION", "ALLOCATION CONTEXT", "PORTFOLIO ALLOCATION", "DECISION RATIONALE")
    if text.startswith("# Global Capital Flow – Daily PM View"):
        return "PM_V2_COMPLETE" if all(re.search(rf"^\d+\. {re.escape(x)}$", text, re.MULTILINE) for x in required) else "PM_V2_TRANSITIONAL"
    return "LEGACY_ENGINE" if "### 🧠 13) Narrative Engine" in text else "LEGACY_BASIC"


def reconstruct_report(path: Path, parity: dict[str, dict[str, str]], parity_hash: str) -> dict:
    text = path.read_text(encoding="utf-8")
    report_date = path.stem.removeprefix("daily_report_")
    data_as_of_raw = _metadata(text, "Data as of")
    as_of_match = re.search(r"\d{4}-\d{2}-\d{2}", data_as_of_raw)
    data_as_of = as_of_match.group(0) if as_of_match else ""
    canonical_row = parity.get(data_as_of) if data_as_of else None
    canonical = _canonical_values(canonical_row) if canonical_row else {}
    source_hash = sha256_text(text)
    fields: dict[str, dict[str, str]] = {}
    authority_conflicts: list[dict[str, str]] = []

    for spec in FIELD_SPECS:
        if spec.key in canonical and canonical[spec.key] != UNAVAILABLE:
            persisted = _persisted_value(text, spec)
            if persisted and spec.key in {
                "f13.risk_budget", "f15.recommended_exposure", "f18.exposure_ceiling",
                "f18.allocated_equity", "f18.tactical_reserve", "f18.cash",
                "f15.exposure_control", "f18.macro_allocation",
                "executive.macro_narrative", "market.macro_narrative",
            }:
                canonical_value = str(canonical[spec.key])
                persisted_value = persisted[0]
                a_num = re.search(r"-?\d+(?:\.\d+)?", canonical_value)
                b_num = re.search(r"-?\d+(?:\.\d+)?", persisted_value)
                same = (
                    abs(float(a_num.group()) - float(b_num.group())) <= 0.051
                    if a_num and b_num
                    else canonical_value.casefold() == persisted_value.casefold()
                )
                if not same:
                    authority_conflicts.append({
                        "field": spec.key,
                        "canonical_replay": canonical_value,
                        "persisted_publication": persisted_value,
                        "persisted_label": persisted[1],
                        "handling": "Canonical replay remains the reconstructed value; persisted publication truth is displayed as a separate conflict and retained losslessly.",
                    })
            fields[spec.key] = {
                "label": spec.label, "section": spec.section, "status": "A",
                "value": str(canonical[spec.key]), "authority": str(PARITY_PATH.relative_to(ROOT)),
                "authority_sha256": parity_hash, "source_clock": data_as_of,
                "reason": "Exact persisted Data as-of matched frozen canonical PIT signal_date.",
            }
            continue
        persisted = _persisted_value(text, spec)
        if persisted:
            value, matched_label = persisted
            fields[spec.key] = {
                "label": spec.label, "section": spec.section, "status": "B", "value": value,
                "authority": str(path.relative_to(ROOT)), "authority_sha256": source_hash,
                "source_clock": data_as_of or report_date,
                "reason": f"Explicit same-date persisted label: {matched_label}.",
            }
        else:
            fields[spec.key] = {
                "label": spec.label, "section": spec.section, "status": "C", "value": UNAVAILABLE,
                "authority": str(path.relative_to(ROOT)), "authority_sha256": source_hash,
                "source_clock": data_as_of or "not recorded",
                "reason": "No exact-clock canonical value and no explicit same-date persisted field.",
            }

    sector_weights: list[dict[str, str]] = []
    if canonical_row:
        for name, value in dict(canonical.get("sector_weights", {})).items():
            sector_weights.append({
                "sector": name, "weight": value, "status": "A",
                "authority": str(PARITY_PATH.relative_to(ROOT)), "authority_sha256": parity_hash,
                "source_clock": data_as_of,
            })
    else:
        allocation = _section(text, "PORTFOLIO ALLOCATION")
        marker = allocation.find("Sector Allocation")
        if marker >= 0:
            for line in allocation[marker + len("Sector Allocation"):].splitlines():
                match = re.match(r"^\s*(.+?)\s{2,}(\d+(?:\.\d+)?%)\s*$", line)
                if match:
                    sector_weights.append({
                        "sector": match.group(1).strip(), "weight": match.group(2), "status": "B",
                        "authority": str(path.relative_to(ROOT)), "authority_sha256": source_hash,
                        "source_clock": data_as_of or report_date,
                    })

    execution_rows: list[dict[str, str]] = []
    execution = _section(text, "EXECUTION")
    for line in execution.splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) == 6 and cells[0] not in {"Sector", ""}:
            sector, etf, weight, action, classification, divergence = cells
            execution_rows.append({
                "sector": sector, "etf": etf, "weight": weight, "action": action,
                "classification": classification, "divergence": divergence, "status": "B",
                "authority": str(path.relative_to(ROOT)), "authority_sha256": source_hash,
                "source_clock": data_as_of or report_date,
            })

    return {
        "contract": CONTRACT_ID, "report_date": report_date, "data_as_of": data_as_of,
        "source_schema": source_schema(text), "source_path": str(path.relative_to(ROOT)),
        "source_sha256": source_hash, "canonical_exact_clock": bool(canonical_row),
        "canonical_signal_date": data_as_of if canonical_row else None,
        "fields": fields, "sector_weights": sector_weights, "execution_rows": execution_rows,
        "authority_conflicts": authority_conflicts,
    }


def build_population() -> list[dict]:
    parity, parity_hash = load_parity()
    return [reconstruct_report(path, parity, parity_hash) for path in sorted(REPORTS_DIR.glob("daily_report_????-??-??.md"))]


def synthetic_pm_v2_markdown(record: dict) -> str:
    value = lambda key: record["fields"][key]["value"]
    weights = "\n".join(f'{row["sector"]:<25}  {row["weight"]}' for row in record["sector_weights"])
    if not weights:
        weights = "Unavailable · no same-date sector allocation source"
    execution = "\n".join(
        " | ".join(row[key] for key in ("sector", "etf", "weight", "action", "classification", "divergence"))
        for row in record["execution_rows"]
    )
    if execution:
        execution = "Sector | ETF | Weight | Action | Classification | Divergence\n" + execution
    else:
        execution = "Unavailable · F19 rows require explicit same-date execution evidence"
    return f"""# Global Capital Flow – Daily PM View
**Date:** {record['report_date']}
**Data as of:** {record['data_as_of'] or 'Unavailable · not recorded in persisted source'}
**Reconstruction Contract:** {CONTRACT_ID}

GLOBAL CAPITAL FLOW MONITOR
DAILY PM VIEW

PORTFOLIO STANCE
{value('decision.action')}

REGIME
{value('decision.regime')}

CONVICTION
{value('decision.conviction')}

1. DECISION PATH
Strategic Risk Budget  {value('f13.risk_budget')}
Recommended Exposure  {value('f15.recommended_exposure')}
Exposure Ceiling      {value('f18.exposure_ceiling')}
Allocated Equity      {value('f18.allocated_equity')}
Tactical Reserve      {value('f18.tactical_reserve')}
Cash                  {value('f18.cash')}
Exposure Control      {value('f15.exposure_control')}
Macro Allocation      {value('f18.macro_allocation')}

2. EXECUTIVE VIEW
Historical PM V2 reconstruction. Every displayed state is exact-clock canonical, explicit same-date persisted, or unavailable.
Macro Narrative      {value('executive.macro_narrative')}
Tactical Signal      {value('executive.tactical_signal')}

3. MARKET STATE
Macro Narrative       {value('market.macro_narrative')}
Policy Bias           {value('market.policy_bias')}
Financial Conditions  {value('market.financial_conditions')}
Real Rate             {value('market.real_rate')}
Liquidity             {value('market.liquidity')}
Liquidity Level       {value('market.liquidity_level')}
Dollar Liquidity      {value('market.dollar_liquidity')}
Fed Plumbing          {value('market.fed_plumbing')}
Structure             {value('market.structure')}
Growth Sustainability {value('market.growth')}
Institutional Flow    {value('market.flow')}
Flow Authenticity     {value('market.flow_authenticity')}
Participation Quality {value('market.participation_quality')}
Participation Mode    {value('market.participation_mode')}
Leadership            {value('market.leadership')}
Positioning           {value('market.positioning')}
Dealer Gamma          {value('market.dealer_gamma')}
Squeeze Risk          {value('market.squeeze_risk')}
Vol Structure         {value('market.vol_structure')}
Positioning Z         {value('market.positioning_z')}
Credit                {value('market.credit')}
Credit Structure      {value('market.credit_structure')}
Drift                 {value('market.drift')}

4. CROSS-ASSET CONFIRMATION
US10Y Yield          {value('cross.us10y')}
USD                  {value('cross.usd')}
Oil                  {value('cross.oil')}
Volatility           {value('cross.vix')}
HY OAS               {value('cross.hy_oas')}

5. LEADERSHIP & PARTICIPATION
Coverage             {value('leadership.coverage')}

Today's Sector Leaders
Unavailable · rows are not synthesized from incomplete history

Breadth & Leadership
Unavailable · rows are not synthesized from incomplete history

6. ALLOCATION CONTEXT
Growth vs Value       {value('allocation.growth_value')}
Duration Tilt         {value('allocation.duration_tilt')}
Cyclical Defensive    {value('allocation.cyclical_defensive')}
Duration Factor       {value('allocation.duration_factor')}
Inflation Factor      {value('allocation.inflation_factor')}
USD Factor            {value('allocation.usd_factor')}
Credit Factor         {value('allocation.credit_factor')}
Regime Controller     {value('f18.regime_controller')}
Exposure Override     {value('f18.exposure_override')}

7. PORTFOLIO ALLOCATION
Exposure Ceiling      {value('f18.exposure_ceiling')}
Allocated Equity      {value('f18.allocated_equity')}
Tactical Reserve      {value('f18.tactical_reserve')}
Cash                  {value('f18.cash')}

Sector Allocation
{weights}

Note: Only exact-clock canonical or explicit persisted weights are shown.

8. ACTIVE CONSTRAINTS
Exposure Control      {value('constraint.exposure_control')}
Squeeze Risk          {value('constraint.squeeze_risk')}
Vol Structure         {value('constraint.vol_structure')}
Correlation Break     {value('constraint.correlation_break')}
Sector Corr Break     {value('constraint.sector_corr_break')}
Rank Control          {value('constraint.rank_control')}
Geopolitical          {value('constraint.geopolitical')}

9. EXECUTION
{execution}

10. DECISION RATIONALE
Decision             {value('rationale.decision')}
Exposure Ceiling     {value('rationale.exposure')}
Tactical Signal      {value('rationale.tactical_signal')}
Conviction           {value('rationale.conviction')}
Rationale
- No rationale is synthesized; inspect field provenance and persisted source.
"""
