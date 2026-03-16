import pandas as pd
import numpy as np

# --------------------------------------------------
# LOAD SOURCE DATA
# --------------------------------------------------

macro = pd.read_csv("macro_data.csv")
credit = pd.read_csv("data/credit_spread_data.csv")

macro["date"] = pd.to_datetime(macro["date"])
credit["date"] = pd.to_datetime(credit["date"])

macro = macro.sort_values("date")
credit = credit.sort_values("date")

# 필요한 컬럼만
macro = macro[["date", "VIX", "HYG", "LQD"]]
credit = credit[["date", "HY_OAS"]]

# 병합
df = pd.merge(macro, credit, on="date", how="left")

# --------------------------------------------------
# FEATURE ENGINEERING
# --------------------------------------------------

# HYG/LQD ratio
df["hyg_lqd"] = df["HYG"] / df["LQD"]

# 컬럼명 맞추기
df["vix"] = df["VIX"]
df["hy_oas"] = df["HY_OAS"]

# --------------------------------------------------
# SIMPLE SENTIMENT PROXY LOGIC (v1)
# --------------------------------------------------
# 점수 높을수록 risk-off / stress 쪽으로 단순 설계
# 50을 중립 baseline으로 사용

score = pd.Series(50.0, index=df.index)

# VIX 조건
score += np.where(df["vix"] > 30, 20, 0)
score += np.where((df["vix"] > 25) & (df["vix"] <= 30), 10, 0)
score += np.where((df["vix"] < 15), -5, 0)

# HY OAS 조건
score += np.where(df["hy_oas"] > 5.0, 20, 0)
score += np.where((df["hy_oas"] > 4.0) & (df["hy_oas"] <= 5.0), 10, 0)
score += np.where(df["hy_oas"] < 3.0, -5, 0)

# HYG/LQD ratio 조건
score += np.where(df["hyg_lqd"] < 0.72, 10, 0)
score += np.where(df["hyg_lqd"] > 0.78, -5, 0)

# 결측이 있으면 기본 fallback
used = np.where(
    df["vix"].notna() & df["hy_oas"].notna() & df["hyg_lqd"].notna(),
    "model",
    "fallback"
)

df["sentiment_proxy"] = score.clip(lower=0, upper=100)
df["used"] = used

# --------------------------------------------------
# OUTPUT FORMAT
# --------------------------------------------------

out = df[["date", "sentiment_proxy", "used", "vix", "hy_oas", "hyg_lqd"]].copy()
out["date"] = out["date"].dt.strftime("%Y-%m-%d")

out.to_csv("data/sentiment_proxy.csv", index=False, encoding="utf-8-sig")
print("Saved: data/sentiment_proxy.csv")