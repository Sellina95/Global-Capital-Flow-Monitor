from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

import pandas as pd


# ============================================================
# Paths / Imports
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import filters.strategist_filters as sf

from scripts.backtest.market_data_builder import build_market_data
from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)


DATA_DIR = ROOT / "data" / "backtest"
PANEL_PATH = DATA_DIR / "master_panel.csv"

RESULT_DIR = DATA_DIR / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DAILY_OUT = RESULT_DIR / "filter13_budget_attribution_current_daily.csv"
SUMMARY_OUT = RESULT_DIR / "filter13_budget_attribution_current_summary.csv"
TEXT_OUT = RESULT_DIR / "filter13_budget_attribution_current_summary.txt"


# ============================================================
# Helpers
# ============================================================

def to_float(x: Any) -> Optional[float]:
    if x is None:
        return None

    if isinstance(x, (int, float)):
        try:
            value = float(x)
            if pd.isna(value):
                return None
            return value
        except Exception:
            return None

    try:
        value = float(
            str(x)
            .replace(",", "")
            .replace("%", "")
        )

        if pd.isna(value):
            return None

        return value

    except Exception:
        return None


def clamp(
    x: int,
    lo: int = 0,
    hi: int = 100,
) -> int:
    return max(
        lo,
        min(
            hi,
            int(x),
        ),
    )


def sentiment_state(
    fear: Optional[float],
) -> str:

    if fear is None:
        return "N/A"

    if fear < 30:
        return "FEAR"

    if fear > 70:
        return "GREED"

    return "NEUTRAL"


def liq_direction(
    pct: Optional[float],
) -> str:

    if pct is None:
        return "N/A"

    if pct > 0:
        return "UP"

    if pct < 0:
        return "DOWN"

    return "FLAT"


# ============================================================
# Current Production Filter13 Budget Attribution
#
# 중요:
# - 현재 strategist_filters.py의 Narrative Engine 계산 구조를
#   Audit 목적으로 단계별 재현한다.
# - Production 함수 자체는 수정하지 않는다.
# - 마지막에는 실제 sf.narrative_engine_filter() 결과와 비교한다.
# ============================================================

def calculate_filter13_attribution(
    market_data: dict[str, Any],
) -> dict[str, Any]:

    # --------------------------------------------------------
    # Pull Inputs
    # --------------------------------------------------------

    struct_v2 = str(
        market_data.get(
            "STRUCT_V2_STATE",
            "NEUTRAL",
        )
        or "NEUTRAL"
    ).upper()

    policy_bias_line = str(
        market_data.get(
            "POLICY_BIAS_LINE",
            "",
        )
        or ""
    )

    sentiment = (
        market_data.get(
            "SENTIMENT",
            {},
        )
        or {}
    )

    fear = to_float(
        sentiment.get(
            "fear_greed"
        )
    )

    sent_state = sentiment_state(
        fear
    )

    hy_oas = (
        market_data.get(
            "HY_OAS",
            {},
        )
        or {}
    )

    hy_oas_today = to_float(
        hy_oas.get(
            "today"
        )
    )

    credit_calm: Optional[bool] = None

    if hy_oas_today is not None:
        credit_calm = (
            hy_oas_today < 4.0
        )

    net_liq = (
        market_data.get(
            "NET_LIQ",
            {},
        )
        or {}
    )

    net_liq_pct = to_float(
        net_liq.get(
            "pct_change"
        )
    )

    liq_dir_tag = liq_direction(
        net_liq_pct
    )

    liq_level_bucket = str(
        net_liq.get(
            "level_bucket"
        )
        or market_data.get(
            "NET_LIQ_LEVEL_BUCKET"
        )
        or "N/A"
    ).upper()

    if liq_level_bucket not in (
        "HIGH",
        "MID",
        "LOW",
    ):
        liq_level_bucket = "N/A"

    phase = str(
        market_data.get(
            "MARKET_REGIME",
            "N/A",
        )
        or "N/A"
    )

    phase_upper = phase.upper()

    macro_narrative = str(
        market_data.get(
            "MACRO_NARRATIVE",
            "N/A",
        )
        or "N/A"
    ).upper()

    cross_asset_tape = (
        market_data.get(
            "CROSS_ASSET_TAPE",
            {},
        )
        or {}
    )

    policy_upper = (
        policy_bias_line.upper()
    )

    mixed = (
        "MIXED"
        in policy_upper
    )

    easing = (
        "EASING"
        in policy_upper
    )

    tightening = (
        "TIGHTENING"
        in policy_upper
    )

    pos_z = to_float(
        market_data.get(
            "SP500_POS_Z",
            0.0,
        )
    )

    if pos_z is None:
        pos_z = 0.0

    drift = (
        market_data.get(
            "DRIFT",
            {},
        )
        or {}
    )

    drift_score = drift.get(
        "score",
        market_data.get(
            "DRIFT_SCORE",
            0,
        ),
    )

    try:
        drift_score = int(
            float(
                drift_score
            )
        )
    except Exception:
        drift_score = 0

    flow = (
        market_data.get(
            "INSTITUTIONAL_FLOW",
            {},
        )
        or {}
    )

    flow_score = flow.get(
        "score",
        0,
    )

    try:
        flow_score = int(
            float(
                flow_score
            )
        )
    except Exception:
        flow_score = 0

    gamma_state = str(
        market_data.get(
            "GAMMA_STATE",
            "N/A",
        )
        or "N/A"
    ).upper()

    prev_flow_state = str(
        market_data.get(
            "PREV_FLOW_STATE",
            "N/A",
        )
        or "N/A"
    ).upper()

    prev_flow_score = to_float(
        market_data.get(
            "PREV_FLOW_SCORE",
            0,
        )
    )

    if prev_flow_score is None:
        prev_flow_score = 0.0

    # --------------------------------------------------------
    # Base Budget
    # --------------------------------------------------------

    if sent_state == "FEAR":
        budget = 35

    elif sent_state == "GREED":
        budget = 70

    elif sent_state == "NEUTRAL":
        budget = 55

    else:
        budget = 50

    base_budget = budget

    # --------------------------------------------------------
    # Policy / Structure
    # --------------------------------------------------------

    before = budget

    if not mixed:

        if (
            easing
            and not tightening
        ):
            budget += 10

        elif (
            tightening
            and not easing
        ):
            budget -= 10

    policy_delta = (
        budget - before
    )

    # --------------------------------------------------------
    # Credit
    # --------------------------------------------------------

    before = budget

    if credit_calm is True:
        budget += 5

    elif credit_calm is False:
        budget -= 10

    credit_delta = (
        budget - before
    )

    # --------------------------------------------------------
    # Liquidity
    # --------------------------------------------------------

    before = budget

    if liq_dir_tag == "UP":
        budget += 5

    elif liq_dir_tag == "DOWN":
        budget -= 10

    if liq_level_bucket == "HIGH":
        budget += 5

    elif liq_level_bucket == "LOW":
        budget -= 5

    liquidity_delta = (
        budget - before
    )

    # --------------------------------------------------------
    # Structural v2
    # CURRENT Production Logic
    # --------------------------------------------------------

    before = budget

    v2_cap = 100

    vix_block = (
        market_data.get(
            "VIX",
            {},
        )
        or {}
    )

    vix_today = to_float(
        vix_block.get(
            "today"
        )
    )

    vix_pct = to_float(
        vix_block.get(
            "pct_change"
        )
    )

    credit_stress = (
        credit_calm is False
    )

    liq_stress = (
        liq_dir_tag == "DOWN"
        and liq_level_bucket == "LOW"
    )

    vol_stress = (
        (
            vix_today is not None
            and vix_today >= 25
        )
        or
        (
            vix_pct is not None
            and vix_pct >= 25
        )
    )

    systemic_confirmed = (
        "SYSTEMIC" in struct_v2
        and (
            credit_stress
            or liq_stress
            or vol_stress
        )
    )

    systemic_watch = (
        "SYSTEMIC" in struct_v2
        and not systemic_confirmed
    )

    if systemic_confirmed:

        budget -= 20
        v2_cap = 30

    elif systemic_watch:

        budget -= 4
        v2_cap = 70

    elif "STAGFLATION" in struct_v2:

        budget -= 15
        v2_cap = 40

    structural_delta = (
        budget - before
    )

    # --------------------------------------------------------
    # Drift
    # --------------------------------------------------------

    before = budget

    drift_tilt = 0

    if drift_score >= 6:
        drift_tilt = 3

    elif drift_score >= 3:
        drift_tilt = 1

    elif drift_score <= -3:
        drift_tilt = -3

    budget += drift_tilt

    drift_delta = (
        budget - before
    )

    # --------------------------------------------------------
    # Flow / Gamma
    # --------------------------------------------------------

    before = budget

    flow_gamma_tilt = 0

    if (
        drift_score >= 3
        and flow_score >= 3
        and "TRANSITION" in gamma_state
    ):
        flow_gamma_tilt = 2

    elif (
        drift_score >= 5
        and flow_score >= 4
        and "POSITIVE" in gamma_state
    ):
        flow_gamma_tilt = 4

    budget += flow_gamma_tilt

    flow_gamma_delta = (
        budget - before
    )

    # --------------------------------------------------------
    # Flow Continuity
    # --------------------------------------------------------

    before = budget

    flow_continuity_tilt = 0
    flow_continuity_note = "N/A"

    if (
        "NO CLEAR FLOW"
        in prev_flow_state
        and flow_score >= 3
    ):

        flow_continuity_tilt = 2
        flow_continuity_note = (
            "NEW_FLOW_TRACE"
        )

    elif (
        "EARLY TRACE"
        in prev_flow_state
        and flow_score >= 5
    ):

        flow_continuity_tilt = 3
        flow_continuity_note = (
            "FLOW_STRENGTHENING"
        )

    elif (
        (
            "EARLY TRACE"
            in prev_flow_state
            or
            "BUILDING"
            in prev_flow_state
        )
        and flow_score <= 2
    ):

        flow_continuity_tilt = -3
        flow_continuity_note = (
            "FLOW_FADE"
        )

    elif (
        prev_flow_score >= 3
        and flow_score >= 3
    ):

        flow_continuity_tilt = 1
        flow_continuity_note = (
            "FLOW_PERSISTENCE"
        )

    budget += (
        flow_continuity_tilt
    )

    flow_continuity_delta = (
        budget - before
    )

    # --------------------------------------------------------
    # Flow Regime
    # --------------------------------------------------------

    before = budget

    flow_regime_tilt = 0

    if flow_score >= 7:
        flow_regime_tilt = 4

    elif flow_score >= 5:
        flow_regime_tilt = 3

    elif flow_score >= 3:
        flow_regime_tilt = 2

    elif flow_score >= 1:
        flow_regime_tilt = 1

    if (
        "SOFT RISK-OFF"
        in phase_upper
        and flow_score >= 3
    ):
        flow_regime_tilt += 1

    if (
        (
            "EVENT-WATCHING"
            in phase_upper
            or
            "WAITING"
            in phase_upper
        )
        and flow_score >= 5
    ):
        flow_regime_tilt += 2

    budget += flow_regime_tilt

    flow_regime_delta = (
        budget - before
    )

    # --------------------------------------------------------
    # Macro
    # --------------------------------------------------------

    before = budget

    macro_tilt = 0

    if "GOLDILOCKS" in phase_upper:
        macro_tilt += 8

    elif "REFLATION" in phase_upper:
        macro_tilt += 6

    elif "LIQUIDITY" in phase_upper:
        macro_tilt += 5

    elif (
        "TIGHTENING_GROWTH_SCARE"
        in macro_narrative
    ):
        macro_tilt -= 8

    elif "STAGFLATION" in phase_upper:
        macro_tilt -= 12

    elif "INFLATION SHOCK" in phase_upper:
        macro_tilt -= 12

    elif "INFLATION" in phase_upper:
        macro_tilt -= 6

    elif "HARD RISK-OFF" in phase_upper:
        macro_tilt -= 20

    budget += macro_tilt

    macro_delta = (
        budget - before
    )

    # --------------------------------------------------------
    # Positioning
    # --------------------------------------------------------

    before = budget

    if pos_z >= 2.0:
        budget -= 8

    elif pos_z >= 1.5:
        budget -= 4

    positioning_delta = (
        budget - before
    )

    # --------------------------------------------------------
    # Event-Watching Floor
    #
    # 이건 tilt가 아니라 floor이므로
    # 별도 attribution으로 기록.
    # --------------------------------------------------------

    before = budget

    if (
        (
            "EVENT-WATCHING"
            in phase_upper
            or
            "WAITING"
            in phase_upper
        )
        and credit_calm is True
    ):

        budget = max(
            budget,
            25,
        )

    event_floor_delta = (
        budget - before
    )

    # --------------------------------------------------------
    # Phase Cap
    # --------------------------------------------------------

    cap = 100

    hy_status = str(
        cross_asset_tape.get(
            "HY_OAS_STATUS",
            "UNKNOWN",
        )
        or "UNKNOWN"
    ).upper()

    if (
        phase_upper.startswith(
            "WAITING"
        )
        or
        "RANGE" in phase_upper
    ):

        cap = 60

    elif (
        phase_upper.startswith(
            "SHOCK RISK-OFF"
        )
        or
        "SYSTEMIC" in phase_upper
        or
        systemic_confirmed
        or
        (
            phase_upper.startswith(
                "HARD RISK-OFF"
            )
            and
            hy_status == "FRACTURE"
        )
    ):

        cap = 20

    elif phase_upper.startswith(
        "HARD RISK-OFF"
    ):

        recovery_watch = (
            liq_dir_tag == "UP"
            and flow_score >= 3
        )

        if (
            recovery_watch
            and hy_status != "FRACTURE"
        ):

            cap = 65

        elif hy_status == "HOT":

            cap = 35

        else:

            cap = 45

    elif phase_upper.startswith(
        "SOFT RISK-OFF"
    ):

        cap = (
            50
            if flow_score >= 3
            else 45
        )

    elif "RISK-OFF" in phase_upper:

        cap = 35

    elif "MIXED / FRAGILE" in phase_upper:

        cap = 55

    elif (
        phase_upper.startswith(
            "TRANSITION"
        )
        or
        "MIXED" in phase_upper
    ):

        cap = 65

    elif phase_upper.startswith(
        "RISK-ON"
    ):

        cap = 85

    if "SYSTEMIC" in struct_v2:
        cap = min(
            cap,
            30,
        )

    final_cap = min(
        cap,
        v2_cap,
    )

    pre_cap_budget = budget

    final_budget = min(
        int(
            round(
                budget
            )
        ),
        final_cap,
    )

    final_budget = clamp(
        final_budget,
        0,
        100,
    )

    phase_cap_delta = (
        final_budget
        - pre_cap_budget
    )

    return {
        # Inputs
        "sentiment_state": sent_state,
        "fear_greed": fear,
        "policy_bias_line": policy_bias_line,
        "credit_calm": credit_calm,
        "hy_oas_today": hy_oas_today,
        "liq_direction": liq_dir_tag,
        "liq_level_bucket": liq_level_bucket,
        "market_regime": phase,
        "macro_narrative": macro_narrative,
        "struct_v2_state": struct_v2,
        "systemic_confirmed": systemic_confirmed,
        "systemic_watch": systemic_watch,
        "drift_score": drift_score,
        "gamma_state": gamma_state,
        "flow_score": flow_score,
        "prev_flow_state": prev_flow_state,
        "prev_flow_score": prev_flow_score,
        "flow_continuity_note": flow_continuity_note,
        "sp500_pos_z": pos_z,

        # Attribution
        "base_budget": base_budget,
        "policy_delta": policy_delta,
        "credit_delta": credit_delta,
        "liquidity_delta": liquidity_delta,
        "structural_delta": structural_delta,
        "drift_delta": drift_delta,
        "flow_gamma_delta": flow_gamma_delta,
        "flow_continuity_delta": flow_continuity_delta,
        "flow_regime_delta": flow_regime_delta,
        "macro_delta": macro_delta,
        "positioning_delta": positioning_delta,
        "event_floor_delta": event_floor_delta,

        # Cap
        "pre_cap_budget": pre_cap_budget,
        "phase_cap": cap,
        "structural_cap": v2_cap,
        "final_cap": final_cap,
        "phase_cap_delta": phase_cap_delta,

        # Shadow result
        "audit_final_budget": final_budget,
    }


# ============================================================
# Main
# ============================================================

def main() -> None:

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    panel = (
        panel
        .sort_values("date")
        .reset_index(drop=True)
    )

    rows: list[
        dict[str, Any]
    ] = []

    flow_memory: dict[str, Any] = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    previous_exposure = 50.0

    valid_indices = panel.index[
        pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    ].tolist()

    # 2022년 Attribution 검증만 실행
    valid_indices = panel.index[
        pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    ].tolist()

    total = len(valid_indices)


    for count, idx in enumerate(
        valid_indices,
        start=1,
    ):

        market_data = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=previous_exposure,
        )

        # ----------------------------------------------------
        # 현재 Backtest Production-equivalent Execution Chain
        # Historical/PIT Drift + historical Flow memory 포함
        # ----------------------------------------------------

        flow_memory = (
            prepare_filter13_execution_state(
                market_data=market_data,
                panel=panel,
                row_index=idx,
                previous_flow_memory=flow_memory,
            )
        )

        # ----------------------------------------------------
        # Shadow Attribution
        # ----------------------------------------------------

        audit = (
            calculate_filter13_attribution(
                market_data
            )
        )

        # ----------------------------------------------------
        # 실제 Production Narrative Engine 실행
        # ----------------------------------------------------

        sf.narrative_engine_filter(
            market_data
        )

        production_budget = (
            market_data.get(
                "RISK_BUDGET"
            )
        )

        final_state = (
            market_data.get(
                "FINAL_STATE",
                {},
            )
            or {}
        )

        signal_date = pd.to_datetime(
            panel.iloc[idx][
                "signal_date"
            ]
        )

        execution_date = (
            panel.iloc[idx][
                "execution_date"
            ]
        )

        rows.append({
            "signal_date": signal_date.strftime(
                "%Y-%m-%d"
            ),

            "execution_date": (
                pd.to_datetime(
                    execution_date
                ).strftime(
                    "%Y-%m-%d"
                )
                if pd.notna(
                    execution_date
                )
                else None
            ),

            **audit,

            "production_risk_budget": production_budget,

            "budget_diff": (
                audit[
                    "audit_final_budget"
                ]
                - production_budget
                if production_budget is not None
                else None
            ),

            "risk_action": (
                final_state.get(
                    "risk_action"
                )
            ),

            "drift_source": (
                market_data.get(
                    "_DRIFT_SOURCE"
                )
            ),

            "drift_asof": (
                market_data.get(
                    "_DRIFT_ASOF"
                )
            ),

            "drift_missing_assets": (
                ",".join(
                    market_data.get(
                        "_DRIFT_MISSING_ASSETS",
                        [],
                    )
                    or []
                )
            ),
        })

        if count % 250 == 0:
            print(
                f"[AUDIT] "
                f"{count:,}/{total:,}"
            )

    daily = pd.DataFrame(
        rows
    )

    daily.to_csv(
        DAILY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Parity
    # ========================================================

    valid_diff = pd.to_numeric(
        daily[
            "budget_diff"
        ],
        errors="coerce",
    )

    parity_pass = (
        valid_diff
        .fillna(999999)
        .eq(0)
    )

    # ========================================================
    # Attribution Summary
    # ========================================================

    attribution_cols = [
        "policy_delta",
        "credit_delta",
        "liquidity_delta",
        "structural_delta",
        "drift_delta",
        "flow_gamma_delta",
        "flow_continuity_delta",
        "flow_regime_delta",
        "macro_delta",
        "positioning_delta",
        "event_floor_delta",
        "phase_cap_delta",
    ]

    summary_rows = []

    for col in attribution_cols:

        s = pd.to_numeric(
            daily[col],
            errors="coerce",
        )

        summary_rows.append({
            "component": col,

            "mean_delta": (
                s.mean()
            ),

            "median_delta": (
                s.median()
            ),

            "mean_negative_only": (
                s[
                    s < 0
                ].mean()
                if (
                    s < 0
                ).any()
                else 0.0
            ),

            "mean_positive_only": (
                s[
                    s > 0
                ].mean()
                if (
                    s > 0
                ).any()
                else 0.0
            ),

            "negative_days": int(
                (
                    s < 0
                ).sum()
            ),

            "positive_days": int(
                (
                    s > 0
                ).sum()
            ),

            "zero_days": int(
                (
                    s == 0
                ).sum()
            ),

            "total_absolute_impact": (
                s.abs().sum()
            ),
        })

    summary = pd.DataFrame(
        summary_rows
    )

    summary[
        "avg_reduction_contribution"
    ] = (
        summary[
            "mean_delta"
        ]
        .clip(
            upper=0
        )
        .abs()
    )

    summary = (
        summary
        .sort_values(
            [
                "avg_reduction_contribution",
                "total_absolute_impact",
            ],
            ascending=[
                False,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    summary.to_csv(
        SUMMARY_OUT,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Text Summary
    # ========================================================

    avg_base = pd.to_numeric(
        daily[
            "base_budget"
        ],
        errors="coerce",
    ).mean()

    avg_final = pd.to_numeric(
        daily[
            "production_risk_budget"
        ],
        errors="coerce",
    ).mean()

    avg_reduction = (
        avg_final
        - avg_base
    )

    pass_count = int(
        parity_pass.sum()
    )

    fail_count = int(
        len(
            daily
        )
        - pass_count
    )

    lines = []

    lines.append(
        "Filter13 Current Production Budget Attribution Audit"
    )

    lines.append(
        "=" * 60
    )

    lines.append(
        ""
    )

    lines.append(
        f"Rows: {len(daily):,}"
    )

    lines.append(
        f"Period: "
        f"{daily['signal_date'].min()} "
        f"~ "
        f"{daily['signal_date'].max()}"
    )

    lines.append(
        ""
    )

    lines.append(
        "Production vs Audit parity"
    )

    lines.append(
        f"PASS: {pass_count:,}"
    )

    lines.append(
        f"FAIL: {fail_count:,}"
    )

    lines.append(
        ""
    )

    lines.append(
        f"Average Base Budget: "
        f"{avg_base:.2f}"
    )

    lines.append(
        f"Average Final Budget: "
        f"{avg_final:.2f}"
    )

    lines.append(
        f"Average Base -> Final Change: "
        f"{avg_reduction:+.2f}%p"
    )

    lines.append(
        ""
    )

    lines.append(
        "Average Attribution"
    )

    lines.append(
        "-" * 60
    )

    for _, row in (
        summary.iterrows()
    ):

        lines.append(
            f"{row['component']:<28} "
            f"{row['mean_delta']:+7.3f} "
            f"| neg days="
            f"{int(row['negative_days']):4d} "
            f"| pos days="
            f"{int(row['positive_days']):4d}"
        )

    lines.append(
        ""
    )

    lines.append(
        "Top Reduction Drivers"
    )

    lines.append(
        "-" * 60
    )

    reduction_rank = (
        summary[
            summary[
                "avg_reduction_contribution"
            ]
            > 0
        ]
        .sort_values(
            "avg_reduction_contribution",
            ascending=False,
        )
    )

    for rank, (_, row) in enumerate(
        reduction_rank.iterrows(),
        start=1,
    ):

        lines.append(
            f"{rank}. "
            f"{row['component']} "
            f"({row['mean_delta']:+.3f}%p avg)"
        )

    TEXT_OUT.write_text(
        "\n".join(
            lines
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 70)

    print(
        "FILTER13 CURRENT ATTRIBUTION AUDIT COMPLETE"
    )

    print("=" * 70)

    print(
        "Daily :",
        DAILY_OUT,
    )

    print(
        "Summary:",
        SUMMARY_OUT,
    )

    print(
        "Text   :",
        TEXT_OUT,
    )

    print()

    print(
        f"Parity PASS: "
        f"{pass_count:,}"
    )

    print(
        f"Parity FAIL: "
        f"{fail_count:,}"
    )

    print()

    print(
        f"Average Base Budget : "
        f"{avg_base:.2f}"
    )

    print(
        f"Average Final Budget: "
        f"{avg_final:.2f}"
    )

    print(
        f"Average Change      : "
        f"{avg_reduction:+.2f}%p"
    )

    print()

    print(
        summary[
            [
                "component",
                "mean_delta",
                "negative_days",
                "positive_days",
            ]
        ]
        .to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
