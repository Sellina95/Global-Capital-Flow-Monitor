from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

POSITIONS_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "daily_positions.csv"
)

FLOW_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter13_budget_attribution_current_daily.csv"
)

PANEL_PATH = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

DETAIL_OUTPUT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter15_credit_release_flow_confirmation_detail.csv"
)

SUMMARY_OUTPUT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "filter15_credit_release_flow_confirmation_summary.csv"
)


def main() -> None:

    # ============================================================
    # 1. LOAD
    # ============================================================

    positions = pd.read_csv(POSITIONS_PATH)
    flow = pd.read_csv(FLOW_PATH)
    panel = pd.read_csv(PANEL_PATH)

    for df in (positions, flow, panel):
        df["signal_date"] = pd.to_datetime(
            df["signal_date"],
            errors="coerce",
        )

    positions = (
        positions
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    flow = (
        flow
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .drop_duplicates("signal_date", keep="last")
    )

    panel = (
        panel
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .drop_duplicates("signal_date", keep="last")
    )

    # ============================================================
    # 2. CONTRACT CHECK
    # ============================================================

    required_position_cols = {
        "signal_date",
        "sew_status",
        "deadman_reason",
        "hy_oas_today",
        "vix_today",
    }

    missing = required_position_cols - set(positions.columns)

    if missing:
        raise ValueError(
            f"daily_positions.csv missing columns: {sorted(missing)}"
        )

    if "flow_score" not in flow.columns:
        raise ValueError(
            "filter13_budget_attribution_current_daily.csv에 "
            "'flow_score' 컬럼이 없습니다.\n"
            f"Available columns:\n{flow.columns.tolist()}"
        )

    if "SPY" not in panel.columns:
        raise ValueError("master_panel.csv missing SPY")

    # ============================================================
    # 3. NUMERIC
    # ============================================================

    positions["hy_oas_today"] = pd.to_numeric(
        positions["hy_oas_today"],
        errors="coerce",
    )

    positions["vix_today"] = pd.to_numeric(
        positions["vix_today"],
        errors="coerce",
    )

    flow["flow_score"] = pd.to_numeric(
        flow["flow_score"],
        errors="coerce",
    )

    panel["SPY"] = pd.to_numeric(
        panel["SPY"],
        errors="coerce",
    )

    # ============================================================
    # 4. ATTACH HISTORICAL FLOW + SPY
    # ============================================================

    df = positions.merge(
        flow[
            [
                "signal_date",
                "flow_score",
            ]
        ],
        on="signal_date",
        how="left",
    )

    df = df.merge(
        panel[
            [
                "signal_date",
                "SPY",
            ]
        ],
        on="signal_date",
        how="left",
    )

    df = (
        df
        .sort_values("signal_date")
        .reset_index(drop=True)
    )

    # ============================================================
    # 5. FORWARD RETURNS
    # ============================================================

    df["spy_return_20d"] = (
        df["SPY"].shift(-20)
        / df["SPY"]
        - 1.0
    ) * 100.0

    df["spy_return_60d"] = (
        df["SPY"].shift(-60)
        / df["SPY"]
        - 1.0
    ) * 100.0

    # ============================================================
    # 6. IDENTIFY CREDIT DEADMAN
    # ============================================================

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

    df["prev_credit_deadman"] = (
        df["credit_deadman"]
        .shift(1)
        .fillna(False)
        .astype(bool)
    )

    # ============================================================
    # 7. TRUE RELEASE EVENT
    #
    # 전일 = Credit HARD_DEADMAN
    # 금일 = Credit threshold 정상화 + VIX 안정
    #
    # 이것만 "Release Event"로 정의한다.
    # ============================================================

    df["base_release_event"] = (
        df["prev_credit_deadman"]
        &
        (df["hy_oas_today"] < 6.0)
        &
        (df["vix_today"] < 30.0)
    )

    # ============================================================
    # 8. FLOW CONFIRMATION SCENARIOS
    # ============================================================

    df["release_current"] = (
        df["base_release_event"]
    )

    df["release_flow_3"] = (
        df["base_release_event"]
        &
        (df["flow_score"] >= 3)
    )

    df["release_flow_5"] = (
        df["base_release_event"]
        &
        (df["flow_score"] >= 5)
    )

    # ============================================================
    # 9. SUMMARY FUNCTION
    # ============================================================

    def summarize(
        scenario: str,
        mask: pd.Series,
    ) -> dict:

        sample = df.loc[mask].copy()

        ret20 = sample["spy_return_20d"].dropna()
        ret60 = sample["spy_return_60d"].dropna()

        return {
            "scenario": scenario,

            "release_events":
                int(mask.sum()),

            "avg_flow_score":
                sample["flow_score"].mean(),

            "avg_spy_20d":
                ret20.mean(),

            "median_spy_20d":
                ret20.median(),

            "positive_20d_rate":
                (ret20 > 0).mean()
                if len(ret20)
                else float("nan"),

            "avg_spy_60d":
                ret60.mean(),

            "median_spy_60d":
                ret60.median(),

            "positive_60d_rate":
                (ret60 > 0).mean()
                if len(ret60)
                else float("nan"),

            "negative_60d_events":
                int((ret60 < 0).sum()),

            "negative_60d_rate":
                (ret60 < 0).mean()
                if len(ret60)
                else float("nan"),

            "worst_60d":
                ret60.min(),

            "best_60d":
                ret60.max(),
        }

    summary = pd.DataFrame(
        [
            summarize(
                "CURRENT_RELEASE",
                df["release_current"],
            ),
            summarize(
                "FLOW_SCORE_GE_3",
                df["release_flow_3"],
            ),
            summarize(
                "FLOW_SCORE_GE_5",
                df["release_flow_5"],
            ),
        ]
    )

    # ============================================================
    # 10. DETAIL
    # ============================================================

    detail = df.loc[
        df["base_release_event"],
        [
            "signal_date",
            "hy_oas_today",
            "vix_today",
            "flow_score",
            "deadman_reason",
            "spy_return_20d",
            "spy_return_60d",
            "release_current",
            "release_flow_3",
            "release_flow_5",
        ],
    ].copy()

    detail.to_csv(
        DETAIL_OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        SUMMARY_OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    # ============================================================
    # 11. REPORT
    # ============================================================

    print("=" * 78)
    print("FILTER15 CREDIT DEADMAN RELEASE — FLOW CONFIRMATION AUDIT")
    print("=" * 78)

    print(
        summary.to_string(
            index=False,
        )
    )

    print("\nActual Release Events:")
    print(
        detail.to_string(
            index=False,
        )
    )

    print("\nSaved:")
    print(DETAIL_OUTPUT)
    print(SUMMARY_OUTPUT)


if __name__ == "__main__":
    main()