from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "data" / "backtest" / "results"

CANONICAL = R / "filter15_staged_restoration_parameter_sensitivity_canonical_daily.csv"
MASTER = ROOT / "data" / "backtest" / "master_panel.csv"

OUT_DAILY = R / "filter15_staged_production_exact_parity_daily.csv"
OUT_SUMMARY = R / "filter15_staged_production_exact_parity_summary.csv"
OUT_TXT = R / "filter15_staged_production_exact_parity_audit.txt"

TARGET_PATH = "RAMP_3"
TOL = 1e-12


def norm_date(s):
    return pd.to_datetime(s, errors="coerce").dt.normalize()


def to_bool(x):
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if pd.isna(x):
        return False
    return str(x).strip().lower() in {"true", "1", "yes", "y"}


def require(df, cols, name):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing columns: {missing}")


def main():
    research = pd.read_csv(CANONICAL)
    mp = pd.read_csv(MASTER)

    require(
        research,
        [
            "episode_id", "signal_date", "path", "candidate",
            "multiplier", "candidate_exposure",
            "counterfactual_exposure",
        ],
        "canonical",
    )
    require(mp, ["date", "VIX", "credit__HY_OAS"], "master_panel")

    research = research[research["path"].astype(str) == TARGET_PATH].copy()
    if research.empty:
        raise ValueError(f"No {TARGET_PATH} rows")

    research["signal_date"] = norm_date(research["signal_date"])

    # ---------------------------------------------------------
    # PIT candidate: canonical research contract
    # FULL master_panel first, then episode/date selection.
    # ---------------------------------------------------------
    mp["signal_date"] = norm_date(mp["date"])
    mp = mp.sort_values("signal_date").copy()

    hy = pd.to_numeric(mp["credit__HY_OAS"], errors="coerce")
    vix = pd.to_numeric(mp["VIX"], errors="coerce")
    hy_prev = hy.shift(1)

    mp["pit_prev_hy_oas"] = hy_prev
    mp["pit_hy_oas"] = hy
    mp["pit_vix"] = vix
    mp["pit_hy_falling"] = (hy < hy_prev).fillna(False)

    mp["production_candidate"] = (
        hy.notna()
        & hy_prev.notna()
        & vix.notna()
        & (hy < hy_prev)
        & (vix < 30.0)
    )

    pit = mp[
        [
            "signal_date", "pit_prev_hy_oas", "pit_hy_oas",
            "pit_vix", "pit_hy_falling", "production_candidate",
        ]
    ].drop_duplicates("signal_date", keep="last")

    research = research.merge(
        pit, on="signal_date", how="left", validate="many_to_one"
    )

    # ---------------------------------------------------------
    # IMPORTANT FIX:
    # canonical artifact can contain repeated episode/date rows.
    # State transition MUST occur once per episode + signal_date.
    # ---------------------------------------------------------
    unique = (
        research.sort_values(["episode_id", "signal_date"])
        .drop_duplicates(["episode_id", "signal_date"], keep="first")
        .copy()
    )

    simulated = []

    for episode_id, g in unique.groupby("episode_id", sort=True):
        g = g.sort_values("signal_date")
        stage_idx = 0

        for _, row in g.iterrows():
            candidate = bool(row["production_candidate"])

            if candidate:
                if stage_idx == 0:
                    mult = 0.25
                    state = "STAGE_1"
                    stage_idx = 1
                elif stage_idx == 1:
                    mult = 0.50
                    state = "STAGE_2"
                    stage_idx = 2
                else:
                    mult = 1.00
                    state = "FULL"
                    stage_idx = 2
            else:
                mult = 0.0
                state = "RE_BRAKE"
                stage_idx = 0

            base = float(row["candidate_exposure"])

            simulated.append(
                {
                    "episode_id": episode_id,
                    "signal_date": row["signal_date"],
                    "production_state": state,
                    "production_multiplier": mult,
                    "production_exposure": base * mult,
                }
            )

    sim = pd.DataFrame(simulated)

    # Broadcast the one-transition-per-date result back to every
    # canonical row for exact row-level comparison.
    out = research.merge(
        sim,
        on=["episode_id", "signal_date"],
        how="left",
        validate="many_to_one",
    )

    out["candidate_match"] = (
        out["candidate"].map(to_bool)
        == out["production_candidate"].map(to_bool)
    )

    out["multiplier_error"] = (
        pd.to_numeric(out["multiplier"], errors="coerce")
        - pd.to_numeric(out["production_multiplier"], errors="coerce")
    ).abs()

    out["exposure_error"] = (
        pd.to_numeric(out["counterfactual_exposure"], errors="coerce")
        - pd.to_numeric(out["production_exposure"], errors="coerce")
    ).abs()

    out["exact_match"] = (
        out["candidate_match"]
        & (out["multiplier_error"] <= TOL)
        & (out["exposure_error"] <= TOL)
    )

    total = len(out)
    exact = int(out["exact_match"].sum())
    fails = total - exact

    eps = (
        out.groupby("episode_id", as_index=False)
        .agg(
            rows=("exact_match", "size"),
            exact_rows=("exact_match", "sum"),
            candidate_fail=("candidate_match", lambda s: int((~s).sum())),
            max_multiplier_error=("multiplier_error", "max"),
            max_exposure_error=("exposure_error", "max"),
        )
    )
    eps["episode_pass"] = eps["rows"] == eps["exact_rows"]

    max_mult = float(out["multiplier_error"].max())
    max_exp = float(out["exposure_error"].max())

    passed = (
        fails == 0
        and max_mult <= TOL
        and max_exp <= TOL
        and bool(eps["episode_pass"].all())
    )

    out.to_csv(OUT_DAILY, index=False)
    eps.to_csv(OUT_SUMMARY, index=False)

    lines = [
        "=" * 78,
        "FILTER15 RESEARCH <-> PRODUCTION CANDIDATE EXACT PARITY v3",
        "=" * 78,
        "",
        f"Research Path            : {TARGET_PATH}",
        "Production Modified      : NO",
        "Future Data Added        : NO",
        "HY Contract              : FULL PANEL HY_t < HY_t-1",
        "VIX Missing              : candidate=False / RE_BRAKE",
        "Duplicate Date Contract  : ONE STATE TRANSITION PER EPISODE/DATE",
        "Staged Path              : 25% -> 50% -> 100%",
        "",
        "===== PARITY SUMMARY =====",
        f"Rows Checked             : {total}",
        f"Exact Match Rows         : {exact}",
        f"Parity Fail Rows         : {fails}",
        f"Max Multiplier Error     : {max_mult:.12f}",
        f"Max Exposure Error       : {max_exp:.12f}",
        f"Episodes Checked         : {len(eps)}",
        f"Episodes PASS            : {int(eps['episode_pass'].sum())}",
        "",
        f"PARITY: {'PASS' if passed else 'FAIL'}",
        "",
    ]

    if passed:
        lines += [
            "PRODUCTION DECISION: CANDIDATE PARITY APPROVED",
            "NEXT GATE: MINIMAL PATCH APPLICATION ON RESEARCH BRANCH + POST-PATCH REGRESSION",
        ]
    else:
        bad = out.loc[
            ~out["exact_match"],
            [
                "episode_id", "signal_date",
                "pit_prev_hy_oas", "pit_hy_oas", "pit_vix",
                "candidate", "production_candidate",
                "multiplier", "production_multiplier",
                "counterfactual_exposure", "production_exposure",
                "multiplier_error", "exposure_error",
            ],
        ].head(40)

        lines += [
            "===== FIRST FAILURES =====",
            bad.to_string(index=False),
            "",
            "PRODUCTION DECISION: NO CHANGE",
            "NEXT GATE: DIAGNOSE REMAINING CONTRACT DIFFERENCE",
        ]

    text = "\n".join(lines)
    OUT_TXT.write_text(text, encoding="utf-8")
    print(text)
    print()
    print(f"Saved: {OUT_DAILY}")
    print(f"Saved: {OUT_SUMMARY}")
    print(f"Saved: {OUT_TXT}")

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
