from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

STRATEGIST = ROOT / "filters" / "strategist_filters.py"
GENERATE = ROOT / "scripts" / "generate_report.py"

OUT = (
    ROOT
    / "data"
    / "backtest"
    / "results"
    / "sovereign_geo_decision_path_audit.csv"
)

SERIES = {
    "KR10Y": "KR10Y_SPREAD",
    "JP10Y": "JP10Y_SPREAD",
    "DE10Y": "DE10Y_SPREAD",
    "IL10Y": "IL10Y_SPREAD",
    "GB10Y": "GB10Y_SPREAD",
    "MX10Y": "MX10Y_SPREAD",
}

strategist = STRATEGIST.read_text(encoding="utf-8")
generate = GENERATE.read_text(encoding="utf-8")

# ------------------------------------------------------------
# Locate actual current backtest python files
# ------------------------------------------------------------

backtest_dir = ROOT / "scripts" / "backtest"

backtest_files = sorted(
    p for p in backtest_dir.glob("*.py")
    if p.is_file()
)

backtest_text = {}

for p in backtest_files:
    try:
        backtest_text[p.name] = p.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        pass


def occurrences(text: str, token: str) -> int:
    return len(
        re.findall(
            rf"\b{re.escape(token)}\b",
            text,
        )
    )


def files_with(token: str):
    out = []

    for name, text in backtest_text.items():
        if token in text:
            out.append(name)

    return out


# ------------------------------------------------------------
# GEO overlay structural checks
# ------------------------------------------------------------

overlay_defined = (
    "def apply_geo_overlay_to_final_state" in strategist
)

overlay_called_strategist = (
    strategist.count("apply_geo_overlay_to_final_state(")
    - int(overlay_defined)
)

overlay_called_generate = generate.count(
    "apply_geo_overlay_to_final_state("
)

geo_builder_called_generate = generate.count(
    "attach_geopolitical_ew_layer("
)

geo_overlay_penalty_present = all(
    x in strategist
    for x in [
        '"ELEVATED": -10',
        '"HIGH": -20',
        '"CONFLICT": -25',
    ]
)

rows = []

for yield_name, spread_name in SERIES.items():

    prod_spread_refs = occurrences(
        strategist,
        spread_name,
    )

    geo_factor_direct = bool(
        re.search(
            rf'\("{re.escape(spread_name)}"\s*,',
            strategist,
        )
    )

    similarity_direct = bool(
        re.search(
            rf'["\']{re.escape(spread_name)}["\']'
            rf'.*comp_map',
            strategist,
        )
    )

    backtest_spread_files = files_with(
        spread_name
    )

    backtest_yield_files = files_with(
        yield_name
    )

    # Different historical naming convention
    country = yield_name[:2]

    historical_alt = (
        f"{country}_US_SPREAD"
    )

    backtest_alt_files = files_with(
        historical_alt
    )

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    if geo_factor_direct:
        production_role = (
            "DIRECT_GEO_FACTOR"
        )

    elif similarity_direct:
        production_role = (
            "DIRECT_GEO_SIMILARITY"
        )

    elif prod_spread_refs > 0:
        production_role = (
            "PRODUCTION_REFERENCE"
        )

    else:
        production_role = (
            "NO_PRODUCTION_DECISION_REFERENCE"
        )

    production_decision_active = (
        production_role
        != "NO_PRODUCTION_DECISION_REFERENCE"
    )

    if (
        production_decision_active
        and (
            backtest_spread_files
            or backtest_alt_files
            or backtest_yield_files
        )
    ):
        status = (
            "ACTIVE_REQUIRES_PIT_VALIDATION"
        )

    elif production_decision_active:
        status = (
            "PRODUCTION_ACTIVE_BACKTEST_PATH_NOT_PROVEN"
        )

    else:
        status = (
            "NOT_PROVEN_AS_82_DECISION_DEPENDENCY"
        )

    rows.append({
        "yield_series": yield_name,
        "production_spread": spread_name,
        "production_role": production_role,
        "production_reference_count":
            prod_spread_refs,
        "geo_factor_direct":
            geo_factor_direct,
        "geo_similarity_direct":
            similarity_direct,
        "backtest_exact_spread_files":
            ";".join(backtest_spread_files),
        "backtest_alt_spread_name":
            historical_alt,
        "backtest_alt_spread_files":
            ";".join(backtest_alt_files),
        "backtest_yield_files":
            ";".join(backtest_yield_files),
        "status": status,
    })


df = pd.DataFrame(rows)

OUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

df.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig",
)


print("=" * 100)
print(
    "SOVEREIGN → GEO → DECISION PATH AUDIT"
)
print(
    "Scope: frozen F13/F15/F18 82-contract PIT validation"
)
print("=" * 100)

print()

print("GLOBAL GEO STRUCTURE")
print("-" * 100)

print(
    "GEO builder called in generate_report:",
    geo_builder_called_generate,
)

print(
    "Geo overlay function defined:",
    overlay_defined,
)

print(
    "Geo overlay calls inside strategist_filters:",
    overlay_called_strategist,
)

print(
    "Geo overlay calls inside generate_report:",
    overlay_called_generate,
)

print(
    "Risk-budget penalty map present:",
    geo_overlay_penalty_present,
)

print()

print("SERIES RESULTS")
print("-" * 100)

print(
    df[
        [
            "yield_series",
            "production_spread",
            "production_role",
            "geo_factor_direct",
            "geo_similarity_direct",
            "status",
        ]
    ].to_string(index=False)
)

print()

print("ACTIVE / PIT REQUIRED")
print("-" * 100)

active = df[
    df["status"].isin([
        "ACTIVE_REQUIRES_PIT_VALIDATION",
        "PRODUCTION_ACTIVE_BACKTEST_PATH_NOT_PROVEN",
    ])
]

if active.empty:
    print("NONE")
else:
    print(
        active[
            [
                "yield_series",
                "production_spread",
                "status",
                "backtest_exact_spread_files",
                "backtest_alt_spread_files",
            ]
        ].to_string(index=False)
    )

print()

print("NOT PROVEN AS DECISION DEPENDENCY")
print("-" * 100)

inactive = df[
    df["status"]
    == "NOT_PROVEN_AS_82_DECISION_DEPENDENCY"
]

if inactive.empty:
    print("NONE")
else:
    print(
        inactive[
            [
                "yield_series",
                "production_spread",
            ]
        ].to_string(index=False)
    )

print()

print("[OUTPUT]")
print(OUT)
