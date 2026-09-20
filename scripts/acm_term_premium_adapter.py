from __future__ import annotations

from pathlib import Path

import pandas as pd


PATH = Path("data/acm_term_premium_latest.csv")


def load_acm_term_premium() -> dict:
    unavailable = {
        "available": False,
        "value_pct": None,
        "delta_bp": None,
        "source_date": None,
    }

    try:
        if not PATH.exists():
            return unavailable

        df = pd.read_csv(PATH)

        if df.empty:
            return unavailable

        row = df.iloc[-1]

        value = pd.to_numeric(
            row.get("acmtp10_pct"),
            errors="coerce",
        )
        delta = pd.to_numeric(
            row.get("delta_bp"),
            errors="coerce",
        )

        if pd.isna(value):
            return unavailable

        return {
            "available": True,
            "value_pct": float(value),
            "delta_bp": None if pd.isna(delta) else float(delta),
            "source_date": str(row.get("source_date", "")),
        }

    except Exception as exc:
        print(f"[WARN] ACM term premium unavailable: {exc}")
        return unavailable
