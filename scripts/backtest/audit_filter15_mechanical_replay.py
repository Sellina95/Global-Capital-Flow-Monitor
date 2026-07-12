"""
Filter 15 Mechanical Replay Audit
=================================

Purpose
-------
Replay Filter 15 independently from the production engine and attribute
the exact date-by-date reduction to:

- volatility
- positioning
- credit
- hard deadman
- rounding / clamp

The production strategy source is read-only and is never modified.

Input
-----
data/backtest/results/exposure_reduction_daily.csv

Outputs
-------
data/backtest/results/filter15_mechanical_replay_daily.csv
data/backtest/results/filter15_mechanical_replay_summary.csv
data/backtest/results/filter15_mechanical_replay_audit.txt
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

INPUT_PATH = RESULT_DIR / "exposure_reduction_daily.csv"

DAILY_OUT = RESULT_DIR / "filter15_mechanical_replay_daily.csv"
SUMMARY_CSV_OUT = RESULT_DIR / "filter15_mechanical_replay_summary.csv"
SUMMARY_TXT_OUT = RESULT_DIR / "filter15_mechanical_replay_audit.txt"


# ============================================================
# Helpers
# ============================================================

def to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def first_existing_column(
    df: pd.DataFrame,
    candidates: Iterable[str],
) -> str | None:
    exact_lookup = {
        str(column).lower(): str(column)
        for column in df.columns
    }

    for candidate in candidates:
        match = exact_lookup.get(candidate.lower())

        if match is not None:
            return match

    return None


def resolve_numeric_series(
    df: pd.DataFrame,
    candidates: Iterable[str],
    *,
    default: float | None = None,
) -> tuple[pd.Series, str]:
    column = first_existing_column(df, candidates)

    if column is not None:
        return to_numeric(df[column]), column

    if default is None:
        return (
            pd.Series(
                np.nan,
                index=df.index,
                dtype=float,
            ),
            "NOT_FOUND",
        )

    return (
        pd.Series(
            float(default),
            index=df.index,
            dtype=float,
        ),
        f"DEFAULT_{default}",
    )


def resolve_text_series(
    df: pd.DataFrame,
    candidates: Iterable[str],
    *,
    default: str = "",
) -> tuple[pd.Series, str]:
    column = first_existing_column(df, candidates)

    if column is not None:
        return (
            df[column]
            .fillna(default)
            .astype(str),
            column,
        )

    return (
        pd.Series(
            default,
            index=df.index,
            dtype="object",
        ),
        f"DEFAULT_{default}",
    )


def original_clamp(value: float) -> float:
    """
    Exact production behavior:

        max(0, min(int(round(x)), 100))
    """

    return float(
        max(
            0,
            min(
                int(round(float(value))),
                100,
            ),
        )
    )


def positive_reduction(
    before: float,
    after: float,
) -> float:
    return max(float(before) - float(after), 0.0)


# ============================================================
# Load and map inputs
# ============================================================

def load_data() -> tuple[
    pd.DataFrame,
    dict[str, str],
]:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input not found:\n{INPUT_PATH}\n\n"
            "Run audit_exposure_reduction.py first."
        )

    df = pd.read_csv(INPUT_PATH)

    required = {
        "signal_date",
        "risk_budget_13",
        "exposure_15",
    }

    missing = sorted(
        required - set(df.columns)
    )

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )

    df["risk_budget_13"] = to_numeric(
        df["risk_budget_13"]
    )

    df["exposure_15"] = to_numeric(
        df["exposure_15"]
    )

    df = (
        df.dropna(
            subset=[
                "signal_date",
                "risk_budget_13",
                "exposure_15",
            ]
        )
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    mappings: dict[str, str] = {}

    # --------------------------------------------------------
    # VIX
    # --------------------------------------------------------

    vix, mappings["vix"] = resolve_numeric_series(
        df,
        (
            "vix_today",
            "VIX",
            "sentiment__vix",
            "fred_sector__VIX",
        ),
    )

    vix_pct, mappings["vix_pct"] = resolve_numeric_series(
        df,
        (
            "vix_pct_change",
            "VIX_PCT_CHANGE",
            "vix_change_pct",
            "sentiment__vix_pct_change",
        ),
    )

    # Filter input used pct_change. If no saved pct-change column
    # exists, reconstruct it from the mapped VIX level.
    if vix_pct.isna().all():
        vix_pct = vix.pct_change() * 100.0
        mappings["vix_pct"] = (
            f"RECONSTRUCTED_FROM_{mappings['vix']}"
        )

    # --------------------------------------------------------
    # Positioning
    # --------------------------------------------------------

    pos_z, mappings["pos_z"] = resolve_numeric_series(
        df,
        (
            "positioning__SP500_POS_Z",
            "SP500_POS_Z",
            "sp500_pos_z",
        ),
        default=0.0,
    )

    pos_slope, mappings["pos_slope"] = resolve_numeric_series(
        df,
        (
            "positioning__POS_SLOPE",
            "POS_SLOPE",
            "pos_slope",
        ),
    )

    # The production function receives POS_SLOPE from market_data.
    # Use saved slope where possible; otherwise reconstruct the
    # one-period slope from POS_Z.
    if pos_slope.isna().all():
        pos_slope = pos_z.diff().fillna(0.0)
        mappings["pos_slope"] = (
            f"RECONSTRUCTED_DIFF_FROM_{mappings['pos_z']}"
        )
    else:
        pos_slope = pos_slope.fillna(0.0)

    gamma, mappings["gamma"] = resolve_numeric_series(
        df,
        (
            "positioning__DEALER_GAMMA_BIAS",
            "DEALER_GAMMA_BIAS",
            "dealer_gamma_bias",
        ),
        default=1.0,
    )

    cta, mappings["cta"] = resolve_numeric_series(
        df,
        (
            "positioning__CTA_MOMENTUM_SCORE",
            "cta_momentum_score",
            "CTA_MOMENTUM_SCORE",
        ),
        default=1.0,
    )

    # --------------------------------------------------------
    # Credit
    # --------------------------------------------------------

    hy_level, mappings["hy_level"] = resolve_numeric_series(
        df,
        (
            "hy_oas_today",
            "credit__HY_OAS",
            "sentiment__hy_oas",
            "HY_OAS",
        ),
    )

    hy_pct, mappings["hy_pct"] = resolve_numeric_series(
        df,
        (
            "hy_oas_pct_change",
            "HY_OAS_PCT_CHANGE",
            "credit__HY_OAS_PCT_CHANGE",
            "sentiment__hy_oas_pct_change",
        ),
    )

    if hy_pct.isna().all():
        hy_pct = hy_level.pct_change() * 100.0
        mappings["hy_pct"] = (
            f"RECONSTRUCTED_FROM_{mappings['hy_level']}"
        )

    # --------------------------------------------------------
    # Macro and cross-asset inputs for Hard Deadman
    # --------------------------------------------------------

    macro_narrative, mappings["macro_narrative"] = (
        resolve_text_series(
            df,
            (
                "MACRO_NARRATIVE",
                "macro_narrative",
                "macro_profile",
            ),
            default="N/A",
        )
    )

    vix_z, mappings["vix_z"] = resolve_numeric_series(
        df,
        (
            "CROSS_ASSET_VIX_Z",
            "cross_asset__VIX_Z",
            "VIX_Z",
            "vix_z",
        ),
        default=0.0,
    )

    # Store canonical replay inputs.
    df["_replay_vix"] = vix
    df["_replay_vix_pct"] = vix_pct
    df["_replay_pos_z"] = pos_z.fillna(0.0)
    df["_replay_pos_slope"] = pos_slope.fillna(0.0)
    df["_replay_gamma"] = gamma.fillna(1.0)
    df["_replay_cta"] = cta.fillna(1.0)
    df["_replay_hy_level"] = hy_level
    df["_replay_hy_pct"] = hy_pct
    df["_replay_macro_narrative"] = (
        macro_narrative
        .fillna("N/A")
        .astype(str)
        .str.upper()
    )
    df["_replay_vix_z"] = vix_z.fillna(0.0)

    return df, mappings


# ============================================================
# Exact independent replay
# ============================================================

def replay_one_row(
    row: pd.Series,
) -> dict[str, object]:
    risk_budget = float(
        row["risk_budget_13"]
    )

    vix_today = row["_replay_vix"]
    vix_pct = row["_replay_vix_pct"]

    pos_z = float(
        row["_replay_pos_z"]
    )

    pos_slope = float(
        row["_replay_pos_slope"]
    )

    gamma = float(
        row["_replay_gamma"]
    )

    cta = float(
        row["_replay_cta"]
    )

    hy_level = row["_replay_hy_level"]
    hy_pct = row["_replay_hy_pct"]

    macro_narrative = str(
        row["_replay_macro_narrative"]
    ).upper()

    vix_z = float(
        row["_replay_vix_z"]
    )

    # Production Filter 15 starts here.
    exposure = risk_budget

    volatility_reduction = 0.0
    positioning_reduction = 0.0
    credit_reduction = 0.0
    deadman_reduction = 0.0
    rounding_reduction = 0.0

    hard_deadman = False
    hard_deadman_reason = ""

    risk_compression = False
    compression_reason = ""

    # --------------------------------------------------------
    # Hard Deadman / Risk Compression decision
    # Exact production ordering
    # --------------------------------------------------------

    if (
        pd.notna(hy_level)
        and float(hy_level) >= 6.0
    ):
        hard_deadman = True
        hard_deadman_reason = (
            f"Credit Crisis / HY_OAS "
            f"{float(hy_level):.2f}%"
        )

    elif macro_narrative == "CREDIT_STRESS":
        hard_deadman = True
        hard_deadman_reason = (
            "Structural Credit Stress"
        )

    elif (
        macro_narrative == "STAGFLATION_RISK"
        and vix_z >= 3.0
    ):
        hard_deadman = True
        hard_deadman_reason = (
            "Stagflation Shock + Volatility Spike"
        )

    elif (
        pd.notna(vix_today)
        and float(vix_today) >= 30.0
    ):
        hard_deadman = True
        hard_deadman_reason = (
            f"VIX Panic ({float(vix_today):.2f})"
        )

    elif abs(pos_z) > 2.0:
        risk_compression = True
        compression_reason = (
            f"POS_Z Extreme ({pos_z:.2f})"
        )

    elif abs(pos_slope) > 0.5:
        risk_compression = True
        compression_reason = (
            f"Aggressive Slope ({pos_slope:.2f})"
        )

    # --------------------------------------------------------
    # Volatility multiplier
    # --------------------------------------------------------

    multiplier = 1.0
    vol_state = "UNKNOWN"

    if pd.notna(vix_today):
        vix_value = float(vix_today)

        if vix_value < 14.0:
            vol_state = "LOW"
            multiplier *= 1.05

        elif vix_value < 20.0:
            vol_state = "NORMAL"

        elif vix_value < 30.0:
            vol_state = "STRESS"
            multiplier *= 0.80

        else:
            vol_state = "PANIC"
            multiplier *= 0.60

    if pd.notna(vix_pct):
        vix_change = float(vix_pct)

        if vix_change > 5.0:
            multiplier *= 0.85

        elif vix_change < -5.0:
            multiplier *= 1.05

    # --------------------------------------------------------
    # VIX convexity adjustment is applied directly first
    # --------------------------------------------------------

    if (
        pd.notna(vix_today)
        and pd.notna(vix_pct)
    ):
        before = exposure

        if (
            float(vix_today) >= 20.0
            and float(vix_pct) >= 10.0
        ):
            exposure *= 0.85

        elif (
            float(vix_today) >= 18.0
            and float(vix_pct) >= 5.0
        ):
            exposure *= 0.92

        volatility_reduction += positive_reduction(
            before,
            exposure,
        )

    # --------------------------------------------------------
    # Positioning multiplier
    # --------------------------------------------------------

    pos_multiplier = 1.0

    if pos_z >= 2.0:
        pos_multiplier *= 0.85

    elif pos_z >= 1.7:
        pos_multiplier *= 0.90

    elif pos_z >= 1.5:
        pos_multiplier *= 0.95

    if (
        pos_z > 2.0
        and pos_slope < 0.0
    ):
        pos_multiplier *= 1.05

    if gamma < 0.5:
        pos_multiplier *= 0.85

    elif gamma > 1.5:
        pos_multiplier *= 1.03

    if cta <= 0.0:
        pos_multiplier *= 0.90

    # --------------------------------------------------------
    # Apply volatility and positioning in production order
    # --------------------------------------------------------

    before = exposure
    exposure *= multiplier

    volatility_reduction += positive_reduction(
        before,
        exposure,
    )

    before = exposure
    exposure *= pos_multiplier

    positioning_reduction += positive_reduction(
        before,
        exposure,
    )

    # Important:
    # The production code calculates a later leadership breadth
    # offset by modifying pos_multiplier after exposure has already
    # been multiplied. It therefore does not alter exposure and is
    # intentionally not applied in this replay.

    # --------------------------------------------------------
    # Credit level
    # --------------------------------------------------------

    if pd.notna(hy_level):
        before = exposure
        hy_value = float(hy_level)

        if hy_value >= 6.0:
            # No direct multiplier here.
            # Hard Deadman is applied later.
            pass

        elif hy_value >= 5.0:
            exposure *= 0.75

        elif hy_value >= 4.0:
            exposure *= 0.90

        credit_reduction += positive_reduction(
            before,
            exposure,
        )

    # --------------------------------------------------------
    # Credit change
    # --------------------------------------------------------

    if pd.notna(hy_pct):
        before = exposure
        hy_change = float(hy_pct)

        if hy_change >= 10.0:
            exposure *= 0.85

        elif hy_change >= 5.0:
            exposure *= 0.93

        credit_reduction += positive_reduction(
            before,
            exposure,
        )

    # --------------------------------------------------------
    # Hard Deadman
    # --------------------------------------------------------

    if hard_deadman:
        before = exposure
        exposure = 0.0

        deadman_reduction += positive_reduction(
            before,
            exposure,
        )

        status = "HARD_DEADMAN"

    elif risk_compression:
        status = "RISK_COMPRESSION"

    else:
        status = "NORMAL"

    # --------------------------------------------------------
    # Exact production clamp / integer rounding
    # --------------------------------------------------------

    before_clamp = exposure
    exposure = original_clamp(exposure)

    rounding_reduction = (
        before_clamp - exposure
    )

    # Rounding can either reduce or increase by less than 0.5.
    replay_error = (
        exposure
        - float(row["exposure_15"])
    )

    actual_reduction = max(
        risk_budget
        - float(row["exposure_15"]),
        0.0,
    )

    modeled_positive_reduction = (
        volatility_reduction
        + positioning_reduction
        + credit_reduction
        + deadman_reduction
        + max(rounding_reduction, 0.0)
    )

    return {
        "replay_exposure_15": exposure,
        "existing_exposure_15": float(
            row["exposure_15"]
        ),
        "replay_error": replay_error,
        "risk_budget_13": risk_budget,
        "actual_reduction_13_to_15": (
            actual_reduction
        ),
        "volatility_reduction": (
            volatility_reduction
        ),
        "positioning_reduction": (
            positioning_reduction
        ),
        "credit_reduction": (
            credit_reduction
        ),
        "deadman_reduction": (
            deadman_reduction
        ),
        "rounding_effect": rounding_reduction,
        "modeled_positive_reduction": (
            modeled_positive_reduction
        ),
        "hard_deadman": hard_deadman,
        "hard_deadman_reason": (
            hard_deadman_reason
        ),
        "risk_compression": risk_compression,
        "compression_reason": (
            compression_reason
        ),
        "replay_status": status,
        "vol_state": vol_state,
        "vol_multiplier": multiplier,
        "positioning_multiplier": (
            pos_multiplier
        ),
    }


# ============================================================
# Summary
# ============================================================

def build_summary(
    replay: pd.DataFrame,
) -> pd.DataFrame:
    family_columns = {
        "volatility": "volatility_reduction",
        "positioning": "positioning_reduction",
        "credit": "credit_reduction",
        "deadman": "deadman_reduction",
    }

    total_family_reduction = sum(
        replay[column].sum()
        for column in family_columns.values()
    )

    rows: list[dict[str, object]] = []

    for family, column in family_columns.items():
        total = float(
            replay[column].sum()
        )

        binding_days = int(
            (replay[column] > 1e-10).sum()
        )

        rows.append({
            "family": family,
            "total_reduction": total,
            "average_daily_reduction": float(
                replay[column].mean()
            ),
            "binding_days": binding_days,
            "binding_day_share": (
                binding_days / len(replay)
            ),
            "mechanical_brake_share": (
                total / total_family_reduction
                if total_family_reduction > 0
                else np.nan
            ),
        })

    return (
        pd.DataFrame(rows)
        .sort_values(
            "total_reduction",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def make_text_summary(
    replay: pd.DataFrame,
    summary: pd.DataFrame,
    mappings: dict[str, str],
) -> str:
    exact_match = (
        replay["replay_error"].abs()
        <= 1e-9
    )

    exact_match_count = int(
        exact_match.sum()
    )

    max_error = float(
        replay["replay_error"]
        .abs()
        .max()
    )

    mean_error = float(
        replay["replay_error"]
        .abs()
        .mean()
    )

    lines = [
        "=" * 72,
        "FILTER 15 MECHANICAL REPLAY AUDIT",
        "=" * 72,
        "",
        "Period",
        "------",
        (
            f"{replay['signal_date'].min().date()} ~ "
            f"{replay['signal_date'].max().date()}"
        ),
        "",
        "Observations",
        "------------",
        f"{len(replay):,}",
        "",
        "Replay reconciliation",
        "---------------------",
        (
            f"Exact-match days       : "
            f"{exact_match_count:,} / {len(replay):,}"
        ),
        (
            f"Exact-match share      : "
            f"{exact_match.mean():.2%}"
        ),
        (
            f"Maximum absolute error : "
            f"{max_error:.10f}%p"
        ),
        (
            f"Mean absolute error    : "
            f"{mean_error:.10f}%p"
        ),
        "",
        "Mechanical brake attribution",
        "--------------------------------",
    ]

    for _, row in summary.iterrows():
        lines.append(
            f"{row['family']:12s} | "
            f"share={row['mechanical_brake_share']:8.2%} | "
            f"avg={row['average_daily_reduction']:7.2f}%p | "
            f"days={int(row['binding_days']):4d} | "
            f"frequency={row['binding_day_share']:7.2%}"
        )

    lines.extend([
        "",
        "Input mappings",
        "--------------",
    ])

    for key, value in mappings.items():
        lines.append(
            f"{key:18s}: {value}"
        )

    lines.extend([
        "",
        "Verdict",
        "-------",
    ])

    if max_error <= 1e-9:
        lines.extend([
            "REPLAY PASS.",
            (
                "The independent replay matches the stored "
                "Filter 15 exposure on every date."
            ),
            (
                "Mechanical attribution can be treated as "
                "exact code-path evidence."
            ),
        ])

    elif max_error <= 1.0:
        lines.extend([
            "REPLAY NEAR-MATCH, NOT YET PASS.",
            (
                "The logic is substantially reproduced, but "
                "one or more saved input mappings differ from "
                "the original market_data inputs."
            ),
            (
                "Do not use the brake shares as final evidence "
                "until reconciliation reaches zero."
            ),
        ])

    else:
        lines.extend([
            "REPLAY FAIL.",
            (
                "The independent replay does not yet reproduce "
                "the production Filter 15 result."
            ),
            (
                "Review the largest-error dates and the input "
                "column mappings. The production engine remains "
                "untouched."
            ),
        ])

    lines.extend([
        "",
        "Original strategy code was not modified.",
        "=" * 72,
    ])

    return "\n".join(lines)


# ============================================================
# Main
# ============================================================

def main() -> None:
    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df, mappings = load_data()

    replay_rows = []

    for _, row in df.iterrows():
        replay_result = replay_one_row(row)

        replay_rows.append({
            "signal_date": row["signal_date"],
            **replay_result,
            "input_vix": row["_replay_vix"],
            "input_vix_pct": row["_replay_vix_pct"],
            "input_pos_z": row["_replay_pos_z"],
            "input_pos_slope": row[
                "_replay_pos_slope"
            ],
            "input_gamma": row["_replay_gamma"],
            "input_cta": row["_replay_cta"],
            "input_hy_level": row[
                "_replay_hy_level"
            ],
            "input_hy_pct": row["_replay_hy_pct"],
            "input_macro_narrative": row[
                "_replay_macro_narrative"
            ],
            "input_vix_z": row["_replay_vix_z"],
        })

    replay = pd.DataFrame(
        replay_rows
    )

    replay["absolute_replay_error"] = (
        replay["replay_error"].abs()
    )

    replay = replay.sort_values(
        "signal_date"
    ).reset_index(drop=True)

    summary = build_summary(
        replay
    )

    text_summary = make_text_summary(
        replay,
        summary,
        mappings,
    )

    replay.to_csv(
        DAILY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        SUMMARY_CSV_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    SUMMARY_TXT_OUT.write_text(
        text_summary,
        encoding="utf-8",
    )

    print(text_summary)

    print()
    print("Largest replay errors")
    print("---------------------")

    print(
        replay.nlargest(
            20,
            "absolute_replay_error",
        )[
            [
                "signal_date",
                "risk_budget_13",
                "existing_exposure_15",
                "replay_exposure_15",
                "replay_error",
                "input_vix",
                "input_vix_pct",
                "input_pos_z",
                "input_gamma",
                "input_cta",
                "input_hy_level",
                "input_hy_pct",
                "replay_status",
            ]
        ].to_string(index=False)
    )

    print()
    print("Saved outputs")
    print("-------------")
    print(DAILY_OUT)
    print(SUMMARY_CSV_OUT)
    print(SUMMARY_TXT_OUT)


if __name__ == "__main__":
    main()