from __future__ import annotations

from pathlib import Path
import pandas as pd

from filters.strategist_filters import build_strategist_commentary
from scripts.risk_alerts import check_regime_change_and_alert


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

KEYS = ["US10Y", "DXY", "WTI", "VIX", "USDKRW"]


def load_macro_df() -> pd.DataFrame:
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

    if "date" not in df.columns:
        df = df.rename(columns={df.columns[0]: "date"})

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    return df


def load_liquidity_df() -> pd.DataFrame:
    csv_path = DATA_DIR / "liquidity_data.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    df = pd.read_csv(csv_path)
    if df.empty:
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def build_market_data(today_row: pd.Series, prev_row: pd.Series) -> dict:
    market_data = {}
    for k in KEYS:
        today = float(today_row.get(k))
        prev = float(prev_row.get(k))
        pct = 0.0 if prev == 0 else ((today - prev) / prev) * 100.0
        market_data[k] = {"today": today, "prev": prev, "pct_change": pct}
    return market_data


def attach_liquidity_layer(market_data: dict) -> dict:
    """
    Attach TGA/RRP/NET_LIQ into market_data using FRED 'last available' values.
    - Always attaches 'today' from last row.
    - Attaches 'prev' only if we have >=2 rows.
    - Adds meta: _LIQ_ASOF = 'YYYY-MM-DD'
    """
    liq_df = load_liquidity_df()

    # If no liquidity file/data
    if liq_df.empty:
        market_data["_LIQ_ASOF"] = None
        return market_data

    # last available
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


def generate_daily_report() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_macro_df()
    today_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    as_of_date = pd.to_datetime(today_row["date"]).strftime("%Y-%m-%d")
    market_data = build_market_data(today_row, prev_row)

    # ✅ attach liquidity (last available)
    market_data = attach_liquidity_layer(market_data)

    # ✅ regime change monitor
    regime_result = check_regime_change_and_alert(market_data, as_of_date)

    # ---- Report ----
    lines = []
    lines.append("# 🌍 Global Capital Flow – Daily Brief")
    lines.append(f"**Date:** {as_of_date}")
    lines.append("")
    lines.append("## 📊 Daily Macro Signals")
    lines.append("")
    lines.append(f"- **미국 10년물 금리**: {market_data['US10Y']['today']:.3f}  ({market_data['US10Y']['pct_change']:+.2f}% vs {market_data['US10Y']['prev']:.3f})")
    lines.append(f"- **달러 인덱스**: {market_data['DXY']['today']:.3f}  ({market_data['DXY']['pct_change']:+.2f}% vs {market_data['DXY']['prev']:.3f})")
    lines.append(f"- **WTI 유가**: {market_data['WTI']['today']:.3f}  ({market_data['WTI']['pct_change']:+.2f}% vs {market_data['WTI']['prev']:.3f})")
    lines.append(f"- **변동성 지수 (VIX)**: {market_data['VIX']['today']:.3f}  ({market_data['VIX']['pct_change']:+.2f}% vs {market_data['VIX']['prev']:.3f})")
    lines.append(f"- **원/달러 환율**: {market_data['USDKRW']['today']:.3f}  ({market_data['USDKRW']['pct_change']:+.2f}% vs {market_data['USDKRW']['prev']:.3f})")

    # Liquidity summary line (always show as-of if available)
    liq_asof = market_data.get("_LIQ_ASOF")
    if liq_asof:
        tga = market_data.get("TGA", {}).get("today")
        rrp = market_data.get("RRP", {}).get("today")
        net = market_data.get("NET_LIQ", {}).get("today")
        lines.append("")
        lines.append(f"## 💧 Liquidity Snapshot (FRED last available)")
        lines.append(f"- **Liquidity as of**: **{liq_asof}** *(FRED latest)*")
        if tga is not None:
            lines.append(f"- **TGA**: {tga:.1f}")
        if rrp is not None:
            lines.append(f"- **RRP**: {rrp:.3f}")
        if net is not None:
            lines.append(f"- **NET_LIQ**: {net:.1f}")

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
