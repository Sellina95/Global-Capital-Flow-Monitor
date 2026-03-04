# experiments/geo/test_geo_events.py
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
IN_CSV = EXP_DATA_DIR / "geo_history.csv"

# ✅ 너의 7.2 로직을 "실험용으로만" 최소 구현 (프로덕션 파일 import 안 함)
GEO_WINDOW = 60

# (key, weight, transform)
# transform: "normal" | "inverse"
GEO_FACTORS = [
    ("VIX",    0.18, "normal"),
    ("WTI",    0.10, "normal"),
    ("GOLD",   0.12, "normal"),
    ("USDCNH", 0.18, "normal"),

    ("USDMXN", 0.05, "normal"),
    ("USDJPY", 0.05, "inverse"),
]

GEO_THRESHOLDS = [
    ("NORMAL",   -0.75, 0.75),
    ("ELEVATED",  0.75, 1.50),
    ("HIGH",      1.50, 2.50),
    ("CONFLICT",  2.50, 99.0),
]


def _pct_series(df: pd.DataFrame, col: str) -> pd.Series:
    s = pd.to_numeric(df[col], errors="coerce")
    return s.pct_change() * 100.0


def _z_last(series: pd.Series, window: int) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < max(10, min(window, 20)):
        return None
    tail = s.tail(window)
    mu = float(tail.mean())
    sd = float(tail.std(ddof=0))
    if sd == 0:
        return None
    return float((tail.iloc[-1] - mu) / sd)


def _level_from_score(score: Optional[float]) -> str:
    if score is None:
        return "N/A"
    for name, lo, hi in GEO_THRESHOLDS:
        if score >= lo and score < hi:
            return name
    return "N/A"


def compute_geo_score(df: pd.DataFrame, as_of: str) -> Dict[str, Any]:
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    as_of_dt = pd.to_datetime(as_of)
    d = d[d["date"] <= as_of_dt].copy()
    if d.empty:
        return {"as_of": as_of, "score": None, "level": "N/A", "missing": ["ALL"], "components": []}

    raw_score = 0.0
    used_weight = 0.0
    missing: List[str] = []
    comps: List[Dict[str, Any]] = []

    for key, w, transform in GEO_FACTORS:
        if key not in d.columns:
            missing.append(key)
            continue

        z = _z_last(_pct_series(d, key), GEO_WINDOW)
        if z is None:
            missing.append(key)
            continue

        z_used = -z if transform == "inverse" else z
        contrib = float(w) * float(z_used)

        raw_score += contrib
        used_weight += float(w)

        comps.append({
            "key": key,
            "weight": float(w),
            "z": float(z),
            "z_used": float(z_used),
            "contrib": float(contrib),
            "transform": transform,
        })

    score = (raw_score / used_weight) if used_weight > 0 else None
    level = _level_from_score(score)

    comps_sorted = sorted(comps, key=lambda x: abs(float(x.get("contrib", 0.0))), reverse=True)

    return {
        "as_of": as_of,
        "score": score,
        "level": level,
        "missing": missing,
        "top": comps_sorted[:4],
        "components": comps_sorted,
        "used_weight": used_weight,
    }


def main() -> None:
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Missing file: {IN_CSV}. 먼저 fetch_geo_history.py를 실행해.")

    df = pd.read_csv(IN_CSV)
    if df.empty:
        raise ValueError("geo_history.csv is empty. fetch 단계부터 다시 확인해.")

    # ✅ 너가 말한 3개 이벤트
    events: List[Tuple[str, str]] = [
        ("2022-02-24", "Russia invasion (Ukraine)"),
        ("2023-10-07", "Gaza war start"),
        ("2024-01-12", "Red Sea attacks escalation"),
    ]

    out_lines: List[str] = []
    out_lines.append("=== GEO EW backtest (experiment) ===")
    out_lines.append(f"window={GEO_WINDOW}")
    out_lines.append("")

    for dt, label in events:
        r = compute_geo_score(df, dt)
        out_lines.append(f"[{dt}] {label}")
        out_lines.append(f"  score={None if r['score'] is None else f'{r['score']:+.2f}'}  level={r['level']}")
        out_lines.append(f"  missing={', '.join(r['missing']) if r['missing'] else 'None'}")
        out_lines.append("  top drivers:")
        for c in r["top"]:
            out_lines.append(
                f"    - {c['key']}: z_used={c['z_used']:+.2f} w={c['weight']:.2f} contrib={c['contrib']:+.2f}"
            )
        out_lines.append("")

    print("\n".join(out_lines))


if __name__ == "__main__":
    main()
