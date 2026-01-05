from pathlib import Path
from datetime import datetime
import pandas as pd
from risk_alerts import check_regime_change_and_alert, send_email_alert  # 이메일 알림 추가
from filters.strategist_filters import build_strategist_commentary


# --------------------------------------------------
# Load market data (today vs prev)
# --------------------------------------------------
def load_market_data_for_today():
    """
    data 폴더에서 macro_data 파일을 찾아서
    가장 최근 row(today)와 이전 row(prev)를 읽어온다.
    - macro_data.xlsx 가 있으면 그걸 사용
    - 없으면 macro_data.csv 를 사용
    """

    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    xlsx_path = data_dir / "macro_data.xlsx"
    csv_path = data_dir / "macro_data.csv"

    if xlsx_path.exists():
        df = pd.read_excel(xlsx_path)
    elif csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(
            f"data 폴더에 macro_data.xlsx 또는 macro_data.csv 가 없습니다: {data_dir}"
        )

    # 시간 기준 정렬
    if "datetime" in df.columns:
        df = df.sort_values("datetime")

    if len(df) < 2:
        raise ValueError("macro_data에 최소 2개 이상의 row가 필요합니다.")

    today_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    market_data = {
        "US10Y": {
            "today": float(today_row["US10Y"]),
            "prev": float(prev_row["US10Y"]),
        },
        "DXY": {
            "today": float(today_row["DXY"]),
            "prev": float(prev_row["DXY"]),
        },
        "WTI": {
            "today": float(today_row["WTI"]),
            "prev": float(prev_row["WTI"]),
        },
        "VIX": {
            "today": float(today_row["VIX"]),
            "prev": float(prev_row["VIX"]),
        },
        "USDKRW": {
            "today": float(today_row["USDKRW"]),
            "prev": float(prev_row["USDKRW"]),
        },
    }

    return market_data


# --------------------------------------------------
# Macro signals section
# --------------------------------------------------
def build_macro_signals_section(market_data):
    label_map = {
        "US10Y": "미국 10년물 금리",
        "DXY": "달러 인덱스",
        "WTI": "WTI 유가",
        "VIX": "변동성 지수 (VIX)",
        "USDKRW": "원/달러 환율",
    }

    lines = []
    lines.append("## 📊 Daily Macro Signals\n")

    for key, label in label_map.items():
        today = market_data[key]["today"]
        prev = market_data[key]["prev"]

        change_pct = ((today - prev) / prev) * 100 if prev != 0 else 0.0
        sign = "+" if change_pct >= 0 else ""

        lines.append(
            f"- **{label}**: {today:.3f}  ({sign}{change_pct:.2f}% vs {prev:.3f})"
        )

    return "\n".join(lines)


# --------------------------------------------------
# Daily report generator
# --------------------------------------------------
def generate_daily_report():
    market_data = load_market_data_for_today()

    # Regime Change Check
    check_regime_change_and_alert(market_data)

    macro_section = build_macro_signals_section(market_data)
    strategist_section = build_strategist_commentary(market_data)

    today_str = datetime.now().strftime("%Y-%m-%d")

    report_text = f"""# 🌍 Global Capital Flow – Daily Brief
**Date:** {today_str}

{macro_section}

---

{strategist_section}
"""

    base_dir = Path(__file__).resolve().parent.parent
    report_dir = base_dir / "reports"
    report_dir.mkdir(exist_ok=True)

    report_path = report_dir / f"daily_report_{today_str}.md"
    report_path.write_text(report_text, encoding="utf-8")

    print(f"[INFO] Report generated → {report_path}")


# --------------------------------------------------
# Entry point
# --------------------------------------------------
if __name__ == "__main__":
    generate_daily_report()
