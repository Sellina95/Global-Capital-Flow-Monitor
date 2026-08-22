from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import filters.strategist_filters as sf
import scripts.backtest.run_backtest as rb

PIT_PANEL = (
    ROOT
    / "data"
    / "backtest"
    / "pit_safe"
    / "master_panel_pit_safe_with_sovereign.csv"
)

OUT_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "daily_positions_pit_safe_geo.csv"
)


if not PIT_PANEL.exists():
    raise FileNotFoundError(PIT_PANEL)


# ============================================================
# Preserve canonical functions
# ============================================================

original_build_market_data = rb.build_market_data
original_narrative = sf.narrative_engine_filter


# ============================================================
# Production-equivalent GEO attach
#
# Production:
# attach_geopolitical_ew_layer(...)
# -> narrative_engine_filter(...)
# -> apply_geo_overlay_to_final_state(...)
# -> F15
# -> F18
# ============================================================

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
    report = original_narrative(market_data)

    sf.apply_geo_overlay_to_final_state(
        market_data
    )

    return report


def main():
    print("=" * 78)
    print("PIT-SAFE GEO PRODUCTION-EQUIVALENT BACKTEST")
    print("=" * 78)
    print("Panel:", PIT_PANEL)
    print("Production modified: NO")
    print("Canonical run_backtest.py modified: NO")
    print()

    # Point canonical replay at PIT-safe panel/output only in memory.
    rb.PANEL_PATH = PIT_PANEL
    rb.OUT_PATH = OUT_PATH

    rb.build_market_data = build_market_data_with_geo
    sf.narrative_engine_filter = narrative_with_geo_overlay

    try:
        rb.main()
    finally:
        # Restore imported module state.
        rb.build_market_data = original_build_market_data
        sf.narrative_engine_filter = original_narrative

    print()
    print("=" * 78)
    print("PIT-SAFE GEO REPLAY COMPLETE")
    print("=" * 78)
    print("Saved:", OUT_PATH)


if __name__ == "__main__":
    main()
