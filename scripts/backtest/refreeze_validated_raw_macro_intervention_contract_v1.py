from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)
from scripts.backtest.market_data_builder import (
    build_market_data,
    build_series_snapshot,
)


PANEL_PATH = ROOT / "data/backtest/master_panel.csv"
CANONICAL_DATES_PATH = (
    ROOT / "data/backtest/results/final_13_15_18_parity_closeout"
    / "final_13_15_18_parity_daily.csv"
)
OLD_CONTRACT_PATH = (
    ROOT / "data/backtest/results/macro_v4_research_classifier_v1"
    / "macro_v4_classifier_daily.csv"
)
TAXONOMY_PATH = (
    ROOT / "data/backtest/results/macro_v4_candidate_taxonomy_spec_v1"
    / "macro_v4_candidate_taxonomy_spec.json"
)
MAPPING_PATH = (
    ROOT / "data/backtest/results/macro_v4_portfolio_mapping_spec_v1"
    / "macro_v4_portfolio_mapping_spec.json"
)
BUILDER_PATH = ROOT / "scripts/backtest/market_data_builder.py"
EXECUTION_CHAIN_PATH = ROOT / "scripts/backtest/filter13_execution_chain.py"

OUT_DIR = (
    ROOT / "data/backtest/results"
    / "validated_raw_macro_intervention_contract_v1"
)
RAW_PATH = OUT_DIR / "validated_raw_macro_contract_daily_v1.csv"
CONTRACT_PATH = OUT_DIR / "validated_intervention_contract_daily_v1.csv"
DIFF_PATH = OUT_DIR / "validated_intervention_date_diff_v1.csv"
MANIFEST_PATH = OUT_DIR / "validated_intervention_contract_manifest_v1.json"
AUDIT_PATH = OUT_DIR / "validated_intervention_contract_audit_v1.txt"

EXPECTED_ROWS = 4645
EXPECTED_TAXONOMY_HASH = (
    "cd7174ea8ec93115b4fc9902fd55fe2b9ba443199929b01eae2bc4db4fb70bf3"
)
EXPECTED_MAPPING_HASH = (
    "6ef7cba1e196fbb067385a2acc20e193adfd357d98669d74c3a745907e47d225"
)
G1_RELEASE_ID = "gcfm-g1-58f2702-7b4c324-pit-v1"
PRODUCTION_SHA = "58f270267bba502b5831a60d8e8a2a375f55f7ef"
RESEARCH_SHA = "7b4c324b27d6a19af3ef61852020da70cc7fe8c2"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_hash(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def semantic_hashes(spec: dict[str, Any]) -> set[str]:
    payloads = (
        json.dumps(spec, ensure_ascii=False, sort_keys=True, indent=2),
        json.dumps(
            spec, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
    )
    return {sha256_bytes(payload.encode("utf-8")) for payload in payloads}


def clean_direction(value: Any) -> int | None:
    try:
        if value is None or pd.isna(value):
            return None
        output = int(float(value))
        return output if output in (-1, 0, 1) else None
    except Exception:
        return None


def scalar(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def direction_name(value: int | None) -> str:
    return {1: "UP", -1: "DOWN", 0: "FLAT"}.get(value, "MISSING")


def classify_family(row: dict[str, Any]) -> tuple[str, str]:
    r, d, v, w = (
        clean_direction(row.get("US10Y_DIR")),
        clean_direction(row.get("DXY_DIR")),
        clean_direction(row.get("VIX_DIR")),
        clean_direction(row.get("WTI_DIR")),
    )
    values = {"RATES": r, "USD": d, "VIX": v, "WTI": w}
    missing = [key for key, value in values.items() if value is None]
    if missing:
        return "MISSING_EVIDENCE", "+".join(missing)
    flat = [key for key, value in values.items() if value == 0]
    if flat:
        return "FLAT_LOW_INFORMATION", "+".join(flat)
    family = (
        f"RATES_{direction_name(r)}_USD_{direction_name(d)}_"
        f"VIX_{direction_name(v)}"
    )
    return family, f"WTI_{direction_name(w)}"


def compile_taxonomy_rules(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        rule for rule in spec["candidate_rules"]
        if str(rule.get("rule_type", "")).startswith("V4_CANDIDATE")
    ]


def classify_candidate(
    row: dict[str, Any], rules: list[dict[str, Any]]
) -> dict[str, Any]:
    if row["raw_macro_narrative"] != "UNKNOWN_TRANSITION":
        return {
            "v4_state": row["raw_macro_narrative"],
            "v4_rule_id": "NOT_APPLICABLE",
            "v4_applied": False,
            "collision_count": 0,
        }
    matches = []
    for rule in rules:
        if row["structural_family"] != rule["family"]:
            continue
        required_wti = rule.get("wti_dir", "*")
        if required_wti != "*" and clean_direction(row["WTI_DIR"]) != int(required_wti):
            continue
        matches.append(rule)
    if len(matches) > 1:
        return {
            "v4_state": "CLASSIFIER_COLLISION",
            "v4_rule_id": "COLLISION",
            "v4_applied": False,
            "collision_count": len(matches),
        }
    if len(matches) == 1:
        return {
            "v4_state": matches[0]["candidate_state"],
            "v4_rule_id": matches[0]["rule_id"],
            "v4_applied": True,
            "collision_count": 1,
        }
    return {
        "v4_state": "UNKNOWN_TRANSITION",
        "v4_rule_id": "FALLBACK",
        "v4_applied": False,
        "collision_count": 0,
    }


def generate_raw(
    panel: pd.DataFrame, indices: list[int]
) -> pd.DataFrame:
    flow_memory: dict[str, Any] = {
        "flow_state": "N/A", "flow_score": 0, "persistence_days": 0
    }
    rows = []
    for sequence, idx in enumerate(indices, start=1):
        market_data = build_market_data(panel, idx, previous_exposure=None)
        with contextlib.redirect_stdout(io.StringIO()):
            flow_memory = prepare_filter13_execution_state(
                market_data, panel, idx, flow_memory
            )
        tape = market_data.get("CROSS_ASSET_TAPE", {}) or {}
        canonical_us10y = build_series_snapshot(panel, idx, "US10Y")
        actual_us10y = market_data.get("US10Y", {}) or {}
        provenance_match = (
            scalar(actual_us10y.get("today")) == scalar(canonical_us10y.get("today"))
            and scalar(actual_us10y.get("prev")) == scalar(canonical_us10y.get("prev"))
            and scalar(actual_us10y.get("pct_change"))
            == scalar(canonical_us10y.get("pct_change"))
        )
        row = {
            "sequence": sequence,
            "panel_index": idx,
            "signal_date": market_data["SIGNAL_DATE"],
            "execution_date": market_data["EXECUTION_DATE"],
            "raw_macro_narrative": str(market_data.get("MACRO_NARRATIVE", "")),
            "US10Y_DIR": clean_direction(tape.get("US10Y_DIR")),
            "DXY_DIR": clean_direction(tape.get("DXY_DIR")),
            "VIX_DIR": clean_direction(tape.get("VIX_DIR")),
            "WTI_DIR": clean_direction(tape.get("WTI_DIR")),
            "HY_OAS_STATUS": str(tape.get("HY_OAS_STATUS", "UNKNOWN")),
            "VIX_TODAY": scalar(tape.get("VIX_TODAY")),
            "US10Y_TODAY": scalar(actual_us10y.get("today")),
            "US10Y_PREV": scalar(actual_us10y.get("prev")),
            "US10Y_PCT_CHANGE": scalar(actual_us10y.get("pct_change")),
            "US10Y_SOURCE_COLUMN": "US10Y",
            "US10Y_SOURCE_CONTRACT": "CANONICAL_CORE_SERIES_NO_NAMESPACE_OVERWRITE",
            "US10Y_CORE_PROVENANCE_MATCH": provenance_match,
            "market_data_builder_sha256": file_hash(BUILDER_PATH),
            "filter13_execution_chain_sha256": file_hash(EXECUTION_CHAIN_PATH),
        }
        family, detail = classify_family(row)
        row["structural_family"] = family
        row["family_detail"] = detail
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    taxonomy_wrapper = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    mapping_wrapper = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    taxonomy_ok = (
        taxonomy_wrapper.get("sha256") == EXPECTED_TAXONOMY_HASH
        and EXPECTED_TAXONOMY_HASH in semantic_hashes(taxonomy_wrapper["spec"])
    )
    mapping_ok = (
        mapping_wrapper.get("sha256") == EXPECTED_MAPPING_HASH
        and EXPECTED_MAPPING_HASH in semantic_hashes(mapping_wrapper["spec"])
    )
    if not taxonomy_ok or not mapping_ok:
        raise RuntimeError("Frozen taxonomy or mapping semantic hash mismatch")

    protected_before = {
        str(path.relative_to(ROOT)): file_hash(path)
        for path in (OLD_CONTRACT_PATH, TAXONOMY_PATH, MAPPING_PATH)
    }
    panel = pd.read_csv(
        PANEL_PATH, parse_dates=["date", "signal_date", "execution_date"]
    )
    canonical = pd.read_csv(
        CANONICAL_DATES_PATH, parse_dates=["signal_date", "execution_date"]
    )
    old = pd.read_csv(
        OLD_CONTRACT_PATH, parse_dates=["signal_date", "execution_date"]
    )
    date_set = set(canonical["signal_date"])
    indices = panel.index[
        panel["signal_date"].isin(date_set)
        & panel["execution_date"].notna()
        & pd.to_numeric(panel["SPY"], errors="coerce").notna()
    ].tolist()

    print("Validated raw replay A")
    raw_a = generate_raw(panel, indices)
    print("Validated raw replay B")
    raw_b = generate_raw(panel, indices)
    raw_identity = (
        raw_a.astype(str).to_dict("records")
        == raw_b.astype(str).to_dict("records")
    )

    rules = compile_taxonomy_rules(taxonomy_wrapper["spec"])
    classified_rows = []
    for record in raw_a.to_dict("records"):
        classified_rows.append({**record, **classify_candidate(record, rules)})
    contract = pd.DataFrame(classified_rows)

    old_dates = set(
        old.loc[old["v4_applied"].astype(str).str.lower().eq("true"), "signal_date"]
        .dt.strftime("%Y-%m-%d")
    )
    new_dates = set(
        contract.loc[contract["v4_applied"], "signal_date"].astype(str)
    )
    all_dates = sorted(old_dates | new_dates)
    diff_rows = []
    old_by_date = old.set_index(old["signal_date"].dt.strftime("%Y-%m-%d"))
    new_by_date = contract.set_index("signal_date")
    for date in all_dates:
        if date in old_dates and date in new_dates:
            status = "UNCHANGED"
        elif date in new_dates:
            status = "ADDED"
        else:
            status = "REMOVED"
        diff_rows.append({
            "signal_date": date,
            "date_status": status,
            "old_raw_macro_narrative": (
                old_by_date.loc[date, "raw_macro_narrative"] if date in old_by_date.index else ""
            ),
            "new_raw_macro_narrative": (
                new_by_date.loc[date, "raw_macro_narrative"] if date in new_by_date.index else ""
            ),
            "old_v4_state": old_by_date.loc[date, "v4_state"] if date in old_by_date.index else "",
            "old_v4_rule_id": old_by_date.loc[date, "v4_rule_id"] if date in old_by_date.index else "",
            "new_v4_state": new_by_date.loc[date, "v4_state"] if date in new_by_date.index else "",
            "new_v4_rule_id": new_by_date.loc[date, "v4_rule_id"] if date in new_by_date.index else "",
            "assignment_status": (
                "UNCHANGED_ASSIGNMENT"
                if status == "UNCHANGED"
                and old_by_date.loc[date, "v4_state"] == new_by_date.loc[date, "v4_state"]
                and old_by_date.loc[date, "v4_rule_id"] == new_by_date.loc[date, "v4_rule_id"]
                else "REASSIGNED"
                if status == "UNCHANGED"
                else status
            ),
        })
    diff = pd.DataFrame(diff_rows)

    applied = contract[contract["v4_applied"]]
    canonical_pairs = list(zip(
        canonical["signal_date"].dt.strftime("%Y-%m-%d"),
        canonical["execution_date"].dt.strftime("%Y-%m-%d"),
    ))
    generated_pairs = list(zip(raw_a["signal_date"], raw_a["execution_date"]))
    mapping_states = set(mapping_wrapper["spec"]["mapping"])
    checks = {
        "canonical_population_4645": len(raw_a) == EXPECTED_ROWS,
        "canonical_date_order_exact": generated_pairs == canonical_pairs,
        "raw_replay_deterministic": raw_identity,
        "taxonomy_semantic_hash_frozen": taxonomy_ok,
        "mapping_semantic_hash_frozen": mapping_ok,
        "taxonomy_rules_unchanged": len(rules) == 7,
        "core_us10y_provenance_all_rows": bool(raw_a["US10Y_CORE_PROVENANCE_MATCH"].all()),
        "intervention_raw_identity_all_unknown": bool(applied["raw_macro_narrative"].eq("UNKNOWN_TRANSITION").all()),
        "intervention_core_us10y_provenance": bool(applied["US10Y_CORE_PROVENANCE_MATCH"].all()),
        "intervention_rule_collision_zero": int((contract["collision_count"] > 1).sum()) == 0,
        "intervention_states_all_mapped": set(applied["v4_state"]).issubset(mapping_states),
        "date_diff_reconciles": (
            len(new_dates) == len(old_dates)
            + int((diff["date_status"] == "ADDED").sum())
            - int((diff["date_status"] == "REMOVED").sum())
        ),
    }
    protected_after = {
        str(path.relative_to(ROOT)): file_hash(path)
        for path in (OLD_CONTRACT_PATH, TAXONOMY_PATH, MAPPING_PATH)
    }
    checks["existing_contract_and_specs_unchanged"] = protected_before == protected_after
    status = "PASS" if all(checks.values()) else "FAIL"

    raw_a.to_csv(RAW_PATH, index=False)
    contract.to_csv(CONTRACT_PATH, index=False)
    diff.to_csv(DIFF_PATH, index=False)
    counts = diff["date_status"].value_counts().to_dict()
    assignment_counts = diff["assignment_status"].value_counts().to_dict()
    manifest = {
        "schema_version": 1,
        "gate": "VALIDATED_RAW_MACRO_AND_INTERVENTION_CONTRACT_REFREEZE",
        "status": status,
        "g1_release_id": G1_RELEASE_ID,
        "g4_status": "PASS",
        "production_sha": PRODUCTION_SHA,
        "research_sha": RESEARCH_SHA,
        "population": {
            "canonical_rows": len(raw_a),
            "validated_unknown_rows": int(raw_a["raw_macro_narrative"].eq("UNKNOWN_TRANSITION").sum()),
            "old_intervention_rows": len(old_dates),
            "new_intervention_rows": len(new_dates),
            "added_intervention_dates": int(counts.get("ADDED", 0)),
            "removed_intervention_dates": int(counts.get("REMOVED", 0)),
            "unchanged_intervention_dates": int(counts.get("UNCHANGED", 0)),
            "unchanged_rule_and_state_assignments": int(
                assignment_counts.get("UNCHANGED_ASSIGNMENT", 0)
            ),
            "reassigned_intervention_dates": int(
                assignment_counts.get("REASSIGNED", 0)
            ),
        },
        "provenance": {
            "master_panel_sha256": file_hash(PANEL_PATH),
            "canonical_dates_sha256": file_hash(CANONICAL_DATES_PATH),
            "market_data_builder_sha256": file_hash(BUILDER_PATH),
            "filter13_execution_chain_sha256": file_hash(EXECUTION_CHAIN_PATH),
            "taxonomy_semantic_sha256": EXPECTED_TAXONOMY_HASH,
            "mapping_semantic_sha256": EXPECTED_MAPPING_HASH,
            "us10y_source": "master_panel.csv::US10Y",
            "us10y_contract": "CANONICAL_CORE_SERIES_NO_NAMESPACE_OVERWRITE",
        },
        "checks": checks,
        "constraints": {
            "production_modified": False,
            "f13_f15_f18_modified": False,
            "threshold_or_mapping_modified": False,
            "returns_pnl_performance_used": False,
        },
        "downstream_status_at_contract_freeze": {
            "claim_5": "STALE_PENDING_RERUN",
            "temporal_scope": "BEFORE_VALIDATED_CAUSAL_REPLAY",
            "current_authority": (
                "data/backtest/results/claim5_validated_causal_propagation_v1/"
                "claim5_validated_causal_manifest_v1.json"
            ),
        },
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "VALIDATED RAW MACRO & INTERVENTION CONTRACT RE-FREEZE",
        "=" * 78,
        f"STATUS: {status}",
        f"Canonical raw rows: {len(raw_a)}",
        f"Validated UNKNOWN rows: {manifest['population']['validated_unknown_rows']}",
        f"Old intervention rows: {len(old_dates)}",
        f"New intervention rows: {len(new_dates)}",
        f"Added / Removed / Unchanged: {counts.get('ADDED', 0)} / {counts.get('REMOVED', 0)} / {counts.get('UNCHANGED', 0)}",
        f"Unchanged assignment / Reassigned: {assignment_counts.get('UNCHANGED_ASSIGNMENT', 0)} / {assignment_counts.get('REASSIGNED', 0)}",
        "", "CHECKS", "-" * 78,
    ]
    lines.extend(f"{key}: {'PASS' if value else 'FAIL'}" for key, value in checks.items())
    lines.extend([
        "", "BOUNDARIES", "-" * 78,
        "Frozen taxonomy changed: NO",
        "Frozen V4 mapping changed: NO",
        "Production/F13/F15/F18/threshold changed: NO",
        "Returns/PnL/performance used: NO",
        "#5 downstream status at contract freeze: STALE_PENDING_RERUN",
        "Temporal scope: BEFORE_VALIDATED_CAUSAL_REPLAY",
        "Current #5 authority: claim5_validated_causal_manifest_v1.json",
    ])
    AUDIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(AUDIT_PATH.read_text(encoding="utf-8"))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
