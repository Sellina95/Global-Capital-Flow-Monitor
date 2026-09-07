from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

G1_FREEZE_COMMIT = "54698c576b1ce17c6604e8c9df1a07659c98f342"
EVIDENCE_FREEZE_COMMIT = "3447c330c43ee1e15d6dff181c327c5fd822e74b"
G1_RELEASE_ID = "gcfm-g1-58f2702-7b4c324-pit-v1"
G1_RESEARCH_REF = "7b4c324b27d6a19af3ef61852020da70cc7fe8c2"

CANONICAL_REL = Path(
    "data/backtest/pit_safe/master_panel_pit_safe_final.csv"
)
LEGACY_CONTROL_REL = Path("data/backtest/master_panel.csv")
G1_MANIFEST_REL = Path(
    "data/backtest/results/canonical_release_baseline_v1/"
    "canonical_release_manifest_v1.json"
)
CANONICAL_MAPPING_REL = Path(
    "data/backtest/results/final_13_15_18_parity_closeout/"
    "final_13_15_18_parity_daily.csv"
)
WITH_SOVEREIGN_REL = Path(
    "data/backtest/pit_safe/master_panel_pit_safe_with_sovereign.csv"
)
CONTROLLED_REL = Path(
    "data/backtest/pit_safe/master_panel_fred_initial_release_controlled.csv"
)
MISSING_RELEASE_REPAIR_REL = Path(
    "data/backtest/pit_safe/master_panel_pit_safe.csv"
)
ALFRED_DIR_REL = Path("data/backtest/alfred_vintage_82")

EXPECTED_CANONICAL_SHA256 = (
    "56b6732948254526bda76749a0e975c40c50d8fc8c3df0660151103aec12a39a"
)
EXPECTED_LEGACY_CONTROL_SHA256 = (
    "106921c2b608b6a9056434d8fbc93d2784c85845793598f88179cd45d16895c1"
)
EXPECTED_CANONICAL_BLOB = "341a0dc53c99008c1dbb4aa1fd86355deda9affe"
EXPECTED_G1_MANIFEST_SHA256 = (
    "33aa7a3b03788bed99d2f57bbd490d2f0e66b2181155989bf309912c089d9e3d"
)
EXPECTED_SCHEMA_SHA256 = (
    "c8385ccd3647096eb5eacb38a316ecc0ecc52a2f2d2efed46fba7e2e4f9641bc"
)
EXPECTED_MAPPING_SHA256 = (
    "4f9858dee9f80b8fde6fab8565b27add5788a3057fcd7cec25605f7088bf8acf"
)
EXPECTED_PAIR_SEMANTIC_SHA256 = (
    "77dc09b2fa8e6d9d95f6076804c63b78bd7c814cd3c32b7f62d8f778bd491d2f"
)

EXPECTED_ROWS = 4817
EXPECTED_COLUMNS = 88
EXPECTED_MAPPING_ROWS = 4645
NUMERIC_ATOL = 1e-12

PROMOTED_FROM_CONTROLLED = {
    "fred_extras__FCI",
    "fred_sector__FCI",
    "liquidity__TGA",
    "liquidity__WALCL",
    "liquidity__NET_LIQ",
}

SOVEREIGN_REMOVED = {
    "sovereign_spreads__KR_US_SPREAD",
    "sovereign_spreads__JP_US_SPREAD",
    "sovereign_spreads__DE_US_SPREAD",
    "sovereign_spreads__IL_US_SPREAD",
}
SOVEREIGN_ADDED = {
    "KR10Y_SPREAD",
    "JP10Y_SPREAD",
    "DE10Y_SPREAD",
    "IL10Y_SPREAD",
}

CANONICAL_REQUIRED_CONSUMERS = [
    Path("scripts/backtest/audit_g4_historical_state_clock_integrity_v1.py"),
    Path("scripts/backtest/refreeze_validated_raw_macro_intervention_contract_v1.py"),
    Path("scripts/backtest/audit_claim5_validated_causal_propagation_v1.py"),
]

OUT_DIR = (
    ROOT
    / "data/backtest/results/canonical_panel_identity_provenance_v1"
)
MANIFEST_PATH = OUT_DIR / "canonical_panel_identity_provenance_manifest_v1.json"
NEGATIVE_PATH = OUT_DIR / "canonical_panel_identity_negative_controls_v1.csv"
AUDIT_PATH = OUT_DIR / "canonical_panel_identity_provenance_audit_v1.txt"


class PanelAuthorityError(RuntimeError):
    pass


def run_git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(payload)


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def git_blob(ref: str, rel: Path) -> str | None:
    value = run_git("rev-parse", f"{ref}:{rel}", check=False)
    return value or None


def introduced_commit(rel: Path) -> str | None:
    output = run_git(
        "log",
        "--diff-filter=A",
        "--format=%H",
        "--",
        str(rel),
        check=False,
    )
    commits = [line for line in output.splitlines() if line]
    return commits[-1] if commits else None


def is_ancestor(older: str, newer: str = "HEAD") -> bool:
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def resolve_panel_authority(
    panel_path: str | Path,
    mode: str = "CANONICAL",
) -> Path:
    """Resolve the only authorized historical panel for the declared mode.

    Future canonical audits should call this function before loading a panel.
    A legacy panel is accepted only when the caller explicitly declares that
    the run is a non-PIT control; arbitrary paths are rejected in both modes.
    """

    requested = Path(panel_path)
    if not requested.is_absolute():
        requested = ROOT / requested
    requested = requested.resolve()

    canonical = (ROOT / CANONICAL_REL).resolve()
    legacy = (ROOT / LEGACY_CONTROL_REL).resolve()

    normalized_mode = str(mode).strip().upper()
    if normalized_mode == "CANONICAL":
        if requested != canonical:
            raise PanelAuthorityError(
                "Canonical historical audit rejected non-canonical panel: "
                f"{requested}"
            )
        return canonical

    if normalized_mode == "NON_PIT_CONTROL":
        if requested != legacy:
            raise PanelAuthorityError(
                "NON_PIT_CONTROL permits only the frozen legacy control: "
                f"{requested}"
            )
        return legacy

    raise PanelAuthorityError(f"Unauthorized panel mode: {mode}")


def resolve_and_validate_panel_authority(
    panel_path: str | Path,
    mode: str = "CANONICAL",
    *,
    consumer: str = "UNSPECIFIED_CONSUMER",
    _payload_override_for_test: bytes | None = None,
) -> dict[str, Any]:
    """Fail-fast path, manifest, and content-hash validation for consumers."""

    resolved = resolve_panel_authority(panel_path, mode)
    if not MANIFEST_PATH.exists():
        raise PanelAuthorityError(
            f"{consumer}: canonical authority manifest is missing: {MANIFEST_PATH}"
        )
    authority = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    canonical_authority = authority.get("canonical_authority", {})
    if (
        authority.get("statuses", {}).get("IDENTITY") != "PASS"
        or canonical_authority.get("path") != str(CANONICAL_REL)
        or canonical_authority.get("sha256") != EXPECTED_CANONICAL_SHA256
        or canonical_authority.get("git_blob_sha") != EXPECTED_CANONICAL_BLOB
    ):
        raise PanelAuthorityError(
            f"{consumer}: authority manifest does not preserve the G1 identity"
        )

    payload = (
        resolved.read_bytes()
        if _payload_override_for_test is None
        else _payload_override_for_test
    )
    observed_sha256 = sha256_bytes(payload)
    normalized_mode = str(mode).strip().upper()
    expected_sha256 = (
        EXPECTED_CANONICAL_SHA256
        if normalized_mode == "CANONICAL"
        else EXPECTED_LEGACY_CONTROL_SHA256
    )
    if observed_sha256 != expected_sha256:
        raise PanelAuthorityError(
            f"{consumer}: panel hash mismatch: expected={expected_sha256}, "
            f"observed={observed_sha256}"
        )

    canonical_mode = normalized_mode == "CANONICAL"
    return {
        "consumer": consumer,
        "mode": normalized_mode,
        "resolved_path": str(resolved),
        "repository_relative_path": relative(resolved),
        "sha256": observed_sha256,
        "identity_status": "PASS" if canonical_mode else "NOT_APPLICABLE_CONTROL",
        "evidence_classification": (
            "G1_CANONICAL_HISTORICAL_INPUT"
            if canonical_mode
            else "NON_CANONICAL_CONTROL_ONLY"
        ),
        "canonical_promotion_eligible": canonical_mode,
        "regeneration_provenance_status": authority.get("statuses", {}).get(
            "REGENERATION_PROVENANCE", "UNKNOWN"
        ),
    }


def run_consumer_authority_startup_controls(
    consumer: str,
) -> dict[str, Any]:
    """No-replay controls used by each canonical historical consumer."""

    resolved = resolve_and_validate_panel_authority(
        CANONICAL_REL,
        "CANONICAL",
        consumer=consumer,
    )
    controls: list[dict[str, Any]] = []

    def rejected(name: str, callback) -> None:
        detected = False
        error = None
        try:
            callback()
        except PanelAuthorityError as exc:
            detected = True
            error = str(exc)
        controls.append(
            {
                "control": name,
                "expected": "REJECT",
                "observed": "REJECT" if detected else "ACCEPT",
                "status": "PASS" if detected else "FAIL",
                "error": error,
            }
        )

    rejected(
        "legacy_panel_substitution",
        lambda: resolve_and_validate_panel_authority(
            LEGACY_CONTROL_REL,
            "CANONICAL",
            consumer=consumer,
        ),
    )

    payload = bytearray((ROOT / CANONICAL_REL).read_bytes())
    payload[-2] ^= 1
    rejected(
        "wrong_hash",
        lambda: resolve_and_validate_panel_authority(
            CANONICAL_REL,
            "CANONICAL",
            consumer=consumer,
            _payload_override_for_test=bytes(payload),
        ),
    )

    rejected(
        "unauthorized_path",
        lambda: resolve_and_validate_panel_authority(
            ROOT / "unauthorized/panel.csv",
            "CANONICAL",
            consumer=consumer,
        ),
    )

    non_pit = resolve_and_validate_panel_authority(
        LEGACY_CONTROL_REL,
        "NON_PIT_CONTROL",
        consumer=consumer,
    )
    isolated = (
        non_pit["canonical_promotion_eligible"] is False
        and non_pit["evidence_classification"]
        == "NON_CANONICAL_CONTROL_ONLY"
        and non_pit["identity_status"] == "NOT_APPLICABLE_CONTROL"
    )
    controls.append(
        {
            "control": "non_pit_control_isolation",
            "expected": "NON_PROMOTABLE",
            "observed": "NON_PROMOTABLE" if isolated else "PROMOTABLE",
            "status": "PASS" if isolated else "FAIL",
            "error": None,
        }
    )
    return {
        "consumer": consumer,
        "status": (
            "PASS" if all(row["status"] == "PASS" for row in controls) else "FAIL"
        ),
        "positive_control": resolved,
        "controls": controls,
        "replay_started": False,
    }


def schema_result(frame: pd.DataFrame) -> dict[str, Any]:
    columns = list(frame.columns)
    return {
        "rows": int(len(frame)),
        "columns": int(len(columns)),
        "schema_sha256": canonical_json_sha256(columns),
        "rows_match": len(frame) == EXPECTED_ROWS,
        "columns_match": len(columns) == EXPECTED_COLUMNS,
        "schema_match": canonical_json_sha256(columns) == EXPECTED_SCHEMA_SHA256,
    }


def date_result(frame: pd.DataFrame) -> dict[str, Any]:
    expected = {
        "date": ("2008-01-01", "2026-06-23", EXPECTED_ROWS),
        "signal_date": ("2008-01-01", "2026-06-23", EXPECTED_ROWS),
        "execution_date": ("2008-01-03", "2026-06-22", EXPECTED_MAPPING_ROWS),
    }
    checks: dict[str, Any] = {}
    for column, (first, last, valid_count) in expected.items():
        if column not in frame.columns:
            checks[column] = {"status": "FAIL", "reason": "MISSING_COLUMN"}
            continue
        values = pd.to_datetime(frame[column], errors="coerce")
        observed = {
            "first": values.dropna().min().strftime("%Y-%m-%d"),
            "last": values.dropna().max().strftime("%Y-%m-%d"),
            "valid_rows": int(values.notna().sum()),
        }
        observed["status"] = (
            "PASS"
            if observed
            == {"first": first, "last": last, "valid_rows": valid_count}
            else "FAIL"
        )
        checks[column] = observed
    return checks


def series_equal(a: pd.Series, b: pd.Series) -> pd.Series:
    an = pd.to_numeric(a, errors="coerce")
    bn = pd.to_numeric(b, errors="coerce")
    numeric = an.notna() | bn.notna()
    result = pd.Series(False, index=a.index)
    result.loc[numeric] = (
        np.isclose(
            an.loc[numeric].fillna(np.inf),
            bn.loc[numeric].fillna(np.inf),
            rtol=0,
            atol=NUMERIC_ATOL,
        )
        & (an.loc[numeric].isna() == bn.loc[numeric].isna())
    )
    result.loc[~numeric] = (
        a.loc[~numeric].fillna("<NA>").astype(str)
        == b.loc[~numeric].fillna("<NA>").astype(str)
    )
    return result


def normalize_by_signal_date(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result["signal_date"] = pd.to_datetime(
        result["signal_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    return result.set_index("signal_date", drop=False)


def promotion_composition_result() -> dict[str, Any]:
    final = normalize_by_signal_date(
        pd.read_csv(ROOT / CANONICAL_REL, low_memory=False)
    )
    with_sovereign = normalize_by_signal_date(
        pd.read_csv(ROOT / WITH_SOVEREIGN_REL, low_memory=False)
    )
    controlled = normalize_by_signal_date(
        pd.read_csv(ROOT / CONTROLLED_REL, low_memory=False)
    )

    mismatches: list[dict[str, Any]] = []
    for column in final.columns:
        source_name = (
            "controlled_initial_release"
            if column in PROMOTED_FROM_CONTROLLED
            else "pit_safe_with_sovereign"
        )
        source = controlled if column in PROMOTED_FROM_CONTROLLED else with_sovereign
        if column not in source.columns:
            mismatches.append(
                {"column": column, "reason": "MISSING_SOURCE_COLUMN"}
            )
            continue
        equal = series_equal(final[column], source[column])
        if not bool(equal.all()):
            mismatches.append(
                {
                    "column": column,
                    "source": source_name,
                    "mismatch_rows": int((~equal).sum()),
                }
            )

    return {
        "status": "PASS" if not mismatches else "FAIL",
        "numeric_atol": NUMERIC_ATOL,
        "controlled_columns": sorted(PROMOTED_FROM_CONTROLLED),
        "remaining_columns_source": str(WITH_SOVEREIGN_REL),
        "mismatches": mismatches,
    }


def sovereign_schema_result() -> dict[str, Any]:
    legacy = pd.read_csv(ROOT / LEGACY_CONTROL_REL, nrows=0)
    final = pd.read_csv(ROOT / CANONICAL_REL, nrows=0)
    removed = set(legacy.columns) - set(final.columns)
    added = set(final.columns) - set(legacy.columns)
    passed = removed == SOVEREIGN_REMOVED and added == SOVEREIGN_ADDED
    return {
        "status": "PASS" if passed else "FAIL",
        "expected_removed": sorted(SOVEREIGN_REMOVED),
        "observed_removed": sorted(removed),
        "expected_added": sorted(SOVEREIGN_ADDED),
        "observed_added": sorted(added),
    }


def mapping_result(panel: pd.DataFrame) -> dict[str, Any]:
    mapping_path = ROOT / CANONICAL_MAPPING_REL
    mapping = pd.read_csv(mapping_path, low_memory=False)
    generated: list[dict[str, str]] = []
    for frame in (panel, mapping):
        for column in ("signal_date", "execution_date"):
            frame[column] = pd.to_datetime(
                frame[column], errors="coerce"
            ).dt.strftime("%Y-%m-%d")

    panel_pairs = panel.loc[
        panel["execution_date"].notna(), ["signal_date", "execution_date"]
    ].to_dict("records")
    mapping_pairs = mapping[
        ["signal_date", "execution_date"]
    ].to_dict("records")
    generated = mapping_pairs
    semantic_hash = canonical_json_sha256(generated)
    return {
        "status": (
            "PASS"
            if len(mapping_pairs) == EXPECTED_MAPPING_ROWS
            and panel_pairs == mapping_pairs
            and sha256_file(mapping_path) == EXPECTED_MAPPING_SHA256
            and semantic_hash == EXPECTED_PAIR_SEMANTIC_SHA256
            else "FAIL"
        ),
        "rows": len(mapping_pairs),
        "panel_pairs_exact": panel_pairs == mapping_pairs,
        "artifact_sha256": sha256_file(mapping_path),
        "pair_semantic_sha256": semantic_hash,
    }


def g1_result() -> dict[str, Any]:
    manifest_path = ROOT / G1_MANIFEST_REL
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = {
        "g1_freeze_is_ancestor": is_ancestor(G1_FREEZE_COMMIT),
        "evidence_freeze_is_ancestor": is_ancestor(EVIDENCE_FREEZE_COMMIT),
        "manifest_hash_match": (
            sha256_file(manifest_path) == EXPECTED_G1_MANIFEST_SHA256
        ),
        "release_id_match": manifest.get("release_id") == G1_RELEASE_ID,
        "g1_status_pass": manifest.get("status") == "PASS",
        "research_ref_match": (
            manifest.get("research", {}).get("commit_sha") == G1_RESEARCH_REF
        ),
        "panel_blob_at_g1_match": (
            git_blob(G1_FREEZE_COMMIT, CANONICAL_REL) == EXPECTED_CANONICAL_BLOB
        ),
        "panel_blob_at_research_ref_match": (
            git_blob(G1_RESEARCH_REF, CANONICAL_REL) == EXPECTED_CANONICAL_BLOB
        ),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "release_id": G1_RELEASE_ID,
        "g1_freeze_commit": G1_FREEZE_COMMIT,
        "research_ref": G1_RESEARCH_REF,
        "checks": checks,
    }


def identity_result(payload: bytes | None = None) -> dict[str, Any]:
    path = resolve_panel_authority(CANONICAL_REL, "CANONICAL")
    data = path.read_bytes() if payload is None else payload
    frame = pd.read_csv(io.BytesIO(data), encoding="utf-8-sig", low_memory=False)
    schema = schema_result(frame)
    dates = date_result(frame)
    g1 = g1_result()
    mapping = mapping_result(frame.copy())
    composition = promotion_composition_result()
    sovereign = sovereign_schema_result()
    checks = {
        "g1": g1["status"] == "PASS",
        "canonical_path": relative(path) == str(CANONICAL_REL),
        "canonical_sha256": sha256_bytes(data) == EXPECTED_CANONICAL_SHA256,
        "canonical_worktree_blob": run_git("hash-object", str(path))
        == EXPECTED_CANONICAL_BLOB,
        "population_schema": all(
            [schema["rows_match"], schema["columns_match"], schema["schema_match"]]
        ),
        "date_ranges": all(x.get("status") == "PASS" for x in dates.values()),
        "canonical_mapping": mapping["status"] == "PASS",
        "promotion_composition": composition["status"] == "PASS",
        "sovereign_schema_allowlist": sovereign["status"] == "PASS",
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "g1": g1,
        "path": str(CANONICAL_REL),
        "sha256": sha256_bytes(data),
        "git_blob_sha": run_git("hash-object", str(path)),
        "schema": schema,
        "dates": dates,
        "mapping": mapping,
        "promotion_composition": composition,
        "sovereign_schema": sovereign,
    }


def consumer_authority_result() -> dict[str, Any]:
    canonical_request_pass = False
    explicit_control_pass = False
    implicit_control_rejected = False
    try:
        canonical_request_pass = (
            resolve_panel_authority(CANONICAL_REL, "CANONICAL")
            == (ROOT / CANONICAL_REL).resolve()
        )
        explicit_control_pass = (
            resolve_panel_authority(LEGACY_CONTROL_REL, "NON_PIT_CONTROL")
            == (ROOT / LEGACY_CONTROL_REL).resolve()
        )
    except PanelAuthorityError:
        pass
    try:
        resolve_panel_authority(LEGACY_CONTROL_REL, "CANONICAL")
    except PanelAuthorityError:
        implicit_control_rejected = True

    consumers: list[dict[str, Any]] = []
    for rel in CANONICAL_REQUIRED_CONSUMERS:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        uses_gate = (
            "resolve_and_validate_panel_authority" in text
            and "audit_canonical_panel_identity_provenance_v1" in text
        )
        hardcodes_legacy = "data/backtest/master_panel.csv" in text or (
            'ROOT / "data/backtest/master_panel.csv"' in text
        )
        status = "PASS" if uses_gate and not hardcodes_legacy else "FAIL"
        consumers.append(
            {
                "path": str(rel),
                "status": status,
                "uses_canonical_authority_gate": uses_gate,
                "hardcodes_legacy_panel": hardcodes_legacy,
            }
        )

    checks = {
        "canonical_request_accepted": canonical_request_pass,
        "explicit_non_pit_control_accepted": explicit_control_pass,
        "implicit_legacy_substitution_rejected": implicit_control_rejected,
        "required_consumers_use_gate": all(
            row["status"] == "PASS" for row in consumers
        ),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "required_consumers": consumers,
        "policy": {
            "CANONICAL": str(CANONICAL_REL),
            "NON_PIT_CONTROL": str(LEGACY_CONTROL_REL),
            "other_paths": "REJECT",
        },
    }


def file_node(rel: Path, role: str, generation_commit: str | None = None) -> dict[str, Any]:
    path = ROOT / rel
    exists = path.exists()
    return {
        "path": str(rel),
        "role": role,
        "status": "PRESENT" if exists else "UNKNOWN",
        "sha256": sha256_file(path) if exists and path.is_file() else None,
        "git_blob_sha": git_blob("HEAD", rel) if exists and path.is_file() else None,
        "introduced_commit": introduced_commit(rel) if exists else None,
        "generation_commit": generation_commit,
    }


def regeneration_provenance_result() -> dict[str, Any]:
    alfred_dir = ROOT / ALFRED_DIR_REL
    missing_release_panel = not (ROOT / MISSING_RELEASE_REPAIR_REL).exists()
    alfred_inputs_present = alfred_dir.exists() and any(alfred_dir.glob("*.json"))
    exact_promotion_recipe = False
    checks = {
        "base_master_present": (ROOT / LEGACY_CONTROL_REL).exists(),
        "exact_base_builder_authority": False,
        "release_repair_generator_present": (
            ROOT / "scripts/backtest/repair_release_timing_82.py"
        ).exists(),
        "release_repair_intermediate_present": not missing_release_panel,
        "sovereign_intermediates_present": all(
            (ROOT / path).exists()
            for path in [
                Path("data/backtest/pit_safe/sovereign_yields_pit_4.csv"),
                Path("data/backtest/pit_safe/sovereign_spreads_pit_safe_4.csv"),
                WITH_SOVEREIGN_REL,
            ]
        ),
        "alfred_raw_sources_present_and_hashable": alfred_inputs_present,
        "controlled_artifact_present": (ROOT / CONTROLLED_REL).exists(),
        "exact_final_promotion_recipe_present": exact_promotion_recipe,
        "final_composition_observationally_verified": (
            promotion_composition_result()["status"] == "PASS"
        ),
    }
    required_for_regeneration = [
        "release_repair_intermediate_present",
        "alfred_raw_sources_present_and_hashable",
        "exact_final_promotion_recipe_present",
    ]
    reproducible = all(checks[name] for name in required_for_regeneration)
    return {
        "status": (
            "PASS" if reproducible else "NON_REGENERABLE_FROZEN_INPUT"
        ),
        "checks": checks,
        "unresolved": [
            {
                "item": "exact_base_builder_authority",
                "path": "scripts/backtest/build_master_panel*.py",
                "status": "UNKNOWN",
                "reason": (
                    "Two builders declare master_panel.csv as output; Git evidence "
                    "does not identify the exact invocation that produced its blob."
                ),
            },
            {
                "item": "release_repair_intermediate",
                "path": str(MISSING_RELEASE_REPAIR_REL),
                "status": "UNKNOWN",
                "reason": "Generator-declared intermediate is absent from the repository.",
            },
            {
                "item": "alfred_initial_release_raw_sources",
                "path": str(ALFRED_DIR_REL),
                "status": "UNKNOWN",
                "reason": "Raw ALFRED JSON inputs and their frozen hashes are absent.",
            },
            {
                "item": "exact_final_promotion_recipe",
                "path": None,
                "status": "UNKNOWN",
                "reason": (
                    "Final composition is observationally verified, but no executable "
                    "recipe in the repository declares the exact final output."
                ),
            },
        ],
    }


def lineage_manifest() -> dict[str, Any]:
    return {
        "nodes": [
            file_node(Path("data/backtest/macro_data.csv"), "RAW_BASE_CALENDAR"),
            file_node(Path("data/backtest/fred_macro_extras.csv"), "RAW_FRED_FCI"),
            file_node(Path("data/backtest/fred_macro_sctorallo.csv"), "RAW_FRED_RATES"),
            file_node(Path("data/backtest/liquidity_data.csv"), "RAW_LIQUIDITY"),
            file_node(Path("data/backtest/sovereign_yields.csv"), "RAW_SOVEREIGN"),
            file_node(
                Path("scripts/backtest/build_master_panel.py"),
                "BASE_BUILDER_CANDIDATE",
            ),
            file_node(
                Path("scripts/backtest/build_master_panel_fg.py"),
                "BASE_BUILDER_CANDIDATE_DUPLICATE_OUTPUT",
            ),
            file_node(LEGACY_CONTROL_REL, "NON_PIT_CONTROL", "e3569ad4d43c93a779d3778e91252f76652a9543"),
            file_node(Path("scripts/backtest/repair_release_timing_82.py"), "PIT_TIMING_TRANSFORMATION", "cb94094c4561b523edd03eddb89d48816525e890"),
            file_node(MISSING_RELEASE_REPAIR_REL, "MISSING_INTERMEDIATE"),
            file_node(Path("data/backtest/pit_safe/sovereign_yields_pit_4.csv"), "SOVEREIGN_PIT_INTERMEDIATE", "cb94094c4561b523edd03eddb89d48816525e890"),
            file_node(Path("data/backtest/pit_safe/sovereign_spreads_pit_safe_4.csv"), "SOVEREIGN_SPREAD_INTERMEDIATE", "cb94094c4561b523edd03eddb89d48816525e890"),
            file_node(WITH_SOVEREIGN_REL, "PIT_WITH_SOVEREIGN", "9f7102a17ba12baf8fc2807186e00b011fe7f85c"),
            {
                "path": str(ALFRED_DIR_REL),
                "role": "ALFRED_INITIAL_RELEASE_RAW",
                "status": "UNKNOWN",
                "sha256": None,
                "git_blob_sha": None,
                "introduced_commit": None,
                "generation_commit": None,
            },
            file_node(CONTROLLED_REL, "INITIAL_RELEASE_CONTROLLED", "9f7102a17ba12baf8fc2807186e00b011fe7f85c"),
            file_node(CANONICAL_REL, "G1_CANONICAL_HISTORICAL_INPUT", "9f7102a17ba12baf8fc2807186e00b011fe7f85c"),
        ],
        "edges": [
            {
                "from": "raw source files",
                "transformation": (
                    "build_master_panel.py or build_master_panel_fg.py; both "
                    "declare the same output path"
                ),
                "to": str(LEGACY_CONTROL_REL),
                "status": "AMBIGUOUS_DUPLICATE_OUTPUT_AUTHORITY",
            },
            {"from": str(LEGACY_CONTROL_REL), "transformation": "repair_release_timing_82.py availability-date transforms", "to": str(MISSING_RELEASE_REPAIR_REL), "status": "CODE_CONFIRMED_OUTPUT_ABSENT"},
            {"from": str(MISSING_RELEASE_REPAIR_REL), "transformation": "merge_sovereign_spreads_into_pit_panel.py", "to": str(WITH_SOVEREIGN_REL), "status": "CODE_CONFIRMED_INPUT_ABSENT"},
            {"from": str(ALFRED_DIR_REL), "transformation": "initial-release replacement for NFCI/WTREGEN/WALCL", "to": str(CONTROLLED_REL), "status": "UNKNOWN_EXACT_RECIPE_AND_RAW_HASHES"},
            {"from": [str(WITH_SOVEREIGN_REL), str(CONTROLLED_REL)], "transformation": "five controlled columns plus all remaining with-sovereign columns", "to": str(CANONICAL_REL), "status": "CONTENT_VERIFIED_RECIPE_UNKNOWN"},
            {"from": str(CANONICAL_REL), "transformation": "G1 immutable path/hash/blob freeze", "to": G1_FREEZE_COMMIT, "status": "G1_PINNED"},
        ],
    }


def negative_controls() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def record(name: str, detected: bool, defect: str) -> None:
        rows.append(
            {
                "negative_control": name,
                "injected_defect": defect,
                "expected": "DETECTED",
                "observed": "DETECTED" if detected else "MISSED",
                "status": "PASS" if detected else "FAIL",
            }
        )

    rejected = False
    try:
        resolve_panel_authority(LEGACY_CONTROL_REL, "CANONICAL")
    except PanelAuthorityError:
        rejected = True
    record("legacy_panel_substitution", rejected, "master_panel.csv in CANONICAL mode")

    canonical_bytes = (ROOT / CANONICAL_REL).read_bytes()
    mutated = bytearray(canonical_bytes)
    mutated[-2] = mutated[-2] ^ 1
    record(
        "hash_mutation",
        sha256_bytes(bytes(mutated)) != EXPECTED_CANONICAL_SHA256,
        "one-byte canonical payload mutation",
    )

    rejected = False
    try:
        resolve_panel_authority(ROOT / "unauthorized/panel.csv", "CANONICAL")
    except PanelAuthorityError:
        rejected = True
    record("unauthorized_path", rejected, "non-allowlisted canonical path")

    frame = pd.read_csv(ROOT / CANONICAL_REL, low_memory=False)
    mutated_schema = schema_result(frame.drop(columns=[frame.columns[-1]]))
    record(
        "schema_mutation",
        not (
            mutated_schema["columns_match"]
            and mutated_schema["schema_match"]
        ),
        "drop final canonical schema column",
    )
    return rows


def build_outputs() -> tuple[dict[str, Any], list[dict[str, str]], str]:
    identity = identity_result()
    consumer = consumer_authority_result()
    regeneration = regeneration_provenance_result()
    negatives = negative_controls()
    negative_pass = all(row["status"] == "PASS" for row in negatives)

    statuses = {
        "IDENTITY": identity["status"],
        "CONSUMER_AUTHORITY": consumer["status"],
        "REGENERATION_PROVENANCE": regeneration["status"],
    }
    overall = (
        "PASS"
        if statuses
        == {
            "IDENTITY": "PASS",
            "CONSUMER_AUTHORITY": "PASS",
            "REGENERATION_PROVENANCE": "PASS",
        }
        and negative_pass
        else "OPEN"
    )
    manifest = {
        "schema_version": 1,
        "gate": "P0_CANONICAL_PANEL_IDENTITY_AND_PROVENANCE",
        "overall_status": overall,
        "statuses": statuses,
        "canonical_authority": {
            "path": str(CANONICAL_REL),
            "sha256": EXPECTED_CANONICAL_SHA256,
            "git_blob_sha": EXPECTED_CANONICAL_BLOB,
            "classification": "G1_CANONICAL_HISTORICAL_INPUT",
        },
        "legacy_control": {
            "path": str(LEGACY_CONTROL_REL),
            "sha256": EXPECTED_LEGACY_CONTROL_SHA256,
            "classification": "NON_PIT_CONTROL_LEGACY",
            "canonical_replacement_candidate": False,
            "canonical_promotion_eligible": False,
        },
        "identity": identity,
        "consumer_authority": consumer,
        "regeneration_provenance": regeneration,
        "lineage": lineage_manifest(),
        "negative_controls": {
            "status": "PASS" if negative_pass else "FAIL",
            "all_detected": negative_pass,
            "count": len(negatives),
        },
        "downstream_readiness": {
            "g4_claim5_canonical_rerun_safe": (
                identity["status"] == "PASS"
                and consumer["status"] == "PASS"
            ),
            "reason": (
                "Canonical identity is frozen, but required historical consumers "
                "have not yet adopted the authority resolver."
                if consumer["status"] != "PASS"
                else "Canonical identity and consumer authority are enforced."
            ),
        },
        "constraints": {
            "canonical_panel_modified_or_regenerated": False,
            "existing_g1_g4_claim5_artifacts_modified": False,
            "production_or_strategy_logic_modified": False,
            "internet_vintage_data_acquired": False,
            "g4_or_claim5_rerun": False,
        },
    }

    lines = [
        "P0 CANONICAL PANEL IDENTITY & PROVENANCE GATE",
        "=" * 78,
        f"OVERALL: {overall}",
        f"IDENTITY: {statuses['IDENTITY']}",
        f"CONSUMER_AUTHORITY: {statuses['CONSUMER_AUTHORITY']}",
        f"REGENERATION_PROVENANCE: {statuses['REGENERATION_PROVENANCE']}",
        "",
        "CANONICAL AUTHORITY",
        "-" * 78,
        f"Path: {CANONICAL_REL}",
        f"SHA256: {EXPECTED_CANONICAL_SHA256}",
        f"Git blob: {EXPECTED_CANONICAL_BLOB}",
        f"Rows x columns: {identity['schema']['rows']} x {identity['schema']['columns']}",
        f"Canonical signal/execution pairs: {identity['mapping']['rows']}",
        f"Numeric comparison tolerance: atol={NUMERIC_ATOL}, rtol=0",
        "",
        "CONSUMER AUTHORITY",
        "-" * 78,
    ]
    lines.extend(
        f"{row['status']}: {row['path']}"
        for row in consumer["required_consumers"]
    )
    lines.extend(
        [
            "",
            "UNRESOLVED REGENERATION LINEAGE",
            "-" * 78,
        ]
    )
    lines.extend(
        f"{row['status']}: {row['item']} — {row['reason']}"
        for row in regeneration["unresolved"]
    )
    lines.extend(
        [
            "",
            "NEGATIVE CONTROLS",
            "-" * 78,
        ]
    )
    lines.extend(
        f"{row['status']}: {row['negative_control']} -> {row['observed']}"
        for row in negatives
    )
    lines.extend(
        [
            "",
            "DOWNSTREAM",
            "-" * 78,
            "G4/#5 canonical rerun safe: "
            + ("YES" if manifest["downstream_readiness"]["g4_claim5_canonical_rerun_safe"] else "NO"),
            manifest["downstream_readiness"]["reason"],
            "",
            "No canonical panel, existing canonical evidence, Production logic,",
            "strategy logic, taxonomy, mapping, or threshold was modified.",
        ]
    )
    return manifest, negatives, "\n".join(lines) + "\n"


def serialize_negative(rows: list[dict[str, str]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "negative_control",
            "injected_defect",
            "expected",
            "observed",
            "status",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    manifest, negatives, audit = build_outputs()
    manifest_text = json.dumps(
        manifest, ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    negative_text = serialize_negative(negatives)

    expected = {
        MANIFEST_PATH: manifest_text,
        NEGATIVE_PATH: negative_text,
        AUDIT_PATH: audit,
    }

    if args.verify_only:
        mismatches = [
            relative(path)
            for path, content in expected.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if mismatches:
            print("P0 VERIFY-ONLY: FAIL")
            for path in mismatches:
                print("mismatch:", path)
            return 1
        print("P0 VERIFY-ONLY: PASS")
        print("OVERALL:", manifest["overall_status"])
        for name, status in manifest["statuses"].items():
            print(f"{name}: {status}")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in expected.items():
        path.write_text(content, encoding="utf-8")
    print(audit, end="")
    print("\n[OUTPUT]")
    for path in expected:
        print(relative(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
