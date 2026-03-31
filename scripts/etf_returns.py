import os
import numpy as np
import pandas as pd

# 1. 포트폴리오 가중치 설정
weights = {
    "BND": 0.15, "EEM": 0.10, "EIS": 0.05, "EMB": 0.10, "EWJ": 0.05,
    "FXI": 0.10, "GLD": 0.05, "SPY": 0.10, "VXX": 0.05, "XLK": 0.05,
    "XLV": 0.05, "XLP": 0.05, "XLF": 0.05, "QUAL": 0.05, "COWZ": 0.05, "MTUM": 0.05
}

RISK_FREE_RATE_ANNUAL = 0.03  # 예시: 연 3%
TRADING_DAYS = 252


def calculate_returns():
    """각 ETF 개별 파일을 읽어 일일 수익률을 계산"""
    all_returns = []
    data_directory = 'data/'
    symbols = list(weights.keys())

    for symbol in symbols:
        file_path = os.path.join(data_directory, f"{symbol}_data.csv")

        if os.path.exists(file_path):
            try:
                # 데이터 로드
                df = pd.read_csv(file_path, skiprows=3, header=None)
                df = df.iloc[:, [0, 1]]
                df.columns = ['Date', 'Price']

                # 전처리
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
                df = df.dropna().set_index('Date').sort_index()

                # 일일 수익률 계산
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


def calculate_performance_metrics(portfolio_returns, risk_free_rate_annual=0.03):
    """포트폴리오 성과지표 계산"""
    portfolio_returns = portfolio_returns.dropna()

    if portfolio_returns.empty:
        return None

    daily_rf = risk_free_rate_annual / TRADING_DAYS

    # 누적수익률
    cumulative_return = (1 + portfolio_returns).prod() - 1

    # 연율화 수익률
    annual_return = (1 + portfolio_returns.mean()) ** TRADING_DAYS - 1

    # 연율화 변동성
    annual_volatility = portfolio_returns.std() * np.sqrt(TRADING_DAYS)

    # Sharpe Ratio
    if annual_volatility != 0:
        sharpe_ratio = ((portfolio_returns.mean() - daily_rf) / portfolio_returns.std()) * np.sqrt(TRADING_DAYS)
    else:
        sharpe_ratio = np.nan

    # 간이 RAROC (현재 프로젝트용 proxy)
    if annual_volatility != 0:
        raroc = (annual_return - risk_free_rate_annual) / annual_volatility
    else:
        raroc = np.nan

    # Max Drawdown
    cumulative_curve = (1 + portfolio_returns).cumprod()
    rolling_max = cumulative_curve.cummax()
    drawdown = (cumulative_curve / rolling_max) - 1
    max_drawdown = drawdown.min()

    metrics = {
        "Cumulative Return": cumulative_return,
        "Annual Return": annual_return,
        "Annual Volatility": annual_volatility,
        "Sharpe Ratio": sharpe_ratio,
        "RAROC_proxy": raroc,
        "Max Drawdown": max_drawdown
    }

    return metrics


if __name__ == "__main__":
    # 단계 1: ETF별 일일 수익률 계산
    combined_df = calculate_returns()

    if combined_df is not None:
        # 너무 이른 날짜에서 NaN 많은 부분 정리
        combined_df = combined_df.sort_index()

        # 사용 가능한 ETF만 반영
        available_cols = [col for col in combined_df.columns if col in weights]
        weight_series = pd.Series(weights)
        weight_series = weight_series[available_cols]

        # 가중치 재정규화 (파일 없는 ETF가 있을 수 있으니까)
        weight_series = weight_series / weight_series.sum()

        # 포트폴리오 일일 수익률 계산
        combined_df['Portfolio_Return'] = combined_df[available_cols].fillna(0).dot(weight_series)

        # 누적수익률 곡선도 추가
        combined_df['Portfolio_Cumulative'] = (1 + combined_df['Portfolio_Return']).cumprod()

        # 성과지표 계산
        metrics = calculate_performance_metrics(
            combined_df['Portfolio_Return'],
            risk_free_rate_annual=RISK_FREE_RATE_ANNUAL
        )

        # 결과 저장
        output_path = "data/etf_daily_returns_combined.csv"
        combined_df.to_csv(output_path)

        print("-" * 40)
        print(f"🚀 ETF별 수익률 + 포트폴리오 결과 저장 완료: {output_path}")

        print("-" * 40)
        print("📊 Portfolio Performance Metrics")
        if metrics:
            for k, v in metrics.items():
                print(f"{k}: {v:.4f}")
        else:
            print("❌ 성과지표 계산 실패")

        print("-" * 40)
        print(combined_df.tail())

    else:
        print("❌ 통합할 데이터가 없습니다.")