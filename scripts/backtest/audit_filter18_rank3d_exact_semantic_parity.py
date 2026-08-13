from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"

RESEARCH_PATH = (
    RESULTS
    / "filter18_rank_persistence_counterfactual_detail.csv"
)

PIPELINE_PATH = (
    RESULTS
    / "filter13_candidate_current_pipeline_detail.csv"
)

DETAIL_PATH = (
    RESULTS
    / "filter18_rank3d_exact_semantic_parity_detail.csv"
)

SUMMARY_PATH = (
    RESULTS
    / "filter18_rank3d_exact_semantic_parity_summary.txt"
)


CONFIRM_DAYS = 3
HOLD_THRESHOLD = 2.0
REBALANCE_THRESHOLD = 5.0
TOL = 1e-9


def normalize_text(value) -> str:
    """CSV blank/NaN and runtime empty-string canonicalization."""
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value)


def safe_float(value, default=0.0):
    try:
        x = float(value)
        if pd.isna(x):
            return default
        return x
    except Exception:
        return default


def apply_threshold(
    target: dict[str, float],
    previous: dict[str, float],
    sectors: list[str],
) -> tuple[dict[str, float], dict[str, str]]:
    """
    Production apply_rebalance_threshold semantics:

    abs diff < 2%p  -> HOLD previous
    abs diff < 5%p  -> SMALL ADJUST target
    otherwise       -> REBALANCE target
    """

    executed = {}
    actions = {}

    # Exact research / Production semantics:
    # iterate only sectors present in today's target dictionary.
    for sector, target_value in target.items():

        target_w = safe_float(
            target_value
        )

        # Production's first appearance semantics:
        # no previous value => target accepted.
        if sector not in previous:

            executed[sector] = round(
                target_w,
                1,
            )

            actions[sector] = "NEW"
            continue

        previous_w = safe_float(
            previous.get(sector, 0.0)
        )

        diff = target_w - previous_w
        abs_diff = abs(diff)

        if abs_diff < HOLD_THRESHOLD:

            executed[sector] = round(
                previous_w,
                1,
            )

            actions[sector] = "HOLD"

        elif abs_diff < REBALANCE_THRESHOLD:

            executed[sector] = round(
                target_w,
                1,
            )

            actions[sector] = "SMALL ADJUST"

        else:

            executed[sector] = round(
                target_w,
                1,
            )

            actions[sector] = "REBALANCE"

    return executed, actions


def main():

    research = pd.read_csv(
        RESEARCH_PATH
    )

    pipeline = pd.read_csv(
        PIPELINE_PATH
    )

    research = research[
        research["scenario"].eq(
            "PERSIST_3D"
        )
    ].copy()

    baseline = pipeline[
        pipeline["scenario"].eq(
            "BASELINE_CURRENT"
        )
    ].copy()

    research["signal_date"] = pd.to_datetime(
        research["signal_date"],
        errors="coerce",
    )

    baseline["signal_date"] = pd.to_datetime(
        baseline["signal_date"],
        errors="coerce",
    )

    research = (
        research
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    baseline = (
        baseline
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Hard date contract
    # --------------------------------------------------------

    if len(research) != 4645:
        raise RuntimeError(
            f"Research row count != 4645: {len(research)}"
        )

    if len(baseline) != 4645:
        raise RuntimeError(
            f"Baseline row count != 4645: {len(baseline)}"
        )

    if not research["signal_date"].equals(
        baseline["signal_date"]
    ):
        raise RuntimeError(
            "Research and baseline dates differ."
        )

    # --------------------------------------------------------
    # Sector universe
    # --------------------------------------------------------

    sectors = sorted(
        c.replace("weight__", "", 1)
        for c in baseline.columns
        if c.startswith("weight__")
    )

    research_sectors = sorted(
        c.replace("executed__", "", 1)
        for c in research.columns
        if c.startswith("executed__")
    )

    if sectors != research_sectors:
        raise RuntimeError(
            "Baseline and research sector universe differ."
        )

    print()
    print("# FILTER18 RANK3D EXACT SEMANTIC PARITY")
    print()
    print(f"Rows    : {len(research):,}")
    print(f"Sectors : {len(sectors)}")

    # --------------------------------------------------------
    # State
    # --------------------------------------------------------

    accepted_rank = ""
    accepted_target = {}

    pending_rank = ""
    pending_count = 0

    previous_executed = {}

    rows = []

    for i in range(len(research)):

        rr = research.iloc[i]
        br = baseline.iloc[i]

        signal_date = rr["signal_date"]

        current_rank = str(
            rr.get(
                "current_rank",
                "",
            )
            or ""
        )

        deleveraging = bool(
            rr.get(
                "deleveraging_required",
                False,
            )
        )

        # Production raw target before persistence.
        raw_target = {}

        # Exact Production / research contract:
        # absent/NaN sector is NOT represented as zero target.
        # It must be omitted from the target dictionary entirely.
        for sector in sectors:

            raw_value = br.get(
                f"weight__{sector}",
                np.nan,
            )

            if pd.isna(raw_value):
                continue

            raw_target[sector] = float(
                raw_value
            )

        # ====================================================
        # Exact patched Production Rank3D semantics
        # ====================================================

        if deleveraging:

            was_uninitialized = not accepted_rank

            accepted_rank = current_rank
            accepted_target = dict(raw_target)

            pending_rank = ""
            pending_count = 0

            target_for_execution = dict(
                raw_target
            )

            action = (
                "INITIAL_ACCEPT"
                if was_uninitialized
                else "FORCED_DELEVERAGE_ACCEPT"
            )

        elif not accepted_rank:

            accepted_rank = current_rank
            accepted_target = dict(raw_target)

            pending_rank = ""
            pending_count = 0

            target_for_execution = dict(
                raw_target
            )

            action = "INITIAL_ACCEPT"

        elif current_rank == accepted_rank:

            accepted_target = dict(raw_target)

            pending_rank = ""
            pending_count = 0

            target_for_execution = dict(
                raw_target
            )

            action = "ACCEPTED_RANK_UPDATE"

        else:

            if pending_rank == current_rank:
                pending_count += 1

            else:
                pending_rank = current_rank
                pending_count = 1

            if (
                pending_rank == current_rank
                and pending_count >= CONFIRM_DAYS
            ):

                accepted_rank = current_rank
                accepted_target = dict(raw_target)

                pending_rank = ""
                pending_count = 0

                target_for_execution = dict(
                    raw_target
                )

                action = "RANK_CONFIRMED"

            else:

                target_for_execution = dict(
                    accepted_target
                )

                action = "RANK_CHANGE_SUPPRESSED"

        # ====================================================
        # Production safety:
        # deleveraging bypasses threshold completely.
        # ====================================================

        if deleveraging:

            executed = {
                sector: round(
                    safe_float(
                        target_for_execution.get(
                            sector,
                            0.0,
                        )
                    ),
                    1,
                )
                for sector in sectors
            }

        else:

            executed, _ = apply_threshold(
                target=target_for_execution,
                previous=previous_executed,
                sectors=sectors,
            )

        # ----------------------------------------------------
        # Research comparison
        # ----------------------------------------------------

        max_weight_error = 0.0
        sector_fail_count = 0

        row = {
            "signal_date":
                signal_date,

            "current_rank":
                current_rank,

            "replay_accepted_rank":
                accepted_rank,

            "research_accepted_rank":
                normalize_text(
                    rr.get(
                        "accepted_rank",
                        "",
                    )
                ),

            "replay_pending_rank":
                pending_rank,

            "research_pending_rank":
                normalize_text(
                    rr.get(
                        "pending_rank",
                        "",
                    )
                ),

            "replay_pending_count":
                pending_count,

            "research_pending_count":
                int(
                    safe_float(
                        rr.get(
                            "pending_count",
                            0,
                        )
                    )
                ),

            "replay_action":
                action,

            "research_action":
                normalize_text(
                    rr.get(
                        "persistence_action",
                        "",
                    )
                ),

            "deleveraging_required":
                deleveraging,
        }

        for sector in sectors:

            replay_w = safe_float(
                executed.get(
                    sector,
                    0.0,
                )
            )

            research_w = safe_float(
                rr.get(
                    f"executed__{sector}",
                    0.0,
                )
            )

            error = replay_w - research_w

            row[
                f"error__{sector}"
            ] = error

            max_weight_error = max(
                max_weight_error,
                abs(error),
            )

            if abs(error) > TOL:
                sector_fail_count += 1

        row["max_weight_error"] = (
            max_weight_error
        )

        row["sector_fail_count"] = (
            sector_fail_count
        )

        row["accepted_rank_match"] = (
            row["replay_accepted_rank"]
            == row["research_accepted_rank"]
        )

        row["pending_rank_match"] = (
            row["replay_pending_rank"]
            == row["research_pending_rank"]
        )

        row["pending_count_match"] = (
            row["replay_pending_count"]
            == row["research_pending_count"]
        )

        row["action_match"] = (
            row["replay_action"]
            == row["research_action"]
        )

        rows.append(row)

        previous_executed = dict(
            executed
        )

    detail = pd.DataFrame(rows)

    # ========================================================
    # Parity gates
    # ========================================================

    weight_fail_days = int(
        (
            detail[
                "max_weight_error"
            ]
            > TOL
        ).sum()
    )

    max_weight_error = float(
        detail[
            "max_weight_error"
        ].max()
    )

    accepted_rank_fail = int(
        (
            ~detail[
                "accepted_rank_match"
            ]
        ).sum()
    )

    pending_rank_fail = int(
        (
            ~detail[
                "pending_rank_match"
            ]
        ).sum()
    )

    pending_count_fail = int(
        (
            ~detail[
                "pending_count_match"
            ]
        ).sum()
    )

    action_fail = int(
        (
            ~detail[
                "action_match"
            ]
        ).sum()
    )

    total_fail = (
        weight_fail_days
        + accepted_rank_fail
        + pending_rank_fail
        + pending_count_fail
        + action_fail
    )

    status = (
        "PASS"
        if total_fail == 0
        else "FAIL"
    )

    lines = [
        "# FILTER18 RANK3D EXACT SEMANTIC PARITY",
        "",
        f"Rows                     : {len(detail):,}",
        f"Sector count             : {len(sectors)}",
        "",
        f"Executed-weight fail days: {weight_fail_days:,}",
        f"Max weight abs error     : {max_weight_error:.10f}",
        f"Accepted-rank fail days  : {accepted_rank_fail:,}",
        f"Pending-rank fail days   : {pending_rank_fail:,}",
        f"Pending-count fail days  : {pending_count_fail:,}",
        f"Action fail days         : {action_fail:,}",
        "",
        f"FINAL STATUS: {status}",
    ]

    if total_fail > 0:

        fail_mask = (
            (detail["max_weight_error"] > TOL)
            | (~detail["accepted_rank_match"])
            | (~detail["pending_rank_match"])
            | (~detail["pending_count_match"])
            | (~detail["action_match"])
        )

        lines += [
            "",
            "FIRST FAILURES",
            detail.loc[
                fail_mask,
                [
                    "signal_date",
                    "current_rank",
                    "replay_accepted_rank",
                    "research_accepted_rank",
                    "replay_pending_rank",
                    "research_pending_rank",
                    "replay_pending_count",
                    "research_pending_count",
                    "replay_action",
                    "research_action",
                    "deleveraging_required",
                    "max_weight_error",
                ],
            ]
            .head(20)
            .to_string(index=False),
        ]

    text = "\n".join(lines)

    detail.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    SUMMARY_PATH.write_text(
        text,
        encoding="utf-8",
    )

    print()
    print(text)

    print()
    print("Saved:")
    print(DETAIL_PATH)
    print(SUMMARY_PATH)

    if status != "PASS":
        raise RuntimeError(
            "Filter18 Rank3D semantic parity FAILED. "
            "Do NOT run Production."
        )


if __name__ == "__main__":
    main()
