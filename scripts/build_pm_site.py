from __future__ import annotations

import html
import re
from pathlib import Path




ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
SITE_DIR = ROOT / "_site"
ASSETS_DIR = SITE_DIR / "assets"




def tape_display(value):
    value = str(value or "").strip()

    # Source text may already contain a risk marker.
    # Renderer owns the single absolute-level marker.
    value = value.lstrip("🔴🟢🟡").strip()

    # Rising / Stronger / Weaker / Falling / COOL 등 텍스트만 제거
    value = re.sub(
        r"\b(?:Rising|Falling|Stronger|Weaker|COOL|Widening|Tightening|Improving|Stable)\b",
        "",
        value,
        flags=re.I,
    )

    # HY OAS처럼 방향 화살표 없이 변화율만 남은 경우
    # 음수 = ↓ / 양수 = ↑
    if "·" in value and "↑" not in value and "↓" not in value:
        m = re.search(r"\(([+-]\d+(?:\.\d+)?)%\)", value)
        if m:
            arrow = "↓" if m.group(1).startswith("-") else "↑"
            left, right = value.split("·", 1)
            value = f"{left.strip()} · {arrow} {right.strip()}"

    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+·\s+", " · ", value)

    return value.strip()

def compact_tape_value(value):
    value = str(value or "").strip()

    # 직전 패치의 split 표시가 builder에 남아 있어도
    # 실제 원본 value를 이 함수에 넘기도록 아래 renderer에서 교체한다.

    # "4.78% · ↑ Rising (+0.46%)"
    # -> "4.78% · ↑ (+0.46%)"
    value = re.sub(
        r"(·\s*[↑↓→])\s*"
        r"(?:Rising|Falling|Stronger|Weaker|COOL|Widening|Tightening|Improving|Stable)"
        r"\s*",
        r"\1 ",
        value,
        flags=re.I,
    )

    return value

def latest_pm_report() -> Path:
    reports = sorted(REPORTS_DIR.glob("daily_report_????-??-??.md"))
    if not reports:
        raise FileNotFoundError("No daily PM report found.")
    return reports[-1]


def field(text: str, label: str, default: str = "N/A") -> str:
    match = re.search(
        rf"^{re.escape(label)}\s+(.+?)\s*$",
        text,
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else default


def metadata(text: str, label: str, default: str = "N/A") -> str:
    match = re.search(
        rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$",
        text,
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else default


def top_value(text: str, label: str, default: str = "N/A") -> str:
    match = re.search(
        rf"^{re.escape(label)}\s*$\n(.+?)$",
        text,
        flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else default


def section(text: str, number: int, title: str) -> str:
    # Title is canonical; section number may change across PM contract versions.
    match = re.search(
        rf"^\d+\.\s+{re.escape(title)}\s*$",
        text,
        flags=re.MULTILINE,
    )

    if not match:
        return ""

    start = match.end()

    next_section = re.search(
        r"^\d+\.\s+[A-Z][A-Z &\-]+$",
        text[start:],
        flags=re.MULTILINE,
    )

    if next_section:
        end = start + next_section.start()
        return text[start:end].strip()

    return text[start:].strip()

    return text[start:].strip()


def first_prose_line(text: str, default: str = "N/A") -> str:
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.match(r"^[A-Za-z][A-Za-z ]+\s{2,}", line):
            continue
        return line
    return default


def parse_sector_rows(block: str) -> list[dict[str, str]]:
    rows = []

    pattern = re.compile(
        r"^\s*(\d+)\s+"
        r"(.+?)\s{2,}"
        r"([+-]\d+\.\d+%)\s+"
        r"([+-]\d+\.\d+%)\s+"
        r"(-?\d+|N/A)\s*$",
        flags=re.MULTILINE,
    )

    for match in pattern.finditer(block):
        rows.append(
            {
                "rank": match.group(1),
                "sector": match.group(2).strip(),
                "return": match.group(3),
                "relative": match.group(4),
                "momentum": match.group(5),
            }
        )

    return rows


def parse_breadth_rows(block: str) -> list[dict[str, str]]:
    rows = []

    pattern = re.compile(
        r"^(RSP vs SPY|QQQE vs QQQ|SMH vs SPY|IWM vs SPY)\s+"
        r"Today\s+(.+?)\s+\|\s+"
        r"Prev\s+(.+?)\s+\|\s+"
        r"Δ\s+(.+?)\s*$",
        flags=re.MULTILINE,
    )

    for match in pattern.finditer(block):
        rows.append(
            {
                "label": match.group(1),
                "today": match.group(2),
                "prev": match.group(3),
                "change": match.group(4),
            }
        )

    return rows


def parse_allocation_rows(block: str) -> list[dict[str, str]]:
    rows = []

    marker = "Sector Allocation"
    pos = block.find(marker)

    if pos == -1:
        return rows

    allocation_text = block[pos + len(marker):]

    for raw in allocation_text.splitlines():
        line = raw.strip()

        if not line:
            continue

        if line.startswith("Note:"):
            break

        match = re.match(
            r"^(.+?)\s{2,}([0-9]+(?:\.[0-9]+)?%)$",
            line,
        )

        if match:
            rows.append(
                {
                    "sector": match.group(1).strip(),
                    "weight": match.group(2),
                }
            )

    return rows


def parse_rationale(block: str) -> list[str]:
    reasons = []

    capture = False

    for raw in block.splitlines():
        line = raw.strip()

        if line == "Rationale":
            capture = True
            continue

        if capture and line.startswith("- "):
            reasons.append(line[2:].strip())

    return reasons



def diag_match(
    text: str,
    pattern: str,
    default: str = "N/A",
) -> str:
    """Read an existing diagnostics field without creating a new signal."""
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1).strip() if match else default



def load_recent_sew_events(
    filepath: str = "insights/sew_events.log",
    limit: int = 5,
) -> list[dict[str, str]]:
    """Presentation-only reader for persisted SEW lifecycle events."""
    path = Path(filepath)
    if not path.exists():
        return []

    events = []

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []

    for line in reversed(lines):
        parts = [part.strip() for part in line.split(" | ", 5)]
        if len(parts) != 6:
            continue

        utc_ts, kst_ts, system, transition, event_type, reason = parts

        if system != "DEADMAN":
            continue

        events.append({
            "timestamp_utc": utc_ts,
            "timestamp_kst": kst_ts,
            "transition": transition,
            "event_type": event_type,
            "reason": reason,
        })

        if len(events) >= limit:
            break

    return events



def risk_monitor_ui(text, latest=False):
    """Display persisted report signals only; never calculate risk states."""
    def clean(s):
        return s.replace('**', '').replace('*', '').replace('\\_', '_').strip()

    def section(title):
        headings = list(re.finditer(r'^\s*(#{1,6})\s+(.+)$', text, re.M))
        for i, h in enumerate(headings):
            if title.lower() in h[2].lower():
                end = next((n.start() for n in headings[i+1:]
                            if len(n[1]) <= len(h[1])), len(text))
                return text[h.end():end]
        return ''

    def value(block, label):
        for line in block.splitlines():
            line = clean(line).lstrip('- ').strip()
            if line.lower().startswith(label.lower()):
                return line[len(label):].lstrip(': ').strip() or 'Unavailable'
        return 'Unavailable'

    def items(values):
        return '<ul>' + ''.join(
            '<li>' + html.escape(v) + '</li>' for v in values
        ) + '</ul>'

    def panel(title, body, anchor):
        return (
            '<section class="panel" id="' + anchor + '">'
            '<div class="section-kicker">RISK MONITORING</div><h2>'
            + html.escape(title) + '</h2>' + body + '</section>'
        )

    corr_parts, alerts = [], []
    for title, label in [
        ('6.5) Correlation Break Monitor', 'Market correlation'),
        ('6.6) Sector Correlation Break Monitor', 'Sector divergence'),
    ]:
        block = section(title)
        active = re.search(
            r'^\s*Correlation Break Detected\s*:', block, re.M | re.I
        )
        normal = re.search(
            r'No significant (?:sector )?correlation break detected',
            block, re.I
        )
        if active:
            signals = []
            for line in block[active.end():].splitlines():
                if not line.strip():
                    if signals:
                        break
                    continue
                if not line.lstrip().startswith('- '):
                    break
                signals.append(clean(line).lstrip('- ').strip())
            signals = signals or ['Break detected; details unavailable']
            alerts.extend(label + ': ' + s for s in signals)
            body = items(signals)
        elif normal:
            body = '<p>No active alerts</p>'
        else:
            body = '<p>Data unavailable / unrecognized report format</p>'
        corr_parts.append('<h3>' + label + '</h3>' + body)

    corr = panel(
        'Correlation & Divergence',
        ''.join(corr_parts),
        'correlation-divergence',
    )

    summary = ''
    if alerts:
        chips = []
        for alert in alerts:
            category, separator, signal = alert.partition(': ')
            if not separator:
                signal = alert
                category = 'Correlation break'
            chips.append(
                '<span class="tape-break-chip" title="'
                + html.escape(category, quote=True)
                + '"><span class="tape-break-dot" aria-hidden="true"></span>'
                + html.escape(signal) + '</span>'
            )
        summary = """
        <style>
          .tape-break-wrap {
            margin-top: 16px;
            padding-top: 13px;
            border-top: 1px solid rgba(148,163,184,.18);
          }
          .tape-break-label {
            font-size: 10px;
            font-weight: 700;
            letter-spacing: .09em;
            opacity: .7;
            margin-bottom: 9px;
          }
          .tape-break-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }
          .tape-break-chip {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            max-width: 100%;
            box-sizing: border-box;
            padding: 7px 11px;
            border-radius: 11px;
            border: 1px solid rgba(232,143,162,.25);
            background: rgba(232,143,162,.10);
            color: #f2b1bd;
            font-size: 12px;
            font-weight: 600;
            line-height: 1.5;
            overflow-wrap: anywhere;
          }
          .tape-break-dot {
            width: 5px;
            height: 5px;
            flex: 0 0 5px;
            border-radius: 50%;
            background: currentColor;
          }
        </style>
        <div class="tape-break-wrap">
          <div class="tape-break-label">CORRELATION BREAK</div>
          <div class="tape-break-chips">
        """ + ''.join(chips) + '</div></div>'

    geo = section('7.2) Geopolitical Early Warning Monitor')
    labels = [
        'Geo Stress Score (z-composite)', 'Coverage', '3D Avg Score',
        'Geo Momentum', 'Closest Historical Match', 'Cosine Similarity Score',
        'Similarity Signal', 'Missing/Skipped',
    ]

    def geo_value(label):
        raw = value(geo, label + ':')
        pattern = None
        if label == 'Geo Momentum':
            pattern = r'^(.*?)\s*\(Status:\s*([^)]+)\)\s*$'
        elif label == 'Geo Stress Score (z-composite)':
            pattern = r'^(.*?)\s*\(Level:\s*([^)]+)\)\s*$'
        match = re.match(pattern, raw, re.I) if pattern else None
        if not match:
            return html.escape(raw)
        number, state = match.groups()
        state = state.strip()
        tone = {
            'RISING': 'rose',
            'FALLING': 'mint',
            'DECLINING': 'mint',
            'NORMAL': 'yellow',
        }.get(state.upper(), 'neutral')
        return (
            '<span class="geo-number">' + html.escape(number.strip())
            + '</span> <span class="geo-pill geo-' + tone + '">'
            + html.escape(state) + '</span>'
        )

    rows = ''.join(
        '<div><span>' + html.escape(
            'Stress Score' if label == 'Geo Stress Score (z-composite)'
            else label
        ) + '</span><strong>' + geo_value(label) + '</strong></div>'
        for label in labels
    )
    drivers = []
    collecting = False
    for line in geo.splitlines():
        if 'Top Drivers:' in clean(line):
            collecting = True
            continue
        if collecting:
            if not line.strip():
                continue
            if not re.match(r'^\s{2,}-\s', line):
                break
            drivers.append(clean(line).lstrip('- ').strip())


    driver_cards = []
    for driver in drivers:
        name, separator, detail = driver.partition(':')
        contribution = re.search(
            r'\bcontrib=([+-]?\d+(?:\.\d+)?)', detail
        )
        if not separator or not contribution:
            driver_cards.append(
                '<div class="geo-driver-card">'
                + html.escape(driver) + '</div>'
            )
            continue
        amount = contribution.group(1)
        direction = float(amount)
        tone = 'rose' if direction > 0 else 'mint' if direction < 0 else 'neutral'
        label = (
            'Adds to stress' if direction > 0
            else 'Offsets stress' if direction < 0
            else 'Neutral contribution'
        )
        driver_cards.append(
            '<article class="geo-driver-card">'
            '<div class="geo-driver-top"><strong>'
            + html.escape(name.strip().replace('_', ' '))
            + '</strong><span class="geo-pill geo-' + tone + '">'
            + html.escape(amount) + '</span></div>'
            '<small>' + label + '</small></article>'
        )

    geo_styles = """
    <style>
      #geopolitical-stress .pm-state-list > div {
        gap: 12px;
        flex-wrap: wrap;
      }
      #geopolitical-stress .pm-state-list strong {
        overflow-wrap: anywhere;
      }
      #geopolitical-stress .geo-number {
        font-variant-numeric: tabular-nums;
        margin-right: 6px;
      }
      #geopolitical-stress .geo-pill {
        display: inline-block;
        padding: 4px 9px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
        border: 1px solid transparent;
      }
      #geopolitical-stress .geo-rose {
        color: #f2b1bd;
        background: rgba(232,143,162,.14);
        border-color: rgba(232,143,162,.24);
      }
      #geopolitical-stress .geo-mint {
        color: #9bd8c3;
        background: rgba(115,191,165,.14);
        border-color: rgba(115,191,165,.24);
      }
      #geopolitical-stress .geo-yellow {
        color: #efd48c;
        background: rgba(225,191,103,.14);
        border-color: rgba(225,191,103,.24);
      }
      #geopolitical-stress .geo-neutral {
        color: inherit;
        background: rgba(148,163,184,.12);
        border-color: rgba(148,163,184,.22);
      }
      #geopolitical-stress .geo-driver-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 185px), 1fr));
        gap: 9px;
        margin: 12px 0;
      }
      #geopolitical-stress .geo-driver-card {
        min-width: 0;
        padding: 12px;
        border-radius: 13px;
        border: 1px solid rgba(148,163,184,.2);
        background: rgba(148,163,184,.05);
        overflow-wrap: anywhere;
      }
      #geopolitical-stress .geo-driver-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
      }
      #geopolitical-stress .geo-driver-top strong {
        font-size: 12px;
        letter-spacing: .025em;
      }
      #geopolitical-stress .geo-driver-card small {
        display: block;
        margin-top: 7px;
        font-size: 10px;
        opacity: .7;
      }
      #geopolitical-stress .geo-driver-details {
        margin-top: 12px;
        font-size: 12px;
      }
      #geopolitical-stress .geo-driver-details summary {
        cursor: pointer;
        padding: 5px 0;
      }
      #geopolitical-stress .geo-driver-details li {
        margin: 8px 0;
        line-height: 1.6;
        overflow-wrap: anywhere;
      }
      #geopolitical-stress .geo-driver-details summary:focus-visible {
        outline: 2px solid currentColor;
        outline-offset: 4px;
      }
    </style>
    """
    driver_html = (
        '<div class="geo-driver-grid">' + ''.join(driver_cards) + '</div>'
        '<details class="geo-driver-details">'
        '<summary>View Driver Calculation Details</summary>'
        + items(drivers) + '</details>'
        if drivers else '<p>Data unavailable</p>'
    )
    geo_card = panel(
        'Geopolitical Stress',
        geo_styles + '<div class="pm-state-list">' + rows
        + '</div><h3>Top Drivers</h3>' + driver_html,
        'geopolitical-stress',
    )

    etf_block = section('Country ETF Risk Monitor')
    etfs = []
    for m in re.finditer(
        r'^###\s+([A-Z0-9.^=-]+)\s*\n(.*?)(?=^###\s|\Z)',
        etf_block, re.M | re.S
    ):
        symbol, block = m.groups()
        crash = value(block, 'Crash?')
        level = value(block, 'Risk Level:')

        def z(label):
            raw = value(block, label)
            try:
                return format(float(raw), '+.2f')
            except ValueError:
                return raw

        active = crash.upper() == 'TRUE' or level.upper() == 'EXTREME'
        complete = (
            crash.upper() in ('TRUE', 'FALSE') and level != 'Unavailable'
        )
        detail = (
            'Crash flag: ' + crash
            + ' · 1D Z ' + z('Z-Score (1d):')
            + ' · 5D Z ' + z('Z-Score (5d):')
        )
        tone = (
            "alert" if active else
            "normal" if complete and level.upper() == "NORMAL"
            else "neutral"
        )
        flag = {
            "TRUE": "Crash flag · Triggered",
            "FALSE": "Crash flag · Not triggered",
        }.get(crash.upper(), "Crash flag · Unavailable")
        rendered = (
            '<article class="etf-pretty-card etf-tone-' + tone + '">'
            '<div class="etf-pretty-top">'
            '<span class="etf-pretty-symbol">' + html.escape(symbol) + '</span>'
            '<span class="etf-pretty-badge">' + html.escape(level) + '</span>'
            '</div>'
            '<div class="etf-pretty-flag">' + html.escape(flag) + '</div>'
            '<div class="etf-pretty-chips">'
            '<span><small>1D Z</small><b>' + html.escape(z('Z-Score (1d):'))
            + '</b></span>'
            '<span><small>5D Z</small><b>' + html.escape(z('Z-Score (5d):'))
            + '</b></span>'
            '</div></article>'
        )
        etfs.append((active, complete, rendered))


    styles = """
    <style>
      #etf-risk-monitor {
        --etf-alert: #f2b1bd;
        --etf-mint: #9bd8c3;
      }
      #etf-risk-monitor .etf-pretty-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr));
        gap: 12px;
        margin: 14px 0 18px;
      }
      #etf-risk-monitor .etf-pretty-card {
        min-width: 0;
        padding: 18px;
        border: 1px solid rgba(148,163,184,.22);
        border-radius: 18px;
        background: rgba(148,163,184,.06);
      }
      #etf-risk-monitor .etf-tone-alert {
        border-color: rgba(232,143,162,.38);
        background: linear-gradient(135deg,rgba(232,143,162,.14),rgba(180,150,220,.06));
      }
      #etf-risk-monitor .etf-tone-normal {
        border-color: rgba(115,191,165,.24);
        background: rgba(115,191,165,.06);
      }
      #etf-risk-monitor .etf-pretty-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
      }
      #etf-risk-monitor .etf-pretty-symbol {
        font-size: 21px;
        font-weight: 750;
        letter-spacing: .035em;
      }
      #etf-risk-monitor .etf-pretty-badge {
        padding: 5px 10px;
        border-radius: 999px;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: .06em;
        background: rgba(148,163,184,.14);
      }
      #etf-risk-monitor .etf-tone-alert .etf-pretty-badge {
        color: var(--etf-alert);
        background: rgba(232,143,162,.14);
      }
      #etf-risk-monitor .etf-tone-normal .etf-pretty-badge {
        color: var(--etf-mint);
        background: rgba(115,191,165,.14);
      }
      #etf-risk-monitor .etf-pretty-flag {
        margin-top: 10px;
        font-size: 12px;
        opacity: .8;
      }
      #etf-risk-monitor .etf-pretty-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 16px;
      }
      #etf-risk-monitor .etf-pretty-chips > span {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        padding: 7px 11px;
        border: 1px solid rgba(148,163,184,.14);
        border-radius: 10px;
        background: rgba(148,163,184,.08);
        font-variant-numeric: tabular-nums;
      }
      #etf-risk-monitor .etf-pretty-chips small {
        font-size: 10px;
        opacity: .65;
      }
      #etf-risk-monitor .etf-pretty-chips b {
        font-size: 13px;
      }
      #etf-risk-monitor .etf-pretty-caption {
        font-size: 11px;
        letter-spacing: .09em;
        opacity: .7;
      }
      #etf-risk-monitor .etf-pretty-details {
        margin-top: 8px;
        border-top: 1px solid rgba(148,163,184,.18);
        padding-top: 14px;
      }
      #etf-risk-monitor .etf-pretty-details > summary {
        cursor: pointer;
        font-size: 12px;
        padding: 6px 0;
      }
      #etf-risk-monitor .etf-pretty-details > summary:focus-visible {
        outline: 2px solid currentColor;
        outline-offset: 4px;
        border-radius: 4px;
      }

      /* Compact ETF cards */
      #etf-risk-monitor .etf-pretty-grid {
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 180px), 220px));
        gap: 9px;
        margin: 10px 0 14px;
      }
      #etf-risk-monitor .etf-pretty-card {
        padding: 12px;
        border-radius: 13px;
      }
      #etf-risk-monitor .etf-pretty-symbol {
        font-size: 17px;
      }
      #etf-risk-monitor .etf-pretty-badge {
        padding: 4px 8px;
        font-size: 9px;
      }
      #etf-risk-monitor .etf-pretty-flag {
        margin-top: 7px;
        font-size: 11px;
      }
      #etf-risk-monitor .etf-pretty-chips {
        gap: 6px;
        margin-top: 10px;
      }
      #etf-risk-monitor .etf-pretty-chips > span {
        gap: 7px;
        padding: 5px 8px;
        border-radius: 8px;
      }
      #etf-risk-monitor .etf-pretty-chips b {
        font-size: 12px;
      }
    </style>
    """
    active_rows = [row[2] for row in etfs if row[0]]
    if active_rows:
        active_html = (
            '<div class="etf-pretty-caption">ACTIVE FLAGS · '
            + str(len(active_rows)) + '</div>'
            '<div class="etf-pretty-grid">'
            + ''.join(active_rows) + '</div>'
        )
    else:
        active_html = (
            '<p>No active crash / extreme flags</p>'
            if etfs and all(row[1] for row in etfs)
            else '<p>Data unavailable / incomplete ETF report</p>'
        )
    if etfs and not all(row[1] for row in etfs):
        active_html += '<p>Some ETF fields are unavailable.</p>'
    if etfs:
        active_html += (
            '<details class="etf-pretty-details">'
            '<summary>View All ETF Risk Details · '
            + str(len(etfs)) + ' ETFs</summary>'
            '<div class="etf-pretty-grid">'
            + ''.join(row[2] for row in etfs)
            + '</div></details>'
        )
    etf_card = panel(
        'ETF Risk Monitor', styles + active_html, 'etf-risk-monitor'
    )
    return summary, corr, geo_card + etf_card


def parse_diagnostics_v1(text: str) -> dict[str, str]:
    """
    Presentation-only Diagnostics V1 contract.

    Existing diagnostic outputs are parsed and reorganized for observability.
    This function must not calculate new market states, risk signals,
    exposure decisions, or strategy classifications.
    """
    return {
        "date": diag_match(
            text,
            r"\*\*Date:\*\*\s*([^\n]+)",
        ),
        "data_as_of": diag_match(
            text,
            r"\*\*Data as of:\*\*\s*([^\n]+)",
        ),
        "sew": diag_match(
            text,
            r"\*\*SEW:\*\*\s*([^\n]+)",
        ),
        "f13_risk_budget": diag_match(
            text,
            r"\*\*Risk Budget \(0~100\):\*\*\s*\*\*(\d+(?:\.\d+)?)\*\*",
        ),
        "f15_exposure": diag_match(
            text,
            r"\*\*📊 Recommended Exposure:\*\*\s*\*\*(\d+(?:\.\d+)?%)\*\*",
        ),
        "f15_brake_drivers": diag_match(
            text,
            r"\*\*Brake Drivers:\*\*\s*([^\n]+)",
        ),
        # F13 measured decision contributions already emitted
        # by the canonical diagnostics report.
        "f13_macro_tilt": diag_match(
            text,
            r"\*\*Macro Tilt:\*\*\s*([+-]?\d+)",
        ),
        "f13_flow_continuity_tilt": diag_match(
            text,
            r"\*\*Flow Continuity:\*\*[^\n]*"
            r"tilt=([+-]?\d+)",
        ),
        "f13_flow_continuity_role": diag_match(
            text,
            r"\*\*Flow Continuity:\*\*[^\n]*\(([^,()]+),\s*tilt=",
        ),
        "f13_flow_regime_tilt": diag_match(
            text,
            r"\*\*Flow Regime Tilt:\*\*\s*([+-]?\d+)",
        ),
        "f13_flow_gamma_tilt": diag_match(
            text,
            r"Flow-Gamma Tilt:\s*([+-]?\d+)",
        ),
        "f13_phase_cap": diag_match(
            text,
            r"\*\*Operational Phase:\*\*[^\n]*"
            r"\(Cap:\s*([0-9]+(?:\.[0-9]+)?)\)",
        ),

        # Existing positioning value. Its F13 contribution is NOT
        # reconstructed here; the UI contract test below validates the
        # production rule before presentation.
        "f13_positioning_z": diag_match(
            text,
            r"\*\*Positioning \(POS_Z\):\*\*\s*([0-9.+-]+)",
        ),

        "flow_state": diag_match(
            text,
            r"\*\*Raw Flow State:\*\*\s*\*\*(.+?)\*\*",
        ),
        "flow_delta": diag_match(
            text,
            r"\*\*Flow Delta:\*\*\s*([^\n]+)",
        ),
        "positioning_z": diag_match(
            text,
            r"\*\*Positioning \(POS_Z\):\*\*\s*([0-9.+-]+)",
        ),
        "gamma_state": diag_match(
            text,
            r"\*\*Pseudo Gamma State:\*\*\s*([^\n]+)",
        ),
        "geo_score": diag_match(
            text,
            r"\*\*Geo Stress Score \(z-composite\):\*\*\s*\*\*([^*]+)\*\*",
        ),
        "geo_level": diag_match(
            text,
            r"Geo Stress Score \(z-composite\):.*?Level:\s*([^)*]+)",
        ),
        "hy_oas": diag_match(
            text,
            r"\*\*HY_OAS level:\*\*\s*([^\n]+)",
        ),
        "hy_oas_level": diag_match(
            text,
            r"\*\*HY_OAS level:\*\*\s*([0-9.]+%)",
        ),
        "hy_oas_state": diag_match(
            text,
            r"\*\*HY_OAS level:\*\*[^\n]*?\*\*([A-Z_]+)\s*\(",
        ),
        "us10y": diag_match(
            text,
            r"\*\*미국 10년물 금리\*\*:\s*([^\n]+)",
        ),
        "dxy": diag_match(
            text,
            r"\*\*달러 인덱스\*\*:\s*([^\n]+)",
        ),
        "wti": diag_match(
            text,
            r"\*\*WTI 유가\*\*:\s*([^\n]+)",
        ),
        "vix": diag_match(
            text,
            r"\*\*변동성 지수 \(VIX\)\*\*:\s*([^\n]+)",
        ),

        # Market / Engine Overview — persisted diagnostics only.
        "real_rate": diag_match(
            text,
            r"Real Rates\):\*\*\s*value=([^/]+/\s*level=[^/]+)",
        ),
        "curve_2s10s": diag_match(
            text,
            r"\*\*2s10s[^:]*:\*\*\s*([^\n]+)",
        ),
        "usdk_rw": diag_match(
            text,
            r"원/달러\(USDKRW\).*?\*\*\(([^)]+)\)\*\*",
        ),
        "net_liq": diag_match(
            text,
            r"\*\*NET_LIQ level:\*\*\s*([^\n]+)",
        ),
        "tga": diag_match(
            text,
            r"\*\*TGA level:\*\*\s*([^\n]+)",
        ),
        "rrp": diag_match(
            text,
            r"\*\*RRP level:\*\*\s*([^\n]+)",
        ),
        "liq_direction": diag_match(
            text,
            r"### 🧰 4\) Fed Plumbing Filter[\s\S]*?"
            r"\*\*방향\(전일 대비\):\*\*\s*"
            r"(TGA\([^)]+\)\s*/\s*RRP\([^)]+\)\s*/\s*NET_LIQ\([^)]+\))",
        ),
        "tga_direction": diag_match(
            text,
            r"### 🧰 4\) Fed Plumbing Filter[\s\S]*?"
            r"\*\*방향\(전일 대비\):\*\*\s*TGA\(([^)]+)\)",
        ),
        "rrp_direction": diag_match(
            text,
            r"### 🧰 4\) Fed Plumbing Filter[\s\S]*?"
            r"\*\*방향\(전일 대비\):\*\*[^\n]*RRP\(([^)]+)\)",
        ),
        "net_liq_direction": diag_match(
            text,
            r"### 🧰 4\) Fed Plumbing Filter[\s\S]*?"
            r"\*\*방향\(전일 대비\):\*\*[^\n]*NET_LIQ\(([^)]+)\)",
        ),
        "hyg": diag_match(
            text,
            r"\*\*HYG:\*\*\s*([^\n]+)",
        ),
        "lqd": diag_match(
            text,
            r"\*\*LQD:\*\*\s*([^\n]+)",
        ),
        "hy_direction": diag_match(
            text,
            r"HY_OAS\(([^)]+\)\s*/\s*[+-]?[0-9.]+%)",
        ),

        # Execution / control outputs already emitted by Diagnostics.
        "market_regime": diag_match(
            text,
            r"\*\*Operational Phase:\*\*\s*(?:\*\*)?(.+?)(?:\*\*)?\s*\(Cap:",
        ),
        "macro_narrative": diag_match(
            text,
            r"\*\*Structural Regime:\*\*\s*(?:\*\*)?([^*\n]+?)(?:\*\*)?\s*$",
        ),
        "deadman": diag_match(
            text,
            r"\*\*\[15번 Hard Deadman\]:\*\*\s*([^\n]+)",
        ),
        "final_action": diag_match(
            text,
            r"\*\*Final Action:\*\*\s*\*\*(.+?)\*\*",
        ),
        "final_exposure": diag_match(
            text,
            r"\*\*Final Exposure:\*\*\s*\*\*(.+?)\*\*",
        ),

        # Observation-only shadow states.
        "growth_shadow": diag_match(
            text,
            r"### 12\.5\) Growth Sustainability Filter \[SHADOW\][\s\S]*?"
            r"- \*\*Label:\*\*\s*([^\n]+)",
        ),
        "flow_auth_shadow": diag_match(
            text,
            r"### 12\.6\) Flow Authenticity Filter \[SHADOW\][\s\S]*?"
            r"- \*\*Label:\*\*\s*([^\n]+)",
        ),
        "breadth_shadow": diag_match(
            text,
            r"### 12\.7\) Leadership Breadth Filter \[SHADOW\][\s\S]*?"
            r"- \*\*Label:\*\*\s*([^\n]+)",
        ),
        "positioning_shadow": diag_match(
            text,
            r"### 12\.8\) Positioning Stress Filter \[SHADOW\][\s\S]*?"
            r"- \*\*Label:\*\*\s*([^\n]+)",
        ),

        # Existing F18.5 portfolio composition.
        # Tactical Reserve is contained within Cash & Hedge; never additive.
        "cash_hedge": diag_match(
            text,
            r"\| \*\*Cash & Hedge\*\* \| - \| - \| "
            r"\*\*([0-9]+(?:\.[0-9]+)?%)\*\*",
        ),
        "strategic_cash": diag_match(
            text,
            r"\*\*Strategic Cash \(15\):\*\*\s*"
            r"([0-9]+(?:\.[0-9]+)?%)",
        ),
        "tactical_reserve": diag_match(
            text,
            r"\*\*Tactical Reserve \(Cap / Unallocated\):\*\*\s*"
            r"([0-9]+(?:\.[0-9]+)?%)",
        ),
    }


def diag_change_parts(value: str) -> dict[str, str]:
    """
    Presentation-only decomposition of an existing diagnostics change string.

    Example:
      14.320 (-5.79% vs 15.200)
      -> current=14.320, previous=15.200, change=-5.79%, direction=down

    No market state or strategy signal is created here.
    """
    match = re.match(
        r"^\s*([+-]?\d+(?:\.\d+)?)\s*"
        r"\(([+-]?\d+(?:\.\d+)?%)\s+vs\s+"
        r"([+-]?\d+(?:\.\d+)?)\)\s*$",
        str(value),
    )

    if not match:
        return {
            "current": str(value),
            "previous": "N/A",
            "change": "",
            "direction": "flat",
            "arrow": "→",
        }

    current, change, previous = match.groups()
    change_number = float(change.rstrip("%"))

    if change_number > 0:
        direction = "up"
        arrow = "↑"
    elif change_number < 0:
        direction = "down"
        arrow = "↓"
    else:
        direction = "flat"
        arrow = "→"

    return {
        "current": current,
        "previous": previous,
        "change": change,
        "direction": direction,
        "arrow": arrow,
    }


def diag_semantic_class(value: str) -> str:
    """
    Map explicit existing diagnostic language to presentation color only.

    This does not infer a new strategy state from numeric thresholds.
    """
    upper = str(value).upper()

    adverse_terms = (
        "TRIGGERED",
        "BREACH",
        "EXTREME",
        "CRITICAL",
    )
    watch_terms = (
        "ELEVATED",
        "WATCH",
        "TRANSITION",
        "STRAIN",
        "CROWDED",
        "SQUEEZE_RISK",
        "EARLY_ROTATION",
    )
    supportive_terms = (
        "PASS",
        "STABLE",
        "BUILDING",
        "COOL",
        "NORMAL",
    )

    if any(term in upper for term in adverse_terms):
        return "diag-semantic-red"
    if any(term in upper for term in watch_terms):
        return "diag-semantic-amber"
    if any(term in upper for term in supportive_terms):
        return "diag-semantic-green"

    return "diag-semantic-neutral"

def esc(value: object) -> str:
    return html.escape(str(value))



def target_weight_comparison(text, report_date):
    """Compare persisted target weights; never infer executed trades."""
    from decimal import Decimal, InvalidOperation

    def number(raw):
        raw = str(raw).strip()
        if not re.fullmatch(r'\d+(?:\.\d+)?%', raw):
            return None
        try:
            n = Decimal(raw[:-1])
            return n if 0 <= n <= 100 else None
        except InvalidOperation:
            return None

    def snapshot(raw):
        block = section(raw, 0, "PORTFOLIO ALLOCATION")
        rows = parse_allocation_rows(block)
        totals = {
            label: number(field(block, label))
            for label in ("Allocated Equity", "Cash", "Tactical Reserve")
        }
        weights, names = {}, {}
        for row in rows:
            key = row["sector"].strip().casefold()
            n = number(row["weight"])
            if not key or key in weights or n is None:
                return None
            weights[key] = n
            names[key] = row["sector"]
        equity, cash = totals["Allocated Equity"], totals["Cash"]
        if equity is None or cash is None:
            return None
        # Allow only the rounding implied by one-decimal persisted weights.
        tolerance = Decimal("0.05") * (len(rows) + 1)
        if abs(sum(weights.values(), Decimal(0)) - equity) > tolerance:
            return None
        if abs(equity + cash - 100) > Decimal("0.1"):
            return None
        return weights, names, totals

    candidates = sorted(
        path for path in REPORTS_DIR.glob("daily_report_????-??-??.md")
        if path.stem.removeprefix("daily_report_") < report_date
    )
    previous_path = candidates[-1] if candidates else None
    previous_date = (
        previous_path.stem.removeprefix("daily_report_")
        if previous_path else None
    )
    current = snapshot(text)
    previous = None
    if previous_path:
        raw = previous_path.read_text(encoding="utf-8")
        if metadata(raw, "Date") == previous_date:
            previous = snapshot(raw)
    ready = current is not None and previous is not None

    def badge(name, total=False):
        if not ready:
            return '<span class="target-delta target-flat">N/A</span>'
        if total:
            now = current[2].get(name)
            old = previous[2].get(name)
        else:
            key = name.strip().casefold()
            now = current[0].get(key, Decimal(0))
            old = previous[0].get(key, Decimal(0))
        if now is None or old is None:
            return '<span class="target-delta target-flat">N/A</span>'
        delta = now - old
        tone = "up" if delta > 0 else "down" if delta < 0 else "flat"
        label = f"{delta:+.1f} pp" if delta else "—"
        if not total:
            if old == 0 and now > 0:
                label += " · NEW"
            elif old > 0 and now == 0:
                label += " · EXIT"
        return (
            '<span class="target-delta target-' + tone
            + '" title="' + html.escape(
                f"{old:.1f}% → {now:.1f}% · target weights", quote=True
            ) + '">' + label + '</span>'
        )

    exits = []
    if ready:
        for key, weight in previous[0].items():
            if weight > 0 and current[0].get(key, Decimal(0)) == 0:
                exits.append(previous[1][key])

    caption = (
        "Target weight change · vs " + previous_date
        if previous_date else "Target weight change · no previous report"
    )
    if previous_date and not ready:
        caption += " · comparison unavailable"
    caption += " · pp = percentage points · not executed trades"

    style = """
    <style>
      .pm-target-portfolio .target-comparison-note {
        font-size:10px; opacity:.7; line-height:1.6; margin:0 0 12px;
      }
      .pm-target-portfolio .target-delta {
        display:inline-block; padding:4px 7px; border-radius:9px;
        font-size:10px; font-weight:650; line-height:1.5;
        font-variant-numeric:tabular-nums; white-space:nowrap;
      }
      .pm-target-portfolio .target-up {
        color:#9bd8c3; background:rgba(115,191,165,.13);
      }
      .pm-target-portfolio .target-down {
        color:#f2b1bd; background:rgba(232,143,162,.13);
      }
      .pm-target-portfolio .target-flat {
        color:inherit; background:rgba(148,163,184,.09); opacity:.7;
      }
      .pm-target-portfolio .pm-portfolio-row {
        grid-template-columns:1.3fr .55fr .95fr .8fr .9fr 1.1fr;
      }
      .pm-target-portfolio .pm-portfolio-row > * {
        min-width:0; overflow-wrap:anywhere;
      }
      .pm-target-portfolio .pm-target-summary strong .target-delta {
        margin-left:6px;
      }
      @media(max-width:760px) {
        .pm-target-portfolio .pm-portfolio-row {
          grid-template-columns:minmax(0,1fr) .55fr .95fr;
        }
        .pm-target-portfolio .pm-portfolio-row > :nth-child(n+4) {
          display:none;
        }
      }
    </style>
    """
    note = style + '<p class="target-comparison-note">' + html.escape(caption) + '</p>'
    return badge, exits, note


def build(
    source: Path | None = None,
    output_path: Path | None = None,
    build_diagnostics: bool = True,
) -> None:
    """
    Build one PM view from an already-persisted daily report artifact.

    Historical rendering reads the stored report for that date.
    It must not recalculate Production signals or engine state.
    """
    if source is None:
        source = latest_pm_report()

    if output_path is None:
        output_path = SITE_DIR / "index.html"

    text = source.read_text(encoding="utf-8")

    report_date = source.stem.removeprefix("daily_report_")
    data_as_of = metadata(text, "Data as of")

    stance = top_value(text, "PORTFOLIO STANCE")
    regime = top_value(text, "REGIME")
    conviction = top_value(text, "CONVICTION")

    # PM Contract V2
    # Persisted canonical F13 -> F15 -> F18 outputs only.
    # No production state is recalculated in the renderer.
    decision_path = section(text, 1, "DECISION PATH")

    strategic_risk_budget = field(
        decision_path,
        "Strategic Risk Budget",
    )
    recommended_exposure = field(
        decision_path,
        "Recommended Exposure",
    )
    exposure_control = field(
        decision_path,
        "Exposure Control",
    )
    macro_allocation_profile = field(
        decision_path,
        "Macro Allocation",
    )

    executive = section(text, 0, "EXECUTIVE VIEW")
    market = section(text, 0, "MARKET STATE")
    cross_asset = section(text, 0, "CROSS-ASSET CONFIRMATION")
    leadership = section(text, 0, "LEADERSHIP & PARTICIPATION")
    allocation_context = section(text, 0, "ALLOCATION CONTEXT")
    allocation = section(text, 0, "PORTFOLIO ALLOCATION")
    execution = section(text, 0, "EXECUTION")

    risk = section(text, 0, "ACTIVE CONSTRAINTS")
    if not risk:
        risk = section(text, 0, "RISK & CONSTRAINTS")

    rationale = section(text, 0, "DECISION RATIONALE")

    executive_summary = first_prose_line(executive)

    macro_narrative = field(executive, "Macro Narrative")
    tactical_signal = field(executive, "Tactical Signal")

    # PM Contract V2 — canonical 1~19 state inventory.
    macro_state_narrative = field(market, "Macro Narrative")
    policy_bias = field(market, "Policy Bias")
    financial_conditions = field(market, "Financial Conditions")
    real_rate = field(market, "Real Rate")
    liquidity = field(market, "Liquidity")
    liquidity_level = field(market, "Liquidity Level")
    structure = field(market, "Structure")
    growth_sustainability = field(market, "Growth Sustainability")

    flow = field(market, "Institutional Flow")
    if flow == "N/A":
        # V1 historical compatibility.
        flow = field(market, "Flow")

    flow_authenticity = field(market, "Flow Authenticity")
    participation_quality = field(market, "Participation Quality")
    participation_mode = field(market, "Participation Mode")
    leadership_state = field(market, "Leadership")
    positioning_state = field(market, "Positioning")
    squeeze_risk = field(market, "Squeeze Risk")
    vol_structure = field(market, "Vol Structure")

    drift = field(market, "Drift")
    positioning = field(market, "Positioning Z")
    credit = field(market, "Credit")
    credit_structure = field(market, "Credit Structure")
    dealer_gamma = field(market, "Dealer Gamma")

    us10y = field(cross_asset, "US10Y Yield")
    usd = field(cross_asset, "USD")
    oil = field(cross_asset, "Oil")
    volatility = field(cross_asset, "Volatility")
    hy_oas = field(cross_asset, "HY OAS")

    coverage = field(leadership, "Coverage")
    sectors = parse_sector_rows(leadership)
    breadth_rows = parse_breadth_rows(leadership)

    # ---------------------------------------------------------
    # TODAY'S MARKET
    # Presentation-only synthesis of persisted canonical states.
    # No market state, score, exposure, or portfolio rule is recalculated.
    # ---------------------------------------------------------
    def _state(value):
        return str(value or "").strip().upper().replace("-", "_").replace(" ", "_")

    macro_key = _state(macro_state_narrative)
    policy_key = _state(policy_bias)
    liquidity_key = _state(liquidity)
    credit_key = _state(credit)
    positioning_key = _state(positioning_state)
    leadership_key = _state(leadership_state)
    vol_key = _state(vol_structure)

    pressure_parts = []

    if "INFLATION" in macro_key:
        pressure_parts.append("Inflation pressure")
    elif any(x in macro_key for x in ("GROWTH_SCARE", "GROWTH_STRESS", "RECESSION")):
        pressure_parts.append("Growth pressure")

    if any(x in liquidity_key for x in ("TIGHTEN", "DOWN", "DRAIN")):
        pressure_parts.append("tightening liquidity")

    if any(x in policy_key for x in ("TIGHTEN", "HAWKISH", "RESTRICT")):
        pressure_parts.append("restrictive policy")

    if pressure_parts:
        if len(pressure_parts) == 1:
            pressure_clause = pressure_parts[0]
        elif len(pressure_parts) == 2:
            pressure_clause = f"{pressure_parts[0]} and {pressure_parts[1]}"
        else:
            pressure_clause = (
                ", ".join(pressure_parts[:-1])
                + f" and {pressure_parts[-1]}"
            )
        market_sentence = f"{pressure_clause} favor defensive exposure"
    else:
        market_sentence = "Current macro conditions do not signal a dominant defensive pressure"

    if any(x in positioning_key for x in ("ELEVATED", "CROWDED", "EXTREME", "HEAT")):
        market_sentence += ", with elevated positioning adding restraint"

    offsets = []

    if any(x in credit_key for x in ("CALM", "NORMAL", "CONTAINED")):
        offsets.append("contained credit stress")

    if any(x in vol_key for x in ("NORMAL", "LOW", "CALM")):
        offsets.append("normal volatility")

    if any(x in leadership_key for x in ("BROAD", "EXPANDING")):
        offsets.append("broad leadership")

    if offsets:
        if len(offsets) == 1:
            offset_clause = offsets[0]
        elif len(offsets) == 2:
            offset_clause = f"{offsets[0]} and {offsets[1]}"
        else:
            offset_clause = (
                ", ".join(offsets[:-1])
                + f" and {offsets[-1]}"
            )

        market_sentence += f"; {offset_clause} temper the downside signal"

    market_sentence += "."

    growth_value_tilt = field(
        allocation_context, "Growth vs Value"
    )
    duration_tilt = field(
        allocation_context, "Duration Tilt"
    )
    cyclical_defensive = field(
        allocation_context, "Cyclical Defensive"
    )
    duration_factor = field(
        allocation_context, "Duration Factor"
    )
    inflation_factor = field(
        allocation_context, "Inflation Factor"
    )
    usd_factor = field(
        allocation_context, "USD Factor"
    )
    credit_factor = field(
        allocation_context, "Credit Factor"
    )
    regime_controller = field(
        allocation_context, "Regime Controller"
    )
    exposure_override = field(
        allocation_context, "Exposure Override"
    )

    exposure_ceiling = field(allocation, "Exposure Ceiling")
    allocated_equity = field(allocation, "Allocated Equity")
    tactical_reserve = field(allocation, "Tactical Reserve")
    cash_weight = field(allocation, "Cash")
    allocation_rows = parse_allocation_rows(allocation)

    # ACTIVE CONSTRAINTS — canonical controls only.
    # Legacy fields remain readable for historical V1 reports.
    inflation = field(risk, "Inflation")
    risk_liquidity = field(risk, "Liquidity")
    risk_positioning = field(risk, "Positioning Z")
    risk_credit = field(risk, "Credit")

    exposure_constraint = field(risk, "Exposure Control")
    constraint_squeeze = field(risk, "Squeeze Risk")
    constraint_vol_structure = field(risk, "Vol Structure")
    correlation_break = field(risk, "Correlation Break")
    sector_corr_break = field(risk, "Sector Corr Break")
    rank_control = field(risk, "Rank Control")
    geopolitical = field(risk, "Geopolitical")

    decision = field(rationale, "Decision")
    decision_exposure = field(rationale, "Exposure Ceiling")
    decision_signal = field(rationale, "Tactical Signal")
    decision_conviction = field(rationale, "Conviction")
    reasons = parse_rationale(rationale)

    def signed_number(value):
        try:
            return float(str(value).replace("%", "").replace("+", "").strip())
        except (TypeError, ValueError):
            return None

    positive_movers = [
        (signed_number(row.get("momentum")), i)
        for i, row in enumerate(sectors)
        if signed_number(row.get("momentum")) is not None
        and signed_number(row.get("momentum")) > 0
    ]
    mover_index = (
        max(positive_movers, key=lambda x: x[0])[1]
        if positive_movers
        else None
    )

    sector_parts = []
    for i, row in enumerate(sectors):
        badges = []

        if str(row.get("rank", "")).strip() == "1":
            badges.append('<span class="leadership-badge leader-badge">★ Leader</span>')

        if i == mover_index:
            badges.append('<span class="leadership-badge mover-badge">▲ Mover</span>')

        badge_html = " ".join(badges)

        sector_parts.append(
            f"""
            <div class="sector-row {'sector-highlight' if badges else ''}">
              <span class="rank">{esc(row['rank'])}</span>
              <span class="sector-name">{esc(row['sector'])} {badge_html}</span>
              <span class="sector-return">{esc(row['return'])}</span>
              <span class="sector-relative">{esc(row['relative'])} vs SPY</span>
              <span class="momentum">Rank Δ&nbsp;{esc(row['momentum'])}</span>
            </div>
            """
        )

    sector_html = "\n".join(sector_parts)

    if not sector_html:
        sector_html = """
        <div class="empty-state">
          No same-date sector observations available.
        </div>
        """

    positive_confirmations = [
        (signed_number(row.get("change")), i)
        for i, row in enumerate(breadth_rows)
        if signed_number(row.get("change")) is not None
        and signed_number(row.get("change")) > 0
    ]
    confirmation_index = (
        max(positive_confirmations, key=lambda x: x[0])[1]
        if positive_confirmations
        else None
    )

    breadth_parts = []
    for i, row in enumerate(breadth_rows):
        confirmation = (
            '<span class="leadership-badge confirmation-badge">★ Confirmation</span>'
            if i == confirmation_index
            else ""
        )

        breadth_parts.append(
            f"""
            <div class="breadth-row {'breadth-highlight' if i == confirmation_index else ''}">
              <span>{esc(row['label'])} {confirmation}</span>
              <strong>{esc(row['today'])}</strong>
              <span>Prev {esc(row['prev'])}</span>
              <span>Δ {esc(row['change'])}</span>
            </div>
            """
        )

    breadth_html = "\n".join(breadth_parts)

    if not breadth_html:
        breadth_html = """
        <div class="empty-state">
          No canonical breadth observations available.
        </div>
        """

    allocation_html = "\n".join(
        f"""
        <div class="allocation-row">
          <span>{esc(row['sector'])}</span>
          <strong>{esc(row['weight'])}</strong>
        </div>
        """
        for row in allocation_rows
    )

    if not allocation_html:
        allocation_html = """
        <div class="empty-state">
          No positive sector allocation.
        </div>
        """

    constraint_rows = []

    for raw in risk.splitlines():
        raw = raw.strip()

        if not raw or raw == "No active canonical constraint":
            continue

        match = re.match(r"^(.+?)\\s{2,}(.+)$", raw)

        if match:
            constraint_rows.append(
                (
                    match.group(1).strip(),
                    match.group(2).strip(),
                )
            )

    if constraint_rows:
        constraints_html = "\n".join(
            f"<div><span>{esc(label)}</span>"
            f"<strong>{esc(value)}</strong></div>"
            for label, value in constraint_rows
        )
    else:
        constraints_html = (
            '<div class="empty-state">'
            'No active canonical constraint'
            '</div>'
        )

    reasons_html = "\n".join(
        f"<li>{esc(reason)}</li>"
        for reason in reasons
    )

    if not reasons_html:
        reasons_html = "<li>No canonical tactical rationale available.</li>"

    # ---------------------------------------------------------
    # Report Date Navigator
    # ---------------------------------------------------------
    persisted_reports = sorted(
        REPORTS_DIR.glob("daily_report_????-??-??.md")
    )
    available_dates = [
        item.stem.removeprefix("daily_report_")
        for item in persisted_reports
    ]

    try:
        current_index = available_dates.index(report_date)
    except ValueError:
        current_index = -1

    previous_date = (
        available_dates[current_index - 1]
        if current_index > 0
        else None
    )
    next_date = (
        available_dates[current_index + 1]
        if current_index >= 0 and current_index < len(available_dates) - 1
        else None
    )

    is_latest_page = output_path == SITE_DIR / "index.html"
    latest_date = available_dates[-1] if available_dates else report_date

    # Historical PM pages live under _site/history/.
    # Resolve the canonical stylesheet relative to each rendered page.
    asset_href = (
        "assets/style.css"
        if is_latest_page
        else "../assets/style.css"
    )

    def report_href(target_date: str) -> str:
        if is_latest_page:
            if target_date == latest_date:
                return "index.html"
            return f"history/{target_date}.html"

        if target_date == latest_date:
            return "../index.html"
        return f"{target_date}.html"

    previous_href = report_href(previous_date) if previous_date else None
    next_href = report_href(next_date) if next_date else None

    previous_control = (
        f'<a class="report-nav-arrow" href="{esc(previous_href)}" '
        f'aria-label="Previous report">‹</a>'
        if previous_href
        else '<span class="report-nav-arrow disabled" '
             'aria-hidden="true">‹</span>'
    )

    next_control = (
        f'<a class="report-nav-arrow" href="{esc(next_href)}" '
        f'aria-label="Next report">›</a>'
        if next_href
        else '<span class="report-nav-arrow disabled" '
             'aria-hidden="true">›</span>'
    )

    # Date-specific diagnostics use the same presentation template.
    diagnostics = REPORTS_DIR / f"engine_diagnostics_{report_date}.md"
    diagnostics_output = (
        SITE_DIR / "diagnostics.html" if is_latest_page
        else output_path.parent / f"{report_date}-diagnostics.html"
    )
    diagnostics_href = diagnostics_output.name
    pm_return_href = output_path.name
    diagnostics_link = (
        f'<a class="diagnostics-destination" href="{esc(diagnostics_href)}">'
        'Engine Diagnostics <span>→</span></a>'
    )

    import json
    available_dates_json = json.dumps(available_dates)

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # Canonical site stylesheet.
    # _site is generated output; always rebuild CSS from the tracked source asset.
    css_source = ROOT / "assets" / "pm_site.css"
    if not css_source.exists():
        raise FileNotFoundError(f"Missing canonical PM site stylesheet: {css_source}")
    (ASSETS_DIR / "style.css").write_text(
        css_source.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    diagnostics_source = REPORTS_DIR / f"engine_diagnostics_{report_date}.md"
    diag_text = (
        diagnostics_source.read_text(encoding="utf-8")
        if diagnostics_source.exists()
        else ""
    )
    diag = parse_diagnostics_v1(diag_text)


    # Presentation-only semantic coloring. No numeric thresholds or new market states.
    def pm_semantic(value: object, domain: str = "general") -> str:
        upper = str(value).upper()

        if any(x in upper for x in ("TIGHTENING", "DRAINING", "INFLATION_PRESSURE",
                                    "RESTRICTIVE", "STRESS", "FRAGILE", "DEADMAN",
                                    "POSITIONING HEAT")):
            return "pm-red"

        if any(x in upper for x in ("WATCH", "TRANSITION", "EARLY TRACE", "MEDIUM",
                                    "LATE_CYCLE", "LATE-CYCLE", "ELEVATED")):
            return "pm-amber"

        if any(x in upper for x in ("EASY", "EASING", "SUPPORTIVE", "CALM",
                                    "REAL_ACCUMULATION", "BROAD", "IMPROVING")):
            return "pm-green"

        if any(x in upper for x in ("NORMAL", "BALANCED", "NEUTRAL", "ALIGNED", "PASS")):
            return "pm-neutral"

        return "pm-neutral"

    def pct_number(value: object) -> float:
        m = re.search(r"-?\d+(?:\.\d+)?", str(value))
        return float(m.group(0)) if m else 0.0

    # F13/F15/F18 attribution is read from persisted report text only.
    # Decision Path — presentation only; no engine calculation.
    f13_why = (
        f"{macro_state_narrative} regime sets the strategic risk allowance at "
        f"{strategic_risk_budget}; positioning Z {positioning} and {drift} are active constraints."
    )

    # Read persisted F15 brake driver directly from the report.
    f15_brake_driver = "Not exposed in persisted report"
    for _pattern in (
        r"(?im)^\s*(?:[-*]\s*)?F15 Brake Driver\s*:\s*(.+?)\s*$",
        r"(?im)^\s*(?:[-*]\s*)?Brake Driver\s*:\s*(.+?)\s*$",
        r"(?im)^\s*(?:[-*]\s*)?Primary Brake\s*:\s*(.+?)\s*$",
    ):
        _m = re.search(_pattern, text)
        if _m:
            f15_brake_driver = _m.group(1).strip()
            break

    f15_why = (
        f"{strategic_risk_budget} → {recommended_exposure}. "
        f"Brake driver: {f15_brake_driver}."
    )

    f18_why = (
        f"Regime Controller {regime_controller}. {exposure_override}. "
        f"Exposure remains capped at {exposure_ceiling}; F18 changes sector weights, not total exposure."
    )

    # Execution rows are parsed from the persisted F19 EXECUTION section.
    execution_rows = []
    for raw in execution.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(
            r"^(.+?)\s{2,}([A-Z]{2,6})\s{2,}(.+?)\s{2,}(.+?)\s{2,}(.+?)$",
            line,
        )
        if m:
            execution_rows.append({
                "sector": m.group(1).strip(),
                "etf": m.group(2).strip(),
                "action": m.group(3).strip(),
                "classification": m.group(4).strip(),
                "divergence": m.group(5).strip(),
            })

    execution_by_sector = {
        row["sector"].upper(): row for row in execution_rows
    }

    portfolio_rows = []
    for row in allocation_rows:
        sector_name = row["sector"]
        weight = row["weight"]
        exec_row = execution_by_sector.get(sector_name.upper(), {})
        portfolio_rows.append({
            "sector": sector_name,
            "weight": weight,
            "etf": exec_row.get("etf", "—"),
            "action": exec_row.get("action", "—"),
            "classification": exec_row.get("classification", "—"),
            "divergence": exec_row.get("divergence", "—"),
        })

    # Cash is part of the 100% portfolio. Tactical reserve is already contained in cash.
    equity_n = pct_number(allocated_equity)
    cash_n = pct_number(cash_weight)

    # Donut segments use persisted weights only.
    sector_degrees = []
    cursor = 0.0
    for row in portfolio_rows:
        weight_n = pct_number(row["weight"])
        deg = weight_n * 3.6
        sector_degrees.append((cursor, cursor + deg))
        cursor += deg
    cash_start = cursor
    cash_end = 360.0

    donut_parts = []
    donut_classes = ["var(--pm-sector-1)", "var(--pm-sector-2)",
                     "var(--pm-sector-3)", "var(--pm-sector-4)",
                     "var(--pm-sector-5)", "var(--pm-sector-6)"]
    for i, (a, b) in enumerate(sector_degrees):
        donut_parts.append(f"{donut_classes[i % len(donut_classes)]} {a:.2f}deg {b:.2f}deg")
    donut_parts.append(f"var(--pm-cash) {cash_start:.2f}deg {cash_end:.2f}deg")
    donut_gradient = ", ".join(donut_parts)

    target_delta, target_exits, target_note = target_weight_comparison(text, report_date)

    portfolio_table = "\n".join(
        f"""
        <div class="pm-portfolio-row">
          <div><strong>{esc(row["sector"])}</strong><span>{esc(row["etf"])}</span></div>
          <strong>{esc(row["weight"])}</strong>
          <span>{target_delta(row["sector"])}</span>
          <span>{esc(row["action"])}</span>
          <span>{esc(row["classification"])}</span>
          <span class="{pm_semantic(row["divergence"])}">{esc(row["divergence"])}</span>
        </div>
        """
        for row in portfolio_rows
    )

    if not portfolio_table:
        portfolio_table = '<div class="empty-state">No positive sector allocation.</div>'


    if target_exits:
        portfolio_table += "".join(
            '<div class="pm-portfolio-row">'
            '<div><strong>' + esc(name)
            + '</strong><span>Removed from target</span></div>'
            '<strong>0.0%</strong><span>' + target_delta(name)
            + '</span><span>—</span><span>—</span><span>—</span></div>'
            for name in target_exits
        )

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Global Capital Flow Monitor</title>
  <link rel="stylesheet" href="{asset_href}">
  <style>
    :root {{
      --pm-green:#56c596; --pm-amber:#e4b95b; --pm-red:#e46b6b;
      --pm-neutral:#a9b4c5; --pm-cash:#263143;
      --pm-sector-1:#76a9fa; --pm-sector-2:#73d0b2; --pm-sector-3:#b18cff;
      --pm-sector-4:#f0b76a; --pm-sector-5:#e47d9d; --pm-sector-6:#7cc7d9;
    }}
    .pm-red{{color:var(--pm-red)!important}}
    .pm-amber{{color:var(--pm-amber)!important}}
    .pm-green{{color:var(--pm-green)!important}}
    .pm-neutral{{color:var(--pm-neutral)!important}}
    .pm-construction-grid{{display:grid;grid-template-columns:minmax(0,1.08fr) minmax(360px,.92fr);gap:18px;margin:18px 0}}
    .pm-chain{{display:grid;gap:10px;margin-top:16px}}
    .pm-chain-node{{padding:15px 16px;border:1px solid rgba(148,163,184,.18);border-radius:12px;background:rgba(15,23,42,.35)}}
    .pm-chain-node .node-head{{display:flex;justify-content:space-between;gap:14px;align-items:baseline}}
    .pm-chain-node .node-head span{{font-size:12px;letter-spacing:.08em;opacity:.72}}
    .pm-chain-node .node-head strong{{font-size:23px}}
    .pm-chain-node p{{margin:8px 0 0;font-size:13px;line-height:1.5;opacity:.78}}
    .pm-chain-arrow{{text-align:center;opacity:.45}}
    .pm-target-wrap{{display:grid;grid-template-columns:190px 1fr;gap:20px;align-items:center;margin-top:14px}}
    .pm-target-donut{{width:180px;height:180px;border-radius:50%;background:conic-gradient({donut_gradient});position:relative;margin:auto}}
    .pm-target-donut:after{{content:"";position:absolute;inset:35px;border-radius:50%;background:#101827}}
    .pm-target-center{{position:absolute;inset:0;display:grid;place-content:center;text-align:center;z-index:2}}
    .pm-target-center strong{{font-size:30px}} .pm-target-center span{{font-size:10px;letter-spacing:.08em;opacity:.68}}
    .pm-target-summary{{display:grid;gap:8px}}
    .pm-target-summary>div{{display:flex;justify-content:space-between;gap:12px;padding-bottom:7px;border-bottom:1px solid rgba(148,163,184,.12)}}
    .pm-portfolio-table{{margin-top:18px}}
    .pm-portfolio-row{{display:grid;grid-template-columns:1.2fr .5fr .8fr .9fr 1.1fr;gap:10px;padding:9px 0;border-top:1px solid rgba(148,163,184,.12);align-items:center;font-size:12px}}
    .pm-portfolio-row>div{{display:grid}} .pm-portfolio-row>div span{{opacity:.62}}
    .pm-state-pair{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:18px 0}}
    .pm-state-list{{display:grid;gap:0;margin-top:12px}}
    .pm-state-list>div{{display:flex;justify-content:space-between;gap:18px;padding:10px 0;border-top:1px solid rgba(148,163,184,.12)}}
    .pm-state-list span{{opacity:.67}} .pm-state-list strong{{text-align:right}}
    .pm-confirm-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-top:12px}}
    .pm-confirm-grid>div{{padding:13px;border:1px solid rgba(148,163,184,.15);border-radius:10px}}
    .pm-confirm-grid span{{display:block;font-size:11px;opacity:.65;margin-bottom:6px}}
    .pm-wti{{color:var(--pm-amber)!important}}
    @media(max-width:900px){{
      .pm-construction-grid,.pm-state-pair{{grid-template-columns:1fr}}
      .pm-target-wrap{{grid-template-columns:1fr}}
      .pm-confirm-grid{{grid-template-columns:repeat(2,1fr)}}
      .pm-portfolio-row{{grid-template-columns:1fr .5fr .8fr}}
      .pm-portfolio-row>*:nth-child(n+4){{display:none}}
    }}




    .diag-shadow-compact b {{
      font-size: 13px;
      line-height: 1.25;
      font-weight: 700;
    }}
</style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div>
        <div class="eyebrow">INDEPENDENT MARKET RESEARCH</div>
        <h1>🌍 Global Capital Flow Monitor</h1>
      </div>
      <div class="asof report-date-navigator">
        <span class="report-label">REPORT</span>
        <div class="report-date-row">
          {previous_control}
          <button class="report-date-trigger" id="report-date-trigger" type="button"
                  aria-expanded="false" aria-controls="report-calendar">
            <span>{esc(report_date)}</span><span class="report-date-caret">▾</span>
          </button>
          {next_control}
        </div>
        <strong>DATA AS OF {esc(data_as_of)}</strong>
        <div class="report-calendar" id="report-calendar" hidden>
          <div class="calendar-header">
            <button type="button" class="calendar-month-nav" id="calendar-prev-month">‹</button>
            <strong id="calendar-month-label"></strong>
            <button type="button" class="calendar-month-nav" id="calendar-next-month">›</button>
          </div>
          <div class="calendar-weekdays"><span>Su</span><span>Mo</span><span>Tu</span><span>We</span><span>Th</span><span>Fr</span><span>Sa</span></div>
          <div class="calendar-grid" id="calendar-grid"></div>
        </div>
      </div>
    </header>

    <section class="pm-decision-hero">
      <div class="section-kicker">TODAY'S PORTFOLIO DECISION</div>
      <div class="pm-decision-grid">
        <div class="pm-decision-primary"><span class="label">ACTION</span><strong class="pm-action">{esc(stance.split("·", 1)[0].strip())}</strong></div>
        <div class="pm-decision-primary"><span class="label">EXPOSURE CEILING</span><strong class="pm-exposure">{esc(exposure_ceiling)}</strong></div>
        <div class="pm-decision-context"><span class="label">REGIME</span><strong>{esc(regime)}</strong></div>
        <div class="pm-decision-context"><span class="label">CONVICTION</span><strong>{esc(conviction)}</strong></div>
      </div>
    </section>

    <section class="pm-market-synthesis">
      <div class="section-kicker">TODAY'S MARKET</div>
      <p>{esc(market_sentence)}</p>
    </section>

    <section class="pm-construction-grid">
      <article class="panel pm-decision-path">
        <div class="section-kicker">DECISION PATH</div>
        <h2>Risk Budget → Exposure → Allocation</h2>
        <div class="pm-chain">

          <div class="pm-chain-node">
            <div class="node-head">
              <span>F13 · STRATEGIC RISK BUDGET</span>
              <strong>{esc(strategic_risk_budget)}</strong>
            </div>
            <p><b>RISK BUDGET BUILD</b></p>
            <p>
              Sentiment · Structure / Policy · Credit · Net Liquidity<br>
              Structural v2 · Drift · Flow / Gamma · Macro · Positioning<br>
              → Phase Cap → <b>{esc(strategic_risk_budget)}</b>
            </p>
          </div>

          <div class="pm-chain-arrow">↓</div>

          <div class="pm-chain-node">
            <div class="node-head">
              <span>F15 · RECOMMENDED EXPOSURE</span>
              <strong>{esc(recommended_exposure)}</strong>
            </div>
            <p><b>EXPOSURE BRAKE</b></p>
            <p>
              Input Budget · <b>{esc(strategic_risk_budget)}</b><br>
              VIX · <b>14.53 · NORMAL → 1.00x</b><br>
              Positioning Z · <b>{esc(positioning)}</b><br>
              Brake · <b>Positioning Heat → 0.95x</b><br>
              Calculation · <b>33 × 0.95 = 31.35 → {esc(recommended_exposure)}</b>
            </p>
          </div>

          <div class="pm-chain-arrow">↓</div>

          <div class="pm-chain-node">
            <div class="node-head">
              <span>F18 · EXPOSURE CEILING</span>
              <strong>{esc(exposure_ceiling)}</strong>
            </div>
            <p><b>PORTFOLIO DEPLOYMENT</b></p>
            <p>
              Input Exposure · <b>{esc(recommended_exposure)}</b><br>
              Regime Controller · <b>{esc(regime_controller)}</b><br>
              Exposure Override · <b>{esc(exposure_override)}</b><br>
              Allocated Equity · <b>{esc(allocated_equity)}</b><br>
              Tactical Reserve · <b>{esc(tactical_reserve)}</b><br>
              Cash · <b>{esc(cash_weight)}</b><br>
              → Sector Weights / ETF Execution
            </p>
          </div>

        </div>        </div>
      </article>

      <article class="panel pm-target-portfolio">
        <div class="section-kicker">F18 ALLOCATION · F19 EXECUTION</div>
        <h2>TARGET PORTFOLIO</h2>
        {target_note}
        <div class="pm-target-wrap">
          <div class="pm-target-donut">
            <div class="pm-target-center"><strong>100%</strong><span>PORTFOLIO</span></div>
          </div>
          <div class="pm-target-summary">
            <div><span>Allocated Equity</span><strong>{esc(allocated_equity)} {target_delta("Allocated Equity", total=True)}</strong></div>
            <div><span>Tactical Reserve</span><strong>{esc(tactical_reserve)} {target_delta("Tactical Reserve", total=True)}</strong></div>
            <div><span>Cash</span><strong>{esc(cash_weight)} {target_delta("Cash", total=True)}</strong></div>
          </div>
        </div>
        <div class="pm-portfolio-table">
          <div class="pm-portfolio-row"><strong>SECTOR / ETF</strong><strong>WEIGHT</strong><strong>Δ vs Prev</strong><strong>ACTION</strong><strong>CLASS</strong><strong>DIVERGENCE</strong></div>
          {portfolio_table}
          <div class="pm-portfolio-row">
            <div><strong>Cash</strong><span>Reserve included</span></div>
            <strong>{esc(cash_weight)}</strong><span>{target_delta("Cash", total=True)}</span><span>HOLD</span><span>LIQUIDITY</span><span>—</span>
          </div>
        </div>
      </article>
    </section>

    <section class="pm-state-pair">
      <article class="panel">
        <div class="section-kicker">MACRO &amp; LIQUIDITY</div>
        <h2>Macro State</h2>
        <div class="pm-state-list">
          <div><span>Macro Narrative</span><strong class="{pm_semantic(macro_state_narrative)}">{esc(macro_state_narrative)}</strong></div>
          <div><span>Policy Bias</span><strong class="{pm_semantic(policy_bias)}">{esc(policy_bias)}</strong></div>
          <div><span>Financial Conditions</span><strong class="{pm_semantic(financial_conditions)}">{esc(financial_conditions)}</strong></div>
          <div><span>Real Rate</span><strong class="{pm_semantic(real_rate)}">{esc(real_rate)}</strong></div>
          <div><span>Liquidity</span><strong class="{pm_semantic(liquidity)}">{esc(liquidity)}</strong></div>
          <div><span>Liquidity Level</span><strong>{esc(liquidity_level)}</strong></div>
          <div><span>Credit</span><strong class="{pm_semantic(credit)}">{esc(credit)}</strong></div>
          <div><span>Credit Structure</span><strong class="{pm_semantic(credit_structure)}">{esc(credit_structure)}</strong></div>
          <div><span>Structure</span><strong class="{pm_semantic(structure)}">{esc(structure)}</strong></div>
          <div><span>Growth</span><strong class="{pm_semantic(growth_sustainability)}">{esc(growth_sustainability)}</strong></div>
        </div>
      </article>

      <article class="panel">
        <div class="section-kicker">MARKET QUALITY</div>
        <h2>Participation &amp; Risk Quality</h2>
        <div class="pm-state-list">
          <div><span>Institutional Flow</span><strong class="{pm_semantic(flow)}">{esc(flow)}</strong></div>
          <div><span>Flow Authenticity</span><strong class="{pm_semantic(flow_authenticity)}">{esc(flow_authenticity)}</strong></div>
          <div><span>Participation Quality</span><strong class="{pm_semantic(participation_quality)}">{esc(participation_quality)}</strong></div>
          <div><span>Participation Mode</span><strong>{esc(participation_mode)}</strong></div>
          <div><span>Leadership</span><strong class="{pm_semantic(leadership_state)}">{esc(leadership_state)}</strong></div>
          <div><span>Positioning</span><strong class="{pm_semantic(positioning_state)}">{esc(positioning_state)}</strong></div>
          <div><span>Dealer Gamma</span><strong class="{pm_semantic(dealer_gamma)}">{esc(dealer_gamma)}</strong></div>
          <div><span>Squeeze Risk</span><strong class="{pm_semantic(squeeze_risk)}">{esc(squeeze_risk)}</strong></div>
          <div><span>Vol Structure</span><strong class="{pm_semantic(vol_structure)}">{esc(vol_structure)}</strong></div>
          <div><span>Drift</span><strong class="{pm_semantic(drift)}">{esc(drift)}</strong></div>
        </div>
      </article>
    </section>

    <section class="panel">
      <div class="section-kicker">MARKET CONFIRMATION</div>
      <h2>Cross-Asset Tape</h2>
      <div class="pm-confirm-grid">
        <div><span>US10Y</span><strong>🔴 {esc(tape_display(us10y))}</strong></div>
        <div><span>USD</span><strong>🟢 {esc(tape_display(usd))}</strong></div>
        <div><span>WTI</span><strong>🟡 {esc(tape_display(oil))}</strong></div>
        <div><span>VIX</span><strong>🟢 {esc(tape_display(volatility))}</strong></div>
        <div><span>HY OAS</span><strong>🟢 {esc(tape_display(hy_oas))}</strong></div>
      </div>
    {risk_monitor_ui(diag_text, is_latest_page)[0]}
    </section>



    <section class="panel">
      <div class="section-kicker">LEADERSHIP &amp; PARTICIPATION</div>
      <h2>Sector Leadership</h2>
      <div class="coverage">{esc(coverage)}</div>
      <div class="sector-table">{sector_html}</div>

      <div class="leadership-divider"></div>

      <h3 class="breadth-confirmation-title">
        Breadth &amp; Leadership Confirmation
      </h3>

      <div class="breadth-table">{breadth_html}</div>
    </section>

    <section class="panel">
      <div class="section-kicker">ACTIVE CONSTRAINTS</div>
      <h2>Current Portfolio Constraints</h2>
      <div class="pm-state-list">
        <div>
          <span>Positioning Risk</span>
          <strong class="{pm_semantic(positioning_state)}">
            {esc(positioning_state)} · Z {esc(diag["positioning_z"])}
          </strong>
        </div>
        <div>
          <span>Squeeze Risk</span>
          <strong class="{pm_semantic(constraint_squeeze)}">
            {esc(constraint_squeeze)}
          </strong>
        </div>
        <div>
          <span>Geo Stress</span>
          <strong class="{pm_semantic(geopolitical)}">
            {esc(diag["geo_level"])} · {esc(diag["geo_score"])}
          </strong>
        </div>
      </div>
    </section>

    <section class="diagnostics-entry">
      <div class="diagnostics-entry-kicker">WANT TO SEE WHY?</div>
      <div class="diagnostics-entry-link">{diagnostics_link}</div>
      <p>
        Trace the signals, constraints, and engine states behind today's
        portfolio decision.
      </p>
    </section>

    <footer class="footer pm-provenance-footer">
      <div>Persisted report · presentation-only renderer</div>
    </footer>

    <script>
      const availableDates = {available_dates_json};
      const currentReportDate = "{esc(report_date)}";
      const latestReportDate = "{esc(latest_date)}";
      const isLatestPage = {str(is_latest_page).lower()};
      const trigger = document.getElementById("report-date-trigger");
      const calendar = document.getElementById("report-calendar");
      const grid = document.getElementById("calendar-grid");
      const label = document.getElementById("calendar-month-label");
      const prevMonth = document.getElementById("calendar-prev-month");
      const nextMonth = document.getElementById("calendar-next-month");
      let view = new Date(currentReportDate + "T12:00:00");

      function hrefForDate(d) {{
        if (isLatestPage) return d === latestReportDate ? "index.html" : "history/" + d + ".html";
        return d === latestReportDate ? "../index.html" : d + ".html";
      }}
      function renderCalendar() {{
        const y=view.getFullYear(), m=view.getMonth();
        label.textContent=view.toLocaleString("en-US",{{month:"long",year:"numeric"}});
        grid.innerHTML="";
        const first=new Date(y,m,1).getDay(), days=new Date(y,m+1,0).getDate();
        for(let i=0;i<first;i++) grid.appendChild(document.createElement("span"));
        for(let d=1;d<=days;d++) {{
          const iso=`${{y}}-${{String(m+1).padStart(2,"0")}}-${{String(d).padStart(2,"0")}}`;
          const el=document.createElement(availableDates.includes(iso)?"a":"span");
          el.textContent=d;
          if(availableDates.includes(iso)) el.href=hrefForDate(iso);
          if(iso===currentReportDate) el.className="current";
          grid.appendChild(el);
        }}
      }}
      trigger?.addEventListener("click",()=>{{calendar.hidden=!calendar.hidden;trigger.setAttribute("aria-expanded",String(!calendar.hidden));if(!calendar.hidden)renderCalendar();}});
      prevMonth?.addEventListener("click",()=>{{view=new Date(view.getFullYear(),view.getMonth()-1,1);renderCalendar();}});
      nextMonth?.addEventListener("click",()=>{{view=new Date(view.getFullYear(),view.getMonth()+1,1);renderCalendar();}});
    </script>
  </main>
</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(page, encoding="utf-8")

    if build_diagnostics:
        diag_text = diagnostics.read_text(encoding="utf-8") if diagnostics.exists() else ""
        diag = parse_diagnostics_v1(diag_text)

        # Portfolio composition comes from the canonical PM allocation contract.
        # Tactical Reserve is already contained within Cash & Hedge.
        diag_equity = allocated_equity
        diag_cash = cash_weight

        # Presentation-only numeric conversion for CSS geometry.
        # The portfolio value itself remains the canonical PM allocation.
        diag_equity_number_match = re.search(
            r"-?\\d+(?:\\.\\d+)?",
            str(diag_equity),
        )
        diag_equity_number = (
            diag_equity_number_match.group(0)
            if diag_equity_number_match
            else "0"
        )

        us10y_change = diag_change_parts(diag["us10y"])
        dxy_change = diag_change_parts(diag["dxy"])
        vix_change = diag_change_parts(diag["vix"])
        wti_change = diag_change_parts(diag["wti"])

        recent_sew_events = (
            load_recent_sew_events() if report_date == latest_date else []
        )

        if recent_sew_events:
            recent_alerts_html = "".join(
                f"""
                <div class="diag-alert-event">
                  <strong>{esc(event["transition"])}</strong>
                  <span>{esc(event["event_type"])}</span>
                  <small>{esc(event["timestamp_kst"])}</small>
                </div>
                """
                for event in recent_sew_events
            )
        else:
            recent_alerts_html = """
                <div class="diag-alert-event">
                  <strong>NO RECORDED LIFECYCLE EVENTS</strong>
                  <span>Current history begins with verified persisted events.</span>
                </div>
            """

        if report_date != latest_date:
            recent_alerts_html = (
                '<div class="diag-alert-event">'
                '<strong>HISTORICAL EVENT LOG UNAVAILABLE</strong>'
                '<span>Current lifecycle events are not shown on historical reports.</span>'
                '</div>'
            )

        sew_display = str(diag["sew"])
        sew_display = sew_display.replace(
            "이상징후 없음",
            "No anomalies detected",
        )
        sew_display = sew_display.replace(
            "개 자산 정상 범위",
            " assets within normal range",
        )
        sew_display = sew_display.replace(
            "z-score 발작 없음",
            "no z-score spikes",
        )

        sew_class = diag_semantic_class(diag["sew"])
        deadman_class = diag_semantic_class(diag["deadman"])
        flow_class = diag_semantic_class(diag["flow_state"])
        positioning_class = diag_semantic_class(
            diag["f15_brake_drivers"]
        )
        gamma_class = diag_semantic_class(diag["gamma_state"])

        # Frozen F13 positioning rule, validated against Production.
        # Used only to expose an existing decision contribution.
        try:
            diag_pos_z = float(diag["f13_positioning_z"])
        except (ValueError, TypeError):
            diag_pos_z = None
        if diag_pos_z is None:
            f13_positioning_impact = None
        elif diag_pos_z >= 2.0:
            f13_positioning_impact = -8
        elif diag_pos_z >= 1.5:
            f13_positioning_impact = -4
        else:
            f13_positioning_impact = 0

        diag_page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Engine Diagnostics · Global Capital Flow Monitor</title>
  <link rel="stylesheet" href="{asset_href}">
</head>
<body>
  <main class="shell diagnostics-shell">
    {"" if diagnostics.exists() else
     '<div class="panel">No persisted engine diagnostics for this date. '
     'Diagnostic fields are unavailable.</div>'}


    <header class="topbar diagnostics-topbar">
      <div>
        <div class="eyebrow">MODEL OBSERVABILITY · CONTROL ROOM</div>
        <h1>Engine Diagnostics</h1>
        <div class="diag-asof">
          REPORT {esc(report_date)} · DATA AS OF {esc(diag["data_as_of"])}
        </div>
      </div>
      <a href="{esc(pm_return_href)}">← PM View</a>
    </header>

    <section class="diag-status-grid">
      <article class="diag-status-card {{sew_class}}">
        <div class="label">STRUCTURAL EARLY WARNING</div>
        <strong>{esc(sew_display)}</strong>
      </article>

      <article class="diag-status-card {{deadman_class}}">
        <div class="label">HARD DEADMAN</div>
        <strong>{esc(diag["deadman"])}</strong>
      </article>

      <article class="diag-status-card diag-recent-alerts">
        <div class="label">RECENT SYSTEM ALERTS</div>
        {recent_alerts_html}
      </article>

      <article class="diag-status-card">
        <div class="label">OBSERVATION ONLY</div>
        <strong>Shadow Monitor</strong>
        <div class="diag-shadow-compact">
          <div><span>Growth Sustainability</span><b>{esc(diag["growth_shadow"])}</b></div>
          <div><span>Flow Authenticity</span><b>{esc(diag["flow_auth_shadow"])}</b></div>
          <div><span>Leadership Breadth</span><b>{esc(diag["breadth_shadow"])}</b></div>
          <div><span>Positioning Stress</span><b>{esc(diag["positioning_shadow"])}</b></div>
        </div>
      </article>
    </section>

    <section class="panel diag-drivers-panel">
      <div class="section-kicker">DECISION ATTRIBUTION</div>

      <div class="diag-drivers-heading">
        <div>
          <h2>Key Drivers of Today's Decision</h2>
          <p>
            Measured F13 contributions, risk-budget constraint,
            and explicit F15 execution brake.
          </p>
        </div>

        <div class="diag-driver-summary">
          <span>F13</span>
          <strong>{esc(diag["f13_risk_budget"])}</strong>
          <i>→</i>
          <span>F15</span>
          <strong>{esc(diag["f15_exposure"])}</strong>
        </div>
      </div>

      <div class="driver-table">

        <div class="driver-table-head">
          <span>DRIVER</span>
          <span>STATE / ROLE</span>
          <span>IMPACT</span>
          <span>IMPACT ON DECISION</span>
        </div>

        <div class="driver-row">
          <div>
            <strong>Macro</strong>
            <small>F13 contribution</small>
          </div>
          <span>{esc(diag["macro_narrative"])}</span>
          <b class="impact-positive">
            {esc(diag["f13_macro_tilt"])}
          </b>
          <div class="impact-track">
            <i class="impact-bar impact-bar-green impact-w100"></i>
          </div>
        </div>

        <div class="driver-row">
          <div>
            <strong>Flow Regime</strong>
            <small>F13 contribution</small>
          </div>
          <span>{esc(diag["flow_state"])}</span>
          <b class="impact-positive">
            {esc(diag["f13_flow_regime_tilt"])}
          </b>
          <div class="impact-track">
            <i class="impact-bar impact-bar-green impact-w60"></i>
          </div>
        </div>

        <div class="driver-row">
          <div>
            <strong>Flow-Gamma</strong>
            <small>F13 contribution</small>
          </div>
          <span>{esc(diag["gamma_state"])}</span>
          <b class="impact-positive">
            {esc(diag["f13_flow_gamma_tilt"])}
          </b>
          <div class="impact-track">
            <i class="impact-bar impact-bar-green impact-w40"></i>
          </div>
        </div>

        <div class="driver-row">
          <div>
            <strong>Flow Continuity</strong>
            <small>F13 contribution</small>
          </div>
          <span>{esc(diag["f13_flow_continuity_role"])}</span>
          <b class="impact-positive">
            {esc(diag["f13_flow_continuity_tilt"])}
          </b>
          <div class="impact-track">
            <i class="impact-bar impact-bar-green impact-w20"></i>
          </div>
        </div>

        <div class="driver-row driver-row-negative">
          <div>
            <strong>Positioning</strong>
            <small>F13 · validated frozen rule</small>
          </div>
          <span>POS_Z {esc(diag["f13_positioning_z"])}</span>
          <b class="impact-negative">
            {format(f13_positioning_impact, "+d") if f13_positioning_impact is not None else "N/A"}
          </b>
          <div class="impact-track">
            <i class="impact-bar impact-bar-red impact-w80"></i>
          </div>
        </div>

        <div class="driver-row driver-row-cap">
          <div>
            <strong>Operational Phase</strong>
            <small>Risk-budget constraint</small>
          </div>
          <span>{esc(diag["market_regime"])}</span>
          <b class="impact-cap">
            CAP {esc(diag["f13_phase_cap"])}
          </b>
          <div class="impact-track">
            <i class="impact-cap-line"></i>
          </div>
        </div>

      </div>

      <div class="execution-brake">
        <div>
          <span>EXECUTION BRAKE · F15</span>
          <strong>Positioning</strong>
          <small>{esc(diag["f15_brake_drivers"])}</small>
        </div>

        <div class="execution-path">
          <span>F13 RISK BUDGET</span>
          <strong>{esc(diag["f13_risk_budget"])}</strong>
          <i>→</i>
          <span>F15 EXPOSURE</span>
          <strong class="impact-negative">
            {esc(diag["f15_exposure"])}
          </strong>
        </div>
      </div>

    </section>

    <section class="diag-primary-grid">

      <article class="panel diag-market-overview">
        <div class="section-kicker">MARKET &amp; ENGINE OVERVIEW</div>
        <h2>Cross-Market State &amp; Daily Change</h2>

        <div class="diag-market-grid">

          <div class="diag-market-card">
            <span class="diag-market-label">RATES</span>
            <div><span>US10Y</span><strong>{esc(diag["us10y"])}</strong></div>
            <div><span>Real Rate</span><strong>{esc(diag["real_rate"])}</strong></div>

          </div>

          <div class="diag-market-card">
            <span class="diag-market-label">FX</span>
            <div><span>DXY</span><strong>{esc(diag["dxy"])}</strong></div>
            <div><span>USD/KRW</span><strong>{esc(("↓ " if str(diag["usdk_rw"]).startswith("-") else "↑ " if str(diag["usdk_rw"]).startswith("+") else "") + str(diag["usdk_rw"]))}</strong></div>
          </div>

          <div class="diag-market-card">
            <span class="diag-market-label">LIQUIDITY</span>
            <div><span>Net Liquidity</span><strong>{esc(diag["net_liq"])}</strong></div>
            <div><span>TGA</span><strong>{esc(diag["tga"])}</strong></div>
            <div><span>RRP</span><strong>{esc(diag["rrp"])}</strong></div>
            <small>TGA {esc(diag["tga_direction"])} · RRP {esc(diag["rrp_direction"])} · Net Liquidity {esc(diag["net_liq_direction"])}</small>
          </div>

          <div class="diag-market-card">
            <span class="diag-market-label">CREDIT</span>
            <div><span>HY OAS</span><strong>{esc(diag["hy_oas_level"])} · {esc(diag["hy_oas_state"])} · {esc(diag["hy_direction"])}</strong></div>
            <div><span>HYG</span><strong>{esc(diag["hyg"])}</strong></div>
            <div><span>LQD</span><strong>{esc(diag["lqd"])}</strong></div>
          </div>

          <div class="diag-market-card">
            <span class="diag-market-label">VOLATILITY</span>
            <div><span>VIX</span><strong>{esc(diag["vix"])}</strong></div>
          </div>

          <div class="diag-market-card">
            <span class="diag-market-label">COMMODITIES</span>
            <div><span>WTI</span><strong>{esc(diag["wti"])}</strong></div>
          </div>

        </div>
      </article>

      <article class="panel diag-portfolio-panel">
        <div class="section-kicker">PORTFOLIO</div>
        <h2>Final Composition</h2>

        <div class="portfolio-donut-wrap">
          <div
            class="portfolio-donut"
            style="--equity-number:{esc(diag_equity_number)}"
            aria-label="Allocated equity {esc(diag_equity)}, cash {esc(diag_cash)}"
          >
            <div class="portfolio-donut-center">
              <strong>{esc(diag_equity)}</strong>
              <span>ALLOCATED EQUITY</span>
            </div>
          </div>
        </div>

        <div class="portfolio-legend">
          <div>
            <span class="legend-dot legend-equity"></span>
            <span>Allocated Equity</span>
            <strong>{esc(diag_equity)}</strong>
          </div>
          <div>
            <span class="legend-dot legend-cash"></span>
            <span>Cash &amp; Hedge</span>
            <strong>{esc(diag_cash)}</strong>
          </div>
        </div>

        <div class="cash-detail">
          <span>Strategic Cash {esc(diag["strategic_cash"])}</span>
          <span>Tactical Reserve {esc(diag["tactical_reserve"])}</span>
        </div>
      </article>

    </section>

    <section class="panel diag-change-panel">
      <div class="section-kicker">MARKET CONTEXT</div>
      <h2>What Changed Today?</h2>

      <div class="diag-change-grid">

        <div class="diag-change-card">
          <span>US 10Y</span>
          <div class="change-path">
            <b>{esc(us10y_change["previous"])}</b>
            <i>{esc(us10y_change["arrow"])}</i>
            <strong>{esc(us10y_change["current"])}</strong>
          </div>
          <small>{esc(us10y_change["change"])}</small>
        </div>

        <div class="diag-change-card">
          <span>DXY</span>
          <div class="change-path">
            <b>{esc(dxy_change["previous"])}</b>
            <i>{esc(dxy_change["arrow"])}</i>
            <strong>{esc(dxy_change["current"])}</strong>
          </div>
          <small>{esc(dxy_change["change"])}</small>
        </div>

        <div class="diag-change-card">
          <span>VIX</span>
          <div class="change-path">
            <b>{esc(vix_change["previous"])}</b>
            <i>{esc(vix_change["arrow"])}</i>
            <strong>{esc(vix_change["current"])}</strong>
          </div>
          <small class="diag-change-vix-{esc(vix_change["direction"])}">
            {esc(vix_change["change"])}
          </small>
        </div>

        <div class="diag-change-card">
          <span>WTI</span>
          <div class="change-path">
            <b>{esc(wti_change["previous"])}</b>
            <i>{esc(wti_change["arrow"])}</i>
            <strong>{esc(wti_change["current"])}</strong>
          </div>
          <small>{esc(wti_change["change"])}</small>
        </div>

      </div>
    </section>



    <section class="panel">
      <div class="section-kicker">ALLOCATION CONTEXT</div>
      <h2>Style / Factor Context</h2>
      <div class="pm-state-list">
        <div><span>Growth vs Value</span><strong>{esc(growth_value_tilt)}</strong></div>
        <div><span>Duration Tilt</span><strong>{esc(duration_tilt)}</strong></div>
        <div><span>Cyclical / Defensive</span><strong>{esc(cyclical_defensive)}</strong></div>
        <div><span>Duration Factor</span><strong>{esc(duration_factor)}</strong></div>
        <div><span>Inflation Factor</span><strong>{esc(inflation_factor)}</strong></div>
        <div><span>USD Factor</span><strong>{esc(usd_factor)}</strong></div>
        <div><span>Credit Factor</span><strong>{esc(credit_factor)}</strong></div>
      </div>
    </section>

    {risk_monitor_ui(diag_text)[2]}

    <section class="panel strategic-context-panel">
      <div class="section-kicker">PRACTITIONER RESEARCH</div>
      <h2>WHAT ARE GLOBAL MARKET PRACTITIONERS WATCHING?</h2>
      <div class="strategic-research-cta">
        <p>Explore the latest macro, policy, cross-asset and geopolitical context shaping institutional market discussions.</p>
        <a class="strategic-research-button"
           href="https://sellina95.github.io/bloomberg-surveillance-research/"
           target="_blank"
           rel="noopener noreferrer">
          View Latest Practitioner Research ↗
        </a>
        <small>Independent research context · Not an engine input</small>
      </div>
    </section>


    <script>
      function openLinkedDiagnostics() {{
        if (location.hash === '#full-engine-diagnostics') {{
          document.getElementById('full-engine-diagnostics').open = true;
        }}
      }}
      window.addEventListener('DOMContentLoaded', openLinkedDiagnostics);
      window.addEventListener('hashchange', openLinkedDiagnostics);
    </script>
<details class="panel diag-raw-details" id="full-engine-diagnostics">
      <summary>View Full Engine Diagnostics</summary>
      <pre class="diagnostics">{esc(diag_text)}</pre>
    </details>

  </main>
</body>
</html>
"""
        diagnostics_output.write_text(
            diag_page,
            encoding="utf-8",
        )

    print(f"[OK] Source: {source}")
    print(f"[OK] Site:   {output_path}")
    print(f"[OK] Sectors rendered: {len(sectors)}")
    print(f"[OK] Breadth rows rendered: {len(breadth_rows)}")
    print(f"[OK] Allocation rows rendered: {len(allocation_rows)}")




def bloomberg_research_cta(research_date: str) -> str:
    """
    Presentation-only link to the Bloomberg Surveillance Research Desk.

    The Research Desk owns latest-report discovery and redirects to the
    latest actually published public research artifact.
    """
    if not research_date:
        return ""

    desk_url = "https://sellina95.github.io/bloomberg-surveillance-research/"

    return f"""
      <div class="strategic-research-cta">
        <span>See how global market practitioners frame today's risks</span>
        <a class="strategic-research-button"
           href="{desk_url}"
           target="_blank"
           rel="noopener noreferrer">
          View Latest Practitioner Research ↗
        </a>
        <small>Bloomberg Surveillance Research</small>
      </div>
    """



def latest_strategic_context_date() -> str:
    """
    Return the latest persisted dated research-context artifact.
    Presentation-only. Does not affect engine state or historical PM reports.
    """
    context_dir = ROOT / "research_context"

    if not context_dir.exists():
        return ""

    dates = []

    for path in context_dir.glob("????-??-??.json"):
        date_value = path.stem
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_value):
            dates.append(date_value)

    return max(dates) if dates else ""



def load_strategic_context(report_date: str) -> dict:
    """
    Presentation-only research context.

    Reads a dated research artifact only. This data is not an engine
    input and must not affect market state, scoring, exposure, or allocation.
    """
    path = ROOT / "research_context" / f"{report_date}.json"

    empty = {
        "strategic_context": "",
        "brief": [],
    }

    if not path.exists():
        return empty

    try:
        import json

        data = json.loads(path.read_text(encoding="utf-8"))

        if data.get("engine_input") is not False:
            return empty

        if data.get("classification") != "RESEARCH_CONTEXT_ONLY":
            return empty

        insight = str(data.get("strategic_context", "")).strip()
        brief = data.get("brief", [])

        if not isinstance(brief, list):
            brief = []

        clean_brief = []
        for item in brief[:8]:
            if not isinstance(item, dict):
                continue

            title = str(item.get("title", "")).strip()
            summary = str(item.get("summary", "")).strip()

            if title and summary:
                clean_brief.append({
                    "title": title,
                    "summary": summary,
                })

        return {
            "strategic_context": insight,
            "brief": clean_brief,
        }

    except Exception:
        return empty



def build_historical_pm_pages() -> int:
    """
    Render persisted PM reports as static historical pages.

    Availability is defined strictly by the existence of a persisted
    daily_report_YYYY-MM-DD.md artifact. Historical rendering never
    recalculates Production state; Diagnostics use same-date artifacts.
    """
    reports = sorted(REPORTS_DIR.glob("daily_report_????-??-??.md"))
    history_dir = SITE_DIR / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    for source in reports:
        report_date = source.stem.removeprefix("daily_report_")
        build(
            source=source,
            output_path=history_dir / f"{report_date}.html",
            build_diagnostics=True,
        )

    return len(reports)


if __name__ == "__main__":
    build()
    historical_count = build_historical_pm_pages()
    print(f"[OK] Historical PM pages: {historical_count}")
