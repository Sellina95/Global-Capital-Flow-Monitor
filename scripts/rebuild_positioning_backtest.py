from pathlib import Path

import numpy as np
import pandas as pd


INPUT_PATH = Path("data/backtest/macro_data_2008.csv")
OUTPUT_PATH = Path("data/backtest/positioning_data.csv")
WINDOW = 252
MIN_Z_PERIODS = 21


def rolling_zscore(series: pd.Series) -> pd.Series:
    """현재 시점까지의 최근 252거래일 가격으로 Z-score 계산."""
    values = pd.to_numeric(series, errors="coerce")
    mean = values.rolling(WINDOW, min_periods=MIN_Z_PERIODS).mean()
    std = values.rolling(WINDOW, min_periods=MIN_Z_PERIODS).std()

    z = (values - mean) / std.replace(0, np.nan)
    return z.replace([np.inf, -np.inf], np.nan)


def build_positioning_proxy() -> None:
    df = pd.read_csv(INPUT_PATH)

    required = ["Date", "SPY", "^TNX", "DX-Y.NYB"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in {INPUT_PATH}: {missing}")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = (
        df.dropna(subset=["Date"])
        .sort_values("Date")
        .drop_duplicates("Date", keep="last")
        .reset_index(drop=True)
    )

    spy = pd.to_numeric(df["SPY"], errors="coerce")
    us10y = pd.to_numeric(df["^TNX"], errors="coerce")
    dxy = pd.to_numeric(df["DX-Y.NYB"], errors="coerce")

    # 운영 코드의 최근 1년 가격 Z-score를 과거 시계열로 재현
    sp500_z = rolling_zscore(spy)
    us10y_z = rolling_zscore(us10y)
    dxy_z = rolling_zscore(dxy)

    # 운영 코드와 동일한 CTA 추세 규칙
    ma50 = spy.rolling(50, min_periods=50).mean()
    ma200 = spy.rolling(200, min_periods=200).mean()

    cta_score = pd.Series(0.0, index=df.index)
    cta_score += np.where(spy > ma50, 0.5, 0.0)
    cta_score += np.where(spy < ma50, -0.5, 0.0)
    cta_score += np.where(spy > ma200, 0.5, 0.0)
    cta_score += np.where(spy < ma200, -0.5, 0.0)

    cta_ok = (
        spy.notna()
        & ma50.notna()
        & ma200.notna()
    ).astype(int)

    out = pd.DataFrame({
        "date": df["Date"].dt.strftime("%Y-%m-%d"),
        "SP500_POS_Z": sp500_z,
        "US10Y_POS_Z": us10y_z,
        "DXY_POS_Z": dxy_z,

        # 과거 옵션 OI가 없으므로 운영 코드의 중립 fallback 사용
        "DEALER_GAMMA_BIAS": 1.0,
        "CTA_MOMENTUM_SCORE": cta_score.where(cta_ok.eq(1), 0.0),
        "GAMMA_FETCH_OK": 0,
        "CTA_FETCH_OK": cta_ok,
    })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved: {OUTPUT_PATH}")
    print(f"Period: {out['date'].min()} ~ {out['date'].max()}")
    print(f"Rows: {len(out):,}")
    print("\nValid counts:")
    print(out.notna().sum().to_string())
    print("\nFirst usable positioning rows:")
    print(
        out.dropna(
            subset=["SP500_POS_Z", "US10Y_POS_Z", "DXY_POS_Z"]
        ).head(3).to_string(index=False)
    )
    print("\nLast rows:")
    print(out.tail(3).to_string(index=False))


if __name__ == "__main__":
    build_positioning_proxy()
