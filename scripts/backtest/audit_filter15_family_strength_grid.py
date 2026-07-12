from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "data" / "backtest" / "results"

INPUT_PATH = RESULT_DIR / "filter15_brake_strength_daily.csv"
SUMMARY_OUT = RESULT_DIR / "filter15_family_strength_grid.csv"
TEXT_OUT = RESULT_DIR / "filter15_family_strength_grid.txt"

TRADING_DAYS = 252
RESTORE_RATES = (0.25, 0.50, 0.75, 1.00)

FAMILIES = {
    "volatility": "volatility_reduction",
    "positioning": "positioning_reduction",
    "credit": "credit_reduction",
}


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def cagr(returns: pd.Series) -> float:
    values = numeric(returns).dropna()

    if values.empty:
        return np.nan

    wealth = (1.0 + values).prod()
    years = len(values) / TRADING_DAYS

    if wealth <= 0 or years <= 0:
        return np.nan

    return float(wealth ** (1.0 / years) - 1.0)


def mdd(returns: pd.Series) -> float:
    equity = (1.0 + numeric(returns).fillna(0.0)).cumprod()
    drawdown = equity / equity.cummax() - 1.0

    return float(drawdown.min())


def volatility(returns: pd.Series) -> float:
    values = numeric(returns).dropna()

    if len(values) < 2:
        return np.nan

    return float(values.std(ddof=1) * np.sqrt(TRADING_DAYS))


def sharpe(returns: pd.Series) -> float:
    values = numeric(returns).dropna()

    if len(values) < 2:
        return np.nan

    std = values.std(ddof=1)

    if std <= 1e-12:
        return np.nan

    return float(
        values.mean() / std * np.sqrt(TRADING_DAYS)
    )


def calmar(cagr_value: float, mdd_value: float) -> float:
    if (
        not np.isfinite(cagr_value)
        or not np.isfinite(mdd_value)
        or abs(mdd_value) <= 1e-12
    ):
        return np.nan

    return float(cagr_value / abs(mdd_value))


def metrics(
    exposure: pd.Series,
    spy_return: pd.Series,
) -> dict[str, float]:
    strategy_return = (
        numeric(exposure) / 100.0
        * numeric(spy_return)
    )

    cagr_value = cagr(strategy_return)
    mdd_value = mdd(strategy_return)

    return {
        "average_exposure": float(exposure.mean()),
        "cagr": cagr_value,
        "mdd": mdd_value,
        "volatility": volatility(strategy_return),
        "sharpe": sharpe(strategy_return),
        "calmar": calmar(cagr_value, mdd_value),
    }


def classify(row: pd.Series) -> str:
    if row["scenario"] == "baseline":
        return "BASELINE"

    cagr_gain = row["cagr_change"]
    mdd_change = row["mdd_change"]
    sharpe_change = row["sharpe_change"]
    calmar_change = row["calmar_change"]

    if (
        cagr_gain >= 0.0025
        and mdd_change >= -0.015
        and (
            sharpe_change > 0
            or calmar_change > 0
        )
    ):
        return "BRAKE_TOO_STRONG"

    if (
        cagr_gain <= 0.001
        and (
            sharpe_change < 0
            or calmar_change < 0
        )
    ):
        return "CURRENT_STRENGTH_JUSTIFIED"

    if (
        cagr_gain > 0
        and (
            sharpe_change > 0
            or calmar_change > 0
        )
    ):
        return "MILD_OVERBRAKING"

    return "NO_IMPROVEMENT"


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"{INPUT_PATH}\n"
            "Run audit_filter15_brake_strength.py first."
        )

    df = pd.read_csv(INPUT_PATH)

    required = {
        "existing_exposure_15",
        "risk_budget_13",
        "spy_next_return",
        "replay_exact_match",
        "deadman_reduction",
        *FAMILIES.values(),
    }

    missing = sorted(required - set(df.columns))

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    for column in required - {"replay_exact_match"}:
        df[column] = numeric(df[column])

    df["replay_exact_match"] = (
        df["replay_exact_match"]
        .astype(str)
        .str.lower()
        .isin({"true", "1", "yes"})
    )

    baseline_exposure = (
        df["existing_exposure_15"]
        .clip(lower=0.0, upper=100.0)
    )

    baseline_metrics = metrics(
        baseline_exposure,
        df["spy_next_return"],
    )

    rows = [{
        "family": "baseline",
        "restore_rate": 0.0,
        "scenario": "baseline",
        **baseline_metrics,
    }]

    for family, reduction_column in FAMILIES.items():
        for restore_rate in RESTORE_RATES:
            restored_exposure = (
                baseline_exposure
                + df[reduction_column].fillna(0.0)
                * restore_rate
            )

            # 기계적 replay가 맞은 날짜만 완화
            restored_exposure = restored_exposure.where(
                df["replay_exact_match"],
                baseline_exposure,
            )

            # 13번 Risk Budget 이상으로는 올리지 않음
            restored_exposure = np.minimum(
                restored_exposure,
                df["risk_budget_13"],
            )

            # Deadman은 절대 완화하지 않음
            deadman_active = (
                df["deadman_reduction"] > 1e-10
            )

            restored_exposure = restored_exposure.where(
                ~deadman_active,
                baseline_exposure,
            )

            scenario_metrics = metrics(
                restored_exposure,
                df["spy_next_return"],
            )

            rows.append({
                "family": family,
                "restore_rate": restore_rate,
                "scenario": (
                    f"{family}_{int(restore_rate * 100)}pct_restored"
                ),
                **scenario_metrics,
            })

    result = pd.DataFrame(rows)

    for metric in (
        "average_exposure",
        "cagr",
        "mdd",
        "sharpe",
        "calmar",
    ):
        result[f"{metric}_change"] = (
            result[metric]
            - baseline_metrics[metric]
        )

    result["verdict"] = result.apply(
        classify,
        axis=1,
    )

    result.to_csv(
        SUMMARY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    lines = [
        "=" * 105,
        "FILTER 15 FAMILY-BY-FAMILY BRAKE STRENGTH GRID",
        "=" * 105,
        "",
        (
            "Baseline: "
            f"Exposure {baseline_metrics['average_exposure']:.2f}% | "
            f"CAGR {baseline_metrics['cagr']:.2%} | "
            f"MDD {baseline_metrics['mdd']:.2%} | "
            f"Sharpe {baseline_metrics['sharpe']:.3f} | "
            f"Calmar {baseline_metrics['calmar']:.3f}"
        ),
        "",
    ]

    for family in FAMILIES:
        lines.append(f"{family.upper()}")
        lines.append("-" * 105)

        family_rows = result.loc[
            result["family"].eq(family)
        ]

        for _, row in family_rows.iterrows():
            lines.append(
                f"Restore {row['restore_rate']:.0%} | "
                f"Exposure {row['average_exposure']:.2f}% "
                f"({row['average_exposure_change']:+.2f}%p) | "
                f"CAGR {row['cagr']:.2%} "
                f"({row['cagr_change']:+.2%}) | "
                f"MDD {row['mdd']:.2%} "
                f"({row['mdd_change']:+.2%}) | "
                f"Sharpe {row['sharpe']:.3f} "
                f"({row['sharpe_change']:+.3f}) | "
                f"Calmar {row['calmar']:.3f} "
                f"({row['calmar_change']:+.3f}) | "
                f"{row['verdict']}"
            )

        lines.append("")

    lines.extend([
        "판정",
        "----",
        "BRAKE_TOO_STRONG: 완화 후 CAGR과 위험조정 성과가 함께 개선.",
        "MILD_OVERBRAKING: 일부 개선 증거.",
        "CURRENT_STRENGTH_JUSTIFIED: CAGR 개선은 거의 없고 위험조정 성과 악화.",
        "NO_IMPROVEMENT: 완화할 경제적 근거 없음.",
        "",
        "Deadman은 모든 시나리오에서 그대로 유지했다.",
        "원본 전략 코드는 수정하지 않았다.",
        "=" * 105,
    ])

    text = "\n".join(lines)

    TEXT_OUT.write_text(
        text,
        encoding="utf-8",
    )

    print(text)
    print()
    print(f"Saved: {SUMMARY_OUT}")
    print(f"Saved: {TEXT_OUT}")


if __name__ == "__main__":
    main()