from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

CAUSAL_PATH = (
    ROOT
    / "data/backtest/results/macro_v4_causal_propagation_v1"
    / "macro_v3_counterfactual_daily.csv"
)

BASELINE_PATH = (
    ROOT
    / "data/backtest/results/final_13_15_18_parity_closeout"
    / "final_13_15_18_parity_daily.csv"
)

ATTR_PATH = (
    ROOT
    / "data/backtest/results/macro_v4_filter18_path_attribution_v1"
    / "filter18_path_attribution_daily.csv"
)

OUT_DIR = (
    ROOT
    / "data/backtest/results"
    / "macro_v4_filter18_macro_profile_path_v1"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

DAILY_OUT = OUT_DIR / "filter18_macro_profile_path_daily.csv"
SUMMARY_OUT = OUT_DIR / "filter18_macro_profile_path_summary.csv"
AUDIT_OUT = OUT_DIR / "filter18_macro_profile_path_audit.txt"


def normalize_date(s):
    return pd.to_datetime(s, errors="coerce").dt.normalize()


def first_existing(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None


print("=" * 120)
print("MACRO V4 — FILTER18 MACRO PROFILE DIRECT PATH AUDIT")
print("=" * 120)

print()
print("Production modified : NO")
print("Returns used        : NO")
print("Performance used    : NO")
print("Parameter tuning    : NO")
print("Engine modified     : NO")
print()


for p in (CAUSAL_PATH, BASELINE_PATH, ATTR_PATH):
    if not p.exists():
        raise FileNotFoundError(
            f"Required artifact missing: {p}"
        )


causal = pd.read_csv(CAUSAL_PATH)
baseline = pd.read_csv(BASELINE_PATH)
attr = pd.read_csv(ATTR_PATH)


for df in (causal, baseline, attr):
    if "signal_date" not in df.columns:
        raise RuntimeError(
            "signal_date missing from required artifact."
        )
    df["signal_date"] = normalize_date(df["signal_date"])


# ============================================================
# Identify the 352 direct/other Filter18 rows
# ============================================================

path_col = first_existing(
    attr,
    [
        "path_attribution",
        "path",
        "attribution",
        "causal_path",
    ],
)

if path_col is None:
    raise RuntimeError(
        "Could not identify Filter18 path attribution column.\n"
        f"Available columns: {attr.columns.tolist()}"
    )


target_label = "DIRECT_OR_OTHER_FILTER18_PATH"

target = attr[
    attr[path_col].astype(str) == target_label
].copy()

if len(target) != 352:
    raise RuntimeError(
        "Expected exactly 352 DIRECT_OR_OTHER_FILTER18_PATH rows, "
        f"found {len(target)}."
    )


# ============================================================
# Existing macro profile columns?
#
# If the causal/baseline artifacts already carry the actual
# Filter18 profile, use them directly.
# ============================================================

baseline_profile_col = first_existing(
    baseline,
    [
        "macro_regime_profile",
        "MACRO_REGIME_PROFILE",
        "macro_profile",
        "filter18_macro_profile",
    ],
)

causal_profile_col = first_existing(
    causal,
    [
        "macro_regime_profile",
        "MACRO_REGIME_PROFILE",
        "macro_profile",
        "filter18_macro_profile",
    ],
)


# ============================================================
# Join target rows to causal + baseline
# ============================================================

base_cols = ["signal_date"]

if baseline_profile_col:
    base_cols.append(baseline_profile_col)

causal_cols = ["signal_date"]

if causal_profile_col:
    causal_cols.append(causal_profile_col)

for c in [
    "v4_state",
    "strategic_market_regime",
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
    "cash_weight",
]:
    if c in causal.columns and c not in causal_cols:
        causal_cols.append(c)


out = (
    target
    .merge(
        baseline[base_cols],
        on="signal_date",
        how="left",
        suffixes=("", "_baseline"),
    )
    .merge(
        causal[causal_cols],
        on="signal_date",
        how="left",
        suffixes=("", "_v4"),
    )
)


# ============================================================
# IMPORTANT GATE
#
# We must NOT invent/reconstruct a Filter18 macro profile here.
# The purpose is to verify the ACTUAL profile used by Filter18.
#
# If historical artifacts did not capture it, this audit stops
# and tells us to instrument the causal harness.
# ============================================================

if baseline_profile_col is None or causal_profile_col is None:

    report = [
        "=" * 120,
        "MACRO V4 — FILTER18 MACRO PROFILE DIRECT PATH AUDIT",
        "=" * 120,
        "",
        "TARGET ROWS",
        f"DIRECT_OR_OTHER_FILTER18_PATH : {len(target)}",
        "",
        "ACTUAL PROFILE AVAILABILITY",
        f"Baseline profile captured : {'YES' if baseline_profile_col else 'NO'}",
        f"V4 profile captured       : {'YES' if causal_profile_col else 'NO'}",
        "",
        "STATUS : PROFILE NOT CAPTURED — INSTRUMENTATION REQUIRED",
        "",
        "INTERPRETATION:",
        "The existing artifacts are sufficient to identify the 352 Filter18-only",
        "allocation changes, but they do not contain the actual MACRO_REGIME_PROFILE",
        "used inside Filter18.",
        "",
        "Do NOT infer the profile after the fact.",
        "Next step is to capture market_data['MACRO_REGIME_PROFILE'] directly",
        "from baseline and V4 Filter18 execution, then compare the same 352 rows.",
        "",
        "Production modified : NO",
        "Returns used        : NO",
        "Performance used    : NO",
        "Parameter tuning    : NO",
        "=" * 120,
    ]

    text = "\n".join(report)

    AUDIT_OUT.write_text(
        text,
        encoding="utf-8",
    )

    print(text)

    print()
    print("AVAILABLE BASELINE COLUMNS:")
    print(baseline.columns.tolist())

    print()
    print("AVAILABLE V4 CAUSAL COLUMNS:")
    print(causal.columns.tolist())

    raise SystemExit(2)


# ============================================================
# Normalize actual profiles
# ============================================================

# Resolve merge naming safely.
baseline_actual_col = baseline_profile_col

if (
    baseline_profile_col == causal_profile_col
    and baseline_profile_col in out.columns
    and f"{baseline_profile_col}_v4" in out.columns
):
    baseline_actual_col = baseline_profile_col
    causal_actual_col = f"{causal_profile_col}_v4"

elif causal_profile_col in out.columns:
    causal_actual_col = causal_profile_col

else:
    possible = [
        c for c in out.columns
        if causal_profile_col.lower() in c.lower()
    ]

    if not possible:
        raise RuntimeError(
            "Could not resolve merged V4 macro profile column."
        )

    causal_actual_col = possible[-1]


out["baseline_macro_profile"] = (
    out[baseline_actual_col]
    .fillna("N/A")
    .astype(str)
    .str.upper()
)

out["v4_macro_profile"] = (
    out[causal_actual_col]
    .fillna("N/A")
    .astype(str)
    .str.upper()
)

out["profile_changed"] = (
    out["baseline_macro_profile"]
    != out["v4_macro_profile"]
)


# ============================================================
# Diagnostics
# ============================================================

profile_changed = out[
    out["profile_changed"]
].copy()

profile_unchanged = out[
    ~out["profile_changed"]
].copy()


transition_counts = (
    profile_changed
    .groupby(
        [
            "baseline_macro_profile",
            "v4_macro_profile",
        ],
        dropna=False,
    )
    .size()
    .reset_index(name="days")
    .sort_values(
        "days",
        ascending=False,
    )
)


summary = pd.DataFrame(
    [
        {
            "metric": "direct_filter18_path_days",
            "value": len(out),
        },
        {
            "metric": "macro_profile_changed_days",
            "value": len(profile_changed),
        },
        {
            "metric": "macro_profile_unchanged_days",
            "value": len(profile_unchanged),
        },
        {
            "metric": "macro_profile_explanation_share",
            "value": (
                len(profile_changed) / len(out)
                if len(out)
                else 0.0
            ),
        },
    ]
)


# ============================================================
# Gate interpretation
# ============================================================

share = (
    len(profile_changed) / len(out)
    if len(out)
    else 0.0
)

if len(profile_unchanged) == 0:
    status = "PASS — FILTER18 DIRECT PATH FULLY EXPLAINED BY MACRO PROFILE"

elif len(profile_changed) > 0:
    status = "PARTIAL — MACRO PROFILE EXPLAINS PART OF FILTER18 DIRECT PATH"

else:
    status = "FAIL — MACRO PROFILE DOES NOT EXPLAIN FILTER18 DIRECT PATH"


# ============================================================
# Write artifacts
# ============================================================

out.to_csv(
    DAILY_OUT,
    index=False,
)

summary.to_csv(
    SUMMARY_OUT,
    index=False,
)


lines = [
    "=" * 120,
    "MACRO V4 — FILTER18 MACRO PROFILE DIRECT PATH AUDIT",
    "=" * 120,
    "",
    "===== CONTRACT =====",
    f"Direct/other Filter18 path days : {len(out)}",
    f"Macro profile changed days      : {len(profile_changed)}",
    f"Macro profile unchanged days    : {len(profile_unchanged)}",
    f"Profile explanation share       : {share:.2%}",
    "",
    "===== PROFILE TRANSITIONS =====",
]

if transition_counts.empty:
    lines.append("NONE")
else:
    for _, r in transition_counts.iterrows():
        lines.append(
            f"{r['baseline_macro_profile']} "
            f"-> {r['v4_macro_profile']} "
            f": {int(r['days'])}"
        )

lines += [
    "",
    "===== INTERPRETATION =====",
    status,
    "",
    "Production modified : NO",
    "Returns used        : NO",
    "Performance used    : NO",
    "Parameter tuning    : NO",
    "Future data used    : NO",
    "",
    f"Daily   : {DAILY_OUT}",
    f"Summary : {SUMMARY_OUT}",
    f"Audit   : {AUDIT_OUT}",
    "",
    "=" * 120,
]

audit_text = "\n".join(lines)

AUDIT_OUT.write_text(
    audit_text,
    encoding="utf-8",
)

print(audit_text)

if len(profile_unchanged):
    print()
    print("===== UNEXPLAINED SAMPLE =====")

    show_cols = [
        c for c in [
            "signal_date",
            "v4_state",
            "baseline_macro_profile",
            "v4_macro_profile",
            "strategic_market_regime",
            "risk_budget_13",
            "exposure_15",
            "allocated_equity_18",
            "cash_weight",
        ]
        if c in profile_unchanged.columns
    ]

    print(
        profile_unchanged[
            show_cols
        ]
        .head(30)
        .to_string(index=False)
    )
