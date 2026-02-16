# scripts/fetch_expectation_data.py
from __future__ import annotations

import time
from typing import List, Dict, Any

import requests
from bs4 import BeautifulSoup


CAL_URL = "https://www.investing.com/economic-calendar/"
HOME_URL = "https://www.investing.com/"


def fetch_expectation_data() -> List[Dict[str, Any]]:
    """
    Fetch expectation-like data from Investing.com economic calendar.

    NOTE:
    - GitHub Actions 환경에서는 Investing이 403(봇 차단)을 줄 수 있음.
    - 헤더/쿠키 세팅으로 우회 시도하지만, Cloudflare 정책에 따라 실패할 수 있음.
    """
    session = requests.Session()

    # 브라우저 흉내 헤더 (최소 세트)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": HOME_URL,
        "Connection": "keep-alive",
    }

    # 1) 홈 한번 찍어서 쿠키/세션 받기 (안 하면 403 잘 남)
    session.get(HOME_URL, headers=headers, timeout=20)

    # 2) 캘린더 요청 (403면 재시도)
    last_err = None
    for attempt in range(3):
        try:
            r = session.get(CAL_URL, headers=headers, timeout=25)
            r.raise_for_status()
            html = r.text
            break
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    else:
        # 여기로 오면 3번 다 실패
        raise RuntimeError(f"Investing calendar fetch failed after retries: {type(last_err).__name__}: {last_err}")

    soup = BeautifulSoup(html, "html.parser")

    # Investing 페이지 구조가 바뀌거나 JS 렌더링이면 table이 없을 수 있음
    events_table = soup.find("table", {"class": "economicCalendarTable"})
    if not events_table:
        # HTML 일부를 힌트로 남겨서 디버깅 가능하게
        title = soup.title.get_text(strip=True) if soup.title else "N/A"
        raise ValueError(f"Economic Calendar table not found. page_title={title}")

    rows = events_table.find_all("tr")
    data: List[Dict[str, Any]] = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) > 5:
            event_name = cols[1].get_text(strip=True)
            actual = cols[2].get_text(strip=True)
            forecast = cols[3].get_text(strip=True)
            previous = cols[4].get_text(strip=True)

            # 비어있는 라인 제거
            if not event_name:
                continue

            data.append(
                {
                    "event": event_name,
                    "forecast": forecast,
                    "actual": actual,
                    "previous": previous,
                    "source": "investing_economic_calendar",
                }
            )

    return data
