from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import requests


URL = (
    "https://www.newyorkfed.org/medialibrary/media/"
    "research/data_indicators/ACMTermPremium.xls"
)

OUT = Path("data/acm_term_premium_latest.csv")


def fetch_acm_term_premium() -> pd.DataFrame:
    response = requests.get(URL, timeout=30)
    response.raise_for_status()

    workbook = pd.ExcelFile(BytesIO(response.content), engine="xlrd")

    if "ACM Daily" not in workbook.sheet_names:
        raise RuntimeError(
            f"Expected 'ACM Daily' sheet not found. "
            f"Available sheets: {workbook.sheet_names}"
        )

    df = pd.read_excel(
        BytesIO(response.content),
        sheet_name="ACM Daily",
        engine="xlrd",
    )

    required = {"DATE", "ACMTP10"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(
            f"Missing expected ACM columns: {sorted(missing)}"
        )

    out = df[["DATE", "ACMTP10"]].copy()
    out["DATE"] = pd.to_datetime(out["DATE"], errors="coerce")
    out["ACMTP10"] = pd.to_numeric(out["ACMTP10"], errors="coerce")
    out = out.dropna().sort_values("DATE")

    if len(out) < 2:
        raise RuntimeError("Not enough valid ACMTP10 observations.")

    latest = out.iloc[-1]
    previous = out.iloc[-2]

    result = pd.DataFrame(
        [{
            "source_date": latest["DATE"].date().isoformat(),
            "acmtp10_pct": round(float(latest["ACMTP10"]), 6),
            "delta_bp": round(
                (float(latest["ACMTP10"]) - float(previous["ACMTP10"])) * 100,
                2,
            ),
            "previous_source_date": previous["DATE"].date().isoformat(),
            "source": "Federal Reserve Bank of New York",
            "series": "ACMTP10",
        }]
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT, index=False)

    return result


if __name__ == "__main__":
    try:
        result = fetch_acm_term_premium()
        print(result.to_string(index=False))
        print(f"[OK] wrote {OUT}")
    except Exception as exc:
        # Never let a failed refresh silently reuse a stale prior observation.
        OUT.unlink(missing_ok=True)
        print(f"[WARN] ACM term premium unavailable: {exc}")
        print("[WARN] Continuing without ACM term premium.")
