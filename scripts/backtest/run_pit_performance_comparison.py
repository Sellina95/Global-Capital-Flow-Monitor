from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.backtest.performance as perf


RESULTS = ROOT / "data" / "backtest" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

CONTROL_POSITIONS = RESULTS / "daily_positions_geo_control.csv"
PIT_POSITIONS = RESULTS / "daily_positions_pit_safe_geo.csv"

CONTROL_DAILY = RESULTS / "daily_portfolio_geo_control.csv"
CONTROL_SUMMARY = RESULTS / "performance_summary_geo_control.csv"

PIT_DAILY = RESULTS / "daily_portfolio_pit_safe_geo.csv"
PIT_SUMMARY = RESULTS / "performance_summary_pit_safe_geo.csv"

PRICE_SNAPSHOT = RESULTS / "performance_price_snapshot_pit_comparison.csv"

COMPARE_OUT = RESULTS / "performance_pit_comparison.csv"


for p in [CONTROL_POSITIONS, PIT_POSITIONS]:
    if not p.exists():
        raise FileNotFoundError(p)


# ============================================================
# 1. Resolve one common execution period
# ============================================================

def execution_range(path: Path):
    df = pd.read_csv(path)

    if "execution_date" not in df.columns:
        raise RuntimeError(f"{path}: execution_date missing")

    if "status" in df.columns:
        df = df[df["status"].eq("OK")]

    d = pd.to_datetime(
        df["execution_date"],
        errors="coerce",
    ).dropna()

    if d.empty:
        raise RuntimeError(f"{path}: no valid execution dates")

    return d.min(), d.max()


c_start, c_end = execution_range(CONTROL_POSITIONS)
p_start, p_end = execution_range(PIT_POSITIONS)

common_start = min(c_start, p_start)
common_end = max(c_end, p_end)


# ============================================================
# 2. Freeze ONE common price snapshot
#
# Both performance runs must use exactly the same prices.
# ============================================================

original_price_path = perf.PRICE_PATH
original_loader = perf.load_or_download_prices

perf.PRICE_PATH = PRICE_SNAPSHOT

print("=" * 80)
print("FREEZING COMMON PERFORMANCE PRICE SNAPSHOT")
print("=" * 80)
print("Range:", common_start.date(), "->", common_end.date())

prices = original_loader(
    common_start,
    common_end,
)

print("Price rows:", len(prices))
print("Saved snapshot:", PRICE_SNAPSHOT)


def frozen_price_loader(start, end):
    # Same exact price dataframe for CONTROL and PIT.
    return prices.copy()


perf.load_or_download_prices = frozen_price_loader


# ============================================================
# 3. Run canonical performance.py unchanged in logic
# ============================================================

def run_case(
    label: str,
    positions_path: Path,
    daily_path: Path,
    summary_path: Path,
):
    print()
    print("=" * 80)
    print(label)
    print("=" * 80)
    print("Positions:", positions_path)

    perf.POSITIONS_PATH = positions_path
    perf.DAILY_PATH = daily_path
    perf.SUMMARY_PATH = summary_path

    perf.main()

    if not summary_path.exists():
        raise RuntimeError(
            f"{label}: summary not produced: {summary_path}"
        )

    out = pd.read_csv(summary_path)
    out.insert(0, "case", label)

    return out


try:
    control = run_case(
        "CONTROL_OLD_DATA_GEO",
        CONTROL_POSITIONS,
        CONTROL_DAILY,
        CONTROL_SUMMARY,
    )

    pit = run_case(
        "PIT_SAFE_DATA_GEO",
        PIT_POSITIONS,
        PIT_DAILY,
        PIT_SUMMARY,
    )

finally:
    perf.PRICE_PATH = original_price_path
    perf.load_or_download_prices = original_loader


# ============================================================
# 4. Side-by-side comparison
# ============================================================

comparison = pd.concat(
    [control, pit],
    ignore_index=True,
)

comparison.to_csv(
    COMPARE_OUT,
    index=False,
    encoding="utf-8-sig",
)


print()
print("=" * 100)
print("PIT-SAFE PERFORMANCE RE-BASELINE")
print("=" * 100)

print(comparison.to_string(index=False))

print()
print("IMPORTANT:")
print("- Same canonical performance.py")
print("- Same ETF price snapshot")
print("- Same 5 bps one-way trading cost")
print("- Same execution/return accounting")
print("- Difference comes from portfolio decisions, not performance formula")

print()
print("[OUTPUT]")
print(CONTROL_SUMMARY)
print(PIT_SUMMARY)
print(COMPARE_OUT)
