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


def esc(value: object) -> str:
    return html.escape(str(value))


def build() -> None:
    source = latest_pm_report()
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

    diagnostics = REPORTS_DIR / f"engine_diagnostics_{report_date}.md"
    diagnostics_link = (
        '<a href="diagnostics.html">Engine Diagnostics</a>'
        if diagnostics.exists()
        else '<span>Engine Diagnostics unavailable</span>'
    )

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

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
        <h1>Global Capital Flow Monitor</h1>
      </div>

      <div class="asof">
        <span>REPORT {esc(report_date)}</span>
        <strong>DATA AS OF {esc(data_as_of)}</strong>
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
</body>
</html>
"""

    (SITE_DIR / "index.html").write_text(page, encoding="utf-8")

    if diagnostics.exists():
        diag_text = diagnostics.read_text(encoding="utf-8")

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
    <header class="topbar">
      <div>
        <div class="eyebrow">MODEL OBSERVABILITY</div>
        <h1>Engine Diagnostics</h1>
      </div>
      <a href="index.html">← PM View</a>
    </header>

    <pre class="diagnostics">{esc(diag_text)}</pre>
  </main>
</body>
</html>
"""
        (SITE_DIR / "diagnostics.html").write_text(
            diag_page,
            encoding="utf-8",
        )

    print(f"[OK] Source: {source}")
    print(f"[OK] Site:   {SITE_DIR / 'index.html'}")
    print(f"[OK] Sectors rendered: {len(sectors)}")
    print(f"[OK] Breadth rows rendered: {len(breadth_rows)}")
    print(f"[OK] Allocation rows rendered: {len(allocation_rows)}")


if __name__ == "__main__":
    build()
