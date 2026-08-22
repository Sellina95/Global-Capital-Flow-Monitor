from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"

# B = 기존 데이터 + GEO
CONTROL = RESULTS / "daily_positions_geo_control.csv"

# C = PIT-safe 데이터 + GEO
PIT = RESULTS / "daily_positions_pit_safe_geo.csv"

OUT_DETAIL = RESULTS / "pit_only_decision_impact_detail.csv"
OUT_SUMMARY = RESULTS / "pit_only_decision_impact_summary.csv"

for p in [CONTROL, PIT]:
    if not p.exists():
        raise FileNotFoundError(p)

control = pd.read_csv(CONTROL)
pit = pd.read_csv(PIT)

control["signal_date"] = pd.to_datetime(
    control["signal_date"], errors="coerce"
).dt.normalize()

pit["signal_date"] = pd.to_datetime(
    pit["signal_date"], errors="coerce"
).dt.normalize()

cols = [
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
]

for col in cols:
    if col not in control.columns:
        raise RuntimeError(f"CONTROL missing: {col}")
    if col not in pit.columns:
        raise RuntimeError(f"PIT missing: {col}")

c = control[["signal_date"] + cols].copy()
p = pit[["signal_date"] + cols].copy()

c = c.rename(columns={x: f"{x}_CONTROL" for x in cols})
p = p.rename(columns={x: f"{x}_PIT" for x in cols})

m = c.merge(
    p,
    on="signal_date",
    how="inner",
)

summary_rows = []
any_changed = pd.Series(False, index=m.index)

for col in cols:

    a = pd.to_numeric(
        m[f"{col}_CONTROL"],
        errors="coerce",
    )

    b = pd.to_numeric(
        m[f"{col}_PIT"],
        errors="coerce",
    )

    comparable = a.notna() & b.notna()

    changed = (
        comparable
        & ~np.isclose(
            a,
            b,
            rtol=0,
            atol=1e-10,
        )
    )

    delta = b - a
    m[f"{col}_delta"] = delta

    any_changed |= changed

    n = int(comparable.sum())
    changed_n = int(changed.sum())

    summary_rows.append({
        "contract": col,
        "comparable_rows": n,
        "changed_rows": changed_n,
        "changed_pct": changed_n / n * 100 if n else np.nan,
        "mean_abs_change": float(delta[comparable].abs().mean()) if n else np.nan,
        "max_abs_change": float(delta[comparable].abs().max()) if n else np.nan,
    })

summary = pd.DataFrame(summary_rows)

affected = int(any_changed.sum())
total = len(m)

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

print("=" * 80)
print("PURE PIT / LOOK-AHEAD DECISION IMPACT")
print("=" * 80)
print()
print("CONTROL = OLD DATA + GEO")
print("PIT     = PIT-SAFE DATA + GEO")
print()
print(summary.to_string(index=False))
print()
print("OVERLAPPING DATES:", total)
print("ANY DECISION CHANGED:", affected)
print(
    "AFFECTED DATE %:",
    round(affected / total * 100, 4)
    if total else "N/A",
)
print()
print("[OUTPUT]")
print(OUT_DETAIL)
print(OUT_SUMMARY)
