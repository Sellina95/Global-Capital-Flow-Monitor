from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

SOURCE = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_v3_execution_contract_v1"
    / "macro_v3_execution_contract_daily.csv"
)

OUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "macro_unknown_decay_sensitivity_v1"
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

DAILY_OUT = OUT_DIR / "unknown_decay_daily.csv"
SUMMARY_OUT = OUT_DIR / "unknown_decay_structural_summary.csv"
DURATION_OUT = OUT_DIR / "unknown_decay_state_durations.csv"
SHOCK_OUT = OUT_DIR / "unknown_decay_credit_stress_safety.csv"
AUDIT_OUT = OUT_DIR / "unknown_decay_sensitivity_audit.txt"


# ============================================================
# LOAD FROZEN RAW MACRO HISTORY
# ============================================================

if not SOURCE.exists():
    raise FileNotFoundError(SOURCE)

df = pd.read_csv(
    SOURCE,
    parse_dates=[
        "signal_date",
        "execution_date",
    ],
)

required = {
    "signal_date",
    "execution_date",
    "raw_macro_narrative",
}

missing = required - set(df.columns)

if missing:
    raise RuntimeError(
        f"Missing required fields: {sorted(missing)}"
    )

raw = (
    df["raw_macro_narrative"]
    .fillna("UNKNOWN_TRANSITION")
    .astype(str)
)

dates = df["signal_date"]


# ============================================================
# FROZEN EXPERIMENT REGISTRY
#
# IMPORTANT:
# These are sensitivity experiments.
# No horizon is selected here.
# ============================================================

EXPERIMENTS = {
    "U1": 1,
    "U2": 2,
    "U3": 3,
    "U5": 5,
}

UNKNOWN = "UNKNOWN_TRANSITION"


# ============================================================
# STATE MACHINE
#
# Entry:
#   New non-UNKNOWN state requires P2 confirmation.
#
# Exit / UNKNOWN:
#   Existing strategic state may survive UNKNOWN for at most
#   grace observations.
#
#   Once UNKNOWN streak > grace:
#       strategic state becomes UNKNOWN_TRANSITION.
#
# Recovery from UNKNOWN:
#   A new non-UNKNOWN state again requires P2 confirmation.
#
# No future backfill.
# ============================================================

def build_state(
    raw_states: pd.Series,
    grace: int,
) -> list[str | None]:

    result: list[str | None] = []

    strategic: str | None = None

    candidate: str | None = None
    candidate_count = 0

    unknown_streak = 0

    for value in raw_states:

        state = str(value)

        # ----------------------------------------------------
        # UNKNOWN
        # ----------------------------------------------------

        if state == UNKNOWN:

            candidate = None
            candidate_count = 0

            if strategic is None:
                result.append(None)
                continue

            unknown_streak += 1

            if unknown_streak <= grace:
                result.append(strategic)
            else:
                strategic = UNKNOWN
                result.append(UNKNOWN)

            continue

        # ----------------------------------------------------
        # NON-UNKNOWN
        # ----------------------------------------------------

        unknown_streak = 0

        # Current strategic state already agrees.
        if strategic == state:
            candidate = None
            candidate_count = 0
            result.append(strategic)
            continue

        # New candidate confirmation.
        if candidate == state:
            candidate_count += 1
        else:
            candidate = state
            candidate_count = 1

        # P2 entry confirmation.
        if candidate_count >= 2:
            strategic = state
            candidate = None
            candidate_count = 0

        result.append(strategic)

    return result


# ============================================================
# HELPERS
# ============================================================

def transition_count(series: pd.Series) -> int:

    valid = series.dropna().astype(str)

    if len(valid) <= 1:
        return 0

    return int(
        valid.ne(valid.shift(1))
        .iloc[1:]
        .sum()
    )


def aba_count(series: pd.Series) -> int:

    values = series.tolist()

    count = 0

    for i in range(1, len(values) - 1):

        a = values[i - 1]
        b = values[i]
        c = values[i + 1]

        if (
            pd.notna(a)
            and pd.notna(b)
            and pd.notna(c)
            and a == c
            and a != b
        ):
            count += 1

    return count


def state_runs(
    dates_: pd.Series,
    states_: pd.Series,
    experiment: str,
) -> pd.DataFrame:

    rows = []

    start = None
    current = None
    duration = 0

    for date, state in zip(dates_, states_):

        if pd.isna(state):
            if current is not None:
                rows.append({
                    "experiment": experiment,
                    "state": current,
                    "start_date": start,
                    "end_date": previous_date,
                    "duration": duration,
                })

            start = None
            current = None
            duration = 0
            previous_date = date
            continue

        state = str(state)

        if current is None:
            current = state
            start = date
            duration = 1

        elif state == current:
            duration += 1

        else:
            rows.append({
                "experiment": experiment,
                "state": current,
                "start_date": start,
                "end_date": previous_date,
                "duration": duration,
            })

            current = state
            start = date
            duration = 1

        previous_date = date

    if current is not None:
        rows.append({
            "experiment": experiment,
            "state": current,
            "start_date": start,
            "end_date": previous_date,
            "duration": duration,
        })

    return pd.DataFrame(rows)


# ============================================================
# RAW CREDIT_STRESS EPISODES
#
# Persistent shock definition remains frozen:
# RAW CREDIT_STRESS duration >= 3 observations.
# ============================================================

credit_episodes = []

start = None
length = 0

for i, state in enumerate(raw):

    if state == "CREDIT_STRESS":

        if start is None:
            start = i
            length = 1
        else:
            length += 1

    else:

        if start is not None:
            credit_episodes.append(
                (start, i - 1, length)
            )

        start = None
        length = 0

if start is not None:
    credit_episodes.append(
        (start, len(raw) - 1, length)
    )

persistent_credit = [
    episode
    for episode in credit_episodes
    if episode[2] >= 3
]


# ============================================================
# RUN SENSITIVITY
# ============================================================

daily = df[
    [
        "signal_date",
        "execution_date",
        "raw_macro_narrative",
    ]
].copy()

summary_rows = []
duration_frames = []
shock_rows = []


for experiment, grace in EXPERIMENTS.items():

    states = pd.Series(
        build_state(
            raw,
            grace,
        ),
        index=df.index,
        dtype="object",
    )

    daily[
        f"strategic_state_{experiment}"
    ] = states

    valid = states.notna()

    observations = int(valid.sum())

    transitions = transition_count(
        states
    )

    aba = aba_count(
        states
    )

    strategic_unknown_days = int(
        states.eq(UNKNOWN).sum()
    )

    disagreement = (
        valid
        &
        states.astype(str).ne(
            raw.astype(str)
        )
    )

    # --------------------------------------------------------
    # Defensive state occupancy — STATE level only.
    # No portfolio regime mapping here.
    # --------------------------------------------------------

    defensive_states = {
        "CREDIT_STRESS",
        "STAGFLATION_RISK",
        "TIGHTENING_GROWTH_SCARE",
    }

    defensive_days = int(
        states.isin(
            defensive_states
        ).sum()
    )

    raw_defensive_days = int(
        raw.isin(
            defensive_states
        ).sum()
    )

    # --------------------------------------------------------
    # Durations
    # --------------------------------------------------------

    runs = state_runs(
        dates,
        states,
        experiment,
    )

    duration_frames.append(
        runs
    )

    if runs.empty:
        mean_duration = float("nan")
        median_duration = float("nan")
        max_duration = 0
    else:
        mean_duration = float(
            runs["duration"].mean()
        )
        median_duration = float(
            runs["duration"].median()
        )
        max_duration = int(
            runs["duration"].max()
        )

    # --------------------------------------------------------
    # Persistent CREDIT_STRESS safety
    # --------------------------------------------------------

    adopted = 0
    delays = []

    for start_idx, end_idx, raw_duration in persistent_credit:

        episode_states = states.iloc[
            start_idx : end_idx + 1
        ]

        hits = [
            offset
            for offset, value
            in enumerate(
                episode_states.tolist()
            )
            if value == "CREDIT_STRESS"
        ]

        if hits:
            adopted += 1
            delays.append(
                hits[0]
            )

    persistent_total = len(
        persistent_credit
    )

    adoption_rate = (
        adopted / persistent_total
        if persistent_total
        else float("nan")
    )

    mean_delay = (
        float(pd.Series(delays).mean())
        if delays
        else float("nan")
    )

    median_delay = (
        float(pd.Series(delays).median())
        if delays
        else float("nan")
    )

    max_delay = (
        int(max(delays))
        if delays
        else None
    )

    shock_rows.append({
        "experiment": experiment,
        "unknown_grace": grace,
        "persistent_shocks": persistent_total,
        "adopted": adopted,
        "adoption_rate": adoption_rate,
        "mean_delay": mean_delay,
        "median_delay": median_delay,
        "max_delay": max_delay,
    })

    summary_rows.append({
        "experiment": experiment,
        "unknown_grace": grace,
        "observations": observations,
        "transitions": transitions,
        "transition_rate": (
            transitions / observations
            if observations
            else float("nan")
        ),
        "aba_centers": aba,
        "strategic_unknown_days": strategic_unknown_days,
        "strategic_unknown_rate": (
            strategic_unknown_days / observations
            if observations
            else float("nan")
        ),
        "raw_slow_disagreement_days": int(
            disagreement.sum()
        ),
        "raw_slow_disagreement_rate": (
            disagreement.sum() / observations
            if observations
            else float("nan")
        ),
        "raw_defensive_days": raw_defensive_days,
        "strategic_defensive_days": defensive_days,
        "defensive_day_delta": (
            defensive_days
            - raw_defensive_days
        ),
        "mean_state_duration": mean_duration,
        "median_state_duration": median_duration,
        "max_state_duration": max_duration,
    })


summary = pd.DataFrame(
    summary_rows
)

shock = pd.DataFrame(
    shock_rows
)

durations = pd.concat(
    duration_frames,
    ignore_index=True,
)


# ============================================================
# SAVE
# ============================================================

daily.to_csv(
    DAILY_OUT,
    index=False,
)

summary.to_csv(
    SUMMARY_OUT,
    index=False,
)

durations.to_csv(
    DURATION_OUT,
    index=False,
)

shock.to_csv(
    SHOCK_OUT,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print("=" * 126)
print("MACRO UNKNOWN DECAY — STRUCTURAL SENSITIVITY")
print("=" * 126)

print()
print("===== EXPERIMENT CONTRACT =====")
print("Entry persistence : P2")
print("UNKNOWN behavior  : finite grace -> UNKNOWN_TRANSITION")
print("Experiments       : U1 / U2 / U3 / U5")
print("Returns used      : NO")
print("13/15/18 used     : NO")
print("Parameter selected: NO")

print()
print("===== STRUCTURAL SUMMARY =====")

display_summary = summary.copy()

print(
    display_summary.to_string(
        index=False,
        formatters={
            "transition_rate":
                lambda x: f"{x:.2%}",
            "strategic_unknown_rate":
                lambda x: f"{x:.2%}",
            "raw_slow_disagreement_rate":
                lambda x: f"{x:.2%}",
            "mean_state_duration":
                lambda x: f"{x:.2f}",
            "median_state_duration":
                lambda x: f"{x:.2f}",
        },
    )
)

print()
print("===== PERSISTENT CREDIT_STRESS SAFETY =====")

print(
    shock.to_string(
        index=False,
        formatters={
            "adoption_rate":
                lambda x: f"{x:.2%}",
            "mean_delay":
                lambda x: f"{x:.2f}",
            "median_delay":
                lambda x: f"{x:.2f}",
        },
    )
)

print()
print("===== INTERPRETATION CONTRACT =====")
print("""
Do NOT select the grace period with the lowest transition count.

The purpose is to find the smallest UNKNOWN grace that:

1. preserves the P2 anti-whipsaw benefit,
2. avoids indefinite stale-state persistence,
3. materially reduces defensive occupancy distortion,
4. preserves recognition of persistent CREDIT_STRESS,
5. does not create pathological UNKNOWN churn.

No returns, CAGR, Sharpe, or portfolio performance may be
used to choose U1/U2/U3/U5 at this gate.
""".strip())


audit = f"""
MACRO UNKNOWN DECAY SENSITIVITY V1

DESIGN
------
Entry persistence       : P2
UNKNOWN release         : finite grace then UNKNOWN_TRANSITION
Sensitivity experiments : U1 / U2 / U3 / U5

PURPOSE
-------
Test whether finite UNKNOWN grace can preserve the structural
benefit of P2 while preventing the indefinite defensive-state
persistence observed in Macro V3.

SELECTION
---------
NO candidate selected.

SAFETY
------
Production modified : NO
Filter13 modified   : NO
Filter15 modified   : NO
Filter18 modified   : NO
13/15/18 executed   : NO
Returns used        : NO
CAGR used           : NO
Sharpe used         : NO
Parameter tuning    : NO
Commit              : NO
""".strip()

AUDIT_OUT.write_text(
    audit,
    encoding="utf-8",
)


print()
print("===== ARTIFACTS =====")
print("Daily     :", DAILY_OUT)
print("Summary   :", SUMMARY_OUT)
print("Durations :", DURATION_OUT)
print("Shock     :", SHOCK_OUT)
print("Audit     :", AUDIT_OUT)

print()
print("PRODUCTION MODIFIED : NO")
print("FILTER13/15/18      : UNCHANGED / NOT EXECUTED")
print("RETURNS USED        : NO")
print("PERFORMANCE USED    : NO")
print("PARAMETER SELECTED  : NO")
print("COMMIT              : NO")

print()
print("=" * 126)
print("UNKNOWN DECAY SENSITIVITY COMPLETE — DO NOT COMMIT")
print("=" * 126)
