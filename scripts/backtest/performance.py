from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "backtest"
RESULT_DIR = DATA_DIR / "results"

POSITIONS_PATH = RESULT_DIR / "daily_positions.csv"
PRICE_PATH = DATA_DIR / "sector_prices.csv"
DAILY_PATH = RESULT_DIR / "daily_portfolio.csv"
SUMMARY_PATH = RESULT_DIR / "performance_summary.csv"

# 18번 섹터명 → 장기 운용 가능한 ETF
SECTOR_TO_ETF = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Consumer Discretionary": "XLY",
    "Health Care": "XLV",
    "Utilities": "XLU",
    "Consumer Staples": "XLP",
    "Materials": "XLB",
    "Communication Services": "VOX",
    "Real Estate": "IYR",
}

BENCHMARK = "SPY"
COST_BPS_ONE_WAY = 5.0
TRADING_DAYS = 252


def download_prices(start: str, end: str) -> pd.DataFrame:
    tickers = sorted(set(SECTOR_TO_ETF.values()) | {BENCHMARK})

    raw = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by="column",
        threads=True,
    )

    if raw.empty:
        raise RuntimeError("ETF 가격 다운로드 결과가 비어 있습니다.")

    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" not in raw.columns.get_level_values(0):
            raise RuntimeError("다운로드 데이터에 Close 컬럼이 없습니다.")
        close = raw["Close"].copy()
    else:
        close = raw[["Close"]].rename(columns={"Close": tickers[0]})

    close.index = pd.to_datetime(close.index).tz_localize(None)
    close.index.name = "date"
    close = close.sort_index()

    PRICE_PATH.parent.mkdir(parents=True, exist_ok=True)
    close.reset_index().to_csv(PRICE_PATH, index=False, encoding="utf-8-sig")

    return close


def load_or_download_prices(
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    # execution_date 수익률 계산에는 직전 거래일도 필요
    fetch_start = (start - pd.Timedelta(days=10)).strftime("%Y-%m-%d")
    fetch_end = (end + pd.Timedelta(days=5)).strftime("%Y-%m-%d")
    return download_prices(fetch_start, fetch_end)


def parse_weights(value: object) -> dict[str, float]:
    if pd.isna(value):
        return {}

    try:
        raw = json.loads(str(value))
    except Exception:
        return {}

    result: dict[str, float] = {}

    for sector, weight in raw.items():
        try:
            result[str(sector)] = float(weight) / 100.0
        except (TypeError, ValueError):
            continue

    return result


def max_drawdown(returns: pd.Series) -> float:
    wealth = (1.0 + returns.fillna(0.0)).cumprod()
    peak = wealth.cummax()
    drawdown = wealth / peak - 1.0
    return float(drawdown.min())


def annualized_return(returns: pd.Series) -> float:
    clean = returns.dropna()

    if clean.empty:
        return float("nan")

    total = float((1.0 + clean).prod())
    years = len(clean) / TRADING_DAYS

    if years <= 0 or total <= 0:
        return float("nan")

    return total ** (1.0 / years) - 1.0


def annualized_volatility(returns: pd.Series) -> float:
    clean = returns.dropna()

    if len(clean) < 2:
        return float("nan")

    return float(clean.std(ddof=1) * math.sqrt(TRADING_DAYS))


def sharpe_ratio(returns: pd.Series) -> float:
    clean = returns.dropna()

    if len(clean) < 2:
        return float("nan")

    vol = clean.std(ddof=1)
    if vol == 0:
        return float("nan")

    return float(clean.mean() / vol * math.sqrt(TRADING_DAYS))


def down_capture(
    strategy: pd.Series,
    benchmark: pd.Series,
) -> float:
    aligned = pd.concat(
        [strategy.rename("strategy"), benchmark.rename("benchmark")],
        axis=1,
    ).dropna()

    down = aligned[aligned["benchmark"] < 0]

    if down.empty or down["benchmark"].mean() == 0:
        return float("nan")

    return float(
        down["strategy"].mean() / down["benchmark"].mean()
    )


def main() -> None:
    positions = pd.read_csv(POSITIONS_PATH)

    required = {
        "signal_date",
        "execution_date",
        "cash_weight",
        "weights_json",
        "status",
    }
    missing = required - set(positions.columns)

    if missing:
        raise ValueError(f"daily_positions missing columns: {sorted(missing)}")

    positions["signal_date"] = pd.to_datetime(
        positions["signal_date"],
        errors="coerce",
    )
    positions["execution_date"] = pd.to_datetime(
        positions["execution_date"],
        errors="coerce",
    )

    positions = (
        positions[
            positions["status"].eq("OK")
            & positions["execution_date"].notna()
        ]
        .sort_values("execution_date")
        .reset_index(drop=True)
    )

    if positions.empty:
        raise RuntimeError("성과 계산에 사용할 포지션이 없습니다.")

    prices = load_or_download_prices(
        positions["execution_date"].min(),
        positions["execution_date"].max(),
    )

    returns = prices.pct_change(fill_method=None)

    rows: list[dict[str, object]] = []
    previous_weights = {
        ticker: 0.0
        for ticker in SECTOR_TO_ETF.values()
    }

    for _, position in positions.iterrows():
        execution_date = pd.Timestamp(position["execution_date"])

        if execution_date not in returns.index:
            rows.append({
                "signal_date": position["signal_date"],
                "execution_date": execution_date,
                "status": "NO_PRICE",
                "error": "execution_date absent from ETF return index",
            })
            continue

        sector_weights = parse_weights(position["weights_json"])

        target_weights = {
            ticker: 0.0
            for ticker in SECTOR_TO_ETF.values()
        }

        unmapped_sectors: list[str] = []

        for sector, weight in sector_weights.items():
            ticker = SECTOR_TO_ETF.get(sector)

            if ticker is None:
                unmapped_sectors.append(sector)
                continue

            target_weights[ticker] += weight

        allocated = float(sum(target_weights.values()))
        cash_weight = max(
            0.0,
            float(position["cash_weight"]) / 100.0,
        )

        # 섹터 비중 합 + 현금 합계 검증
        total_weight = allocated + cash_weight
        if abs(total_weight - 1.0) > 0.003:
            raise RuntimeError(
                f"{execution_date.date()} total weight={total_weight:.6f}"
            )

        gross_return = 0.0
        missing_price_tickers: list[str] = []

        for ticker, weight in target_weights.items():
            if weight == 0:
                continue

            ticker_return = returns.at[execution_date, ticker]

            if pd.isna(ticker_return):
                missing_price_tickers.append(ticker)
                continue

            gross_return += weight * float(ticker_return)

        turnover = float(
            sum(
                abs(target_weights[ticker] - previous_weights.get(ticker, 0.0))
                for ticker in target_weights
            )
        )

        transaction_cost = turnover * COST_BPS_ONE_WAY / 10000.0
        net_return = gross_return - transaction_cost

        benchmark_return = returns.at[execution_date, BENCHMARK]
        benchmark_return = (
            float(benchmark_return)
            if pd.notna(benchmark_return)
            else np.nan
        )

        rows.append({
            "signal_date": position["signal_date"],
            "execution_date": execution_date,
            "gross_exposure": allocated,
            "cash_weight": cash_weight,
            "turnover": turnover,
            "transaction_cost": transaction_cost,
            "strategy_return_gross": gross_return,
            "strategy_return_net": net_return,
            "benchmark_return": benchmark_return,
            "excess_return_net": (
                net_return - benchmark_return
                if pd.notna(benchmark_return)
                else np.nan
            ),
            "unmapped_sectors": "|".join(unmapped_sectors),
            "missing_price_tickers": "|".join(missing_price_tickers),
            "status": "OK",
            "error": "",
        })

        previous_weights = target_weights

    daily = pd.DataFrame(rows).sort_values("execution_date")

    valid = daily[daily["status"].eq("OK")].copy()

    if valid.empty:
        raise RuntimeError("유효한 성과 계산 행이 없습니다.")

    valid["strategy_value"] = (
        1.0 + valid["strategy_return_net"]
    ).cumprod()

    valid["benchmark_value"] = (
        1.0 + valid["benchmark_return"].fillna(0.0)
    ).cumprod()

    valid["strategy_drawdown"] = (
        valid["strategy_value"] / valid["strategy_value"].cummax() - 1.0
    )

    valid["benchmark_drawdown"] = (
        valid["benchmark_value"] / valid["benchmark_value"].cummax() - 1.0
    )

    # 계산된 누적값을 원본 daily에 병합
    daily = daily.merge(
        valid[
            [
                "execution_date",
                "strategy_value",
                "benchmark_value",
                "strategy_drawdown",
                "benchmark_drawdown",
            ]
        ],
        on="execution_date",
        how="left",
    )

    daily.to_csv(DAILY_PATH, index=False, encoding="utf-8-sig")

    strategy = valid["strategy_return_net"]
    benchmark = valid["benchmark_return"]

    strategy_cagr = annualized_return(strategy)
    benchmark_cagr = annualized_return(benchmark)
    annual_turnover = float(valid["turnover"].mean() * TRADING_DAYS)
    total_cost = float(valid["transaction_cost"].sum())

    summary = pd.DataFrame([
        {
            "start_date": valid["execution_date"].min().date(),
            "end_date": valid["execution_date"].max().date(),
            "observations": len(valid),
            "strategy_cagr": strategy_cagr,
            "spy_cagr": benchmark_cagr,
            "strategy_mdd": max_drawdown(strategy),
            "spy_mdd": max_drawdown(benchmark),
            "strategy_volatility": annualized_volatility(strategy),
            "spy_volatility": annualized_volatility(benchmark),
            "sharpe": sharpe_ratio(strategy),
            "down_capture": down_capture(strategy, benchmark),
            "average_exposure": float(valid["gross_exposure"].mean()),
            "average_cash": float(valid["cash_weight"].mean()),
            "annual_turnover": annual_turnover,
            "total_transaction_cost": total_cost,
            "net_alpha_after_costs": strategy_cagr - benchmark_cagr,
        }
    ])

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"Saved: {PRICE_PATH}")
    print(f"Saved: {DAILY_PATH}")
    print(f"Saved: {SUMMARY_PATH}")

    print("\nPerformance summary:")
    print(summary.T.to_string(header=False))

    print("\nData quality:")
    print("NO_PRICE rows:", int((daily["status"] == "NO_PRICE").sum()))
    print(
        "Rows with missing sector prices:",
        int(valid["missing_price_tickers"].fillna("").ne("").sum()),
    )
    print(
        "Rows with unmapped sectors:",
        int(valid["unmapped_sectors"].fillna("").ne("").sum()),
    )


if __name__ == "__main__":
    main()
