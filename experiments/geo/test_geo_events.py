from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

# =========================================================
# Paths
# =========================================================
BASE_DIR = Path(__file__).resolve().parents[2]
EXP_DIR = BASE_DIR / "exp_data" / "geo"
HIST_PATH = EXP_DIR / "geo_history.csv"  # TSV expected
OUT_MD = EXP_DIR / "geo_event_backtest.md"  # workflow debug step가 찾는 파일명

# =========================================================
# ✅ 우리가 테스트하려던 3개 이벤트 (고정)
# =========================================================
EVENTS = [
    {"date": "2022-02-24", "label": "Russia invasion (Ukraine)"},
    {"date": "2023-10-07", "label": "Gaza war start"},
    {"date": "2024-01-12", "label": "Red Sea attacks escalation"},
]

WINDOW_DAYS_BEFORE = 3
WINDOW_DAYS_AFTER = 3

# 유효일 판정용 (네 기존 파일처럼 최소 핵심만 유지)
REQUIRED_COLS_FOR_VALID_DAY = ["USDCNH", "GOLD", "VIX", "WTI"]


# =========================================================
# ✅ Import your REAL Geo EW layer (7.2)
# =========================================================
# ⚠️ 경로가 다르면 여기 import만 너 레포 구조에 맞춰 수정하면 됨.
# 너가 아까 보여준 코드 기준으로는 filters/strategist_filters.py 안에 함수가 있음.
from filters.strategist_filters import (
    attach_geopolitical_ew_layer,
    geopolitical_early_warning_filter,
)

# (선택) attach_geopolitical_ew_layer가 내부에서 load_sovereign_spreads_df()를 호출함.
# 만약 그 함수가 같은 모듈/네임스페이스로 import가 안 되어 있으면,
# strategist_filters.py 쪽에서 이미 해결되어 있어야 함. (보통 거기서 import/정의됨)


def _read_geo_history() -> pd.DataFrame:
    if not HIST_PATH.exists() or HIST_PATH.stat().st_size == 0:
        raise FileNotFoundError(f"Missing geo history file: {HIST_PATH}")

    try:
        df = pd.read_csv(HIST_PATH, sep="\t")
    except Exception:
        df = pd.read_csv(HIST_PATH, sep=None, engine="python")

    if df.empty or "date" not in df.columns:
        raise ValueError(
            f"geo_history.csv has no usable 'date' column: cols={list(df.columns)[:30]}"
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # 숫자 변환
    for c in df.columns:
        if c == "date":
            continue
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def _is_valid_day(row: pd.Series) -> bool:
    """
    REQUIRED_COLS_FOR_VALID_DAY가 모두 존재하고 NaN이 아니면 valid.
    (요청대로 최소 체크만 유지)
    """
    for c in REQUIRED_COLS_FOR_VALID_DAY:
        if c not in row.index:
            # 컬럼이 아예 없으면 "검증 불가"이지만 테스트는 계속 굴리기 위해 True
            return True
        if pd.isna(row[c]):
            return False
    return True


def _best_in_window_geoew(
    df: pd.DataFrame,
    event_date: pd.Timestamp,
) -> Optional[Tuple[pd.Timestamp, float, str, List[str]]]:
    """
    이벤트 전후 WINDOW 안에서
    attach_geopolitical_ew_layer()로 계산한 GEO_EW.score의 절댓값이 가장 큰 날을 best로 선택.

    return: (best_date, best_score, best_level, missing_list)
    """
    start = event_date - pd.Timedelta(days=WINDOW_DAYS_BEFORE)
    end = event_date + pd.Timedelta(days=WINDOW_DAYS_AFTER)

    mask = (df["date"] >= start) & (df["date"] <= end)
    sub = df.loc[mask].copy()
    if sub.empty:
        return None

    best: Optional[Tuple[pd.Timestamp, float, str, List[str]]] = None

    # sub는 df의 부분집합이라 iloc 인덱스를 사용해서 today_idx로 넘겨줌
    # attach_geopolitical_ew_layer는 df.iloc[:today_idx+1]를 사용하므로
    # 반드시 "sub가 아니라 df 전체 기준 idx"로 넘겨야 함.
    # 그래서 여기서는 df의 원래 인덱스를 직접 활용하기 위해, sub의 원래 인덱스(=df 인덱스)를 씀.
    for today_idx in sub.index.tolist():
        row = df.loc[today_idx]
        if not _is_valid_day(row):
            continue

        market_data: Dict[str, Any] = {}
        try:
            # ✅ 핵심: 본코드 7.2 레이어 실행
            md = attach_geopolitical_ew_layer(
                market_data=market_data,
                df=df,
                today_idx=int(today_idx),
            )
            geo = (md.get("GEO_EW") or {})
            score = geo.get("score", None)
            level = geo.get("level", "N/A")
            missing = geo.get("missing", []) or []
            if score is None:
                continue

            cand = (df.loc[today_idx, "date"], float(score), str(level), list(missing))

            if best is None:
                best = cand
            else:
                # abs(score) 최대
                if abs(cand[1]) > abs(best[1]):
                    best = cand
                elif abs(cand[1]) == abs(best[1]) and cand[0] < best[0]:
                    best = cand

        except Exception:
            # 테스트는 계속 돌리되, 해당 날짜는 스킵
            continue

    return best


def _write_md(lines: List[str]) -> None:
    EXP_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] wrote: {OUT_MD}")


def main() -> None:
    df = _read_geo_history()

    lines: List[str] = []
    lines.append("=== GEO EW backtest (REAL 7.2 via attach_geopolitical_ew_layer) ===")
    lines.append("")
    lines.append(f"- Source: {HIST_PATH}")
    lines.append(f"- Window: [{WINDOW_DAYS_BEFORE}d before, {WINDOW_DAYS_AFTER}d after]")
    lines.append("")

    date_set = set(df["date"].dt.strftime("%Y-%m-%d").tolist())

    for ev in EVENTS:
        ev_date_str = ev["date"]
        label = ev["label"]
        ev_ts = pd.to_datetime(ev_date_str, errors="coerce")

        lines.append(f"[{ev_date_str}] {label}")

        if ev_ts is pd.NaT:
            lines.append("  best_in_window=NA  score=NA  level=NA  missing=NA")
            lines.append("")
            continue

        # event date 자체가 df에 없을 수 있음(주말/휴일/누락) -> 그래도 window best는 찾는다
        best = _best_in_window_geoew(df, ev_ts)
        if best is None:
            lines.append("  best_in_window=NA  score=NA  level=NA  missing=NA")
            lines.append("")
            continue

        best_date, best_score, best_level, missing = best
        miss_txt = ", ".join(missing) if missing else "None"
        lines.append(
            f"  best_in_window={best_date.strftime('%Y-%m-%d')}  score={best_score:+.2f}  level={best_level}  missing={miss_txt}"
        )

        # (옵션) 그 날짜의 7.2 리포트 스트링도 붙여서 디버깅하기 좋게
        try:
            # best_date에 해당하는 today_idx 찾기
            # df["date"]는 Timestamp라 날짜만 매칭
            target = best_date.normalize()
            idx_list = df.index[df["date"].dt.normalize() == target].tolist()
            if idx_list:
                md: Dict[str, Any] = {}
                md = attach_geopolitical_ew_layer(md, df, int(idx_list[0]))
                report = geopolitical_early_warning_filter(md)
                lines.append("")
                lines.append("  --- 7.2 report snapshot ---")
                for ln in report.splitlines():
                    lines.append(f"  {ln}")
        except Exception:
            pass

        lines.append("")

    _write_md(lines)
    print("\n".join(lines))


if __name__ == "__main__":
    main()