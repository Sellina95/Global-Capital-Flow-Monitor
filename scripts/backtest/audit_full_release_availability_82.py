from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"

PIT_DETAIL = RESULTS / "full_pit_lineage_82_detail.csv"

OUT_DETAIL = RESULTS / "full_release_availability_82_detail.csv"
OUT_SUMMARY = RESULTS / "full_release_availability_82_summary.csv"
OUT_TXT = RESULTS / "full_release_availability_82_summary.txt"

df = pd.read_csv(PIT_DETAIL)

# ------------------------------------------------------------
# Release / availability rule registry
# ------------------------------------------------------------

def classify(row):
    fam = str(row.get("source_family", ""))
    col = str(row.get("source_column", ""))
    stype = str(row.get("source_type", ""))
    status = str(row.get("status", ""))

    if status == "NO_VALID_SOURCE_VALUES":
        return pd.Series({
            "availability_class": "NO_VALID_SOURCE_VALUES",
            "release_rule_status": "REVIEW_REQUIRED",
            "release_rule": "",
            "notes": "No usable historical source values in current replay."
        })

    if fam == "execution_mapping":
        return pd.Series({
            "availability_class": "EXECUTION_MAPPING",
            "release_rule_status": "PASS_BY_CONSTRUCTION",
            "release_rule": "execution_date > signal_date",
            "notes": "Already checked in PIT chronology audit."
        })

    if fam == "master_panel_builder":
        return pd.Series({
            "availability_class": "PIPELINE_CONTROL",
            "release_rule_status": "PASS_BY_CONSTRUCTION",
            "release_rule": "ffill only; no bfill",
            "notes": "No future-row propagation."
        })

    if fam in {"macro", "country_etf"} and stype == "MARKET":
        return pd.Series({
            "availability_class": "MARKET_PRICE",
            "release_rule_status": "REVIEW_REQUIRED",
            "release_rule": "usable only after market close / provider availability",
            "notes": "Need signal timestamp vs market-close timing evidence."
        })

    if fam == "positioning":
        return pd.Series({
            "availability_class": "DERIVED_FROM_MARKET_HISTORY",
            "release_rule_status": "REVIEW_REQUIRED",
            "release_rule": "inherits availability from SPY / US10Y / DXY history",
            "notes": "Rolling historical construction is causal; parent market timing still required."
        })

    if fam == "sentiment":
        return pd.Series({
            "availability_class": "DERIVED_SOURCE",
            "release_rule_status": "REVIEW_REQUIRED",
            "release_rule": "inherits availability from VIX / HY_OAS / HYG-LQD",
            "notes": "Parent-source release timing must be closed first."
        })

    if fam == "sovereign_spreads":
        return pd.Series({
            "availability_class": "DERIVED_SOURCE",
            "release_rule_status": "REVIEW_REQUIRED",
            "release_rule": "inherits availability from sovereign yield inputs",
            "notes": "Spread is derived from yield source timing."
        })

    if fam == "credit" and col == "HY_OAS":
        return pd.Series({
            "availability_class": "FRED_CREDIT",
            "release_rule_status": "RELEASE_LAG_REQUIRED",
            "release_rule": "verify BAMLH0A0HYM2 publication availability",
            "notes": "Current pipeline uses FRED observation date directly."
        })

    if fam == "liquidity":
        if col in {"TGA", "WALCL"}:
            return pd.Series({
                "availability_class": "FRED_LOW_FREQUENCY",
                "release_rule_status": "RELEASE_LAG_REQUIRED",
                "release_rule": f"verify {col} publication/release date",
                "notes": "Observation date may precede public availability."
            })
        if col == "RRP":
            return pd.Series({
                "availability_class": "FRED_DAILY_LIQUIDITY",
                "release_rule_status": "REVIEW_REQUIRED",
                "release_rule": "verify RRP publication timing",
                "notes": "Daily series but exact availability timing still needs evidence."
            })
        if col == "NET_LIQ":
            return pd.Series({
                "availability_class": "DERIVED_SOURCE",
                "release_rule_status": "REVIEW_REQUIRED",
                "release_rule": "inherits max availability lag of WALCL/TGA/RRP",
                "notes": "Derived from three liquidity parents."
            })

    if fam in {"fred_sector", "fred_extras"}:
        if col == "FCI":
            return pd.Series({
                "availability_class": "FRED_LOW_FREQUENCY",
                "release_rule_status": "RELEASE_LAG_REQUIRED",
                "release_rule": "verify NFCI publication date vs observation date",
                "notes": "Weekly series; current pipeline uses observation date."
            })
        if col in {"REAL_RATE", "DFII10", "DGS2", "T10Y2Y", "T10YIE", "VIX"}:
            return pd.Series({
                "availability_class": "FRED_DAILY",
                "release_rule_status": "REVIEW_REQUIRED",
                "release_rule": f"verify {col} same-day/next-day availability",
                "notes": "Daily series; timing still needs source-level evidence."
            })

    if fam == "sovereign_yields":
        return pd.Series({
            "availability_class": "FRED_SOVEREIGN",
            "release_rule_status": "REVIEW_REQUIRED",
            "release_rule": f"verify publication lag for {col}",
            "notes": "Several sovereign series are monthly/low-frequency."
        })

    return pd.Series({
        "availability_class": "UNCLASSIFIED",
        "release_rule_status": "REVIEW_REQUIRED",
        "release_rule": "",
        "notes": "Needs manual classification."
    })


classified = df.join(df.apply(classify, axis=1))

classified.to_csv(OUT_DETAIL, index=False)

summary = (
    classified
    .groupby(
        ["availability_class", "release_rule_status"],
        dropna=False
    )
    .size()
    .reset_index(name="series_count")
)

summary.to_csv(OUT_SUMMARY, index=False)

release_required = int(
    (classified["release_rule_status"] == "RELEASE_LAG_REQUIRED").sum()
)

review_required = int(
    (classified["release_rule_status"] == "REVIEW_REQUIRED").sum()
)

pass_by_construction = int(
    (classified["release_rule_status"] == "PASS_BY_CONSTRUCTION").sum()
)

print("=" * 78)
print("FULL F13/F15/F18 RELEASE / AVAILABILITY INVENTORY")
print("=" * 78)
print(summary.to_string(index=False))
print()
print("PASS BY CONSTRUCTION:", pass_by_construction)
print("RELEASE LAG REQUIRED:", release_required)
print("REVIEW REQUIRED:", review_required)
print()

if release_required == 0 and review_required == 0:
    gate = "RELEASE / AVAILABILITY GATE: PASS"
else:
    gate = "RELEASE / AVAILABILITY GATE: NOT CLOSED"

print(gate)

txt = "\n".join([
    "FULL F13/F15/F18 RELEASE / AVAILABILITY INVENTORY",
    "=" * 78,
    f"PASS BY CONSTRUCTION: {pass_by_construction}",
    f"RELEASE LAG REQUIRED: {release_required}",
    f"REVIEW REQUIRED: {review_required}",
    "",
    gate,
    "",
    "Scope remains frozen to the same 82 F13/F15/F18 stage-contract pairs."
])

OUT_TXT.write_text(txt, encoding="utf-8")

print()
print("[OUTPUT]")
print(OUT_DETAIL)
print(OUT_SUMMARY)
print(OUT_TXT)
