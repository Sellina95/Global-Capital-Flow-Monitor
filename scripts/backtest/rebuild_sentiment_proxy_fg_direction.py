from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = ROOT / "data/backtest/sentiment_proxy.csv"
OUTPUT = ROOT / "data/backtest/sentiment_proxy_fg_direction.csv"


def main():

    df = pd.read_csv(INPUT)

    stress = pd.to_numeric(
        df["sentiment_proxy"],
        errors="coerce"
    )

    # -----------------------------
    # Stress Score -> Fear & Greed
    # -----------------------------
    # 기존:
    # low  = calm
    # high = stress
    #
    # 변환:
    # low  = fear
    # high = greed

    stress_min = stress.min()
    stress_max = stress.max()

    normalized = (
        (stress - stress_min)
        /
        (stress_max - stress_min)
        * 100
    )

    fg = 100 - normalized

    df["sentiment_proxy_original"] = stress
    df["sentiment_proxy"] = fg.clip(0,100)

    df["direction_fix"] = (
        "stress_to_fear_greed_rescaled"
    )

    df.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig"
    )

    print("Saved:", OUTPUT)

    print(df["sentiment_proxy"].describe())

    print(
        "FEAR:",
        (df["sentiment_proxy"] < 30).sum()
    )

    print(
        "NEUTRAL:",
        (
            (df["sentiment_proxy"] >= 30)
            &
            (df["sentiment_proxy"] <=70)
        ).sum()
    )

    print(
        "GREED:",
        (df["sentiment_proxy"] >70).sum()
    )


if __name__ == "__main__":
    main()