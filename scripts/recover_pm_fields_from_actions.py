from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from datetime import date, timedelta


REPO = "Sellina95/Global-Capital-Flow-Monitor"
WORKFLOW = "daily-macro.yml"


def gh_json(*args: str):
    p = subprocess.run(
        ["gh", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(p.stdout)


def gh_text(*args: str) -> str:
    p = subprocess.run(
        ["gh", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return p.stdout


def find_run_for_report_date(report_date: str) -> tuple[int, int, str]:
    """
    Find the exact Daily Macro Report run that generated
    reports/daily_report_<report_date>.md.

    Uses gh run list instead of the brittle Actions API created-range filter.
    """
    target_marker = f"reports/daily_report_{report_date}.md"

    # Usually report date == workflow calendar date.
    # Search the date itself plus +/- 1 day for UTC/KST boundary safety.
    d = date.fromisoformat(report_date)

    candidate_dates = [
        d - timedelta(days=1),
        d,
        d + timedelta(days=1),
    ]

    seen = set()

    for candidate_date in candidate_dates:
        try:
            runs = gh_json(
                "run",
                "list",
                "--repo", REPO,
                "--workflow", WORKFLOW,
                "--created", candidate_date.isoformat(),
                "--limit", "100",
                "--json", "databaseId,conclusion,createdAt",
            )
        except subprocess.CalledProcessError:
            continue

        for run in runs:
            run_id = int(run["databaseId"])

            if run_id in seen:
                continue
            seen.add(run_id)

            if run.get("conclusion") != "success":
                continue

            try:
                log = gh_text(
                    "run",
                    "view",
                    str(run_id),
                    "--repo", REPO,
                    "--log",
                )
            except subprocess.CalledProcessError:
                continue

            if target_marker not in log:
                continue

            # Job id is informational only here.
            jobs = gh_json(
                "api",
                f"/repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100",
            ).get("jobs", [])

            job_id = int(jobs[0]["id"]) if jobs else 0

            return run_id, job_id, log

    raise SystemExit(
        f"ABORT: no exact Actions log found for report date {report_date}"
    )

def parse_exact_pm_fields(log: str) -> dict[str, str]:
    """
    Recover ONLY explicit values printed by the historical engine.
    No recalculation and no semantic inference.
    """
    out: dict[str, str] = {}

    # ------------------------------------------------------------
    # Participation Quality / Mode
    # Example:
    # [DEBUG][18_PARTICIPATION_META]
    # {'participation_quality': 'COMPRESSED_OR_FAILED',
    #  'participation_quality_score': -5,
    #  'participation_mode': 'FAILED_BREADTH_MODE'}
    # ------------------------------------------------------------
    m = re.search(
        r"\[DEBUG\]\[18_PARTICIPATION_META\]\s*(\{[^\n]+\})",
        log,
    )
    if m:
        try:
            payload = ast.literal_eval(m.group(1))
            q = payload.get("participation_quality")
            mode = payload.get("participation_mode")

            if q:
                out["Participation Quality"] = str(q)
            if mode:
                out["Participation Mode"] = str(mode)
        except (ValueError, SyntaxError):
            pass

    # ------------------------------------------------------------
    # Squeeze Risk / Vol Structure
    # Example:
    # [DEBUG][18_MARKET_QUALITY_CONTEXT]
    # {'squeeze_risk': 'HIGH', ..., 'vol_structure': 'COMPRESSION'}
    # ------------------------------------------------------------
    m = re.search(
        r"\[DEBUG\]\[18_MARKET_QUALITY_CONTEXT\]\s*(\{[^\n]+\})",
        log,
    )
    if m:
        try:
            payload = ast.literal_eval(m.group(1))

            if payload.get("squeeze_risk"):
                out["Squeeze Risk"] = str(payload["squeeze_risk"])

            if payload.get("vol_structure"):
                out["Vol Structure"] = str(payload["vol_structure"])

            if payload.get("leadership_state"):
                out["Leadership"] = str(payload["leadership_state"])

            if payload.get("positioning_state"):
                out["Positioning"] = str(payload["positioning_state"])
        except (ValueError, SyntaxError):
            pass

    # ------------------------------------------------------------
    # Final state
    # ------------------------------------------------------------
    m = re.search(
        r"\[DEBUG\]\[FINAL_STATE FIXED\]\s*FINAL_STATE\s*=\s*(\{[^\n]+\})",
        log,
    )
    if m:
        try:
            payload = ast.literal_eval(m.group(1))

            mapping = {
                "macro_narrative": "Macro Narrative",
                "policy_bias_line": "Policy Bias",
                "liquidity_level_bucket": "Liquidity Level",
                "structure_tag": "Structure",
                "flow_state": "Institutional Flow",
                "pos_z": "Positioning Z",
                "drift_state": "Drift",
                "risk_budget": "Strategic Risk Budget",
            }

            for source_key, target_label in mapping.items():
                value = payload.get(source_key)
                if value is not None:
                    out[target_label] = str(value)

            cross = payload.get("cross_asset_tape")
            if isinstance(cross, dict):
                if cross.get("HY_OAS_LEVEL") is not None:
                    out["HY OAS"] = str(cross["HY_OAS_LEVEL"])
        except (ValueError, SyntaxError):
            pass

    # ------------------------------------------------------------
    # Allocated Equity / Cash
    # ------------------------------------------------------------
    m = re.search(
        r"\[DEBUG\]\[18_ALLOCATED_EQUITY\]\s*([^\n]+)",
        log,
    )
    if m:
        out["Allocated Equity"] = m.group(1).strip()

    m = re.search(
        r"\[DEBUG\]\[18_CASH_WEIGHT\]\s*([^\n]+)",
        log,
    )
    if m:
        out["Cash"] = m.group(1).strip()

    # ------------------------------------------------------------
    # Dealer Gamma
    # Preserve exact historical engine output.
    # ------------------------------------------------------------
    m = re.search(
        r"gamma_state['\"]?\s*:\s*['\"]([^'\"]+)['\"]",
        log,
    )
    if m:
        out["Dealer Gamma"] = m.group(1).strip()

    return out


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "usage: python scripts/recover_pm_fields_from_actions.py YYYY-MM-DD"
        )

    report_date = sys.argv[1]

    run_id, job_id, log = find_run_for_report_date(report_date)
    values = parse_exact_pm_fields(log)

    result = {
        "report_date": report_date,
        "workflow_run_id": run_id,
        "job_id": job_id,
        "recovered_exact_values": values,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
