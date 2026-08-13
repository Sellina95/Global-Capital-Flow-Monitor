from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"

SOURCE = RESULTS / "filter13_canonical_full_attribution_daily.csv"

OUT_CSV = RESULTS / "filter13_dead_layer_contract_summary.csv"
OUT_TXT = RESULTS / "filter13_dead_layer_contract_summary.txt"


def norm_text(series: pd.Series) -> pd.Series:
    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )


def main() -> None:

    if not SOURCE.exists():
        raise FileNotFoundError(
            f"Missing canonical attribution source:\n{SOURCE}"
        )

    df = pd.read_csv(SOURCE)

    print("# FILTER13 DEAD-LAYER CONTRACT AUDIT")
    print()
    print("Source:", SOURCE)
    print("Rows  :", len(df))
    print()

    # --------------------------------------------------
    # Required canonical fields
    # --------------------------------------------------

    required = [
        "liq_dir_tag",
        "liq_level_bucket",
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        print("AVAILABLE COLUMNS:")
        for c in df.columns:
            print(c)

        raise RuntimeError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    # ==================================================
    # 1. LIQUIDITY LEVEL CONTRACT
    # ==================================================

    liq_level = norm_text(df["liq_level_bucket"])

    liq_counts = (
        liq_level
        .replace("", "<BLANK>")
        .value_counts(dropna=False)
    )

    liq_high = int((liq_level == "HIGH").sum())
    liq_low = int((liq_level == "LOW").sum())

    liq_actionable = liq_high + liq_low

    if liq_actionable == 0:
        liquidity_verdict = (
            "FAIL_CONTRACT_NO_ACTIONABLE_VALUES"
        )
    else:
        liquidity_verdict = "PASS_ACTIONABLE_VALUES_PRESENT"

    # ==================================================
    # 2. STRUCTURE CONTRACT
    #
    # We intentionally do NOT infer Production semantics.
    # First inspect which execution-state columns actually
    # exist in the canonical runtime capture.
    # ==================================================

    structure_candidates = [
        "mixed",
        "easing",
        "tightening",
        "structure_mixed",
        "structure_easing",
        "structure_tightening",
        "market_structure",
        "structure_state",
    ]

    structure_present = [
        c for c in structure_candidates
        if c in df.columns
    ]

    structure_details = []

    for col in structure_present:

        s = norm_text(df[col])

        counts = (
            s.replace("", "<BLANK>")
            .value_counts(dropna=False)
        )

        structure_details.append(
            {
                "column": col,
                "nonblank": int((s != "").sum()),
                "unique": int(s[s != ""].nunique()),
                "top_values": " | ".join(
                    f"{k}:{v}"
                    for k, v in counts.head(10).items()
                ),
            }
        )

    if not structure_present:
        structure_verdict = (
            "UNRESOLVED_RUNTIME_INPUTS_NOT_CAPTURED"
        )
    else:
        structure_verdict = (
            "RUNTIME_INPUTS_PRESENT_REVIEW_VALUES"
        )

    # ==================================================
    # Summary
    # ==================================================

    rows = [
        {
            "layer": "Liquidity Level",
            "rows": len(df),
            "actionable_rows": liq_actionable,
            "verdict": liquidity_verdict,
        },
        {
            "layer": "Structure",
            "rows": len(df),
            "actionable_rows": None,
            "verdict": structure_verdict,
        },
    ]

    summary = pd.DataFrame(rows)
    summary.to_csv(OUT_CSV, index=False)

    lines = []

    lines.append("# FILTER13 DEAD-LAYER CONTRACT AUDIT")
    lines.append("")
    lines.append("## Source Contract")
    lines.append("")
    lines.append(
        "- CURRENT canonical full-attribution daily artifact"
    )
    lines.append(
        "- Production code modified: NO"
    )
    lines.append(
        "- Candidate logic used: NO"
    )
    lines.append(
        "- Economic optimization performed: NO"
    )
    lines.append("")

    # Liquidity
    lines.append("## Liquidity Level")
    lines.append("")
    lines.append(
        f"HIGH rows       : {liq_high:,}"
    )
    lines.append(
        f"LOW rows        : {liq_low:,}"
    )
    lines.append(
        f"Actionable rows : {liq_actionable:,}"
    )
    lines.append(
        f"Verdict         : {liquidity_verdict}"
    )
    lines.append("")
    lines.append("Observed values:")
    lines.append("")

    for value, count in liq_counts.items():
        lines.append(
            f"- {value}: {count:,}"
        )

    lines.append("")

    # Structure
    lines.append("## Structure")
    lines.append("")
    lines.append(
        "Captured candidate runtime columns: "
        + (
            ", ".join(structure_present)
            if structure_present
            else "NONE"
        )
    )
    lines.append(
        f"Verdict: {structure_verdict}"
    )
    lines.append("")

    if structure_details:

        for item in structure_details:
            lines.append(
                f"### {item['column']}"
            )
            lines.append(
                f"- Nonblank: {item['nonblank']:,}"
            )
            lines.append(
                f"- Unique: {item['unique']:,}"
            )
            lines.append(
                f"- Top values: {item['top_values']}"
            )
            lines.append("")

    else:
        lines.append(
            "The canonical attribution artifact does not "
            "capture the actual `mixed`, `easing`, and "
            "`tightening` runtime inputs."
        )
        lines.append("")
        lines.append(
            "Therefore Structure=0 cannot yet be classified "
            "as intentional inactivity or a broken contract."
        )
        lines.append("")
        lines.append(
            "NEXT GATE: capture the actual Production "
            "Structure runtime inputs without modifying "
            "Production logic."
        )
        lines.append("")

    lines.append("## Decision")
    lines.append("")
    lines.append(
        "- Liquidity Level can be classified directly from "
        "the observed canonical values."
    )
    lines.append(
        "- Structure must NOT be guessed if its runtime "
        "inputs were not captured."
    )
    lines.append(
        "- No Filter13 Production rule should be changed "
        "from this audit."
    )

    OUT_TXT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print("\n".join(lines))

    print()
    print("Saved:")
    print(OUT_CSV)
    print(OUT_TXT)


if __name__ == "__main__":
    main()
