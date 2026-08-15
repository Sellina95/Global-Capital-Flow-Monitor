from __future__ import annotations

"""
FILTER15 CORRECTED DAILY-BASELINE ROBUSTNESS AUDIT

This audit validates the corrected production-economics research contract:

    DAILY Filter15 pre-deadman baseline
        -> candidate False: 0% RE-BRAKE
        -> first True:      25%
        -> second True:     50%
        -> third True:      100% / RECOVERY COMPLETE
        -> thereafter:      100% of daily baseline

Important
---------
- Reads corrected canonical artifacts only.
- Does NOT modify Production.
- Does NOT introduce a new indicator or threshold.
- Does NOT optimize 25/50/100.
- Does NOT forward-fill missing market dates.
- Treats episode 1 (TIMING_RISK / 2008) separately so one crisis cannot
  dominate the conclusion.
- Separates recovery-completed and incomplete episodes.
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "data" / "backtest" / "results"

DAILY_PATH = R / "filter15_staged_restoration_corrected_canonical_daily.csv"
EP_PATH = R / "filter15_staged_restoration_corrected_canonical_episodes.csv"

OUT_EP = R / "filter15_corrected_robustness_episode.csv"
OUT_ERA = R / "filter15_corrected_robustness_era.csv"
OUT_LOO = R / "filter15_corrected_robustness_leave_one_out.csv"
OUT_STATE = R / "filter15_corrected_robustness_completion_state.csv"
OUT_SUM = R / "filter15_corrected_robustness_summary.csv"
OUT_TXT = R / "filter15_corrected_robustness_audit.txt"

TOL = 1e-12


def require(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def pct(x: float) -> str:
    if pd.isna(x):
        return "N/A"
    return f"{100.0 * x:.3f}%"


def era_from_date(x) -> str:
    y = pd.Timestamp(x).year
    if y <= 2010:
        return "2008-2010"
    if y <= 2013:
        return "2011-2013"
    if y <= 2016:
        return "2014-2016"
    if y <= 2019:
        return "2017-2019"
    if y <= 2021:
        return "2020-2021"
    if y <= 2023:
        return "2022-2023"
    return "2024+"


def recompute_episode_metrics(g: pd.DataFrame) -> tuple[float, float]:
    r = pd.to_numeric(g["corrected_return"], errors="coerce").fillna(0.0)
    eq = (1.0 + r).cumprod()
    dd = eq / eq.cummax() - 1.0
    return float(eq.iloc[-1] - 1.0), float(dd.min())


def main() -> None:
    if not DAILY_PATH.exists():
        raise FileNotFoundError(f"Missing: {DAILY_PATH}")
    if not EP_PATH.exists():
        raise FileNotFoundError(f"Missing: {EP_PATH}")

    daily = pd.read_csv(DAILY_PATH)
    ep = pd.read_csv(EP_PATH)

    require(
        daily,
        [
            "episode_id",
            "diagnosis",
            "signal_date",
            "corrected_state",
            "corrected_multiplier",
            "corrected_exposure",
            "corrected_return",
            "daily_filter15_baseline",
        ],
        "corrected daily",
    )
    require(
        ep,
        [
            "episode_id",
            "start_signal_date",
            "end_signal_date",
            "rows",
            "recovery_completed",
            "total_return",
            "mdd",
            "avg_exposure",
            "invested_days",
            "full_days",
            "rebrake_days",
            "stage1_days",
            "stage2_days",
            "completion_count",
        ],
        "corrected episodes",
    )

    daily["signal_date"] = pd.to_datetime(
        daily["signal_date"], errors="coerce"
    )
    ep["start_signal_date"] = pd.to_datetime(
        ep["start_signal_date"], errors="coerce"
    )
    ep["end_signal_date"] = pd.to_datetime(
        ep["end_signal_date"], errors="coerce"
    )

    # ------------------------------------------------------------
    # 1) Reconciliation: daily -> episode artifact
    # ------------------------------------------------------------
    rec_rows = []
    for eid, g in daily.groupby("episode_id", sort=True):
        ret, mdd = recompute_episode_metrics(
            g.sort_values("signal_date")
        )
        rec_rows.append(
            {
                "episode_id": eid,
                "recomputed_total_return": ret,
                "recomputed_mdd": mdd,
            }
        )
    rec = pd.DataFrame(rec_rows)

    ep = ep.merge(rec, on="episode_id", how="left", validate="one_to_one")
    ep["return_reconciliation_error"] = (
        ep["total_return"] - ep["recomputed_total_return"]
    ).abs()
    ep["mdd_reconciliation_error"] = (
        ep["mdd"] - ep["recomputed_mdd"]
    ).abs()

    max_ret_rec_err = float(ep["return_reconciliation_error"].max())
    max_mdd_rec_err = float(ep["mdd_reconciliation_error"].max())

    ep["diagnosis"] = ep["episode_id"].map(
        daily.groupby("episode_id")["diagnosis"].first()
    )
    ep["era"] = ep["start_signal_date"].map(era_from_date)

    # ------------------------------------------------------------
    # 2) Basic robustness / concentration
    # ------------------------------------------------------------
    n = len(ep)
    total_sum = float(ep["total_return"].sum())
    positive = int((ep["total_return"] > 0).sum())
    negative = int((ep["total_return"] < 0).sum())
    flat = int((ep["total_return"].abs() <= TOL).sum())

    completed = ep[ep["recovery_completed"].astype(bool)].copy()
    incomplete = ep[~ep["recovery_completed"].astype(bool)].copy()

    worst_idx = ep["mdd"].idxmin()
    worst_eid = ep.loc[worst_idx, "episode_id"]
    worst_mdd = float(ep.loc[worst_idx, "mdd"])
    worst_return = float(ep.loc[worst_idx, "total_return"])

    # episode 1 / 2008 exclusion
    ex2008 = ep[ep["episode_id"] != 1].copy()
    ex2008_total = float(ex2008["total_return"].sum())
    ex2008_avg = float(ex2008["total_return"].mean())
    ex2008_worst_mdd = float(ex2008["mdd"].min())

    # Return contribution concentration.
    abs_ret_sum = float(ep["total_return"].abs().sum())
    largest_abs_contribution = (
        float(ep["total_return"].abs().max() / abs_ret_sum)
        if abs_ret_sum > TOL
        else np.nan
    )

    # ------------------------------------------------------------
    # 3) Leave-One-Episode-Out
    #    Question: does aggregate direction remain positive?
    # ------------------------------------------------------------
    loo_rows = []
    for _, row in ep.iterrows():
        sub = ep[ep["episode_id"] != row["episode_id"]]
        loo_total = float(sub["total_return"].sum())
        loo_avg = float(sub["total_return"].mean())
        loo_rows.append(
            {
                "excluded_episode_id": row["episode_id"],
                "excluded_diagnosis": row["diagnosis"],
                "excluded_return": row["total_return"],
                "remaining_episodes": len(sub),
                "remaining_total_episode_return": loo_total,
                "remaining_avg_episode_return": loo_avg,
                "positive_direction_survives": loo_total > 0,
            }
        )

    loo = pd.DataFrame(loo_rows)
    loo_positive_rate = float(
        loo["positive_direction_survives"].mean()
    )
    loo_min_total = float(
        loo["remaining_total_episode_return"].min()
    )

    # ------------------------------------------------------------
    # 4) Era robustness
    # ------------------------------------------------------------
    era_rows = []
    for era, g in ep.groupby("era", sort=True):
        era_rows.append(
            {
                "era": era,
                "episodes": len(g),
                "completed_episodes": int(
                    g["recovery_completed"].astype(bool).sum()
                ),
                "positive_episodes": int((g["total_return"] > 0).sum()),
                "negative_episodes": int((g["total_return"] < 0).sum()),
                "total_episode_return": float(g["total_return"].sum()),
                "avg_episode_return": float(g["total_return"].mean()),
                "median_episode_return": float(
                    g["total_return"].median()
                ),
                "worst_episode_return": float(
                    g["total_return"].min()
                ),
                "worst_mdd": float(g["mdd"].min()),
                "avg_exposure": float(g["avg_exposure"].mean()),
            }
        )
    era_df = pd.DataFrame(era_rows)

    # ------------------------------------------------------------
    # 5) Completion-state robustness
    # ------------------------------------------------------------
    state_rows = []
    for label, g in [
        ("RECOVERY_COMPLETED", completed),
        ("RECOVERY_INCOMPLETE", incomplete),
    ]:
        if g.empty:
            continue
        state_rows.append(
            {
                "state_group": label,
                "episodes": len(g),
                "positive_episodes": int((g["total_return"] > 0).sum()),
                "negative_episodes": int((g["total_return"] < 0).sum()),
                "total_episode_return": float(g["total_return"].sum()),
                "avg_episode_return": float(g["total_return"].mean()),
                "median_episode_return": float(
                    g["total_return"].median()
                ),
                "worst_episode_return": float(
                    g["total_return"].min()
                ),
                "avg_mdd": float(g["mdd"].mean()),
                "worst_mdd": float(g["mdd"].min()),
                "avg_exposure": float(g["avg_exposure"].mean()),
                "avg_rebrake_days": float(g["rebrake_days"].mean()),
            }
        )
    state_df = pd.DataFrame(state_rows)

    # ------------------------------------------------------------
    # 6) Tail attribution
    # ------------------------------------------------------------
    worst10 = ep.nsmallest(
        min(10, len(ep)), "mdd"
    )[
        [
            "episode_id",
            "start_signal_date",
            "diagnosis",
            "recovery_completed",
            "total_return",
            "mdd",
            "avg_exposure",
            "full_days",
            "rebrake_days",
            "stage1_days",
            "stage2_days",
        ]
    ].copy()

    # ------------------------------------------------------------
    # 7) Gate logic
    #
    # We do NOT claim causal improvement versus old fixed-exposure research.
    # This gate asks whether the corrected contract is internally robust
    # enough to continue to actual-source parity.
    # ------------------------------------------------------------
    reconciliation_pass = (
        max_ret_rec_err <= 1e-10 and max_mdd_rec_err <= 1e-10
    )
    aggregate_positive = total_sum > 0
    ex2008_positive = ex2008_total > 0
    loo_pass = loo_positive_rate >= 0.95 and loo_min_total > 0

    # Require the result not to be purely a single-era phenomenon.
    nonempty_eras = len(era_df)
    positive_eras = int(
        (era_df["total_episode_return"] > 0).sum()
    )
    era_direction_rate = (
        positive_eras / nonempty_eras if nonempty_eras else np.nan
    )
    era_pass = (
        nonempty_eras > 0
        and positive_eras >= max(1, int(np.ceil(nonempty_eras / 2)))
    )

    # Concentration is a warning rather than a hard optimization rule.
    concentration_warning = (
        pd.notna(largest_abs_contribution)
        and largest_abs_contribution > 0.50
    )

    # Worst MDD -7.5% must be explicitly carried forward.
    tail_warning = worst_mdd <= -0.05

    core_pass = (
        reconciliation_pass
        and aggregate_positive
        and ex2008_positive
        and loo_pass
        and era_pass
    )

    if core_pass and (tail_warning or concentration_warning):
        decision = "PASS_WITH_TAIL_WARNING"
        next_gate = (
            "ACTUAL-SOURCE EXACT PARITY + WORST-EPISODE TRACE"
        )
    elif core_pass:
        decision = "PASS"
        next_gate = "ACTUAL-SOURCE EXACT PARITY"
    else:
        decision = "FAIL"
        next_gate = (
            "STOP PRODUCTION PROMOTION; DIAGNOSE CORRECTED CONTRACT"
        )

    summary = pd.DataFrame(
        [
            {
                "status": decision,
                "episodes": n,
                "completed_episodes": len(completed),
                "incomplete_episodes": len(incomplete),
                "positive_episodes": positive,
                "negative_episodes": negative,
                "flat_episodes": flat,
                "total_episode_return": total_sum,
                "avg_episode_return": float(
                    ep["total_return"].mean()
                ),
                "median_episode_return": float(
                    ep["total_return"].median()
                ),
                "worst_episode_return": float(
                    ep["total_return"].min()
                ),
                "worst_mdd": worst_mdd,
                "worst_mdd_episode_id": worst_eid,
                "excluding_2008_total_return": ex2008_total,
                "excluding_2008_avg_return": ex2008_avg,
                "excluding_2008_worst_mdd": ex2008_worst_mdd,
                "loo_positive_pass_rate": loo_positive_rate,
                "loo_min_remaining_total_return": loo_min_total,
                "positive_era_rate": era_direction_rate,
                "largest_abs_return_contribution_share": (
                    largest_abs_contribution
                ),
                "tail_warning": tail_warning,
                "concentration_warning": concentration_warning,
                "max_return_reconciliation_error": max_ret_rec_err,
                "max_mdd_reconciliation_error": max_mdd_rec_err,
                "next_gate": next_gate,
            }
        ]
    )

    ep.to_csv(OUT_EP, index=False)
    era_df.to_csv(OUT_ERA, index=False)
    loo.to_csv(OUT_LOO, index=False)
    state_df.to_csv(OUT_STATE, index=False)
    summary.to_csv(OUT_SUM, index=False)

    lines = [
        "=" * 78,
        "FILTER15 CORRECTED DAILY-BASELINE ROBUSTNESS AUDIT",
        "=" * 78,
        "",
        "Production Modified         : NO",
        "New Indicator               : NO",
        "New Threshold               : NO",
        "Parameter Optimization      : NO",
        "Forward Fill                : NO",
        "Contract                    : DAILY BASELINE x 25/50/100",
        "",
        "===== RECONCILIATION =====",
        f"Max Return Error            : {max_ret_rec_err:.12f}",
        f"Max MDD Error               : {max_mdd_rec_err:.12f}",
        f"Reconciliation              : {'PASS' if reconciliation_pass else 'FAIL'}",
        "",
        "===== OVERALL =====",
        f"Episodes                    : {n}",
        f"Recovery Completed          : {len(completed)}",
        f"Recovery Incomplete         : {len(incomplete)}",
        f"Positive / Negative / Flat  : {positive} / {negative} / {flat}",
        f"Total Episode Return        : {pct(total_sum)}",
        f"Average Episode Return      : {pct(float(ep['total_return'].mean()))}",
        f"Median Episode Return       : {pct(float(ep['total_return'].median()))}",
        f"Worst Episode Return        : {pct(float(ep['total_return'].min()))}",
        f"Worst MDD                   : {pct(worst_mdd)}",
        f"Worst MDD Episode           : {worst_eid}",
        "",
        "===== EXCLUDING 2008 / EPISODE 1 =====",
        f"Episodes                    : {len(ex2008)}",
        f"Total Episode Return        : {pct(ex2008_total)}",
        f"Average Episode Return      : {pct(ex2008_avg)}",
        f"Worst MDD                   : {pct(ex2008_worst_mdd)}",
        f"Direction Positive          : {ex2008_positive}",
        "",
        "===== LEAVE-ONE-EPISODE-OUT =====",
        f"Positive Conclusion Survives: {loo_positive_rate:.2%}",
        f"Worst Remaining Total       : {pct(loo_min_total)}",
        f"LOO Gate                    : {'PASS' if loo_pass else 'FAIL'}",
        "",
        "===== ERA ROBUSTNESS =====",
        era_df.to_string(index=False),
        "",
        f"Positive Era Rate           : {era_direction_rate:.2%}",
        f"Era Gate                    : {'PASS' if era_pass else 'FAIL'}",
        "",
        "===== COMPLETION STATE =====",
        state_df.to_string(index=False),
        "",
        "===== WORST TAIL EPISODES =====",
        worst10.to_string(index=False),
        "",
        "===== CONCENTRATION =====",
        (
            "Largest Absolute Return Contribution: "
            f"{largest_abs_contribution:.2%}"
            if pd.notna(largest_abs_contribution)
            else "Largest Absolute Return Contribution: N/A"
        ),
        f"Concentration Warning       : {concentration_warning}",
        f"Tail Warning (MDD <= -5%)   : {tail_warning}",
        "",
        "===== INSTITUTIONAL GATE DECISION =====",
        f"STATUS                      : {decision}",
        "",
    ]

    if decision == "PASS_WITH_TAIL_WARNING":
        lines += [
            "해석:",
            "- Corrected daily-baseline contract의 aggregate 방향은 유지된다.",
            "- 2008 episode를 제거해도 방향이 유지되고 LOO도 통과한다.",
            "- 다만 worst-tail이 충분히 크므로 Production 승격 전에",
            "  해당 episode의 state/exposure path를 별도로 trace해야 한다.",
            "- 여기서 25/50/100 숫자를 다시 최적화하지 않는다.",
            "",
            "PRODUCTION DECISION: NO CHANGE",
            f"NEXT GATE: {next_gate}",
        ]
    elif decision == "PASS":
        lines += [
            "해석:",
            "- Corrected daily-baseline contract가 robustness gate를 통과했다.",
            "- 아직 Production 승인은 아니다.",
            "- 다음은 실제 patched source와 canonical의 exact parity다.",
            "",
            "PRODUCTION DECISION: NO CHANGE",
            f"NEXT GATE: {next_gate}",
        ]
    else:
        lines += [
            "해석:",
            "- Corrected contract가 robustness gate를 통과하지 못했다.",
            "- Production patch 승격을 중단한다.",
            "- 수익률 기준 parameter tuning으로 문제를 숨기지 않는다.",
            "",
            "PRODUCTION DECISION: STOP",
            f"NEXT GATE: {next_gate}",
        ]

    txt = "\n".join(lines)
    OUT_TXT.write_text(txt, encoding="utf-8")

    print(txt)
    print()
    print(f"Saved: {OUT_EP}")
    print(f"Saved: {OUT_ERA}")
    print(f"Saved: {OUT_LOO}")
    print(f"Saved: {OUT_STATE}")
    print(f"Saved: {OUT_SUM}")
    print(f"Saved: {OUT_TXT}")

    if decision == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
