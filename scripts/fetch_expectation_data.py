import re
import datetime as dt
import requests
from bs4 import BeautifulSoup


AJAX_URL = "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
HOME_URL = "https://www.investing.com/"


def _to_float(x: str):
    if x is None:
        return None
    s = str(x).strip()
    if not s or s in ("-", "N/A"):
        return None

    # remove commas, percent, etc.
    s = s.replace(",", "").replace("%", "").strip()

    # handle K/M/B
    m = re.match(r"^(-?\d+(\.\d+)?)([KMB])$", s, re.IGNORECASE)
    if m:
        val = float(m.group(1))
        unit = m.group(3).upper()
        if unit == "K":
            return val * 1_000
        if unit == "M":
            return val * 1_000_000
        if unit == "B":
            return val * 1_000_000_000
        return val

    # plain number
    try:
        return float(s)
    except Exception:
        return None


def fetch_expectation_data(
    days_back: int = 0,
    days_forward: int = 1,
    countries: list[str] | None = None,
    time_zone: str = "55",  # Investing internal TZ id; not critical for our use
    limit_from: int = 0,
):
    """
    Fetch Investing.com economic calendar via AJAX endpoint (works even when HTML table is JS-rendered).
    Returns: list[dict]
      keys: time, currency, event, importance, actual, forecast, previous
    """

    # Default: United States only (country id commonly "5")
    if countries is None:
        countries = ["5"]

    today = dt.date.today()
    date_from = (today - dt.timedelta(days=days_back)).strftime("%Y-%m-%d")
    date_to = (today + dt.timedelta(days=days_forward)).strftime("%Y-%m-%d")

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.investing.com/economic-calendar/",
        "Origin": "https://www.investing.com",
    }

    s = requests.Session()

    # 1) warm-up to set cookies (helps reduce 403)
    s.get(HOME_URL, headers=headers, timeout=20)

    payload = {
        "dateFrom": date_from,
        "dateTo": date_to,
        "timeZone": time_zone,
        "timeFilter": "timeRemain",
        "currentTab": "custom",
        "limit_from": str(limit_from),
    }

    # repeated keys for country[]
    # requests supports lists for same key
    payload["country[]"] = countries

    r = s.post(AJAX_URL, data=payload, headers=headers, timeout=25)
    r.raise_for_status()

    j = r.json()
    html = j.get("data")
    if not html or not isinstance(html, str):
        raise ValueError("Investing AJAX returned empty 'data' HTML.")

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr")
    if not rows:
        raise ValueError("No rows found in Investing AJAX HTML.")

    out = []
    for tr in rows:
        tds = tr.select("td")
        if len(tds) < 6:
            continue

        # Investing calendar row typical columns:
        # 0 time | 1 currency | 2 importance | 3 event | 4 actual | 5 forecast | 6 previous (sometimes)
        time_txt = tds[0].get_text(strip=True) if len(tds) > 0 else ""
        cur_txt = tds[1].get_text(strip=True) if len(tds) > 1 else ""
        imp_td = tds[2] if len(tds) > 2 else None
        event_txt = tds[3].get_text(strip=True) if len(tds) > 3 else ""
        actual_txt = tds[4].get_text(strip=True) if len(tds) > 4 else ""
        forecast_txt = tds[5].get_text(strip=True) if len(tds) > 5 else ""
        previous_txt = tds[6].get_text(strip=True) if len(tds) > 6 else ""

        # importance: count "sentiment" icons if present
        importance = None
        if imp_td is not None:
            # Many implementations use <i class="grayFullBullishIcon"> etc.
            importance = len(imp_td.select("i"))
            if importance == 0:
                # fallback: sometimes spans
                importance = len(imp_td.select("span"))

        out.append(
            {
                "time": time_txt,
                "currency": cur_txt,
                "event": event_txt,
                "importance": importance,
                "actual": _to_float(actual_txt),
                "forecast": _to_float(forecast_txt),
                "previous": _to_float(previous_txt),
            }
        )

    return out
    if __name__ == "__main__":
    data = fetch_expectation_data()
    print("[DEBUG] expectations list len:", len(data))
    for i, item in enumerate(data):
        print(f"[DEBUG] item[{i}]:", item)

