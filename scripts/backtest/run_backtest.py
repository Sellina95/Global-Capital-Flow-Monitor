from __future__ import annotations

import contextlib
import io
import json
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
from scripts.backtest.institutional_backtest import (
    disable_live_side_effects,
    neutralize_all_side_effects,
)

DATA_DIR = ROOT / "data" / "backtest"
PANEL_PATH = DATA_DIR / "master_panel.csv"
RESULT_DIR = DATA_DIR / "results"
OUT_PATH = RESULT_DIR / "daily_positions.csv"

START_DATE = pd.Timestamp("2008-12-01")
END_DATE = None


def run_engine(
    market_data: dict[str, Any],
    previous_exposure: float,
) -> dict[str, Any]:
    disable_live_side_effects(previous_exposure)
    neutralize_all_side_effects(previous_exposure)

    captured: dict[str, Any] = {}
    original_builder = sf.build_tactical_allocation

    def capture_allocation(*args, **kwargs):
        result = original_builder(*args, **kwargs)
        captured["allocation"] = result
        return result

    sf.build_tactical_allocation = capture_allocation

    try:
        # 수천 줄의 DEBUG 출력은 루프 중 숨긴다.
        with contextlib.redirect_stdout(io.StringIO()):
            sf.narrative_engine_filter(market_data)
            exposure_report = sf.volatility_controlled_exposure_filter(market_data)
            sf.sector_allocation_filter(market_data)

        allocation = captured.get("allocation")
        if allocation is None:
            raise RuntimeError("18번 allocation 결과를 포착하지 못했습니다.")

        deadman_reason = ""
        brake_drivers = ""

        for line in str(exposure_report).splitlines():
            clean = line.replace("**", "").strip()

            if clean.startswith("- Reason:"):
                deadman_reason = clean.split(":", 1)[1].strip()

            elif clean.startswith("- Brake Drivers:"):
                brake_drivers = clean.split(":", 1)[1].strip()

        return {
            "allocation": allocation,
            "deadman_reason": deadman_reason,
            "brake_drivers": brake_drivers,
        }

    finally:
        sf.build_tactical_allocation = original_builder


def main() -> None:
    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=["date", "signal_date", "execution_date"],
    )

    mask = (
        panel["signal_date"].ge(START_DATE)
        & panel["execution_date"].notna()
        & pd.to_numeric(panel["SPY"], errors="coerce").notna()
    )

    if END_DATE is not None:
        mask &= panel["signal_date"].le(END_DATE)
    indices = panel.index[mask].tolist()

    if not indices:
        raise RuntimeError("2008년 12월 실행 대상 날짜가 없습니다.")

    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    previous_exposure = 50.0

    for count, idx in enumerate(indices, start=1):
        market_data = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=previous_exposure,
        )

        try:
            engine_result = run_engine(
                market_data=market_data,
                previous_exposure=previous_exposure,
            )

            allocation = engine_result["allocation"]
            weights = allocation.get("weights", {}) or {}
            risk_budget = market_data.get("RISK_BUDGET")
            exposure = market_data.get("RECOMMENDED_EXPOSURE")
            allocated_equity = allocation.get(
                "allocated_equity",
                round(sum(weights.values()), 1),
            )
            cash_weight = allocation.get(
                "cash_weight",
                round(100.0 - allocated_equity, 1),
            )

            row = {
                "signal_date": market_data.get("SIGNAL_DATE"),
                "execution_date": market_data.get("EXECUTION_DATE"),
                "risk_budget_13": risk_budget,
                "exposure_15": exposure,
                "allocated_equity_18": allocated_equity,
                "cash_weight": cash_weight,
                "macro_profile": allocation.get("macro_profile"),
                "sew_status": market_data.get("SEW_STATUS"),
                "deadman_reason": engine_result.get("deadman_reason", ""),
                "brake_drivers": engine_result.get("brake_drivers", ""),
                "macro_narrative": market_data.get("MACRO_NARRATIVE", ""),
                "vix_today": (
                    market_data.get("VIX", {}).get("today")
                    if isinstance(market_data.get("VIX"), dict)
                    else market_data.get("VIX")
                ),
                "hy_oas_today": (
                    market_data.get("HY_OAS", {}).get("today")
                    if isinstance(market_data.get("HY_OAS"), dict)
                    else market_data.get("HY_OAS")
                ),
                "cta_momentum_score": market_data.get("CTA_MOMENTUM_SCORE"),
                "cta_fetch_ok": market_data.get("CTA_FETCH_OK"),
                "weights_json": json.dumps(
                    weights,
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                "status": "OK",
                "error": "",
            }

            # 분석하기 쉽도록 섹터 비중을 개별 컬럼으로도 저장
            for sector, weight in weights.items():
                row[f"weight__{sector}"] = weight

            rows.append(row)

            if exposure is not None:
                previous_exposure = float(exposure)

        except Exception as exc:
            rows.append({
                "signal_date": market_data.get("SIGNAL_DATE"),
                "execution_date": market_data.get("EXECUTION_DATE"),
                "risk_budget_13": market_data.get("RISK_BUDGET"),
                "exposure_15": market_data.get("RECOMMENDED_EXPOSURE"),
                "allocated_equity_18": None,
                "cash_weight": None,
                "macro_profile": None,
                "sew_status": market_data.get("SEW_STATUS"),
                "weights_json": "{}",
                "status": "ERROR",
                "error": f"{type(exc).__name__}: {exc}",
            })

        print(
            f"\rProcessed {count}/{len(indices)}",
            end="",
            flush=True,
        )

    print()

    result = pd.DataFrame(rows).sort_values("signal_date")
    result.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    ok_count = int((result["status"] == "OK").sum())
    error_count = int((result["status"] == "ERROR").sum())

    print(f"Saved: {OUT_PATH}")
    print(f"Rows: {len(result)}")
    print(f"OK: {ok_count}")
    print(f"ERROR: {error_count}")

    print("\nExposure / Cash preview:")
    print(
        result[
            [
                "signal_date",
                "risk_budget_13",
                "exposure_15",
                "allocated_equity_18",
                "cash_weight",
                "status",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
