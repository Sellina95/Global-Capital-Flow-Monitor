from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

RESULTS_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

ATTRIBUTION_PATH = (
    RESULTS_DIR
    / "filter13_budget_attribution_final_daily.csv"
)

MACRO_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "macro_data.csv"
)

OUTPUT_DAILY = (
    RESULTS_DIR
    / "filter13_hard_trigger_attribution_daily.csv"
)

OUTPUT_SUMMARY = (
    RESULTS_DIR
    / "filter13_hard_trigger_attribution_summary.csv"
)


# ============================================================
# Helpers
# ============================================================

def to_num(x):
    try:
        v = pd.to_numeric(x, errors="coerce")
        return None if pd.isna(v) else float(v)
    except Exception:
        return None


def direction(today, prev):
    today = to_num(today)
    prev = to_num(prev)

    if today is None or prev is None:
        return 0

    if today > prev:
        return 1

    if today < prev:
        return -1

    return 0


def rolling_zscore(series, window=60):
    """
    Historical-only rolling z-score.

    IMPORTANT:
    shift(1)을 사용하므로 오늘의 변화율을
    오늘 자신의 historical mean/std 계산에 넣지 않는다.

    이는 진입 trigger를 새로 만드는 용도가 아니라,
    기존 HARD 판정의 magnitude context를 audit하기 위한 값이다.
    """

    s = pd.to_numeric(
        series,
        errors="coerce",
    )

    mean = (
        s
        .rolling(
            window=window,
            min_periods=20,
        )
        .mean()
        .shift(1)
    )

    std = (
        s
        .rolling(
            window=window,
            min_periods=20,
        )
        .std()
        .shift(1)
    )

    z = (s - mean) / std.replace(0, np.nan)

    return z


# ============================================================
# Load
# ============================================================

if not ATTRIBUTION_PATH.exists():
    raise FileNotFoundError(
        f"Missing attribution file: "
        f"{ATTRIBUTION_PATH}"
    )

if not MACRO_PATH.exists():
    raise FileNotFoundError(
        f"Missing macro file: "
        f"{MACRO_PATH}"
    )


a = pd.read_csv(
    ATTRIBUTION_PATH
)

m = pd.read_csv(
    MACRO_PATH
)


a["date"] = pd.to_datetime(
    a["date"],
    errors="coerce",
)

m["date"] = pd.to_datetime(
    m["date"],
    errors="coerce",
)


a = (
    a
    .dropna(
        subset=["date"]
    )
    .sort_values("date")
    .reset_index(drop=True)
)

m = (
    m
    .dropna(
        subset=["date"]
    )
    .sort_values("date")
    .reset_index(drop=True)
)


# ============================================================
# Hard PIT gate
# ============================================================

if "pit_status" not in a.columns:
    raise RuntimeError(
        "pit_status missing from attribution file"
    )

bad_pit = a[
    ~a["pit_status"].isin(
        [
            "PASS",
            "FIRST_ROW",
        ]
    )
]

if not bad_pit.empty:
    raise RuntimeError(
        "PIT gate failed. "
        "Do not continue HARD trigger attribution."
    )


# ============================================================
# Macro raw tape reconstruction
# ============================================================

required_macro = [
    "US10Y",
    "DXY",
    "VIX",
    "WTI",
]

missing = [
    c
    for c in required_macro
    if c not in m.columns
]

if missing:
    raise RuntimeError(
        f"macro_data.csv missing columns: "
        f"{missing}"
    )


for col in required_macro:

    m[col] = pd.to_numeric(
        m[col],
        errors="coerce",
    )

    m[f"{col}_PREV"] = (
        m[col]
        .shift(1)
    )

    m[f"{col}_DIR_AUDIT"] = [
        direction(
            today,
            prev,
        )
        for today, prev
        in zip(
            m[col],
            m[f"{col}_PREV"],
        )
    ]

    m[f"{col}_PCT_AUDIT"] = (
        m[col]
        .pct_change(
            fill_method=None
        )
    )

    m[f"{col}_Z_AUDIT"] = (
        rolling_zscore(
            m[f"{col}_PCT_AUDIT"],
            window=60,
        )
    )


keep_macro = [
    "date",

    "US10Y",
    "DXY",
    "VIX",
    "WTI",

    "US10Y_DIR_AUDIT",
    "DXY_DIR_AUDIT",
    "VIX_DIR_AUDIT",
    "WTI_DIR_AUDIT",

    "US10Y_Z_AUDIT",
    "DXY_Z_AUDIT",
    "VIX_Z_AUDIT",
    "WTI_Z_AUDIT",
]


d = a.merge(
    m[keep_macro],
    on="date",
    how="left",
)


# ============================================================
# HARD RISK-OFF only
# ============================================================

hard = d[
    d["market_regime"]
    .astype(str)
    .str.startswith(
        "HARD RISK-OFF"
    )
].copy()


if hard.empty:
    raise RuntimeError(
        "No HARD RISK-OFF rows found."
    )


# ============================================================
# Trigger attribution
#
# IMPORTANT:
#
# Production order:
#
# 1 Sigma systemic
# 2 Sigma inflation
# 3 Sigma VIX+DXY abs override
# 4 CREDIT_STRESS
# 5 TIGHTENING_GROWTH_SCARE + VIX >= 22
# 6 STAGFLATION + VIX/HY
#
# 현재 attribution CSV에는 production CROSS_ASSET_TAPE의
# 모든 Z 값이 저장되어 있지 않으므로,
#
# Sigma trigger는 audit reconstruction으로 별도 표시한다.
#
# CREDIT / GROWTH / STAGFLATION은
# 실제 저장된 macro_narrative + regime을 기준으로 분류한다.
# ============================================================


def classify_trigger(row):

    regime = str(
        row.get(
            "market_regime",
            "",
        )
    ).upper()

    narrative = str(
        row.get(
            "macro_narrative",
            "",
        )
    ).upper()

    vix_today = to_num(
        row.get(
            "VIX",
        )
    )

    vix_z = to_num(
        row.get(
            "VIX_Z_AUDIT",
        )
    )

    dxy_z = to_num(
        row.get(
            "DXY_Z_AUDIT",
        )
    )

    us10y_z = to_num(
        row.get(
            "US10Y_Z_AUDIT",
        )
    )

    wti_z = to_num(
        row.get(
            "WTI_Z_AUDIT",
        )
    )

    # ----------------------------------------------
    # Reconstructed sigma flags
    # ----------------------------------------------

    sigma_abs_vix_dxy = (
        vix_z is not None
        and dxy_z is not None
        and abs(vix_z) >= 2
        and abs(dxy_z) >= 1.5
    )

    sigma_inflation = (
        vix_z is not None
        and us10y_z is not None
        and wti_z is not None
        and abs(vix_z) >= 2.5
        and abs(us10y_z) >= 2
        and abs(wti_z) >= 1.5
    )

    # ----------------------------------------------
    # Actual narrative/regime attribution
    # ----------------------------------------------

    if (
        "INFLATION SHOCK"
        in regime
    ):
        return (
            "STAGFLATION_OR_INFLATION_SHOCK"
        )

    if (
        narrative
        == "CREDIT_STRESS"
    ):
        return (
            "CREDIT_STRESS"
        )

    if (
        narrative
        == "TIGHTENING_GROWTH_SCARE"
        and
        vix_today is not None
        and
        vix_today >= 22
    ):
        return (
            "GROWTH_SCARE_VIX"
        )

    if sigma_inflation:
        return (
            "SIGMA_INFLATION_RECONSTRUCTED"
        )

    if sigma_abs_vix_dxy:
        return (
            "SIGMA_ABS_OVERRIDE_RECONSTRUCTED"
        )

    return "OTHER_OR_UNRESOLVED"


hard["trigger"] = hard.apply(
    classify_trigger,
    axis=1,
)


# ============================================================
# Direction check for Sigma ABS issue
# ============================================================

def sigma_direction_check(row):

    vix_z = to_num(
        row.get(
            "VIX_Z_AUDIT",
        )
    )

    dxy_z = to_num(
        row.get(
            "DXY_Z_AUDIT",
        )
    )

    if (
        vix_z is None
        or dxy_z is None
        or abs(vix_z) < 2
        or abs(dxy_z) < 1.5
    ):
        return "NOT_SIGMA_ABS"

    vix_dir = int(
        row.get(
            "VIX_DIR_AUDIT",
            0,
        )
        or 0
    )

    dxy_dir = int(
        row.get(
            "DXY_DIR_AUDIT",
            0,
        )
        or 0
    )

    # Risk-off 방향:
    # VIX 상승 + Dollar 상승

    if (
        vix_dir == 1
        and dxy_dir == 1
    ):
        return "DIRECTION_CONFIRMED"

    return "DIRECTION_MISMATCH"


hard[
    "sigma_direction_check"
] = hard.apply(
    sigma_direction_check,
    axis=1,
)


# ============================================================
# One-day / flicker context
# ============================================================

all_regimes = (
    d[
        [
            "date",
            "market_regime",
        ]
    ]
    .copy()
    .reset_index(drop=True)
)

all_regimes[
    "prev_regime"
] = (
    all_regimes[
        "market_regime"
    ]
    .shift(1)
)

all_regimes[
    "next_regime"
] = (
    all_regimes[
        "market_regime"
    ]
    .shift(-1)
)


hard = hard.merge(
    all_regimes[
        [
            "date",
            "prev_regime",
            "next_regime",
        ]
    ],
    on="date",
    how="left",
)


hard[
    "hard_next_day"
] = (
    hard[
        "next_regime"
    ]
    .astype(str)
    .str.startswith(
        "HARD RISK-OFF"
    )
)


hard[
    "one_day_hard_candidate"
] = (
    ~hard[
        "prev_regime"
    ]
    .astype(str)
    .str.startswith(
        "HARD RISK-OFF"
    )
    &
    ~hard[
        "next_regime"
    ]
    .astype(str)
    .str.startswith(
        "HARD RISK-OFF"
    )
)


# ============================================================
# Summary
# ============================================================

trigger_summary = (
    hard
    .groupby(
        "trigger",
        dropna=False,
    )
    .agg(

        days=(
            "date",
            "count",
        ),

        avg_phase_cut=(
            "phase_cap_effect",
            "mean",
        ),

        avg_final_budget=(
            "final_budget",
            "mean",
        ),

        one_day_candidates=(
            "one_day_hard_candidate",
            "sum",
        ),

    )
    .reset_index()
    .sort_values(
        "days",
        ascending=False,
    )
)


# ============================================================
# Print
# ============================================================

print(
    "\n"
    "=== FILTER13 HARD RISK-OFF "
    "TRIGGER ATTRIBUTION ==="
)

print(
    "\n[PERIOD]"
)

print(
    "ROWS:",
    len(d),
)

print(
    "FROM:",
    d["date"].min().date(),
)

print(
    "TO  :",
    d["date"].max().date(),
)


print(
    "\n[HARD RISK-OFF]"
)

print(
    "HARD DAYS:",
    len(hard),
)


print(
    "\n=== TRIGGER SUMMARY ==="
)

print(
    trigger_summary.to_string(
        index=False
    )
)


print(
    "\n=== SIGMA ABS DIRECTION CHECK ==="
)

print(
    hard[
        "sigma_direction_check"
    ]
    .value_counts(
        dropna=False
    )
    .to_string()
)


print(
    "\n=== ONE-DAY HARD CANDIDATES ==="
)

print(
    "COUNT:",
    int(
        hard[
            "one_day_hard_candidate"
        ].sum()
    ),
    "/",
    len(hard),
)


print(
    "\n=== HARD DAY DETAIL ==="
)

detail_cols = [

    "date",

    "market_regime",

    "macro_narrative",

    "trigger",

    "US10Y_DIR_AUDIT",
    "DXY_DIR_AUDIT",
    "VIX_DIR_AUDIT",
    "WTI_DIR_AUDIT",

    "US10Y_Z_AUDIT",
    "DXY_Z_AUDIT",
    "VIX_Z_AUDIT",
    "WTI_Z_AUDIT",

    "sigma_direction_check",

    "prev_regime",
    "next_regime",

    "one_day_hard_candidate",

    "pre_cap_budget",
    "phase_cap",
    "phase_cap_effect",
    "final_budget",
]


print(
    hard[
        detail_cols
    ]
    .to_string(
        index=False
    )
)


# ============================================================
# Save
# ============================================================

hard[
    detail_cols
].to_csv(
    OUTPUT_DAILY,
    index=False,
)

trigger_summary.to_csv(
    OUTPUT_SUMMARY,
    index=False,
)


print(
    "\n[SAVED]",
    OUTPUT_DAILY,
)

print(
    "[SAVED]",
    OUTPUT_SUMMARY,
)


print(
    "\n"
    "HARD TRIGGER ATTRIBUTION COMPLETE."
)

print(
    "Do NOT modify Filter13 yet."
)