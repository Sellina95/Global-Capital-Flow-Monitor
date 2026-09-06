from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "canonical_release_baseline_v1"
)

EXPECTED_TAXONOMY_HASH = (
    "cd7174ea8ec93115b4fc9902fd55fe2b9ba443199929b01eae2bc4db4fb70bf3"
)
EXPECTED_MAPPING_HASH = (
    "6ef7cba1e196fbb067385a2acc20e193adfd357d98669d74c3a745907e47d225"
)

# G1 certifies immutable release objects, not moving branch names.  Keeping
# full object IDs here also makes --verify-only stable after this audit tool
# itself is committed on top of the research baseline.
PRODUCTION_REF = "58f270267bba502b5831a60d8e8a2a375f55f7ef"
RESEARCH_REF = "7b4c324b27d6a19af3ef61852020da70cc7fe8c2"

PRODUCTION_DECISION_FILES = [
    "filters/strategist_filters.py",
    "portfolio/save_portfolio.py",
]

PRODUCTION_REFERENCE_FILES = [
    "scripts/generate_report.py",
]

RESEARCH_ADAPTER_FILES = [
    "scripts/backtest/run_backtest.py",
    "scripts/backtest/market_data_builder.py",
    "scripts/backtest/filter13_execution_chain.py",
    "scripts/backtest/historical_execution_contract.py",
    "scripts/backtest/institutional_backtest.py",
]

DATA_AND_SPEC_FILES = [
    (
        "data/backtest/pit_safe/master_panel_pit_safe_final.csv",
        "PIT_INPUT_PANEL",
    ),
    (
        "data/backtest/results/macro_v4_research_classifier_v1/"
        "macro_v4_classifier_daily.csv",
        "V4_INTERVENTION_CONTRACT",
    ),
    (
        "data/backtest/results/macro_v4_candidate_taxonomy_spec_v1/"
        "macro_v4_candidate_taxonomy_spec.json",
        "FROZEN_TAXONOMY_SPEC",
    ),
    (
        "data/backtest/results/macro_v4_portfolio_mapping_spec_v1/"
        "macro_v4_portfolio_mapping_spec.json",
        "FROZEN_MAPPING_SPEC",
    ),
    (
        "data/backtest/results/final_13_15_18_parity_closeout/"
        "final_13_15_18_parity_daily.csv",
        "FROZEN_PARITY_BASELINE",
    ),
]

EVIDENCE_FILES = [
    "data/backtest/results/full_value_execution_closure_summary.txt",
    "data/backtest/results/pit_repair_integrity_final_summary.txt",
    "data/backtest/results/risk_controls_correct_contract_summary.txt",
    "data/backtest/results/final_13_15_18_parity_closeout/"
    "final_13_15_18_parity_summary.txt",
]

KNOWN_EXCEPTIONS = [
    {
        "exception_id": "SOVEREIGN_VINTAGE_2008_2013",
        "status": "DOCUMENTED_LIMITATION",
        "scope": ["KR10Y", "JP10Y", "DE10Y", "IL10Y"],
        "period": "2008-01-01 through pre-2013 ALFRED availability",
        "description": (
            "Historical vintage availability remains unverified where the "
            "authoritative ALFRED vintage evidence is unavailable."
        ),
    }
]

CLAIM_APPLICABILITY = [
    {
        "claim": "#1 Point-in-Time / Look-ahead Integrity",
        "status": "CONDITIONAL",
        "reason": "Pinned to this panel and subject to the sovereign-vintage exception.",
    },
    {
        "claim": "#2 Production <-> Backtest Parity",
        "status": "CONDITIONAL",
        "reason": "Valid only for the pinned decision surfaces, adapters, data, and artifacts.",
    },
    {
        "claim": "#3 Data Revision / Release Lag",
        "status": "CONDITIONAL",
        "reason": "Pinned PIT repair remains subject to the documented sovereign exception.",
    },
    {
        "claim": "#4 Historical Universe / Survivorship",
        "status": "CONDITIONAL",
        "reason": "Pinned to the recorded historical panel and parity population.",
    },
    {
        "claim": "#5 Signal -> Risk -> Exposure -> Allocation Causality",
        "status": "STALE_PENDING_RERUN",
        "reason": "G4 state/clock integrity must close before causal results are reusable.",
    },
    {
        "claim": "#12 Risk Controls / Invariants",
        "status": "CONDITIONAL",
        "reason": "The arithmetic result remains pinned to the recorded 4,645-row replay.",
    },
    {
        "claim": "#14 Research <-> Production Separation",
        "status": "CURRENT",
        "reason": "Separate branches and minimal promotion records are present.",
    },
]


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ref_bytes(ref: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Missing Git object {ref}:{path}: "
            f"{result.stderr.decode(errors='replace').strip()}"
        )
    return result.stdout


def ref_blob_sha(ref: str, path: str) -> str:
    return run_git("rev-parse", f"{ref}:{path}")


def file_row(ref: str, path: str, role: str) -> dict[str, Any]:
    payload = ref_bytes(ref, path)
    return {
        "path": path,
        "role": role,
        "ref": ref,
        "git_blob_sha": ref_blob_sha(ref, path),
        "sha256": sha256_bytes(payload),
        "size_bytes": len(payload),
        "status": "PRESENT",
    }


def csv_metadata(path: Path) -> dict[str, Any]:
    frame = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    result: dict[str, Any] = {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
    }

    for column in ("date", "signal_date", "execution_date"):
        if column not in frame.columns:
            continue
        parsed = pd.to_datetime(frame[column], errors="coerce")
        valid = parsed.dropna()
        result[f"{column}_first"] = (
            valid.min().strftime("%Y-%m-%d") if not valid.empty else None
        )
        result[f"{column}_last"] = (
            valid.max().strftime("%Y-%m-%d") if not valid.empty else None
        )

    return result


def semantic_spec_hashes(spec: Any) -> set[str]:
    payloads = [
        json.dumps(
            spec,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        json.dumps(
            spec,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
    ]
    return {sha256_bytes(payload.encode("utf-8")) for payload in payloads}


def verify_frozen_spec(path: Path, expected_hash: str) -> dict[str, Any]:
    artifact = json.loads(path.read_text(encoding="utf-8"))
    embedded = str(artifact.get("sha256", ""))
    computed = semantic_spec_hashes(artifact.get("spec"))
    return {
        "path": str(path.relative_to(ROOT)),
        "expected_hash": expected_hash,
        "embedded_hash": embedded,
        "semantic_hash_verified": embedded in computed,
        "expected_hash_verified": embedded == expected_hash,
        "status": (
            "PASS"
            if embedded == expected_hash and embedded in computed
            else "FAIL"
        ),
    }


ALLOWED_OBSERVABILITY_KEYS = {
    "FILTER14_STATUS",
    "FILTER14_ACTION",
    "FILTER14_EXPLANATION",
    "FILTER15_BRAKE_DRIVERS",
    "FILTER15_POSITIONING_NOTES",
    "FILTER15_HARD_DEADMAN",
    "FILTER15_HARD_DEADMAN_REASON",
    "FILTER15_RISK_COMPRESSION",
    "FILTER15_COMPRESSION_REASON",
    "FILTER15_VOL_STATE",
    "STYLE_TILT",
    "FACTOR_LAYER",
    "PM_FINAL_ALLOCATION",
    "FILTER18_PARTICIPATION_QUALITY",
    "FILTER18_PARTICIPATION_MODE",
    "FILTER18_EXPOSURE_OVERRIDE",
    "FILTER18_REBALANCE_ACTIONS",
    "FILTER19_ETF_PLAN",
}


def assigned_market_data_key(node: ast.stmt) -> str | None:
    if not isinstance(node, (ast.Assign, ast.AnnAssign)):
        return None
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    if len(targets) != 1:
        return None
    target = targets[0]
    if not isinstance(target, ast.Subscript):
        return None
    if not isinstance(target.value, ast.Name) or target.value.id != "market_data":
        return None
    value = target.slice
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return None


class RemoveAllowlistedObservability(ast.NodeTransformer):
    def visit_Assign(self, node: ast.Assign) -> ast.AST | None:
        if assigned_market_data_key(node) in ALLOWED_OBSERVABILITY_KEYS:
            return None
        return self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST | None:
        if assigned_market_data_key(node) in ALLOWED_OBSERVABILITY_KEYS:
            return None
        return self.generic_visit(node)


def normalized_ast(payload: bytes, remove_observability: bool) -> str:
    tree = ast.parse(payload.decode("utf-8"))
    if remove_observability:
        tree = RemoveAllowlistedObservability().visit(tree)
        ast.fix_missing_locations(tree)
    return ast.dump(tree, annotate_fields=True, include_attributes=False)


def classify_decision_diff(path: str) -> dict[str, Any]:
    production = ref_bytes(PRODUCTION_REF, path)
    research = ref_bytes(RESEARCH_REF, path)

    if production == research:
        return {
            "path": path,
            "classification": "IDENTICAL",
            "decision_impact": "NONE",
            "authorized": True,
            "evidence": "Byte-identical Git content.",
        }

    if path == "filters/strategist_filters.py":
        production_ast = normalized_ast(production, remove_observability=True)
        research_ast = normalized_ast(research, remove_observability=True)
        if production_ast == research_ast:
            return {
                "path": path,
                "classification": "ALLOWLISTED_OBSERVABILITY_ONLY",
                "decision_impact": "NONE",
                "authorized": True,
                "evidence": (
                    "AST identity after removing only the explicitly allowlisted "
                    "market_data presentation/diagnostic assignments."
                ),
            }

    return {
        "path": path,
        "classification": "UNKNOWN",
        "decision_impact": "UNRESOLVED",
        "authorized": False,
        "evidence": "Non-identical decision surface was not allowlisted.",
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"Refusing to write empty CSV: {path}")
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify that regenerated content equals existing artifacts.",
    )
    args = parser.parse_args()

    production_sha = run_git("rev-parse", PRODUCTION_REF)
    research_sha = run_git("rev-parse", RESEARCH_REF)
    release_id = (
        f"gcfm-g1-{production_sha[:7]}-{research_sha[:7]}-pit-v1"
    )

    surface_rows: list[dict[str, Any]] = []
    for path in PRODUCTION_DECISION_FILES:
        surface_rows.append(file_row(PRODUCTION_REF, path, "PRODUCTION_DECISION"))
        surface_rows.append(file_row(RESEARCH_REF, path, "RESEARCH_DECISION"))
    for path in PRODUCTION_REFERENCE_FILES:
        surface_rows.append(
            file_row(PRODUCTION_REF, path, "PRODUCTION_ORCHESTRATION_REFERENCE")
        )
        surface_rows.append(
            file_row(RESEARCH_REF, path, "RESEARCH_ORCHESTRATION_REFERENCE")
        )
    for path in RESEARCH_ADAPTER_FILES:
        surface_rows.append(file_row(RESEARCH_REF, path, "HISTORICAL_ADAPTER"))
    for path, role in DATA_AND_SPEC_FILES:
        row = file_row(RESEARCH_REF, path, role)
        local_path = ROOT / path
        if path.endswith(".csv"):
            row.update(csv_metadata(local_path))
        surface_rows.append(row)
    for path in EVIDENCE_FILES:
        surface_rows.append(file_row(RESEARCH_REF, path, "PINNED_EVIDENCE"))

    diff_rows = [classify_decision_diff(path) for path in PRODUCTION_DECISION_FILES]

    taxonomy_path = ROOT / DATA_AND_SPEC_FILES[2][0]
    mapping_path = ROOT / DATA_AND_SPEC_FILES[3][0]
    spec_checks = [
        verify_frozen_spec(taxonomy_path, EXPECTED_TAXONOMY_HASH),
        verify_frozen_spec(mapping_path, EXPECTED_MAPPING_HASH),
    ]

    pit_path = ROOT / DATA_AND_SPEC_FILES[0][0]
    classifier_path = ROOT / DATA_AND_SPEC_FILES[1][0]
    parity_path = ROOT / DATA_AND_SPEC_FILES[4][0]

    pit = pd.read_csv(pit_path, encoding="utf-8-sig", low_memory=False)
    classifier = pd.read_csv(classifier_path, encoding="utf-8-sig", low_memory=False)
    parity = pd.read_csv(parity_path, encoding="utf-8-sig", low_memory=False)

    pit_signal_dates = pd.to_datetime(pit["signal_date"], errors="coerce")
    parity_signal_dates = pd.to_datetime(parity["signal_date"], errors="coerce")
    v4_applied = classifier["v4_applied"].astype(str).str.lower().eq("true")

    population_checks = {
        "pit_panel_rows": int(len(pit)),
        "parity_rows": int(len(parity)),
        "v4_contract_rows": int(len(classifier)),
        "v4_applied_rows": int(v4_applied.sum()),
        "parity_unique_signal_dates": bool(parity_signal_dates.is_unique),
        "parity_dates_in_pit_panel": bool(
            set(parity_signal_dates.dropna()).issubset(set(pit_signal_dates.dropna()))
        ),
        "expected_parity_rows_4645": len(parity) == 4645,
        "expected_v4_applied_rows_992": int(v4_applied.sum()) == 992,
    }

    failures: list[str] = []
    if any(row["status"] != "PRESENT" for row in surface_rows):
        failures.append("Missing release-surface file")
    for row in diff_rows:
        if not row["authorized"]:
            failures.append(f"Unclassified decision diff: {row['path']}")
    for item in spec_checks:
        if item["status"] != "PASS":
            failures.append(f"Frozen spec hash failure: {item['path']}")
    for key in (
        "parity_unique_signal_dates",
        "parity_dates_in_pit_panel",
        "expected_parity_rows_4645",
        "expected_v4_applied_rows_992",
    ):
        if not population_checks[key]:
            failures.append(f"Population check failed: {key}")

    status = "PASS" if not failures else "FAIL"

    manifest = {
        "schema_version": 1,
        "release_id": release_id,
        "gate": "G1_CANONICAL_RELEASE_BASELINE",
        "status": status,
        "production": {
            "ref": PRODUCTION_REF,
            "commit_sha": production_sha,
        },
        "research": {
            "ref": RESEARCH_REF,
            "commit_sha": research_sha,
        },
        "runtime_policy": {
            "status": "NOT_PINNED_IN_G1",
            "validation_gate": "G9_DEPENDENCY_ENVIRONMENT_REPRODUCIBILITY",
        },
        "population": population_checks,
        "frozen_spec_checks": spec_checks,
        "known_exceptions": KNOWN_EXCEPTIONS,
        "claim_applicability": CLAIM_APPLICABILITY,
        "failures": failures,
        "next_gate": "G4_HISTORICAL_STATE_AND_CLOCK_INTEGRITY",
    }

    audit_lines = [
        "G1 — CANONICAL RELEASE BASELINE",
        "=" * 88,
        f"Release ID       : {release_id}",
        f"Production SHA   : {production_sha}",
        f"Research SHA     : {research_sha}",
        f"Surface entries  : {len(surface_rows)}",
        f"Parity rows      : {population_checks['parity_rows']}",
        f"V4 applied rows  : {population_checks['v4_applied_rows']}",
        "",
        "DECISION SURFACE",
        "-" * 88,
    ]
    for row in diff_rows:
        audit_lines.append(
            f"{row['path']}: {row['classification']} "
            f"(authorized={row['authorized']})"
        )
    audit_lines += ["", "FROZEN SPECS", "-" * 88]
    for item in spec_checks:
        audit_lines.append(f"{item['path']}: {item['status']}")
    audit_lines += ["", "KNOWN EXCEPTION", "-" * 88]
    audit_lines.append(
        "SOVEREIGN_VINTAGE_2008_2013: DOCUMENTED_LIMITATION "
        "(KR10Y/JP10Y/DE10Y/IL10Y)"
    )
    audit_lines += ["", "CLAIM APPLICABILITY", "-" * 88]
    for claim in CLAIM_APPLICABILITY:
        audit_lines.append(f"{claim['claim']}: {claim['status']}")
    audit_lines += ["", "FINAL", "-" * 88, f"G1 STATUS: {status}"]
    if failures:
        audit_lines.append("Failures:")
        audit_lines.extend(f"- {failure}" for failure in failures)
    else:
        audit_lines.append(
            "The code/data/spec comparison boundary is pinned and has no "
            "unclassified decision-surface difference."
        )
        audit_lines.append(
            "This gate does not certify causal validity; G4 remains mandatory."
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUT_DIR / "canonical_release_manifest_v1.json"
    surface_path = OUT_DIR / "canonical_release_surface_v1.csv"
    diff_path = OUT_DIR / "canonical_release_diff_classification_v1.csv"
    audit_path = OUT_DIR / "canonical_release_baseline_audit_v1.txt"

    generated = {
        manifest_path: json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        audit_path: "\n".join(audit_lines) + "\n",
    }

    if args.verify_only:
        verify_failures = []
        for path, expected in generated.items():
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                verify_failures.append(str(path.relative_to(ROOT)))

        temp_surface = OUT_DIR / ".surface.verify.csv"
        temp_diff = OUT_DIR / ".diff.verify.csv"
        write_csv(temp_surface, surface_rows)
        write_csv(temp_diff, diff_rows)
        try:
            if not surface_path.exists() or sha256_file(temp_surface) != sha256_file(surface_path):
                verify_failures.append(str(surface_path.relative_to(ROOT)))
            if not diff_path.exists() or sha256_file(temp_diff) != sha256_file(diff_path):
                verify_failures.append(str(diff_path.relative_to(ROOT)))
        finally:
            temp_surface.unlink(missing_ok=True)
            temp_diff.unlink(missing_ok=True)

        if verify_failures:
            print("G1 VERIFY-ONLY: FAIL")
            for failure in verify_failures:
                print(f"- mismatch: {failure}")
            return 1
        print("G1 VERIFY-ONLY: PASS")
        return 0

    for path, content in generated.items():
        path.write_text(content, encoding="utf-8")
    write_csv(surface_path, surface_rows)
    write_csv(diff_path, diff_rows)

    print("\n".join(audit_lines))
    print("\nArtifacts:")
    for path in (manifest_path, surface_path, diff_path, audit_path):
        print(path.relative_to(ROOT))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
