from __future__ import annotations

import ast
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


FILTER_FILE = ROOT / "filters" / "strategist_filters.py"

RESULT_DIR = ROOT / "data" / "backtest" / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

OUT = RESULT_DIR / "f13_f15_f18_value_parity_manifest.csv"
OUT_TXT = RESULT_DIR / "f13_f15_f18_value_parity_manifest.txt"


TARGETS = {
    "F13": "narrative_engine_filter",
    "F15": "volatility_controlled_exposure_filter",
    "F18": "sector_allocation_filter",
}


def literal_key(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def get_function(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise RuntimeError(f"Function not found: {name}")


def collect_contracts(fn):
    reads = {}
    writes = {}

    def add(target, key, lineno):
        target.setdefault(key, set()).add(lineno)

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
            ):
                key = literal_key(node.args[0])
                if key:
                    add(reads, key, node.lineno)

        # market_data["KEY"]
        if isinstance(node, ast.Subscript):
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == "market_data"
            ):
                key = literal_key(node.slice)

                if key:
                    if isinstance(node.ctx, ast.Load):
                        add(reads, key, node.lineno)
                    elif isinstance(node.ctx, ast.Store):
                        add(writes, key, node.lineno)

        # assignments
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "market_data"
                ):
                    key = literal_key(target.slice)
                    if key:
                        add(writes, key, node.lineno)

    return reads, writes


def classify(key, reads, writes):

    if key in reads and key in writes:
        return "READ_WRITE_STATE"

    if key in reads:
        return "INPUT_OR_PRIOR_STATE"

    return "OUTPUT_OR_INTERNAL_STATE"


def main():

    source = FILTER_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    rows = []

    for stage, function_name in TARGETS.items():

        fn = get_function(tree, function_name)

        reads, writes = collect_contracts(fn)

        keys = sorted(set(reads) | set(writes))

        for key in keys:

            rows.append({
                "stage": stage,
                "function": function_name,
                "contract": key,
                "contract_role": classify(
                    key,
                    reads,
                    writes,
                ),
                "read_lines": ",".join(
                    str(x)
                    for x in sorted(reads.get(key, []))
                ),
                "write_lines": ",".join(
                    str(x)
                    for x in sorted(writes.get(key, []))
                ),
            })

    df = pd.DataFrame(rows)

    # Same key may legitimately appear in multiple stages.
    df = (
        df
        .sort_values(["stage", "contract"])
        .reset_index(drop=True)
    )

    df.to_csv(OUT, index=False)

    lines = []

    lines.append("F13 / F15 / F18 VALUE PARITY MANIFEST")
    lines.append("=" * 78)
    lines.append("")

    for stage in TARGETS:

        x = df[df["stage"] == stage]

        lines.append(f"{stage}: {len(x)} contracts")

        for _, row in x.iterrows():
            lines.append(
                f"  {row['contract']:<35} "
                f"{row['contract_role']}"
            )

        lines.append("")

    unique_contracts = df["contract"].nunique()

    lines.append("=" * 78)
    lines.append(f"TOTAL STAGE-CONTRACT PAIRS: {len(df)}")
    lines.append(f"TOTAL UNIQUE CONTRACTS: {unique_contracts}")

    OUT_TXT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print("\n".join(lines))

    print()
    print("[OUTPUT]")
    print(OUT)
    print(OUT_TXT)


if __name__ == "__main__":
    main()
