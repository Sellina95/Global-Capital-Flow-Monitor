import requests
from bs4 import BeautifulSoup


def fetch_expectation_data():
    url = "https://www.investing.com/economic-calendar/"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"[DEBUG] fetch_expectation_data() ERROR: {type(e).__name__} {e}")
        return []

    try:
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"[DEBUG] BeautifulSoup ERROR: {type(e).__name__} {e}")
        return []

    events_table = soup.find("table", {"id": "economicCalendarData"})

    if not events_table:
        print("[DEBUG] Economic Calendar table not found.")
        return []

    rows = events_table.find_all("tr")

    data = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        try:
            time = cols[0].get_text(strip=True)
            currency = cols[1].get_text(strip=True)
            event_name = cols[2].get_text(strip=True)
            actual = cols[3].get_text(strip=True)
            forecast = cols[4].get_text(strip=True)
            previous = cols[5].get_text(strip=True) if len(cols) > 5 else None
        except Exception:
            continue

        # 🔹 발언/연설류 제외
        name_lower = event_name.lower()
        if any(k in name_lower for k in ["speaks", "speech", "testifies", "remarks"]):
            continue

        # 🔹 숫자 이벤트만 usable 대상으로
        if actual in (None, "", "N/A") or forecast in (None, "", "N/A"):
            continue

        data.append({
            "time": time,
            "currency": currency,
            "event": event_name,
            "actual": actual,
            "forecast": forecast,
            "previous": previous,
        })

    # 🔎 DEBUG
    print(f"[DEBUG] usable events count: {len(data)}")
    if len(data) > 0:
        print(f"[DEBUG] sample usable event: {data[0]}")

    return data

