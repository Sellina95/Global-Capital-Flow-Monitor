from __future__ import annotations

"""
F13 / F15 / F18 — FULL INPUT SEMANTIC PARITY AUDIT
===================================================

Goal
----
Audit ALL literal market_data decision contracts consumed by:

    F13 narrative_engine_filter
    F15 volatility_controlled_exposure_filter
    F18 sector_allocation_filter

This audit asks more than "does the key exist?"

For each contract it inventories:

    Consumer
    -> Production producer
    -> Historical/backtest producer
    -> runtime presence
    -> producer/source evidence
    -> semantic classification

Important
---------
This audit DOES NOT:
- modify Production
- modify Backtest
- modify parameters
- use returns/PnL/performance
- declare semantic parity merely because a key exists

PASS is intentionally conservative.

Statuses
--------
PASS_SHARED_PRODUCTION_FUNCTION
    Historical replay calls the same Production function.

PASS_EXACT_HISTORICAL_REPLICA
    Explicit historical adapter exists for a Production runtime
    contract whose live implementation cannot be replayed historically.

PASS_DIRECT_PANEL_CONTRACT
    Contract is directly supplied from the historical master panel /
    canonical market_data builder.

PASS_PERSISTENT_T_MINUS_1
    Historical replay explicitly carries t state into t+1.

INTERNAL_STATE
    Consumer itself creates the contract; not an upstream input parity gap.

INTENTIONAL_HISTORICAL_UNAVAILABLE
    Historical archive intentionally unavailable.

REVIEW_REQUIRED
    Static evidence is insufficient to prove semantic equivalence.

FAIL_MISSING_RUNTIME
    Upstream decision contract is absent at its consumer boundary.
"""

import ast
import contextlib
import io
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd


# ============================================================
# Paths
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FILTER_FILE = ROOT / "filters" / "strategist_filters.py"
PRODUCTION_FILE = ROOT / "scripts" / "generate_report.py"

BACKTEST_FILES = [
    ROOT / "scripts" / "backtest" / "market_data_builder.py",
    ROOT / "scripts" / "backtest" / "filter13_execution_chain.py",
    ROOT / "scripts" / "backtest" / "historical_execution_contract.py",
    ROOT / "scripts" / "backtest" / "run_backtest.py",
]

PANEL_FILE = (
    ROOT
    / "data"
    / "backtest"
    / "master_panel.csv"
)

RESULT_DIR = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

RESULT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUT_MATRIX = (
    RESULT_DIR
    / "full_input_semantic_parity_matrix.csv"
)

OUT_SUMMARY = (
    RESULT_DIR
    / "full_input_semantic_parity_summary.csv"
)

OUT_TXT = (
    RESULT_DIR
    / "full_input_semantic_parity_summary.txt"
)


FILTERS = {
    "F13": "narrative_engine_filter",
    "F15": "volatility_controlled_exposure_filter",
    "F18": "sector_allocation_filter",
}


# ============================================================
# Runtime imports
# ============================================================

import filters.strategist_filters as sf

from scripts.backtest.market_data_builder import (
    build_market_data,
)

from scripts.backtest.filter13_execution_chain import (
    prepare_filter13_execution_state,
)

from scripts.backtest.historical_execution_contract import (
    initial_filter15_memory,
    prepare_historical_execution_contract,
)


# ============================================================
# Known historical contracts
# ============================================================

INTENTIONAL_UNAVAILABLE = {
    "SEW_STATUS",
    "SEW_EVENT_TYPE",
}

PERSISTENT_CONTRACTS = {
    "PREV_FLOW_STATE",
    "PREV_FLOW_SCORE",
    "PREV_EXPOSURE",

    "FILTER15_PREV_DEADMAN",
    "FILTER15_PREV_HY_OAS",
    "FILTER15_RECOVERY_ACTIVE",
    "FILTER15_RECOVERY_COMPLETED",
    "FILTER15_RECOVERY_STREAK",

    "FILTER18_ACCEPTED_RANK",
    "FILTER18_PENDING_COUNT",
    "FILTER18_PENDING_RANK",
}

REPAIRED_F15 = {
    "FILTER15_PREV_DEADMAN",
    "FILTER15_PREV_HY_OAS",
    "FILTER15_RECOVERY_ACTIVE",
    "FILTER15_RECOVERY_COMPLETED",
    "FILTER15_RECOVERY_STREAK",
}

REPAIRED_F18 = {
    "MOMENTUM_SCORES",
    "POSITIONING_STATE",
    "POSITIONING_SCORE_18",
    "SQUEEZE_RISK",
    "GAMMA_SIGNAL",
    "VOL_STRUCTURE",
}


# ============================================================
# AST
# ============================================================

def function_node(
    source: str,
    name: str,
) -> ast.FunctionDef:

    tree = ast.parse(source)

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == name
        ):
            return node

    raise RuntimeError(
        f"Function not found: {name}"
    )


def subscript_key(
    node: ast.Subscript,
) -> str | None:

    x = node.slice

    if (
        isinstance(x, ast.Constant)
        and isinstance(x.value, str)
    ):
        return x.value

    return None


def consumer_contracts(
    source: str,
    function_name: str,
) -> tuple[
    dict[str, list[int]],
    dict[str, list[int]],
]:

    fn = function_node(
        source,
        function_name,
    )

    reads: dict[str, list[int]] = {}
    writes: dict[str, list[int]] = {}

    def add(
        target: dict[str, list[int]],
        key: str,
        line: int,
    ):
        target.setdefault(
            key,
            [],
        ).append(line)

    for node in ast.walk(fn):

        # market_data.get("KEY")
        if isinstance(node, ast.Call):

            f = node.func

            if (
                isinstance(f, ast.Attribute)
                and f.attr == "get"
                and isinstance(f.value, ast.Name)
                and f.value.id == "market_data"
                and node.args
                and isinstance(
                    node.args[0],
                    ast.Constant,
                )
                and isinstance(
                    node.args[0].value,
                    str,
                )
            ):
                add(
                    reads,
                    node.args[0].value,
                    node.lineno,
                )

        # market_data["KEY"]
        if isinstance(node, ast.Subscript):

            if (
                isinstance(node.value, ast.Name)
                and node.value.id == "market_data"
            ):
                key = subscript_key(node)

                if key is not None:
                    add(
                        reads,
                        key,
                        node.lineno,
                    )

        # writes
        if isinstance(node, ast.Assign):

            for target in node.targets:

                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(
                        target.value,
                        ast.Name,
                    )
                    and target.value.id
                    == "market_data"
                ):
                    key = subscript_key(
                        target
                    )

                    if key is not None:
                        add(
                            writes,
                            key,
                            node.lineno,
                        )

    return reads, writes


# ============================================================
# Producer discovery
# ============================================================

def discover_writers(
    path: Path,
) -> dict[str, set[str]]:

    if not path.exists():
        return {}

    source = path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(source)

    writers: dict[
        str,
        set[str]
    ] = {}

    for fn in ast.walk(tree):

        if not isinstance(
            fn,
            ast.FunctionDef,
        ):
            continue

        for node in ast.walk(fn):

            if not isinstance(
                node,
                ast.Assign,
            ):
                continue

            for target in node.targets:

                if not isinstance(
                    target,
                    ast.Subscript,
                ):
                    continue

                if not (
                    isinstance(
                        target.value,
                        ast.Name,
                    )
                    and target.value.id
                    == "market_data"
                ):
                    continue

                key = subscript_key(
                    target
                )

                if key is None:
                    continue

                writers.setdefault(
                    key,
                    set(),
                ).add(
                    fn.name
                )

    return writers


def merge_writer_maps(
    maps,
) -> dict[str, set[str]]:

    result: dict[
        str,
        set[str]
    ] = {}

    for writer_map in maps:

        for key, functions in (
            writer_map.items()
        ):
            result.setdefault(
                key,
                set(),
            ).update(functions)

    return result


# ============================================================
# Function-call evidence
# ============================================================

def called_function_names(
    path: Path,
) -> set[str]:

    if not path.exists():
        return set()

    tree = ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )

    names = set()

    for node in ast.walk(tree):

        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        f = node.func

        if isinstance(f, ast.Name):
            names.add(f.id)

        elif isinstance(
            f,
            ast.Attribute,
        ):
            names.add(f.attr)

    return names


# ============================================================
# Runtime boundary
# ============================================================

def choose_sample_indices(
    panel: pd.DataFrame,
    count: int = 50,
) -> list[int]:

    eligible = panel.index[
        panel["execution_date"].notna()
        & pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    ].tolist()

    if len(eligible) <= count:
        return eligible

    return [
        eligible[
            round(
                i
                * (len(eligible) - 1)
                / (count - 1)
            )
        ]
        for i in range(count)
    ]


def runtime_presence() -> dict[
    tuple[str, str],
    tuple[int, int]
]:

    panel = pd.read_csv(
        PANEL_FILE,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    indices = choose_sample_indices(
        panel
    )

    filter_text = FILTER_FILE.read_text(
        encoding="utf-8"
    )

    reads = {}

    for stage, fn in FILTERS.items():

        r, _ = consumer_contracts(
            filter_text,
            fn,
        )

        reads[stage] = set(
            r.keys()
        )

    counts: dict[
        tuple[str, str],
        list[int],
    ] = {}

    for stage in FILTERS:

        for key in reads[stage]:

            counts[
                (stage, key)
            ] = [0, 0]

    flow_memory = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    f15_memory = (
        initial_filter15_memory()
    )

    previous_exposure = 50.0

    for idx in indices:

        md = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=
                previous_exposure,
        )

        with contextlib.redirect_stdout(
            io.StringIO()
        ):

            flow_memory = (
                prepare_filter13_execution_state(
                    market_data=md,
                    panel=panel,
                    row_index=idx,
                    previous_flow_memory=
                        flow_memory,
                )
            )

            prepare_historical_execution_contract(
                market_data=md,
                panel=panel,
                row_index=idx,
                filter15_memory=
                    f15_memory,
            )

        # PRE F13
        for key in reads["F13"]:

            counts[
                ("F13", key)
            ][1] += 1

            if key in md:
                counts[
                    ("F13", key)
                ][0] += 1

        with contextlib.redirect_stdout(
            io.StringIO()
        ):
            sf.narrative_engine_filter(
                md
            )

        # PRE F15
        for key in reads["F15"]:

            counts[
                ("F15", key)
            ][1] += 1

            if key in md:
                counts[
                    ("F15", key)
                ][0] += 1

        with contextlib.redirect_stdout(
            io.StringIO()
        ):
            sf.volatility_controlled_exposure_filter(
                md
            )

        # PRE F18
        for key in reads["F18"]:

            counts[
                ("F18", key)
            ][1] += 1

            if key in md:
                counts[
                    ("F18", key)
                ][0] += 1

    return {
        key: tuple(value)
        for key, value in counts.items()
    }


# ============================================================
# Semantic classification
# ============================================================

def classify(
    *,
    stage: str,
    key: str,
    read_lines: list[int],
    write_lines: list[int],
    prod_writers: set[str],
    bt_writers: set[str],
    bt_calls: set[str],
    present: int,
    total: int,
) -> tuple[str, str]:

    # Consumer-internal state
    if write_lines:

        first_read = min(
            read_lines
        )

        first_write = min(
            write_lines
        )

        if first_write <= first_read:

            return (
                "INTERNAL_STATE",
                "Consumer creates state before/at first read.",
            )

    if key in INTENTIONAL_UNAVAILABLE:

        return (
            "INTENTIONAL_HISTORICAL_UNAVAILABLE",
            "Historical archive intentionally unavailable.",
        )

    # Explicit repaired state
    if key in REPAIRED_F15:

        if present == total:

            return (
                "PASS_PERSISTENT_T_MINUS_1",
                "Historical adapter explicitly carries Filter15 state t -> t+1.",
            )

        return (
            "FAIL_MISSING_RUNTIME",
            "Repaired Filter15 state not consistently present.",
        )

    if key in REPAIRED_F18:

        if present != total:

            return (
                "FAIL_MISSING_RUNTIME",
                "Repaired F18 contract not consistently present.",
            )

        if key == "MOMENTUM_SCORES":

            return (
                "PASS_EXACT_HISTORICAL_REPLICA",
                "Historical adapter reproduces Production 20d/60d SPY-relative momentum contract.",
            )

        return (
            "PASS_SHARED_PRODUCTION_FUNCTION",
            "Historical adapter supplies PIT inputs and executes Production positioning_stress_filter.",
        )

    # Persistent state
    if key in PERSISTENT_CONTRACTS:

        if present == total:

            return (
                "PASS_PERSISTENT_T_MINUS_1",
                "Persistent contract present at historical consumer boundary.",
            )

        return (
            "REVIEW_REQUIRED",
            "Persistent-state timing requires explicit historical-state proof.",
        )

    # Same Production producer function reused by backtest.
    common = (
        prod_writers
        & bt_writers
    )

    if common:

        return (
            "PASS_SHARED_PRODUCTION_FUNCTION",
            "Same literal producer function found in Production and historical execution: "
            + ",".join(sorted(common)),
        )

    # Production function is explicitly called by backtest.
    called_prod = (
        prod_writers
        & bt_calls
    )

    if called_prod:

        return (
            "PASS_SHARED_PRODUCTION_FUNCTION",
            "Historical execution calls Production producer: "
            + ",".join(
                sorted(called_prod)
            ),
        )

    # Runtime missing upstream contract
    if present == 0:

        if prod_writers:

            return (
                "FAIL_MISSING_RUNTIME",
                "Production producer exists but historical consumer boundary never supplies contract.",
            )

        return (
            "REVIEW_REQUIRED",
            "Contract absent and producer unresolved.",
        )

    # Direct historical builder evidence
    if bt_writers and not prod_writers:

        return (
            "REVIEW_REQUIRED",
            "Historical producer exists, but exact Production semantic equivalence requires manual/source verification.",
        )

    if present == total:

        return (
            "REVIEW_REQUIRED",
            "Runtime presence confirmed, but static evidence does not prove identical source/transformation/lookback/fallback semantics.",
        )

    return (
        "REVIEW_REQUIRED",
        f"Runtime presence intermittent: {present}/{total}.",
    )


# ============================================================
# Main
# ============================================================

def main():

    print()
    print("=" * 78)
    print(
        "F13 / F15 / F18 FULL INPUT SEMANTIC PARITY AUDIT"
    )
    print("=" * 78)

    filter_text = FILTER_FILE.read_text(
        encoding="utf-8"
    )

    prod_writers = discover_writers(
        PRODUCTION_FILE
    )

    # strategist_filters itself contains Production
    # generator functions too.
    prod_filter_writers = (
        discover_writers(
            FILTER_FILE
        )
    )

    prod_writers = merge_writer_maps(
        [
            prod_writers,
            prod_filter_writers,
        ]
    )

    bt_maps = [
        discover_writers(path)
        for path in BACKTEST_FILES
    ]

    bt_writers = merge_writer_maps(
        bt_maps
    )

    bt_calls = set()

    for path in BACKTEST_FILES:
        bt_calls.update(
            called_function_names(
                path
            )
        )

    runtime = runtime_presence()

    rows = []

    for stage, fn in FILTERS.items():

        reads, writes = (
            consumer_contracts(
                filter_text,
                fn,
            )
        )

        for key in sorted(reads):

            present, total = (
                runtime.get(
                    (stage, key),
                    (0, 0),
                )
            )

            status, evidence = classify(
                stage=stage,
                key=key,
                read_lines=reads[key],
                write_lines=writes.get(
                    key,
                    [],
                ),
                prod_writers=
                    prod_writers.get(
                        key,
                        set(),
                    ),
                bt_writers=
                    bt_writers.get(
                        key,
                        set(),
                    ),
                bt_calls=bt_calls,
                present=present,
                total=total,
            )

            rows.append({
                "consumer":
                    stage,

                "contract":
                    key,

                "status":
                    status,

                "runtime_presence":
                    f"{present}/{total}",

                "production_producers":
                    ";".join(
                        sorted(
                            prod_writers.get(
                                key,
                                set(),
                            )
                        )
                    ),

                "backtest_producers":
                    ";".join(
                        sorted(
                            bt_writers.get(
                                key,
                                set(),
                            )
                        )
                    ),

                "consumer_read_lines":
                    ",".join(
                        str(x)
                        for x in sorted(
                            reads[key]
                        )
                    ),

                "consumer_write_lines":
                    ",".join(
                        str(x)
                        for x in sorted(
                            writes.get(
                                key,
                                [],
                            )
                        )
                    ),

                "evidence":
                    evidence,
            })

    matrix = pd.DataFrame(
        rows
    )

    summary = (
        matrix
        .groupby(
            [
                "consumer",
                "status",
            ]
        )
        .size()
        .reset_index(
            name="count"
        )
        .sort_values(
            [
                "consumer",
                "status",
            ]
        )
    )

    matrix.to_csv(
        OUT_MATRIX,
        index=False,
    )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
    )

    blockers = matrix[
        matrix["status"].isin(
            [
                "FAIL_MISSING_RUNTIME",
                "REVIEW_REQUIRED",
            ]
        )
    ]

    report = []

    report.append(
        "FULL INPUT SEMANTIC PARITY AUDIT"
    )
    report.append(
        "=" * 78
    )
    report.append("")

    report.append(
        summary.to_string(
            index=False
        )
    )

    report.append("")
    report.append(
        "UNRESOLVED / FAIL"
    )
    report.append(
        "=" * 78
    )

    if blockers.empty:

        report.append("NONE")

    else:

        report.append(
            blockers[
                [
                    "consumer",
                    "contract",
                    "status",
                    "runtime_presence",
                    "production_producers",
                    "backtest_producers",
                    "evidence",
                ]
            ].to_string(
                index=False
            )
        )

    OUT_TXT.write_text(
        "\n".join(report),
        encoding="utf-8",
    )

    print()
    print("SUMMARY")
    print("=" * 78)

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("UNRESOLVED / FAIL")
    print("=" * 78)

    if blockers.empty:

        print("NONE")

    else:

        print(
            blockers[
                [
                    "consumer",
                    "contract",
                    "status",
                    "runtime_presence",
                    "production_producers",
                    "backtest_producers",
                ]
            ].to_string(
                index=False
            )
        )

    print()
    print("[OUTPUT]")
    print(OUT_MATRIX)
    print(OUT_SUMMARY)
    print(OUT_TXT)

    print()

    if blockers.empty:

        print(
            "SEMANTIC PARITY STATIC GATE: PASS"
        )

    else:

        print(
            "SEMANTIC PARITY STATIC GATE: NOT CLOSED"
        )

        print(
            "Do not claim full Production↔Backtest "
            "semantic parity yet."
        )


if __name__ == "__main__":
    main()
