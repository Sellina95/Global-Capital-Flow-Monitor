from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import filters.strategist_filters as sf

from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)
from scripts.backtest.institutional_backtest import (
    disable_live_side_effects,
    neutralize_all_side_effects,
)


DATA_DIR = ROOT / "data" / "backtest"
PANEL_PATH = DATA_DIR / "master_panel.csv"

# 우선 현재 canonical run_backtest와 같은 구간에서 검사
START_DATE = pd.Timestamp("2026-06-08")
END_DATE = pd.Timestamp("2026-06-19")


def _nested(data: dict[str, Any], key: str, subkey: str):
    value = data.get(key)

    if isinstance(value, dict):
        return value.get(subkey)

    return None


def _is_missing(value: Any) -> bool:
    if value is None:
        return True

    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def snapshot_filter15_contract(
    market_data: dict[str, Any],
) -> dict[str, Any]:

    values = {
        "RISK_BUDGET":
            market_data.get("RISK_BUDGET"),

        "VIX.today":
            _nested(market_data, "VIX", "today"),

        "VIX.pct_change":
            _nested(market_data, "VIX", "pct_change"),

        "SP500_POS_Z":
            market_data.get("SP500_POS_Z"),

        "POS_SLOPE":
            market_data.get("POS_SLOPE"),

        "DEALER_GAMMA_BIAS":
            market_data.get("DEALER_GAMMA_BIAS"),

        "CTA_MOMENTUM_SCORE":
            market_data.get("CTA_MOMENTUM_SCORE"),

        "HY_OAS.today":
            _nested(market_data, "HY_OAS", "today"),

        "HY_OAS.pct_change":
            _nested(market_data, "HY_OAS", "pct_change"),

        "INSTITUTIONAL_FLOW.score":
            _nested(
                market_data,
                "INSTITUTIONAL_FLOW",
                "score",
            ),

        "MACRO_NARRATIVE":
            market_data.get("MACRO_NARRATIVE"),

        "CROSS_ASSET_TAPE.VIX_Z":
            _nested(
                market_data,
                "CROSS_ASSET_TAPE",
                "VIX_Z",
            ),

        "LEADERSHIP_BREADTH_SCORE":
            market_data.get("LEADERSHIP_BREADTH_SCORE"),

        "HY_OAS_STATUS":
            market_data.get("HY_OAS_STATUS"),
    }

    result: dict[str, Any] = {}

    for key, value in values.items():
        result[key] = value
        result[f"{key}__STATUS"] = (
            "MISSING"
            if _is_missing(value)
            else "PRESENT"
        )

    return result


def main() -> None:

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    mask = (
        panel["signal_date"].ge(START_DATE)
        & panel["signal_date"].le(END_DATE)
        & panel["execution_date"].notna()
        & pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    )

    indices = panel.index[mask].tolist()

    if not indices:
        raise RuntimeError(
            "Filter15 Input Contract audit 대상 날짜가 없습니다."
        )

    previous_exposure = 50.0

    flow_memory: dict[str, Any] = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    audit_rows: list[dict[str, Any]] = []

    for idx in indices:

        market_data = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=previous_exposure,
        )

        # Filter13 parity에서 확정한 canonical
        # Production pre-13 execution chain
        with contextlib.redirect_stdout(io.StringIO()):
            flow_memory = prepare_filter13_execution_state(
                market_data=market_data,
                panel=panel,
                row_index=idx,
                previous_flow_memory=flow_memory,
            )

        # Filter13 실행
        #
        # 중요:
        # 이 함수가 끝난 직후 market_data가
        # Production Filter15가 실제로 받는 boundary state다.
        disable_live_side_effects(previous_exposure)
        neutralize_all_side_effects(previous_exposure)

        with contextlib.redirect_stdout(io.StringIO()):
            sf.narrative_engine_filter(market_data)

        snapshot = snapshot_filter15_contract(
            market_data
        )

        audit_rows.append({
            "signal_date":
                market_data.get("SIGNAL_DATE"),

            "execution_date":
                market_data.get("EXECUTION_DATE"),

            **snapshot,
        })

        # 이 audit에서는 Filter15를 실행하지 않는다.
        #
        # 목적은 Filter15 직전 Input Contract 확인이므로
        # previous_exposure 역시 Filter15 결과로 업데이트하지 않는다.

    audit = pd.DataFrame(audit_rows)

    print("\n")
    print("=" * 78)
    print("FILTER15 INPUT CONTRACT AUDIT")
    print("Boundary: AFTER Filter13 / BEFORE Filter15")
    print("=" * 78)

    contract_names = [
        "RISK_BUDGET",
        "VIX.today",
        "VIX.pct_change",
        "SP500_POS_Z",
        "POS_SLOPE",
        "DEALER_GAMMA_BIAS",
        "CTA_MOMENTUM_SCORE",
        "HY_OAS.today",
        "HY_OAS.pct_change",
        "INSTITUTIONAL_FLOW.score",
        "MACRO_NARRATIVE",
        "CROSS_ASSET_TAPE.VIX_Z",
        "LEADERSHIP_BREADTH_SCORE",
        "HY_OAS_STATUS",
    ]

    summary_rows = []

    for name in contract_names:

        status_col = f"{name}__STATUS"

        present = int(
            (audit[status_col] == "PRESENT").sum()
        )

        missing = int(
            (audit[status_col] == "MISSING").sum()
        )

        summary_rows.append({
            "input": name,
            "present_days": present,
            "missing_days": missing,
            "total_days": len(audit),
            "availability": (
                "EXPECTED_FALLBACK"
                if name == "HY_OAS_STATUS" and missing == len(audit)
                else "PASS"
                if missing == 0
                else "FAIL"
            ),
        })

    summary = pd.DataFrame(summary_rows)

    print(
        summary.to_string(
            index=False
        )
    )

    print("\n")
    print("=" * 78)
    print("SAMPLE — LAST AUDIT DATE")
    print("=" * 78)

    last = audit.iloc[-1]

    print(
        f"signal_date    : {last['signal_date']}"
    )
    print(
        f"execution_date : {last['execution_date']}"
    )
    print()

    for name in contract_names:
        print(
            f"{name:<30} "
            f"{str(last[name]):<30} "
            f"{last[f'{name}__STATUS']}"
        )

    failed = summary[
        summary["availability"] == "FAIL"
    ]

    print("\n")
    print("=" * 78)

    if failed.empty:
        print(
            "RESULT: INPUT AVAILABILITY PASS"
        )
        print(
            "All 14 Production Filter15 inputs "
            "exist at the Filter13→15 boundary."
        )
    else:
        print(
            "RESULT: INPUT AVAILABILITY FAIL"
        )
        print(
            "Missing Filter15 contract fields:"
        )

        for name in failed["input"].tolist():
            print(f"  - {name}")

    print("=" * 78)

    print(
        "\nNOTE: PRESENT does NOT mean parity."
    )
    print(
        "Next gate = PIT provenance / transform / fallback parity."
    )


if __name__ == "__main__":
    main()
