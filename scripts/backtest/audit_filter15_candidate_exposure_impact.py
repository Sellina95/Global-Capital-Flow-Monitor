from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

POSITIONS_PATH = (
    RESULT_DIR
    / "daily_positions.csv"
)

PANEL_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter15_candidate_exposure_impact_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter15_candidate_exposure_impact_summary.csv"
)


# =========================================================
# Helpers
# =========================================================

def clamp_exposure(x: float) -> float:
    return max(
        0.0,
        min(
            100.0,
            float(round(x)),
        ),
    )


def annualized_metrics(
    returns: pd.Series,
) -> dict:

    r = pd.to_numeric(
        returns,
        errors="coerce",
    ).dropna()

    if len(r) == 0:
        return {
            "total_return": np.nan,
            "cagr": np.nan,
            "mdd": np.nan,
            "volatility": np.nan,
            "sharpe": np.nan,
        }

    equity = (
        1.0 + r
    ).cumprod()

    total_return = (
        equity.iloc[-1] - 1.0
    )

    years = len(r) / 252.0

    cagr = (
        equity.iloc[-1] ** (1.0 / years)
        - 1.0
        if years > 0
        else np.nan
    )

    running_max = equity.cummax()

    drawdown = (
        equity
        /
        running_max
        - 1.0
    )

    mdd = drawdown.min()

    volatility = (
        r.std(ddof=1)
        * np.sqrt(252.0)
    )

    annual_return = (
        r.mean()
        * 252.0
    )

    sharpe = (
        annual_return / volatility
        if volatility > 0
        else np.nan
    )

    return {
        "total_return":
            total_return * 100.0,

        "cagr":
            cagr * 100.0,

        "mdd":
            mdd * 100.0,

        "volatility":
            volatility * 100.0,

        "sharpe":
            sharpe,
    }


# =========================================================
# Main
# =========================================================

def main() -> None:

    positions = pd.read_csv(
        POSITIONS_PATH
    )

    panel = pd.read_csv(
        PANEL_PATH
    )

    positions["signal_date"] = pd.to_datetime(
        positions["signal_date"],
        errors="coerce",
    )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"],
        errors="coerce",
    )

    positions = (
        positions
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    panel = (
        panel
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    # =====================================================
    # Attach PIT inputs
    # =====================================================

    panel["SPY"] = pd.to_numeric(
        panel["SPY"],
        errors="coerce",
    )

    panel["positioning__SP500_POS_Z"] = (
        pd.to_numeric(
            panel[
                "positioning__SP500_POS_Z"
            ],
            errors="coerce",
        )
    )

    panel["liquidity__NET_LIQ"] = (
        pd.to_numeric(
            panel[
                "liquidity__NET_LIQ"
            ],
            errors="coerce",
        )
    )

    panel["net_liq_20d_change"] = (
        panel["liquidity__NET_LIQ"]
        -
        panel[
            "liquidity__NET_LIQ"
        ].shift(20)
    )

    df = positions.merge(
        panel[
            [
                "signal_date",
                "SPY",
                "positioning__SP500_POS_Z",
                "liquidity__NET_LIQ",
                "net_liq_20d_change",
            ]
        ],
        on="signal_date",
        how="left",
    )

    # =====================================================
    # Numeric
    # =====================================================

    for col in [
        "risk_budget_13",
        "exposure_15",
        "hy_oas_today",
        "vix_today",
    ]:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce",
        )

    # =====================================================
    # SPY next-day return
    #
    # signal_date t 의 exposure가
    # 다음 거래일 수익률에 적용된다는 가정.
    # =====================================================

    df["spy_next_return"] = (
        df["SPY"]
        .pct_change()
        .shift(-1)
    )

    # =====================================================
    # Identify production Credit Deadman
    # =====================================================

    df["credit_deadman"] = (
        df["sew_status"]
        .astype(str)
        .eq("HARD_DEADMAN")
        &
        df["deadman_reason"]
        .astype(str)
        .str.contains(
            "Credit Crisis",
            case=False,
            na=False,
        )
    )

    # =====================================================
    # Candidate State Machine
    #
    # Entry:
    #   Production Credit Deadman 그대로
    #
    # Release:
    #   HY < 6
    #   VIX < 30
    #   3 trading days persistence
    #   POS_Z < 1.5
    #   NET_LIQ 20D change >= 0
    #
    # 중요:
    # Candidate는 Deadman ENTRY를 절대 변경하지 않는다.
    # =====================================================

    candidate_exposure = []

    candidate_deadman_active = False
    recovery_streak = 0

    candidate_release_event = []

    for idx, row in df.iterrows():

        prod_exposure = float(
            row["exposure_15"]
        )

        is_credit_deadman = bool(
            row["credit_deadman"]
        )

        hy = row["hy_oas_today"]
        vix = row["vix_today"]

        pos_z = row[
            "positioning__SP500_POS_Z"
        ]

        liq_20d = row[
            "net_liq_20d_change"
        ]

        released_today = False

        # -------------------------------------------------
        # Deadman Entry
        # -------------------------------------------------

        if is_credit_deadman:
            candidate_deadman_active = True
            recovery_streak = 0

            candidate_exposure.append(
                0.0
            )

            candidate_release_event.append(
                False
            )

            continue

        # -------------------------------------------------
        # Not inside Credit Deadman state
        # -------------------------------------------------

        if not candidate_deadman_active:

            candidate_exposure.append(
                prod_exposure
            )

            candidate_release_event.append(
                False
            )

            continue

        # -------------------------------------------------
        # Candidate Recovery State
        # -------------------------------------------------

        recovery_condition = (
            pd.notna(hy)
            and float(hy) < 6.0
            and pd.notna(vix)
            and float(vix) < 30.0
        )

        if recovery_condition:
            recovery_streak += 1
        else:
            recovery_streak = 0

        confirmation_ok = (
            recovery_streak >= 3
            and pd.notna(pos_z)
            and float(pos_z) < 1.5
            and pd.notna(liq_20d)
            and float(liq_20d) >= 0.0
        )

        # -------------------------------------------------
        # Candidate Release
        # -------------------------------------------------

        if confirmation_ok:

            candidate_deadman_active = False

            released_today = True

            # Release 당일부터
            # Production Filter15 exposure를 다시 허용.
            #
            # 즉 다른 volatility / positioning /
            # credit multiplier는 Production 값 그대로 사용.
            candidate_exposure.append(
                prod_exposure
            )

        else:

            candidate_exposure.append(
                0.0
            )

        candidate_release_event.append(
            released_today
        )

    df["candidate_exposure_15"] = (
        candidate_exposure
    )

    df["candidate_release_event"] = (
        candidate_release_event
    )

    # =====================================================
    # Exposure-only Counterfactual Return
    #
    # Filter15 영향만 격리하기 위해
    # SPY를 동일 underlying proxy로 사용.
    #
    # 이것은 Filter18 portfolio return이 아님.
    # =====================================================

    df["baseline_return"] = (
        df["spy_next_return"]
        *
        df["exposure_15"]
        /
        100.0
    )

    df["candidate_return"] = (
        df["spy_next_return"]
        *
        df["candidate_exposure_15"]
        /
        100.0
    )

    # =====================================================
    # Metrics
    # =====================================================

    baseline_metrics = annualized_metrics(
        df["baseline_return"]
    )

    candidate_metrics = annualized_metrics(
        df["candidate_return"]
    )

    summary = pd.DataFrame(
        [
            {
                "scenario":
                    "BASELINE_FILTER15",

                "avg_exposure":
                    df[
                        "exposure_15"
                    ].mean(),

                "zero_exposure_days":
                    int(
                        (
                            df[
                                "exposure_15"
                            ]
                            == 0
                        ).sum()
                    ),

                "release_events":
                    np.nan,

                **baseline_metrics,
            },

            {
                "scenario":
                    "CANDIDATE_RELEASE_GATE",

                "avg_exposure":
                    df[
                        "candidate_exposure_15"
                    ].mean(),

                "zero_exposure_days":
                    int(
                        (
                            df[
                                "candidate_exposure_15"
                            ]
                            == 0
                        ).sum()
                    ),

                "release_events":
                    int(
                        df[
                            "candidate_release_event"
                        ].sum()
                    ),

                **candidate_metrics,
            },
        ]
    )

    # =====================================================
    # Diagnostics
    # =====================================================

    df["exposure_difference"] = (
        df["candidate_exposure_15"]
        -
        df["exposure_15"]
    )

    changed_days = int(
        (
            df["exposure_difference"]
            .abs()
            >
            1e-9
        ).sum()
    )

    # Candidate release should only delay exposure,
    # never create more exposure than production.
    invalid_increase_days = int(
        (
            df["candidate_exposure_15"]
            >
            df["exposure_15"] + 1e-9
        ).sum()
    )

    # =====================================================
    # Save
    # =====================================================

    detail_cols = [
        "signal_date",
        "risk_budget_13",
        "exposure_15",
        "candidate_exposure_15",
        "exposure_difference",
        "sew_status",
        "deadman_reason",
        "hy_oas_today",
        "vix_today",
        "positioning__SP500_POS_Z",
        "net_liq_20d_change",
        "candidate_release_event",
        "spy_next_return",
        "baseline_return",
        "candidate_return",
    ]

    df[
        detail_cols
    ].to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # =====================================================
    # Report
    # =====================================================

    print("=" * 82)
    print(
        "FILTER15 CANDIDATE EXPOSURE IMPACT AUDIT"
    )
    print("=" * 82)

    print(
        summary.to_string(
            index=False
        )
    )

    print()

    print(
        f"Exposure changed days      : "
        f"{changed_days:,}"
    )

    print(
        f"Invalid exposure increases : "
        f"{invalid_increase_days:,}"
    )

    print(
        f"Candidate release events   : "
        f"{int(df['candidate_release_event'].sum()):,}"
    )

    print()

    print("Saved:")
    print(DETAIL_PATH)
    print(SUMMARY_PATH)


if __name__ == "__main__":
    main()