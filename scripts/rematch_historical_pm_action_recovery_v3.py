from __future__ import annotations

import json
import re
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

from recover_pm_fields_from_actions import (
    REPO,
    WORKFLOW,
    parse_exact_pm_fields,
)

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "historical_pm_action_logs"

SOURCE = (
    ROOT
    / "data"
    / "audit"
    / "historical_pm_action_recovery_v2.json"
)

OUT = (
    ROOT
    / "data"
    / "audit"
    / "historical_pm_action_recovery_v3.json"
)


def gh_json(*args: str):
    p = subprocess.run(
        ["gh", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(p.stdout)


def iso_date(value: str) -> date:
    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).date()


def strong_evidence(
    log: str,
    report_date: str,
) -> tuple[int, list[str]]:

    target = f"daily_report_{report_date}.md"

    evidence: list[str] = []
    best = 0

    report_date_patterns = (
        re.compile(
            rf"\breport_date\s*\(KST\)\s*=\s*{re.escape(report_date)}",
            re.I,
        ),
        re.compile(
            rf"\breport_date\s*=\s*{re.escape(report_date)}",
            re.I,
        ),
        re.compile(
            rf"\bREPORT_DATE\s*[:=]\s*{re.escape(report_date)}",
        ),
    )

    generation_words = re.compile(
        r"written|saved|generated|created|"
        r"report file|latest=|latest report|create mode|"
        r"저장|생성|작성",
        re.I,
    )

    for raw in log.splitlines():

        line = raw.strip()

        # Strongest: generator explicitly declares report date.
        if any(p.search(line) for p in report_date_patterns):
            best = max(best, 100)
            evidence.append(line[:300])
            continue

        # Exact report filename is accepted ONLY when the same line says
        # this run wrote/saved/generated/selected that report.
        if target in line and generation_words.search(line):

            score = 90

            if "PM Report written" in line:
                score = 100

            elif "LATEST=" in line:
                score = 95

            elif "LATEST REPORT" in line:
                score = 95

            elif "create mode" in line:
                score = 85

            best = max(best, score)
            evidence.append(line[:300])

    return best, evidence


def main():

    original = json.loads(
        SOURCE.read_text(encoding="utf-8")
    )

    print("loading Actions metadata...")

    runs = gh_json(
        "run",
        "list",
        "--repo", REPO,
        "--workflow", WORKFLOW,
        "--limit", "1000",
        "--json",
        "databaseId,createdAt,conclusion,event",
    )

    metadata = {
        int(r["databaseId"]): r
        for r in runs
        if r.get("conclusion") == "success"
    }

    result = {}

    first_pass = 0
    strong_found = 0
    identical_tie = 0
    conflicts = 0
    unresolved = 0

    for report_date, old in sorted(original.items()):

        if old.get("match_stage") == "FIRST_PASS":

            result[report_date] = old
            first_pass += 1
            continue

        d = date.fromisoformat(report_date)

        candidates = []

        for path in CACHE.glob("*.log"):

            try:
                run_id = int(path.stem)
            except ValueError:
                continue

            meta = metadata.get(run_id)

            if not meta:
                continue

            created = iso_date(meta["createdAt"])

            # Time-zone boundary protection only.
            if created not in {
                d - timedelta(days=1),
                d,
                d + timedelta(days=1),
            }:
                continue

            log = path.read_text(
                encoding="utf-8",
                errors="replace",
            )

            score, evidence = strong_evidence(
                log,
                report_date,
            )

            if score == 0:
                continue

            candidates.append(
                {
                    "run_id": run_id,
                    "created_at": meta["createdAt"],
                    "event": meta.get("event"),
                    "score": score,
                    "evidence": evidence,
                    "values": parse_exact_pm_fields(log),
                }
            )

        if not candidates:

            result[report_date] = {
                "status": "UNRESOLVED",
                "match_stage": "V3_STRONG_ONLY",
                "values": {},
            }

            unresolved += 1
            print(report_date, "UNRESOLVED")
            continue

        max_score = max(
            c["score"]
            for c in candidates
        )

        top = [
            c for c in candidates
            if c["score"] == max_score
        ]

        if len(top) == 1:

            c = top[0]

            result[report_date] = {
                "status": "FOUND",
                "match_stage": "V3_STRONG",
                "run_id": c["run_id"],
                "created_at": c["created_at"],
                "event": c["event"],
                "score": c["score"],
                "evidence": c["evidence"],
                "values": c["values"],
            }

            strong_found += 1

            print(
                report_date,
                "FOUND_STRONG",
                f"run={c['run_id']}",
                f"score={c['score']}",
                f"fields={len(c['values'])}",
            )

            continue

        # Multiple equally strong runs:
        # Accept only if their recovered exact values are identical.
        signatures = {
            json.dumps(
                c["values"],
                ensure_ascii=False,
                sort_keys=True,
            )
            for c in top
        }

        if len(signatures) == 1:

            # Prefer scheduled run only as provenance pointer;
            # values themselves are identical.
            scheduled = [
                c for c in top
                if c.get("event") == "schedule"
            ]

            chosen = (
                scheduled[0]
                if scheduled
                else top[0]
            )

            result[report_date] = {
                "status": "FOUND",
                "match_stage": "V3_IDENTICAL_RUNS",
                "run_id": chosen["run_id"],
                "equivalent_run_ids": [
                    c["run_id"]
                    for c in top
                ],
                "score": max_score,
                "evidence": chosen["evidence"],
                "values": chosen["values"],
            }

            identical_tie += 1

            print(
                report_date,
                "FOUND_IDENTICAL_RUNS",
                f"runs={len(top)}",
                f"fields={len(chosen['values'])}",
            )

        else:

            result[report_date] = {
                "status": "CONFLICTING_RUNS",
                "match_stage": "V3_STRONG_ONLY",
                "candidates": [
                    {
                        "run_id": c["run_id"],
                        "created_at": c["created_at"],
                        "event": c["event"],
                        "score": c["score"],
                        "evidence": c["evidence"],
                        "values": c["values"],
                    }
                    for c in top
                ],
                "values": {},
            }

            conflicts += 1

            print(
                report_date,
                "CONFLICT",
                f"runs={len(top)}",
            )

    OUT.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("DONE V3")
    print("dates:", len(result))
    print("first-pass exact:", first_pass)
    print("v3 strong exact:", strong_found)
    print("identical-run exact:", identical_tie)
    print("conflicting runs:", conflicts)
    print("still unresolved:", unresolved)
    print(
        "total exact:",
        first_pass + strong_found + identical_tie,
    )
    print("output:", OUT)


if __name__ == "__main__":
    main()
