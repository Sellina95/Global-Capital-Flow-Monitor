from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

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

DETAIL_PATH = (
    RESULT_DIR
    / "filter13_high70_suppression_detail.csv"
)

ATTRIBUTION_OUTPUT_PATH = (
    RESULT_DIR
    / "filter13_high70_suppression_attribution.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_high70_suppression_summary.txt"
)


# ============================================================
# Attribution components
#
# 실제 filter13_budget_attribution_final_daily.csv 컬럼명 기준
# ============================================================

COMPONENTS = [
    "structure_delta",
    "credit_delta",
    "liquidity_delta",
    "structural_v2_delta",
    "drift_delta",
    "flow_gamma_delta",
    "flow_continuity_delta",
    "flow_regime_delta",
    "macro_delta",
    "positioning_delta",
    "event_floor_delta",
    "phase_cap_effect",
    "final_cap_effect",
]


# ============================================================
# Helpers
# ============================================================

def forward_return(
    price: pd.Series,
    horizon: int,
) -> pd.Series:

    return (
        price.shift(-horizon)
        / price
        - 1.0
    ) * 100.0


def classify_forward_return(
    x: float,
) -> str:

    if pd.isna(x):
        return "NO_FORWARD_DATA"

    if x >= 5.0:
        return "GOOD_FORWARD"

    if x <= -5.0:
        return "BAD_FORWARD"

    return "OTHER_FORWARD"


def safe_mean(
    series: pd.Series,
) -> float:

    s = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if len(s) == 0:
        return np.nan

    return float(
        s.mean()
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # 1. Load
    # --------------------------------------------------------

    if not ATTRIBUTION_PATH.exists():
        raise FileNotFoundError(
            ATTRIBUTION_PATH
        )

    if not PANEL_PATH.exists():
        raise FileNotFoundError(
            PANEL_PATH
        )

    audit = pd.read_csv(
        ATTRIBUTION_PATH
    )

    panel = pd.read_csv(
        PANEL_PATH
    )

    # --------------------------------------------------------
    # 2. Contract checks
    # --------------------------------------------------------

    required_audit_cols = {
        "date",
        "base_budget",
        "final_budget",
    }

    required_audit_cols.update(
        COMPONENTS
    )

    missing_audit = (
        required_audit_cols
        - set(audit.columns)
    )

    if missing_audit:
        raise ValueError(
            "Attribution file missing columns:\n"
            f"{sorted(missing_audit)}"
        )

    required_panel_cols = {
        "signal_date",
        "SPY",
    }

    missing_panel = (
        required_panel_cols
        - set(panel.columns)
    )

    if missing_panel:
        raise ValueError(
            "master_panel.csv missing columns:\n"
            f"{sorted(missing_panel)}"
        )

    # --------------------------------------------------------
    # 3. Normalize dates
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 4. Numeric conversion
    # --------------------------------------------------------

    numeric_audit_cols = [
        "base_budget",
        "final_budget",
        "pre_cap_budget",
        "phase_cap",
        "final_cap",
    ] + COMPONENTS

    for col in numeric_audit_cols:

        if col in audit.columns:

            audit[col] = pd.to_numeric(
                audit[col],
                errors="coerce",
            )

    panel["SPY"] = pd.to_numeric(
        panel["SPY"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # 5. Forward market outcome
    #
    # IMPORTANT:
    # Forward returns are evaluation labels only.
    # They are NOT used to produce Filter13 budget.
    # --------------------------------------------------------

    market = panel[
        [
            "signal_date",
            "SPY",
        ]
    ].copy()

    market["spy_return_20d"] = (
        forward_return(
            market["SPY"],
            20,
        )
    )

    market["spy_return_60d"] = (
        forward_return(
            market["SPY"],
            60,
        )
    )

    df = audit.merge(
        market,
        on="signal_date",
        how="left",
    )

    # --------------------------------------------------------
    # 6. HIGH BASE ONLY
    # --------------------------------------------------------

    high70 = df[
        df["base_budget"]
        .round()
        .eq(70)
    ].copy()

    if high70.empty:
        raise ValueError(
            "No Base Budget = 70 rows found."
        )

    # --------------------------------------------------------
    # 7. Forward outcome labels
    # --------------------------------------------------------

    high70["forward_group"] = (
        high70[
            "spy_return_60d"
        ]
        .apply(
            classify_forward_return
        )
    )

    # --------------------------------------------------------
    # 8. Total suppression
    # --------------------------------------------------------

    high70["total_suppression"] = (
        high70["final_budget"]
        - high70["base_budget"]
    )

    high70["suppression_amount"] = (
        high70["base_budget"]
        - high70["final_budget"]
    )

    # --------------------------------------------------------
    # 9. Useful diagnostic labels
    # --------------------------------------------------------

    high70["strong_market_suppressed"] = (
        high70["spy_return_60d"].ge(5)
        &
        high70["final_budget"].lt(50)
    )

    high70["very_strong_market_suppressed"] = (
        high70["spy_return_60d"].ge(10)
        &
        high70["final_budget"].lt(50)
    )

    high70["bad_market_protected"] = (
        high70["spy_return_60d"].le(-5)
        &
        high70["final_budget"].lt(50)
    )

    # --------------------------------------------------------
    # 10. Component attribution by forward outcome
    # --------------------------------------------------------

    attribution_rows = []

    ordered_groups = [
        "ALL_HIGH70",
        "GOOD_FORWARD",
        "BAD_FORWARD",
        "OTHER_FORWARD",
    ]

    for group_name in ordered_groups:

        if group_name == "ALL_HIGH70":

            group = high70[
                high70["forward_group"]
                != "NO_FORWARD_DATA"
            ].copy()

        else:

            group = high70[
                high70["forward_group"]
                == group_name
            ].copy()

        if group.empty:
            continue

        for component in COMPONENTS:

            values = pd.to_numeric(
                group[component],
                errors="coerce",
            )

            attribution_rows.append(
                {
                    "forward_group":
                        group_name,

                    "component":
                        component,

                    "days":
                        len(group),

                    "mean_delta":
                        values.mean(),

                    "median_delta":
                        values.median(),

                    "negative_days":
                        int(
                            (values < 0).sum()
                        ),

                    "positive_days":
                        int(
                            (values > 0).sum()
                        ),

                    "zero_days":
                        int(
                            (values == 0).sum()
                        ),

                    "negative_day_rate":
                        (
                            (values < 0).mean()
                        ),

                    "mean_negative_delta":
                        values[
                            values < 0
                        ].mean(),

                    "total_delta":
                        values.sum(),
                }
            )

    attribution = pd.DataFrame(
        attribution_rows
    )

    # --------------------------------------------------------
    # 11. Good-vs-Bad comparison
    # --------------------------------------------------------

    good = high70[
        high70["forward_group"]
        == "GOOD_FORWARD"
    ].copy()

    bad = high70[
        high70["forward_group"]
        == "BAD_FORWARD"
    ].copy()

    comparison_rows = []

    for component in COMPONENTS:

        good_mean = safe_mean(
            good[component]
        )

        bad_mean = safe_mean(
            bad[component]
        )

        comparison_rows.append(
            {
                "component":
                    component,

                "good_forward_mean_delta":
                    good_mean,

                "bad_forward_mean_delta":
                    bad_mean,

                # Negative means:
                # component cuts MORE in good markets
                # than in bad markets.
                "good_minus_bad_delta":
                    (
                        good_mean
                        - bad_mean
                    )
                    if (
                        pd.notna(good_mean)
                        and pd.notna(bad_mean)
                    )
                    else np.nan,

                "good_negative_days":
                    int(
                        (
                            pd.to_numeric(
                                good[component],
                                errors="coerce",
                            )
                            < 0
                        ).sum()
                    ),

                "bad_negative_days":
                    int(
                        (
                            pd.to_numeric(
                                bad[component],
                                errors="coerce",
                            )
                            < 0
                        ).sum()
                    ),
            }
        )

    comparison = pd.DataFrame(
        comparison_rows
    )

    comparison = comparison.sort_values(
        "good_forward_mean_delta",
        ascending=True,
    )

    # --------------------------------------------------------
    # 12. Append comparison into attribution output
    # --------------------------------------------------------

    attribution["section"] = (
        "GROUP_ATTRIBUTION"
    )

    comparison_export = (
        comparison.copy()
    )

    comparison_export["section"] = (
        "GOOD_VS_BAD_COMPARISON"
    )

    # Make common output shape
    combined_columns = sorted(
        set(
            attribution.columns
        )
        |
        set(
            comparison_export.columns
        )
    )

    attribution_export = (
        attribution.reindex(
            columns=combined_columns
        )
    )

    comparison_export = (
        comparison_export.reindex(
            columns=combined_columns
        )
    )

    attribution_final = pd.concat(
        [
            attribution_export,
            comparison_export,
        ],
        ignore_index=True,
    )

    # --------------------------------------------------------
    # 13. Save detail
    # --------------------------------------------------------

    detail_cols = [
        "signal_date",
        "sentiment_state",
        "base_budget",
        "final_budget",
        "total_suppression",
        "suppression_amount",
        "spy_return_20d",
        "spy_return_60d",
        "forward_group",
        "strong_market_suppressed",
        "very_strong_market_suppressed",
        "bad_market_protected",
    ]

    for col in COMPONENTS:

        if col not in detail_cols:
            detail_cols.append(
                col
            )

    optional_cols = [
        "pre_cap_budget",
        "phase_cap",
        "final_cap",
        "market_regime",
        "macro_narrative",
        "hy_oas_today",
        "net_liq_pct_change",
        "sp500_pos_z",
    ]

    for col in optional_cols:

        if col in high70.columns:
            detail_cols.append(
                col
            )

    high70[
        detail_cols
    ].to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    attribution_final.to_csv(
        ATTRIBUTION_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # 14. Summary diagnostics
    # --------------------------------------------------------

    valid = high70[
        high70["forward_group"]
        != "NO_FORWARD_DATA"
    ].copy()

    other = high70[
        high70["forward_group"]
        == "OTHER_FORWARD"
    ].copy()

    strong_suppressed = int(
        valid[
            "strong_market_suppressed"
        ].sum()
    )

    very_strong_suppressed = int(
        valid[
            "very_strong_market_suppressed"
        ].sum()
    )

    bad_protected = int(
        valid[
            "bad_market_protected"
        ].sum()
    )

    # --------------------------------------------------------
    # 15. Top suppressors
    # --------------------------------------------------------

    all_attr = attribution[
        attribution["forward_group"]
        == "ALL_HIGH70"
    ].copy()

    good_attr = attribution[
        attribution["forward_group"]
        == "GOOD_FORWARD"
    ].copy()

    bad_attr = attribution[
        attribution["forward_group"]
        == "BAD_FORWARD"
    ].copy()

    all_attr = all_attr.sort_values(
        "mean_delta",
        ascending=True,
    )

    good_attr = good_attr.sort_values(
        "mean_delta",
        ascending=True,
    )

    bad_attr = bad_attr.sort_values(
        "mean_delta",
        ascending=True,
    )

    # --------------------------------------------------------
    # 16. Text report
    # --------------------------------------------------------

    lines = []

    lines.append(
        "=" * 82
    )

    lines.append(
        "FILTER13 HIGH-70 SUPPRESSION AUDIT"
    )

    lines.append(
        "=" * 82
    )

    lines.append(
        f"Period               : "
        f"{high70['signal_date'].min().date()} "
        f"~ "
        f"{high70['signal_date'].max().date()}"
    )

    lines.append(
        f"Base=70 Days         : "
        f"{len(high70):,}"
    )

    lines.append(
        f"Valid 60D Outcomes   : "
        f"{len(valid):,}"
    )

    lines.append("")

    lines.append(
        f"Average Base Budget  : "
        f"{high70['base_budget'].mean():.2f}"
    )

    lines.append(
        f"Average Final Budget : "
        f"{high70['final_budget'].mean():.2f}"
    )

    lines.append(
        f"Average Suppression  : "
        f"{high70['suppression_amount'].mean():.2f}%p"
    )

    lines.append("")

    lines.append(
        "Forward Outcome Distribution"
    )

    lines.append(
        "----------------------------"
    )

    lines.append(
        f"GOOD_FORWARD >= +5% : "
        f"{len(good):,} "
        f"({len(good) / len(valid):.1%})"
        if len(valid)
        else "GOOD_FORWARD: N/A"
    )

    lines.append(
        f"BAD_FORWARD <= -5%  : "
        f"{len(bad):,} "
        f"({len(bad) / len(valid):.1%})"
        if len(valid)
        else "BAD_FORWARD: N/A"
    )

    lines.append(
        f"OTHER_FORWARD       : "
        f"{len(other):,} "
        f"({len(other) / len(valid):.1%})"
        if len(valid)
        else "OTHER_FORWARD: N/A"
    )

    lines.append("")

    lines.append(
        f"Average SPY 60D — ALL : "
        f"{valid['spy_return_60d'].mean():+.2f}%"
    )

    lines.append(
        f"Average SPY 60D — GOOD: "
        f"{good['spy_return_60d'].mean():+.2f}%"
        if len(good)
        else "Average SPY 60D — GOOD: N/A"
    )

    lines.append(
        f"Average SPY 60D — BAD : "
        f"{bad['spy_return_60d'].mean():+.2f}%"
        if len(bad)
        else "Average SPY 60D — BAD: N/A"
    )

    lines.append("")

    lines.append(
        "Suppression Diagnostics"
    )

    lines.append(
        "-----------------------"
    )

    lines.append(
        f"GOOD market + Final Budget < 50 : "
        f"{strong_suppressed:,}"
    )

    if len(good):

        lines.append(
            f"Good-Market Suppression Rate     : "
            f"{strong_suppressed / len(good):.1%}"
        )

    lines.append(
        f"SPY >= +10% + Final Budget < 50  : "
        f"{very_strong_suppressed:,}"
    )

    lines.append(
        f"BAD market + Final Budget < 50   : "
        f"{bad_protected:,}"
    )

    if len(bad):

        lines.append(
            f"Bad-Market Protection Rate       : "
            f"{bad_protected / len(bad):.1%}"
        )

    lines.append("")

    lines.append(
        "=" * 82
    )

    lines.append(
        "TOP SUPPRESSORS — ALL HIGH70"
    )

    lines.append(
        "=" * 82
    )

    lines.append(
        all_attr[
            [
                "component",
                "mean_delta",
                "negative_days",
                "negative_day_rate",
            ]
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "=" * 82
    )

    lines.append(
        "TOP SUPPRESSORS — GOOD FORWARD"
    )

    lines.append(
        "=" * 82
    )

    lines.append(
        good_attr[
            [
                "component",
                "mean_delta",
                "negative_days",
                "negative_day_rate",
            ]
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "=" * 82
    )

    lines.append(
        "TOP SUPPRESSORS — BAD FORWARD"
    )

    lines.append(
        "=" * 82
    )

    lines.append(
        bad_attr[
            [
                "component",
                "mean_delta",
                "negative_days",
                "negative_day_rate",
            ]
        ]
        .head(10)
        .to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "=" * 82
    )

    lines.append(
        "GOOD vs BAD DELTA COMPARISON"
    )

    lines.append(
        "=" * 82
    )

    lines.append(
        comparison[
            [
                "component",
                "good_forward_mean_delta",
                "bad_forward_mean_delta",
                "good_minus_bad_delta",
            ]
        ]
        .to_string(
            index=False
        )
    )

    report = "\n".join(
        lines
    )

    SUMMARY_PATH.write_text(
        report,
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # 17. Terminal
    # --------------------------------------------------------

    print(report)

    print()
    print("Saved:")
    print(DETAIL_PATH)
    print(ATTRIBUTION_OUTPUT_PATH)
    print(SUMMARY_PATH)


if __name__ == "__main__":
    main()