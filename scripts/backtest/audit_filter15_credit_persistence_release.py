from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"

POSITIONS_PATH = RESULT_DIR / "daily_positions.csv"
PANEL_PATH = ROOT / "data" / "backtest" / "master_panel.csv"

SUMMARY_PATH = (
    RESULT_DIR
    / "filter15_credit_persistence_release_summary.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter15_credit_persistence_release_detail.csv"
)


def summarize(
    df: pd.DataFrame,
    mask: pd.Series,
    name: str,
) -> dict:

    x = df.loc[mask].copy()

    r20 = x["spy_return_20d"].dropna()
    r60 = x["spy_return_60d"].dropna()

    return {
        "scenario": name,
        "release_events": int(mask.sum()),

        "avg_hy_oas":
            x["hy_oas_today"].mean(),

        "avg_spy_20d":
            r20.mean() if len(r20) else None,

        "avg_spy_60d":
            r60.mean() if len(r60) else None,

        "median_spy_60d":
            r60.median() if len(r60) else None,

        "positive_60d_rate":
            (r60 > 0).mean() if len(r60) else None,

        "negative_60d_rate":
            (r60 < 0).mean() if len(r60) else None,

        "worst_60d":
            r60.min() if len(r60) else None,

        "best_60d":
            r60.max() if len(r60) else None,
    }


def main() -> None:

    # ======================================================
    # Load
    # ======================================================

    positions = pd.read_csv(POSITIONS_PATH)
    panel = pd.read_csv(PANEL_PATH)

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
        .drop_duplicates("signal_date", keep="last")
    )

    # ======================================================
    # Attach SPY
    # ======================================================

    df = positions.merge(
        panel[
            [
                "signal_date",
                "SPY",
            ]
        ],
        on="signal_date",
        how="left",
    )

    df["SPY"] = pd.to_numeric(
        df["SPY"],
        errors="coerce",
    )

    df["hy_oas_today"] = pd.to_numeric(
        df["hy_oas_today"],
        errors="coerce",
    )

    df["vix_today"] = pd.to_numeric(
        df["vix_today"],
        errors="coerce",
    )

    # ======================================================
    # Forward Return
    # ======================================================

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

    # ======================================================
    # Credit Deadman
    # ======================================================

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

    # ======================================================
    # Recovery Condition
    # ======================================================

    df["credit_recovered"] = (
        (df["hy_oas_today"] < 6.0)
        &
        (df["vix_today"] < 30.0)
    )

    # ======================================================
    # Post-Deadman Recovery State
    #
    # 핵심:
    # Deadman이 실제로 발생한 뒤에만 recovery countdown 시작.
    # 평상시 HY<6 구간은 Release event로 세지 않는다.
    # ======================================================

    current_release = [False] * len(df)
    persist_3_release = [False] * len(df)
    persist_5_release = [False] * len(df)

    waiting_for_recovery = False
    recovery_streak = 0

    audit_streak = [0] * len(df)

    for idx in range(len(df)):

        is_deadman = bool(
            df.iloc[idx]["credit_deadman"]
        )

        recovered = bool(
            df.iloc[idx]["credit_recovered"]
        )

        # Credit Deadman 발생:
        # 이후 정상화 확인을 기다린다.
        if is_deadman:
            waiting_for_recovery = True
            recovery_streak = 0
            audit_streak[idx] = 0
            continue

        # Deadman 이후가 아니면 Release Audit 대상 아님
        if not waiting_for_recovery:
            recovery_streak = 0
            audit_streak[idx] = 0
            continue

        # Deadman 이후 Recovery 시작
        if recovered:

            recovery_streak += 1
            audit_streak[idx] = recovery_streak

            # 현재 방식: 첫 정상화 날
            if recovery_streak == 1:
                current_release[idx] = True

            # 3일 Persistence
            if recovery_streak == 3:
                persist_3_release[idx] = True

            # 5일 Persistence
            if recovery_streak == 5:
                persist_5_release[idx] = True

        else:
            # 다시 악화되면 persistence reset.
            # 하지만 아직 post-deadman 상태이므로
            # 다음 recovery sequence를 계속 기다린다.
            recovery_streak = 0
            audit_streak[idx] = 0

        # 5일 확인까지 완료한 뒤에는
        # 하나의 Deadman episode 검증 종료.
        if recovery_streak >= 5:
            waiting_for_recovery = False

    df["post_deadman_recovery_streak"] = audit_streak
    df["current_release"] = current_release
    df["persist_3_release"] = persist_3_release
    df["persist_5_release"] = persist_5_release

    # ======================================================
    # Summary
    # ======================================================

    summary = pd.DataFrame(
        [
            summarize(
                df,
                df["current_release"],
                "CURRENT_RELEASE",
            ),
            summarize(
                df,
                df["persist_3_release"],
                "HY_PERSIST_3D",
            ),
            summarize(
                df,
                df["persist_5_release"],
                "HY_PERSIST_5D",
            ),
        ]
    )

    detail = df.loc[
        (
            df["current_release"]
            |
            df["persist_3_release"]
            |
            df["persist_5_release"]
        ),
        [
            "signal_date",
            "hy_oas_today",
            "vix_today",
            "post_deadman_recovery_streak",
            "spy_return_20d",
            "spy_return_60d",
            "current_release",
            "persist_3_release",
            "persist_5_release",
        ],
    ].copy()

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    detail.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # ======================================================
    # Report
    # ======================================================

    print("=" * 78)
    print("FILTER15 CREDIT PERSISTENCE RELEASE AUDIT v2")
    print("=" * 78)

    print(
        summary.to_string(
            index=False,
        )
    )

    print("\nSaved:")
    print(SUMMARY_PATH)
    print(DETAIL_PATH)


if __name__ == "__main__":
    main()