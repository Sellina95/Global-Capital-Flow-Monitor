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

        # CNN 페이지 내부 JSON 패턴에서 score 추출
        match = re.search(r'"fear_and_greed":{"score":(\d+)', html)

        if match:
            return float(match.group(1))

    except Exception as e:
        print(f"[Sentiment Error] {e}")

    return None
