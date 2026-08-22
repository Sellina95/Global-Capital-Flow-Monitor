from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"

REFERENCE = RESULTS / "daily_positions_pit_safe_geo.csv"
RERUN = RESULTS / "daily_positions_pit_safe_geo_recert.csv"

OUT_DETAIL = RESULTS / "pit_geo_execution_recertification_detail.csv"
OUT_SUMMARY = RESULTS / "pit_geo_execution_recertification_summary.csv"
OUT_TXT = RESULTS / "pit_geo_execution_recertification_summary.txt"

RUNNER = ROOT / "scripts" / "backtest" / "run_backtest_pit_safe_geo.py"

KEYS = [
    "risk_budget_13",
    "exposure_15",
    "allocated_equity_18",
    "cash_weight",
]

if not REFERENCE.exists():
    raise FileNotFoundError(REFERENCE)

if not RUNNER.exists():
    raise FileNotFoundError(RUNNER)


# ============================================================
# 1. Preserve reference baseline
# ============================================================

reference = pd.read_csv(REFERENCE)

reference["signal_date"] = pd.to_datetime(
    reference["signal_date"],
    errors="coerce",
).dt.normalize()

reference = (
    reference
    .sort_values("signal_date")
    .drop_duplicates("signal_date", keep="last")
    .reset_index(drop=True)
)


# ============================================================
# 2. Temporarily patch output path of runner
#
# Do NOT overwrite reference baseline.
# ============================================================

runner_text = RUNNER.read_text(encoding="utf-8")

old = '''    / "daily_positions_pit_safe_geo.csv"
)'''

new = '''    / "daily_positions_pit_safe_geo_recert.csv"
)'''

if old not in runner_text:
    raise RuntimeError(
        "Expected OUT_PATH block not found in run_backtest_pit_safe_geo.py"
    )

patched = runner_text.replace(old, new, 1)

TMP_RUNNER = (
    ROOT
    / "scripts"
    / "backtest"
    / "_tmp_run_backtest_pit_safe_geo_recert.py"
)

TMP_RUNNER.write_text(
    patched,
    encoding="utf-8",
)


# ============================================================
# 3. Independent full-period rerun
# ============================================================

print("=" * 80)
print("PIT-SAFE + GEO EXECUTION RECERTIFICATION")
print("=" * 80)
print()
print("Running independent full-period replay...")
print()

try:
    subprocess.run(
        [sys.executable, str(TMP_RUNNER)],
        cwd=ROOT,
        check=True,
    )
finally:
    if TMP_RUNNER.exists():
        TMP_RUNNER.unlink()


if not RERUN.exists():
    raise RuntimeError(
        f"Independent rerun did not produce {RERUN}"
    )


# ============================================================
# 4. Exact comparison
# ============================================================

rerun = pd.read_csv(RERUN)

rerun["signal_date"] = pd.to_datetime(
    rerun["signal_date"],
    errors="coerce",
).dt.normalize()

rerun = (
    rerun
    .sort_values("signal_date")
    .drop_duplicates("signal_date", keep="last")
    .reset_index(drop=True)
)

m = reference[
    ["signal_date"] + KEYS
].merge(
    rerun[
        ["signal_date"] + KEYS
    ],
    on="signal_date",
    suffixes=("_REFERENCE", "_RERUN"),
    how="outer",
    indicator=True,
)


rows = []

for key in KEYS:

    a = pd.to_numeric(
        m[f"{key}_REFERENCE"],
        errors="coerce",
    )

    b = pd.to_numeric(
        m[f"{key}_RERUN"],
        errors="coerce",
    )

    comparable = (
        m["_merge"].eq("both")
        & a.notna()
        & b.notna()
    )

    mismatch = (
        comparable
        & ~np.isclose(
            a,
            b,
            rtol=0.0,
            atol=1e-12,
            equal_nan=True,
        )
    )

    delta = b - a

    rows.append({
        "contract": key,
        "comparable_rows": int(comparable.sum()),
        "mismatch_rows": int(mismatch.sum()),
        "max_abs_delta": (
            float(delta[comparable].abs().max())
            if comparable.any()
            else np.nan
        ),
        "status": (
            "PASS"
            if int(mismatch.sum()) == 0
            else "FAIL"
        ),
    })


summary = pd.DataFrame(rows)

date_only_reference = int(
    (m["_merge"] == "left_only").sum()
)

date_only_rerun = int(
    (m["_merge"] == "right_only").sum()
)

all_contracts_pass = (
    summary["status"].eq("PASS").all()
)

gate = (
    all_contracts_pass
    and date_only_reference == 0
    and date_only_rerun == 0
)


# ============================================================
# 5. Save evidence
# ============================================================

m.to_csv(
    OUT_DETAIL,
    index=False,
    encoding="utf-8-sig",
)

summary.to_csv(
    OUT_SUMMARY,
    index=False,
    encoding="utf-8-sig",
)

txt = "\n".join([
    "PIT-SAFE + GEO EXECUTION RECERTIFICATION",
    "=" * 72,
    "",
    f"Reference rows: {len(reference)}",
    f"Rerun rows: {len(rerun)}",
    f"Reference-only dates: {date_only_reference}",
    f"Rerun-only dates: {date_only_rerun}",
    "",
    *[
        (
            f"{r.contract}: {r.status} "
            f"(mismatch={r.mismatch_rows}, "
            f"max_abs_delta={r.max_abs_delta})"
        )
        for r in summary.itertuples()
    ],
    "",
    (
        "GEO-INCLUSIVE EXECUTION RECERTIFICATION: PASS"
        if gate
        else
        "GEO-INCLUSIVE EXECUTION RECERTIFICATION: FAIL"
    ),
])

OUT_TXT.write_text(
    txt,
    encoding="utf-8",
)


print()
print("=" * 80)
print("RESULT")
print("=" * 80)

print(summary.to_string(index=False))

print()
print("REFERENCE ROWS:", len(reference))
print("RERUN ROWS:", len(rerun))
print("REFERENCE-ONLY DATES:", date_only_reference)
print("RERUN-ONLY DATES:", date_only_rerun)

print()
print(
    "GEO-INCLUSIVE EXECUTION RECERTIFICATION:",
    "PASS" if gate else "FAIL",
)

print()
print("[OUTPUT]")
print(OUT_DETAIL)
print(OUT_SUMMARY)
print(OUT_TXT)
