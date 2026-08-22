from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "backtest"
RESULTS = DATA / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

PANEL_PATH = DATA / "master_panel.csv"
PIT_DETAIL = RESULTS / "full_pit_lineage_82_detail.csv"

OUT_DETAIL = RESULTS / "full_release_timing_82_detail.csv"
OUT_SUMMARY = RESULTS / "full_release_timing_82_summary.csv"
OUT_FAILURES = RESULTS / "full_release_timing_82_failures.csv"
OUT_TXT = RESULTS / "full_release_timing_82_summary.txt"


# ============================================================
# Officially evidenced release rules
# ============================================================

# NFCI:
# observation covers through Friday
# release = following Wednesday 08:30 ET
#
# H.4.1:
# WALCL / WTREGEN observation week ending Wednesday
# release = Thursday ~16:30 ET
#
# RRPONTSYD:
# daily operation result; same-day availability.
#
# Other daily FRED / sovereign series remain REVIEW_REQUIRED
# until their individual official availability rules are frozen.


def us_federal_holidays(start, end):
    cal = USFederalHolidayCalendar()
    return set(
        pd.to_datetime(
            cal.holidays(start=start, end=end)
        ).normalize()
    )


def nfci_release_date(obs_date, holidays):
    """
    NFCI observation through Friday -> following Wednesday.

    Chicago Fed notes that when a federal holiday occurs on
    Wednesday or earlier in that week, release moves to Thursday.
    """

    obs_date = pd.Timestamp(obs_date).normalize()

    # FRED NFCI observation is weekly.
    # Move to Wednesday following the observation week.
    days_until_wed = (2 - obs_date.weekday()) % 7

    if days_until_wed == 0:
        days_until_wed = 7

    release = obs_date + pd.Timedelta(days=days_until_wed)

    monday = release - pd.Timedelta(days=2)

    week_pre_release = {
        monday,
        monday + pd.Timedelta(days=1),
        release,
    }

    if any(d in holidays for d in week_pre_release):
        release += pd.Timedelta(days=1)

    return release


def h41_release_date(obs_date, holidays):
    """
    H.4.1 Wednesday observation -> Thursday publication.
    If Thursday is a federal holiday, move forward to next
    non-holiday weekday.
    """

    obs_date = pd.Timestamp(obs_date).normalize()

    release = obs_date + pd.Timedelta(days=1)

    while (
        release.weekday() >= 5
        or release in holidays
    ):
        release += pd.Timedelta(days=1)

    return release


def same_day_release(obs_date, holidays):
    return pd.Timestamp(obs_date).normalize()


def load_source(filename, value_col):
    path = DATA / filename

    df = pd.read_csv(path)

    date_col = next(
        c for c in df.columns
        if c.lower() in {"date", "datetime"}
    )

    df = df.rename(columns={date_col: "observation_date"})

    df["observation_date"] = pd.to_datetime(
        df["observation_date"],
        errors="coerce",
    ).dt.normalize()

    df[value_col] = pd.to_numeric(
        df[value_col],
        errors="coerce",
    )

    return (
        df[
            ["observation_date", value_col]
        ]
        .dropna(subset=["observation_date", value_col])
        .sort_values("observation_date")
        .drop_duplicates("observation_date", keep="last")
        .reset_index(drop=True)
    )


def audit_series(
    panel,
    source_family,
    source_column,
    filename,
    value_col,
    rule_name,
    release_func,
    holidays,
):
    source = load_source(filename, value_col)

    if source.empty:
        return [], []

    src = source.copy()

    src["available_date"] = src["observation_date"].apply(
        lambda d: release_func(d, holidays)
    )

    left = (
        panel[
            ["signal_date", "execution_date"]
        ]
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .copy()
    )

    # Current backtest behavior:
    # latest observation_date <= signal_date
    merged = pd.merge_asof(
        left,
        src,
        left_on="signal_date",
        right_on="observation_date",
        direction="backward",
    )

    merged = merged.dropna(subset=["observation_date"])

    if merged.empty:
        return [], []

    merged["early_use"] = (
        merged["available_date"]
        > merged["signal_date"]
    )

    detail = [{
        "source_family": source_family,
        "source_column": source_column,
        "release_rule": rule_name,
        "checked_rows": len(merged),
        "early_use_rows": int(merged["early_use"].sum()),
        "status": (
            "PASS"
            if int(merged["early_use"].sum()) == 0
            else "FAIL_EARLY_USE"
        ),
    }]

    failures = merged.loc[
        merged["early_use"],
        [
            "signal_date",
            "execution_date",
            "observation_date",
            "available_date",
        ],
    ].copy()

    if not failures.empty:
        failures["source_family"] = source_family
        failures["source_column"] = source_column
        failures["release_rule"] = rule_name

    return detail, failures.to_dict("records")


def main():

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"]
    ).dt.normalize()

    panel["execution_date"] = pd.to_datetime(
        panel["execution_date"]
    ).dt.normalize()

    start = panel["signal_date"].min() - pd.Timedelta(days=10)
    end = panel["signal_date"].max() + pd.Timedelta(days=10)

    holidays = us_federal_holidays(start, end)

    detail_rows = []
    failure_rows = []

    print("=" * 78)
    print("FULL F13/F15/F18 RELEASE TIMING AUDIT")
    print("Frozen universe: 82 stage-contract pairs")
    print("=" * 78)

    # --------------------------------------------------------
    # 1. NFCI / FCI
    # --------------------------------------------------------

    # NFCI must be audited from the sparse/raw observation source.
    # fred_macro_sctorallo.csv already forward-fills FCI daily, so using it
    # as the observation source would falsely treat every carried-forward
    # day as a new NFCI observation.
    filename = "fred_macro_extras.csv"
    path = DATA / filename

    if path.exists():
        cols = pd.read_csv(path, nrows=1).columns

        if "FCI" in cols:
            d, f = audit_series(
                panel,
                "fred_extras",
                "FCI",
                filename,
                "FCI",
                "NFCI_NEXT_WEDNESDAY_0830_ET",
                nfci_release_date,
                holidays,
            )

            detail_rows.extend(d)
            failure_rows.extend(f)

    # fred_sector FCI is a downstream carried-forward copy of the same NFCI.
    # It inherits the release result from the canonical NFCI source above.
    detail_rows.append({
        "source_family": "fred_sector",
        "source_column": "FCI",
        "release_rule": "INHERITS_CANONICAL_NFCI_RELEASE",
        "checked_rows": len(panel),
        "early_use_rows": 0,
        "status": "INHERITS_NFCI_RESULT",
    })

    # --------------------------------------------------------
    # 2. H.4.1 Liquidity
    # --------------------------------------------------------

    for col in ["TGA", "WALCL"]:

        d, f = audit_series(
            panel,
            "liquidity",
            col,
            "liquidity_data.csv",
            col,
            "H41_THURSDAY_1630_ET",
            h41_release_date,
            holidays,
        )

        detail_rows.extend(d)
        failure_rows.extend(f)

    # NET_LIQ cannot be known before its slowest parent.
    # Current construction requires TGA + RRP + WALCL,
    # therefore H.4.1 availability is the binding rule.

    d, f = audit_series(
        panel,
        "liquidity",
        "NET_LIQ",
        "liquidity_data.csv",
        "NET_LIQ",
        "INHERITS_H41_PARENT_AVAILABILITY",
        h41_release_date,
        holidays,
    )

    detail_rows.extend(d)
    failure_rows.extend(f)

    # --------------------------------------------------------
    # 3. Daily RRP
    # --------------------------------------------------------

    d, f = audit_series(
        panel,
        "liquidity",
        "RRP",
        "liquidity_data.csv",
        "RRP",
        "RRP_SAME_DAY_POST_OPERATION",
        same_day_release,
        holidays,
    )

    detail_rows.extend(d)
    failure_rows.extend(f)

    # --------------------------------------------------------
    # 4. Market-price family
    #
    # Strategy uses signal-date close and execution occurs
    # on following valid trading date.
    # --------------------------------------------------------

    market_check = panel[
        panel["signal_date"].notna()
        & panel["execution_date"].notna()
    ]

    bad_market_execution = (
        market_check["execution_date"]
        <= market_check["signal_date"]
    )

    detail_rows.append({
        "source_family": "market_price_family",
        "source_column": "ALL_MARKET_CLOSE_INPUTS",
        "release_rule": "SIGNAL_DATE_CLOSE -> NEXT_TRADING_DAY_EXECUTION",
        "checked_rows": len(market_check),
        "early_use_rows": int(bad_market_execution.sum()),
        "status": (
            "PASS"
            if int(bad_market_execution.sum()) == 0
            else "FAIL_EARLY_USE"
        ),
    })

    # --------------------------------------------------------
    # 5. Remaining frozen PIT inventory
    #
    # Do NOT silently pass anything without an evidenced rule.
    # --------------------------------------------------------

    pit = pd.read_csv(PIT_DETAIL)

    already_covered = {
        ("fred_sector", "FCI"),
        ("fred_extras", "FCI"),
        ("liquidity", "TGA"),
        ("liquidity", "WALCL"),
        ("liquidity", "NET_LIQ"),
        ("liquidity", "RRP"),
    }

    for _, row in pit.iterrows():

        fam = str(row.get("source_family", ""))
        col = str(row.get("source_column", ""))
        stype = str(row.get("source_type", ""))
        old_status = str(row.get("status", ""))

        if (fam, col) in already_covered:
            continue

        if fam in {
            "execution_mapping",
            "master_panel_builder",
        }:
            continue

        if old_status == "NO_VALID_SOURCE_VALUES":
            detail_rows.append({
                "source_family": fam,
                "source_column": col,
                "release_rule": "NO_VALID_SOURCE_VALUES",
                "checked_rows": 0,
                "early_use_rows": 0,
                "status": "REVIEW_NO_VALUES",
            })
            continue

        if stype == "MARKET":
            # Covered economically by common market-close rule.
            detail_rows.append({
                "source_family": fam,
                "source_column": col,
                "release_rule": "MARKET_CLOSE_INHERIT",
                "checked_rows": int(row.get("checked_rows", 0)),
                "early_use_rows": 0,
                "status": "PASS_INHERITED_MARKET_CLOSE",
            })
            continue

        if fam == "positioning":
            detail_rows.append({
                "source_family": fam,
                "source_column": col,
                "release_rule": "INHERITS_MARKET_HISTORY",
                "checked_rows": int(row.get("checked_rows", 0)),
                "early_use_rows": 0,
                "status": "PASS_INHERITED_MARKET_CLOSE",
            })
            continue

        if fam == "sentiment":
            detail_rows.append({
                "source_family": fam,
                "source_column": col,
                "release_rule": "DERIVED_PARENT_TIMING",
                "checked_rows": int(row.get("checked_rows", 0)),
                "early_use_rows": 0,
                "status": "REVIEW_PARENT_RELEASE",
            })
            continue

        if fam == "sovereign_spreads":
            detail_rows.append({
                "source_family": fam,
                "source_column": col,
                "release_rule": "INHERITS_SOVEREIGN_YIELD_TIMING",
                "checked_rows": int(row.get("checked_rows", 0)),
                "early_use_rows": 0,
                "status": "REVIEW_PARENT_RELEASE",
            })
            continue

        # Remaining FRED daily, credit, sovereign etc.
        detail_rows.append({
            "source_family": fam,
            "source_column": col,
            "release_rule": "OFFICIAL_RELEASE_RULE_NOT_YET_FROZEN",
            "checked_rows": int(row.get("checked_rows", 0)),
            "early_use_rows": 0,
            "status": "REVIEW_REQUIRED",
        })

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    detail = pd.DataFrame(detail_rows)

    failures = pd.DataFrame(failure_rows)

    if failures.empty:
        failures = pd.DataFrame(columns=[
            "signal_date",
            "execution_date",
            "observation_date",
            "available_date",
            "source_family",
            "source_column",
            "release_rule",
        ])

    detail.to_csv(
        OUT_DETAIL,
        index=False,
        encoding="utf-8-sig",
    )

    failures.to_csv(
        OUT_FAILURES,
        index=False,
        encoding="utf-8-sig",
    )

    summary = (
        detail
        .groupby("status", dropna=False)
        .size()
        .reset_index(name="series_count")
    )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
        encoding="utf-8-sig",
    )

    fail_series = int(
        detail["status"]
        .eq("FAIL_EARLY_USE")
        .sum()
    )

    early_rows = int(
        detail["early_use_rows"].sum()
    )

    review_series = int(
        detail["status"]
        .str.startswith("REVIEW", na=False)
        .sum()
    )

    print()
    print(summary.to_string(index=False))

    print()
    print("FAIL EARLY-USE SERIES:", fail_series)
    print("EARLY-USE OBSERVATIONS:", early_rows)
    print("REVIEW SERIES:", review_series)

    print()

    if fail_series == 0 and review_series == 0:
        gate = "RELEASE TIMING GATE: PASS"
    else:
        gate = "RELEASE TIMING GATE: NOT CLOSED"

    print(gate)

    if fail_series:
        print()
        print("EARLY-USE BY SERIES:")
        print(
            detail.loc[
                detail["status"] == "FAIL_EARLY_USE",
                [
                    "source_family",
                    "source_column",
                    "release_rule",
                    "checked_rows",
                    "early_use_rows",
                ],
            ].to_string(index=False)
        )

    OUT_TXT.write_text(
        "\n".join([
            "FULL F13/F15/F18 RELEASE TIMING AUDIT",
            "=" * 78,
            "Frozen universe: 82 stage-contract pairs",
            f"Fail early-use series: {fail_series}",
            f"Early-use observations: {early_rows}",
            f"Review series: {review_series}",
            "",
            gate,
            "",
            "No Production decision code modified.",
            "No Backtest decision logic modified.",
        ]),
        encoding="utf-8",
    )

    print()
    print("[OUTPUT]")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)
    print(OUT_FAILURES)
    print(OUT_TXT)


if __name__ == "__main__":
    main()
