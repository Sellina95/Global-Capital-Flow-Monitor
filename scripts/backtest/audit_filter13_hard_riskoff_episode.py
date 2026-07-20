from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[2]

ATTR_PATH = (
    ROOT
    / "data/backtest/results/filter13_budget_attribution_final_daily.csv"
)

MACRO_PATH = (
    ROOT
    / "data/backtest/macro_data.csv"
)

OUT_DIR = ROOT / "data/backtest/results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DAILY_OUT = OUT_DIR / "filter13_hard_riskoff_episode_daily.csv"
SUMMARY_OUT = OUT_DIR / "filter13_hard_riskoff_episode_summary.csv"


def main():

    # ============================================================
    # 1. Load verified Filter13 attribution
    # ============================================================

    d = pd.read_csv(ATTR_PATH)
    m = pd.read_csv(MACRO_PATH)

    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    m["date"] = pd.to_datetime(m["date"], errors="coerce")

    d = (
        d.dropna(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )

    m = (
        m.dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates("date")
        .reset_index(drop=True)
    )

    if "SPY" not in m.columns:
        raise RuntimeError("SPY column missing from macro_data.csv")

    m["SPY"] = pd.to_numeric(m["SPY"], errors="coerce")

    # Exact-date merge only.
    # No backward fill / forward fill -> future leakage 방지.
    d = d.merge(
        m[["date", "SPY"]],
        on="date",
        how="left",
    )

    # ============================================================
    # 2. Identify HARD RISK-OFF
    #
    # Includes:
    # - HARD RISK-OFF
    # - HARD RISK-OFF / INFLATION SHOCK
    #
    # 하지만 subtype은 따로 저장해서 나중에 구분한다.
    # ============================================================

    regime = (
        d["market_regime"]
        .fillna("")
        .astype(str)
        .str.upper()
    )

    d["is_hard_riskoff"] = regime.str.startswith(
        "HARD RISK-OFF"
    )

    d["hard_subtype"] = np.where(
        regime.str.contains("INFLATION SHOCK", regex=False),
        "INFLATION_SHOCK",
        np.where(
            d["is_hard_riskoff"],
            "PLAIN_HARD",
            "NOT_HARD",
        ),
    )

    # ============================================================
    # 3. Build consecutive HARD episodes
    # ============================================================

    episode_ids = []
    current_episode = 0
    prev_hard = False

    for is_hard in d["is_hard_riskoff"]:

        if is_hard and not prev_hard:
            current_episode += 1

        episode_ids.append(
            current_episode if is_hard else np.nan
        )

        prev_hard = bool(is_hard)

    d["episode_id"] = episode_ids

    # ============================================================
    # 4. Forward SPY prices / returns
    #
    # Ex-post evaluation ONLY.
    # These values never enter the Filter13 signal.
    # ============================================================

    for h in [1, 5, 10, 20]:

        d[f"spy_fwd_{h}d"] = (
            d["SPY"].shift(-h) / d["SPY"] - 1.0
        )

    # ============================================================
    # 5. Episode analysis
    # ============================================================

    summaries = []

    hard = d[d["is_hard_riskoff"]].copy()

    for episode_id, ep in hard.groupby("episode_id"):

        ep = ep.sort_values("date")

        start_idx = ep.index.min()
        end_idx = ep.index.max()

        start_date = ep.iloc[0]["date"]
        end_date = ep.iloc[-1]["date"]

        start_spy = ep.iloc[0]["SPY"]
        end_spy = ep.iloc[-1]["SPY"]

        duration = len(ep)

        # --------------------------------------------------------
        # Episode return while HARD remained active
        # --------------------------------------------------------

        if pd.notna(start_spy) and pd.notna(end_spy):
            episode_return = (
                end_spy / start_spy - 1.0
            )
        else:
            episode_return = np.nan

        # --------------------------------------------------------
        # Max drawdown from HARD entry during episode
        # --------------------------------------------------------

        ep_prices = ep["SPY"].dropna()

        if (
            len(ep_prices) > 0
            and pd.notna(start_spy)
            and start_spy != 0
        ):
            returns_from_entry = (
                ep_prices / start_spy - 1.0
            )

            max_drawdown_from_entry = (
                returns_from_entry.min()
            )

            max_rally_from_entry = (
                returns_from_entry.max()
            )

        else:
            max_drawdown_from_entry = np.nan
            max_rally_from_entry = np.nan

        # --------------------------------------------------------
        # Exit information
        # First trading day AFTER HARD episode
        # --------------------------------------------------------

        exit_idx = end_idx + 1

        if exit_idx < len(d):

            exit_date = d.loc[exit_idx, "date"]
            exit_regime = d.loc[
                exit_idx,
                "market_regime",
            ]

            exit_spy = d.loc[exit_idx, "SPY"]

        else:

            exit_date = pd.NaT
            exit_regime = None
            exit_spy = np.nan

        # --------------------------------------------------------
        # Returns after entry
        # --------------------------------------------------------

        entry_fwd_5 = ep.iloc[0]["spy_fwd_5d"]
        entry_fwd_10 = ep.iloc[0]["spy_fwd_10d"]
        entry_fwd_20 = ep.iloc[0]["spy_fwd_20d"]

        # --------------------------------------------------------
        # Returns after exit
        #
        # Important for detecting late exit / missed re-risking.
        # --------------------------------------------------------

        if exit_idx < len(d):

            exit_fwd_5 = d.loc[
                exit_idx,
                "spy_fwd_5d",
            ]

            exit_fwd_10 = d.loc[
                exit_idx,
                "spy_fwd_10d",
            ]

            exit_fwd_20 = d.loc[
                exit_idx,
                "spy_fwd_20d",
            ]

        else:

            exit_fwd_5 = np.nan
            exit_fwd_10 = np.nan
            exit_fwd_20 = np.nan

        # --------------------------------------------------------
        # Opportunity cost inside HARD episode
        #
        # Positive SPY movement while exposure was capped
        # is potential missed upside.
        # This is descriptive, not causal proof.
        # --------------------------------------------------------

        avg_phase_cut = (
            pd.to_numeric(
                ep["phase_cap_effect"],
                errors="coerce",
            ).mean()
        )

        avg_final_budget = (
            pd.to_numeric(
                ep["final_budget"],
                errors="coerce",
            ).mean()
        )

        avg_pre_cap_budget = (
            pd.to_numeric(
                ep["pre_cap_budget"],
                errors="coerce",
            ).mean()
        )

        # --------------------------------------------------------
        # Simple diagnostic classification
        #
        # NOT a production decision rule.
        # Audit label only.
        #
        # FALSE_ENTRY_CANDIDATE:
        # little/no downside after entry + strong rebound
        #
        # VALID_DEFENSE:
        # meaningful downside after entry
        #
        # LATE_EXIT_CANDIDATE:
        # downside happened, but market recovered strongly
        # by/around exit or immediately afterward
        # --------------------------------------------------------

        diagnosis = "MIXED_REVIEW"

        if pd.notna(max_drawdown_from_entry):

            if (
                max_drawdown_from_entry > -0.02
                and pd.notna(entry_fwd_20)
                and entry_fwd_20 > 0.03
            ):
                diagnosis = "FALSE_ENTRY_CANDIDATE"

            elif max_drawdown_from_entry <= -0.05:

                diagnosis = "VALID_DEFENSE"

                if (
                    pd.notna(exit_fwd_10)
                    and exit_fwd_10 > 0.03
                ):
                    diagnosis = (
                        "VALID_DEFENSE_WITH_REENTRY_RISK"
                    )

        summaries.append(
            {
                "episode_id":
                    int(episode_id),

                "start_date":
                    start_date,

                "end_date":
                    end_date,

                "duration_days":
                    duration,

                "subtypes":
                    " | ".join(
                        sorted(
                            ep[
                                "hard_subtype"
                            ]
                            .dropna()
                            .unique()
                        )
                    ),

                "entry_regime":
                    ep.iloc[0][
                        "market_regime"
                    ],

                "entry_macro":
                    ep.iloc[0][
                        "macro_narrative"
                    ],

                "exit_date":
                    exit_date,

                "exit_regime":
                    exit_regime,

                "start_spy":
                    start_spy,

                "end_spy":
                    end_spy,

                "episode_return":
                    episode_return,

                "max_drawdown_from_entry":
                    max_drawdown_from_entry,

                "max_rally_from_entry":
                    max_rally_from_entry,

                "entry_fwd_5d":
                    entry_fwd_5,

                "entry_fwd_10d":
                    entry_fwd_10,

                "entry_fwd_20d":
                    entry_fwd_20,

                "exit_fwd_5d":
                    exit_fwd_5,

                "exit_fwd_10d":
                    exit_fwd_10,

                "exit_fwd_20d":
                    exit_fwd_20,

                "avg_pre_cap_budget":
                    avg_pre_cap_budget,

                "avg_phase_cap_effect":
                    avg_phase_cut,

                "avg_final_budget":
                    avg_final_budget,

                "diagnosis":
                    diagnosis,
            }
        )

    summary = pd.DataFrame(summaries)

    # ============================================================
    # 6. Save
    # ============================================================

    hard.to_csv(
        DAILY_OUT,
        index=False,
    )

    summary.to_csv(
        SUMMARY_OUT,
        index=False,
    )

    # ============================================================
    # 7. Print institutional-style audit
    # ============================================================

    print(
        "\n=== FILTER13 HARD RISK-OFF "
        "ENTRY / PERSISTENCE / EXIT AUDIT ==="
    )

    print("\n[PERIOD]")
    print("ROWS:", len(d))
    print(
        "FROM:",
        d["date"].min().date()
    )
    print(
        "TO  :",
        d["date"].max().date()
    )

    print("\n[HARD RISK-OFF]")
    print(
        "HARD DAYS:",
        int(d["is_hard_riskoff"].sum())
    )
    print(
        "EPISODES :",
        len(summary)
    )

    if not summary.empty:

        print("\n=== EPISODE SUMMARY ===")

        show_cols = [
            "episode_id",
            "start_date",
            "end_date",
            "duration_days",
            "subtypes",
            "entry_macro",
            "episode_return",
            "max_drawdown_from_entry",
            "entry_fwd_20d",
            "exit_date",
            "exit_regime",
            "exit_fwd_10d",
            "avg_phase_cap_effect",
            "avg_final_budget",
            "diagnosis",
        ]

        print(
            summary[
                show_cols
            ].to_string(
                index=False
            )
        )

        print(
            "\n=== DIAGNOSIS COUNTS ==="
        )

        print(
            summary[
                "diagnosis"
            ].value_counts(
                dropna=False
            ).to_string()
        )

        print(
            "\n=== POSSIBLE FALSE ENTRY ==="
        )

        false_entry = summary[
            summary["diagnosis"]
            == "FALSE_ENTRY_CANDIDATE"
        ]

        if false_entry.empty:
            print("NONE")
        else:
            print(
                false_entry[
                    show_cols
                ].to_string(
                    index=False
                )
            )

        print(
            "\n=== POSSIBLE RE-ENTRY / EXIT ISSUE ==="
        )

        reentry = summary[
            summary["diagnosis"]
            == "VALID_DEFENSE_WITH_REENTRY_RISK"
        ]

        if reentry.empty:
            print("NONE")
        else:
            print(
                reentry[
                    show_cols
                ].to_string(
                    index=False
                )
            )

    print("\n[SAVED]", DAILY_OUT)
    print("[SAVED]", SUMMARY_OUT)

    print(
        "\nAUDIT COMPLETE."
    )

    print(
        "Forward returns are EX-POST evaluation only."
    )

    print(
        "Do NOT modify Filter13 until episode results are reviewed."
    )


if __name__ == "__main__":
    main()