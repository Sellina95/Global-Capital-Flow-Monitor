from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULTS = (
    ROOT
    / "data"
    / "backtest"
    / "results"
)

REF_FILE = (
    RESULTS
    / "frozen_82_contract_code_references.csv"
)

OUT_DETAIL = (
    RESULTS
    / "fred_vintage_82_blast_radius_candidates.csv"
)

OUT_SUMMARY = (
    RESULTS
    / "fred_vintage_82_blast_radius_summary.csv"
)

OUT_TXT = (
    RESULTS
    / "fred_vintage_82_blast_radius_summary.txt"
)


# ============================================================
# Frozen Gate #3 contaminated upstream sources
# ============================================================

CONTAMINATED = {
    "NFCI": {
        "severity": "MATERIAL",
        "aliases": [
            "NFCI",
            "FCI",
            "fred_extras__FCI",
            "fred_sector__FCI",
        ],
    },

    "WTREGEN": {
        "severity": "MATERIAL",
        "aliases": [
            "WTREGEN",
            "TGA",
            "NET_LIQ",
            "NET_LIQ_LEVEL",
            "NET_LIQ_LEVEL_BUCKET",
        ],
    },

    "WALCL": {
        "severity": "MATERIAL",
        "aliases": [
            "WALCL",
            "NET_LIQ",
            "NET_LIQ_LEVEL",
            "NET_LIQ_LEVEL_BUCKET",
        ],
    },

    "DGS2": {
        "severity": "ISOLATED",
        "aliases": [
            "DGS2",
            "US2Y",
        ],
    },

    "T10Y2Y": {
        "severity": "ISOLATED",
        "aliases": [
            "T10Y2Y",
        ],
    },

    "T10YIE": {
        "severity": "ISOLATED",
        "aliases": [
            "T10YIE",
        ],
    },

    "DGS10": {
        "severity": "ISOLATED",
        "aliases": [
            "DGS10",
            "US10Y",
        ],
    },
}


# ============================================================
# Helpers
# ============================================================

def read_context(
    relative_path: str,
    lineno: int,
    radius: int = 20,
) -> str:

    if not relative_path:
        return ""

    path = ROOT / relative_path

    if not path.exists():
        return ""

    try:
        lines = path.read_text(
            errors="ignore"
        ).splitlines()
    except Exception:
        return ""

    lineno = int(lineno)

    start = max(
        0,
        lineno - 1 - radius,
    )

    end = min(
        len(lines),
        lineno + radius,
    )

    return "\n".join(
        lines[start:end]
    )


def matched_aliases(
    text: str,
    aliases: list[str],
) -> list[str]:

    text_upper = text.upper()

    return [
        alias
        for alias in aliases
        if alias.upper() in text_upper
    ]


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 88)
    print(
        "GATE #3 — FRED VINTAGE 82-CONTRACT "
        "BLAST-RADIUS CANDIDATE AUDIT"
    )
    print("=" * 88)

    print()
    print(
        "AUDIT ONLY — no Production, Backtest "
        "or PIT data will be modified."
    )

    if not REF_FILE.exists():
        raise FileNotFoundError(
            f"Missing reference artifact: {REF_FILE}"
        )

    refs = pd.read_csv(REF_FILE)

    required = {
        "stage",
        "contract",
        "file",
        "line",
        "code",
        "reference_status",
    }

    missing = required - set(refs.columns)

    if missing:
        raise RuntimeError(
            f"Reference artifact missing columns: {missing}"
        )

    rows = []

    # --------------------------------------------------------
    # Examine every real code reference for all 82 contracts.
    # --------------------------------------------------------

    for _, r in refs.iterrows():

        if r["reference_status"] != "FOUND":
            continue

        path = str(r["file"])

        try:
            lineno = int(r["line"])
        except Exception:
            continue

        context = read_context(
            path,
            lineno,
            radius=25,
        )

        search_blob = (
            str(r["code"])
            + "\n"
            + context
        )

        for source, meta in CONTAMINATED.items():

            aliases = matched_aliases(
                search_blob,
                meta["aliases"],
            )

            if not aliases:
                continue

            rows.append({
                "stage": r["stage"],
                "contract": r["contract"],
                "upstream_source": source,
                "source_severity": meta["severity"],
                "matched_aliases": "|".join(
                    sorted(set(aliases))
                ),
                "file": path,
                "line": lineno,
                "contract_reference": r["code"],
                "candidate_status":
                    "REQUIRES_LINEAGE_REVIEW",
            })

    detail = pd.DataFrame(rows)

    if detail.empty:

        detail = pd.DataFrame(
            columns=[
                "stage",
                "contract",
                "upstream_source",
                "source_severity",
                "matched_aliases",
                "file",
                "line",
                "contract_reference",
                "candidate_status",
            ]
        )

    detail = detail.drop_duplicates()

    detail.to_csv(
        OUT_DETAIL,
        index=False,
    )

    # --------------------------------------------------------
    # Contract-level candidate summary
    # --------------------------------------------------------

    universe = (
        refs[
            ["stage", "contract"]
        ]
        .drop_duplicates()
        .sort_values(
            ["stage", "contract"]
        )
    )

    assert len(universe) == 82, (
        f"Expected 82 frozen contracts, "
        f"got {len(universe)}"
    )

    if detail.empty:

        summary = universe.copy()

        summary["candidate_sources"] = ""
        summary["material_source_candidate"] = False
        summary["isolated_source_candidate"] = False
        summary["candidate_reference_count"] = 0
        summary["blast_radius_status"] = (
            "NO_CONTAMINATED_SOURCE_REFERENCE_FOUND"
        )

    else:

        grouped = (
            detail
            .groupby(
                ["stage", "contract"]
            )
            .agg(
                candidate_sources=(
                    "upstream_source",
                    lambda x:
                    "|".join(
                        sorted(set(x))
                    ),
                ),
                candidate_reference_count=(
                    "upstream_source",
                    "size",
                ),
                material_source_candidate=(
                    "source_severity",
                    lambda x:
                    bool(
                        (x == "MATERIAL").any()
                    ),
                ),
                isolated_source_candidate=(
                    "source_severity",
                    lambda x:
                    bool(
                        (x == "ISOLATED").any()
                    ),
                ),
            )
            .reset_index()
        )

        summary = universe.merge(
            grouped,
            on=[
                "stage",
                "contract",
            ],
            how="left",
        )

        summary[
            "candidate_sources"
        ] = (
            summary[
                "candidate_sources"
            ]
            .fillna("")
        )

        summary[
            "candidate_reference_count"
        ] = (
            summary[
                "candidate_reference_count"
            ]
            .fillna(0)
            .astype(int)
        )

        for col in [
            "material_source_candidate",
            "isolated_source_candidate",
        ]:
            summary[col] = (
                summary[col]
                .fillna(False)
                .astype(bool)
            )

        def classify(r):

            if r[
                "material_source_candidate"
            ]:
                return (
                    "MATERIAL_BLAST_RADIUS_CANDIDATE"
                )

            if r[
                "isolated_source_candidate"
            ]:
                return (
                    "ISOLATED_BLAST_RADIUS_CANDIDATE"
                )

            return (
                "NO_CONTAMINATED_SOURCE_REFERENCE_FOUND"
            )

        summary[
            "blast_radius_status"
        ] = summary.apply(
            classify,
            axis=1,
        )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
    )

    # --------------------------------------------------------
    # Console / text evidence
    # --------------------------------------------------------

    counts = (
        summary[
            "blast_radius_status"
        ]
        .value_counts()
    )

    by_stage = (
        summary.groupby(
            [
                "stage",
                "blast_radius_status",
            ]
        )
        .size()
    )

    candidate = summary[
        summary[
            "blast_radius_status"
        ]
        != "NO_CONTAMINATED_SOURCE_REFERENCE_FOUND"
    ]

    text = []

    text.append(
        "FRED VINTAGE 82-CONTRACT "
        "BLAST-RADIUS CANDIDATE AUDIT"
    )

    text.append("=" * 80)

    text.append(
        "Frozen universe: "
        f"{len(summary)} contracts"
    )

    text.append("")

    text.append(
        "IMPORTANT: this is candidate discovery, "
        "not final causal lineage classification."
    )

    text.append(
        "A nearby code reference is not sufficient "
        "to declare contamination."
    )

    text.append("")

    text.append("STATUS COUNTS")
    text.append("-" * 80)

    text.append(
        counts.to_string()
    )

    text.append("")

    text.append("BY STAGE")
    text.append("-" * 80)

    text.append(
        by_stage.to_string()
    )

    text.append("")

    text.append("CANDIDATE CONTRACTS")
    text.append("-" * 80)

    if candidate.empty:
        text.append("NONE")
    else:
        text.append(
            candidate[
                [
                    "stage",
                    "contract",
                    "candidate_sources",
                    "blast_radius_status",
                ]
            ].to_string(
                index=False
            )
        )

    text.append("")
    text.append(
        "NEXT GATE:"
    )

    text.append(
        "Review candidate code paths and classify "
        "DIRECT_CONTAMINATED / "
        "DERIVED_CONTAMINATED / CLEAN."
    )

    text.append("")

    text.append(
        "AUDIT ONLY — no Production or "
        "Backtest logic modified."
    )

    OUT_TXT.write_text(
        "\n".join(text)
    )

    print()
    print("=" * 88)
    print("CANDIDATE SUMMARY")
    print("=" * 88)

    print(
        counts.to_string()
    )

    print()
    print("BY STAGE")

    print(
        by_stage.to_string()
    )

    print()
    print("=" * 88)
    print("CANDIDATE CONTRACTS")
    print("=" * 88)

    if candidate.empty:
        print("NONE")
    else:
        print(
            candidate[
                [
                    "stage",
                    "contract",
                    "candidate_sources",
                    "blast_radius_status",
                ]
            ].to_string(
                index=False
            )
        )

    print()
    print("[OUTPUT]")
    print(OUT_DETAIL)
    print(OUT_SUMMARY)
    print(OUT_TXT)


if __name__ == "__main__":
    main()
