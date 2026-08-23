from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# Repository import path
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.run_backtest import run_engine
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)


ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data" / "backtest"
PIT = DATA / "pit_safe"
RESULTS = DATA / "results"

# CONTROL:
# Exact canonical panel used by the frozen F13/F15/F18 replay.
BASE_PANEL_PATH = (
    DATA / "master_panel.csv"
)

# TREATMENT:
# Exact copy of canonical master_panel with ONLY the confirmed
# FRED-vintage intervention columns replaced.
CF_PANEL_PATH = (
    PIT / "master_panel_fred_initial_release_controlled.csv"
)

# Frozen canonical replay produced by the already-passed
# Macro V4 causal-propagation baseline gate.
BASELINE_REPLAY_PATH = (
    RESULTS
    / "final_13_15_18_parity_closeout"
    / "final_13_15_18_parity_daily.csv"
)

# Fallback search locations only if repository layout differs.
BASELINE_REPLAY_CANDIDATES = [
    BASELINE_REPLAY_PATH,
    RESULTS / "canonical_baseline_replay.csv",
]

OUT_DAILY = (
    RESULTS
    / "fred_vintage_counterfactual_propagation_daily.csv"
)

OUT_SUMMARY = (
    RESULTS
    / "fred_vintage_counterfactual_propagation_summary.csv"
)

OUT_TXT = (
    RESULTS
    / "fred_vintage_counterfactual_propagation_summary.txt"
)

RESULTS.mkdir(parents=True, exist_ok=True)


# ============================================================
# Helpers
# ============================================================

def as_float(x: Any) -> float:
    try:
        if x is None or pd.isna(x):
            return np.nan
        return float(x)
    except Exception:
        return np.nan


def numeric_changed(
    a: pd.Series,
    b: pd.Series,
    tol: float = 1e-9,
) -> pd.Series:

    a = pd.to_numeric(a, errors="coerce")
    b = pd.to_numeric(b, errors="coerce")

    both_nan = a.isna() & b.isna()

    same = np.isclose(
        a.fillna(0.0),
        b.fillna(0.0),
        atol=tol,
        rtol=0.0,
    )

    same = same & (a.isna() == b.isna())

    return ~(both_nan | same)


def normalize_panel(path: Path) -> pd.DataFrame:

    if not path.exists():
        raise FileNotFoundError(path)

    panel = pd.read_csv(path)

    if "signal_date" not in panel.columns:
        if "date" not in panel.columns:
            raise RuntimeError(
                f"{path.name}: neither signal_date nor date exists."
            )

        panel["signal_date"] = panel["date"]

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"],
        errors="coerce",
    )

    if "execution_date" in panel.columns:
        panel["execution_date"] = pd.to_datetime(
            panel["execution_date"],
            errors="coerce",
        )

    # IMPORTANT:
    # Do not reset index.
    # Canonical replay depends on original panel row positions.
    return panel


def find_frozen_replay() -> Path:

    for path in BASELINE_REPLAY_CANDIDATES:
        if path.exists():
            return path

    matches = list(
        DATA.rglob("canonical_baseline_replay.csv")
    )

    if len(matches) == 1:
        return matches[0]

    if not matches:
        raise FileNotFoundError(
            "canonical_baseline_replay.csv not found."
        )

    raise RuntimeError(
        "Multiple canonical_baseline_replay.csv files found:\n"
        + "\n".join(str(x) for x in matches)
    )


# ============================================================
# Canonical replay
#
# This intentionally mirrors the already-validated Gate-1
# replay structure in audit_macro_v4_causal_propagation.py.
#
# NO strategic intervention.
# NO Production logic modification.
# ============================================================

def replay_panel(
    panel: pd.DataFrame,
    canonical_dates: set[pd.Timestamp],
    label: str,
) -> pd.DataFrame:

    required = [
        "signal_date",
        "execution_date",
        "SPY",
    ]

    missing = [
        c for c in required
        if c not in panel.columns
    ]

    if missing:
        raise RuntimeError(
            f"{label}: missing required columns: {missing}"
        )

    indices = panel.index[
        panel["signal_date"].isin(canonical_dates)
        & panel["execution_date"].notna()
        & pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    ].tolist()

    if not indices:
        raise RuntimeError(
            f"{label}: no canonical execution dates."
        )

    print()
    print("=" * 80)
    print(f"REPLAY — {label}")
    print("=" * 80)
    print("Rows:", len(indices))

    previous_exposure = 50.0

    flow_memory: dict[str, Any] = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    rows: list[dict[str, Any]] = []

    for count, idx in enumerate(indices, start=1):

        market_data = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=previous_exposure,
        )

        with contextlib.redirect_stdout(io.StringIO()):

            flow_memory = prepare_filter13_execution_state(
                market_data=market_data,
                panel=panel,
                row_index=idx,
                previous_flow_memory=flow_memory,
            )

            engine_result = run_engine(
                market_data=market_data,
                previous_exposure=previous_exposure,
            )

        allocation = engine_result["allocation"]

        weights = allocation.get(
            "weights",
            {},
        ) or {}

        risk_budget = as_float(
            market_data.get("RISK_BUDGET")
        )

        exposure = as_float(
            market_data.get("RECOMMENDED_EXPOSURE")
        )

        allocated_equity = allocation.get(
            "allocated_equity"
        )

        if allocated_equity is None:
            allocated_equity = round(
                sum(
                    float(v)
                    for v in weights.values()
                ),
                1,
            )

        allocated_equity = as_float(
            allocated_equity
        )

        cash_weight = allocation.get(
            "cash_weight"
        )

        if cash_weight is None:
            cash_weight = round(
                100.0 - allocated_equity,
                1,
            )

        cash_weight = as_float(
            cash_weight
        )

        rows.append(
            {
                "signal_date": market_data.get(
                    "SIGNAL_DATE"
                ),
                "execution_date": market_data.get(
                    "EXECUTION_DATE"
                ),

                "macro_narrative": market_data.get(
                    "MACRO_NARRATIVE"
                ),

                "market_regime": market_data.get(
                    "MARKET_REGIME"
                ),

                "risk_budget_13": risk_budget,
                "exposure_15": exposure,
                "allocated_equity_18": allocated_equity,
                "cash_weight": cash_weight,

                "sector_final_score": json.dumps(
                    market_data.get(
                        "SECTOR_FINAL_SCORE",
                        {},
                    ),
                    sort_keys=True,
                    default=str,
                ),

                "weights": json.dumps(
                    weights,
                    sort_keys=True,
                    default=str,
                ),

                "rank_raw": str(
                    market_data.get(
                        "FILTER18_RAW_RANK",
                        "",
                    )
                ),

                "rank_accepted": str(
                    market_data.get(
                        "FILTER18_ACCEPTED_RANK",
                        "",
                    )
                ),

                "rank_action": str(
                    market_data.get(
                        "FILTER18_RANK_ACTION",
                        "",
                    )
                ),
            }
        )

        # Preserve the same recursive exposure chain.
        if not np.isnan(exposure):
            previous_exposure = exposure

        if count % 500 == 0:
            print(
                f"  completed {count}/{len(indices)}"
            )

    out = pd.DataFrame(rows)

    out["signal_date"] = pd.to_datetime(
        out["signal_date"],
        errors="coerce",
    )

    print("Completed:", len(out))

    return out


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 80)
    print(
        "GATE #3 — FRED VINTAGE COUNTERFACTUAL "
        "CAUSAL PROPAGATION"
    )
    print("=" * 80)
    print()
    print(
        "Question: If historically available FRED vintages "
        "had been used, would F13/F15/F18 decisions change?"
    )
    print()
    print(
        "AUDIT ONLY — decision logic is identical in both replays."
    )

    baseline_panel = normalize_panel(
        BASE_PANEL_PATH
    )

    cf_panel = normalize_panel(
        CF_PANEL_PATH
    )

    if len(baseline_panel) != len(cf_panel):
        raise RuntimeError(
            "Baseline and counterfactual panel row counts differ: "
            f"{len(baseline_panel)} vs {len(cf_panel)}"
        )

    # --------------------------------------------------------
    # Frozen canonical date universe
    # --------------------------------------------------------

    frozen_replay_path = find_frozen_replay()

    frozen = pd.read_csv(
        frozen_replay_path
    )

    if "signal_date" not in frozen.columns:
        raise RuntimeError(
            "Frozen canonical replay has no signal_date."
        )

    frozen["signal_date"] = pd.to_datetime(
        frozen["signal_date"],
        errors="coerce",
    )

    canonical_dates = set(
        frozen["signal_date"].dropna()
    )

    print()
    print("Frozen replay:", frozen_replay_path)
    print("Frozen canonical dates:", len(canonical_dates))

    # --------------------------------------------------------
    # Replay BOTH universes independently.
    #
    # Critical:
    # baseline recursion cannot leak into counterfactual.
    # --------------------------------------------------------

    baseline = replay_panel(
        baseline_panel,
        canonical_dates,
        "CURRENT / REVISED INPUT",
    )

    counterfactual = replay_panel(
        cf_panel,
        canonical_dates,
        "INITIAL-RELEASE PIT INPUT",
    )

    # Diagnostic artifacts must be preserved even when
    # baseline identity fails. This allows root-cause tracing
    # without interpreting the counterfactual.
    baseline_debug_path = (
        RESULTS / "fred_vintage_current_replay_debug.csv"
    )

    counterfactual_debug_path = (
        RESULTS / "fred_vintage_pit_replay_debug.csv"
    )

    baseline.to_csv(
        baseline_debug_path,
        index=False,
    )

    counterfactual.to_csv(
        counterfactual_debug_path,
        index=False,
    )

    print()
    print("Diagnostic replay saved:")
    print(baseline_debug_path)
    print(counterfactual_debug_path)

    # --------------------------------------------------------
    # CONTROL CONTRACT
    #
    # IMPORTANT:
    # The historical frozen parity artifact was generated under
    # the pre-45ae8ee2 market_data_builder semantics, where a
    # namespaced series could overwrite an already-built CORE_SERIES.
    #
    # Therefore it is NOT a valid identity anchor for this FRED
    # vintage experiment.
    #
    # Experimental design:
    #
    # CONTROL   = current canonical code + current master_panel
    # TREATMENT = identical current canonical code + identical panel
    #             except the five controlled FRED vintage fields
    #
    # Structural identity of all non-intervention columns must be
    # verified separately before interpreting this audit.
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("GATE 1 — CURRENT CANONICAL CONTROL")
    print("=" * 80)
    print("Control rows:", len(baseline))
    print("Treatment rows:", len(counterfactual))
    print(
        "Old frozen parity artifact: NOT USED AS IDENTITY ANCHOR "
        "(pre-fix builder semantics)"
    )
    print("CURRENT CANONICAL CONTROL: READY")

    # --------------------------------------------------------
    # Compare baseline vs initial-release counterfactual
    # --------------------------------------------------------

    comparison = baseline.merge(
        counterfactual,
        on="signal_date",
        how="inner",
        suffixes=("_baseline", "_pit"),
    )

    if comparison.empty:
        raise RuntimeError(
            "No overlapping replay rows."
        )

    numeric_fields = [
        "risk_budget_13",
        "exposure_15",
        "allocated_equity_18",
        "cash_weight",
    ]

    summary_rows = []

    for field in numeric_fields:

        a = pd.to_numeric(
            comparison[f"{field}_baseline"],
            errors="coerce",
        )

        b = pd.to_numeric(
            comparison[f"{field}_pit"],
            errors="coerce",
        )

        changed = numeric_changed(a, b)

        diff = b - a

        comparison[f"{field}_changed"] = changed
        comparison[f"{field}_delta"] = diff

        changed_diff = diff[changed].dropna()

        summary_rows.append(
            {
                "field": field,
                "rows": len(comparison),
                "changed_days": int(changed.sum()),
                "changed_pct": (
                    float(changed.mean() * 100.0)
                ),
                "mean_delta_changed": (
                    float(changed_diff.mean())
                    if len(changed_diff)
                    else 0.0
                ),
                "median_abs_delta_changed": (
                    float(changed_diff.abs().median())
                    if len(changed_diff)
                    else 0.0
                ),
                "max_abs_delta": (
                    float(diff.abs().max())
                    if diff.notna().any()
                    else 0.0
                ),
            }
        )

    # --------------------------------------------------------
    # State / allocation changes
    # --------------------------------------------------------

    categorical_fields = [
        "macro_narrative",
        "market_regime",
        "sector_final_score",
        "weights",
        "rank_raw",
        "rank_accepted",
        "rank_action",
    ]

    categorical_summary = {}

    for field in categorical_fields:

        a = (
            comparison[f"{field}_baseline"]
            .fillna("<NA>")
            .astype(str)
        )

        b = (
            comparison[f"{field}_pit"]
            .fillna("<NA>")
            .astype(str)
        )

        changed = a.ne(b)

        comparison[f"{field}_changed"] = changed

        categorical_summary[field] = int(
            changed.sum()
        )

    summary = pd.DataFrame(
        summary_rows
    )

    # --------------------------------------------------------
    # Overall causal footprint
    # --------------------------------------------------------

    decision_change_cols = [
        f"{x}_changed"
        for x in numeric_fields
    ]

    comparison["any_capital_chain_change"] = (
        comparison[
            decision_change_cols
        ].any(axis=1)
    )

    any_chain = int(
        comparison[
            "any_capital_chain_change"
        ].sum()
    )

    total = len(comparison)

    any_chain_pct = (
        100.0 * any_chain / total
        if total
        else 0.0
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    comparison.to_csv(
        OUT_DAILY,
        index=False,
    )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
    )

    lines = [
        "GATE #3 — FRED VINTAGE COUNTERFACTUAL CAUSAL PROPAGATION",
        "=" * 80,
        "",
        "AUDIT ONLY — Production / Backtest decision logic unchanged.",
        "",
        f"Historical reference artifact: {frozen_replay_path}",
        f"Replay rows compared: {total}",
        "",
        "CONTROL DESIGN",
        "-" * 80,
        "Control: current canonical master_panel.csv",
        "Treatment: controlled initial-release FRED panel",
        "Only the five audited FRED intervention fields differ.",
        "Historical frozen parity artifact is not used as the identity anchor",
        "because it predates the validated CORE_SERIES namespace fix.",
        "",
        "CURRENT CANONICAL CONTROL: READY",
        "",
        "CAPITAL CHAIN IMPACT",
        "-" * 80,
        summary.to_string(index=False),
        "",
        (
            "Any F13/F15/F18/Cash change: "
            f"{any_chain}/{total} "
            f"({any_chain_pct:.2f}%)"
        ),
        "",
        "STATE / ALLOCATION IMPACT",
        "-" * 80,
    ]

    for field, n in categorical_summary.items():
        lines.append(
            f"{field}: changed_days={n}"
        )

    # Interpretation is deliberately mechanical.
    if any_chain == 0:
        verdict = (
            "NO DECISION IMPACT — vintage contamination exists "
            "upstream but did not propagate into the capital chain."
        )
    else:
        verdict = (
            "DECISION IMPACT CONFIRMED — revised-vintage inputs "
            "changed historical capital-chain decisions. "
            "Magnitude/materiality must now be evaluated."
        )

    lines += [
        "",
        "VERDICT",
        "-" * 80,
        verdict,
        "",
        "[OUTPUT]",
        str(OUT_DAILY),
        str(OUT_SUMMARY),
        str(OUT_TXT),
    ]

    OUT_TXT.write_text(
        "\n".join(lines) + "\n"
    )

    print()
    print("=" * 80)
    print("FINAL CAUSAL IMPACT")
    print("=" * 80)
    print(summary.to_string(index=False))

    print()
    print(
        "Any F13/F15/F18/Cash change:",
        f"{any_chain}/{total}",
        f"({any_chain_pct:.2f}%)",
    )

    print()
    print("STATE / ALLOCATION CHANGES")

    for field, n in categorical_summary.items():
        print(
            f"{field}: {n}"
        )

    print()
    print("VERDICT:")
    print(verdict)

    print()
    print("[OUTPUT]")
    print(OUT_DAILY)
    print(OUT_SUMMARY)
    print(OUT_TXT)


if __name__ == "__main__":
    main()
