from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULT = ROOT / "data/backtest/results"

df = pd.read_csv(RESULT / "daily_positions.csv")

df["signal_date"] = pd.to_datetime(df["signal_date"])
df["year"] = df["signal_date"].dt.year

df["cut_13_15"] = df["risk_budget_13"] - df["exposure_15"]
df["cut_15_18"] = df["exposure_15"] - df["allocated_equity_18"]

summary = (
    df.groupby("year")
      .agg(
          days=("year","count"),
          budget13=("risk_budget_13","mean"),
          exposure15=("exposure_15","mean"),
          allocation18=("allocated_equity_18","mean"),
          cut13_15=("cut_13_15","mean"),
          cut15_18=("cut_15_18","mean"),
          hard_deadman=("sew_status", lambda x:(x=="HARD_DEADMAN").sum()),
          compression=("sew_status", lambda x:(x=="RISK_COMPRESSION").sum()),
      )
      .round(2)
)

print("="*80)
print("ALPHA DIAGNOSTICS")
print("="*80)
print(summary)

summary.to_csv(
    RESULT / "alpha_diagnostics_summary.csv",
    encoding="utf-8-sig"
)

print("\nSaved:")
print(RESULT / "alpha_diagnostics_summary.csv")
