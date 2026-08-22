from __future__ import annotations

import os
import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

OUT_DETAIL = RESULTS / "active_sovereign_vintage_4_detail.csv"
OUT_SUMMARY = RESULTS / "active_sovereign_vintage_4_summary.csv"
OUT_TXT = RESULTS / "active_sovereign_vintage_4_summary.txt"


SERIES = {
    "KR10Y": "IRLTLT01KRM156N",
    "JP10Y": "IRLTLT01JPM156N",
    "DE10Y": "IRLTLT01DEM156N",
    "IL10Y": "IRLTLT01ILM156N",
}


API_KEY = os.environ.get("FRED_API_KEY", "").strip()


def api_get(endpoint: str, params: dict) -> dict:
    params = dict(params)
    params["api_key"] = API_KEY
    params["file_type"] = "json"

    url = (
        "https://api.stlouisfed.org/fred/"
        + endpoint
        + "?"
        + urllib.parse.urlencode(params)
    )

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Global-Capital-Flow-Monitor/1.0"
        },
    )

    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(
            resp.read().decode("utf-8")
        )


def get_vintage_dates(series_id: str) -> list[pd.Timestamp]:
    obj = api_get(
        "series/vintagedates",
        {
            "series_id": series_id,
            "realtime_start": "2008-01-01",
            "realtime_end": "2026-12-31",
            "limit": 10000,
            "sort_order": "asc",
        },
    )

    return [
        pd.Timestamp(x).normalize()
        for x in obj.get("vintage_dates", [])
    ]


def get_initial_release_observations(
    series_id: str,
    vintage_dates: list[pd.Timestamp],
) -> pd.DataFrame:

    rows = []

    for vintage in vintage_dates:

        obj = api_get(
            "series/observations",
            {
                "series_id": series_id,
                "realtime_start": vintage.strftime("%Y-%m-%d"),
                "realtime_end": vintage.strftime("%Y-%m-%d"),
                "observation_start": "2007-01-01",
                "observation_end": "2026-12-31",
                "limit": 100000,
                "sort_order": "asc",
            },
        )

        observations = obj.get("observations", [])

        for obs in observations:
            value = obs.get("value")

            if value in {None, ".", ""}:
                continue

            try:
                value = float(value)
            except Exception:
                continue

            obs_date = pd.Timestamp(
                obs["date"]
            ).normalize()

            rows.append({
                "observation_date": obs_date,
                "vintage_date": vintage,
                "value": value,
            })

    if not rows:
        return pd.DataFrame(
            columns=[
                "observation_date",
                "vintage_date",
                "value",
            ]
        )

    df = pd.DataFrame(rows)

    # First vintage where each observation exists
    first = (
        df.sort_values(
            ["observation_date", "vintage_date"]
        )
        .drop_duplicates(
            "observation_date",
            keep="first",
        )
        .reset_index(drop=True)
    )

    return first


def main():

    print("=" * 80)
    print("ACTIVE SOVEREIGN HISTORICAL RELEASE / VINTAGE AUDIT")
    print("Scope: KR10Y / JP10Y / DE10Y / IL10Y")
    print("=" * 80)

    if not API_KEY:
        print()
        print("FRED_API_KEY: NOT FOUND")
        print("AUDIT STATUS: BLOCKED")
        print()
        print(
            "No release dates will be guessed."
        )
        print(
            "The 4 active sovereign series remain unresolved."
        )
        return

    all_rows = []

    for name, series_id in SERIES.items():

        print()
        print(
            f"[{name}] {series_id}"
        )

        vintages = get_vintage_dates(
            series_id
        )

        print(
            "Vintage dates:",
            len(vintages),
        )

        first = get_initial_release_observations(
            series_id,
            vintages,
        )

        if first.empty:
            print(
                "No historical release observations found."
            )
            continue

        first["series"] = name
        first["fred_series_id"] = series_id

        first["release_lag_days"] = (
            first["vintage_date"]
            - first["observation_date"]
        ).dt.days

        first["pit_status"] = first[
            "release_lag_days"
        ].apply(
            lambda x:
            "PASS_RELEASE_AFTER_OBSERVATION"
            if x >= 0
            else "FAIL_NEGATIVE_RELEASE_LAG"
        )

        all_rows.append(first)

        print(
            "Observations:",
            len(first),
        )

        print(
            "Lag days min/median/max:",
            int(first["release_lag_days"].min()),
            float(first["release_lag_days"].median()),
            int(first["release_lag_days"].max()),
        )

    if not all_rows:
        print()
        print("AUDIT STATUS: NO DATA")
        return

    detail = pd.concat(
        all_rows,
        ignore_index=True,
    )

    detail.to_csv(
        OUT_DETAIL,
        index=False,
        encoding="utf-8-sig",
    )

    summary = (
        detail
        .groupby("series")
        .agg(
            observations=("observation_date", "count"),
            first_observation=("observation_date", "min"),
            last_observation=("observation_date", "max"),
            min_release_lag_days=("release_lag_days", "min"),
            median_release_lag_days=("release_lag_days", "median"),
            max_release_lag_days=("release_lag_days", "max"),
            negative_lag_count=(
                "pit_status",
                lambda s: int(
                    (s == "FAIL_NEGATIVE_RELEASE_LAG").sum()
                ),
            ),
        )
        .reset_index()
    )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
        encoding="utf-8-sig",
    )

    failures = int(
        (
            detail["pit_status"]
            == "FAIL_NEGATIVE_RELEASE_LAG"
        ).sum()
    )

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(
        summary.to_string(index=False)
    )

    print()
    print(
        "NEGATIVE RELEASE-LAG FAILURES:",
        failures,
    )

    if failures == 0:
        gate = (
            "SOVEREIGN VINTAGE EVIDENCE GATE: PASS"
        )
    else:
        gate = (
            "SOVEREIGN VINTAGE EVIDENCE GATE: FAIL"
        )

    print(gate)

    OUT_TXT.write_text(
        "\n".join([
            "ACTIVE SOVEREIGN HISTORICAL RELEASE / VINTAGE AUDIT",
            "=" * 80,
            "Scope: KR10Y / JP10Y / DE10Y / IL10Y",
            f"Rows: {len(detail)}",
            f"Negative release-lag failures: {failures}",
            "",
            gate,
            "",
            "Release evidence source: FRED/ALFRED vintage dates.",
        ]),
        encoding="utf-8",
    )

    print()
    print("[OUTPUT]")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)
    print(OUT_TXT)


if __name__ == "__main__":
    main()
