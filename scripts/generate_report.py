from pathlib import Path
from datetime import datetime
import pandas as pd
import yfinance as yf

from filters.strategist_filters import build_strategist_commentary
from scripts.risk_alerts import check_regime_change_and_alert

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
INSIGHTS_DIR = BASE_DIR / "insights"

KEYS = ["US10Y", "DXY", "WTI", "VIX", "USDKRW"]

# 산업별 ETF 리스트 (예시)
etfs = ['XLF', 'XLE', 'XLI', 'XLB', 'XLK']  # 금융, 에너지, 산업, 기본소재, 기술

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

    # date 컬럼 정리
    if "date" not in df.columns:
        df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).reset_index(drop=True)

    return df

def build_market_data(today_row: pd.Series, prev_row: pd.Series) -> dict:
    market_data = {}
    for k in KEYS:
        today = float(today_row.get(k))
        prev = float(prev_row.get(k))
        pct = 0.0
        if prev != 0:
            pct = ((today - prev) / prev) * 100.0
        market_data[k] = {"today": today, "prev": prev, "pct_change": pct}
    return market_data

# Cross-Asset Filter - ETF 데이터 가져오기
def fetch_etf_data(etfs):
    data = {}
    for etf in etfs:
        etf_data = yf.Ticker(etf)
        data[etf] = etf_data.history(period="1d", start="2023-01-01", end="2026-01-01")
    return data

# 경제 데이터 가져오기 (US10Y, VIX, DXY)
def fetch_economic_data():
    # US10Y (미국 10년물 금리) 데이터를 가져오기
    us10y_data = yf.Ticker("US10Y=RR").history(period="1d")  # period만 사용

    # VIX (변동성 지수) 데이터를 가져오기
    vix_data = yf.Ticker("^VIX").history(period="1d")  # period만 사용

    # DXY (달러 인덱스) 데이터를 가져오기
    dxy_data = yf.Ticker("DX-Y.NYB").history(period="1d")  # period만 사용

    return us10y_data, vix_data, dxy_data


# 상관관계 계산 (Pearson correlation 사용)
def calculate_correlation(etf_data, economic_data):
    # ETF 데이터와 경제 지표 데이터를 결합
    etf_prices = pd.DataFrame({etf: data['Close'] for etf, data in etf_data.items()})
    economic_prices = pd.DataFrame({
        'US10Y': economic_data[0]['Close'],
        'VIX': economic_data[1]['Close'],
        'DXY': economic_data[2]['Close']
    })

    # 상관관계 계산
    correlation = etf_prices.corrwith(economic_prices)
    return correlation

# Cross-Asset Filter 리포트 작성
def build_cross_asset_report(correlation):
    lines = []
    lines.append("### 🧩 5) Cross-Asset Filter (연쇄효과 분석)")
    lines.append("추가 이유: 한 지표의 변화가 다른 자산군에 어떻게 전파되는지, 즉 연쇄효과를 파악하기 위함")

    for etf, corr in correlation.items():
        lines.append(f"- **{etf}**와 경제 지표 간 상관관계: {corr:.2f}")

    return "\n".join(lines)

def generate_daily_report() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_macro_df()
    today_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    as_of_date = today_row["date"].strftime("%Y-%m-%d")
    market_data = build_market_data(today_row, prev_row)

    # 경제 지표 데이터 가져오기
    us10y_data, vix_data, dxy_data = fetch_economic_data()
    
    # ETF 데이터 가져오기
    etf_data = fetch_etf_data(etfs)

    # 상관관계 계산
    correlation = calculate_correlation(etf_data, (us10y_data, vix_data, dxy_data))

    # ✅ Regime 변화 감지 결과(항상 리포트에 표시)
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
    else:  # BASELINE_SET
        lines.append(f"- **Status:** ⚪ BASELINE SET (first run)")
        lines.append(f"- **Current Regime:** {regime_result['current_regime']}")
        lines.append(f"- **File/Email:** not created (no previous regime to compare)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(build_strategist_commentary(market_data))
    lines.append("")
    lines.append(build_cross_asset_report(correlation))

    report_path = REPORTS_DIR / f"daily_report_{as_of_date}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Report written: {report_path}")


if __name__ == "__main__":
    generate_daily_report()
