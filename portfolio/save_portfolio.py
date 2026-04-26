import os
from datetime import datetime
from typing import Dict

import pandas as pd


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
