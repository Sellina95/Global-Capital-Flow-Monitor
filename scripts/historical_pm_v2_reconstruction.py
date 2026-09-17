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
ACTION_LOG_RECOVERY_PATH = ROOT / "data/historical/action_log_recovery.json"
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
    FieldSpec("market.summary", "EXECUTIVE VIEW", "Market Summary"),
    FieldSpec("f13.risk_budget", "DECISION PATH", "Strategic Risk Budget", ("Risk Budget (0~100)",)),
    FieldSpec("f15.recommended_exposure", "DECISION PATH", "Recommended Exposure", ("📊 Recommended Exposure",)),
    FieldSpec("f18.exposure_ceiling", "DECISION PATH", "Exposure Ceiling"),
    FieldSpec("f18.allocated_equity", "DECISION PATH", "Allocated Equity"),
    FieldSpec("f18.tactical_reserve", "DECISION PATH", "Tactical Reserve", ("Tactical Reserve (Cap / Unallocated)",)),
    FieldSpec("f18.cash", "DECISION PATH", "Cash"),
    FieldSpec("f15.exposure_control", "DECISION PATH", "Exposure Control"),
    FieldSpec("f15.vix_control", "DECISION PATH", "VIX Control"),
    FieldSpec("f15.brake_drivers", "DECISION PATH", "Brake Drivers"),
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
    # The opening and closing decorations are paired explicitly.  The old
    # ``\**`` expression could match zero stars and therefore matched REGIME
    # inside ``Regime Controller``.  Historical field semantics must never be
    # selected by a prefix collision.
    literal = re.escape(label)
    patterns = (
        rf"(?im)^\s*(?:[-*•]\s*)?(?:\*\*)?{literal}(?::)?(?:\*\*)?\s*:\s*(?:\*\*)?(.+?)(?:\*\*)?\s*$",
        rf"(?im)^\s*(?:\*\*{literal}\*\*|{literal})\s*$\n\s*(?:\*\*)?(.+?)(?:\*\*)?\s*$",
        rf"(?im)^\s*(?:[-*•]\s*)?(?:\*\*{literal}\*\*|{literal})[ \t]+(?:\*\*)?(.+?)(?:\*\*)?\s*$",
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


def _heading_block(text: str, heading: str) -> str:
    """Return one legacy markdown heading block without crossing its peer."""
    match = re.search(rf"(?m)^###\s+.*?{re.escape(heading)}.*?$", text)
    if not match:
        return ""
    tail = text[match.end():]
    following = re.search(r"(?m)^###\s+", tail)
    return tail[:following.start()].strip() if following else tail.strip()


def _markdown_table(block: str) -> tuple[list[str], list[list[str]]]:
    lines = [line.strip() for line in block.splitlines() if line.strip().startswith("|")]
    for index in range(len(lines) - 1):
        header = [_clean(cell) for cell in lines[index].strip("|").split("|")]
        separator = [cell.strip() for cell in lines[index + 1].strip("|").split("|")]
        if header and len(header) == len(separator) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in separator):
            rows: list[list[str]] = []
            for line in lines[index + 2:]:
                cells = [_clean(cell) for cell in line.strip("|").split("|")]
                if len(cells) != len(header):
                    break
                rows.append(cells)
            return header, rows
    return [], []


def _pm_v2_leadership_rows(text: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    block = _section(text, "LEADERSHIP & PARTICIPATION")
    sectors = [
        {"rank": match.group(1), "sector": match.group(2).strip(), "return": match.group(3), "relative": match.group(4), "momentum": match.group(5)}
        for match in re.finditer(
            r"^\s*(\d+)\s+(.+?)\s{2,}([+-]\d+\.\d+%)\s+([+-]\d+\.\d+%)\s+(-?\d+|N/A)\s*$",
            block,
            re.MULTILINE,
        )
    ]
    breadth = [
        {"label": match.group(1), "today": match.group(2), "prev": match.group(3), "change": match.group(4)}
        for match in re.finditer(
            r"^(RSP vs SPY|QQQE vs QQQ|SMH vs SPY|IWM vs SPY)\s+Today\s+(.+?)\s+\|\s+Prev\s+(.+?)\s+\|\s+Δ\s+(.+?)\s*$",
            block,
            re.MULTILINE,
        )
    ]
    return sectors, breadth


def _legacy_engine_values(text: str) -> dict[str, object]:
    """Map explicit legacy engine outputs into the fixed PM V2 state.

    This is an adapter over same-date persisted evidence, not a calculation.
    Values are taken only from named engine blocks/labels whose semantics match
    the current PM V2 field.
    """
    values: dict[str, object] = {}
    f13 = _heading_block(text, "13) Narrative Engine")
    f15 = _heading_block(text, "15) Volatility-Controlled Exposure")
    f16 = _heading_block(text, "16) Style Tilt")
    f17 = _heading_block(text, "17) Factor Layer")
    f18 = _heading_block(text, "18) Sector Allocation Engine")
    f185 = _heading_block(text, "18.5) Tactical Asset Allocation")
    f19 = _heading_block(text, "19) Execution Layer")

    def put(key: str, block: str, *labels: str, transform=None) -> None:
        for label in labels:
            raw = _explicit_label(block, label)
            if raw:
                values[key] = transform(raw) if transform else raw
                return

    put("decision.action", f13, "🎯 Final Risk Action", "Final Risk Action")
    put("decision.regime", f13, "Operational Phase", transform=lambda x: re.sub(r"\s*\(Cap:\s*[^)]+\)\s*$", "", x).strip())
    put("decision.conviction", text, "Tactical Confidence", "Rally Confidence")
    put("f13.risk_budget", f13, "Risk Budget (0~100)")
    put("f15.recommended_exposure", f15, "📊 Recommended Exposure", "Recommended Exposure")
    put("f15.exposure_control", text, "SEW")
    vix_level = _explicit_label(f15, "VIX Level")
    if vix_level:
        change = _explicit_label(f15, "Change")
        values["f15.vix_control"] = vix_level + (f" | Change: {change}" if change else "")
    put("f15.brake_drivers", f15, "Brake Drivers")
    put("allocation.growth_value", f16, "Growth vs Value")
    put("allocation.duration_tilt", f16, "Duration Tilt")
    put("allocation.cyclical_defensive", f16, "Cyclical vs Defensive", "Cyclical Defensive")
    put("allocation.duration_factor", f17, "Duration Factor")
    put("allocation.inflation_factor", f17, "Inflation Factor")
    put("allocation.usd_factor", f17, "USD Factor")
    put("allocation.credit_factor", f17, "Credit Factor")
    put("f18.macro_allocation", f18, "Macro Profile")
    put("f18.exposure_override", f185, "Exposure Override")
    controller = re.search(r"(?ms)^\*\*Regime Controller:\*\*\s*\n\s*-\s*(.+?)\s*$", f18)
    if controller:
        values["f18.regime_controller"] = _clean(controller.group(1))

    strategic = re.search(r"(?m)^-\s*\*\*Strategic Exposure \(15\):\*\*\s*\*\*([^*]+)\*\*\s*→\s*\*\*Regime Adjusted:\*\*\s*\*\*([^*]+)\*\*", f185)
    if strategic:
        values["f18.exposure_ceiling"] = _clean(strategic.group(2))
    header, rows = _markdown_table(f185)
    allocation_rows: list[dict[str, str]] = []
    if header:
        normalized = [re.sub(r"[^a-z]", "", item.casefold()) for item in header]
        sector_i = normalized.index("sector") if "sector" in normalized else -1
        weight_i = next((i for i, item in enumerate(normalized) if "weightinportfolio" in item), -1)
        if sector_i >= 0 and weight_i >= 0:
            for row in rows:
                if row[sector_i].casefold() in {"cash", "cash & hedge"}:
                    values["f18.cash"] = row[weight_i]
                    continue
                allocation_rows.append({"sector": row[sector_i], "weight": row[weight_i]})
    if allocation_rows:
        values["sector_weights"] = allocation_rows
        allocated = sum(float(re.search(r"\d+(?:\.\d+)?", row["weight"]).group()) for row in allocation_rows)
        values["f18.allocated_equity"] = f"{allocated:.1f}%"
    put("f18.tactical_reserve", f185, "Tactical Reserve (Cap / Unallocated)", "Tactical Reserve")
    if "f18.cash" not in values:
        put("f18.cash", f185, "Cash & Hedge", "Cash")

    header, rows = _markdown_table(f19)
    execution_rows: list[dict[str, str]] = []
    if header:
        normalized = [re.sub(r"[^a-z]", "", item.casefold()) for item in header]
        aliases = {
            "sector": ("sector",), "etf": ("etf",), "weight": ("weight", "finalweight"),
            "action": ("action",), "classification": ("classification", "class"),
            "divergence": ("divergence",),
        }
        indices = {key: next((i for i, item in enumerate(normalized) if item in names), -1) for key, names in aliases.items()}
        if all(indices[key] >= 0 for key in ("sector", "etf", "weight", "action")):
            for row in rows:
                execution_rows.append({
                    key: row[index] if index >= 0 else UNAVAILABLE
                    for key, index in indices.items()
                })
    if execution_rows:
        values["execution_rows"] = execution_rows

    # Same-date market inputs and explicit derived states used by PM V2.
    mapping = {
        "market.financial_conditions": ("\ud604\uc2e4(FCI)",),
        "market.real_rate": ("\uc720\uc778(Real Rates)",),
        "market.liquidity_level": ("NET_LIQ level",),
        "market.flow": ("Flow",), "market.dealer_gamma": ("Gamma",),
        "market.positioning_z": ("POS_Z",), "market.drift": ("Drift",),
        "cross.us10y": ("\ubbf8\uad6d 10\ub144\ubb3c \uae08\ub9ac",), "cross.usd": ("\ub2ec\ub7ec \uc778\ub371\uc2a4",),
        "cross.oil": ("WTI \uc720\uac00",), "cross.vix": ("\ubcc0\ub3d9\uc131 \uc9c0\uc218 (VIX)",),
        "cross.hy_oas": ("HY_OAS level",),
    }
    for key, labels in mapping.items():
        put(key, text, *labels)
    for block_name, key in (("12.5) Growth Sustainability", "market.growth"), ("12.6) Flow Authenticity", "market.flow_authenticity"), ("12.7) Leadership Breadth", "market.leadership"), ("12.8) Positioning Stress", "market.positioning")):
        put(key, _heading_block(text, block_name), "Label")
    put("market.structure", text, "Structure")
    put("market.policy_bias", text, "Policy Bias")
    put("market.liquidity", text, "Liquidity")
    put("market.credit", text, "Credit")
    put("market.credit_structure", text, "Credit Stress")
    put("market.squeeze_risk", text, "Squeeze Risk")
    put("market.vol_structure", text, "Vol Structure")
    rotation_rows: list[dict[str, str]] = []
    for label in ("RSP vs SPY", "QQQE vs QQQ", "SMH vs SPY", "IWM vs SPY"):
        match = re.search(
            rf"(?ms)^{re.escape(label)}\s*$.*?^Yesterday:\s*([^\n]+)\s*$.*?^Today:\s*([^\n]+)\s*$.*?^Change:\s*([^\n]+)\s*$",
            text,
        )
        if match:
            rotation_rows.append({"label": label, "prev": _clean(match.group(1)), "today": _clean(match.group(2)), "change": _clean(match.group(3))})
    if rotation_rows:
        values["breadth_rows"] = rotation_rows
    return values


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


def _persisted_market_summary(text: str, schema: str) -> str:
    if schema.startswith("PM_V2"):
        block = _section(text, "EXECUTIVE VIEW")
        for raw in block.splitlines():
            line = raw.strip()
            if line and not re.match(r"^[A-Za-z][A-Za-z ]+\s{2,}", line):
                return _clean(line)
    if schema == "LEGACY_ENGINE":
        match = re.search(r"(?ms)^[^\n]*1\.\s+Executive Summary\s*$\n(.*?)(?=^[^\n]*2\.\s+Macro Regime\s*$)", text)
        if match:
            for raw in match.group(1).splitlines():
                if raw.strip():
                    return _clean(raw)
    return ""


def reconstruct_report(path: Path, parity: dict[str, dict[str, str]], parity_hash: str) -> dict:
    text = path.read_text(encoding="utf-8")
    report_date = path.stem.removeprefix("daily_report_")
    data_as_of_raw = _metadata(text, "Data as of")
    as_of_match = re.search(r"\d{4}-\d{2}-\d{2}", data_as_of_raw)
    data_as_of = as_of_match.group(0) if as_of_match else ""
    canonical_row = parity.get(data_as_of) if data_as_of else None
    canonical = _canonical_values(canonical_row) if canonical_row else {}
    schema = source_schema(text)
    legacy = _legacy_engine_values(text) if schema == "LEGACY_ENGINE" else {}
    diagnostics_path = REPORTS_DIR / f"engine_diagnostics_{report_date}.md"
    diagnostics_text = diagnostics_path.read_text(encoding="utf-8") if diagnostics_path.exists() else ""
    diagnostics_date = _metadata(diagnostics_text, "Date") if diagnostics_text else ""
    diagnostics_as_of_raw = _metadata(diagnostics_text, "Data as of") if diagnostics_text else ""
    diagnostics_as_of_match = re.search(r"\d{4}-\d{2}-\d{2}", diagnostics_as_of_raw)
    diagnostics_as_of = diagnostics_as_of_match.group(0) if diagnostics_as_of_match else ""
    diagnostics_clock_valid = bool(
        diagnostics_text and diagnostics_date == report_date and diagnostics_as_of == data_as_of
    )
    if diagnostics_text and not diagnostics_clock_valid:
        diagnostics_text = ""
    diagnostics_hash = sha256_text(diagnostics_text) if diagnostics_text else ""
    diagnostics_values = _legacy_engine_values(diagnostics_text) if diagnostics_text else {}

    # Historical diagnostics storage cutover:
    # - before 2026-09-02: diagnostics are embedded in daily_report_D.md
    # - from 2026-09-02: separate engine_diagnostics_D.md is authoritative
    persisted_diagnostics_text = diagnostics_text or text
    persisted_diagnostics_path = diagnostics_path if diagnostics_text else path
    persisted_diagnostics_hash = diagnostics_hash if diagnostics_text else sha256_text(text)
    pm_sector_rows, pm_breadth_rows = _pm_v2_leadership_rows(text)
    market_summary = _persisted_market_summary(text, schema)
    source_hash = sha256_text(text)

    # Supplemental same-date bindings:
    # These values already exist in the persisted historical report/diagnostics.
    # This adapter only exposes them to the fixed PM V2 schema; it does not
    # calculate, infer, or backfill new historical state.
    supplemental_values: dict[str, dict[str, str]] = {}

    # Exact same-date production outputs recovered from historical GitHub
    # Actions logs. This is persisted historical evidence, not a replay and
    # not a recalculation with current code. It is lower priority than frozen
    # canonical PIT, the public report, and same-date engine diagnostics.
    if ACTION_LOG_RECOVERY_PATH.exists():
        recovery_raw = ACTION_LOG_RECOVERY_PATH.read_text(encoding="utf-8")
        recovery_doc = json.loads(recovery_raw)
        recovery_item = recovery_doc.get("dates", {}).get(report_date, {})
        recovery_fields = recovery_item.get("fields", {})
        if recovery_fields:
            recovery_hash = sha256_text(recovery_raw)
            run_id = recovery_item.get("run_id", "")
            head_sha = recovery_item.get("head_sha", "")
            for recovery_key, recovery_value in recovery_fields.items():
                if recovery_value in ("", None):
                    continue

                recovered_item = {
                    "value": str(recovery_value),
                    "authority": str(ACTION_LOG_RECOVERY_PATH.relative_to(ROOT)),
                    "authority_sha256": recovery_hash,
                    "reason": (
                        "Exact same-date production value recovered from "
                        f"GitHub Actions Daily Macro Report run {run_id} "
                        f"at historical head {head_sha}."
                    ),
                }
                supplemental_values[recovery_key] = recovered_item

                # ACTIVE CONSTRAINTS exposes the same persisted engine states
                # under separate PM V2 field keys. Bind them without
                # recalculating or changing their historical semantics.
                constraint_alias = {
                    "market.squeeze_risk": "constraint.squeeze_risk",
                    "market.vol_structure": "constraint.vol_structure",
                }.get(recovery_key)

                if constraint_alias:
                    supplemental_values[constraint_alias] = dict(recovered_item)

    macro_narrative = _explicit_label(text, "Macro Narrative")
    if macro_narrative:
        supplemental_values["market.macro_narrative"] = {
            "value": macro_narrative,
            "authority": str(path.relative_to(ROOT)),
            "authority_sha256": source_hash,
            "reason": "Explicit same-date persisted Macro Narrative.",
        }

    coverage = _explicit_label(text, "Coverage")
    if coverage:
        supplemental_values["leadership.coverage"] = {
            "value": coverage,
            "authority": str(path.relative_to(ROOT)),
            "authority_sha256": source_hash,
            "reason": "Explicit same-date persisted leadership coverage.",
        }

    geopolitical = _explicit_label(text, "Geopolitical")
    if geopolitical:
        supplemental_values["constraint.geopolitical"] = {
            "value": geopolitical,
            "authority": str(path.relative_to(ROOT)),
            "authority_sha256": source_hash,
            "reason": "Explicit same-date persisted Geopolitical state.",
        }

    if persisted_diagnostics_text:
        sew_match = re.search(
            r"(?im)^-\s*\*\*SEW:\*\*\s*STABLE\s*/\s*NORMAL\s*$",
            persisted_diagnostics_text,
        )
        if sew_match:
            supplemental_values["constraint.exposure_control"] = {
                "value": "NORMAL",
                "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
                "authority_sha256": persisted_diagnostics_hash,
                "reason": "Explicit same-date SEW state: STABLE / NORMAL.",
            }

        vol_match = re.search(
            r"(?im)^-\s*Term Structure:\s*VIX3M-VIX=[^\n]*?→\s*(healthy contango / stable structure)\s*$",
            persisted_diagnostics_text,
        )
        if vol_match:
            supplemental_values["market.vol_structure"] = {
                "value": "NORMAL",
                "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
                "authority_sha256": persisted_diagnostics_hash,
                "reason": "Explicit same-date VIX term structure: healthy contango / stable structure.",
            }

        fed_block = _heading_block(persisted_diagnostics_text, "4) Fed Plumbing Filter")
        fed_match = re.search(
            r"(?m)^-\s*\*\*판정:\*\*\s*\*\*(.+?)\*\*\s*$",
            fed_block,
        )
        if fed_match:
            supplemental_values["market.fed_plumbing"] = {
                "value": _clean(fed_match.group(1)),
                "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
                "authority_sha256": persisted_diagnostics_hash,
                "reason": "Explicit same-date Fed Plumbing verdict.",
            }

        credit_block = _heading_block(persisted_diagnostics_text, "4.5) Credit Stress Filter")
        credit_match = re.search(
            r"(?m)^-\s*\*\*판정:\*\*\s*\*\*(.+?)\*\*\s*$",
            credit_block,
        )
        if credit_match:
            supplemental_values["market.credit_structure"] = {
                "value": _clean(credit_match.group(1)),
                "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
                "authority_sha256": persisted_diagnostics_hash,
                "reason": "Explicit same-date Credit Stress verdict.",
            }

        # Explicit SEW state -> Exposure Control
    sew_match = re.search(
        r"(?im)^-\s*\*\*SEW:\*\*\s*(RISK_COMPRESSION|DEADMAN|STABLE)(?:\s*[|/]\s*[^\n]+)?",
        persisted_diagnostics_text,
    )
    if sew_match:
        sew_state = sew_match.group(1)
        exposure_value = "NORMAL" if sew_state == "STABLE" else sew_state
        supplemental_values["constraint.exposure_control"] = {
            "value": exposure_value,
            "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
            "authority_sha256": persisted_diagnostics_hash,
            "reason": f"Explicit same-date SEW state: {sew_state}.",
        }

    # Explicit/stable VIX term structure -> Vol Structure NORMAL
    # Preserve stronger exact same-date recovered engine state when present.
    # Generic publication/term-structure evidence may fill a gap, but must not
    # overwrite an already recovered production-semantic Vol Structure state.
    if "constraint.vol_structure" not in supplemental_values:
        vol_explicit = _explicit_label(text, "Vol Structure")
        if vol_explicit:
            supplemental_values["constraint.vol_structure"] = {
                "value": vol_explicit,
                "authority": str(path.relative_to(ROOT)),
                "authority_sha256": source_hash,
                "reason": "Explicit same-date persisted Vol Structure.",
            }
        elif re.search(
            r"(?im)^-\s*Term Structure:.*(?:healthy contango / stable structure|mild contango)\s*$",
            persisted_diagnostics_text,
        ):
            supplemental_values["constraint.vol_structure"] = {
                "value": "NORMAL",
                "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
                "authority_sha256": persisted_diagnostics_hash,
                "reason": "Explicit same-date VIX term structure indicates stable/contango structure.",
            }

    # Explicit Geo Stress Level
    geo_level_match = re.search(
        r"(?im)^-\s*\*\*Geo Stress Score.*?Level:\s*(NORMAL|LOW|ELEVATED|HIGH)",
        persisted_diagnostics_text,
    )
    if geo_level_match and "constraint.geopolitical" not in supplemental_values:
        supplemental_values["constraint.geopolitical"] = {
            "value": geo_level_match.group(1),
            "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
            "authority_sha256": persisted_diagnostics_hash,
            "reason": "Explicit same-date Geo Stress level.",
        }

    corr_block = _heading_block(persisted_diagnostics_text, "6.5) Correlation Break Monitor")
    if "No significant correlation break detected." in corr_block:
        supplemental_values["constraint.correlation_break"] = {
            "value": "No significant correlation break detected.",
            "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
            "authority_sha256": persisted_diagnostics_hash,
            "reason": "Explicit same-date Correlation Break result.",
        }
    elif "Correlation Break Detected" in corr_block:
        supplemental_values["constraint.correlation_break"] = {
            "value": "Correlation Break Detected",
            "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
            "authority_sha256": persisted_diagnostics_hash,
            "reason": "Explicit same-date Correlation Break result.",
        }

    sector_corr_block = _heading_block(
        persisted_diagnostics_text, "6.6) Sector Correlation Break Monitor"
    )
    if "Correlation Break Detected" in sector_corr_block:
        supplemental_values["constraint.sector_corr_break"] = {
            "value": "Correlation Break Detected",
            "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
            "authority_sha256": persisted_diagnostics_hash,
            "reason": "Explicit same-date Sector Correlation Break result.",
        }
    elif "No significant sector-level correlation break detected." in sector_corr_block:
        supplemental_values["constraint.sector_corr_break"] = {
            "value": "No significant sector-level correlation break detected.",
            "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
            "authority_sha256": persisted_diagnostics_hash,
            "reason": "Explicit same-date Sector Correlation Break result.",
        }
    fields: dict[str, dict[str, str]] = {}
    authority_conflicts: list[dict[str, str]] = []

    for spec in FIELD_SPECS:
        if spec.key == "market.summary" and market_summary:
            fields[spec.key] = {
                "label": spec.label, "section": spec.section, "status": "B", "value": market_summary,
                "authority": str(path.relative_to(ROOT)), "authority_sha256": source_hash,
                "source_clock": data_as_of or report_date,
                "reason": "Explicit same-date persisted executive summary.",
            }
            continue
        if spec.key in canonical and canonical[spec.key] != UNAVAILABLE:
            persisted = (str(legacy[spec.key]), f"legacy engine adapter: {spec.label}") if spec.key in legacy else _persisted_value(text, spec)
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
        persisted = (str(legacy[spec.key]), f"legacy engine adapter: {spec.label}") if spec.key in legacy else _persisted_value(text, spec)
        if persisted:
            value, matched_label = persisted
            fields[spec.key] = {
                "label": spec.label, "section": spec.section, "status": "B", "value": value,
                "authority": str(path.relative_to(ROOT)), "authority_sha256": source_hash,
                "source_clock": data_as_of or report_date,
                "reason": f"Explicit same-date persisted label: {matched_label}.",
            }
        elif spec.key in diagnostics_values:
            fields[spec.key] = {
                "label": spec.label, "section": spec.section, "status": "B",
                "value": str(diagnostics_values[spec.key]),
                "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
                "authority_sha256": persisted_diagnostics_hash,
                "source_clock": data_as_of or report_date,
                "reason": f"Explicit same-date persisted diagnostics field: {spec.label}.",
            }
        elif spec.key in supplemental_values:
            item = supplemental_values[spec.key]
            fields[spec.key] = {
                "label": spec.label,
                "section": spec.section,
                "status": "B",
                "value": item["value"],
                "authority": item["authority"],
                "authority_sha256": item["authority_sha256"],
                "source_clock": data_as_of or report_date,
                "reason": item["reason"],
            }
        else:
            fields[spec.key] = {
                "label": spec.label, "section": spec.section, "status": "C", "value": UNAVAILABLE,
                "authority": str(path.relative_to(ROOT)), "authority_sha256": source_hash,
                "source_clock": data_as_of or "not recorded",
                "reason": "Historical source unavailable after canonical PIT replay, same-date persisted publication, and same-date diagnostics checks.",
                "sources_checked": [
                    str(PARITY_PATH.relative_to(ROOT)),
                    str(path.relative_to(ROOT)),
                    f"reports/engine_diagnostics_{report_date}.md",
                ],
                "required_evidence": f"Exact-clock production-semantic source for {spec.key}",
                "reconstruction_possible": False,
            }

    sector_weights: list[dict[str, str]] = []
    if canonical_row:
        for name, value in dict(canonical.get("sector_weights", {})).items():
            sector_weights.append({
                "sector": name, "weight": value, "status": "A",
                "authority": str(PARITY_PATH.relative_to(ROOT)), "authority_sha256": parity_hash,
                "source_clock": data_as_of,
            })
    elif legacy.get("sector_weights"):
        collection = legacy["sector_weights"]
        for row in collection:
            sector_weights.append({
                **row, "status": "B", "authority": str(path.relative_to(ROOT)),
                "authority_sha256": source_hash, "source_clock": data_as_of or report_date,
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
        if not sector_weights and diagnostics_values.get("sector_weights"):
            for row in diagnostics_values["sector_weights"]:
                sector_weights.append({
                    **row, "status": "B", "authority": str(persisted_diagnostics_path.relative_to(ROOT)),
                    "authority_sha256": persisted_diagnostics_hash, "source_clock": data_as_of or report_date,
                })

    execution_rows: list[dict[str, str]] = []
    raw_execution_rows = list(legacy.get("execution_rows", []))
    execution_path = path
    execution_hash = source_hash
    if not raw_execution_rows:
        execution = _section(text, "EXECUTION")
        for line in execution.splitlines():
            cells = [cell.strip() for cell in line.split("|")]
            if len(cells) == 6 and cells[0] not in {"Sector", ""}:
                sector, etf, weight, action, classification, divergence = cells
                raw_execution_rows.append({
                    "sector": sector, "etf": etf, "weight": weight, "action": action,
                    "classification": classification, "divergence": divergence,
                })
    if not raw_execution_rows and diagnostics_values.get("execution_rows"):
        raw_execution_rows = list(diagnostics_values["execution_rows"])
        execution_path = diagnostics_path
        execution_hash = diagnostics_hash
    for row in raw_execution_rows:
        execution_rows.append({
            **row, "status": "B", "authority": str(execution_path.relative_to(ROOT)),
            "authority_sha256": execution_hash, "source_clock": data_as_of or report_date,
        })

    return {
        "contract": CONTRACT_ID, "report_date": report_date, "data_as_of": data_as_of,
        "source_schema": schema, "source_path": str(path.relative_to(ROOT)),
        "source_sha256": source_hash, "canonical_exact_clock": bool(canonical_row),
        "canonical_signal_date": data_as_of if canonical_row else None,
        "fields": fields, "sector_weights": sector_weights, "execution_rows": execution_rows,
        "leadership_rows": pm_sector_rows,
        "breadth_rows": pm_breadth_rows or legacy.get("breadth_rows", []) or diagnostics_values.get("breadth_rows", []),
        "authority_conflicts": authority_conflicts,
        "upstream_checks": {
            "canonical_pit_replay": "exact signal_date match" if canonical_row else "no exact signal_date match",
            "same_date_persisted_publication": str(path.relative_to(ROOT)),
            "same_date_diagnostics": str(persisted_diagnostics_path.relative_to(ROOT)) if diagnostics_clock_valid else "not persisted or clock mismatch",
            "legacy_engine_adapter": bool(legacy),
        },
    }


def build_population() -> list[dict]:
    parity, parity_hash = load_parity()
    population = [reconstruct_report(path, parity, parity_hash) for path in sorted(REPORTS_DIR.glob("daily_report_????-??-??.md"))]

    def number(raw: str) -> float | None:
        match = re.fullmatch(r"(\d+(?:\.\d+)?)%", str(raw).strip())
        return float(match.group(1)) if match else None

    def snapshot(record: dict) -> dict[str, object] | None:
        allocated = number(record["fields"]["f18.allocated_equity"]["value"])
        reserve = number(record["fields"]["f18.tactical_reserve"]["value"])
        cash = number(record["fields"]["f18.cash"]["value"])
        weights = {row["sector"].casefold(): (row["sector"], number(row["weight"])) for row in record["sector_weights"]}
        if None in (allocated, reserve, cash) or any(value is None for _, value in weights.values()):
            return None
        if abs(sum(value for _, value in weights.values()) - allocated) > 0.35 or abs(allocated + cash - 100) > 0.11:
            return None
        return {"weights": weights, "totals": {"Allocated Equity": allocated, "Tactical Reserve": reserve, "Cash": cash}}

    previous_record: dict | None = None
    previous_snapshot: dict[str, object] | None = None
    for record in population:
        current = snapshot(record)
        comparison = {"available": False, "previous_date": previous_record["report_date"] if previous_record else None, "deltas": {}, "exits": []}
        if current is not None and previous_snapshot is not None and previous_record is not None:
            current_weights = current["weights"]
            previous_weights = previous_snapshot["weights"]
            deltas = {
                name: current_weights.get(name, ("", 0.0))[1] - previous_weights.get(name, ("", 0.0))[1]
                for name in set(current_weights) | set(previous_weights)
            }
            exits = [display for name, (display, value) in previous_weights.items() if value > 0 and name not in current_weights]
            total_deltas = {
                key: current["totals"][key] - previous_snapshot["totals"][key]
                for key in current["totals"]
            }
            comparison = {
                "available": True, "previous_date": previous_record["report_date"],
                "deltas": deltas, "total_deltas": total_deltas, "exits": exits,
                "authority": "adjacent HistoricalPMV2State snapshots with independently validated same-date allocation authority",
            }
        record["target_comparison"] = comparison
        previous_record = record
        previous_snapshot = current
    return population


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
    breadth = "\n".join(
        f'{row["label"]:<18} Today {row["today"]} | Prev {row["prev"]} | Δ {row["change"]}'
        for row in record.get("breadth_rows", [])
    ) or "Unavailable · no exact-clock breadth observations were reconstructed"
    leadership = "\n".join(
        f'{row["rank"]:>4}  {row["sector"]:<26} {row["return"]:>9} {row["relative"]:>10} {row["momentum"]:>10}'
        for row in record.get("leadership_rows", [])
    ) or "Unavailable · no same-date sector observations were reconstructed"

    # ACTIVE CONSTRAINTS follows production semantics:
    # show only materially active constraints.
    # NORMAL / benign / unavailable states are not rendered as active risks.
    active_constraint_specs = (
        ("Exposure Control", "constraint.exposure_control"),
        ("Squeeze Risk", "constraint.squeeze_risk"),
        ("Vol Structure", "constraint.vol_structure"),
        ("Correlation Break", "constraint.correlation_break"),
        ("Sector Corr Break", "constraint.sector_corr_break"),
        ("Rank Control", "constraint.rank_control"),
        ("Geopolitical", "constraint.geopolitical"),
    )

    benign_values = {
        "",
        UNAVAILABLE,
        "NORMAL",
        "STABLE",
        "NONE",
        "PASS",
        "No significant correlation break detected.",
        "No significant sector-level correlation break detected.",
    }

    active_constraint_lines = []
    for label, key in active_constraint_specs:
        raw = str(value(key)).strip()
        if raw in benign_values:
            continue
        active_constraint_lines.append(f"{label:<22}{raw}")

    active_constraints = "\n".join(active_constraint_lines)
    if not active_constraints:
        active_constraints = "No active constraints."
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
VIX Control           {value('f15.vix_control')}
Brake Drivers         {value('f15.brake_drivers')}
Macro Allocation      {value('f18.macro_allocation')}

2. EXECUTIVE VIEW
{value('market.summary')}
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
{leadership}

Breadth & Leadership
{breadth}

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
