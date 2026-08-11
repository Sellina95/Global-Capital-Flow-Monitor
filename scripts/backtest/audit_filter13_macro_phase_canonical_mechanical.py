from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

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

DETAIL_PATH = (
    RESULT_DIR
    / "filter13_macro_phase_canonical_mechanical_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_macro_phase_canonical_mechanical_summary.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter13_macro_phase_canonical_mechanical_summary.txt"
)


# ============================================================
# Research candidate only
# ============================================================

COMBINED_CUT_LIMIT = 20.0


# ============================================================
# Helpers
# ============================================================

def num(x):
    return pd.to_numeric(
        pd.Series([x]),
        errors="coerce",
    ).iloc[0]


def production_clamp(x):
    """
    attribution_final.py의 _clamp 형태와 맞춤:
    max(lo, min(hi, int(value)))
    """

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


# ============================================================
# Main
# ============================================================

def main():

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    attr = pd.read_csv(
        ATTR_PATH
    )

    panel = pd.read_csv(
        PANEL_PATH
    )

    # --------------------------------------------------------
    # Contract
    # --------------------------------------------------------

    required = {
        "date",
        "base_budget",
        "macro_delta",
        "pre_cap_budget",
        "phase_cap",
        "phase_cap_effect",
        "v2_cap",
        "final_cap",
        "final_cap_effect",
        "final_budget",
    }

    missing = (
        required
        - set(attr.columns)
    )

    if missing:
        raise ValueError(
            "Canonical attribution missing columns:\n"
            f"{sorted(missing)}"
        )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Numeric
    # --------------------------------------------------------

    numeric_cols = [
        "base_budget",
        "macro_delta",
        "pre_cap_budget",
        "phase_cap",
        "phase_cap_effect",
        "v2_cap",
        "final_cap",
        "final_cap_effect",
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

    # --------------------------------------------------------
    # Market evaluation labels
    # --------------------------------------------------------

    panel["spy_next_return"] = (
        panel["SPY"]
        .pct_change()
        .shift(-1)
    )

    panel["spy_return_20d"] = (
        forward_return(
            panel["SPY"],
            20,
        )
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
                "spy_return_20d",
                "spy_return_60d",
            ]
        ],
        on="signal_date",
        how="left",
    )

    # ========================================================
    # Canonical mechanical replay
    #
    # pre_cap_budget
    #       ↓
    # phase_cap
    #       ↓
    # v2_cap
    #       ↓
    # clamp
    #
    # final_cap은 audit diagnostic으로 함께 확인.
    # ========================================================

    baseline_budget = []
    candidate_budget = []

    candidate_changed = []

    phase_cut_amounts = []
    candidate_phase_cut_amounts = []

    both_cut_flags = []

    for _, row in df.iterrows():

        base = num(
            row["base_budget"]
        )

        macro_delta = num(
            row["macro_delta"]
        )

        pre_cap = num(
            row["pre_cap_budget"]
        )

        phase_cap = num(
            row["phase_cap"]
        )

        v2_cap = num(
            row["v2_cap"]
        )

        if pd.isna(pre_cap):
            baseline_budget.append(
                np.nan
            )
            candidate_budget.append(
                np.nan
            )
            candidate_changed.append(
                False
            )
            phase_cut_amounts.append(
                np.nan
            )
            candidate_phase_cut_amounts.append(
                np.nan
            )
            both_cut_flags.append(
                False
            )
            continue

        # ----------------------------------------------------
        # Baseline Phase Cap
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Baseline v2 cap
        # ----------------------------------------------------

        baseline_after_v2 = (
            min(
                baseline_after_phase,
                v2_cap,
            )
            if pd.notna(v2_cap)
            else baseline_after_phase
        )

        baseline_final = (
            production_clamp(
                baseline_after_v2
            )
        )

        # ----------------------------------------------------
        # Candidate eligibility
        #
        # Base 70
        # Macro negative
        # Phase actually binding
        # ----------------------------------------------------

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

        candidate_phase_cut = (
            baseline_phase_cut
        )

        # ----------------------------------------------------
        # LIMITED COMBINED
        #
        # Macro cut + Phase cut <= 20%p
        #
        # Macro는 건드리지 않고,
        # 중복되는 Phase cut만 완화.
        # ----------------------------------------------------

        if both_cut:

            macro_cut_amount = max(
                -macro_delta,
                0.0,
            )

            allowed_phase_cut = max(
                COMBINED_CUT_LIMIT
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

        # ----------------------------------------------------
        # Reapply v2 cap mechanically
        # ----------------------------------------------------

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

        baseline_budget.append(
            baseline_final
        )

        candidate_budget.append(
            candidate_final
        )

        candidate_changed.append(
            (
                pd.notna(
                    baseline_final
                )
                and
                pd.notna(
                    candidate_final
                )
                and
                candidate_final
                != baseline_final
            )
        )

        phase_cut_amounts.append(
            baseline_phase_cut
        )

        candidate_phase_cut_amounts.append(
            candidate_phase_cut
        )

        both_cut_flags.append(
            both_cut
        )

    # ========================================================
    # Attach
    # ========================================================

    df[
        "baseline_mechanical_budget"
    ] = baseline_budget

    df[
        "candidate_budget"
    ] = candidate_budget

    df[
        "candidate_changed"
    ] = candidate_changed

    df[
        "baseline_phase_cut_amount"
    ] = phase_cut_amounts

    df[
        "candidate_phase_cut_amount"
    ] = candidate_phase_cut_amounts

    df[
        "both_cut"
    ] = both_cut_flags

    # ========================================================
    # PARITY
    # ========================================================

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

    mean_error = (
        abs_error.mean()
    )

    # --------------------------------------------------------
    # If baseline doesn't replay exactly:
    # STOP. Do not interpret candidate.
    # --------------------------------------------------------

    if parity_fail_days > 0:

        print(
            "=" * 88
        )

        print(
            "FILTER13 CANONICAL MACRO–PHASE "
            "MECHANICAL REPLAY"
        )

        print(
            "=" * 88
        )

        print()

        print(
            "BASELINE CANONICAL PARITY: FAIL"
        )

        print(
            f"Parity Fail Days : "
            f"{parity_fail_days:,}"
        )

        print(
            f"Max Abs Error    : "
            f"{max_error:.8f}"
        )

        print(
            f"Mean Abs Error   : "
            f"{mean_error:.8f}"
        )

        print()

        print(
            "First 20 failures:"
        )

        bad = df.loc[
            abs_error > 1e-9,
            [
                "signal_date",
                "pre_cap_budget",
                "phase_cap",
                "v2_cap",
                "final_cap",
                "final_budget",
                "baseline_mechanical_budget",
                "baseline_replay_error",
            ],
        ].head(
            20
        )

        print(
            bad.to_string(
                index=False
            )
        )

        print()

        print(
            "STOP — Candidate must not be interpreted."
        )

        return

    # ========================================================
    # Candidate diagnostics
    # ========================================================

    changed = df[
        df[
            "candidate_changed"
        ]
    ].copy()

    changed60 = pd.to_numeric(
        changed[
            "spy_return_60d"
        ],
        errors="coerce",
    ).dropna()

    # ========================================================
    # Economic proxy
    # Filter13 isolated only
    # ========================================================

    df[
        "baseline_return"
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

    df[
        "candidate_return"
    ] = (
        df[
            "spy_next_return"
        ]
        *
        df[
            "candidate_budget"
        ]
        /
        100.0
    )

    baseline_metrics = (
        metrics(
            df[
                "baseline_return"
            ]
        )
    )

    candidate_metrics = (
        metrics(
            df[
                "candidate_return"
            ]
        )
    )

    # ========================================================
    # Safety
    # ========================================================

    invalid_decrease_days = int(
        (
            df[
                "candidate_budget"
            ]
            <
            df[
                "baseline_mechanical_budget"
            ]
        ).sum()
    )

    invalid_over_100 = int(
        (
            df[
                "candidate_budget"
            ]
            > 100
        ).sum()
    )

    invalid_below_zero = int(
        (
            df[
                "candidate_budget"
            ]
            < 0
        ).sum()
    )

    # ========================================================
    # Summary
    # ========================================================

    summary = pd.DataFrame(
        [
            {
                "scenario":
                    "BASELINE_CANONICAL",

                "avg_budget":
                    df[
                        "baseline_mechanical_budget"
                    ].mean(),

                "changed_days":
                    0,

                **baseline_metrics,
            },

            {
                "scenario":
                    "LIMITED_COMBINED_20",

                "avg_budget":
                    df[
                        "candidate_budget"
                    ].mean(),

                "changed_days":
                    len(changed),

                **candidate_metrics,
            },
        ]
    )

    # ========================================================
    # Save
    # ========================================================

    detail_cols = [
        "signal_date",
        "base_budget",
        "macro_delta",
        "pre_cap_budget",
        "phase_cap",
        "phase_cap_effect",
        "v2_cap",
        "final_cap",
        "final_cap_effect",
        "final_budget",
        "baseline_mechanical_budget",
        "candidate_budget",
        "baseline_phase_cut_amount",
        "candidate_phase_cut_amount",
        "both_cut",
        "candidate_changed",
        "spy_return_20d",
        "spy_return_60d",
        "baseline_replay_error",
    ]

    df[
        detail_cols
    ].to_csv(
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
        "=" * 88
    )

    lines.append(
        "FILTER13 CANONICAL MACRO–PHASE "
        "MECHANICAL REPLAY"
    )

    lines.append(
        "=" * 88
    )

    lines.append("")

    lines.append(
        "BASELINE CANONICAL PARITY: PASS"
    )

    lines.append(
        f"Parity Fail Days       : "
        f"{parity_fail_days}"
    )

    lines.append(
        f"Max Abs Error          : "
        f"{max_error:.8f}"
    )

    lines.append(
        f"Mean Abs Error         : "
        f"{mean_error:.8f}"
    )

    lines.append("")

    lines.append(
        f"Combined Cut Limit     : "
        f"{COMBINED_CUT_LIMIT:.1f}%p"
    )

    lines.append(
        f"BOTH_CUT Candidate Days: "
        f"{int(df['both_cut'].sum()):,}"
    )

    lines.append(
        f"Actually Changed Days  : "
        f"{len(changed):,}"
    )

    lines.append(
        f"Invalid Decrease Days  : "
        f"{invalid_decrease_days:,}"
    )

    lines.append(
        f"Budget >100 Days       : "
        f"{invalid_over_100:,}"
    )

    lines.append(
        f"Budget <0 Days         : "
        f"{invalid_below_zero:,}"
    )

    lines.append("")

    lines.append(
        "Portfolio Proxy Summary"
    )

    lines.append(
        "-----------------------"
    )

    lines.append(
        summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "Changed-Day Diagnostics"
    )

    lines.append(
        "-----------------------"
    )

    lines.append(
        f"Changed Days           : "
        f"{len(changed):,}"
    )

    if len(changed):

        lines.append(
            f"Avg Budget Increase    : "
            f"{(
                changed['candidate_budget']
                -
                changed[
                    'baseline_mechanical_budget'
                ]
            ).mean():+.2f}%p"
        )

        lines.append(
            f"Avg SPY 20D            : "
            f"{changed['spy_return_20d'].mean():+.2f}%"
        )

    if len(changed60):

        lines.append(
            f"Avg SPY 60D            : "
            f"{changed60.mean():+.2f}%"
        )

        lines.append(
            f"SPY 60D >= +5% Rate    : "
            f"{(changed60 >= 5).mean():.1%}"
        )

        lines.append(
            f"SPY 60D <= -5% Rate    : "
            f"{(changed60 <= -5).mean():.1%}"
        )

        lines.append(
            f"Worst SPY 60D          : "
            f"{changed60.min():+.2f}%"
        )

    lines.append("")

    lines.append(
        "FINAL FILTER13 RESEARCH RULE"
    )

    lines.append(
        "----------------------------"
    )

    lines.append(
        "1. Canonical parity must PASS."
    )

    lines.append(
        "2. Candidate Changed Days must be > 0."
    )

    lines.append(
        "3. Candidate should improve CAGR/Sharpe."
    )

    lines.append(
        "4. MDD deterioration must remain acceptable."
    )

    lines.append(
        "5. Changed-day good/bad asymmetry must remain favorable."
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
    print(DETAIL_PATH)
    print(SUMMARY_PATH)
    print(TEXT_PATH)


if __name__ == "__main__":
    main()