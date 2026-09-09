from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "backtest"
RESULTS = DATA / "results"

POSITIONS = (
    RESULTS
    / "canonical_performance_input_contract_v1"
    / "canonical_performance_positions_v1.csv"
)
LEGACY_PRICES = DATA / "sector_prices.csv"
XLC_PRICES = DATA / "research_price_completion" / "xlc_yahoo_auto_adjust_close.csv"
XLRE_PRICES = DATA / "research_price_completion" / "xlre_yahoo_auto_adjust_close.csv"
OUTPUT_DIR = RESULTS / "research_performance_v1"

EXPECTED_SHA256 = {
    POSITIONS: "1cf97d6553db7b09dfaf1b60f0ca973092f2515c439c63c3ba9b341d0b079305",
    LEGACY_PRICES: "8d333ebe45a394f9eda93308772644f23f69364c496eb2f471c4982d5966fad8",
    XLC_PRICES: "afe42d8cce02e0727c757045e9e3f5b3f215ce43cb10f9cc4192ca4d435098cb",
    XLRE_PRICES: "7194af0f0e162065116418e74f5ba20db89ff9dd769e9f401b7a3f0be9febc04",
}

SECTOR_TO_ETF = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Energy": "XLE",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Health Care": "XLV",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
}
ETF_UNIVERSE = tuple(SECTOR_TO_ETF.values())
REQUIRED_PRICE_COLUMNS = (*ETF_UNIVERSE, "SPY")

SIGNAL_START = pd.Timestamp("2018-06-18")
EXECUTION_START = pd.Timestamp("2018-06-19")
EXECUTION_END = pd.Timestamp("2026-06-22")
FINAL_RETURN_ENDPOINT = pd.Timestamp("2026-06-23")
EXPECTED_ROWS = 2012
ARM = "BASELINE_PRODUCTION_AUTHORITY"
TRADING_DAYS = 252
CLAIM_LABEL = "RESEARCH-GRADE HISTORICAL BACKTEST — PUBLIC/YAHOO MARKET DATA"
DISCLAIMER = "NOT A LIVE OR PRODUCTION TRACK RECORD"


class ContractError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def verify_identities() -> None:
    for path, expected in EXPECTED_SHA256.items():
        require(path.is_file(), f"missing required input: {path.relative_to(ROOT)}")
        observed = sha256(path)
        require(
            observed == expected,
            f"SHA256 mismatch: {path.relative_to(ROOT)} expected={expected} observed={observed}",
        )


def load_positions() -> pd.DataFrame:
    positions = pd.read_csv(POSITIONS)
    required = {
        "signal_date", "execution_date", "arm", "allocated_equity_18",
        "cash_weight", "weights_json", "weights_sha256", "capital_sum",
    }
    require(required.issubset(positions.columns), f"positions schema missing: {sorted(required - set(positions.columns))}")
    positions["signal_date"] = pd.to_datetime(positions["signal_date"], errors="raise")
    positions["execution_date"] = pd.to_datetime(positions["execution_date"], errors="raise")
    positions = positions.loc[positions["signal_date"] >= SIGNAL_START].copy()
    positions = positions.sort_values("execution_date").reset_index(drop=True)

    require(len(positions) == EXPECTED_ROWS, f"expected {EXPECTED_ROWS} frozen rows, observed {len(positions)}")
    require(positions["arm"].eq(ARM).all(), "non-authorized portfolio arm detected")
    require(positions["execution_date"].min() == EXECUTION_START, "wrong first execution date")
    require(positions["execution_date"].max() == EXECUTION_END, "wrong final execution date")
    require(not positions["execution_date"].duplicated().any(), "duplicate execution date")
    require(positions["execution_date"].is_monotonic_increasing, "execution dates are not chronological")
    require(np.isfinite(pd.to_numeric(positions["capital_sum"], errors="coerce")).all(), "nonfinite capital_sum")
    require(np.allclose(positions["capital_sum"].astype(float), 100.0, atol=1e-9), "portfolio equity+cash identity failure")
    return positions


def load_single_price(path: Path, ticker: str) -> pd.DataFrame:
    frame = pd.read_csv(path)
    require(list(frame.columns) == ["Date", ticker], f"wrong {ticker} price schema")
    frame["date"] = pd.to_datetime(frame.pop("Date"), errors="raise")
    require(not frame["date"].duplicated().any(), f"duplicate {ticker} price date")
    frame[ticker] = pd.to_numeric(frame[ticker], errors="coerce")
    require(np.isfinite(frame[ticker]).all(), f"nonfinite {ticker} price")
    require((frame[ticker] > 0).all(), f"nonpositive {ticker} price")
    return frame.set_index("date").sort_index()


def load_prices() -> pd.DataFrame:
    prices = pd.read_csv(LEGACY_PRICES)
    require("date" in prices.columns, "legacy research price date column missing")
    prices["date"] = pd.to_datetime(prices["date"], errors="raise")
    require(not prices["date"].duplicated().any(), "duplicate legacy price date")

    prohibited = {"IYR", "VOX"}
    selected_legacy = [c for c in REQUIRED_PRICE_COLUMNS if c not in {"XLRE", "XLC"}]
    require(not prohibited.intersection(selected_legacy), "IYR/VOX selected for performance")
    require(set(selected_legacy).issubset(prices.columns), "required legacy research price column missing")
    prices = prices.set_index("date")[selected_legacy].sort_index()
    prices = prices.join(load_single_price(XLRE_PRICES, "XLRE"), how="inner")
    prices = prices.join(load_single_price(XLC_PRICES, "XLC"), how="inner")
    prices = prices.loc[:, list(REQUIRED_PRICE_COLUMNS)]
    for column in prices:
        prices[column] = pd.to_numeric(prices[column], errors="coerce")
    return prices


def parse_target_weights(row: pd.Series) -> dict[str, float]:
    try:
        sector_weights = json.loads(row["weights_json"])
    except (TypeError, json.JSONDecodeError) as exc:
        raise ContractError(f"invalid weights_json at {row['execution_date'].date()}") from exc
    unknown = set(sector_weights) - set(SECTOR_TO_ETF)
    require(not unknown, f"unmapped sectors at {row['execution_date'].date()}: {sorted(unknown)}")
    target = {ticker: 0.0 for ticker in ETF_UNIVERSE}
    for sector, weight in sector_weights.items():
        target[SECTOR_TO_ETF[sector]] += float(weight) / 100.0
    allocated = float(row["allocated_equity_18"]) / 100.0
    cash = float(row["cash_weight"]) / 100.0
    require(abs(sum(target.values()) - allocated) <= 1e-9, f"sector/F18 identity failure at {row['execution_date'].date()}")
    require(abs(allocated + cash - 1.0) <= 1e-9, f"equity/cash identity failure at {row['execution_date'].date()}")
    return target


def build_validated_intervals(positions: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    require(not prices.index.duplicated().any(), "duplicate combined price date")
    require(set(REQUIRED_PRICE_COLUMNS) == set(prices.columns), "price universe mismatch")
    rows: list[dict[str, object]] = []
    calendar = prices.index.sort_values()

    for _, position in positions.iterrows():
        execution = pd.Timestamp(position["execution_date"])
        require(execution in calendar, f"missing execution close: {execution.date()}")
        next_index = int(calendar.searchsorted(execution, side="right"))
        require(next_index < len(calendar), f"missing next trading-day close after {execution.date()}")
        accrual_end = pd.Timestamp(calendar[next_index])
        require(accrual_end > execution, f"ambiguous execution→next-date mapping: {execution.date()}")

        endpoints = prices.loc[[execution, accrual_end], list(REQUIRED_PRICE_COLUMNS)]
        missing = endpoints.columns[endpoints.isna().any()].tolist()
        require(not missing, f"missing required price at {execution.date()}→{accrual_end.date()}: {missing}")
        require(np.isfinite(endpoints.to_numpy(dtype=float)).all(), f"nonfinite required price at {execution.date()}→{accrual_end.date()}")
        require((endpoints.to_numpy(dtype=float) > 0).all(), f"nonpositive required price at {execution.date()}→{accrual_end.date()}")

        forward = endpoints.iloc[1] / endpoints.iloc[0] - 1.0
        require(np.isfinite(forward.to_numpy(dtype=float)).all(), f"nonfinite forward return at {execution.date()}→{accrual_end.date()}")
        target = parse_target_weights(position)
        missing_nonzero = [ticker for ticker, weight in target.items() if weight != 0.0 and pd.isna(forward[ticker])]
        require(not missing_nonzero, f"missing nonzero-weight return at {execution.date()}: {missing_nonzero}")

        rows.append({
            "signal_date": position["signal_date"],
            "execution_date": execution,
            "return_accrual_end": accrual_end,
            "weights": target,
            "allocated_equity": float(position["allocated_equity_18"]) / 100.0,
            "cash_weight": float(position["cash_weight"]) / 100.0,
            "forward_returns": forward.to_dict(),
        })

    intervals = pd.DataFrame(rows)
    require(len(intervals) == EXPECTED_ROWS, "not exactly one interval per frozen position")
    require(not intervals["execution_date"].duplicated().any(), "duplicate validated interval")
    require(intervals.iloc[0]["return_accrual_end"] == pd.Timestamp("2018-06-20"), "wrong first accrual endpoint")
    require(intervals.iloc[-1]["return_accrual_end"] == FINAL_RETURN_ENDPOINT, "wrong final accrual endpoint")
    return intervals


def annualized_return(returns: pd.Series) -> float:
    wealth = float((1.0 + returns).prod())
    return wealth ** (TRADING_DAYS / len(returns)) - 1.0


def max_drawdown(returns: pd.Series) -> float:
    wealth = (1.0 + returns).cumprod()
    return float((wealth / wealth.cummax() - 1.0).min())


def calculate_performance(
    intervals: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    daily_rows = []
    for _, row in intervals.iterrows():
        forwards = row["forward_returns"]
        weights = row["weights"]
        gcf_return = sum(weights[ticker] * forwards[ticker] for ticker in ETF_UNIVERSE)
        spy_return = forwards["SPY"]
        matched_return = row["allocated_equity"] * spy_return
        daily_rows.append({
            "signal_date": row["signal_date"],
            "execution_date": row["execution_date"],
            "return_accrual_end": row["return_accrual_end"],
            "gcf_gross_return": gcf_return,
            "spy_return": spy_return,
            "exposure_matched_spy_return": matched_return,
            "allocated_equity": row["allocated_equity"],
            "cash_weight": row["cash_weight"],
        })
    daily = pd.DataFrame(daily_rows)
    return_columns = [
        "gcf_gross_return",
        "spy_return",
        "exposure_matched_spy_return",
    ]
    for name in return_columns:
        daily[f"{name}_cumulative"] = (1.0 + daily[name]).cumprod() - 1.0

    daily["calendar_year"] = daily["return_accrual_end"].dt.year
    annual = (
        daily.groupby("calendar_year", sort=True)
        .agg(
            gcf_return=("gcf_gross_return", lambda x: (1.0 + x).prod() - 1.0),
            spy_return=("spy_return", lambda x: (1.0 + x).prod() - 1.0),
            exposure_matched_spy_return=(
                "exposure_matched_spy_return",
                lambda x: (1.0 + x).prod() - 1.0,
            ),
            average_gcf_exposure=("allocated_equity", "mean"),
            observations=("return_accrual_end", "size"),
            first_return_endpoint=("return_accrual_end", "min"),
            last_return_endpoint=("return_accrual_end", "max"),
        )
        .reset_index()
    )
    annual["period_type"] = "FULL_CALENDAR_YEAR"
    annual.loc[
        annual["calendar_year"].isin(
            [annual["calendar_year"].min(), annual["calendar_year"].max()]
        ),
        "period_type",
    ] = "PARTIAL_YEAR"

    summary: dict[str, object] = {
        "claim_label": CLAIM_LABEL,
        "disclaimer": DISCLAIMER,
        "cash_assumption": "ZERO-CARRY CASH ASSUMPTION",
        "cost_convention": "GROSS BEFORE TRANSACTION COSTS",
        "sharpe_convention": "mean daily gross return / sample daily volatility * sqrt(252); risk-free=0; research statistic",
        "observations": len(daily),
        "execution_window": {
            "start": str(daily["execution_date"].min().date()),
            "end": str(daily["execution_date"].max().date()),
        },
        "return_endpoint_window": {
            "start": str(daily["return_accrual_end"].min().date()),
            "end": str(daily["return_accrual_end"].max().date()),
        },
    }
    for name in return_columns:
        series = daily[name]
        summary[name] = {
            "cumulative_return": float((1.0 + series).prod() - 1.0),
            "cagr": annualized_return(series),
            "maximum_drawdown": max_drawdown(series),
            "annualized_volatility": float(series.std(ddof=1) * math.sqrt(TRADING_DAYS)),
            "sharpe_like": float(series.mean() / series.std(ddof=1) * math.sqrt(TRADING_DAYS)),
        }
    summary["average_equity_exposure"] = float(daily["allocated_equity"].mean())
    summary["average_cash_weight"] = float(daily["cash_weight"].mean())
    summary["comparisons"] = {
        "gcf_cagr_minus_spy_cagr": (
            summary["gcf_gross_return"]["cagr"] - summary["spy_return"]["cagr"]
        ),
        "gcf_mdd_minus_spy_mdd": (
            summary["gcf_gross_return"]["maximum_drawdown"]
            - summary["spy_return"]["maximum_drawdown"]
        ),
        "gcf_volatility_minus_spy_volatility": (
            summary["gcf_gross_return"]["annualized_volatility"]
            - summary["spy_return"]["annualized_volatility"]
        ),
        "gcf_cagr_minus_exposure_matched_spy_cagr": (
            summary["gcf_gross_return"]["cagr"]
            - summary["exposure_matched_spy_return"]["cagr"]
        ),
        "gcf_cumulative_minus_exposure_matched_spy_cumulative": (
            summary["gcf_gross_return"]["cumulative_return"]
            - summary["exposure_matched_spy_return"]["cumulative_return"]
        ),
    }
    return daily, annual, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--run", action="store_true")
    args = parser.parse_args()

    verify_identities()
    positions = load_positions()
    prices = load_prices()
    intervals = build_validated_intervals(positions, prices)

    if args.validate_only:
        print("RESEARCH PERFORMANCE INPUT VALIDATION: PASS")
        print(f"POSITIONS: {len(positions)}")
        print(f"EXECUTION: {positions['execution_date'].min().date()} -> {positions['execution_date'].max().date()}")
        print(f"RETURN ENDPOINTS: {intervals['return_accrual_end'].min().date()} -> {intervals['return_accrual_end'].max().date()}")
        print("IYR/VOX USED: 0")
        print("PERFORMANCE METRICS CALCULATED: 0")
        print("RESEARCH_PERFORMANCE_RUNNER_READY")
        return

    daily, annual, summary = calculate_performance(intervals)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    daily.to_csv(OUTPUT_DIR / "research_performance_daily_v1.csv", index=False)
    annual.to_csv(OUTPUT_DIR / "research_performance_calendar_year_v1.csv", index=False)
    with (OUTPUT_DIR / "research_performance_summary_v1.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(CLAIM_LABEL)
    print(DISCLAIMER)
    print(f"Saved: {OUTPUT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except ContractError as exc:
        raise SystemExit(f"RESEARCH PERFORMANCE INPUT VALIDATION: FAIL - {exc}") from exc
