from __future__ import annotations

import contextlib
import io
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import pandas as pd

from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)


ROOT = Path(__file__).resolve().parents[2]

PANEL_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

CONTRACT_PATH = (
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
    / "macro_unknown_evidence_attribution_v1"
)

OUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DAILY_OUT = OUT_DIR / "unknown_evidence_daily.csv"
COMBO_OUT = OUT_DIR / "unknown_evidence_combinations.csv"
REASON_OUT = OUT_DIR / "unknown_reason_summary.csv"
EPISODE_OUT = OUT_DIR / "unknown_episodes.csv"
TRANSITION_OUT = OUT_DIR / "unknown_neighbor_transitions.csv"
AUDIT_OUT = OUT_DIR / "unknown_evidence_attribution_audit.txt"


UNKNOWN = "UNKNOWN_TRANSITION"


# ============================================================
# LOAD
# ============================================================

panel = pd.read_csv(
    PANEL_PATH,
    parse_dates=[
        "date",
        "signal_date",
        "execution_date",
    ],
)

contract = pd.read_csv(
    CONTRACT_PATH,
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

missing = required - set(contract.columns)

if missing:
    raise RuntimeError(
        f"Contract missing fields: {sorted(missing)}"
    )


# ============================================================
# PANEL INDEX MAP
# ============================================================

panel_signal = pd.to_datetime(
    panel["signal_date"],
    errors="coerce",
)

index_map = {}

for idx, value in panel_signal.items():

    if pd.notna(value):
        index_map[
            pd.Timestamp(value).normalize()
        ] = int(idx)


# ============================================================
# HELPERS
# ============================================================

def clean_int(value):

    try:
        if value is None or pd.isna(value):
            return None

        return int(value)

    except Exception:
        return None


def clean_float(value):

    try:
        if value is None or pd.isna(value):
            return None

        return float(value)

    except Exception:
        return None


def classify_unknown_reason(
    us10y,
    dxy,
    vix,
    wti,
    hy_status,
    vix_today,
):

    """
    IMPORTANT

    This does NOT invent a new macro regime.

    It only describes WHY the exact Production
    interpret_macro_narrative() decision tree reached
    its final residual UNKNOWN_TRANSITION branch.
    """

    dirs = {
        "US10Y": us10y,
        "DXY": dxy,
        "VIX": vix,
        "WTI": wti,
    }

    missing_dirs = [
        key
        for key, value in dirs.items()
        if value not in (-1, 0, 1)
    ]

    if missing_dirs:
        return (
            "MISSING_DIRECTION_EVIDENCE",
            ",".join(missing_dirs),
        )

    zero_dirs = [
        key
        for key, value in dirs.items()
        if value == 0
    ]

    # Production's named directional narratives
    # mostly require exact +/- combinations.
    if zero_dirs:
        return (
            "FLAT_OR_NO_DIRECTION",
            ",".join(zero_dirs),
        )

    # POLICY_EASING requires:
    # US10Y=-1, DXY=-1, VIX != +1.
    #
    # Therefore this exact combination fails because
    # VIX is rising.
    if (
        us10y == -1
        and dxy == -1
        and vix == 1
    ):
        return (
            "EASING_AXES_BUT_VIX_RISING",
            "US10Y_DOWN+DXY_DOWN+VIX_UP",
        )

    # Remaining cases have valid +/- directions but
    # simply do not belong to any named Production rule.
    return (
        "UNMAPPED_DIRECTION_COMBINATION",
        (
            f"US10Y={us10y}|"
            f"DXY={dxy}|"
            f"VIX={vix}|"
            f"WTI={wti}|"
            f"HY={hy_status}"
        ),
    )


# ============================================================
# RECONSTRUCT EXACT PIT TAPE
#
# We execute only the pre-13 generator chain.
# Filter13 / Filter15 / Filter18 are NOT executed.
# ============================================================

rows = []

flow_memory = {
    "flow_state": "N/A",
    "flow_score": 0,
    "persistence_days": 0,
}

contract_lookup = (
    contract
    .set_index(
        contract["signal_date"].dt.normalize()
    )
)

total = len(contract)

for count, record in enumerate(
    contract.itertuples(index=False),
    start=1,
):

    signal_date = pd.Timestamp(
        record.signal_date
    ).normalize()

    if signal_date not in index_map:
        raise RuntimeError(
            "Signal date not found in master_panel: "
            f"{signal_date.date()}"
        )

    idx = index_map[signal_date]

    md = build_market_data(
        panel=panel,
        row_index=idx,
        previous_exposure=None,
    )

    # Exact historical/PIT pre-13 chain.
    with contextlib.redirect_stdout(
        io.StringIO()
    ):
        flow_memory = (
            prepare_filter13_execution_state(
                market_data=md,
                panel=panel,
                row_index=idx,
                previous_flow_memory=flow_memory,
            )
        )

    actual_raw = str(
        md.get(
            "MACRO_NARRATIVE",
            "",
        )
    )

    expected_raw = str(
        record.raw_macro_narrative
    )

    if actual_raw != expected_raw:
        raise RuntimeError(
            "RAW macro reconstruction mismatch "
            f"on {signal_date.date()}: "
            f"expected={expected_raw}, "
            f"actual={actual_raw}"
        )

    tape = (
        md.get(
            "CROSS_ASSET_TAPE",
            {},
        )
        or {}
    )

    us10y = clean_int(
        tape.get("US10Y_DIR")
    )

    dxy = clean_int(
        tape.get("DXY_DIR")
    )

    vix = clean_int(
        tape.get("VIX_DIR")
    )

    wti = clean_int(
        tape.get("WTI_DIR")
    )

    hy_status = str(
        tape.get(
            "HY_OAS_STATUS",
            "UNKNOWN",
        )
    )

    vix_today = clean_float(
        tape.get(
            "VIX_TODAY"
        )
    )

    reason = ""
    reason_detail = ""

    if actual_raw == UNKNOWN:

        reason, reason_detail = (
            classify_unknown_reason(
                us10y=us10y,
                dxy=dxy,
                vix=vix,
                wti=wti,
                hy_status=hy_status,
                vix_today=vix_today,
            )
        )

    rows.append({
        "signal_date": signal_date,
        "execution_date": record.execution_date,
        "raw_macro_narrative": actual_raw,
        "is_unknown": (
            actual_raw == UNKNOWN
        ),
        "US10Y_DIR": us10y,
        "DXY_DIR": dxy,
        "VIX_DIR": vix,
        "WTI_DIR": wti,
        "HY_OAS_STATUS": hy_status,
        "VIX_TODAY": vix_today,
        "US10Y_Z": clean_float(
            tape.get("US10Y_Z")
        ),
        "DXY_Z": clean_float(
            tape.get("DXY_Z")
        ),
        "VIX_Z": clean_float(
            tape.get("VIX_Z")
        ),
        "WTI_Z": clean_float(
            tape.get("WTI_Z")
        ),
        "unknown_reason": reason,
        "unknown_reason_detail": reason_detail,
    })

    if (
        count % 250 == 0
        or count == total
    ):
        print(
            f"\rProcessed {count}/{total}",
            end="",
            flush=True,
        )

print()


daily = pd.DataFrame(rows)


# ============================================================
# NEIGHBOR STATES
#
# Descriptive only.
# No future information is used to GENERATE a signal.
# next_raw_state is only retrospective audit metadata.
# ============================================================

daily["previous_raw_state"] = (
    daily[
        "raw_macro_narrative"
    ].shift(1)
)

daily["next_raw_state"] = (
    daily[
        "raw_macro_narrative"
    ].shift(-1)
)


unknown = daily[
    daily["is_unknown"]
].copy()


# ============================================================
# CONTRACT GATE
# ============================================================

expected_unknown = int(
    contract[
        "raw_macro_narrative"
    ]
    .astype(str)
    .eq(UNKNOWN)
    .sum()
)

actual_unknown = len(
    unknown
)

if actual_unknown != expected_unknown:
    raise RuntimeError(
        "UNKNOWN count identity failed: "
        f"expected={expected_unknown}, "
        f"actual={actual_unknown}"
    )


# ============================================================
# EXACT EVIDENCE COMBINATIONS
# ============================================================

combo_cols = [
    "US10Y_DIR",
    "DXY_DIR",
    "VIX_DIR",
    "WTI_DIR",
    "HY_OAS_STATUS",
]

combos = (
    unknown
    .groupby(
        combo_cols,
        dropna=False,
    )
    .size()
    .rename("observations")
    .reset_index()
    .sort_values(
        "observations",
        ascending=False,
    )
)

combos["share_of_unknown"] = (
    combos["observations"]
    / actual_unknown
)


# ============================================================
# REASON SUMMARY
# ============================================================

reasons = (
    unknown
    .groupby(
        [
            "unknown_reason",
            "unknown_reason_detail",
        ],
        dropna=False,
    )
    .size()
    .rename("observations")
    .reset_index()
    .sort_values(
        "observations",
        ascending=False,
    )
)

reasons["share_of_unknown"] = (
    reasons["observations"]
    / actual_unknown
)


# ============================================================
# UNKNOWN EPISODES
# ============================================================

episode_rows = []

episode_id = 0
start_idx = None

unknown_mask = (
    daily["is_unknown"]
    .tolist()
)

for i, flag in enumerate(
    unknown_mask
):

    if flag and start_idx is None:
        start_idx = i

    is_last = (
        i == len(unknown_mask) - 1
    )

    if (
        start_idx is not None
        and (
            (not flag)
            or is_last
        )
    ):

        if flag and is_last:
            end_idx = i
        else:
            end_idx = i - 1

        episode_id += 1

        block = daily.iloc[
            start_idx : end_idx + 1
        ]

        prev_state = (
            daily.iloc[
                start_idx - 1
            ]["raw_macro_narrative"]
            if start_idx > 0
            else None
        )

        next_state = (
            daily.iloc[
                end_idx + 1
            ]["raw_macro_narrative"]
            if end_idx + 1 < len(daily)
            else None
        )

        episode_rows.append({
            "episode_id": episode_id,
            "start_date": block[
                "signal_date"
            ].iloc[0],
            "end_date": block[
                "signal_date"
            ].iloc[-1],
            "duration": len(block),
            "previous_raw_state": prev_state,
            "next_raw_state": next_state,
            "dominant_reason": (
                block[
                    "unknown_reason"
                ]
                .value_counts()
                .index[0]
            ),
        })

        start_idx = None


episodes = pd.DataFrame(
    episode_rows
)


# ============================================================
# NEIGHBOR TRANSITION MATRIX
#
# This tells us whether UNKNOWN commonly means:
#
# A -> UNKNOWN -> A
# A -> UNKNOWN -> B
#
# without changing the state machine yet.
# ============================================================

neighbors = (
    unknown
    .groupby(
        [
            "previous_raw_state",
            "next_raw_state",
        ],
        dropna=False,
    )
    .size()
    .rename("unknown_days")
    .reset_index()
    .sort_values(
        "unknown_days",
        ascending=False,
    )
)

neighbors["share_of_unknown"] = (
    neighbors["unknown_days"]
    / actual_unknown
)


# ============================================================
# SAVE
# ============================================================

daily.to_csv(
    DAILY_OUT,
    index=False,
)

combos.to_csv(
    COMBO_OUT,
    index=False,
)

reasons.to_csv(
    REASON_OUT,
    index=False,
)

episodes.to_csv(
    EPISODE_OUT,
    index=False,
)

neighbors.to_csv(
    TRANSITION_OUT,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print("=" * 128)
print("MACRO UNKNOWN — EVIDENCE ATTRIBUTION")
print("=" * 128)

print()
print("===== CONTRACT =====")
print(
    f"Rows                  : {len(daily)}"
)
print(
    f"Expected UNKNOWN      : {expected_unknown}"
)
print(
    f"Reconstructed UNKNOWN : {actual_unknown}"
)
print(
    "UNKNOWN identity      : PASS"
)

print()
print("===== UNKNOWN REASON SUMMARY =====")

print(
    reasons.to_string(
        index=False,
        formatters={
            "share_of_unknown":
                lambda x: f"{x:.2%}",
        },
    )
)

print()
print("===== TOP 20 EXACT EVIDENCE COMBINATIONS =====")

print(
    combos
    .head(20)
    .to_string(
        index=False,
        formatters={
            "share_of_unknown":
                lambda x: f"{x:.2%}",
        },
    )
)

print()
print("===== UNKNOWN EPISODE STRUCTURE =====")

if episodes.empty:

    print("NO EPISODES")

else:

    print(
        "Episodes              :",
        len(episodes),
    )
    print(
        "Mean duration         :",
        f"{episodes['duration'].mean():.2f}",
    )
    print(
        "Median duration       :",
        f"{episodes['duration'].median():.2f}",
    )
    print(
        "Max duration          :",
        int(
            episodes[
                "duration"
            ].max()
        ),
    )

    print()
    print("Duration distribution:")

    duration_dist = (
        episodes[
            "duration"
        ]
        .value_counts()
        .sort_index()
        .rename_axis(
            "duration"
        )
        .reset_index(
            name="episodes"
        )
    )

    print(
        duration_dist
        .head(20)
        .to_string(
            index=False
        )
    )


print()
print("===== TOP UNKNOWN NEIGHBOR PATHS =====")

print(
    neighbors
    .head(20)
    .to_string(
        index=False,
        formatters={
            "share_of_unknown":
                lambda x: f"{x:.2%}",
        },
    )
)


# ============================================================
# AUDIT MEMO
# ============================================================

reason_counts = {
    str(row.unknown_reason):
        int(row.observations)
    for row in reasons.itertuples()
}

audit = f"""
MACRO UNKNOWN EVIDENCE ATTRIBUTION V1

PURPOSE
-------
Explain why Production interpret_macro_narrative()
returns UNKNOWN_TRANSITION.

This audit does NOT redefine UNKNOWN and does NOT
introduce a new macro classifier.

CONTRACT
--------
Rows                    : {len(daily)}
Expected UNKNOWN        : {expected_unknown}
Reconstructed UNKNOWN   : {actual_unknown}
UNKNOWN identity        : PASS

REASON COUNTS
-------------
{reason_counts}

IMPORTANT
---------
UNKNOWN_TRANSITION is the residual branch of the current
Production decision tree.

This audit separates:

1. missing directional evidence,
2. flat / no-direction evidence,
3. easing axes blocked by rising VIX,
4. valid but unmapped directional combinations.

No candidate handling rule is selected here.

Neighbor states and next-state fields are retrospective
diagnostic metadata only. They are NOT used to generate
historical signals.

SAFETY
------
Production modified : NO
Filter13 modified   : NO
Filter15 modified   : NO
Filter18 modified   : NO
Filter13 executed   : NO
Filter15 executed   : NO
Filter18 executed   : NO
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
print("Daily      :", DAILY_OUT)
print("Combination:", COMBO_OUT)
print("Reasons    :", REASON_OUT)
print("Episodes   :", EPISODE_OUT)
print("Neighbors  :", TRANSITION_OUT)
print("Audit      :", AUDIT_OUT)

print()
print("PRODUCTION MODIFIED : NO")
print("FILTER13/15/18      : UNCHANGED / NOT EXECUTED")
print("RETURNS USED        : NO")
print("PERFORMANCE USED    : NO")
print("PARAMETER SELECTED  : NO")
print("COMMIT              : NO")

print()
print("=" * 128)
print("UNKNOWN EVIDENCE ATTRIBUTION COMPLETE — DO NOT COMMIT")
print("=" * 128)
