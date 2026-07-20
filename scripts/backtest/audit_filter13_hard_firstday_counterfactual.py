from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[2]

ATTR_PATH = (
    ROOT
    / "data/backtest/results/filter13_budget_attribution_final_daily.csv"
)

MARKET_PATH = (
    ROOT
    / "data/backtest/macro_data.csv"
)

OUT_DAILY = (
    ROOT
    / "data/backtest/results/"
    "filter13_hard_firstday_counterfactual_daily.csv"
)

OUT_SUMMARY = (
    ROOT
    / "data/backtest/results/"
    "filter13_hard_firstday_counterfactual_summary.csv"
)


# ============================================================
# Load
# ============================================================

d = pd.read_csv(ATTR_PATH)
m = pd.read_csv(MARKET_PATH)

d["date"] = pd.to_datetime(d["date"])
m["date"] = pd.to_datetime(m["date"])

m["SPY"] = pd.to_numeric(
    m["SPY"],
    errors="coerce",
)

d = (
    d.merge(
        m[["date", "SPY"]],
        on="date",
        how="left",
    )
    .sort_values("date")
    .reset_index(drop=True)
)


# ============================================================
# Identify HARD regime
# ============================================================

d["is_hard"] = (
    d["market_regime"]
    .fillna("")
    .str.upper()
    .str.startswith("HARD RISK-OFF")
)


# First day of each HARD episode
d["prev_is_hard"] = (
    d["is_hard"]
    .shift(1)
    .fillna(False)
    .astype(bool)
)

d["hard_first_day"] = (
    d["is_hard"]
    & ~d["prev_is_hard"]
)


# ============================================================
# Counterfactual scenarios
#
# CURRENT:
#   기존 Filter13 final_budget 그대로
#
# CF30:
#   HARD 최초 진입일에만
#   20 cap 대신 최소한 30까지 허용
#
# CF35:
#   HARD 최초 진입일에만
#   20 cap 대신 최소한 35까지 허용
#
# IMPORTANT:
#   pre_cap_budget 이상으로 올리지 않는다.
#   HARD가 다음 날에도 지속되면 기존 20 cap 그대로.
# ============================================================

d["budget_current"] = (
    pd.to_numeric(
        d["final_budget"],
        errors="coerce",
    )
)

d["pre_cap_budget_num"] = (
    pd.to_numeric(
        d["pre_cap_budget"],
        errors="coerce",
    )
)


def make_counterfactual(first_day_floor):
    out = d["budget_current"].copy()

    mask = (
        d["hard_first_day"]
        & (d["budget_current"] <= 20)
    )

    buffered = np.minimum(
        d.loc[mask, "pre_cap_budget_num"],
        first_day_floor,
    )

    # 기존보다 낮아지는 counterfactual은 허용하지 않음
    buffered = np.maximum(
        buffered,
        d.loc[mask, "budget_current"],
    )

    out.loc[mask] = buffered

    return out


d["budget_cf30"] = make_counterfactual(30)
d["budget_cf35"] = make_counterfactual(35)


# ============================================================
# SPY next-day return
#
# Signal date budget은 다음 trading-day return에 적용한다고 가정.
# Look-ahead 방지를 위해 미래 수익률은 성과 평가에만 사용.
# ============================================================

d["spy_ret_next"] = (
    d["SPY"]
    .shift(-1)
    / d["SPY"]
    - 1
)


# ============================================================
# Strategy return approximation
#
# Filter13 budget 효과만 격리하기 위한 counterfactual.
# Filter15 / Filter18 / transaction cost는 여기서 재구성하지 않는다.
#
# 목적:
# HARD 최초일 cap 강도 차이가
# 방향적으로 어떤 효과를 냈는지 확인.
# ============================================================

for name in [
    "current",
    "cf30",
    "cf35",
]:
    d[f"ret_{name}"] = (
        d[f"budget_{name}"]
        / 100.0
        * d["spy_ret_next"]
    )


# ============================================================
# Equity curves
# ============================================================

for name in [
    "current",
    "cf30",
    "cf35",
]:
    d[f"equity_{name}"] = (
        1.0
        + d[f"ret_{name}"].fillna(0)
    ).cumprod()


# ============================================================
# Metrics
# ============================================================

def max_drawdown(equity):
    peak = equity.cummax()
    dd = equity / peak - 1
    return dd.min()


def total_return(equity):
    if len(equity) == 0:
        return np.nan

    return (
        equity.iloc[-1]
        / equity.iloc[0]
        - 1
    )


summary_rows = []

for name in [
    "current",
    "cf30",
    "cf35",
]:

    summary_rows.append(
        {
            "scenario": name,
            "avg_budget":
                d[f"budget_{name}"].mean(),

            "total_return":
                total_return(
                    d[f"equity_{name}"]
                ),

            "max_drawdown":
                max_drawdown(
                    d[f"equity_{name}"]
                ),

            "hard_first_days":
                int(
                    d["hard_first_day"].sum()
                ),

            "avg_budget_on_hard_first_day":
                d.loc[
                    d["hard_first_day"],
                    f"budget_{name}",
                ].mean(),
        }
    )

summary = pd.DataFrame(summary_rows)


# ============================================================
# First-day specific attribution
# ============================================================

first = (
    d[
        d["hard_first_day"]
    ]
    .copy()
)

first["lift_cf30"] = (
    first["budget_cf30"]
    - first["budget_current"]
)

first["lift_cf35"] = (
    first["budget_cf35"]
    - first["budget_current"]
)

first["return_effect_cf30"] = (
    first["ret_cf30"]
    - first["ret_current"]
)

first["return_effect_cf35"] = (
    first["ret_cf35"]
    - first["ret_current"]
)


# ============================================================
# Print
# ============================================================

print(
    "\n=== FILTER13 HARD FIRST-DAY "
    "COUNTERFACTUAL AUDIT ==="
)

print("\n[PERIOD]")
print("ROWS:", len(d))
print(
    "FROM:",
    d["date"].min().date(),
)
print(
    "TO  :",
    d["date"].max().date(),
)

print("\n[HARD FIRST DAYS]")
print(
    "COUNT:",
    int(
        d["hard_first_day"].sum()
    ),
)

print(
    "\n=== SCENARIO SUMMARY ==="
)

print(
    summary.to_string(
        index=False
    )
)


print(
    "\n=== HARD FIRST-DAY "
    "BUDGET COMPARISON ==="
)

cols = [
    "date",
    "market_regime",
    "macro_narrative",
    "pre_cap_budget",
    "budget_current",
    "budget_cf30",
    "budget_cf35",
    "spy_ret_next",
    "return_effect_cf30",
    "return_effect_cf35",
]

print(
    first[cols]
    .to_string(
        index=False
    )
)


print(
    "\n=== AGGREGATE FIRST-DAY EFFECT ==="
)

print(
    "AVG CURRENT BUDGET:",
    round(
        first[
            "budget_current"
        ].mean(),
        3,
    ),
)

print(
    "AVG CF30 BUDGET:",
    round(
        first[
            "budget_cf30"
        ].mean(),
        3,
    ),
)

print(
    "AVG CF35 BUDGET:",
    round(
        first[
            "budget_cf35"
        ].mean(),
        3,
    ),
)

print(
    "\nCF30 TOTAL RETURN EFFECT:",
    round(
        first[
            "return_effect_cf30"
        ].sum()
        * 100,
        3,
    ),
    "%",
)

print(
    "CF35 TOTAL RETURN EFFECT:",
    round(
        first[
            "return_effect_cf35"
        ].sum()
        * 100,
        3,
    ),
    "%",
)


# ============================================================
# Save
# ============================================================

d.to_csv(
    OUT_DAILY,
    index=False,
)

summary.to_csv(
    OUT_SUMMARY,
    index=False,
)

print(
    "\n[SAVED]",
    OUT_DAILY,
)

print(
    "[SAVED]",
    OUT_SUMMARY,
)

print(
    "\nAUDIT COMPLETE."
)

print(
    "This is a counterfactual diagnostic only."
)

print(
    "No production Filter13 logic was modified."
)

print(
    "Forward returns are EX-POST evaluation only."
)