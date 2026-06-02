import os
import pandas as pd
import matplotlib.pyplot as plt

def make_my_charts(csv_path="daily_macro_data.csv"):
    """
    세연 님의 매일 쌓이는 CSV 파일을 읽어 명품 차트 2종을 생성하고 
    마크다운 리포트에 결합할 수 있도록 이미지를 저장하는 독립형 함수
    """
    # 1. 파일 존재 여부 체크 안전장치
    if not os.path.exists(csv_path):
        print(f"⚠️ 에러: {csv_path} 파일을 찾을 수 없습니다. 경로를 확인해 주세요!")
        return

    # 2. 데이터 로드 및 날짜 정렬
    df = pd.read_csv(csv_path)
    
    # 💡 세연 님 CSV 파일의 실제 컬럼명에 맞게 대소문자를 맞춰주세요!
    # 예: 'Date'가 아니라 'date'라면 소문자로 수정
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)
    else:
        print("⚠️ 경고: CSV에 'Date' 컬럼이 없습니다.")
        return

    print(f"📊 {csv_path} 읽기 성공! 차트 작성을 시작합니다... (데이터 수: {len(df)}개)")

    # ----------------------------------------------------
    # CHART 1: 유동성 3총사 누적 영역 차트 (WALCL vs TGA & RRP)
    # ----------------------------------------------------
    required_c1 = ['WALCL', 'TGA', 'RRP']
    if all(col in df.columns for col in required_c1):
        plt.figure(figsize=(10, 5))
        
        # 전체 연준 자산 (검은 선)
        plt.plot(df['Date'], df['WALCL'], color='#333333', linewidth=2, label='WALCL (Fed Total Assets)')
        
        # TGA와 RRP를 쌓아서 영역 채우기
        plt.stackplot(df['Date'], df['TGA'], df['RRP'], 
                      labels=['TGA (Gov Account)', 'RRP (Reverse Repo)'],
                      colors=['#ff9999', '#cccccc'], alpha=0.7)
        
        plt.title("Fed Plumbing: WALCL vs TGA & RRP Stacked Chart", fontsize=12, fontweight='bold')
        plt.xlabel("Date")
        plt.ylabel("USD Value")
        plt.legend(loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.tight_layout()
        
        # 깃허브 레포 내에 항상 같은 이름으로 덮어쓰기 저장
        plt.savefig('liquidity_3_musketeers.png', dpi=300)
        plt.close()
        print("✅ Chart 1 (누적 영역 차트) 저장 완료!")
    else:
        print(f"⏭️ Chart 1 스킵: 필요한 컬럼{required_c1}이 데이터에 부족합니다.")

    # ----------------------------------------------------
    # CHART 2: 실제 달러 체력(NET_LIQ) vs 주가지수(SPY) 이중 축 차트
    # ----------------------------------------------------
    if 'NET_LIQ' in df.columns:
        # 주가지수 컬럼명 자동 매칭 (SPY 또는 CLOSE 또는 다른 이름)
        spy_col = None
        for col in ['SPY', 'CLOSE', 'Spy', 'close']:
            if col in df.columns:
                spy_col = col
                break
        
        if spy_col:
            fig, ax1 = plt.subplots(figsize=(10, 5))
            
            # 왼쪽축: NET_LIQ (초록색)
            color = '#2ca02c'
            ax1.set_xlabel('Date')
            ax1.set_ylabel('NET_LIQ', color=color, fontweight='bold')
            ax1.plot(df['Date'], df['NET_LIQ'], color=color, linewidth=2.5, label='NET_LIQ')
            ax1.tick_params(axis='y', labelcolor=color)
            ax1.grid(True, linestyle='--', alpha=0.3)

            # 오른쪽축: 주가지수 (파란색)
            ax2 = ax1.twinx()
            color = '#1f77b4'
            ax2.set_ylabel(f'{spy_col} Index', color=color, fontweight='bold')
            ax2.plot(df['Date'], df[spy_col], color=color, linewidth=2, label=spy_col)
            ax2.tick_params(axis='y', labelcolor=color)

            plt.title("Market Liquidity (NET_LIQ) vs Stock Index", fontsize=12, fontweight='bold')
            fig.tight_layout()
            
            # 깃허브 레포 내에 항상 같은 이름으로 덮어쓰기 저장
            plt.savefig('net_liq_vs_spy.png', dpi=300)
            plt.close()
            print("✅ Chart 2 (이중 축 지수 비교 차트) 저장 완료!")
        else:
            print("⏭️ Chart 2 스킵: 주가지수(SPY/CLOSE 등) 컬럼을 찾을 수 없습니다.")
    else:
        print("⏭️ Chart 2 스킵: NET_LIQ 컬럼이 데이터에 없습니다.")

if __name__ == "__main__":
    # 💡 세연 님이 매일 파이썬으로 떨어뜨리는 실제 CSV 파일 이름을 여기에 정확히 적어주세요!
    # 예: 'macro_history_2026.csv' 등등
    TARGET_CSV = "daily_macro_data.csv" 
    make_my_charts(TARGET_CSV)
