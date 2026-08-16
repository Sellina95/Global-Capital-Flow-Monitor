from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

for path in (ROOT, ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


INPUT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_unknown_evidence_attribution_v1"
    / "unknown_evidence_daily.csv"
)

OUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_unknown_structural_families_v1"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

DAILY_OUT = OUT_DIR / "unknown_structural_family_daily.csv"
SUMMARY_OUT = OUT_DIR / "unknown_structural_family_summary.csv"
ERA_OUT = OUT_DIR / "unknown_structural_family_by_era.csv"
YEAR_OUT = OUT_DIR / "unknown_structural_family_by_year.csv"
PATH_OUT = OUT_DIR / "unknown_structural_family_neighbor_paths.csv"
EPISODE_OUT = OUT_DIR / "unknown_structural_family_episodes.csv"
AUDIT_OUT = OUT_DIR / "unknown_structural_family_audit.txt"


# ============================================================
# LOAD
# ============================================================

if not INPUT.exists():
    raise FileNotFoundError(INPUT)

df = pd.read_csv(
    INPUT,
    parse_dates=[
        "signal_date",
        "execution_date",
    ],
)

required = {
    "signal_date",
    "raw_macro_narrative",
    "is_unknown",
    "US10Y_DIR",
    "DXY_DIR",
    "VIX_DIR",
    "WTI_DIR",
    "HY_OAS_STATUS",
    "previous_raw_state",
    "next_raw_state",
}

missing = required - set(df.columns)

if missing:
    raise RuntimeError(
        f"Missing required columns: {sorted(missing)}"
    )


# ============================================================
# NORMALIZE
# ============================================================

def as_bool(value) -> bool:
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {
        "true", "1", "yes"
    }


df["is_unknown"] = df["is_unknown"].map(as_bool)

unknown = (
    df[df["is_unknown"]]
    .copy()
    .reset_index(drop=True)
)

EXPECTED_UNKNOWN = 1328

if len(unknown) != EXPECTED_UNKNOWN:
    raise RuntimeError(
        "UNKNOWN identity failure: "
        f"expected={EXPECTED_UNKNOWN}, actual={len(unknown)}"
    )


def clean_dir(value):
    try:
        if pd.isna(value):
            return None

        value = int(float(value))

        if value in (-1, 0, 1):
            return value

        return None

    except Exception:
        return None


for col in (
    "US10Y_DIR",
    "DXY_DIR",
    "VIX_DIR",
    "WTI_DIR",
):
    unknown[col] = unknown[col].map(clean_dir)


# ============================================================
# STRUCTURAL FAMILY
#
# IMPORTANT:
# These are evidence families, NOT new macro regimes.
#
# Priority:
# 1. Missing evidence
# 2. Flat / low-information evidence
# 3. Rates/USD relationship
# 4. VIX is retained as sub-family context
#
# We deliberately do NOT use returns or future states.
# ============================================================

def direction_name(value):

    if value == 1:
        return "UP"

    if value == -1:
        return "DOWN"

    if value == 0:
        return "FLAT"

    return "MISSING"


def classify_family(row):

    r = row["US10Y_DIR"]
    d = row["DXY_DIR"]
    v = row["VIX_DIR"]
    w = row["WTI_DIR"]

    dirs = {
        "RATES": r,
        "USD": d,
        "VIX": v,
        "WTI": w,
    }

    missing_fields = [
        key
        for key, value in dirs.items()
        if value is None
    ]

    if missing_fields:
        return (
            "MISSING_EVIDENCE",
            "+".join(missing_fields),
        )

    flat_fields = [
        key
        for key, value in dirs.items()
        if value == 0
    ]

    if flat_fields:
        return (
            "FLAT_LOW_INFORMATION",
            "+".join(flat_fields),
        )

    # --------------------------------------------
    # Rates down / USD down
    # --------------------------------------------

    if r == -1 and d == -1:

        if v == 1:
            family = "RATES_DOWN_USD_DOWN_VIX_UP"
        else:
            family = "RATES_DOWN_USD_DOWN_VIX_DOWN"

        return (
            family,
            f"WTI_{direction_name(w)}",
        )

    # --------------------------------------------
    # Rates down / USD up
    # --------------------------------------------

    if r == -1 and d == 1:

        family = (
            "RATES_DOWN_USD_UP_"
            f"VIX_{direction_name(v)}"
        )

        return (
            family,
            f"WTI_{direction_name(w)}",
        )

    # --------------------------------------------
    # Rates up / USD down
    # --------------------------------------------

    if r == 1 and d == -1:

        family = (
            "RATES_UP_USD_DOWN_"
            f"VIX_{direction_name(v)}"
        )

        return (
            family,
            f"WTI_{direction_name(w)}",
        )

    # --------------------------------------------
    # Rates up / USD up
    #
    # Normally Production catches the principal
    # inflation/tightening combinations. Any UNKNOWN
    # surviving here is worth isolating explicitly.
    # --------------------------------------------

    if r == 1 and d == 1:

        family = (
            "RATES_UP_USD_UP_"
            f"VIX_{direction_name(v)}"
        )

        return (
            family,
            f"WTI_{direction_name(w)}",
        )

    return (
        "OTHER_UNMAPPED_EVIDENCE",
        (
            f"R={r}|D={d}|V={v}|W={w}"
        ),
    )


classified = unknown.apply(
    classify_family,
    axis=1,
    result_type="expand",
)

classified.columns = [
    "structural_family",
    "family_detail",
]

unknown[
    [
        "structural_family",
        "family_detail",
    ]
] = classified


# ============================================================
# FAMILY SUMMARY
# ============================================================

summary = (
    unknown
    .groupby(
        "structural_family",
        dropna=False,
    )
    .agg(
        observations=("signal_date", "size"),
        first_date=("signal_date", "min"),
        last_date=("signal_date", "max"),
        years_present=("signal_date", lambda s: s.dt.year.nunique()),
        hy_cool=("HY_OAS_STATUS", lambda s: (s == "COOL").sum()),
        hy_watch=("HY_OAS_STATUS", lambda s: (s == "WATCH").sum()),
        hy_hot=("HY_OAS_STATUS", lambda s: (s == "HOT").sum()),
        hy_fracture=("HY_OAS_STATUS", lambda s: (s == "FRACTURE").sum()),
    )
    .reset_index()
)

summary["share_of_unknown"] = (
    summary["observations"]
    / len(unknown)
)

summary = summary.sort_values(
    "observations",
    ascending=False,
)


# ============================================================
# TIME STABILITY
# ============================================================

unknown["year"] = (
    unknown["signal_date"].dt.year
)


def era(year):

    if year <= 2010:
        return "2008-2010_GFC_AFTERMATH"

    if year <= 2014:
        return "2011-2014_EURO_QE"

    if year <= 2019:
        return "2015-2019_PRE_COVID"

    if year <= 2021:
        return "2020-2021_COVID"

    if year <= 2023:
        return "2022-2023_INFLATION"

    return "2024-2026_RECENT"


unknown["era"] = unknown["year"].map(era)


by_year = (
    unknown
    .groupby(
        [
            "year",
            "structural_family",
        ],
        dropna=False,
    )
    .size()
    .rename("observations")
    .reset_index()
)


by_era = (
    unknown
    .groupby(
        [
            "era",
            "structural_family",
        ],
        dropna=False,
    )
    .size()
    .rename("observations")
    .reset_index()
)

era_totals = (
    unknown
    .groupby("era")
    .size()
    .rename("era_unknown_total")
)

by_era = by_era.merge(
    era_totals,
    on="era",
    how="left",
)

by_era["share_within_era"] = (
    by_era["observations"]
    / by_era["era_unknown_total"]
)


# ============================================================
# FAMILY EPISODES
#
# Consecutive UNKNOWN days belonging to the SAME family.
# ============================================================

episode_rows = []

episode_id = 0
start = 0

for i in range(1, len(unknown) + 1):

    end_episode = False

    if i == len(unknown):
        end_episode = True

    else:
        current = unknown.iloc[i]
        previous = unknown.iloc[i - 1]

        # Must be consecutive rows in original daily dataset.
        current_original_idx = df.index[
            df["signal_date"].eq(
                current["signal_date"]
            )
        ][0]

        previous_original_idx = df.index[
            df["signal_date"].eq(
                previous["signal_date"]
            )
        ][0]

        consecutive_unknown = (
            current_original_idx
            == previous_original_idx + 1
        )

        same_family = (
            current["structural_family"]
            == previous["structural_family"]
        )

        if not (
            consecutive_unknown
            and same_family
        ):
            end_episode = True

    if end_episode:

        block = unknown.iloc[
            start:i
        ]

        episode_id += 1

        episode_rows.append({
            "episode_id": episode_id,
            "structural_family": (
                block[
                    "structural_family"
                ].iloc[0]
            ),
            "start_date": (
                block[
                    "signal_date"
                ].iloc[0]
            ),
            "end_date": (
                block[
                    "signal_date"
                ].iloc[-1]
            ),
            "duration": len(block),
            "previous_raw_state": (
                block[
                    "previous_raw_state"
                ].iloc[0]
            ),
            "next_raw_state": (
                block[
                    "next_raw_state"
                ].iloc[-1]
            ),
        })

        start = i


episodes = pd.DataFrame(
    episode_rows
)


episode_stats = (
    episodes
    .groupby(
        "structural_family",
        dropna=False,
    )
    .agg(
        episodes=("episode_id", "size"),
        mean_duration=("duration", "mean"),
        median_duration=("duration", "median"),
        max_duration=("duration", "max"),
    )
    .reset_index()
)

summary = summary.merge(
    episode_stats,
    on="structural_family",
    how="left",
)


# ============================================================
# NEIGHBOR PATHS BY FAMILY
#
# Retrospective diagnostics only.
# next_raw_state MUST NOT be used for signal construction.
# ============================================================

paths = (
    unknown
    .groupby(
        [
            "structural_family",
            "previous_raw_state",
            "next_raw_state",
        ],
        dropna=False,
    )
    .size()
    .rename("observations")
    .reset_index()
    .sort_values(
        [
            "structural_family",
            "observations",
        ],
        ascending=[
            True,
            False,
        ],
    )
)


family_totals = (
    unknown
    .groupby(
        "structural_family"
    )
    .size()
    .rename(
        "family_total"
    )
)

paths = paths.merge(
    family_totals,
    on="structural_family",
    how="left",
)

paths["share_within_family"] = (
    paths["observations"]
    / paths["family_total"]
)


# ============================================================
# STABILITY FLAGS
#
# Descriptive audit only.
#
# A family is called broad-history if it appears in:
# >= 10 calendar years AND >= 4 eras.
#
# This is NOT a selection rule for production.
# ============================================================

era_presence = (
    unknown
    .groupby(
        "structural_family"
    )["era"]
    .nunique()
    .rename(
        "eras_present"
    )
)

summary = summary.merge(
    era_presence,
    on="structural_family",
    how="left",
)

summary["broad_history_flag"] = (
    (summary["years_present"] >= 10)
    & (summary["eras_present"] >= 4)
)


# ============================================================
# SAVE
# ============================================================

unknown.to_csv(
    DAILY_OUT,
    index=False,
)

summary.to_csv(
    SUMMARY_OUT,
    index=False,
)

by_era.to_csv(
    ERA_OUT,
    index=False,
)

by_year.to_csv(
    YEAR_OUT,
    index=False,
)

paths.to_csv(
    PATH_OUT,
    index=False,
)

episodes.to_csv(
    EPISODE_OUT,
    index=False,
)


# ============================================================
# PRINT
# ============================================================

print("=" * 130)
print("MACRO UNKNOWN — STRUCTURAL FAMILY AUDIT")
print("=" * 130)

print()
print("===== CONTRACT =====")
print(f"UNKNOWN observations : {len(unknown)}")
print("Expected             : 1328")
print("Identity             : PASS")
print("Returns used         : NO")
print("13/15/18 executed    : NO")
print("Future state used    : DIAGNOSTIC ONLY")

print()
print("===== STRUCTURAL FAMILY SUMMARY =====")

print(
    summary.to_string(
        index=False,
        formatters={
            "share_of_unknown":
                lambda x: f"{x:.2%}",
            "mean_duration":
                lambda x: f"{x:.2f}",
            "median_duration":
                lambda x: f"{x:.2f}",
        },
    )
)

print()
print("===== FAMILY PRESENCE BY ERA =====")

era_pivot = (
    by_era
    .pivot(
        index="structural_family",
        columns="era",
        values="observations",
    )
    .fillna(0)
    .astype(int)
)

print(
    era_pivot.to_string()
)

print()
print("===== TOP NEIGHBOR PATHS BY FAMILY =====")

top_paths = (
    paths
    .groupby(
        "structural_family",
        group_keys=False,
    )
    .head(5)
)

print(
    top_paths.to_string(
        index=False,
        formatters={
            "share_within_family":
                lambda x: f"{x:.2%}",
        },
    )
)

print()
print("===== INTERPRETATION CONTRACT =====")
print(
    """
Do NOT convert these families directly into new macro regimes.

This gate asks only:

1. Is UNKNOWN structurally heterogeneous?
2. Do the same evidence families recur across market eras?
3. Are families mostly transient or persistent?
4. Do different families sit between different named macro states?

A family being frequent or persistent does NOT authorize
a Production rule.

Returns, CAGR, Sharpe and downstream portfolio performance
must not be used at this gate.
""".strip()
)


# ============================================================
# AUDIT MEMO
# ============================================================

broad = (
    summary.loc[
        summary[
            "broad_history_flag"
        ],
        "structural_family",
    ]
    .astype(str)
    .tolist()
)

audit = f"""
MACRO UNKNOWN STRUCTURAL FAMILY AUDIT V1

CONTRACT
--------
UNKNOWN observations : {len(unknown)}
Expected             : 1328
Identity             : PASS

PURPOSE
-------
Determine whether Production UNKNOWN_TRANSITION is:

A) one coherent transition state,
B) a heterogeneous residual bucket,
C) a mixture of low-information and economically conflicting
   cross-asset evidence.

FAMILY CONSTRUCTION
-------------------
Families are defined only from contemporaneous PIT evidence:

- US10Y direction
- DXY direction
- VIX direction
- WTI direction
- HY OAS status as context

No returns are used.
No future state is used to construct a family.
No new macro regime is created.

BROAD-HISTORY DESCRIPTIVE FLAG
------------------------------
Appears in >=10 calendar years and >=4 eras.

Families meeting descriptive flag:
{broad}

IMPORTANT
---------
The broad-history flag is descriptive only.
It is NOT a Production selection criterion.

Neighbor next-state data is retrospective diagnostic metadata
and MUST NOT be used to generate a historical signal.

SAFETY
------
Production modified : NO
Filter13 modified   : NO
Filter15 modified   : NO
Filter18 modified   : NO
Filter13 executed   : NO
Filter15 executed   : NO
Filter18 executed   : NO
Returns used        : NO
Performance used    : NO
Parameter selected  : NO
Commit              : NO
""".strip()

AUDIT_OUT.write_text(
    audit,
    encoding="utf-8",
)


print()
print("===== ARTIFACTS =====")
print("Daily    :", DAILY_OUT)
print("Summary  :", SUMMARY_OUT)
print("Era      :", ERA_OUT)
print("Year     :", YEAR_OUT)
print("Paths    :", PATH_OUT)
print("Episodes :", EPISODE_OUT)
print("Audit    :", AUDIT_OUT)

print()
print("PRODUCTION MODIFIED : NO")
print("FILTER13/15/18      : UNCHANGED / NOT EXECUTED")
print("RETURNS USED        : NO")
print("PERFORMANCE USED    : NO")
print("PARAMETER SELECTED  : NO")
print("COMMIT              : NO")

print()
print("=" * 130)
print("STRUCTURAL FAMILY AUDIT COMPLETE — DO NOT COMMIT")
print("=" * 130)
