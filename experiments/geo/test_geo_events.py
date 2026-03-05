# experiments/geo/test_geo_events.py
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
IN_CSV = EXP_DATA_DIR / "geo_history.csv"

# -----------------------
# GEO EW (experiment)
# -----------------------
GEO_WINDOW = 60

# (key, weight, transform, mode?)
# mode: "pct" | "level"
GEO_FACTORS = [
    ("VIX",    0.18, "normal", "pct"),
    ("WTI",    0.10, "normal", "pct"),
    ("GOLD",   0.12, "normal", "pct"),
    ("USDCNH", 0.18, "normal", "pct"),

    ("EEM",    0.10, "inverse", "pct"),
    ("EMB",    0.12, "inverse", "pct"),
    ("USDMXN", 0.05, "normal",  "pct"),
    ("USDJPY", 0.05, "inverse", "pct"),

    ("SEA",    0.05, "inverse", "pct"),
    ("BDRY",   0.05, "normal",  "pct"),

    ("ITA",    0.03, "normal",  "pct"),
    ("XAR",    0.02, "normal",  "pct"),

    # spreads are "level" z-score (not pct)
    ("KR10Y_SPREAD", 0.08, "normal", "level"),
    ("JP10Y_SPREAD", 0.04, "normal", "level"),
    ("CN10Y_SPREAD", 0.04, "normal", "level"),
    ("IL10Y_SPREAD", 0.03, "normal", "level"),
    ("TR10Y_SPREAD", 0.05, "normal", "level"),
]

# stress bands (absolute intensity only)
GEO_STRESS_THRESHOLDS = [
    ("NORMAL",   0.00, 0.75),
    ("ELEVATED", 0.75, 1.50),
    ("HIGH",     1.50, 2.50),
    ("CONFLICT", 2.50, 99.0),
]

EVENT_OFFSETS_DEFAULT = list(range(-3, 6))  # [-3, +5]


# -----------------------
# Robust loader (NO MORE KeyError: 'date')
# -----------------------
def load_geo_history_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    # 1) try TAB first (your exp files are TSV-in-csv-name)
    try:
        df = pd.read_csv(path, sep="\t", engine="python")
    except Exception:
        df = pd.read_csv(path)

    # 2) if date column missing, handle "single-column with tabs"
    if "date" not in df.columns:
        if len(df.columns) == 1 and isinstance(df.columns[0], str) and "\t" in df.columns[0]:
            # header got read as one big string "date\tVIX\tWTI..."
            # -> re-read as raw text and split by tabs safely
            raw = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            if not raw:
                raise ValueError("geo_history.csv is empty (no lines).")

            header = raw[0].split("\t")
            rows = [line.split("\t") for line in raw[1:] if line.strip()]

            df = pd.DataFrame(rows, columns=header)
        else:
            # last attempt: comma
            df = pd.read_csv(path)
            if "date" not in df.columns:
                raise ValueError(
                    f"'date' column not found. columns={list(df.columns)[:10]} ...\n"
                    f"Hint: file is likely TAB-separated. Ensure fetch writes sep='\\t' and this reader uses sep='\\t'."
                )

    # normalize
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)

    # numeric conversion for all non-date cols
    for c in df.columns:
        if c == "date":
            continue
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # ✅ user request: "빈칸 없도록" (best-effort)
    # forward-fill then back-fill (covers start-of-series NaNs too)
    non_date_cols = [c for c in df.columns if c != "date"]
    if non_date_cols:
        df[non_date_cols] = df[non_date_cols].ffill().bfill()

    return df


# -----------------------
# Math helpers
# -----------------------
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


def stress_level(score: Optional[float]) -> str:
    if score is None:
        return "N/A"
    a = abs(float(score))
    for name, lo, hi in GEO_STRESS_THRESHOLDS:
        if a >= lo and a < hi:
            return name
    return "N/A"


def direction_label(score: Optional[float]) -> str:
    if score is None:
        return "N/A"
    return "RISK-OFF" if score < 0 else "RISK-ON"


# -----------------------
# Core scoring
# -----------------------
def compute_geo_score(df: pd.DataFrame, as_of: str) -> Dict[str, Any]:
    d = df.copy()
    as_of_dt = pd.to_datetime(as_of)

    d = d[d["date"] <= as_of_dt].copy()
    if d.empty:
        return {"as_of": as_of, "score": None, "stress": "N/A", "direction": "N/A", "missing": ["ALL"], "components": []}

    raw_score = 0.0
    used_weight = 0.0
    missing: List[str] = []
    comps: List[Dict[str, Any]] = []

    for item in GEO_FACTORS:
        key, w, transform, mode = item

        if key not in d.columns:
            missing.append(key)
            continue

        if mode == "level":
            z = _z_last_level(d[key], GEO_WINDOW)
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
    comps_sorted = sorted(comps, key=lambda x: abs(float(x.get("contrib", 0.0))), reverse=True)

    return {
        "as_of": as_of,
        "score": score,
        "stress": stress_level(score),
        "direction": direction_label(score),
        "missing": missing,
        "top": comps_sorted[:4],
        "components": comps_sorted,
        "used_weight": used_weight,
    }


def pick_best_in_window(df: pd.DataFrame, event_date: str, offsets: List[int]) -> Dict[str, Any]:
    base = pd.to_datetime(event_date)
    best: Optional[Dict[str, Any]] = None
    best_abs = -1.0

    for k in offsets:
        dt = (base + pd.Timedelta(days=int(k))).strftime("%Y-%m-%d")
        r = compute_geo_score(df, dt)
        s = r.get("score")
        if s is None:
            continue
        a = abs(float(s))
        if a > best_abs:
            best_abs = a
            best = r

    if best is None:
        best = compute_geo_score(df, event_date)
    return best


def main() -> None:
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Missing file: {IN_CSV}. 먼저 fetch_geo_history.py를 실행해.")

    df = load_geo_history_df(IN_CSV)
    if df.empty:
        raise ValueError("geo_history.csv is empty. fetch 단계부터 다시 확인해.")

    events: List[Tuple[str, str]] = [
        ("2022-02-24", "Russia invasion (Ukraine)"),
        ("2023-10-07", "Gaza war start"),
        ("2024-01-12", "Red Sea attacks escalation"),
    ]

    offsets = EVENT_OFFSETS_DEFAULT

    out_lines: List[str] = []
    out_lines.append("=== GEO EW backtest (experiment) ===")
    out_lines.append(f"window={GEO_WINDOW}")
    out_lines.append(f"event_window=[{offsets[0]}, {offsets[-1]}] days (pick max |score|)")
    out_lines.append("")

    for dt, label in events:
        best = pick_best_in_window(df, dt, offsets)
        score = best["score"]
        score_str = "None" if score is None else f"{score:+.2f}"
        out_lines.append(f"[{dt}] {label}")
        out_lines.append(f"  best_in_window={best['as_of']}  score={score_str}  stress={best['stress']}  direction={best['direction']}")
        out_lines.append(f"  missing={', '.join(best['missing']) if best['missing'] else 'None'}")
        out_lines.append("  top drivers:")
        for c in best["top"]:
            out_lines.append(
                f"    - {c['key']}: z_used={c['z_used']:+.2f} w={c['weight']:.2f} contrib={c['contrib']:+.2f} mode={c['mode']}"
            )
        out_lines.append("")

    # write a markdown artifact too (optional)
    out_md = EXP_DATA_DIR / "geo_event_backtest.md"
    out_md.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    print("\n".join(out_lines))
    print(f"[OK] wrote: {out_md}")


if __name__ == "__main__":
    main()
