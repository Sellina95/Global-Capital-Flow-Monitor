from __future__ import annotations

from pathlib import Path
from io import BytesIO
import urllib.request

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import BDay


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "backtest"
OUT_DIR = DATA / "pit_safe"
RESULTS = DATA / "results"

OUT_DIR.mkdir(parents=True, exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)

MASTER = DATA / "master_panel.csv"
OUT_PANEL = OUT_DIR / "master_panel_pit_safe.csv"
OUT_MANIFEST = RESULTS / "release_timing_repair_82_manifest.csv"
OUT_UNRESOLVED = RESULTS / "release_timing_repair_82_unresolved.csv"


# ============================================================
# FRED raw source
# ============================================================

FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="


def fetch_fred(series_id: str) -> pd.DataFrame:
    """
    Offline / deterministic historical source loader.

    Do NOT re-download current FRED history during PIT repair.
    Use the exact historical source CSVs already frozen under
    data/backtest so the repair remains reproducible.
    """

    source_map = {
        # NFCI / FCI
        "NFCI": (
            DATA / "fred_macro_extras.csv",
            "FCI",
        ),

        # Liquidity
        "WTREGEN": (
            DATA / "liquidity_data.csv",
            "TGA",
        ),
        "RRPONTSYD": (
            DATA / "liquidity_data.csv",
            "RRP",
        ),
        "WALCL": (
            DATA / "liquidity_data.csv",
            "WALCL",
        ),

        # FRED macro
        "DFII10": (
            DATA / "fred_macro_sctorallo.csv",
            "DFII10",
        ),
        "DGS2": (
            DATA / "fred_macro_sctorallo.csv",
            "DGS2",
        ),
        "T10Y2Y": (
            DATA / "fred_macro_sctorallo.csv",
            "T10Y2Y",
        ),
        "T10YIE": (
            DATA / "fred_macro_sctorallo.csv",
            "T10YIE",
        ),

        # Credit
        "BAMLH0A0HYM2": (
            DATA / "credit_spread_data.csv",
            "HY_OAS",
        ),

        # Sovereign US10Y
        "DGS10": (
            DATA / "sovereign_yields.csv",
            "US10Y",
        ),
    }

    if series_id not in source_map:
        raise KeyError(
            f"No frozen historical source mapping for {series_id}"
        )

    path, value_col = source_map[series_id]

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    date_col = next(
        (
            c for c in df.columns
            if c.lower() in {"date", "datetime"}
        ),
        None,
    )

    if date_col is None:
        raise ValueError(
            f"{path}: date column not found"
        )

    if value_col not in df.columns:
        raise ValueError(
            f"{path}: value column {value_col} not found"
        )

    out = df[
        [date_col, value_col]
    ].copy()

    out = out.rename(
        columns={
            date_col: "observation_date",
            value_col: series_id,
        }
    )

    out["observation_date"] = pd.to_datetime(
        out["observation_date"],
        errors="coerce",
    ).dt.normalize()

    out[series_id] = pd.to_numeric(
        out[series_id],
        errors="coerce",
    )

    out = (
        out
        .dropna(
            subset=[
                "observation_date",
                series_id,
            ]
        )
        .sort_values("observation_date")
        .drop_duplicates(
            "observation_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    return out


# ============================================================
# Calendar helpers
# ============================================================

panel = pd.read_csv(
    MASTER,
    parse_dates=["date", "signal_date", "execution_date"],
)

panel["date"] = pd.to_datetime(panel["date"]).dt.normalize()

calendar = pd.DataFrame({
    "date": panel["date"].copy()
})

start = panel["date"].min() - pd.Timedelta(days=30)
end = panel["date"].max() + pd.Timedelta(days=30)

holiday_calendar = USFederalHolidayCalendar()
US_HOLIDAYS = set(
    pd.to_datetime(
        holiday_calendar.holidays(start=start, end=end)
    ).normalize()
)


def next_business_day(d):
    return (pd.Timestamp(d) + BDay(1)).normalize()


def next_nonholiday_weekday(d):
    d = pd.Timestamp(d).normalize()

    while d.weekday() >= 5 or d in US_HOLIDAYS:
        d += pd.Timedelta(days=1)

    return d


def nfci_available_date(obs):
    """
    NFCI observation week -> following Wednesday.
    Holiday disruption -> next valid weekday.
    """
    obs = pd.Timestamp(obs).normalize()

    days = (2 - obs.weekday()) % 7
    if days == 0:
        days = 7

    release = obs + pd.Timedelta(days=days)

    return next_nonholiday_weekday(release)


def h41_available_date(obs):
    """
    H.4.1 Wednesday observation -> Thursday publication.
    """
    obs = pd.Timestamp(obs).normalize()
    return next_nonholiday_weekday(
        obs + pd.Timedelta(days=1)
    )


def same_day(obs):
    return pd.Timestamp(obs).normalize()


# ============================================================
# Convert raw observations -> availability-date series
# ============================================================

def build_available_series(
    series_id: str,
    output_name: str,
    availability_func,
) -> pd.DataFrame:

    raw = fetch_fred(series_id)

    raw["available_date"] = raw["observation_date"].apply(
        availability_func
    )

    out = raw[
        ["available_date", series_id]
    ].rename(
        columns={
            "available_date": "date",
            series_id: output_name,
        }
    )

    out = (
        out.sort_values("date")
        .drop_duplicates("date", keep="last")
    )

    # Map only information actually available by each date.
    base = calendar.merge(
        out,
        on="date",
        how="left",
    )

    base[output_name] = base[output_name].ffill()

    return base


manifest = []


def record(name, source, rule, status="REPAIRED"):
    manifest.append({
        "series": name,
        "source": source,
        "availability_rule": rule,
        "status": status,
    })


# ============================================================
# 1. NFCI / FCI
# ============================================================

fci = build_available_series(
    "NFCI",
    "FCI",
    nfci_available_date,
)

panel = panel.drop(
    columns=[
        c for c in [
            "fred_extras__FCI",
            "fred_sector__FCI",
        ]
        if c in panel.columns
    ]
)

panel = panel.merge(
    fci.rename(columns={"FCI": "fred_extras__FCI"}),
    on="date",
    how="left",
)

panel["fred_sector__FCI"] = panel["fred_extras__FCI"]

record(
    "FCI/NFCI",
    "FRED:NFCI",
    "following Wednesday availability",
)


# ============================================================
# 2. Liquidity
# ============================================================

tga = build_available_series(
    "WTREGEN",
    "TGA",
    h41_available_date,
)

walcl = build_available_series(
    "WALCL",
    "WALCL",
    h41_available_date,
)

rrp = build_available_series(
    "RRPONTSYD",
    "RRP",
    same_day,
)

liq = (
    calendar
    .merge(tga, on="date", how="left")
    .merge(rrp, on="date", how="left")
    .merge(walcl, on="date", how="left")
)

liq["NET_LIQ"] = (
    liq["WALCL"]
    - liq["TGA"]
    - liq["RRP"]
)

for col in ["TGA", "RRP", "WALCL", "NET_LIQ"]:

    panel_col = f"liquidity__{col}"

    if panel_col in panel.columns:
        panel = panel.drop(columns=[panel_col])

    panel = panel.merge(
        liq[["date", col]].rename(
            columns={col: panel_col}
        ),
        on="date",
        how="left",
    )

record("TGA", "FRED:WTREGEN", "H.4.1 Thursday availability")
record("WALCL", "FRED:WALCL", "H.4.1 Thursday availability")
record("RRP", "FRED:RRPONTSYD", "same-day post-operation")
record("NET_LIQ", "derived", "max parent availability; recomputed")


# ============================================================
# 3. H.15 / daily Treasury-related series
# ============================================================

daily_next_day = {
    "DFII10": "DFII10",
    "DGS2": "DGS2",
    "T10Y2Y": "T10Y2Y",
    "T10YIE": "T10YIE",
}

for output_name, fred_id in daily_next_day.items():

    repaired = build_available_series(
        fred_id,
        output_name,
        next_business_day,
    )

    panel_col = f"fred_sector__{output_name}"

    if panel_col in panel.columns:
        panel = panel.drop(columns=[panel_col])

    panel = panel.merge(
        repaired.rename(
            columns={output_name: panel_col}
        ),
        on="date",
        how="left",
    )

    record(
        output_name,
        f"FRED:{fred_id}",
        "next business day availability",
    )


# REAL_RATE = DFII10 in current production/backtest contract
panel["fred_sector__REAL_RATE"] = panel["fred_sector__DFII10"]

if "fred_extras__REAL_RATE" in panel.columns:
    panel = panel.drop(columns=["fred_extras__REAL_RATE"])

panel["fred_extras__REAL_RATE"] = panel["fred_sector__DFII10"]

record(
    "REAL_RATE",
    "FRED:DFII10",
    "inherits repaired DFII10 availability",
)


# ============================================================
# 4. Sovereign US10Y / DGS10
# ============================================================

us10 = build_available_series(
    "DGS10",
    "US10Y",
    next_business_day,
)

if "sovereign_yields__US10Y" in panel.columns:
    panel = panel.drop(columns=["sovereign_yields__US10Y"])

panel = panel.merge(
    us10.rename(
        columns={"US10Y": "sovereign_yields__US10Y"}
    ),
    on="date",
    how="left",
)

record(
    "sovereign_yields__US10Y",
    "FRED:DGS10",
    "next business day availability",
)


# ============================================================
# 5. HY OAS
# ============================================================

# Daily close source.
# It is retained on observation date because strategy execution
# occurs on the following trading date.

hy = build_available_series(
    "BAMLH0A0HYM2",
    "HY_OAS",
    same_day,
)

if "credit__HY_OAS" in panel.columns:
    panel = panel.drop(columns=["credit__HY_OAS"])

panel = panel.merge(
    hy.rename(
        columns={"HY_OAS": "credit__HY_OAS"}
    ),
    on="date",
    how="left",
)

record(
    "HY_OAS",
    "FRED:BAMLH0A0HYM2",
    "daily close / signal-close availability",
)


# ============================================================
# 6. Sentiment
#
# Must inherit repaired VIX / HY OAS timing.
# Do NOT blindly keep the old HY input.
# ============================================================

if "sentiment__hy_oas" in panel.columns:
    panel["sentiment__hy_oas"] = panel["credit__HY_OAS"]

record(
    "sentiment__hy_oas",
    "derived",
    "inherits repaired HY_OAS",
)


# ============================================================
# 7. Monthly sovereign series
#
# IMPORTANT:
# Exact historical publication dates are not yet proven.
# DO NOT invent release dates.
#
# Preserve them in current panel for comparison only, but mark
# them unresolved and prevent this script from claiming full PIT closure.
# ============================================================

MONTHLY_SOVEREIGN = [
    "KR10Y",
    "JP10Y",
    "DE10Y",
    "IL10Y",
    "GB10Y",
    "MX10Y",
]

unresolved = []

for col in MONTHLY_SOVEREIGN:

    unresolved.append({
        "series": f"sovereign_yields__{col}",
        "reason":
            "Exact historical publication/availability dates not yet frozen.",
        "required_next_step":
            "Build official release-date/vintage mapping before PIT closure.",
    })

    record(
        f"sovereign_yields__{col}",
        "FRED/OECD monthly",
        "UNRESOLVED exact historical publication date",
        status="UNRESOLVED",
    )


# ============================================================
# 8. Preserve chronology
# ============================================================

panel = panel.sort_values("date").reset_index(drop=True)

# signal/execution dates remain the original validated mapping.
panel["signal_date"] = pd.to_datetime(
    panel["signal_date"]
).dt.strftime("%Y-%m-%d")

panel["execution_date"] = pd.to_datetime(
    panel["execution_date"]
).dt.strftime("%Y-%m-%d")

panel["date"] = pd.to_datetime(
    panel["date"]
).dt.strftime("%Y-%m-%d")


# ============================================================
# Save — NEVER overwrite canonical master_panel
# ============================================================

panel.to_csv(
    OUT_PANEL,
    index=False,
    encoding="utf-8-sig",
)

pd.DataFrame(manifest).to_csv(
    OUT_MANIFEST,
    index=False,
    encoding="utf-8-sig",
)

pd.DataFrame(unresolved).to_csv(
    OUT_UNRESOLVED,
    index=False,
    encoding="utf-8-sig",
)


print("=" * 78)
print("F13/F15/F18 PIT RELEASE-TIMING REPAIR")
print("FROZEN UNIVERSE: 82 CONTRACTS")
print("=" * 78)

print()
print("PIT-SAFE CANDIDATE PANEL:")
print(OUT_PANEL)

print()
print("REPAIRED / CONTROLLED SERIES:")
print(
    pd.DataFrame(manifest)[
        ["series", "status", "availability_rule"]
    ].to_string(index=False)
)

print()
print("UNRESOLVED EXACT RELEASE SERIES:", len(unresolved))

if unresolved:
    print(
        pd.DataFrame(unresolved)[
            ["series", "reason"]
        ].to_string(index=False)
    )

print()
print("CANONICAL master_panel.csv MODIFIED: NO")
print("PRODUCTION MODIFIED: NO")

print()
if unresolved:
    print(
        "PIT REPAIR GATE: NOT CLOSED — "
        "MONTHLY SOVEREIGN RELEASE DATES REMAIN"
    )
else:
    print("PIT REPAIR GATE: READY FOR FULL REPLAY")
