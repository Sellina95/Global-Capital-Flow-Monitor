from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)
from scripts.backtest.historical_execution_contract import (
    initial_filter15_memory,
    prepare_historical_execution_contract,
    capture_filter15_memory,
)

import filters.strategist_filters as sf


PANEL = "data/backtest/master_panel.csv"

REQUIRED = [
    "FILTER15_PREV_DEADMAN",
    "FILTER15_RECOVERY_ACTIVE",
    "FILTER15_RECOVERY_COMPLETED",
    "FILTER15_RECOVERY_STREAK",
    "FILTER15_PREV_HY_OAS",
    "MOMENTUM_SCORES",
    "POSITIONING_STATE",
    "POSITIONING_SCORE_18",
    "SQUEEZE_RISK",
    "GAMMA_SIGNAL",
    "VOL_STRUCTURE",
]


def main():

    panel = pd.read_csv(
        PANEL,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    eligible = panel.index[
        panel["execution_date"].notna()
        & pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    ].tolist()

    print("FULL-PERIOD CONTRACT VALIDATION")
    print("=" * 70)
    print("ROWS:", len(eligible))

    if eligible:
        print(
            "RANGE:",
            panel.loc[eligible[0], "signal_date"],
            "->",
            panel.loc[eligible[-1], "signal_date"],
        )

    filter15_memory = initial_filter15_memory()

    flow_memory = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    previous_exposure = 50.0

    failures = []
    counts = {key: 0 for key in REQUIRED}

    for n, idx in enumerate(eligible, start=1):

        md = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=previous_exposure,
        )

        with contextlib.redirect_stdout(io.StringIO()):

            flow_memory = prepare_filter13_execution_state(
                market_data=md,
                panel=panel,
                row_index=idx,
                previous_flow_memory=flow_memory,
            )

            prepare_historical_execution_contract(
                market_data=md,
                panel=panel,
                row_index=idx,
                filter15_memory=filter15_memory,
            )

        # ---------------------------------------------
        # Contract presence BEFORE F13/F15/F18 chain
        # ---------------------------------------------

        row_failures = []

        for key in REQUIRED:

            exists = key in md

            # None is legitimate for initial PREV_HY_OAS.
            if key == "FILTER15_PREV_HY_OAS":
                ok = exists
            else:
                ok = exists and md.get(key) is not None

            if ok:
                counts[key] += 1
            else:
                row_failures.append(key)

        if row_failures:

            failures.append({
                "signal_date":
                    panel.loc[idx, "signal_date"],

                "missing":
                    ",".join(row_failures),
            })

        # ---------------------------------------------
        # Execute canonical chain so F15 state produced
        # today becomes t+1 memory.
        # ---------------------------------------------

        with contextlib.redirect_stdout(io.StringIO()):

            sf.narrative_engine_filter(md)

            exposure_report = (
                sf.volatility_controlled_exposure_filter(md)
            )

            sf.sector_allocation_filter(md)

        filter15_memory = capture_filter15_memory(md)

        exposure = md.get("RECOMMENDED_EXPOSURE")

        if exposure is None and isinstance(
            exposure_report,
            dict,
        ):
            exposure = exposure_report.get(
                "recommended_exposure"
            )

        if exposure is not None:
            try:
                previous_exposure = float(exposure)
            except Exception:
                pass

        if n % 500 == 0:
            print(
                f"checked {n}/{len(eligible)}"
            )

    print()
    print("=" * 70)
    print("RESULT")
    print("=" * 70)

    for key in REQUIRED:
        print(
            f"{key:32s} "
            f"{counts[key]}/{len(eligible)}"
        )

    print()
    print("FAILURE ROWS:", len(failures))

    if failures:

        out = pd.DataFrame(failures)

        path = (
            "data/backtest/results/"
            "full_period_repaired_contract_failures.csv"
        )

        out.to_csv(
            path,
            index=False,
        )

        print("FAIL")
        print(out.head(30).to_string(index=False))
        print("OUTPUT:", path)

        raise SystemExit(1)

    print()
    print(
        f"PASS — {len(eligible)}/{len(eligible)} historical rows"
    )
    print(
        "11/11 repaired contracts supplied across full period."
    )


if __name__ == "__main__":
    main()
