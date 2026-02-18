import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


def _safe_text(td):
    return td.get_text(strip=True) if td else None


def fetch_expectation_data():
    """
    Fetch economic calendar events from Investing.com via its AJAX endpoint.
    Returns: list[dict] with keys:
      - time, currency, event, importance, actual, forecast, previous
    """

    base_url = "https://www.investing.com/economic-calendar/"
    ajax_url = "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"

    headers_base = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": base_url,
    }

    s = requests.Session()

    # 1) First GET to set cookies/session
    try:
        r0 = s.get(base_url, headers=headers_base, timeout=15)
        r0.raise_for_status()
    except Exception as e:
        print(f"[DEBUG] fetch_expectation_data() ERROR: initial GET failed: {type(e).__name__} {e}")
        return []

    # 2) POST to AJAX endpoint
    # date range: today -> today+1 (Investing expects mm/dd/YYYY)
    today = datetime.utcnow().date()
    date_from = today.strftime("%m/%d/%Y")
    date_to = (today + timedelta(days=1)).strftime("%m/%d/%Y")

    payload = {
        # typical params used by Investing calendar
        "dateFrom": date_from,
        "dateTo": date_to,
        "timeZone": "55",          # 55 is often "GMT" in their internal mapping; ok as placeholder
        "timeFilter": "timeRemain",
        "currentTab": "custom",
        "limit_from": 0,
    }

    headers_ajax = {
        **headers_base,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    }

    try:
        r = s.post(ajax_url, data=payload, headers=headers_ajax, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[DEBUG] fetch_expectation_data() ERROR: AJAX POST failed: {type(e).__name__} {e}")
        return []

    # 3) Parse JSON -> HTML fragment
    try:
        j = r.json()
    except Exception as e:
        print(f"[DEBUG] fetch_expectation_data() ERROR: JSON parse failed: {type(e).__name__} {e}")
        return []

    html = j.get("data") or j.get("html") or ""
    if not html or not isinstance(html, str):
        print("[DEBUG] fetch_expectation_data() ERROR: AJAX returned no HTML fragment.")
        return []

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")

    out = []
    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue

        # Investing markup varies. We try to be resilient:
        time = _safe_text(tds[0])
        currency = _safe_text(tds[1])
        event = _safe_text(tds[2])

        # Importance: often represented by icons/spans; fallback = count of "bull" icons if present
        importance = 0
        try:
            # common: <i class="grayFullBullishIcon"> or similar
            importance = len(tr.select("i.grayFullBullishIcon, i.bullishIcon, i.fullBullishIcon"))
            if importance == 0:
                # some layouts use spans
                importance = len(tr.select("span.grayFullBullishIcon, span.bullishIcon, span.fullBullishIcon"))
        except Exception:
            importance = 0

        # columns for actual/forecast/previous may shift; we try typical positions:
        actual = _safe_text(tds[3]) if len(tds) > 3 else None
        forecast = _safe_text(tds[4]) if len(tds) > 4 else None
        previous = _safe_text(tds[5]) if len(tds) > 5 else None

        # filter out speech/remarks
        if event:
            low = event.lower()
            if any(k in low for k in ["speaks", "speech", "testifies", "remarks"]):
                continue

        out.append(
            {
                "time": time,
                "currency": currency,
                "event": event,
                "importance": importance,
                "actual": actual if actual not in ("", "N/A", "-", "—") else None,
                "forecast": forecast if forecast not in ("", "N/A", "-", "—") else None,
                "previous": previous if previous not in ("", "N/A", "-", "—") else None,
            }
        )

    print(f"[DEBUG] fetch_expectation_data() AJAX events count: {len(out)}")
    if out:
        print(f"[DEBUG] sample event: {out[0]}")

    return out
