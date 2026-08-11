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

DETAIL_PATH = (
    RESULT_DIR
    / "filter13_phase_macro_interaction_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_phase_macro_interaction_summary.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter13_phase_macro_interaction_summary.txt"
)


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


def safe_rate(
    condition: pd.Series,
) -> float:

    if len(condition) == 0:
        return np.nan

    return float(
        condition.mean()
    )


def summarize_group(
    group: pd.DataFrame,
    interaction_group: str,
) -> dict:

    r20 = pd.to_numeric(
        group["spy_return_20d"],
        errors="coerce",
    ).dropna()

    r60 = pd.to_numeric(
        group["spy_return_60d"],
        errors="coerce",
    ).dropna()

    return {
        "interaction_group":
            interaction_group,

        "days":
            len(group),

        "share_of_high70":
            np.nan,

        "avg_base_budget":
            group["base_budget"].mean(),

        "avg_pre_cap_budget":
            group["pre_cap_budget"].mean(),

        "avg_final_budget":
            group["final_budget"].mean(),

        "avg_total_suppression":
            (
                group["base_budget"]
                - group["final_budget"]
            ).mean(),

        "avg_macro_delta":
            group["macro_delta"].mean(),

        "avg_phase_cap_effect":
            group["phase_cap_effect"].mean(),

        "avg_macro_plus_phase":
            (
                group["macro_delta"]
                + group["phase_cap_effect"]
            ).mean(),

        "macro_cut_rate":
            safe_rate(
                group["macro_delta"] < 0
            ),

        "phase_cap_rate":
            safe_rate(
                group["phase_cap_effect"] < 0
            ),

        # ----------------------------------------------------
        # 20D outcome
        # ----------------------------------------------------

        "avg_spy_20d":
            r20.mean()
            if len(r20)
            else np.nan,

        "median_spy_20d":
            r20.median()
            if len(r20)
            else np.nan,

        "positive_20d_rate":
            safe_rate(
                r20 > 0
            ),

        # ----------------------------------------------------
        # 60D outcome
        # ----------------------------------------------------

        "avg_spy_60d":
            r60.mean()
            if len(r60)
            else np.nan,

        "median_spy_60d":
            r60.median()
            if len(r60)
            else np.nan,

        "positive_60d_rate":
            safe_rate(
                r60 > 0
            ),

        "negative_60d_rate":
            safe_rate(
                r60 < 0
            ),

        "good_forward_rate":
            safe_rate(
                r60 >= 5
            ),

        "very_good_forward_rate":
            safe_rate(
                r60 >= 10
            ),

        "bad_forward_rate":
            safe_rate(
                r60 <= -5
            ),

        "worst_60d":
            r60.min()
            if len(r60)
            else np.nan,

        "best_60d":
            r60.max()
            if len(r60)
            else np.nan,
    }


# ============================================================
# Main
# ============================================================

def main() -> None:

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

    # ========================================================
    # Contract checks
    # ========================================================

    required_audit = {
        "date",
        "base_budget",
        "pre_cap_budget",
        "final_budget",
        "macro_delta",
        "phase_cap",
        "phase_cap_effect",
        "market_regime",
        "macro_narrative",
    }

    missing = (
        required_audit
        - set(audit.columns)
    )

    if missing:
        raise ValueError(
            "Missing attribution columns: "
            f"{sorted(missing)}"
        )

    if (
        "signal_date" not in panel.columns
        or "SPY" not in panel.columns
    ):
        raise ValueError(
            "master_panel.csv must contain "
            "signal_date and SPY"
        )

    # ========================================================
    # Dates
    # ========================================================

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

    # ========================================================
    # Numeric
    # ========================================================

    numeric_cols = [
        "base_budget",
        "pre_cap_budget",
        "final_budget",
        "macro_delta",
        "phase_cap",
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

    # ========================================================
    # Forward returns — evaluation only
    # ========================================================

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

    # ========================================================
    # HIGH-70 universe only
    # ========================================================

    high70 = df[
        df["base_budget"]
        .round()
        .eq(70)
    ].copy()

    if high70.empty:
        raise ValueError(
            "No Base Budget = 70 rows found."
        )

    # ========================================================
    # Macro / Phase active flags
    # ========================================================

    high70["macro_cut"] = (
        high70["macro_delta"] < 0
    )

    high70["phase_cap_cut"] = (
        high70["phase_cap_effect"] < 0
    )

    # ========================================================
    # Interaction Group
    # ========================================================

    high70["interaction_group"] = np.select(
        [
            (
                high70["macro_cut"]
                &
                high70["phase_cap_cut"]
            ),
            (
                high70["macro_cut"]
                &
                ~high70["phase_cap_cut"]
            ),
            (
                ~high70["macro_cut"]
                &
                high70["phase_cap_cut"]
            ),
            (
                ~high70["macro_cut"]
                &
                ~high70["phase_cap_cut"]
            ),
        ],
        [
            "BOTH_CUT",
            "MACRO_ONLY",
            "PHASE_ONLY",
            "NEITHER",
        ],
        default="UNKNOWN",
    )

    # ========================================================
    # Forward labels
    # ========================================================

    high70["forward_group"] = np.select(
        [
            high70["spy_return_60d"] >= 5,
            high70["spy_return_60d"] <= -5,
        ],
        [
            "GOOD_FORWARD",
            "BAD_FORWARD",
        ],
        default="OTHER_FORWARD",
    )

    high70.loc[
        high70["spy_return_60d"].isna(),
        "forward_group",
    ] = "NO_FORWARD_DATA"

    # ========================================================
    # Suppression fields
    # ========================================================

    high70["total_suppression"] = (
        high70["base_budget"]
        - high70["final_budget"]
    )

    high70["macro_phase_combined_delta"] = (
        high70["macro_delta"]
        + high70["phase_cap_effect"]
    )

    high70["strong_market_suppressed"] = (
        high70["spy_return_60d"].ge(5)
        &
        high70["final_budget"].lt(50)
    )

    # ========================================================
    # Group Summary
    # ========================================================

    ordered_groups = [
        "BOTH_CUT",
        "MACRO_ONLY",
        "PHASE_ONLY",
        "NEITHER",
    ]

    summary_rows = []

    for name in ordered_groups:

        group = high70[
            high70["interaction_group"]
            == name
        ].copy()

        if group.empty:
            continue

        summary_rows.append(
            summarize_group(
                group,
                name,
            )
        )

    summary = pd.DataFrame(
        summary_rows
    )

    if not summary.empty:

        summary["share_of_high70"] = (
            summary["days"]
            / summary["days"].sum()
        )

    # ========================================================
    # Good Forward specific interaction
    # ========================================================

    good = high70[
        high70["forward_group"]
        == "GOOD_FORWARD"
    ].copy()

    bad = high70[
        high70["forward_group"]
        == "BAD_FORWARD"
    ].copy()

    good_counts = (
        good["interaction_group"]
        .value_counts()
    )

    bad_counts = (
        bad["interaction_group"]
        .value_counts()
    )

    # ========================================================
    # Diagnostic table:
    # each interaction group's good / bad share
    # ========================================================

    outcome_rows = []

    for name in ordered_groups:

        group = high70[
            high70["interaction_group"]
            == name
        ].copy()

        valid = group[
            group["spy_return_60d"]
            .notna()
        ].copy()

        if len(valid) == 0:
            continue

        outcome_rows.append(
            {
                "interaction_group":
                    name,

                "valid_days":
                    len(valid),

                "good_days":
                    int(
                        (
                            valid["spy_return_60d"]
                            >= 5
                        ).sum()
                    ),

                "bad_days":
                    int(
                        (
                            valid["spy_return_60d"]
                            <= -5
                        ).sum()
                    ),

                "good_rate":
                    (
                        valid["spy_return_60d"]
                        >= 5
                    ).mean(),

                "bad_rate":
                    (
                        valid["spy_return_60d"]
                        <= -5
                    ).mean(),

                "avg_spy_60d":
                    valid[
                        "spy_return_60d"
                    ].mean(),

                "avg_final_budget":
                    valid[
                        "final_budget"
                    ].mean(),

                "avg_macro_delta":
                    valid[
                        "macro_delta"
                    ].mean(),

                "avg_phase_cap_effect":
                    valid[
                        "phase_cap_effect"
                    ].mean(),

                "avg_combined_delta":
                    valid[
                        "macro_phase_combined_delta"
                    ].mean(),
            }
        )

    outcome_summary = pd.DataFrame(
        outcome_rows
    )

    # ========================================================
    # Save Detail
    # ========================================================

    detail_cols = [
        "signal_date",
        "base_budget",
        "pre_cap_budget",
        "final_budget",
        "macro_delta",
        "phase_cap",
        "phase_cap_effect",
        "macro_phase_combined_delta",
        "macro_cut",
        "phase_cap_cut",
        "interaction_group",
        "market_regime",
        "macro_narrative",
        "spy_return_20d",
        "spy_return_60d",
        "forward_group",
        "strong_market_suppressed",
        "total_suppression",
    ]

    high70[
        detail_cols
    ].to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Combined CSV Summary
    # ========================================================

    summary_export = (
        summary.copy()
    )

    summary_export["section"] = (
        "INTERACTION_SUMMARY"
    )

    outcome_export = (
        outcome_summary.copy()
    )

    outcome_export["section"] = (
        "OUTCOME_SUMMARY"
    )

    all_columns = sorted(
        set(
            summary_export.columns
        )
        |
        set(
            outcome_export.columns
        )
    )

    combined = pd.concat(
        [
            summary_export.reindex(
                columns=all_columns
            ),
            outcome_export.reindex(
                columns=all_columns
            ),
        ],
        ignore_index=True,
    )

    combined.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Text Report
    # ========================================================

    valid = high70[
        high70["spy_return_60d"]
        .notna()
    ]

    both = high70[
        high70["interaction_group"]
        == "BOTH_CUT"
    ]

    both_good = both[
        both["spy_return_60d"]
        >= 5
    ]

    both_bad = both[
        both["spy_return_60d"]
        <= -5
    ]

    good_suppressed = good[
        good["final_budget"] < 50
    ]

    both_good_suppressed = (
        both_good[
            both_good["final_budget"]
            < 50
        ]
    )

    lines = []

    lines.append(
        "=" * 84
    )

    lines.append(
        "FILTER13 PHASE ↔ MACRO INTERACTION AUDIT"
    )

    lines.append(
        "=" * 84
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
        "Interaction Distribution"
    )

    lines.append(
        "------------------------"
    )

    for name in ordered_groups:

        n = int(
            (
                high70["interaction_group"]
                == name
            ).sum()
        )

        lines.append(
            f"{name:12s}: "
            f"{n:,} "
            f"({n / len(high70):.1%})"
        )

    lines.append("")

    lines.append(
        "Interaction Summary"
    )

    lines.append(
        "-------------------"
    )

    lines.append(
        summary[
            [
                "interaction_group",
                "days",
                "avg_final_budget",
                "avg_total_suppression",
                "avg_macro_delta",
                "avg_phase_cap_effect",
                "avg_macro_plus_phase",
                "avg_spy_60d",
                "good_forward_rate",
                "bad_forward_rate",
            ]
        ]
        .to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "Outcome Summary"
    )

    lines.append(
        "---------------"
    )

    lines.append(
        outcome_summary[
            [
                "interaction_group",
                "valid_days",
                "good_days",
                "bad_days",
                "good_rate",
                "bad_rate",
                "avg_spy_60d",
                "avg_final_budget",
                "avg_macro_delta",
                "avg_phase_cap_effect",
            ]
        ]
        .to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "Good Forward Distribution"
    )

    lines.append(
        "-------------------------"
    )

    for name in ordered_groups:

        n = int(
            good_counts.get(
                name,
                0,
            )
        )

        lines.append(
            f"{name:12s}: "
            f"{n:,} "
            f"({n / len(good):.1%})"
            if len(good)
            else f"{name}: N/A"
        )

    lines.append("")

    lines.append(
        "Bad Forward Distribution"
    )

    lines.append(
        "------------------------"
    )

    for name in ordered_groups:

        n = int(
            bad_counts.get(
                name,
                0,
            )
        )

        lines.append(
            f"{name:12s}: "
            f"{n:,} "
            f"({n / len(bad):.1%})"
            if len(bad)
            else f"{name}: N/A"
        )

    lines.append("")

    lines.append(
        "=" * 84
    )

    lines.append(
        "DOUBLE-PENALTY DIAGNOSTICS"
    )

    lines.append(
        "=" * 84
    )

    lines.append(
        f"BOTH_CUT Days                    : "
        f"{len(both):,}"
    )

    lines.append(
        f"BOTH_CUT + GOOD_FORWARD          : "
        f"{len(both_good):,}"
    )

    lines.append(
        f"BOTH_CUT + BAD_FORWARD           : "
        f"{len(both_bad):,}"
    )

    if len(good):

        lines.append(
            f"Share of GOOD_FORWARD in BOTH    : "
            f"{len(both_good) / len(good):.1%}"
        )

    if len(bad):

        lines.append(
            f"Share of BAD_FORWARD in BOTH     : "
            f"{len(both_bad) / len(bad):.1%}"
        )

    lines.append(
        f"GOOD_FORWARD Final<50            : "
        f"{len(good_suppressed):,}"
    )

    lines.append(
        f"GOOD + BOTH_CUT + Final<50       : "
        f"{len(both_good_suppressed):,}"
    )

    if len(good_suppressed):

        lines.append(
            f"Share of suppressed GOOD due BOTH: "
            f"{len(both_good_suppressed) / len(good_suppressed):.1%}"
        )

    lines.append("")

    lines.append(
        "Interpretation Rule:"
    )

    lines.append(
        "- BOTH_CUT dominates GOOD_FORWARD suppression "
        "→ possible Macro/Phase double penalty."
    )

    lines.append(
        "- BOTH_CUT dominates BAD_FORWARD but not GOOD "
        "→ interaction may be valid risk protection."
    )

    lines.append(
        "- PHASE_ONLY or MACRO_ONLY independently show poor "
        "forward outcomes → single layer may be informative."
    )

    report = "\n".join(
        lines
    )

    TEXT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print(report)

    print()
    print("Saved:")
    print(DETAIL_PATH)
    print(SUMMARY_PATH)
    print(TEXT_PATH)


if __name__ == "__main__":
    main()