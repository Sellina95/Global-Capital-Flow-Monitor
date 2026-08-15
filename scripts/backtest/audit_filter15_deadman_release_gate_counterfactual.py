from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

DAILY_PATH = (
    RESULT_DIR
    / "filter15_exposure_attribution_daily.csv"
)

EPISODE_PATH = (
    RESULT_DIR
    / "filter15_deadman_episodes.csv"
)

OUT_DAILY = (
    RESULT_DIR
    / "filter15_deadman_release_gate_counterfactual_daily.csv"
)

OUT_EPISODES = (
    RESULT_DIR
    / "filter15_deadman_release_gate_counterfactual_episodes.csv"
)

OUT_SUMMARY = (
    RESULT_DIR
    / "filter15_deadman_release_gate_counterfactual_summary.csv"
)

OUT_TXT = (
    RESULT_DIR
    / "filter15_deadman_release_gate_counterfactual_audit.txt"
)


# ============================================================
# Helpers
# ============================================================

def numeric(x):
    return pd.to_numeric(x, errors="coerce")


def first_existing(df: pd.DataFrame, candidates):
    lookup = {
        str(c).lower(): str(c)
        for c in df.columns
    }

    for candidate in candidates:
        found = lookup.get(candidate.lower())
        if found is not None:
            return found

    return None


def resolve_numeric(
    df: pd.DataFrame,
    candidates,
    default=np.nan,
):
    col = first_existing(df, candidates)

    if col is None:
        return (
            pd.Series(
                default,
                index=df.index,
                dtype=float,
            ),
            "NOT_FOUND",
        )

    return numeric(df[col]), col


def max_drawdown_from_returns(returns: pd.Series) -> float:
    r = numeric(returns).fillna(0.0)

    wealth = (1.0 + r).cumprod()

    peak = wealth.cummax()

    dd = wealth / peak - 1.0

    if len(dd) == 0:
        return np.nan

    return float(dd.min())


# ============================================================
# Load
# ============================================================

if not DAILY_PATH.exists():
    raise FileNotFoundError(
        f"Missing input:\n{DAILY_PATH}\n\n"
        "Run audit_filter15_exposure_attribution.py first."
    )

if not EPISODE_PATH.exists():
    raise FileNotFoundError(
        f"Missing input:\n{EPISODE_PATH}\n\n"
        "Run audit_filter15_deadman_episodes.py first."
    )


df = pd.read_csv(DAILY_PATH)
episodes = pd.read_csv(EPISODE_PATH)


# ============================================================
# Date
# ============================================================

date_col = first_existing(
    df,
    (
        "signal_date",
        "date",
    ),
)

if date_col is None:
    raise ValueError(
        "No signal_date/date column found."
    )

df["signal_date"] = pd.to_datetime(
    df[date_col],
    errors="coerce",
)

df = (
    df
    .dropna(subset=["signal_date"])
    .sort_values("signal_date")
    .reset_index(drop=True)
)


# ============================================================
# Required baseline fields
# ============================================================

risk_budget, risk_budget_source = resolve_numeric(
    df,
    (
        "risk_budget_13",
        "RISK_BUDGET",
    ),
)

baseline_exposure, exposure_source = resolve_numeric(
    df,
    (
        "actual_exposure_15",
        "exposure_15",
        "final_exposure_15",
    ),
)

hy, hy_source = resolve_numeric(
    df,
    (
        "hy_oas_today",
        "HY_OAS",
        "hy_level",
    ),
)

vix, vix_source = resolve_numeric(
    df,
    (
        "vix_today",
        "VIX",
    ),
)

spy, spy_source = resolve_numeric(
    df,
    (
        "SPY",
        "spy",
        "spy_close",
        "market__SPY",
    ),
)


# ============================================================
# If SPY is not in attribution output, get it from master panel
# ============================================================

if spy.isna().all():

    master_path = (
        ROOT
        / "data"
        / "backtest"
        / "master_panel.csv"
    )

    if not master_path.exists():
        raise FileNotFoundError(
            "SPY not present in attribution output and "
            f"master panel missing:\n{master_path}"
        )

    master = pd.read_csv(master_path)

    master_date_col = first_existing(
        master,
        (
            "signal_date",
            "date",
        ),
    )

    master_spy_col = first_existing(
        master,
        (
            "SPY",
            "spy",
        ),
    )

    if (
        master_date_col is None
        or master_spy_col is None
    ):
        raise ValueError(
            "Could not resolve SPY from master_panel.csv"
        )

    master["_merge_date"] = pd.to_datetime(
        master[master_date_col],
        errors="coerce",
    )

    master["_merge_spy"] = numeric(
        master[master_spy_col]
    )

    lookup = (
        master
        .dropna(subset=["_merge_date"])
        .drop_duplicates(
            "_merge_date",
            keep="last",
        )
        .set_index("_merge_date")["_merge_spy"]
    )

    spy = df["signal_date"].map(lookup)

    spy_source = (
        f"master_panel:{master_spy_col}"
    )


# ============================================================
# HY/VIX fallback from master panel if necessary
# ============================================================

need_master = (
    hy.isna().all()
    or vix.isna().all()
)

if need_master:

    master_path = (
        ROOT
        / "data"
        / "backtest"
        / "master_panel.csv"
    )

    if not master_path.exists():
        raise FileNotFoundError(
            f"Missing master panel:\n{master_path}"
        )

    master = pd.read_csv(master_path)

    master_date_col = first_existing(
        master,
        (
            "signal_date",
            "date",
        ),
    )

    if master_date_col is None:
        raise ValueError(
            "No date column in master panel."
        )

    master["_merge_date"] = pd.to_datetime(
        master[master_date_col],
        errors="coerce",
    )

    if hy.isna().all():

        master_hy_col = first_existing(
            master,
            (
                "HY_OAS",
                "hy_oas",
                "credit__HY_OAS",
            ),
        )

        if master_hy_col is not None:

            master["_merge_hy"] = numeric(
                master[master_hy_col]
            )

            lookup = (
                master
                .dropna(subset=["_merge_date"])
                .drop_duplicates(
                    "_merge_date",
                    keep="last",
                )
                .set_index("_merge_date")[
                    "_merge_hy"
                ]
            )

            hy = df["signal_date"].map(lookup)

            hy_source = (
                f"master_panel:{master_hy_col}"
            )

    if vix.isna().all():

        master_vix_col = first_existing(
            master,
            (
                "VIX",
                "vix",
            ),
        )

        if master_vix_col is not None:

            master["_merge_vix"] = numeric(
                master[master_vix_col]
            )

            lookup = (
                master
                .dropna(subset=["_merge_date"])
                .drop_duplicates(
                    "_merge_date",
                    keep="last",
                )
                .set_index("_merge_date")[
                    "_merge_vix"
                ]
            )

            vix = df["signal_date"].map(lookup)

            vix_source = (
                f"master_panel:{master_vix_col}"
            )


df["risk_budget_13"] = risk_budget
df["baseline_exposure_15"] = baseline_exposure
df["HY_OAS"] = hy
df["VIX"] = vix
df["SPY"] = spy


# ============================================================
# Identify Hard Deadman rows
# ============================================================

hard_col = first_existing(
    df,
    (
        "hard_deadman",
        "is_hard_deadman",
    ),
)

if hard_col is None:
    raise ValueError(
        "Could not find hard_deadman field in "
        "filter15_exposure_attribution_daily.csv"
    )

hard_raw = df[hard_col]

if hard_raw.dtype == bool:
    df["hard_deadman"] = hard_raw
else:
    df["hard_deadman"] = (
        hard_raw
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(
            (
                "true",
                "1",
                "yes",
            )
        )
    )


# ============================================================
# Daily SPY return
#
# IMPORTANT:
# return t is generated from prices available through t.
# Counterfactual exposure is shifted one row before applying
# to return t+1.
#
# This prevents same-day signal/return leakage.
# ============================================================

df["spy_return"] = (
    df["SPY"]
    .pct_change()
)


# ============================================================
# Candidate release gates
# ============================================================

CANDIDATES = [
    "BASELINE",
    "HY_LT_5_5",
    "HY_LT_5_VIX_LT_30",
    "HY_FALLING_VIX_LT_30",
    "HY_FALLING_SPY_RECOVERY_5",
    "VIX_LT_25_SPY_RECOVERY_5",
]


# ============================================================
# Counterfactual engine
# ============================================================

daily_records = []
episode_records = []


episodes["start_signal_date"] = pd.to_datetime(
    episodes["start_signal_date"],
    errors="coerce",
)

episodes["end_signal_date"] = pd.to_datetime(
    episodes["end_signal_date"],
    errors="coerce",
)


for _, ep in episodes.iterrows():

    episode_id = ep["episode_id"]

    start = ep["start_signal_date"]
    end = ep["end_signal_date"]

    dominant_trigger = str(
        ep.get(
            "dominant_trigger",
            "",
        )
    )

    mask = (
        (df["signal_date"] >= start)
        & (df["signal_date"] <= end)
    )

    block = df.loc[mask].copy()

    if block.empty:
        continue

    block = block.sort_values(
        "signal_date"
    ).copy()

    # --------------------------------------------------------
    # Point-in-time running low
    #
    # Only information observed up through the current row.
    # NO episode-final low is used.
    # --------------------------------------------------------

    block["running_spy_low"] = (
        block["SPY"].cummin()
    )

    block["spy_recovery_from_running_low"] = (
        block["SPY"]
        / block["running_spy_low"]
        - 1.0
    )

    # HY direction uses prior observable row only.
    block["hy_prev"] = (
        block["HY_OAS"].shift(1)
    )

    block["hy_falling"] = (
        block["HY_OAS"]
        < block["hy_prev"]
    )

    for candidate in CANDIDATES:

        release_date = pd.NaT
        release_idx = None

        # ----------------------------------------------------
        # Baseline = production deadman through episode end
        # ----------------------------------------------------

        if candidate == "BASELINE":
            release_date = pd.NaT
            release_idx = None

        else:

            for idx, row in block.iterrows():

                hy_now = row["HY_OAS"]
                vix_now = row["VIX"]

                hy_falling = bool(
                    row["hy_falling"]
                )

                recovery = row[
                    "spy_recovery_from_running_low"
                ]

                condition = False

                if candidate == "HY_LT_5_5":

                    condition = (
                        pd.notna(hy_now)
                        and hy_now < 5.5
                    )

                elif candidate == "HY_LT_5_VIX_LT_30":

                    condition = (
                        pd.notna(hy_now)
                        and pd.notna(vix_now)
                        and hy_now < 5.0
                        and vix_now < 30.0
                    )

                elif candidate == "HY_FALLING_VIX_LT_30":

                    condition = (
                        pd.notna(hy_now)
                        and pd.notna(vix_now)
                        and hy_falling
                        and vix_now < 30.0
                    )

                elif candidate == "HY_FALLING_SPY_RECOVERY_5":

                    condition = (
                        pd.notna(hy_now)
                        and pd.notna(recovery)
                        and hy_falling
                        and recovery >= 0.05
                    )

                elif candidate == "VIX_LT_25_SPY_RECOVERY_5":

                    condition = (
                        pd.notna(vix_now)
                        and pd.notna(recovery)
                        and vix_now < 25.0
                        and recovery >= 0.05
                    )

                if condition:
                    release_date = row[
                        "signal_date"
                    ]
                    release_idx = idx
                    break

        # ----------------------------------------------------
        # Counterfactual exposure
        #
        # Before release:
        #     keep production Filter15 exposure (normally 0).
        #
        # After release:
        #     restore Filter13 risk budget.
        #
        # This isolates the economic value/cost of the
        # deadman release gate itself.
        #
        # We deliberately DO NOT invent a new Filter15
        # post-release sizing algorithm here.
        # ----------------------------------------------------

        cf_exposure = (
            block["baseline_exposure_15"]
            .copy()
        )

        if release_idx is not None:

            release_mask = (
                block.index >= release_idx
            )

            cf_exposure.loc[
                release_mask
            ] = (
                block.loc[
                    release_mask,
                    "risk_budget_13",
                ]
            )

        # ----------------------------------------------------
        # Execution timing:
        #
        # Today's signal affects NEXT row's return.
        # ----------------------------------------------------

        executed_exposure = (
            cf_exposure
            .shift(1)
            .fillna(0.0)
            / 100.0
        )

        baseline_executed = (
            block["baseline_exposure_15"]
            .shift(1)
            .fillna(0.0)
            / 100.0
        )

        cf_return = (
            executed_exposure
            * block["spy_return"].fillna(0.0)
        )

        baseline_return = (
            baseline_executed
            * block["spy_return"].fillna(0.0)
        )

        cf_total_return = (
            (1.0 + cf_return).prod()
            - 1.0
        )

        baseline_total_return = (
            (1.0 + baseline_return).prod()
            - 1.0
        )

        incremental_return = (
            cf_total_return
            - baseline_total_return
        )

        cf_mdd = max_drawdown_from_returns(
            cf_return
        )

        baseline_mdd = (
            max_drawdown_from_returns(
                baseline_return
            )
        )

        incremental_mdd = (
            cf_mdd
            - baseline_mdd
        )

        rows_early = 0

        if release_idx is not None:
            rows_early = int(
                (
                    block.index
                    >= release_idx
                ).sum()
            )

        episode_records.append(
            {
                "episode_id":
                    episode_id,

                "candidate":
                    candidate,

                "dominant_trigger":
                    dominant_trigger,

                "start_signal_date":
                    start,

                "production_end_signal_date":
                    end,

                "counterfactual_release_date":
                    release_date,

                "duration_rows":
                    len(block),

                "rows_released_early":
                    rows_early,

                "baseline_return":
                    baseline_total_return,

                "counterfactual_return":
                    cf_total_return,

                "incremental_return":
                    incremental_return,

                "baseline_mdd":
                    baseline_mdd,

                "counterfactual_mdd":
                    cf_mdd,

                "incremental_mdd":
                    incremental_mdd,
            }
        )

        for local_i, (
            idx,
            row,
        ) in enumerate(
            block.iterrows()
        ):

            daily_records.append(
                {
                    "episode_id":
                        episode_id,

                    "candidate":
                        candidate,

                    "signal_date":
                        row["signal_date"],

                    "dominant_trigger":
                        dominant_trigger,

                    "HY_OAS":
                        row["HY_OAS"],

                    "VIX":
                        row["VIX"],

                    "SPY":
                        row["SPY"],

                    "running_spy_low":
                        row[
                            "running_spy_low"
                        ],

                    "spy_recovery_from_running_low":
                        row[
                            "spy_recovery_from_running_low"
                        ],

                    "hy_falling":
                        row["hy_falling"],

                    "baseline_exposure_15":
                        row[
                            "baseline_exposure_15"
                        ],

                    "counterfactual_exposure":
                        cf_exposure.loc[idx],

                    "counterfactual_release_date":
                        release_date,

                    "spy_return":
                        row["spy_return"],

                    "baseline_strategy_return":
                        baseline_return.loc[idx],

                    "counterfactual_strategy_return":
                        cf_return.loc[idx],
                }
            )


# ============================================================
# Results
# ============================================================

daily_out = pd.DataFrame(
    daily_records
)

episode_out = pd.DataFrame(
    episode_records
)


# ============================================================
# Summary
# ============================================================

summary_rows = []

for candidate in CANDIDATES:

    x = episode_out[
        episode_out["candidate"]
        == candidate
    ].copy()

    if x.empty:
        continue

    released = x[
        x[
            "counterfactual_release_date"
        ].notna()
    ]

    summary_rows.append(
        {
            "candidate":
                candidate,

            "episodes":
                len(x),

            "episodes_released_early":
                len(released),

            "pct_released_early":
                (
                    len(released)
                    / len(x)
                    * 100.0
                ),

            "avg_rows_released_early":
                (
                    released[
                        "rows_released_early"
                    ].mean()
                    if len(released)
                    else 0.0
                ),

            "avg_incremental_return":
                x[
                    "incremental_return"
                ].mean(),

            "median_incremental_return":
                x[
                    "incremental_return"
                ].median(),

            "total_incremental_return":
                x[
                    "incremental_return"
                ].sum(),

            "positive_incremental_episodes":
                int(
                    (
                        x[
                            "incremental_return"
                        ]
                        > 0
                    ).sum()
                ),

            "negative_incremental_episodes":
                int(
                    (
                        x[
                            "incremental_return"
                        ]
                        < 0
                    ).sum()
                ),

            "avg_incremental_mdd":
                x[
                    "incremental_mdd"
                ].mean(),

            "worst_incremental_mdd":
                x[
                    "incremental_mdd"
                ].min(),
        }
    )


summary = pd.DataFrame(
    summary_rows
)


# ============================================================
# HY-dominant subset
# ============================================================

hy_subset = episode_out[
    episode_out[
        "dominant_trigger"
    ].eq("HY_OAS_GE_6")
].copy()

hy_summary_rows = []

for candidate in CANDIDATES:

    x = hy_subset[
        hy_subset["candidate"]
        == candidate
    ]

    if x.empty:
        continue

    released = x[
        x[
            "counterfactual_release_date"
        ].notna()
    ]

    hy_summary_rows.append(
        {
            "candidate":
                candidate,

            "hy_episodes":
                len(x),

            "hy_released_early":
                len(released),

            "hy_avg_rows_released_early":
                (
                    released[
                        "rows_released_early"
                    ].mean()
                    if len(released)
                    else 0.0
                ),

            "hy_avg_incremental_return":
                x[
                    "incremental_return"
                ].mean(),

            "hy_total_incremental_return":
                x[
                    "incremental_return"
                ].sum(),

            "hy_avg_incremental_mdd":
                x[
                    "incremental_mdd"
                ].mean(),

            "hy_worst_incremental_mdd":
                x[
                    "incremental_mdd"
                ].min(),
        }
    )


hy_summary = pd.DataFrame(
    hy_summary_rows
)


# ============================================================
# Save
# ============================================================

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

daily_out.to_csv(
    OUT_DAILY,
    index=False,
)

episode_out.to_csv(
    OUT_EPISODES,
    index=False,
)

summary.to_csv(
    OUT_SUMMARY,
    index=False,
)


# ============================================================
# Audit report
# ============================================================

lines = []

lines.append(
    "=" * 78
)

lines.append(
    "FILTER15 DEADMAN RELEASE GATE COUNTERFACTUAL"
)

lines.append(
    "=" * 78
)

lines.append("")

lines.append(
    f"Episodes Analyzed : "
    f"{episode_out['episode_id'].nunique()}"
)

lines.append(
    f"Daily Rows        : "
    f"{len(daily_out)}"
)

lines.append("")

lines.append(
    "Production source modified : NO"
)

lines.append(
    "Future-data backfill       : NO"
)

lines.append(
    "SPY recovery calculation   : "
    "POINT-IN-TIME RUNNING LOW"
)

lines.append(
    "Execution timing           : "
    "SIGNAL t -> RETURN t+1"
)

lines.append("")

lines.append(
    "===== INPUT SOURCES ====="
)

lines.append(
    f"Risk Budget : {risk_budget_source}"
)

lines.append(
    f"Exposure    : {exposure_source}"
)

lines.append(
    f"HY OAS      : {hy_source}"
)

lines.append(
    f"VIX         : {vix_source}"
)

lines.append(
    f"SPY         : {spy_source}"
)

lines.append("")

lines.append(
    "===== ALL DEADMAN EPISODES ====="
)

if not summary.empty:
    lines.append(
        summary.to_string(
            index=False
        )
    )

lines.append("")

lines.append(
    "===== HY_OAS DOMINANT EPISODES ====="
)

if not hy_summary.empty:
    lines.append(
        hy_summary.to_string(
            index=False
        )
    )

lines.append("")

lines.append(
    "=" * 78
)

lines.append(
    "INTERPRETATION RULE"
)

lines.append(
    "=" * 78
)

lines.append(
    ""
)

lines.append(
    "A candidate is NOT accepted merely because "
    "incremental return is positive."
)

lines.append(
    "A release rule is economically interesting only if:"
)

lines.append(
    "1. recovery participation improves materially,"
)

lines.append(
    "2. incremental drawdown remains controlled,"
)

lines.append(
    "3. results are not driven by one crisis episode,"
)

lines.append(
    "4. performance survives episode-by-episode review,"
)

lines.append(
    "5. no future information is used."
)

lines.append("")

lines.append(
    "This audit does NOT authorize a Production change."
)

lines.append(
    "Any candidate must pass a separate robustness / "
    "release gate before promotion."
)

text = "\n".join(lines)

OUT_TXT.write_text(
    text,
    encoding="utf-8",
)


# ============================================================
# Console
# ============================================================

print()
print(text)
print()

print(
    f"Saved: {OUT_DAILY}"
)

print(
    f"Saved: {OUT_EPISODES}"
)

print(
    f"Saved: {OUT_SUMMARY}"
)

print(
    f"Saved: {OUT_TXT}"
)