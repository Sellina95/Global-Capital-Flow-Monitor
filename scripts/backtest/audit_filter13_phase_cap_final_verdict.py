from pathlib import Path
import pandas as pd
import numpy as np

# ============================================================
# FILTER13 PHASE CAP FINAL VERDICT AUDIT
#
# 목적:
# 1) Phase Cap별 총 노출 제거량
# 2) 실제 이후 시장 방향
# 3) 방어 성공 / 기회비용
# 4) 최종적으로 어떤 Cap이 Filter13 저노출의 핵심 원인인지 판정
#
# IMPORTANT:
# - Production code 수정 없음
# - Forward return은 EX-POST 평가에만 사용
# - 신호 생성에는 절대 사용하지 않음
# ============================================================

RESULTS = Path("data/backtest/results")

ATTR_PATH = RESULTS / "filter13_budget_attribution_final_daily.csv"
MACRO_PATH = Path("data/backtest/macro_data.csv")

OUT_DAILY = RESULTS / "filter13_phase_cap_final_verdict_daily.csv"
OUT_SUMMARY = RESULTS / "filter13_phase_cap_final_verdict_summary.csv"
OUT_TXT = RESULTS / "filter13_phase_cap_final_verdict_summary.txt"


def load_data():
    if not ATTR_PATH.exists():
        raise FileNotFoundError(f"Missing: {ATTR_PATH}")

    if not MACRO_PATH.exists():
        raise FileNotFoundError(f"Missing: {MACRO_PATH}")

    df = pd.read_csv(ATTR_PATH)
    macro = pd.read_csv(MACRO_PATH)

    df["date"] = pd.to_datetime(df["date"])
    macro["date"] = pd.to_datetime(macro["date"])

    if "SPY" not in macro.columns:
        raise ValueError("SPY column not found in macro_data.csv")

    macro = (
        macro[["date", "SPY"]]
        .drop_duplicates("date")
        .sort_values("date")
        .reset_index(drop=True)
    )

    # Forward returns — EX-POST evaluation only
    for h in [1, 5, 20]:
        macro[f"spy_fwd_{h}d"] = macro["SPY"].shift(-h) / macro["SPY"] - 1

    df = df.merge(
        macro[
            [
                "date",
                "SPY",
                "spy_fwd_1d",
                "spy_fwd_5d",
                "spy_fwd_20d",
            ]
        ],
        on="date",
        how="left",
    )

    return df.sort_values("date").reset_index(drop=True)


def main():
    df = load_data()

    required = [
        "phase_cap",
        "pre_cap_budget",
        "final_budget",
    ]

    for c in required:
        if c not in df.columns:
            raise ValueError(f"Required column missing: {c}")

    # --------------------------------------------------------
    # Phase cap effect
    # --------------------------------------------------------
    if "phase_cap_effect" not in df.columns:
        df["phase_cap_effect"] = (
            df["phase_cap"] - df["pre_cap_budget"]
        ).clip(upper=0)

    df["exposure_removed"] = (
        df["pre_cap_budget"] - df["phase_cap"]
    ).clip(lower=0)

    df["cap_binding"] = df["exposure_removed"] > 0

    # 분석 대상
    target_caps = [20, 30, 45, 65]

    rows = []

    for cap in target_caps:

        x = df[
            (df["phase_cap"] == cap)
            & (df["cap_binding"])
        ].copy()

        binding_days = len(x)

        total_removed = x["exposure_removed"].sum()
        avg_removed = (
            x["exposure_removed"].mean()
            if binding_days
            else np.nan
        )

        row = {
            "phase_cap": cap,
            "binding_days": binding_days,
            "total_exposure_removed_pct_points": total_removed,
            "avg_exposure_removed_when_binding": avg_removed,
        }

        # ----------------------------------------------------
        # Forward effectiveness
        # Positive cap_effect = cap helped
        # Negative cap_effect = opportunity cost
        #
        # If market falls:
        # reduced exposure helps
        #
        # effect ≈ -(removed exposure fraction) × market return
        # ----------------------------------------------------
        for h in [1, 5, 20]:

            ret_col = f"spy_fwd_{h}d"

            valid = x.dropna(subset=[ret_col]).copy()

            valid[f"cap_effect_{h}d"] = (
                -(valid["exposure_removed"] / 100.0)
                * valid[ret_col]
            )

            success = (
                valid[f"cap_effect_{h}d"] > 0
            ).sum()

            cost = (
                valid[f"cap_effect_{h}d"] < 0
            ).sum()

            row[f"valid_{h}d"] = len(valid)

            row[f"defensive_success_{h}d"] = success
            row[f"opportunity_cost_{h}d"] = cost

            row[f"success_rate_{h}d_pct"] = (
                success / len(valid) * 100
                if len(valid)
                else np.nan
            )

            row[f"avg_spy_fwd_{h}d_pct"] = (
                valid[ret_col].mean() * 100
                if len(valid)
                else np.nan
            )

            row[f"avg_cap_effect_{h}d_pct"] = (
                valid[f"cap_effect_{h}d"].mean() * 100
                if len(valid)
                else np.nan
            )

            row[f"total_cap_effect_{h}d_pct"] = (
                valid[f"cap_effect_{h}d"].sum() * 100
                if len(valid)
                else np.nan
            )

        rows.append(row)

    summary = pd.DataFrame(rows)

    # --------------------------------------------------------
    # Share of total exposure destruction
    # --------------------------------------------------------
    total_removed_all = summary[
        "total_exposure_removed_pct_points"
    ].sum()

    summary["share_of_total_removed_pct"] = (
        summary["total_exposure_removed_pct_points"]
        / total_removed_all
        * 100
    )

    # --------------------------------------------------------
    # Diagnostic classification
    #
    # 이것은 전략 최적화 규칙이 아니라
    # audit용 descriptive verdict.
    # --------------------------------------------------------
    def classify(row):

        share = row["share_of_total_removed_pct"]

        success20 = row["success_rate_20d_pct"]
        effect20 = row["total_cap_effect_20d_pct"]

        # 많이 잘랐는데 장기 방어효과가 약하거나 음수
        if (
            share >= 25
            and (
                pd.isna(effect20)
                or effect20 <= 0
                or (
                    not pd.isna(success20)
                    and success20 < 60
                )
            )
        ):
            return "PRIMARY_OVERCONSTRAINT_SUSPECT"

        # 실제 방어 효과가 강함
        if (
            not pd.isna(success20)
            and success20 >= 70
            and not pd.isna(effect20)
            and effect20 > 0
        ):
            return "DEFENSIVE_VALUE_CONFIRMED"

        # 노출 제거량이 작음
        if share < 15:
            return "SECONDARY_IMPACT"

        return "MIXED_REVIEW"

    summary["diagnostic_verdict"] = summary.apply(
        classify,
        axis=1,
    )

    # --------------------------------------------------------
    # Ranking:
    # 누가 가장 많은 exposure를 없앴는가
    # --------------------------------------------------------
    summary = summary.sort_values(
        "total_exposure_removed_pct_points",
        ascending=False,
    ).reset_index(drop=True)

    summary["exposure_destruction_rank"] = (
        np.arange(1, len(summary) + 1)
    )

    # --------------------------------------------------------
    # Save daily
    # --------------------------------------------------------
    daily_cols = [
        c for c in [
            "date",
            "market_regime",
            "macro_narrative",
            "struct_v2_state",
            "base_budget",
            "pre_cap_budget",
            "phase_cap",
            "phase_cap_effect",
            "exposure_removed",
            "final_budget",
            "SPY",
            "spy_fwd_1d",
            "spy_fwd_5d",
            "spy_fwd_20d",
        ]
        if c in df.columns
    ]

    df[
        df["phase_cap"].isin(target_caps)
    ][daily_cols].to_csv(
        OUT_DAILY,
        index=False,
    )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
    )

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------
    print()
    print(
        "=== FILTER13 PHASE CAP FINAL VERDICT AUDIT ==="
    )

    print()
    print("[PERIOD]")
    print("ROWS:", len(df))
    print(
        "FROM:",
        df["date"].min().date(),
    )
    print(
        "TO  :",
        df["date"].max().date(),
    )

    print()
    print(
        "=== EXPOSURE DESTRUCTION RANKING ==="
    )

    print(
        summary[
            [
                "exposure_destruction_rank",
                "phase_cap",
                "binding_days",
                "total_exposure_removed_pct_points",
                "share_of_total_removed_pct",
                "avg_exposure_removed_when_binding",
            ]
        ].to_string(index=False)
    )

    print()
    print(
        "=== T+20 EFFECTIVENESS ==="
    )

    print(
        summary[
            [
                "phase_cap",
                "valid_20d",
                "defensive_success_20d",
                "opportunity_cost_20d",
                "success_rate_20d_pct",
                "avg_spy_fwd_20d_pct",
                "avg_cap_effect_20d_pct",
                "total_cap_effect_20d_pct",
            ]
        ].to_string(index=False)
    )

    print()
    print(
        "=== FINAL DIAGNOSTIC VERDICT ==="
    )

    print(
        summary[
            [
                "phase_cap",
                "share_of_total_removed_pct",
                "success_rate_20d_pct",
                "total_cap_effect_20d_pct",
                "diagnostic_verdict",
            ]
        ].to_string(index=False)
    )

    # --------------------------------------------------------
    # Human-readable summary
    # --------------------------------------------------------
    lines = []

    lines.append(
        "FILTER13 PHASE CAP FINAL VERDICT"
    )
    lines.append("=" * 60)
    lines.append("")

    for _, r in summary.iterrows():

        lines.append(
            f"CAP {int(r['phase_cap'])}"
        )

        lines.append(
            f"- Binding days: "
            f"{int(r['binding_days'])}"
        )

        lines.append(
            f"- Total exposure removed: "
            f"{r['total_exposure_removed_pct_points']:.1f} "
            f"%p-days"
        )

        lines.append(
            f"- Share of analyzed cap removal: "
            f"{r['share_of_total_removed_pct']:.1f}%"
        )

        if not pd.isna(
            r["success_rate_20d_pct"]
        ):
            lines.append(
                f"- T+20 defensive success: "
                f"{r['success_rate_20d_pct']:.1f}%"
            )

        if not pd.isna(
            r["total_cap_effect_20d_pct"]
        ):
            lines.append(
                f"- T+20 total cap effect: "
                f"{r['total_cap_effect_20d_pct']:.3f}%"
            )

        lines.append(
            f"- Verdict: "
            f"{r['diagnostic_verdict']}"
        )

        lines.append("")

    # 핵심 exposure destroyer
    if len(summary):

        top = summary.iloc[0]

        lines.append(
            "PRIMARY EXPOSURE DESTRUCTION SOURCE"
        )

        lines.append(
            f"CAP {int(top['phase_cap'])}"
        )

        lines.append(
            f"It removed "
            f"{top['total_exposure_removed_pct_points']:.1f} "
            f"%p-days of exposure, representing "
            f"{top['share_of_total_removed_pct']:.1f}% "
            f"of analyzed Phase Cap exposure removal."
        )

    lines.append("")
    lines.append(
        "IMPORTANT:"
    )
    lines.append(
        "Forward returns are EX-POST evaluation only."
    )
    lines.append(
        "This audit does NOT justify changing production thresholds by itself."
    )
    lines.append(
        "Any production change requires out-of-sample validation across "
        "2008 / 2020 / 2022 and full portfolio re-backtest."
    )

    OUT_TXT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print()
    print("[SAVED]", OUT_DAILY)
    print("[SAVED]", OUT_SUMMARY)
    print("[SAVED]", OUT_TXT)

    print()
    print("FINAL VERDICT AUDIT COMPLETE.")
    print(
        "Forward returns are EX-POST evaluation only."
    )
    print(
        "No production Filter13 logic was modified."
    )


if __name__ == "__main__":
    main()