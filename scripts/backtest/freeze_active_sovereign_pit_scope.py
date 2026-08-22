from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "backtest" / "results"

IN_PATH = RESULTS / "sovereign_geo_decision_path_audit.csv"
OUT_PATH = RESULTS / "active_sovereign_pit_scope.csv"
OUT_TXT = RESULTS / "active_sovereign_pit_scope.txt"

df = pd.read_csv(IN_PATH)

active = df[
    df["status"] == "ACTIVE_REQUIRES_PIT_VALIDATION"
].copy()

expected = {"KR10Y", "JP10Y", "DE10Y", "IL10Y"}
actual = set(active["yield_series"])

if actual != expected:
    raise SystemExit(
        f"ABORT — active sovereign scope mismatch: {sorted(actual)}"
    )

active["pit_scope"] = "REQUIRED"
active["reason"] = (
    "Direct GEO decision factor feeding FINAL_STATE risk overlay"
)

active.to_csv(
    OUT_PATH,
    index=False,
    encoding="utf-8-sig",
)

txt = "\n".join([
    "ACTIVE SOVEREIGN PIT SCOPE",
    "=" * 72,
    "",
    "Frozen F13/F15/F18 decision scope:",
    "KR10Y",
    "JP10Y",
    "DE10Y",
    "IL10Y",
    "",
    "Excluded from PIT closure:",
    "GB10Y",
    "MX10Y",
    "",
    "Reason:",
    "GB10Y and MX10Y are not proven Production decision dependencies.",
    "",
    "Next gate:",
    "Historical release / availability / vintage verification for the 4 active series.",
])

OUT_TXT.write_text(
    txt,
    encoding="utf-8",
)

print("=" * 72)
print("ACTIVE SOVEREIGN PIT SCOPE FROZEN")
print("=" * 72)

print(
    active[
        [
            "yield_series",
            "production_spread",
            "production_role",
            "pit_scope",
        ]
    ].to_string(index=False)
)

print()
print("ACTIVE SERIES:", len(active))
print("EXPECTED ACTIVE SERIES: 4")
print("SCOPE GATE: PASS")

print()
print("[OUTPUT]")
print(OUT_PATH)
print(OUT_TXT)
