import pandas as pd
from pathlib import Path

# 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "macro_data.csv"
INSIGHTS_DIR = BASE_DIR / "insights"

SUMMARY_PATH = INSIGHTS_DIR / "daily_summary.txt"
RISK_PATH = INSIGHTS_DIR / "risk_alerts.txt"


def load_latest_row():
    """macro_data.csv에서 가장 최근 날짜 한 줄을 가져옴."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"{DATA_PATH} not found")

    # 1) 그냥 읽고
    df = pd.read_csv(DATA_PATH)

    # 2) date 컬럼이 없으면 첫 번째 컬럼을 date 로 간주
    if "date" not in df.columns:
        first_col = df.columns[0]
        df = df.rename(columns={first_col: "date"})

    # 3) 문자열 → datetime 변환
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # 유효한 날짜만
    df = df.dropna(subset=["date"])

    # 4) 날짜 기준 정렬 후 마지막 행 선택
    df = df.sort_values("date")
    latest = df.iloc[-1]

    return latest


def read_text_file(path: Path) -> str:
    """텍스트 파일이 있으면 내용 읽고, 없으면 빈 문자열 반환."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def generate_report():
    latest = load_latest_row()

    date = latest["date"]
    if isinstance(date, str):
        date_for_title = date[:10]
    else:
        date_for_title = date.strftime("%Y-%m-%d")

    us10y = latest.get("US10Y", None)
    dxy = latest.get("DXY", None)
    wti = latest.get("WTI", None)
    vix = latest.get("VIX", None)
    usdkrw = latest.get("USDKRW", None)

    # 요약/리스크 텍스트 읽기
    summary_text = read_text_file(SUMMARY_PATH)
    risk_text = read_text_file(RISK_PATH)

    # 파일 이름: daily_report_YYYY-MM-DD.md
    report_filename = f"daily_report_{date_for_title}.md"
    report_path = INSIGHTS_DIR / report_filename

    # 마크다운 내용 구성 (Mirror 에디터에 바로 붙여넣기용)
    lines = []

    lines.append(f"# Daily Macro Report – {date_for_title}")
    lines.append("")
    lines.append("## 1. Today’s Macro Snapshot")
    lines.append("")

    def fmt(label, value, suffix=""):
        if value is None or pd.isna(value):
            return f"- **{label}**: N/A"
        if suffix:
            return f"- **{label}**: {value:.2f}{suffix}"
        return f"- **{label}**: {value:.2f}"

    lines.append(fmt("US 10Y Yield", us10y, "%"))
    lines.append(fmt("DXY (Dollar Index)", dxy))
    lines.append(fmt("WTI Crude Oil (USD/bbl)", wti))
    lines.append(fmt("VIX (Volatility Index)", vix))
    lines.append(fmt("USD/KRW", usdkrw))
    lines.append("")

    lines.append("## 2. Auto Summary (3 Lines)")
    lines.append("")
    if summary_text:
        lines.append(summary_text)
    else:
        lines.append("_No summary generated yet._")
    lines.append("")

    lines.append("## 3. Risk Alerts")
    lines.append("")
    if risk_text:
        lines.append(risk_text)
    else:
        lines.append("_No specific risk alerts for today._")
    lines.append("")

    lines.append("## 4. Strategist Memo (세연 메모)")
    lines.append("")
    lines.append("> 오늘 시장에서 전략가 관점에서 체크할 포인트를 간단히 적어보세요.")
    lines.append("")
    lines.append("- 오늘 눈에 띄는 지표 / 움직임:")
    lines.append("- 내일/이번 주 추가로 확인할 이벤트 (FOMC, CPI, 고용지표 등):")
    lines.append("- 포지셔닝/리스크 관리에 대한 개인 메모:")

    # 파일로 저장
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"[OK] Generated report: {report_path}")


if __name__ == "__main__":
    generate_report()
