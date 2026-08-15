from __future__ import annotations

"""
Filter15 Hard Deadman Episode Audit

Purpose
-------
Using the already validated Filter15 exposure-attribution output:

1. Decompose every Hard Deadman day by Production trigger.
2. Group consecutive Hard Deadman rows into episodes.
3. Measure episode duration.
4. Inspect the first executable day after each episode.
5. Determine whether Filter15 itself remains at zero after Deadman release.

Important
---------
- Production source is READ ONLY.
- Existing Filter15 parity / attribution code is READ ONLY.
- No strategy tuning.
- No future-data backfill.
- This audit studies historical behavior only.

Production Hard Deadman priority
--------------------------------
1. HY_OAS >= 6.0
2. MACRO_NARRATIVE == CREDIT_STRESS
3. MACRO_NARRATIVE == STAGFLATION_RISK and VIX_Z >= 3
4. VIX >= 30
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

INPUT_PATH = (
    RESULT_DIR
    / "filter15_exposure_attribution_daily.csv"
)

TRIGGER_SUMMARY_OUT = (
    RESULT_DIR
    / "filter15_deadman_trigger_summary.csv"
)

EPISODES_OUT = (
    RESULT_DIR
    / "filter15_deadman_episodes.csv"
)

AUDIT_OUT = (
    RESULT_DIR
    / "filter15_deadman_release_audit.txt"
)


# ============================================================
# Helpers
# ============================================================

def _numeric(
    df: pd.DataFrame,
    candidates: list[str],
) -> tuple[pd.Series, str]:

    lookup = {
        str(col).lower(): str(col)
        for col in df.columns
    }

    for candidate in candidates:

        actual = lookup.get(
            candidate.lower()
        )

        if actual is not None:

            return (
                pd.to_numeric(
                    df[actual],
                    errors="coerce",
                ),
                actual,
            )

    return (
        pd.Series(
            np.nan,
            index=df.index,
            dtype=float,
        ),
        "NOT_FOUND",
    )


def _text(
    df: pd.DataFrame,
    candidates: list[str],
) -> tuple[pd.Series, str]:

    lookup = {
        str(col).lower(): str(col)
        for col in df.columns
    }

    for candidate in candidates:

        actual = lookup.get(
            candidate.lower()
        )

        if actual is not None:

            return (
                df[actual]
                .fillna("")
                .astype(str),
                actual,
            )

    return (
        pd.Series(
            "",
            index=df.index,
            dtype="object",
        ),
        "NOT_FOUND",
    )


def _bool_series(
    df: pd.DataFrame,
    candidates: list[str],
) -> tuple[pd.Series, str]:

    lookup = {
        str(col).lower(): str(col)
        for col in df.columns
    }

    for candidate in candidates:

        actual = lookup.get(
            candidate.lower()
        )

        if actual is None:
            continue

        raw = df[actual]

        if pd.api.types.is_bool_dtype(raw):

            return (
                raw.fillna(False).astype(bool),
                actual,
            )

        normalized = (
            raw.fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        result = normalized.isin(
            [
                "TRUE",
                "1",
                "1.0",
                "YES",
                "Y",
            ]
        )

        return result, actual

    return (
        pd.Series(
            False,
            index=df.index,
            dtype=bool,
        ),
        "NOT_FOUND",
    )


def _safe_float(value):

    try:

        if pd.isna(value):
            return np.nan

        return float(value)

    except Exception:

        return np.nan


# ============================================================
# Load
# ============================================================

def load_data() -> tuple[
    pd.DataFrame,
    dict[str, str],
]:

    if not INPUT_PATH.exists():

        raise FileNotFoundError(
            "\nRequired validated attribution file "
            "does not exist:\n"
            f"{INPUT_PATH}\n\n"
            "Run:\n"
            "python scripts/backtest/"
            "audit_filter15_exposure_attribution.py\n"
        )

    df = pd.read_csv(INPUT_PATH)

    if "signal_date" not in df.columns:

        raise ValueError(
            "signal_date missing from attribution output."
        )

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )

    if "execution_date" in df.columns:

        df["execution_date"] = pd.to_datetime(
            df["execution_date"],
            errors="coerce",
        )

    else:

        df["execution_date"] = pd.NaT

    df = (
        df.dropna(
            subset=["signal_date"]
        )
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    mapping: dict[str, str] = {}

    # --------------------------------------------------------
    # Hard Deadman flag
    # --------------------------------------------------------

    hard_deadman, mapping["hard_deadman"] = (
        _bool_series(
            df,
            [
                "hard_deadman",
                "is_hard_deadman",
            ],
        )
    )

    # If bool field was not saved, use oracle status.
    if mapping["hard_deadman"] == "NOT_FOUND":

        status, mapping["oracle_status"] = _text(
            df,
            [
                "oracle_status",
                "filter15_status",
                "sew_status",
            ],
        )

        hard_deadman = (
            status
            .str.upper()
            .eq("HARD_DEADMAN")
        )

    df["_HARD_DEADMAN"] = hard_deadman

    # --------------------------------------------------------
    # Filter13 / Filter15 exposure
    # --------------------------------------------------------

    risk_budget, mapping["risk_budget"] = _numeric(
        df,
        [
            "risk_budget_13",
            "risk_budget",
            "start_exposure",
        ],
    )

    exposure_15, mapping["exposure_15"] = _numeric(
        df,
        [
            "actual_exposure_15",
            "exposure_15",
            "final_exposure",
            "recommended_exposure",
        ],
    )

    df["_RISK_BUDGET_13"] = risk_budget
    df["_EXPOSURE_15"] = exposure_15

    # --------------------------------------------------------
    # Deadman inputs
    # --------------------------------------------------------

    hy_level, mapping["hy_level"] = _numeric(
        df,
        [
            "hy_level",
            "hy_oas_today",
            "HY_OAS.today",
            "HY_OAS",
        ],
    )

    vix_today, mapping["vix_today"] = _numeric(
        df,
        [
            "vix_today",
            "VIX.today",
            "VIX",
        ],
    )

    vix_z, mapping["vix_z"] = _numeric(
        df,
        [
            "vix_z",
            "cross_asset_vix_z",
            "CROSS_ASSET_TAPE.VIX_Z",
        ],
    )

    macro, mapping["macro_narrative"] = _text(
        df,
        [
            "macro_narrative",
            "MACRO_NARRATIVE",
        ],
    )

    df["_HY_LEVEL"] = hy_level
    df["_VIX_TODAY"] = vix_today
    df["_VIX_Z"] = vix_z

    df["_MACRO_NARRATIVE"] = (
        macro
        .str.strip()
        .str.upper()
    )

    # --------------------------------------------------------
    # Saved Production reason if available
    # --------------------------------------------------------

    reason, mapping["deadman_reason"] = _text(
        df,
        [
            "hard_deadman_reason",
            "deadman_reason",
        ],
    )

    df["_SAVED_DEADMAN_REASON"] = reason

    return df, mapping


# ============================================================
# Production-priority trigger classification
# ============================================================

def classify_trigger(
    row: pd.Series,
) -> str:

    hy_level = _safe_float(
        row["_HY_LEVEL"]
    )

    vix_today = _safe_float(
        row["_VIX_TODAY"]
    )

    vix_z = _safe_float(
        row["_VIX_Z"]
    )

    macro = str(
        row["_MACRO_NARRATIVE"]
    ).upper()

    # --------------------------------------------------------
    # Exact Production priority
    # --------------------------------------------------------

    if (
        not pd.isna(hy_level)
        and hy_level >= 6.0
    ):

        return "HY_OAS_GE_6"

    if macro == "CREDIT_STRESS":

        return "MACRO_CREDIT_STRESS"

    if (
        macro == "STAGFLATION_RISK"
        and not pd.isna(vix_z)
        and vix_z >= 3.0
    ):

        return "STAGFLATION_VIX_SHOCK"

    if (
        not pd.isna(vix_today)
        and vix_today >= 30.0
    ):

        return "VIX_PANIC"

    return "UNRESOLVED"


def add_trigger_flags(
    df: pd.DataFrame,
) -> pd.DataFrame:

    out = df.copy()

    out["_PRIMARY_TRIGGER"] = "NONE"

    mask = out["_HARD_DEADMAN"]

    out.loc[
        mask,
        "_PRIMARY_TRIGGER",
    ] = out.loc[
        mask
    ].apply(
        classify_trigger,
        axis=1,
    )

    # --------------------------------------------------------
    # Raw trigger overlap flags
    # These ignore Production elif priority.
    # --------------------------------------------------------

    out["_TRIGGER_HY6"] = (
        out["_HY_LEVEL"] >= 6.0
    )

    out["_TRIGGER_MACRO_CREDIT"] = (
        out["_MACRO_NARRATIVE"]
        == "CREDIT_STRESS"
    )

    out["_TRIGGER_STAG_VIX"] = (
        (
            out["_MACRO_NARRATIVE"]
            == "STAGFLATION_RISK"
        )
        & (
            out["_VIX_Z"] >= 3.0
        )
    )

    out["_TRIGGER_VIX30"] = (
        out["_VIX_TODAY"] >= 30.0
    )

    trigger_cols = [
        "_TRIGGER_HY6",
        "_TRIGGER_MACRO_CREDIT",
        "_TRIGGER_STAG_VIX",
        "_TRIGGER_VIX30",
    ]

    out["_RAW_TRIGGER_COUNT"] = (
        out[trigger_cols]
        .fillna(False)
        .astype(int)
        .sum(axis=1)
    )

    return out


# ============================================================
# Trigger Summary
# ============================================================

def build_trigger_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    dead = df[
        df["_HARD_DEADMAN"]
    ].copy()

    rows = []

    trigger_order = [
        "HY_OAS_GE_6",
        "MACRO_CREDIT_STRESS",
        "STAGFLATION_VIX_SHOCK",
        "VIX_PANIC",
        "UNRESOLVED",
    ]

    total_deadman = len(dead)

    for trigger in trigger_order:

        sample = dead[
            dead["_PRIMARY_TRIGGER"]
            == trigger
        ]

        count = len(sample)

        rows.append(
            {
                "trigger": trigger,
                "deadman_days": count,
                "pct_of_deadman_days": (
                    count
                    / total_deadman
                    * 100.0
                    if total_deadman
                    else 0.0
                ),
                "avg_filter13_budget": (
                    sample[
                        "_RISK_BUDGET_13"
                    ].mean()
                ),
                "avg_filter15_exposure": (
                    sample[
                        "_EXPOSURE_15"
                    ].mean()
                ),
                "total_zeroed_exposure_points": (
                    (
                        sample[
                            "_RISK_BUDGET_13"
                        ]
                        - sample[
                            "_EXPOSURE_15"
                        ]
                    ).sum()
                ),
                "avg_hy_oas": (
                    sample[
                        "_HY_LEVEL"
                    ].mean()
                ),
                "avg_vix": (
                    sample[
                        "_VIX_TODAY"
                    ].mean()
                ),
                "avg_vix_z": (
                    sample[
                        "_VIX_Z"
                    ].mean()
                ),
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# Episode Construction
# ============================================================

def build_episodes(
    df: pd.DataFrame,
) -> pd.DataFrame:

    work = df.copy()

    # Episode begins when current row is Deadman and previous
    # executable row was not Deadman.
    start_flag = (
        work["_HARD_DEADMAN"]
        & ~work[
            "_HARD_DEADMAN"
        ].shift(
            1,
            fill_value=False,
        )
    )

    work["_EPISODE_ID"] = (
        start_flag.astype(int).cumsum()
    )

    dead = work[
        work["_HARD_DEADMAN"]
    ].copy()

    episodes = []

    for episode_id, group in dead.groupby(
        "_EPISODE_ID",
        sort=True,
    ):

        group = group.sort_index()

        first_idx = int(
            group.index.min()
        )

        last_idx = int(
            group.index.max()
        )

        start_row = work.loc[
            first_idx
        ]

        end_row = work.loc[
            last_idx
        ]

        next_idx = last_idx + 1

        if next_idx < len(work):

            next_row = work.loc[
                next_idx
            ]

            next_signal_date = (
                next_row["signal_date"]
            )

            next_execution_date = (
                next_row["execution_date"]
            )

            next_deadman = bool(
                next_row["_HARD_DEADMAN"]
            )

            next_exposure = (
                next_row[
                    "_EXPOSURE_15"
                ]
            )

            next_budget = (
                next_row[
                    "_RISK_BUDGET_13"
                ]
            )

            next_primary_trigger = (
                next_row[
                    "_PRIMARY_TRIGGER"
                ]
            )

            next_hy = (
                next_row[
                    "_HY_LEVEL"
                ]
            )

            next_vix = (
                next_row[
                    "_VIX_TODAY"
                ]
            )

            next_macro = (
                next_row[
                    "_MACRO_NARRATIVE"
                ]
            )

            next_vix_z = (
                next_row[
                    "_VIX_Z"
                ]
            )

        else:

            next_signal_date = pd.NaT
            next_execution_date = pd.NaT
            next_deadman = np.nan
            next_exposure = np.nan
            next_budget = np.nan
            next_primary_trigger = "END_OF_SAMPLE"
            next_hy = np.nan
            next_vix = np.nan
            next_macro = ""
            next_vix_z = np.nan

        primary_counts = (
            group[
                "_PRIMARY_TRIGGER"
            ]
            .value_counts()
        )

        dominant_trigger = (
            primary_counts.index[0]
            if len(primary_counts)
            else "UNKNOWN"
        )

        # Trigger transition history inside episode.
        trigger_sequence = []

        previous_trigger = None

        for trigger in group[
            "_PRIMARY_TRIGGER"
        ].tolist():

            if trigger != previous_trigger:

                trigger_sequence.append(
                    trigger
                )

                previous_trigger = trigger

        # ----------------------------------------------------
        # Release classification
        # ----------------------------------------------------

        if pd.isna(next_signal_date):

            release_status = (
                "END_OF_SAMPLE"
            )

        elif next_deadman is True:

            # Should not normally occur because consecutive
            # rows belong to the same episode.
            release_status = (
                "STILL_DEADMAN"
            )

        elif (
            pd.notna(next_exposure)
            and float(next_exposure) > 0
        ):

            release_status = (
                "IMMEDIATE_POSITIVE_EXPOSURE"
            )

        elif (
            pd.notna(next_exposure)
            and float(next_exposure) == 0
        ):

            release_status = (
                "DEADMAN_RELEASED_BUT_EXPOSURE_ZERO"
            )

        else:

            release_status = (
                "NEXT_EXPOSURE_MISSING"
            )

        episodes.append(
            {
                "episode_id": int(
                    episode_id
                ),

                "start_signal_date": (
                    start_row[
                        "signal_date"
                    ]
                ),

                "start_execution_date": (
                    start_row[
                        "execution_date"
                    ]
                ),

                "end_signal_date": (
                    end_row[
                        "signal_date"
                    ]
                ),

                "end_execution_date": (
                    end_row[
                        "execution_date"
                    ]
                ),

                "duration_rows": len(
                    group
                ),

                "calendar_days": (
                    (
                        end_row[
                            "signal_date"
                        ]
                        - start_row[
                            "signal_date"
                        ]
                    ).days
                    + 1
                ),

                "start_trigger": (
                    start_row[
                        "_PRIMARY_TRIGGER"
                    ]
                ),

                "end_trigger": (
                    end_row[
                        "_PRIMARY_TRIGGER"
                    ]
                ),

                "dominant_trigger": (
                    dominant_trigger
                ),

                "trigger_sequence": (
                    " -> ".join(
                        trigger_sequence
                    )
                ),

                "hy6_days": int(
                    group[
                        "_TRIGGER_HY6"
                    ].sum()
                ),

                "macro_credit_days": int(
                    group[
                        "_TRIGGER_MACRO_CREDIT"
                    ].sum()
                ),

                "stagflation_vix_days": int(
                    group[
                        "_TRIGGER_STAG_VIX"
                    ].sum()
                ),

                "vix30_days": int(
                    group[
                        "_TRIGGER_VIX30"
                    ].sum()
                ),

                "multi_trigger_days": int(
                    (
                        group[
                            "_RAW_TRIGGER_COUNT"
                        ]
                        >= 2
                    ).sum()
                ),

                "avg_filter13_budget": (
                    group[
                        "_RISK_BUDGET_13"
                    ].mean()
                ),

                "avg_filter15_exposure": (
                    group[
                        "_EXPOSURE_15"
                    ].mean()
                ),

                "avg_hy_oas": (
                    group[
                        "_HY_LEVEL"
                    ].mean()
                ),

                "max_hy_oas": (
                    group[
                        "_HY_LEVEL"
                    ].max()
                ),

                "avg_vix": (
                    group[
                        "_VIX_TODAY"
                    ].mean()
                ),

                "max_vix": (
                    group[
                        "_VIX_TODAY"
                    ].max()
                ),

                "max_vix_z": (
                    group[
                        "_VIX_Z"
                    ].max()
                ),

                # First executable row after release
                "next_signal_date": (
                    next_signal_date
                ),

                "next_execution_date": (
                    next_execution_date
                ),

                "next_deadman": (
                    next_deadman
                ),

                "next_risk_budget_13": (
                    next_budget
                ),

                "next_exposure_15": (
                    next_exposure
                ),

                "next_primary_trigger": (
                    next_primary_trigger
                ),

                "next_hy_oas": (
                    next_hy
                ),

                "next_vix": (
                    next_vix
                ),

                "next_macro_narrative": (
                    next_macro
                ),

                "next_vix_z": (
                    next_vix_z
                ),

                "release_status": (
                    release_status
                ),
            }
        )

    return pd.DataFrame(
        episodes
    )


# ============================================================
# Audit
# ============================================================

def main() -> None:

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df, mapping = load_data()

    df = add_trigger_flags(
        df
    )

    dead = df[
        df["_HARD_DEADMAN"]
    ].copy()

    trigger_summary = (
        build_trigger_summary(
            df
        )
    )

    episodes = build_episodes(
        df
    )

    # ========================================================
    # Validation
    # ========================================================

    deadman_days = len(dead)

    classified_days = int(
        (
            dead["_PRIMARY_TRIGGER"]
            != "UNRESOLVED"
        ).sum()
    )

    unresolved_days = int(
        (
            dead["_PRIMARY_TRIGGER"]
            == "UNRESOLVED"
        ).sum()
    )

    episode_days = int(
        episodes[
            "duration_rows"
        ].sum()
        if len(episodes)
        else 0
    )

    reconciliation_ok = (
        episode_days
        == deadman_days
    )

    # ========================================================
    # Episode stats
    # ========================================================

    episode_count = len(
        episodes
    )

    if episode_count:

        mean_duration = float(
            episodes[
                "duration_rows"
            ].mean()
        )

        median_duration = float(
            episodes[
                "duration_rows"
            ].median()
        )

        max_duration = int(
            episodes[
                "duration_rows"
            ].max()
        )

        p90_duration = float(
            episodes[
                "duration_rows"
            ].quantile(
                0.90
            )
        )

    else:

        mean_duration = 0.0
        median_duration = 0.0
        max_duration = 0
        p90_duration = 0.0

    release_counts = (
        episodes[
            "release_status"
        ]
        .value_counts()
        if episode_count
        else pd.Series(dtype=int)
    )

    immediate_positive = int(
        release_counts.get(
            "IMMEDIATE_POSITIVE_EXPOSURE",
            0,
        )
    )

    released_but_zero = int(
        release_counts.get(
            "DEADMAN_RELEASED_BUT_EXPOSURE_ZERO",
            0,
        )
    )

    end_of_sample = int(
        release_counts.get(
            "END_OF_SAMPLE",
            0,
        )
    )

    # ========================================================
    # Overall verdict
    # ========================================================

    audit_pass = (
        deadman_days > 0
        and unresolved_days == 0
        and reconciliation_ok
    )

    verdict = (
        "PASS"
        if audit_pass
        else "FAIL"
    )

    # ========================================================
    # Save
    # ========================================================

    trigger_summary.to_csv(
        TRIGGER_SUMMARY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    episodes.to_csv(
        EPISODES_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Text report
    # ========================================================

    lines = []

    lines.append(
        "# FILTER15 HARD DEADMAN EPISODE AUDIT"
    )

    lines.append("")

    lines.append(
        f"Rows                  : {len(df)}"
    )

    lines.append(
        f"Hard Deadman Days     : {deadman_days}"
    )

    lines.append(
        f"Classified Days       : {classified_days}"
    )

    lines.append(
        f"Unresolved Days       : {unresolved_days}"
    )

    lines.append(
        f"Episode Days          : {episode_days}"
    )

    lines.append(
        "Episode Reconciliation: "
        + (
            "PASS"
            if reconciliation_ok
            else "FAIL"
        )
    )

    lines.append("")

    lines.append(
        f"Deadman Episodes      : {episode_count}"
    )

    lines.append(
        f"Mean Duration         : {mean_duration:.2f} rows"
    )

    lines.append(
        f"Median Duration       : {median_duration:.2f} rows"
    )

    lines.append(
        f"P90 Duration          : {p90_duration:.2f} rows"
    )

    lines.append(
        f"Max Duration          : {max_duration} rows"
    )

    lines.append("")

    lines.append(
        "Release:"
    )

    lines.append(
        "- Immediate positive exposure: "
        f"{immediate_positive}"
    )

    lines.append(
        "- Deadman released but exposure still zero: "
        f"{released_but_zero}"
    )

    lines.append(
        "- End of sample: "
        f"{end_of_sample}"
    )

    lines.append("")

    lines.append(
        "Primary Trigger Attribution:"
    )

    for _, row in trigger_summary.iterrows():

        lines.append(
            "- "
            f"{row['trigger']}: "
            f"days={int(row['deadman_days'])}, "
            f"share={row['pct_of_deadman_days']:.2f}%, "
            "zeroed_points="
            f"{row['total_zeroed_exposure_points']:.2f}"
        )

    lines.append("")

    lines.append(
        "Input Mapping:"
    )

    for key, value in mapping.items():

        lines.append(
            f"- {key}: {value}"
        )

    lines.append("")

    lines.append(
        "Production source modified: NO"
    )

    lines.append(
        "Existing parity code modified: NO"
    )

    lines.append(
        "Future-data backfill: NO"
    )

    lines.append("")

    lines.append(
        f"RESULT: FILTER15 DEADMAN EPISODE AUDIT {verdict}"
    )

    lines.append("")

    lines.append(
        "Interpretation:"
    )

    lines.append(
        "This audit does NOT change the strategy."
    )

    lines.append(
        "It measures why Hard Deadman activated, "
        "how long each episode lasted, and whether "
        "Filter15 returned to positive exposure on "
        "the first executable row after the Deadman "
        "condition disappeared."
    )

    AUDIT_OUT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    # ========================================================
    # Console
    # ========================================================

    print(
        "\n"
        + "=" * 78
    )

    print(
        "FILTER15 HARD DEADMAN EPISODE AUDIT"
    )

    print(
        "=" * 78
    )

    print(
        f"\nHard Deadman Days : {deadman_days}"
    )

    print(
        f"Deadman Episodes  : {episode_count}"
    )

    print(
        f"Mean Duration     : {mean_duration:.2f}"
    )

    print(
        f"Median Duration   : {median_duration:.2f}"
    )

    print(
        f"P90 Duration      : {p90_duration:.2f}"
    )

    print(
        f"Max Duration      : {max_duration}"
    )

    print(
        "\n===== PRIMARY TRIGGERS ====="
    )

    print(
        trigger_summary.to_string(
            index=False
        )
    )

    print(
        "\n===== RELEASE ====="
    )

    if len(release_counts):

        print(
            release_counts.to_string()
        )

    else:

        print(
            "No episodes."
        )

    print(
        "\n===== LONGEST 15 EPISODES ====="
    )

    if episode_count:

        display_cols = [
            "episode_id",
            "start_signal_date",
            "end_signal_date",
            "duration_rows",
            "dominant_trigger",
            "trigger_sequence",
            "max_hy_oas",
            "max_vix",
            "next_signal_date",
            "next_risk_budget_13",
            "next_exposure_15",
            "release_status",
        ]

        print(
            episodes
            .sort_values(
                "duration_rows",
                ascending=False,
            )
            .head(15)[
                display_cols
            ]
            .to_string(
                index=False
            )
        )

    print(
        "\n"
        + "=" * 78
    )

    print(
        f"RESULT: FILTER15 DEADMAN EPISODE AUDIT {verdict}"
    )

    print(
        "=" * 78
    )

    print(
        f"\nSaved: {TRIGGER_SUMMARY_OUT}"
    )

    print(
        f"Saved: {EPISODES_OUT}"
    )

    print(
        f"Saved: {AUDIT_OUT}"
    )


if __name__ == "__main__":
    main()