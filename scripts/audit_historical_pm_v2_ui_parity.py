from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from collections import Counter
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

try:
    from scripts.audit_historical_pm_v2_reconstruction import audit as reconstruction_audit
    from scripts.historical_pm_v2_reconstruction import FIELD_SPECS, REPORTS_DIR, ROOT, UNAVAILABLE, build_population
except ModuleNotFoundError:
    from audit_historical_pm_v2_reconstruction import audit as reconstruction_audit  # type: ignore
    from historical_pm_v2_reconstruction import FIELD_SPECS, REPORTS_DIR, ROOT, UNAVAILABLE, build_population  # type: ignore


CONTRACT_ID = "GCF_HISTORICAL_PM_V2_UI_PARITY_V1"
CONTRACT_PATH = ROOT / "artifacts/historical_pm_v2_ui_contract_v1.json"
TEMPLATE_DATE = "2026-09-12"
REPRESENTATIVE_DATES = ("2025-12-11", "2026-06-22", "2026-08-28", "2026-09-02", "2026-09-12")


def _pairs(page: str, attribute: str) -> list[list[str]]:
    pairs: list[list[str]] = []
    pattern = rf'<[^>]*{re.escape(attribute)}="([^"]+)"[^>]*>'
    for match in re.finditer(pattern, page):
        tag = match.group(0)
        label_pattern = r'data-ui-label="([^"]+)"' if attribute == "data-ui-section" else r'data-ui-(?:field-)?label="([^"]+)"'
        label = re.search(label_pattern, tag)
        pairs.append([html.unescape(match.group(1)), html.unescape(label.group(1)) if label else ""])
    return pairs


class _StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[tuple[str, str | None]] = []
        self.sections: list[list[str | None]] = []
        self.field_sections: list[list[str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        section_id = values.get("data-ui-section")
        parent = self.stack[-1][1] if self.stack else None
        if section_id:
            self.sections.append([section_id, html.unescape(values.get("data-ui-label") or ""), parent])
        if values.get("data-ui-field"):
            self.field_sections.append([values["data-ui-field"], section_id or parent])
        self.stack.append((tag, section_id or parent))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                self.stack = self.stack[:index]
                return


def _hierarchy(page: str) -> tuple[list[list[str | None]], list[list[str | None]]]:
    parser = _StructureParser()
    parser.feed(page)
    return parser.sections, parser.field_sections


def _expected_field_sections(contract: dict) -> list[list[str | None]]:
    expected: list[list[str | None]] = []
    for section, start, end in contract["field_section_ranges"]:
        expected.extend([[field_id, section] for field_id, _ in contract["fields"][start:end]])
    return expected


def audit(site_dir: Path) -> dict:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    reports = sorted(REPORTS_DIR.glob("daily_report_????-??-??.md"))
    dates = [path.stem.removeprefix("daily_report_") for path in reports]
    population = build_population()
    records = {record["report_date"]: record for record in population}
    failures: Counter[str] = Counter()
    issues: list[dict[str, str]] = []
    checks = 0

    def check(ok: bool, kind: str, report_date: str, detail: str) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures[kind] += 1
            issues.append({"failure_class": kind, "report_date": report_date, "detail": detail})

    check(contract.get("contract") == CONTRACT_ID, "ui_contract_identity", "population", "wrong contract id")
    source = ROOT / contract["authority"]["source_path"]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    check(source_hash == contract["authority"]["source_sha256"], "ui_contract_identity", TEMPLATE_DATE, "template source hash changed")

    template_path = site_dir / "history" / f"{TEMPLATE_DATE}.html"
    check(template_path.exists(), "missing_page", TEMPLATE_DATE, "authoritative template page missing")
    template = template_path.read_text(encoding="utf-8") if template_path.exists() else ""
    template_sections = _pairs(template, "data-ui-section")
    template_fields = _pairs(template, "data-ui-field")
    template_hierarchy, template_field_sections = _hierarchy(template)
    check(template_sections == contract["sections"], "ui_contract_drift", TEMPLATE_DATE, "rendered section hierarchy differs from frozen contract")
    check(template_fields == contract["fields"], "ui_contract_drift", TEMPLATE_DATE, "rendered field inventory/order/labels differs from frozen contract")
    check(template_hierarchy == contract["section_hierarchy"], "ui_contract_drift", TEMPLATE_DATE, "rendered section nesting differs from frozen contract")
    check(template_field_sections == _expected_field_sections(contract), "ui_contract_drift", TEMPLATE_DATE, "rendered fields moved between sections")
    check(len(template_sections) == contract["counts"]["sections"], "ui_contract_drift", TEMPLATE_DATE, "section count differs")
    check(len(template_fields) == contract["counts"]["fields"], "ui_contract_drift", TEMPLATE_DATE, "field count differs")

    index = (site_dir / "index.html").read_text(encoding="utf-8")
    calendar = re.search(r"const availableDates\s*=\s*(\[[^;]+\])", index)
    calendar_dates = json.loads(calendar.group(1)) if calendar else []
    check(calendar_dates == dates, "calendar_population", "population", "calendar dates differ from persisted reports")
    check(set(records) == set(dates), "state_population", "population", "HistoricalPMV2State population differs")

    statuses: Counter[str] = Counter()
    unavailable_causes: Counter[str] = Counter()
    unavailable_by_schema: Counter[str] = Counter()
    unavailable_by_field: Counter[str] = Counter()
    collection_statuses: Counter[str] = Counter()
    coverage_matrix: list[dict[str, object]] = []
    structural_pass = 0
    phase_coverage = f_chain_coverage = allocation_structure = f19_structure = macro_structure = 0
    fabricated_defaults = 0

    for report_date in dates:
        record = records[report_date]
        page_path = site_dir / "history" / f"{report_date}.html"
        check(page_path.exists(), "missing_page", report_date, "calendar route target missing")
        if not page_path.exists():
            continue
        page = page_path.read_text(encoding="utf-8")
        sections = _pairs(page, "data-ui-section")
        fields = _pairs(page, "data-ui-field")
        hierarchy, field_sections = _hierarchy(page)
        same_sections = sections == contract["sections"]
        same_fields = fields == contract["fields"]
        same_hierarchy = hierarchy == contract["section_hierarchy"]
        same_field_sections = field_sections == _expected_field_sections(contract)
        check(same_sections, "section_parity", report_date, "section hierarchy/name/order mismatch")
        check(same_fields, "field_parity", report_date, "field inventory/label/order mismatch")
        check(same_hierarchy, "section_hierarchy_parity", report_date, "section nesting mismatch")
        check(same_field_sections, "field_section_parity", report_date, "field moved to a different section")
        if same_sections and same_fields and same_hierarchy and same_field_sections:
            structural_pass += 1

        field_ids = [item[0] for item in fields]
        phase_ok = "decision.regime" in field_ids
        chain_ok = all(item in field_ids for item in ("decision.f13", "decision.f15", "decision.f18"))
        allocation_ok = all(item in field_ids for item in ("portfolio.composition", "portfolio.total", "portfolio.rows", "portfolio.columns", "portfolio.cash_row"))
        f19_ok = "F19 EXECUTION" in page and "ACTION" in page and "CLASS" in page and "DIVERGENCE" in page
        macro_ok = all(item in field_ids for item in ("macro.narrative", "market.institutional_flow", "confirmation.us10y", "constraints.positioning_risk"))
        phase_coverage += phase_ok
        f_chain_coverage += chain_ok
        allocation_structure += allocation_ok
        f19_structure += f19_ok
        macro_structure += macro_ok
        check(phase_ok, "phase_structure", report_date, "REGIME/phase position missing")
        check(chain_ok, "decision_path_structure", report_date, "F13/F15/F18 structure missing")
        check(allocation_ok, "allocation_structure", report_date, "allocation container/header/cash row missing")
        check(f19_ok, "f19_structure", report_date, "F19 execution structure missing")
        check(macro_ok, "macro_market_constraint_structure", report_date, "macro/market/confirmation/constraint structure missing")

        source_text = (ROOT / record["source_path"]).read_text(encoding="utf-8")
        if record["data_as_of"]:
            check(date.fromisoformat(record["data_as_of"]) <= date.fromisoformat(report_date), "pit_clock", report_date, "future data-as-of")
        check(report_date in page, "report_date", report_date, "selected report date not rendered")

        matrix_fields = []
        for key, item in record["fields"].items():
            statuses[item["status"]] += 1
            matrix_fields.append({"field": key, "status": item["status"], "authority": item["authority"], "source_clock": item["source_clock"], "reason": item["reason"]})
            check(item["status"] in {"A", "B", "C"}, "provenance_class", report_date, f"{key}: invalid class")
            if item["status"] == "A":
                check(record["canonical_exact_clock"] and item["source_clock"] == record["data_as_of"], "canonical_clock", report_date, f"{key}: non-exact canonical binding")
            elif item["status"] == "B":
                check(item["authority"] in {record["source_path"], f"reports/engine_diagnostics_{report_date}.md"}, "persisted_authority", report_date, f"{key}: not bound to same-date persisted evidence")
            else:
                unavailable_causes[item["required_evidence"]] += 1
                unavailable_by_schema[record["source_schema"]] += 1
                unavailable_by_field[key] += 1
                ok = item["value"] == UNAVAILABLE and len(item.get("sources_checked", [])) >= 3 and item.get("reconstruction_possible") is False
                check(ok, "unavailable_proof", report_date, f"{key}: missing value or upstream absence evidence")
                if item["value"] != UNAVAILABLE or re.fullmatch(r"(?:0(?:\.0+)?%?|NEUTRAL|NORMAL|BALANCED|100%)", item["value"], re.I):
                    fabricated_defaults += 1
                    check(False, "fabricated_default", report_date, f"{key}: C field carries a default-like value")
        collections = {
            "portfolio.rows": record["sector_weights"][0]["status"] if record["sector_weights"] else "C",
            "f19.execution_rows": record["execution_rows"][0]["status"] if record["execution_rows"] else "C",
            "leadership.sector_rows": "B" if record.get("leadership_rows") else "C",
            "leadership.breadth_rows": "B" if record.get("breadth_rows") else "C",
        }
        collection_statuses.update(collections.values())
        coverage_matrix.append({
            "report_date": report_date, "data_as_of": record["data_as_of"],
            "source_schema": record["source_schema"], "fields": matrix_fields,
            "variable_collections": collections,
        })

        # Latent same-date evidence must not be mistaken for report-schema absence.
        phase_evidence = bool(re.search(r"(?im)^-?\s*(?:\*\*)?(?:Operational|Strategic) Phase(?:\*\*)?\s*:", source_text))
        if phase_evidence:
            check(record["fields"]["decision.regime"]["status"] != "C", "missed_upstream_evidence", report_date, "explicit historical Phase was not bound")
            check(not record["fields"]["decision.regime"]["value"].startswith("Controller:"), "semantic_prefix_collision", report_date, "Regime incorrectly bound to Regime Controller")
        allocation_evidence = bool(re.search(r"(?ms)18\.5\).*?\|\s*Sector\s*\|.*?Weight in Portfolio.*?\n\|\s*[^:-]", source_text))
        if allocation_evidence and not record["canonical_exact_clock"]:
            check(bool(record["sector_weights"]), "missed_upstream_evidence", report_date, "explicit F18.5 allocation table was not bound")
        execution_evidence = bool(re.search(r"(?ms)19\) Execution Layer.*?\|\s*Sector\s*\|\s*ETF\s*\|\s*Weight\s*\|\s*Action\s*\|.*?\n\|\s*[^:-]", source_text))
        if execution_evidence:
            check(bool(record["execution_rows"]), "missed_upstream_evidence", report_date, "explicit F19 rows were not bound")
        breadth_evidence = "RSP vs SPY" in source_text and "Yesterday:" in source_text and "Today:" in source_text
        if breadth_evidence:
            check(bool(record.get("breadth_rows")), "missed_upstream_evidence", report_date, "explicit breadth rows were not bound")

    # Known previous failure must now be sourced from its own persisted engine state.
    aug28 = records["2026-08-28"]
    expected_aug28 = {
        "decision.regime": "RISK-ON / REFLATION", "f13.risk_budget": "58",
        "f15.recommended_exposure": "52%", "f18.exposure_ceiling": "52.0%",
        "f18.allocated_equity": "50.6%", "f18.tactical_reserve": "1.4%", "f18.cash": "49.4%",
    }
    for key, expected_value in expected_aug28.items():
        check(aug28["fields"][key]["value"] == expected_value and aug28["fields"][key]["status"] == "B", "representative_semantics", "2026-08-28", f"{key}: wrong same-date legacy value")
    check(len(aug28["sector_weights"]) == 6, "representative_semantics", "2026-08-28", "F18 allocation rows missing")
    check(len(aug28["execution_rows"]) == 6, "representative_semantics", "2026-08-28", "F19 execution rows missing")
    check(len(aug28.get("breadth_rows", [])) == 4, "representative_semantics", "2026-08-28", "breadth rows missing")

    old_basic = records["2025-12-11"]
    check(not old_basic["data_as_of"], "representative_semantics", "2025-12-11", "invented Data as-of")
    check(all(old_basic["fields"][key]["status"] == "B" for key in ("cross.us10y", "cross.usd", "cross.oil", "cross.vix")), "representative_semantics", "2025-12-11", "explicit cross-asset values not preserved")
    check(all(old_basic["fields"][key]["status"] == "C" for key in ("decision.regime", "f13.risk_budget", "f15.recommended_exposure", "f18.exposure_ceiling")), "representative_semantics", "2025-12-11", "missing engine state was fabricated")

    jun22 = records["2026-06-22"]
    jun22_page = (site_dir / "history/2026-06-22.html").read_text(encoding="utf-8")
    check(jun22["canonical_exact_clock"] and jun22["data_as_of"] == "2026-06-18", "representative_semantics", "2026-06-22", "canonical replay clock mismatch")
    check(all(jun22["fields"][key]["status"] == "A" for key in ("f13.risk_budget", "f15.recommended_exposure", "f18.exposure_ceiling", "f18.allocated_equity", "f18.tactical_reserve", "f18.cash")), "representative_semantics", "2026-06-22", "canonical decision chain not bound")
    check("CANONICAL REPLAY · NOT THE ORIGINAL PUBLICATION" in jun22_page and "Authority difference disclosed" in jun22_page, "representative_semantics", "2026-06-22", "replay/publication separation hidden")
    check(re.search(r"Consumer Staples.*?7\.3%.*?Unavailable.*?Unavailable.*?Unavailable", jun22_page, re.DOTALL) is not None, "representative_semantics", "2026-06-22", "divergent original F19 was attached to canonical F18")

    sep02 = records["2026-09-02"]
    check(sep02["fields"]["f13.risk_budget"]["value"] == "25" and sep02["fields"]["f15.recommended_exposure"]["value"] == "20%", "representative_semantics", "2026-09-02", "same-date diagnostics F13/F15 not bound")
    check(sep02["fields"]["f13.risk_budget"]["authority"] == "reports/engine_diagnostics_2026-09-02.md", "representative_semantics", "2026-09-02", "F13 authority is not same-date diagnostics")
    check(len(sep02["sector_weights"]) == 3 and len(sep02["execution_rows"]) == 3, "representative_semantics", "2026-09-02", "transitional F18/F19 evidence not bound")

    sep12 = records[TEMPLATE_DATE]
    check(sep12["source_schema"] == "PM_V2_COMPLETE" and sep12["data_as_of"] == "2026-09-11", "current_pm_v2_regression", TEMPLATE_DATE, "native template identity/clock changed")
    check(sep12["fields"]["decision.regime"]["value"] == "SOFT RISK-OFF", "current_pm_v2_regression", TEMPLATE_DATE, "native REGIME semantic changed")
    check('data-reconstruction-contract=' not in template, "current_pm_v2_regression", TEMPLATE_DATE, "native template was replaced by reconstruction")

    old = reconstruction_audit(site_dir)
    check(old["verdict"] == "PASS", "reconstruction_v1_regression", "population", f"existing reconstruction verdict {old['verdict']}")
    check(old["legacy_reliability_v1"]["verdict"] == "PASS", "historical_reliability_v1_regression", "population", "existing public reliability failed")

    coverage = {
        "contract": CONTRACT_ID,
        "template_date": TEMPLATE_DATE,
        "calendar_dates": len(calendar_dates),
        "reports": len(reports),
        "field_inventory": len(FIELD_SPECS),
        "status_counts": dict(statuses),
        "variable_collection_status_counts": dict(collection_statuses),
        "unavailable_by_schema": dict(unavailable_by_schema),
        "unavailable_by_field": dict(unavailable_by_field),
        "unavailable_root_causes": dict(unavailable_causes),
        "matrix": coverage_matrix,
    }
    (site_dir / "historical-pm-v2-ui-coverage.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    representatives = []
    for report_date in REPRESENTATIVE_DATES:
        record = records[report_date]
        representatives.append({
            "report_date": report_date,
            "structural_parity": _pairs((site_dir / "history" / f"{report_date}.html").read_text(encoding="utf-8"), "data-ui-field") == contract["fields"],
            "data_as_of": record["data_as_of"],
            "source_schema": record["source_schema"],
            "field_classes": dict(Counter(item["status"] for item in record["fields"].values())),
            "sector_rows": len(record["sector_weights"]), "f19_rows": len(record["execution_rows"]),
        })

    return {
        "contract": CONTRACT_ID, "verdict": "PASS" if not issues else "FAIL",
        "template": {"date": TEMPLATE_DATE, "sections": len(contract["sections"]), "fields": len(contract["fields"])},
        "calendar_dates": len(calendar_dates), "reports": len(reports), "structural_parity": f"{structural_pass}/{len(dates)}",
        "phase_coverage": f"{phase_coverage}/{len(dates)}", "f13_f15_f18_structure": f"{f_chain_coverage}/{len(dates)}",
        "allocation_structure": f"{allocation_structure}/{len(dates)}", "f19_structure": f"{f19_structure}/{len(dates)}",
        "macro_market_constraint_structure": f"{macro_structure}/{len(dates)}",
        "field_provenance": dict(statuses), "unavailable": statuses["C"],
        "variable_collection_provenance": dict(collection_statuses),
        "unavailable_by_schema": dict(unavailable_by_schema),
        "unavailable_root_causes": dict(unavailable_causes), "fabricated_defaults": fabricated_defaults,
        "checks": checks, "existing_reconstruction_checks": old["field_level_checks"],
        "existing_reliability_checks": old["legacy_reliability_v1"]["checks"],
        "representative_dates": representatives, "failure_total": len(issues),
        "failure_classes": dict(failures), "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", type=Path, default=ROOT / "_site")
    parser.add_argument("--write-evidence", type=Path)
    args = parser.parse_args()
    result = audit(args.site_dir.resolve())
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.write_evidence:
        target = args.write_evidence if args.write_evidence.is_absolute() else ROOT / args.write_evidence
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
