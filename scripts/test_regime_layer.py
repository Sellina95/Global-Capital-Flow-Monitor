from filters.strategist_filters import (
    build_cross_asset_tape,
    interpret_macro_narrative,
    map_to_portfolio_regime,
)

history_template = {
    "US10Y_PCT_HISTORY": [
        -0.4, 0.2, 0.1, -0.3, 0.5,
        -0.2, 0.3, 0.1, -0.1, 0.4,
        -0.5, 0.2, 0.0, -0.2, 0.3,
        0.1, -0.1, 0.2, -0.3, 0.4,
    ],
    "DXY_PCT_HISTORY": [
        -0.2, 0.1, 0.0, -0.1, 0.2,
        -0.1, 0.1, 0.0, -0.2, 0.2,
        -0.1, 0.1, 0.0, -0.1, 0.2,
        0.1, -0.1, 0.0, -0.2, 0.1,
    ],
    "VIX_PCT_HISTORY": [
        -2.0, 1.5, -1.0, 2.0, -1.5,
        1.0, -2.5, 2.2, -1.8, 1.6,
        -2.1, 1.9, -1.2, 2.4, -1.7,
        1.3, -2.0, 1.8, -1.5, 2.1,
    ],
    "WTI_PCT_HISTORY": [
        -1.0, 0.8, -0.5, 1.2, -1.1,
        0.7, -0.9, 1.0, -0.6, 1.3,
        -1.2, 0.9, -0.4, 1.1, -0.8,
        0.6, -1.0, 0.7, -0.9, 1.2,
    ],
    "US10Y_HIST": [3.8, 3.9, 4.0, 4.1, 4.2, 4.0, 3.95, 4.05],
    "DXY_HIST": [98.0, 98.5, 99.0, 99.5, 100.0, 99.2, 98.8, 99.3],
    "VIX_HIST": [13.0, 14.2, 15.1, 16.0, 14.8, 15.5, 14.0, 15.2],
    "WTI_HIST": [70, 72, 74, 73, 75, 76, 74.5, 73.8],
}

cases = {
    "Goldilocks": {
        **history_template,
        "US10Y": {"today": 4.0, "prev": 4.2},
        "DXY": {"today": 98.0, "prev": 99.0},
        "VIX": {"today": 13.0, "prev": 15.0},
        "WTI": {"today": 70.0, "prev": 73.0},
        "HY_OAS": {"today": 2.8},
    },

    "Tightening Growth Scare": {
        **history_template,
        "US10Y": {"today": 4.6, "prev": 4.4},
        "DXY": {"today": 99.3, "prev": 98.8},
        "VIX": {"today": 18.4, "prev": 17.2},
        "WTI": {"today": 101.0, "prev": 105.0},
        "HY_OAS": {"today": 2.76},
    },

    "Inflation Shock": {
        **history_template,
        "US10Y": {"today": 4.8, "prev": 4.5},
        "DXY": {"today": 103.0, "prev": 101.0},
        "VIX": {"today": 24.0, "prev": 18.0},
        "WTI": {"today": 95.0, "prev": 88.0},
        "HY_OAS": {"today": 4.8},
    },

    "Reflation": {
        **history_template,
        "US10Y": {"today": 4.7, "prev": 4.5},
        "DXY": {"today": 98.0, "prev": 99.0},
        "VIX": {"today": 14.0, "prev": 16.0},
        "WTI": {"today": 90.0, "prev": 84.0},
        "HY_OAS": {"today": 2.9},
    },

    "Policy Easing": {
        **history_template,
        "US10Y": {"today": 4.0, "prev": 4.3},
        "DXY": {"today": 99.0, "prev": 101.0},
        "VIX": {"today": 15.0, "prev": 16.0},
        "WTI": {"today": 72.0, "prev": 74.0},
        "HY_OAS": {"today": 2.8},
    },

    "Stagflation": {
        **history_template,
        "US10Y": {"today": 4.9, "prev": 4.6},
        "DXY": {"today": 103.0, "prev": 101.0},
        "VIX": {"today": 19.0, "prev": 17.0},
        "WTI": {"today": 96.0, "prev": 90.0},
        "HY_OAS": {"today": 4.2},
    },
}

for case in test_cases:
    tape = build_cross_asset_tape(case)
    macro = interpret_macro_narrative(tape)
    regime = map_to_portfolio_regime("MIXED", macro, tape)

    print("=" * 60)
    print(case["name"])
    print("TAPE:", tape)
    print("MACRO:", macro)
    print("REGIME:", regime)
    