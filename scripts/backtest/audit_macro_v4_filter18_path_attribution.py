from __future__ import annotations

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

CF_PATH = (
    ROOT / "data/backtest/results/"
    "macro_v4_causal_propagation_v1/"
    "macro_v3_counterfactual_daily.csv"
)

BASE_PATH = (
    ROOT / "data/backtest/results/"
    "final_13_15_18_parity_closeout/"
    "final_13_15_18_parity_daily.csv"
)

OUT_DIR = (
    ROOT / "data/backtest/results/"
    "macro_v4_filter18_path_attribution_v1"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

DAILY_PATH = OUT_DIR / "filter18_path_attribution_daily.csv"
SUMMARY_PATH = OUT_DIR / "filter18_path_attribution_summary.csv"
AUDIT_PATH = OUT_DIR / "filter18_path_attribution_audit.txt"


def changed(a, b, tol=1e-9):
    if pd.isna(a) and pd.isna(b):
        return False
    if pd.isna(a) or pd.isna(b):
        return True
    try:
        return abs(float(a) - float(b)) > tol
    except Exception:
        return str(a) != str(b)


cf = pd.read_csv(CF_PATH)
base = pd.read_csv(BASE_PATH)

required_cf = {
    "signal_date",
    "v4_state",
    "strategic_market_regime",
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
    "cash_weight",
}

required_base = {
    "signal_date",
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
    "cash_weight",
}

missing_cf = required_cf - set(cf.columns)
missing_base = required_base - set(base.columns)

if missing_cf:
    raise RuntimeError(
        f"Counterfactual missing columns: {sorted(missing_cf)}"
    )

if missing_base:
    raise RuntimeError(
        f"Baseline missing columns: {sorted(missing_base)}"
    )

cf["signal_date"] = pd.to_datetime(cf["signal_date"])
base["signal_date"] = pd.to_datetime(base["signal_date"])

base = base[
    [
        "signal_date",
        "risk_budget_13",
        "exposure_15",
        "allocated_equity_18",
        "cash_weight",
    ]
].rename(
    columns={
        "risk_budget_13": "baseline_risk_budget_13",
        "exposure_15": "baseline_exposure_15",
        "allocated_equity_18": "baseline_allocated_equity_18",
        "cash_weight": "baseline_cash_weight",
    }
)

x = cf.merge(
    base,
    on="signal_date",
    how="left",
    validate="one_to_one",
)

if x["baseline_risk_budget_13"].isna().all():
    raise RuntimeError("Baseline merge failed.")

x["filter13_changed"] = [
    changed(a, b)
    for a, b in zip(
        x["risk_budget_13"],
        x["baseline_risk_budget_13"],
    )
]

x["filter15_changed"] = [
    changed(a, b)
    for a, b in zip(
        x["exposure_15"],
        x["baseline_exposure_15"],
    )
]

x["filter18_changed"] = [
    changed(a, b)
    for a, b in zip(
        x["allocated_equity_18"],
        x["baseline_allocated_equity_18"],
    )
]

x["cash_changed"] = [
    changed(a, b)
    for a, b in zip(
        x["cash_weight"],
        x["baseline_cash_weight"],
    )
]


def classify(row):
    f13 = bool(row["filter13_changed"])
    f15 = bool(row["filter15_changed"])
    f18 = bool(row["filter18_changed"])

    if not f18:
        return "FILTER18_UNCHANGED"

    if f13 and f15:
        return "F13_AND_F15_CHANGED_BEFORE_F18"

    if f13 and not f15:
        return "F13_CHANGED_F15_ABSORBED_F18_CHANGED"

    if not f13 and f15:
        return "F15_CHANGED_WITHOUT_F13_CHANGE"

    return "DIRECT_OR_OTHER_FILTER18_PATH"


x["causal_path"] = x.apply(classify, axis=1)

changed18 = x[x["filter18_changed"]].copy()

summary = (
    changed18["causal_path"]
    .value_counts()
    .rename_axis("causal_path")
    .reset_index(name="days")
)

summary["share_of_filter18_changed"] = (
    summary["days"] / len(changed18)
    if len(changed18)
    else 0.0
)

x.to_csv(DAILY_PATH, index=False)
summary.to_csv(SUMMARY_PATH, index=False)

n = len(x)
n13 = int(x["filter13_changed"].sum())
n15 = int(x["filter15_changed"].sum())
n18 = int(x["filter18_changed"].sum())
ncash = int(x["cash_changed"].sum())

direct = int(
    (
        x["causal_path"]
        == "DIRECT_OR_OTHER_FILTER18_PATH"
    ).sum()
)

lines = [
    "=" * 110,
    "MACRO V4 — FILTER18 CAUSAL PATH ATTRIBUTION",
    "=" * 110,
    "",
    "===== CONTRACT =====",
    f"V4 observations              : {n}",
    f"Filter13 changed days         : {n13}",
    f"Filter15 changed days         : {n15}",
    f"Filter18 changed days         : {n18}",
    f"Cash changed days             : {ncash}",
    "",
    "===== FILTER18 PATH ATTRIBUTION =====",
]

for _, row in summary.iterrows():
    lines.append(
        f"{row['causal_path']:<42} "
        f"{int(row['days']):>4} "
        f"({row['share_of_filter18_changed']:.2%})"
    )

lines += [
    "",
    "===== KEY DIAGNOSTIC =====",
    f"13 unchanged + 15 unchanged + 18 changed : {direct}",
    "",
]

if n18 != 790:
    status = "FAIL — FILTER18 CHANGE COUNT DOES NOT MATCH PRIOR CAUSAL AUDIT"
elif ncash != 790:
    status = "FAIL — CASH CHANGE COUNT DOES NOT MATCH PRIOR CAUSAL AUDIT"
elif direct > 0:
    status = (
        "REQUIRES DIRECT FILTER18 PATH INSPECTION"
    )
else:
    status = (
        "PASS — ALL FILTER18 CHANGES HAVE "
        "UPSTREAM 13/15 CHANGE"
    )

lines += [
    f"STATUS : {status}",
    "",
    "Production modified : NO",
    "Returns used        : NO",
    "Performance used    : NO",
    "Parameter tuning    : NO",
    "Engine rerun        : NO",
    "",
    f"Daily   : {DAILY_PATH}",
    f"Summary : {SUMMARY_PATH}",
    "=" * 110,
]

text = "\n".join(lines)

AUDIT_PATH.write_text(text)
print(text)
