from __future__ import annotations

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MACRO_CSV = DATA_DIR / "macro_data.csv"                 # date,US10Y,DXY,WTI,VIX,USDKRW,HYG,LQD
CREDIT_CSV = DATA_DIR / "credit_spread_data.csv"        # date,HY_OAS
OUT_CSV = DATA_DIR / "sentiment_proxy.csv"


def _to_float(x):
    try:
        return float(x)
    except Exception:
        return None


def _zscore(series: pd.Series, window: int = 120) -> pd.Series:
    """rolling zscore; returns z of last row too"""
    mu = series.rolling(window).mean()
    sd = series.rolling(window).std(ddof=0)
    z = (series - mu) / sd
    return z


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not MACRO_CSV.exists():
        raise FileNotFoundError(f"missing {MACRO_CSV}")

    macro = pd.read_csv(MACRO_CSV)
    if macro.empty or "date" not in macro.columns:
        raise RuntimeError("macro_data.csv is empty or missing date")

    macro["date"] = pd.to_datetime(macro["date"], errors="coerce")
    macro = macro.dropna(subset=["date"]).sort_values("date")

    # Keep only what we need
    for c in ["VIX", "HYG", "LQD"]:
        if c in macro.columns:
            macro[c] = pd.to_numeric(macro[c], errors="coerce")

    # Daily key (macro has timestamps)
    macro["d"] = macro["date"].dt.strftime("%Y-%m-%d")
    daily = macro.groupby("d").tail(1).copy()  # last print of the day
    daily["d"] = pd.to_datetime(daily["d"])

    # Credit (HY OAS) is “last available”
    hy_oas = None
    if CREDIT_CSV.exists():
        cdf = pd.read_csv(CREDIT_CSV)
        if not cdf.empty and "date" in cdf.columns and "HY_OAS" in cdf.columns:
            cdf["date"] = pd.to_datetime(cdf["date"], errors="coerce")
            cdf["HY_OAS"] = pd.to_numeric(cdf["HY_OAS"], errors="coerce")
            cdf = cdf.dropna(subset=["date"]).sort_values("date")
            hy_oas = cdf[["date", "HY_OAS"]].copy()

    if hy_oas is not None:
        # Merge by nearest previous date (as-of)
        daily = pd.merge_asof(
            daily.sort_values("d"),
            hy_oas.sort_values("date"),
            left_on="d",
            right_on="date",
            direction="backward",
        )
    else:
        daily["HY_OAS"] = pd.NA

    # --- build components ---
    # 1) VIX: higher = more fear => negative for sentiment
    daily["VIX_z"] = _zscore(daily["VIX"], window=120)

    # 2) Credit stress: higher HY_OAS = more fear => negative
    daily["HY_OAS_z"] = _zscore(daily["HY_OAS"], window=60)

    # 3) Credit risk appetite: HYG/LQD (higher = risk-on) => positive
    daily["HYG_LQD"] = daily["HYG"] / daily["LQD"]
    daily["HYG_LQD_z"] = _zscore(daily["HYG_LQD"], window=120)

    # --- combine into 0~100 proxy ---
    # weights: VIX 0.45, HY_OAS 0.35, HYG/LQD 0.20 (sum=1)
    # sign: fear indicators are negative, risk appetite positive
    def _combine(row):
        parts = []
        score = 0.0
        w_sum = 0.0

        if pd.notna(row.get("VIX_z")):
            score += 0.45 * (-row["VIX_z"])
            w_sum += 0.45
            parts.append("VIX")
        if pd.notna(row.get("HY_OAS_z")):
            score += 0.35 * (-row["HY_OAS_z"])
            w_sum += 0.35
            parts.append("HY_OAS")
        if pd.notna(row.get("HYG_LQD_z")):
            score += 0.20 * (row["HYG_LQD_z"])
            w_sum += 0.20
            parts.append("HYG/LQD")

        if w_sum == 0:
            return 50.0, "fallback"
        score = score / w_sum  # normalized

        # map z-ish score to 0~100 (soft)
        proxy = 50 + 15 * score
        proxy = max(0.0, min(100.0, proxy))
        return float(proxy), "+".join(parts)

    out_rows = []
    for _, r in daily.iterrows():
        proxy, used = _combine(r)
        out_rows.append(
            {
                "date": r["d"].strftime("%Y-%m-%d"),
                "sentiment_proxy": proxy,
                "used": used,
                "vix": _to_float(r.get("VIX")),
                "hy_oas": _to_float(r.get("HY_OAS")),
                "hyg_lqd": _to_float(r.get("HYG_LQD")),
            }
        )

    out = pd.DataFrame(out_rows)
    out.to_csv(OUT_CSV, index=False)
    print(f"[OK] sentiment_proxy updated: {OUT_CSV} (rows={len(out)})")
    print("[DEBUG] last:", out.tail(1).to_dict(orient="records")[0])


if __name__ == "__main__":
    main()
