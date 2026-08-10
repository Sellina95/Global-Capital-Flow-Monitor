from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)

ROOT = Path(__file__).resolve().parents[2]
PANEL_PATH = ROOT / "data" / "backtest" / "master_panel.csv"

START_DATE = pd.Timestamp("2026-06-08")
END_DATE = pd.Timestamp("2026-06-19")


def main() -> None:
    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=["date", "signal_date", "execution_date"],
    )

    mask = (
        panel["signal_date"].ge(START_DATE)
        & panel["signal_date"].le(END_DATE)
        & panel["execution_date"].notna()
        & pd.to_numeric(panel["SPY"], errors="coerce").notna()
    )

    indices = panel.index[mask].tolist()

    if not indices:
        raise RuntimeError("테스트 기간에 실행 가능한 날짜가 없습니다.")

    flow_memory: dict[str, Any] = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    rows = []

    for idx in indices:
        market_data = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=50.0,
        )

        prev_memory_snapshot = dict(flow_memory)

        flow_memory = prepare_filter13_execution_state(
        market_data=market_data,
        panel=panel,
        row_index=idx,
        previous_flow_memory=flow_memory,
        )

        institutional_flow = (
            market_data.get("INSTITUTIONAL_FLOW", {}) or {}
        )

        row = {
            "signal_date": market_data.get("SIGNAL_DATE"),
            "market_regime": market_data.get("MARKET_REGIME"),
            "macro_narrative": market_data.get("MACRO_NARRATIVE"),
            "cross_asset_tape": json.dumps(
                market_data.get("CROSS_ASSET_TAPE", {}),
                ensure_ascii=False,
                default=str,
            ),
            "policy_bias_line": market_data.get("POLICY_BIAS_LINE"),
            "drift_state": market_data.get("DRIFT_STATE"),
            "drift_score": market_data.get("DRIFT_SCORE"),
            "gamma_state": market_data.get("GAMMA_STATE"),
            "gamma_combo": market_data.get("GAMMA_COMBO"),
            "institutional_flow_state": institutional_flow.get("state"),
            "institutional_flow_score": institutional_flow.get("score"),
            "prev_flow_state": market_data.get("PREV_FLOW_STATE"),
            "prev_flow_score": market_data.get("PREV_FLOW_SCORE"),
            "expected_prev_flow_state": prev_memory_snapshot.get(
                "flow_state"
            ),
            "expected_prev_flow_score": prev_memory_snapshot.get(
                "flow_score"
            ),
            "next_flow_state": flow_memory.get("flow_state"),
            "next_flow_score": flow_memory.get("flow_score"),
            "persistence_days": flow_memory.get("persistence_days"),
            "struct_v2_state": market_data.get("STRUCT_V2_STATE"),
        }

        rows.append(row)

    result = pd.DataFrame(rows)

    print(
        result[
            [
                "signal_date",
                "market_regime",
                "macro_narrative",
                "drift_state",
                "drift_score",
                "gamma_state",
                "institutional_flow_state",
                "institutional_flow_score",
                "prev_flow_state",
                "prev_flow_score",
                "next_flow_state",
                "next_flow_score",
                "persistence_days",
                "struct_v2_state",
            ]
        ].to_string(index=False)
    )

    print("\n=== FLOW MEMORY PARITY ===")

    state_pass = (
        result["prev_flow_state"].astype(str)
        == result["expected_prev_flow_state"].astype(str)
    ).all()

    score_pass = (
        pd.to_numeric(result["prev_flow_score"], errors="coerce").fillna(0)
        == pd.to_numeric(
            result["expected_prev_flow_score"],
            errors="coerce",
        ).fillna(0)
    ).all()

    print("PREV_FLOW_STATE:", "PASS" if state_pass else "FAIL")
    print("PREV_FLOW_SCORE:", "PASS" if score_pass else "FAIL")

    required = [
        "market_regime",
        "macro_narrative",
        "policy_bias_line",
        "drift_state",
        "gamma_state",
        "institutional_flow_state",
        "struct_v2_state",
    ]

    print("\n=== STATE PRESENCE ===")

    for col in required:
        passed = result[col].notna().all()
        print(f"{col}: {'PASS' if passed else 'FAIL'}")


if __name__ == "__main__":
    main()
