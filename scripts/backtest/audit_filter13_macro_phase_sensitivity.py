from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

ATTR_PATH = (
    RESULT_DIR
    / "filter13_budget_attribution_final_daily.csv"
)

PANEL_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_macro_phase_sensitivity_summary.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter13_macro_phase_sensitivity_detail.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter13_macro_phase_sensitivity_summary.txt"
)


LIMITS = [
    15.0,
    20.0,
    25.0,
    30.0,
]


def production_clamp(x):

    if pd.isna(x):
        return np.nan

    return max(
        0,
        min(
            100,
            int(x),
        ),
    )


def forward_return(
    price: pd.Series,
    horizon: int,
):

    return (
        price.shift(-horizon)
        / price
        - 1.0
    ) * 100.0


def metrics(
    returns: pd.Series,
):

    r = pd.to_numeric(
        returns,
        errors="coerce",
    ).dropna()

    if len(r) == 0:

        return {
            "total_return": np.nan,
            "cagr": np.nan,
            "mdd": np.nan,
            "volatility": np.nan,
            "sharpe": np.nan,
        }

    equity = (
        1.0 + r
    ).cumprod()

    total_return = (
        equity.iloc[-1] - 1.0
    )

    years = (
        len(r) / 252.0
    )

    cagr = (
        equity.iloc[-1] ** (1.0 / years)
        - 1.0
        if years > 0
        else np.nan
    )

    drawdown = (
        equity
        / equity.cummax()
        - 1.0
    )

    vol = (
        r.std(ddof=1)
        * np.sqrt(252.0)
    )

    sharpe = (
        (
            r.mean()
            / r.std(ddof=1)
        )
        * np.sqrt(252.0)
        if r.std(ddof=1) > 0
        else np.nan
    )

    return {
        "total_return":
            total_return * 100.0,

        "cagr":
            cagr * 100.0,

        "mdd":
            drawdown.min() * 100.0,

        "volatility":
            vol * 100.0,

        "sharpe":
            sharpe,
    }


def build_candidate(
    df: pd.DataFrame,
    limit: float,
):

    candidate = []

    changed = []

    for _, row in df.iterrows():

        base = row["base_budget"]

        macro_delta = row["macro_delta"]

        pre_cap = row["pre_cap_budget"]

        phase_cap = row["phase_cap"]

        v2_cap = row["v2_cap"]

        # --------------------------------------------------
        # Baseline Phase Cap
        # --------------------------------------------------

        baseline_after_phase = (
            min(
                pre_cap,
                phase_cap,
            )
            if pd.notna(phase_cap)
            else pre_cap
        )

        baseline_phase_cut = max(
            pre_cap
            - baseline_after_phase,
            0.0,
        )

        # --------------------------------------------------
        # Candidate eligibility
        # --------------------------------------------------

        both_cut = (
            pd.notna(base)
            and round(base) == 70
            and pd.notna(macro_delta)
            and macro_delta < 0
            and baseline_phase_cut > 0
        )

        candidate_after_phase = (
            baseline_after_phase
        )

        if both_cut:

            macro_cut_amount = max(
                -macro_delta,
                0.0,
            )

            allowed_phase_cut = max(
                limit
                - macro_cut_amount,
                0.0,
            )

            candidate_phase_cut = min(
                baseline_phase_cut,
                allowed_phase_cut,
            )

            candidate_after_phase = (
                pre_cap
                - candidate_phase_cut
            )

        # --------------------------------------------------
        # Reapply v2 cap
        # --------------------------------------------------

        candidate_after_v2 = (
            min(
                candidate_after_phase,
                v2_cap,
            )
            if pd.notna(v2_cap)
            else candidate_after_phase
        )

        candidate_final = (
            production_clamp(
                candidate_after_v2
            )
        )

        baseline_final = (
            row[
                "baseline_mechanical_budget"
            ]
        )

        candidate.append(
            candidate_final
        )

        changed.append(
            (
                pd.notna(candidate_final)
                and pd.notna(baseline_final)
                and candidate_final
                != baseline_final
            )
        )

    return (
        pd.Series(
            candidate,
            index=df.index,
        ),
        pd.Series(
            changed,
            index=df.index,
        ),
    )


def main():

    attr = pd.read_csv(
        ATTR_PATH
    )

    panel = pd.read_csv(
        PANEL_PATH
    )

    # ======================================================
    # Dates
    # ======================================================

    attr["signal_date"] = pd.to_datetime(
        attr["date"],
        errors="coerce",
    )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"],
        errors="coerce",
    )

    attr = (
        attr
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    panel = (
        panel
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    # ======================================================
    # Numeric
    # ======================================================

    numeric_cols = [
        "base_budget",
        "macro_delta",
        "pre_cap_budget",
        "phase_cap",
        "v2_cap",
        "final_budget",
    ]

    for col in numeric_cols:

        attr[col] = pd.to_numeric(
            attr[col],
            errors="coerce",
        )

    panel["SPY"] = pd.to_numeric(
        panel["SPY"],
        errors="coerce",
    )

    # ======================================================
    # Market returns
    # ======================================================

    panel["spy_next_return"] = (
        panel["SPY"]
        .pct_change()
        .shift(-1)
    )

    panel["spy_return_60d"] = (
        forward_return(
            panel["SPY"],
            60,
        )
    )

    df = attr.merge(
        panel[
            [
                "signal_date",
                "SPY",
                "spy_next_return",
                "spy_return_60d",
            ]
        ],
        on="signal_date",
        how="left",
    )

    # ======================================================
    # Canonical baseline mechanical replay
    # ======================================================

    baseline = []

    for _, row in df.iterrows():

        pre_cap = row["pre_cap_budget"]

        phase_cap = row["phase_cap"]

        v2_cap = row["v2_cap"]

        after_phase = (
            min(
                pre_cap,
                phase_cap,
            )
            if pd.notna(phase_cap)
            else pre_cap
        )

        after_v2 = (
            min(
                after_phase,
                v2_cap,
            )
            if pd.notna(v2_cap)
            else after_phase
        )

        baseline.append(
            production_clamp(
                after_v2
            )
        )

    df[
        "baseline_mechanical_budget"
    ] = baseline

    # ======================================================
    # Parity first
    # ======================================================

    df[
        "baseline_replay_error"
    ] = (
        df[
            "baseline_mechanical_budget"
        ]
        -
        df[
            "final_budget"
        ]
    )

    abs_error = (
        df[
            "baseline_replay_error"
        ]
        .abs()
    )

    parity_fail_days = int(
        (
            abs_error > 1e-9
        ).sum()
    )

    max_error = (
        abs_error.max()
    )

    if parity_fail_days > 0:

        print(
            "BASELINE CANONICAL PARITY: FAIL"
        )

        print(
            "Parity Fail Days:",
            parity_fail_days,
        )

        print(
            "Max Error:",
            max_error,
        )

        return

    # ======================================================
    # Baseline Return
    # ======================================================

    df[
        "return_baseline"
    ] = (
        df[
            "spy_next_return"
        ]
        *
        df[
            "baseline_mechanical_budget"
        ]
        /
        100.0
    )

    baseline_metrics = metrics(
        df[
            "return_baseline"
        ]
    )

    summary_rows = []

    summary_rows.append(
        {
            "scenario":
                "BASELINE",

            "limit":
                np.nan,

            "avg_budget":
                df[
                    "baseline_mechanical_budget"
                ].mean(),

            "changed_days":
                0,

            "avg_budget_increase":
                0.0,

            "avg_changed_spy_60d":
                np.nan,

            "good_60d_rate":
                np.nan,

            "bad_60d_rate":
                np.nan,

            **baseline_metrics,
        }
    )

    # ======================================================
    # Sensitivity Scenarios
    # ======================================================

    detail_cols = [
        "signal_date",
        "base_budget",
        "macro_delta",
        "pre_cap_budget",
        "phase_cap",
        "v2_cap",
        "final_budget",
        "baseline_mechanical_budget",
        "spy_return_60d",
    ]

    for limit in LIMITS:

        candidate_col = (
            f"candidate_budget_{int(limit)}"
        )

        changed_col = (
            f"changed_{int(limit)}"
        )

        candidate, changed = (
            build_candidate(
                df,
                limit,
            )
        )

        df[
            candidate_col
        ] = candidate

        df[
            changed_col
        ] = changed

        return_col = (
            f"return_{int(limit)}"
        )

        df[
            return_col
        ] = (
            df[
                "spy_next_return"
            ]
            *
            df[
                candidate_col
            ]
            /
            100.0
        )

        scenario_metrics = metrics(
            df[
                return_col
            ]
        )

        changed_df = df[
            df[
                changed_col
            ]
        ].copy()

        changed60 = pd.to_numeric(
            changed_df[
                "spy_return_60d"
            ],
            errors="coerce",
        ).dropna()

        avg_budget_increase = (
            (
                changed_df[
                    candidate_col
                ]
                -
                changed_df[
                    "baseline_mechanical_budget"
                ]
            ).mean()
            if len(changed_df)
            else np.nan
        )

        summary_rows.append(
            {
                "scenario":
                    f"LIMIT_{int(limit)}",

                "limit":
                    limit,

                "avg_budget":
                    df[
                        candidate_col
                    ].mean(),

                "changed_days":
                    len(
                        changed_df
                    ),

                "avg_budget_increase":
                    avg_budget_increase,

                "avg_changed_spy_60d":
                    (
                        changed60.mean()
                        if len(changed60)
                        else np.nan
                    ),

                "good_60d_rate":
                    (
                        (
                            changed60 >= 5
                        ).mean()
                        if len(changed60)
                        else np.nan
                    ),

                "bad_60d_rate":
                    (
                        (
                            changed60 <= -5
                        ).mean()
                        if len(changed60)
                        else np.nan
                    ),

                **scenario_metrics,
            }
        )

        detail_cols.extend(
            [
                candidate_col,
                changed_col,
            ]
        )

    summary = pd.DataFrame(
        summary_rows
    )

    # ======================================================
    # Delta vs Baseline
    # ======================================================

    baseline_cagr = (
        summary.loc[
            summary["scenario"]
            == "BASELINE",
            "cagr",
        ].iloc[0]
    )

    baseline_mdd = (
        summary.loc[
            summary["scenario"]
            == "BASELINE",
            "mdd",
        ].iloc[0]
    )

    baseline_sharpe = (
        summary.loc[
            summary["scenario"]
            == "BASELINE",
            "sharpe",
        ].iloc[0]
    )

    summary[
        "cagr_improvement"
    ] = (
        summary["cagr"]
        - baseline_cagr
    )

    summary[
        "mdd_change"
    ] = (
        summary["mdd"]
        - baseline_mdd
    )

    summary[
        "sharpe_improvement"
    ] = (
        summary["sharpe"]
        - baseline_sharpe
    )

    # ======================================================
    # Save
    # ======================================================

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    df[
        detail_cols
    ].to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # ======================================================
    # Report
    # ======================================================

    lines = []

    lines.append(
        "=" * 92
    )

    lines.append(
        "FILTER13 MACRO–PHASE COMBINED CUT "
        "SENSITIVITY VALIDATION"
    )

    lines.append(
        "=" * 92
    )

    lines.append("")

    lines.append(
        "BASELINE CANONICAL PARITY: PASS"
    )

    lines.append(
        f"Parity Fail Days : "
        f"{parity_fail_days}"
    )

    lines.append(
        f"Max Error        : "
        f"{max_error:.8f}"
    )

    lines.append("")

    lines.append(
        summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "Interpretation:"
    )

    lines.append(
        "- Look for broad improvement across multiple limits."
    )

    lines.append(
        "- Do NOT select the single highest CAGR."
    )

    lines.append(
        "- Prefer robust plateau + acceptable MDD trade-off."
    )

    lines.append(
        "- If only one limit works, treat as overfit risk."
    )

    report = "\n".join(
        lines
    )

    TEXT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print(
        report
    )

    print()
    print("Saved:")
    print(SUMMARY_PATH)
    print(DETAIL_PATH)
    print(TEXT_PATH)


if __name__ == "__main__":
    main()