import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import pandas as pd


# ---- 경로 설정 ----
BASE_DIR = Path(__file__).resolve().parent.parent  # repo 루트
DATA_PATH = BASE_DIR / "data" / "macro_data.csv"
ALERT_PATH = BASE_DIR / "insights" / "risk_alerts.txt"


def load_latest_row():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"{DATA_PATH} not found. Run fetch_macro_data.py first.")

    # 일단 그냥 읽기 (parse_dates 안 씀)
    df = pd.read_csv(DATA_PATH)

    if df.empty:
        raise ValueError("macro_data.csv is empty.")

    # date 컬럼이 없으면, 첫 번째 컬럼을 date로 간주해서 이름 바꾸기
    if "date" not in df.columns:
        first_col = df.columns[0]
        df = df.rename(columns={first_col: "date"})

    # date 컬럼을 datetime으로 변환 (문자열이면)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    latest = df.iloc[-1]
    return latest


def evaluate_risks(row):
    """
    row: 마지막 행 (Series)
    리스크 조건에 맞는 메시지 리스트와 전체 레벨을 반환
    """
    alerts = []

    if hasattr(row["date"], "strftime"):
        date_str = row["date"].strftime("%Y-%m-%d")
    else:
        date_str = str(row["date"])

    us10y = float(row.get("US10Y", float("nan")))
    dxy = float(row.get("DXY", float("nan")))
    wti = float(row.get("WTI", float("nan")))
    krw = float(row.get("USDKRW", float("nan")))
    vix = float(row.get("VIX", float("nan")))

    # 각 지표별 기준
    if dxy >= 105:
        alerts.append(f"⚠️ DXY {dxy:.2f} (>=105) → 강달러·리스크오프 구간, EM 통화/위험자산 압박 가능성")

    if vix >= 20:
        alerts.append(f"⚠️ VIX {vix:.2f} (>=20) → 변동성 확대, 위험회피 심리 강화 가능성")

    if us10y >= 5.0:
        alerts.append(f"⚠️ 미 10년물 금리 {us10y:.2f}% (>=5%) → 장기금리 쇼크, 밸류에이션/유동성 압박")

    if krw >= 1450:
        alerts.append(f"⚠️ USD/KRW {krw:.2f} (>=1450) → 원화 약세, 외국인 자금 이탈/커버링 수요 가능성")

    if wti <= 70:
        alerts.append(f"🟡 WTI {wti:.2f} (<=70) → 경기 둔화/수요 약화 우려")
    elif wti >= 90:
        alerts.append(f"🟡 WTI {wti:.2f} (>=90) → 인플레이션 압력 재점화, 정책 부담 증가")

    # 전체 레벨 대충 분류 (알림 개수 기준 간단 버전)
    if not alerts:
        level = "GREEN"
        headline = "✅ TODAY RISK STATUS: GREEN (주요 리스크 신호 없음)"
    elif len(alerts) == 1:
        level = "YELLOW"
        headline = "🟡 TODAY RISK STATUS: YELLOW (국지적/부분 리스크 신호)"
    else:
        level = "RED"
        headline = "🚨 TODAY RISK STATUS: RED (복수의 리스크 신호 감지)"

    return date_str, level, headline, alerts


def send_email_alert(regime_change):
    sender_email = "your_email@example.com"  # 발신자 이메일 주소
    receiver_email = "seyeon8163@gmail.com"  # 수신자 이메일 주소 (세연의 이메일)
    password = "your_password"  # 발신자 이메일 비밀번호

    # 이메일 내용
    subject = "Regime Change Alert"
    body = f"Regime change detected: {regime_change}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    # 이메일 서버 설정 (예: Gmail)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"Email sent successfully to {receiver_email}")
    except Exception as e:
        print(f"Error sending email: {e}")


def write_alert_file(date_str, level, headline, alerts):
    ALERT_PATH.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append(f"[{date_str}] Daily Risk Alerts ({level})")
    lines.append(headline)
    lines.append("")

    if alerts:
        lines.append("■ 트리거 신호 목록")
        for msg in alerts:
            lines.append(f"- {msg}")
    else:
        lines.append("오늘은 설정된 기준을 넘어서는 리스크 신호가 없습니다.")

    lines.append("")
    lines.append("※ 기준값은 개인 학습·연구 목적의 임시 설정이며, 추후 조정 가능")
    lines.append("-" * 60)
    lines.append("")

    ALERT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Risk alerts written to {ALERT_PATH}")


if __name__ == "__main__":
    latest = load_latest_row()
    date_str, level, headline, alerts = evaluate_risks(latest)
    write_alert_file(date_str, level, headline, alerts)
    if level == "RED":
        send_email_alert("Regime change detected!")  # 이메일 알림 추가
