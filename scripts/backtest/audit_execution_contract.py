from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

FILTER_FILE = ROOT / "filters" / "strategist_filters.py"
RUN_FILE = ROOT / "scripts" / "backtest" / "run_backtest.py"

filter_text = FILTER_FILE.read_text(encoding="utf-8")
run_text = RUN_FILE.read_text(encoding="utf-8")

print("=" * 60)
print("EXECUTION CONTRACT AUDIT")
print("=" * 60)

# ---------------------------------------------------
# Production execution chain
# ---------------------------------------------------

prod_generators = re.findall(
    r"sections\.append\((\w+)\(market_data\)\)",
    filter_text,
)

prod_generators = [
    x for x in prod_generators
    if x != "narrative_engine_filter"
]

# ---------------------------------------------------
# Backtest sf execution
# ---------------------------------------------------

backtest_sf = re.findall(
    r"sf\.(\w+)\(",
    run_text,
)

backtest_sf = [
    x for x in backtest_sf
    if x != "build_tactical_allocation"
]

# ---------------------------------------------------
# Attach Layer
# ---------------------------------------------------

attach_layers = re.findall(
    r"(attach_\w+)\(",
    run_text,
)

print()

print("Production Generators")
print("-" * 60)

missing = []

for g in prod_generators:

    if g in backtest_sf:

        print(f"✓ {g}")

    else:

        print(f"✗ {g}")

        missing.append(g)

print()

print("Backtest Attach Layer")
print("-" * 60)

for a in attach_layers:

    print(f"• {a}")

print()

print("Narrative Consumer")
print("-" * 60)

consumer = sorted(set(re.findall(
    r'market_data\.get\("([^"]+)"',
    filter_text[
        filter_text.find("def narrative_engine_filter"):
        filter_text.find("def volatility_controlled_exposure_filter")
    ]
)))

for c in consumer:

    print(c)

print()

print("=" * 60)
print("Missing Generators")
print("=" * 60)

for g in missing:

    print(g)

print()
print("Audit Complete")