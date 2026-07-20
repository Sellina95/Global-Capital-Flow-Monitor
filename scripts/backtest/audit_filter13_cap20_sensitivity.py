from pathlib import Path
import pandas as pd
import numpy as np

INPUT = Path(
    "data/backtest/results/filter13_phase_cap_effectiveness_daily.csv"
)

OUT_DAILY = Path(
    "data/backtest/results/filter13_cap20_sensitivity_daily.csv"
)

OUT_SUMMARY = Path(
    "data/backtest/results/filter13_cap20_sensitivity_summary.csv"
)

if not INPUT.exists():
    raise FileNotFoundError(INPUT)

df = pd.read_csv(INPUT)

# --------------------------------------------------
# Basic cleanup
# --------------------------------------------------
df["date"] = pd.to_datetime(df["date"], errors="coerce")

numeric_cols = [
    "pre_cap_budget",
    "phase_cap",
    "final_budget",
    "v2_cap",
    "final_cap",
    "spy_fwd_1d",
    "spy_fwd_5d",
    "spy_fwd_20d",
]

for c in numeric_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce")

# --------------------------------------------------
# Scope:
# Only days where Phase Cap itself was 20.
#
# IMPORTANT:
# This is NOT a proposed production rule.
# This is a counterfactual sensitivity test only.
# --------------------------------------------------
hard = df[df["phase_cap"] == 20].copy()

if hard.empty:
    raise RuntimeError("No phase_cap == 20 rows found.")

# --------------------------------------------------
# Episode persistence classification
#
# Consecutive CAP20 trading rows = same episode.
# ONE_DAY means episode length == 1.
# PERSISTENT means episode length >= 2.
# --------------------------------------------------
hard = hard.sort_values("date").copy()

all_dates = df.sort_values("date")["date"].tolist()
date_position = {d: i for i, d in enumerate(all_dates)}

episode_ids = []
episode_id = 0
prev_pos = None

for d in hard["date"]:
    pos = date_position.get(d)

    if prev_pos is None or pos != prev_pos + 1:
        episode_id += 1

    episode_ids.append(episode_id)
    prev_pos = pos

hard["episode_id_cf"] = episode_ids

episode_sizes = hard.groupby("episode_id_cf").size()

hard["episode_type"] = hard["episode_id_cf"].map(
    lambda x: "ONE_DAY" if episode_sizes.loc[x] == 1 else "PERSISTENT"
)

# --------------------------------------------------
# Trigger classification
# Diagnostic grouping only.
# --------------------------------------------------
def classify_trigger(row):
    macro = str(row.get("macro_narrative", "")).upper()

    if "CREDIT_STRESS" in macro:
        return "CREDIT_STRESS"

    if "TIGHTENING_GROWTH_SCARE" in macro:
        return "GROWTH_SCARE"

    if "STAGFLATION" in macro or "INFLATION" in macro:
        return "STAGFLATION_OR_INFLATION"

    return "OTHER"

hard["trigger"] = hard.apply(classify_trigger, axis=1)

# --------------------------------------------------
# Counterfactual budgets
#
# Key design:
# We only relax the PHASE CAP from 20 to candidate levels.
#
# Other existing caps are preserved.
# Therefore:
#
# CF budget = min(pre-cap budget,
#                 candidate phase cap,
#                 v2 cap)
#
# This avoids pretending that relaxing Phase Cap
# automatically removes Structural-v2 protection.
# --------------------------------------------------
candidate_caps = [20, 30, 35, 45]

for cap in candidate_caps:

    hard[f"cf{cap}_budget"] = np.minimum(
        hard["pre_cap_budget"],
        cap
    )

    if "v2_cap" in hard.columns:
        hard[f"cf{cap}_budget"] = np.minimum(
            hard[f"cf{cap}_budget"],
            hard["v2_cap"]
        )

# Current actual final budget remains source of truth.
hard["current_budget"] = hard["final_budget"]

# Exposure restored relative to actual current system.
for cap in [30, 35, 45]:
    hard[f"restore_{cap}"] = (
        hard[f"cf{cap}_budget"] - hard["current_budget"]
    )

# --------------------------------------------------
# Ex-post return effect
#
# Approximation:
# incremental exposure × forward SPY return
#
# IMPORTANT:
# This is NOT a full portfolio backtest.
# It measures directional sensitivity only.
# --------------------------------------------------
for horizon in [1, 5, 20]:

    ret_col = f"spy_fwd_{horizon}d"

    for cap in [30, 35, 45]:

        hard[f"effect_{cap}_{horizon}d"] = (
            hard[f"restore_{cap}"] / 100.0
        ) * hard[ret_col]

# --------------------------------------------------
# Summary helper
# --------------------------------------------------
def summarize(group, label):

    row = {
        "group": label,
        "days": len(group),
        "avg_pre_cap_budget": group["pre_cap_budget"].mean(),
        "avg_current_budget": group["current_budget"].mean(),
    }

    for cap in [30, 35, 45]:

        row[f"avg_cf{cap}_budget"] = group[
            f"cf{cap}_budget"
        ].mean()

        row[f"avg_restore_{cap}"] = group[
            f"restore_{cap}"
        ].mean()

        for horizon in [1, 5, 20]:

            effect = group[
                f"effect_{cap}_{horizon}d"
            ].dropna()

            row[
                f"avg_effect_{cap}_{horizon}d_pct"
            ] = (
                effect.mean() * 100
                if len(effect)
                else np.nan
            )

            row[
                f"total_effect_{cap}_{horizon}d_pct"
            ] = (
                effect.sum() * 100
                if len(effect)
                else np.nan
            )

    return row

summary_rows = []

# Overall
summary_rows.append(
    summarize(hard, "ALL_CAP20")
)

# Episode type
for name, g in hard.groupby("episode_type"):
    summary_rows.append(
        summarize(g, f"EPISODE_{name}")
    )

# Trigger
for name, g in hard.groupby("trigger"):
    summary_rows.append(
        summarize(g, f"TRIGGER_{name}")
    )

summary = pd.DataFrame(summary_rows)

# --------------------------------------------------
# Console output
# --------------------------------------------------
print()
print("=== FILTER13 CAP20 SENSITIVITY AUDIT ===")
print()

print("[CAP20 DAYS]")
print("DAYS:", len(hard))
print(
    "AVG PRE-CAP BUDGET:",
    round(hard["pre_cap_budget"].mean(), 3)
)
print(
    "AVG CURRENT BUDGET:",
    round(hard["current_budget"].mean(), 3)
)

print()
print("=== COUNTERFACTUAL AVERAGE BUDGET ===")

for cap in candidate_caps:
    print(
        f"CAP{cap}:",
        round(hard[f"cf{cap}_budget"].mean(), 3)
    )

print()
print("=== AVERAGE EXPOSURE RESTORED ===")

for cap in [30, 35, 45]:
    print(
        f"20 → {cap}:",
        round(hard[f"restore_{cap}"].mean(), 3),
        "%p"
    )

print()
print("=== EX-POST SENSITIVITY EFFECT ===")

for horizon in [1, 5, 20]:

    print()
    print(f"[T+{horizon}]")

    for cap in [30, 35, 45]:

        x = hard[
            f"effect_{cap}_{horizon}d"
        ].dropna()

        print(
            f"CAP{cap} | "
            f"VALID={len(x)} | "
            f"AVG={x.mean()*100:.4f}% | "
            f"TOTAL={x.sum()*100:.4f}%"
        )

print()
print("=== ONE-DAY vs PERSISTENT ===")

cols = [
    "group",
    "days",
    "avg_current_budget",
    "avg_cf30_budget",
    "avg_cf35_budget",
    "avg_cf45_budget",
    "total_effect_30_20d_pct",
    "total_effect_35_20d_pct",
    "total_effect_45_20d_pct",
]

print(
    summary[
        summary["group"].str.startswith("EPISODE_")
    ][cols].to_string(index=False)
)

print()
print("=== TRIGGER BREAKDOWN ===")

print(
    summary[
        summary["group"].str.startswith("TRIGGER_")
    ][cols].to_string(index=False)
)

# --------------------------------------------------
# Save
# --------------------------------------------------
OUT_DAILY.parent.mkdir(
    parents=True,
    exist_ok=True
)

hard.to_csv(
    OUT_DAILY,
    index=False
)

summary.to_csv(
    OUT_SUMMARY,
    index=False
)

print()
print("[SAVED]", OUT_DAILY)
print("[SAVED]", OUT_SUMMARY)

print()
print("AUDIT COMPLETE.")
print(
    "Counterfactual caps are sensitivity tests only, "
    "not production recommendations."
)
print(
    "Forward returns are EX-POST evaluation only."
)
