from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"

BASE = RESULTS / "daily_positions.csv"
PIT = RESULTS / "daily_positions_pit_safe_geo.csv"

OUT_DETAIL = RESULTS / "pit_safe_decision_impact_detail.csv"
OUT_SUMMARY = RESULTS / "pit_safe_decision_impact_summary.csv"

if not BASE.exists():
    raise FileNotFoundError(BASE)

if not PIT.exists():
    raise FileNotFoundError(PIT)

base = pd.read_csv(BASE)
pit = pd.read_csv(PIT)

# ------------------------------------------------------------
# Find common date key
# ------------------------------------------------------------

date_candidates = [
    "signal_date",
    "date",
    "execution_date",
]

date_col = next(
    (
        c for c in date_candidates
        if c in base.columns and c in pit.columns
    ),
    None,
)

if date_col is None:
    raise RuntimeError(
        "No common date column found.\n"
        f"BASE columns: {list(base.columns)}\n"
        f"PIT columns: {list(pit.columns)}"
    )

base[date_col] = pd.to_datetime(
    base[date_col], errors="coerce"
).dt.normalize()

pit[date_col] = pd.to_datetime(
    pit[date_col], errors="coerce"
).dt.normalize()


# ------------------------------------------------------------
# Resolve F13 / F15 / F18 output columns
# ------------------------------------------------------------

CONTRACTS = {
    "F13_RISK_BUDGET": [
        "risk_budget",
        "risk_budget_13",
        "RISK_BUDGET",
    ],
    "F15_EXPOSURE": [
        "final_exposure",
        "exposure",
        "exposure_15",
        "FINAL_EXPOSURE",
    ],
    "F18_ALLOCATED_EQUITY": [
        "allocated_equity",
        "allocated_equity_18",
        "ALLOCATED_EQUITY",
    ],
}


def resolve_column(df, candidates, label):
    for c in candidates:
        if c in df.columns:
            return c

    raise RuntimeError(
        f"{label}: output column not found.\n"
        f"Candidates: {candidates}\n"
        f"Available: {list(df.columns)}"
    )


resolved = {}

for label, candidates in CONTRACTS.items():
    resolved[label] = {
        "base": resolve_column(base, candidates, label),
        "pit": resolve_column(pit, candidates, label),
    }


# ------------------------------------------------------------
# Merge
# ------------------------------------------------------------

base_keep = [date_col] + [
    x["base"] for x in resolved.values()
]

pit_keep = [date_col] + [
    x["pit"] for x in resolved.values()
]

b = base[base_keep].copy()
p = pit[pit_keep].copy()

b = b.drop_duplicates(date_col, keep="last")
p = p.drop_duplicates(date_col, keep="last")

rename_b = {}
rename_p = {}

for label, cols in resolved.items():
    rename_b[cols["base"]] = f"{label}_BASE"
    rename_p[cols["pit"]] = f"{label}_PIT"

b = b.rename(columns=rename_b)
p = p.rename(columns=rename_p)

m = b.merge(
    p,
    on=date_col,
    how="inner",
)

if m.empty:
    raise RuntimeError("No overlapping replay dates.")


# ------------------------------------------------------------
# Compare decisions
# ------------------------------------------------------------

summary_rows = []

for label in CONTRACTS:

    bcol = f"{label}_BASE"
    pcol = f"{label}_PIT"

    m[bcol] = pd.to_numeric(
        m[bcol],
        errors="coerce",
    )

    m[pcol] = pd.to_numeric(
        m[pcol],
        errors="coerce",
    )

    delta = m[pcol] - m[bcol]

    m[f"{label}_DELTA"] = delta

    comparable = (
        m[bcol].notna()
        & m[pcol].notna()
    )

    changed = (
        comparable
        & ~np.isclose(
            m[bcol],
            m[pcol],
            rtol=0,
            atol=1e-10,
        )
    )

    n = int(comparable.sum())
    changed_n = int(changed.sum())

    summary_rows.append({
        "contract": label,
        "comparable_rows": n,
        "changed_rows": changed_n,
        "changed_pct": (
            changed_n / n * 100
            if n else np.nan
        ),
        "mean_abs_change": (
            float(delta[comparable].abs().mean())
            if n else np.nan
        ),
        "max_abs_change": (
            float(delta[comparable].abs().max())
            if n else np.nan
        ),
    })


summary = pd.DataFrame(summary_rows)

m.to_csv(
    OUT_DETAIL,
    index=False,
    encoding="utf-8-sig",
)

summary.to_csv(
    OUT_SUMMARY,
    index=False,
    encoding="utf-8-sig",
)


# ------------------------------------------------------------
# Overall affected dates
# ------------------------------------------------------------

delta_cols = [
    f"{label}_DELTA"
    for label in CONTRACTS
]

affected = pd.Series(
    False,
    index=m.index,
)

for col in delta_cols:
    affected |= (
        pd.to_numeric(
            m[col],
            errors="coerce",
        )
        .abs()
        .gt(1e-10)
    )

affected_rows = int(affected.sum())
total_rows = len(m)

print("=" * 80)
print("PIT-SAFE DECISION IMPACT AUDIT")
print("=" * 80)

print()
print("THIS IS NOT A RETURN / PERFORMANCE TEST.")
print("Question: Did removing unavailable future information change decisions?")
print()

print(summary.to_string(index=False))

print()
print("OVERLAPPING DATES:", total_rows)
print("ANY DECISION CHANGED:", affected_rows)
print(
    "AFFECTED DATE %:",
    round(affected_rows / total_rows * 100, 4)
    if total_rows else "N/A",
)

print()
print("[OUTPUT]")
print(OUT_DETAIL)
print(OUT_SUMMARY)
