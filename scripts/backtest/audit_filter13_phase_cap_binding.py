from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "data/backtest/results/filter13_budget_attribution_final_daily.csv"
)

OUT_DAILY = (
    ROOT
    / "data/backtest/results/filter13_phase_cap_binding_daily.csv"
)

OUT_SUMMARY = (
    ROOT
    / "data/backtest/results/filter13_phase_cap_binding_summary.csv"
)


# ============================================================
# Load verified PIT attribution output
# ============================================================

d = pd.read_csv(INPUT)

d["date"] = pd.to_datetime(
    d["date"],
    errors="coerce",
)

numeric_cols = [
    "base_budget",
    "pre_cap_budget",
    "phase_cap",
    "phase_cap_effect",
    "final_budget",
]

for c in numeric_cols:
    d[c] = pd.to_numeric(
        d[c],
        errors="coerce",
    )


# ============================================================
# Binding definition
#
# A Phase Cap is "binding" only when it actually reduces
# pre-cap budget.
#
# Example:
# pre_cap=70, cap=20 -> binding, cut=-50
# pre_cap=15, cap=20 -> NOT binding
# ============================================================

d["cap_binding"] = (
    d["phase_cap_effect"] < 0
)

d["exposure_removed"] = (
    -d["phase_cap_effect"]
).clip(lower=0)


# ============================================================
# Basic summary by exact cap
# ============================================================

rows = []

total_days = len(d)

for cap, g in d.groupby(
    "phase_cap",
    dropna=False,
):

    active = g[
        g["cap_binding"]
    ].copy()

    rows.append(
        {
            "phase_cap": cap,

            "days_regime_cap_present":
                len(g),

            "share_of_all_days_pct":
                len(g)
                / total_days
                * 100
                if total_days
                else np.nan,

            "binding_days":
                len(active),

            "binding_rate_within_cap_pct":
                len(active)
                / len(g)
                * 100
                if len(g)
                else np.nan,

            "total_exposure_removed_pct_points":
                active[
                    "exposure_removed"
                ].sum(),

            "avg_exposure_removed_when_binding":
                active[
                    "exposure_removed"
                ].mean()
                if len(active)
                else 0.0,

            "max_single_day_exposure_removed":
                active[
                    "exposure_removed"
                ].max()
                if len(active)
                else 0.0,

            "avg_pre_cap_budget":
                g[
                    "pre_cap_budget"
                ].mean(),

            "avg_final_budget":
                g[
                    "final_budget"
                ].mean(),
        }
    )

summary = pd.DataFrame(rows)


# ============================================================
# Rank caps by total exposure destruction
# ============================================================

summary = (
    summary
    .sort_values(
        "total_exposure_removed_pct_points",
        ascending=False,
    )
    .reset_index(drop=True)
)

summary[
    "exposure_removal_rank"
] = np.arange(
    1,
    len(summary) + 1,
)


total_removed = (
    summary[
        "total_exposure_removed_pct_points"
    ].sum()
)

if total_removed > 0:

    summary[
        "share_of_total_removed_pct"
    ] = (
        summary[
            "total_exposure_removed_pct_points"
        ]
        / total_removed
        * 100
    )

else:

    summary[
        "share_of_total_removed_pct"
    ] = 0.0


# ============================================================
# Regime × Cap attribution
# ============================================================

binding = d[
    d["cap_binding"]
].copy()

if not binding.empty:

    regime_summary = (
        binding
        .groupby(
            [
                "market_regime",
                "phase_cap",
            ],
            dropna=False,
        )
        .agg(
            binding_days=(
                "date",
                "count",
            ),

            total_exposure_removed=(
                "exposure_removed",
                "sum",
            ),

            avg_exposure_removed=(
                "exposure_removed",
                "mean",
            ),

            avg_pre_cap_budget=(
                "pre_cap_budget",
                "mean",
            ),

            avg_final_budget=(
                "final_budget",
                "mean",
            ),
        )
        .reset_index()
        .sort_values(
            "total_exposure_removed",
            ascending=False,
        )
    )

else:

    regime_summary = pd.DataFrame()


# ============================================================
# Daily diagnostic
# ============================================================

daily_cols = [
    "date",
    "pit_status",
    "market_regime",
    "macro_narrative",
    "base_budget",
    "macro_delta",
    "pre_cap_budget",
    "phase_cap",
    "phase_cap_effect",
    "cap_binding",
    "exposure_removed",
    "final_budget",
]

daily_cols = [
    c
    for c in daily_cols
    if c in d.columns
]

daily = (
    d[daily_cols]
    .sort_values(
        "date"
    )
)


# ============================================================
# Print
# ============================================================

print(
    "\n=== FILTER13 PHASE CAP "
    "BINDING AUDIT ==="
)

print("\n[PERIOD]")

print(
    "ROWS:",
    len(d),
)

print(
    "FROM:",
    d["date"].min().date(),
)

print(
    "TO  :",
    d["date"].max().date(),
)


print(
    "\n[OVERALL]"
)

print(
    "TOTAL DAYS:",
    len(d),
)

print(
    "BINDING DAYS:",
    int(
        d[
            "cap_binding"
        ].sum()
    ),
)

print(
    "BINDING RATE:",
    round(
        d[
            "cap_binding"
        ].mean()
        * 100,
        1,
    ),
    "%",
)

print(
    "TOTAL EXPOSURE REMOVED:",
    round(
        d[
            "exposure_removed"
        ].sum(),
        3,
    ),
    "%p-days",
)

print(
    "AVG DAILY EXPOSURE REMOVED:",
    round(
        d[
            "exposure_removed"
        ].mean(),
        3,
    ),
    "%p",
)


print(
    "\n=== CAP RANKING BY TOTAL "
    "EXPOSURE REMOVED ==="
)

show_cols = [
    "exposure_removal_rank",
    "phase_cap",
    "days_regime_cap_present",
    "binding_days",
    "binding_rate_within_cap_pct",
    "total_exposure_removed_pct_points",
    "share_of_total_removed_pct",
    "avg_exposure_removed_when_binding",
]

print(
    summary[
        show_cols
    ].to_string(
        index=False
    )
)


print(
    "\n=== REGIME × CAP "
    "EXPOSURE DESTRUCTION ==="
)

if regime_summary.empty:

    print("NONE")

else:

    print(
        regime_summary.to_string(
            index=False
        )
    )


print(
    "\n=== TOP 20 LARGEST "
    "SINGLE-DAY CAP CUTS ==="
)

top = (
    daily[
        daily[
            "cap_binding"
        ]
    ]
    .sort_values(
        "exposure_removed",
        ascending=False,
    )
    .head(20)
)

print(
    top.to_string(
        index=False
    )
)


# ============================================================
# Save
# ============================================================

daily.to_csv(
    OUT_DAILY,
    index=False,
)

summary.to_csv(
    OUT_SUMMARY,
    index=False,
)

print(
    "\n[SAVED]",
    OUT_DAILY,
)

print(
    "[SAVED]",
    OUT_SUMMARY,
)

print(
    "\nPHASE CAP BINDING AUDIT COMPLETE."
)

print(
    "No production Filter13 logic was modified."
)