# experiments/geo/fetch_geo_history.py
# ------------------------------------------------------------
# Geo EW 실험용 히스토리 수집기 (2016-08-16 ~ today)
# - FRED: CSV endpoint 직접 호출 (pandas_datareader 불필요, 의존성 꼬임 방지)
# - STOOQ: ETF/주식은 stooq csv endpoint 사용 (yfinance 불안정/레이트리밋 회피)
# - OUTPUT: exp_data/geo/geo_history.csv  (TSV)
# - META  : exp_data/geo/sources_meta.json
# ------------------------------------------------------------

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root
EXP_DATA_DIR = BASE_DIR / "exp_data" / "geo"
OUT_CSV = EXP_DATA_DIR / "geo_history.csv"
OUT_META = EXP_DATA_DIR / "sources_meta.json"

# ✅ 요구사항: 2016-08-16부터
START_DATE = "2016-08-16"


# -----------------------------
# FRED via CSV endpoint
# -----------------------------
def fetch_fred_series(series_id: str, start: str, end: str, col_name: str) -> pd.Series:
    """
    FRED CSV endpoint로 시계열을 가져와 Series로 반환.
    schema: DATE,<SERIES_ID>
    """
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    r = requests.get(url, timeout=45)
    r.raise_for_status()

    df = pd.read_csv(StringIO(r.text))
    if "DATE" not in df.columns or series_id not in df.columns:
        raise RuntimeError(f"FRED CSV schema unexpected for {series_id}. cols={df.columns.tolist()}")

    df["DATE"] = pd.to_datetime(df["DATE"], errors="coerce")
    df = df.dropna(subset=["DATE"]).sort_values("DATE")

    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")

    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    df = df[(df["DATE"] >= start_dt) & (df["DATE"] <= end_dt)]

    s = df.set_index("DATE")[series_id]
    s.name = col_name
    return s


# -----------------------------
# STOOQ via CSV endpoint
# -----------------------------
def fetch_stooq_daily(symbol: str, start: str, end: str, col_name: str) -> pd.Series:
    """
    Stooq CSV endpoint로 일봉 Close를 가져와 Series로 반환.
    - symbol 예: "eem.us", "emb.us", "sea.us"
    schema(일반): Date,Open,High,Low,Close,Volume
    """
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    r = requests.get(url, timeout=45)
    r.raise_for_status()

    df = pd.read_csv(StringIO(r.text))
    if df.empty:
        raise RuntimeError(f"STOOQ returned empty for {symbol}")

    # stooq는 Date 대문자/소문자 혼용 가능성 대비
    date_col = "Date" if "Date" in df.columns else ("date" if "date" in df.columns else None)
    if date_col is None or "Close" not in df.columns:
        raise RuntimeError(f"STOOQ CSV schema unexpected for {symbol}. cols={df.columns.tolist()}")

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col]).sort_values(date_col)

    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")

    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    df = df[(df[date_col] >= start_dt) & (df[date_col] <= end_dt)]

    s = df.set_index(date_col)["Close"]
    s.name = col_name
    return s


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def build_spreads(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sovereign spreads proxy:
    KR/JP/CN/IL/TR 10Y - US10Y (level spread, percentage points)
    """
    out = df.copy()

    # 안전: 숫자화
    for c in out.columns:
        if c != "date":
            out[c] = pd.to_numeric(out[c], errors="coerce")

    if "US10Y_Y" not in out.columns:
        return out

    base = out["US10Y_Y"]

    mapping = {
        "KR10Y_Y": "KR10Y_SPREAD",
        "JP10Y_Y": "JP10Y_SPREAD",
        "CN10Y_Y": "CN10Y_SPREAD",
        "IL10Y_Y": "IL10Y_SPREAD",
        "TR10Y_Y": "TR10Y_SPREAD",
    }
    for y_col, sp_col in mapping.items():
        if y_col in out.columns:
            out[sp_col] = out[y_col] - base

    return out


def main() -> None:
    ensure_dir(EXP_DATA_DIR)

    end_date = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")

    # -----------------------------
    # 1) Define sources
    # -----------------------------
    fred_series: List[Tuple[str, str]] = [
        # Market reaction
        ("VIX", "VIXCLS"),
        ("WTI", "DCOILWTICO"),
        ("GOLD", "GOLDAMGBD228NLBM"),
        # FX
        ("USDCNH", "DEXCHUS"),  # NOTE: FRED에서 CNH가 아니라 CNY 계열일 수 있음
        ("USDJPY", "DEXJPUS"),
        ("USDMXN", "DEXMXUS"),
        # Sovereign yields
        ("US10Y_Y", "DGS10"),
        ("KR10Y_Y", "IRLTLT01KRM156N"),
        ("JP10Y_Y", "IRLTLT01JPM156N"),
        ("CN10Y_Y", "IRLTLT01CNM156N"),
        ("IL10Y_Y", "IRLTLT01ILM156N"),
        ("TR10Y_Y", "IRLTLT01TRM156N"),
    ]

    stooq_series: List[Tuple[str, str]] = [
        ("EEM", "eem.us"),
        ("EMB", "emb.us"),
        ("SEA", "sea.us"),
        ("BDRY", "bdry.us"),
        ("ITA", "ita.us"),
        ("XAR", "xar.us"),
    ]

    meta: Dict[str, Any] = {
        "start": START_DATE,
        "end": end_date,
        "sources": {},
    }

    series_list: List[pd.Series] = []

    # -----------------------------
    # 2) Fetch FRED
    # -----------------------------
    for col, sid in fred_series:
        try:
            print(f"[FETCH] {col} <- FRED:{sid}")
            s = fetch_fred_series(sid, START_DATE, end_date, col)
            ok_rows = int(s.dropna().shape[0])
            series_list.append(s)
            meta["sources"][col] = {
                "source": "fred_csv",
                "id": sid,
                "status": "OK",
                "rows": ok_rows,
                "from": str(s.index.min().date()) if ok_rows > 0 else None,
                "to": str(s.index.max().date()) if ok_rows > 0 else None,
                "error": None,
            }
        except Exception as e:
            meta["sources"][col] = {
                "source": "fred_csv",
                "id": sid,
                "status": "ERROR",
                "rows": 0,
                "from": None,
                "to": None,
                "error": str(e),
            }

    # -----------------------------
    # 3) Fetch STOOQ
    # -----------------------------
    for col, sym in stooq_series:
        try:
            print(f"[FETCH] {col} <- STOOQ:{sym}")
            s = fetch_stooq_daily(sym, START_DATE, end_date, col)
            ok_rows = int(s.dropna().shape[0])
            series_list.append(s)
            meta["sources"][col] = {
                "source": "stooq_csv",
                "id": sym,
                "status": "OK",
                "rows": ok_rows,
                "from": str(s.index.min().date()) if ok_rows > 0 else None,
                "to": str(s.index.max().date()) if ok_rows > 0 else None,
                "error": None,
            }
        except Exception as e:
            meta["sources"][col] = {
                "source": "stooq_csv",
                "id": sym,
                "status": "ERROR",
                "rows": 0,
                "from": None,
                "to": None,
                "error": str(e),
            }

    # -----------------------------
    # 4) Build output dataframe
    # -----------------------------
    # series_list가 비어있으면 기존 파일을 망가뜨리지 않기 위해 실패 처리
    if not series_list:
        raise RuntimeError("No series downloaded at all (FRED+STOOQ 모두 실패).")

    df = pd.concat(series_list, axis=1)
    df = df.sort_index()

    # ✅ 반드시 date 컬럼 생성
    out = df.reset_index().rename(columns={"index": "date"})
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"]).sort_values("date")

    # spreads 계산
    out = build_spreads(out)

    # ✅ 빈칸 없게: 숫자 컬럼 ffill/bfill
    for c in out.columns:
        if c != "date":
            out[c] = pd.to_numeric(out[c], errors="coerce")
    num_cols = [c for c in out.columns if c != "date"]
    out[num_cols] = out[num_cols].ffill().bfill()

    # ✅ 최종 헤더 순서 고정 (사용자가 원한 “원본과 동일”)
    desired_cols = [
        "date",
        "VIX", "WTI", "GOLD", "USDCNH", "USDJPY", "USDMXN",
        "US10Y_Y", "KR10Y_Y", "JP10Y_Y", "CN10Y_Y", "IL10Y_Y", "TR10Y_Y",
        "EEM", "EMB", "SEA", "BDRY", "ITA", "XAR",
        "KR10Y_SPREAD", "JP10Y_SPREAD", "CN10Y_SPREAD", "IL10Y_SPREAD", "TR10Y_SPREAD",
    ]
    # 존재하는 것만
    final_cols = [c for c in desired_cols if c in out.columns]
    # 혹시 새로 생긴 컬럼이 있으면 뒤에 붙임
    for c in out.columns:
        if c not in final_cols:
            final_cols.append(c)
    out = out[final_cols]

    # -----------------------------
    # 5) Sanity check (EMPTY 방지)
    # -----------------------------
    if out.empty or out.shape[0] < 100:
        raise RuntimeError(
            f"geo_history result looks too small/empty (rows={out.shape[0]}). "
            "fetch 실패 또는 date 파싱 문제."
        )

    # ✅ TSV 저장 (탭)
    out.to_csv(OUT_CSV, sep="\t", index=False)

    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[OK] wrote: {OUT_CSV} (rows={out.shape[0]})")
    print(f"[OK] meta : {OUT_META}")


if __name__ == "__main__":
    main()
