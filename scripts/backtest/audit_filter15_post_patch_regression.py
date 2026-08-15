from __future__ import annotations

"""
Filter15 POST-PATCH regression.

목적
----
실제로 수정된 filters/strategist_filters.py의
volatility_controlled_exposure_filter()를 실행하여 Research canonical
RAMP_3와 비교한다.

중요:
- candidate simulator를 다시 쓰지 않는다.
- 실제 patched source를 import해서 호출한다.
- signal t 정보만 사용한다.
- episode/date 중복은 state transition 1회만 수행한다.
- Production main은 수정하지 않는다.
"""

from pathlib import Path
import copy
import importlib
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

R = ROOT / "data" / "backtest" / "results"

CANONICAL = R / "filter15_staged_restoration_parameter_sensitivity_canonical_daily.csv"
ATTR = R / "filter15_exposure_attribution_daily.csv"
MASTER = ROOT / "data" / "backtest" / "master_panel.csv"

OUT_DAILY = R / "filter15_post_patch_regression_daily.csv"
OUT_SUMMARY = R / "filter15_post_patch_regression_summary.csv"
OUT_TXT = R / "filter15_post_patch_regression_audit.txt"

TARGET_PATH = "RAMP_3"
TOL = 1e-9


def norm_date(s):
    return pd.to_datetime(s, errors="coerce").dt.normalize()


def num(x, default=None):
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def text(x, default=""):
    if pd.isna(x):
        return default
    return str(x)


def require(df, cols, label):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")


def load():
    research = pd.read_csv(CANONICAL)
    attr = pd.read_csv(ATTR)
    mp = pd.read_csv(MASTER)

    require(
        research,
        [
            "episode_id",
            "signal_date",
            "path",
            "candidate",
            "multiplier",
            "candidate_exposure",
            "counterfactual_exposure",
        ],
        "canonical",
    )

    require(
        attr,
        [
            "signal_date",
            "risk_budget_13",
            "vix_today",
            "vix_pct_change",
            "sp500_pos_z",
            "pos_slope",
            "dealer_gamma_bias",
            "cta_momentum_score",
            "hy_oas_today",
            "hy_oas_pct_change",
            "macro_narrative",
            "cross_asset_vix_z",
            "leadership_breadth_score",
            "hy_oas_status",
            "actual_exposure_15",
            "hard_deadman",
        ],
        "attribution",
    )

    require(mp, ["date", "credit__HY_OAS", "VIX"], "master_panel")

    research = research[
        research["path"].astype(str) == TARGET_PATH
    ].copy()

    research["signal_date"] = norm_date(research["signal_date"])
    attr["signal_date"] = norm_date(attr["signal_date"])
    mp["signal_date"] = norm_date(mp["date"])

    # Canonical artifact contains repeated episode/date rows.
    # A persistent state machine may transition only once per signal date.
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

    mp = mp.sort_values("signal_date").copy()
    mp["panel_hy"] = pd.to_numeric(mp["credit__HY_OAS"], errors="coerce")
    mp["panel_prev_hy"] = mp["panel_hy"].shift(1)
    mp["panel_vix"] = pd.to_numeric(mp["VIX"], errors="coerce")

    pit = mp[
        ["signal_date", "panel_hy", "panel_prev_hy", "panel_vix"]
    ].drop_duplicates("signal_date", keep="last")

    df = research.merge(
        attr,
        on="signal_date",
        how="left",
        validate="many_to_one",
        suffixes=("", "_attr"),
    ).merge(
        pit,
        on="signal_date",
        how="left",
        validate="many_to_one",
    )

    # ---------------------------------------------------------
    # Trading-calendar alignment
    # ---------------------------------------------------------
    # Canonical research artifact may contain calendar dates
    # (weekends / US market holidays), while Filter15 attribution
    # exists only for executable trading signal dates.
    #
    # Institutional contract:
    # - do NOT forward-fill Filter15 inputs
    # - do NOT synthesize a signal on a non-trading day
    # - compare only dates on which the production execution
    #   chain actually has a Filter15 attribution row.
    # ---------------------------------------------------------

    missing_attr = df["risk_budget_13"].isna()

    if missing_attr.any():
        skipped = df.loc[
            missing_attr,
            ["episode_id", "signal_date"],
        ].copy()

        print(
            "[INFO][TRADING CALENDAR] "
            f"Skipping {len(skipped)} canonical rows with no "
            "executable Filter15 attribution row."
        )

        print(
            skipped.head(30).to_string(index=False)
        )

        df = df.loc[~missing_attr].copy()

    if df.empty:
        raise ValueError(
            "No executable trading-date rows remain after "
            "calendar alignment."
        )

    return df


def build_market_data(row, state):
    """
    실제 Filter15가 필요로 하는 signal-t 입력만 구성.
    전일 recovery state는 직전 실제 patched call의 output을 사용한다.
    """
    md = {
        "RISK_BUDGET": num(row["risk_budget_13"], 50.0),
        "VIX": {
            "today": num(row["vix_today"]),
            "pct_change": num(row["vix_pct_change"]),
        },
        "SP500_POS_Z": num(row["sp500_pos_z"], 0.0),
        "POS_SLOPE": num(row["pos_slope"], 0.0),
        "DEALER_GAMMA_BIAS": num(row["dealer_gamma_bias"], 1.0),
        "CTA_MOMENTUM_SCORE": num(row["cta_momentum_score"], 1.0),
        "HY_OAS": {
            "today": num(row["hy_oas_today"]),
            "pct_change": num(row["hy_oas_pct_change"]),
        },
        "INSTITUTIONAL_FLOW": {"score": 0},
        "MACRO_NARRATIVE": text(row["macro_narrative"], "N/A").upper(),
        "CROSS_ASSET_TAPE": {
            "VIX_Z": num(row["cross_asset_vix_z"], 0.0)
        },
        "LEADERSHIP_BREADTH_SCORE": num(
            row["leadership_breadth_score"], 0.0
        ),
        "HY_OAS_STATUS": text(row["hy_oas_status"], ""),
        "FILTER15_PREV_DEADMAN": bool(state["prev_deadman"]),
        "FILTER15_RECOVERY_ACTIVE": bool(state["recovery_active"]),
        "FILTER15_RECOVERY_STREAK": int(state["recovery_streak"]),
        "FILTER15_PREV_HY_OAS": state["prev_hy_oas"],
    }
    return md


def main():
    df = load()

    # Import the CURRENT WORKTREE source, not the committed GitHub version.
    import filters.strategist_filters as sf
    sf = importlib.reload(sf)

    if not hasattr(sf, "volatility_controlled_exposure_filter"):
        raise AttributeError(
            "filters.strategist_filters.volatility_controlled_exposure_filter missing"
        )

    rows = []

    for episode_id, g in df.groupby("episode_id", sort=True):
        g = g.sort_values("signal_date").copy()

        # Episode research window begins at release candidate.
        # Canonical first row is treated as the day immediately after
        # a prior deadman regime, matching the intended release test.
        state = {
            "prev_deadman": True,
            "recovery_active": False,
            "recovery_streak": 0,
            # Critical PIT contract:
            # prior observable full-panel HY, never episode-local shift.
            "prev_hy_oas": num(g.iloc[0]["panel_prev_hy"]),
        }

        for _, row in g.iterrows():
            md = build_market_data(row, state)

            sf.volatility_controlled_exposure_filter(md)

            actual = num(md.get("RECOMMENDED_EXPOSURE"))
            expected = num(row["counterfactual_exposure"])

            patched_prev_deadman = bool(
                md.get("FILTER15_PREV_DEADMAN", False)
            )
            patched_active = bool(
                md.get("FILTER15_RECOVERY_ACTIVE", False)
            )
            patched_streak = int(
                md.get("FILTER15_RECOVERY_STREAK", 0) or 0
            )
            patched_prev_hy = num(
                md.get("FILTER15_PREV_HY_OAS")
            )

            # Research candidate is retained only as an audit comparator.
            research_candidate = str(row["candidate"]).strip().lower() in {
                "true", "1", "yes", "y"
            }

            patched_candidate_from_pit = (
                num(row["hy_oas_today"]) is not None
                and state["prev_hy_oas"] is not None
                and num(row["hy_oas_today"]) < state["prev_hy_oas"]
                and num(row["vix_today"]) is not None
                and num(row["vix_today"]) < 30.0
            )

            error = (
                abs(actual - expected)
                if actual is not None and expected is not None
                else np.nan
            )

            rows.append(
                {
                    "episode_id": episode_id,
                    "signal_date": row["signal_date"],
                    "research_candidate": research_candidate,
                    "patched_candidate_from_pit": patched_candidate_from_pit,
                    "hy_oas": num(row["hy_oas_today"]),
                    "prev_hy_oas_injected": state["prev_hy_oas"],
                    "vix": num(row["vix_today"]),
                    "research_multiplier": num(row["multiplier"]),
                    "research_candidate_exposure": num(
                        row["candidate_exposure"]
                    ),
                    "research_expected_exposure": expected,
                    "patched_exposure": actual,
                    "exposure_error": error,
                    "original_production_exposure": num(
                        row["actual_exposure_15"]
                    ),
                    "original_hard_deadman": bool(row["hard_deadman"]),
                    "patched_prev_deadman_out": patched_prev_deadman,
                    "patched_recovery_active_out": patched_active,
                    "patched_recovery_streak_out": patched_streak,
                    "patched_prev_hy_out": patched_prev_hy,
                    "patched_status": md.get("SEW_STATUS"),
                }
            )

            # Durable state passed to the next signal date.
            state = {
                "prev_deadman": patched_prev_deadman,
                "recovery_active": patched_active,
                "recovery_streak": patched_streak,
                "prev_hy_oas": patched_prev_hy,
            }

    out = pd.DataFrame(rows)

    out["exact_match"] = (
        out["exposure_error"].notna()
        & (out["exposure_error"] <= TOL)
    )

    total = len(out)
    exact = int(out["exact_match"].sum())
    fail = total - exact
    max_err = float(out["exposure_error"].max())

    eps = (
        out.groupby("episode_id", as_index=False)
        .agg(
            rows=("exact_match", "size"),
            exact_rows=("exact_match", "sum"),
            max_exposure_error=("exposure_error", "max"),
        )
    )
    eps["episode_pass"] = eps["rows"] == eps["exact_rows"]

    passed = fail == 0 and max_err <= TOL and bool(eps["episode_pass"].all())

    out.to_csv(OUT_DAILY, index=False)
    eps.to_csv(OUT_SUMMARY, index=False)

    lines = [
        "=" * 78,
        "FILTER15 ACTUAL PATCHED-SOURCE POST-PATCH REGRESSION",
        "=" * 78,
        "",
        "Execution Target         : CURRENT WORKTREE strategist_filters.py",
        "Research Path            : RAMP_3",
        "Research Contract        : 25% -> 50% -> 100% / break -> 0%",
        "Future Data Added        : NO",
        "Episode/Date Transition : ONCE",
        "",
        "===== SUMMARY =====",
        f"Rows Checked             : {total}",
        f"Exact Match Rows         : {exact}",
        f"Regression Fail Rows     : {fail}",
        f"Max Exposure Error       : {max_err:.12f}",
        f"Episodes Checked         : {len(eps)}",
        f"Episodes PASS            : {int(eps['episode_pass'].sum())}",
        "",
        f"POST-PATCH REGRESSION: {'PASS' if passed else 'FAIL'}",
        "",
    ]

    if not passed:
        bad = out.loc[
            ~out["exact_match"],
            [
                "episode_id",
                "signal_date",
                "hy_oas",
                "prev_hy_oas_injected",
                "vix",
                "research_candidate",
                "patched_candidate_from_pit",
                "original_hard_deadman",
                "research_expected_exposure",
                "patched_exposure",
                "exposure_error",
                "patched_status",
                "patched_prev_deadman_out",
                "patched_recovery_active_out",
                "patched_recovery_streak_out",
            ],
        ].head(40)

        lines += [
            "===== FIRST FAILURES =====",
            bad.to_string(index=False),
            "",
            "DECISION: DO NOT COMMIT PATCH YET",
            "NEXT: diagnose actual patched-source contract mismatch.",
        ]
    else:
        lines += [
            "DECISION: POST-PATCH REGRESSION APPROVED",
            "NEXT: commit research-branch patch, then prepare minimal main promotion.",
        ]

    text_out = "\n".join(lines)
    OUT_TXT.write_text(text_out, encoding="utf-8")

    print(text_out)
    print()
    print(f"Saved: {OUT_DAILY}")
    print(f"Saved: {OUT_SUMMARY}")
    print(f"Saved: {OUT_TXT}")

    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
