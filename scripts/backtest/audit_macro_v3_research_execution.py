from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"

for p in (ROOT, SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import filters.strategist_filters as sf
from scripts.backtest.market_data_builder import build_market_data


# ============================================================
# FROZEN CONTRACT
# ============================================================

RESULTS = ROOT / "data/backtest/results"

BASELINE_FILE = (
    RESULTS
    / "final_13_15_18_parity_closeout"
    / "final_13_15_18_parity_daily.csv"
)

CONTRACT_FILE = (
    RESULTS
    / "macro_v3_execution_contract_v1"
    / "macro_v3_execution_contract_daily.csv"
)

SPEC_FILE = (
    RESULTS
    / "macro_production_repair_spec_v3"
    / "macro_production_repair_spec_v3.json"
)

OUT = (
    RESULTS
    / "macro_v3_research_execution_harness_v1"
)

OUT.mkdir(parents=True, exist_ok=True)

CHECKPOINT = OUT / "macro_v3_checkpoint.csv"
DAILY_OUT = OUT / "macro_v3_execution_daily.csv"
SUMMARY_OUT = OUT / "macro_v3_execution_summary.csv"
ERROR_OUT = OUT / "macro_v3_execution_errors.csv"
AUDIT_OUT = OUT / "macro_v3_execution_audit.txt"

EXPECTED_SPEC_HASH = (
    "f4473f73c4f7e8861e2797e93ee5cc4c"
    "f37e543f190f8ea48b3f31151010bfa6"
)

CHECKPOINT_EVERY = 100


# ============================================================
# HELPERS
# ============================================================

def quiet_call(fn, *args, **kwargs):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn(*args, **kwargs)


def scalar(x):
    if x is None:
        return np.nan
    try:
        return float(x)
    except Exception:
        return np.nan


def first_numeric(md, keys):
    for key in keys:
        if key in md:
            value = scalar(md.get(key))
            if not np.isnan(value):
                return value
    return np.nan


def series_today(md, key):
    obj = md.get(key)

    if isinstance(obj, dict):
        return scalar(obj.get("today"))

    return scalar(obj)


def find_function(names):
    for name in names:
        fn = getattr(sf, name, None)
        if callable(fn):
            return name, fn
    return None, None


def get_tape(md):
    tape = md.get("CROSS_ASSET_TAPE")

    if isinstance(tape, dict):
        return tape

    fn = getattr(sf, "build_cross_asset_tape", None)

    if not callable(fn):
        raise RuntimeError(
            "Production build_cross_asset_tape not found."
        )

    tape = quiet_call(fn, md)

    if not isinstance(tape, dict):
        raise RuntimeError(
            "Production build_cross_asset_tape did not return dict."
        )

    md["CROSS_ASSET_TAPE"] = tape
    return tape


# ============================================================
# SAFETY / INPUT
# ============================================================

print("=" * 126)
print("MACRO V3 — RESUMABLE RESEARCH EXECUTION HARNESS")
print("=" * 126)

for path in (
    BASELINE_FILE,
    CONTRACT_FILE,
    SPEC_FILE,
):
    if not path.exists():
        raise FileNotFoundError(path)

actual_hash = hashlib.sha256(
    SPEC_FILE.read_bytes()
).hexdigest()

if actual_hash != EXPECTED_SPEC_HASH:
    raise RuntimeError(
        "V3 SPEC HASH MISMATCH\n"
        f"Expected: {EXPECTED_SPEC_HASH}\n"
        f"Actual  : {actual_hash}"
    )

print("Spec hash : PASS")


# ============================================================
# LOAD FROZEN BASELINE
# ============================================================

base = pd.read_csv(BASELINE_FILE)
contract = pd.read_csv(CONTRACT_FILE)

for frame in (base, contract):
    frame["signal_date"] = pd.to_datetime(frame["signal_date"])
    frame["execution_date"] = pd.to_datetime(frame["execution_date"])

required_base = [
    "signal_date",
    "execution_date",
    "macro_narrative",
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
]

required_contract = [
    "signal_date",
    "execution_date",
    "raw_macro_narrative",
    "strategic_macro_state",
]

for c in required_base:
    if c not in base.columns:
        raise RuntimeError(f"Missing baseline column: {c}")

for c in required_contract:
    if c not in contract.columns:
        raise RuntimeError(f"Missing contract column: {c}")


df = base.merge(
    contract[
        [
            "signal_date",
            "execution_date",
            "raw_macro_narrative",
            "strategic_macro_state",
        ]
    ],
    on=["signal_date", "execution_date"],
    how="left",
    validate="one_to_one",
)

df = (
    df.sort_values(["signal_date", "execution_date"])
    .reset_index(drop=True)
)

if len(df) != len(base):
    raise RuntimeError("DATE SET IDENTITY FAILURE")

# ============================================================
# P2 INITIAL WARM-UP CONTRACT
# ============================================================
#
# A strategic state cannot exist until two consecutive PIT
# observations confirm the first valid RAW state.
#
# Therefore an initial unresolved row is expected under P2.
# Missing strategic states are authorized ONLY when they form
# one contiguous prefix at the beginning of the sample.
#
# Never backfill from future observations.
# ============================================================

strategic_missing = df["strategic_macro_state"].isna()

if strategic_missing.any():

    missing_idx = df.index[strategic_missing].tolist()
    expected_prefix = list(range(len(missing_idx)))

    if missing_idx != expected_prefix:
        raise RuntimeError(
            "Strategic macro state has non-initial missing rows: "
            f"{missing_idx[:20]}"
        )

    print()
    print("===== P2 INITIAL WARM-UP =====")
    print("Unresolved rows :", len(missing_idx))
    print(
        "Dates           :",
        ", ".join(
            df.loc[
                strategic_missing,
                "signal_date"
            ].dt.strftime("%Y-%m-%d")
        )
    )
    print("Treatment       : EXCLUDE FROM V3 PROPAGATION")
    print("Future backfill : NO")

    df = (
        df.loc[~strategic_missing]
        .copy()
        .reset_index(drop=True)
    )

raw_identity = (
    df["macro_narrative"].astype(str)
    == df["raw_macro_narrative"].astype(str)
)

if not raw_identity.all():
    raise RuntimeError("RAW narrative identity failed.")

print(f"Rows      : {len(df)}")
print("RAW       : PASS")


# ============================================================
# PRODUCTION FUNCTION DISCOVERY
# ============================================================

f13_name, f13 = find_function([
    "narrative_engine_filter",
])

f15_name, f15 = find_function([
    "volatility_controlled_exposure_filter",
    "volatility_controlled_exposure",
])

f18_name, f18 = find_function([
    "sector_allocation_filter",
    "sector_allocation",
])

regime_name, regime_fn = find_function([
    "map_to_portfolio_regime",
])

if f13 is None:
    raise RuntimeError("Filter13 function not found.")

if f15 is None:
    raise RuntimeError("Filter15 function not found.")

if f18 is None:
    raise RuntimeError("Filter18 function not found.")

if regime_fn is None:
    raise RuntimeError("map_to_portfolio_regime not found.")

print()
print("===== FUNCTIONS =====")
print("Filter13 :", f13_name)
print("Filter15 :", f15_name)
print("Filter18 :", f18_name)
print("Regime   :", regime_name)


# ============================================================
# CHECKPOINT / RESUME
# ============================================================

records = []

if CHECKPOINT.exists():

    checkpoint_df = pd.read_csv(CHECKPOINT)

    if len(checkpoint_df):

        checkpoint_df["signal_date"] = pd.to_datetime(
            checkpoint_df["signal_date"]
        )

        records = checkpoint_df.to_dict("records")

        completed_dates = set(
            checkpoint_df["signal_date"]
            .dt.strftime("%Y-%m-%d")
        )

        print()
        print("===== RESUME =====")
        print("Checkpoint rows :", len(checkpoint_df))
        print(
            "Last date       :",
            checkpoint_df["signal_date"].max().date(),
        )

    else:
        completed_dates = set()

else:
    completed_dates = set()

    print()
    print("===== RESUME =====")
    print("No checkpoint. Starting from row 1.")


# ============================================================
# IMPORTANT:
#
# We do NOT recursively carry a counterfactual PREV_EXPOSURE
# from an interrupted checkpoint.
#
# This harness is currently a structural propagation audit.
#
# Existing recursive Filter15 state must not silently depend
# on whether the process was restarted.
#
# Therefore baseline / CF execution is rebuilt independently
# per PIT observation here.
#
# If exact recursive V3 Filter15 execution is later required,
# that receives its own explicit state-machine audit.
# ============================================================


errors = []

processed_this_run = 0


# ============================================================
# EXECUTION LOOP
# ============================================================

for i, row in df.iterrows():

    signal_date = row["signal_date"]
    execution_date = row["execution_date"]

    signal_key = signal_date.strftime("%Y-%m-%d")

    if signal_key in completed_dates:
        continue

    raw_macro = str(row["raw_macro_narrative"])
    strategic_macro = str(row["strategic_macro_state"])

    try:

        # ----------------------------------------------------
        # PIT MARKET DATA
        # ----------------------------------------------------

        md = quiet_call(
            build_market_data,
            signal_key,
        )

        if not isinstance(md, dict):
            raise RuntimeError(
                "build_market_data did not return dict."
            )

        md = copy.deepcopy(md)

        # ----------------------------------------------------
        # CURRENT PRODUCTION TAPE
        # ----------------------------------------------------

        tape = get_tape(md)

        production_raw = quiet_call(
            sf.interpret_macro_narrative,
            tape,
        )

        if str(production_raw) != raw_macro:
            raise RuntimeError(
                "RAW narrative mismatch "
                f"frozen={raw_macro} "
                f"rebuilt={production_raw}"
            )

        # ----------------------------------------------------
        # SPLIT OBJECTS
        # ----------------------------------------------------

        baseline_md = copy.deepcopy(md)
        cf_md = copy.deepcopy(md)

        # ====================================================
        # BASELINE MACRO
        # ====================================================

        baseline_md["MACRO_NARRATIVE"] = raw_macro

        baseline_policy = str(
            baseline_md.get(
                "POLICY_BACKBONE_STATE",
                "MIXED",
            )
        )

        baseline_regime = quiet_call(
            regime_fn,
            baseline_policy,
            raw_macro,
            tape,
        )

        baseline_md["MARKET_REGIME"] = baseline_regime
        baseline_md["CROSS_ASSET_TAPE"] = copy.deepcopy(tape)

        # ====================================================
        # V3 COUNTERFACTUAL MACRO
        # ====================================================

        cf_md["RAW_MACRO_NARRATIVE"] = raw_macro
        cf_md["STRATEGIC_MACRO_STATE"] = strategic_macro

        # Research-only intervention.
        # Production source remains untouched.

        cf_md["MACRO_NARRATIVE"] = strategic_macro

        cf_policy = str(
            cf_md.get(
                "POLICY_BACKBONE_STATE",
                "MIXED",
            )
        )

        cf_regime = quiet_call(
            regime_fn,
            cf_policy,
            strategic_macro,
            tape,
        )

        cf_md["MARKET_REGIME"] = cf_regime
        cf_md["CROSS_ASSET_TAPE"] = copy.deepcopy(tape)

        # ----------------------------------------------------
        # FAST PIT SNAPSHOT
        # ----------------------------------------------------

        hy_today = series_today(md, "HY_OAS")
        vix_today = series_today(md, "VIX")

        # ====================================================
        # FILTER13
        # ====================================================

        quiet_call(f13, baseline_md)
        quiet_call(f13, cf_md)

        baseline_13 = first_numeric(
            baseline_md,
            ["RISK_BUDGET", "RISK_BUDGET_13"],
        )

        cf_13 = first_numeric(
            cf_md,
            ["RISK_BUDGET", "RISK_BUDGET_13"],
        )

        frozen_13 = scalar(row["risk_budget_13"])

        baseline_13_match = (
            not np.isnan(baseline_13)
            and np.isclose(
                baseline_13,
                frozen_13,
                atol=1e-9,
                rtol=0,
            )
        )

        # ====================================================
        # FILTER15 — EXISTING LOGIC ONLY
        # ====================================================

        quiet_call(f15, baseline_md)
        quiet_call(f15, cf_md)

        baseline_15 = first_numeric(
            baseline_md,
            [
                "RECOMMENDED_EXPOSURE",
                "EXPOSURE_15",
            ],
        )

        cf_15 = first_numeric(
            cf_md,
            [
                "RECOMMENDED_EXPOSURE",
                "EXPOSURE_15",
            ],
        )

        frozen_15 = scalar(row["exposure_15"])

        baseline_15_match = (
            not np.isnan(baseline_15)
            and np.isclose(
                baseline_15,
                frozen_15,
                atol=1e-9,
                rtol=0,
            )
        )

        # ----------------------------------------------------
        # SEMANTIC BOUNDARY DIAGNOSTIC
        # ----------------------------------------------------

        strategic_credit = (
            strategic_macro == "CREDIT_STRESS"
        )

        raw_credit = (
            raw_macro == "CREDIT_STRESS"
        )

        # Diagnostic thresholds ONLY.
        # Not a new Production fast-shock contract.

        hy_fast_crisis = (
            not np.isnan(hy_today)
            and hy_today >= 6.0
        )

        vix_fast_panic = (
            not np.isnan(vix_today)
            and vix_today >= 30.0
        )

        strategic_credit_only = (
            strategic_credit
            and not raw_credit
            and not hy_fast_crisis
            and not vix_fast_panic
        )

        f15_semantic_contamination = (
            strategic_credit_only
            and not np.isnan(cf_15)
            and cf_15 == 0
        )

        # ====================================================
        # FILTER18
        # ====================================================

        quiet_call(f18, baseline_md)
        quiet_call(f18, cf_md)

        baseline_18 = first_numeric(
            baseline_md,
            [
                "ALLOCATED_EQUITY",
                "ALLOCATED_EQUITY_18",
            ],
        )

        cf_18 = first_numeric(
            cf_md,
            [
                "ALLOCATED_EQUITY",
                "ALLOCATED_EQUITY_18",
            ],
        )

        frozen_18 = scalar(row["allocated_equity_18"])

        baseline_18_match = (
            not np.isnan(baseline_18)
            and np.isclose(
                baseline_18,
                frozen_18,
                atol=1e-9,
                rtol=0,
            )
        )

        # ====================================================
        # RECORD
        # ====================================================

        records.append({
            "signal_date": signal_key,
            "execution_date":
                execution_date.strftime("%Y-%m-%d"),

            "raw_macro_narrative": raw_macro,
            "strategic_macro_state": strategic_macro,

            "macro_state_changed":
                raw_macro != strategic_macro,

            "baseline_market_regime":
                baseline_regime,

            "cf_market_regime":
                cf_regime,

            "market_regime_changed":
                baseline_regime != cf_regime,

            "frozen_13": frozen_13,
            "baseline_13": baseline_13,
            "cf_13": cf_13,

            "delta_13":
                cf_13 - baseline_13
                if (
                    not np.isnan(cf_13)
                    and not np.isnan(baseline_13)
                )
                else np.nan,

            "baseline_13_match":
                baseline_13_match,

            "frozen_15": frozen_15,
            "baseline_15": baseline_15,
            "cf_15_existing_logic": cf_15,

            "delta_15_existing_logic":
                cf_15 - baseline_15
                if (
                    not np.isnan(cf_15)
                    and not np.isnan(baseline_15)
                )
                else np.nan,

            "baseline_15_match":
                baseline_15_match,

            "strategic_credit":
                strategic_credit,

            "raw_credit":
                raw_credit,

            "hy_oas_today":
                hy_today,

            "vix_today":
                vix_today,

            "strategic_credit_only":
                strategic_credit_only,

            "f15_semantic_contamination":
                f15_semantic_contamination,

            "frozen_18": frozen_18,
            "baseline_18": baseline_18,
            "cf_18": cf_18,

            "delta_18":
                cf_18 - baseline_18
                if (
                    not np.isnan(cf_18)
                    and not np.isnan(baseline_18)
                )
                else np.nan,

            "baseline_18_match":
                baseline_18_match,
        })

        completed_dates.add(signal_key)
        processed_this_run += 1

        # ----------------------------------------------------
        # CHECKPOINT
        # ----------------------------------------------------

        if processed_this_run % CHECKPOINT_EVERY == 0:

            cp = pd.DataFrame(records)

            cp = (
                cp.drop_duplicates(
                    subset=["signal_date"],
                    keep="last",
                )
                .sort_values("signal_date")
            )

            cp.to_csv(
                CHECKPOINT,
                index=False,
            )

            print(
                f"[CHECKPOINT] "
                f"{len(cp):>4}/{len(df)} "
                f"through {signal_key}"
            )

    except Exception as exc:

        errors.append({
            "signal_date": signal_key,
            "execution_date":
                execution_date.strftime("%Y-%m-%d"),
            "error": repr(exc),
        })

        print(
            f"[ERROR] {signal_key}: {repr(exc)}"
        )

        # Fail immediately.
        # Do not silently skip a PIT observation.

        if records:
            pd.DataFrame(records).to_csv(
                CHECKPOINT,
                index=False,
            )

        pd.DataFrame(errors).to_csv(
            ERROR_OUT,
            index=False,
        )

        raise


# ============================================================
# FINALIZE
# ============================================================

res = pd.DataFrame(records)

res = (
    res.drop_duplicates(
        subset=["signal_date"],
        keep="last",
    )
    .sort_values("signal_date")
    .reset_index(drop=True)
)

if len(res) != len(df):
    raise RuntimeError(
        "FINAL ROW ACCOUNTING FAILURE: "
        f"{len(res)} != {len(df)}"
    )


# ============================================================
# BASELINE PARITY
# ============================================================

baseline_13_pass = bool(
    res["baseline_13_match"].all()
)

baseline_15_pass = bool(
    res["baseline_15_match"].all()
)

baseline_18_pass = bool(
    res["baseline_18_match"].all()
)


# ============================================================
# STRUCTURAL SUMMARY
# ============================================================

def delta_summary(stage, column):

    values = pd.to_numeric(
        res[column],
        errors="coerce",
    )

    changed = int(
        (values.abs() > 1e-12).sum()
    )

    return {
        "stage": stage,
        "observations": len(res),
        "changed_days": changed,
        "changed_rate": changed / len(res),
        "mean_delta": values.mean(),
        "median_delta": values.median(),
        "mean_abs_delta": values.abs().mean(),
    }


summary_rows = [
    {
        "stage": "MACRO_STATE",
        "observations": len(res),
        "changed_days":
            int(res["macro_state_changed"].sum()),
        "changed_rate":
            float(res["macro_state_changed"].mean()),
        "mean_delta": np.nan,
        "median_delta": np.nan,
        "mean_abs_delta": np.nan,
    },
    {
        "stage": "MARKET_REGIME",
        "observations": len(res),
        "changed_days":
            int(res["market_regime_changed"].sum()),
        "changed_rate":
            float(res["market_regime_changed"].mean()),
        "mean_delta": np.nan,
        "median_delta": np.nan,
        "mean_abs_delta": np.nan,
    },
    delta_summary(
        "FILTER13",
        "delta_13",
    ),
    delta_summary(
        "FILTER15_EXISTING_LOGIC",
        "delta_15_existing_logic",
    ),
    delta_summary(
        "FILTER18",
        "delta_18",
    ),
]

summary = pd.DataFrame(summary_rows)


strategic_credit_only_days = int(
    res["strategic_credit_only"].sum()
)

contaminated_days = int(
    res["f15_semantic_contamination"].sum()
)


# ============================================================
# GATES
# ============================================================

gates = {
    "SPEC_HASH_IDENTITY":
        actual_hash == EXPECTED_SPEC_HASH,

    "ROW_ACCOUNTING":
        len(res) == len(df),

    "BASELINE_FILTER13_PARITY":
        baseline_13_pass,

    "BASELINE_FILTER15_PARITY":
        baseline_15_pass,

    "BASELINE_FILTER18_PARITY":
        baseline_18_pass,
}

overall = all(gates.values())


# ============================================================
# SAVE FINAL
# ============================================================

res.to_csv(
    DAILY_OUT,
    index=False,
)

summary.to_csv(
    SUMMARY_OUT,
    index=False,
)

pd.DataFrame(errors).to_csv(
    ERROR_OUT,
    index=False,
)


# ============================================================
# AUDIT MEMO
# ============================================================

memo = [
    "MACRO V3 — RESUMABLE RESEARCH EXECUTION HARNESS",
    "=" * 90,
    "",
    f"Rows                         : {len(res)}",
    f"Spec SHA256                  : {actual_hash}",
    "",
    "BASELINE PARITY",
    "-" * 90,
    f"Filter13                     : {'PASS' if baseline_13_pass else 'FAIL'}",
    f"Filter15                     : {'PASS' if baseline_15_pass else 'FAIL'}",
    f"Filter18                     : {'PASS' if baseline_18_pass else 'FAIL'}",
    "",
    "MACRO V3",
    "-" * 90,
    f"RAW != Strategic days        : {int(res['macro_state_changed'].sum())}",
    f"MARKET_REGIME changed days   : {int(res['market_regime_changed'].sum())}",
    "",
    "FILTER15 SEMANTIC BOUNDARY",
    "-" * 90,
    f"Strategic CREDIT only days   : {strategic_credit_only_days}",
    f"Potential contaminated zeros : {contaminated_days}",
    "",
    "SAFETY",
    "-" * 90,
    "Production modified          : NO",
    "Filter13/15/18 source        : UNCHANGED",
    "Returns used                 : NO",
    "Performance used             : NO",
    "Parameter tuning             : NO",
    "Commit                       : NO",
    "",
    f"STATUS : {'PASS' if overall else 'FAIL'}",
]

AUDIT_OUT.write_text(
    "\n".join(memo) + "\n",
    encoding="utf-8",
)


# ============================================================
# OUTPUT
# ============================================================

print()
print("=" * 126)
print("MACRO V3 — RESEARCH EXECUTION RESULT")
print("=" * 126)

print()
print("===== EXECUTION =====")
print("Rows       :", len(res))
print("Errors     :", len(errors))
print("Checkpoint :", CHECKPOINT)

print()
print("===== BASELINE PARITY =====")
print(
    "Filter13 :",
    "PASS" if baseline_13_pass else "FAIL"
)
print(
    "Filter15 :",
    "PASS" if baseline_15_pass else "FAIL"
)
print(
    "Filter18 :",
    "PASS" if baseline_18_pass else "FAIL"
)

print()
print("===== STRUCTURAL PROPAGATION =====")
print(
    summary.to_string(
        index=False,
        formatters={
            "changed_rate":
                lambda x: f"{x:.2%}",
            "mean_delta":
                lambda x: (
                    ""
                    if pd.isna(x)
                    else f"{x:.4f}"
                ),
            "median_delta":
                lambda x: (
                    ""
                    if pd.isna(x)
                    else f"{x:.4f}"
                ),
            "mean_abs_delta":
                lambda x: (
                    ""
                    if pd.isna(x)
                    else f"{x:.4f}"
                ),
        },
    )
)

print()
print("===== FILTER15 SEMANTIC BOUNDARY =====")
print(
    "Strategic CREDIT_STRESS only days :",
    strategic_credit_only_days,
)
print(
    "Potential contaminated zero days  :",
    contaminated_days,
)

print()
print("=" * 126)
print("RESEARCH GATES")
print("=" * 126)

for name, passed in gates.items():
    print(
        f"{name:<36} : "
        f"{'PASS' if passed else 'FAIL'}"
    )

print()
print(
    "STATUS :",
    "PASS" if overall else "FAIL"
)

print()
print("===== ARTIFACTS =====")
print("Daily      :", DAILY_OUT)
print("Summary    :", SUMMARY_OUT)
print("Errors     :", ERROR_OUT)
print("Audit      :", AUDIT_OUT)
print("Checkpoint :", CHECKPOINT)

print()
print("PRODUCTION MODIFIED : NO")
print("FILTER13/15/18 CODE : UNCHANGED")
print("RETURNS USED        : NO")
print("PERFORMANCE USED    : NO")
print("PARAMETER TUNING    : NO")
print("COMMIT              : NO")

