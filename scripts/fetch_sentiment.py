import requests
import re
from typing import Optional


CNN_URL = "https://edition.cnn.com/markets/fear-and-greed"


def fetch_cnn_fear_greed() -> Optional[float]:
    """
    CNN Fear & Greed Index 크롤링
    실패 시 None 반환
    """

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(CNN_URL, headers=headers, timeout=10)
        html = response.text

        match = re.search(r'"fear_and_greed":{"score":(\d+)', html)

        if match:
            value = float(match.group(1))
            print(f"[OK] Fear & Greed fetched: {value}")
            return value

        print("[WARN] Fear & Greed pattern not found")

    except Exception as e:
        print(f"[Sentiment Error] {e}")

    return None
