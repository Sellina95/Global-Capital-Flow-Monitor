# scripts/visualize_macro.py

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

DATA_PATH = Path("data") / "macro_data.csv"
OUT_PATH = Path("insights") / "macro_timeseries.png"


def load_data():
    # 1) CSV 읽기 (일단 그냥)
    df = pd.read_csv(DATA_PATH)

    # 2) 어떤 컬럼이 날짜인지 안전하게 처리
    #    우선 'date'가 있으면 그걸 사용하고,
    #    없으면 첫 번째 컬럼을 날짜로 간주해서 'date'로 이름 바꿔줌.
    if "date" in df.columns:
        date_col = "date"
    else:
        # 첫 번째 컬럼 이름
        first_col = df.columns[0]
        df.rename(columns={first_col: "date"}, inplace=True)
        date_col = "date"

    # 3) 날짜 형식으로 변환
    df[date_col] = pd.to_datetime(df[date_col])

    # 4) 날짜 기준 정렬 + 인덱스로 설정
    df = df.sort_values(date_col)
    df.set_index(date_col, inplace=True)

    return df


def plot_with_risk_levels(df: pd.DataFrame):
    plt.style.use("default")

    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    fig.suptitle("Global Macro Signals with Risk Levels", fontsize=16)

    # 1) US10Y
    ax = axes[0, 0]
    if "US10Y" in df.columns:
        ax.plot(df.index, df["US10Y"], label="US10Y (%)")
        ax.set_title("US 10Y Yield")
        ax.set_ylabel("%")
        ax.axhline(4.5, linestyle="--", linewidth=1, label="4.5% (주의)")
        ax.axhline(5.0, linestyle="--", linewidth=1, label="5.0% (경고)")
        ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 2) DXY
    ax = axes[0, 1]
    if "DXY" in df.columns:
        ax.plot(df.index, df["DXY"], label="DXY")
        ax.set_title("DXY (Dollar Index)")
        ax.axhline(102, linestyle="--", linewidth=1, label="102 (주의)")
        ax.axhline(105, linestyle="--", linewidth=1, label="105 (경고)")
        ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 3) WTI
    ax = axes[1, 0]
    if "WTI" in df.columns:
        ax.plot(df.index, df["WTI"], label="WTI ($)")
        ax.set_title("WTI Crude Oil")
        ax.set_ylabel("$")
        ax.axhline(90, linestyle="--", linewidth=1, label="90$ (주의)")
        ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 4) VIX
    ax = axes[1, 1]
    if "VIX" in df.columns:
        ax.plot(df.index, df["VIX"], label="VIX")
        ax.set_title("VIX (Volatility Index)")
        ax.axhline(20, linestyle="--", linewidth=1, label="20 (주의)")
        ax.axhline(25, linestyle="--", linewidth=1, label="25 (경고)")
        ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 5) USDKRW
    ax = axes[2, 0]
    if "USDKRW" in df.columns:
        ax.plot(df.index, df["USDKRW"], label="USD/KRW")
        ax.set_title("USD/KRW")
        ax.set_ylabel("KRW")
        ax.axhline(1350, linestyle="--", linewidth=1, label="1350 (주의)")
        ax.axhline(1400, linestyle="--", linewidth=1, label="1400 (경고)")
        ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # 6) 설명 박스
    ax = axes[2, 1]
    ax.axis("off")
    txt = [
        "Risk Levels (예시 기준선)",
        "- US10Y ≥ 4.5%: 밸류에이션 부담 구간",
        "- US10Y ≥ 5.0%: 채권·주식 동시 변동성 확대 가능",
        "- DXY ≥ 105: 달러 강세, EM/원화 압력",
        "- VIX ≥ 20/25: 변동성 경계 / 위험 구간",
        "- USDKRW ≥ 1350/1400: 원화 약세 심화",
        "- WTI ≥ 90$: 인플레·원가 부담 재부각"
    ]
    ax.text(
        0.0, 0.9,
        "\n".join(txt),
        transform=ax.transAxes,
        fontsize=9,
        va="top"
    )

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, dpi=150)
    plt.close()
    print(f"Saved chart with risk levels to: {OUT_PATH}")


if __name__ == "__main__":
    df = load_data()
    plot_with_risk_levels(df)
