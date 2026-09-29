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

import json
import math
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.request import Request, urlopen

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


def _fetch_spy_gex_shadow_yahoo() -> Dict[str, Any]:
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
        "source": "YAHOO",
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



def _gex_quality_reasons(result: Dict[str, Any]) -> List[str]:
    """Fail-closed quality gate for a completed GEX snapshot."""
    reasons: List[str] = []

    if result.get("status") != "OK":
        reasons.append("SOURCE_FETCH_FAILED")
        return reasons

    try:
        spot = float(result.get("spot"))
        total = float(result.get("total_unsigned_gex"))
        valid = int(result.get("contracts_valid", 0))
        total_contracts = int(result.get("contracts_total", 0))
        zones = result.get("major_gamma_zones") or []
    except (TypeError, ValueError):
        return ["CALCULATION_ANOMALY"]

    if (
        not math.isfinite(spot)
        or spot <= 0
        or not math.isfinite(total)
        or total <= 0
    ):
        reasons.append("CALCULATION_ANOMALY")

    if total_contracts <= 0 or valid <= 0:
        reasons.append("INCOMPLETE_CHAIN")
    elif valid / total_contracts < 0.50:
        reasons.append("INCOMPLETE_CHAIN")

    positive_zones = []
    for zone in zones:
        try:
            strike = float(zone["strike"])
            gex = float(zone["unsigned_gex"])
            distance = abs(float(zone["distance_pct"]))
        except (KeyError, TypeError, ValueError):
            continue
        if (
            math.isfinite(strike)
            and math.isfinite(gex)
            and gex > 0
        ):
            positive_zones.append((strike, gex, distance))

    if len(positive_zones) < 3:
        reasons.append("SEMANTIC_ANOMALY")
    elif positive_zones[0][2] > 15.0:
        reasons.append("SEMANTIC_ANOMALY")

    try:
        top3 = float(result.get("top3_concentration_share"))
        if not math.isfinite(top3) or not (0.0 <= top3 <= 1.0):
            reasons.append("CALCULATION_ANOMALY")
        elif top3 > 0.95:
            reasons.append("SEMANTIC_ANOMALY")
    except (TypeError, ValueError):
        reasons.append("CALCULATION_ANOMALY")

    return list(dict.fromkeys(reasons))


def _fetch_spy_gex_shadow_cboe() -> Dict[str, Any]:
    """Cboe delayed-chain fallback. No dealer-position sign is inferred."""
    url = "https://cdn.cboe.com/api/global/delayed_quotes/options/SPY.json"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(req, timeout=30) as response:
        payload = json.load(response)

    data = payload.get("data") or {}
    options = data.get("options") or []
    spot = float(data.get("current_price") or 0.0)

    if spot <= 0 or not options:
        raise RuntimeError("Cboe returned no usable SPY option chain")

    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()
    pattern = re.compile(r"^SPY(\d{6})([CP])(\d{8})$")

    rows: List[Dict[str, Any]] = []
    expirations = set()

    for item in options:
        match = pattern.match(str(item.get("option", "")))
        if not match:
            continue

        expiry = datetime.strptime(match.group(1), "%y%m%d").date()
        dte = (expiry - today).days
        if not (0 <= dte <= MAX_DAYS_TO_EXPIRY):
            continue

        expirations.add(expiry.isoformat())

        strike = int(match.group(3)) / 1000.0
        oi = item.get("open_interest")
        iv = item.get("iv")
        gamma = item.get("gamma")

        try:
            oi = float(oi)
            iv = float(iv)
            gamma = float(gamma)
        except (TypeError, ValueError):
            rows.append(
                {
                    "expiration": expiry.isoformat(),
                    "option_type": "CALL" if match.group(2) == "C" else "PUT",
                    "strike": strike,
                    "iv": iv,
                    "open_interest": oi,
                    "gamma": gamma,
                    "unsigned_gex": float("nan"),
                    "valid": False,
                    "reason": "MISSING_OR_INVALID_CBOE_FIELDS",
                    "last_trade_date": item.get("last_trade_time"),
                }
            )
            continue

        valid = (
            strike > 0
            and oi >= 0
            and math.isfinite(iv)
            and math.isfinite(gamma)
            and iv >= 0
            and gamma >= 0
        )

        unsigned_gex = (
            gamma
            * oi
            * CONTRACT_MULTIPLIER
            * spot
            * spot
            * 0.01
            if valid
            else float("nan")
        )

        rows.append(
            {
                "expiration": expiry.isoformat(),
                "option_type": "CALL" if match.group(2) == "C" else "PUT",
                "strike": strike,
                "iv": iv,
                "open_interest": oi,
                "gamma": gamma,
                "unsigned_gex": unsigned_gex,
                "valid": valid,
                "reason": "OK" if valid else "INVALID_CBOE_FIELDS",
                "last_trade_date": item.get("last_trade_time"),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError("Cboe produced no contracts inside GEX horizon")

    valid = df[
        (df["valid"] == True)
        & df["unsigned_gex"].notna()
    ].copy()

    if valid.empty:
        raise RuntimeError("Cboe produced no valid GEX contracts")

    # Source-level QC: widespread zero OI near spot is exactly the Yahoo
    # degradation observed on 2026-09-29. Individual zero-OI contracts
    # remain legitimate and are not rejected individually.
    near = valid[
        (valid["strike"] >= spot * 0.98)
        & (valid["strike"] <= spot * 1.02)
    ]
    positive_oi = int((valid["open_interest"] > 0).sum())
    near_positive_oi = int((near["open_interest"] > 0).sum())

    if positive_oi == 0 or len(near) == 0 or near_positive_oi == 0:
        raise RuntimeError("Cboe option-chain OI failed source quality gate")

    by_strike = (
        valid.groupby("strike", as_index=False)["unsigned_gex"]
        .sum()
        .sort_values("unsigned_gex", ascending=False)
    )

    top_zones = [
        {
            "strike": float(row["strike"]),
            "unsigned_gex": float(row["unsigned_gex"]),
            "distance_pct": (float(row["strike"]) / spot - 1.0) * 100.0,
        }
        for _, row in by_strike.head(5).iterrows()
    ]

    total_unsigned_gex = float(valid["unsigned_gex"].sum())
    top3_share = (
        float(by_strike.head(3)["unsigned_gex"].sum()) / total_unsigned_gex
        if total_unsigned_gex > 0
        else 0.0
    )

    return {
        "contract": "SPY_OPTIONS_GEX_SHADOW_V0",
        "status": "OK",
        "source": "CBOE_DELAYED",
        "source_timestamp": payload.get("timestamp"),
        "snapshot_timestamp_utc": now_utc.isoformat(),
        "underlying": UNDERLYING,
        "spot": spot,
        "risk_free_rate": None,
        "dividend_yield": None,
        "horizon_days": MAX_DAYS_TO_EXPIRY,
        "expirations_requested": sorted(expirations),
        "expiries_successful": len(expirations),
        "expiries_failed": 0,
        "contracts_total": int(len(df)),
        "contracts_valid": int(len(valid)),
        "contracts_invalid": int(len(df) - len(valid)),
        "contracts_missing_oi": int(
            (df["reason"] == "MISSING_OR_INVALID_CBOE_FIELDS").sum()
        ),
        "contracts_missing_iv": int(
            (df["reason"] == "MISSING_OR_INVALID_CBOE_FIELDS").sum()
        ),
        "quality": {
            "positive_oi_contracts": positive_oi,
            "near_spot_contracts": int(len(near)),
            "near_spot_positive_oi_contracts": near_positive_oi,
        },
        "total_unsigned_gex": total_unsigned_gex,
        "top3_concentration_share": top3_share,
        "major_gamma_zones": top_zones,
        "interpretation": (
            "Unsigned option-gamma concentration map. "
            "No dealer long/short positioning is inferred."
        ),
        "production_impact": "NONE",
    }


def fetch_spy_gex_shadow() -> Dict[str, Any]:
    """Yahoo primary -> QC -> Cboe fallback -> fail closed."""
    failures: List[Dict[str, Any]] = []

    try:
        yahoo = _fetch_spy_gex_shadow_yahoo()
        yahoo_reasons = _gex_quality_reasons(yahoo)

        # Additional source QC for the observed Yahoo failure mode.
        # A result whose major zones collapse to zero/far-away nonsense
        # will also fail the common semantic gate above.
        if not yahoo_reasons:
            yahoo["quality_gate"] = {
                "verdict": "PASS",
                "reasons": [],
            }
            return yahoo

        failures.append(
            {"source": "YAHOO", "reasons": yahoo_reasons}
        )
        print(
            f"[WARN][SPY GEX] Yahoo QC failed: {yahoo_reasons}"
        )
    except Exception as exc:
        failures.append(
            {"source": "YAHOO", "reasons": ["SOURCE_FETCH_FAILED"], "detail": str(exc)}
        )
        print(f"[WARN][SPY GEX] Yahoo failed: {exc}")

    try:
        cboe = _fetch_spy_gex_shadow_cboe()
        cboe_reasons = _gex_quality_reasons(cboe)

        if not cboe_reasons:
            cboe["quality_gate"] = {
                "verdict": "PASS",
                "reasons": [],
                "fallback_from": failures,
            }
            return cboe

        failures.append(
            {"source": "CBOE_DELAYED", "reasons": cboe_reasons}
        )
        print(
            f"[WARN][SPY GEX] Cboe QC failed: {cboe_reasons}"
        )
    except Exception as exc:
        failures.append(
            {
                "source": "CBOE_DELAYED",
                "reasons": ["SOURCE_FETCH_FAILED"],
                "detail": str(exc),
            }
        )
        print(f"[WARN][SPY GEX] Cboe failed: {exc}")

    return {
        "contract": "SPY_OPTIONS_GEX_SHADOW_V0",
        "status": "UNAVAILABLE",
        "source": None,
        "snapshot_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "underlying": UNDERLYING,
        "quality_gate": {
            "verdict": "FAIL",
            "reasons": ["ALL_SOURCES_FAILED_QC"],
            "source_failures": failures,
        },
        "major_gamma_zones": [],
        "interpretation": (
            "Gamma map withheld because source/data quality validation failed."
        ),
        "production_impact": "NONE",
    }

def save_spy_gex_snapshot(
    result: Dict[str, Any],
    snapshot_date: str | None = None,
) -> str:
    """
    Persist one daily GEX Shadow snapshot.

    Historical valid snapshots remain immutable. A same-day snapshot that
    fails the current quality gate may be replaced by a newly validated
    result. Writes are atomic.
    """
    if snapshot_date is None:
        snapshot_date = str(
            result["snapshot_timestamp_utc"]
        )[:10]

    out_dir = Path("data/options_gex_shadow/spy")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{snapshot_date}.json"

    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text())
            existing_ok = (
                existing.get("status") == "OK"
                and not _gex_quality_reasons(existing)
            )
        except Exception:
            existing_ok = False

        if existing_ok:
            print(
                f"[INFO][SPY GEX] valid snapshot already exists: "
                f"{out_path}"
            )
            return str(out_path)

        if result.get("status") != "OK":
            print(
                f"[WARN][SPY GEX] existing snapshot is invalid, "
                f"but replacement also failed QC: {out_path}"
            )
        else:
            print(
                f"[WARN][SPY GEX] replacing invalid snapshot: "
                f"{out_path}"
            )

    encoded = json.dumps(result, indent=2, default=str) + "\n"

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{snapshot_date}.",
        suffix=".tmp",
        dir=str(out_dir),
    )
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, out_path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    print(f"[INFO][SPY GEX] snapshot saved: {out_path}")
    return str(out_path)


def _fetch_gex_shadow_yahoo(underlying: str) -> Dict[str, Any]:
    """Generic Yahoo GEX path for QQQ/TLT. SPY keeps its frozen path."""
    ticker = yf.Ticker(underlying)
    price_hist = ticker.history(period="5d")

    if price_hist.empty:
        raise RuntimeError(f"No {underlying} price data available")

    spot = float(price_hist["Close"].dropna().iloc[-1])
    rate = _latest_irx_rate()

    # Same dividend-yield normalization contract as SPY.
    info = ticker.info or {}
    dividend_yield = info.get("trailingAnnualDividendYield")
    if dividend_yield is None:
        dividend_yield = info.get("dividendYield")
        if dividend_yield is not None:
            dividend_yield = float(dividend_yield)
            if dividend_yield > 0.20:
                dividend_yield /= 100.0
    dividend_yield = float(dividend_yield or 0.0)

    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()

    expirations = []
    for expiry_text in ticker.options:
        expiry_date = datetime.strptime(expiry_text, "%Y-%m-%d").date()
        dte = (expiry_date - today).days
        if 0 <= dte <= MAX_DAYS_TO_EXPIRY:
            expirations.append(expiry_text)

    if not expirations:
        raise RuntimeError(
            f"No {underlying} expirations inside GEX Shadow horizon"
        )

    rows = []
    expiries_successful = 0
    expiries_failed = 0

    for expiry_text in expirations:
        expiry_date = datetime.strptime(expiry_text, "%Y-%m-%d").date()
        dte = max((expiry_date - today).days, 0)
        time_years = max(dte, 0.5) / 365.0

        try:
            chain = ticker.option_chain(expiry_text)
            expiries_successful += 1
        except Exception as exc:
            expiries_failed += 1
            print(
                f"[WARN][{underlying} GEX] "
                f"{expiry_text} fetch failed: {exc}"
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

                if pd.isna(strike) or missing_iv or missing_oi:
                    rows.append({
                        "expiration": expiry_text,
                        "option_type": option_type,
                        "strike": strike,
                        "iv": iv,
                        "open_interest": oi,
                        "gamma": float("nan"),
                        "unsigned_gex": float("nan"),
                        "valid": False,
                        "reason": (
                            "MISSING_IV" if missing_iv else "MISSING_OI"
                        ),
                    })
                    continue

                strike = float(strike)
                iv = float(iv)
                oi = float(oi)

                if iv <= MIN_IV or oi < 0:
                    rows.append({
                        "expiration": expiry_text,
                        "option_type": option_type,
                        "strike": strike,
                        "iv": iv,
                        "open_interest": oi,
                        "gamma": float("nan"),
                        "unsigned_gex": float("nan"),
                        "valid": False,
                        "reason": "INVALID_IV_OR_OI",
                    })
                    continue

                gamma = _option_gamma(
                    spot=spot,
                    strike=strike,
                    iv=iv,
                    time_years=time_years,
                    risk_free_rate=rate,
                    dividend_yield=dividend_yield,
                )

                unsigned_gex = (
                    gamma
                    * oi
                    * CONTRACT_MULTIPLIER
                    * spot
                    * spot
                    * 0.01
                )

                rows.append({
                    "expiration": expiry_text,
                    "option_type": option_type,
                    "strike": strike,
                    "iv": iv,
                    "open_interest": oi,
                    "gamma": gamma,
                    "unsigned_gex": unsigned_gex,
                    "valid": True,
                    "reason": "OK",
                })

    df = pd.DataFrame(rows)
    if df.empty:
        raise RuntimeError(f"{underlying} Yahoo produced no contracts")

    valid = df[
        (df["valid"] == True)
        & df["unsigned_gex"].notna()
    ].copy()

    if valid.empty:
        raise RuntimeError(
            f"{underlying} Yahoo produced no valid contracts"
        )

    by_strike = (
        valid.groupby("strike", as_index=False)["unsigned_gex"]
        .sum()
        .sort_values("unsigned_gex", ascending=False)
    )

    zones = [
        {
            "strike": float(row["strike"]),
            "unsigned_gex": float(row["unsigned_gex"]),
            "distance_pct": (
                float(row["strike"]) / spot - 1.0
            ) * 100.0,
        }
        for _, row in by_strike.head(5).iterrows()
    ]

    total_unsigned_gex = float(valid["unsigned_gex"].sum())
    top3_share = (
        float(by_strike.head(3)["unsigned_gex"].sum())
        / total_unsigned_gex
        if total_unsigned_gex > 0 else 0.0
    )

    return {
        "contract": f"{underlying}_OPTIONS_GEX_SHADOW_V0",
        "status": "OK",
        "source": "YAHOO",
        "snapshot_timestamp_utc": now_utc.isoformat(),
        "underlying": underlying,
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
        "major_gamma_zones": zones,
        "interpretation": (
            "Unsigned option-gamma concentration map. "
            "No dealer long/short positioning is inferred."
        ),
        "production_impact": "NONE",
    }


def _fetch_gex_shadow_cboe(underlying: str) -> Dict[str, Any]:
    """Generic Cboe delayed-chain fallback for QQQ/TLT."""
    url = (
        "https://cdn.cboe.com/api/global/delayed_quotes/options/"
        f"{underlying}.json"
    )
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    with urlopen(req, timeout=30) as response:
        payload = json.load(response)

    data = payload.get("data") or {}
    options = data.get("options") or []
    spot = float(data.get("current_price") or 0.0)

    if spot <= 0 or not options:
        raise RuntimeError(
            f"Cboe returned no usable {underlying} option chain"
        )

    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()

    pattern = re.compile(
        rf"^{re.escape(underlying)}(\d{{6}})([CP])(\d{{8}})$"
    )

    rows = []
    expirations = set()

    for item in options:
        match = pattern.match(str(item.get("option", "")))
        if not match:
            continue

        expiry = datetime.strptime(match.group(1), "%y%m%d").date()
        dte = (expiry - today).days

        if not (0 <= dte <= MAX_DAYS_TO_EXPIRY):
            continue

        expirations.add(expiry.isoformat())
        strike = int(match.group(3)) / 1000.0

        try:
            oi = float(item.get("open_interest"))
            iv = float(item.get("iv"))
            gamma = float(item.get("gamma"))
        except (TypeError, ValueError):
            rows.append({
                "expiration": expiry.isoformat(),
                "strike": strike,
                "open_interest": item.get("open_interest"),
                "iv": item.get("iv"),
                "gamma": item.get("gamma"),
                "unsigned_gex": float("nan"),
                "valid": False,
                "reason": "MISSING_OR_INVALID_CBOE_FIELDS",
            })
            continue

        valid_row = (
            strike > 0
            and oi >= 0
            and math.isfinite(iv)
            and math.isfinite(gamma)
            and iv >= 0
            and gamma >= 0
        )

        gex = (
            gamma
            * oi
            * CONTRACT_MULTIPLIER
            * spot
            * spot
            * 0.01
            if valid_row else float("nan")
        )

        rows.append({
            "expiration": expiry.isoformat(),
            "strike": strike,
            "open_interest": oi,
            "iv": iv,
            "gamma": gamma,
            "unsigned_gex": gex,
            "valid": valid_row,
            "reason": (
                "OK" if valid_row else "INVALID_CBOE_FIELDS"
            ),
        })

    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError(
            f"Cboe produced no {underlying} contracts in horizon"
        )

    valid = df[
        (df["valid"] == True)
        & df["unsigned_gex"].notna()
    ].copy()

    if valid.empty:
        raise RuntimeError(
            f"Cboe produced no valid {underlying} contracts"
        )

    near = valid[
        (valid["strike"] >= spot * 0.98)
        & (valid["strike"] <= spot * 1.02)
    ]

    positive_oi = int((valid["open_interest"] > 0).sum())
    near_positive_oi = int(
        (near["open_interest"] > 0).sum()
    )

    if (
        positive_oi == 0
        or len(near) == 0
        or near_positive_oi == 0
    ):
        raise RuntimeError(
            f"{underlying} Cboe OI failed source quality gate"
        )

    by_strike = (
        valid.groupby("strike", as_index=False)["unsigned_gex"]
        .sum()
        .sort_values("unsigned_gex", ascending=False)
    )

    zones = [
        {
            "strike": float(row["strike"]),
            "unsigned_gex": float(row["unsigned_gex"]),
            "distance_pct": (
                float(row["strike"]) / spot - 1.0
            ) * 100.0,
        }
        for _, row in by_strike.head(5).iterrows()
    ]

    total_unsigned_gex = float(valid["unsigned_gex"].sum())
    top3_share = (
        float(by_strike.head(3)["unsigned_gex"].sum())
        / total_unsigned_gex
        if total_unsigned_gex > 0 else 0.0
    )

    return {
        "contract": f"{underlying}_OPTIONS_GEX_SHADOW_V0",
        "status": "OK",
        "source": "CBOE_DELAYED",
        "source_timestamp": payload.get("timestamp"),
        "snapshot_timestamp_utc": now_utc.isoformat(),
        "underlying": underlying,
        "spot": spot,
        "risk_free_rate": None,
        "dividend_yield": None,
        "horizon_days": MAX_DAYS_TO_EXPIRY,
        "expirations_requested": sorted(expirations),
        "expiries_successful": len(expirations),
        "expiries_failed": 0,
        "contracts_total": int(len(df)),
        "contracts_valid": int(len(valid)),
        "contracts_invalid": int(len(df) - len(valid)),
        "contracts_missing_oi": int(
            (df["reason"] == "MISSING_OR_INVALID_CBOE_FIELDS").sum()
        ),
        "contracts_missing_iv": int(
            (df["reason"] == "MISSING_OR_INVALID_CBOE_FIELDS").sum()
        ),
        "quality": {
            "positive_oi_contracts": positive_oi,
            "near_spot_contracts": int(len(near)),
            "near_spot_positive_oi_contracts": near_positive_oi,
        },
        "total_unsigned_gex": total_unsigned_gex,
        "top3_concentration_share": top3_share,
        "major_gamma_zones": zones,
        "interpretation": (
            "Unsigned option-gamma concentration map. "
            "No dealer long/short positioning is inferred."
        ),
        "production_impact": "NONE",
    }


def fetch_gex_shadow(underlying: str) -> Dict[str, Any]:
    underlying = underlying.upper()

    if underlying not in {"QQQ", "TLT"}:
        raise ValueError(
            f"Generic GEX engine unsupported underlying: {underlying}"
        )

    failures = []

    try:
        yahoo = _fetch_gex_shadow_yahoo(underlying)
        reasons = _gex_quality_reasons(yahoo)

        if not reasons:
            yahoo["quality_gate"] = {
                "verdict": "PASS",
                "reasons": [],
            }
            return yahoo

        failures.append({
            "source": "YAHOO",
            "reasons": reasons,
        })
        print(
            f"[WARN][{underlying} GEX] "
            f"Yahoo QC failed: {reasons}"
        )

    except Exception as exc:
        failures.append({
            "source": "YAHOO",
            "reasons": ["SOURCE_FETCH_FAILED"],
            "detail": str(exc),
        })
        print(
            f"[WARN][{underlying} GEX] Yahoo failed: {exc}"
        )

    try:
        cboe = _fetch_gex_shadow_cboe(underlying)
        reasons = _gex_quality_reasons(cboe)

        if not reasons:
            cboe["quality_gate"] = {
                "verdict": "PASS",
                "reasons": [],
                "fallback_from": failures,
            }
            return cboe

        failures.append({
            "source": "CBOE_DELAYED",
            "reasons": reasons,
        })

    except Exception as exc:
        failures.append({
            "source": "CBOE_DELAYED",
            "reasons": ["SOURCE_FETCH_FAILED"],
            "detail": str(exc),
        })

    return {
        "contract": f"{underlying}_OPTIONS_GEX_SHADOW_V0",
        "status": "UNAVAILABLE",
        "source": None,
        "snapshot_timestamp_utc": (
            datetime.now(timezone.utc).isoformat()
        ),
        "underlying": underlying,
        "quality_gate": {
            "verdict": "FAIL",
            "reasons": ["ALL_SOURCES_FAILED_QC"],
            "source_failures": failures,
        },
        "major_gamma_zones": [],
        "interpretation": (
            "Gamma map withheld because source/data quality "
            "validation failed."
        ),
        "production_impact": "NONE",
    }


def save_gex_snapshot(
    result: Dict[str, Any],
    underlying: str,
    snapshot_date: str | None = None,
) -> str:
    underlying = underlying.upper()

    if snapshot_date is None:
        snapshot_date = str(
            result["snapshot_timestamp_utc"]
        )[:10]

    out_dir = Path(
        f"data/options_gex_shadow/{underlying.lower()}"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{snapshot_date}.json"

    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text())
            existing_ok = (
                existing.get("status") == "OK"
                and not _gex_quality_reasons(existing)
            )
        except Exception:
            existing_ok = False

        if existing_ok:
            print(
                f"[INFO][{underlying} GEX] "
                f"valid snapshot already exists: {out_path}"
            )
            return str(out_path)

    encoded = json.dumps(
        result,
        indent=2,
        default=str,
    ) + "\n"

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{snapshot_date}.",
        suffix=".tmp",
        dir=str(out_dir),
    )

    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(tmp_name, out_path)

    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    print(
        f"[INFO][{underlying} GEX] snapshot saved: {out_path}"
    )
    return str(out_path)



if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report-date",
        default=None,
        help="Snapshot date YYYY-MM-DD; daily Production passes KST report date.",
    )
    parser.add_argument(
        "--underlying",
        default="SPY",
        choices=["SPY", "QQQ", "TLT"],
        help="Underlying for the presentation-only GEX Shadow.",
    )
    args = parser.parse_args()

    if args.underlying == "SPY":
        result = fetch_spy_gex_shadow()
        save_spy_gex_snapshot(
            result,
            snapshot_date=args.report_date,
        )
    else:
        result = fetch_gex_shadow(args.underlying)
        save_gex_snapshot(
            result,
            underlying=args.underlying,
            snapshot_date=args.report_date,
        )

    print(json.dumps(result, indent=2, default=str))
