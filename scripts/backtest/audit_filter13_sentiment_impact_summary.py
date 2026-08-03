from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

BASE_AUDIT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter13_budget_attribution_final_daily.csv"
)

SENTIMENT_AUDIT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter13_sentiment_direction_audit.csv"
)


def main():

    base = pd.read_csv(BASE_AUDIT)
    sent = pd.read_csv(SENTIMENT_AUDIT)


    print("=" * 70)
    print("FILTER13 SENTIMENT IMPACT SUMMARY")
    print("=" * 70)


    print("\n[BASE AUDIT]")
    print("Rows:", len(base))

    print(
        "Average Base Budget:",
        base["base_budget"].mean()
        if "base_budget" in base.columns
        else "N/A"
    )

    print(
        "Average Final Budget:",
        base["final_budget"].mean()
        if "final_budget" in base.columns
        else "N/A"
    )


    print("\n[SENTIMENT DIRECTION]")
    print(
        "Current Base:",
        sent["current_budget"].mean()
    )

    print(
        "Corrected Base:",
        sent["inverted_budget"].mean()
    )


    delta = (
        sent["inverted_budget"].mean()
        -
        sent["current_budget"].mean()
    )

    print(
        "\nSentiment Direction Impact:",
        round(delta, 2)
    )


    if "final_budget" in base.columns:

        final = base["final_budget"].mean()

        estimated_corrected = final + delta

        print(
            "\nEstimated Final Budget after sentiment correction:",
            round(estimated_corrected, 2)
        )

        print(
            "Estimated Final Change:",
            round(delta, 2)
        )


    print("\nDONE")


if __name__ == "__main__":
    main()