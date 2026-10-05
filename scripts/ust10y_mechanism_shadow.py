from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Dict, Optional
import urllib.request

import pandas as pd


# ============================================================
# UST 10Y MECHANISM SHADOW V0
#
# Evidence authority:
# Evidence-and-Mechanisms / CASE-002 V0
#
# PRESENTATION ONLY
# - No F13 consumer
# - No F15 consumer
# - No F18 consumer
# - No score consumer
# - No allocation consumer
#
# Critical contract:
# - Exact source dates only
# - No forward fill
# - No interpolation
# - No missing = 0
# - Any unavailable required input => UNAVAILABLE
# ============================================================

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"

REQUIRED_FRED = (
    "DGS10",
    "DGS2",
    "DFII10",
    "T10YIE",
    "DGS30",
)

ACM_PATH = Path("data/acm_term_premium_latest.csv")


def _unavailable(reason: str) -> Dict:
    return {
        "status": "UNAVAILABLE",
        "classification": "INCONCLUSIVE",
        "interpretation": "Mechanism classification unavailable.",
        "reason": reason,
        "source_date": None,
        "previous_source_date": None,
        "inputs_bp": {},
        "production_impact": "NONE",
        "evidence_contract": "CASE-002_V0",
    }


def _fetch_fred(series: str) -> pd.DataFrame:
    url = FRED_URL.format(series=series)

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Global-Capital-Flow-Monitor/1.0",
            "Accept": "text/csv,*/*",
        },
    )

    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read()

    df = pd.read_csv(BytesIO(raw))

    if len(df.columns) < 2:
        raise RuntimeError(f"{series}: unexpected FRED response")

    df = df.iloc[:, :2].copy()
    df.columns = ["date", series]

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[series] = pd.to_numeric(df[series], errors="coerce")

    # IMPORTANT:
    # Keep only actual observations returned by FRED.
    # Never ffill/interpolate.
    df = (
        df.dropna(subset=["date", series])
        .sort_values("date")
        .reset_index(drop=True)
    )

    return df


def _load_acm_dates() -> tuple[str, str, float]:
    if not ACM_PATH.exists():
        raise RuntimeError("ACM term premium snapshot missing")

    df = pd.read_csv(ACM_PATH)

    if df.empty:
        raise RuntimeError("ACM term premium snapshot empty")

    row = df.iloc[-1]

    source_date = str(row.get("source_date", "")).strip()
    previous_date = str(row.get("previous_source_date", "")).strip()

    delta_bp = pd.to_numeric(row.get("delta_bp"), errors="coerce")

    if not source_date or not previous_date or pd.isna(delta_bp):
        raise RuntimeError("ACM snapshot missing required date/delta fields")

    return source_date, previous_date, float(delta_bp)


def _exact_value(
    df: pd.DataFrame,
    series: str,
    date_str: str,
) -> Optional[float]:
    target = pd.Timestamp(date_str)

    rows = df.loc[df["date"] == target, series]

    if rows.empty:
        return None

    value = pd.to_numeric(rows.iloc[-1], errors="coerce")

    if pd.isna(value):
        return None

    return float(value)


def _same_direction(a: float, b: float) -> bool:
    if a == 0 or b == 0:
        return False

    return (a > 0 and b > 0) or (a < 0 and b < 0)


def _classify(
    d10: float,
    d2: float,
    real10: float,
    breakeven10: float,
    d30: float,
    term_premium: float,
) -> tuple[str, str]:
    # CASE-002 V0:
    # exact zero 10Y move -> inconclusive
    if d10 == 0:
        return (
            "INCONCLUSIVE",
            "No directional 10Y move to classify.",
        )

    inflation = (
        _same_direction(breakeven10, d10)
        and abs(breakeven10) > abs(real10)
    )

    policy = (
        _same_direction(real10, d10)
        and _same_direction(d2, d10)
        and abs(real10) > abs(breakeven10)
    )

    long_end = (
        _same_direction(d30, d10)
        and _same_direction(term_premium, d10)
        and abs(real10) >= abs(breakeven10)
    )

    if policy and long_end:
        return (
            "MIXED",
            "Policy-path / real-rate and long-end repricing are both present.",
        )

    if inflation:
        return (
            "INFLATION_COMPENSATION",
            "Inflation-compensation repricing dominant.",
        )

    if policy:
        return (
            "POLICY_PATH",
            "Policy-path / real-rate repricing dominant.",
        )

    if long_end:
        return (
            "TERM_PREMIUM_LONG_END",
            "Long-end / term-premium repricing dominant.",
        )

    return (
        "INCONCLUSIVE",
        "No clear dominant mechanism under CASE-002 V0 rules.",
    )


def build_ust10y_mechanism_shadow() -> Dict:
    """
    Fail-open presentation-only shadow.

    This function must never raise into the production report path.
    """
    try:
        source_date, previous_date, acm_delta_bp = _load_acm_dates()

        frames = {
            series: _fetch_fred(series)
            for series in REQUIRED_FRED
        }

        changes_bp: Dict[str, float] = {}

        for series, df in frames.items():
            today = _exact_value(df, series, source_date)
            previous = _exact_value(df, series, previous_date)

            if today is None:
                return _unavailable(
                    f"{series}: no exact observation on {source_date}"
                )

            if previous is None:
                return _unavailable(
                    f"{series}: no exact observation on {previous_date}"
                )

            changes_bp[series] = round(
                (today - previous) * 100.0,
                4,
            )

        classification, interpretation = _classify(
            d10=changes_bp["DGS10"],
            d2=changes_bp["DGS2"],
            real10=changes_bp["DFII10"],
            breakeven10=changes_bp["T10YIE"],
            d30=changes_bp["DGS30"],
            term_premium=acm_delta_bp,
        )

        return {
            "status": "OK",
            "classification": classification,
            "interpretation": interpretation,
            "reason": None,
            "source_date": source_date,
            "previous_source_date": previous_date,
            "inputs_bp": {
                "DGS10": changes_bp["DGS10"],
                "DGS2": changes_bp["DGS2"],
                "DFII10": changes_bp["DFII10"],
                "T10YIE": changes_bp["T10YIE"],
                "DGS30": changes_bp["DGS30"],
                "ACMTP10": round(acm_delta_bp, 4),
            },
            "production_impact": "NONE",
            "evidence_contract": "CASE-002_V0",
        }

    except Exception as exc:
        return _unavailable(
            f"{type(exc).__name__}: {exc}"
        )


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            build_ust10y_mechanism_shadow(),
            indent=2,
            ensure_ascii=False,
        )
    )
