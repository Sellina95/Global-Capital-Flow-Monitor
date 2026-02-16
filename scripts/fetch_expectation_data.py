import requests
from bs4 import BeautifulSoup


def fetch_expectation_data():
    """
    Fetch economic calendar expectation data from Investing.com.

    Returns:
        list[dict]
            [
              {
                "time": "13:25",
                "currency": "USD",
                "event": "FOMC Member Bowman Speaks",
                "importance": 3,
                "actual": None,
                "forecast": None,
                "previous": None,
              },
              ...
            ]

    Notes:
      - GitHub Actions 환경에서 403 방지를 위해 헤더 추가
      - lxml 없이 html.parser 사용
      - 테이블 구조 변경 가능성 대비 방어 로직 포함
    """

    url = "https://www.investing.com/economic-calendar/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.investing.com/",
        "Connection": "keep-alive",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # 1️⃣ 기본 테이블 찾기
    events_table = soup.find("table", {"class": "economicCalendarTable"})

    # 2️⃣ class 구조가 바뀐 경우 방어
    if not events_table:
        for t in soup.find_all("table"):
            cls = " ".join(t.get("class", []))
            if "economicCalendarTable" in cls:
                events_table = t
                break

    if not events_table:
        title = soup.title.get_text(strip=True) if soup.title else None
        raise ValueError(f"Economic Calendar table not found. page_title={title}")

    rows = events_table.find_all("tr")
    data = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        def safe_text(i):
            if i >= len(cols):
                return None
            txt = cols[i].get_text(strip=True)
            return txt if txt else None

        time_txt = safe_text(0)
        currency = safe_text(1)
        event_name = safe_text(2)
        actual = safe_text(3)
        forecast = safe_text(4)
        previous = safe_text(5) if len(cols) > 5 else None

        if not event_name:
            continue

        # 중요도 계산 (별 아이콘 개수 기반)
        importance = 0
        try:
            importance = len(row.find_all(class_="grayFullBullishIcon")) + \
                         len(row.find_all(class_="redFullBullishIcon"))
        except Exception:
            importance = 0

        data.append(
            {
                "time": time_txt,
                "currency": currency,
                "event": event_name,
                "importance": int(importance),
                "actual": actual,
                "forecast": forecast,
                "previous": previous,
            }
        )

    return data


# -------------------------
# Debug (GitHub Actions 로그 확인용)
# -------------------------
if __name__ == "__main__":
    try:
        events = fetch_expectation_data()
        print("[DEBUG] fetch_expectation_data() type:", type(events))
        print("[DEBUG] expectations list len:", len(events))
        if events:
            print("[DEBUG] first item:", events[0])
    except Exception as e:
        print("[DEBUG] fetch_expectation_data() ERROR:", type(e).__name__, str(e))
        raise


