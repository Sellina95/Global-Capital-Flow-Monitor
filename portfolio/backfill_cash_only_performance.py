## 포트폴리오 비어있느날짜있을경우 사용하는 파일 
import os
import pandas as pd
import yfinance as yf

PERF_PATH = "data/paper_portfolio_performance.csv"
TARGET_DATES = ["2026-05-08", "2026-05-09"]


def fetch_spy_return_for_date(target_date: str) -> float:
    """
    target_date가 실제 거래일이면 전 거래일 종가 대비 SPY 수익률 계산.
    비거래일이면 0.0으로 처리.
    """
    target = pd.to_datetime(target_date)

    start = (target - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    end = (target + pd.Timedelta(days=2)).strftime("%Y-%m-%d")

    df = yf.download(
        "SPY",
        start=start,
        end=end,
        interval="1d",
        progress=False,
        auto_adjust=False,
        threads=False,
    )

    if df is None or df.empty or "Close" not in df.columns:
        return 0.0

    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.squeeze()

    close = pd.to_numeric(close, errors="coerce").dropna()
    close.index = pd.to_datetime(close.index).normalize()

    # 비거래일이면 0 처리
    if target.normalize() not in close.index:
        return 0.0

    pos = list(close.index).index(target.normalize())
    if pos == 0:
        return 0.0

    prev_close = float(close.iloc[pos - 1])
    today_close = float(close.iloc[pos])

    if prev_close == 0:
        return 0.0

    return round(((today_close - prev_close) / prev_close) * 100.0, 4)


def backfill():
    if not os.path.exists(PERF_PATH):
        raise FileNotFoundError(f"{PERF_PATH} not found")

    df = pd.read_csv(PERF_PATH)
    df["date"] = df["date"].astype(str)

    for d in TARGET_DATES:
        benchmark = fetch_spy_return_for_date(d)

        row = {col: "" for col in df.columns}
        row["date"] = d
        row["portfolio_return_pct"] = 0.0
        row["benchmark_return_pct"] = benchmark
        row["alpha_vs_spy_pct"] = round(0.0 - benchmark, 4)
        row["cash_weight"] = 100.0
        row["contrib_CASH"] = 0.0
        row["trade_cost_impact_pct"] = 0.0
        row["net_portfolio_return_pct"] = 0.0
        row["net_alpha_vs_spy_pct"] = round(0.0 - benchmark, 4)

        # 기존 해당 날짜 제거 후 새 row 삽입
        df = df[df["date"] != d].copy()
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

        print(f"✅ Backfilled {d}: SPY={benchmark:.4f}%, Portfolio=0.0000%")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    df.to_csv(PERF_PATH, index=False)
    print(f"✅ Saved: {PERF_PATH}")


if __name__ == "__main__":
    backfill()
