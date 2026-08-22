from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data" / "backtest"
PIT = DATA / "pit_safe"
RESULTS = DATA / "results"

SOV4 = PIT / "sovereign_yields_pit_4.csv"
PANEL = PIT / "master_panel_pit_safe.csv"

OUT = PIT / "sovereign_spreads_pit_safe_4.csv"
SUMMARY = RESULTS / "sovereign_spreads_pit_safe_4_summary.csv"

if not SOV4.exists():
    raise FileNotFoundError(SOV4)

if not PANEL.exists():
    raise FileNotFoundError(PANEL)


# ============================================================
# 1. Load PIT-safe sovereign 4
# ============================================================

sov = pd.read_csv(SOV4)

sov["date"] = pd.to_datetime(
    sov["date"],
    errors="coerce",
).dt.normalize()

sov = (
    sov.dropna(subset=["date"])
    .sort_values("date")
    .drop_duplicates("date", keep="last")
)


# ============================================================
# 2. Load already repaired PIT-safe US10Y
# ============================================================

panel = pd.read_csv(PANEL)

panel["date"] = pd.to_datetime(
    panel["date"],
    errors="coerce",
).dt.normalize()

us_col = "sovereign_yields__US10Y"

if us_col not in panel.columns:
    raise RuntimeError(
        f"{us_col} not found in PIT-safe master panel"
    )

us = panel[
    ["date", us_col]
].copy()

us = us.rename(
    columns={us_col: "US10Y"}
)

us["US10Y"] = pd.to_numeric(
    us["US10Y"],
    errors="coerce",
)


# ============================================================
# 3. Merge only information available on each date
# ============================================================

df = sov.merge(
    us,
    on="date",
    how="left",
)

for col in [
    "KR10Y",
    "JP10Y",
    "DE10Y",
    "IL10Y",
    "US10Y",
]:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce",
    )


# ============================================================
# 4. Rebuild Production-contract spreads
# ============================================================

df["KR10Y_SPREAD"] = df["KR10Y"] - df["US10Y"]
df["JP10Y_SPREAD"] = df["JP10Y"] - df["US10Y"]
df["DE10Y_SPREAD"] = df["DE10Y"] - df["US10Y"]
df["IL10Y_SPREAD"] = df["IL10Y"] - df["US10Y"]


# ============================================================
# 5. Evidence boundary
# ============================================================

EVIDENCE_START = pd.Timestamp("2013-06-03")

df["evidence_status"] = "ALFRED_EVIDENCED"

df.loc[
    df["date"] < EVIDENCE_START,
    "evidence_status"
] = "UNVERIFIED_PRE_2013"


# No PIT-safe sovereign values should exist before evidence.
for col in [
    "KR10Y",
    "JP10Y",
    "DE10Y",
    "IL10Y",
]:
    bad = (
        (df["date"] < EVIDENCE_START)
        & df[col].notna()
    )

    if bad.any():
        raise SystemExit(
            f"ABORT — {col} populated before ALFRED evidence boundary"
        )


# ============================================================
# 6. Save
# ============================================================

keep = [
    "date",
    "US10Y",
    "KR10Y",
    "JP10Y",
    "DE10Y",
    "IL10Y",
    "KR10Y_SPREAD",
    "JP10Y_SPREAD",
    "DE10Y_SPREAD",
    "IL10Y_SPREAD",
    "evidence_status",
]

df[keep].to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig",
)


summary_rows = []

for col in [
    "KR10Y_SPREAD",
    "JP10Y_SPREAD",
    "DE10Y_SPREAD",
    "IL10Y_SPREAD",
]:

    x = df[col]

    summary_rows.append({
        "series": col,
        "first_valid_date": (
            df.loc[x.notna(), "date"].min()
        ),
        "last_valid_date": (
            df.loc[x.notna(), "date"].max()
        ),
        "valid_rows": int(x.notna().sum()),
        "pre_2013_valid_rows": int(
            (
                (df["date"] < EVIDENCE_START)
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
print("PIT-SAFE SOVEREIGN SPREAD BUILD")
print("=" * 80)

print(summary.to_string(index=False))

print()
print(
    "PRE-2013 POPULATED SPREADS:",
    int(summary["pre_2013_valid_rows"].sum()),
)

print("PRODUCTION MODIFIED: NO")
print("CANONICAL MASTER PANEL MODIFIED: NO")

print()
print("[OUTPUT]")
print(OUT)
print(SUMMARY)
