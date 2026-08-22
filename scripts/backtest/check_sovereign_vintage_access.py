from __future__ import annotations

import os
from pathlib import Path
import urllib.parse
import urllib.request
import json

ROOT = Path(__file__).resolve().parents[2]

SERIES = {
    "KR10Y": "IRLTLT01KRM156N",
    "JP10Y": "IRLTLT01JPM156N",
    "DE10Y": "IRLTLT01DEM156N",
    "IL10Y": "IRLTLT01ILM156N",
    "GB10Y": "IRLTLT01GBM156N",
    "MX10Y": "IRLTLT01MXM156N",
}

api_key = os.environ.get("FRED_API_KEY", "").strip()

print("=" * 78)
print("SOVEREIGN HISTORICAL VINTAGE ACCESS CHECK")
print("=" * 78)

print("Frozen scope:")
for name, sid in SERIES.items():
    print(f"  {name}: {sid}")

print()

if not api_key:
    print("FRED_API_KEY: NOT FOUND")
    print()
    print("RESULT: EXACT HISTORICAL RELEASE/VINTAGE AUDIT CANNOT RUN YET")
    print(
        "Do not invent monthly release dates. "
        "Six sovereign series remain UNRESOLVED."
    )
    raise SystemExit(0)

params = {
    "series_id": SERIES["KR10Y"],
    "api_key": api_key,
    "file_type": "json",
}

url = (
    "https://api.stlouisfed.org/fred/series/vintagedates?"
    + urllib.parse.urlencode(params)
)

try:
    with urllib.request.urlopen(url, timeout=30) as resp:
        obj = json.loads(resp.read().decode("utf-8"))

    vintages = obj.get("vintage_dates", [])

    print("FRED_API_KEY: FOUND")
    print("API TEST: PASS")
    print("KR10Y VINTAGE DATES RETURNED:", len(vintages))

    if vintages:
        print("FIRST:", vintages[0])
        print("LAST :", vintages[-1])

    print()
    print("RESULT: READY FOR 6-SERIES HISTORICAL VINTAGE AUDIT")

except Exception as exc:
    print("FRED_API_KEY: FOUND")
    print("API TEST: FAIL")
    print(type(exc).__name__, ":", exc)
    print()
    print(
        "RESULT: DO NOT MODIFY PIT PANEL. "
        "Historical release evidence is still unresolved."
    )
