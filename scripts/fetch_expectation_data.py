import requests
from bs4 import BeautifulSoup

def fetch_expectation_data():
    url = "https://www.investing.com/economic-calendar/"  # Example URL for economic calendar
    
    # 요청 보내기
    response = requests.get(url)
    response.raise_for_status()  # 요청에 문제가 있으면 에러 발생
    
    # HTML 파싱
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 예상치와 실제값을 포함하는 테이블 찾기 (테이블 클래스는 웹 페이지 구조에 맞게 변경 필요)
    events_table = soup.find('table', {'class': 'economicCalendarTable'})
    rows = events_table.find_all('tr')
    
    # 예시로 금리 인상 확률과 같은 경제 지표의 예상치 추출
    data = []
    for row in rows:
        cols = row.find_all('td')
        if len(cols) > 5:
            event_name = cols[1].get_text(strip=True)
            actual = cols[2].get_text(strip=True)  # 실제 발표 값
            forecast = cols[3].get_text(strip=True)  # 예상치
            previous = cols[4].get_text(strip=True)  # 이전 발표 값

            # 데이터 리스트에 저장
            data.append({
                'event': event_name,
                'forecast': forecast,
                'actual': actual,
                'previous': previous,
            })

    return data
