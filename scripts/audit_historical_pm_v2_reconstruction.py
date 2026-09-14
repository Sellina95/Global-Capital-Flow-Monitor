from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

try:
    from scripts.audit_public_historical_reliability import audit as audit_v1
    from scripts.historical_pm_v2_reconstruction import CONTRACT_ID, FIELD_SPECS, PARITY_PATH, REPORTS_DIR, ROOT, UNAVAILABLE, build_population, load_parity
except ModuleNotFoundError:
    from audit_public_historical_reliability import audit as audit_v1  # type: ignore
    from historical_pm_v2_reconstruction import CONTRACT_ID, FIELD_SPECS, PARITY_PATH, REPORTS_DIR, ROOT, UNAVAILABLE, build_population, load_parity  # type: ignore


DEFAULT_SITE_DIR = ROOT / "_site"
REPRESENTATIVE_DATES = ("2025-12-11", "2026-06-22", "2026-09-02", "2026-09-13")


def audit(site_dir: Path) -> dict:
    reports = sorted(REPORTS_DIR.glob("daily_report_????-??-??.md"))
    dates = [path.stem.removeprefix("daily_report_") for path in reports]
    population = build_population()
    expected = {record["report_date"]: record for record in population}
    parity, parity_hash = load_parity()
    issues: list[dict[str, str]] = []
    failures: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    conflict_fields: Counter[str] = Counter()
    conflict_reports: set[str] = set()
    checks = reconstructed = native = execution_count = sector_count = 0

    def check(ok: bool, failure_class: str, report_date: str, detail: str) -> None:
        nonlocal checks
        checks += 1
        if not ok:
            failures[failure_class] += 1
            issues.append({"failure_class": failure_class, "report_date": report_date, "detail": detail})

    manifest_path = site_dir / "historical-pm-v2-reconstruction.json"
    check(manifest_path.exists(), "missing_stale_broken_reconstruction", "population", "population manifest missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    check(manifest.get("contract") == CONTRACT_ID, "schema_contract_mismatch", "population", "wrong contract id")
    check([x.get("report_date") for x in manifest.get("reports", [])] == dates,
          "calendar_population_mismatch", "population", "manifest/report population mismatch")

    index = (site_dir / "index.html").read_text(encoding="utf-8")
    calendar_match = re.search(r"const availableDates\s*=\s*(\[[^;]+\])", index)
    calendar_dates = json.loads(calendar_match.group(1)) if calendar_match else []
    check(calendar_dates == dates, "calendar_population_mismatch", "population", "calendar/report population mismatch")

    for report_date in dates:
        record = expected[report_date]
        source_text = (ROOT / record["source_path"]).read_text(encoding="utf-8")
        page_path = site_dir / "history" / f"{report_date}.html"
        check(page_path.exists(), "missing_stale_broken_reconstruction", report_date, "historical route missing")
        if not page_path.exists():
            continue
        page = page_path.read_text(encoding="utf-8")
        check(report_date in page, "report_date_data_as_of_mismatch", report_date, "report date not displayed")
        if record["data_as_of"]:
            check(date.fromisoformat(record["data_as_of"]) <= date.fromisoformat(report_date),
                  "pit_clock_integrity", report_date, "future data-as-of")

        if record["source_schema"] == "PM_V2_COMPLETE":
            native += 1
            check('data-reconstruction-contract=' not in page, "current_pm_v2_regression", report_date,
                  "native PM V2 was replaced")
        else:
            reconstructed += 1
            check(f'data-reconstruction-contract="{CONTRACT_ID}"' in page,
                  "schema_contract_mismatch", report_date, "reconstruction marker missing")
            expected_notice = "CANONICAL REPLAY · NOT THE ORIGINAL PUBLICATION" if record["canonical_exact_clock"] else "PERSISTED-SOURCE RECONSTRUCTION"
            check(expected_notice in page, "authority_semantics_hidden", report_date, "top-of-page authority notice missing")
            match = re.search(r'<script type="application/json" id="historical-pm-v2-reconstruction-record">(.*?)</script>', page, re.DOTALL)
            check(bool(match), "field_provenance_missing", report_date, "embedded provenance missing")
            embedded = json.loads(match.group(1)) if match else {}
            check(embedded == record, "field_provenance_mismatch", report_date, "embedded record differs from rebuild")
            cockpit = page.split('<section class="panel reconstruction-contract"', 1)[0]
            check(
                not re.search(r'class="[^"]*pm-neutral[^"]*"[^>]*>\s*Unavailable\s*<', cockpit),
                "unavailable_semantic_presentation",
                report_date,
                "Unavailable is styled as genuine neutral",
            )
            check(
                not re.search(r'[🔴🟢🟡][^<]{0,32}Unavailable', cockpit),
                "unavailable_semantic_presentation",
                report_date,
                "Unavailable carries a market-state color icon",
            )
            unavailable_elements = re.findall(
                r'<(?:strong|span|b)([^>]*)>\s*Unavailable\s*</(?:strong|span|b)>',
                cockpit,
            )
            check(bool(unavailable_elements), "unavailable_semantic_presentation", report_date, "reconstruction has no marked unavailable elements")
            for attrs in unavailable_elements:
                check(
                    "pm-unavailable" in attrs and 'data-availability="unavailable"' in attrs,
                    "unavailable_semantic_presentation",
                    report_date,
                    "exact Unavailable element lacks dedicated class/data marker",
                )
            if not record["sector_weights"]:
                check(
                    "reconstruction-unavailable" in page
                    and "<strong>100%</strong><span>PORTFOLIO</span>" not in cockpit,
                    "fabricated_default_value",
                    report_date,
                    "absent allocation is rendered as a numeric portfolio",
                )
            if not record["execution_rows"] and record["sector_weights"]:
                portfolio = re.search(r'<div class="pm-portfolio-table"[^>]*>(.*?)</article>', cockpit, re.DOTALL)
                check(
                    bool(portfolio) and portfolio.group(1).count('data-availability="unavailable"') >= 4 * len(record["sector_weights"]),
                    "f19_final_state_consistency",
                    report_date,
                    "missing F19 evidence received action/class/divergence defaults",
                )
            # Public provenance/audit panel is intentionally not rendered.
            # Validate lossless source identity directly against repository authority.
            check(
                record["source_sha256"] == hashlib.sha256(source_text.encode()).hexdigest(),
                "lossless_source_regression",
                report_date,
                "persisted source hash mismatch",
            )
            for conflict in record.get("authority_conflicts", []):
                conflict_fields[conflict["field"]] += 1
                conflict_reports.add(report_date)
                check(
                    bool(conflict.get("canonical_replay")) and bool(conflict.get("persisted_publication")),
                    "authority_conflict_missing",
                    report_date,
                    f"{conflict['field']}: incomplete authority conflict record",
                )

        for key, item in record["fields"].items():
            statuses[item["status"]] += 1
            check(item["status"] in {"A", "B", "C"}, "schema_contract_mismatch", report_date, f"{key}: invalid class")
            check(bool(item["authority_sha256"] and item["reason"]), "field_provenance_missing", report_date, f"{key}: incomplete provenance")
            if item["status"] == "C":
                check(item["value"] == UNAVAILABLE, "fabricated_default_value", report_date, f"{key}: C carries value")
                check(
                    "Historical source unavailable" in item["reason"]
                    and len(item.get("sources_checked", [])) >= 3
                    and item.get("reconstruction_possible") is False,
                    "unavailable_semantics", report_date, f"{key}: absence proof missing",
                )
            elif item["status"] == "A":
                check(record["canonical_exact_clock"], "pit_clock_integrity", report_date, f"{key}: A without exact clock")
                check(record["data_as_of"] in parity, "pit_clock_integrity", report_date, f"{key}: nearest/noncanonical clock")
                check(item["authority"] == str(PARITY_PATH.relative_to(ROOT)) and item["authority_sha256"] == parity_hash,
                      "canonical_identity_mismatch", report_date, f"{key}: wrong frozen authority")
            else:
                diagnostics_authority = f"reports/engine_diagnostics_{report_date}.md"
                allowed = {record["source_path"]: record["source_sha256"]}
                diagnostics_path = ROOT / diagnostics_authority
                if diagnostics_path.exists():
                    allowed[diagnostics_authority] = hashlib.sha256(diagnostics_path.read_bytes()).hexdigest()
                check(item["authority"] in allowed and item["authority_sha256"] == allowed.get(item["authority"]),
                      "persisted_source_mismatch", report_date, f"{key}: wrong same-date persisted authority")
            if record["source_schema"] != "PM_V2_COMPLETE":
                # Field provenance is validated through the embedded reconstruction
                # record above; it is intentionally not exposed as a public table.
                check(
                    key in embedded.get("fields", {}),
                    "field_provenance_missing",
                    report_date,
                    f"{key}: missing from embedded reconstruction record",
                )

        if record["canonical_exact_clock"]:
            fields = record["fields"]
            number = lambda key: float(re.search(r"-?\d+(?:\.\d+)?", fields[key]["value"]).group())
            f15, allocated = number("f15.recommended_exposure"), number("f18.allocated_equity")
            reserve, cash = number("f18.tactical_reserve"), number("f18.cash")
            check(abs(allocated + reserve - f15) <= .11, "f13_f15_f18_consistency", report_date, "allocation + reserve != F15")
            check(abs(allocated + cash - 100) <= .11, "f13_f15_f18_consistency", report_date, "equity + cash != 100")
            check(record["canonical_signal_date"] == record["data_as_of"], "pit_clock_integrity", report_date, "signal clock mismatch")

        if record["sector_weights"]:
            total = sum(float(row["weight"].rstrip("%")) for row in record["sector_weights"])
            allocated_raw = record["fields"]["f18.allocated_equity"]["value"]
            allocated_match = re.fullmatch(r"(\d+(?:\.\d+)?)%", allocated_raw)
            check(bool(allocated_match), "f18_consistency", report_date, "sector weights lack an authoritative allocated-equity total")
            if allocated_match:
                check(abs(total - float(allocated_match.group(1))) <= .31, "f18_consistency", report_date, "sector weights do not reconcile")
            sector_count += len(record["sector_weights"])
            for row in record["sector_weights"]:
                check(html.escape(row["sector"]) in page and html.escape(row["weight"]) in page,
                      "displayed_field_mismatch", report_date, f"sector {row['sector']} not rendered")

        execution_count += len(record["execution_rows"])
        for row in record["execution_rows"]:
            for key in ("sector", "etf", "weight", "action", "classification", "divergence"):
                check(html.escape(row[key]) in page, "f19_final_state_consistency", report_date, f"F19 {row['sector']} {key} not rendered")

        if record["source_schema"] != "PM_V2_COMPLETE":
            for forbidden in ("No positive sector allocation.", "No canonical tactical rationale available.", ">—<"):
                check(forbidden not in page, "fabricated_default_value", report_date, f"renderer fallback present: {forbidden}")

    v1 = audit_v1(site_dir)
    check(v1["verdict"] == "PASS", "historical_reliability_v1_regression", "population", f"V1 verdict {v1['verdict']}")
    check(v1["failure_total"] == 0, "historical_reliability_v1_regression", "population", "V1 failures nonzero")

    representatives = []
    for report_date in REPRESENTATIVE_DATES:
        record = expected[report_date]
        representatives.append({
            "report_date": report_date, "source_schema": record["source_schema"],
            "data_as_of": record["data_as_of"] or "not recorded",
            "canonical_exact_clock": record["canonical_exact_clock"],
            "field_classes": dict(Counter(x["status"] for x in record["fields"].values())),
            "sector_weights": len(record["sector_weights"]), "f19_rows": len(record["execution_rows"]),
            "decision_chain": {key: record["fields"][key]["value"] for key in (
                "f13.risk_budget", "f15.recommended_exposure", "f18.exposure_ceiling",
                "f18.allocated_equity", "f18.tactical_reserve", "f18.cash")},
        })

    return {
        "contract": CONTRACT_ID, "verdict": "PASS" if not issues else "FAIL",
        "audited_calendar_dates": len(calendar_dates), "audited_reports": len(reports),
        "pm_v2_surface_coverage": {"reconstructed": reconstructed, "native_complete": native, "total": reconstructed + native},
        "canonical_exact_clock_reports": sum(x["canonical_exact_clock"] for x in population),
        "field_inventory_size": len(FIELD_SPECS), "field_provenance_population": dict(statuses),
        "field_level_checks": checks, "sector_weight_checks": sector_count,
        "f19_rows_checked": execution_count, "fabricated_default_values": failures.get("fabricated_default_value", 0),
        "authority_differences": {"reports": len(conflict_reports), "fields": sum(conflict_fields.values()), "by_field": dict(sorted(conflict_fields.items()))},
        "legacy_reliability_v1": {"verdict": v1["verdict"], "checks": v1["reconciled_displayed_fields_checks"], "failures": v1["failure_total"]},
        "representative_dates": representatives, "failure_total": len(issues),
        "failure_class_counts": dict(sorted(failures.items())), "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", type=Path, default=DEFAULT_SITE_DIR)
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
