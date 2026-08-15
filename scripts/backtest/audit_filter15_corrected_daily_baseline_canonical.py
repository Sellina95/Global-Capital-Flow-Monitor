from __future__ import annotations

"""
FILTER15 CORRECTED DAILY-BASELINE CANONICAL

Purpose
-------
Rebuild the staged re-risking research contract so it matches the actual
Filter15 production economics.

Corrected contract
------------------
1. Daily baseline exposure is the Filter15 exposure immediately BEFORE
   Hard Deadman override: attribution column `after_credit_change`.
2. Recovery candidate is NOT re-invented here. Reuse the already validated
   canonical RAMP_3 `candidate` signal.
3. State machine:
      DEADMAN / recovery pending
          candidate False -> 0% (RE_BRAKE)
          1st True        -> 25% of DAILY baseline
          2nd True        -> 50% of DAILY baseline
          3rd True        -> 100% of DAILY baseline, RECOVERY_COMPLETE
      after RECOVERY_COMPLETE:
          remain at 100% of DAILY baseline through the episode window.
          Do NOT restart 25/50/100 while the original deadman condition
          remains mechanically true.
4. Non-trading dates with no Filter15 attribution row are excluded.
   No forward-fill and no synthetic signal.
5. Existing research artifacts are never overwritten.

Production source is NOT modified by this script.
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "data" / "backtest" / "results"

OLD_CANONICAL = (
    R / "filter15_staged_restoration_parameter_sensitivity_canonical_daily.csv"
)
ATTR = R / "filter15_exposure_attribution_daily.csv"

OUT_DAILY = R / "filter15_staged_restoration_corrected_canonical_daily.csv"
OUT_EP = R / "filter15_staged_restoration_corrected_canonical_episodes.csv"
OUT_SUM = R / "filter15_staged_restoration_corrected_canonical_summary.csv"
OUT_TXT = R / "filter15_staged_restoration_corrected_canonical_audit.txt"

SOURCE_PATH = "RAMP_3"
TOL = 1e-10


def norm_date(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.normalize()


def as_bool(x) -> bool:
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if pd.isna(x):
        return False
    return str(x).strip().lower() in {"true", "1", "yes", "y"}


def require(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def episode_metrics(g: pd.DataFrame) -> dict:
    r = pd.to_numeric(g["corrected_return"], errors="coerce").fillna(0.0)
    eq = (1.0 + r).cumprod()
    peak = eq.cummax()
    dd = eq / peak - 1.0

    return {
        "total_return": float(eq.iloc[-1] - 1.0),
        "mdd": float(dd.min()),
        "avg_exposure": float(g["corrected_exposure"].mean()),
        "invested_days": int((g["corrected_exposure"] > TOL).sum()),
        "full_days": int(
            np.isclose(g["corrected_multiplier"], 1.0, atol=1e-12).sum()
        ),
        "rebrake_days": int(
            np.isclose(g["corrected_multiplier"], 0.0, atol=1e-12).sum()
        ),
        "stage1_days": int(
            np.isclose(g["corrected_multiplier"], 0.25, atol=1e-12).sum()
        ),
        "stage2_days": int(
            np.isclose(g["corrected_multiplier"], 0.50, atol=1e-12).sum()
        ),
        "completion_count": int(
            (g["corrected_state"] == "RECOVERY_COMPLETE").sum()
        ),
    }


def main() -> None:
    if not OLD_CANONICAL.exists():
        raise FileNotFoundError(f"Missing: {OLD_CANONICAL}")
    if not ATTR.exists():
        raise FileNotFoundError(f"Missing: {ATTR}")

    research = pd.read_csv(OLD_CANONICAL)
    attr = pd.read_csv(ATTR)

    require(
        research,
        [
            "episode_id",
            "signal_date",
            "path",
            "candidate",
            "spy_return_t1",
        ],
        "old canonical",
    )

    require(
        attr,
        [
            "signal_date",
            "after_credit_change",
            "hard_deadman",
            "actual_exposure_15",
        ],
        "Filter15 attribution",
    )

    # Use only the already validated canonical state path.
    research = research[
        research["path"].astype(str).str.upper().eq(SOURCE_PATH)
    ].copy()

    if research.empty:
        raise ValueError(f"No {SOURCE_PATH} rows in {OLD_CANONICAL.name}")

    research["signal_date"] = norm_date(research["signal_date"])
    attr["signal_date"] = norm_date(attr["signal_date"])

    # Persistent state transition may occur only once per episode/date.
    research = (
        research.sort_values(["episode_id", "signal_date"])
        .drop_duplicates(["episode_id", "signal_date"], keep="first")
        .copy()
    )

    attr = (
        attr.sort_values("signal_date")
        .drop_duplicates("signal_date", keep="last")
        .copy()
    )

    attr["daily_filter15_baseline"] = pd.to_numeric(
        attr["after_credit_change"], errors="coerce"
    )

    df = research.merge(
        attr[
            [
                "signal_date",
                "daily_filter15_baseline",
                "hard_deadman",
                "actual_exposure_15",
            ]
        ],
        on="signal_date",
        how="left",
        validate="many_to_one",
    )

    # Trading-calendar alignment: no ffill, no synthetic execution row.
    missing_exec = df["daily_filter15_baseline"].isna()
    skipped = df.loc[
        missing_exec, ["episode_id", "signal_date"]
    ].copy()

    if len(skipped):
        print(
            "[INFO][TRADING CALENDAR] "
            f"Skipping {len(skipped)} rows with no executable Filter15 row."
        )
        print(skipped.head(40).to_string(index=False))
        df = df.loc[~missing_exec].copy()

    if df.empty:
        raise ValueError("No executable rows remain after calendar alignment.")

    # Sanity: the pre-deadman baseline must be a valid exposure.
    bad_baseline = (
        ~np.isfinite(df["daily_filter15_baseline"])
        | (df["daily_filter15_baseline"] < -TOL)
        | (df["daily_filter15_baseline"] > 100.0 + TOL)
    )
    if bad_baseline.any():
        print(
            df.loc[
                bad_baseline,
                ["episode_id", "signal_date", "daily_filter15_baseline"],
            ].head(30).to_string(index=False)
        )
        raise ValueError("Invalid daily Filter15 pre-deadman baseline.")

    records: list[dict] = []

    for episode_id, g in df.groupby("episode_id", sort=True):
        g = g.sort_values("signal_date").copy()

        streak = 0
        completed = False

        for _, row in g.iterrows():
            candidate = as_bool(row["candidate"])
            baseline = float(row["daily_filter15_baseline"])

            if completed:
                mult = 1.0
                state = "POST_RECOVERY_NORMAL"

            elif candidate:
                streak += 1

                if streak == 1:
                    mult = 0.25
                    state = "RECOVERY_STAGE_1"

                elif streak == 2:
                    mult = 0.50
                    state = "RECOVERY_STAGE_2"

                else:
                    mult = 1.0
                    state = "RECOVERY_COMPLETE"
                    completed = True

            else:
                streak = 0
                mult = 0.0
                state = "RECOVERY_REBRAKE"

            exposure = baseline * mult
            spy_t1 = pd.to_numeric(
                pd.Series([row["spy_return_t1"]]), errors="coerce"
            ).iloc[0]
            if pd.isna(spy_t1):
                spy_t1 = 0.0

            rec = row.to_dict()
            rec.update(
                {
                    "source_path": SOURCE_PATH,
                    "daily_filter15_baseline": baseline,
                    "corrected_candidate": candidate,
                    "corrected_streak": int(streak),
                    "corrected_completed": bool(completed),
                    "corrected_state": state,
                    "corrected_multiplier": float(mult),
                    "corrected_exposure": float(exposure),
                    "corrected_return": float(exposure / 100.0 * spy_t1),
                }
            )
            records.append(rec)

    daily = pd.DataFrame(records)

    # Contract checks.
    expected = (
        daily["daily_filter15_baseline"]
        * daily["corrected_multiplier"]
    )
    exposure_error = (
        daily["corrected_exposure"] - expected
    ).abs()

    max_exposure_formula_error = float(exposure_error.max())

    # Once completed, no later row in that episode may restart stage 1/2/rebrake.
    completion_violations = []
    for eid, g in daily.groupby("episode_id", sort=True):
        g = g.sort_values("signal_date")
        complete_pos = np.flatnonzero(
            g["corrected_state"].eq("RECOVERY_COMPLETE").to_numpy()
        )
        if len(complete_pos):
            tail = g.iloc[complete_pos[0] + 1 :]
            bad = tail[
                ~tail["corrected_state"].eq("POST_RECOVERY_NORMAL")
            ]
            if not bad.empty:
                completion_violations.append(bad)

    completion_violation_rows = (
        pd.concat(completion_violations, ignore_index=True)
        if completion_violations
        else pd.DataFrame()
    )

    ep_rows = []
    for eid, g in daily.groupby("episode_id", sort=True):
        m = episode_metrics(g)
        ep_rows.append(
            {
                "episode_id": eid,
                "start_signal_date": g["signal_date"].iloc[0],
                "end_signal_date": g["signal_date"].iloc[-1],
                "rows": len(g),
                "recovery_completed": bool(
                    g["corrected_completed"].any()
                ),
                **m,
            }
        )

    episodes = pd.DataFrame(ep_rows)

    summary = pd.DataFrame(
        [
            {
                "contract": "DAILY_BASELINE_25_50_100_COMPLETE",
                "episodes": len(episodes),
                "completed_episodes": int(
                    episodes["recovery_completed"].sum()
                ),
                "positive_episodes": int(
                    (episodes["total_return"] > 0).sum()
                ),
                "negative_episodes": int(
                    (episodes["total_return"] < 0).sum()
                ),
                "total_episode_return": float(
                    episodes["total_return"].sum()
                ),
                "avg_episode_return": float(
                    episodes["total_return"].mean()
                ),
                "median_episode_return": float(
                    episodes["total_return"].median()
                ),
                "avg_mdd": float(episodes["mdd"].mean()),
                "worst_mdd": float(episodes["mdd"].min()),
                "avg_exposure": float(
                    episodes["avg_exposure"].mean()
                ),
                "max_exposure_formula_error": (
                    max_exposure_formula_error
                ),
                "completion_violation_rows": len(
                    completion_violation_rows
                ),
                "calendar_rows_skipped": len(skipped),
            }
        ]
    )

    contract_pass = (
        max_exposure_formula_error <= 1e-12
        and completion_violation_rows.empty
        and len(episodes) == df["episode_id"].nunique()
    )

    daily.to_csv(OUT_DAILY, index=False)
    episodes.to_csv(OUT_EP, index=False)
    summary.to_csv(OUT_SUM, index=False)

    lines = [
        "=" * 78,
        "FILTER15 CORRECTED DAILY-BASELINE CANONICAL AUDIT",
        "=" * 78,
        "",
        f"Old Canonical Source      : {OLD_CANONICAL.name}",
        f"Attribution Source        : {ATTR.name}",
        "Daily Baseline Column    : after_credit_change",
        "Recovery Candidate       : reused canonical candidate",
        "Recovery Path            : 25% -> 50% -> 100%",
        "Re-brake                 : candidate break before completion -> 0%",
        "Completion Semantics     : once complete, remain normal",
        "Forward Fill             : NO",
        "Future Data Added        : NO",
        "Production Modified      : NO",
        "",
        "===== CONTRACT CHECK =====",
        f"Episodes                  : {len(episodes)}",
        f"Completed Episodes        : {int(episodes['recovery_completed'].sum())}",
        f"Calendar Rows Skipped     : {len(skipped)}",
        f"Exposure Formula Max Error: {max_exposure_formula_error:.12f}",
        f"Completion Violations     : {len(completion_violation_rows)}",
        f"CONTRACT                  : {'PASS' if contract_pass else 'FAIL'}",
        "",
        "===== CORRECTED RESEARCH SUMMARY =====",
        summary.to_string(index=False),
        "",
    ]

    if contract_pass:
        lines += [
            "RESULT: CORRECTED CANONICAL BUILT",
            "",
            "IMPORTANT:",
            "- This does NOT approve Production.",
            "- Old fixed-release-exposure research economics are superseded",
            "  for the production-parity decision.",
            "- Robustness must be rerun on this corrected daily-baseline contract.",
            "",
            "PRODUCTION DECISION: NO CHANGE",
            "NEXT GATE: CORRECTED ROBUSTNESS + ACTUAL-SOURCE PARITY",
        ]
    else:
        lines += [
            "RESULT: CONTRACT FAIL",
            "Do not interpret returns and do not modify Production.",
        ]

    txt = "\n".join(lines)
    OUT_TXT.write_text(txt, encoding="utf-8")

    print(txt)
    print()
    print(f"Saved: {OUT_DAILY}")
    print(f"Saved: {OUT_EP}")
    print(f"Saved: {OUT_SUM}")
    print(f"Saved: {OUT_TXT}")

    if not contract_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
