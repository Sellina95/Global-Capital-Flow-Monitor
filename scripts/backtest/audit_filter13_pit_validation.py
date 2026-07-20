"""
Filter 13 — Point-in-Time Dependency Validation

목적
----
Phase 1 dependency gate가 사용한 historical market_data가
각 signal_date 당시 이용 가능한 정보만 사용했는지 검증한다.

중요:
- Production 코드 수정 없음
- Attribution 실행 없음
- 현재 insights/*.json 사용 금지
- 단순 non-null PASS 금지
- source_asof > signal_date 이면 FUTURE_LEAK
- source/asof를 증명할 수 없으면 UNVERIFIED
- PASS / FAIL / UNVERIFIED를 명시적으로 분리
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.generate_report import build_market_data

from scripts.backtest.backtest_market_data_builder import (
    attach_liquidity_layer,
    attach_fred_extras_layer,
    attach_sovereign_spread_layer,
    attach_geopolitical_ew_layer,
    attach_country_risk_layer,
    attach_sector_momentum_layer,
    attach_geo_similarity_layer,
    attach_sentiment_proxy_layer,
    attach_drift_data_layer,
    attach_growth_sustainability_layer,
    attach_breadth_layer,
    attach_leadership_layer,
    attach_credit_spread_layer,
)

# 기존 Phase1에서 이미 만든 PIT positioning helper 재사용
from scripts.backtest.audit_filter13_budget_attribution_v2 import (
    load_backtest_macro_df,
    attach_positioning_layer_backtest,
)

OUTPUT_DIR = ROOT / "data" / "backtest" / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2022-01-03")
END = pd.Timestamp("2022-01-14")


def norm_date(x):
    try:
        x = pd.to_datetime(x, errors="coerce")
        if pd.isna(x):
            return None
        return x.normalize()
    except Exception:
        return None


def scalar(x):
    if isinstance(x, dict):
        for k in ("today", "value", "level", "score"):
            if k in x:
                return x.get(k)
    return x


def add_row(
    rows,
    signal_date,
    dependency,
    value,
    source_asof=None,
    source="",
    verification="ASOF",
    expected=None,
    note="",
):
    """
    verification:
      EXACT  = historical source expected value와 직접 대조
      ASOF   = source_asof <= signal_date 검증
      DERIVED = 당시 입력으로 계산된 파생 상태
      UNVERIFIED = 아직 시점 증명 불가
    """

    t = norm_date(signal_date)
    a = norm_date(source_asof)

    status = "UNVERIFIED"

    if verification == "EXACT":
        try:
            v = float(value)
            e = float(expected)

            if np.isclose(v, e, equal_nan=False):
                status = "PASS"
            else:
                status = "FAIL_VALUE_MISMATCH"
        except Exception:
            status = (
                "PASS"
                if str(value) == str(expected)
                else "FAIL_VALUE_MISMATCH"
            )

    elif verification == "ASOF":
        if a is None:
            status = "UNVERIFIED"
        elif a > t:
            status = "FAIL_FUTURE_LEAK"
        else:
            status = "PASS"

    elif verification == "DERIVED":
        status = "DERIVED_REVIEW"

    rows.append({
        "signal_date": (
            t.strftime("%Y-%m-%d")
            if t is not None else None
        ),
        "dependency": dependency,
        "actual_value": value,
        "expected_value": expected,
        "source_asof": (
            a.strftime("%Y-%m-%d")
            if a is not None else None
        ),
        "source": source,
        "verification": verification,
        "pit_status": status,
        "note": note,
    })


def load_credit():
    p = ROOT / "data" / "backtest" / "credit_spread_data.csv"
    df = pd.read_csv(p)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.sort_values("date")


def historical_credit_expected(df, signal_date):
    """
    signal_date까지 공개되어 있는 가장 최근 HY_OAS.
    현재 파일은 daily historical series이므로 <= T 마지막 관측값 사용.
    """
    hist = df[df["date"] <= signal_date].dropna(subset=["HY_OAS"])

    if hist.empty:
        return None, None

    r = hist.iloc[-1]

    return r["HY_OAS"], r["date"]


def main():

    macro = load_backtest_macro_df().copy()

    date_col = next(
        c for c in macro.columns
        if c.lower() in ("date", "datetime")
    )

    macro[date_col] = pd.to_datetime(
        macro[date_col],
        errors="coerce",
    )

    macro = macro.sort_values(date_col)

    selected = macro[
        (macro[date_col] >= START)
        & (macro[date_col] <= END)
    ]

    credit_df = load_credit()

    rows = []

    print("[PIT AUDIT] rows:", len(selected))

    for _, r in selected.iterrows():

        signal_date = norm_date(r[date_col])

        # -----------------------------------------
        # 동일한 Phase1 historical construction
        # -----------------------------------------
        market_data = build_market_data(
            signal_date=signal_date
        )

        attach_liquidity_layer(
            market_data,
            signal_date,
        )

        attach_credit_spread_layer(
            market_data,
            signal_date,
        )

        attach_fred_extras_layer(
            market_data,
            signal_date,
        )

        attach_sovereign_spread_layer(
            market_data,
            signal_date,
        )

        attach_positioning_layer_backtest(
            market_data,
            signal_date,
        )

        attach_geopolitical_ew_layer(
            market_data,
            signal_date,
        )

        attach_country_risk_layer(
            market_data,
            signal_date,
        )

        attach_sector_momentum_layer(
            market_data,
            signal_date,
        )

        attach_geo_similarity_layer(
            market_data,
            signal_date,
        )

        attach_sentiment_proxy_layer(
            market_data,
            signal_date,
        )

        attach_drift_data_layer(
            market_data,
            signal_date,
        )

        attach_growth_sustainability_layer(
            market_data,
            signal_date,
        )

        attach_breadth_layer(
            market_data,
            signal_date,
        )

        attach_leadership_layer(
            market_data,
            signal_date,
        )

        # =================================================
        # 1. HY OAS — 원본 historical CSV와 직접 대조
        # =================================================

        hy = market_data.get("HY_OAS", {}) or {}

        actual_hy = (
            hy.get("today")
            if isinstance(hy, dict)
            else hy
        )

        expected_hy, expected_hy_date = (
            historical_credit_expected(
                credit_df,
                signal_date,
            )
        )

        add_row(
            rows,
            signal_date,
            "HY_OAS",
            actual_hy,
            source_asof=expected_hy_date,
            source="credit_spread_data.csv",
            verification="EXACT",
            expected=expected_hy,
            note=(
                "Actual market_data HY_OAS must equal "
                "historical <= signal_date source value."
            ),
        )

        # =================================================
        # 2. Positioning — helper가 기록한 실제 ASOF 검증
        # =================================================

        add_row(
            rows,
            signal_date,
            "SP500_POS_Z",
            market_data.get("SP500_POS_Z"),
            source_asof=market_data.get("_POS_ASOF"),
            source="historical positioning layer",
            verification="ASOF",
            note="Must use latest observation available on/before T.",
        )

        # =================================================
        # 3. Explicit ASOF metadata가 있는 historical layers
        # =================================================

        asof_groups = [
            (
                "GROWTH",
                "_GROWTH_ASOF",
                [
                    "GROWTH_US10Y",
                    "GROWTH_DXY",
                    "GROWTH_WTI",
                    "GROWTH_T10Y2Y",
                    "GROWTH_DFII10",
                    "GROWTH_REAL_RATE",
                ],
            ),
            (
                "BREADTH",
                "_BREADTH_ASOF",
                [
                    "BREADTH_SPY",
                    "BREADTH_SPY_PREV",
                    "BREADTH_RSP",
                    "BREADTH_RSP_PREV",
                    "BREADTH_QQQ",
                    "BREADTH_QQQ_PREV",
                    "BREADTH_QQQE",
                    "BREADTH_QQQE_PREV",
                ],
            ),
            (
                "LEADERSHIP",
                "_LEADERSHIP_ASOF",
                [
                    "LEAD_QQQ",
                    "LEAD_QQQ_PREV",
                    "LEAD_SMH",
                    "LEAD_SMH_PREV",
                    "LEAD_SOXX",
                    "LEAD_SOXX_PREV",
                    "LEAD_IWM",
                    "LEAD_IWM_PREV",
                    "LEAD_XLF",
                    "LEAD_XLF_PREV",
                    "LEAD_XLI",
                    "LEAD_XLI_PREV",
                    "LEAD_XLY",
                    "LEAD_XLY_PREV",
                ],
            ),
        ]

        for group, asof_key, keys in asof_groups:

            asof = market_data.get(asof_key)

            # builder가 _XXX_ASOF 대신 dict 안 asof를
            # 저장하는 경우도 지원
            if asof is None:
                node = market_data.get(group, {})
                if isinstance(node, dict):
                    asof = node.get("asof")

            for key in keys:
                if key in market_data:
                    value = market_data.get(key)
                else:
                    node = market_data.get(group, {})
                    value = (
                        node.get(key)
                        if isinstance(node, dict)
                        else None
                    )

                add_row(
                    rows,
                    signal_date,
                    key,
                    value,
                    source_asof=asof,
                    source=f"{group} historical layer",
                    verification="ASOF",
                    note=(
                        "PASS only when explicit source_asof "
                        "is available and <= signal_date."
                    ),
                )

        # =================================================
        # 4. Phase1 derived dependencies
        #
        # 값 존재만으로 PIT PASS 주지 않는다.
        # source date가 없는 파생 상태는 DERIVED_REVIEW.
        # =================================================

        sentiment = market_data.get("SENTIMENT", {}) or {}
        net_liq = market_data.get("NET_LIQ", {}) or {}
        drift = market_data.get("DRIFT", {}) or {}

        derived = {
            "MARKET_REGIME":
                market_data.get("MARKET_REGIME"),

            "MACRO_NARRATIVE":
                market_data.get("MACRO_NARRATIVE"),

            "POLICY_BIAS_LINE":
                market_data.get("POLICY_BIAS_LINE"),

            "SENTIMENT_FEAR_GREED":
                sentiment.get("fear_greed")
                if isinstance(sentiment, dict)
                else None,

            "NET_LIQ_PCT_CHANGE":
                net_liq.get("pct_change")
                if isinstance(net_liq, dict)
                else None,

            "NET_LIQ_LEVEL_BUCKET":
                (
                    net_liq.get("level_bucket")
                    if isinstance(net_liq, dict)
                    else None
                )
                or market_data.get(
                    "NET_LIQ_LEVEL_BUCKET"
                ),

            "STRUCT_V2_STATE":
                market_data.get("STRUCT_V2_STATE"),

            "DRIFT_SCORE":
                (
                    drift.get("score")
                    if isinstance(drift, dict)
                    else market_data.get("DRIFT_SCORE")
                ),

            "DRIFT_STATE":
                (
                    drift.get("state")
                    if isinstance(drift, dict)
                    else market_data.get("DRIFT_STATE")
                ),

            "GAMMA_STATE":
                market_data.get("GAMMA_STATE"),
        }

        for key, value in derived.items():

            add_row(
                rows,
                signal_date,
                key,
                value,
                source="derived Phase1 dependency",
                verification="DERIVED",
                note=(
                    "Not automatically PIT PASS. "
                    "Underlying source dates must be proven."
                ),
            )

        print(
            "[PIT]",
            signal_date.strftime("%Y-%m-%d"),
            "HY actual=",
            actual_hy,
            "expected=",
            expected_hy,
            "POS asof=",
            market_data.get("_POS_ASOF"),
        )

    # -----------------------------------------
    # SAVE
    # -----------------------------------------

    result = pd.DataFrame(rows)

    detail_path = (
        OUTPUT_DIR
        / "filter13_pit_validation_detail.csv"
    )

    result.to_csv(
        detail_path,
        index=False,
        encoding="utf-8-sig",
    )

    summary = (
        result.groupby(
            ["dependency", "pit_status"],
            dropna=False,
        )
        .size()
        .reset_index(name="count")
    )

    summary_path = (
        OUTPUT_DIR
        / "filter13_pit_validation_summary.csv"
    )

    summary.to_csv(
        summary_path,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("[SAVED]", detail_path)
    print("[SAVED]", summary_path)

    print()
    print("[PIT STATUS]")
    print(
        result["pit_status"]
        .value_counts(dropna=False)
        .to_string()
    )

    print()
    print("[SUMMARY]")
    print(summary.to_string(index=False))

    bad = result[
        ~result["pit_status"].isin(["PASS"])
    ]

    print()
    print("[NON-PASS / MUST REVIEW]")

    if bad.empty:
        print("NONE — ALL PIT VERIFIED")
    else:
        print(
            bad[
                [
                    "signal_date",
                    "dependency",
                    "actual_value",
                    "expected_value",
                    "source_asof",
                    "pit_status",
                ]
            ]
            .to_string(index=False)
        )

    print()
    print(
        "PIT AUDIT COMPLETE. "
        "DO NOT RUN ATTRIBUTION UNTIL "
        "FAIL AND UNVERIFIED ARE RESOLVED."
    )


if __name__ == "__main__":
    main()
