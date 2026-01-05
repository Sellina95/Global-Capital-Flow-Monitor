import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from filters.strategist_filters import get_regime_label

BASE_DIR = Path(__file__).resolve().parent.parent
INSIGHTS_DIR = BASE_DIR / "insights"
ALERT_FILE = INSIGHTS_DIR / "risk_alerts.txt"
STATE_FILE = INSIGHTS_DIR / "last_regime_state.json"


def _ensure_dirs():
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(state: Dict[str, Any]) -> None:
    _ensure_dirs()
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def write_regime_alert_file(as_of_date: str, prev_regime: str, new_regime: str) -> None:
    _ensure_dirs()
    lines = []
    lines.append(f"[{as_of_date}] 🚨 Regime Change Detected")
    lines.append(f"- Previous: {prev_regime}")
    lines.append(f"- Current : {new_regime}")
    lines.append("")
    lines.append("※ 이 파일은 '시장 국면(Regime) 변화'가 감지되었을 때만 생성됩니다.")
    ALERT_FILE.write_text("\n".join(lines), encoding="utf-8")


def send_email_resend(subject: str, body: str) -> Tuple[bool, str]:
    """
    Requires:
      - RESEND_API_KEY (GitHub Secret)
      - RESEND_FROM (e.g. "alerts@yourdomain.com")  *Resend에서 발신 도메인 인증 필요할 수 있음*
      - RESEND_TO   (e.g. "seyeon8143@gmail.com")
    """
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM")
    to_email = os.getenv("RESEND_TO")

    if not api_key or not from_email or not to_email:
        return False, "RESEND env missing (RESEND_API_KEY/RESEND_FROM/RESEND_TO)"

    try:
        import requests  # needs 'requests' in dependencies
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": from_email, "to": [to_email], "subject": subject, "text": body},
            timeout=20,
        )
        if 200 <= r.status_code < 300:
            return True, "sent"
        return False, f"resend http {r.status_code}: {r.text}"
    except Exception as e:
        return False, f"exception: {e}"


def check_regime_change_and_alert(market_data: Dict[str, Any], as_of_date: str) -> Dict[str, Any]:
    """
    Returns dict for report display:
      status: "DETECTED" | "NOT_DETECTED" | "BASELINE_SET"
      prev_regime, current_regime
      alert_file_created: bool
      email_sent: bool
      email_note: str
    """
    current = get_regime_label(market_data)

    state = _load_state()
    prev = state.get("last_regime")

    # 첫 실행: 비교 대상이 없으니 baseline만 저장
    if not prev:
        _save_state({"last_regime": current, "last_date": as_of_date})
        return {
            "status": "BASELINE_SET",
            "prev_regime": None,
            "current_regime": current,
            "alert_file_created": False,
            "email_sent": False,
            "email_note": "baseline saved (first run)",
        }

    # 변화 감지
    if prev != current:
        write_regime_alert_file(as_of_date, prev, current)

        subject = f"[Regime Alert] {as_of_date} | {prev} → {current}"
        body = (
            f"Regime change detected.\n\n"
            f"- Date: {as_of_date}\n"
            f"- Previous: {prev}\n"
            f"- Current : {current}\n\n"
            f"File created: insights/risk_alerts.txt"
        )
        ok, note = send_email_resend(subject, body)

        _save_state({"last_regime": current, "last_date": as_of_date})

        return {
            "status": "DETECTED",
            "prev_regime": prev,
            "current_regime": current,
            "alert_file_created": True,
            "email_sent": ok,
            "email_note": note,
        }

    # 변화 없음
    _save_state({"last_regime": current, "last_date": as_of_date})
    return {
        "status": "NOT_DETECTED",
        "prev_regime": prev,
        "current_regime": current,
        "alert_file_created": False,
        "email_sent": False,
        "email_note": "no change",
    }
