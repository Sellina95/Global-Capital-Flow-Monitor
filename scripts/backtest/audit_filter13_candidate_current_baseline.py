from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Path bootstrap
# ============================================================

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


# ============================================================
# Reuse the runner we already built
# ============================================================

from scripts.backtest.audit_filter13_candidate_full_pipeline import (
    run_scenario,
    attach_portfolio_returns,
    portfolio_metrics,
)


# ============================================================
# Paths
# ============================================================

DATA_DIR = ROOT / "data" / "backtest"
RESULT_DIR = DATA_DIR / "results"

PANEL_PATH = (
    DATA_DIR
    / "master_panel.csv"
)

ATTR_PATH = (
    RESULT_DIR
    / "filter13_budget_attribution_final_daily.csv"
)

BASELINE_PATH = (
    RESULT_DIR
    / "filter13_current_pipeline_baseline_snapshot.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter13_candidate_current_pipeline_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_candidate_current_pipeline_summary.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter13_candidate_current_pipeline_summary.txt"
)


LIMITS = [
    15.0,
    20.0,
    25.0,
    30.0,
]


# ============================================================
# Helpers
# ============================================================

def numeric_mean(
    df: pd.DataFrame,
    col: str,
) -> float:

    if col not in df.columns:
        return np.nan

    return pd.to_numeric(
        df[col],
        errors="coerce",
    ).mean()


def summarize_scenario(
    df: pd.DataFrame,
    scenario: str,
) -> dict:

    metrics = portfolio_metrics(
        df[
            "portfolio_return_gross"
        ]
    )

    return {
        "scenario":
            scenario,

        "days":
            len(df),

        "avg_risk_budget_13":
            numeric_mean(
                df,
                "risk_budget_13",
            ),

        "avg_exposure_15":
            numeric_mean(
                df,
                "exposure_15",
            ),

        "avg_allocated_equity_18":
            numeric_mean(
                df,
                "allocated_equity_18",
            ),

        "avg_cash_18":
            numeric_mean(
                df,
                "cash_weight_18",
            ),

        **metrics,
    }


# ============================================================
# Main
# ============================================================

def main() -> None:

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # Load current master panel
    # ========================================================

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    # ========================================================
    # Load canonical Filter13 PIT attribution
    # ========================================================

    attr = pd.read_csv(
        ATTR_PATH
    )

    attr[
        "signal_date"
    ] = pd.to_datetime(
        attr["date"],
        errors="coerce",
    )

    attr = (
        attr
        .dropna(
            subset=[
                "signal_date"
            ]
        )
        .sort_values(
            "signal_date"
        )
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
    )

    attr_lookup = {
        pd.Timestamp(
            row["signal_date"]
        ).normalize():
        row

        for _, row
        in attr.iterrows()
    }

    # ========================================================
    # 1. CURRENT CODE BASELINE
    #
    # No historical daily_positions comparison.
    #
    # This is the new frozen baseline generated from:
    #
    # current master_panel
    # current execution state builder
    # current production 13
    # current production 15
    # current production 18
    # ========================================================

    print()
    print("=" * 90)
    print(
        "RUNNING CURRENT-CODE BASELINE"
    )
    print("=" * 90)

    baseline = run_scenario(
        panel=panel,
        attr_lookup=attr_lookup,
        limit=None,
        scenario_name="BASELINE_CURRENT",
    )

    baseline = (
        attach_portfolio_returns(
            scenario_df=baseline,
            panel=panel,
        )
    )

    # ========================================================
    # Baseline sanity checks
    # ========================================================

    baseline[
        "production_budget_13"
    ] = pd.to_numeric(
        baseline[
            "production_budget_13"
        ],
        errors="coerce",
    )

    baseline[
        "risk_budget_13"
    ] = pd.to_numeric(
        baseline[
            "risk_budget_13"
        ],
        errors="coerce",
    )

    baseline[
        "_baseline_budget_error"
    ] = (
        baseline[
            "risk_budget_13"
        ]
        -
        baseline[
            "production_budget_13"
        ]
    )

    baseline_budget_fail = int(
        (
            baseline[
                "_baseline_budget_error"
            ].abs()
            > 1e-9
        ).sum()
    )

    print()
    print(
        "CURRENT BASELINE SANITY"
    )

    print(
        f"Rows                 : "
        f"{len(baseline):,}"
    )

    print(
        f"Filter13 Injection Err: "
        f"{baseline_budget_fail:,}"
    )

    if baseline_budget_fail > 0:

        print()
        print(
            "STOP — Baseline scenario unexpectedly "
            "modified Filter13 budget."
        )

        print(
            baseline.loc[
                baseline[
                    "_baseline_budget_error"
                ].abs()
                > 1e-9,
                [
                    "signal_date",
                    "production_budget_13",
                    "risk_budget_13",
                    "_baseline_budget_error",
                ],
            ]
            .head(20)
            .to_string(
                index=False
            )
        )

        return

    # ========================================================
    # Freeze current-code baseline
    # ========================================================

    baseline.to_csv(
        BASELINE_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(
        "[OK] Current baseline frozen:"
    )
    print(
        BASELINE_PATH
    )

    # ========================================================
    # 2. Candidate scenarios
    # ========================================================

    frames = [
        baseline
    ]

    for limit in LIMITS:

        name = (
            f"LIMIT_{int(limit)}"
        )

        print()
        print("=" * 90)

        print(
            f"RUNNING {name}"
        )

        print("=" * 90)

        candidate = run_scenario(
            panel=panel,
            attr_lookup=attr_lookup,
            limit=limit,
            scenario_name=name,
        )

        candidate = (
            attach_portfolio_returns(
                scenario_df=candidate,
                panel=panel,
            )
        )

        frames.append(
            candidate
        )

    # ========================================================
    # 3. Combine
    # ========================================================

    detail = pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )

    # ========================================================
    # 4. Summary
    # ========================================================

    rows = []

    for scenario, group in (
        detail.groupby(
            "scenario",
            sort=False,
        )
    ):

        rows.append(
            summarize_scenario(
                group,
                scenario,
            )
        )

    summary = pd.DataFrame(
        rows
    )

    order = {
        "BASELINE_CURRENT": 0,
        "LIMIT_15": 1,
        "LIMIT_20": 2,
        "LIMIT_25": 3,
        "LIMIT_30": 4,
    }

    summary[
        "_order"
    ] = (
        summary[
            "scenario"
        ]
        .map(
            order
        )
    )

    summary = (
        summary
        .sort_values(
            "_order"
        )
        .drop(
            columns=[
                "_order"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # 5. Delta vs CURRENT baseline
    # ========================================================

    base = (
        summary.loc[
            summary[
                "scenario"
            ]
            == "BASELINE_CURRENT"
        ]
        .iloc[0]
    )

    compare_metrics = [
        "avg_risk_budget_13",
        "avg_exposure_15",
        "avg_allocated_equity_18",
        "avg_cash_18",
        "cagr",
        "mdd",
        "volatility",
        "sharpe",
    ]

    for col in compare_metrics:

        summary[
            f"{col}_delta"
        ] = (
            summary[col]
            - base[col]
        )

    # ========================================================
    # 6. Transmission ratios
    #
    # How much of restored Filter13 budget survives 15 / 18?
    # ========================================================

    summary[
        "filter13_to_15_ratio"
    ] = (
        summary[
            "avg_exposure_15"
        ]
        /
        summary[
            "avg_risk_budget_13"
        ]
    )

    summary[
        "filter15_to_18_ratio"
    ] = (
        summary[
            "avg_allocated_equity_18"
        ]
        /
        summary[
            "avg_exposure_15"
        ]
    )

    # ========================================================
    # Candidate delta transmission
    # ========================================================

    base_13 = float(
        base[
            "avg_risk_budget_13"
        ]
    )

    base_15 = float(
        base[
            "avg_exposure_15"
        ]
    )

    base_18 = float(
        base[
            "avg_allocated_equity_18"
        ]
    )

    summary[
        "restored_budget_13"
    ] = (
        summary[
            "avg_risk_budget_13"
        ]
        - base_13
    )

    summary[
        "restored_exposure_15"
    ] = (
        summary[
            "avg_exposure_15"
        ]
        - base_15
    )

    summary[
        "restored_allocated_18"
    ] = (
        summary[
            "avg_allocated_equity_18"
        ]
        - base_18
    )

    summary[
        "restoration_survival_13_to_15"
    ] = np.where(
        summary[
            "restored_budget_13"
        ].abs()
        > 1e-9,

        summary[
            "restored_exposure_15"
        ]
        /
        summary[
            "restored_budget_13"
        ],

        np.nan,
    )

    summary[
        "restoration_survival_15_to_18"
    ] = np.where(
        summary[
            "restored_exposure_15"
        ].abs()
        > 1e-9,

        summary[
            "restored_allocated_18"
        ]
        /
        summary[
            "restored_exposure_15"
        ],

        np.nan,
    )

    # ========================================================
    # Save
    # ========================================================

    detail.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Report
    # ========================================================

    lines = []

    lines.append(
        "=" * 105
    )

    lines.append(
        "FILTER13 CANDIDATE — CURRENT CODE "
        "FULL PIPELINE COUNTERFACTUAL"
    )

    lines.append(
        "=" * 105
    )

    lines.append("")

    lines.append(
        "BASELINE SOURCE:"
    )

    lines.append(
        "Current branch + current master_panel + "
        "current 13→15→18 execution chain"
    )

    lines.append("")

    lines.append(
        "Legacy daily_positions.csv parity:"
    )

    lines.append(
        "NOT USED — historical version mismatch "
        "already identified."
    )

    lines.append("")

    lines.append(
        f"Baseline rows              : "
        f"{len(baseline):,}"
    )

    lines.append(
        f"Baseline Filter13 injection: "
        f"{baseline_budget_fail} failures"
    )

    lines.append("")

    lines.append(
        "FULL PIPELINE SUMMARY"
    )

    lines.append(
        "-" * 105
    )

    display_cols = [
        "scenario",

        "avg_risk_budget_13",
        "avg_exposure_15",
        "avg_allocated_equity_18",

        "cagr",
        "mdd",
        "volatility",
        "sharpe",

        "restored_budget_13",
        "restored_exposure_15",
        "restored_allocated_18",

        "restoration_survival_13_to_15",
        "restoration_survival_15_to_18",
    ]

    lines.append(
        summary[
            display_cols
        ]
        .to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "Decision Logic"
    )

    lines.append(
        "--------------"
    )

    lines.append(
        "1. If Filter13 budget rises but Filter15 does not, "
        "Filter15 is the next bottleneck."
    )

    lines.append(
        "2. If Filter15 rises but Filter18 does not, "
        "Filter18 is the next bottleneck."
    )

    lines.append(
        "3. If restored exposure survives through Filter18 "
        "and CAGR/Sharpe improve, Filter13 candidate survives "
        "the full-pipeline test."
    )

    lines.append(
        "4. MDD deterioration remains a mandatory trade-off check."
    )

    lines.append(
        "5. This output is gross/pre-cost; production change "
        "still requires turnover/cost and final implementation validation."
    )

    report = "\n".join(
        lines
    )

    TEXT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print()
    print(
        report
    )

    print()
    print(
        "Saved:"
    )

    print(
        BASELINE_PATH
    )

    print(
        DETAIL_PATH
    )

    print(
        SUMMARY_PATH
    )

    print(
        TEXT_PATH
    )


if __name__ == "__main__":
    main()