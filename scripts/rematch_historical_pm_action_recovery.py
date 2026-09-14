from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from recover_pm_fields_from_actions import parse_exact_pm_fields


ROOT = Path(__file__).resolve().parents[1]

CACHE_DIR = ROOT / ".cache" / "historical_pm_action_logs"

SOURCE = (
    ROOT
    / "data"
    / "audit"
    / "historical_pm_action_recovery.json"
)

OUT = (
    ROOT
    / "data"
    / "audit"
    / "historical_pm_action_recovery_v2.json"
)


DATE = r"\d{4}-\d{2}-\d{2}"


# Only explicit date evidence.
#
# Do NOT use:
# - neighboring dates
# - run creation date alone
# - market data dates
# - performance dates
# - arbitrary date strings
#
# A log is linked to report date D only when the report generator/log
# explicitly identifies D as its report date or report filename.
DATE_PATTERNS = (
    (
        "daily_report_filename",
        re.compile(
            rf"daily_report_({DATE})\.md",
            re.IGNORECASE,
        ),
    ),
    (
        "debug_report_date_kst",
        re.compile(
            rf"\breport_date\s*\(KST\)\s*=\s*({DATE})",
            re.IGNORECASE,
        ),
    ),
    (
        "report_date_assignment",
        re.compile(
            rf"\breport_date\s*=\s*({DATE})",
            re.IGNORECASE,
        ),
    ),
    (
        "report_date_label",
        re.compile(
            rf"\breport\s+date\s*[:=]\s*({DATE})",
            re.IGNORECASE,
        ),
    ),
    (
        "report_date_constant",
        re.compile(
            rf"\bREPORT_DATE\s*[:=]\s*({DATE})",
        ),
    ),
)


def extract_explicit_report_dates(
    log: str,
) -> dict[str, set[str]]:

    found: dict[str, set[str]] = defaultdict(set)

    for evidence_name, pattern in DATE_PATTERNS:
        for match in pattern.finditer(log):
            found[match.group(1)].add(evidence_name)

    return found


def main() -> None:

    if not SOURCE.exists():
        raise SystemExit(
            f"ABORT: source audit missing: {SOURCE}"
        )

    if not CACHE_DIR.exists():
        raise SystemExit(
            f"ABORT: cache missing: {CACHE_DIR}"
        )

    original = json.loads(
        SOURCE.read_text(encoding="utf-8")
    )

    cache_files = sorted(
        CACHE_DIR.glob("*.log")
    )

    print("cached logs:", len(cache_files))
    print("building local date index...")

    # date -> candidates
    index: dict[str, list[dict]] = defaultdict(list)

    for i, path in enumerate(cache_files, 1):

        try:
            run_id = int(path.stem)
        except ValueError:
            continue

        log = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        explicit_dates = extract_explicit_report_dates(log)

        for report_date, evidence in explicit_dates.items():

            index[report_date].append(
                {
                    "run_id": run_id,
                    "log_path": str(path),
                    "evidence": sorted(evidence),
                    "log": log,
                }
            )

        if i % 50 == 0:
            print(
                f"  scanned {i}/{len(cache_files)}"
            )

    result: dict[str, dict] = {}

    original_found = 0
    second_pass_found = 0
    ambiguous = 0
    unresolved = 0

    for report_date, old in sorted(original.items()):

        # Preserve already proven first-pass result.
        if old.get("status") == "FOUND":

            result[report_date] = {
                **old,
                "match_stage": "FIRST_PASS",
            }

            original_found += 1
            continue

        candidates = index.get(report_date, [])

        # Deduplicate same run if multiple patterns matched.
        by_run: dict[int, dict] = {}

        for candidate in candidates:
            run_id = candidate["run_id"]

            if run_id not in by_run:
                by_run[run_id] = candidate
            else:
                merged = set(
                    by_run[run_id]["evidence"]
                )
                merged.update(
                    candidate["evidence"]
                )

                by_run[run_id]["evidence"] = sorted(merged)

        unique = list(by_run.values())

        if len(unique) == 1:

            candidate = unique[0]

            values = parse_exact_pm_fields(
                candidate["log"]
            )

            result[report_date] = {
                "status": "FOUND",
                "match_stage": "SECOND_PASS",
                "run_id": candidate["run_id"],
                "date_evidence": candidate["evidence"],
                "values": values,
            }

            second_pass_found += 1

            print(
                f"{report_date} "
                f"FOUND_SECOND_PASS "
                f"run={candidate['run_id']} "
                f"fields={len(values)} "
                f"evidence={','.join(candidate['evidence'])}"
            )

        elif len(unique) > 1:

            result[report_date] = {
                "status": "AMBIGUOUS_EXACT_DATE",
                "match_stage": "SECOND_PASS",
                "candidates": [
                    {
                        "run_id": c["run_id"],
                        "evidence": c["evidence"],
                    }
                    for c in unique
                ],
                "values": {},
            }

            ambiguous += 1

            print(
                f"{report_date} "
                f"AMBIGUOUS "
                f"runs={len(unique)}"
            )

        else:

            result[report_date] = {
                "status": "UNRESOLVED",
                "match_stage": "SECOND_PASS",
                "values": {},
            }

            unresolved += 1

    OUT.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("DONE V2")
    print("dates:", len(result))
    print("first-pass exact:", original_found)
    print("second-pass exact:", second_pass_found)
    print("ambiguous exact-date:", ambiguous)
    print("still unresolved:", unresolved)
    print(
        "total exact:",
        original_found + second_pass_found,
    )
    print("output:", OUT)


if __name__ == "__main__":
    main()
