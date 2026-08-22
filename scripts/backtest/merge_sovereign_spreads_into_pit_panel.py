from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

PIT_DIR = ROOT / "data" / "backtest" / "pit_safe"
RESULTS = ROOT / "data" / "backtest" / "results"

PANEL_PATH = PIT_DIR / "master_panel_pit_safe.csv"
SPREAD_PATH = PIT_DIR / "sovereign_spreads_pit_safe_4.csv"

OUT = PIT_DIR / "master_panel_pit_safe_with_sovereign.csv"
SUMMARY = RESULTS / "pit_panel_sovereign_merge_summary.csv"

panel = pd.read_csv(PANEL_PATH)
spread = pd.read_csv(SPREAD_PATH)

panel["date"] = pd.to_datetime(
    panel["date"], errors="coerce"
).dt.normalize()

spread["date"] = pd.to_datetime(
    spread["date"], errors="coerce"
).dt.normalize()

SPREAD_COLS = [
    "KR10Y_SPREAD",
    "JP10Y_SPREAD",
    "DE10Y_SPREAD",
    "IL10Y_SPREAD",
]

# 기존 잘못된/구형 sovereign spread contract가 있으면 제거
drop_cols = [
    c for c in panel.columns
    if c in {
        "sovereign_spreads__KR_US_SPREAD",
        "sovereign_spreads__JP_US_SPREAD",
        "sovereign_spreads__DE_US_SPREAD",
        "sovereign_spreads__IL_US_SPREAD",
    }
]

if drop_cols:
    panel = panel.drop(columns=drop_cols)

right = spread[
    ["date"] + SPREAD_COLS
].copy()

panel = panel.merge(
    right,
    on="date",
    how="left",
)

# Production contract 이름 그대로 유지
panel = panel.sort_values("date").reset_index(drop=True)

panel.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig",
)

summary_rows = []

for col in SPREAD_COLS:
    x = panel[col]

    summary_rows.append({
        "series": col,
        "valid_rows": int(x.notna().sum()),
        "first_valid_date": panel.loc[x.notna(), "date"].min(),
        "last_valid_date": panel.loc[x.notna(), "date"].max(),
        "pre_2013_valid_rows": int(
            (
                (panel["date"] < pd.Timestamp("2013-06-03"))
                & x.notna()
            ).sum()
        ),
    })

summary = pd.DataFrame(summary_rows)

summary.to_csv(
    SUMMARY,
    index=False,
    encoding="utf-8-sig",
)

print("=" * 80)
print("PIT PANEL + SOVEREIGN SPREAD MERGE")
print("=" * 80)

print(summary.to_string(index=False))

print()
print(
    "PRE-2013 POPULATED:",
    int(summary["pre_2013_valid_rows"].sum()),
)

print("CANONICAL master_panel.csv MODIFIED: NO")
print("PRODUCTION MODIFIED: NO")

print()
print("[OUTPUT]")
print(OUT)
print(SUMMARY)
