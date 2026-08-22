from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data" / "backtest"
RESULTS = DATA / "results"
PIT = DATA / "pit_safe"

BASE_PATH = DATA / "master_panel.csv"
PIT_PATH = PIT / "master_panel_pit_safe_with_sovereign.csv"

OUT_DETAIL = RESULTS / "pit_repair_integrity_final_detail.csv"
OUT_SUMMARY = RESULTS / "pit_repair_integrity_final_summary.csv"
OUT_TXT = RESULTS / "pit_repair_integrity_final_summary.txt"

# ------------------------------------------------------------------
# Allowed repair scope
#
# These are the contracts intentionally modified during PIT repair.
# Sovereign aliases are included because they were deliberately added
# for Production-equivalent GEO execution.
# ------------------------------------------------------------------

ALLOWED_EXACT = {
    "FCI",
    "TGA",
    "WALCL",
    "RRP",
    "NET_LIQ",
    "DFII10",
    "DGS2",
    "T10Y2Y",
    "T10YIE",
    "REAL_RATE",
    "US10Y",
    "HY_OAS",

    "KR10Y_SPREAD",
    "JP10Y_SPREAD",
    "DE10Y_SPREAD",
    "IL10Y_SPREAD",

    "sovereign_spreads__KR_US_SPREAD",
    "sovereign_spreads__JP_US_SPREAD",
    "sovereign_spreads__DE_US_SPREAD",
    "sovereign_spreads__IL_US_SPREAD",
}

# Prefix / suffix matching is needed because master_panel contains
# source-family-qualified names such as fred_sector__DFII10.
ALLOWED_TOKENS = {
    "FCI",
    "TGA",
    "WALCL",
    "RRP",
    "NET_LIQ",
    "DFII10",
    "DGS2",
    "T10Y2Y",
    "T10YIE",
    "REAL_RATE",
    "US10Y",
    "HY_OAS",
    "KR10Y",
    "JP10Y",
    "DE10Y",
    "IL10Y",
}


def is_allowed_repair_column(col: str) -> bool:

    if col in ALLOWED_EXACT:
        return True

    u = str(col).upper()

    return any(
        token in u
        for token in ALLOWED_TOKENS
    )


def normalize_dates(df: pd.DataFrame) -> pd.DataFrame:

    x = df.copy()

    if "signal_date" not in x.columns:
        raise RuntimeError("signal_date missing")

    x["signal_date"] = pd.to_datetime(
        x["signal_date"],
        errors="coerce",
    ).dt.normalize()

    x = (
        x.dropna(subset=["signal_date"])
        .drop_duplicates(
            subset=["signal_date"],
            keep="last",
        )
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    return x


def series_changed(a: pd.Series, b: pd.Series):

    # First try numeric comparison.
    an = pd.to_numeric(a, errors="coerce")
    bn = pd.to_numeric(b, errors="coerce")

    numeric_mask = an.notna() | bn.notna()

    numeric_changed = pd.Series(
        False,
        index=a.index,
    )

    both_nan = an.isna() & bn.isna()

    numeric_changed.loc[numeric_mask] = (
        ~both_nan.loc[numeric_mask]
        & ~np.isclose(
            an.loc[numeric_mask].fillna(np.inf),
            bn.loc[numeric_mask].fillna(np.inf),
            rtol=0,
            atol=1e-12,
        )
    )

    # For rows that are genuinely non-numeric, compare normalized strings.
    non_numeric_mask = ~numeric_mask

    text_changed = pd.Series(
        False,
        index=a.index,
    )

    if non_numeric_mask.any():

        aa = (
            a.loc[non_numeric_mask]
            .fillna("<NA>")
            .astype(str)
        )

        bb = (
            b.loc[non_numeric_mask]
            .fillna("<NA>")
            .astype(str)
        )

        text_changed.loc[non_numeric_mask] = aa != bb

    return numeric_changed | text_changed


# ------------------------------------------------------------------
# Load
# ------------------------------------------------------------------

if not BASE_PATH.exists():
    raise FileNotFoundError(BASE_PATH)

if not PIT_PATH.exists():
    raise FileNotFoundError(PIT_PATH)

base = normalize_dates(
    pd.read_csv(BASE_PATH)
)

pit = normalize_dates(
    pd.read_csv(PIT_PATH)
)

# ------------------------------------------------------------------
# Align exact historical dates
# ------------------------------------------------------------------

common_dates = sorted(
    set(base["signal_date"])
    & set(pit["signal_date"])
)

base = (
    base[base["signal_date"].isin(common_dates)]
    .set_index("signal_date")
    .sort_index()
)

pit = (
    pit[pit["signal_date"].isin(common_dates)]
    .set_index("signal_date")
    .sort_index()
)

if not base.index.equals(pit.index):
    raise RuntimeError("Date alignment failed")

common_cols = sorted(
    (set(base.columns) & set(pit.columns))
    - {"date", "execution_date"}
)

rows = []

for col in common_cols:

    changed = series_changed(
        base[col],
        pit[col],
    )

    changed_rows = int(changed.sum())

    rows.append({
        "column": col,
        "allowed_repair":
            is_allowed_repair_column(col),
        "changed_rows": changed_rows,
        "changed_pct":
            changed_rows / len(base) * 100
            if len(base)
            else np.nan,
        "status": (
            "UNCHANGED"
            if changed_rows == 0
            else (
                "EXPECTED_CHANGE"
                if is_allowed_repair_column(col)
                else "UNEXPECTED_CHANGE"
            )
        ),
    })

detail = pd.DataFrame(rows)

# ------------------------------------------------------------------
# Added / removed columns
# ------------------------------------------------------------------

added_cols = sorted(
    set(pit.columns)
    - set(base.columns)
)

removed_cols = sorted(
    set(base.columns)
    - set(pit.columns)
)

added_rows = []

for col in added_cols:

    allowed = is_allowed_repair_column(col)

    added_rows.append({
        "column": col,
        "allowed_repair": allowed,
        "changed_rows": len(pit),
        "changed_pct": 100.0,
        "status": (
            "EXPECTED_ADDED_COLUMN"
            if allowed
            else "UNEXPECTED_ADDED_COLUMN"
        ),
    })

if added_rows:
    detail = pd.concat(
        [
            detail,
            pd.DataFrame(added_rows),
        ],
        ignore_index=True,
    )

# ------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------

summary = (
    detail.groupby(
        ["status"],
        dropna=False,
    )
    .size()
    .reset_index(name="column_count")
)

unexpected = detail[
    detail["status"].isin({
        "UNEXPECTED_CHANGE",
        "UNEXPECTED_ADDED_COLUMN",
    })
].copy()

unexpected_removed = [
    c
    for c in removed_cols
    if not is_allowed_repair_column(c)
]

expected_changed = detail[
    detail["status"].isin({
        "EXPECTED_CHANGE",
        "EXPECTED_ADDED_COLUMN",
    })
].copy()

gate_pass = (
    unexpected.empty
    and not unexpected_removed
    and not expected_changed.empty
)

# ------------------------------------------------------------------
# Save
# ------------------------------------------------------------------

RESULTS.mkdir(
    parents=True,
    exist_ok=True,
)

detail.to_csv(
    OUT_DETAIL,
    index=False,
    encoding="utf-8-sig",
)

summary.to_csv(
    OUT_SUMMARY,
    index=False,
    encoding="utf-8-sig",
)

lines = []

lines.append(
    "F13/F15/F18 PIT REPAIR INTEGRITY — FINAL CLOSURE"
)
lines.append("=" * 72)

lines.append(
    f"Overlapping dates: {len(base)}"
)

lines.append(
    f"Common columns checked: {len(common_cols)}"
)

lines.append(
    f"Expected changed/added columns: {len(expected_changed)}"
)

lines.append(
    f"Unexpected changed/added columns: {len(unexpected)}"
)

lines.append(
    f"Unexpected removed columns: {len(unexpected_removed)}"
)

lines.append("")

if gate_pass:
    lines.append(
        "PIT REPAIR INTEGRITY GATE: PASS"
    )
else:
    lines.append(
        "PIT REPAIR INTEGRITY GATE: FAIL"
    )

lines.append("")
lines.append(
    "NOTE: 2008–2013 active sovereign vintage evidence "
    "remains historically unverified and must remain documented."
)

OUT_TXT.write_text(
    "\n".join(lines),
    encoding="utf-8",
)

# ------------------------------------------------------------------
# Console
# ------------------------------------------------------------------

print("=" * 80)
print("F13/F15/F18 PIT REPAIR INTEGRITY — FINAL CLOSURE")
print("=" * 80)

print()
print(summary.to_string(index=False))

print()
print("OVERLAPPING DATES:", len(base))
print("COMMON COLUMNS CHECKED:", len(common_cols))
print(
    "EXPECTED CHANGED / ADDED:",
    len(expected_changed),
)
print(
    "UNEXPECTED CHANGED / ADDED:",
    len(unexpected),
)
print(
    "UNEXPECTED REMOVED:",
    len(unexpected_removed),
)

if not unexpected.empty:

    print()
    print("UNEXPECTED CHANGES:")
    print(
        unexpected[
            [
                "column",
                "changed_rows",
                "changed_pct",
                "status",
            ]
        ].to_string(index=False)
    )

if unexpected_removed:

    print()
    print("UNEXPECTED REMOVED COLUMNS:")
    for col in unexpected_removed:
        print(" -", col)

print()
print(
    "PIT REPAIR INTEGRITY GATE:",
    "PASS" if gate_pass else "FAIL",
)

print()
print(
    "Historical limitation: "
    "2008–2013 sovereign vintage remains UNVERIFIED."
)

print()
print("[OUTPUT]")
print(OUT_DETAIL)
print(OUT_SUMMARY)
print(OUT_TXT)
