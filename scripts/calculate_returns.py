import pandas as pd

def calculate_returns(etf_symbols):
    # 예시로 각 ETF 심볼에 대해 종가 가격을 받아 수익률 계산
    etf_data = {}  # etf 심볼별 데이터 저장
    for symbol in etf_symbols:
        # 데이터 수집하고 수익률 계산 로직 추가
        # 예시: 데이터를 받아와서 수익률 계산
        etf_data[symbol] = calculate_somehow(symbol)  # 실제 계산 함수 필요

    return etf_data

def save_to_csv(etf_data):
    # 계산된 수익률을 CSV로 저장
    df = pd.DataFrame(etf_data)
    df.to_csv("data/etf_returns.csv", index=False)

if __name__ == "__main__":
    etf_symbols = ["BND", "EEM", "EWJ", "SPY", "VXX"]  # 예시 ETF 리스트
    etf_data = calculate_returns(etf_symbols)
    save_to_csv(etf_data)