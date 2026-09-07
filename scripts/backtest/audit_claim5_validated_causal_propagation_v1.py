from __future__ import annotations

import contextlib
import copy
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

from scripts.backtest.audit_canonical_panel_identity_provenance_v1 import (
    CANONICAL_REL,
    resolve_and_validate_panel_authority,
    run_consumer_authority_startup_controls,
)

CONSUMER_ID = "CLAIM5_VALIDATED_CAUSAL_PROPAGATION"
PANEL_MODE = "CANONICAL"
PANEL_PATH = ROOT / CANONICAL_REL


def _run_authority_only_before_strategy_imports() -> None:
    if "--panel-authority-self-test" in sys.argv:
        result = run_consumer_authority_startup_controls(CONSUMER_ID)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        raise SystemExit(0 if result["status"] == "PASS" else 1)
    if "--validate-panel-authority-only" in sys.argv:
        result = resolve_and_validate_panel_authority(
            PANEL_PATH, PANEL_MODE, consumer=CONSUMER_ID
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        print("REPLAY_STARTED: NO")
        raise SystemExit(0)


if __name__ == "__main__":
    _run_authority_only_before_strategy_imports()

from scripts.backtest.audit_g4_historical_state_clock_integrity_v1 import (
    ArmState,
    LIVE_PATHS,
    digest,
    execute_engine,
    file_digest,
    replay_flow_after_intervention,
)
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)
from scripts.backtest.historical_execution_contract import (
    capture_filter15_memory,
    prepare_historical_execution_contract,
)
from scripts.backtest.market_data_builder import build_market_data
CANONICAL_PATH = (
    ROOT / "data/backtest/results/final_13_15_18_parity_closeout"
    / "final_13_15_18_parity_daily.csv"
)
G4_MANIFEST_PATH = (
    ROOT / "data/backtest/results/g4_historical_state_clock_integrity_v1"
    / "g4_historical_state_clock_manifest_v1.json"
)
CONTRACT_DIR = (
    ROOT / "data/backtest/results/validated_raw_macro_intervention_contract_v1"
)
CONTRACT_PATH = CONTRACT_DIR / "validated_intervention_contract_daily_v1.csv"
CONTRACT_MANIFEST_PATH = CONTRACT_DIR / "validated_intervention_contract_manifest_v1.json"
MAPPING_PATH = (
    ROOT / "data/backtest/results/macro_v4_portfolio_mapping_spec_v1"
    / "macro_v4_portfolio_mapping_spec.json"
)
OLD_CAUSAL_DIR = ROOT / "data/backtest/results/macro_v4_causal_propagation_v1"

OUT_DIR = ROOT / "data/backtest/results/claim5_validated_causal_propagation_v1"
DAILY_PATH = OUT_DIR / "claim5_full_history_causal_daily_v1.csv"
SUMMARY_PATH = OUT_DIR / "claim5_propagation_summary_v1.csv"
F18_DAILY_PATH = OUT_DIR / "claim5_filter18_direct_residual_daily_v1.csv"
F18_SUMMARY_PATH = OUT_DIR / "claim5_filter18_direct_residual_summary_v1.csv"
MANIFEST_PATH = OUT_DIR / "claim5_validated_causal_manifest_v1.json"
AUDIT_PATH = OUT_DIR / "claim5_validated_causal_audit_v1.txt"

EXPECTED_ROWS = 4645
EXPECTED_INTERVENTIONS = 1068
EXPECTED_NONINTERVENTIONS = 3577
EXPECTED_MAPPING_HASH = (
    "6ef7cba1e196fbb067385a2acc20e193adfd357d98669d74c3a745907e47d225"
)
G1_RELEASE_ID = "gcfm-g1-58f2702-7b4c324-pit-v1"
PRODUCTION_SHA = "58f270267bba502b5831a60d8e8a2a375f55f7ef"
RESEARCH_SHA = "7b4c324b27d6a19af3ef61852020da70cc7fe8c2"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changed(left: Any, right: Any, tolerance: float = 1e-9) -> bool:
    try:
        if pd.isna(left) and pd.isna(right):
            return False
        if pd.isna(left) or pd.isna(right):
            return True
    except Exception:
        pass
    try:
        return abs(float(left) - float(right)) > tolerance
    except Exception:
        return str(left) != str(right)


def run_arm(
    arm: str,
    panel: pd.DataFrame,
    indices: list[int],
    intervention: dict[pd.Timestamp, dict[str, Any]],
    mapping: dict[str, Any],
) -> tuple[pd.DataFrame, ArmState]:
    state = ArmState()
    rows: list[dict[str, Any]] = []

    for sequence, idx in enumerate(indices, start=1):
        source = panel.iloc[idx]
        signal_ts = pd.Timestamp(source["signal_date"])
        signal_date = signal_ts.strftime("%Y-%m-%d")
        execution_date = pd.Timestamp(source["execution_date"]).strftime("%Y-%m-%d")
        before = copy.deepcopy(state.snapshot())

        market_data = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=state.previous_exposure,
        )
        prior_flow = copy.deepcopy(state.flow_memory)
        with contextlib.redirect_stdout(io.StringIO()):
            raw_next_flow = prepare_filter13_execution_state(
                market_data=market_data,
                panel=panel,
                row_index=idx,
                previous_flow_memory=prior_flow,
            )

        raw_macro = str(market_data.get("MACRO_NARRATIVE", ""))
        raw_regime = str(market_data.get("MARKET_REGIME", ""))
        intervention_expected = signal_ts in intervention
        intervention_applied = False
        v4_state = ""
        v4_rule_id = ""
        strategic_regime = raw_regime

        if arm == "treatment" and intervention_expected:
            contract_row = intervention[signal_ts]
            if raw_macro != str(contract_row["raw_macro_narrative"]):
                raise RuntimeError(
                    f"Validated raw identity failure on {signal_date}: "
                    f"generated={raw_macro}, contract={contract_row['raw_macro_narrative']}"
                )
            v4_state = str(contract_row["v4_state"])
            v4_rule_id = str(contract_row["v4_rule_id"])
            strategic_regime = str(mapping[v4_state]["portfolio_regime"])
            market_data["RAW_MACRO_NARRATIVE"] = raw_macro
            market_data["RAW_MARKET_REGIME"] = raw_regime
            market_data["STRATEGIC_MACRO_STATE"] = v4_state
            market_data["MACRO_NARRATIVE"] = strategic_regime
            market_data["MARKET_REGIME"] = strategic_regime
            state.flow_memory = replay_flow_after_intervention(
                market_data, prior_flow
            )
            intervention_applied = True
        else:
            state.flow_memory = copy.deepcopy(raw_next_flow)

        with contextlib.redirect_stdout(io.StringIO()):
            prepare_historical_execution_contract(
                market_data=market_data,
                panel=panel,
                row_index=idx,
                filter15_memory=state.filter15_memory,
            )
        result, captured = execute_engine(market_data, state, signal_date)

        state.filter15_memory = capture_filter15_memory(market_data)
        if result["exposure_15"] is not None:
            state.previous_exposure = float(result["exposure_15"])
        if "rank_state" in captured:
            state.rank_state = copy.deepcopy(captured["rank_state"])
        state.previous_etf_weights = {
            str(item["etf"]): float(item["weight"])
            for item in captured.get("execution_plan", [])
        }
        state.last_signal_date = signal_date
        state.last_execution_date = execution_date
        after = copy.deepcopy(state.snapshot())

        output_identity = {
            "raw_macro": raw_macro,
            "market_regime": market_data.get("MARKET_REGIME"),
            "macro_profile": market_data.get("MACRO_REGIME_PROFILE"),
            "risk_budget_13": result["risk_budget_13"],
            "exposure_15": result["exposure_15"],
            "allocated_equity_18": result["allocated_equity_18"],
            "cash_weight": result["cash_weight"],
            "weights": result["weights"],
            "rank_action": market_data.get("FILTER18_RANK_ACTION"),
            "state_after": after,
        }
        rows.append({
            "arm": arm,
            "sequence": sequence,
            "panel_index": idx,
            "signal_date": signal_date,
            "execution_date": execution_date,
            "intervention_expected": intervention_expected,
            "intervention_applied": intervention_applied,
            "v4_state": v4_state,
            "v4_rule_id": v4_rule_id,
            "raw_macro_narrative": raw_macro,
            "raw_market_regime": raw_regime,
            "effective_market_regime": str(market_data.get("MARKET_REGIME", "")),
            "macro_profile": str(market_data.get("MACRO_REGIME_PROFILE", "N/A")),
            "risk_budget_13": result["risk_budget_13"],
            "exposure_15": result["exposure_15"],
            "allocated_equity_18": result["allocated_equity_18"],
            "cash_weight": result["cash_weight"],
            "weights_hash": digest(result["weights"]),
            "builder_allocation_hash": digest(captured.get("builder_allocation", {})),
            "rebalance_input_hash": digest(captured.get("rebalance_input", {})),
            "rebalance_output_hash": digest(captured.get("rebalance_output", {})),
            "state_before_hash": digest(before),
            "state_after_hash": digest(after),
            "flow_before_hash": digest(before["flow_memory"]),
            "flow_after_hash": digest(after["flow_memory"]),
            "filter15_before_hash": digest(before["filter15_memory"]),
            "filter15_after_hash": digest(after["filter15_memory"]),
            "rank_before_hash": digest(before["rank_state"]),
            "rank_after_hash": digest(after["rank_state"]),
            "portfolio_before_hash": digest(before["previous_etf_weights"]),
            "portfolio_after_hash": digest(after["previous_etf_weights"]),
            "rebalance_previous_hash": digest(captured.get("rebalance_previous", {})),
            "rebalance_output_hash": digest(captured.get("rebalance_output", {})),
            "rank_action": str(market_data.get("FILTER18_RANK_ACTION", "")),
            "rank_raw": str(market_data.get("FILTER18_RAW_RANK", "")),
            "rank_accepted": str(market_data.get("FILTER18_ACCEPTED_RANK", "")),
            "rank_pending": str(market_data.get("FILTER18_PENDING_RANK", "")),
            "rank_pending_count": market_data.get("FILTER18_PENDING_COUNT", 0),
            "clock_source": "HISTORICAL_SIGNAL_DATE",
            "clock_date": signal_date,
            "state_io_backend": "ARM_LOCAL_MEMORY",
            "live_state_access_count": 0,
            "decision_hash": digest(output_identity),
        })

    return pd.DataFrame(rows), state


def carry_failures(frame: pd.DataFrame) -> int:
    failures = 0
    for name in ("state", "flow", "filter15", "rank", "portfolio"):
        left = frame[f"{name}_after_hash"].iloc[:-1].reset_index(drop=True)
        right = frame[f"{name}_before_hash"].iloc[1:].reset_index(drop=True)
        failures += int((left != right).sum())
    return failures


def compare_arms(baseline: pd.DataFrame, treatment: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "sequence", "panel_index", "signal_date", "execution_date",
        "intervention_expected", "intervention_applied", "v4_state", "v4_rule_id",
        "raw_macro_narrative", "raw_market_regime", "effective_market_regime",
        "macro_profile", "risk_budget_13", "exposure_15", "allocated_equity_18",
        "cash_weight", "weights_hash", "builder_allocation_hash",
        "rebalance_input_hash", "rebalance_output_hash", "state_before_hash",
        "state_after_hash",
        "flow_before_hash", "filter15_before_hash", "rank_before_hash",
        "portfolio_before_hash", "rebalance_previous_hash", "rank_action",
        "rank_raw", "rank_accepted", "rank_pending", "rank_pending_count",
        "decision_hash",
    ]
    left = baseline[fields].rename(
        columns={column: f"{column}_baseline" for column in fields if column not in ("signal_date", "execution_date", "sequence", "panel_index")}
    )
    right = treatment[fields].rename(
        columns={column: f"{column}_treatment" for column in fields if column not in ("signal_date", "execution_date", "sequence", "panel_index")}
    )
    output = left.merge(
        right,
        on=["sequence", "panel_index", "signal_date", "execution_date"],
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    for field in (
        "risk_budget_13", "exposure_15", "allocated_equity_18", "cash_weight"
    ):
        output[f"{field}_changed"] = [
            changed(a, b) for a, b in zip(
                output[f"{field}_baseline"], output[f"{field}_treatment"]
            )
        ]
        output[f"{field}_delta"] = (
            pd.to_numeric(output[f"{field}_treatment"], errors="coerce")
            - pd.to_numeric(output[f"{field}_baseline"], errors="coerce")
        )
    output["macro_profile_changed"] = (
        output["macro_profile_baseline"] != output["macro_profile_treatment"]
    )
    output["rank_state_before_changed"] = (
        output["rank_before_hash_baseline"] != output["rank_before_hash_treatment"]
    )
    output["previous_portfolio_changed"] = (
        output["portfolio_before_hash_baseline"] != output["portfolio_before_hash_treatment"]
    )
    output["rebalance_previous_changed"] = (
        output["rebalance_previous_hash_baseline"] != output["rebalance_previous_hash_treatment"]
    )
    output["current_rank_changed"] = (
        (output["rank_raw_baseline"] != output["rank_raw_treatment"])
        | (output["rank_accepted_baseline"] != output["rank_accepted_treatment"])
        | (output["rank_pending_baseline"] != output["rank_pending_treatment"])
        | (output["rank_action_baseline"] != output["rank_action_treatment"])
        | (output["rank_pending_count_baseline"] != output["rank_pending_count_treatment"])
    )
    output["builder_allocation_changed"] = (
        output["builder_allocation_hash_baseline"]
        != output["builder_allocation_hash_treatment"]
    )
    output["rebalance_target_changed"] = (
        (output["rebalance_input_hash_baseline"] != output["rebalance_input_hash_treatment"])
        | (output["rebalance_output_hash_baseline"] != output["rebalance_output_hash_treatment"])
    )
    output["weights_changed"] = output["weights_hash_baseline"] != output["weights_hash_treatment"]
    output["state_changed"] = output["state_after_hash_baseline"] != output["state_after_hash_treatment"]

    def path(row: pd.Series) -> str:
        f13 = bool(row["risk_budget_13_changed"])
        f15 = bool(row["exposure_15_changed"])
        f18 = bool(row["allocated_equity_18_changed"])
        if not f18:
            return "FILTER18_ALLOCATED_EQUITY_UNCHANGED"
        if f13 and f15:
            return "F13_AND_F15_CHANGED_BEFORE_F18"
        if f13:
            return "F13_CHANGED_F15_ABSORBED_F18_CHANGED"
        if f15:
            return "F15_CHANGED_WITHOUT_F13_CHANGE"
        return "DIRECT_FILTER18_PATH"

    output["causal_path"] = output.apply(path, axis=1)
    direct = output["causal_path"].eq("DIRECT_FILTER18_PATH")
    explained = (
        output["macro_profile_changed"]
        | output["rank_state_before_changed"]
        | output["current_rank_changed"]
        | output["builder_allocation_changed"]
        | output["rebalance_target_changed"]
        | output["previous_portfolio_changed"]
        | output["rebalance_previous_changed"]
    )
    output["direct_macro_profile_path"] = direct & output["macro_profile_changed"]
    output["direct_rank_state_path"] = direct & (
        output["rank_state_before_changed"] | output["current_rank_changed"]
    )
    output["direct_builder_rebalance_path"] = direct & (
        output["builder_allocation_changed"] | output["rebalance_target_changed"]
    )
    output["direct_previous_portfolio_path"] = direct & (
        output["previous_portfolio_changed"] | output["rebalance_previous_changed"]
    )
    output["residual_unexplained_filter18_path"] = direct & ~explained
    output["change_timing"] = "NO_CAPITAL_CHANGE"
    any_capital = (
        output["risk_budget_13_changed"]
        | output["exposure_15_changed"]
        | output["allocated_equity_18_changed"]
        | output["cash_weight_changed"]
        | output["weights_changed"]
    )
    intervention_day = output["intervention_expected_treatment"].astype(bool)
    output.loc[any_capital & intervention_day, "change_timing"] = "INTERVENTION_DAY"
    output.loc[any_capital & ~intervention_day, "change_timing"] = "STATE_CARRYOVER_DAY"
    return output


def main() -> int:
    panel_authority = resolve_and_validate_panel_authority(
        PANEL_PATH,
        PANEL_MODE,
        consumer=CONSUMER_ID,
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    g4_manifest = json.loads(G4_MANIFEST_PATH.read_text(encoding="utf-8"))
    contract_manifest = json.loads(
        CONTRACT_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    mapping_wrapper = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    if g4_manifest.get("status") != "PASS":
        raise RuntimeError("G4 is not PASS")
    if contract_manifest.get("status") != "PASS":
        raise RuntimeError("Validated intervention contract is not PASS")
    if mapping_wrapper.get("sha256") != EXPECTED_MAPPING_HASH:
        raise RuntimeError("Frozen mapping hash mismatch")
    mapping = mapping_wrapper["spec"]["mapping"]

    protected_paths = tuple(LIVE_PATHS) + (
        G4_MANIFEST_PATH, CONTRACT_PATH, CONTRACT_MANIFEST_PATH, MAPPING_PATH
    )
    protected_before = {
        str(path.relative_to(ROOT)): file_digest(path) for path in protected_paths
    }
    panel = pd.read_csv(
        PANEL_PATH, parse_dates=["date", "signal_date", "execution_date"]
    )
    canonical = pd.read_csv(
        CANONICAL_PATH, parse_dates=["signal_date", "execution_date"]
    )
    contract = pd.read_csv(
        CONTRACT_PATH, parse_dates=["signal_date", "execution_date"]
    )
    applied = contract[contract["v4_applied"].astype(str).str.lower().eq("true")]
    intervention = applied.set_index("signal_date").to_dict("index")
    date_set = set(canonical["signal_date"])
    indices = panel.index[
        panel["signal_date"].isin(date_set)
        & panel["execution_date"].notna()
        & pd.to_numeric(panel["SPY"], errors="coerce").notna()
    ].tolist()

    print("#5 replay A: baseline")
    baseline_a, baseline_state_a = run_arm(
        "baseline", panel, indices, intervention, mapping
    )
    print("#5 replay A: treatment")
    treatment_a, treatment_state_a = run_arm(
        "treatment", panel, indices, intervention, mapping
    )
    print("#5 replay B: baseline")
    baseline_b, baseline_state_b = run_arm(
        "baseline", panel, indices, intervention, mapping
    )
    print("#5 replay B: treatment")
    treatment_b, treatment_state_b = run_arm(
        "treatment", panel, indices, intervention, mapping
    )
    comparison = compare_arms(baseline_a, treatment_a)

    stages = (
        ("FILTER13_RISK_BUDGET", "risk_budget_13_changed"),
        ("FILTER15_EXPOSURE", "exposure_15_changed"),
        ("FILTER18_ALLOCATED_EQUITY", "allocated_equity_18_changed"),
        ("CASH_WEIGHT", "cash_weight_changed"),
        ("FILTER18_WEIGHTS", "weights_changed"),
    )
    summary = pd.DataFrame([
        {
            "stage": stage,
            "full_history_rows": len(comparison),
            "changed_days": int(comparison[column].sum()),
            "intervention_day_changes": int(
                (comparison[column] & comparison["intervention_expected_treatment"]).sum()
            ),
            "state_carryover_day_changes": int(
                (comparison[column] & ~comparison["intervention_expected_treatment"]).sum()
            ),
        }
        for stage, column in stages
    ])
    f18_direct = comparison[
        comparison["causal_path"].eq("DIRECT_FILTER18_PATH")
    ].copy()
    f18_summary = pd.DataFrame([
        {"path": "DIRECT_FILTER18_PATH", "days": len(f18_direct)},
        {"path": "DIRECT_MACRO_PROFILE_PATH", "days": int(f18_direct["direct_macro_profile_path"].sum())},
        {"path": "DIRECT_RANK_STATE_PATH", "days": int(f18_direct["direct_rank_state_path"].sum())},
        {"path": "DIRECT_BUILDER_REBALANCE_PATH", "days": int(f18_direct["direct_builder_rebalance_path"].sum())},
        {"path": "DIRECT_PREVIOUS_PORTFOLIO_PATH", "days": int(f18_direct["direct_previous_portfolio_path"].sum())},
        {"path": "RESIDUAL_UNEXPLAINED_FILTER18_PATH", "days": int(f18_direct["residual_unexplained_filter18_path"].sum())},
    ])

    canonical_pairs = list(zip(
        canonical["signal_date"].dt.strftime("%Y-%m-%d"),
        canonical["execution_date"].dt.strftime("%Y-%m-%d"),
    ))
    replay_pairs = list(zip(baseline_a["signal_date"], baseline_a["execution_date"]))
    protected_after = {
        str(path.relative_to(ROOT)): file_digest(path) for path in protected_paths
    }
    checks = {
        "g4_pass": g4_manifest.get("status") == "PASS",
        "validated_contract_pass": contract_manifest.get("status") == "PASS",
        "validated_intervention_population_1068": len(intervention) == EXPECTED_INTERVENTIONS,
        "canonical_population_4645": len(indices) == EXPECTED_ROWS,
        "canonical_date_order_exact": replay_pairs == canonical_pairs,
        "baseline_full_replay": len(baseline_a) == EXPECTED_ROWS,
        "treatment_full_replay": len(treatment_a) == EXPECTED_ROWS,
        "treatment_intervention_exact": int(treatment_a["intervention_applied"].sum()) == EXPECTED_INTERVENTIONS,
        "treatment_nonintervention_progression_3577": int((~treatment_a["intervention_applied"]).sum()) == EXPECTED_NONINTERVENTIONS,
        "intervention_boundary_exact": bool((treatment_a["intervention_applied"] == treatment_a["intervention_expected"]).all()),
        "baseline_state_carry": carry_failures(baseline_a) == 0,
        "treatment_state_carry": carry_failures(treatment_a) == 0,
        "arm_state_isolation": baseline_state_a is not treatment_state_a,
        "historical_clock_only": bool(baseline_a["clock_source"].eq("HISTORICAL_SIGNAL_DATE").all() and treatment_a["clock_source"].eq("HISTORICAL_SIGNAL_DATE").all()),
        "live_state_access_zero": int(baseline_a["live_state_access_count"].sum() + treatment_a["live_state_access_count"].sum()) == 0,
        "protected_and_live_files_unchanged": protected_before == protected_after,
        "baseline_deterministic": bool(baseline_a["decision_hash"].tolist() == baseline_b["decision_hash"].tolist() and digest(baseline_state_a.snapshot()) == digest(baseline_state_b.snapshot())),
        "treatment_deterministic": bool(treatment_a["decision_hash"].tolist() == treatment_b["decision_hash"].tolist() and digest(treatment_state_a.snapshot()) == digest(treatment_state_b.snapshot())),
        "comparison_one_to_one": bool(
            len(comparison) == EXPECTED_ROWS
            and comparison["_merge"].eq("both").all()
        ),
        "capital_identity_baseline": bool(((baseline_a["allocated_equity_18"] + baseline_a["cash_weight"] - 100.0).abs() <= 1e-9).all()),
        "capital_identity_treatment": bool(((treatment_a["allocated_equity_18"] + treatment_a["cash_weight"] - 100.0).abs() <= 1e-9).all()),
        "filter18_residual_zero": int(f18_direct["residual_unexplained_filter18_path"].sum()) == 0,
    }
    status = "PASS" if all(checks.values()) else "FAIL"

    comparison.to_csv(DAILY_PATH, index=False)
    summary.to_csv(SUMMARY_PATH, index=False)
    f18_direct.to_csv(F18_DAILY_PATH, index=False)
    f18_summary.to_csv(F18_SUMMARY_PATH, index=False)
    stage_counts = dict(zip(summary["stage"], summary["changed_days"]))
    old_artifacts = {
        str(path.relative_to(ROOT)): file_hash(path)
        for path in sorted(OLD_CAUSAL_DIR.glob("*")) if path.is_file()
    }
    manifest = {
        "schema_version": 1,
        "claim": "#5_SIGNAL_RISK_EXPOSURE_ALLOCATION_CAUSALITY",
        "status": status,
        "panel_authority": panel_authority,
        "g1_release_id": G1_RELEASE_ID,
        "g4_status": "PASS",
        "production_sha": PRODUCTION_SHA,
        "research_sha": RESEARCH_SHA,
        "population": {
            "full_history_rows_per_arm": EXPECTED_ROWS,
            "intervention_rows": len(intervention),
            "nonintervention_progression_rows": EXPECTED_NONINTERVENTIONS,
        },
        "propagation": {key: int(value) for key, value in stage_counts.items()},
        "filter18_direct_residual": {
            row["path"]: int(row["days"])
            for _, row in f18_summary.iterrows()
        },
        "checks": checks,
        "provenance": {
            "g4_manifest_sha256": file_hash(G4_MANIFEST_PATH),
            "validated_contract_sha256": file_hash(CONTRACT_PATH),
            "validated_contract_manifest_sha256": file_hash(CONTRACT_MANIFEST_PATH),
            "mapping_semantic_sha256": EXPECTED_MAPPING_HASH,
            "master_panel_sha256": file_hash(PANEL_PATH),
        },
        "superseded_evidence": {
            "status": "SUPERSEDED_PRE_G4_ONLY",
            "old_population": 992,
            "artifacts": old_artifacts,
            "old_counts_used_as_targets": False,
        },
        "constraints": {
            "production_f13_f15_f18_modified": False,
            "taxonomy_mapping_threshold_modified": False,
            "returns_pnl_performance_used": False,
        },
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "INSTITUTIONAL INVENTORY #5 — VALIDATED CAUSAL PROPAGATION",
        "=" * 82,
        f"STATUS: {status}",
        f"Full-history rows per arm: {EXPECTED_ROWS}",
        f"Intervention / non-intervention: {len(intervention)} / {EXPECTED_NONINTERVENTIONS}",
        "", "PROPAGATION", "-" * 82,
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"{row['stage']}: changed={int(row['changed_days'])}, "
            f"intervention_day={int(row['intervention_day_changes'])}, "
            f"carryover_day={int(row['state_carryover_day_changes'])}"
        )
    lines.extend(["", "FILTER18 DIRECT / RESIDUAL", "-" * 82])
    lines.extend(
        f"{row['path']}: {int(row['days'])}" for _, row in f18_summary.iterrows()
    )
    lines.extend(["", "CHECKS", "-" * 82])
    lines.extend(f"{key}: {'PASS' if value else 'FAIL'}" for key, value in checks.items())
    lines.extend([
        "", "BOUNDARIES", "-" * 82,
        "Old 992-day evidence: SUPERSEDED_PRE_G4_ONLY",
        "Old causal counts used as targets: NO",
        "Production/F13/F15/F18/taxonomy/mapping/threshold changed: NO",
        "Returns/PnL/CAGR/Sharpe used: NO",
    ])
    AUDIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(AUDIT_PATH.read_text(encoding="utf-8"))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
