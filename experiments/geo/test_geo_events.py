# experiments/geo/test_geo_events.py
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
EXP_DIR = BASE_DIR / "exp_data" / "geo"
HIST_PATH = EXP_DIR / "geo_history.csv"  # TSV
OUT_MD = EXP_DIR / "geo_event_backtest.md"  # ✅ workflow debug step가 찾는 파일명

# =========================================================
# ✅ 우리가 테스트하려던 3개 이벤트 (고정)
# =========================================================
EVENTS = [
    {"date": "2022-02-24", "label": "Russia invasion (Ukraine)"},
    {"date": "2023-10-07", "label": "Gaza war start"},
    {"date": "2024-01-12", "label": "Red Sea attacks escalation"},
]

# 이벤트 주변 며칠을 윈도우로 볼지 (best_in_window 찾기)
WINDOW_DAYS_BEFORE = 3
WINDOW_DAYS_AFTER = 3

# 유효일 판정에 쓸 핵심 컬럼 (없으면 자동으로 스킵)
REQUIRED_COLS_FOR_VALID_DAY = ["USDCNH", "GOLD", "VIX", "WTI"]


def _read_geo_history() -> pd.DataFrame:
    if not HIST_PATH.exists() or HIST_PATH.stat().st_size == 0:
        raise FileNotFoundError(f"Missing geo history file: {HIST_PATH}")

    try:
        df = pd.read_csv(HIST_PATH, sep="\t")
    except Exception:
        df = pd.read_csv(HIST_PATH, sep=None, engine="python")

    if df.empty or "date" not in df.columns:
        raise ValueError(f"geo_history.csv has no usable 'date' column: cols={list(df.columns)[:30]}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # 숫자 변환
    for c in df.columns:
        if c == "date":
            continue
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def _zscore(series: pd.Series, lookback: int = 252) -> pd.Series:
    s = series.astype("float64")
    mu = s.rolling(lookback, min_periods=max(20, lookback // 5)).mean()
    sd = s.rolling(lookback, min_periods=max(20, lookback // 5)).std()
    return (s - mu) / sd


def _compute_geo_score_series(df: pd.DataFrame) -> pd.Series:
    """
    너의 Geo EW scoring 로직이 따로 있으면 여기를 교체하면 됨.
    지금은 실험용(로그 재현/파일 생성)으로 z 기반 composite.
    """
    # 없는 컬럼은 NaN 시리즈로 처리
    def _col(name: str) -> pd.Series:
        return df[name] if name in df.columns else pd.Series([pd.NA] * len(df), index=df.index, dtype="float64")

    z_usdcnh = _zscore(_col("USDCNH"))
    z_vix = _zscore(_col("VIX"))
    z_gold = _zscore(_col("GOLD"))
    z_wti = _zscore(_col("WTI"))

    # weight (예시)
    w = {"USDCNH": 0.35, "VIX": 0.35, "GOLD": 0.20, "WTI": 0.10}

    # GOLD는 safe haven이라 risk score에선 반대로(-)
    score = (
        w["USDCNH"] * z_usdcnh
        + w["VIX"] * z_vix
        - w["GOLD"] * z_gold
        + w["WTI"] * z_wti
    )
    score.name = "geo_score"
    return score


def _stress_bucket(score: float) -> str:
    """
    너가 원하는 방식으로 컷을 조절하면 됨.
    """
    a = abs(score)
    if a >= 1.8:
        return "HIGH"
    if a >= 0.8:
        return "ELEVATED"
    if a >= 0.4:
        return "WATCH"
    return "CALM"


def _direction(score: float) -> str:
    # score가 +면 RISK-ON, -면 RISK-OFF (너 예시와 맞춤)
    return "RISK-ON" if score >= 0 else "RISK-OFF"


def _is_valid_day(row: pd.Series) -> bool:
    ok_any = False
    for c in REQUIRED_COLS_FOR_VALID_DAY:
        if c in row.index:
            ok_any = True
            if pd.isna(row[c]):
                return False
    # required 컬럼이 하나도 없으면 유효성 체크 불가 → 그냥 True 처리(파일은 만들자)
    return True if not ok_any else True


def _best_in_window(df: pd.DataFrame, score_s: pd.Series, event_date: pd.Timestamp) -> Optional[Tuple[pd.Timestamp, float]]:
    start = event_date - pd.Timedelta(days=WINDOW_DAYS_BEFORE)
    end = event_date + pd.Timedelta(days=WINDOW_DAYS_AFTER)

    mask = (df["date"] >= start) & (df["date"] <= end)
    sub = df.loc[mask].copy()
    if sub.empty:
        return None

    # 유효일만 남기기
    sub["score"] = score_s.loc[sub.index]
    sub = sub.dropna(subset=["score"])
    if sub.empty:
        return None

    # best = 절댓값 최대 (이벤트 충격 최대치)
    sub["abs_score"] = sub["score"].abs()
    sub = sub.sort_values(["abs_score", "date"], ascending=[False, True])
    best_row = sub.iloc[0]
    return best_row["date"], float(best_row["score"])


def _write_md(lines: List[str]) -> None:
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] wrote: {OUT_MD}")


def main() -> None:
    df = _read_geo_history()
    score_s = _compute_geo_score_series(df)

    lines: List[str] = []
    lines.append("=== GEO EW backtest (experiment) ===")
    lines.append("")

    # 인덱싱 편하게
    date_set = set(df["date"].dt.strftime("%Y-%m-%d").tolist())

    for ev in EVENTS:
        ev_date_str = ev["date"]
        label = ev["label"]
        ev_ts = pd.to_datetime(ev_date_str, errors="coerce")

        lines.append(f"[{ev_date_str}] {label}")

        if ev_ts is pd.NaT:
            lines.append("  best_in_window=NA  score=NA  stress=NA  direction=NA")
            lines.append("")
            continue

        # event date 자체가 df에 없을 수 있음(주말/휴일/누락)
        if ev_date_str not in date_set:
            # 그래도 best_in_window는 윈도우에서 찾게 함
            best = _best_in_window(df, score_s, ev_ts)
            if best is None:
                lines.append("  best_in_window=NA  score=NA  stress=NA  direction=NA")
                lines.append("")
                continue
            best_date, best_score = best
            stress = _stress_bucket(best_score)
            direction = _direction(best_score)
            lines.append(f"  best_in_window={best_date.strftime('%Y-%m-%d')}  score={best_score:+.2f}  stress={stress}  direction={direction}")
            lines.append("")
            continue

        # event date가 존재하면 윈도우 best 뽑기
        best = _best_in_window(df, score_s, ev_ts)
        if best is None:
            lines.append("  best_in_window=NA  score=NA  stress=NA  direction=NA")
            lines.append("")
            continue

        best_date, best_score = best
        stress = _stress_bucket(best_score)
        direction = _direction(best_score)
        lines.append(f"  best_in_window={best_date.strftime('%Y-%m-%d')}  score={best_score:+.2f}  stress={stress}  direction={direction}")
        lines.append("")

    # 파일 저장 + stdout에도 핵심은 찍어주기
    _write_md(lines)

    print("\n".join(lines))


if __name__ == "__main__":
    main()