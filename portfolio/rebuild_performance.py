import os
from typing import Dict, Optional

import pandas as pd
import yfinance as yf


PORTFOLIO_LOG_PATH = "data/paper_portfolio_log.csv"
TRADE_LOG_PATH = "data/trade_log.csv"
OUTPUT_PATH = "data/paper_portfolio_performance.csv"


META_COLS = {"date", "CASH", "total_exposure"}


def fetch_return_for_date(ticker: str, target_date: str) -> float:
    target = pd.to_datetime(target_date).normalize()

    start = (target - pd.Timedelta(days=7)).strftime("%Y-%m-%d")
    end = (target + pd.Timedelta(days=2)).strftime("%Y-%m-%d")

    df = yf.download(
        ticker,
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

    # 주말/휴장일이면 수익률 0
    if target not in close.index:
        return 0.0

    pos = list(close.index).index(target)
    if pos == 0:
        return 0.0

    prev_close = float(close.iloc[pos - 1])
    today_close = float(close.iloc[pos])

    if prev_close == 0:
        return 0.0

    return round(((today_close - prev_close) / prev_close) * 100.0, 4)


def load_trade_cost_for_date(date: str) -> float:
    if not os.path.exists(TRADE_LOG_PATH):
        return 0.0

    df = pd.read_csv(TRADE_LOG_PATH)

    if df.empty or "date" not in df.columns:
        return 0.0

    if "trade_cost_impact_pct" not in df.columns:
        return 0.0

    df["date"] = df["date"].astype(str)
    day_df = df[df["date"] == date].copy()

    if day_df.empty:
        return 0.0

    return round(
        pd.to_numeric(day_df["trade_cost_impact_pct"], errors="coerce")
        .fillna(0.0)
        .sum(),
        4,
    )


def extract_weights(row: pd.Series) -> Dict[str, float]:
    weights = {}

    for col, val in row.items():
        if col in META_COLS:
            continue
        if pd.isna(val):
            continue

        try:
            w = float(val)
        except Exception:
            continue

        if w > 0:
            weights[col] = w

    return weights


def rebuild() -> None:
    if not os.path.exists(PORTFOLIO_LOG_PATH):
        raise FileNotFoundError(f"{PORTFOLIO_LOG_PATH} not found")

    pf = pd.read_csv(PORTFOLIO_LOG_PATH)

    if pf.empty or "date" not in pf.columns:
        raise ValueError("paper_portfolio_log.csv is empty or missing date column")

    pf["date"] = pd.to_datetime(pf["date"], errors="coerce")
    pf = pf.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    pf["date"] = pf["date"].dt.strftime("%Y-%m-%d")

    rows = []

    for _, row in pf.iterrows():
        date = str(row["date"])

        weights = extract_weights(row)

        try:
            cash_weight = float(row.get("CASH", 0.0) or 0.0)
        except Exception:
            cash_weight = 0.0

        portfolio_return = 0.0
        ticker_returns = {}
        contribs = {}

        for ticker, weight in weights.items():
            ret = fetch_return_for_date(ticker, date)
            ticker_returns[ticker] = ret

            contrib = round((weight / 100.0) * ret, 4)
            contribs[ticker] = contrib
            portfolio_return += contrib

        portfolio_return = round(portfolio_return, 4)

        benchmark_return = fetch_return_for_date("SPY", date)
        alpha = round(portfolio_return - benchmark_return, 4)

        trade_cost = load_trade_cost_for_date(date)
        net_return = round(portfolio_return - trade_cost, 4)
        net_alpha = round(net_return - benchmark_return, 4)

        out = {
            "date": date,
            "portfolio_return_pct": portfolio_return,
            "benchmark_return_pct": benchmark_return,
            "alpha_vs_spy_pct": alpha,
            "cash_weight": round(cash_weight, 2),
            "trade_cost_impact_pct": trade_cost,
            "net_portfolio_return_pct": net_return,
            "net_alpha_vs_spy_pct": net_alpha,
        }

        for ticker, weight in weights.items():
            out[f"w_{ticker}"] = round(weight, 2)

        for ticker, ret in ticker_returns.items():
            out[f"r_{ticker}"] = round(ret, 4)

        for ticker, contrib in contribs.items():
            out[f"contrib_{ticker}"] = round(contrib, 4)

        out["contrib_CASH"] = 0.0

        rows.append(out)

        print(
            f"✅ {date} | port={portfolio_return:.4f}% | "
            f"SPY={benchmark_return:.4f}% | net={net_return:.4f}%"
        )

    out_df = pd.DataFrame(rows)
    out_df = out_df.sort_values("date").reset_index(drop=True)

    os.makedirs("data", exist_ok=True)
    out_df.to_csv(OUTPUT_PATH, index=False)

    print(f"✅ Rebuilt performance file: {OUTPUT_PATH}")


if __name__ == "__main__":
    rebuild()
