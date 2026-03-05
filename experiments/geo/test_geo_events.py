# experiments/geo/test_geo_events.py
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
IN_CSV = EXP_DATA_DIR / "geo_history.csv"
OUT_MD = EXP_DATA_DIR / "geo_event_backtest.md"

GEO_WINDOW = 60

# (key, weight, transform, mode?)
# mode: "pct" | "level"
# - mode 생략 시: *_SPREAD => level, else pct
GEO_FACTORS = [
    # Market reaction
    ("VIX",    0.18, "normal"),
    ("WTI",    0.10, "normal"),
    ("GOLD",   0.12, "normal"),
    ("USDCNH", 0.18, "normal"),

    # EM stress
    ("EEM",    0.10, "inverse"),
    ("EMB",    0.12, "inverse"),
    ("USDMXN", 0.05, "normal"),
    ("USDJPY", 0.05, "inverse"),

    # Supply chain / shipping
    ("SEA",    0.05, "inverse"),
    ("BDRY",   0.05, "normal"),

    # Defense
    ("ITA",    0.03, "normal"),
    ("XAR",    0.02, "normal"),

    # Sovereign spreads (CDS proxy) - level mode 권장
    ("KR10Y_SPREAD", 0.08, "normal", "level"),
    ("JP10Y_SPREAD", 0.05, "normal", "level"),
    ("CN10Y_SPREAD", 0.05, "normal", "level"),
    ("IL10Y_SPREAD", 0.05, "normal", "level"),
    ("TR10Y_SPREAD", 0.05, "normal", "level"),
]

# ✅ Stress level은 |score| 기반으로 판단 (방향과 분리)
STRESS_THRESHOLDS = [
    ("NORMAL",    0.00, 0.75),
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

def _z_last_level(series: pd.Series, window: int) -> Optional[float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < max(10, min(window, 20)):
        return None
    tail = s.tail(window)
    mu = float(tail.mean())
    sd = float(tail.std(ddof=0))
    if sd == 0:
        return None
    return float((tail.iloc[-1] - mu) / sd)

def _stress_level(score: Optional[float]) -> str:
    if score is None:
        return "N/A"
    x = abs(float(score))
    for name, lo, hi in STRESS_THRESHOLDS:
        if x >= lo and x < hi:
            return name
    return "N/A"

def _direction(score: Optional[float]) -> str:
    if score is None:
        return "N/A"
    return "RISK-OFF" if score < 0 else "RISK-ON"

def compute_geo_score(df: pd.DataFrame, as_of: str) -> Dict[str, Any]:
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    as_of_dt = pd.to_datetime(as_of)
    d = d[d["date"] <= as_of_dt].copy()
    if d.empty:
        return {"as_of": as_of, "score": None, "missing": ["ALL"], "components": [], "used_weight": 0.0}

    raw_score = 0.0
    used_weight = 0.0
    missing: List[str] = []
    comps: List[Dict[str, Any]] = []

    for item in GEO_FACTORS:
        if not isinstance(item, (list, tuple)) or len(item) < 3:
            continue

        key = item[0]
        w = float(item[1])
        transform = item[2]
        mode = item[3] if len(item) >= 4 else None
        if mode is None:
            mode = "level" if str(key).endswith("_SPREAD") else "pct"

        if key not in d.columns:
            missing.append(key)
            continue

        z = None
        if mode == "level":
            z = _z_last_level(pd.to_numeric(d[key], errors="coerce"), GEO_WINDOW)
        else:
            z = _z_last(_pct_series(d, key), GEO_WINDOW)

        if z is None:
            missing.append(key)
            continue

        z_used = -z if transform == "inverse" else z
        contrib = w * float(z_used)

        raw_score += contrib
        used_weight += w

        comps.append({
            "key": key,
            "weight": w,
            "z": float(z),
            "z_used": float(z_used),
            "contrib": float(contrib),
            "transform": transform,
            "mode": mode,
        })

    score = (raw_score / used_weight) if used_weight > 0 else None
    comps_sorted = sorted(comps, key=lambda x: abs(float(x.get("contrib", 0.0))), reverse=True)

    return {
        "as_of": as_of,
        "score": score,
        "stress_level": _stress_level(score),
        "direction": _direction(score),
        "missing": missing,
        "top": comps_sorted[:4],
        "components": comps_sorted,
        "used_weight": used_weight,
    }

def pick_best_in_window(df: pd.DataFrame, event_date: str, offsets: List[int]) -> Dict[str, Any]:
    base = pd.to_datetime(event_date)
    best: Optional[Dict[str, Any]] = None
    for k in offsets:
        dt = (base + pd.Timedelta(days=int(k))).strftime("%Y-%m-%d")
        r = compute_geo_score(df, dt)
        if best is None:
            best = r
            continue
        # pick max |score|
        s1 = abs(best["score"]) if best["score"] is not None else -1
        s2 = abs(r["score"]) if r["score"] is not None else -1
        if s2 > s1:
            best = r
    return best or compute_geo_score(df, event_date)

def main() -> None:
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Missing file: {IN_CSV}. 먼저 fetch_geo_history.py를 실행해.")

    df = pd.read_csv(IN_CSV)
    if df.empty:
        raise ValueError("geo_history.csv is empty. fetch 단계부터 다시 확인해.")

    events: List[Tuple[str, str]] = [
        ("2022-02-24", "Russia invasion (Ukraine)"),
        ("2023-10-07", "Gaza war start"),
        ("2024-01-12", "Red Sea attacks escalation"),
    ]

    offsets = list(range(-3, 6))  # [-3..+5]

    out_lines: List[str] = []
    out_lines.append("=== GEO EW backtest (experiment) ===")
    out_lines.append(f"window={GEO_WINDOW}")
    out_lines.append(f"event_window=[-3, 5] days (pick max |score|)")
    out_lines.append("")

    md_lines: List[str] = []
    md_lines.append("# GEO EW backtest (experiment)")
    md_lines.append("")
    md_lines.append(f"- window: {GEO_WINDOW}")
    md_lines.append(f"- event_window: [-3, +5] days (pick max |score|)")
    md_lines.append("")
    md_lines.append("## Results")
    md_lines.append("")

    for dt, label in events:
        best = pick_best_in_window(df, dt, offsets)

        score_str = "None" if best["score"] is None else f"{best['score']:+.2f}"
        miss_str = ", ".join(best["missing"]) if best["missing"] else "None"

        out_lines.append(f"[{dt}] {label}")
        out_lines.append(f"  best_in_window={best['as_of']}  score={score_str}  stress={best['stress_level']}  direction={best['direction']}")
        out_lines.append(f"  missing={miss_str}")
        out_lines.append("  top drivers:")
        for c in best["top"]:
            out_lines.append(f"    - {c['key']}: z_used={c['z_used']:+.2f} w={c['weight']:.2f} contrib={c['contrib']:+.2f} mode={c['mode']}")
        out_lines.append("")

        md_lines.append(f"### {dt} — {label}")
        md_lines.append(f"- best_in_window: `{best['as_of']}`")
        md_lines.append(f"- score: **{score_str}**")
        md_lines.append(f"- stress_level(|score|): **{best['stress_level']}**")
        md_lines.append(f"- direction(sign): **{best['direction']}**")
        md_lines.append(f"- missing: `{miss_str}`")
        md_lines.append("")
        md_lines.append("Top drivers:")
        for c in best["top"]:
            md_lines.append(f"- {c['key']}: z_used={c['z_used']:+.2f} (w={c['weight']:.2f}) contrib={c['contrib']:+.2f} mode={c['mode']}")
        md_lines.append("")

    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")
    out_lines.append(f"[OK] wrote: {OUT_MD}")

    print("\n".join(out_lines))

if __name__ == "__main__":
    main()
