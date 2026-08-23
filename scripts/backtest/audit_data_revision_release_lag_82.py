from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


# =============================================================================
# Institutional Gate #3
# Data Revision / Release Lag
#
# Frozen scope:
#   F13 22 + F15 20 + F18 40 = 82 stage-contract pairs
#
# This script is AUDIT ONLY.
# It does NOT modify Production, Backtest logic, strategy parameters,
# or the frozen PIT-safe baseline.
#
# Tests:
#   1. RELEASE LAG
#      Was the observation actually available by the historical decision date?
#
#   2. REVISION
#      Did the initially published value later change?
#      Revision itself is NOT a failure.
#
#   3. PIT VALUE MATCH
#      Did the PIT-safe backtest use the value that was actually available
#      at that historical decision point, rather than a later revised value?
# =============================================================================


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
BACKTEST = DATA / "backtest"
RESULTS = BACKTEST / "results"
PIT_SAFE = BACKTEST / "pit_safe"

RESULTS.mkdir(parents=True, exist_ok=True)

OUT_DETAIL = RESULTS / "data_revision_release_lag_82_detail.csv"
OUT_SUMMARY = RESULTS / "data_revision_release_lag_82_summary.csv"
OUT_TXT = RESULTS / "data_revision_release_lag_82_summary.txt"
OUT_FAILURES = RESULTS / "data_revision_release_lag_82_failures.csv"

# Frozen local ALFRED initial-release evidence.
# These files were downloaded directly from FRED/ALFRED using
# output_type=4 and the frozen historical realtime window.
LOCAL_ALFRED = BACKTEST / "alfred_vintage_82"



# ---------------------------------------------------------------------------
# Direct FRED upstreams proven relevant by the frozen 82-contract inventory.
#
# Derived contracts such as REAL_RATE / NET_LIQ / sentiment__hy_oas inherit
# their parent PIT result and are NOT independently queried from ALFRED.
# ---------------------------------------------------------------------------

FRED_SERIES = {
    "FCI/NFCI": "NFCI",
    "TGA": "WTREGEN",
    "WALCL": "WALCL",
    "RRP": "RRPONTSYD",
    "DFII10": "DFII10",
    "DGS2": "DGS2",
    "T10Y2Y": "T10Y2Y",
    "T10YIE": "T10YIE",
    "US10Y": "DGS10",
    "HY_OAS": "BAMLH0A0HYM2",
}


# Existing sovereign evidence is intentionally reused rather than rebuilt.
ACTIVE_SOVEREIGN = {
    "KR10Y",
    "JP10Y",
    "DE10Y",
    "IL10Y",
}


API_KEY = os.environ.get("FRED_API_KEY", "").strip()

START_DATE = "2008-01-01"
END_DATE = "2026-06-18"

EPS = 1e-10


# =============================================================================
# Helpers
# =============================================================================

def api_get(endpoint: str, params: dict, retries: int = 3) -> dict:
    if not API_KEY:
        raise RuntimeError("FRED_API_KEY is not set.")

    q = dict(params)
    q["api_key"] = API_KEY
    q["file_type"] = "json"

    url = (
        "https://api.stlouisfed.org/fred/"
        + endpoint
        + "?"
        + urllib.parse.urlencode(q)
    )

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Global-Capital-Flow-Monitor/1.0"
        },
    )

    last_error = None

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(
        f"FRED request failed: endpoint={endpoint}: {last_error}"
    )


def as_float(x):
    if x in {None, "", "."}:
        return None

    try:
        return float(x)
    except Exception:
        return None


def values_equal(a, b) -> bool:
    if pd.isna(a) and pd.isna(b):
        return True

    if pd.isna(a) or pd.isna(b):
        return False

    return abs(float(a) - float(b)) <= EPS


def get_all_vintage_observations(
    name: str,
    series_id: str,
) -> pd.DataFrame:
    """
    Fetch ALFRED vintage observations in YEAR-SIZED chunks.

    This avoids requesting the full 2008-2026 revision history
    in one large API response.

    AUDIT ONLY.
    """

    all_rows = []

    for year in range(2008, 2027):

        observation_start = f"{year}-01-01"

        if year == 2026:
            observation_end = END_DATE
        else:
            observation_end = f"{year}-12-31"

        print(
            f"  [{series_id}] observation year {year}...",
            flush=True,
        )

        offset = 0
        limit = 10000

        while True:

            obj = api_get(
                "series/observations",
                {
                    "series_id": series_id,

                    # We need all historical realtime vintages
                    # relevant to observations in this year.
                    "realtime_start": START_DATE,
                    "realtime_end": END_DATE,

                    "observation_start": observation_start,
                    "observation_end": observation_end,

                    "output_type": 4,
                    "limit": limit,
                    "offset": offset,
                    "sort_order": "asc",
                },
            )

            observations = obj.get(
                "observations",
                [],
            )

            for obs in observations:

                value = as_float(
                    obs.get("value")
                )

                if value is None:
                    continue

                realtime_start = pd.to_datetime(
                    obs.get("realtime_start"),
                    errors="coerce",
                )

                realtime_end = pd.to_datetime(
                    obs.get("realtime_end"),
                    errors="coerce",
                )

                if pd.isna(realtime_start):
                    continue

                all_rows.append(
                    {
                        "series": name,
                        "fred_series_id": series_id,

                        "observation_date":
                            pd.Timestamp(
                                obs["date"]
                            ).normalize(),

                        "vintage_start":
                            realtime_start.normalize(),

                        "vintage_end":
                            realtime_end.normalize()
                            if pd.notna(realtime_end)
                            else pd.NaT,

                        "value": float(value),
                    }
                )

            count = int(
                obj.get(
                    "count",
                    len(observations),
                )
            )

            offset += len(observations)

            print(
                f"      {offset}/{count}",
                flush=True,
            )

            if (
                not observations
                or offset >= count
            ):
                break

            time.sleep(0.20)

    if not all_rows:
        return pd.DataFrame()

    raw = pd.DataFrame(all_rows)

    raw = (
        raw
        .sort_values(
            [
                "observation_date",
                "vintage_start",
            ]
        )
        .reset_index(drop=True)
    )

    first = (
        raw
        .drop_duplicates(
            "observation_date",
            keep="first",
        )
        [
            [
                "observation_date",
                "vintage_start",
                "value",
            ]
        ]
        .rename(
            columns={
                "vintage_start":
                    "first_available_date",
                "value":
                    "first_value",
            }
        )
    )

    latest = (
        raw
        .drop_duplicates(
            "observation_date",
            keep="last",
        )
        [
            [
                "observation_date",
                "vintage_start",
                "value",
            ]
        ]
        .rename(
            columns={
                "vintage_start":
                    "latest_vintage_date",
                "value":
                    "latest_value",
            }
        )
    )

    history = first.merge(
        latest,
        on="observation_date",
        how="left",
        validate="one_to_one",
    )

    history["series"] = name
    history["fred_series_id"] = series_id

    history["was_revised"] = history.apply(
        lambda r: not values_equal(
            r["first_value"],
            r["latest_value"],
        ),
        axis=1,
    )

    history["release_lag_days"] = (
        history["first_available_date"]
        - history["observation_date"]
    ).dt.days

    return (
        history[
            [
                "series",
                "fred_series_id",
                "observation_date",
                "first_available_date",
                "first_value",
                "latest_vintage_date",
                "latest_value",
                "was_revised",
                "release_lag_days",
            ]
        ]
        .sort_values("observation_date")
        .reset_index(drop=True)
    )



def load_local_initial_release(
    name: str,
    series_id: str,
) -> pd.DataFrame | None:
    """
    Load frozen local FRED/ALFRED output_type=4 evidence.

    Returns
    -------
    DataFrame
        Local initial-release evidence when valid.
    None
        No usable local evidence exists.

    Important:
    RRPONTSYD is known not to exist in ALFRED. Its tiny JSON file
    contains a FRED error and must never be treated as evidence.
    """
    path = LOCAL_ALFRED / f"{series_id}_initial_release.json"

    if not path.exists():
        return None

    try:
        obj = json.loads(path.read_text())
    except Exception:
        return None

    if "error_code" in obj:
        print(
            f"  [{series_id}] local file is not evidence: "
            f"{obj.get('error_message', 'FRED error')}"
        )
        return None

    observations = obj.get("observations", [])

    if not observations:
        return None

    rows = []

    for obs in observations:
        value = obs.get("value")

        if value in {None, "", "."}:
            continue

        try:
            value = float(value)
        except Exception:
            continue

        obs_date = pd.Timestamp(
            obs["date"]
        ).normalize()

        realtime_start = pd.Timestamp(
            obs["realtime_start"]
        ).normalize()

        rows.append({
            "series": name,
            "fred_series_id": series_id,
            "observation_date": obs_date,
            "first_available_date": realtime_start,

            # Existing audit contract:
            # first_value = actual initial-release value.
            "first_value": value,

            # IMPORTANT:
            # output_type=4 proves the initial release only.
            # It does NOT prove the final/latest value or whether
            # the observation was subsequently revised.
            "latest_value": pd.NA,
            "was_revised": pd.NA,
        })

    if not rows:
        return None

    df = pd.DataFrame(rows)

    df = (
        df.sort_values(
            ["observation_date", "first_available_date"]
        )
        .drop_duplicates(
            "observation_date",
            keep="first",
        )
        .reset_index(drop=True)
    )

    df["release_lag_days"] = (
        df["first_available_date"]
        - df["observation_date"]
    ).dt.days

    # --------------------------------------------------------
    # Latest-value evidence
    # --------------------------------------------------------
    latest_path = LOCAL_ALFRED / f"{series_id}_latest.json"

    if latest_path.exists():
        try:
            latest_obj = json.loads(
                latest_path.read_text()
            )

            if "error_code" not in latest_obj:
                latest_rows = []

                for obs in latest_obj.get("observations", []):
                    value = obs.get("value")

                    if value in {None, "", "."}:
                        continue

                    try:
                        value = float(value)
                    except Exception:
                        continue

                    latest_rows.append({
                        "observation_date": pd.Timestamp(
                            obs["date"]
                        ).normalize(),
                        "_latest_value": value,
                    })

                if latest_rows:
                    latest = pd.DataFrame(latest_rows)

                    latest = (
                        latest
                        .sort_values("observation_date")
                        .drop_duplicates(
                            "observation_date",
                            keep="last",
                        )
                    )

                    df = df.merge(
                        latest,
                        on="observation_date",
                        how="left",
                    )

                    df["latest_value"] = df["_latest_value"]

                    comparable = (
                        df["first_value"].notna()
                        & df["latest_value"].notna()
                    )

                    df["was_revised"] = pd.NA

                    df.loc[
                        comparable,
                        "was_revised",
                    ] = (
                        (
                            df.loc[comparable, "first_value"]
                            - df.loc[comparable, "latest_value"]
                        ).abs()
                        > 1e-10
                    )

                    df = df.drop(
                        columns=["_latest_value"]
                    )

        except Exception as exc:
            print(
                f"  [{series_id}] latest evidence unreadable: "
                f"{exc}"
            )

    comparable_n = int(
        df["was_revised"].notna().sum()
    )

    revised_n = int(
        (df["was_revised"] == True).sum()
    )

    print(
        f"  [{series_id}] LOCAL INITIAL RELEASE EVIDENCE: "
        f"{len(df)} rows"
    )

    print(
        f"  [{series_id}] REVISION COMPARABLE: "
        f"{comparable_n} | REVISED: {revised_n}"
    )

    return df


def build_alfred_history(
    name: str,
    series_id: str,
) -> pd.DataFrame:

    local = load_local_initial_release(
        name,
        series_id,
    )

    if local is not None:
        return local

    # RRPONTSYD has no ALFRED vintage history.
    # Do not retry or invent revision evidence.
    if series_id == "RRPONTSYD":
        print(
            "  [RRPONTSYD] ALFRED VINTAGE HISTORY: NOT AVAILABLE"
        )
        return pd.DataFrame()

    # Fallback only when frozen local evidence is absent.
    return get_all_vintage_observations(
        name,
        series_id,
    )


# =============================================================================
# PIT-safe panel
# =============================================================================

def load_pit_panel() -> pd.DataFrame:

    candidates = [
        PIT_SAFE / "master_panel_pit_safe_with_sovereign.csv",
        PIT_SAFE / "master_panel_pit_safe.csv",
    ]

    for path in candidates:
        if not path.exists():
            continue

        df = pd.read_csv(path)

        date_col = None

        for c in ["signal_date", "date", "datetime"]:
            if c in df.columns:
                date_col = c
                break

        if date_col is None:
            continue

        df[date_col] = pd.to_datetime(
            df[date_col],
            errors="coerce",
        ).dt.normalize()

        df = df.rename(
            columns={date_col: "signal_date"}
        )

        df = df[
            (df["signal_date"] >= pd.Timestamp(START_DATE))
            & (df["signal_date"] <= pd.Timestamp(END_DATE))
        ].copy()

        print(f"PIT panel: {path}")
        print(f"PIT rows: {len(df)}")

        return df

    raise FileNotFoundError(
        "No PIT-safe master panel found."
    )


PANEL_CANDIDATES = {
    "FCI/NFCI": [
        "fred_extras__FCI",
        "fred_sector__FCI",
        "FCI",
    ],
    "TGA": [
        "liquidity__TGA",
        "TGA",
    ],
    "WALCL": [
        "liquidity__WALCL",
        "WALCL",
    ],
    "RRP": [
        "liquidity__RRP",
        "RRP",
    ],
    "DFII10": [
        "fred_sector__DFII10",
        "fred_extras__DFII10",
        "DFII10",
    ],
    "DGS2": [
        "fred_sector__DGS2",
        "fred_extras__DGS2",
        "DGS2",
    ],
    "T10Y2Y": [
        "fred_sector__T10Y2Y",
        "fred_extras__T10Y2Y",
        "T10Y2Y",
    ],
    "T10YIE": [
        "fred_sector__T10YIE",
        "fred_extras__T10YIE",
        "T10YIE",
    ],
    "US10Y": [
        "sovereign_yields__US10Y",
        "US10Y",
    ],
    "HY_OAS": [
        "credit__HY_OAS",
        "sentiment__hy_oas",
        "HY_OAS",
    ],
}


def find_panel_column(
    panel: pd.DataFrame,
    name: str,
) -> str | None:

    for col in PANEL_CANDIDATES[name]:
        if col in panel.columns:
            return col

    return None


# =============================================================================
# Historical PIT comparison
# =============================================================================

def compare_to_pit_panel(
    history: pd.DataFrame,
    panel: pd.DataFrame,
    name: str,
) -> pd.DataFrame:

    panel_col = find_panel_column(
        panel,
        name,
    )

    x = history.copy()

    if panel_col is None:
        x["signal_date"] = pd.NaT
        x["backtest_value"] = pd.NA
        x["panel_column"] = pd.NA
        x["pit_value_match"] = pd.NA
        x["used_before_available"] = pd.NA
        x["audit_status"] = "MISSING_PANEL_COLUMN"
        return x

    p = panel[
        ["signal_date", panel_col]
    ].copy()

    p[panel_col] = pd.to_numeric(
        p[panel_col],
        errors="coerce",
    )

    p = p.dropna(
        subset=["signal_date"]
    ).sort_values("signal_date")

    # -------------------------------------------------------------
    # For each historical decision date:
    # use only ALFRED observations whose first_available_date
    # is <= that decision date.
    #
    # This reconstructs the latest information actually available
    # at each signal date.
    # -------------------------------------------------------------

    h = x[
        [
            "observation_date",
            "first_available_date",
            "first_value",
            "latest_value",
            "was_revised",
            "release_lag_days",
            "fred_series_id",
            "series",
        ]
    ].copy()

    h = h.sort_values(
        "first_available_date"
    )

    # For a given decision date, choose latest observation that had
    # already become available.
    available = pd.merge_asof(
        p,
        h,
        left_on="signal_date",
        right_on="first_available_date",
        direction="backward",
        allow_exact_matches=True,
    )

    available = available.rename(
        columns={
            panel_col: "backtest_value",
            "first_value": "available_pit_value",
        }
    )

    available["panel_column"] = panel_col

    available["used_before_available"] = (
        available["first_available_date"].notna()
        & (
            available["first_available_date"]
            > available["signal_date"]
        )
    )

    def match_row(row):
        if pd.isna(row["backtest_value"]):
            return pd.NA

        if pd.isna(row["available_pit_value"]):
            return pd.NA

        return values_equal(
            row["backtest_value"],
            row["available_pit_value"],
        )

    available["pit_value_match"] = available.apply(
        match_row,
        axis=1,
    )

    def classify(row):
        if pd.isna(row["available_pit_value"]):
            return "NO_ALFRED_VALUE_AVAILABLE"

        if bool(row["used_before_available"]):
            return "FAIL_RELEASE_LAG"

        if pd.isna(row["pit_value_match"]):
            return "NO_COMPARABLE_BACKTEST_VALUE"

        if not bool(row["pit_value_match"]):
            return "FAIL_PIT_VALUE_MISMATCH"

        if bool(row["was_revised"]):
            return "PASS_USED_PIT_VALUE_REVISED_LATER"

        return "PASS_USED_PIT_VALUE"

    available["audit_status"] = available.apply(
        classify,
        axis=1,
    )

    return available


# =============================================================================
# Existing sovereign evidence
# =============================================================================

def load_existing_sovereign_evidence() -> pd.DataFrame:

    path = RESULTS / "sovereign_alfred_pit_4_detail.csv"

    if not path.exists():
        return pd.DataFrame(
            [
                {
                    "series": x,
                    "source_class": "ACTIVE_SOVEREIGN",
                    "status": "MISSING_EXISTING_EVIDENCE",
                }
                for x in sorted(ACTIVE_SOVEREIGN)
            ]
        )

    df = pd.read_csv(path)

    rows = []

    for series in sorted(ACTIVE_SOVEREIGN):

        x = df[
            df["series"].astype(str) == series
        ].copy()

        if x.empty:
            rows.append(
                {
                    "series": series,
                    "source_class": "ACTIVE_SOVEREIGN",
                    "status": "MISSING_EXISTING_EVIDENCE",
                }
            )
            continue

        revised = (
            int(
                pd.to_numeric(
                    x.get("was_revised"),
                    errors="coerce",
                )
                .fillna(0)
                .astype(bool)
                .sum()
            )
            if "was_revised" in x.columns
            else pd.NA
        )

        rows.append(
            {
                "series": series,
                "source_class": "ACTIVE_SOVEREIGN",
                "status": "EXISTING_ALFRED_EVIDENCE",
                "evidenced_observations": len(x),
                "revised_observations": revised,
                "first_evidenced_observation": (
                    x["observation_date"].min()
                    if "observation_date" in x.columns
                    else pd.NA
                ),
                "last_evidenced_observation": (
                    x["observation_date"].max()
                    if "observation_date" in x.columns
                    else pd.NA
                ),
            }
        )

    return pd.DataFrame(rows)


# =============================================================================
# Main
# =============================================================================

def main():

    print("=" * 80)
    print("INSTITUTIONAL GATE #3 — DATA REVISION / RELEASE LAG")
    print("=" * 80)
    print("Frozen scope: F13 22 + F15 20 + F18 40 = 82 contracts")
    print("Historical window: 2008-01-02 -> 2026-06-18")
    print()
    print("AUDIT ONLY — no Production or Backtest logic will be modified.")
    print()

    if not API_KEY:
        print("FRED_API_KEY: NOT FOUND")
        print("GATE STATUS: BLOCKED")
        print()
        print(
            "Set FRED_API_KEY before running. "
            "No vintage/release dates will be guessed."
        )
        return

    panel = load_pit_panel()

    all_detail = []
    summary_rows = []

    for name, series_id in FRED_SERIES.items():

        print()
        print("-" * 80)
        print(f"[{name}] FRED:{series_id}")
        print("-" * 80)

        try:
            history = build_alfred_history(
                name,
                series_id,
            )
        except Exception as exc:
            print(f"ERROR: {exc}")

            summary_rows.append(
                {
                    "series": name,
                    "fred_series_id": series_id,
                    "status": "BLOCKED_API_ERROR",
                    "error": str(exc),
                }
            )
            continue

        if history.empty:
            print("No ALFRED history.")
            summary_rows.append(
                {
                    "series": name,
                    "fred_series_id": series_id,
                    "status": "NO_ALFRED_HISTORY",
                }
            )
            continue

        compared = compare_to_pit_panel(
            history,
            panel,
            name,
        )

        compared["source_class"] = "FRED_UPSTREAM"

        all_detail.append(compared)

        revised = int(
            history["was_revised"].sum()
        )

        release_failures = int(
            (
                compared["audit_status"]
                == "FAIL_RELEASE_LAG"
            ).sum()
        )

        value_failures = int(
            (
                compared["audit_status"]
                == "FAIL_PIT_VALUE_MISMATCH"
            ).sum()
        )

        comparable = int(
            compared["pit_value_match"]
            .notna()
            .sum()
        )

        matches = int(
            (
                compared["pit_value_match"]
                == True
            ).sum()
        )

        missing_panel = int(
            (
                compared["audit_status"]
                == "MISSING_PANEL_COLUMN"
            ).sum()
        )

        if missing_panel > 0:
            status = "MISSING_PANEL_COLUMN"
        elif release_failures > 0:
            status = "FAIL_RELEASE_LAG"
        elif value_failures > 0:
            status = "FAIL_PIT_VALUE_MISMATCH"
        elif comparable == 0:
            status = "UNVERIFIED_NO_COMPARABLE_ROWS"
        else:
            status = "PASS"

        summary_rows.append(
            {
                "series": name,
                "fred_series_id": series_id,
                "alfred_observations": len(history),
                "revised_observations": revised,
                "comparable_decision_rows": comparable,
                "pit_value_matches": matches,
                "release_lag_failures": release_failures,
                "pit_value_mismatches": value_failures,
                "status": status,
            }
        )

        print(f"ALFRED observations: {len(history)}")
        print(f"Revised observations: {revised}")
        print(f"Comparable decision rows: {comparable}")
        print(f"PIT value matches: {matches}")
        print(f"Release-lag failures: {release_failures}")
        print(f"PIT-value mismatches: {value_failures}")
        print(f"STATUS: {status}")

    # ------------------------------------------------------------------
    # Write FRED detail
    # ------------------------------------------------------------------

    if all_detail:
        detail = pd.concat(
            all_detail,
            ignore_index=True,
        )
    else:
        detail = pd.DataFrame()

    detail.to_csv(
        OUT_DETAIL,
        index=False,
        encoding="utf-8-sig",
    )

    # ------------------------------------------------------------------
    # Existing sovereign evidence
    # ------------------------------------------------------------------

    sovereign = load_existing_sovereign_evidence()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    summary = pd.DataFrame(summary_rows)

    if not sovereign.empty:
        sovereign_summary = sovereign.copy()

        sovereign_summary["fred_series_id"] = pd.NA
        sovereign_summary["alfred_observations"] = sovereign_summary.get(
            "evidenced_observations",
            pd.NA,
        )
        sovereign_summary["comparable_decision_rows"] = pd.NA
        sovereign_summary["pit_value_matches"] = pd.NA
        sovereign_summary["release_lag_failures"] = pd.NA
        sovereign_summary["pit_value_mismatches"] = pd.NA

        keep = [
            "series",
            "fred_series_id",
            "alfred_observations",
            "revised_observations",
            "comparable_decision_rows",
            "pit_value_matches",
            "release_lag_failures",
            "pit_value_mismatches",
            "status",
        ]

        for col in keep:
            if col not in sovereign_summary.columns:
                sovereign_summary[col] = pd.NA

        summary = pd.concat(
            [
                summary,
                sovereign_summary[keep],
            ],
            ignore_index=True,
        )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
        encoding="utf-8-sig",
    )

    # ------------------------------------------------------------------
    # Failures
    # ------------------------------------------------------------------

    if not detail.empty:
        failures = detail[
            detail["audit_status"].isin(
                {
                    "FAIL_RELEASE_LAG",
                    "FAIL_PIT_VALUE_MISMATCH",
                    "MISSING_PANEL_COLUMN",
                }
            )
        ].copy()
    else:
        failures = pd.DataFrame()

    failures.to_csv(
        OUT_FAILURES,
        index=False,
        encoding="utf-8-sig",
    )

    # ------------------------------------------------------------------
    # Gate
    # ------------------------------------------------------------------

    fred_summary = summary[
        summary["series"].isin(FRED_SERIES.keys())
    ].copy()

    fred_pass = (
        len(fred_summary) == len(FRED_SERIES)
        and (fred_summary["status"] == "PASS").all()
    )

    sovereign_missing = (
        sovereign.empty
        or (
            sovereign["status"]
            != "EXISTING_ALFRED_EVIDENCE"
        ).any()
    )

    # Existing repository evidence explicitly documents that active
    # sovereign vintage history before its ALFRED evidence boundary
    # remains unverified. Therefore this audit must NOT falsely declare
    # the entire 82-contract gate closed solely because the 10 FRED
    # upstreams pass.
    if not fred_pass:
        final_gate = "FAIL_OR_UNVERIFIED"
    elif sovereign_missing:
        final_gate = "PARTIALLY_VERIFIED"
    else:
        final_gate = "PARTIALLY_VERIFIED_PENDING_SOVEREIGN_PRE_EVIDENCE_PERIOD"

    revised_total = int(
        pd.to_numeric(
            fred_summary.get(
                "revised_observations",
                pd.Series(dtype=float),
            ),
            errors="coerce",
        ).fillna(0).sum()
    )

    mismatch_total = int(
        pd.to_numeric(
            fred_summary.get(
                "pit_value_mismatches",
                pd.Series(dtype=float),
            ),
            errors="coerce",
        ).fillna(0).sum()
    )

    release_failure_total = int(
        pd.to_numeric(
            fred_summary.get(
                "release_lag_failures",
                pd.Series(dtype=float),
            ),
            errors="coerce",
        ).fillna(0).sum()
    )

    txt = "\n".join(
        [
            "INSTITUTIONAL GATE #3 — DATA REVISION / RELEASE LAG",
            "=" * 80,
            "Frozen universe: F13 22 + F15 20 + F18 40 = 82 stage-contract pairs",
            "Historical window: 2008-01-02 -> 2026-06-18",
            "",
            f"Direct FRED upstreams audited: {len(FRED_SERIES)}",
            f"Revised FRED observations found: {revised_total}",
            f"Release-lag failures: {release_failure_total}",
            f"PIT-value mismatches: {mismatch_total}",
            "",
            "Revision by itself is NOT a failure.",
            "Failure means the backtest used information/value not yet historically available.",
            "",
            "Active sovereign evidence reused: KR10Y / JP10Y / DE10Y / IL10Y",
            "Repository evidence documents a pre-ALFRED sovereign evidence gap.",
            "",
            f"FINAL DATA REVISION / RELEASE LAG GATE: {final_gate}",
            "",
            "No Production decision code modified.",
            "No Backtest decision logic modified.",
            "No strategy parameters modified.",
        ]
    )

    OUT_TXT.write_text(
        txt,
        encoding="utf-8",
    )

    print()
    print("=" * 80)
    print("FINAL")
    print("=" * 80)
    print(summary.to_string(index=False))
    print()
    print(txt)
    print()
    print("[OUTPUT]")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)
    print(OUT_FAILURES)
    print(OUT_TXT)


if __name__ == "__main__":
    main()
