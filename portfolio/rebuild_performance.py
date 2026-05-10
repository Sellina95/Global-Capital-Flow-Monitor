import os
from typing import Dict, Optional

import pandas as pd
import yfinance as yf


PORTFOLIO_LOG_PATH = "data/paper_portfolio_log.csv"
TRADE_LOG_PATH = "data/trade_log.csv"
OUTPUT_PATH = "data/paper_portfolio_performance.csv"

META_COLS = {"date", "CASH", "total_exposure"}


def is_weekend(date_str: str) -> bool:
    return pd.to_datetime(date_str).weekday() >= 5


def get_latest_completed_market_date(ticker: str = "SPY") -> Optional[str]:
    try:
        df = yf.download(
            ticker,
            period="14d",
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False,
        )
    except Exception as e:
        print(f"❌ Failed to fetch latest market date: {e}")
        return None

    if df is None or df.empty:
        return None

    df = df.dropna(how="all")
    if df.empty:
        return None

    return pd.to_datetime(df.index[-1]).strftime("%Y-%m-%d")


def fetch_return_for_date(ticker: str, target_date: str) -> float:
    """
    date=T 기준:
    T-1 close → T close 수익률.
    단, 주말/휴장일이면 0.
    """
    target = pd.to_datetime(target_date).normalize()

    if target.weekday() >= 5:
        return 0.0

    start = (target - pd.Timedelta(days=15)).strftime("%Y-%m-%d")
    end = (target + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        df = yf.download(
            ticker,
            start=start,
            end=end,
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False,
        )
    except Exception as e:
        print(f"⚠️ Return fetch failed for {ticker} on {target_date}: {e}")
        return 0.0

    if df is None or df.empty or "Close" not in df.columns:
        return 0.0

    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.squeeze()

    close = pd.to_numeric(close, errors="coerce").dropna()
    if close.empty:
        return 0.0

    close.index = pd.to_datetime(close.index).normalize()
    close = close.sort_index()

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
    if is_weekend(date):
        return 0.0

    if not os.path.exists(TRADE_LOG_PATH):
        return 0.0

    try:
        df = pd.read_csv(TRADE_LOG_PATH)
    except Exception:
        return 0.0

    if df.empty or "date" not in df.columns:
        return 0.0

    if "trade_cost_impact_pct" not in df.columns:
        return 0.0

    df["date"] = df["date"].astype(str)
    day_df = df[df["date"] == str(date)].copy()

    if day_df.empty:
        return 0.0

    return round(
        pd.to_numeric(day_df["trade_cost_impact_pct"], errors="coerce")
        .fillna(0.0)
        .sum(),
        4,
    )


def extract_weights(row: pd.Series) -> Dict[str, float]:
    weights: Dict[str, float] = {}

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
    latest_market_date = get_latest_completed_market_date("SPY")
    if latest_market_date is None:
        raise RuntimeError("Could not determine latest completed market date")

    latest_market_ts = pd.to_datetime(latest_market_date)

    if not os.path.exists(PORTFOLIO_LOG_PATH):
        raise FileNotFoundError(f"{PORTFOLIO_LOG_PATH} not found")

    pf = pd.read_csv(PORTFOLIO_LOG_PATH)

    if pf.empty or "date" not in pf.columns:
        raise ValueError("paper_portfolio_log.csv is empty or missing date column")

    pf["date"] = pd.to_datetime(pf["date"], errors="coerce")
    pf = pf.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # 아직 종가 확정 안 된 날짜는 제외
    pf = pf[pf["date"] <= latest_market_ts].copy()

    pf["date"] = pf["date"].dt.strftime("%Y-%m-%d")

    rows = []

    for _, row in pf.iterrows():
        date = str(row["date"])
        weekend = is_weekend(date)

        weights = extract_weights(row)

        try:
            cash_weight = float(row.get("CASH", 0.0) or 0.0)
        except Exception:
            cash_weight = 0.0

        portfolio_return = 0.0
        benchmark_return = 0.0
        ticker_returns: Dict[str, float] = {}
        contribs: Dict[str, float] = {}

        if weekend:
            for ticker in weights:
                ticker_returns[ticker] = 0.0
                contribs[ticker] = 0.0
        else:
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
            "contrib_CASH": 0.0,
        }

        for ticker, weight in weights.items():
            out[f"w_{ticker}"] = round(weight, 2)

        for ticker, ret in ticker_returns.items():
            out[f"r_{ticker}"] = round(ret, 4)

        for ticker, contrib in contribs.items():
            out[f"contrib_{ticker}"] = round(contrib, 4)

        rows.append(out)

        print(
            f"✅ {date} | weekend={weekend} | "
            f"port={portfolio_return:.4f}% | "
            f"SPY={benchmark_return:.4f}% | "
            f"cost={trade_cost:.4f}% | "
            f"net={net_return:.4f}%"
        )

    out_df = pd.DataFrame(rows)
    out_df = out_df.sort_values("date").reset_index(drop=True)

    os.makedirs("data", exist_ok=True)
    out_df.to_csv(OUTPUT_PATH, index=False)

    print(f"✅ Rebuilt performance file: {OUTPUT_PATH}")
    print(f"✅ Latest completed market date: {latest_market_date}")


if __name__ == "__main__":
    rebuild()