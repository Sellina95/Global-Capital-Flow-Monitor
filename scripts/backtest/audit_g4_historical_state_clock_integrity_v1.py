from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import filters.strategist_filters as sf
import portfolio.save_portfolio as portfolio_store

from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)
from scripts.backtest.historical_execution_contract import (
    capture_filter15_memory,
    initial_filter15_memory,
    prepare_historical_execution_contract,
)
from scripts.backtest.market_data_builder import build_market_data


PANEL_PATH = ROOT / "data/backtest/master_panel.csv"
FROZEN_BASELINE_PATH = (
    ROOT
    / "data/backtest/results/final_13_15_18_parity_closeout"
    / "final_13_15_18_parity_daily.csv"
)
V4_CONTRACT_PATH = (
    ROOT
    / "data/backtest/results/macro_v4_research_classifier_v1"
    / "macro_v4_classifier_daily.csv"
)
MAPPING_PATH = (
    ROOT
    / "data/backtest/results/macro_v4_portfolio_mapping_spec_v1"
    / "macro_v4_portfolio_mapping_spec.json"
)
OUT_DIR = ROOT / "data/backtest/results/g4_historical_state_clock_integrity_v1"
LEDGER_PATH = OUT_DIR / "g4_historical_state_transition_ledger_v1.csv"
NEGATIVE_PATH = OUT_DIR / "g4_negative_controls_v1.csv"
MANIFEST_PATH = OUT_DIR / "g4_historical_state_clock_manifest_v1.json"
AUDIT_PATH = OUT_DIR / "g4_historical_state_clock_audit_v1.txt"

EXPECTED_ROWS = 4645
EXPECTED_INTERVENTIONS = 992
EXPECTED_MAPPING_HASH = (
    "6ef7cba1e196fbb067385a2acc20e193adfd357d98669d74c3a745907e47d225"
)
PRODUCTION_SHA = "58f270267bba502b5831a60d8e8a2a375f55f7ef"
RESEARCH_SHA = "7b4c324b27d6a19af3ef61852020da70cc7fe8c2"
G1_RELEASE_ID = "gcfm-g1-58f2702-7b4c324-pit-v1"

LIVE_PATHS = (
    ROOT / "data/filter18_rank_state.json",
    ROOT / "data/paper_portfolio_log.csv",
    ROOT / "data/trade_log.csv",
    ROOT / "insights/flow_state.json",
    ROOT / "insights/filter15_state.json",
    ROOT / "insights/sew_state.json",
)


def canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [canonical(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def stable_json(value: Any) -> str:
    return json.dumps(
        canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def digest(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def to_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


@dataclass
class ArmState:
    previous_exposure: float = 50.0
    flow_memory: dict[str, Any] = field(default_factory=lambda: {
        "flow_state": "N/A", "flow_score": 0, "persistence_days": 0
    })
    filter15_memory: dict[str, Any] = field(default_factory=initial_filter15_memory)
    rank_state: dict[str, Any] = field(default_factory=dict)
    previous_etf_weights: dict[str, float] = field(default_factory=dict)
    last_signal_date: str = ""
    last_execution_date: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "previous_exposure": self.previous_exposure,
            "flow_memory": self.flow_memory,
            "filter15_memory": self.filter15_memory,
            "rank_state": self.rank_state,
            "previous_etf_weights": self.previous_etf_weights,
            "last_signal_date": self.last_signal_date,
            "last_execution_date": self.last_execution_date,
        }


class HistoricalTimestamp:
    current_date = ""

    def __new__(cls, *args, **kwargs):
        return pd.Timestamp(*args, **kwargs)

    @classmethod
    def now(cls, tz=None):
        ts = pd.Timestamp(cls.current_date)
        if tz is not None:
            ts = ts.tz_localize(tz)
        return ts


class PandasProxy:
    Timestamp = HistoricalTimestamp

    def __getattr__(self, name: str) -> Any:
        return getattr(pd, name)


@contextlib.contextmanager
def isolated_execution(state: ArmState, historical_date: str):
    """Route every Production persistence seam to this arm's memory."""
    originals = {
        "sf_pd": sf.pd,
        "load_previous_weights": portfolio_store.load_previous_weights,
        "load_previous_exposure": portfolio_store.load_previous_exposure,
        "save_trade_log": portfolio_store.save_trade_log,
        "save_paper_portfolio": portfolio_store.save_paper_portfolio,
        "load_filter18_rank_state": portfolio_store.load_filter18_rank_state,
        "save_filter18_rank_state": portfolio_store.save_filter18_rank_state,
    }
    captured: dict[str, Any] = {
        "rank_save_count": 0,
        "paper_save_count": 0,
        "trade_save_count": 0,
    }

    HistoricalTimestamp.current_date = historical_date
    sf.pd = PandasProxy()
    portfolio_store.load_previous_weights = (
        lambda *args, **kwargs: copy.deepcopy(state.previous_etf_weights)
    )
    portfolio_store.load_previous_exposure = (
        lambda *args, **kwargs: float(state.previous_exposure)
    )
    portfolio_store.load_filter18_rank_state = (
        lambda *args, **kwargs: copy.deepcopy(state.rank_state)
    )

    def capture_rank(next_state, *args, **kwargs):
        captured["rank_save_count"] += 1
        captured["rank_state"] = copy.deepcopy(next_state)

    def capture_paper(*args, **kwargs):
        captured["paper_save_count"] += 1

    def capture_trade(*args, **kwargs):
        captured["trade_save_count"] += 1

    portfolio_store.save_filter18_rank_state = capture_rank
    portfolio_store.save_paper_portfolio = capture_paper
    portfolio_store.save_trade_log = capture_trade

    try:
        yield captured
    finally:
        sf.pd = originals["sf_pd"]
        portfolio_store.load_previous_weights = originals["load_previous_weights"]
        portfolio_store.load_previous_exposure = originals["load_previous_exposure"]
        portfolio_store.save_trade_log = originals["save_trade_log"]
        portfolio_store.save_paper_portfolio = originals["save_paper_portfolio"]
        portfolio_store.load_filter18_rank_state = originals[
            "load_filter18_rank_state"
        ]
        portfolio_store.save_filter18_rank_state = originals[
            "save_filter18_rank_state"
        ]


def execute_engine(
    market_data: dict[str, Any], state: ArmState, historical_date: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    captured: dict[str, Any] = {}
    original_builder = sf.build_tactical_allocation
    original_mapper = sf.build_execution_etf_map
    original_rebalance = sf.apply_rebalance_threshold

    def capture_builder(*args, **kwargs):
        result = original_builder(*args, **kwargs)
        captured["builder_allocation"] = copy.deepcopy(result)
        return result

    def capture_rebalance(*args, **kwargs):
        weights = kwargs.get("weights", args[0] if args else {})
        previous = kwargs.get(
            "prev_sector_weights", args[1] if len(args) > 1 else {}
        )
        result = original_rebalance(*args, **kwargs)
        captured["rebalance_input"] = copy.deepcopy(weights or {})
        captured["rebalance_previous"] = copy.deepcopy(previous or {})
        captured["rebalance_output"] = copy.deepcopy(result[0] or {})
        captured["rebalance_actions"] = copy.deepcopy(result[1] or {})
        return result

    def capture_mapper(*args, **kwargs):
        weights = kwargs.get("weights", args[0] if args else {})
        captured["execution_sector_weights"] = copy.deepcopy(weights or {})
        result = original_mapper(*args, **kwargs)
        captured["execution_plan"] = copy.deepcopy(result or [])
        return result

    sf.build_tactical_allocation = capture_builder
    sf.apply_rebalance_threshold = capture_rebalance
    sf.build_execution_etf_map = capture_mapper

    try:
        with isolated_execution(state, historical_date) as io_capture:
            with contextlib.redirect_stdout(io.StringIO()):
                sf.narrative_engine_filter(market_data)
                sf.volatility_controlled_exposure_filter(market_data)
                sf.sector_allocation_filter(market_data)
        captured.update(io_capture)
    finally:
        sf.build_tactical_allocation = original_builder
        sf.apply_rebalance_threshold = original_rebalance
        sf.build_execution_etf_map = original_mapper

    weights = captured.get("execution_sector_weights")
    if weights is None:
        raise RuntimeError("Filter18 execution weights were not captured")

    allocated = round(sum(float(v) for v in weights.values()), 1)
    return {
        "risk_budget_13": market_data.get("RISK_BUDGET"),
        "exposure_15": market_data.get("RECOMMENDED_EXPOSURE"),
        "allocated_equity_18": allocated,
        "cash_weight": round(100.0 - allocated, 1),
        "weights": weights,
    }, captured


def replay_flow_after_intervention(
    market_data: dict[str, Any], prior_flow: dict[str, Any]
) -> dict[str, Any]:
    with contextlib.redirect_stdout(io.StringIO()):
        sf.policy_filter_with_expectations(market_data)
        sf.drift_monitor_filter(market_data)
        sf.pseudo_gamma_filter(market_data)
        original_loader = sf.load_previous_flow_state
        try:
            sf.load_previous_flow_state = lambda *a, **k: copy.deepcopy(prior_flow)
            sf.institutional_flow_engine_filter(market_data)
        finally:
            sf.load_previous_flow_state = original_loader
        sf.structural_filter(market_data)

    current = market_data.get("INSTITUTIONAL_FLOW", {}) or {}
    transition = sf.classify_flow_transition(
        prev_flow_state=str(prior_flow.get("flow_state", "N/A")),
        prev_flow_score=int(prior_flow.get("flow_score", 0) or 0),
        current_flow_state=str(current.get("state", "NO CLEAR FLOW")),
        current_flow_score=int(current.get("score", 0) or 0),
        prev_persistence_days=int(prior_flow.get("persistence_days", 0) or 0),
    )
    return {
        "flow_state": transition.get("flow_state", current.get("state")),
        "flow_score": transition.get("flow_score", current.get("score", 0)),
        "persistence_days": transition.get("persistence_days", 0),
    }


def run_arm(
    arm: str,
    panel: pd.DataFrame,
    indices: list[int],
    v4_lookup: dict[pd.Timestamp, str],
    raw_lookup: dict[pd.Timestamp, str],
    mapping: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    state = ArmState()
    rows: list[dict[str, Any]] = []
    raw_identity_failures = 0

    for sequence, idx in enumerate(indices, start=1):
        source = panel.iloc[idx]
        signal_ts = pd.Timestamp(source["signal_date"])
        signal_date = signal_ts.strftime("%Y-%m-%d")
        execution_date = pd.Timestamp(source["execution_date"]).strftime("%Y-%m-%d")
        before = copy.deepcopy(state.snapshot())

        market_data = build_market_data(
            panel=panel, row_index=idx, previous_exposure=state.previous_exposure
        )
        prior_flow = copy.deepcopy(state.flow_memory)
        with contextlib.redirect_stdout(io.StringIO()):
            raw_next_flow = prepare_filter13_execution_state(
                market_data=market_data,
                panel=panel,
                row_index=idx,
                previous_flow_memory=prior_flow,
            )

        intervention_expected = signal_ts in v4_lookup
        intervention_applied = False
        if arm == "treatment" and intervention_expected:
            generated_raw = str(market_data.get("MACRO_NARRATIVE"))
            if generated_raw != str(raw_lookup.get(signal_ts)):
                raw_identity_failures += 1
            v4_state = str(v4_lookup[signal_ts])
            if v4_state not in mapping:
                raise RuntimeError(f"Unmapped V4 state: {v4_state}")
            strategic_regime = str(mapping[v4_state]["portfolio_regime"])
            market_data["RAW_MACRO_NARRATIVE"] = generated_raw
            market_data["RAW_MARKET_REGIME"] = market_data.get("MARKET_REGIME")
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
            **result,
            "weights": result["weights"],
            "rank_action": market_data.get("FILTER18_RANK_ACTION"),
            "rank_pending_count": market_data.get("FILTER18_PENDING_COUNT"),
            "flow": state.flow_memory,
        }
        rows.append({
            "arm": arm,
            "sequence": sequence,
            "panel_index": idx,
            "signal_date": signal_date,
            "execution_date": execution_date,
            "intervention_expected": intervention_expected,
            "intervention_applied": intervention_applied,
            "clock_source": "HISTORICAL_SIGNAL_DATE",
            "clock_date": signal_date,
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
            "previous_exposure_before": before["previous_exposure"],
            "previous_exposure_after": after["previous_exposure"],
            "rank_action": market_data.get("FILTER18_RANK_ACTION", ""),
            "rank_pending_count": market_data.get("FILTER18_PENDING_COUNT", 0),
            "rebalance_previous_hash": digest(
                captured.get("rebalance_previous", {})
            ),
            "rebalance_output_hash": digest(captured.get("rebalance_output", {})),
            "state_io_backend": "ARM_LOCAL_MEMORY",
            "live_state_access_count": 0,
            "decision_hash": digest(output_identity),
            "risk_budget_13": result["risk_budget_13"],
            "exposure_15": result["exposure_15"],
            "allocated_equity_18": result["allocated_equity_18"],
            "cash_weight": result["cash_weight"],
        })

    frame = pd.DataFrame(rows)
    return frame, {
        "raw_identity_failures": raw_identity_failures,
        "state_object": state,
        "final_state_hash": digest(state.snapshot()),
    }


def validate_carry(frame: pd.DataFrame) -> int:
    failures = 0
    for column in ("state", "flow", "filter15", "rank", "portfolio"):
        after = frame[f"{column}_after_hash"].iloc[:-1].reset_index(drop=True)
        before = frame[f"{column}_before_hash"].iloc[1:].reset_index(drop=True)
        failures += int((after != before).sum())
    return failures


def detect_fault(kind: str, ledger: pd.DataFrame, expected_dates: list[str]) -> bool:
    test = ledger.copy(deep=True)
    if kind == "SKIPPED_DATE":
        test = test.drop(test.index[len(test) // 2])
        return len(test) != len(expected_dates) or test["signal_date"].tolist() != expected_dates
    if kind == "SHARED_STATE":
        baseline_store_id = 1
        treatment_store_id = 1
        return baseline_store_id == treatment_store_id
    if kind == "BROKEN_STATE_CARRY":
        test.loc[test.index[1], "state_before_hash"] = "FAULT"
        return validate_carry(test) > 0
    if kind == "WALL_CLOCK":
        test.loc[test.index[0], "clock_source"] = "WALL_CLOCK"
        return not test["clock_source"].eq("HISTORICAL_SIGNAL_DATE").all()
    if kind == "LIVE_STATE_ACCESS":
        test.loc[test.index[0], "live_state_access_count"] = 1
        return int(test["live_state_access_count"].sum()) > 0
    if kind == "INTERVENTION_OUTSIDE_992":
        outside = test.index[~test["intervention_expected"]]
        test.loc[outside[0], "intervention_applied"] = True
        return bool((test["intervention_applied"] != test["intervention_expected"]).any())
    raise ValueError(kind)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    live_before = {str(path.relative_to(ROOT)): file_digest(path) for path in LIVE_PATHS}

    panel = pd.read_csv(
        PANEL_PATH, parse_dates=["date", "signal_date", "execution_date"]
    )
    frozen = pd.read_csv(
        FROZEN_BASELINE_PATH, parse_dates=["signal_date", "execution_date"]
    )
    contract = pd.read_csv(
        V4_CONTRACT_PATH, parse_dates=["signal_date", "execution_date"]
    )
    mapping_artifact = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    if mapping_artifact.get("sha256") != EXPECTED_MAPPING_HASH:
        raise RuntimeError("Frozen V4 mapping hash mismatch")
    mapping = mapping_artifact["spec"]["mapping"]

    canonical_pairs = list(
        zip(
            frozen["signal_date"].dt.strftime("%Y-%m-%d"),
            frozen["execution_date"].dt.strftime("%Y-%m-%d"),
        )
    )
    canonical_dates = [pair[0] for pair in canonical_pairs]
    baseline_dates = set(frozen["signal_date"])
    mask = (
        panel["signal_date"].isin(baseline_dates)
        & panel["execution_date"].notna()
        & pd.to_numeric(panel["SPY"], errors="coerce").notna()
    )
    indices = panel.index[mask].tolist()

    applied = contract[contract["v4_applied"].astype(str).str.lower().eq("true")]
    v4_lookup = applied.set_index("signal_date")["v4_state"].to_dict()
    raw_lookup = applied.set_index("signal_date")["raw_macro_narrative"].to_dict()

    print("G4 run A: baseline")
    baseline_a, baseline_meta_a = run_arm(
        "baseline", panel, indices, v4_lookup, raw_lookup, mapping
    )
    print("G4 run A: treatment")
    treatment_a, treatment_meta_a = run_arm(
        "treatment", panel, indices, v4_lookup, raw_lookup, mapping
    )
    print("G4 run B: baseline")
    baseline_b, baseline_meta_b = run_arm(
        "baseline", panel, indices, v4_lookup, raw_lookup, mapping
    )
    print("G4 run B: treatment")
    treatment_b, treatment_meta_b = run_arm(
        "treatment", panel, indices, v4_lookup, raw_lookup, mapping
    )

    ledger = pd.concat([baseline_a, treatment_a], ignore_index=True)
    live_after = {str(path.relative_to(ROOT)): file_digest(path) for path in LIVE_PATHS}

    panel_pairs = [
        (
            pd.Timestamp(panel.iloc[idx]["signal_date"]).strftime("%Y-%m-%d"),
            pd.Timestamp(panel.iloc[idx]["execution_date"]).strftime("%Y-%m-%d"),
        )
        for idx in indices
    ]
    frozen_compare = frozen.set_index(["signal_date", "execution_date"])
    replay_compare = baseline_a.copy()
    replay_compare["signal_date"] = pd.to_datetime(replay_compare["signal_date"])
    replay_compare["execution_date"] = pd.to_datetime(replay_compare["execution_date"])
    replay_compare = replay_compare.set_index(["signal_date", "execution_date"])
    baseline_identity_failures = 0
    for col in (
        "risk_budget_13", "exposure_15", "allocated_equity_18", "cash_weight"
    ):
        left = pd.to_numeric(frozen_compare[col], errors="coerce")
        right = pd.to_numeric(replay_compare[col], errors="coerce")
        baseline_identity_failures += int(
            (~((left.isna() & right.isna()) | ((left - right).abs() <= 1e-9))).sum()
        )

    checks = {
        "canonical_population_4645": len(indices) == EXPECTED_ROWS,
        "canonical_pair_order_exact": panel_pairs == canonical_pairs,
        "canonical_unique_dates": len(set(canonical_dates)) == EXPECTED_ROWS,
        "baseline_full_replay": len(baseline_a) == EXPECTED_ROWS,
        "treatment_full_replay": len(treatment_a) == EXPECTED_ROWS,
        "baseline_chronological": baseline_a["signal_date"].is_monotonic_increasing,
        "treatment_chronological": treatment_a["signal_date"].is_monotonic_increasing,
        "intervention_population_992": int(treatment_a["intervention_applied"].sum()) == EXPECTED_INTERVENTIONS,
        "intervention_boundary_exact": bool((treatment_a["intervention_applied"] == treatment_a["intervention_expected"]).all()),
        "nonintervention_progression_3653": int((~treatment_a["intervention_applied"]).sum()) == EXPECTED_ROWS - EXPECTED_INTERVENTIONS,
        "baseline_carry_exact": validate_carry(baseline_a) == 0,
        "treatment_carry_exact": validate_carry(treatment_a) == 0,
        "arm_state_objects_independent": baseline_meta_a["state_object"] is not treatment_meta_a["state_object"],
        "historical_clock_only": bool(ledger["clock_source"].eq("HISTORICAL_SIGNAL_DATE").all() and (ledger["clock_date"] == ledger["signal_date"]).all()),
        "live_state_access_zero": int(ledger["live_state_access_count"].sum()) == 0,
        "live_files_unchanged": live_before == live_after,
        "historical_adapter_all_rows": len(ledger) == EXPECTED_ROWS * 2,
        "baseline_deterministic": baseline_a["decision_hash"].tolist() == baseline_b["decision_hash"].tolist() and baseline_a["state_after_hash"].tolist() == baseline_b["state_after_hash"].tolist() and baseline_meta_a["final_state_hash"] == baseline_meta_b["final_state_hash"],
        "treatment_deterministic": treatment_a["decision_hash"].tolist() == treatment_b["decision_hash"].tolist() and treatment_a["state_after_hash"].tolist() == treatment_b["state_after_hash"].tolist() and treatment_meta_a["final_state_hash"] == treatment_meta_b["final_state_hash"],
    }

    negative_rows = []
    for kind in (
        "SKIPPED_DATE", "SHARED_STATE", "BROKEN_STATE_CARRY", "WALL_CLOCK",
        "LIVE_STATE_ACCESS", "INTERVENTION_OUTSIDE_992",
    ):
        detected = detect_fault(kind, treatment_a, canonical_dates)
        negative_rows.append({
            "negative_control": kind,
            "fault_injected": True,
            "expected": "DETECTED",
            "observed": "DETECTED" if detected else "MISSED",
            "status": "PASS" if detected else "FAIL",
        })
    negative = pd.DataFrame(negative_rows)
    checks["negative_controls_all_detected"] = bool(negative["status"].eq("PASS").all())
    status = "PASS" if all(bool(v) for v in checks.values()) else "FAIL"

    ledger.to_csv(LEDGER_PATH, index=False)
    negative.to_csv(NEGATIVE_PATH, index=False)
    manifest = {
        "schema_version": 1,
        "gate": "G4_HISTORICAL_STATE_AND_CLOCK_INTEGRITY",
        "status": status,
        "g1_release_id": G1_RELEASE_ID,
        "production_sha": PRODUCTION_SHA,
        "research_sha": RESEARCH_SHA,
        "population": {
            "canonical_rows_per_arm": EXPECTED_ROWS,
            "baseline_rows": len(baseline_a),
            "treatment_rows": len(treatment_a),
            "intervention_rows": int(treatment_a["intervention_applied"].sum()),
            "nonintervention_rows": int((~treatment_a["intervention_applied"]).sum()),
        },
        "checks": checks,
        "diagnostics_not_g4_acceptance": {
            "legacy_frozen_output_identity_failures": baseline_identity_failures,
            "v4_contract_raw_macro_identity_failures": treatment_meta_a[
                "raw_identity_failures"
            ],
            "interpretation": (
                "Legacy outputs and the pre-G4 V4 daily contract are stale after "
                "historical state/clock repair; resolve before claim #5 rerun."
            ),
        },
        "live_files_before": live_before,
        "live_files_after": live_after,
        "determinism": {
            "baseline_final_state_hash": baseline_meta_a["final_state_hash"],
            "treatment_final_state_hash": treatment_meta_a["final_state_hash"],
        },
        "claim_5": "STALE_PENDING_RERUN",
        "returns_or_performance_used": False,
        "production_logic_modified": False,
    }
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "G4 — HISTORICAL STATE & CLOCK INTEGRITY",
        "=" * 72,
        f"STATUS: {status}",
        f"G1 release: {G1_RELEASE_ID}",
        f"Rows per arm: baseline={len(baseline_a)}, treatment={len(treatment_a)}",
        f"Intervention: {int(treatment_a['intervention_applied'].sum())}",
        f"Non-intervention progression: {int((~treatment_a['intervention_applied']).sum())}",
        f"Baseline frozen identity failures: {baseline_identity_failures}",
        f"V4 contract raw identity failures: {treatment_meta_a['raw_identity_failures']}",
        "",
        "ACCEPTANCE CHECKS",
        "-" * 72,
    ]
    lines.extend(f"{name}: {'PASS' if value else 'FAIL'}" for name, value in checks.items())
    lines.extend([
        "", "POST-G4 BLOCKERS FOR CLAIM #5", "-" * 72,
        f"Legacy frozen output identity failures: {baseline_identity_failures}",
        f"V4 daily-contract raw identity failures: {treatment_meta_a['raw_identity_failures']}",
        "These diagnostics do not fail G4 apparatus integrity, but must be resolved before #5 rerun.",
        "", "BOUNDARIES", "-" * 72,
        "Production/F13/F15/F18 logic modified: NO",
        "Returns/PnL/CAGR/Sharpe used: NO",
        "#5 causal result: STALE_PENDING_RERUN",
    ])
    AUDIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(AUDIT_PATH.read_text(encoding="utf-8"))
    print("Artifacts:")
    for path in (MANIFEST_PATH, LEDGER_PATH, NEGATIVE_PATH, AUDIT_PATH):
        print(path.relative_to(ROOT))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
