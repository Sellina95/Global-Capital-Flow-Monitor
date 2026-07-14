"""
Filter13 Budget Audit

목적:
13번 Narrative Engine Risk Budget이
총노출(Risk Budget)을 줄인 원인을 단계별로 분해한다.

원칙:
- strategist_filters.py 수정 금지
- production 코드 수정 금지
- build_market_data() 재사용
- Audit 전용
"""
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

def load_backtest_macro_df():
    path = ROOT / "data" / "backtest" / "macro_data.csv"

    print(f"[DEBUG] loading backtest macro -> {path}")

    df = pd.read_csv(path)

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df = df.sort_values("date").reset_index(drop=True)

    return df

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from scripts.generate_report import (
    load_macro_df,
    merge_sovereign_spreads_into_macro_df,
    build_market_data,
    attach_liquidity_layer,
    attach_credit_spread_layer,
    attach_fred_extras_layer,
    attach_sovereign_spread_layer,
    attach_breadth_layer,
    attach_sentiment_proxy_layer,
    attach_sector_momentum_layer,
    attach_drift_data_layer,
    attach_growth_sustainability_layer,
    attach_leadership_layer,
    attach_positioning_layer,
    attach_expectation_layer,
    attach_geopolitical_ew_layer,
    attach_country_risk_layer,
    attach_geo_similarity_layer,
)

from filters.strategist_filters import (
    market_regime_filter,
)


OUTPUT_DIR = Path("data/backtest/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _to_float(x) -> Optional[float]:
    if x is None:
        return None

    if isinstance(x, (int, float)):
        return float(x)

    try:
        return float(
            str(x)
            .replace(",", "")
            .replace("%", "")
        )
    except Exception:
        return None


def _clamp(x: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(x)))


def _sentiment_state(fear: Optional[float]) -> str:

    if fear is None:
        return "N/A"

    if fear < 30:
        return "FEAR"

    if fear > 70:
        return "GREED"

    return "NEUTRAL"


def _liq_dir_tag(pct: Optional[float]) -> str:

    if pct is None:
        return "N/A"

    if pct > 0:
        return "UP"

    if pct < 0:
        return "DOWN"

    return "FLAT"


def audit_filter13_budget(
    market_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    13번 Budget Ledger

    각 단계별:
    before
    delta
    after

    기록 예정
    """

    result = {}

    # --------------------------------------------------
    # 1. Pull Signals
    # --------------------------------------------------

    sentiment = market_data.get(
        "SENTIMENT",
        {}
    ) or {}

    fear = _to_float(
        sentiment.get("fear_greed")
    )

    sent_state = _sentiment_state(fear)


    if sent_state == "FEAR":
        budget = 35

    elif sent_state == "GREED":
        budget = 70

    elif sent_state == "NEUTRAL":
        budget = 55

    else:
        budget = 50


    result["base_budget"] = budget


    # 다음 파트에서
    # Structure / Credit / Liquidity
    # 부터 이어서 작성

        # --------------------------------------------------
    # 2. Structure Tilt
    # --------------------------------------------------

    policy_bias_line = str(
        market_data.get("POLICY_BIAS_LINE", "") or ""
    )

    policy_upper = policy_bias_line.upper()

    mixed = "MIXED" in policy_upper
    easing = "EASING" in policy_upper
    tightening = "TIGHTENING" in policy_upper

    before = budget
    structure_delta = 0

    if not mixed:

        if easing and not tightening:
            structure_delta = 10

        elif tightening and not easing:
            structure_delta = -10


    budget += structure_delta

    result["structure_before"] = before
    result["structure_delta"] = structure_delta
    result["structure_after"] = budget


    # --------------------------------------------------
    # 3. Credit Tilt
    # --------------------------------------------------

    hy_oas = market_data.get(
        "HY_OAS",
        {}
    ) or {}

    hy_oas_today = _to_float(
        hy_oas.get("today")
    )


    credit_calm = None

    if hy_oas_today is not None:
        credit_calm = hy_oas_today < 4.0


    before = budget

    credit_delta = 0

    if credit_calm is True:
        credit_delta = 5

    elif credit_calm is False:
        credit_delta = -10


    budget += credit_delta


    result["credit_before"] = before
    result["credit_delta"] = credit_delta
    result["credit_after"] = budget
    result["credit_calm"] = credit_calm
    result["hy_oas_today"] = hy_oas_today


    # --------------------------------------------------
    # 4. Liquidity Tilt
    # --------------------------------------------------

    net_liq = market_data.get(
        "NET_LIQ",
        {}
    ) or {}


    net_liq_pct = _to_float(
        net_liq.get("pct_change")
    )


    liq_dir = _liq_dir_tag(
        net_liq_pct
    )


    before = budget

    liquidity_delta = 0


    if liq_dir == "UP":
        liquidity_delta = 5

    elif liq_dir == "DOWN":
        liquidity_delta = -10


    level_bucket = str(
        net_liq.get(
            "level_bucket",
            "N/A"
        )
    ).upper()


    if level_bucket == "HIGH":
        liquidity_delta += 5

    elif level_bucket == "LOW":
        liquidity_delta -= 5



    budget += liquidity_delta


    result["liquidity_before"] = before
    result["liquidity_delta"] = liquidity_delta
    result["liquidity_after"] = budget

    result["liquidity_dir"] = liq_dir
    result["liquidity_level"] = level_bucket


    # 다음 파트에서
    # Structural v2
    # Drift
    # Flow
    # Macro
    # Positioning
    # Phase Cap
    # Final Budget
    # 추가 예정
        # --------------------------------------------------
    # 5. Structural v2 Penalty
    # --------------------------------------------------

    before = budget

    struct_v2 = str(
        market_data.get(
            "STRUCT_V2_STATE",
            "NEUTRAL"
        )
    ).upper()


    vix_block = market_data.get(
        "VIX",
        {}
    ) or {}

    vix_today = _to_float(
        vix_block.get("today")
    )

    vix_pct = _to_float(
        vix_block.get("pct_change")
    )


    credit_stress = credit_calm is False

    liq_stress = (
        liq_dir == "DOWN"
        and level_bucket == "LOW"
    )

    vol_stress = (
        (vix_today is not None and vix_today >= 25)
        or
        (vix_pct is not None and vix_pct >= 25)
    )


    structural_delta = 0


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

        structural_delta = -20


    elif systemic_watch:

        structural_delta = -4


    elif "STAGFLATION" in struct_v2:

        structural_delta = -15



    budget += structural_delta


    result["structural_v2_before"] = before
    result["structural_v2_delta"] = structural_delta
    result["structural_v2_after"] = budget



    # --------------------------------------------------
    # 6. Drift Adjustment
    # --------------------------------------------------

    drift = market_data.get(
        "DRIFT",
        {}
    ) or {}


    drift_score = drift.get(
        "score",
        market_data.get(
            "DRIFT_SCORE",
            0
        )
    )


    try:
        drift_score = int(drift_score)

    except Exception:
        drift_score = 0



    before = budget

    drift_delta = 0


    if drift_score >= 6:

        drift_delta = 3

    elif drift_score >= 3:

        drift_delta = 1

    elif drift_score <= -3:

        drift_delta = -3



    budget += drift_delta


    result["drift_before"] = before
    result["drift_delta"] = drift_delta
    result["drift_after"] = budget
    result["drift_score"] = drift_score



    # --------------------------------------------------
    # 7. Flow Gamma Alignment
    # --------------------------------------------------

    flow = market_data.get(
        "INSTITUTIONAL_FLOW",
        {}
    ) or {}


    gamma_state = str(
        market_data.get(
            "GAMMA_STATE",
            "N/A"
        )
    ).upper()


    flow_score = flow.get(
        "score",
        0
    )


    try:
        flow_score = int(flow_score)

    except Exception:

        flow_score = 0



    before = budget

    flow_gamma_delta = 0


    if (
        drift_score >= 3
        and flow_score >= 3
        and "TRANSITION" in gamma_state
    ):

        flow_gamma_delta = 2


    elif (
        drift_score >= 5
        and flow_score >= 4
        and "POSITIVE" in gamma_state
    ):

        flow_gamma_delta = 4



    budget += flow_gamma_delta


    result["flow_gamma_before"] = before
    result["flow_gamma_delta"] = flow_gamma_delta
    result["flow_gamma_after"] = budget



    # --------------------------------------------------
    # 다음 파트:
    # Flow Continuity
    # Flow Regime
    # Macro
    # Positioning
    # Phase Cap
    # Output
    # --------------------------------------------------
        # --------------------------------------------------
    # 8. Flow Continuity
    # --------------------------------------------------

    before = budget

    prev_flow_state = str(
        market_data.get(
            "PREV_FLOW_STATE",
            "N/A"
        )
        or "N/A"
    ).upper()

    prev_flow_score = _to_float(
        market_data.get(
            "PREV_FLOW_SCORE",
            0
        )
    )

    if prev_flow_score is None:
        prev_flow_score = 0


    flow_continuity_delta = 0


    if (
        "NO CLEAR FLOW" in prev_flow_state
        and flow_score >= 3
    ):
        flow_continuity_delta = 2


    elif (
        "EARLY TRACE" in prev_flow_state
        and flow_score >= 5
    ):
        flow_continuity_delta = 3


    elif (
        (
            "EARLY TRACE" in prev_flow_state
            or "BUILDING" in prev_flow_state
        )
        and flow_score <= 2
    ):
        flow_continuity_delta = -3


    elif (
        prev_flow_score >= 3
        and flow_score >= 3
    ):
        flow_continuity_delta = 1



    budget += flow_continuity_delta


    result["flow_continuity_before"] = before
    result["flow_continuity_delta"] = flow_continuity_delta
    result["flow_continuity_after"] = budget



    # --------------------------------------------------
    # 9. Flow Regime
    # --------------------------------------------------

    before = budget

    flow_regime_delta = 0


    if flow_score >= 7:

        flow_regime_delta = 4

    elif flow_score >= 5:

        flow_regime_delta = 3

    elif flow_score >= 3:

        flow_regime_delta = 2

    elif flow_score >= 1:

        flow_regime_delta = 1



    phase = str(
        market_data.get(
            "MARKET_REGIME",
            "N/A"
        )
    )

    phase_upper = phase.upper()


    if (
        "SOFT RISK-OFF" in phase_upper
        and flow_score >= 3
    ):
        flow_regime_delta += 1


    if (
        (
            "EVENT-WATCHING" in phase_upper
            or "WAITING" in phase_upper
        )
        and flow_score >= 5
    ):
        flow_regime_delta += 2



    budget += flow_regime_delta


    result["flow_regime_before"] = before
    result["flow_regime_delta"] = flow_regime_delta
    result["flow_regime_after"] = budget



    # --------------------------------------------------
    # 10. Macro Tilt
    # --------------------------------------------------

    before = budget

    macro_delta = 0


    if "GOLDILOCKS" in phase_upper:

        macro_delta = 8

    elif "REFLATION" in phase_upper:

        macro_delta = 6

    elif "LIQUIDITY" in phase_upper:

        macro_delta = 5

    elif "TIGHTENING_GROWTH_SCARE" in str(
        market_data.get(
            "MACRO_NARRATIVE",
            ""
        )
    ).upper():

        macro_delta = -8

    elif "STAGFLATION" in phase_upper:

        macro_delta = -12

    elif "INFLATION SHOCK" in phase_upper:

        macro_delta = -12

    elif "INFLATION" in phase_upper:

        macro_delta = -6

    elif "HARD RISK-OFF" in phase_upper:

        macro_delta = -20



    budget += macro_delta


    result["macro_before"] = before
    result["macro_delta"] = macro_delta
    result["macro_after"] = budget



    # --------------------------------------------------
    # 11. Positioning Penalty
    # --------------------------------------------------

    before = budget

    positioning_delta = 0


    pos_z = _to_float(
        market_data.get(
            "SP500_POS_Z",
            0
        )
    )


    if pos_z is None:
        pos_z = 0


    if pos_z >= 2.0:

        positioning_delta = -8

    elif pos_z >= 1.5:

        positioning_delta = -4



    budget += positioning_delta


    result["positioning_before"] = before
    result["positioning_delta"] = positioning_delta
    result["positioning_after"] = budget
    result["pos_z"] = pos_z



    # 다음 파트:
    # Event Floor
    # Phase Cap
    # Final Budget
    # return
        # --------------------------------------------------
    # 12. Event Floor
    # --------------------------------------------------

    before = budget

    event_floor_delta = 0

    credit_calm = result.get(
        "credit_calm",
        None
    )


    if (
        (
            "EVENT-WATCHING" in phase_upper
            or "WAITING" in phase_upper
        )
        and credit_calm is True
        and budget < 25
    ):
        event_floor_delta = 25 - budget
        budget = 25


    result["event_floor_before"] = before
    result["event_floor_delta"] = event_floor_delta
    result["event_floor_after"] = budget



    # --------------------------------------------------
    # 13. Phase Cap
    # --------------------------------------------------

    before = budget

    phase_cap = 100


    if (
        phase_upper.startswith("WAITING")
        or "RANGE" in phase_upper
    ):

        phase_cap = 60


    elif phase_upper.startswith("HARD RISK-OFF"):

        phase_cap = 20


    elif phase_upper.startswith("SOFT RISK-OFF"):

        phase_cap = 50 if flow_score >= 3 else 45


    elif "RISK-OFF" in phase_upper:

        phase_cap = 35


    elif "MIXED / FRAGILE" in phase_upper:

        phase_cap = 55


    elif (
        phase_upper.startswith("TRANSITION")
        or "MIXED" in phase_upper
    ):

        phase_cap = 65


    elif phase_upper.startswith("RISK-ON"):

        phase_cap = 85



    v2_cap = 100

    if "SYSTEMIC" in struct_v2:
        v2_cap = 30

    elif "STAGFLATION" in struct_v2:
        v2_cap = 30



    final_cap = min(
        phase_cap,
        v2_cap
    )


    cap_reduction = 0

    if budget > final_cap:
        cap_reduction = final_cap - budget



    budget = min(
        int(round(budget)),
        final_cap
    )

    budget = _clamp(
        budget,
        0,
        100
    )


    result["phase_cap"] = phase_cap
    result["v2_cap"] = v2_cap
    result["final_cap"] = final_cap
    result["cap_reduction"] = cap_reduction


    result["final_budget"] = budget

    return result

def main():

    df = load_backtest_macro_df()

    df = merge_sovereign_spreads_into_macro_df(df)


    rows = []


    start_date = pd.Timestamp("2022-01-01")
    end_date = pd.Timestamp("2022-06-30")

    selected_indices = df.index[
        (pd.to_datetime(df["date"]) >= start_date)
        & (pd.to_datetime(df["date"]) <= end_date)
    ]

    print("DEBUG ROW COUNT:", len(selected_indices))

    for idx in selected_indices:

        try:

            market_data = build_market_data(
                df,
                idx
            )
            


            # Production pipeline 동일 재현
            market_data = attach_liquidity_layer(
                market_data
            ) or market_data

            market_data = attach_credit_spread_layer(
                market_data
            ) or market_data

            market_data = attach_fred_extras_layer(
                market_data
            ) or market_data

            market_data = attach_sovereign_spread_layer(
                market_data
            ) or market_data

            market_data = attach_expectation_layer(
                market_data
            ) or market_data

            market_data = attach_geopolitical_ew_layer(
                market_data,
                df,
                idx
            ) or market_data

            market_data = attach_country_risk_layer(
                market_data,
                df,
                idx
            ) or market_data

            market_data = attach_sector_momentum_layer(
                market_data,
                df,
                idx
            ) or market_data

            market_data = attach_geo_similarity_layer(
                market_data
            ) or market_data

            market_data = attach_sentiment_proxy_layer(
                market_data
            ) or market_data

            market_data = attach_drift_data_layer(
                market_data
            ) or market_data

            market_data = attach_growth_sustainability_layer(
                market_data,
                df,
                idx
            ) or market_data

            market_data = attach_breadth_layer(
                market_data,
                df,
                idx
            ) or market_data

            market_data = attach_leadership_layer(
                market_data,
                df,
                idx
            ) or market_data

            market_data = attach_positioning_layer(
                market_data
            ) or market_data


            market_regime_filter(
                market_data
            )
           




            audit = audit_filter13_budget(
                market_data
            )


            audit["date"] = (
                pd.to_datetime(
                    df.iloc[idx]["date"]
                )
                .strftime("%Y-%m-%d")
            )


            rows.append(audit)


        except Exception as e:
            print("ERROR:", idx, e)

            rows.append(
                {
                    "date": str(idx),
                    "error": str(e)
                }
            )


    print("DEBUG ROW COUNT:", len(rows))
    result = pd.DataFrame(rows)


    daily_path = (
        OUTPUT_DIR
        /
        "filter13_budget_audit_daily.csv"
    )

    summary_path = (
        OUTPUT_DIR
        /
        "filter13_budget_audit_summary.csv"
    )

    txt_path = (
        OUTPUT_DIR
        /
        "filter13_budget_audit_summary.txt"
    )



    result.to_csv(
        daily_path,
        index=False,
        encoding="utf-8-sig"
    )


    numeric = result.select_dtypes(
        include="number"
    )


    summary = numeric.sum().sort_values()


    summary.to_csv(
        summary_path
    )


    with open(
        txt_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "Filter13 Budget Audit Summary\n"
        )

        f.write(
            "=" * 40
            +
            "\n\n"
        )

        f.write(
            summary.to_string()
        )


    print("[OK]", daily_path)
    print("[OK]", summary_path)
    print("[OK]", txt_path)



if __name__ == "__main__":

    main()