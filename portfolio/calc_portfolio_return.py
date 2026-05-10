import os
from typing import Dict, Tuple, Optional

import pandas as pd
import yfinance as yf


PORTFOLIO_LOG_PATH = "data/paper_portfolio_log.csv"
OUTPUT_PATH = "data/paper_portfolio_performance.csv"
TRADE_LOG_PATH = "data/trade_log.csv"


def is_non_trading_calendar_day(date_str: str) -> bool:
    return pd.to_datetime(date_str).weekday() >= 5


def load_latest_portfolio(filepath: str = PORTFOLIO_LOG_PATH) -> Optional[pd.Series]:
    if not os.path.exists(filepath):
        print(f"❌ Portfolio log not found: {filepath}")
        return None

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"❌ Failed to read portfolio log: {e}")
        return None

    if df.empty or "date" not in df.columns:
        print("❌ Portfolio log empty or date column missing")
        return None

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    if df.empty:
        print("❌ No valid dated rows in portfolio log")
        return None

    return df.iloc[-1]


def extract_ticker_weights(portfolio_row: pd.Series) -> Tuple[Dict[str, float], float]:
    reserved_cols = {
        "date",
        "CASH",
        "cash_weight",
        "Cash",
        "total_exposure",
        "recommended_exposure",
    }

    ticker_weights: Dict[str, float] = {}

    for col, val in portfolio_row.items():
        if col in reserved_cols:
            continue
        if pd.isna(val):
            continue

        try:
            weight = float(val)
        except Exception:
            continue

        if weight > 0:
            ticker_weights[col] = weight

    cash_raw = (
        portfolio_row.get("CASH", None)
        if "CASH" in portfolio_row.index
        else portfolio_row.get("cash_weight", 0.0)
    )

    try:
        cash_weight = float(0.0 if pd.isna(cash_raw) else cash_raw)
    except Exception:
        cash_weight = 0.0

    return ticker_weights, cash_weight


def fetch_return_for_date(ticker: str, portfolio_date: str) -> float:
    """
    portfolio_date 기준 1D 수익률 계산.
    주말/휴장일이면 0.
    """
    target = pd.to_datetime(portfolio_date).normalize()

    if target.weekday() >= 5:
        return 0.0

    start = (target - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
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

        if df is None or df.empty or "Close" not in df.columns:
            print(f"⚠️ No close data for {ticker} on {portfolio_date}")
            return 0.0

        close = df["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.squeeze()

        close = pd.to_numeric(close, errors="coerce").dropna()
        close.index = pd.to_datetime(close.index).normalize()
        close = close.sort_index()

        # 해당 날짜가 실제 거래일이 아니면 0
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

    except Exception as e:
        print(f"⚠️ Return fetch failed for {ticker} on {portfolio_date}: {e}")
        return 0.0


def calculate_portfolio_return(
    ticker_weights: Dict[str, float],
    cash_weight: float,
    portfolio_date: str,
) -> Dict[str, float]:
    ticker_returns: Dict[str, float] = {}
    weighted_contribs: Dict[str, float] = {}

    portfolio_return = 0.0

    if is_non_trading_calendar_day(portfolio_date):
        for ticker in ticker_weights:
            ticker_returns[ticker] = 0.0
            weighted_contribs[ticker] = 0.0

        weighted_contribs["CASH"] = 0.0

        return {
            "portfolio_return_pct": 0.0,
            "cash_weight": round(cash_weight, 2),
            "ticker_returns": ticker_returns,
            "weighted_contribs": weighted_contribs,
        }

    for ticker, weight in ticker_weights.items():
        ret_pct = fetch_return_for_date(ticker, portfolio_date)
        ticker_returns[ticker] = ret_pct

        contrib = round((weight / 100.0) * ret_pct, 4)
        weighted_contribs[ticker] = contrib
        portfolio_return += contrib

    weighted_contribs["CASH"] = 0.0

    return {
        "portfolio_return_pct": round(portfolio_return, 4),
        "cash_weight": round(cash_weight, 2),
        "ticker_returns": ticker_returns,
        "weighted_contribs": weighted_contribs,
    }


def fetch_benchmark_return(portfolio_date: str, ticker: str = "SPY") -> float:
    return fetch_return_for_date(ticker, portfolio_date)


def load_trade_cost_for_date(
    portfolio_date: str,
    filepath: str = TRADE_LOG_PATH,
) -> float:
    if is_non_trading_calendar_day(portfolio_date):
        return 0.0

    if not os.path.exists(filepath):
        return 0.0

    try:
        df = pd.read_csv(filepath)
    except Exception:
        return 0.0

    if df.empty or "date" not in df.columns:
        return 0.0

    if "trade_cost_impact_pct" not in df.columns:
        return 0.0

    df["date"] = df["date"].astype(str)
    day_df = df[df["date"] == portfolio_date].copy()

    if day_df.empty:
        return 0.0

    total_cost = pd.to_numeric(
        day_df["trade_cost_impact_pct"], errors="coerce"
    ).fillna(0).sum()

    return round(float(total_cost), 4)


def save_performance_row(
    portfolio_date: str,
    ticker_weights: Dict[str, float],
    result: Dict[str, float],
    benchmark_return: float,
    trade_cost_impact: float,
    net_portfolio_return: float,
    net_alpha_vs_spy: float,
    output_path: str = OUTPUT_PATH,
) -> None:
    row = {
        "date": portfolio_date,
        "portfolio_return_pct": result["portfolio_return_pct"],
        "benchmark_return_pct": benchmark_return,
        "alpha_vs_spy_pct": round(result["portfolio_return_pct"] - benchmark_return, 4),
        "cash_weight": result["cash_weight"],
        "trade_cost_impact_pct": trade_cost_impact,
        "net_portfolio_return_pct": net_portfolio_return,
        "net_alpha_vs_spy_pct": net_alpha_vs_spy,
    }

    for ticker, weight in ticker_weights.items():
        row[f"w_{ticker}"] = round(weight, 2)

    for ticker, ret in result["ticker_returns"].items():
        row[f"r_{ticker}"] = round(ret, 4)

    for ticker, contrib in result["weighted_contribs"].items():
        row[f"contrib_{ticker}"] = round(contrib, 4)

    if "contrib_CASH" not in row:
        row["contrib_CASH"] = 0.0

    new_df = pd.DataFrame([row])

    if os.path.exists(output_path):
        try:
            old_df = pd.read_csv(output_path)
        except Exception:
            old_df = pd.DataFrame()

        if not old_df.empty and "date" in old_df.columns:
            old_df["date"] = old_df["date"].astype(str)
            old_df = old_df[old_df["date"] != portfolio_date].copy()

        out_df = pd.concat([old_df, new_df], ignore_index=True)
    else:
        out_df = new_df

    if "date" in out_df.columns:
        out_df["date"] = pd.to_datetime(out_df["date"], errors="coerce")
        out_df = out_df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        out_df["date"] = out_df["date"].dt.strftime("%Y-%m-%d")

    os.makedirs("data", exist_ok=True)
    out_df.to_csv(output_path, index=False)

    print(f"✅ Performance saved/updated: {portfolio_date}")
    print(f"✅ File path: {output_path}")


def print_summary(
    result: Dict[str, float],
    benchmark_return: float,
    trade_cost_impact: float,
    net_portfolio_return: float,
    net_alpha_vs_spy: float,
) -> None:
    print("")
    print("=== Portfolio Return Summary ===")
    print(f"Portfolio 1D Return: {result['portfolio_return_pct']:.4f}%")
    print(f"SPY 1D Return: {benchmark_return:.4f}%")
    print(f"Alpha vs SPY: {result['portfolio_return_pct'] - benchmark_return:.4f}%")
    print(f"Trade Cost Impact: -{trade_cost_impact:.4f}%")
    print(f"Net Portfolio Return: {net_portfolio_return:.4f}%")
    print(f"Net Alpha vs SPY: {net_alpha_vs_spy:.4f}%")
    print("")


def main() -> None:
    latest_row = load_latest_portfolio()
    if latest_row is None:
        return

    portfolio_date = pd.to_datetime(latest_row["date"]).strftime("%Y-%m-%d")
    ticker_weights, cash_weight = extract_ticker_weights(latest_row)

    print(f"📌 Portfolio date: {portfolio_date}")
    print(f"📌 Cash weight: {cash_weight:.2f}%")

    if is_non_trading_calendar_day(portfolio_date):
        print("🛑 Weekend detected: returns and trade cost forced to 0")

    if not ticker_weights and cash_weight < 99.0:
        print("⚠️ No ETF weights found and cash is not 100%")
        print(f"cash_weight={cash_weight:.2f}%")
        return

    if not ticker_weights:
        print("🛡️ CASH-ONLY / DEADMAN portfolio detected")
        print("📌 ETF weights: none")
    else:
        print(f"📌 ETF weights: {ticker_weights}")

    result = calculate_portfolio_return(
        ticker_weights=ticker_weights,
        cash_weight=cash_weight,
        portfolio_date=portfolio_date,
    )

    benchmark_return = fetch_benchmark_return(portfolio_date, "SPY")
    trade_cost_impact = load_trade_cost_for_date(portfolio_date)

    net_portfolio_return = round(result["portfolio_return_pct"] - trade_cost_impact, 4)
    net_alpha_vs_spy = round(net_portfolio_return - benchmark_return, 4)

    print_summary(
        result=result,
        benchmark_return=benchmark_return,
        trade_cost_impact=trade_cost_impact,
        net_portfolio_return=net_portfolio_return,
        net_alpha_vs_spy=net_alpha_vs_spy,
    )

    if ticker_weights:
        print("=== ETF Returns ===")
        for ticker, ret in result["ticker_returns"].items():
            print(f"{ticker}: {ret:.4f}%")

        print("")
        print("=== Weighted Contributions ===")
        for ticker, contrib in result["weighted_contribs"].items():
            print(f"{ticker}: {contrib:.4f}%")

    save_performance_row(
        portfolio_date=portfolio_date,
        ticker_weights=ticker_weights,
        result=result,
        benchmark_return=benchmark_return,
        trade_cost_impact=trade_cost_impact,
        net_portfolio_return=net_portfolio_return,
        net_alpha_vs_spy=net_alpha_vs_spy,
    )


if __name__ == "__main__":
    main()
