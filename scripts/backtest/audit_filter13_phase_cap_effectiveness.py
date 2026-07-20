from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

ATTRIBUTION_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter13_budget_attribution_final_daily.csv"
)

MACRO_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "macro_data.csv"
)

OUTPUT_DAILY = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter13_phase_cap_effectiveness_daily.csv"
)

OUTPUT_SUMMARY = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter13_phase_cap_effectiveness_summary.csv"
)


# ============================================================
# Helpers
# ============================================================

def forward_return(series: pd.Series, horizon: int) -> pd.Series:
    """
    Trading-row forward return.

    Example:
    horizon=5 means:
    today's SPY -> SPY 5 trading rows later.

    IMPORTANT:
    This is outcome/evaluation data only.
    It must never feed back into Filter13 decisions.
    """
    return (
        series.shift(-horizon)
        / series
        - 1.0
    )


def classify_outcome(ret):
    """
    Simple ex-post classification.

    Positive forward return:
        reducing exposure created opportunity cost.

    Negative forward return:
        reducing exposure was directionally defensive.
    """
    if pd.isna(ret):
        return "N/A"

    if ret < 0:
        return "DEFENSIVE_SUCCESS"

    if ret > 0:
        return "OPPORTUNITY_COST"

    return "FLAT"


# ============================================================
# Main
# ============================================================

def main():

    # --------------------------------------------------------
    # 1. Load verified Filter13 attribution
    # --------------------------------------------------------

    if not ATTRIBUTION_PATH.exists():
        raise FileNotFoundError(
            f"Missing attribution file: {ATTRIBUTION_PATH}"
        )

    a = pd.read_csv(ATTRIBUTION_PATH)

    required_attr = [
        "date",
        "pit_status",
        "base_budget",
        "pre_cap_budget",
        "phase_cap",
        "phase_cap_effect",
        "final_budget",
        "market_regime",
        "macro_narrative",
    ]

    missing = [
        c for c in required_attr
        if c not in a.columns
    ]

    if missing:
        raise RuntimeError(
            f"Missing attribution columns: {missing}"
        )

    a["date"] = pd.to_datetime(
        a["date"],
        errors="coerce",
    )

    # PIT gate
    allowed_status = {
        "PASS",
        "FIRST_ROW",
    }

    bad = a[
        ~a["pit_status"].isin(
            allowed_status
        )
    ]

    if not bad.empty:
        raise RuntimeError(
            "PIT attribution gate failed. "
            "Audit aborted."
        )

    # --------------------------------------------------------
    # 2. Load SPY price history
    # --------------------------------------------------------

    if not MACRO_PATH.exists():
        raise FileNotFoundError(
            f"Missing macro file: {MACRO_PATH}"
        )

    m = pd.read_csv(
        MACRO_PATH,
        usecols=[
            "date",
            "SPY",
        ],
    )

    m["date"] = pd.to_datetime(
        m["date"],
        errors="coerce",
    )

    m["SPY"] = pd.to_numeric(
        m["SPY"],
        errors="coerce",
    )

    m = (
        m
        .dropna(
            subset=[
                "date",
                "SPY",
            ]
        )
        .sort_values("date")
        .drop_duplicates(
            subset=["date"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # 3. Forward returns
    #
    # IMPORTANT:
    # These are ex-post labels ONLY.
    # No Filter13 signal uses these values.
    # --------------------------------------------------------

    for h in [1, 5, 20]:

        m[f"spy_fwd_{h}d"] = (
            forward_return(
                m["SPY"],
                h,
            )
        )

    # --------------------------------------------------------
    # 4. Merge outcome data onto Filter13 dates
    # --------------------------------------------------------

    d = a.merge(
        m[
            [
                "date",
                "SPY",
                "spy_fwd_1d",
                "spy_fwd_5d",
                "spy_fwd_20d",
            ]
        ],
        on="date",
        how="left",
        validate="one_to_one",
    )

    missing_spy = int(
        d["SPY"].isna().sum()
    )

    if missing_spy > 0:

        print(
            f"[WARNING] Missing SPY on "
            f"{missing_spy} attribution rows."
        )

    # --------------------------------------------------------
    # 5. Identify actual Phase Cap interventions
    # --------------------------------------------------------

    d["phase_cap_active"] = (
        d["phase_cap_effect"] < 0
    )

    active = d[
        d["phase_cap_active"]
    ].copy()

    if active.empty:
        raise RuntimeError(
            "No Phase Cap intervention days found."
        )

    # Amount of exposure removed by Phase Cap
    active["exposure_cut"] = (
        -active["phase_cap_effect"]
    )

    # --------------------------------------------------------
    # 6. Ex-post outcome classification
    # --------------------------------------------------------

    for h in [1, 5, 20]:

        ret_col = f"spy_fwd_{h}d"

        active[
            f"outcome_{h}d"
        ] = active[
            ret_col
        ].apply(
            classify_outcome
        )

        # Approximate foregone/avoided contribution:
        #
        # exposure_cut is percentage points,
        # so divide by 100.
        #
        # Negative:
        # cap avoided loss.
        #
        # Positive:
        # cap missed gain.
        active[
            f"cap_opportunity_effect_{h}d"
        ] = (
            active["exposure_cut"]
            / 100.0
            * active[ret_col]
        )

    # --------------------------------------------------------
    # 7. Summary
    # --------------------------------------------------------

    print(
        "\n=== FILTER13 PHASE CAP "
        "EFFECTIVENESS AUDIT ==="
    )

    print("\n[PERIOD]")

    print(
        "ROWS:",
        len(d),
    )

    print(
        "FROM:",
        d["date"].min().date(),
    )

    print(
        "TO  :",
        d["date"].max().date(),
    )

    print("\n[PHASE CAP ACTIVITY]")

    print(
        "CAP ACTIVE DAYS:",
        len(active),
    )

    print(
        "ACTIVE RATE:",
        f"{len(active) / len(d):.1%}",
    )

    print(
        "AVG EXPOSURE CUT:",
        round(
            active[
                "exposure_cut"
            ].mean(),
            3,
        ),
        "%p",
    )

    summary_rows = []

    for h in [1, 5, 20]:

        ret_col = (
            f"spy_fwd_{h}d"
        )

        outcome_col = (
            f"outcome_{h}d"
        )

        effect_col = (
            f"cap_opportunity_effect_{h}d"
        )

        valid = active[
            active[ret_col].notna()
        ].copy()

        defensive = int(
            (
                valid[outcome_col]
                == "DEFENSIVE_SUCCESS"
            ).sum()
        )

        opportunity = int(
            (
                valid[outcome_col]
                == "OPPORTUNITY_COST"
            ).sum()
        )

        total = len(valid)

        defensive_rate = (
            defensive / total
            if total
            else np.nan
        )

        opportunity_rate = (
            opportunity / total
            if total
            else np.nan
        )

        avg_fwd = (
            valid[ret_col].mean()
            if total
            else np.nan
        )

        avg_effect = (
            valid[effect_col].mean()
            if total
            else np.nan
        )

        print(
            f"\n[T+{h} TRADING DAYS]"
        )

        print(
            "VALID DAYS:",
            total,
        )

        print(
            "DEFENSIVE SUCCESS:",
            defensive,
            (
                f"({defensive_rate:.1%})"
                if total
                else ""
            ),
        )

        print(
            "OPPORTUNITY COST :",
            opportunity,
            (
                f"({opportunity_rate:.1%})"
                if total
                else ""
            ),
        )

        print(
            "AVG SPY FWD RETURN:",
            (
                f"{avg_fwd:.3%}"
                if pd.notna(avg_fwd)
                else "N/A"
            ),
        )

        print(
            "AVG CAP EFFECT:",
            (
                f"{avg_effect:.3%}"
                if pd.notna(avg_effect)
                else "N/A"
            ),
        )

        summary_rows.append(
            {
                "horizon_trading_days": h,
                "valid_days": total,
                "defensive_success_days":
                    defensive,
                "defensive_success_rate":
                    defensive_rate,
                "opportunity_cost_days":
                    opportunity,
                "opportunity_cost_rate":
                    opportunity_rate,
                "avg_spy_forward_return":
                    avg_fwd,
                "avg_cap_opportunity_effect":
                    avg_effect,
            }
        )

    # --------------------------------------------------------
    # 8. Regime breakdown
    # --------------------------------------------------------

    print(
        "\n=== REGIME × CAP EFFECTIVENESS "
        "(T+20) ==="
    )

    regime = (
        active[
            active[
                "spy_fwd_20d"
            ].notna()
        ]
        .groupby(
            [
                "market_regime",
                "phase_cap",
            ],
            dropna=False,
        )
        .agg(
            days=(
                "date",
                "count",
            ),
            avg_exposure_cut=(
                "exposure_cut",
                "mean",
            ),
            avg_spy_fwd_20d=(
                "spy_fwd_20d",
                "mean",
            ),
            avg_cap_effect_20d=(
                "cap_opportunity_effect_20d",
                "mean",
            ),
        )
        .sort_values(
            "days",
            ascending=False,
        )
    )

    print(
        regime.to_string()
    )

    # --------------------------------------------------------
    # 9. Largest opportunity costs
    # --------------------------------------------------------

    print(
        "\n=== TOP 15 POSSIBLE "
        "OPPORTUNITY-COST DAYS (T+20) ==="
    )

    cols = [
        "date",
        "market_regime",
        "macro_narrative",
        "pre_cap_budget",
        "phase_cap",
        "phase_cap_effect",
        "final_budget",
        "SPY",
        "spy_fwd_20d",
        "cap_opportunity_effect_20d",
    ]

    top_cost = (
        active[
            active[
                "spy_fwd_20d"
            ].notna()
        ]
        .sort_values(
            "cap_opportunity_effect_20d",
            ascending=False,
        )
        .head(15)
    )

    print(
        top_cost[
            cols
        ].to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # 10. Largest defensive successes
    # --------------------------------------------------------

    print(
        "\n=== TOP 15 POSSIBLE "
        "DEFENSIVE-SUCCESS DAYS (T+20) ==="
    )

    top_defense = (
        active[
            active[
                "spy_fwd_20d"
            ].notna()
        ]
        .sort_values(
            "cap_opportunity_effect_20d",
            ascending=True,
        )
        .head(15)
    )

    print(
        top_defense[
            cols
        ].to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_DAILY.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    active.to_csv(
        OUTPUT_DAILY,
        index=False,
    )

    summary_df = pd.DataFrame(
        summary_rows
    )

    summary_df.to_csv(
        OUTPUT_SUMMARY,
        index=False,
    )

    print(
        f"\n[SAVED] {OUTPUT_DAILY}"
    )

    print(
        f"[SAVED] {OUTPUT_SUMMARY}"
    )

    print(
        "\nPHASE CAP EFFECTIVENESS "
        "AUDIT COMPLETE."
    )

    print(
        "Forward returns were used "
        "for ex-post evaluation only."
    )


if __name__ == "__main__":
    main()