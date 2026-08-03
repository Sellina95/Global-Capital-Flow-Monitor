from pathlib import Path
import difflib

ROOT = Path(__file__).resolve().parents[2]

prod = ROOT / "filters" / "strategist_filters.py"
audit = ROOT / "scripts" / "backtest" / "audit_filter13_budget_audit.py"

prod_text = prod.read_text(encoding="utf-8", errors="ignore")
audit_text = audit.read_text(encoding="utf-8", errors="ignore")

markers = [
    ("Base", "Base from sentiment", "base_budget"),
    ("Structure", "Structure tilt", "Structure Tilt"),
    ("Credit", "Credit tilt", "Credit"),
    ("Liquidity", "Liquidity tilt", "Liquidity"),
    ("Structural_v2", "Structural v2", "Structural v2"),
    ("Drift", "Drift Adjustment", "Drift"),
    ("FlowGamma", "Flow / Gamma", "Flow Gamma"),
    ("FlowContinuity", "Flow Continuity", "Flow Continuity"),
    ("FlowRegime", "Flow Regime", "Flow Regime"),
    ("Macro", "Macro Narrative", "Macro"),
    ("Positioning", "Positioning", "Positioning"),
    ("EventFloor", "Event-Watching Floor", "Event Floor"),
    ("PhaseCap", "Phase Cap", "Phase Cap"),
]

for name, prod_key, audit_key in markers:

    p = prod_text.find(prod_key)
    a = audit_text.find(audit_key)

    print("=" * 80)
    print(name)

    if p == -1:
        print("❌ Production section not found:", prod_key)
        continue

    if a == -1:
        print("❌ Audit section not found:", audit_key)
        continue

    prod_chunk = prod_text[p:p+1200].splitlines()
    audit_chunk = audit_text[a:a+1200].splitlines()

    diff = list(
        difflib.unified_diff(
            audit_chunk,
            prod_chunk,
            fromfile="Audit",
            tofile="Production",
            lineterm=""
        )
    )

    if not diff:
        print("✅ IDENTICAL")
    else:
        print("❌ DIFFERENT")
        print("\n".join(diff[:120]))