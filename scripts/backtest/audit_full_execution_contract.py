from __future__ import annotations

"""
FULL EXECUTION CONTRACT AUDIT v2
================================

Purpose
-------
Revalidate the canonical historical execution contract for:

    F13 -> F15 -> F18

without modifying Production or Backtest logic.

v2 improvement
--------------
v1 treated every literal market_data.get()/[] read as an upstream input.

That creates false positives because a filter may:
    - read an upstream input
    - create and later read an internal state
    - expose an output
    - consume a persistent t-1 state

v2 classifies contracts before declaring a parity gap.

Classification
--------------
UPSTREAM_INPUT
INTERNAL_STATE
PERSISTENT_STATE
INTENTIONAL_UNAVAILABLE
UNRESOLVED

Runtime status
--------------
PRESENT
MISSING
INTERMITTENT

Final audit status
------------------
PASS_RUNTIME_PRESENT
PASS_INTERNAL_STATE
HISTORICAL_EQUIVALENT
INTENTIONAL_UNAVAILABLE
CANDIDATE_PARITY_GAP
REVIEW_REQUIRED

IMPORTANT
---------
CANDIDATE_PARITY_GAP is not automatically a final FAIL.

It means:
    Production has evidence of an upstream producer,
    the consumer reads the contract,
    and the canonical historical boundary does not supply it.

No Production/Backtest logic is modified.
No returns/PnL/performance are used.
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
SCRIPTS_DIR = ROOT / "scripts"

for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

FILTER_FILE = ROOT / "filters" / "strategist_filters.py"
PRODUCTION_FILE = ROOT / "scripts" / "generate_report.py"

PANEL_PATH = (
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

OUTPUT_MATRIX = (
    RESULT_DIR
    / "full_execution_contract_matrix.csv"
)

OUTPUT_SUMMARY = (
    RESULT_DIR
    / "full_execution_contract_summary.csv"
)

OUTPUT_TXT = (
    RESULT_DIR
    / "full_execution_contract_summary.txt"
)


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

from scripts.backtest.institutional_backtest import (
    disable_live_side_effects,
    neutralize_all_side_effects,
)


# ============================================================
# Configuration
# ============================================================

FILTERS = {
    "F13": "narrative_engine_filter",
    "F15": "volatility_controlled_exposure_filter",
    "F18": "sector_allocation_filter",
}

BOUNDARIES = {
    "F13": "PRE_F13",
    "F15": "PRE_F15",
    "F18": "PRE_F18",
}

TARGET_SAMPLE_COUNT = 25


# Historical design exceptions that must remain visible.
INTENTIONAL_HISTORICAL_UNAVAILABLE = {
    "SEW_STATUS",
    "SEW_EVENT_TYPE",
}


# Known historical replacements for live/current state.
HISTORICAL_EQUIVALENTS = {
    "PREV_FLOW_STATE":
        "historical t-1 flow memory",

    "PREV_FLOW_SCORE":
        "historical t-1 flow memory",

    "POS_SLOPE":
        "historical PIT positioning history",

    "DRIFT_DATA":
        "historical PIT drift builder",

    "NET_LIQ_LEVEL_BUCKET":
        "historical liquidity level contract",
}


# State that by semantics is expected to persist from t-1.
#
# This list does NOT automatically mean parity.
# It only prevents us from misclassifying them as ordinary
# same-day upstream inputs.
PERSISTENT_STATE_KEYS = {
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


# ============================================================
# AST helpers
# ============================================================

def get_function_node(
    tree: ast.AST,
    function_name: str,
) -> ast.FunctionDef:

    for node in ast.walk(tree):

        if (
            isinstance(node, ast.FunctionDef)
            and node.name == function_name
        ):
            return node

    raise RuntimeError(
        f"Function not found: {function_name}"
    )


def literal_subscript_key(
    node: ast.Subscript,
) -> str | None:

    slice_node = node.slice

    if (
        isinstance(slice_node, ast.Constant)
        and isinstance(slice_node.value, str)
    ):
        return slice_node.value

    return None


def extract_reads(
    source_text: str,
    function_name: str,
) -> set[str]:

    tree = ast.parse(source_text)

    fn = get_function_node(
        tree,
        function_name,
    )

    reads: set[str] = set()

    for node in ast.walk(fn):

        # market_data.get("KEY")
        if isinstance(node, ast.Call):

            func = node.func

            if (
                isinstance(func, ast.Attribute)
                and func.attr == "get"
                and isinstance(func.value, ast.Name)
                and func.value.id == "market_data"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ):
                reads.add(
                    node.args[0].value
                )

        # market_data["KEY"]
        if isinstance(node, ast.Subscript):

            if not (
                isinstance(node.value, ast.Name)
                and node.value.id == "market_data"
            ):
                continue

            key = literal_subscript_key(
                node
            )

            if key is not None:
                reads.add(key)

    return reads


def extract_writes_with_lines(
    source_text: str,
    function_name: str,
) -> dict[str, list[int]]:
    """
    Detect literal writes inside the consumer:

        market_data["KEY"] = ...
        market_data["KEY"] += ...
        market_data["KEY"].update(...)

    Returns:
        KEY -> source line numbers
    """

    tree = ast.parse(source_text)

    fn = get_function_node(
        tree,
        function_name,
    )

    writes: dict[str, list[int]] = {}

    def add(
        key: str,
        line: int,
    ):
        writes.setdefault(
            key,
            [],
        ).append(line)

    for node in ast.walk(fn):

        # market_data["KEY"] = ...
        if isinstance(node, ast.Assign):

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

                key = literal_subscript_key(
                    target
                )

                if key is not None:
                    add(
                        key,
                        node.lineno,
                    )

        # market_data["KEY"] += ...
        elif isinstance(node, ast.AugAssign):

            target = node.target

            if (
                isinstance(
                    target,
                    ast.Subscript,
                )
                and isinstance(
                    target.value,
                    ast.Name,
                )
                and target.value.id
                == "market_data"
            ):

                key = literal_subscript_key(
                    target
                )

                if key is not None:
                    add(
                        key,
                        node.lineno,
                    )

        # market_data["KEY"].update(...)
        elif isinstance(node, ast.Call):

            func = node.func

            if not isinstance(
                func,
                ast.Attribute,
            ):
                continue

            base = func.value

            if not isinstance(
                base,
                ast.Subscript,
            ):
                continue

            if not (
                isinstance(
                    base.value,
                    ast.Name,
                )
                and base.value.id
                == "market_data"
            ):
                continue

            key = literal_subscript_key(
                base
            )

            if key is not None:
                add(
                    key,
                    node.lineno,
                )

    return writes


def extract_read_lines(
    source_text: str,
    function_name: str,
) -> dict[str, list[int]]:

    tree = ast.parse(source_text)

    fn = get_function_node(
        tree,
        function_name,
    )

    reads: dict[str, list[int]] = {}

    def add(
        key: str,
        line: int,
    ):
        reads.setdefault(
            key,
            [],
        ).append(line)

    for node in ast.walk(fn):

        if isinstance(node, ast.Call):

            func = node.func

            if (
                isinstance(func, ast.Attribute)
                and func.attr == "get"
                and isinstance(func.value, ast.Name)
                and func.value.id == "market_data"
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
                    node.args[0].value,
                    node.lineno,
                )

        elif isinstance(node, ast.Subscript):

            if not (
                isinstance(
                    node.value,
                    ast.Name,
                )
                and node.value.id
                == "market_data"
            ):
                continue

            key = literal_subscript_key(
                node
            )

            if key is not None:

                add(
                    key,
                    node.lineno,
                )

    return reads


# ============================================================
# Production producer discovery
# ============================================================

def get_top_level_functions(
    source_text: str,
) -> dict[str, ast.FunctionDef]:

    tree = ast.parse(source_text)

    out = {}

    for node in tree.body:

        if isinstance(
            node,
            ast.FunctionDef,
        ):
            out[node.name] = node

    return out


def extract_function_writes_from_node(
    node: ast.FunctionDef,
) -> set[str]:

    writes: set[str] = set()

    for child in ast.walk(node):

        if not isinstance(
            child,
            ast.Assign,
        ):
            continue

        for target in child.targets:

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

            key = literal_subscript_key(
                target
            )

            if key is not None:
                writes.add(key)

    return writes


def discover_production_producers(
    source_text: str,
) -> dict[str, list[str]]:
    """
    Discover literal market_data writes across Production
    top-level functions.

    This is broader than v1 attach_* only discovery.
    """

    functions = get_top_level_functions(
        source_text
    )

    producers: dict[
        str,
        list[str]
    ] = {}

    for fn_name, node in (
        functions.items()
    ):

        writes = (
            extract_function_writes_from_node(
                node
            )
        )

        for key in writes:

            producers.setdefault(
                key,
                [],
            ).append(
                fn_name
            )

    return producers


# ============================================================
# Runtime helpers
# ============================================================

def is_missing(
    value: Any,
) -> bool:

    if value is None:
        return True

    try:

        result = pd.isna(value)

        if isinstance(
            result,
            bool,
        ):
            return result

    except Exception:
        pass

    return False


def value_shape(
    value: Any,
) -> str:

    if is_missing(value):
        return "MISSING"

    if isinstance(value, dict):

        if not value:
            return "EMPTY_DICT"

        return f"DICT[{len(value)}]"

    if isinstance(value, list):

        if not value:
            return "EMPTY_LIST"

        return f"LIST[{len(value)}]"

    if isinstance(value, tuple):

        if not value:
            return "EMPTY_TUPLE"

        return f"TUPLE[{len(value)}]"

    if isinstance(value, str):

        if not value.strip():
            return "EMPTY_STRING"

        return "STRING"

    return type(value).__name__.upper()


def snapshot(
    market_data: dict[str, Any],
    keys: set[str],
) -> dict[str, dict[str, Any]]:

    out = {}

    for key in sorted(keys):

        exists = (
            key in market_data
        )

        value = market_data.get(
            key
        )

        out[key] = {
            "exists":
                exists,

            "shape":
                value_shape(
                    value
                ),

            "value":
                value,
        }

    return out


def choose_sample_indices(
    panel: pd.DataFrame,
    count: int,
) -> list[int]:

    eligible = panel.index[
        panel["execution_date"].notna()
        & pd.to_numeric(
            panel["SPY"],
            errors="coerce",
        ).notna()
    ].tolist()

    if not eligible:

        raise RuntimeError(
            "No eligible historical rows."
        )

    if len(eligible) <= count:
        return eligible

    positions = [
        round(
            i
            * (len(eligible) - 1)
            / (count - 1)
        )
        for i in range(count)
    ]

    return [
        eligible[p]
        for p in positions
    ]


def runtime_status(
    observations:
        list[dict[str, Any]],
) -> tuple[str, str]:

    total = len(
        observations
    )

    if total == 0:

        return (
            "MISSING",
            "No runtime observations.",
        )

    exists_count = sum(
        1
        for obs in observations
        if obs["exists"]
    )

    shapes = sorted(
        set(
            obs["shape"]
            for obs in observations
        )
    )

    if exists_count == 0:

        return (
            "MISSING",
            (
                f"0/{total} sampled "
                f"boundaries supplied key."
            ),
        )

    if exists_count < total:

        return (
            "INTERMITTENT",
            (
                f"{exists_count}/{total} "
                f"sampled boundaries supplied key; "
                f"shapes={shapes}"
            ),
        )

    return (
        "PRESENT",
        (
            f"{exists_count}/{total} "
            f"sampled boundaries supplied key; "
            f"shapes={shapes}"
        ),
    )


# ============================================================
# Contract classification
# ============================================================

def classify_contract(
    key: str,
    read_lines: list[int],
    write_lines: list[int],
    production_producers:
        list[str],
    runtime_state: str,
) -> tuple[str, str, str]:
    """
    Returns:
        contract_class
        final_status
        rationale
    """

    # --------------------------------------------------------
    # Intentional historical unavailable
    # --------------------------------------------------------

    if (
        key
        in INTENTIONAL_HISTORICAL_UNAVAILABLE
    ):

        return (
            "INTENTIONAL_UNAVAILABLE",
            "INTENTIONAL_UNAVAILABLE",
            (
                "Explicit historical design "
                "difference."
            ),
        )

    # --------------------------------------------------------
    # Historical equivalent
    # --------------------------------------------------------

    if key in HISTORICAL_EQUIVALENTS:

        if runtime_state == "PRESENT":

            return (
                "PERSISTENT_STATE",
                "HISTORICAL_EQUIVALENT",
                HISTORICAL_EQUIVALENTS[
                    key
                ],
            )

        return (
            "PERSISTENT_STATE",
            "REVIEW_REQUIRED",
            (
                "Historical equivalent is "
                "expected but runtime boundary "
                "did not consistently supply it."
            ),
        )

    # --------------------------------------------------------
    # Persistent state
    # --------------------------------------------------------

    if key in PERSISTENT_STATE_KEYS:

        if runtime_state == "PRESENT":

            return (
                "PERSISTENT_STATE",
                "PASS_RUNTIME_PRESENT",
                (
                    "Persistent state present "
                    "at runtime; source semantics "
                    "still require parity evidence."
                ),
            )

        return (
            "PERSISTENT_STATE",
            "REVIEW_REQUIRED",
            (
                "Persistent state is not "
                "consistently supplied at "
                "consumer boundary."
            ),
        )

    # --------------------------------------------------------
    # Consumer-internal state
    #
    # If the same consumer writes this key, PRE-boundary
    # absence is NOT sufficient evidence of a parity gap.
    # --------------------------------------------------------

    if write_lines:

        first_write = min(
            write_lines
        )

        first_read = (
            min(read_lines)
            if read_lines
            else None
        )

        if (
            first_read is None
            or first_write <= first_read
        ):

            return (
                "INTERNAL_STATE",
                "PASS_INTERNAL_STATE",
                (
                    f"Consumer writes key at "
                    f"line {first_write} before/"
                    f"at first literal read "
                    f"{first_read}."
                ),
            )

        # Read-before-write is different:
        # previous/external value may matter.
        if runtime_state == "PRESENT":

            return (
                "READ_BEFORE_WRITE",
                "PASS_RUNTIME_PRESENT",
                (
                    f"First read line "
                    f"{first_read}; first write "
                    f"line {first_write}; "
                    f"boundary supplied value."
                ),
            )

        if production_producers:

            return (
                "UPSTREAM_INPUT",
                "CANDIDATE_PARITY_GAP",
                (
                    f"Consumer reads at line "
                    f"{first_read} before writing "
                    f"at line {first_write}; "
                    f"Production producer(s): "
                    f"{production_producers}; "
                    f"historical boundary missing."
                ),
            )

        return (
            "READ_BEFORE_WRITE",
            "REVIEW_REQUIRED",
            (
                f"Consumer reads at line "
                f"{first_read} before first write "
                f"at line {first_write}, but "
                f"no Production producer was "
                f"statically resolved."
            ),
        )

    # --------------------------------------------------------
    # Pure upstream read
    # --------------------------------------------------------

    if runtime_state == "PRESENT":

        return (
            "UPSTREAM_INPUT",
            "PASS_RUNTIME_PRESENT",
            (
                "Consumer does not write this "
                "contract and historical boundary "
                "supplied it."
            ),
        )

    if runtime_state == "INTERMITTENT":

        return (
            "UPSTREAM_INPUT",
            "REVIEW_REQUIRED",
            (
                "Upstream contract is only "
                "intermittently available."
            ),
        )

    if production_producers:

        return (
            "UPSTREAM_INPUT",
            "CANDIDATE_PARITY_GAP",
            (
                "Production producer detected "
                "but canonical historical "
                "consumer boundary supplied "
                "no contract."
            ),
        )

    return (
        "UNRESOLVED",
        "REVIEW_REQUIRED",
        (
            "Consumer reads this key, "
            "historical boundary does not "
            "supply it, and static Production "
            "producer was not resolved."
        ),
    )


# ============================================================
# Main
# ============================================================

def main() -> None:

    print()
    print("=" * 78)
    print(
        "FULL EXECUTION CONTRACT AUDIT v2"
    )
    print(
        "F13 / F15 / F18"
    )
    print("=" * 78)

    filter_text = FILTER_FILE.read_text(
        encoding="utf-8"
    )

    production_text = (
        PRODUCTION_FILE.read_text(
            encoding="utf-8"
        )
    )

    # --------------------------------------------------------
    # Static contract discovery
    # --------------------------------------------------------

    reads_by_filter = {}
    read_lines_by_filter = {}
    writes_by_filter = {}

    for stage, fn_name in (
        FILTERS.items()
    ):

        reads_by_filter[stage] = (
            extract_reads(
                filter_text,
                fn_name,
            )
        )

        read_lines_by_filter[stage] = (
            extract_read_lines(
                filter_text,
                fn_name,
            )
        )

        writes_by_filter[stage] = (
            extract_writes_with_lines(
                filter_text,
                fn_name,
            )
        )

        print()
        print(
            f"[{stage}] {fn_name}"
        )

        print(
            "reads:",
            len(
                reads_by_filter[
                    stage
                ]
            ),
        )

        print(
            "writes:",
            len(
                writes_by_filter[
                    stage
                ]
            ),
        )

    production_producers = (
        discover_production_producers(
            production_text
        )
    )

    print()
    print(
        "[PRODUCTION CONTRACT KEYS WITH "
        "LITERAL PRODUCERS]",
        len(production_producers),
    )

    # --------------------------------------------------------
    # Historical runtime
    # --------------------------------------------------------

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    sample_indices = (
        choose_sample_indices(
            panel,
            TARGET_SAMPLE_COUNT,
        )
    )

    print()
    print(
        "[RUNTIME SAMPLE ROWS]",
        len(sample_indices),
    )

    print(
        "[RANGE]",
        panel.loc[
            sample_indices[0],
            "signal_date",
        ],
        "->",
        panel.loc[
            sample_indices[-1],
            "signal_date",
        ],
    )

    runtime = {
        "PRE_F13": {},
        "PRE_F15": {},
        "PRE_F18": {},
    }

    for idx in sample_indices:

        previous_exposure = 50.0

        flow_memory = {
            "flow_state": "N/A",
            "flow_score": 0,
            "persistence_days": 0,
        }

        market_data = (
            build_market_data(
                panel=panel,
                row_index=idx,
                previous_exposure=
                    previous_exposure,
            )
        )

        with contextlib.redirect_stdout(
            io.StringIO()
        ):

            prepare_filter13_execution_state(
                market_data=market_data,
                panel=panel,
                row_index=idx,
                previous_flow_memory=
                    flow_memory,
            )

        # PRE F13
        pre_f13 = snapshot(
            market_data,
            reads_by_filter["F13"],
        )

        for key, obs in (
            pre_f13.items()
        ):

            runtime[
                "PRE_F13"
            ].setdefault(
                key,
                [],
            ).append(obs)

        disable_live_side_effects(
            previous_exposure
        )

        neutralize_all_side_effects(
            previous_exposure
        )

        with contextlib.redirect_stdout(
            io.StringIO()
        ):

            sf.narrative_engine_filter(
                market_data
            )

        # PRE F15
        pre_f15 = snapshot(
            market_data,
            reads_by_filter["F15"],
        )

        for key, obs in (
            pre_f15.items()
        ):

            runtime[
                "PRE_F15"
            ].setdefault(
                key,
                [],
            ).append(obs)

        with contextlib.redirect_stdout(
            io.StringIO()
        ):

            sf.volatility_controlled_exposure_filter(
                market_data
            )

        # PRE F18
        pre_f18 = snapshot(
            market_data,
            reads_by_filter["F18"],
        )

        for key, obs in (
            pre_f18.items()
        ):

            runtime[
                "PRE_F18"
            ].setdefault(
                key,
                [],
            ).append(obs)

    # --------------------------------------------------------
    # Matrix
    # --------------------------------------------------------

    rows = []

    for stage in (
        "F13",
        "F15",
        "F18",
    ):

        boundary = BOUNDARIES[
            stage
        ]

        for key in sorted(
            reads_by_filter[
                stage
            ]
        ):

            observations = (
                runtime[
                    boundary
                ].get(
                    key,
                    [],
                )
            )

            rt_status, rt_evidence = (
                runtime_status(
                    observations
                )
            )

            read_lines = (
                read_lines_by_filter[
                    stage
                ].get(
                    key,
                    [],
                )
            )

            write_lines = (
                writes_by_filter[
                    stage
                ].get(
                    key,
                    [],
                )
            )

            prod = (
                production_producers.get(
                    key,
                    [],
                )
            )

            (
                contract_class,
                final_status,
                rationale,
            ) = classify_contract(
                key=key,
                read_lines=read_lines,
                write_lines=write_lines,
                production_producers=prod,
                runtime_state=rt_status,
            )

            rows.append({
                "consumer":
                    stage,

                "boundary":
                    boundary,

                "contract":
                    key,

                "contract_class":
                    contract_class,

                "runtime_status":
                    rt_status,

                "final_status":
                    final_status,

                "read_lines":
                    ",".join(
                        str(x)
                        for x in sorted(
                            read_lines
                        )
                    ),

                "consumer_write_lines":
                    ",".join(
                        str(x)
                        for x in sorted(
                            write_lines
                        )
                    ),

                "production_producers":
                    ";".join(prod),

                "runtime_evidence":
                    rt_evidence,

                "classification_rationale":
                    rationale,
            })

    matrix = pd.DataFrame(
        rows
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    summary = (
        matrix
        .groupby(
            [
                "consumer",
                "final_status",
            ],
            dropna=False,
        )
        .size()
        .reset_index(
            name="count"
        )
        .sort_values(
            [
                "consumer",
                "final_status",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    matrix.to_csv(
        OUTPUT_MATRIX,
        index=False,
    )

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
    )

    # --------------------------------------------------------
    # Human-readable report
    # --------------------------------------------------------

    lines = []

    lines.append(
        "FULL EXECUTION CONTRACT AUDIT v2"
    )

    lines.append(
        "=" * 78
    )

    lines.append(
        f"Runtime samples: "
        f"{len(sample_indices)}"
    )

    lines.append("")

    for stage in (
        "F13",
        "F15",
        "F18",
    ):

        subset = matrix[
            matrix["consumer"].eq(
                stage
            )
        ]

        lines.append(
            f"[{stage}]"
        )

        counts = (
            subset[
                "final_status"
            ]
            .value_counts()
            .to_dict()
        )

        for status, count in (
            sorted(
                counts.items()
            )
        ):

            lines.append(
                f"  {status}: {count}"
            )

        lines.append("")

    candidate_gaps = matrix[
        matrix[
            "final_status"
        ].eq(
            "CANDIDATE_PARITY_GAP"
        )
    ]

    review = matrix[
        matrix[
            "final_status"
        ].eq(
            "REVIEW_REQUIRED"
        )
    ]

    lines.append(
        "[CANDIDATE PARITY GAPS]"
    )

    if candidate_gaps.empty:

        lines.append(
            "  NONE"
        )

    else:

        for _, row in (
            candidate_gaps.iterrows()
        ):

            lines.append(
                f"  {row['consumer']} | "
                f"{row['contract']} | "
                f"{row['contract_class']} | "
                f"Production="
                f"{row['production_producers']}"
            )

    lines.append("")
    lines.append(
        "[REVIEW REQUIRED]"
    )

    if review.empty:

        lines.append(
            "  NONE"
        )

    else:

        for _, row in (
            review.iterrows()
        ):

            lines.append(
                f"  {row['consumer']} | "
                f"{row['contract']} | "
                f"{row['contract_class']}"
            )

    lines.append("")
    lines.append(
        "IMPORTANT:"
    )

    lines.append(
        "Candidate gap != final failure."
    )

    lines.append(
        "No repair should be made until "
        "all candidate/review contracts "
        "are classified and frozen."
    )

    lines.append(
        "No Production or Backtest "
        "decision logic was modified."
    )

    OUTPUT_TXT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Console
    # --------------------------------------------------------

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print()

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print("=" * 78)
    print(
        "CANDIDATE PARITY GAPS"
    )
    print("=" * 78)

    if candidate_gaps.empty:

        print("NONE")

    else:

        print(
            candidate_gaps[
                [
                    "consumer",
                    "contract",
                    "contract_class",
                    "runtime_status",
                    "production_producers",
                    "read_lines",
                    "consumer_write_lines",
                ]
            ].to_string(
                index=False
            )
        )

    print()
    print("=" * 78)
    print(
        "REVIEW REQUIRED"
    )
    print("=" * 78)

    if review.empty:

        print("NONE")

    else:

        print(
            review[
                [
                    "consumer",
                    "contract",
                    "contract_class",
                    "runtime_status",
                    "production_producers",
                    "read_lines",
                    "consumer_write_lines",
                ]
            ].to_string(
                index=False
            )
        )

    print()
    print("[OUTPUT]")
    print(OUTPUT_MATRIX)
    print(OUTPUT_SUMMARY)
    print(OUTPUT_TXT)

    print()
    print(
        "AUDIT v2 COMPLETE — "
        "NO DECISION CODE MODIFIED"
    )


if __name__ == "__main__":
    main()
