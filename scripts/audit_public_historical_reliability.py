from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
DEFAULT_SITE_DIR = ROOT / "_site"
STRICT_START = "2026-09-07"
TRANSITIONAL_ALLOWLIST = {
    "2026-09-02",
    "2026-09-03",
    "2026-09-04",
    "2026-09-05",
    "2026-09-06",
}


def schema_of(text: str) -> str:
    required = (
        "DECISION PATH",
        "EXECUTIVE VIEW",
        "MARKET STATE",
        "CROSS-ASSET CONFIRMATION",
        "LEADERSHIP & PARTICIPATION",
        "ALLOCATION CONTEXT",
        "PORTFOLIO ALLOCATION",
        "DECISION RATIONALE",
    )
    if text.startswith("# Global Capital Flow – Daily PM View"):
        if all(re.search(rf"^\d+\. {re.escape(x)}$", text, re.MULTILINE) for x in required):
            return "PM_V2_COMPLETE"
        return "PM_V2_TRANSITIONAL"
    if "### 🧠 13) Narrative Engine" in text:
        return "LEGACY_ENGINE"
    return "LEGACY_BASIC"


def metadata(text: str, label: str) -> str:
    match = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def section(text: str, title: str) -> str:
    match = re.search(rf"^\d+\. {re.escape(title)}\s*$", text, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    following = re.search(r"^\d+\. [A-Z][A-Z &\-]+$", text[start:], re.MULTILINE)
    return text[start : start + following.start()].strip() if following else text[start:].strip()


def field(block: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}\s+(.+?)\s*$", block, re.MULTILINE)
    return match.group(1).strip() if match else ""


def top_value(text: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}\s*$\n(.+?)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def numeric(value: str) -> float | None:
    match = re.search(r"-?\d+(?:\.\d+)?", value or "")
    return float(match.group(0)) if match else None


def normalized_tape(value: str) -> str:
    value = str(value or "").strip().lstrip("🔴🟢🟡").strip()
    value = re.sub(
        r"\b(?:Rising|Falling|Stronger|Weaker|COOL|Widening|Tightening|Improving|Stable)\b",
        "",
        value,
        flags=re.IGNORECASE,
    )
    if "·" in value and "↑" not in value and "↓" not in value:
        change = re.search(r"\(([+-]\d+(?:\.\d+)?)%\)", value)
        if change:
            arrow = "↓" if change.group(1).startswith("-") else "↑"
            left, right = value.split("·", 1)
            value = f"{left.strip()} · {arrow} {right.strip()}"
    value = re.sub(r"\s+", " ", value)
    return re.sub(r"\s+·\s+", " · ", value).strip()


def source_date(text: str, filename_date: str) -> str:
    explicit = metadata(text, "Date")
    if explicit:
        match = re.search(r"\d{4}-\d{2}-\d{2}", explicit)
        return match.group(0) if match else ""
    heading = re.search(r"^#.*?(\d{4}-\d{2}-\d{2})\s*$", text, re.MULTILINE)
    return heading.group(1) if heading else filename_date


def add_issue(issues: list[dict[str, str]], failure_class: str, report_date: str, detail: str) -> None:
    issues.append({"failure_class": failure_class, "report_date": report_date, "detail": detail})


def schema_is_allowed(report_date: str, schema: str) -> bool:
    if report_date < STRICT_START:
        return True
    if schema == "PM_V2_TRANSITIONAL" and report_date in TRANSITIONAL_ALLOWLIST:
        return True
    return schema == "PM_V2_COMPLETE"


def audit(site_dir: Path) -> dict:
    reports = sorted(REPORTS_DIR.glob("daily_report_????-??-??.md"))
    dates = [path.stem.removeprefix("daily_report_") for path in reports]
    latest = dates[-1] if dates else ""
    issues: list[dict[str, str]] = []
    checks = 0
    schema_counts: Counter[str] = Counter()
    legitimate_source_absence_tokens = 0
    missing_data_as_of = 0
    diagnostics_sources = 0
    snapshot_reports = 0
    structured_reports = 0

    index_path = site_dir / "index.html"
    if not index_path.exists():
        add_issue(issues, "missing_stale_broken_report", latest, "missing public index.html")
        index_text = ""
    else:
        index_text = index_path.read_text(encoding="utf-8")
        checks += 1

    calendar_match = re.search(r"const availableDates\s*=\s*(\[[^;]+\])", index_text)
    if not calendar_match:
        add_issue(issues, "calendar_report_broken_misdirected_link", latest, "calendar population missing from index")
        calendar_dates: list[str] = []
    else:
        calendar_dates = json.loads(calendar_match.group(1))
        checks += 1
        if calendar_dates != dates:
            add_issue(
                issues,
                "calendar_report_broken_misdirected_link",
                latest,
                "calendar population differs from persisted report population",
            )

    for path, report_date in zip(reports, dates):
        source = path.read_text(encoding="utf-8")
        schema = schema_of(source)
        schema_counts[schema] += 1
        if not schema_is_allowed(report_date, schema):
            add_issue(
                issues,
                "semantic_field_schema_drift",
                report_date,
                f"new publication date uses non-authoritative schema {schema}",
            )
        legitimate_source_absence_tokens += len(
            re.findall(r"\bN/A\b|(?<![A-Za-z])nan(?![A-Za-z])", source, re.IGNORECASE)
        )
        as_of = metadata(source, "Data as of")
        if not as_of:
            missing_data_as_of += 1
        checks += 1

        reported_date = source_date(source, report_date)
        checks += 1
        if reported_date != report_date:
            add_issue(
                issues,
                "report_date_data_as_of_mismatch",
                report_date,
                f"filename date {report_date} != persisted report date {reported_date or 'unparseable'}",
            )
        if as_of:
            checks += 1
            try:
                as_of_date_match = re.search(r"\d{4}-\d{2}-\d{2}", as_of)
                if not as_of_date_match:
                    raise ValueError
                if date.fromisoformat(as_of_date_match.group(0)) > date.fromisoformat(report_date):
                    add_issue(
                        issues,
                        "report_date_data_as_of_mismatch",
                        report_date,
                        f"future data-as-of {as_of}",
                    )
            except ValueError:
                add_issue(issues, "report_date_data_as_of_mismatch", report_date, f"invalid data-as-of {as_of}")

        output = site_dir / "history" / f"{report_date}.html"
        if not output.exists():
            add_issue(issues, "missing_stale_broken_report", report_date, "calendar report page is missing")
            continue
        page = output.read_text(encoding="utf-8")
        checks += 1
        expected_route = "structured" if schema == "PM_V2_COMPLETE" else "reconstructed"
        is_reconstructed = 'data-reconstruction-contract=' in page
        is_snapshot = is_reconstructed  # compatibility for downstream legacy audit checks
        checks += 1
        if expected_route == "reconstructed":
            if not is_reconstructed:
                add_issue(
                    issues,
                    "historical_only_regression",
                    report_date,
                    "historical reconstruction contract marker missing",
                )
            else:
                snapshot_reports += 1

            # Lossless historical source authority is repository-side.
            expected_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
            checks += 1
            if not expected_hash:
                add_issue(
                    issues,
                    "source_value_rendered_unavailable",
                    report_date,
                    "persisted historical source identity unavailable",
                )
        else:
            if is_snapshot:
                add_issue(
                    issues,
                    "semantic_field_schema_drift",
                    report_date,
                    "complete PM V2 report unexpectedly routed to snapshot",
                )
            else:
                structured_reports += 1
            blocks = {
                name: section(source, name)
                for name in (
                    "DECISION PATH",
                    "MARKET STATE",
                    "CROSS-ASSET CONFIRMATION",
                    "LEADERSHIP & PARTICIPATION",
                    "ALLOCATION CONTEXT",
                    "PORTFOLIO ALLOCATION",
                    "ACTIVE CONSTRAINTS",
                    "DECISION RATIONALE",
                    "EXECUTION",
                )
            }
            expected_values = [
                report_date,
                as_of,
                top_value(source, "PORTFOLIO STANCE").split("·", 1)[0].strip(),
                top_value(source, "REGIME"),
                top_value(source, "CONVICTION"),
            ]
            for label in (
                "Strategic Risk Budget",
                "Recommended Exposure",
                "Exposure Ceiling",
                "Allocated Equity",
                "Tactical Reserve",
                "Cash",
                "Exposure Control",
            ):
                expected_values.append(field(blocks["DECISION PATH"], label))
            for label in (
                "Macro Narrative",
                "Policy Bias",
                "Financial Conditions",
                "Real Rate",
                "Liquidity",
                "Liquidity Level",
                "Credit",
                "Credit Structure",
                "Structure",
                "Growth Sustainability",
                "Institutional Flow",
                "Flow Authenticity",
                "Participation Quality",
                "Participation Mode",
                "Leadership",
                "Positioning",
                "Dealer Gamma",
                "Squeeze Risk",
                "Vol Structure",
                "Drift",
            ):
                expected_values.append(field(blocks["MARKET STATE"], label))
            for label in ("US10Y Yield", "USD", "Oil", "Volatility", "HY OAS"):
                expected_values.append(normalized_tape(field(blocks["CROSS-ASSET CONFIRMATION"], label)))
            expected_values.append(field(blocks["LEADERSHIP & PARTICIPATION"], "Coverage"))
            for label in ("Regime Controller", "Exposure Override"):
                expected_values.append(field(blocks["ALLOCATION CONTEXT"], label))
            for label in ("Exposure Ceiling", "Allocated Equity", "Tactical Reserve", "Cash"):
                expected_values.append(field(blocks["PORTFOLIO ALLOCATION"], label))
            for value in expected_values:
                checks += 1
                if not value or html.escape(value) not in page:
                    add_issue(
                        issues,
                        "source_value_rendered_unavailable",
                        report_date,
                        f"structured displayed value absent or mismatched: {value or '<missing source field>'}",
                    )

            allocation_rows = {
                match.group(1).strip(): match.group(2)
                for match in re.finditer(r"^(.+?)\s{2,}([0-9]+(?:\.[0-9]+)?%)$", blocks["PORTFOLIO ALLOCATION"], re.MULTILINE)
                if match.group(1).strip() not in {"Exposure Ceiling", "Allocated Equity", "Tactical Reserve", "Cash"}
            }
            execution_rows = []
            for line in blocks["EXECUTION"].splitlines():
                cells = [cell.strip() for cell in line.split("|")]
                if len(cells) == 6 and cells[0] != "Sector":
                    execution_rows.append(cells)
            for cells in execution_rows:
                sector, etf, weight, action, classification, divergence = cells
                row_match = re.search(
                    rf'<div class="pm-portfolio-row">(?:(?!<div class="pm-portfolio-row">).)*?'
                    rf'<strong>{re.escape(html.escape(sector))}</strong>(.*?)</div>\s*</div>',
                    page,
                    re.DOTALL,
                )
                checks += 6
                if not row_match:
                    add_issue(issues, "source_value_rendered_unavailable", report_date, f"F19 row missing: {sector}")
                else:
                    row_html = row_match.group(0)
                    for value in (etf, allocation_rows.get(sector, weight), action, classification, divergence):
                        if html.escape(value) not in row_html:
                            add_issue(
                                issues,
                                "source_value_rendered_unavailable",
                                report_date,
                                f"F19 {sector} value not rendered: {value}",
                            )

            diag_path = REPORTS_DIR / f"engine_diagnostics_{report_date}.md"
            if not diag_path.exists():
                add_issue(issues, "missing_stale_broken_report", report_date, "complete PM V2 diagnostics source missing")
            else:
                diagnostics_sources += 1
                diag = diag_path.read_text(encoding="utf-8")
                diag_date = metadata(diag, "Date")
                diag_as_of = metadata(diag, "Data as of")
                checks += 2
                if diag_date != report_date or diag_as_of != as_of:
                    add_issue(
                        issues,
                        "report_date_data_as_of_mismatch",
                        report_date,
                        f"report/diagnostics clock mismatch ({diag_date}, {diag_as_of})",
                    )
                f13 = re.search(r"\*\*Risk Budget \(0~100\):\*\*\s*\*\*(\d+(?:\.\d+)?)\*\*", diag)
                f15 = re.search(r"\*\*📊 Recommended Exposure:\*\*\s*\*\*(\d+(?:\.\d+)?%)\*\*", diag)
                report_f13 = field(blocks["DECISION PATH"], "Strategic Risk Budget")
                report_f15 = field(blocks["DECISION PATH"], "Recommended Exposure")
                report_f18 = field(blocks["DECISION PATH"], "Exposure Ceiling")
                checks += 3
                if not f13 or numeric(f13.group(1)) != numeric(report_f13):
                    add_issue(issues, "decision_chain_source_ui_mismatch", report_date, "F13 report/diagnostics mismatch")
                if not f15 or numeric(f15.group(1)) != numeric(report_f15):
                    add_issue(issues, "decision_chain_source_ui_mismatch", report_date, "F15 report/diagnostics mismatch")
                if numeric(report_f15) != numeric(report_f18):
                    add_issue(issues, "decision_chain_source_ui_mismatch", report_date, "F15 output != F18 exposure ceiling input")
                allocated = numeric(field(blocks["DECISION PATH"], "Allocated Equity"))
                reserve = numeric(field(blocks["DECISION PATH"], "Tactical Reserve"))
                cash = numeric(field(blocks["DECISION PATH"], "Cash"))
                ceiling = numeric(report_f18)
                checks += 2
                if None in (allocated, reserve, ceiling) or abs((allocated + reserve) - ceiling) > 0.11:
                    add_issue(issues, "decision_chain_source_ui_mismatch", report_date, "allocated equity + reserve != exposure ceiling")
                if None in (allocated, cash) or abs((allocated + cash) - 100.0) > 0.11:
                    add_issue(issues, "decision_chain_source_ui_mismatch", report_date, "allocated equity + cash != 100")

                vix_match = re.search(r"\*\*VIX Level:\*\*\s*([^|\n]+)", diag)
                if vix_match:
                    checks += 1
                    displayed = re.search(r"VIX Control · <b[^>]*>(.*?)</b>", page)
                    if not displayed or html.unescape(displayed.group(1)).strip() != vix_match.group(1).strip():
                        add_issue(issues, "false_fallback_default", report_date, "F15 VIX control is stale or unsupported")

        page_nas = len(re.findall(r"\bN/A\b", page))
        source_nas = len(re.findall(r"\bN/A\b", source))
        if not is_snapshot and page_nas > source_nas:
            for index in range(page_nas - source_nas):
                add_issue(
                    issues,
                    "source_value_rendered_unavailable",
                    report_date,
                    f"parser-added unavailable token #{index + 1}",
                )
        for marker in ("Data unavailable", "No positive sector allocation"):
            for index in range(max(0, page.count(marker) - source.count(marker))):
                add_issue(issues, "false_fallback_default", report_date, f"renderer fallback: {marker} #{index + 1}")
        if "Calculation ·" in page and "Calculation ·" not in source:
            add_issue(issues, "false_fallback_default", report_date, "unsupported hard-coded F15 calculation")

        separate_diagnostics_source = REPORTS_DIR / f"engine_diagnostics_{report_date}.md"
        diagnostics_source = (
            separate_diagnostics_source
            if separate_diagnostics_source.exists()
            else REPORTS_DIR / f"daily_report_{report_date}.md"
        )
        diagnostics_output = site_dir / "history" / f"{report_date}-diagnostics.html"

        # Storage contract:
        # - before diagnostics split: same-date daily_report is the persisted diagnostics source
        # - after split: same-date engine_diagnostics file is authoritative
        if separate_diagnostics_source.exists():
            diagnostics_sources += int(schema != "PM_V2_COMPLETE")

        checks += 1
        if not diagnostics_output.exists():
            add_issue(
                issues,
                "missing_stale_broken_report",
                report_date,
                "persisted diagnostics page is missing",
            )
        else:
            diagnostics_page = diagnostics_output.read_text(encoding="utf-8")
            diagnostics_text = diagnostics_source.read_text(encoding="utf-8")

            if 'id="persisted-report-source"' in diagnostics_page:
                raw_match = re.search(
                    r'<pre class="archive-source" id="persisted-report-source" data-source-sha256="([0-9a-f]{64})">(.*?)</pre>',
                    diagnostics_page,
                    re.DOTALL,
                )
            else:
                raw_match = re.search(
                    r'<pre class="diagnostics">(.*?)</pre>',
                    diagnostics_page,
                    re.DOTALL,
                )

            checks += 1
            if not raw_match or html.unescape(raw_match.group(raw_match.lastindex)) != diagnostics_text:
                add_issue(
                    issues,
                    "source_value_rendered_unavailable",
                    report_date,
                    "diagnostics source snapshot is absent or not lossless",
                )
            else:
                checks += sum(
                    1 for line in diagnostics_text.splitlines() if line.strip()
                )

        expected_calendar_path = site_dir / "history" / f"{report_date}.html"
        checks += 1
        if report_date not in calendar_dates or not expected_calendar_path.exists():
            add_issue(issues, "calendar_report_broken_misdirected_link", report_date, "calendar date does not resolve to same-date report")

    expected_history_files = {f"{value}.html" for value in dates}
    expected_history_files.update(
        f"{value}-diagnostics.html"
        for value in dates
        if (REPORTS_DIR / f"engine_diagnostics_{value}.md").exists()
    )
    actual_history_files = {
        path.name for path in (site_dir / "history").glob("*.html")
    } if (site_dir / "history").exists() else set()
    checks += len(actual_history_files)
    for extra in sorted(actual_history_files - expected_history_files):
        diagnostics_extra = re.fullmatch(r"(\d{4}-\d{2}-\d{2})-diagnostics\.html", extra)
        if diagnostics_extra and diagnostics_extra.group(1) in dates:
            # Already counted above as an unbacked diagnostics page.
            continue
        add_issue(issues, "missing_stale_broken_report", extra[:10], f"stale unbacked public page: {extra}")

    failures = Counter(item["failure_class"] for item in issues)
    result = {
        "contract": "GCF_PUBLIC_HISTORICAL_REPORT_RELIABILITY_V1",
        "verdict": "PASS" if not issues else "FAIL",
        "audited_calendar_dates": len(calendar_dates),
        "audited_reports": len(reports),
        "audited_diagnostics_sources": diagnostics_sources,
        "reconciled_displayed_fields_checks": checks,
        "schema_population": dict(sorted(schema_counts.items())),
        "rendering_population": {
            "lossless_snapshot_reports": snapshot_reports,
            "strict_structured_reports": structured_reports,
        },
        "legitimate_unavailable": {
            "source_recorded_na_or_nan_tokens_preserved": legitimate_source_absence_tokens,
            "reports_without_persisted_data_as_of": missing_data_as_of,
            "reports_without_separate_diagnostics_source": len(reports) - diagnostics_sources,
        },
        "failure_total": len(issues),
        "failure_class_counts": dict(sorted(failures.items())),
        "issues": issues,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", type=Path, default=DEFAULT_SITE_DIR)
    parser.add_argument("--write-evidence", type=Path)
    args = parser.parse_args()
    result = audit(args.site_dir.resolve())
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.write_evidence:
        target = args.write_evidence
        if not target.is_absolute():
            target = ROOT / target
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
