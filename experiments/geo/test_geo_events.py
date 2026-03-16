from __future__ import annotations

import sys
import os
from pathlib import Path

import pandas as pd
import numpy as np


# ------------------------------------------------------------
# PROJECT ROOT PATH FIX
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

print("PROJECT_ROOT =", PROJECT_ROOT)


# ------------------------------------------------------------
# LOAD MACRO DATA
# ------------------------------------------------------------

MACRO_PATH = PROJECT_ROOT / "macro_data.csv"

print("MACRO_PATH =", MACRO_PATH)
print("MACRO_PATH exists =", MACRO_PATH.exists())

df = pd.read_csv(MACRO_PATH)

df["date"] = pd.to_datetime(df["date"])
df = df.set_index("date")
df = df.sort_index()


# ------------------------------------------------------------
# CREATE RETURN (SPY 기반)
# ------------------------------------------------------------

df["Return"] = df["SPY"].pct_change()


# ------------------------------------------------------------
# CREATE GEO STRESS SCORE (v1)
# ------------------------------------------------------------

df["Geo Stress Score"] = (
    (df["VIX"] > 25).astype(int)
    + (df["DXY"] > df["DXY"].rolling(20).mean()).astype(int)
    + (df["EMB"].pct_change() < -0.01).astype(int)
)


# ------------------------------------------------------------
# BACKTEST FUNCTION
# ------------------------------------------------------------

def backtest_strategy(df: pd.DataFrame, crisis_dates: list, risk_threshold: float, window: int):

    results = []

    crisis_dates = pd.to_datetime(crisis_dates)

    for date in crisis_dates:

        start_date = date - pd.Timedelta(days=window)
        end_date = date + pd.Timedelta(days=window)

        print("\nProcessing crisis date:", date)
        print("Window:", start_date, "~", end_date)

        df_window = df[(df.index >= start_date) & (df.index <= end_date)]

        if df_window.empty:
            print("No data in window")
            continue

        geo_stress_score = df_window["Geo Stress Score"].iloc[-1]

        print("Geo Stress Score:", geo_stress_score)

        window_return = df_window["Return"].sum()

        results.append(window_return)

    if len(results) == 0:
        return None

    return np.mean(results)


# ------------------------------------------------------------
# CRISIS EVENTS
# ------------------------------------------------------------

crisis_dates = [
    "2022-02-24",   # Ukraine invasion
    "2023-10-07",   # Israel war
]


# ------------------------------------------------------------
# RUN BACKTEST
# ------------------------------------------------------------

result = backtest_strategy(
    df,
    crisis_dates,
    risk_threshold=1.0,
    window=5
)


if result is not None:

    print("\nBacktest Result =", result)

else:

    print("No valid backtest results.")