import os
from typing import Dict, Tuple, Optional

import pandas as pd
import yfinance as yf


PORTFOLIO_LOG_PATH = "data/paper_portfolio_log.csv"
OUTPUT_PATH = "data/paper_portfolio_performance.csv"


def load_latest_portfolio(filepath: str = PORTFOLIO_LOG_PATH) -> Optional[pd.Series]:
    """
    paper_portfolio_log.csv에서 가장 최근 포트폴리오 row를 가져온다.
    """
    if not os.path.exists(filepath):
        print(f"❌ Portfolio log not found: {filepath}")
        return None

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"❌ Failed to read portfolio log: {e}")
        return None

    if df.empty:
        print(f"❌ Portfolio log is empty: {filepath}")
        return None

    if "date" not in df.columns:
        print("❌ 'date' column missing in portfolio log")
        return None

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    if df.empty:
        print("❌ No valid dated rows in portfolio log")
        return None

    return df.iloc[-1]


def extract_ticker_weights(portfolio_row: pd.Series) -> Tuple[Dict[str, float], float]:
    """
    portfolio row에서 ETF 비중과 cash 비중을 분리한다.
    """
    reserved_cols = {"date", "CASH", "total_exposure"}
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

    cash_weight = float(portfolio_row.get("CASH", 0.0) or 0.0)
    return ticker_weights, cash_weight


def fetch_1d_return(ticker: str) -> Optional[float]:
    """
    최근 2개 종가를 가져와 1일 수익률(%) 계산
    """
    try:
        df = yf.download(
            ticker,
            period="5d",
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=False,
        )

        if df is None or df.empty:
            print(f"⚠️ No data for {ticker}")
            return None

        if "Close" not in df.columns:
            print(f"⚠️ Close column missing for {ticker}")
            return None

        close_series = df["Close"]
        if isinstance(close_series, pd.DataFrame):
            close_series = close_series.squeeze()

        close_series = pd.to_numeric(close_series, errors="coerce").dropna()

        if len(close_series) < 2:
            print(f"⚠️ Not enough close data for {ticker}")
            return None

        prev_close = float(close_series.iloc[-2])
        last_close = float(close_series.iloc[-1])

        if prev_close == 0:
            return None

        ret_pct = ((last_close - prev_close) / prev_close) * 100.0
        return float(ret_pct)

    except Exception as e:
        print(f"⚠️ Return fetch failed for {ticker}: {e}")
        return None


def calculate_portfolio_return(
    ticker_weights: Dict[str, float],
    cash_weight: float,
) -> Dict[str, float]:
    """
    ETF 비중과 현금 비중으로 포트폴리오 1일 수익률 계산
    - ETF 수익률: 최근 1일
    - Cash: 0%
    """
    ticker_returns: Dict[str, float] = {}
    weighted_contribs: Dict[str, float] = {}

    portfolio_return = 0.0

    for ticker, weight in ticker_weights.items():
        ret_pct = fetch_1d_return(ticker)

        if ret_pct is None:
            ret_pct = 0.0

        ticker_returns[ticker] = ret_pct

        # weight는 % 단위, ret_pct도 % 단위
        contrib = (weight / 100.0) * ret_pct
        weighted_contribs[ticker] = contrib
        portfolio_return += contrib

    weighted_contribs["CASH"] = 0.0

    return {
        "portfolio_return_pct": round(portfolio_return, 4),
        "cash_weight": round(cash_weight, 2),
        "ticker_returns": ticker_returns,
        "weighted_contribs": weighted_contribs,
    }


def fetch_benchmark_return(ticker: str = "SPY") -> float:
    """
    SPY 1일 수익률 계산
    """
    ret = fetch_1d_return(ticker)
    return round(ret if ret is not None else 0.0, 4)


def save_performance_row(
    portfolio_date: str,
    ticker_weights: Dict[str, float],
    result: Dict[str, float],
    benchmark_return: float,
    output_path: str = OUTPUT_PATH,
) -> None:
    """
    계산 결과를 performance CSV에 저장
    - 같은 portfolio_date가 이미 있으면 기존 row를 삭제하고 최신 값으로 덮어쓴다.
    """
    row = {
        "date": portfolio_date,
        "portfolio_return_pct": result["portfolio_return_pct"],
        "benchmark_return_pct": benchmark_return,
        "alpha_vs_spy_pct": round(result["portfolio_return_pct"] - benchmark_return, 4),
        "cash_weight": result["cash_weight"],
    }

    # ETF 비중 저장
    for ticker, weight in ticker_weights.items():
        row[f"w_{ticker}"] = round(weight, 2)

    # ETF 수익률 저장
    for ticker, ret in result["ticker_returns"].items():
        row[f"r_{ticker}"] = round(ret, 4)

    # ETF 기여도 저장
    for ticker, contrib in result["weighted_contribs"].items():
        row[f"contrib_{ticker}"] = round(contrib, 4)

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


def main() -> None:
    latest_row = load_latest_portfolio()
    if latest_row is None:
        return

    # ✅ 현재 시스템 기준:
    # paper_portfolio_log.csv의 날짜를 그대로 성과 CSV의 날짜로 사용
    portfolio_date = pd.to_datetime(latest_row["date"]).strftime("%Y-%m-%d")

    ticker_weights, cash_weight = extract_ticker_weights(latest_row)

    if not ticker_weights:
        print("⚠️ No ETF weights found in latest portfolio row")
        return

    print(f"📌 Portfolio date: {portfolio_date}")
    print(f"📌 ETF weights: {ticker_weights}")
    print(f"📌 Cash weight: {cash_weight:.2f}%")

    result = calculate_portfolio_return(ticker_weights, cash_weight)
    benchmark_return = fetch_benchmark_return("SPY")

    print("")
    print("=== Portfolio Return Summary ===")
    print(f"Portfolio 1D Return: {result['portfolio_return_pct']:.4f}%")
    print(f"SPY 1D Return: {benchmark_return:.4f}%")
    print(f"Alpha vs SPY: {result['portfolio_return_pct'] - benchmark_return:.4f}%")
    print("")

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
    )


if __name__ == "__main__":
    main()