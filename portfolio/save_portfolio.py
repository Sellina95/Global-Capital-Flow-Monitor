import os
import pandas as pd
from datetime import datetime


def save_paper_portfolio(weights: dict, cash_weight: float, exposure: float):
    """
    weights: {"XLK": 22.4, "XLI": 22.4 ...}
    cash_weight: 35.0
    exposure: 65.0
    """

    filepath = "data/paper_portfolio_log.csv"

    # 오늘 날짜
    today = datetime.now().strftime("%Y-%m-%d")

    # 한 줄 데이터 만들기
    row = {"date": today}

    for ticker, weight in weights.items():
        row[ticker] = round(weight, 2)

    row["CASH"] = round(cash_weight, 2)
    row["total_exposure"] = round(exposure, 2)

    df_new = pd.DataFrame([row])

    # 파일 있으면 이어붙이고, 없으면 새로 생성
    if os.path.exists(filepath):
        df_old = pd.read_csv(filepath)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    os.makedirs("data", exist_ok=True)
    df.to_csv(filepath, index=False)

    print(f"✅ Portfolio saved: {today}")
