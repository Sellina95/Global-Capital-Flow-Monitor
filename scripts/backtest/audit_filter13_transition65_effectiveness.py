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
    / "data/backtest/results/filter13_transition65_effectiveness_daily.csv"
)

OUT_SUMMARY = (
    ROOT
    / "data/backtest/results/filter13_transition65_effectiveness_summary.csv"
)


def main():

    # --------------------------------------------------
    # 1. Load audited Filter13 attribution
    # --------------------------------------------------

    d = pd.read_csv(ATTR_PATH)
    d["date"] = pd.to_datetime(d["date"])

    # PIT PASS / FIRST_ROW only
    if "pit_status" in d.columns:
        d = d[
            d["pit_status"].isin(
                ["PASS", "FIRST_ROW"]
            )
        ].copy()

    # --------------------------------------------------
    # 2. Load SPY prices
    # --------------------------------------------------

    px = pd.read_csv(
        MACRO_PATH,
        usecols=["date", "SPY"],
    )

    px["date"] = pd.to_datetime(px["date"])
    px["SPY"] = pd.to_numeric(
        px["SPY"],
        errors="coerce",
    )

    px = (
        px
        .dropna(subset=["date", "SPY"])
        .sort_values("date")
        .drop_duplicates("date", keep="last")
        .reset_index(drop=True)
    )

    # Trading-day forward returns
    px["spy_fwd_1d"] = (
        px["SPY"].shift(-1) / px["SPY"] - 1
    )

    px["spy_fwd_5d"] = (
        px["SPY"].shift(-5) / px["SPY"] - 1
    )

    px["spy_fwd_20d"] = (
        px["SPY"].shift(-20) / px["SPY"] - 1
    )

    # --------------------------------------------------
    # 3. Merge
    # --------------------------------------------------

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

    # --------------------------------------------------
    # 4. Transition / Mixed + cap 65
    # --------------------------------------------------

    x = x[
        (x["market_regime"] == "TRANSITION / MIXED")
        & (x["phase_cap"] == 65)
    ].copy()

    # cap이 실제 노출을 잘랐는지
    x["cap_binding"] = (
        x["phase_cap_effect"] < 0
    )

    x["exposure_removed"] = (
        -x["phase_cap_effect"].clip(upper=0)
    )

    # --------------------------------------------------
    # 5. Counterfactual effect
    #
    # 현재: final_budget
    # CF : phase cap 65가 없었다면 pre_cap_budget
    #
    # 단순 exposure difference × future SPY return
    #
    # Forward return은 EX-POST 평가에만 사용.
    # --------------------------------------------------

    x["cf_exposure_lift"] = (
        x["pre_cap_budget"]
        - x["final_budget"]
    ).clip(lower=0)

    for h in [1, 5, 20]:

        ret_col = f"spy_fwd_{h}d"

        x[f"cap_effect_{h}d"] = (
            -(
                x["cf_exposure_lift"] / 100.0
            )
            * x[ret_col]
        )

        # 양수:
        # cap이 손실을 피하는 데 도움
        #
        # 음수:
        # cap 때문에 상승 수익을 놓침

        x[f"diagnosis_{h}d"] = "NO_EFFECT"

        mask = (
            x["cf_exposure_lift"] > 0
        ) & x[ret_col].notna()

        x.loc[
            mask & (x[ret_col] < 0),
            f"diagnosis_{h}d",
        ] = "DEFENSIVE_SUCCESS"

        x.loc[
            mask & (x[ret_col] > 0),
            f"diagnosis_{h}d",
        ] = "OPPORTUNITY_COST"

    # --------------------------------------------------
    # 6. Summary
    # --------------------------------------------------

    print(
        "\n=== FILTER13 TRANSITION CAP65 EFFECTIVENESS AUDIT ==="
    )

    print("\n[PERIOD]")
    print("ROWS:", len(x))

    if not x.empty:
        print(
            "FROM:",
            x["date"].min().strftime("%Y-%m-%d"),
        )
        print(
            "TO  :",
            x["date"].max().strftime("%Y-%m-%d"),
        )

    print("\n[CAP 65 ACTIVITY]")

    binding = x[x["cap_binding"]].copy()

    print("CAP65 DAYS:", len(x))
    print("BINDING DAYS:", len(binding))

    if len(x):
        print(
            "BINDING RATE:",
            round(
                100 * len(binding) / len(x),
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

    # --------------------------------------------------
    # Horizon evaluation
    # --------------------------------------------------

    summary_rows = []

    for h in [1, 5, 20]:

        ret_col = f"spy_fwd_{h}d"
        diag_col = f"diagnosis_{h}d"
        effect_col = f"cap_effect_{h}d"

        z = binding[
            binding[ret_col].notna()
        ].copy()

        defensive = (
            z[diag_col]
            == "DEFENSIVE_SUCCESS"
        ).sum()

        opportunity = (
            z[diag_col]
            == "OPPORTUNITY_COST"
        ).sum()

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
                f"({100*defensive/len(z):.1f}%)",
            )

            print(
                "OPPORTUNITY COST :",
                opportunity,
                f"({100*opportunity/len(z):.1f}%)",
            )

            print(
                "AVG SPY FWD RETURN:",
                f"{100*z[ret_col].mean():.3f}%",
            )

            print(
                "AVG CAP EFFECT:",
                f"{100*z[effect_col].mean():.3f}%",
            )

            print(
                "TOTAL CAP EFFECT:",
                f"{100*z[effect_col].sum():.3f}%",
            )

        summary_rows.append(
            {
                "horizon_days": h,
                "cap65_days": len(x),
                "binding_days": len(binding),
                "valid_days": len(z),
                "defensive_success_days":
                    defensive,
                "opportunity_cost_days":
                    opportunity,
                "avg_exposure_removed":
                    binding[
                        "exposure_removed"
                    ].mean()
                    if len(binding)
                    else 0,
                "avg_spy_forward_return":
                    z[ret_col].mean()
                    if len(z)
                    else None,
                "avg_cap_effect":
                    z[effect_col].mean()
                    if len(z)
                    else None,
                "total_cap_effect":
                    z[effect_col].sum()
                    if len(z)
                    else None,
            }
        )

    # --------------------------------------------------
    # 7. Biggest opportunity-cost / defensive days
    # --------------------------------------------------

    valid20 = binding[
        binding["spy_fwd_20d"].notna()
    ].copy()

    print(
        "\n=== TOP CAP65 OPPORTUNITY-COST DAYS (T+20) ==="
    )

    cols = [
        "date",
        "market_regime",
        "macro_narrative",
        "struct_v2_state",
        "base_budget",
        "pre_cap_budget",
        "phase_cap",
        "phase_cap_effect",
        "final_budget",
        "spy_fwd_20d",
        "cap_effect_20d",
    ]

    print(
        valid20
        .sort_values(
            "cap_effect_20d",
            ascending=True,
        )
        [cols]
        .head(15)
        .to_string(index=False)
    )

    print(
        "\n=== TOP CAP65 DEFENSIVE-SUCCESS DAYS (T+20) ==="
    )

    print(
        valid20
        .sort_values(
            "cap_effect_20d",
            ascending=False,
        )
        [cols]
        .head(15)
        .to_string(index=False)
    )

    # --------------------------------------------------
    # 8. Save
    # --------------------------------------------------

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
        "\nAUDIT COMPLETE."
    )

    print(
        "Forward returns are EX-POST evaluation only."
    )

    print(
        "No production Filter13 logic was modified."
    )


if __name__ == "__main__":
    main()