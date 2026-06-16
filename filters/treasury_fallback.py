from typing import Dict, Optional
import pandas as pd


TREASURY_NOMINAL_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "TextView?field_tdr_date_value=2026&type=daily_treasury_yield_curve"
)

TREASURY_REAL_URL = (
    "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
    "TextView?field_tdr_date_value=2026&type=daily_treasury_real_yield_curve"
)


def _latest_table_value(url: str, column: str) -> Optional[float]:
    try:
        tables = pd.read_html(url)
        if not tables:
            return None

        df = tables[0]
        df.columns = [str(c).strip() for c in df.columns]

        if "Date" not in df.columns or column not in df.columns:
            return None

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df[column] = pd.to_numeric(df[column], errors="coerce")
        df = df.dropna(subset=["Date", column]).sort_values("Date")

        if df.empty:
            return None

        return float(df.iloc[-1][column])

    except Exception as e:
        print(f"[WARN][TREASURY_FALLBACK] {column} failed: {e}")
        return None


def fetch_treasury_yield_fallback() -> Dict[str, Optional[float]]:
    dgs10 = _latest_table_value(TREASURY_NOMINAL_URL, "10 Yr")
    dgs2 = _latest_table_value(TREASURY_NOMINAL_URL, "2 Yr")
    real10 = _latest_table_value(TREASURY_REAL_URL, "10 YR")

    t10y2y = round(dgs10 - dgs2, 4) if dgs10 is not None and dgs2 is not None else None
    t10yie = round(dgs10 - real10, 4) if dgs10 is not None and real10 is not None else None

    return {
        "DGS10": dgs10,
        "DGS2": dgs2,
        "T10Y2Y": t10y2y,
        "DFII10": real10,
        "REAL_RATE": real10,
        "T10YIE": t10yie,
    }