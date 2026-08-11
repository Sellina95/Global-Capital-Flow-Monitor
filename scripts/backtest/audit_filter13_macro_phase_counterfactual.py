from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

ATTRIBUTION_PATH = (
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
    / "filter13_macro_phase_counterfactual_summary.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter13_macro_phase_counterfactual_detail.csv"
)


def calc_metrics(
    returns: pd.Series,
) -> dict:

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
        equity.iloc[-1]
        - 1.0
    )

    years = (
        len(r)
        / 252.0
    )

    cagr = (
        equity.iloc[-1]
        ** (1.0 / years)
        - 1.0
        if years > 0
        else np.nan
    )

    dd = (
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
            dd.min() * 100.0,

        "volatility":
            vol * 100.0,

        "sharpe":
            sharpe,
    }


def main() -> None:

    audit = pd.read_csv(
        ATTRIBUTION_PATH
    )

    panel = pd.read_csv(
        PANEL_PATH
    )

    # ======================================================
    # Dates
    # ======================================================

    audit["signal_date"] = pd.to_datetime(
        audit["date"],
        errors="coerce",
    )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"],
        errors="coerce",
    )

    audit = (
        audit
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
        "final_budget",
        "macro_delta",
        "phase_cap_effect",
    ]

    for col in numeric_cols:
        audit[col] = pd.to_numeric(
            audit[col],
            errors="coerce",
        )

    panel["SPY"] = pd.to_numeric(
        panel["SPY"],
        errors="coerce",
    )

    # ======================================================
    # Market Return
    # ======================================================

    panel["spy_next_return"] = (
        panel["SPY"]
        .pct_change()
        .shift(-1)
    )

    panel["spy_return_60d"] = (
        panel["SPY"].shift(-60)
        / panel["SPY"]
        - 1.0
    ) * 100.0

    df = audit.merge(
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
    # Interaction Flags
    # ======================================================

    df["macro_cut"] = (
        df["macro_delta"] < 0
    )

    df["phase_cut"] = (
        df["phase_cap_effect"] < 0
    )

    df["both_cut"] = (
        df["macro_cut"]
        &
        df["phase_cut"]
    )

    # ======================================================
    # Counterfactual Budgets
    #
    # 핵심:
    # 기존 final_budget에서
    # 해당 레이어의 감산만 되돌린다.
    #
    # Production 코드 수정 없음.
    # ======================================================

    df["budget_baseline"] = (
        df["final_budget"]
    )

    # ------------------------------------------------------
    # Scenario 1:
    # Macro가 이미 음수면
    # Phase Cap 효과를 되돌림
    # ------------------------------------------------------

    df["budget_no_double_phase"] = (
        df["final_budget"]
    )

    mask = (
        df["both_cut"]
    )

    df.loc[
        mask,
        "budget_no_double_phase",
    ] = (
        df.loc[
            mask,
            "final_budget",
        ]
        -
        df.loc[
            mask,
            "phase_cap_effect",
        ]
    )

    # ------------------------------------------------------
    # Scenario 2:
    # Phase Cap이 이미 작동하면
    # Macro 감산을 되돌림
    # ------------------------------------------------------

    df["budget_no_double_macro"] = (
        df["final_budget"]
    )

    df.loc[
        mask,
        "budget_no_double_macro",
    ] = (
        df.loc[
            mask,
            "final_budget",
        ]
        -
        df.loc[
            mask,
            "macro_delta",
        ]
    )

    # ------------------------------------------------------
    # Scenario 3:
    # Macro + Phase combined cut 최대 -20%p
    #
    # 탐색용 Research cap.
    # Production threshold 아님.
    # ------------------------------------------------------

    combined_delta = (
        df["macro_delta"]
        +
        df["phase_cap_effect"]
    )

    current_combined_cut = (
        -combined_delta
    )

    allowed_combined_cut = (
        current_combined_cut
        .clip(
            lower=0,
            upper=20,
        )
    )

    excess_cut = (
        current_combined_cut
        -
        allowed_combined_cut
    )

    excess_cut = (
        excess_cut
        .clip(lower=0)
    )

    df["budget_limited_combined"] = (
        df["final_budget"]
        +
        np.where(
            df["both_cut"],
            excess_cut,
            0.0,
        )
    )

    # ======================================================
    # Clamp
    # ======================================================

    budget_cols = [
        "budget_baseline",
        "budget_no_double_phase",
        "budget_no_double_macro",
        "budget_limited_combined",
    ]

    for col in budget_cols:

        df[col] = (
            df[col]
            .clip(
                lower=0,
                upper=100,
            )
        )

    # ======================================================
    # Exposure proxy return
    #
    # Filter13 단독 영향 격리:
    # SPY × Risk Budget
    #
    # 아직 Filter15/18 전체 pipeline return 아님.
    # ======================================================

    for col in budget_cols:

        return_col = (
            col.replace(
                "budget_",
                "return_",
            )
        )

        df[return_col] = (
            df["spy_next_return"]
            *
            df[col]
            / 100.0
        )

    # ======================================================
    # Summary
    # ======================================================

    scenarios = {
        "BASELINE":
            "budget_baseline",

        "NO_DOUBLE_PHASE":
            "budget_no_double_phase",

        "NO_DOUBLE_MACRO":
            "budget_no_double_macro",

        "LIMITED_COMBINED":
            "budget_limited_combined",
    }

    summary_rows = []

    for name, budget_col in scenarios.items():

        return_col = budget_col.replace(
            "budget_",
            "return_",
        )

        metrics = calc_metrics(
            df[return_col]
        )

        summary_rows.append(
            {
                "scenario":
                    name,

                "avg_budget":
                    df[
                        budget_col
                    ].mean(),

                "avg_budget_high70":
                    df.loc[
                        df["base_budget"]
                        .round()
                        .eq(70),
                        budget_col,
                    ].mean(),

                "avg_budget_both_cut":
                    df.loc[
                        df["both_cut"],
                        budget_col,
                    ].mean(),

                "changed_days":
                    int(
                        (
                            (
                                df[budget_col]
                                -
                                df["budget_baseline"]
                            )
                            .abs()
                            > 1e-9
                        ).sum()
                    ),

                **metrics,
            }
        )

    summary = pd.DataFrame(
        summary_rows
    )

    # ======================================================
    # Forward outcome diagnostics for changed days
    # ======================================================

    diagnostic_rows = []

    for name, budget_col in scenarios.items():

        if name == "BASELINE":
            continue

        changed = (
            (
                df[budget_col]
                -
                df["budget_baseline"]
            )
            .abs()
            > 1e-9
        )

        x = df.loc[
            changed
        ].copy()

        r60 = pd.to_numeric(
            x["spy_return_60d"],
            errors="coerce",
        ).dropna()

        diagnostic_rows.append(
            {
                "scenario":
                    name,

                "changed_days":
                    len(x),

                "avg_budget_increase":
                    (
                        x[budget_col]
                        -
                        x["budget_baseline"]
                    ).mean(),

                "avg_spy_60d":
                    r60.mean()
                    if len(r60)
                    else np.nan,

                "good_60d_rate":
                    (
                        r60 >= 5
                    ).mean()
                    if len(r60)
                    else np.nan,

                "bad_60d_rate":
                    (
                        r60 <= -5
                    ).mean()
                    if len(r60)
                    else np.nan,
            }
        )

    diagnostics = pd.DataFrame(
        diagnostic_rows
    )

    # ======================================================
    # Save
    # ======================================================

    detail_cols = [
        "signal_date",
        "base_budget",
        "final_budget",
        "macro_delta",
        "phase_cap_effect",
        "macro_cut",
        "phase_cut",
        "both_cut",
        "spy_return_60d",
        "budget_baseline",
        "budget_no_double_phase",
        "budget_no_double_macro",
        "budget_limited_combined",
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

    print("=" * 84)
    print(
        "FILTER13 MACRO–PHASE DOUBLE PENALTY COUNTERFACTUAL"
    )
    print("=" * 84)

    print()
    print("Portfolio Proxy Summary")
    print("-----------------------")

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("Changed-Day Forward Diagnostics")
    print("--------------------------------")

    print(
        diagnostics.to_string(
            index=False
        )
    )

    print()
    print("Saved:")
    print(SUMMARY_PATH)
    print(DETAIL_PATH)


if __name__ == "__main__":
    main()