from __future__ import annotations

from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import filters.strategist_filters as sf
import scripts.backtest.run_backtest as rb


DATA = ROOT / "data" / "backtest"
RESULTS = DATA / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

CANONICAL_PANEL = DATA / "master_panel.csv"

CONTROL_PANEL = (
    DATA
    / "pit_safe"
    / "master_panel_geo_control_old_data.csv"
)

OUT_PATH = (
    RESULTS
    / "daily_positions_geo_control.csv"
)


# ============================================================
# 1. Build CONTROL panel
#
# OLD DATA 그대로 사용.
# 단지 GEO가 Production contract 이름을 읽을 수 있도록
# 기존 sovereign spread 이름만 연결한다.
#
# KR_US_SPREAD -> KR10Y_SPREAD
# JP_US_SPREAD -> JP10Y_SPREAD
# DE_US_SPREAD -> DE10Y_SPREAD
# IL_US_SPREAD -> IL10Y_SPREAD
#
# 데이터 값/날짜는 전혀 수정하지 않는다.
# ============================================================

panel = pd.read_csv(CANONICAL_PANEL)

mapping = {
    "sovereign_spreads__KR_US_SPREAD": "KR10Y_SPREAD",
    "sovereign_spreads__JP_US_SPREAD": "JP10Y_SPREAD",
    "sovereign_spreads__DE_US_SPREAD": "DE10Y_SPREAD",
    "sovereign_spreads__IL_US_SPREAD": "IL10Y_SPREAD",
}

for source, target in mapping.items():

    if source not in panel.columns:
        raise RuntimeError(
            f"Required old-data sovereign column missing: {source}"
        )

    panel[target] = pd.to_numeric(
        panel[source],
        errors="coerce",
    )

CONTROL_PANEL.parent.mkdir(
    parents=True,
    exist_ok=True,
)

panel.to_csv(
    CONTROL_PANEL,
    index=False,
    encoding="utf-8-sig",
)


# ============================================================
# 2. Production-equivalent GEO execution order
#
# attach GEO
# -> F13
# -> GEO overlay
# -> F15
# -> F18
# ============================================================

original_build_market_data = rb.build_market_data
original_narrative = sf.narrative_engine_filter


def build_market_data_with_geo(
    panel,
    row_index,
    previous_exposure,
):

    market_data = original_build_market_data(
        panel=panel,
        row_index=row_index,
        previous_exposure=previous_exposure,
    )

    market_data = (
        sf.attach_geopolitical_ew_layer(
            market_data,
            panel,
            row_index,
        )
        or market_data
    )

    return market_data


def narrative_with_geo_overlay(market_data):

    report = original_narrative(
        market_data
    )

    sf.apply_geo_overlay_to_final_state(
        market_data
    )

    return report


def main():

    print("=" * 78)
    print("GEO CONTROL BACKTEST — OLD DATA + GEO")
    print("=" * 78)

    print("Control panel:", CONTROL_PANEL)
    print("Canonical master_panel modified: NO")
    print("Production modified: NO")
    print()

    rb.PANEL_PATH = CONTROL_PANEL
    rb.OUT_PATH = OUT_PATH

    rb.build_market_data = build_market_data_with_geo
    sf.narrative_engine_filter = narrative_with_geo_overlay

    try:
        rb.main()

    finally:
        rb.build_market_data = original_build_market_data
        sf.narrative_engine_filter = original_narrative

    print()
    print("=" * 78)
    print("GEO CONTROL REPLAY COMPLETE")
    print("=" * 78)

    print("Saved:", OUT_PATH)


if __name__ == "__main__":
    main()
