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

from scripts.backtest.audit_filter13_budget_audit import (
    audit_filter13_budget,
)

ROOT = Path(__file__).resolve().parents[2]

panel = pd.read_csv(ROOT / "data/backtest/master_panel.csv")
panel["date"] = pd.to_datetime(panel["date"])

# ===== 원하는 날짜 =====
DATE = "2008-12-02"
# ======================

idx = panel.index[
    panel["date"] == pd.Timestamp(DATE)
][0]

market_data = build_market_data(
    panel,
    idx,
)

# -------------------------
# Production
# -------------------------
sf.narrative_engine_filter(market_data)

prod = {
    "RISK_BUDGET": market_data.get("RISK_BUDGET"),
    "PRE_CAP": market_data.get("PRE_CAP_BUDGET"),
    "CAP": market_data.get("PHASE_CAP"),
}

# -------------------------
# Audit
# -------------------------
audit = audit_filter13_budget(market_data)

print("=" * 80)
print(DATE)
print("=" * 80)

print("\nPRODUCTION")
for k, v in prod.items():
    print(f"{k:25s}: {v}")

print("\nAUDIT")

keys = [
    "base_budget",
    "structure_after",
    "credit_after",
    "liquidity_after",
    "structural_v2_after",
    "drift_after",
    "flow_gamma_after",
    "flow_continuity_after",
    "flow_regime_after",
    "macro_after",
    "positioning_after",
    "event_floor_after",
    "final_budget",
]

for k in keys:
    print(f"{k:25s}: {audit.get(k)}")