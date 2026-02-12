import requests
from bs4 import BeautifulSoup

# Investing.com에서 주요 지표 데이터를 가져오는 함수
def fetch_investing_data():
    # 예시: 미국 10년물 금리, 달러 인덱스, 유가, 변동성 지수, 원/달러 환율
    url = "https://www.investing.com/economic-calendar/"
    
    # HTTP 요청 보내기
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Failed to fetch data")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 경제 지표 데이터 추출하기
    data = {}
    
    # 예시로 몇 가지 주요 지표를 가져옵니다. 실제로는 필요한 지표에 맞게 클래스명을 수정하세요.
    try:
        us10y_rate = soup.find('tr', {'data-row-key': '10yearTreasuryYield'}).find_all('td')[1].text.strip()
        dxy = soup.find('tr', {'data-row-key': 'dollarIndex'}).find_all('td')[1].text.strip()
        wti = soup.find('tr', {'data-row-key': 'wtiCrudeOil'}).find_all('td')[1].text.strip()
        vix = soup.find('tr', {'data-row-key': 'vix'}).find_all('td')[1].text.strip()
        usdkrw = soup.find('tr', {'data-row-key': 'usDkrw'}).find_all('td')[1].text.strip()

        data['US10Y'] = us10y_rate
        data['DXY'] = dxy
        data['WTI'] = wti
        data['VIX'] = vix
        data['USDKRW'] = usdkrw
        
    except Exception as e:
        print(f"Error while fetching data: {e}")
        return None
    
    return data

# fetch_investing_data 예시 사용
if __name__ == "__main__":
    data = fetch_investing_data()
    if data:
        print("Fetched Data:")
        for key, value in data.items():
            print(f"{key}: {value}")
