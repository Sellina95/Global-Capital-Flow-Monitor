from __future__ import annotations

from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"

REF_FILE = RESULTS / "frozen_82_contract_code_references.csv"
OUT_DETAIL = RESULTS / "fred_vintage_82_causal_lineage.csv"
OUT_SUMMARY = RESULTS / "fred_vintage_82_causal_lineage_summary.txt"


# ============================================================
# Confirmed contaminated upstream sources from vintage audit
# ============================================================

MATERIAL = {
    "NFCI",
    "WTREGEN",
    "WALCL",
}

ISOLATED = {
    "DGS2",
    "T10Y2Y",
    "T10YIE",
    "DGS10",
}


# ============================================================
# Explicit causal lineage
#
# IMPORTANT:
# This is NOT grep proximity.
# Only confirmed generator/data dependencies belong here.
# ============================================================

DIRECT_SOURCE_CONTRACTS = {
    # FRED extras
    "FCI": {"NFCI"},
    "REAL_RATE": set(),       # DFII10 passed vintage audit
    "DFII10": set(),
    "DGS2": {"DGS2"},
    "T10Y2Y": {"T10Y2Y"},
    "T10YIE": {"T10YIE"},

    # liquidity
    "TGA": {"WTREGEN"},
    "WALCL": {"WALCL"},

    # core market rate
    "US10Y": {"DGS10"},
}


DERIVED_SOURCE_CONTRACTS = {
    # NET_LIQ is constructed from liquidity parents.
    # RRP is unresolved for ALFRED, but the known contaminated
    # parents alone are sufficient to mark this derived path.
    "NET_LIQ": {"WTREGEN", "WALCL"},
    "NET_LIQ_DIR": {"WTREGEN", "WALCL"},
    "NET_LIQ_LEVEL_BUCKET": {"WTREGEN", "WALCL"},
    "LIQUIDITY_MOMENTUM": {"WTREGEN", "WALCL"},
}


# ============================================================
# Generator-produced contracts
#
# These are downstream state variables. They are not declared
# contaminated merely because the same source name appears
# somewhere in the file.
#
# They inherit contamination only when their generator consumes
# a contaminated direct/derived input.
# ============================================================

GENERATOR_DEPENDENCIES = {
    # market_regime_filter consumes macro/cross-asset information.
    # Confirmed contaminated macro parents relevant to this audit:
    "MARKET_REGIME": {
        "FCI",
        "NET_LIQ",
        "US10Y",
        "DGS2",
        "T10Y2Y",
        "T10YIE",
    },

    # narrative_engine_filter runs after market_regime_filter.
    "MACRO_NARRATIVE": {
        "MARKET_REGIME",
    },

    "FINAL_STATE": {
        "MARKET_REGIME",
        "MACRO_NARRATIVE",
    },
}


# ============================================================
# Propagation helper
# ============================================================

def resolve_sources(contract: str, seen=None):
    if seen is None:
        seen = set()

    if contract in seen:
        return set()

    seen = set(seen)
    seen.add(contract)

    if contract in DIRECT_SOURCE_CONTRACTS:
        return set(DIRECT_SOURCE_CONTRACTS[contract])

    if contract in DERIVED_SOURCE_CONTRACTS:
        return set(DERIVED_SOURCE_CONTRACTS[contract])

    if contract in GENERATOR_DEPENDENCIES:
        out = set()

        for parent in GENERATOR_DEPENDENCIES[contract]:
            out |= resolve_sources(parent, seen)

        return out

    return set()


def classify(contract: str):
    sources = resolve_sources(contract)

    material = sorted(sources & MATERIAL)
    isolated = sorted(sources & ISOLATED)

    if contract in DIRECT_SOURCE_CONTRACTS and (material or isolated):
        status = "DIRECT_CONTAMINATED"

    elif contract in DERIVED_SOURCE_CONTRACTS and (material or isolated):
        status = "DERIVED_CONTAMINATED"

    elif contract in GENERATOR_DEPENDENCIES and (material or isolated):
        status = "DERIVED_CONTAMINATED"

    elif sources:
        status = "CLEAN"

    else:
        # No confirmed causal dependency has been established.
        # Do NOT infer contamination from grep proximity.
        status = "UNRESOLVED"

    return {
        "causal_sources": "|".join(sorted(sources)),
        "material_sources": "|".join(material),
        "isolated_sources": "|".join(isolated),
        "causal_status": status,
    }


def main():

    print("=" * 88)
    print("GATE #3 — FRED VINTAGE 82-CONTRACT CAUSAL LINEAGE")
    print("=" * 88)
    print()
    print("AUDIT ONLY — no Production, Backtest or PIT data will be modified.")
    print()

    if not REF_FILE.exists():
        raise FileNotFoundError(REF_FILE)

    ref = pd.read_csv(REF_FILE)

    required = {"stage", "contract"}

    missing = required - set(ref.columns)

    if missing:
        raise RuntimeError(
            f"Missing required columns in {REF_FILE.name}: "
            f"{sorted(missing)}"
        )

    # --------------------------------------------------------
    # Reference artifact contains MANY code-reference rows
    # per contract.
    #
    # Gate universe is 82 UNIQUE (stage, contract) pairs.
    # Never treat reference rows as separate contracts.
    # --------------------------------------------------------

    universe = (
        ref[
            ["stage", "contract"]
        ]
        .dropna()
        .drop_duplicates()
        .sort_values(
            ["stage", "contract"]
        )
        .reset_index(drop=True)
    )

    if len(universe) != 82:
        raise RuntimeError(
            "Frozen UNIQUE contract universe changed: "
            f"expected 82, got {len(universe)}"
        )

    rows = []

    for _, r in universe.iterrows():

        stage = str(r["stage"])
        contract = str(r["contract"])

        result = classify(contract)

        rows.append({
            "stage": stage,
            "contract": contract,
            **result,
        })

    out = pd.DataFrame(rows)

    # frozen universe integrity
    if len(out) != 82:
        raise RuntimeError(
            f"Expected 82 classified contracts, got {len(out)}"
        )

    if out[
        ["stage", "contract"]
    ].duplicated().any():
        raise RuntimeError(
            "Duplicate frozen contracts detected "
            "after classification."
        )

    out.to_csv(
        OUT_DETAIL,
        index=False,
    )

    counts = (
        out["causal_status"]
        .value_counts()
        .rename_axis("causal_status")
        .to_frame("contracts")
    )

    by_stage = (
        out.groupby(
            ["stage", "causal_status"]
        )
        .size()
        .rename("contracts")
    )

    contaminated = out[
        out["causal_status"].isin(
            [
                "DIRECT_CONTAMINATED",
                "DERIVED_CONTAMINATED",
            ]
        )
    ].copy()

    unresolved = out[
        out["causal_status"] == "UNRESOLVED"
    ].copy()

    print("=" * 88)
    print("CAUSAL CLASSIFICATION")
    print("=" * 88)
    print(counts.to_string())

    print()
    print("BY STAGE")
    print(by_stage.to_string())

    print()
    print("=" * 88)
    print("CONFIRMED CONTAMINATED CONTRACTS")
    print("=" * 88)

    if contaminated.empty:
        print("NONE")
    else:
        print(
            contaminated[
                [
                    "stage",
                    "contract",
                    "causal_sources",
                    "material_sources",
                    "isolated_sources",
                    "causal_status",
                ]
            ].to_string(index=False)
        )

    print()
    print("=" * 88)
    print("UNRESOLVED CONTRACTS")
    print("=" * 88)

    if unresolved.empty:
        print("NONE")
    else:
        print(
            unresolved[
                [
                    "stage",
                    "contract",
                ]
            ].to_string(index=False)
        )

    lines = [
        "FRED VINTAGE 82-CONTRACT CAUSAL LINEAGE",
        "=" * 88,
        "",
        "Frozen universe: 82 contracts",
        "",
        "CLASSIFICATION",
        "-" * 88,
        counts.to_string(),
        "",
        "BY STAGE",
        "-" * 88,
        by_stage.to_string(),
        "",
        "CONFIRMED CONTAMINATED CONTRACTS",
        "-" * 88,
        (
            contaminated[
                [
                    "stage",
                    "contract",
                    "causal_sources",
                    "material_sources",
                    "isolated_sources",
                    "causal_status",
                ]
            ].to_string(index=False)
            if not contaminated.empty
            else "NONE"
        ),
        "",
        "UNRESOLVED CONTRACTS",
        "-" * 88,
        (
            unresolved[
                ["stage", "contract"]
            ].to_string(index=False)
            if not unresolved.empty
            else "NONE"
        ),
        "",
        "Interpretation:",
        "DIRECT_CONTAMINATED = contract directly consumes contaminated FRED source.",
        "DERIVED_CONTAMINATED = contract inherits contamination through a confirmed parent.",
        "CLEAN = causal source lineage established and no contaminated source found.",
        "UNRESOLVED = causal dependency not yet proven; grep proximity is insufficient.",
        "",
        "IMPORTANT:",
        "This audit intentionally prefers UNRESOLVED over false contamination claims.",
        "",
        "AUDIT ONLY — no Production or Backtest logic modified.",
    ]

    OUT_SUMMARY.write_text(
        "\n".join(lines) + "\n"
    )

    print()
    print("[OUTPUT]")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)


if __name__ == "__main__":
    main()
