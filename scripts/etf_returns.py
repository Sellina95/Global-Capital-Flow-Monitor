import os
import numpy as np
import pandas as pd

# 원래 포트폴리오
base_weights = {
    "BND": 0.15, "EEM": 0.10, "EIS": 0.05, "EMB": 0.10, "EWJ": 0.05,
    "FXI": 0.10, "GLD": 0.05, "SPY": 0.10, "VXX": 0.05, "XLK": 0.05,
    "XLV": 0.05, "XLP": 0.05, "XLF": 0.05, "QUAL": 0.05, "COWZ": 0.05, "MTUM": 0.05
}

# 19번 필터 반영 예시 포트폴리오
filtered_weights = {
    "BND": 0.20,
    "EEM": 0.03,
    "EIS": 0.02,
    "EMB": 0.08,
    "EWJ": 0.04,
    "FXI": 0.03,
    "GLD": 0.10,
    "SPY": 0.05,
    "VXX": 0.00,
    "XLK": 0.03,
    "XLV": 0.12,
    "XLP": 0.12,
    "XLF": 0.05,
    "QUAL": 0.08,
    "COWZ": 0.08,
    "MTUM": 0.00
}

RISK_FREE_RATE_ANNUAL = 0.03
TRADING_DAYS = 252


def calculate_returns(weights_dict):
    """각 ETF 개별 파일을 읽어 일일 수익률 계산"""
    all_returns = []
    data_directory = 'data/'
    symbols = list(weights_dict.keys())

    for symbol in symbols:
        file_path = os.path.join(data_directory, f"{symbol}_data.csv")

        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, skiprows=3, header=None)
                df = df.iloc[:, [0, 1]]
                df.columns = ['Date', 'Price']

                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
                df = df.dropna().set_index('Date').sort_index()

                returns = df['Price'].pct_change()
                returns.name = symbol
                all_returns.append(returns)

                print(f"✅ {symbol}: 계산 성공")

            except Exception as e:
                print(f"❌ {symbol} 처리 중 에러: {e}")
        else:
            print(f"⚠️ 파일 없음: {file_path}")

    if all_returns:
        combined = pd.concat(all_returns, axis=1)
        return combined
    return None


def build_portfolio_returns(combined_df, weights_dict, portfolio_name="Portfolio"):
    """주어진 가중치로 포트폴리오 일일수익률 생성"""
    available_cols = [col for col in combined_df.columns if col in weights_dict]
    weight_series = pd.Series(weights_dict)
    weight_series = weight_series[available_cols]

    # 가중치 재정규화
    weight_series = weight_series / weight_series.sum()

    portfolio_returns = combined_df[available_cols].fillna(0).dot(weight_series)
    portfolio_returns.name = f"{portfolio_name}_Return"

    return portfolio_returns


def calculate_performance_metrics(portfolio_returns, risk_free_rate_annual=0.03):
    """성과지표 계산"""
    portfolio_returns = portfolio_returns.dropna()

    if portfolio_returns.empty:
        return None

    daily_rf = risk_free_rate_annual / TRADING_DAYS

    cumulative_return = (1 + portfolio_returns).prod() - 1
    annual_return = (1 + portfolio_returns.mean()) ** TRADING_DAYS - 1
    annual_volatility = portfolio_returns.std() * np.sqrt(TRADING_DAYS)

    if portfolio_returns.std() != 0:
        sharpe_ratio = ((portfolio_returns.mean() - daily_rf) / portfolio_returns.std()) * np.sqrt(TRADING_DAYS)
    else:
        sharpe_ratio = np.nan

    if annual_volatility != 0:
        raroc_proxy = (annual_return - risk_free_rate_annual) / annual_volatility
    else:
        raroc_proxy = np.nan

    cumulative_curve = (1 + portfolio_returns).cumprod()
    rolling_max = cumulative_curve.cummax()
    drawdown = (cumulative_curve / rolling_max) - 1
    max_drawdown = drawdown.min()

    return {
        "Cumulative Return": cumulative_return,
        "Annual Return": annual_return,
        "Annual Volatility": annual_volatility,
        "Sharpe Ratio": sharpe_ratio,
        "RAROC Proxy": raroc_proxy,
        "Max Drawdown": max_drawdown
    }


def compare_portfolios(base_returns, filtered_returns):
    """적용 전/후 성과 비교표"""
    base_metrics = calculate_performance_metrics(base_returns, RISK_FREE_RATE_ANNUAL)
    filtered_metrics = calculate_performance_metrics(filtered_returns, RISK_FREE_RATE_ANNUAL)

    comparison = pd.DataFrame({
        "Base Portfolio": base_metrics,
        "Filtered Portfolio": filtered_metrics
    })

    comparison["Difference (Filtered - Base)"] = (
        comparison["Filtered Portfolio"] - comparison["Base Portfolio"]
    )

    return comparison


if __name__ == "__main__":
    # ETF 수익률 데이터 로드
    combined_df = calculate_returns(base_weights)

    if combined_df is not None:
        combined_df = combined_df.sort_index()

        # 기존 포트폴리오
        base_portfolio_returns = build_portfolio_returns(
            combined_df,
            base_weights,
            portfolio_name="Base"
        )

        # 19번 필터 반영 포트폴리오
        filtered_portfolio_returns = build_portfolio_returns(
            combined_df,
            filtered_weights,
            portfolio_name="Filtered"
        )

        # 결과 합치기
        result_df = combined_df.copy()
        result_df["Base_Portfolio_Return"] = base_portfolio_returns
        result_df["Filtered_Portfolio_Return"] = filtered_portfolio_returns
        result_df["Base_Cumulative"] = (1 + result_df["Base_Portfolio_Return"]).cumprod()
        result_df["Filtered_Cumulative"] = (1 + result_df["Filtered_Portfolio_Return"]).cumprod()

        # 저장
        output_path = "data/etf_portfolio_comparison.csv"
        result_df.to_csv(output_path)

        # 비교표 출력
        comparison = compare_portfolios(base_portfolio_returns, filtered_portfolio_returns)

        print("-" * 50)
        print("📊 Base vs Filtered Portfolio Comparison")
        print(comparison.round(4))

        print("-" * 50)
        print(f"✅ 비교 결과 저장 완료: {output_path}")
        print(result_df.tail())

    else:
        print("❌ 통합할 데이터가 없습니다.")