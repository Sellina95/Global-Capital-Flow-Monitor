from __future__ import annotations

import json
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

from recover_pm_fields_from_actions import (
    REPO,
    WORKFLOW,
    parse_exact_pm_fields,
)

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
CACHE = ROOT / ".cache" / "historical_pm_action_logs"
OUT = ROOT / "data" / "audit" / "historical_pm_action_recovery.json"

CACHE.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)


def gh_json(*args: str):
    p = subprocess.run(
        ["gh", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(p.stdout)


def get_log(run_id: int) -> str:
    cache_file = CACHE / f"{run_id}.log"

    if cache_file.exists():
        return cache_file.read_text(errors="replace")

    p = subprocess.run(
        [
            "gh", "run", "view", str(run_id),
            "--repo", REPO,
            "--log",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    cache_file.write_text(p.stdout)
    return p.stdout


def run_date(value: str) -> date:
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).date()


def main():
    report_dates = sorted(
        p.stem.replace("daily_report_", "")
        for p in REPORTS.glob("daily_report_????-??-??.md")
    )

    print(f"REPORT DATES: {len(report_dates)}")

    runs = gh_json(
        "run",
        "list",
        "--repo", REPO,
        "--workflow", WORKFLOW,
        "--limit", "1000",
        "--json", "databaseId,createdAt,conclusion",
    )

    successful_runs = [
        r for r in runs
        if r.get("conclusion") == "success"
    ]

    result = {}

    for idx, report_date in enumerate(report_dates, 1):
        d = date.fromisoformat(report_date)
        marker = f"reports/daily_report_{report_date}.md"

        candidates = [
            r for r in successful_runs
            if run_date(r["createdAt"])
            in {d - timedelta(days=1), d, d + timedelta(days=1)}
        ]

        matched = None

        for run in candidates:
            run_id = int(run["databaseId"])

            try:
                log = get_log(run_id)
            except subprocess.CalledProcessError:
                continue

            if marker in log:
                matched = {
                    "run_id": run_id,
                    "created_at": run["createdAt"],
                    "values": parse_exact_pm_fields(log),
                }
                break

        if matched:
            result[report_date] = {
                "status": "FOUND",
                **matched,
            }

            print(
                f"[{idx}/{len(report_dates)}] "
                f"{report_date} FOUND "
                f"{len(matched['values'])} fields"
            )
        else:
            result[report_date] = {
                "status": "NO_EXACT_RUN",
                "values": {},
            }

            print(
                f"[{idx}/{len(report_dates)}] "
                f"{report_date} NO_EXACT_RUN"
            )

    OUT.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )

    found = sum(
        1 for x in result.values()
        if x["status"] == "FOUND"
    )

    print()
    print("DONE")
    print("dates:", len(result))
    print("exact runs found:", found)
    print("no exact run:", len(result) - found)
    print("output:", OUT)


if __name__ == "__main__":
    main()
