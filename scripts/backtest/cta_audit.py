

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "data" / "backtest" / "results"

df = pd.read_csv(RESULT / "daily_positions.csv")

df["signal_date"] = pd.to_datetime(df["signal_date"])

cols = [
    "signal_date",
    "cta_momentum_score",
    "exposure_15",
    "risk_budget_13",
    "sew_status",
    "brake_drivers",
]

cols = [c for c in cols if c in df.columns]

cta = df[cols].copy()

print("=" * 80)
print("CTA AUDIT")
print("=" * 80)

if "cta_momentum_score" in cta.columns:
    print(cta["cta_momentum_score"].describe())

    print("\nValue Counts (rounded)")
    print(
        cta["cta_momentum_score"]
        .round(1)
        .value_counts()
        .sort_index()
    )

print("\nFirst 20 rows")
print(cta.head(20).to_string(index=False))

cta.to_csv(
    RESULT / "cta_audit.csv",
    index=False,
    encoding="utf-8-sig",
)

print("\nSaved:")
print(RESULT / "cta_audit.csv")