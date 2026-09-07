from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = (
    ROOT
    / "data/backtest/results/canonical_pit_evidence_chain_v1"
    / "canonical_pit_evidence_authority_manifest_v1.json"
)
REPORT = REGISTRY.with_name("canonical_pit_evidence_chain_verification_v1.txt")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    checks: dict[str, bool] = {}

    for group in ("canonical_artifacts", "consumer_implementation"):
        for relative, expected in registry[group].items():
            path = ROOT / relative
            checks[f"hash::{relative}"] = path.is_file() and digest(path) == expected

    for entry in registry["legacy_authority"]:
        path = ROOT / entry["manifest"]
        checks[f"legacy_immutable::{entry['stage']}"] = (
            entry["status"] == "IMMUTABLE_SUPERSEDED_HISTORICAL_REFERENCE"
            and path.is_file()
            and digest(path) == entry["manifest_sha256"]
        )

    panel = registry["canonical_panel"]
    checks["canonical_panel_identity"] = digest(ROOT / panel["path"]) == panel["sha256"]
    checks["regeneration_provenance_not_overstated"] = (
        panel["regeneration_provenance_status"] == "NON_REGENERABLE_FROZEN_INPUT"
    )
    checks["g1_release_is_ancestor"] = subprocess.run(
        ["git", "merge-base", "--is-ancestor", registry["g1"]["release_commit"], "HEAD"],
        cwd=ROOT,
        check=False,
    ).returncode == 0

    chain = {entry["stage"]: entry for entry in registry["authority_chain"]}
    g4 = load(chain["G4_HISTORICAL_STATE_CLOCK"]["manifest"])
    contract = load(chain["VALIDATED_RAW_MACRO_INTERVENTION_CONTRACT"]["manifest"])
    claim5 = load(chain["CLAIM5_CAUSAL_PROPAGATION"]["manifest"])
    checks["canonical_stage_statuses_pass"] = all(
        item.get("status") == "PASS" for item in (g4, contract, claim5)
    )
    checks["g4_uses_canonical_panel"] = (
        g4["panel_authority"]["sha256"] == panel["sha256"]
    )
    checks["contract_uses_canonical_panel"] = (
        contract["panel_authority"]["sha256"] == panel["sha256"]
    )
    checks["claim5_uses_canonical_panel"] = (
        claim5["panel_authority"]["sha256"] == panel["sha256"]
    )
    checks["claim5_uses_registered_contract"] = (
        claim5["provenance"]["validated_contract_sha256"]
        == chain["VALIDATED_RAW_MACRO_INTERVENTION_CONTRACT"]["contract_sha256"]
    )
    checks["intervention_population_1068"] = (
        contract["population"]["new_intervention_rows"] == 1068
        and claim5["population"]["intervention_rows"] == 1068
    )
    checks["frozen_mapping_consistent"] = all(
        item["provenance"]["mapping_semantic_sha256"]
        == registry["frozen_mapping"]["semantic_sha256"]
        for item in (contract, claim5)
    )
    checks["legacy_is_non_promotable"] = registry["promotion_policy"][
        "legacy_evidence_is_non_promotable"
    ]
    checks["non_pit_is_non_promotable"] = registry["promotion_policy"][
        "non_pit_control_is_non_promotable"
    ]

    status = "PASS" if all(checks.values()) else "FAIL"
    lines = [
        "CANONICAL PIT EVIDENCE CHAIN FREEZE VERIFICATION",
        "=" * 78,
        f"STATUS: {status}",
        f"AUTHORITY: {registry['authority_id']}",
        "",
    ]
    lines.extend(f"{name}: {'PASS' if result else 'FAIL'}" for name, result in checks.items())
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8"))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
