from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

ATTR_PATH = (
    ROOT
    / "data/backtest/results/filter13_budget_attribution_final_daily.csv"
)

MACRO_PATH = (
    ROOT
    / "data/backtest/macro_data.csv"
)

OUT_DAILY = (
    ROOT
    / "data/backtest/results/filter13_cap45_effectiveness_daily.csv"
)

OUT_SUMMARY = (
    ROOT
    / "data/backtest/results/filter13_cap45_effectiveness_summary.csv"
)


def main():

    # ==================================================
    # 1. Load PIT-safe Filter13 attribution
    # ==================================================

    d = pd.read_csv(ATTR_PATH)

    d["date"] = pd.to_datetime(
        d["date"],
        errors="coerce",
    )

    d = d.dropna(
        subset=["date"]
    ).copy()

    if "pit_status" in d.columns:

        d = d[
            d["pit_status"].isin(
                ["PASS", "FIRST_ROW"]
            )
        ].copy()

    # ==================================================
    # 2. Load SPY
    # ==================================================

    px = pd.read_csv(
        MACRO_PATH,
        usecols=["date", "SPY"],
    )

    px["date"] = pd.to_datetime(
        px["date"],
        errors="coerce",
    )

    px["SPY"] = pd.to_numeric(
        px["SPY"],
        errors="coerce",
    )

    px = (
        px
        .dropna(
            subset=["date", "SPY"]
        )
        .sort_values("date")
        .drop_duplicates(
            "date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------
    # Trading-day forward returns
    #
    # IMPORTANT:
    # Ex-post evaluation ONLY.
    # Filter13 signal generation에는 사용하지 않는다.
    # --------------------------------------------------

    for h in [1, 5, 20]:

        px[f"spy_fwd_{h}d"] = (
            px["SPY"].shift(-h)
            / px["SPY"]
            - 1
        )

    # ==================================================
    # 3. Merge
    # ==================================================

    x = d.merge(
        px[
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
    )

    # ==================================================
    # 4. Isolate Phase Cap = 45
    # ==================================================

    x = x[
        x["phase_cap"] == 45
    ].copy()

    x["cap_binding"] = (
        x["phase_cap_effect"] < 0
    )

    x["exposure_removed"] = (
        -x["phase_cap_effect"].clip(
            upper=0
        )
    )

    # ==================================================
    # 5. Counterfactual exposure lift
    #
    # Current:
    #   final_budget
    #
    # Counterfactual:
    #   Phase 45 cap이 binding하지 않았다면
    #   pre-cap exposure를 유지했다고 가정.
    #
    # 이것은 정책 변경안이 아니라
    # attribution diagnostic이다.
    # ==================================================

    x["cf_exposure_lift"] = (
        x["pre_cap_budget"]
        - x["final_budget"]
    ).clip(lower=0)

    # ==================================================
    # 6. Ex-post effectiveness
    #
    # cap_effect > 0
    #   → exposure를 줄여 손실을 방어
    #
    # cap_effect < 0
    #   → exposure를 줄여 상승을 놓침
    # ==================================================

    for h in [1, 5, 20]:

        ret_col = (
            f"spy_fwd_{h}d"
        )

        effect_col = (
            f"cap_effect_{h}d"
        )

        diag_col = (
            f"diagnosis_{h}d"
        )

        x[effect_col] = (
            -(
                x["cf_exposure_lift"]
                / 100.0
            )
            * x[ret_col]
        )

        x[diag_col] = (
            "NO_EFFECT"
        )

        valid = (
            (x["cf_exposure_lift"] > 0)
            & x[ret_col].notna()
        )

        x.loc[
            valid
            & (x[ret_col] < 0),
            diag_col,
        ] = "DEFENSIVE_SUCCESS"

        x.loc[
            valid
            & (x[ret_col] > 0),
            diag_col,
        ] = "OPPORTUNITY_COST"

    # ==================================================
    # 7. Basic Activity
    # ==================================================

    binding = x[
        x["cap_binding"]
    ].copy()

    print(
        "\n=== FILTER13 CAP45 EFFECTIVENESS AUDIT ==="
    )

    print(
        "\n[PERIOD]"
    )

    print(
        "CAP45 DAYS:",
        len(x),
    )

    if not x.empty:

        print(
            "FROM:",
            x["date"]
            .min()
            .strftime("%Y-%m-%d"),
        )

        print(
            "TO  :",
            x["date"]
            .max()
            .strftime("%Y-%m-%d"),
        )

    print(
        "\n[CAP45 ACTIVITY]"
    )

    print(
        "CAP45 DAYS:",
        len(x),
    )

    print(
        "BINDING DAYS:",
        len(binding),
    )

    if len(x):

        print(
            "BINDING RATE:",
            round(
                100
                * len(binding)
                / len(x),
                1,
            ),
            "%",
        )

    if len(binding):

        print(
            "AVG EXPOSURE REMOVED:",
            round(
                binding[
                    "exposure_removed"
                ].mean(),
                3,
            ),
            "%p",
        )

        print(
            "TOTAL EXPOSURE REMOVED:",
            round(
                binding[
                    "exposure_removed"
                ].sum(),
                3,
            ),
            "%p-days",
        )

    # ==================================================
    # 8. Horizon Evaluation
    # ==================================================

    summary_rows = []

    for h in [1, 5, 20]:

        ret_col = (
            f"spy_fwd_{h}d"
        )

        effect_col = (
            f"cap_effect_{h}d"
        )

        diag_col = (
            f"diagnosis_{h}d"
        )

        z = binding[
            binding[
                ret_col
            ].notna()
        ].copy()

        defensive = int(
            (
                z[diag_col]
                == "DEFENSIVE_SUCCESS"
            ).sum()
        )

        opportunity = int(
            (
                z[diag_col]
                == "OPPORTUNITY_COST"
            ).sum()
        )

        print(
            f"\n[T+{h} TRADING DAYS]"
        )

        print(
            "VALID BINDING DAYS:",
            len(z),
        )

        if len(z):

            print(
                "DEFENSIVE SUCCESS:",
                defensive,
                f"({100 * defensive / len(z):.1f}%)",
            )

            print(
                "OPPORTUNITY COST :",
                opportunity,
                f"({100 * opportunity / len(z):.1f}%)",
            )

            print(
                "AVG SPY FWD RETURN:",
                f"{100 * z[ret_col].mean():.3f}%",
            )

            print(
                "AVG CAP EFFECT:",
                f"{100 * z[effect_col].mean():.3f}%",
            )

            print(
                "TOTAL CAP EFFECT:",
                f"{100 * z[effect_col].sum():.3f}%",
            )

        summary_rows.append(
            {
                "horizon_days": h,

                "cap45_days":
                    len(x),

                "binding_days":
                    len(binding),

                "valid_binding_days":
                    len(z),

                "defensive_success_days":
                    defensive,

                "opportunity_cost_days":
                    opportunity,

                "avg_exposure_removed":
                    (
                        binding[
                            "exposure_removed"
                        ].mean()
                        if len(binding)
                        else 0
                    ),

                "total_exposure_removed":
                    (
                        binding[
                            "exposure_removed"
                        ].sum()
                        if len(binding)
                        else 0
                    ),

                "avg_spy_forward_return":
                    (
                        z[
                            ret_col
                        ].mean()
                        if len(z)
                        else None
                    ),

                "avg_cap_effect":
                    (
                        z[
                            effect_col
                        ].mean()
                        if len(z)
                        else None
                    ),

                "total_cap_effect":
                    (
                        z[
                            effect_col
                        ].sum()
                        if len(z)
                        else None
                    ),
            }
        )

    # ==================================================
    # 9. Regime-specific effectiveness
    # ==================================================

    print(
        "\n=== CAP45 REGIME EFFECTIVENESS T+20 ==="
    )

    valid20 = binding[
        binding[
            "spy_fwd_20d"
        ].notna()
    ].copy()

    if not valid20.empty:

        regime_summary = (
            valid20
            .groupby(
                [
                    "market_regime",
                    "macro_narrative",
                ],
                dropna=False,
            )
            .agg(
                days=(
                    "date",
                    "count",
                ),

                avg_exposure_removed=(
                    "exposure_removed",
                    "mean",
                ),

                avg_spy_fwd_20d=(
                    "spy_fwd_20d",
                    "mean",
                ),

                avg_cap_effect_20d=(
                    "cap_effect_20d",
                    "mean",
                ),
            )
            .reset_index()
            .sort_values(
                "days",
                ascending=False,
            )
        )

        print(
            regime_summary
            .to_string(
                index=False
            )
        )

    # ==================================================
    # 10. Daily Detail
    # ==================================================

    cols = [
        "date",
        "market_regime",
        "macro_narrative",
        "struct_v2_state",
        "base_budget",
        "macro_delta",
        "pre_cap_budget",
        "phase_cap",
        "phase_cap_effect",
        "final_budget",
        "spy_fwd_1d",
        "spy_fwd_5d",
        "spy_fwd_20d",
        "cap_effect_20d",
        "diagnosis_20d",
    ]

    cols = [
        c
        for c in cols
        if c in x.columns
    ]

    print(
        "\n=== CAP45 BINDING DAILY DETAIL ==="
    )

    if len(binding):

        print(
            binding[
                cols
            ]
            .sort_values(
                "date"
            )
            .to_string(
                index=False
            )
        )

    # ==================================================
    # 11. Biggest Opportunity Costs
    # ==================================================

    print(
        "\n=== TOP CAP45 OPPORTUNITY-COST DAYS T+20 ==="
    )

    if not valid20.empty:

        print(
            valid20
            .sort_values(
                "cap_effect_20d",
                ascending=True,
            )
            [cols]
            .head(15)
            .to_string(
                index=False
            )
        )

    # ==================================================
    # 12. Biggest Defensive Success
    # ==================================================

    print(
        "\n=== TOP CAP45 DEFENSIVE-SUCCESS DAYS T+20 ==="
    )

    if not valid20.empty:

        print(
            valid20
            .sort_values(
                "cap_effect_20d",
                ascending=False,
            )
            [cols]
            .head(15)
            .to_string(
                index=False
            )
        )

    # ==================================================
    # 13. Save
    # ==================================================

    OUT_DAILY.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    x.to_csv(
        OUT_DAILY,
        index=False,
    )

    pd.DataFrame(
        summary_rows
    ).to_csv(
        OUT_SUMMARY,
        index=False,
    )

    print(
        "\n[SAVED]",
        OUT_DAILY,
    )

    print(
        "[SAVED]",
        OUT_SUMMARY,
    )

    print(
        "\nCAP45 AUDIT COMPLETE."
    )

    print(
        "Forward returns are EX-POST evaluation only."
    )

    print(
        "No production Filter13 logic was modified."
    )


if __name__ == "__main__":
    main()