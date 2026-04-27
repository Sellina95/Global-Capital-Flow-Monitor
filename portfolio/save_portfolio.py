import os
from datetime import datetime
from typing import Dict

import pandas as pd



def apply_slippage_to_trades(
    trade_df: pd.DataFrame,
    market_data: dict,
) -> pd.DataFrame:
    """
    Trade Log에 슬리피지 반영
    """


    vix_node = market_data.get("VIX", 20)

    if isinstance(vix_node, dict):
        vix = float(vix_node.get("today", 20) or 20)
    else:
        vix = float(vix_node or 20)

    def calc_slippage(row):
        slip = 0.1  # base 0.1%

        # 🔥 VIX 기반 (시장 발작)
        if vix > 30:
            slip += 0.4
        elif vix > 25:
            slip += 0.3
        elif vix > 20:
            slip += 0.1

        # 🔥 유동성 낮은 ETF
        low_liq = ["XLU", "XLRE"]
        if row["etf"] in low_liq:
            slip += 0.2

        # 🔥 거래 규모
        if abs(row["trade_weight"]) > 5:
            slip += 0.2

        return round(slip, 2)

    trade_df["slippage_pct"] = trade_df.apply(calc_slippage, axis=1)

    return trade_df

def apply_transaction_cost(trade_df: pd.DataFrame) -> pd.DataFrame:
    """
    거래 수수료 + 세금 반영
    """

    def calc_cost(row):
        cost = 0.05  # 기본 0.05%

        if row["action"] == "SELL":
            cost += 0.1  # 매도 세금

        return round(cost, 2)

    trade_df["transaction_cost_pct"] = trade_df.apply(calc_cost, axis=1)

    return trade_df


def save_trade_log(
    prev_weights: dict,
    target_weights: dict,
    market_data: dict,
    filepath: str = "data/trade_log.csv",
):
    """
    이전 ETF 비중 vs 현재 목표 비중 비교해서 BUY/SELL/HOLD 로그 생성
    + slippage / transaction cost / total cost 반영
    """

    today = datetime.now().strftime("%Y-%m-%d")
    rows = []

    all_etfs = sorted(set(prev_weights.keys()) | set(target_weights.keys()))

    for etf in all_etfs:
        prev_w = float(prev_weights.get(etf, 0.0) or 0.0)
        target_w = float(target_weights.get(etf, 0.0) or 0.0)
        diff_w = round(target_w - prev_w, 2)

        if diff_w > 0:
            action = "BUY"
        elif diff_w < 0:
            action = "SELL"
        else:
            action = "HOLD"

        rows.append({
            "date": today,
            "etf": etf,
            "prev_weight": round(prev_w, 2),
            "target_weight": round(target_w, 2),
            "trade_weight": diff_w,
            "action": action,
        })

    # 오늘 거래 로그 생성
    df_today = pd.DataFrame(rows)

    # 비용 계산 적용
    df_today = apply_slippage_to_trades(df_today, market_data)
    df_today = apply_transaction_cost(df_today)
    
    print("🔥 DEBUG COLUMNS:", df_today.columns)
    df_today["total_cost_pct"] = (
        df_today["slippage_pct"] + df_today["transaction_cost_pct"]
    ).round(2)
    
    df_today["trade_cost_impact_pct"] = (
        df_today["trade_weight"].abs() * df_today["total_cost_pct"] / 100
    ).round(4)

    # 🔥 총 거래 비용 계산
    total_cost_impact = df_today["trade_cost_impact_pct"].sum().round(4)
    
    print(f"💸 Total Trade Cost Impact: {total_cost_impact}%")

    # 기존 파일 있으면 오늘 row 제거 후 병합
    if os.path.exists(filepath):
        try:
            old_df = pd.read_csv(filepath)

            if not old_df.empty and "date" in old_df.columns:
                old_df["date"] = old_df["date"].astype(str)
                old_df = old_df[old_df["date"] != today].copy()

            df = pd.concat([old_df, df_today], ignore_index=True)

        except Exception:
            df = df_today
    else:
        df = df_today

    os.makedirs("data", exist_ok=True)
    df.to_csv(filepath, index=False)

    print(f"✅ Trade log saved/updated: {today}")
    print(f"✅ File path: {filepath}")


def load_previous_exposure(filepath: str = "data/paper_portfolio_log.csv") -> float:
    """
    paper_portfolio_log.csv에서 가장 최근 저장된 total_exposure를 읽는다.
    - 오늘 row는 제외하고, 직전 거래/리포트 날짜의 exposure를 반환
    - 없으면 50.0 반환
    """
    today = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(filepath):
        return 50.0

    try:
        df = pd.read_csv(filepath)
    except Exception:
        return 50.0

    if df.empty or "date" not in df.columns or "total_exposure" not in df.columns:
        return 50.0

    df["date"] = df["date"].astype(str)

    # 오늘 row는 제외해야 진짜 prev_exposure가 됨
    df = df[df["date"] != today].copy()

    if df.empty:
        return 50.0

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    if df.empty:
        return 50.0

    val = df.iloc[-1].get("total_exposure")

    try:
        return float(val)
    except Exception:
        return 50.0

def load_previous_weights(filepath: str = "data/paper_portfolio_log.csv") -> dict:
    """
    오늘 row를 제외하고 직전 ETF weights를 가져온다.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(filepath):
        return {}

    try:
        df = pd.read_csv(filepath)
    except Exception:
        return {}

    if df.empty or "date" not in df.columns:
        return {}

    df["date"] = df["date"].astype(str)
    df = df[df["date"] != today].copy()

    if df.empty:
        return {}

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    if df.empty:
        return {}

    last = df.iloc[-1].to_dict()

    ignore_cols = {"date", "CASH", "total_exposure"}
    weights = {}

    for k, v in last.items():
        if k in ignore_cols:
            continue
        try:
            if pd.notna(v):
                weights[k] = float(v)
        except Exception:
            continue

    return weights

def save_paper_portfolio(weights: Dict[str, float], cash_weight: float, exposure: float) -> None:
    """
    페이퍼 포트폴리오를 CSV에 저장한다.
    - 같은 날짜가 이미 있으면 기존 row를 삭제하고 최신 값으로 덮어쓴다.
    - weights는 ETF 티커 기준 비중 딕셔너리여야 한다.
      예: {"XLK": 22.4, "XLI": 22.4, "XLY": 14.9, "XLF": 5.2}
    """

    filepath = "data/paper_portfolio_log.csv"
    today = datetime.now().strftime("%Y-%m-%d")

    # 1) 기존 파일 로드
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
        except Exception:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    # 2) 같은 날짜 기존 row 제거 (오버라이트용)
    if not df.empty and "date" in df.columns:
        df["date"] = df["date"].astype(str)
        df = df[df["date"] != today].copy()

    # 3) 새 row 생성
    new_row = {"date": today}

    for ticker, weight in weights.items():
        new_row[ticker] = round(float(weight), 2)

    new_row["CASH"] = round(float(cash_weight), 2)
    new_row["total_exposure"] = round(float(exposure), 2)

    # 4) 새 row 추가
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # 5) 컬럼 정리
    fixed_cols = ["date"]
    tail_cols = ["CASH", "total_exposure"]

    dynamic_cols = [c for c in df.columns if c not in fixed_cols + tail_cols]
    dynamic_cols = sorted(dynamic_cols)

    ordered_cols = fixed_cols + dynamic_cols + tail_cols
    df = df.reindex(columns=ordered_cols)

    # 6) 날짜순 정렬
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # 7) 저장
    os.makedirs("data", exist_ok=True)
    df.to_csv(filepath, index=False)

    print(f"✅ Portfolio saved/updated: {today}")
    print(f"✅ File path: {filepath}")


if __name__ == "__main__":
    test_weights = {
        "XLK": 22.4,
        "XLI": 22.4,
        "XLY": 14.9,
        "XLF": 5.2,
    }

    save_paper_portfolio(
        weights=test_weights,
        cash_weight=35.0,
        exposure=65.0,
    )
