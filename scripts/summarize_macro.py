# scripts/summarize_macro.py

from pathlib import Path
from datetime import datetime
import pandas as pd


# 경로 설정
ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "macro_data.csv"
OUT_PATH = ROOT / "insights" / "daily_summary.txt"


def format_change(curr: float, prev: float):
    """현재 값과 이전 값 차이를 (+0.12 / -0.34 이런 형식)으로 반환"""
    if prev is None:
        return "", ""
    diff = curr - prev
    diff_pct = (diff / prev) * 100 if prev != 0 else 0.0
    sign = "+" if diff >= 0 else "-"
    return f"{sign}{abs(diff):.3f}", f"{sign}{abs(diff_pct):.2f}%"


def main():
    df = pd.read_csv(CSV_PATH)
    if df.empty:
        raise SystemExit("macro_data.csv 에 데이터가 없습니다.")

    # datetime 컬럼을 문자열 그대로 쓰되, 마지막 행을 기준으로 사용
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else None

    def get_prev(col):
        return prev[col] if prev is not None else None

    # 현재 값
    us10y = float(last["US10Y"])
    dxy = float(last["DXY"])
    wti = float(last["WTI"])
    vix = float(last["VIX"])
    usdkrw = float(last["USDKRW"])

    # 전일 대비 변화
    us10y_diff, us10y_pct = format_change(us10y, get_prev("US10Y"))
    dxy_diff, dxy_pct = format_change(dxy, get_prev("DXY"))
    wti_diff, wti_pct = format_change(wti, get_prev("WTI"))
    vix_diff, vix_pct = format_change(vix, get_prev("VIX"))
    usd_diff, usd_pct = format_change(usdkrw, get_prev("USDKRW"))

    # 날짜 포맷(한국 기준으로 보이게 그냥 날짜만 써도 충분)
    dt_str = str(last["datetime"])
    try:
        dt_parsed = datetime.fromisoformat(str(last["datetime"]))
        dt_str = dt_parsed.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    # --- 여기서 “3줄 요약” 텍스트 생성 ---
    line1 = (
        f"[{dt_str}] US 10Y는 {us10y:.2f}% "
        + (f"({us10y_diff}p)" if us10y_diff else "(전일 데이터 없음)")
        + f", DXY는 {dxy:.2f} "
        + (f"({dxy_pct})" if dxy_pct else "")
        + " 입니다."
    )

    line2 = (
        f"WTI 유가는 배럴당 {wti:.2f}달러"
        + (f" ({wti_pct})" if wti_pct else "")
        + ", 변동성 지수(VIX)는 {vix:.2f}"
        + (f" ({vix_pct})" if vix_pct else "")
        + " 수준입니다."
    )

    line3 = (
        f"원/달러 환율은 {usdkrw:.2f}원"
        + (f" ({usd_pct})" if usd_pct else "")
        + "으로, 하루 단위 글로벌 자본 흐름을 요약한 수치입니다."
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        f.write(line1 + "\n")
        f.write(line2 + "\n")
        f.write(line3 + "\n")

    print("✅ Saved daily summary to", OUT_PATH)


if __name__ == "__main__":
    main()

