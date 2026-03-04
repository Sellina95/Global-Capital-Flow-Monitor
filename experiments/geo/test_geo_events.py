# experiments/geo/test_geo_events.py
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# -------------------------
# Paths
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
IN_CSV = EXP_DATA_DIR / "geo_history.csv"

# (optional) write a markdown report for easy viewing in repo
OUT_MD = EXP_DATA_DIR / "geo_event_backtest.md"

# -------------------------
# Config (Experiment only)
# -------------------------
GEO_WINDOW = 60

# ✅ "프로덕션에서 쓰던 후보 지표들" 최대한 포함
# - 테스트 데이터에 없는 건 missing으로만 뜨고, 절대 크래시 안 남.
# (key, weight, transform, mode)
# transform: "normal" | "inverse"
# mode: "pct" | "level"
GEO_FACTORS = [
    # -----------------------
    # Market Reaction
    # -----------------------
    ("VIX",    0.18, "normal", "pct"),
    ("WTI",    0.10, "normal", "pct"),
    ("GOLD",   0.12, "normal", "pct"),
    ("USDCNH", 0.18, "normal", "pct"),

    # -----------------------
    # EM Stress / FX
    # -----------------------
    ("EEM",    0.10, "inverse", "pct"),
    ("EMB",    0.12, "inverse", "pct"),
    ("USDMXN", 0.05, "normal",  "pct"),
    ("USDJPY", 0.05, "inverse", "pct"),

    # -----------------------
    # Shipping / Supply Chain
    # -----------------------
    ("SEA",    0.05, "inverse", "pct"),
    ("BDRY",   0.05, "normal",  "pct"),

    # -----------------------
    # Defense Attention
    # -----------------------
    ("ITA",    0.03, "normal", "pct"),
    ("XAR",    0.02, "normal", "pct"),

    # -----------------------
    # Sovereign spreads (CDS proxy) - "level" z-score
    # -----------------------
    ("KR10Y_SPREAD", 0.08, "normal", "level"),
    ("JP10Y_SPREAD", 0.05, "normal", "level"),
    ("CN10Y_SPREAD", 0.05, "normal", "level"),
    ("IL10Y_SPREAD", 0.05, "normal", "level"),
    ("TR10Y_SPREAD", 0.05, "normal", "level"),
]

# ✅ 레벨 판정: "양수만"이 아니라 abs(score) 기준 + 방향 라벨
# abs(score) < 0.75 -> NORMAL
# 0.75~1.50 -> ELEVATED
# 1.50~2.50 -> HIGH
# >=2.50 -> CONFLICT
LEVEL_BINS = [
    ("NORMAL",   0.00, 0.75),
    ("ELEVATED", 0.75, 1.50),
    ("HIGH",     1.50, 2.50),
    ("CONFLICT", 2.50, 99.0),
]

# event window: pick max |score| inside [D-3, D+5]
EVENT_WINDOW = (-3, +5)


# -------------------------
# Helpers
# -------------------------
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


def _z_last_level(df: pd.DataFrame, col: str, window: int) -> Optional[float]:
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if len(s) < max(10, min(window, 20)):
        return None
    tail = s.tail(window)
    mu = float(tail.mean())
    sd = float(tail.std(ddof=0))
    if sd == 0:
        return None
    return float((tail.iloc[-1] - mu) / sd)


def _level_from_score(score: Optional[float]) -> str:
    """
    ✅ FIX: negative score도 'stress'로 인정
    - abs(score)로 강도 구간 판단
    - 방향은 RISK-ON / RISK-OFF로 라벨링
    """
    if score is None:
        return "N/A"
    a = abs(float(score))
    base = "N/A"
    for name, lo, hi in LEVEL_BINS:
        if a >= lo and a < hi:
            base = name
            break

    if base == "N/A":
        return "N/A"

    # direction tag
    direction = "RISK-ON" if score > 0 else ("RISK-OFF" if score < 0 else "FLAT")
    return f"{base} ({direction})"


def _fmt_score(x: Optional[float]) -> str:
    if x is None:
        return "None"
    return f"{float(x):+.2f}"


def compute_geo_score(df: pd.DataFrame, as_of: str) -> Dict[str, Any]:
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    as_of_dt = pd.to_datetime(as_of)
    d = d[d["date"] <= as_of_dt].copy()
    if d.empty:
        return {
            "as_of": as_of,
            "score": None,
            "level": "N/A",
            "missing": ["ALL"],
            "top": [],
            "components": [],
            "used_weight": 0.0,
        }

    raw_score = 0.0
    used_weight = 0.0
    missing: List[str] = []
    comps: List[Dict[str, Any]] = []

    for item in GEO_FACTORS:
        key, w, transform, mode = item

        if key not in d.columns:
            missing.append(key)
            continue

        z: Optional[float] = None
        if mode == "level":
            z = _z_last_level(d, key, GEO_WINDOW)
        else:
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
            "mode": mode,
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


def best_in_event_window(df: pd.DataFrame, event_date: str, window: Tuple[int, int]) -> Dict[str, Any]:
    lo, hi = window
    base = pd.to_datetime(event_date)

    best = None
    for offset in range(lo, hi + 1):
        dt = (base + pd.Timedelta(days=offset)).strftime("%Y-%m-%d")
        r = compute_geo_score(df, dt)
        s = r["score"]
        if s is None:
            continue
        if best is None or abs(float(s)) > abs(float(best["score"])):
            best = r

    if best is None:
        return {"event_date": event_date, "best_as_of": None, "score": None, "level": "N/A", "missing": ["ALL"], "top": []}

    return {
        "event_date": event_date,
        "best_as_of": best["as_of"],
        "score": best["score"],
        "level": best["level"],
        "missing": best["missing"],
        "top": best["top"],
    }


def main() -> None:
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Missing file: {IN_CSV}. 먼저 geo_history.csv를 생성/복원해.")

    df = pd.read_csv(IN_CSV)
    if df.empty:
        raise ValueError("geo_history.csv is empty. fetch 단계부터 다시 확인해.")

    # ✅ 테스트 이벤트 3개
    events: List[Tuple[str, str]] = [
        ("2022-02-24", "Russia invasion (Ukraine)"),
        ("2023-10-07", "Gaza war start"),
        ("2024-01-12", "Red Sea attacks escalation"),
    ]

    # print + markdown report
    out_lines: List[str] = []
    out_lines.append("=== GEO EW backtest (experiment) ===")
    out_lines.append(f"window={GEO_WINDOW}")
    out_lines.append(f"event_window=[{EVENT_WINDOW[0]}, {EVENT_WINDOW[1]}] days (pick max |score|)")
    out_lines.append("")

    md: List[str] = []
    md.append("# GEO EW backtest (experiment)")
    md.append("")
    md.append(f"- window: `{GEO_WINDOW}`")
    md.append(f"- event window: `{EVENT_WINDOW[0]} .. {EVENT_WINDOW[1]}` (pick max |score|)")
    md.append("")
    md.append("## Results")
    md.append("")

    for dt, label in events:
        r = best_in_event_window(df, dt, EVENT_WINDOW)

        out_lines.append(f"[{dt}] {label}")
        out_lines.append(f"  best_in_window={r['best_as_of']}  score={_fmt_score(r['score'])}  level={r['level']}")
        out_lines.append(f"  missing={', '.join(r['missing']) if r['missing'] else 'None'}")
        out_lines.append("  top drivers:")
        for c in r["top"]:
            out_lines.append(
                f"    - {c['key']}: z_used={c['z_used']:+.2f} w={c['weight']:.2f} contrib={c['contrib']:+.2f} mode={c.get('mode')}"
            )
        out_lines.append("")

        md.append(f"### {dt} — {label}")
        md.append(f"- best_in_window: `{r['best_as_of']}`")
        md.append(f"- score: `{_fmt_score(r['score'])}`")
        md.append(f"- level: `{r['level']}`")
        md.append(f"- missing/skipped: `{', '.join(r['missing']) if r['missing'] else 'None'}`")
        md.append("")
        md.append("Top drivers:")
        if r["top"]:
            for c in r["top"]:
                md.append(f"- {c['key']}: z_used={c['z_used']:+.2f}, w={c['weight']:.2f}, contrib={c['contrib']:+.2f}, mode={c.get('mode')}")
        else:
            md.append("- (none)")
        md.append("")

    # write md
    try:
        EXP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        OUT_MD.write_text("\n".join(md), encoding="utf-8")
    except Exception:
        pass

    print("\n".join(out_lines))
    print(f"[OK] wrote: {OUT_MD}")


if __name__ == "__main__":
    main()
