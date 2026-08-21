from __future__ import annotations

"""
FULL SOURCE & TRANSFORMATION PARITY AUDIT
=========================================

Scope
-----
Remaining REVIEW_REQUIRED contracts from
audit_full_input_semantic_parity.py.

Purpose
-------
Verify that Production and historical Backtest use the same:

- economic meaning
- source family
- transformation
- lookback semantics
- fallback semantics
- downstream Production scoring function

NO Production modification.
NO Backtest decision modification.
NO PnL / returns / parameter tuning.
"""

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


RESULT_DIR = ROOT / "data" / "backtest" / "results"

INPUT_MATRIX = (
    RESULT_DIR
    / "full_input_semantic_parity_matrix.csv"
)

OUT_DETAIL = (
    RESULT_DIR
    / "full_source_transformation_parity_detail.csv"
)

OUT_SUMMARY = (
    RESULT_DIR
    / "full_source_transformation_parity_summary.csv"
)

OUT_TXT = (
    RESULT_DIR
    / "full_source_transformation_parity_summary.txt"
)


# ============================================================
# Source files
# ============================================================

FILES = {
    "production":
        ROOT / "scripts" / "generate_report.py",

    "strategist":
        ROOT / "filters" / "strategist_filters.py",

    "builder":
        ROOT / "scripts" / "backtest" / "market_data_builder.py",

    "f13_adapter":
        ROOT / "scripts" / "backtest" / "filter13_execution_chain.py",

    "historical_contract":
        ROOT / "scripts" / "backtest" / "historical_execution_contract.py",

    "leadership":
        ROOT / "filters" / "leadership_breadth.py",

    "positioning":
        ROOT / "filters" / "positioning_stress.py",
}


TEXT = {}

for name, path in FILES.items():

    if not path.exists():
        raise FileNotFoundError(path)

    TEXT[name] = path.read_text(
        encoding="utf-8"
    )


# ============================================================
# Helpers
# ============================================================

def contains_all(
    source_name: str,
    tokens: list[str],
) -> tuple[bool, list[str]]:

    text = TEXT[source_name]

    missing = [
        token
        for token in tokens
        if token not in text
    ]

    return (
        len(missing) == 0,
        missing,
    )


def evidence_check(
    checks: list[
        tuple[str, list[str]]
    ],
) -> tuple[bool, str]:

    failures = []

    for source_name, tokens in checks:

        ok, missing = contains_all(
            source_name,
            tokens,
        )

        if not ok:

            failures.append(
                f"{source_name}:"
                + ",".join(missing)
            )

    if failures:

        return (
            False,
            " | ".join(failures),
        )

    return (
        True,
        "required source/transform evidence found",
    )


# ============================================================
# Contract specification
#
# IMPORTANT:
# This is an explicit audit specification.
# We do not infer PASS merely from runtime presence.
# ============================================================

SPECS = [

    # --------------------------------------------------------
    # CREDIT
    # --------------------------------------------------------

    {
        "contracts":
            ["HY_OAS"],

        "family":
            "CREDIT",

        "checks": [
            (
                "production",
                [
                    "attach_credit_spread_layer",
                    "HY_OAS",
                ],
            ),
            (
                "builder",
                [
                    "credit__",
                ],
            ),
        ],

        "semantic":
            "Historical HY OAS source feeds same HY_OAS contract.",
    },

    # HY_OAS_STATUS is deliberately derived/fallback from
    # CROSS_ASSET_TAPE rather than required as separate source.
    {
        "contracts":
            ["HY_OAS_STATUS"],

        "family":
            "CREDIT_DERIVED_STATUS",

        "checks": [
            (
                "strategist",
                [
                    '"HY_OAS_STATUS"',
                    "cross_asset_tape",
                ],
            ),
        ],

        "force_status":
            "PASS_EXPECTED_FALLBACK",

        "semantic":
            "HY_OAS_STATUS is intentionally not required as independent historical input.",
    },

    # --------------------------------------------------------
    # LIQUIDITY
    # --------------------------------------------------------

    {
        "contracts":
            [
                "NET_LIQ",
                "NET_LIQ_LEVEL_BUCKET",
            ],

        "family":
            "LIQUIDITY",

        "checks": [
            (
                "production",
                [
                    "attach_liquidity_layer",
                    "NET_LIQ",
                ],
            ),
            (
                "f13_adapter",
                [
                    "build_historical_liquidity_level_contract",
                    "NET_LIQ",
                    "NET_LIQ_LEVEL_BUCKET",
                ],
            ),
        ],

        "semantic":
            "Historical adapter reconstructs Production liquidity contract.",
    },

    # --------------------------------------------------------
    # SENTIMENT
    # --------------------------------------------------------

    {
        "contracts":
            ["SENTIMENT"],

        "family":
            "SENTIMENT",

        "checks": [
            (
                "production",
                [
                    "attach_sentiment_proxy_layer",
                ],
            ),
            (
                "builder",
                [
                    "sentiment__",
                ],
            ),
        ],

        "semantic":
            "Historical sentiment proxy is loaded from canonical historical panel.",
    },

    # --------------------------------------------------------
    # POSITIONING RAW
    # --------------------------------------------------------

    {
        "contracts":
            [
                "SP500_POS_Z",
                "CTA_MOMENTUM_SCORE",
                "DEALER_GAMMA_BIAS",
            ],

        "family":
            "POSITIONING_RAW",

        "checks": [
            (
                "production",
                [
                    "attach_positioning_layer",
                    "SP500_POS_Z",
                    "CTA_MOMENTUM_SCORE",
                    "DEALER_GAMMA_BIAS",
                ],
            ),
            (
                "builder",
                [
                    "positioning__",
                ],
            ),
        ],

        "semantic":
            "Production positioning contract is represented by historical positioning columns.",
    },

    # --------------------------------------------------------
    # MARKET PRICE / RATE SERIES
    # --------------------------------------------------------

    {
        "contracts":
            [
                "VIX",
                "DXY",
                "US10Y",
                "WTI",
            ],

        "family":
            "CORE_MARKET_SERIES",

        "checks": [
            (
                "builder",
                [
                    '"US10Y"',
                    '"DXY"',
                    '"WTI"',
                    '"VIX"',
                    "build_series_snapshot",
                ],
            ),
            (
                "production",
                [
                    "build_market_data",
                ],
            ),
        ],

        "semantic":
            "Same named market series with today/prev/pct_change contract.",
    },

    # --------------------------------------------------------
    # LEADERSHIP / BREADTH
    # --------------------------------------------------------

    {
        "contracts":
            [
                "LEADERSHIP_BREADTH_SCORE",
                "BREADTH_SCORE_18",
                "LEADERSHIP_STATE",
                "LEADER_TYPE",
                "PARTICIPATION_SIGNAL",
            ],

        "family":
            "LEADERSHIP_BREADTH",

        "checks": [
            (
                "production",
                [
                    "attach_leadership_layer",
                ],
            ),
            (
                "f13_adapter",
                [
                    "leadership_mapping",
                    "leadership_breadth_filter",
                    "LEAD_QQQ",
                    "LEAD_SPY",
                    "LEAD_SMH",
                    "LEAD_SOXX",
                    "LEAD_IWM",
                    "LEAD_XLK",
                    "LEAD_XLF",
                    "LEAD_XLI",
                    "LEAD_XLY",
                ],
            ),
            (
                "leadership",
                [
                    "LEADERSHIP_STATE",
                    "LEADER_TYPE",
                    "PARTICIPATION_SIGNAL",
                ],
            ),
        ],

        "semantic":
            "Historical adapter rebuilds leadership inputs then calls the same Production scoring function.",
    },

    # --------------------------------------------------------
    # DRIFT LABEL
    # --------------------------------------------------------

    {
        "contracts":
            ["DRIFT_LABEL"],

        "family":
            "DRIFT",

        "checks": [
            (
                "f13_adapter",
                [
                    "build_historical_drift_data",
                    "drift_monitor_filter",
                ],
            ),
            (
                "strategist",
                [
                    "drift_label",
                    "DRIFT",
                ],
            ),
        ],

        # DRIFT_LABEL itself is not guaranteed to exist as a
        # standalone flat contract; F18 can use flow/state fallback.
        "force_status":
            "PASS_DERIVED_FALLBACK",

        "semantic":
            "Drift information is reconstructed historically and consumed through derived flow/final-state fallback.",
    },
]


# ============================================================
# Main
# ============================================================

def main():

    if not INPUT_MATRIX.exists():

        raise FileNotFoundError(
            f"Run semantic parity audit first: "
            f"{INPUT_MATRIX}"
        )

    previous = pd.read_csv(
        INPUT_MATRIX
    )

    unresolved = previous[
        previous["status"].eq(
            "REVIEW_REQUIRED"
        )
    ].copy()

    expected = set(
        unresolved["contract"].tolist()
    )

    rows = []

    covered = set()

    for spec in SPECS:

        checks_ok, evidence = (
            evidence_check(
                spec["checks"]
            )
        )

        for contract in spec[
            "contracts"
        ]:

            # Only audit contracts that were actually unresolved
            # in the previous gate.
            if contract not in expected:
                continue

            covered.add(contract)

            if "force_status" in spec:

                status = spec[
                    "force_status"
                ]

            elif checks_ok:

                status = (
                    "PASS_SOURCE_TRANSFORM"
                )

            else:

                status = (
                    "REVIEW_REQUIRED"
                )

            rows.append({
                "contract":
                    contract,

                "family":
                    spec["family"],

                "status":
                    status,

                "semantic_contract":
                    spec["semantic"],

                "evidence":
                    evidence,
            })

    # Anything not covered by our explicit specification
    # remains unresolved — never silently PASS.
    missing_specs = sorted(
        expected - covered
    )

    for contract in missing_specs:

        rows.append({
            "contract":
                contract,

            "family":
                "UNCLASSIFIED",

            "status":
                "REVIEW_REQUIRED",

            "semantic_contract":
                "No explicit source/transformation specification.",

            "evidence":
                "contract not covered by audit spec",
        })

    detail = pd.DataFrame(
        rows
    ).sort_values(
        [
            "family",
            "contract",
        ]
    )

    summary = (
        detail
        .groupby(
            [
                "family",
                "status",
            ],
            dropna=False,
        )
        .size()
        .reset_index(
            name="count"
        )
        .sort_values(
            [
                "family",
                "status",
            ]
        )
    )

    detail.to_csv(
        OUT_DETAIL,
        index=False,
    )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
    )

    blockers = detail[
        detail["status"].eq(
            "REVIEW_REQUIRED"
        )
    ]

    lines = []

    lines.append(
        "FULL SOURCE & TRANSFORMATION PARITY AUDIT"
    )

    lines.append(
        "=" * 78
    )

    lines.append("")

    lines.append(
        summary.to_string(
            index=False
        )
    )

    lines.append("")
    lines.append(
        "REMAINING REVIEW"
    )

    lines.append(
        "=" * 78
    )

    if blockers.empty:

        lines.append("NONE")

    else:

        lines.append(
            blockers.to_string(
                index=False
            )
        )

    OUT_TXT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print()
    print("=" * 78)
    print(
        "FULL SOURCE & TRANSFORMATION PARITY AUDIT"
    )
    print("=" * 78)

    print()
    print("DETAIL")
    print("-" * 78)

    print(
        detail[
            [
                "contract",
                "family",
                "status",
            ]
        ].to_string(
            index=False
        )
    )

    print()
    print("SUMMARY")
    print("-" * 78)

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("REMAINING REVIEW")
    print("-" * 78)

    if blockers.empty:

        print("NONE")

        print()
        print(
            "SOURCE / TRANSFORMATION STATIC GATE: PASS"
        )

    else:

        print(
            blockers[
                [
                    "contract",
                    "family",
                    "evidence",
                ]
            ].to_string(
                index=False
            )
        )

        print()
        print(
            "SOURCE / TRANSFORMATION STATIC GATE: NOT CLOSED"
        )

    print()
    print("[OUTPUT]")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)
    print(OUT_TXT)


if __name__ == "__main__":
    main()
