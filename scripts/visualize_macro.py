import os
import pandas as pd
import matplotlib.pyplot as plt

# ===== 1. 경로 설정 =====
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
INSIGHTS_DIR = os.path.join(BASE_DIR, "insights")
CSV_PATH = os.path.join(DATA_DIR, "macro_data.csv")

os.makedirs(INSIGHTS_DIR, exist_ok=True)


# ===== 2. 데이터 로드 =====
def load_macro_data():
    if not os.path.isfile(CSV_PATH):
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH, parse_dates=["datetime"])
    df = df.sort_values("datetime")
    df.set_index("datetime", inplace=True)
    return df


# ===== 3. 시각화 함수 =====
def plot_macro_timeseries():
    df = load_macro_data()

    indicators = ["US10Y", "DXY", "WTI", "VIX", "USDKRW"]
    df = df[indicators]

    fig, axes = plt.subplots(len(indicators), 1, figsize=(10, 12), sharex=True)
    fig.suptitle("Global Macro Indicators Over Time", fontsize=16)

    for ax, col in zip(axes, indicators):
        ax.plot(df.index, df[col], marker="o", linewidth=1)
        ax.set_ylabel(col)
        ax.grid(True, linestyle="--", alpha=0.3)

    axes[-1].set_xlabel("Date / Time")
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    out_path = os.path.join(INSIGHTS_DIR, "macro_timeseries.png")
    plt.savefig(out_path, dpi=200)
    plt.close(fig)

    print(f"✅ Saved chart to {out_path}")


if __name__ == "__main__":
    plot_macro_timeseries()



