from __future__ import annotations

from pathlib import Path
from io import TextIOWrapper
import re
import zipfile

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2008-01-01")
END = pd.Timestamp("2026-06-18")

# ALFRED files supplied by user start their recorded vintage history here.
EVIDENCE_START = pd.Timestamp("2013-06-03")


SERIES = {
    "KR10Y": {
        "fred_id": "IRLTLT01KRM156N",
        "zip": "IRLTLT01KRM156N_2.zip",
    },
    "JP10Y": {
        "fred_id": "IRLTLT01JPM156N",
        "zip": "IRLTLT01JPM156N_2.zip",
    },
    "DE10Y": {
        "fred_id": "IRLTLT01DEM156N",
        "zip": "IRLTLT01DEM156N_2.zip",
    },
    "IL10Y": {
        "fred_id": "IRLTLT01ILM156N",
        "zip": "IRLTLT01ILM156N_2.zip",
    },
}


OUT_DETAIL = RESULTS / "active_sovereign_alfred_vintage_4_detail.csv"
OUT_SUMMARY = RESULTS / "active_sovereign_alfred_vintage_4_summary.csv"
OUT_PIT_MAP = RESULTS / "active_sovereign_alfred_vintage_4_pit_map.csv"
OUT_TXT = RESULTS / "active_sovereign_alfred_vintage_4_summary.txt"


def find_zip(filename: str) -> Path:
    candidates = [
        ROOT / filename,
        ROOT / "data" / "backtest" / "vintage" / filename,
        ROOT / "data" / "backtest" / filename,
    ]

    for p in candidates:
        if p.exists():
            return p

    raise FileNotFoundError(
        f"ZIP not found: {filename}\n"
        f"Put the four ALFRED ZIP files in repository root."
    )


def load_alfred_zip(path: Path, fred_id: str) -> tuple[pd.DataFrame, list[tuple[str, pd.Timestamp]]]:

    with zipfile.ZipFile(path) as zf:
        csv_names = [
            n for n in zf.namelist()
            if n.lower().endswith(".csv")
        ]

        if len(csv_names) != 1:
            raise RuntimeError(
                f"{path.name}: expected exactly one CSV, found {csv_names}"
            )

        with zf.open(csv_names[0]) as raw:
            df = pd.read_csv(raw)

    if "observation_date" not in df.columns:
        raise RuntimeError(
            f"{path.name}: observation_date missing"
        )

    df["observation_date"] = pd.to_datetime(
        df["observation_date"],
        errors="coerce",
    )

    vintage_cols = []

    pattern = re.compile(
        rf"^{re.escape(fred_id)}_(\d{{8}})$"
    )

    for col in df.columns:
        m = pattern.match(str(col))
        if not m:
            continue

        vintage_date = pd.to_datetime(
            m.group(1),
            format="%Y%m%d",
            errors="raise",
        )

        vintage_cols.append(
            (col, vintage_date)
        )

    vintage_cols.sort(
        key=lambda x: x[1]
    )

    if not vintage_cols:
        raise RuntimeError(
            f"{path.name}: no vintage columns found"
        )

    for col, _ in vintage_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    return df, vintage_cols


def values_equal(a, b) -> bool:
    if pd.isna(a) and pd.isna(b):
        return True

    if pd.isna(a) or pd.isna(b):
        return False

    return bool(
        np.isclose(
            float(a),
            float(b),
            rtol=0.0,
            atol=1e-12,
        )
    )


detail_rows = []
pit_rows = []


for series_name, spec in SERIES.items():

    fred_id = spec["fred_id"]
    zip_path = find_zip(spec["zip"])

    print()
    print("=" * 78)
    print(series_name, zip_path)
    print("=" * 78)

    df, vintage_cols = load_alfred_zip(
        zip_path,
        fred_id,
    )

    first_recorded_vintage = vintage_cols[0][1]
    last_recorded_vintage = vintage_cols[-1][1]

    print(
        "ALFRED vintage coverage:",
        first_recorded_vintage.date(),
        "->",
        last_recorded_vintage.date(),
    )

    sample = df[
        (df["observation_date"] >= START)
        & (df["observation_date"] <= END)
    ].copy()

    for _, row in sample.iterrows():

        obs_date = pd.Timestamp(
            row["observation_date"]
        ).normalize()

        # ----------------------------------------------------
        # Pre-ALFRED evidence boundary
        # ----------------------------------------------------

        if obs_date < EVIDENCE_START:

            detail_rows.append({
                "series": series_name,
                "fred_id": fred_id,
                "observation_date": obs_date,
                "first_available_date": pd.NaT,
                "release_lag_days": pd.NA,
                "first_published_value": pd.NA,
                "latest_value": pd.NA,
                "revised_after_first_release": pd.NA,
                "status": "EVIDENCE_UNAVAILABLE_PRE_2013_06_03",
            })

            continue

        # ----------------------------------------------------
        # Find first ALFRED vintage in which observation exists
        # ----------------------------------------------------

        first_col = None
        first_vintage = None
        first_value = None

        latest_value = None

        observed_values = []

        for col, vintage_date in vintage_cols:

            value = row[col]

            if pd.isna(value):
                continue

            latest_value = float(value)

            observed_values.append(
                (
                    vintage_date,
                    float(value),
                )
            )

            if first_col is None:
                first_col = col
                first_vintage = vintage_date
                first_value = float(value)

        if first_vintage is None:

            detail_rows.append({
                "series": series_name,
                "fred_id": fred_id,
                "observation_date": obs_date,
                "first_available_date": pd.NaT,
                "release_lag_days": pd.NA,
                "first_published_value": pd.NA,
                "latest_value": pd.NA,
                "revised_after_first_release": pd.NA,
                "status": "NO_RECORDED_VALUE",
            })

            continue

        lag = int(
            (
                first_vintage.normalize()
                - obs_date
            ).days
        )

        revised = not values_equal(
            first_value,
            latest_value,
        )

        status = (
            "PASS_EVIDENCED_RELEASE"
            if lag >= 0
            else "FAIL_NEGATIVE_RELEASE_LAG"
        )

        detail_rows.append({
            "series": series_name,
            "fred_id": fred_id,
            "observation_date": obs_date,
            "first_available_date": first_vintage.normalize(),
            "release_lag_days": lag,
            "first_published_value": first_value,
            "latest_value": latest_value,
            "revised_after_first_release": revised,
            "status": status,
        })

        # PIT-safe mapping:
        # use the value that actually existed on its FIRST recorded vintage.
        if lag >= 0:
            pit_rows.append({
                "series": series_name,
                "fred_id": fred_id,
                "observation_date": obs_date,
                "available_date": first_vintage.normalize(),
                "pit_value": first_value,
                "latest_value": latest_value,
                "was_revised": revised,
            })


detail = pd.DataFrame(detail_rows)
pit_map = pd.DataFrame(pit_rows)

detail.to_csv(
    OUT_DETAIL,
    index=False,
    encoding="utf-8-sig",
)

pit_map.to_csv(
    OUT_PIT_MAP,
    index=False,
    encoding="utf-8-sig",
)


def count_status(s, value):
    return int(
        (s == value).sum()
    )


summary_rows = []

for series_name in SERIES:

    x = detail[
        detail["series"] == series_name
    ].copy()

    evidenced = x[
        x["status"] == "PASS_EVIDENCED_RELEASE"
    ].copy()

    unavailable = count_status(
        x["status"],
        "EVIDENCE_UNAVAILABLE_PRE_2013_06_03",
    )

    negative = count_status(
        x["status"],
        "FAIL_NEGATIVE_RELEASE_LAG",
    )

    no_value = count_status(
        x["status"],
        "NO_RECORDED_VALUE",
    )

    revisions = int(
        evidenced[
            "revised_after_first_release"
        ]
        .fillna(False)
        .astype(bool)
        .sum()
    )

    if evidenced.empty:
        lag_min = pd.NA
        lag_median = pd.NA
        lag_max = pd.NA
    else:
        lag_min = int(
            evidenced["release_lag_days"].min()
        )
        lag_median = float(
            evidenced["release_lag_days"].median()
        )
        lag_max = int(
            evidenced["release_lag_days"].max()
        )

    summary_rows.append({
        "series": series_name,
        "rows_2008_2026": len(x),
        "evidenced_release_rows": len(evidenced),
        "pre_2013_evidence_unavailable_rows": unavailable,
        "no_recorded_value_rows": no_value,
        "negative_release_lag_failures": negative,
        "revised_rows": revisions,
        "min_release_lag_days": lag_min,
        "median_release_lag_days": lag_median,
        "max_release_lag_days": lag_max,
    })


summary = pd.DataFrame(
    summary_rows
)

summary.to_csv(
    OUT_SUMMARY,
    index=False,
    encoding="utf-8-sig",
)


negative_total = int(
    summary[
        "negative_release_lag_failures"
    ].sum()
)

unavailable_total = int(
    summary[
        "pre_2013_evidence_unavailable_rows"
    ].sum()
)


print()
print("=" * 90)
print("ACTIVE SOVEREIGN ALFRED VINTAGE AUDIT — 4 SERIES")
print("=" * 90)

print(
    summary.to_string(index=False)
)

print()
print(
    "NEGATIVE RELEASE-LAG FAILURES:",
    negative_total,
)

print(
    "PRE-2013 EVIDENCE-UNAVAILABLE OBSERVATIONS:",
    unavailable_total,
)

print()

if negative_total > 0:
    gate = (
        "SOVEREIGN RELEASE/VINTAGE GATE: FAIL"
    )
elif unavailable_total > 0:
    gate = (
        "SOVEREIGN RELEASE/VINTAGE GATE: "
        "PARTIAL PASS — 2013-06-03+ EVIDENCED; "
        "2008~2013-06-02 EVIDENCE UNAVAILABLE"
    )
else:
    gate = (
        "SOVEREIGN RELEASE/VINTAGE GATE: PASS"
    )

print(gate)


OUT_TXT.write_text(
    "\n".join([
        "ACTIVE SOVEREIGN ALFRED VINTAGE AUDIT",
        "=" * 90,
        "Scope: KR10Y / JP10Y / DE10Y / IL10Y",
        "Decision scope: frozen F13/F15/F18 82-contract universe",
        "",
        f"ALFRED evidence boundary: {EVIDENCE_START.date()}",
        f"Negative release-lag failures: {negative_total}",
        f"Pre-2013 evidence-unavailable observations: {unavailable_total}",
        "",
        gate,
        "",
        "Policy:",
        "- No release date was guessed.",
        "- Pre-2013 observations remain explicitly unverified.",
        "- For evidenced observations, PIT value = first value visible in ALFRED.",
        "- Latest revised values are not substituted for first-published values.",
    ]),
    encoding="utf-8",
)


print()
print("[OUTPUT]")
print(OUT_DETAIL)
print(OUT_SUMMARY)
print(OUT_PIT_MAP)
print(OUT_TXT)
