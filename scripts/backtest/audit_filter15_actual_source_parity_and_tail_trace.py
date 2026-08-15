from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

for p in (ROOT, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import filters.strategist_filters as sf

from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.filter13_execution_chain import prepare_filter13_execution_state
from scripts.backtest.institutional_backtest import (
    disable_live_side_effects,
    neutralize_all_side_effects,
)

DATA_DIR = ROOT / "data" / "backtest"
RESULTS_DIR = DATA_DIR / "results"

PANEL_PATH = DATA_DIR / "master_panel.csv"
CANONICAL_PATH = RESULTS_DIR / "filter15_staged_restoration_corrected_canonical_daily.csv"

OUT_DAILY = RESULTS_DIR / "filter15_actual_source_parity_daily.csv"
OUT_SUMMARY = RESULTS_DIR / "filter15_actual_source_parity_summary.csv"
OUT_TAIL = RESULTS_DIR / "filter15_actual_source_episode1_tail_trace.csv"
OUT_AUDIT = RESULTS_DIR / "filter15_actual_source_parity_and_tail_trace_audit.txt"

TOL = 1e-10


def _num(x: Any) -> float | None:
    if x is None:
        return None
    try:
        v = float(x)
    except Exception:
        return None
    return v if np.isfinite(v) else None


def _dt_series(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce").dt.normalize()


def _safe_bool(x: Any) -> bool:
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if x is None:
        return False
    if isinstance(x, str):
        return x.strip().lower() in {"true", "1", "yes", "y"}
    try:
        if pd.isna(x):
            return False
    except Exception:
        pass
    return bool(x)


def _mdd(returns: pd.Series) -> float:
    r = pd.to_numeric(returns, errors="coerce").fillna(0.0)
    wealth = (1.0 + r).cumprod()
    dd = wealth / wealth.cummax() - 1.0
    return float(dd.min()) if len(dd) else 0.0


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not PANEL_PATH.exists():
        raise FileNotFoundError(PANEL_PATH)
    if not CANONICAL_PATH.exists():
        raise FileNotFoundError(CANONICAL_PATH)

    panel = pd.read_csv(PANEL_PATH)
    canonical = pd.read_csv(CANONICAL_PATH)

    for col in ("signal_date", "execution_date"):
        if col in panel.columns:
            panel[col] = _dt_series(panel[col])
        if col in canonical.columns:
            canonical[col] = _dt_series(canonical[col])

    required = {
        "episode_id",
        "signal_date",
        "corrected_exposure",
        "corrected_multiplier",
        "corrected_state",
        "corrected_candidate",
        "corrected_streak",
        "corrected_completed",
        "daily_filter15_baseline",
        "spy_return_t1",
        "corrected_return",
    }
    missing = sorted(required - set(canonical.columns))
    if missing:
        raise ValueError(f"Corrected canonical missing columns: {missing}")

    canonical = canonical.sort_values(
        ["signal_date", "episode_id"]
    ).reset_index(drop=True)

    return panel, canonical


def main() -> None:
    panel, canonical = load_inputs()

    target_dates = set(canonical["signal_date"].dropna())
    if not target_dates:
        raise RuntimeError("No canonical signal dates.")

    first_target = min(target_dates)
    last_target = max(target_dates)

    # We need the immediately preceding executable row so PREV_HY is PIT-correct.
    executable = panel["signal_date"].notna()
    if "execution_date" in panel.columns:
        executable &= panel["execution_date"].notna()
    if "SPY" in panel.columns:
        executable &= pd.to_numeric(panel["SPY"], errors="coerce").notna()

    exec_indices = panel.index[executable].tolist()
    if not exec_indices:
        raise RuntimeError("No executable rows in master_panel.csv")

    target_positions = [
        pos for pos, idx in enumerate(exec_indices)
        if panel.loc[idx, "signal_date"] >= first_target
        and panel.loc[idx, "signal_date"] <= last_target
    ]
    if not target_positions:
        raise RuntimeError("No executable rows overlap canonical range.")

    start_pos = max(0, min(target_positions) - 1)
    end_pos = max(target_positions)
    replay_indices = exec_indices[start_pos : end_pos + 1]

    previous_exposure = 50.0
    flow_memory: dict[str, Any] = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    # Durable Filter15 state. This is carried only from the prior actual call.
    f15_state = {
        "prev_deadman": False,
        "recovery_active": False,
        "recovery_completed": False,
        "recovery_streak": 0,
        "prev_hy_oas": None,
    }

    actual_rows: list[dict[str, Any]] = []

    for idx in replay_indices:
        signal_date = pd.Timestamp(panel.loc[idx, "signal_date"]).normalize()

        market_data = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=previous_exposure,
        )

        with contextlib.redirect_stdout(io.StringIO()):
            flow_memory = prepare_filter13_execution_state(
                market_data=market_data,
                panel=panel,
                row_index=idx,
                previous_flow_memory=flow_memory,
            )

        disable_live_side_effects(previous_exposure)
        neutralize_all_side_effects(previous_exposure)

        with contextlib.redirect_stdout(io.StringIO()):
            sf.narrative_engine_filter(market_data)

        # Exact production-candidate state injection.
        market_data["FILTER15_PREV_DEADMAN"] = f15_state["prev_deadman"]
        market_data["FILTER15_RECOVERY_ACTIVE"] = f15_state["recovery_active"]
        market_data["FILTER15_RECOVERY_COMPLETED"] = f15_state["recovery_completed"]
        market_data["FILTER15_RECOVERY_STREAK"] = f15_state["recovery_streak"]
        market_data["FILTER15_PREV_HY_OAS"] = f15_state["prev_hy_oas"]

        pre_state = dict(f15_state)

        with contextlib.redirect_stdout(io.StringIO()):
            sf.volatility_controlled_exposure_filter(market_data)

        actual_exposure = _num(market_data.get("RECOMMENDED_EXPOSURE"))
        actual_status = str(market_data.get("SEW_STATUS", "N/A"))

        hy = market_data.get("HY_OAS", {}) or {}
        vix = market_data.get("VIX", {}) or {}

        hy_now = _num(hy.get("today"))
        vix_now = _num(vix.get("today"))

        actual_candidate = (
            hy_now is not None
            and pre_state["prev_hy_oas"] is not None
            and hy_now < float(pre_state["prev_hy_oas"])
            and vix_now is not None
            and vix_now < 30.0
        )

        # State must be read from the actual patched function output.
        f15_state = {
            "prev_deadman": _safe_bool(
                market_data.get("FILTER15_PREV_DEADMAN", False)
            ),
            "recovery_active": _safe_bool(
                market_data.get("FILTER15_RECOVERY_ACTIVE", False)
            ),
            "recovery_completed": bool(
                market_data.get("FILTER15_RECOVERY_COMPLETED", False)
            ),
            "recovery_streak": int(
                market_data.get("FILTER15_RECOVERY_STREAK", 0) or 0
            ),
            "prev_hy_oas": _num(
                market_data.get("FILTER15_PREV_HY_OAS")
            ),
        }

        if actual_exposure is not None:
            previous_exposure = actual_exposure

        if signal_date in target_dates:
            actual_rows.append(
                {
                    "signal_date": signal_date,
                    "actual_source_exposure": actual_exposure,
                    "actual_source_state": actual_status,
                    "actual_source_candidate": actual_candidate,
                    "actual_source_prev_deadman_in": pre_state["prev_deadman"],
                    "actual_source_recovery_active_in": pre_state["recovery_active"],
                    "actual_source_streak_in": pre_state["recovery_streak"],
                    "actual_source_prev_hy_in": pre_state["prev_hy_oas"],
                    "actual_source_prev_deadman_out": f15_state["prev_deadman"],
                    "actual_source_recovery_active_out": f15_state["recovery_active"],
                    "actual_source_streak_out": f15_state["recovery_streak"],
                    "actual_source_prev_hy_out": f15_state["prev_hy_oas"],
                    "pit_hy_oas": hy_now,
                    "pit_vix": vix_now,
                    "risk_budget_13": _num(market_data.get("RISK_BUDGET")),
                }
            )

    actual = pd.DataFrame(actual_rows)

    # One actual call per signal date. If this fails, stop: duplicated execution
    # would corrupt state continuity.
    dup = actual["signal_date"].duplicated(keep=False)
    if dup.any():
        raise ValueError(
            "Actual-source replay produced duplicate signal dates:\n"
            + actual.loc[dup, ["signal_date"]].head(30).to_string(index=False)
        )

    merged = canonical.merge(
        actual,
        on="signal_date",
        how="left",
        validate="many_to_one",
    )

    missing_actual = merged["actual_source_exposure"].isna()
    if missing_actual.any():
        print("[WARNING] canonical rows without actual executable replay:")
        print(
            merged.loc[
                missing_actual, ["episode_id", "signal_date"]
            ].head(50).to_string(index=False)
        )

    # Corrected canonical uses daily baseline x staged multiplier.
    # Actual source output should equal corrected exposure on executable rows.
    merged["exposure_error"] = (
        pd.to_numeric(merged["actual_source_exposure"], errors="coerce")
        - pd.to_numeric(merged["corrected_exposure"], errors="coerce")
    ).abs()

    merged["candidate_match"] = (
        merged["actual_source_candidate"].astype("boolean")
        == merged["corrected_candidate"].astype("boolean")
    )

    # Canonical state names are expected to match actual patched status.
    merged["state_match"] = (
        merged["actual_source_state"].astype(str)
        == merged["corrected_state"].astype(str)
    )

    # Streak is checked only while canonical recovery is not completed.
    canon_streak = pd.to_numeric(
        merged["corrected_streak"], errors="coerce"
    ).fillna(0).astype(int)

    actual_streak_out = pd.to_numeric(
        merged["actual_source_streak_out"], errors="coerce"
    ).fillna(0).astype(int)

    completed = merged["corrected_completed"].map(_safe_bool)

    merged["streak_match"] = np.where(
        completed,
        True,
        canon_streak.eq(actual_streak_out),
    )

    valid = ~missing_actual

    merged["exact_match"] = (
        valid
        & merged["exposure_error"].le(TOL)
        & merged["candidate_match"].fillna(False)
        & merged["state_match"].fillna(False)
        & pd.Series(merged["streak_match"], index=merged.index).fillna(False)
    )

    checked = int(valid.sum())
    exact = int(merged.loc[valid, "exact_match"].sum())
    fails = checked - exact
    max_exp_err = float(
        merged.loc[valid, "exposure_error"].max()
    ) if checked else float("nan")

    episode_gate = (
        merged.loc[valid]
        .groupby("episode_id", as_index=False)
        .agg(
            rows=("signal_date", "size"),
            exact_rows=("exact_match", "sum"),
            max_exposure_error=("exposure_error", "max"),
        )
    )
    episode_gate["pass"] = (
        episode_gate["rows"].eq(episode_gate["exact_rows"])
        & episode_gate["max_exposure_error"].le(TOL)
    )

    episodes_checked = len(episode_gate)
    episodes_pass = int(episode_gate["pass"].sum())

    # ------------------------------------------------------------------
    # Episode 1 tail trace
    # ------------------------------------------------------------------
    tail = merged.loc[
        merged["episode_id"].eq(1) & valid
    ].copy()

    tail["actual_source_return"] = (
        pd.to_numeric(tail["actual_source_exposure"], errors="coerce")
        / 100.0
        * pd.to_numeric(tail["spy_return_t1"], errors="coerce").fillna(0.0)
    )
    tail["canonical_wealth"] = (
        1.0 + pd.to_numeric(tail["corrected_return"], errors="coerce").fillna(0.0)
    ).cumprod()
    tail["canonical_drawdown"] = (
        tail["canonical_wealth"] / tail["canonical_wealth"].cummax() - 1.0
    )
    tail["actual_wealth"] = (
        1.0 + tail["actual_source_return"].fillna(0.0)
    ).cumprod()
    tail["actual_drawdown"] = (
        tail["actual_wealth"] / tail["actual_wealth"].cummax() - 1.0
    )

    canonical_tail_mdd = _mdd(tail["corrected_return"])
    actual_tail_mdd = _mdd(tail["actual_source_return"])

    if not tail.empty:
        worst_i = tail["canonical_drawdown"].idxmin()
        worst_date = tail.loc[worst_i, "signal_date"]
        worst_state = tail.loc[worst_i, "corrected_state"]
        worst_exposure = tail.loc[worst_i, "corrected_exposure"]
    else:
        worst_date = pd.NaT
        worst_state = "N/A"
        worst_exposure = np.nan

    parity_pass = (
        checked > 0
        and fails == 0
        and episodes_checked > 0
        and episodes_pass == episodes_checked
    )

    tail_reconciles = (
        np.isfinite(canonical_tail_mdd)
        and np.isfinite(actual_tail_mdd)
        and abs(canonical_tail_mdd - actual_tail_mdd) <= TOL
    )

    final_pass = parity_pass and tail_reconciles

    summary = pd.DataFrame(
        [
            {
                "rows_checked": checked,
                "exact_match_rows": exact,
                "parity_fail_rows": fails,
                "max_exposure_error": max_exp_err,
                "episodes_checked": episodes_checked,
                "episodes_pass": episodes_pass,
                "episode1_canonical_mdd": canonical_tail_mdd,
                "episode1_actual_source_mdd": actual_tail_mdd,
                "episode1_mdd_reconciles": tail_reconciles,
                "parity_pass": parity_pass,
                "final_pass": final_pass,
            }
        ]
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUT_DAILY, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
    tail.to_csv(OUT_TAIL, index=False)

    lines = [
        "=" * 78,
        "FILTER15 ACTUAL-SOURCE EXACT PARITY + WORST EPISODE TRACE",
        "=" * 78,
        "",
        "Production Main Modified     : NO",
        "Source Under Test            : current-worktree filters/strategist_filters.py",
        "Simulator Rewrite            : NO",
        "Signal Timing                : t only",
        "Forward Fill                 : NO",
        "State Transition             : one actual call per executable signal date",
        "Canonical                    : corrected daily-baseline 25/50/100",
        "",
        "===== ACTUAL-SOURCE PARITY =====",
        f"Rows Checked                 : {checked}",
        f"Exact Match Rows             : {exact}",
        f"Parity Fail Rows             : {fails}",
        f"Max Exposure Error           : {max_exp_err:.12f}",
        f"Episodes Checked             : {episodes_checked}",
        f"Episodes PASS                : {episodes_pass}",
        f"PARITY                       : {'PASS' if parity_pass else 'FAIL'}",
        "",
        "===== EPISODE 1 / 2008 TAIL TRACE =====",
        f"Rows                         : {len(tail)}",
        f"Canonical MDD                : {canonical_tail_mdd:.3%}",
        f"Actual-Source MDD            : {actual_tail_mdd:.3%}",
        f"MDD Reconciliation           : {'PASS' if tail_reconciles else 'FAIL'}",
        f"Worst Drawdown Signal Date   : {worst_date}",
        f"State at Worst Drawdown      : {worst_state}",
        f"Exposure at Worst Drawdown   : {worst_exposure}",
        "",
    ]

    if fails:
        lines.extend(
            [
                "===== FIRST PARITY FAILURES =====",
                merged.loc[
                    valid & ~merged["exact_match"],
                    [
                        "episode_id",
                        "signal_date",
                        "daily_filter15_baseline",
                        "corrected_candidate",
                        "actual_source_candidate",
                        "corrected_streak",
                        "actual_source_streak_out",
                        "corrected_state",
                        "actual_source_state",
                        "corrected_exposure",
                        "actual_source_exposure",
                        "exposure_error",
                        "pit_hy_oas",
                        "pit_vix",
                    ],
                ]
                .head(30)
                .to_string(index=False),
                "",
            ]
        )

    lines.extend(
        [
            "===== FINAL GATE =====",
            f"STATUS                       : {'PASS' if final_pass else 'FAIL'}",
            "",
            "판정:",
        ]
    )

    if final_pass:
        lines.extend(
            [
                "- 현재 worktree의 실제 Filter15 patch가 corrected research contract와 exact parity다.",
                "- Episode 1 tail도 actual-source replay와 동일하게 재현된다.",
                "- 다음 단계는 final production safety regression이다.",
                "- 아직 main에는 승격하지 않는다.",
                "",
                "PRODUCTION DECISION: NO CHANGE",
                "NEXT GATE: FINAL PRODUCTION SAFETY REGRESSION",
            ]
        )
    else:
        lines.extend(
            [
                "- 현재 actual source와 corrected canonical 사이에 contract 차이가 남아 있다.",
                "- Production behavior를 추가 수정하지 말고 최초 mismatch를 진단한다.",
                "- 특히 candidate/state/streak/exposure 중 최초로 갈라지는 열을 확인한다.",
                "",
                "PRODUCTION DECISION: NO CHANGE",
                "NEXT GATE: DIAGNOSE FIRST ACTUAL-SOURCE MISMATCH",
            ]
        )

    lines.extend(
        [
            "",
            f"Saved: {OUT_DAILY}",
            f"Saved: {OUT_SUMMARY}",
            f"Saved: {OUT_TAIL}",
            f"Saved: {OUT_AUDIT}",
        ]
    )

    text = "\n".join(lines)
    OUT_AUDIT.write_text(text, encoding="utf-8")

    print(text)


if __name__ == "__main__":
    main()
