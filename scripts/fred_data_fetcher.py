import pandas as pd
from fredapi import Fred

# FRED API 키 설정
API_KEY = 'your_fred_api_key'  # FRED에서 API 키를 발급받아 입력하세요
fred = Fred(api_key=API_KEY)

# FRED에서 필요한 데이터 가져오기
def get_fred_data():
    # T10Y2Y: 10년물과 2년물 금리 차이 (Yield Curve)
    t10y2y = fred.get_series('T10Y2Y')

    # T10YIE: 10년 기대 인플레이션 (10-year breakeven inflation rate)
    t10yie = fred.get_series('T10YIE')

    # VIXCLS: VIX 지수 (Volatility Index)
    vix = fred.get_series('VIXCLS')

    # 데이터 병합
    data = pd.DataFrame({
        'T10Y2Y': t10y2y,
        'T10YIE': t10yie,
        'VIX': vix
    })

    # 데이터 확인 (마지막 5행 출력)
    print(data.tail())

    return data

# FRED 데이터를 가져오고 CSV로 저장
def save_fred_data_to_csv():
    data = get_fred_data()
    data.to_csv('data/fred_data.csv', index=True)  # 저장 경로 지정
    print("FRED 데이터가 'data/fred_data.csv'에 저장되었습니다.")

if __name__ == "__main__":
    save_fred_data_to_csv()