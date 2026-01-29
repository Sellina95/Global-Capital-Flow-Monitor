from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from filters.strategist_filters import build_strategist_commentary
from scripts.risk_alerts import check_regime_change_and_alert


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

# macro_data.csv에 들어있는 키들 (여기서 추가된 지표는 자동으로 읽히지만,
# 필수 daily macro 라인은 이 KEYS를 기준으로 출력)
KEYS = ["US10Y", "DXY", "WTI", "VIX", "USDKRW"]

# 리포트 상단에 따로 Liquidity Snapshot 블럭을 띄울지 (Fed Plumbing Filter가 있으니 보통 False 추천)
SHOW_LIQUIDITY_SNAPSHOT = False


# -------------------------
# Loaders
# -------------------------
def load_macro_df() -> pd.DataFrame:
    """
    Supports:
      - data/macro_data.xlsx
      - data/macro_data.csv
    Columns:
      - date or datetime (first column이면 자동으로 date로 rename)
      - indicator columns (US10Y, DXY, WTI, VIX, USDKRW, HYG, LQD ...)
    """
    xlsx_path = DATA_DIR / "macro_data.xlsx"
    csv_path = DATA_DIR / "macro_data.csv"

    if xlsx_path.exists():
        df = pd.read_excel(xlsx_path)
    elif csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(f"data 폴더에 macro_data.xlsx 또는 macro_data.csv 가 없습니다: {DATA_DIR}")

    if df.empty or len(df) < 2:
        raise ValueError("macro_data에 최소 2개 이상의 row가 필요합니다.")

    # 첫 컬럼이 날짜일 가능성이 높으므로 통일
    cols = list(df.columns)
    if "date" not in cols and "datetime" not in cols:
        # 첫 컬럼을 date로 가정
        df = df.rename(columns={cols[0]: "date"})

    # datetime -> date로 통일
    if "date" not in df.columns and "datetime" in df.columns:
        df = df.rename(columns={"datetime": "date"})

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    if len(df) < 2:
        raise ValueError("macro_data에 최소 2개 이상의 유효한 date row가 필요합니다.")

    return df


def load_fred_extras_df() -> pd.DataFrame:
    csv_path = DATA_DIR / "fred_macro_extras.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=["date", "FCI", "REAL_RATE"])

    df = pd.read_csv(csv_path)
    if df.empty:
        return pd.DataFrame(columns=["date", "FCI", "REAL_RATE"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def attach_fred_extras_layer(market_data: dict) -> dict:
    """
    Attach FCI & REAL_RATE using FRED 'last available' values.
    Adds meta:
      - _FCI_ASOF, _REAL_ASOF (same as last row date)
    Adds series:
      - FCI, REAL_RATE as {today, prev, pct_change}
    """
    df = load_fred_extras_df()
    if df.empty:
        market_data["_FCI_ASOF"] = None
        market_data["_REAL_ASOF"] = None
        return market_data

    today_row = df.iloc[-1]
    asof = pd.to_datetime(today_row["date"]).strftime("%Y-%m-%d")
    market_data["_FCI_ASOF"] = asof
    market_data["_REAL_ASOF"] = asof

    prev_row = df.iloc[-2] if len(df) >= 2 else None

    def add_key(key: str):
        today_val = float(today_row.get(key))
        if prev_row is None:
            market_data[key] = {"today": today_val, "prev": None, "pct_change": None}
            return
        prev_val = float(prev_row.get(key))
        pct = 0.0 if prev_val == 0 else ((today_val - prev_val) / prev_val) * 100.0
        market_data[key] = {"today": today_val, "prev": prev_val, "pct_change": pct}

    add_key("FCI")
    add_key("REAL_RATE")
    return market_data



def load_liquidity_df() -> pd.DataFrame:
    csv_path = DATA_DIR / "liquidity_data.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    # empty/parse-safe
    try:
        if csv_path.stat().st_size == 0:
            return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def load_credit_spread_df() -> pd.DataFrame:
    csv_path = DATA_DIR / "credit_spread_data.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=["date", "HY_OAS"])

    try:
        if csv_path.stat().st_size == 0:
            return pd.DataFrame(columns=["date", "HY_OAS"])
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame(columns=["date", "HY_OAS"])

    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date", "HY_OAS"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


# -------------------------
# Builders
# -------------------------
def build_market_data(today_row: pd.Series, prev_row: pd.Series) -> Dict[str, Any]:
    """
    Builds market_data dict like:
      market_data["US10Y"] = {"today":..., "prev":..., "pct_change":...}
    Also supports extra columns (HYG, LQD 등) automatically if present in dataframe.
    """
    market_data: Dict[str, Any] = {}

    # 1) 필수 KEYS
    for k in KEYS:
        if k not in today_row.index or k not in prev_row.index:
            continue
        today = pd.to_numeric(today_row.get(k), errors="coerce")
        prev = pd.to_numeric(prev_row.get(k), errors="coerce")
        if pd.isna(today) or pd.isna(prev):
            continue
        today_f = float(today)
        prev_f = float(prev)
        pct = 0.0 if prev_f == 0 else ((today_f - prev_f) / prev_f) * 100.0
        market_data[k] = {"today": today_f, "prev": prev_f, "pct_change": pct}

    # 2) 추가 지표들 (macro_data.csv에 있으면 자동으로 포함)
    # date 컬럼 제외하고 숫자 변환 가능한 것들만
    for col in today_row.index:
        if col == "date":
            continue
        if col in market_data:
            continue

        # numeric으로 바뀌는 컬럼만 market_data로
        t = pd.to_numeric(today_row.get(col), errors="coerce")
        p = pd.to_numeric(prev_row.get(col), errors="coerce")
        if pd.isna(t) or pd.isna(p):
            continue

        t_f = float(t)
        p_f = float(p)
        pct = 0.0 if p_f == 0 else ((t_f - p_f) / p_f) * 100.0
        market_data[col] = {"today": t_f, "prev": p_f, "pct_change": pct}

    return market_data


def attach_liquidity_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach TGA/RRP/NET_LIQ into market_data using FRED 'last available' values.
    Adds meta: _LIQ_ASOF = 'YYYY-MM-DD'
    """
    if market_data is None:
        market_data = {}

    liq_df = load_liquidity_df()
    if liq_df.empty:
        market_data["_LIQ_ASOF"] = None
        return market_data

    liq_today = liq_df.iloc[-1]
    liq_asof = pd.to_datetime(liq_today["date"]).strftime("%Y-%m-%d")
    market_data["_LIQ_ASOF"] = liq_asof

    liq_prev = liq_df.iloc[-2] if len(liq_df) >= 2 else None

    def add_liq_key(key: str, today_val, prev_val):
        if today_val is None:
            return
        today_val = float(today_val)
        if prev_val is None:
            market_data[key] = {"today": today_val, "prev": None, "pct_change": None}
            return
        prev_val = float(prev_val)
        pct = 0.0 if prev_val == 0 else ((today_val - prev_val) / prev_val) * 100.0
        market_data[key] = {"today": today_val, "prev": prev_val, "pct_change": pct}

    add_liq_key("TGA", liq_today.get("TGA"), None if liq_prev is None else liq_prev.get("TGA"))
    add_liq_key("RRP", liq_today.get("RRP"), None if liq_prev is None else liq_prev.get("RRP"))
    add_liq_key("NET_LIQ", liq_today.get("NET_LIQ"), None if liq_prev is None else liq_prev.get("NET_LIQ"))

    return market_data


def attach_credit_spread_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach HY_OAS (FRED last available) into market_data.
    Adds:
      - HY_OAS = {today, prev, pct_change}
      - _HY_ASOF = 'YYYY-MM-DD'
    """
    if market_data is None:
        market_data = {}

    df = load_credit_spread_df()
    if df.empty:
        market_data["_HY_ASOF"] = None
        return market_data

    today_row = df.iloc[-1]
    asof = pd.to_datetime(today_row["date"]).strftime("%Y-%m-%d")
    market_data["_HY_ASOF"] = asof

    prev_row = df.iloc[-2] if len(df) >= 2 else None
    today_val = pd.to_numeric(today_row.get("HY_OAS"), errors="coerce")

    if pd.isna(today_val):
        return market_data

    today_val_f = float(today_val)

    if prev_row is None:
        market_data["HY_OAS"] = {"today": today_val_f, "prev": None, "pct_change": None}
        return market_data

    prev_val = pd.to_numeric(prev_row.get("HY_OAS"), errors="coerce")
    if pd.isna(prev_val):
        market_data["HY_OAS"] = {"today": today_val_f, "prev": None, "pct_change": None}
        return market_data

    prev_val_f = float(prev_val)
    pct = 0.0 if prev_val_f == 0 else ((today_val_f - prev_val_f) / prev_val_f) * 100.0
    market_data["HY_OAS"] = {"today": today_val_f, "prev": prev_val_f, "pct_change": pct}
    return market_data


# -------------------------
# Report
# -------------------------
def generate_daily_report() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_macro_df()
    today_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    as_of_date = pd.to_datetime(today_row["date"]).strftime("%Y-%m-%d")
    market_data = build_market_data(today_row, prev_row)

    # Attach layers (never allow None overwrite)
    market_data = attach_liquidity_layer(market_data) or market_data
    market_data = attach_credit_spread_layer(market_data) or market_data
    market_data = attach_fred_extras_layer(market_data)

    # ✅ regime change monitor
    regime_result = check_regime_change_and_alert(market_data, as_of_date)

    # ---- Report ----
    lines = []
    lines.append("# 🌍 Global Capital Flow – Daily Brief")
    lines.append(f"**Date:** {as_of_date}")
    lines.append("")
    lines.append("## 📊 Daily Macro Signals")
    lines.append("")

    # daily core signals (only if exists)
    if "US10Y" in market_data and market_data["US10Y"].get("today") is not None:
        lines.append(
            f"- **미국 10년물 금리**: {market_data['US10Y']['today']:.3f}  "
            f"({market_data['US10Y']['pct_change']:+.2f}% vs {market_data['US10Y']['prev']:.3f})"
        )
    if "DXY" in market_data and market_data["DXY"].get("today") is not None:
        lines.append(
            f"- **달러 인덱스**: {market_data['DXY']['today']:.3f}  "
            f"({market_data['DXY']['pct_change']:+.2f}% vs {market_data['DXY']['prev']:.3f})"
        )
    if "WTI" in market_data and market_data["WTI"].get("today") is not None:
        lines.append(
            f"- **WTI 유가**: {market_data['WTI']['today']:.3f}  "
            f"({market_data['WTI']['pct_change']:+.2f}% vs {market_data['WTI']['prev']:.3f})"
        )
    if "VIX" in market_data and market_data["VIX"].get("today") is not None:
        lines.append(
            f"- **변동성 지수 (VIX)**: {market_data['VIX']['today']:.3f}  "
            f"({market_data['VIX']['pct_change']:+.2f}% vs {market_data['VIX']['prev']:.3f})"
        )
    if "USDKRW" in market_data and market_data["USDKRW"].get("today") is not None:
        lines.append(
            f"- **원/달러 환율**: {market_data['USDKRW']['today']:.3f}  "
            f"({market_data['USDKRW']['pct_change']:+.2f}% vs {market_data['USDKRW']['prev']:.3f})"
        )

    # Optional: Liquidity Snapshot block (usually off)
    if SHOW_LIQUIDITY_SNAPSHOT:
        liq_asof = market_data.get("_LIQ_ASOF")
        tga = market_data.get("TGA", {}).get("today")
        rrp = market_data.get("RRP", {}).get("today")
        net = market_data.get("NET_LIQ", {}).get("today")

        if liq_asof and (tga is not None or rrp is not None or net is not None):
            lines.append("")
            lines.append("## 💧 Liquidity Snapshot (FRED last available)")
            lines.append(f"- **Liquidity as of**: **{liq_asof}** *(FRED latest)*")
            if tga is not None:
                lines.append(f"- **TGA**: {float(tga):.1f}")
            if rrp is not None:
                lines.append(f"- **RRP**: {float(rrp):.3f}")
            if net is not None:
                lines.append(f"- **NET_LIQ**: {float(net):.1f}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🚨 Regime Change Monitor (always-on)")

    if regime_result["status"] == "DETECTED":
        lines.append(f"- **Status:** ✅ DETECTED")
        lines.append(f"- **Prev → Current:** {regime_result['prev_regime']} → {regime_result['current_regime']}")
        lines.append(f"- **File:** `insights/risk_alerts.txt` ✅ created")
        lines.append(f"- **Email:** {'✅ sent' if regime_result['email_sent'] else '❌ not sent'} ({regime_result['email_note']})")
    elif regime_result["status"] == "NOT_DETECTED":
        lines.append(f"- **Status:** ❎ NOT DETECTED")
        lines.append(f"- **Current Regime:** {regime_result['current_regime']}")
        lines.append(f"- **File:** not created")
        lines.append(f"- **Email:** not sent")
    else:
        lines.append(f"- **Status:** ⚪ BASELINE SET (first run)")
        lines.append(f"- **Current Regime:** {regime_result['current_regime']}")
        lines.append(f"- **File/Email:** not created (no previous regime to compare)")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(build_strategist_commentary(market_data))

    report_path = REPORTS_DIR / f"daily_report_{as_of_date}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Report written: {report_path}")


if __name__ == "__main__":
    generate_daily_report()
