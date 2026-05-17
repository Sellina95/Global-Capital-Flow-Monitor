from filters.strategist_filters import narrative_engine_filter

# 테스트 케이스 공통 베이스
base_template = {
    "STRUCT_V2_STATE": "NEUTRAL",
    "POLICY_BIAS_LINE": "Policy Bias: MIXED",
    "SENTIMENT": {"fear_greed": 55},
    "HY_OAS": {"today": 2.8},
    "NET_LIQ": {"pct_change": 1.2, "level_bucket": "MID"},
    "SP500_POS_Z": 0.5,
    "DRIFT": {"score": 2, "state": "👀 EARLY DRIFT", "label": "NEUTRAL", "combo_signal": "NONE"},
    "INSTITUTIONAL_FLOW": {"score": 2, "state": "🌱 LIGHT TRACE", "confidence": "LOW"},
    "GAMMA_STATE": "🟡 TRANSITION",
    "PREV_FLOW_STATE": "NO CLEAR FLOW",
    "PREV_FLOW_SCORE": 0,
    "FINAL_STATE": {},
}

test_cases = {
    "Goldilocks": {
        **base_template,
        "MARKET_REGIME": "GOLDILOCKS",
        "MACRO_NARRATIVE": "DISINFLATION",
    },

    "Reflation": {
        **base_template,
        "MARKET_REGIME": "RISK-ON / REFLATION",
        "MACRO_NARRATIVE": "REFLATION",
    },

    "Inflation Shock": {
        **base_template,
        "MARKET_REGIME": "HARD RISK-OFF / INFLATION SHOCK",
        "MACRO_NARRATIVE": "STAGFLATION_RISK",
        "HY_OAS": {"today": 4.8},
        "STRUCT_V2_STATE": "STAGFLATION",
        "POLICY_BIAS_LINE": "Policy Bias: TIGHTENING",
        
    
    },
    
    "Stagflation": {
        **base_template,
        "MARKET_REGIME": "SOFT RISK-OFF / STAGFLATION",
        "MACRO_NARRATIVE": "STAGFLATION_RISK",
        "HY_OAS": {"today": 4.2},
        "STRUCT_V2_STATE": "STAGFLATION",
        "POLICY_BIAS_LINE": "Policy Bias: TIGHTENING",
    },

    "Credit Crisis": {
        **base_template,
        "MARKET_REGIME": "HARD RISK-OFF / CREDIT CRISIS",
        "MACRO_NARRATIVE": "CREDIT_STRESS",
        "HY_OAS": {"today": 7.5},
        "STRUCT_V2_STATE": "SYSTEMIC",
        "POLICY_BIAS_LINE": "Policy Bias: TIGHTENING",
    },
    
    
}

for name, market_data in test_cases.items():
    print("=" * 70)
    print(name)
    print(narrative_engine_filter(market_data))
    print("[FINAL_STATE]")
    print(market_data.get("FINAL_STATE"))