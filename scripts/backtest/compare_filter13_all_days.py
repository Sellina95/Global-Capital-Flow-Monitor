from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

for p in (ROOT, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from scripts.backtest.market_data_builder import build_market_data
import filters.strategist_filters as sf
from scripts.backtest.audit_filter13_budget_audit import audit_filter13_budget

panel = pd.read_csv(ROOT / "data/backtest/master_panel.csv")
panel["date"] = pd.to_datetime(panel["date"])

bt = pd.read_csv(ROOT / "data/backtest/results/daily_positions.csv")
bt["signal_date"] = pd.to_datetime(bt["signal_date"])

for i in range(len(panel)):

    market_data = build_market_data(panel, i)

    sf.narrative_engine_filter(market_data)
    prod = market_data["RISK_BUDGET"]

    row = bt.loc[
        bt["signal_date"] == panel.iloc[i]["date"]
    ]

    if row.empty:
        continue

    saved = row.iloc[0]["risk_budget_13"]

    if int(prod) != int(saved):
        print("=" * 80)
        print("FIRST DIFFERENCE")
        print("DATE       :", panel.iloc[i]["date"])
        print("PRODUCTION :", prod)
        print("CSV        :", saved)
        break

else:
    print("ALL MATCH")