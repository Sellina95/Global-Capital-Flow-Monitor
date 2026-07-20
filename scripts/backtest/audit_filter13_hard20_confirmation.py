from pathlib import Path
import pandas as pd
import numpy as np

# ============================================================
# FILTER13 HARD-RISK-OFF CAP20 CONFIRMATION AUDIT
#
# 목적:
# HARD RISK-OFF → CAP20 진입이
# 어떤 "당시 관측 가능 신호(PIT)"에 의해 발생했는지 분해한다.
#
# 핵심 질문:
# 1) CAP20 진입 당시 Credit은 얼마나 심각했는가?
# 2) VIX/DXY/US10Y/WTI 방향 정렬은 어땠는가?
# 3) HARD가 하루짜리였는가, 지속됐는가?
# 4) 즉시 CAP20이 필요할 만큼 confirmation이 있었는가?
#
# 주의:
# - Production 코드 수정 없음
# - Forward return은 진단용 EX-POST 평가에만 사용
# - 미래 수익률로 confirmation 조건을 만들지 않음
# ============================================================

RESULTS = Path("data/backtest/results")

ATTR = RESULTS / "filter13_budget_attribution_final_daily.csv"
EPISODE = RESULTS / "filter13_hard_riskoff_episode_daily.csv"
MACRO = Path("data/backtest/macro_data.csv")

OUT = RESULTS / "filter13_hard20_confirmation.csv"
OUT_SUMMARY = RESULTS / "filter13_hard20_confirmation_summary.txt"


def direction(x):
    if pd.isna(x):
        return "N/A"
    if x > 0:
        return "UP"
    if x < 0:
        return "DOWN"
    return "FLAT"


def main():

    # --------------------------------------------------------
    # Load attribution
    # --------------------------------------------------------
    if not ATTR.exists():
        raise FileNotFoundError(f"Missing: {ATTR}")

    df = pd.read_csv(ATTR)
    df["date"] = pd.to_datetime(df["date"])

    # HARD + CAP20 only
    hard = df[
        (df["phase_cap"] == 20)
        & (
            df["market_regime"]
            .astype(str)
            .str.contains("HARD RISK-OFF", case=False, na=False)
        )
    ].copy()

    # --------------------------------------------------------
    # Load raw macro prices
    # --------------------------------------------------------
    if not MACRO.exists():
        raise FileNotFoundError(f"Missing: {MACRO}")

    m = pd.read_csv(MACRO)
    m["date"] = pd.to_datetime(m["date"])
    m = m.sort_values("date").drop_duplicates("date")

    raw_cols = [
        c for c in [
            "date",
            "US10Y",
            "DXY",
            "VIX",
            "WTI",
            "SPY",
        ]
        if c in m.columns
    ]

    raw = m[raw_cols].copy()

    # IMPORTANT:
    # 방향은 해당 날짜와 직전 거래일만 사용
    # → 미래정보 없음
    for col in ["US10Y", "DXY", "VIX", "WTI"]:
        if col in raw.columns:
            raw[f"{col}_pct"] = raw[col].pct_change()
            raw[f"{col}_dir"] = raw[f"{col}_pct"].apply(direction)

    # Forward SPY = EX-POST evaluation only
    if "SPY" in raw.columns:
        raw["spy_fwd_20d"] = raw["SPY"].shift(-20) / raw["SPY"] - 1

    merge_cols = ["date"]

    for col in [
        "US10Y_dir",
        "DXY_dir",
        "VIX_dir",
        "WTI_dir",
        "spy_fwd_20d",
    ]:
        if col in raw.columns:
            merge_cols.append(col)

    hard = hard.merge(
        raw[merge_cols],
        on="date",
        how="left",
    )

    # --------------------------------------------------------
    # Episode duration
    # --------------------------------------------------------
    episode_duration_map = {}

    if EPISODE.exists():

        ep = pd.read_csv(EPISODE)

        if "date" in ep.columns:
            ep["date"] = pd.to_datetime(ep["date"])

        # 파일 구조가 daily 형식일 경우 episode_id로 duration 계산
        if (
            "episode_id" in ep.columns
            and "date" in ep.columns
        ):
            duration = (
                ep.groupby("episode_id")["date"]
                .nunique()
                .to_dict()
            )

            for _, r in ep.iterrows():
                episode_duration_map[
                    r["date"]
                ] = duration.get(
                    r["episode_id"],
                    np.nan,
                )

    hard["episode_duration"] = hard["date"].map(
        episode_duration_map
    )

    # 이전 audit 구조 차이 대비 fallback
    if hard["episode_duration"].isna().all():

        is_hard = (
            df["market_regime"]
            .astype(str)
            .str.contains("HARD RISK-OFF", case=False, na=False)
        )

        temp = df[["date"]].copy()
        temp["is_hard"] = is_hard.values

        episode_id = (
            temp["is_hard"]
            != temp["is_hard"].shift()
        ).cumsum()

        temp["episode_id_tmp"] = np.where(
            temp["is_hard"],
            episode_id,
            np.nan,
        )

        duration_map = (
            temp[temp["is_hard"]]
            .groupby("episode_id_tmp")["date"]
            .transform("count")
        )

        temp.loc[
            temp["is_hard"],
            "episode_duration",
        ] = duration_map.values

        hard = hard.drop(
            columns=["episode_duration"]
        ).merge(
            temp[
                [
                    "date",
                    "episode_duration",
                ]
            ],
            on="date",
            how="left",
        )

    # --------------------------------------------------------
    # Trigger classification from Macro Narrative
    # --------------------------------------------------------
    def trigger(row):

        macro = str(
            row.get("macro_narrative", "")
        ).upper()

        regime = str(
            row.get("market_regime", "")
        ).upper()

        if "CREDIT_STRESS" in macro:
            return "CREDIT_STRESS"

        if "STAGFLATION" in macro or "INFLATION SHOCK" in regime:
            return "STAGFLATION_OR_INFLATION"

        if "TIGHTENING_GROWTH_SCARE" in macro:
            return "GROWTH_SCARE"

        return "OTHER"

    hard["trigger"] = hard.apply(
        trigger,
        axis=1,
    )

    # --------------------------------------------------------
    # Credit severity
    #
    # HY OAS:
    # <3 COOL
    # 3~4 WATCH
    # 4~6 HOT
    # >=6 FRACTURE
    # --------------------------------------------------------
    hy_col = None

    for candidate in [
        "hy_oas_today",
        "HY_OAS",
        "hy_oas",
    ]:
        if candidate in hard.columns:
            hy_col = candidate
            break

    def credit_bucket(x):

        try:
            x = float(x)
        except Exception:
            return "UNKNOWN"

        if x >= 6:
            return "FRACTURE"

        if x >= 4:
            return "HOT"

        if x >= 3:
            return "WATCH"

        return "COOL"

    if hy_col:
        hard["credit_bucket"] = hard[
            hy_col
        ].apply(credit_bucket)
    else:
        hard["credit_bucket"] = "UNKNOWN"

    # --------------------------------------------------------
    # PIT Confirmation Evidence Count
    #
    # 이것은 아직 Production rule이 아님.
    # 단지 "당시 몇 개의 위험 증거가 동시에 있었나"를 세는 Audit.
    # --------------------------------------------------------

    hard["confirm_credit_fracture"] = (
        hard["credit_bucket"] == "FRACTURE"
    )

    hard["confirm_credit_hot"] = (
        hard["credit_bucket"].isin(
            ["HOT", "FRACTURE"]
        )
    )

    hard["confirm_vix_up"] = (
        hard.get(
            "VIX_dir",
            pd.Series(index=hard.index, dtype=object),
        )
        == "UP"
    )

    hard["confirm_dxy_up"] = (
        hard.get(
            "DXY_dir",
            pd.Series(index=hard.index, dtype=object),
        )
        == "UP"
    )

    # Strict evidence:
    # Credit FRACTURE 또는
    # HOT credit + VIX/DXY 동시 악화
    #
    # 주의: 후보 진단일 뿐 production threshold 아님.
    hard["strict_confirmation_candidate"] = (
        hard["confirm_credit_fracture"]
        |
        (
            hard["confirm_credit_hot"]
            & hard["confirm_vix_up"]
            & hard["confirm_dxy_up"]
        )
    )

    hard["one_day_hard"] = (
        hard["episode_duration"] == 1
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print(
        "=== FILTER13 HARD CAP20 CONFIRMATION AUDIT ==="
    )

    print()
    print("[COUNT]")
    print(
        "HARD CAP20 DAYS:",
        len(hard),
    )

    print()
    print("=== TRIGGER ===")
    print(
        hard["trigger"]
        .value_counts(dropna=False)
        .to_string()
    )

    print()
    print(
        "=== EPISODE PERSISTENCE ==="
    )

    print(
        "ONE-DAY HARD:",
        int(hard["one_day_hard"].sum()),
    )

    print(
        "PERSISTENT HARD DAYS:",
        int((~hard["one_day_hard"]).sum()),
    )

    print()
    print(
        "=== CREDIT SEVERITY ==="
    )

    print(
        hard["credit_bucket"]
        .value_counts(dropna=False)
        .to_string()
    )

    print()
    print(
        "=== STRICT CONFIRMATION CANDIDATE ==="
    )

    print(
        hard[
            "strict_confirmation_candidate"
        ]
        .value_counts(dropna=False)
        .rename(
            index={
                True: "CONFIRMED_CANDIDATE",
                False: "UNCONFIRMED_CANDIDATE",
            }
        )
        .to_string()
    )

    # --------------------------------------------------------
    # One-day vs persistent
    # --------------------------------------------------------

    print()
    print(
        "=== ONE-DAY vs PERSISTENT CONFIRMATION ==="
    )

    cross = pd.crosstab(
        np.where(
            hard["one_day_hard"],
            "ONE_DAY",
            "PERSISTENT_DAY",
        ),
        np.where(
            hard[
                "strict_confirmation_candidate"
            ],
            "CONFIRMED_CANDIDATE",
            "UNCONFIRMED_CANDIDATE",
        ),
    )

    print(cross.to_string())

    # --------------------------------------------------------
    # Ex-post diagnostic only
    # --------------------------------------------------------

    if "spy_fwd_20d" in hard.columns:

        print()
        print(
            "=== EX-POST T+20 BY CONFIRMATION ==="
        )

        tmp = hard.dropna(
            subset=["spy_fwd_20d"]
        ).copy()

        tmp["confirmation_group"] = np.where(
            tmp[
                "strict_confirmation_candidate"
            ],
            "CONFIRMED_CANDIDATE",
            "UNCONFIRMED_CANDIDATE",
        )

        result = (
            tmp.groupby(
                "confirmation_group"
            )
            .agg(
                days=(
                    "date",
                    "count",
                ),
                avg_spy_fwd_20d=(
                    "spy_fwd_20d",
                    "mean",
                ),
                negative_market_rate=(
                    "spy_fwd_20d",
                    lambda x:
                    (x < 0).mean(),
                ),
            )
            .reset_index()
        )

        result[
            "avg_spy_fwd_20d"
        ] *= 100

        result[
            "negative_market_rate"
        ] *= 100

        print(
            result.to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # Detail
    # --------------------------------------------------------

    print()
    print(
        "=== DETAIL ==="
    )

    detail_cols = [
        c for c in [
            "date",
            "market_regime",
            "macro_narrative",
            "trigger",
            "credit_bucket",
            "US10Y_dir",
            "DXY_dir",
            "VIX_dir",
            "WTI_dir",
            "episode_duration",
            "one_day_hard",
            "strict_confirmation_candidate",
            "pre_cap_budget",
            "phase_cap",
            "final_budget",
            "spy_fwd_20d",
        ]
        if c in hard.columns
    ]

    print(
        hard[
            detail_cols
        ].to_string(
            index=False
        )
    )

    hard[
        detail_cols
    ].to_csv(
        OUT,
        index=False,
    )

    # --------------------------------------------------------
    # Memo file
    # --------------------------------------------------------

    lines = []

    lines.append(
        "FILTER13 HARD CAP20 CONFIRMATION AUDIT"
    )
    lines.append("=" * 60)
    lines.append("")

    lines.append(
        f"HARD CAP20 DAYS: {len(hard)}"
    )

    lines.append(
        f"ONE-DAY HARD: "
        f"{int(hard['one_day_hard'].sum())}"
    )

    lines.append(
        f"STRICT CONFIRMED CANDIDATES: "
        f"{int(hard['strict_confirmation_candidate'].sum())}"
    )

    lines.append(
        f"UNCONFIRMED CANDIDATES: "
        f"{int((~hard['strict_confirmation_candidate']).sum())}"
    )

    lines.append("")
    lines.append(
        "IMPORTANT INTERPRETATION"
    )

    lines.append(
        "- strict_confirmation_candidate is an AUDIT hypothesis only."
    )

    lines.append(
        "- It is NOT a production trading rule."
    )

    lines.append(
        "- Forward returns are EX-POST evaluation only."
    )

    lines.append(
        "- Production changes require multi-cycle validation."
    )

    OUT_SUMMARY.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print()
    print("[SAVED]", OUT)
    print("[SAVED]", OUT_SUMMARY)

    print()
    print("AUDIT COMPLETE.")
    print(
        "No production Filter13 logic was modified."
    )


if __name__ == "__main__":
    main()