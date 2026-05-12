from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, List, Tuple

import pandas as pd
import yfinance as yf
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "macro_data.csv"
DATA_DIR.mkdir(parents=True, exist_ok=True)

NY = ZoneInfo("America/New_York")

INDICATORS: Dict[str, str] = {
    "US10Y": "^TNX",
    "DXY": "DX-Y.NYB",
    "WTI": "CL=F",
    "VIX": "^VIX",
    "USDKRW": "KRW=X",
    "HYG": "HYG",
    "LQD": "LQD",
    "XLK": "XLK",
    "XLF": "XLF",
    "XLE": "XLE",
    "XLRE": "XLRE",
    "QQQ": "QQQ",
    "SPY": "SPY",
    "RSP": "RSP",
    "QQQE": "QQQE",
    "GOLD": "GC=F",
    "USDCNH": "CNH=X",
    "USDJPY": "JPY=X",
    "USDMXN": "MXN=X",
    "SEA": "SEA",
    "BDRY": "BDRY",
    "ITA": "ITA",
    "XAR": "XAR",
    "EEM": "EEM",
    "EMB": "EMB",
    "SMH": "SMH",
    "SOXX": "SOXX",
    "IWM": "IWM",
    "VIX3M": "^VIX3M",
    "^VIX9D": "VIX9D",

    
}

FALLBACK_TICKERS = {
    "USDCNH": ["CNH=X", "CNY=X"],
    "DXY": ["DX-Y.NYB", "DX=F", "UUP"],
}

MARKET_DATE_KEYS = {"US10Y", "DXY", "WTI", "VIX", "HYG", "LQD", "SPY", "QQQ"}


def _expected_market_date_kst() -> str:
    now_kst = pd.Timestamp.now(tz="Asia/Seoul")
    expected = (now_kst.normalize() - pd.tseries.offsets.BDay(1)).strftime("%Y-%m-%d")
    print(f"[DEBUG] now_kst={now_kst}")
    print(f"[DEBUG] expected_market_date={expected}")
    return expected


def _normalize_to_market_date(ts) -> Optional[str]:
    try:
        t = pd.Timestamp(ts)
        if pd.isna(t):
            return None
        if t.tzinfo is not None:
            t = t.tz_convert(NY)
        return t.strftime("%Y-%m-%d")
    except Exception:
        return None


def _safe_last_close_and_date(
    df: pd.DataFrame,
    max_market_date: Optional[str] = None,
) -> Tuple[Optional[float], Optional[str]]:
    if df is None or df.empty:
        return None, None

    try:
        max_dt = pd.to_datetime(max_market_date).date() if max_market_date else None

        if isinstance(df.columns, pd.MultiIndex):
            close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
            if not close_cols:
                return None, None

            close_block = df[close_cols].dropna(how="all")
            if close_block.empty:
                return None, None

            valid_rows = []
            for idx in close_block.index:
                asof = _normalize_to_market_date(idx)
                if asof is None:
                    continue
                asof_dt = pd.to_datetime(asof).date()
                if max_dt is not None and asof_dt > max_dt:
                    continue

                row = close_block.loc[idx].dropna()
                if row.empty:
                    continue

                valid_rows.append((idx, row, asof))

            if not valid_rows:
                return None, None

            _, last_row, asof_date = valid_rows[-1]
            return float(last_row.iloc[-1]), asof_date

        if "Close" not in df.columns:
            return None, None

        close = pd.to_numeric(df["Close"], errors="coerce").dropna()
        if close.empty:
            return None, None

        valid_items = []
        for idx, value in close.items():
            asof = _normalize_to_market_date(idx)
            if asof is None:
                continue
            asof_dt = pd.to_datetime(asof).date()
            if max_dt is not None and asof_dt > max_dt:
                continue
            valid_items.append((idx, float(value), asof))

        if not valid_items:
            return None, None

        _, value, asof_date = valid_items[-1]
        return value, asof_date

    except Exception as e:
        print(f"⚠️ _safe_last_close_and_date failed: {e}")
        return None, None


def fetch_macro_data() -> Tuple[Dict[str, float], Optional[str]]:
    results: Dict[str, float] = {}
    market_date_candidates: List[str] = []

    expected_market_date = _expected_market_date_kst()

    def _fetch(ticker: str):
        try:
            df = yf.download(
                ticker,
                period="30d",
                interval="1d",
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            return _safe_last_close_and_date(df, max_market_date=expected_market_date)
        except Exception as e:
            print(f"⚠️ Fetch failed for {ticker}: {e}")
            return None, None

    for name, ticker in INDICATORS.items():
        value, asof_date = None, None

        for t in FALLBACK_TICKERS.get(name, [ticker]):
            value, asof_date = _fetch(t)
            if value is not None:
                break

        if value is None:
            results[name] = float("nan")
            continue

        results[name] = value

        if asof_date and name in MARKET_DATE_KEYS:
            market_date_candidates.append(asof_date)

    print(f"[DEBUG] market_date_candidates={market_date_candidates}")

    ready_count = sum(1 for d in market_date_candidates if d == expected_market_date)

    if ready_count < 4:
        print(
            f"❌ Market data not ready. Skip save. "
            f"expected={expected_market_date}, "
            f"ready_count={ready_count}, "
            f"candidates={market_date_candidates}"
        )
        return results, None

    print(f"[DEBUG] final market_date={expected_market_date}")
    return results, expected_market_date


def append_to_csv(values: Dict[str, float], market_date: Optional[str]) -> None:
    if market_date is None:
        print("❌ append_to_csv skipped: market_date is None")
        return

    row_date = market_date

    # ✅ Daily EOD file: datetime도 기준일로 고정
    row = {"datetime": row_date, "date": row_date}
    row.update(values)

    df_row = pd.DataFrame([row])

    if not CSV_PATH.exists():
        df_row["date"] = pd.to_datetime(df_row["date"], errors="coerce")
        df_row = df_row.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        df_row["date"] = df_row["date"].dt.strftime("%Y-%m-%d")
        df_row["datetime"] = df_row["date"]
        df_row.to_csv(CSV_PATH, index=False)
        print(f"✅ Saved row for {row_date} (new file)")
        return

    df_existing = pd.read_csv(CSV_PATH)

    if "date" not in df_existing.columns:
        df_row.to_csv(CSV_PATH, index=False)
        print(f"✅ Saved row for {row_date} (date column rebuilt)")
        return

    df_existing["date"] = pd.to_datetime(df_existing["date"], errors="coerce")
    df_row["date"] = pd.to_datetime(df_row["date"], errors="coerce")

    df_existing = df_existing.dropna(subset=["date"]).copy()
    df_row = df_row.dropna(subset=["date"]).copy()

    if df_row.empty:
        print("❌ New macro row has invalid date. Skip save.")
        return

    row_date_dt = df_row["date"].iloc[0]
    row_date_str = row_date_dt.strftime("%Y-%m-%d")

    # 같은 date는 overwrite only
    df_existing = df_existing[df_existing["date"] != row_date_dt].copy()

    df_updated = pd.concat([df_existing, df_row], ignore_index=True)

    df_updated["date"] = pd.to_datetime(df_updated["date"], errors="coerce")
    df_updated = df_updated.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    df_updated["date"] = df_updated["date"].dt.strftime("%Y-%m-%d")
    df_updated["datetime"] = pd.to_datetime(df_updated["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    df_updated.to_csv(CSV_PATH, index=False)

    print(f"✅ Saved row for {row_date_str} (overwrite-safe, sorted)")


if __name__ == "__main__":
    vals, market_date = fetch_macro_data()

    if market_date is None:
        print("❌ Skip append_to_csv: previous market close data is not ready.")
    else:
        append_to_csv(vals, market_date)
