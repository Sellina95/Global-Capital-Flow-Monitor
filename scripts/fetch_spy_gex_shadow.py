"""
SPY Options GEX Shadow V0

Purpose
-------
Build a daily, presentation-only map of where SPY option gamma exposure
is concentrated.

This module is isolated from:
- legacy DEALER_GAMMA_BIAS
- GAMMA_STATE
- GAMMA_SIGNAL
- SEW
- Total Score
- F13 / F15 / F18
- allocation / action logic

V0 deliberately does NOT infer dealer long/short gamma.
It calculates unsigned gamma exposure only.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf


UNDERLYING = "SPY"

# Daily-map horizon. Do not make the report depend only on 0DTE.
MAX_DAYS_TO_EXPIRY = 7

# Standard SPY option contract multiplier.
CONTRACT_MULTIPLIER = 100.0

# Ignore contracts with essentially unusable IV.
MIN_IV = 0.0001


def _normal_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _option_gamma(
    spot: float,
    strike: float,
    iv: float,
    time_years: float,
    risk_free_rate: float,
    dividend_yield: float,
) -> float:
    """Black-Scholes-Merton gamma for one share."""

    if (
        spot <= 0
        or strike <= 0
        or iv <= 0
        or time_years <= 0
    ):
        return float("nan")

    sqrt_t = math.sqrt(time_years)

    d1 = (
        math.log(spot / strike)
        + (
            risk_free_rate
            - dividend_yield
            + 0.5 * iv * iv
        )
        * time_years
    ) / (iv * sqrt_t)

    return (
        math.exp(-dividend_yield * time_years)
        * _normal_pdf(d1)
        / (spot * iv * sqrt_t)
    )


def _latest_irx_rate() -> float:
    """
    ^IRX is quoted in percentage points.
    Example: 4.07 -> 0.0407.
    """

    hist = yf.Ticker("^IRX").history(period="5d")

    if hist.empty:
        raise RuntimeError("No ^IRX data available")

    value = float(hist["Close"].dropna().iloc[-1])
    return value / 100.0


def _spy_dividend_yield(spy: yf.Ticker) -> float:
    """
    Prefer trailingAnnualDividendYield because it is already returned
    as a decimal by the current yfinance runtime.
    """

    info = spy.info or {}

    value = info.get("trailingAnnualDividendYield")

    if value is not None:
        return float(value)

    # yfinance dividendYield may be percentage-style in this runtime.
    value = info.get("dividendYield")

    if value is not None:
        value = float(value)
        return value / 100.0 if value > 0.20 else value

    # Explicit fallback, not silently treated as observed.
    return 0.0


def fetch_spy_gex_shadow() -> Dict[str, Any]:
    spy = yf.Ticker(UNDERLYING)

    price_hist = spy.history(period="5d")

    if price_hist.empty:
        raise RuntimeError("No SPY price data available")

    spot = float(price_hist["Close"].dropna().iloc[-1])
    rate = _latest_irx_rate()
    dividend_yield = _spy_dividend_yield(spy)

    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()

    expirations: List[str] = []

    for expiry_text in spy.options:
        expiry_date = datetime.strptime(
            expiry_text,
            "%Y-%m-%d",
        ).date()

        dte = (expiry_date - today).days

        if 0 <= dte <= MAX_DAYS_TO_EXPIRY:
            expirations.append(expiry_text)

    if not expirations:
        raise RuntimeError(
            "No SPY expirations inside GEX Shadow horizon"
        )

    rows = []

    expiries_successful = 0
    expiries_failed = 0

    for expiry_text in expirations:
        expiry_date = datetime.strptime(
            expiry_text,
            "%Y-%m-%d",
        ).date()

        # Daily V0: use a small positive floor for same-day expiry.
        dte = max((expiry_date - today).days, 0)
        time_years = max(dte, 0.5) / 365.0

        try:
            chain = spy.option_chain(expiry_text)
            expiries_successful += 1
        except Exception as exc:
            expiries_failed += 1
            print(
                f"[WARN][SPY GEX] {expiry_text} fetch failed: {exc}"
            )
            continue

        for option_type, frame in (
            ("CALL", chain.calls),
            ("PUT", chain.puts),
        ):
            if frame is None or frame.empty:
                continue

            for _, row in frame.iterrows():
                strike = row.get("strike")
                iv = row.get("impliedVolatility")
                oi = row.get("openInterest")

                missing_oi = pd.isna(oi)
                missing_iv = pd.isna(iv)

                if (
                    pd.isna(strike)
                    or missing_iv
                    or missing_oi
                ):
                    rows.append(
                        {
                            "expiration": expiry_text,
                            "option_type": option_type,
                            "strike": strike,
                            "iv": iv,
                            "open_interest": oi,
                            "gamma": float("nan"),
                            "unsigned_gex": float("nan"),
                            "valid": False,
                            "reason": (
                                "MISSING_IV"
                                if missing_iv
                                else "MISSING_OI"
                            ),
                            "last_trade_date": row.get(
                                "lastTradeDate"
                            ),
                        }
                    )
                    continue

                strike = float(strike)
                iv = float(iv)
                oi = float(oi)

                if iv <= MIN_IV or oi < 0:
                    rows.append(
                        {
                            "expiration": expiry_text,
                            "option_type": option_type,
                            "strike": strike,
                            "iv": iv,
                            "open_interest": oi,
                            "gamma": float("nan"),
                            "unsigned_gex": float("nan"),
                            "valid": False,
                            "reason": "INVALID_IV_OR_OI",
                            "last_trade_date": row.get(
                                "lastTradeDate"
                            ),
                        }
                    )
                    continue

                gamma = _option_gamma(
                    spot=spot,
                    strike=strike,
                    iv=iv,
                    time_years=time_years,
                    risk_free_rate=rate,
                    dividend_yield=dividend_yield,
                )

                # Dollar gamma exposure for a 1% move in SPY.
                #
                # IMPORTANT:
                # This is UNSIGNED. Calls and puts are not assigned
                # a dealer-position sign in V0.
                unsigned_gex = (
                    gamma
                    * oi
                    * CONTRACT_MULTIPLIER
                    * spot
                    * spot
                    * 0.01
                )

                rows.append(
                    {
                        "expiration": expiry_text,
                        "option_type": option_type,
                        "strike": strike,
                        "iv": iv,
                        "open_interest": oi,
                        "gamma": gamma,
                        "unsigned_gex": unsigned_gex,
                        "valid": True,
                        "reason": "OK",
                        "last_trade_date": row.get(
                            "lastTradeDate"
                        ),
                    }
                )

    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError("SPY GEX Shadow produced no contracts")

    valid = df[
        (df["valid"] == True)
        & df["unsigned_gex"].notna()
    ].copy()

    if valid.empty:
        raise RuntimeError(
            "SPY GEX Shadow produced no valid contracts"
        )

    by_strike = (
        valid.groupby("strike", as_index=False)["unsigned_gex"]
        .sum()
        .sort_values("unsigned_gex", ascending=False)
    )

    top_zones = []

    for _, row in by_strike.head(5).iterrows():
        top_zones.append(
            {
                "strike": float(row["strike"]),
                "unsigned_gex": float(row["unsigned_gex"]),
                "distance_pct": (
                    float(row["strike"]) / spot - 1.0
                )
                * 100.0,
            }
        )

    total_unsigned_gex = float(valid["unsigned_gex"].sum())

    top3_share = (
        float(by_strike.head(3)["unsigned_gex"].sum())
        / total_unsigned_gex
        if total_unsigned_gex > 0
        else 0.0
    )

    return {
        "contract": "SPY_OPTIONS_GEX_SHADOW_V0",
        "status": "OK",
        "snapshot_timestamp_utc": now_utc.isoformat(),
        "underlying": UNDERLYING,
        "spot": spot,
        "risk_free_rate": rate,
        "dividend_yield": dividend_yield,
        "horizon_days": MAX_DAYS_TO_EXPIRY,
        "expirations_requested": expirations,
        "expiries_successful": expiries_successful,
        "expiries_failed": expiries_failed,
        "contracts_total": int(len(df)),
        "contracts_valid": int(len(valid)),
        "contracts_invalid": int(len(df) - len(valid)),
        "contracts_missing_oi": int(
            (df["reason"] == "MISSING_OI").sum()
        ),
        "contracts_missing_iv": int(
            (df["reason"] == "MISSING_IV").sum()
        ),
        "total_unsigned_gex": total_unsigned_gex,
        "top3_concentration_share": top3_share,
        "major_gamma_zones": top_zones,
        "interpretation": (
            "Unsigned option-gamma concentration map. "
            "No dealer long/short positioning is inferred."
        ),
        "production_impact": "NONE",
    }


def save_spy_gex_snapshot(result: Dict[str, Any]) -> str:
    """
    Persist one immutable daily GEX Shadow snapshot.

    Historical snapshots are not reconstructed or backfilled.
    """
    import json
    from pathlib import Path

    snapshot_date = str(
        result["snapshot_timestamp_utc"]
    )[:10]

    out_dir = Path("data/options_gex_shadow/spy")
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{snapshot_date}.json"

    if out_path.exists():
        print(
            f"[INFO][SPY GEX] snapshot already exists: "
            f"{out_path}"
        )
        return str(out_path)

    out_path.write_text(
        json.dumps(
            result,
            indent=2,
            default=str,
        )
        + "\n"
    )

    print(
        f"[INFO][SPY GEX] snapshot saved: {out_path}"
    )

    return str(out_path)


if __name__ == "__main__":
    import json

    result = fetch_spy_gex_shadow()
    save_spy_gex_snapshot(result)

    print(json.dumps(result, indent=2, default=str))
