from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "daily_positions.csv"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

DETAIL_OUTPUT = (
    OUTPUT_DIR
    / "credit_deadman_counterfactual_detail.csv"
)

SUMMARY_OUTPUT = (
    OUTPUT_DIR
    / "credit_deadman_counterfactual_summary.csv"
)


# ============================================================
# Counterfactual Recovery Condition
#
# 목적:
# Credit Crisis 이후 recovery phase에서
# Hard Deadman이 과도하게 유지되었는지 확인
#
# Production 수정 X
# ============================================================

def recovery_condition(
    df: pd.DataFrame,
    idx: int,
) -> bool:

    row = df.iloc[idx]

    hy = row.get("hy_oas_today")
    vix = row.get("vix_today")
    macro = str(
        row.get(
            "macro_narrative",
            "",
        )
    ).upper()

    if pd.isna(hy) or pd.isna(vix):
        return False

    # 현재 Credit Stress
    if hy < 6:
        return False

    # VIX 안정
    if vix >= 30:
        return False

    # Credit crisis narrative 제외
    if "CREDIT_STRESS" in macro:
        return False

    # HY OAS 방향 개선 확인
    if idx < 20:
        return False

    hy_20d_ago = df.iloc[idx - 20]["hy_oas_today"]

    if pd.isna(hy_20d_ago):
        return False

    hy_improving = hy < hy_20d_ago

    return bool(hy_improving)


def main():

    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    df = pd.read_csv(INPUT)

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )

    numeric_cols = [
        "risk_budget_13",
        "exposure_15",
        "hy_oas_today",
        "vix_today",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    # --------------------------------------------------------
    # 2008-2010 First Validation
    # --------------------------------------------------------

    df = df[
        (
            df["signal_date"]
            >= pd.Timestamp("2008-12-01")
        )
        &
        (
            df["signal_date"]
            <= pd.Timestamp("2010-12-31")
        )
    ].reset_index(drop=True)


    rows = []

    for idx, row in df.iterrows():

        production_deadman = (
            str(row.get("sew_status"))
            == "HARD_DEADMAN"
        )

        counterfactual_release = False

        if production_deadman:
            counterfactual_release = recovery_condition(
                df,
                idx,
            )

        production_exposure = row[
            "exposure_15"
        ]

        counterfactual_exposure = (
            row["risk_budget_13"] * 0.4
            if counterfactual_release
            else production_exposure
        )

        rows.append(
            {
                "signal_date": row["signal_date"],
                "hy_oas": row["hy_oas_today"],
                "vix": row["vix_today"],
                "risk_budget_13": row[
                    "risk_budget_13"
                ],
                "production_exposure": production_exposure,
                "counterfactual_exposure": counterfactual_exposure,
                "production_deadman": production_deadman,
                "counterfactual_release": counterfactual_release,
                "macro_narrative": row[
                    "macro_narrative"
                ],
            }
        )


    result = pd.DataFrame(rows)

    result.to_csv(
        DETAIL_OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )


    summary = pd.DataFrame(
        [
            {
                "period":
                f"{result.signal_date.min().date()} ~ {result.signal_date.max().date()}",

                "days":
                len(result),

                "production_deadman_days":
                int(
                    result.production_deadman.sum()
                ),

                "counterfactual_release_days":
                int(
                    result.counterfactual_release.sum()
                ),

                "production_avg_exposure":
                result.production_exposure.mean(),

                "counterfactual_avg_exposure":
                result.counterfactual_exposure.mean(),

                "additional_exposure":
                (
                    result.counterfactual_exposure.mean()
                    -
                    result.production_exposure.mean()
                ),
            }
        ]
    )


    summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )


    print("=" * 70)
    print("CREDIT DEADMAN COUNTERFACTUAL AUDIT")
    print("=" * 70)

    print(
        f"Period : "
        f"{result.signal_date.min().date()} ~ "
        f"{result.signal_date.max().date()}"
    )

    print(
        f"Deadman days : "
        f"{int(result.production_deadman.sum())}"
    )

    print(
        f"Counterfactual release days : "
        f"{int(result.counterfactual_release.sum())}"
    )

    print()

    print(
        f"Production Avg Exposure : "
        f"{result.production_exposure.mean():.2f}"
    )

    print(
        f"Counterfactual Avg Exposure : "
        f"{result.counterfactual_exposure.mean():.2f}"
    )

    print(
        f"Additional Exposure : "
        f"{(
            result.counterfactual_exposure.mean()
            -
            result.production_exposure.mean()
        ):.2f}"
    )

    print("=" * 70)

    print(
        f"Saved:\n{DETAIL_OUTPUT}\n{SUMMARY_OUTPUT}"
    )


if __name__ == "__main__":
    main()