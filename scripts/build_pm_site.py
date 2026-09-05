from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
SITE_DIR = ROOT / "_site"
ASSETS_DIR = SITE_DIR / "assets"


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
    start_marker = f"{number}. {title}"
    start = text.find(start_marker)

    if start == -1:
        return ""

    start += len(start_marker)

    next_section = re.search(
        r"^\d+\.\s+[A-Z][A-Z &\-]+$",
        text[start:],
        flags=re.MULTILINE,
    )

    if next_section:
        end = start + next_section.start()
        return text[start:end].strip()

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
        "hy_oas": diag_match(
            text,
            r"\*\*HY_OAS level:\*\*\s*([^\n]+)",
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

        # Execution / control outputs already emitted by Diagnostics.
        "market_regime": diag_match(
            text,
            r"\*\*국면 전환 감지:\*\*[^\n]*?→\s*\*\*(.+?)\*\*",
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

    report_date = metadata(text, "Date")
    data_as_of = metadata(text, "Data as of")

    stance = top_value(text, "PORTFOLIO STANCE")
    regime = top_value(text, "REGIME")
    conviction = top_value(text, "CONVICTION")

    executive = section(text, 1, "EXECUTIVE VIEW")
    market = section(text, 2, "MARKET STATE")
    cross_asset = section(text, 3, "CROSS-ASSET CONFIRMATION")
    leadership = section(text, 4, "LEADERSHIP & PARTICIPATION")
    allocation = section(text, 5, "PORTFOLIO ALLOCATION")
    risk = section(text, 6, "RISK & CONSTRAINTS")
    rationale = section(text, 7, "DECISION RATIONALE")

    executive_summary = first_prose_line(executive)

    macro_narrative = field(executive, "Macro Narrative")
    tactical_signal = field(executive, "Tactical Signal")

    liquidity = field(market, "Liquidity")
    flow = field(market, "Flow")
    structure = field(market, "Structure")
    drift = field(market, "Drift")
    positioning = field(market, "Positioning Z")
    credit = field(market, "Credit")

    us10y = field(cross_asset, "US10Y Yield")
    usd = field(cross_asset, "USD")
    oil = field(cross_asset, "Oil")
    volatility = field(cross_asset, "Volatility")
    hy_oas = field(cross_asset, "HY OAS")

    coverage = field(leadership, "Coverage")
    sectors = parse_sector_rows(leadership)
    breadth_rows = parse_breadth_rows(leadership)

    exposure_ceiling = field(allocation, "Exposure Ceiling")
    allocated_equity = field(allocation, "Allocated Equity")
    tactical_reserve = field(allocation, "Tactical Reserve")
    cash_weight = field(allocation, "Cash")
    allocation_rows = parse_allocation_rows(allocation)

    inflation = field(risk, "Inflation")
    risk_liquidity = field(risk, "Liquidity")
    risk_positioning = field(risk, "Positioning Z")
    risk_credit = field(risk, "Credit")
    geopolitical = field(risk, "Geopolitical")

    decision = field(rationale, "Decision")
    decision_exposure = field(rationale, "Exposure Ceiling")
    decision_signal = field(rationale, "Tactical Signal")
    decision_conviction = field(rationale, "Conviction")
    reasons = parse_rationale(rationale)

    sector_html = "\n".join(
        f"""
        <div class="sector-row">
          <span class="rank">{esc(row['rank'])}</span>
          <span class="sector-name">{esc(row['sector'])}</span>
          <span class="sector-return">{esc(row['return'])}</span>
          <span class="sector-relative">{esc(row['relative'])} vs SPY</span>
          <span class="momentum">M {esc(row['momentum'])}</span>
        </div>
        """
        for row in sectors
    )

    if not sector_html:
        sector_html = """
        <div class="empty-state">
          No same-date sector observations available.
        </div>
        """

    breadth_html = "\n".join(
        f"""
        <div class="breadth-row">
          <span>{esc(row['label'])}</span>
          <strong>{esc(row['today'])}</strong>
          <span>Prev {esc(row['prev'])}</span>
          <span>Δ {esc(row['change'])}</span>
        </div>
        """
        for row in breadth_rows
    )

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

    # Only the latest PM page may point at the canonical latest
    # diagnostics page. Historical PM pages must never fall through
    # to a different report date's diagnostics.
    diagnostics = REPORTS_DIR / f"engine_diagnostics_{report_date}.md"
    diagnostics_link = (
        '<a href="diagnostics.html">Engine Diagnostics</a>'
        if is_latest_page and diagnostics.exists()
        else '<span>Engine Diagnostics unavailable</span>'
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

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Global Capital Flow Monitor</title>
  <link rel="stylesheet" href="assets/style.css">
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

          <button
            class="report-date-trigger"
            id="report-date-trigger"
            type="button"
            aria-expanded="false"
            aria-controls="report-calendar"
          >
            <span>{esc(report_date)}</span>
            <span class="report-date-caret">▾</span>
          </button>

          {next_control}
        </div>

        <strong>DATA AS OF {esc(data_as_of)}</strong>

        <div
          class="report-calendar"
          id="report-calendar"
          hidden
        >
          <div class="calendar-header">
            <button
              type="button"
              class="calendar-month-nav"
              id="calendar-prev-month"
              aria-label="Previous month"
            >‹</button>

            <strong id="calendar-month-label"></strong>

            <button
              type="button"
              class="calendar-month-nav"
              id="calendar-next-month"
              aria-label="Next month"
            >›</button>
          </div>

          <div class="calendar-weekdays" aria-hidden="true">
            <span>Su</span>
            <span>Mo</span>
            <span>Tu</span>
            <span>We</span>
            <span>Th</span>
            <span>Fr</span>
            <span>Sa</span>
          </div>

          <div
            class="calendar-grid"
            id="calendar-grid"
          ></div>
        </div>
      </div>
    </header>

    <section class="decision-grid decision-grid-three">
      <article class="hero-card">
        <div class="label">PORTFOLIO STANCE</div>
        <div class="hero-value">{esc(stance)}</div>
      </article>

      <article class="hero-card">
        <div class="label">REGIME</div>
        <div class="hero-value">{esc(regime)}</div>
      </article>

      <article class="hero-card">
        <div class="label">CONVICTION</div>
        <div class="hero-value">{esc(conviction)}</div>
      </article>
    </section>

    <section class="panel executive-panel">
      <div class="panel-title">EXECUTIVE VIEW</div>
      <p class="executive-copy">{esc(executive_summary)}</p>

      <div class="executive-meta">
        <div>
          <span>Macro Narrative</span>
          <strong>{esc(macro_narrative)}</strong>
        </div>
        <div>
          <span>Tactical Signal</span>
          <strong>{esc(tactical_signal)}</strong>
        </div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-title">MARKET STATE</div>
      <div class="metric-grid">
        <div><span>Liquidity</span><strong>{esc(liquidity)}</strong></div>
        <div><span>Flow</span><strong>{esc(flow)}</strong></div>
        <div><span>Structure</span><strong>{esc(structure)}</strong></div>
        <div><span>Drift</span><strong>{esc(drift)}</strong></div>
        <div><span>Positioning Z</span><strong>{esc(positioning)}</strong></div>
        <div><span>Credit</span><strong>{esc(credit)}</strong></div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-title">CROSS-ASSET CONFIRMATION</div>
      <div class="metric-grid">
        <div><span>US10Y</span><strong>{esc(us10y)}</strong></div>
        <div><span>USD</span><strong>{esc(usd)}</strong></div>
        <div><span>Oil</span><strong>{esc(oil)}</strong></div>
        <div><span>Volatility</span><strong>{esc(volatility)}</strong></div>
        <div><span>HY OAS</span><strong>{esc(hy_oas)}</strong></div>
      </div>
    </section>

    <section class="panel">
      <div class="panel-header">
        <div class="panel-title">LEADERSHIP & PARTICIPATION</div>
        <div class="coverage">{esc(coverage)}</div>
      </div>

      <div class="subpanel-label">TODAY'S SECTOR LEADERS</div>

      <div class="sector-table">
        {sector_html}
      </div>

      <div class="subpanel-label subpanel-spaced">
        BREADTH & LEADERSHIP
      </div>

      <div class="breadth-table">
        {breadth_html}
      </div>
    </section>

    <section class="panel allocation-panel">
      <div class="panel-title">PORTFOLIO ALLOCATION</div>

      <div class="allocation-summary">
        <div>
          <span>Exposure Ceiling</span>
          <strong>{esc(exposure_ceiling)}</strong>
        </div>
        <div>
          <span>Allocated Equity</span>
          <strong>{esc(allocated_equity)}</strong>
        </div>
        <div>
          <span>Tactical Reserve</span>
          <strong>{esc(tactical_reserve)}</strong>
        </div>
        <div>
          <span>Cash</span>
          <strong>{esc(cash_weight)}</strong>
        </div>
      </div>

      <div class="allocation-note">
        Tactical Reserve is undeployed capacity within the Exposure Ceiling
        and is already included in Cash.
      </div>

      <div class="subpanel-label subpanel-spaced">
        FINAL F18 SECTOR ALLOCATION
      </div>

      <div class="allocation-table">
        {allocation_html}
      </div>
    </section>

    <section class="panel">
      <div class="panel-title">RISK & CONSTRAINTS</div>
      <div class="metric-grid">
        <div><span>Inflation</span><strong>{esc(inflation)}</strong></div>
        <div><span>Liquidity</span><strong>{esc(risk_liquidity)}</strong></div>
        <div><span>Positioning Z</span><strong>{esc(risk_positioning)}</strong></div>
        <div><span>Credit</span><strong>{esc(risk_credit)}</strong></div>
        <div><span>Geopolitical</span><strong>{esc(geopolitical)}</strong></div>
      </div>
    </section>

    <section class="panel rationale-panel">
      <div class="panel-title">DECISION RATIONALE</div>

      <div class="decision-rationale-grid">
        <div>
          <span>Decision</span>
          <strong>{esc(decision)}</strong>
        </div>
        <div>
          <span>Exposure Ceiling</span>
          <strong>{esc(decision_exposure)}</strong>
        </div>
        <div>
          <span>Tactical Signal</span>
          <strong>{esc(decision_signal)}</strong>
        </div>
        <div>
          <span>Conviction</span>
          <strong>{esc(decision_conviction)}</strong>
        </div>
      </div>

      <ul class="rationale-list">
        {reasons_html}
      </ul>
    </section>

    <section class="panel diagnostics-cta">
      <div class="panel-title">ENGINE TRANSPARENCY</div>
      <div class="diagnostics-cta-content">
        <div>
          <h2>Want to see what drives this decision?</h2>
          <p>
            Inspect the signals, filters, constraints, and decision path
            behind the current portfolio stance.
          </p>
        </div>
        <div class="diagnostics-cta-link">
          {diagnostics_link}
        </div>
      </div>
    </section>

    <footer class="site-footer">
      <span>Global Capital Flow Monitor</span>
      <span class="footer-links">
        <a href="https://github.com/Sellina95/Global-Capital-Flow-Monitor"
           target="_blank" rel="noopener noreferrer">GitHub</a>
        <span>·</span>
        <a href="https://petal-chair-9d2.notion.site/Global-Capital-Flow-Risk-Budgeting-Framework-2025-12-3980169c5b498029b04ae49187e484fb?source=copy_link"
           target="_blank" rel="noopener noreferrer">Portfolio</a>
        <span>·</span>
        {diagnostics_link}
      </span>
    </footer>

  </main>

<script>
(() => {{
  const availableDates = {available_dates_json};
  const available = new Set(availableDates);
  const currentDate = "{esc(report_date)}";
  const latestDate = availableDates[availableDates.length - 1];

  const trigger = document.getElementById("report-date-trigger");
  const calendar = document.getElementById("report-calendar");
  const grid = document.getElementById("calendar-grid");
  const label = document.getElementById("calendar-month-label");
  const prevMonth = document.getElementById("calendar-prev-month");
  const nextMonth = document.getElementById("calendar-next-month");

  if (!trigger || !calendar || !grid || !label) return;

  const parts = currentDate.split("-").map(Number);
  let visibleYear = parts[0];
  let visibleMonth = parts[1] - 1;

  function targetHref(date) {{
    if (date === latestDate) {{
      return {str(is_latest_page).lower()}
        ? "index.html"
        : "../index.html";
    }}

    return {str(is_latest_page).lower()}
      ? `history/${{date}}.html`
      : `${{date}}.html`;
  }}

  function isoDate(year, month, day) {{
    return (
      String(year).padStart(4, "0") + "-" +
      String(month + 1).padStart(2, "0") + "-" +
      String(day).padStart(2, "0")
    );
  }}

  function renderCalendar() {{
    grid.innerHTML = "";

    const monthName = new Intl.DateTimeFormat(
      "en-US",
      {{ month: "long", year: "numeric" }}
    ).format(new Date(visibleYear, visibleMonth, 1));

    label.textContent = monthName;

    const firstWeekday = new Date(
      visibleYear,
      visibleMonth,
      1
    ).getDay();

    const daysInMonth = new Date(
      visibleYear,
      visibleMonth + 1,
      0
    ).getDate();

    for (let i = 0; i < firstWeekday; i += 1) {{
      const spacer = document.createElement("span");
      spacer.className = "calendar-day spacer";
      grid.appendChild(spacer);
    }}

    for (let day = 1; day <= daysInMonth; day += 1) {{
      const date = isoDate(visibleYear, visibleMonth, day);

      if (available.has(date)) {{
        const link = document.createElement("a");
        link.className = "calendar-day available";
        link.href = targetHref(date);
        link.textContent = String(day);
        link.setAttribute("aria-label", `Open report ${{date}}`);

        if (date === currentDate) {{
          link.classList.add("selected");
          link.setAttribute("aria-current", "date");
        }}

        grid.appendChild(link);
      }} else {{
        const disabled = document.createElement("span");
        disabled.className = "calendar-day unavailable";
        disabled.textContent = String(day);
        grid.appendChild(disabled);
      }}
    }}
  }}

  trigger.addEventListener("click", (event) => {{
    event.stopPropagation();

    const opening = calendar.hidden;
    calendar.hidden = !opening;
    trigger.setAttribute("aria-expanded", String(opening));

    if (opening) renderCalendar();
  }});

  prevMonth.addEventListener("click", (event) => {{
    event.stopPropagation();
    visibleMonth -= 1;

    if (visibleMonth < 0) {{
      visibleMonth = 11;
      visibleYear -= 1;
    }}

    renderCalendar();
  }});

  nextMonth.addEventListener("click", (event) => {{
    event.stopPropagation();
    visibleMonth += 1;

    if (visibleMonth > 11) {{
      visibleMonth = 0;
      visibleYear += 1;
    }}

    renderCalendar();
  }});

  calendar.addEventListener("click", (event) => {{
    event.stopPropagation();
  }});

  document.addEventListener("click", () => {{
    calendar.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
  }});

  document.addEventListener("keydown", (event) => {{
    if (event.key === "Escape") {{
      calendar.hidden = true;
      trigger.setAttribute("aria-expanded", "false");
      trigger.focus();
    }}
  }});
}})();
</script>

</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(page, encoding="utf-8")

    if build_diagnostics and diagnostics.exists():
        diag_text = diagnostics.read_text(encoding="utf-8")
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

        sew_class = diag_semantic_class(diag["sew"])
        deadman_class = diag_semantic_class(diag["deadman"])
        flow_class = diag_semantic_class(diag["flow_state"])
        positioning_class = diag_semantic_class(
            diag["f15_brake_drivers"]
        )
        gamma_class = diag_semantic_class(diag["gamma_state"])

        # Frozen F13 positioning rule, validated against Production.
        # Used only to expose an existing decision contribution.
        diag_pos_z = float(diag["f13_positioning_z"])
        if diag_pos_z >= 2.0:
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
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <main class="shell diagnostics-shell">

    <header class="topbar diagnostics-topbar">
      <div>
        <div class="eyebrow">MODEL OBSERVABILITY · CONTROL ROOM</div>
        <h1>Engine Diagnostics</h1>
        <div class="diag-asof">
          REPORT {esc(diag["date"])} · DATA AS OF {esc(diag["data_as_of"])}
        </div>
      </div>
      <a href="index.html">← PM View</a>
    </header>

    <section class="diag-status-grid">
      <article class="diag-status-card {{sew_class}}">
        <div class="label">STRUCTURAL EARLY WARNING</div>
        <strong>{esc(diag["sew"])}</strong>
      </article>

      <article class="diag-status-card {{deadman_class}}">
        <div class="label">HARD DEADMAN</div>
        <strong>{esc(diag["deadman"])}</strong>
      </article>

      <article class="diag-status-card {{flow_class}}">
        <div class="label">INSTITUTIONAL FLOW</div>
        <strong>{esc(diag["flow_state"])}</strong>
        <span>{esc(diag["flow_delta"])}</span>
      </article>

      <article class="diag-status-card diag-status-watch {{positioning_class}}">
        <div class="label">POSITIONING</div>
        <strong>POS_Z {esc(diag["positioning_z"])}</strong>
        <span>{esc(diag["f15_brake_drivers"])}</span>
      </article>
    </section>

    <section class="diag-primary-grid">

      <article class="panel diag-chain-panel">
        <div class="section-kicker">DECISION PATH</div>
        <h2>From Market State to Portfolio</h2>

        <div class="decision-chain">

          <div class="chain-node">
            <span>MARKET REGIME</span>
            <strong>{esc(diag["market_regime"])}</strong>
          </div>

          <div class="chain-arrow">↓</div>

          <div class="chain-node">
            <span>F13 · RISK BUDGET</span>
            <strong>{esc(diag["f13_risk_budget"])}</strong>
          </div>

          <div class="chain-arrow">↓</div>

          <div class="chain-node chain-node-watch {{positioning_class}}">
            <span>F15 · CONTROLLED EXPOSURE</span>
            <strong>{esc(diag["f15_exposure"])}</strong>
            <small>{esc(diag["f15_brake_drivers"])}</small>
          </div>

          <div class="chain-arrow">↓</div>

          <div class="chain-node">
            <span>FINAL ACTION</span>
            <strong>
              {esc(diag["final_action"])} · {esc(diag["final_exposure"])}
            </strong>
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
          <span>{esc(diag["market_regime"])}</span>
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
          <span>FLOW PERSISTENCE</span>
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
            {f13_positioning_impact:+d}
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

    <section class="diag-secondary-grid">

      <article class="panel">
        <div class="section-kicker">SUPPORTING RISK CONTEXT</div>
        <h2>Supporting Risk Context</h2>

        <div class="diag-context-row">
          <span>Credit / HY OAS</span>
          <strong>{esc(diag["hy_oas"])}</strong>
        </div>

        <div class="diag-context-row">
          <span>Geo Stress</span>
          <strong>{esc(diag["geo_score"])}</strong>
        </div>

        <div class="diag-context-row">
          <span>Pseudo Gamma</span>
          <strong class="{{gamma_class}}">{esc(diag["gamma_state"])}</strong>
        </div>
      </article>

      <article class="panel">
        <div class="section-kicker">OBSERVATION ONLY</div>
        <h2>Shadow Monitor</h2>

        <div class="engine-map">
          <div>
            <span>12.5 Growth Sustainability</span>
            <strong>{esc(diag["growth_shadow"])}</strong>
          </div>
          <div>
            <span>12.6 Flow Authenticity</span>
            <strong>{esc(diag["flow_auth_shadow"])}</strong>
          </div>
          <div>
            <span>12.7 Leadership Breadth</span>
            <strong>{esc(diag["breadth_shadow"])}</strong>
          </div>
          <div>
            <span>12.8 Positioning Stress</span>
            <strong>{esc(diag["positioning_shadow"])}</strong>
          </div>
        </div>

        <p class="shadow-disclaimer">
          Observation-only diagnostics. These states are not presented
          as independent portfolio decisions.
        </p>
      </article>

    </section>

    <details class="panel diag-raw-details">
      <summary>View Full Engine Diagnostics</summary>
      <pre class="diagnostics">{esc(diag_text)}</pre>
    </details>

  </main>
</body>
</html>
"""
        (SITE_DIR / "diagnostics.html").write_text(
            diag_page,
            encoding="utf-8",
        )

    print(f"[OK] Source: {source}")
    print(f"[OK] Site:   {output_path}")
    print(f"[OK] Sectors rendered: {len(sectors)}")
    print(f"[OK] Breadth rows rendered: {len(breadth_rows)}")
    print(f"[OK] Allocation rows rendered: {len(allocation_rows)}")


def build_historical_pm_pages() -> int:
    """
    Render persisted PM reports as static historical pages.

    Availability is defined strictly by the existence of a persisted
    daily_report_YYYY-MM-DD.md artifact. Historical rendering never
    recalculates Production state and never writes Diagnostics.
    """
    reports = sorted(REPORTS_DIR.glob("daily_report_????-??-??.md"))
    history_dir = SITE_DIR / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    for source in reports:
        report_date = source.stem.removeprefix("daily_report_")
        build(
            source=source,
            output_path=history_dir / f"{report_date}.html",
            build_diagnostics=False,
        )

    return len(reports)


if __name__ == "__main__":
    build()
    historical_count = build_historical_pm_pages()
    print(f"[OK] Historical PM pages: {historical_count}")
