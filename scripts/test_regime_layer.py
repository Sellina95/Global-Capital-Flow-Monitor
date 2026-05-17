from filters.strategist_filters import (
    build_cross_asset_tape,
    interpret_macro_narrative,
    map_to_portfolio_regime,
)

test_cases = [
    {
        "name": "Goldilocks",
        "US10Y": {"today": 4.0, "prev": 4.2},
        "DXY": {"today": 98, "prev": 99},
        "VIX": {"today": 13, "prev": 15},
        "WTI": {"today": 70, "prev": 73},
        "HY_OAS": {"today": 2.8},
    },
    {
        "name": "Tightening Growth Scare",
        "US10Y": {"today": 4.6, "prev": 4.4},
        "DXY": {"today": 99.3, "prev": 98.8},
        "VIX": {"today": 18.4, "prev": 17.2},
        "WTI": {"today": 101, "prev": 105},
        "HY_OAS": {"today": 2.76},
    },
    {
        "name": "Inflation Shock",
        "US10Y": {"today": 4.8, "prev": 4.5},
        "DXY": {"today": 103, "prev": 101},
        "VIX": {"today": 24, "prev": 18},
        "WTI": {"today": 95, "prev": 88},
        "HY_OAS": {"today": 4.8},
    },
]

for case in test_cases:
    tape = build_cross_asset_tape(case)
    macro = interpret_macro_narrative(tape)
    regime = map_to_portfolio_regime("MIXED", macro, tape)

    print("=" * 60)
    print(case["name"])
    print("TAPE:", tape)
    print("MACRO:", macro)
    print("REGIME:", regime)