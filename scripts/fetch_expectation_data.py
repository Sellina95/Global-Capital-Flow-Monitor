# scripts/fetch_expectation_data.py
from __future__ import annotations

import time
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import requests


# Keyless FRED CSV endpoint
# Example: https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"


# You can adjust series choices anytime (all are public + stable IDs)
SERIES = {
    # Inflation
    "CPI": "CPIAUCSL",       # CPI-U (SA), Index 1982-84=100 (monthly)
    "PCE": "PCEPI",          # PCE price index (monthly)

    # Labor
    "UNRATE": "UNRATE",      # Unemployment rate (monthly)
    "PAYEMS": "PAYEMS",      # Nonfarm payrolls (monthly level, thousands)

    # Policy / expectations
    "FEDFUNDS": "FEDFUNDS",  # Effective Fed Funds Rate (monthly)
    "T10YIE": "T10YIE",      # 10-Year Breakeven Inflation Rate (daily)
}


def _fetch_fred_series_df(series_id: str, timeout: int = 20) -> pd.DataFrame:
    """
    Fetch a single FRED series as a dataframe with columns: date, value
    Uses keyless fredgraph.csv endpoint.
    """
    url = f"{FRED_CSV}?id={series_id}"

    headers = {
        # Helps reduce occasional blocking / weird responses
        "User-Agent": "Mozilla/5.0 (compatible; Global-Capital-Flow-Monitor/1.0; +https://github.com/)",
        "Accept": "text/csv,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    # Small retry (network hiccup safe)
    last_err = None
    for i in range(3):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            # fredgraph.csv is tiny; parse via pandas from string
            from io import StringIO
            df = pd.read_csv(StringIO(r.text))
            # Expected columns: DATE, <SERIES_ID>
            if df.empty or "DATE" not in df.columns:
                raise ValueError(f"Unexpected CSV format for {series_id}")
            value_col = series_id
            if value_col not in df.columns:
                # sometimes column name can differ; fallback to last column
                value_col = df.columns[-1]

            out = df.rename(columns={"DATE": "date", value_col: "value"})[["date", "value"]]
            out["date"] = pd.to_datetime(out["date"], errors="coerce")
            out["value"] = pd.to_numeric(out["value"], errors="coerce")
            out = out.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
            return out
        except Exception as e:
            last_err = e
            # backoff
            time.sleep(0.7 * (i + 1))
            continue

    raise last_err  # type: ignore


def _latest_and_prev(df: pd.DataFrame) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Return latest_value, prev_value, asof_date(YYYY-MM-DD) based on last non-NaN rows.
    """
    if df is None or df.empty:
        return None, None, None

    d = df.dropna(subset=["value"]).copy()
    if d.empty:
        return None, None, None

    latest = d.iloc[-1]
    latest_val = float(latest["value"])
    asof = pd.to_datetime(latest["date"]).strftime("%Y-%m-%d")

    prev_val = None
    if len(d) >= 2:
        prev = d.iloc[-2]
        prev_val = float(prev["value"])

    return latest_val, prev_val, asof


def _delta(latest: Optional[float], prev: Optional[float]) -> Optional[float]:
    if latest is None or prev is None:
        return None
    return latest - prev


def _fmt(x: Optional[float], nd: int = 2) -> str:
    if x is None:
        return "N/A"
    try:
        return f"{x:.{nd}f}"
    except Exception:
        return "N/A"


def fetch_expectation_data() -> Dict[str, Any]:
    """
    Keyless, stable "Policy Event Surprise Proxy" from FRED.

    Returns a dict that attach_expectation_layer() will store under market_data["EXPECTATIONS"].
    Recommended usage in strategist_filters:
      - Use EXPECTATIONS["proxy"]["CPI_delta"], ["UNRATE_delta"], ["PAYEMS_delta"], etc.
      - Add a one-line bias: inflation cooling vs heating, labor cooling vs overheating, policy easing vs tightening.
    """
    out: Dict[str, Any] = {
        "source": "FRED (keyless) policy-event proxies",
        "as_of": None,
        "series": {},
        "proxy": {},
        "bias_line": None,
    }

    errors = {}

    # Fetch all series
    asof_candidates = []

    for name, sid in SERIES.items():
        try:
            df = _fetch_fred_series_df(sid)
            latest, prev, asof = _latest_and_prev(df)
            asof_candidates.append(asof)

            out["series"][name] = {
                "fred_id": sid,
                "asof": asof,
                "latest": latest,
                "prev": prev,
                "delta": _delta(latest, prev),
            }
        except Exception as e:
            errors[name] = f"{type(e).__name__}: {e}"

    if errors:
        out["errors"] = errors

    # Choose most recent non-null as_of
    asof_candidates = [d for d in asof_candidates if d]
    out["as_of"] = max(asof_candidates) if asof_candidates else None

    # Build proxies we care about
    def get_delta(key: str) -> Optional[float]:
        s = out["series"].get(key, {})
        return s.get("delta")

    cpi_d = get_delta("CPI")
    pce_d = get_delta("PCE")
    unrate_d = get_delta("UNRATE")
    payems_d = get_delta("PAYEMS")
    ffr_d = get_delta("FEDFUNDS")
    be10y_d = get_delta("T10YIE")

    out["proxy"] = {
        "CPI_delta": cpi_d,
        "PCE_delta": pce_d,
        "UNRATE_delta": unrate_d,
        "PAYEMS_delta": payems_d,
        "FEDFUNDS_delta": ffr_d,
        "T10YIE_delta": be10y_d,
    }

    # One-line bias heuristic (simple but stable)
    # Interpretation:
    # - Inflation cooling if CPI/PCE delta < 0
    # - Labor cooling if UNRATE delta > 0 or PAYEMS delta < 0
    # - Policy easing if FEDFUNDS delta < 0
    inflation = "Inflation: N/A"
    if cpi_d is not None or pce_d is not None:
        # prefer CPI, fallback PCE
        base = cpi_d if cpi_d is not None else pce_d
        inflation = "Inflation: cooling" if (base is not None and base < 0) else "Inflation: heating/firm"

    labor = "Labor: N/A"
    if unrate_d is not None or payems_d is not None:
        # If unemployment up OR payrolls down => cooling
        cooling = (unrate_d is not None and unrate_d > 0) or (payems_d is not None and payems_d < 0)
        labor = "Labor: cooling" if cooling else "Labor: firm"

    policy = "Policy: N/A"
    if ffr_d is not None:
        policy = "Policy: easing" if ffr_d < 0 else ("Policy: tightening/hold" if ffr_d > 0 else "Policy: hold")

    breakeven = "Infl. expectations(10y): N/A"
    if be10y_d is not None:
        breakeven = "Infl. expectations(10y): down" if be10y_d < 0 else ("Infl. expectations(10y): up" if be10y_d > 0 else "Infl. expectations(10y): flat")

    out["bias_line"] = (
        f"{inflation} (CPIΔ {_fmt(cpi_d,2)} / PCEΔ {_fmt(pce_d,2)}) | "
        f"{labor} (URΔ {_fmt(unrate_d,2)} / PAYEMSΔ {_fmt(payems_d,1)}) | "
        f"{policy} (FFRΔ {_fmt(ffr_d,2)}) | "
        f"{breakeven} (T10YIEΔ {_fmt(be10y_d,2)})"
    )

    return out


if __name__ == "__main__":
    # Local quick test
    data = fetch_expectation_data()
    print(data.get("source"), data.get("as_of"))
    print(data.get("bias_line"))
