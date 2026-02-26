# scripts/repair_macro_csv.py
from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "macro_data.csv"

# ✅ 너가 현재 macro_data에 넣는 "정답 컬럼"을 여기 고정
EXPECTED_COLS = [
    "date",
    "US10Y", "DXY", "WTI", "VIX", "USDKRW", "HYG", "LQD",
    "XLK", "XLF", "XLE", "XLRE",
]

def repair_csv(path: Path) -> None:
    if (not path.exists()) or path.stat().st_size == 0:
        print("[SKIP] macro_data.csv not found or empty.")
        return

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        print("[SKIP] macro_data.csv has no lines.")
        return

    # 헤더 파싱
    header = lines[0].split(",")
    header = [h.strip() for h in header if h.strip()]

    # 헤더가 date부터 시작한다고 가정
    # 헤더에 EXPECTED_COLS 없는 것 붙이기
    final_header = header[:]
    for c in EXPECTED_COLS:
        if c not in final_header:
            final_header.append(c)

    target_n = len(final_header)

    fixed = []
    fixed.append(",".join(final_header))

    # 각 row를 target_n으로 pad/truncate
    for i, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        parts = line.split(",")

        # 너무 짧으면 빈칸 padding
        if len(parts) < target_n:
            parts = parts + [""] * (target_n - len(parts))

        # 너무 길면 잘라내기 (보통 header 부족으로 생긴 extra 필드)
        elif len(parts) > target_n:
            parts = parts[:target_n]

        fixed.append(",".join(parts))

    # 원본 백업
    bak = path.with_suffix(".csv.bak")
    bak.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 정규화 저장
    path.write_text("\n".join(fixed) + "\n", encoding="utf-8")
    print(f"[OK] macro_data.csv repaired. backup saved -> {bak}")

if __name__ == "__main__":
    repair_csv(CSV_PATH)
