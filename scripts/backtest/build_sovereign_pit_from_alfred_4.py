from pathlib import Path
import re
import zipfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data/backtest/results"
OUTDIR = ROOT / "data/backtest/pit_safe"
RESULTS.mkdir(parents=True, exist_ok=True)
OUTDIR.mkdir(parents=True, exist_ok=True)

END = pd.Timestamp("2026-06-18")
EVIDENCE_START = pd.Timestamp("2013-06-03")

SERIES = {
    "KR10Y": ("IRLTLT01KRM156N", "IRLTLT01KRM156N_2.zip"),
    "JP10Y": ("IRLTLT01JPM156N", "IRLTLT01JPM156N_2.zip"),
    "DE10Y": ("IRLTLT01DEM156N", "IRLTLT01DEM156N_2.zip"),
    "IL10Y": ("IRLTLT01ILM156N", "IRLTLT01ILM156N_2.zip"),
}

DETAIL_OUT = RESULTS / "sovereign_alfred_pit_4_detail.csv"
MAP_OUT = OUTDIR / "sovereign_yields_pit_4.csv"
SUMMARY_OUT = RESULTS / "sovereign_alfred_pit_4_summary.csv"


def locate_zip(filename):
    candidates = [
        ROOT / filename,
        ROOT / "data" / filename,
        ROOT / "data/backtest/vintage" / filename,
        ROOT / "data/backtest" / filename,
    ]

    for p in candidates:
        if p.exists():
            return p

    raise FileNotFoundError(
        f"{filename} not found. Put the four ZIP files in repo root."
    )


def load_alfred(name, fred_id, zip_name):
    path = locate_zip(zip_name)

    with zipfile.ZipFile(path) as z:
        csvs = [x for x in z.namelist() if x.lower().endswith(".csv")]

        if len(csvs) != 1:
            raise RuntimeError(f"{zip_name}: expected one CSV, got {csvs}")

        with z.open(csvs[0]) as f:
            df = pd.read_csv(f)

    df["observation_date"] = pd.to_datetime(
        df["observation_date"], errors="coerce"
    )

    pat = re.compile(rf"^{re.escape(fred_id)}_(\d{{8}})$")

    vintage_cols = []
    for c in df.columns:
        m = pat.match(str(c))
        if m:
            vintage_cols.append(
                (c, pd.to_datetime(m.group(1), format="%Y%m%d"))
            )

    vintage_cols.sort(key=lambda x: x[1])

    rows = []

    for _, r in df.iterrows():
        obs = r["observation_date"]

        if pd.isna(obs) or obs > END:
            continue

        # ALFRED evidence before this boundary does not prove first release.
        if obs < EVIDENCE_START:
            continue

        first_date = None
        first_value = None
        latest_value = None

        for col, vintage_date in vintage_cols:
            val = pd.to_numeric(r[col], errors="coerce")

            if pd.isna(val):
                continue

            latest_value = float(val)

            if first_date is None:
                first_date = vintage_date.normalize()
                first_value = float(val)

        if first_date is None:
            continue

        rows.append({
            "series": name,
            "observation_date": obs.normalize(),
            "available_date": first_date,
            "pit_value": first_value,
            "latest_value": latest_value,
            "release_lag_days": int(
                (first_date - obs.normalize()).days
            ),
            "was_revised": (
                abs(first_value - latest_value) > 1e-12
            ),
        })

    return pd.DataFrame(rows)


all_detail = []

for name, (fred_id, zip_name) in SERIES.items():
    x = load_alfred(name, fred_id, zip_name)

    if x.empty:
        raise RuntimeError(f"{name}: no evidenced PIT rows")

    all_detail.append(x)

detail = pd.concat(all_detail, ignore_index=True)

if (detail["release_lag_days"] < 0).any():
    bad = detail[detail["release_lag_days"] < 0]
    print(bad.to_string(index=False))
    raise SystemExit("ABORT — negative release lag detected")

detail.to_csv(DETAIL_OUT, index=False, encoding="utf-8-sig")


# ------------------------------------------------------------
# Build daily availability panel.
#
# A value becomes usable ONLY from ALFRED available_date onward.
# Then forward-fill until a newer observation becomes available.
# ------------------------------------------------------------

calendar = pd.DataFrame({
    "date": pd.date_range(EVIDENCE_START, END, freq="D")
})

pit_panel = calendar.copy()

for name in SERIES:
    x = (
        detail[detail["series"] == name]
        [["available_date", "pit_value"]]
        .sort_values("available_date")
        .drop_duplicates("available_date", keep="last")
        .rename(columns={
            "available_date": "date",
            "pit_value": name,
        })
    )

    pit_panel = pit_panel.merge(x, on="date", how="left")
    pit_panel[name] = pit_panel[name].ffill()

pit_panel.to_csv(MAP_OUT, index=False, encoding="utf-8-sig")


summary = (
    detail.groupby("series")
    .agg(
        evidenced_observations=("observation_date", "count"),
        first_evidenced_observation=("observation_date", "min"),
        last_evidenced_observation=("observation_date", "max"),
        min_release_lag_days=("release_lag_days", "min"),
        median_release_lag_days=("release_lag_days", "median"),
        max_release_lag_days=("release_lag_days", "max"),
        revised_observations=("was_revised", "sum"),
    )
    .reset_index()
)

summary.to_csv(SUMMARY_OUT, index=False, encoding="utf-8-sig")

print("=" * 80)
print("ACTIVE SOVEREIGN PIT MAP — ALFRED EVIDENCE")
print("=" * 80)
print(summary.to_string(index=False))

print()
print("NEGATIVE RELEASE LAGS:", int((detail["release_lag_days"] < 0).sum()))
print("EVIDENCE START:", EVIDENCE_START.date())
print("PRE-2013 STATUS: UNVERIFIED — NOT IMPUTED")
print("PRODUCTION MODIFIED: NO")
print("CANONICAL MASTER PANEL MODIFIED: NO")

print()
print("[OUTPUT]")
print(DETAIL_OUT)
print(MAP_OUT)
print(SUMMARY_OUT)
