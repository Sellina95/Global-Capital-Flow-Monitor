# scripts/test_geo_ew_events.py
from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd

# ✅ 너 프로젝트에 이미 있는 함수들 import
from scripts.generate_report import load_macro_df
from filters.strategist_filters import attach_geopolitical_ew_layer


def _find_nearest_idx_by_date(df: pd.DataFrame, target: str) -> int:
    """
    target 날짜가 정확히 없을 수도 있어서 (주말/휴장/결측)
    <= target 중 가장 가까운 날짜 row를 선택
    """
    t = pd.to_datetime(target, errors="coerce")
    if pd.isna(t):
        raise ValueError(f"Bad date: {target}")

    # df["date"]는 load_macro_df에서 datetime으로 보장
    s = pd.to_datetime(df["date"], errors="coerce")
    df2 = df.copy()
    df2["__dt"] = s
    df2 = df2.dropna(subset=["__dt"]).sort_values("__dt").reset_index(drop=True)

    # target 이전 중 가장 최근
    le = df2[df2["__dt"] <= t]
    if le.empty:
        # target 이전이 하나도 없으면 가장 첫 row
        return 0

    return int(le.index[-1])


def _pretty_top_drivers(geo: Dict[str, Any], top_n: int = 6) -> List[str]:
    comps = geo.get("components", []) or []
    comps_sorted = sorted(
        comps,
        key=lambda x: abs(float(x.get("contrib", 0.0))),
        reverse=True,
    )
    out = []
    for c in comps_sorted[:top_n]:
        key = c.get("key")
        z_used = c.get("z_used")
        w = c.get("weight")
        contrib = c.get("contrib")
        out.append(f"- {key}: z_used={z_used:+.2f} (w={w:.2f}) → contrib={contrib:+.2f}")
    return out


def run() -> None:
    df = load_macro_df()
    if df is None or df.empty:
        raise RuntimeError("macro df is empty")

    # ✅ 여기만 바꿔가면서 테스트하면 됨
    events = [
        ("2022-02-24", "러시아 침공"),
        ("2023-10-07", "가자 전쟁"),
        ("2024-01-12", "홍해 공격"),
    ]

    print("== GEO_EW Event Backtest (no side effects) ==")
    print(f"df rows={len(df)} | range: {df['date'].min()} ~ {df['date'].max()}")
    print("")

    for d, label in events:
        idx = _find_nearest_idx_by_date(df, d)
        used_date = pd.to_datetime(df.iloc[idx]["date"]).strftime("%Y-%m-%d")

        market_data: Dict[str, Any] = {}
        # ✅ 기존 엔진과 동일하게 계산 (단지 today_idx만 과거 idx로)
        attach_geopolitical_ew_layer(market_data, df, idx)

        geo = market_data.get("GEO_EW", {}) or {}
        score = geo.get("score")
        level = geo.get("level")
        missing = geo.get("missing", []) or []

        print(f"[{label}] target={d} | used={used_date} | idx={idx}")
        print(f"  score={None if score is None else f'{score:+.2f}'} | level={level}")
        print("  Top drivers:")
        for line in _pretty_top_drivers(geo, top_n=6):
            print(" ", line)

        # ✅ 항상 missing 출력 (너가 원하던 형태)
        print("  Missing/Skipped:", ", ".join(missing) if missing else "None")
        print("")


if __name__ == "__main__":
    run()
