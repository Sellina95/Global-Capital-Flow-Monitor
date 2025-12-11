# generate_report.py

import sys
from pathlib import Path
from datetime import date
import pandas as pd

# 🔧 프로젝트 루트 경로를 모듈 검색 경로에 추가
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from filters.strategist_filters import build_strategist_commentary


# ---------------------------------------
# 1) 데이터 로딩: macro_data.xlsx 읽기
# ---------------------------------------


def load_market_data_for_today():
    """
    data 폴더에서 macro_data 파일을 찾아서
    가장 최근 row(today)와 이전 row(yesterday)를 읽어온다.
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
            f"data 폴더에 macro_data.xlsx 나 macro_data.csv 가 없습니다. "
            f"현재 경로: {data_dir}"
        )

    # datetime 기준 정렬
    if "datetime" in df.columns:
        df = df.sort_values("datetime")

    # 최근 값 2개
    today_row = df.iloc[-1]
    yesterday_row = df.iloc[-2]

    market_data = {
        "US10Y": {
            "today": float(today_row["US10Y"]),
            "yesterday": float(yesterday_row["US10Y"]),
        },
        "DXY": {
            "today": float(today_row["DXY"]),
            "yesterday": float(yesterday_row["DXY"]),
        },
        "WTI": {
            "today": float(today_row["WTI"]),
            "yesterday": float(yesterday_row["WTI"]),
        },
        "VIX": {
            "today": float(today_row["VIX"]),
            "yesterday": float(yesterday_row["VIX"]),
        },
        "USDKRW": {
            "today": float(today_row["USDKRW"]),
            "yesterday": float(yesterday_row["USDKRW"]),
        },
    }
    return market_data


# ---------------------------------------
# 2) Daily Macro Signals 섹션 작성
# ---------------------------------------

def build_macro_signals_section(market_data):
    lines = []
    lines.append("## 📊 Daily Macro Signals\n")

    for key, label in {
        "US10Y": "미국 10년물 금리",
        "DXY": "달러 인덱스",
        "WTI": "WTI 유가",
        "VIX": "변동성 지수 (VIX)",
        "USDKRW": "원/달러 환율",
    }.items():

        today = market_data[key]["today"]
        yesterday = market_data[key]["yesterday"]
        pct = (today - yesterday) / yesterday * 100

        lines.append(f"- **{label}**: {today:.3f}  ({pct:+.2f}% vs {yesterday:.3f})")

    return "\n".join(lines)


# ---------------------------------------
# 3) 전체 리포트 만들기
# ---------------------------------------

def generate_daily_report():
    today = date.today().isoformat()
    report_path = Path(f"reports/daily_report_{today}.md")

    market_data = load_market_data_for_today()
    macro_section = build_macro_signals_section(market_data)
    strategist_section = "\n".join(build_strategist_commentary(market_data))

    text = f"""
# 🌍 Global Capital Flow Daily Report — {today}

{macro_section}

---

{strategist_section}

"""

    report_path.write_text(text, encoding="utf-8")
    print(f"[INFO] Report generated → {report_path}")
    return report_path


if __name__ == "__main__":
    generate_daily_report()
