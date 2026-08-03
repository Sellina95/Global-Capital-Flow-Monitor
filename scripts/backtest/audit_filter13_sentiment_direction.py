from __future__ import annotations

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

SENTIMENT_FILE = ROOT / "data" / "backtest" / "sentiment_proxy.csv"


def sentiment_state(value):
    if value is None:
        return "N/A"

    if value < 30:
        return "FEAR"

    if value > 70:
        return "GREED"

    return "NEUTRAL"


def base_budget(state):
    if state == "FEAR":
        return 35

    if state == "GREED":
        return 70

    if state == "NEUTRAL":
        return 55

    return 50


def main():

    df = pd.read_csv(SENTIMENT_FILE)

    # 현재 방식
    df["current_state"] = (
        df["sentiment_proxy"]
        .apply(sentiment_state)
    )

    df["current_budget"] = (
        df["current_state"]
        .apply(base_budget)
    )


    # 방향 반전
    # Stress Score → Fear & Greed Score 변환
    df["inverted_sentiment"] = (
        100 - df["sentiment_proxy"]
    )


    df["inverted_state"] = (
        df["inverted_sentiment"]
        .apply(sentiment_state)
    )


    df["inverted_budget"] = (
        df["inverted_state"]
        .apply(base_budget)
    )


    print("=" * 70)
    print("FILTER13 SENTIMENT DIRECTION COUNTERFACTUAL")
    print("=" * 70)


    print("\nCURRENT")
    print(df["current_state"].value_counts())
    print(
        "Average Base Budget:",
        round(df["current_budget"].mean(), 2)
    )


    print("\nINVERTED")
    print(df["inverted_state"].value_counts())
    print(
        "Average Base Budget:",
        round(df["inverted_budget"].mean(), 2)
    )


    print("\nBUDGET CHANGE")
    print(
        round(
            df["inverted_budget"].mean()
            -
            df["current_budget"].mean(),
            2
        )
    )


    out = ROOT / "data/backtest/results/filter13_sentiment_direction_audit.csv"

    df.to_csv(
        out,
        index=False
    )

    print("\nSaved:", out)


if __name__ == "__main__":
    main()