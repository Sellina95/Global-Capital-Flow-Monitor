from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Any

import pandas as pd

# 프로젝트 루트 import 보장
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from scripts.backtest.market_data_builder import build_market_data
import filters.strategist_filters as sf


DATA_DIR = ROOT / "data" / "backtest"
PANEL_PATH = DATA_DIR / "master_panel.csv"


def disable_live_side_effects(previous_exposure: float = 50.0) -> None:
    """
    백테스트 smoke test 중 운영 포트폴리오·트레이드 로그를
    읽거나 덮어쓰지 못하도록 차단한다.
    """

    # strategist_filters 전역에 이미 import된 함수 차단
    if hasattr(sf, "save_paper_portfolio"):
        sf.save_paper_portfolio = lambda *args, **kwargs: None
    if hasattr(sf, "save_trade_log"):
        sf.save_trade_log = lambda *args, **kwargs: None
    if hasattr(sf, "load_previous_weights"):
        sf.load_previous_weights = lambda *args, **kwargs: {}
    if hasattr(sf, "load_previous_exposure"):
        sf.load_previous_exposure = (
            lambda *args, **kwargs: previous_exposure
        )

    # 함수 내부 local import까지 차단
    try:
        import portfolio.save_portfolio as portfolio_store

        if hasattr(portfolio_store, "save_paper_portfolio"):
            portfolio_store.save_paper_portfolio = (
                lambda *args, **kwargs: None
            )
        if hasattr(portfolio_store, "load_previous_weights"):
            portfolio_store.load_previous_weights = (
                lambda *args, **kwargs: {}
            )
        if hasattr(portfolio_store, "load_previous_exposure"):
            portfolio_store.load_previous_exposure = (
                lambda *args, **kwargs: previous_exposure
            )
    except Exception:
        pass

    try:
        import scripts.fetch_positioning_data as positioning_store

        if hasattr(positioning_store, "save_trade_log"):
            positioning_store.save_trade_log = (
                lambda *args, **kwargs: None
            )
    except Exception:
        pass



def neutralize_all_side_effects(previous_exposure: float = 50.0) -> None:
    """
    현재 로드된 모든 관련 모듈에서 운영 저장/조회 함수를 차단한다.
    local import와 모듈 alias 양쪽을 모두 방어한다.
    """
    import sys

    def no_write(*args, **kwargs):
        return None

    def no_weights(*args, **kwargs):
        return {}

    def prior_exposure(*args, **kwargs):
        return previous_exposure

    replacements = {
        "save_trade_log": no_write,
        "save_paper_portfolio": no_write,
        "save_portfolio": no_write,
        "load_previous_weights": no_weights,
        "load_previous_exposure": prior_exposure,
    }

    # strategist_filters 전역 포함, 이미 로드된 모든 모듈 alias 패치
    for module in list(sys.modules.values()):
        if module is None:
            continue

        for name, replacement in replacements.items():
            if hasattr(module, name):
                try:
                    setattr(module, name, replacement)
                except Exception:
                    pass

def choose_smoke_test_index(panel: pd.DataFrame) -> int:
    """
    252거래일의 warm-up 이후 첫 번째 2008년 말 관측치를 선택한다.
    """
    signal_dates = pd.to_datetime(panel["signal_date"], errors="coerce")

    candidates = panel.index[
        (signal_dates >= pd.Timestamp("2008-12-01"))
        & (signal_dates <= pd.Timestamp("2008-12-31"))
        & panel["execution_date"].notna()
    ].tolist()

    if not candidates:
        raise RuntimeError("2008년 12월 smoke-test 날짜를 찾지 못했습니다.")

    return int(candidates[0])


def main() -> None:
    if not PANEL_PATH.exists():
        raise FileNotFoundError(PANEL_PATH)

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=["date", "signal_date", "execution_date"],
    )

    idx = choose_smoke_test_index(panel)
    previous_exposure = 50.0

    market_data = build_market_data(
        panel=panel,
        row_index=idx,
        previous_exposure=previous_exposure,
    )

    disable_live_side_effects(previous_exposure)
    neutralize_all_side_effects(previous_exposure)

    captured: dict[str, Any] = {}
    original_builder = sf.build_tactical_allocation

    def capture_allocation(*args, **kwargs):
        result = original_builder(*args, **kwargs)
        captured["allocation"] = result
        return result

    # sector_allocation_filter 내부의 실제 18.5 결과 가로채기
    sf.build_tactical_allocation = capture_allocation

    print("=" * 72)
    print("INSTITUTIONAL BACKTEST — 2008 ONE-DAY SMOKE TEST")
    print("=" * 72)
    print("Signal date   :", market_data.get("SIGNAL_DATE"))
    print("Execution date:", market_data.get("EXECUTION_DATE"))

    try:
        print("\n[13] Risk Budget")
        sf.narrative_engine_filter(market_data)
        risk_budget = market_data.get("RISK_BUDGET")
        print("RISK_BUDGET =", risk_budget)

        print("\n[15] Volatility-Controlled Exposure")
        sf.volatility_controlled_exposure_filter(market_data)
        exposure = market_data.get("RECOMMENDED_EXPOSURE")
        print("RECOMMENDED_EXPOSURE =", exposure)

        print("\n[18] Sector Allocation")
        sf.sector_allocation_filter(market_data)

        allocation = captured.get("allocation")
        if allocation is None:
            raise RuntimeError(
                "18번은 실행됐지만 build_tactical_allocation 결과를 "
                "가로채지 못했습니다."
            )

        weights = allocation.get("weights", {})
        cash_weight = allocation.get("cash_weight")
        allocated_equity = allocation.get(
            "allocated_equity",
            round(sum(weights.values()), 1),
        )

        print("\n" + "=" * 72)
        print("SMOKE TEST RESULT")
        print("=" * 72)
        print("Risk Budget (13) :", risk_budget)
        print("Exposure (15)    :", exposure)
        print("Allocated (18)   :", allocated_equity)
        print("Cash (18)        :", cash_weight)
        print("Macro profile    :", allocation.get("macro_profile"))
        print("\nSector weights:")
        print(json.dumps(weights, indent=2, ensure_ascii=False))

        if abs(float(allocated_equity) + float(cash_weight) - 100.0) > 0.2:
            raise RuntimeError(
                "Allocation check failed: equity + cash != 100"
            )

        print("\nAllocation check : PASS")
        print("Operating files  : NOT MODIFIED")
        print("Smoke test       : PASS")

    except Exception:
        print("\n" + "=" * 72)
        print("SMOKE TEST FAILED")
        print("=" * 72)
        traceback.print_exc()
        raise

    finally:
        sf.build_tactical_allocation = original_builder


if __name__ == "__main__":
    main()
