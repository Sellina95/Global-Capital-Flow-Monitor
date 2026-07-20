from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"

INPUT = RESULTS / "filter13_budget_attribution_final_daily.csv"
OUTPUT = RESULTS / "filter13_hard_riskoff_oneday_audit.csv"


def is_hard(regime):
    return str(regime).upper().startswith("HARD RISK-OFF")


def classify_trigger(row):
    regime = str(row.get("market_regime", "")).upper()
    macro = str(row.get("macro_narrative", "")).upper()

    if macro == "CREDIT_STRESS":
        return "CREDIT_STRESS"

    if (
        "STAGFLATION" in macro
        or "INFLATION SHOCK" in regime
    ):
        return "STAGFLATION_OR_INFLATION_SHOCK"

    if macro == "TIGHTENING_GROWTH_SCARE":
        return "GROWTH_SCARE_VIX"

    return "OTHER"


def main():

    d = pd.read_csv(INPUT)
    d["date"] = pd.to_datetime(d["date"])

    rows = []

    for i in range(len(d)):

        row = d.iloc[i]

        if not is_hard(row.get("market_regime")):
            continue

        prev_hard = (
            i > 0
            and is_hard(
                d.iloc[i - 1].get("market_regime")
            )
        )

        next_hard = (
            i + 1 < len(d)
            and is_hard(
                d.iloc[i + 1].get("market_regime")
            )
        )

        # 정확히 하루만 HARD였던 경우
        if prev_hard or next_hard:
            continue

        next_row = (
            d.iloc[i + 1]
            if i + 1 < len(d)
            else None
        )

        rows.append({

            "date":
                row["date"].strftime("%Y-%m-%d"),

            "trigger":
                classify_trigger(row),

            "hard_regime":
                row.get("market_regime"),

            "hard_macro":
                row.get("macro_narrative"),

            "hard_hy_oas":
                row.get("hy_oas_today"),

            "hard_base_budget":
                row.get("base_budget"),

            "hard_pre_cap_budget":
                row.get("pre_cap_budget"),

            "hard_phase_cap":
                row.get("phase_cap"),

            "hard_phase_cut":
                row.get("phase_cap_effect"),

            "hard_final_budget":
                row.get("final_budget"),

            # 다음 거래일
            "next_date":
                (
                    next_row["date"].strftime("%Y-%m-%d")
                    if next_row is not None
                    else None
                ),

            "next_regime":
                (
                    next_row.get("market_regime")
                    if next_row is not None
                    else None
                ),

            "next_macro":
                (
                    next_row.get("macro_narrative")
                    if next_row is not None
                    else None
                ),

            "next_hy_oas":
                (
                    next_row.get("hy_oas_today")
                    if next_row is not None
                    else None
                ),

            "next_phase_cap":
                (
                    next_row.get("phase_cap")
                    if next_row is not None
                    else None
                ),

            "next_final_budget":
                (
                    next_row.get("final_budget")
                    if next_row is not None
                    else None
                ),

            # 무엇이 다음날 바뀌었는지
            "macro_changed":
                (
                    row.get("macro_narrative")
                    != next_row.get("macro_narrative")
                    if next_row is not None
                    else None
                ),

            "regime_changed":
                (
                    row.get("market_regime")
                    != next_row.get("market_regime")
                    if next_row is not None
                    else None
                ),
        })

    out = pd.DataFrame(rows)

    out.to_csv(
        OUTPUT,
        index=False,
    )

    print(
        "\n=== FILTER13 ONE-DAY HARD RISK-OFF AUDIT ==="
    )

    print("\n[COUNT]")
    print(
        "ONE-DAY HARD:",
        len(out),
    )

    if out.empty:
        print("NONE")
        return

    print("\n=== TRIGGER DISTRIBUTION ===")

    print(
        out["trigger"]
        .value_counts()
        .to_string()
    )

    print(
        "\n=== WHAT HAPPENED NEXT TRADING DAY ==="
    )

    print(
        out["next_regime"]
        .value_counts(dropna=False)
        .to_string()
    )

    print(
        "\n=== MACRO NEXT DAY ==="
    )

    print(
        out[
            [
                "trigger",
                "hard_macro",
                "next_macro",
            ]
        ]
        .value_counts(dropna=False)
        .to_string()
    )

    print(
        "\n=== ONE-DAY HARD DETAIL ==="
    )

    cols = [
        "date",
        "trigger",
        "hard_regime",
        "hard_macro",
        "hard_hy_oas",
        "hard_pre_cap_budget",
        "hard_phase_cut",
        "hard_final_budget",
        "next_date",
        "next_regime",
        "next_macro",
        "next_hy_oas",
        "next_final_budget",
    ]

    print(
        out[cols]
        .to_string(index=False)
    )

    print(
        "\n=== BUDGET SNAPBACK ==="
    )

    print(
        "AVG HARD FINAL:",
        round(
            pd.to_numeric(
                out["hard_final_budget"],
                errors="coerce",
            ).mean(),
            3,
        ),
    )

    print(
        "AVG NEXT FINAL:",
        round(
            pd.to_numeric(
                out["next_final_budget"],
                errors="coerce",
            ).mean(),
            3,
        ),
    )

    print(
        "\n[SAVED]",
        OUTPUT,
    )

    print(
        "\nAUDIT COMPLETE."
    )

    print(
        "This audit diagnoses one-day HARD regime instability only."
    )

    print(
        "Do NOT modify production Filter13 from this result alone."
    )


if __name__ == "__main__":
    main()