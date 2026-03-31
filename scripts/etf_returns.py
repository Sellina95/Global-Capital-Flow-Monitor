import os
import numpy as np
import pandas as pd

from filters.executive_layer import execution_layer_filter

# =========================
# 1) 원래 포트폴리오
# =========================
base_weights = {
    "BND": 0.15, "EEM": 0.10, "EIS": 0.05, "EMB": 0.10, "EWJ": 0.05,
    "FXI": 0.10, "GLD": 0.05, "SPY": 0.10, "VXX": 0.05, "XLK": 0.05,
    "XLV": 0.05, "XLP": 0.05, "XLF": 0.05, "QUAL": 0.05, "COWZ": 0.05, "MTUM": 0.05
}

# =========================
# 2) ETF ↔ 스타일 매핑
# =========================
ETF_STYLE_MAP = {
    "BND":  ["low_beta", "defensive"],
    "EEM":  ["high_beta", "em_beta"],
    "EIS":  ["high_beta", "single_country_risk"],
    "EMB":  ["credit", "income"],
    "EWJ":  ["beta", "developed_ex_us"],
    "FXI":  ["high_beta", "china_beta"],
    "GLD":  ["defensive", "hedge"],
    "SPY":  ["beta", "broad_equity"],
    "VXX":  ["volatility_hedge"],
    "XLK":  ["growth", "long_duration"],
    "XLV":  ["defensive", "quality"],
    "XLP":  ["defensive", "quality"],
    "XLF":  ["balance_sheet_strength", "cyclical_financials"],
    "QUAL": ["quality", "raroc_friendly"],
    "COWZ": ["cashflow_strength", "raroc_friendly"],
    "MTUM": ["high_beta", "growth"]
}

# =========================
# 3) 현재 시장 상태 (임시 수동 입력)
#    - 지금은 액션 결과 기준으로 넣어둠
#    - 나중에 generate_report.py 결과와 자동 연결 가능
# =========================
CURRENT_MARKET_DATA = {
    "FINAL_STATE": {
        "structure_tag": "TIGHTENING",          # 또는 EVENT-WATCHING이면 바꿔도 됨
        "liquidity_dir": "DOWN",
        "liquidity_level_bucket": "MID",
        "credit_calm": True
    },
    "SECTOR_OW": ["Consumer Staples", "Utilities", "Health Care"],
    "SECTOR_UW": ["Technology", "Consumer Discretionary", "Real Estate"]
}

RISK_FREE_RATE_ANNUAL = 0.03
TRADING_DAYS = 252


def score_etfs(style_tags, etf_map):
    """
    style_tags와 ETF_STYLE_MAP를 바탕으로 ETF 점수 계산
    """
    scores = {}

    for etf, tags in etf_map.items():
        score = 0

        for tag in tags:
            if tag in style_tags:
                score += 1

        # 방어 스타일인데 고베타/성장 ETF면 패널티
        if ("high_beta" in tags or "growth" in tags) and "defensive" in style_tags:
            score -= 1

        # 듀레이션 민감 회피 환경이면 long_duration 패널티
        if "duration_aware" in style_tags and "long_duration" in tags:
            score -= 1

        # low_beta 선호면 broad beta/high beta 추가 패널티
        if "low_beta" in style_tags and ("beta" in tags or "high_beta" in tags):
            score -= 1

        scores[etf] = score

    return scores


def normalize_weights(scores):
    import pandas as pd

    scores_series = pd.Series(scores)

    # ---------------------------
    # 1. Soft penalty 적용
    # ---------------------------
    # 기존: 음수 → 0
    # 개선: 음수도 완전 제거 안하고 약하게 반영
    adjusted = scores_series.copy()

    # negative penalty 완화
    adjusted = adjusted.apply(lambda x: x if x > 0 else x * 0.3)

    # ---------------------------
    # 2. 최소 비중 floor 설정
    # ---------------------------
    MIN_WEIGHT = 0.02  # 2% 최소 비중

    # score scaling (shift)
    adjusted = adjusted - adjusted.min() + 0.1

    # ---------------------------
    # 3. core / satellite 구분
    # ---------------------------
    CORE_ETF = ["BND", "XLV", "XLP", "QUAL", "COWZ"]

    core_boost = 1.3
    adjusted = adjusted * [
        core_boost if etf in CORE_ETF else 1.0
        for etf in adjusted.index
    ]

    # ---------------------------
    # 4. 정규화
    # ---------------------------
    weights = adjusted / adjusted.sum()

    # ---------------------------
    # 5. floor 적용
    # ---------------------------
    weights = weights.apply(lambda x: max(x, MIN_WEIGHT))

    # 다시 정규화
    weights = weights / weights.sum()

    return weights.to_dict()


def calculate_returns(weights_dict):
    """
    각 ETF 개별 파일을 읽어 일일 수익률 계산
    """
    all_returns = []
    data_directory = "data/"
    symbols = list(weights_dict.keys())

    for symbol in symbols:
        file_path = os.path.join(data_directory, f"{symbol}_data.csv")

        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path, skiprows=3, header=None)
                df = df.iloc[:, [0, 1]]
                df.columns = ["Date", "Price"]

                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
                df = df.dropna().set_index("Date").sort_index()

                returns = df["Price"].pct_change()
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
    """
    주어진 가중치로 포트폴리오 일일수익률 생성
    """
    available_cols = [col for col in combined_df.columns if col in weights_dict]

    if not available_cols:
        raise ValueError(f"{portfolio_name}: 사용 가능한 ETF 컬럼이 없습니다.")

    weight_series = pd.Series(weights_dict, dtype=float)
    weight_series = weight_series[available_cols]

    # 가중치 재정규화
    weight_series = weight_series / weight_series.sum()

    portfolio_returns = combined_df[available_cols].fillna(0).dot(weight_series)
    portfolio_returns.name = f"{portfolio_name}_Return"

    return portfolio_returns


def build_filtered_portfolio(market_data):
    """
    19번 필터 실행 → style_tags 추출 → ETF 점수화 → 자동 가중치 생성
    """
    result = execution_layer_filter(market_data)
    style_tags = result["style_tags"]

    scores = score_etfs(style_tags, ETF_STYLE_MAP)
    weights = normalize_weights(scores)

    return weights, scores, result

def calculate_performance_metrics(portfolio_returns, risk_free_rate_annual=0.03):
    """
    포트폴리오 성과지표 계산
    """
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


def calculate_active_metrics(portfolio_returns, benchmark_returns):
    """
    Active Return / Tracking Error / Information Ratio 계산
    """
    df = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()

    if df.empty:
        return None

    port = df.iloc[:, 0]
    bench = df.iloc[:, 1]

    active_returns = port - bench

    cumulative_port = (1 + port).prod() - 1
    cumulative_bench = (1 + bench).prod() - 1
    active_return = cumulative_port - cumulative_bench

    tracking_error = active_returns.std() * np.sqrt(TRADING_DAYS)

    if tracking_error != 0:
        information_ratio = (active_returns.mean() * TRADING_DAYS) / tracking_error
    else:
        information_ratio = np.nan

    return {
        "Portfolio Cumulative Return": cumulative_port,
        "Benchmark Cumulative Return": cumulative_bench,
        "Active Return": active_return,
        "Tracking Error": tracking_error,
        "Information Ratio": information_ratio,
    }


def compare_portfolios(base_returns, filtered_returns):
    """
    Base 포트폴리오 vs Filtered 포트폴리오 비교표
    """
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


def compare_against_benchmark(portfolio_returns, benchmark_returns, benchmark_label="Benchmark"):
    """
    포트폴리오 vs 벤치마크 비교표
    """
    portfolio_metrics = calculate_performance_metrics(portfolio_returns, RISK_FREE_RATE_ANNUAL)
    benchmark_metrics = calculate_performance_metrics(benchmark_returns, RISK_FREE_RATE_ANNUAL)
    active_metrics = calculate_active_metrics(portfolio_returns, benchmark_returns)

    comparison = pd.DataFrame({
        "Portfolio": portfolio_metrics,
        benchmark_label: benchmark_metrics
    })

    if active_metrics is not None:
        for k, v in active_metrics.items():
            comparison.loc[k, "Active vs Benchmark"] = v

    return comparison
    
def build_single_benchmark_returns(combined_df, symbol, benchmark_name=None):
    """
    단일 ETF benchmark 수익률 생성
    예: SPY
    """
    if symbol not in combined_df.columns:
        raise ValueError(f"Benchmark symbol {symbol} not found in combined_df")

    benchmark_returns = combined_df[symbol].fillna(0).copy()
    benchmark_returns.name = benchmark_name or f"{symbol}_Return"
    return benchmark_returns


def build_6040_benchmark_returns(combined_df):
    """
    60/40 benchmark 생성 (SPY 60%, BND 40%)
    """
    benchmark_weights = {"SPY": 0.6, "BND": 0.4}
    return build_portfolio_returns(combined_df, benchmark_weights, portfolio_name="Benchmark_60_40")


if __name__ == "__main__":
    # =========================
    # A. ETF 일일수익률 데이터 로드
    # =========================
    combined_df = calculate_returns(base_weights)

    if combined_df is not None:
        combined_df = combined_df.sort_index()

        # =========================
        # B. 기존 포트폴리오
        # =========================
        base_portfolio_returns = build_portfolio_returns(
            combined_df,
            base_weights,
            portfolio_name="Base"
        )

        # =========================
        # C. 19번 필터 기반 자동 가중치 생성
        # =========================
        filtered_weights, scores, filter_result = build_filtered_portfolio(CURRENT_MARKET_DATA)

        if filtered_weights is None:
            raise ValueError("❌ 필터 기반 가중치 생성 실패: 모든 ETF 점수가 0 이하입니다.")

        print("-" * 60)
        print("🧬 19번 필터 리포트")
        print(filter_result["report"])

        print("-" * 60)
        print("📊 Style Tags")
        print(filter_result["style_tags"])

        print("-" * 60)
        print("📊 ETF Scores")
        print(pd.Series(scores).sort_values(ascending=False))

        print("-" * 60)
        print("📊 Auto Generated ETF Weights")
        print(pd.Series(filtered_weights).sort_values(ascending=False).round(4))

        # =========================
        # D. 필터 적용 포트폴리오
        # =========================
        filtered_portfolio_returns = build_portfolio_returns(
            combined_df,
            filtered_weights,
            portfolio_name="Filtered"
        )

        # =========================
        # E. 결과 합치기
        # =========================
        result_df = combined_df.copy()
        result_df["Base_Portfolio_Return"] = base_portfolio_returns
        result_df["Filtered_Portfolio_Return"] = filtered_portfolio_returns
        result_df["Base_Cumulative"] = (1 + result_df["Base_Portfolio_Return"]).cumprod()
        result_df["Filtered_Cumulative"] = (1 + result_df["Filtered_Portfolio_Return"]).cumprod()

        # =========================
        # F. 저장
        # =========================
        output_path = "data/etf_portfolio_comparison.csv"
        result_df.to_csv(output_path)

        # 자동 생성 weight도 저장
        weights_output_path = "data/etf_filtered_weights.csv"
        pd.Series(filtered_weights, name="Weight").to_csv(weights_output_path)

        scores_output_path = "data/etf_scores.csv"
        pd.Series(scores, name="Score").to_csv(scores_output_path)

        # =========================
        # G. 비교표 출력
        # =========================
        comparison = compare_portfolios(base_portfolio_returns, filtered_portfolio_returns)
                # =========================
        # H. SPY benchmark
        # =========================
        spy_returns = build_single_benchmark_returns(
            combined_df,
            symbol="SPY",
            benchmark_name="SPY_Return"
        )

        spy_comparison = compare_against_benchmark(
            filtered_portfolio_returns,
            spy_returns,
            benchmark_label="SPY"
        )

        # =========================
        # I. 60/40 benchmark
        # =========================
        benchmark_6040_returns = build_6040_benchmark_returns(combined_df)

        benchmark_6040_comparison = compare_against_benchmark(
            filtered_portfolio_returns,
            benchmark_6040_returns,
            benchmark_label="60_40"
        )

        print("-" * 60)
        print("📊 Base vs Filtered Portfolio Comparison")
        print(comparison.round(4))

        print("-" * 60)
        print("📊 Filtered Portfolio vs SPY")
        print(spy_comparison.round(4))

        print("-" * 60)
        print("📊 Filtered Portfolio vs 60/40")
        print(benchmark_6040_comparison.round(4))

        print("-" * 60)
        print("📊 Base vs Filtered Portfolio Comparison")
        print(comparison.round(4))

        print("-" * 60)
        print(f"✅ 비교 결과 저장 완료: {output_path}")
        print(f"✅ 자동 가중치 저장 완료: {weights_output_path}")
        print(f"✅ ETF 점수 저장 완료: {scores_output_path}")

        print("-" * 60)
        print(result_df.tail())

    else:
        print("❌ 통합할 데이터가 없습니다.")