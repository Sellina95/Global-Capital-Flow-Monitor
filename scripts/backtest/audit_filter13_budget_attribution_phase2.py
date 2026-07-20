"""
Filter13 Budget Attribution Audit v2
Phase 1 — Historical Dependency Harness

목적
----
13번 Narrative Engine의 attribution을 수행하기 전에,
각 historical signal_date에서 필요한 dependency가 실제로 존재하는지 검증한다.

중요
----
- Production 코드 수정 금지
- 기존 audit_filter13_budget_audit.py 수정 금지
- 미래 데이터 사용 금지
- 현재 insights/flow_state.json을 historical PREV_FLOW로 사용 금지
- Phase 1에서는 attribution 결과를 만들지 않는다.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

DATA_DIR = ROOT / "data" / "backtest"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = pd.Timestamp("2022-01-01")
END_DATE = pd.Timestamp("2022-06-30")


# ---------------------------------------------------------
# Existing backtest infrastructure
# ---------------------------------------------------------

from scripts.generate_report import (
    merge_sovereign_spreads_into_macro_df,
    build_market_data,
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


# ---------------------------------------------------------
# Production dependency producers
#
# Phase 1에서는 stateful Institutional Flow를 실행하지 않는다.
# current flow_state.json이 historical date로 유입될 위험을
# 먼저 차단하기 위함이다.
# ---------------------------------------------------------

from filters.strategist_filters import (
    market_regime_filter,
    liquidity_filter,
    policy_filter_with_expectations,
    high_yield_spread_filter,
    credit_stress_filter,
    drift_monitor_filter,
    pseudo_gamma_filter,
    structural_filter,
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def load_backtest_macro_df() -> pd.DataFrame:

    path = DATA_DIR / "macro_data.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Backtest macro file not found: {path}"
        )

    print(f"[LOAD] {path}")

    df = pd.read_csv(path)

    if "date" not in df.columns:
        raise ValueError(
            "macro_data.csv does not contain 'date'"
        )

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df = (
        df.dropna(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )

    return df


def attach_positioning_layer_backtest(
    market_data: dict[str, Any],
    df: pd.DataFrame,
    idx: int,
) -> dict[str, Any]:

    path = DATA_DIR / "positioning_data.csv"

    if not path.exists():
        market_data["_POSITIONING_AUDIT_ERROR"] = (
            f"missing file: {path}"
        )
        return market_data

    pos_df = pd.read_csv(path)

    if "date" not in pos_df.columns:
        market_data["_POSITIONING_AUDIT_ERROR"] = (
            "positioning_data.csv missing date"
        )
        return market_data

    pos_df["date"] = pd.to_datetime(
        pos_df["date"],
        errors="coerce",
    )

    current_date = pd.to_datetime(
        df.iloc[idx]["date"]
    )

    # PIT rule:
    # current signal date보다 미래인 positioning row는 절대 사용 금지.
    hist = (
        pos_df[
            pos_df["date"] <= current_date
        ]
        .dropna(subset=["date"])
        .sort_values("date")
    )

    if hist.empty:
        market_data["_POSITIONING_AUDIT_ERROR"] = (
            "no historical positioning row"
        )
        return market_data

    latest = hist.iloc[-1]

    keys = (
        "SP500_POS_Z",
        "US10Y_POS_Z",
        "DXY_POS_Z",
        "DEALER_GAMMA_BIAS",
        "CTA_MOMENTUM_SCORE",
        "GAMMA_FETCH_OK",
        "CTA_FETCH_OK",
    )

    for key in keys:
        if key in latest.index:
            market_data[key] = latest.get(key)

    market_data["_POS_ASOF"] = (
        latest["date"].strftime("%Y-%m-%d")
    )

    return market_data

# ---------------------------------------------------------
# PIT Safety Wrapper
# ---------------------------------------------------------

def run_pit_safe_attach(
    attach_func,
    market_data: dict[str, Any],
    signal_date: pd.Timestamp,
    asof_keys: tuple[str, ...],
) -> dict[str, Any]:
    """
    Audit 전용 PIT wrapper.

    Production attach 함수 자체는 수정하지 않는다.

    원리:
    1. attach 함수가 사용하는 CSV를 signal_date까지만 보이도록 해야 한다.
    2. attach 실행 후 ASOF가 signal_date 이후면 즉시 실패시킨다.

    주의:
    이 함수 자체만으로 CSV를 잘라주지는 않는다.
    따라서 다음 단계에서 각 loader를 historical cutoff 방식으로
    audit 안에서 patch한다.

    여기서는 우선 미래 날짜 유입을 탐지하는 hard gate 역할을 한다.
    """

    market_data = attach_func(market_data) or market_data

    future_asof = []

    for key in asof_keys:

        raw = market_data.get(key)

        if raw in (None, "", "N/A"):
            continue

        # Treasury fallback 같은 문자열은 historical audit에서 허용하지 않음
        if str(raw).upper() == "TREASURY_FALLBACK":
            future_asof.append(
                f"{key}=TREASURY_FALLBACK"
            )
            continue

        try:
            asof = pd.to_datetime(raw)

            if asof > signal_date:
                future_asof.append(
                    f"{key}={asof.strftime('%Y-%m-%d')}"
                )

        except Exception:
            future_asof.append(
                f"{key}=INVALID:{raw}"
            )

    if future_asof:
        raise RuntimeError(
            "PIT VIOLATION | "
            f"signal_date={signal_date.strftime('%Y-%m-%d')} | "
            + " | ".join(future_asof)
        )

    return market_data

from unittest.mock import patch


def _cut_df_to_signal_date(
    df: pd.DataFrame,
    signal_date: pd.Timestamp,
) -> pd.DataFrame:
    """
    Point-in-time cutoff:
    signal_date 이후의 row를 제거한다.
    """
    if df is None or df.empty:
        return df

    if "date" not in df.columns:
        return df

    out = df.copy()

    out["date"] = pd.to_datetime(
        out["date"],
        errors="coerce",
    )

    out = (
        out[
            out["date"] <= signal_date
        ]
        .copy()
        .sort_values("date")
        .reset_index(drop=True)
    )

    return out


def attach_pit_external_layers(
    market_data: dict[str, Any],
    signal_date: pd.Timestamp,
) -> dict[str, Any]:
    """
    Phase 1 Audit 전용 PIT external-data harness.

    대상:
    - Liquidity
    - Credit / HY OAS
    - FRED extras
    - Sovereign
    - Sentiment

    Production 코드는 수정하지 않는다.
    각 production attach 함수가 loader를 호출할 때
    signal_date 이후 데이터가 보이지 않도록 임시 patch한다.
    """

    import scripts.generate_report as gr

    # --------------------------------------------------
    # 원본 데이터 로드
    # --------------------------------------------------

    liq_df = gr.load_liquidity_df()

    credit_df = gr.load_credit_spread_df()

    fred_df = gr.load_fred_extras_df()

    sovereign_df = gr.load_sovereign_spreads_df()

    # --------------------------------------------------
    # signal_date 기준 PIT cutoff
    # --------------------------------------------------

    liq_hist = _cut_df_to_signal_date(
        liq_df,
        signal_date,
    )

    credit_hist = _cut_df_to_signal_date(
        credit_df,
        signal_date,
    )

    fred_hist = _cut_df_to_signal_date(
        fred_df,
        signal_date,
    )

    sovereign_hist = _cut_df_to_signal_date(
        sovereign_df,
        signal_date,
    )

    # --------------------------------------------------
    # 1) Liquidity
    # --------------------------------------------------

    with patch.object(
        gr,
        "load_liquidity_df",
        return_value=liq_hist,
    ):
        market_data = (
            gr.attach_liquidity_layer(
                market_data
            )
            or market_data
        )

    # --------------------------------------------------
    # 2) Credit / HY OAS
    # --------------------------------------------------

    with patch.object(
        gr,
        "load_credit_spread_df",
        return_value=credit_hist,
    ):
        market_data = (
            gr.attach_credit_spread_layer(
                market_data
            )
            or market_data
        )

    # --------------------------------------------------
    # 3) FRED extras
    #
    # 중요:
    # historical audit에서 Treasury fallback이
    # 현재값을 끌어오는 것을 막는다.
    # --------------------------------------------------

    with (
        patch.object(
            gr,
            "load_fred_extras_df",
            return_value=fred_hist,
        ),
        patch(
            "filters.treasury_fallback."
            "fetch_treasury_yield_fallback",
            return_value={},
        ),
    ):
        market_data = (
            gr.attach_fred_extras_layer(
                market_data
            )
            or market_data
        )

    # --------------------------------------------------
    # 4) Sovereign
    # --------------------------------------------------

    with patch.object(
        gr,
        "load_sovereign_spreads_df",
        return_value=sovereign_hist,
    ):
        market_data = (
            gr.attach_sovereign_spread_layer(
                market_data
            )
            or market_data
        )

    # --------------------------------------------------
    # 5) Sentiment
    #
    # attach_sentiment_proxy_layer()는 loader가 아니라
    # CSV를 직접 읽고 마지막 row를 사용한다.
    #
    # 따라서 Production 함수를 호출하지 않고,
    # 동일 CSV를 signal_date까지 잘라 마지막 값을 사용한다.
    # --------------------------------------------------

    sentiment_path = (
        DATA_DIR
        / "sentiment_proxy.csv"
    )

    if (
        sentiment_path.exists()
        and sentiment_path.stat().st_size > 0
    ):
        try:

            sentiment_df = pd.read_csv(
                sentiment_path
            )

            sentiment_hist = (
                _cut_df_to_signal_date(
                    sentiment_df,
                    signal_date,
                )
            )

            if (
                not sentiment_hist.empty
                and
                "sentiment_proxy"
                in sentiment_hist.columns
            ):

                last = (
                    sentiment_hist.iloc[-1]
                )

                val = pd.to_numeric(
                    last.get(
                        "sentiment_proxy"
                    ),
                    errors="coerce",
                )

                if pd.notna(val):

                    market_data[
                        "SENTIMENT"
                    ] = {
                        "fear_greed":
                            float(val),

                        "source":
                            str(
                                last.get(
                                    "used",
                                    "proxy",
                                )
                            ),

                        "as_of":
                            pd.to_datetime(
                                last["date"]
                            ).strftime(
                                "%Y-%m-%d"
                            ),
                    }

        except Exception as exc:

            raise RuntimeError(
                "PIT SENTIMENT ERROR | "
                f"signal_date="
                f"{signal_date:%Y-%m-%d} | "
                f"{exc!r}"
            )

    # --------------------------------------------------
    # Hard PIT validation
    # --------------------------------------------------

    asof_checks = {
        "_LIQ_ASOF":
            market_data.get(
                "_LIQ_ASOF"
            ),

        "_HY_ASOF":
            market_data.get(
                "_HY_ASOF"
            ),

        "_FRED_ASOF":
            market_data.get(
                "_FRED_ASOF"
            ),

        "_SOV_ASOF":
            market_data.get(
                "_SOV_ASOF"
            ),

        "_SENTIMENT_ASOF":
            (
                market_data
                .get(
                    "SENTIMENT",
                    {},
                )
                .get(
                    "as_of"
                )
                if isinstance(
                    market_data.get(
                        "SENTIMENT"
                    ),
                    dict,
                )
                else None
            ),
    }

    violations = []

    for key, raw in (
        asof_checks.items()
    ):

        if raw in (
            None,
            "",
            "N/A",
        ):
            continue

        if (
            str(raw).upper()
            == "TREASURY_FALLBACK"
        ):
            violations.append(
                f"{key}="
                "TREASURY_FALLBACK"
            )
            continue

        try:

            asof = pd.to_datetime(
                raw
            )

            if asof > signal_date:

                violations.append(
                    f"{key}="
                    f"{asof:%Y-%m-%d}"
                )

        except Exception:

            violations.append(
                f"{key}=INVALID:"
                f"{raw}"
            )

    if violations:

        raise RuntimeError(
            "PIT VIOLATION | "
            f"signal_date="
            f"{signal_date:%Y-%m-%d} | "
            + " | ".join(
                violations
            )
        )

    return market_data


def nonempty(value: Any) -> bool:

    if value is None:
        return False

    if isinstance(value, str):
        return value.strip() not in {
            "",
            "N/A",
            "UNKNOWN",
        }

    if isinstance(value, dict):
        return bool(value)

    return True


def get_nested(
    obj: dict[str, Any],
    *keys: str,
) -> Any:

    value: Any = obj

    for key in keys:

        if not isinstance(value, dict):
            return None

        value = value.get(key)

    return value


# ---------------------------------------------------------
# Dependency Gate
# ---------------------------------------------------------

def dependency_snapshot(
    market_data: dict[str, Any],
) -> dict[str, Any]:

    sentiment = (
        market_data.get("SENTIMENT", {})
        or {}
    )

    hy = (
        market_data.get("HY_OAS", {})
        or {}
    )

    net_liq = (
        market_data.get("NET_LIQ", {})
        or {}
    )

    drift = (
        market_data.get("DRIFT", {})
        or {}
    )

    return {

        "market_regime":
            market_data.get("MARKET_REGIME"),

        "macro_narrative":
            market_data.get("MACRO_NARRATIVE"),

        "policy_bias_line":
            market_data.get("POLICY_BIAS_LINE"),

        "sentiment_fear_greed":
            sentiment.get("fear_greed"),

        "hy_oas_today":
            hy.get("today")
            if isinstance(hy, dict)
            else hy,

        "net_liq_pct_change":
            net_liq.get("pct_change")
            if isinstance(net_liq, dict)
            else None,

        "net_liq_level_bucket":
            (
                net_liq.get("level_bucket")
                if isinstance(net_liq, dict)
                else None
            )
            or market_data.get(
                "NET_LIQ_LEVEL_BUCKET"
            ),

        "struct_v2_state":
            market_data.get("STRUCT_V2_STATE"),

        "drift_score":
            (
                drift.get("score")
                if isinstance(drift, dict)
                else None
            )
            if drift
            else market_data.get(
                "DRIFT_SCORE"
            ),

        "drift_state":
            (
                drift.get("state")
                if isinstance(drift, dict)
                else None
            )
            if drift
            else market_data.get(
                "DRIFT_STATE"
            ),

        "gamma_state":
            market_data.get("GAMMA_STATE"),

        "sp500_pos_z":
            market_data.get("SP500_POS_Z"),

        "pos_asof":
            market_data.get("_POS_ASOF"),

        # Phase 1에서 일부러 실행하지 않음.
        "institutional_flow":
            market_data.get(
                "INSTITUTIONAL_FLOW"
            ),

        "prev_flow_state":
            market_data.get(
                "PREV_FLOW_STATE"
            ),

        "prev_flow_score":
            market_data.get(
                "PREV_FLOW_SCORE"
            ),
    }


def evaluate_gate(
    snapshot: dict[str, Any],
) -> tuple[str, str]:

    # Phase 1 핵심:
    # stateful Flow 3개는 아직 Gate 대상에서 제외.
    required = (
        "market_regime",
        "macro_narrative",
        "policy_bias_line",
        "sentiment_fear_greed",
        "hy_oas_today",
        "net_liq_pct_change",
        "struct_v2_state",
        "drift_score",
        "gamma_state",
        "sp500_pos_z",
    )

    missing = [
        key
        for key in required
        if not nonempty(snapshot.get(key))
    ]

    if missing:
        return (
            "FAIL",
            "|".join(missing),
        )

    return "PASS", ""


# ---------------------------------------------------------
# Historical Harness
# ---------------------------------------------------------

def main() -> None:

    df = load_backtest_macro_df()

    df = merge_sovereign_spreads_into_macro_df(
        df
    )

    dates = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    selected_indices = df.index[
        (dates >= START_DATE)
        & (dates <= END_DATE)
    ]
    selected_indices = selected_indices[:10]

    print(
        "[PHASE1] rows:",
        len(selected_indices),
    )

    rows: list[dict[str, Any]] = []

    for count, idx in enumerate(
        selected_indices,
        start=1,
    ):

        signal_date = pd.to_datetime(
            df.iloc[idx]["date"]
        )

        try:

            # ---------------------------------------------
            # 1. Historical base market_data
            # ---------------------------------------------

            market_data = build_market_data(
                df,
                idx,
            )

            # ---------------------------------------------
            # 2. PIT-oriented attach layers
            # ---------------------------------------------
            market_data = attach_pit_external_layers(
                market_data,
                signal_date,
            )


            market_data = (
                attach_positioning_layer_backtest(
                    market_data,
                    df,
                    idx,
                )
            )

            market_data = (
                attach_geopolitical_ew_layer(
                    market_data,
                    df,
                    idx,
                )
                or market_data
            )

            market_data = (
                attach_country_risk_layer(
                    market_data,
                    df,
                    idx,
                )
                or market_data
            )

            market_data = (
                attach_sector_momentum_layer(
                    market_data,
                    df,
                    idx,
                )
                or market_data
            )

            market_data = (
                attach_geo_similarity_layer(
                    market_data
                )
                or market_data
            )

        

            market_data = (
                attach_drift_data_layer(
                    market_data
                )
                or market_data
            )

            market_data = (
                attach_growth_sustainability_layer(
                    market_data,
                    df,
                    idx,
                )
                or market_data
            )

            market_data = (
                attach_breadth_layer(
                    market_data,
                    df,
                    idx,
                )
                or market_data
            )

            market_data = (
                attach_leadership_layer(
                    market_data,
                    df,
                    idx,
                )
                or market_data
            )

            # ---------------------------------------------
            # 3. Dependency producers
            #
            # Production 상대적 순서를 유지한다.
            # Institutional Flow는 Phase 2에서
            # historical state replay와 함께 추가한다.
            # ---------------------------------------------

            market_regime_filter(
                market_data
            )

            liquidity_filter(
                market_data
            )

            policy_filter_with_expectations(
                market_data
            )

            high_yield_spread_filter(
                market_data
            )

            credit_stress_filter(
                market_data
            )

            drift_monitor_filter(
                market_data
            )

            pseudo_gamma_filter(
                market_data
            )

            structural_filter(
                market_data
            )

            # ---------------------------------------------
            # 4. Snapshot + Gate
            # ---------------------------------------------

            snapshot = dependency_snapshot(
                market_data
            )

            gate_status, missing = (
                evaluate_gate(snapshot)
            )

            row = {
                "date":
                    signal_date.strftime(
                        "%Y-%m-%d"
                    ),

                "gate_status":
                    gate_status,

                "missing_dependencies":
                    missing,

                **snapshot,
            }

            rows.append(row)

        except Exception as exc:

            rows.append({
                "date":
                    signal_date.strftime(
                        "%Y-%m-%d"
                    ),
                "gate_status":
                    "ERROR",
                "missing_dependencies":
                    "",
                "error":
                    repr(exc),
            })

        if (
            count % 25 == 0
            or count == len(selected_indices)
        ):
            print(
                f"[PHASE1] "
                f"{count}/"
                f"{len(selected_indices)}"
            )

    # -----------------------------------------------------
    # Output
    # -----------------------------------------------------

    result = pd.DataFrame(rows)

    out = (
        OUTPUT_DIR
        / "filter13_dependency_gate_v2.csv"
    )

    result.to_csv(
        out,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("[SAVED]", out)

    if "gate_status" in result.columns:

        print()
        print(
            "[GATE STATUS]"
        )

        print(
            result["gate_status"]
            .value_counts(
                dropna=False
            )
            .to_string()
        )

    failed = result[
        result["gate_status"] != "PASS"
    ]

    if not failed.empty:

        print()
        print(
            "[FIRST FAILED ROWS]"
        )

        cols = [
            c
            for c in (
                "date",
                "gate_status",
                "missing_dependencies",
                "error",
            )
            if c in failed.columns
        ]

        print(
            failed[cols]
            .head(20)
            .to_string(
                index=False
            )
        )

    print()
    print(
        "PHASE 1 COMPLETE."
    )

    print(
        "Do NOT run attribution yet."
    )


if __name__ == "__main__":
    main()