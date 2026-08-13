from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"


# ============================================================
# Required audit artifacts
# ============================================================

FILTER13_CANONICAL = (
    RESULTS
    / "filter13_canonical_baseline_daily.csv"
)

SOURCE_PARITY = (
    RESULTS
    / "filter18_current_source_parity.txt"
)

SEMANTIC_PARITY = (
    RESULTS
    / "filter18_rank3d_exact_semantic_parity_summary.txt"
)

RANK3D_SUMMARY = (
    RESULTS
    / "filter18_rank_persistence_counterfactual_summary.csv"
)

OUT_CSV = (
    RESULTS
    / "filter18_rank3d_final_production_gate.csv"
)

OUT_TXT = (
    RESULTS
    / "filter18_rank3d_final_production_gate.txt"
)


# ============================================================
# Hard Production gates
# ============================================================

EXPECTED_ROWS = 4645
TARGET_SCENARIO = "PERSIST_3D"
BASELINE_SCENARIO = "BASELINE_1D"

MIN_TURNOVER_REDUCTION = 0.30
MIN_NET_CAGR_IMPROVEMENT = 0.0
MIN_NET_SHARPE_IMPROVEMENT = 0.0

TOL = 1e-9


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Required audit artifact missing:\n{path}"
        )


def require_pass_text(
    path: Path,
    label: str,
) -> str:

    text = path.read_text(
        encoding="utf-8"
    )

    if "FINAL STATUS: PASS" not in text:
        raise RuntimeError(
            f"{label} did not PASS:\n{path}"
        )

    return text


def main() -> None:

    # ========================================================
    # 1. Artifact existence
    # ========================================================

    for path in [
        FILTER13_CANONICAL,
        SOURCE_PARITY,
        SEMANTIC_PARITY,
        RANK3D_SUMMARY,
    ]:
        require_file(path)

    # ========================================================
    # 2. Current canonical Filter13 contract
    # ========================================================

    canonical = pd.read_csv(
        FILTER13_CANONICAL
    )

    canonical_ok = (
        canonical[
            canonical["status"].eq("OK")
        ].copy()
        if "status" in canonical.columns
        else canonical.copy()
    )

    canonical_rows = len(
        canonical_ok
    )

    if canonical_rows != EXPECTED_ROWS:
        raise RuntimeError(
            "Canonical Filter13 coverage failure: "
            f"{canonical_rows:,} != {EXPECTED_ROWS:,}"
        )

    # Same-frame errors must still be zero.
    parity_cols = [
        "pre_cap_error",
        "budget_error",
        "final_state_budget_error",
        "macro_tilt_error",
        "phase_cap_error",
    ]

    missing_parity_cols = (
        set(parity_cols)
        - set(canonical_ok.columns)
    )

    if missing_parity_cols:
        raise RuntimeError(
            "Canonical Filter13 missing parity columns: "
            f"{sorted(missing_parity_cols)}"
        )

    canonical_parity_fail = 0
    canonical_max_error = 0.0

    for col in parity_cols:

        values = pd.to_numeric(
            canonical_ok[col],
            errors="coerce",
        )

        canonical_parity_fail += int(
            (
                values.abs() > TOL
            ).sum()
        )

        max_err = values.abs().max()

        if pd.notna(max_err):
            canonical_max_error = max(
                canonical_max_error,
                float(max_err),
            )

    if canonical_parity_fail != 0:
        raise RuntimeError(
            "Current canonical Filter13 parity "
            f"failed on {canonical_parity_fail:,} checks."
        )

    # ========================================================
    # 3. Filter18 lineage / semantic parity hard gates
    # ========================================================

    source_text = require_pass_text(
        SOURCE_PARITY,
        "Filter18 source parity",
    )

    semantic_text = require_pass_text(
        SEMANTIC_PARITY,
        "Filter18 Rank3D semantic parity",
    )

    # Additional exact semantic checks.
    required_semantic_markers = [
        "Executed-weight fail days: 0",
        "Accepted-rank fail days  : 0",
        "Pending-rank fail days   : 0",
        "Pending-count fail days  : 0",
        "Action fail days         : 0",
    ]

    missing_markers = [
        marker
        for marker in required_semantic_markers
        if marker not in semantic_text
    ]

    if missing_markers:
        raise RuntimeError(
            "Semantic parity report does not contain "
            "all required zero-mismatch gates:\n"
            + "\n".join(missing_markers)
        )

    # ========================================================
    # 4. Rank3D economic results
    # ========================================================

    summary = pd.read_csv(
        RANK3D_SUMMARY
    )

    required_cols = {
        "scenario",
        "annualized_turnover",
        "total_cost_pct",
        "gross_cagr",
        "net_cagr",
        "net_mdd",
        "net_volatility",
        "net_sharpe",
    }

    missing = (
        required_cols
        - set(summary.columns)
    )

    if missing:
        raise RuntimeError(
            "Rank persistence summary missing columns: "
            f"{sorted(missing)}"
        )

    baseline_rows = summary[
        summary["scenario"].eq(
            BASELINE_SCENARIO
        )
    ]

    candidate_rows = summary[
        summary["scenario"].eq(
            TARGET_SCENARIO
        )
    ]

    if len(baseline_rows) != 1:
        raise RuntimeError(
            f"{BASELINE_SCENARIO} row not uniquely found."
        )

    if len(candidate_rows) != 1:
        raise RuntimeError(
            f"{TARGET_SCENARIO} row not uniquely found."
        )

    baseline = baseline_rows.iloc[0]
    candidate = candidate_rows.iloc[0]

    baseline_turnover = float(
        baseline["annualized_turnover"]
    )

    candidate_turnover = float(
        candidate["annualized_turnover"]
    )

    baseline_net_cagr = float(
        baseline["net_cagr"]
    )

    candidate_net_cagr = float(
        candidate["net_cagr"]
    )

    baseline_net_sharpe = float(
        baseline["net_sharpe"]
    )

    candidate_net_sharpe = float(
        candidate["net_sharpe"]
    )

    baseline_mdd = float(
        baseline["net_mdd"]
    )

    candidate_mdd = float(
        candidate["net_mdd"]
    )

    turnover_reduction = (
        1.0
        - candidate_turnover
        / baseline_turnover
    )

    net_cagr_delta = (
        candidate_net_cagr
        - baseline_net_cagr
    )

    net_sharpe_delta = (
        candidate_net_sharpe
        - baseline_net_sharpe
    )

    net_mdd_delta = (
        candidate_mdd
        - baseline_mdd
    )

    # ========================================================
    # 5. Production decision gates
    # ========================================================

    gate_turnover = (
        turnover_reduction
        >= MIN_TURNOVER_REDUCTION
    )

    gate_cagr = (
        net_cagr_delta
        > MIN_NET_CAGR_IMPROVEMENT
    )

    gate_sharpe = (
        net_sharpe_delta
        > MIN_NET_SHARPE_IMPROVEMENT
    )

    # Candidate MDD must not be worse than baseline.
    # Here "higher" means less negative.
    gate_mdd = (
        candidate_mdd
        >= baseline_mdd
    )

    gates = {
        "canonical_filter13_parity":
            canonical_parity_fail == 0,

        "filter18_source_parity":
            "FINAL STATUS: PASS"
            in source_text,

        "filter18_semantic_parity":
            "FINAL STATUS: PASS"
            in semantic_text,

        "turnover_reduction":
            gate_turnover,

        "net_cagr_improvement":
            gate_cagr,

        "net_sharpe_improvement":
            gate_sharpe,

        "mdd_not_worse":
            gate_mdd,
    }

    all_pass = all(
        gates.values()
    )

    # ========================================================
    # 6. Output
    # ========================================================

    output = pd.DataFrame(
        [
            {
                "scenario":
                    BASELINE_SCENARIO,

                "annualized_turnover":
                    baseline_turnover,

                "total_cost_pct":
                    float(
                        baseline[
                            "total_cost_pct"
                        ]
                    ),

                "gross_cagr":
                    float(
                        baseline[
                            "gross_cagr"
                        ]
                    ),

                "net_cagr":
                    baseline_net_cagr,

                "net_mdd":
                    baseline_mdd,

                "net_volatility":
                    float(
                        baseline[
                            "net_volatility"
                        ]
                    ),

                "net_sharpe":
                    baseline_net_sharpe,

                "turnover_reduction_vs_baseline":
                    0.0,

                "net_cagr_delta":
                    0.0,

                "net_mdd_delta":
                    0.0,

                "net_sharpe_delta":
                    0.0,
            },
            {
                "scenario":
                    TARGET_SCENARIO,

                "annualized_turnover":
                    candidate_turnover,

                "total_cost_pct":
                    float(
                        candidate[
                            "total_cost_pct"
                        ]
                    ),

                "gross_cagr":
                    float(
                        candidate[
                            "gross_cagr"
                        ]
                    ),

                "net_cagr":
                    candidate_net_cagr,

                "net_mdd":
                    candidate_mdd,

                "net_volatility":
                    float(
                        candidate[
                            "net_volatility"
                        ]
                    ),

                "net_sharpe":
                    candidate_net_sharpe,

                "turnover_reduction_vs_baseline":
                    turnover_reduction,

                "net_cagr_delta":
                    net_cagr_delta,

                "net_mdd_delta":
                    net_mdd_delta,

                "net_sharpe_delta":
                    net_sharpe_delta,
            },
        ]
    )

    output.to_csv(
        OUT_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    lines = []

    lines.append(
        "# FILTER18 RANK3D FINAL PRODUCTION GATE"
    )

    lines.append("")

    lines.append(
        "## Lineage / Parity"
    )

    lines.append(
        f"Canonical Filter13 rows : "
        f"{canonical_rows:,}"
    )

    lines.append(
        f"Canonical parity fails  : "
        f"{canonical_parity_fail:,}"
    )

    lines.append(
        f"Canonical max error     : "
        f"{canonical_max_error:.10f}"
    )

    lines.append(
        "Filter18 source parity  : PASS"
    )

    lines.append(
        "Rank3D semantic parity  : PASS"
    )

    lines.append("")

    lines.append(
        "## Economic Comparison"
    )

    lines.append("")

    lines.append(
        output.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "## Production Gates"
    )

    lines.append("")

    for name, passed in gates.items():

        lines.append(
            f"{name:30s}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    lines.append("")

    lines.append(
        f"Turnover reduction : "
        f"{turnover_reduction:.2%}"
    )

    lines.append(
        f"Net CAGR delta      : "
        f"{net_cagr_delta:+.6f}%p"
    )

    lines.append(
        f"Net Sharpe delta    : "
        f"{net_sharpe_delta:+.6f}"
    )

    lines.append(
        f"Net MDD delta       : "
        f"{net_mdd_delta:+.6f}%p"
    )

    lines.append("")

    if all_pass:

        lines.append(
            "FINAL STATUS: PASS"
        )

        lines.append("")

        lines.append(
            "PRODUCTION DECISION:"
        )

        lines.append(
            "Filter13 = CURRENT / NO CHANGE"
        )

        lines.append(
            "Filter15 = CURRENT / NO CHANGE"
        )

        lines.append(
            "Filter18 = RANK PERSISTENCE 3D APPROVED"
        )

        lines.append(
            "Macro persistence = REJECTED / NOT USED"
        )

    else:

        lines.append(
            "FINAL STATUS: FAIL"
        )

        lines.append("")

        lines.append(
            "STOP — Rank3D must not be approved "
            "until every Production gate passes."
        )

    text = "\n".join(
        lines
    )

    OUT_TXT.write_text(
        text,
        encoding="utf-8",
    )

    print()
    print(text)

    print()
    print("Saved:")
    print(OUT_CSV)
    print(OUT_TXT)

    if not all_pass:

        raise RuntimeError(
            "FILTER18 RANK3D FINAL PRODUCTION GATE FAILED."
        )


if __name__ == "__main__":
    main()
