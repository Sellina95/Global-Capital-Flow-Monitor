from __future__ import annotations

from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MACRO_CSV = DATA_DIR / "macro_data.csv"          # usually: datetime,US10Y,DXY,WTI,VIX,USDKRW,HYG,LQD
CREDIT_CSV = DATA_DIR / "credit_spread_data.csv" # date,HY_OAS
OUT_CSV = DATA_DIR / "sentiment_proxy.csv"


EXPECTED_MACRO_COLS = ["datetime", "US10Y", "DXY", "WTI", "VIX", "USDKRW", "HYG", "LQD"]


def _to_float(x):
    try:
        return float(x)
    except Exception:
        return None


def _zscore(series: pd.Series, window: int = 120, min_periods: int = 20) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    mu = s.rolling(window=window, min_periods=min_periods).mean()
    sd = s.rolling(window=window, min_periods=min_periods).std(ddof=0)
    z = (s - mu) / sd
    return z


def _load_macro_df() -> pd.DataFrame:
    """
    Robust loader:
    - Accepts 'date' or 'datetime'
    - If header missing or corrupted, tries reading with fixed column names
    """
    if not MACRO_CSV.exists():
        raise FileNotFoundError(f"missing {MACRO_CSV}")

    # 1) normal read
    df = pd.read_csv(MACRO_CSV)

    # If header is broken (single column) try fallback
    if df.shape[1] == 1 and df.columns.tolist() == [EXPECTED_MACRO_COLS[0]]:
        # rare case: file already has correct header but parsing odd; keep as-is
        pass

    # If no 'date'/'datetime', try forcing names (headerless append scenario)
    if ("date" not in df.columns) and ("datetime" not in df.columns):
        df2 = pd.read_csv(MACRO_CSV, header=None, names=EXPECTED_MACRO_COLS)
        # sanity: must at least have datetime + VIX
        if "datetime" in df2.columns and "VIX" in df2.columns:
            df = df2

    # Now decide time column
    time_col = "date" if "date" in df.columns else ("datetime" if "datetime" in df.columns else None)
    if time_col is None:
        raise RuntimeError("macro_data.csv missing 'date'/'datetime' column")

    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col]).sort_values(time_col)

    # Normalize column name to 'datetime' internally
    if time_col != "datetime":
        df = df.rename(columns={time_col: "datetime"})

    # numeric conversion
    for c in ["VIX", "HYG", "LQD"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    macro = _load_macro_df()
    if macro.empty:
        raise RuntimeError("macro_data.csv is empty after parsing")

    # daily key: last print of each day
    macro["d"] = macro["datetime"].dt.strftime("%Y-%m-%d")
    daily = macro.groupby("d").tail(1).copy()
    daily["d"] = pd.to_datetime(daily["d"], errors="coerce")
    daily = daily.dropna(subset=["d"]).sort_values("d")

    # HY OAS (last available, as-of merge)
    if CREDIT_CSV.exists():
        cdf = pd.read_csv(CREDIT_CSV)
        if (not cdf.empty) and ("date" in cdf.columns) and ("HY_OAS" in cdf.columns):
            cdf["date"] = pd.to_datetime(cdf["date"], errors="coerce")
            cdf["HY_OAS"] = pd.to_numeric(cdf["HY_OAS"], errors="coerce")
            cdf = cdf.dropna(subset=["date"]).sort_values("date")
            daily = pd.merge_asof(
                daily.sort_values("d"),
                cdf[["date", "HY_OAS"]].sort_values("date"),
                left_on="d",
                right_on="date",
                direction="backward",
            )
        else:
            daily["HY_OAS"] = pd.NA
    else:
        daily["HY_OAS"] = pd.NA

    # --- components ---
    daily["VIX_z"] = _zscore(daily["VIX"], window=120) if "VIX" in daily.columns else pd.NA
    daily["HY_OAS_z"] = _zscore(daily["HY_OAS"], window=60)
    daily["HYG_LQD"] = (daily["HYG"] / daily["LQD"]) if ("HYG" in daily.columns and "LQD" in daily.columns) else pd.NA
    daily["HYG_LQD_z"] = _zscore(daily["HYG_LQD"], window=120)
    # --- combine into 0~100 ---
    def _combine(row):
        score = 0.0
        w_sum = 0.0
        used = []

        if pd.notna(row.get("VIX_z")):
            score += 0.45 * (-row["VIX_z"])
            w_sum += 0.45
            used.append("VIX")
        if pd.notna(row.get("HY_OAS_z")):
            score += 0.35 * (-row["HY_OAS_z"])
            w_sum += 0.35
            used.append("HY_OAS")
        if pd.notna(row.get("HYG_LQD_z")):
            score += 0.20 * (row["HYG_LQD_z"])
            w_sum += 0.20
            used.append("HYG/LQD")

        if w_sum == 0:
            return 50.0, "fallback"

        score = score / w_sum
        proxy = 50 + 15 * score
        proxy = max(0.0, min(100.0, proxy))
        return float(proxy), "+".join(used)

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
