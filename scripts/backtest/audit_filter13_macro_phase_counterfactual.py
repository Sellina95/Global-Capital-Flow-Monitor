from pathlib import Path
import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter13_budget_attribution_final_daily.csv"
)

OUTPUT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter13_macro_phase_counterfactual.csv"
)


# ============================================================
# Main
# ============================================================

def main():

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT}"
        )

    df = pd.read_csv(INPUT)

    required = [
        "date",
        "pit_status",
        "macro_delta",
        "pre_cap_budget",
        "phase_cap",
        "phase_cap_effect",
        "final_budget",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Missing required columns: {missing}"
        )

    d = df.copy()

    # --------------------------------------------------------
    # Gate
    # --------------------------------------------------------

    valid_status = {"PASS", "FIRST_ROW"}

    bad = d[
        ~d["pit_status"].isin(valid_status)
    ]

    if not bad.empty:
        raise RuntimeError(
            "PIT gate failed. "
            "Counterfactual audit aborted."
        )

    # ========================================================
    # A. CURRENT
    #
    # 실제 현재 13번:
    # Macro adjustment + Phase Cap
    # ========================================================

    d["A_current"] = d["final_budget"]

    # ========================================================
    # B. PHASE ONLY
    #
    # Macro delta를 되돌린다.
    # 그 후 동일 Phase Cap은 유지한다.
    #
    # 현재:
    # pre_cap_budget = (... + macro_delta ...)
    #
    # 따라서:
    # no_macro_pre_cap
    # = pre_cap_budget - macro_delta
    # ========================================================

    d["B_no_macro_pre_cap"] = (
        d["pre_cap_budget"]
        - d["macro_delta"]
    )

    d["B_phase_only"] = d[
        [
            "B_no_macro_pre_cap",
            "phase_cap",
        ]
    ].min(axis=1)

    # ========================================================
    # C. MACRO ONLY
    #
    # Macro adjustment는 유지.
    # Phase Cap만 제거.
    #
    # 즉 pre_cap_budget 자체가 결과.
    # ========================================================

    d["C_macro_only"] = (
        d["pre_cap_budget"]
    )

    # ========================================================
    # Differences vs Current
    # ========================================================

    d["B_lift_vs_current"] = (
        d["B_phase_only"]
        - d["A_current"]
    )

    d["C_lift_vs_current"] = (
        d["C_macro_only"]
        - d["A_current"]
    )

    # ========================================================
    # Overlap flag
    # ========================================================

    d["macro_phase_overlap"] = (
        (d["macro_delta"] < 0)
        & (d["phase_cap_effect"] < 0)
    )

    # ========================================================
    # Summary
    # ========================================================

    print(
        "\n=== FILTER13 MACRO × PHASE "
        "COUNTERFACTUAL AUDIT ==="
    )

    print("\n[PERIOD]")
    print("ROWS :", len(d))
    print("FROM :", d["date"].iloc[0])
    print("TO   :", d["date"].iloc[-1])

    print("\n[AVERAGE BUDGET]")

    print(
        "A CURRENT (Macro + Phase):",
        round(
            d["A_current"].mean(),
            3,
        ),
    )

    print(
        "B PHASE ONLY             :",
        round(
            d["B_phase_only"].mean(),
            3,
        ),
    )

    print(
        "C MACRO ONLY             :",
        round(
            d["C_macro_only"].mean(),
            3,
        ),
    )

    print("\n[AVERAGE LIFT VS CURRENT]")

    print(
        "Remove Macro, keep Phase :",
        round(
            d["B_lift_vs_current"].mean(),
            3,
        ),
    )

    print(
        "Keep Macro, remove Phase :",
        round(
            d["C_lift_vs_current"].mean(),
            3,
        ),
    )

    print("\n[20% EXPOSURE DAYS]")

    print(
        "A CURRENT    :",
        int(
            (d["A_current"] <= 20).sum()
        ),
    )

    print(
        "B PHASE ONLY :",
        int(
            (d["B_phase_only"] <= 20).sum()
        ),
    )

    print(
        "C MACRO ONLY :",
        int(
            (d["C_macro_only"] <= 20).sum()
        ),
    )

    # ========================================================
    # Overlap subset
    # ========================================================

    overlap = d[
        d["macro_phase_overlap"]
    ].copy()

    print("\n[MACRO × PHASE OVERLAP]")

    print(
        "OVERLAP DAYS:",
        len(overlap),
    )

    if not overlap.empty:

        print(
            "CURRENT AVG:",
            round(
                overlap[
                    "A_current"
                ].mean(),
                3,
            ),
        )

        print(
            "PHASE ONLY AVG:",
            round(
                overlap[
                    "B_phase_only"
                ].mean(),
                3,
            ),
        )

        print(
            "MACRO ONLY AVG:",
            round(
                overlap[
                    "C_macro_only"
                ].mean(),
                3,
            ),
        )

        print(
            "\nAVG LIFT IF MACRO REMOVED:",
            round(
                overlap[
                    "B_lift_vs_current"
                ].mean(),
                3,
            ),
        )

        print(
            "AVG LIFT IF PHASE REMOVED:",
            round(
                overlap[
                    "C_lift_vs_current"
                ].mean(),
                3,
            ),
        )

    # ========================================================
    # Largest differences
    # ========================================================

    show_cols = [
        "date",
        "macro_delta",
        "pre_cap_budget",
        "phase_cap",
        "phase_cap_effect",
        "A_current",
        "B_phase_only",
        "C_macro_only",
        "B_lift_vs_current",
        "C_lift_vs_current",
    ]

    print(
        "\n[TOP 20 DAYS WHERE PHASE CAP "
        "REDUCED EXPOSURE MOST]"
    )

    top_phase = (
        d.sort_values(
            "C_lift_vs_current",
            ascending=False,
        )
        .head(20)
    )

    print(
        top_phase[
            show_cols
        ].to_string(
            index=False
        )
    )

    # ========================================================
    # Save
    # ========================================================

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    d.to_csv(
        OUTPUT,
        index=False,
    )

    print(
        f"\n[SAVED] {OUTPUT}"
    )

    print(
        "\nCOUNTERFACTUAL AUDIT COMPLETE."
    )

    print(
        "No production code was modified."
    )


if __name__ == "__main__":
    main()