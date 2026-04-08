
from __future__ import annotations
from filters.decision_layer import decision_layer_filter
from filters.transmission_layer import transmission_layer_filter
from pathlib import Path
# generate_report.py 파일에서 'save_etf_data_to_combined_csv' 임포트 문을 제거
from scripts.data_processing import download_all_etfs_and_save, load_etf_data_from_csv
from typing import Dict, Any
import pandas as pd
import os


from filters.strategist_filters import build_strategist_commentary
from filters.strategist_filters import attach_geopolitical_ew_layer
from filters.strategist_filters import geopolitical_early_warning_filter
from filters.strategist_filters import attach_country_risk_layer
from filters.strategist_filters import attach_geo_similarity_layer
from filters.executive_layer import executive_summary_filter
#from filters.executive_layer import calculate_raroc
from filters.scenario_layer import scenario_generator_filter
from filters.strategist_filters import apply_geo_overlay_to_final_state
from scripts.risk_alerts import check_regime_change_and_alert
from scripts.fetch_expectation_data import fetch_expectation_data  # external expectations
from scripts.fetch_sentiment import fetch_cnn_fear_greed


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
BACKTEST_DATA_DIR = DATA_DIR / "backtests"
BACKTEST_REPORTS_DIR = REPORTS_DIR / "backtests"

# macro_data.csv에 들어있는 키들 (여기서 추가된 지표는 자동으로 읽히지만,
# 필수 daily macro 라인은 이 KEYS를 기준으로 출력)
KEYS = ["US10Y", "DXY", "WTI", "VIX", "USDKRW"]

# 리포트 상단에 따로 Liquidity Snapshot 블럭을 띄울지 (Fed Plumbing Filter가 있으니 보통 False 추천)
SHOW_LIQUIDITY_SNAPSHOT = False


# -------------------------
# Loaders
# -------------------------
def load_macro_df() -> pd.DataFrame:
    """
    Supports:
      - data/macro_data.xlsx
      - data/macro_data.csv

    Robust to:
      - duplicated columns
      - mixed 'date'/'datetime'
      - schema changes causing bad/epoch rows
      - occasional malformed rows (skip bad lines)
      - occasional single-row CSV (won't crash report pipeline)

    Output:
      - Always returns a DataFrame with a valid 'date' (datetime64)
      - Sorted by date ascending
    """
    xlsx_path = DATA_DIR / "macro_data.xlsx"
    csv_path = DATA_DIR / "macro_data.csv"

    if xlsx_path.exists():
        df = pd.read_excel(xlsx_path)
    elif csv_path.exists():
        # ✅ tolerant read for occasional malformed rows
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            df = pd.read_csv(csv_path, on_bad_lines="skip")
    else:
        raise FileNotFoundError(
            f"data 폴더에 macro_data.xlsx 또는 macro_data.csv 가 없습니다: {DATA_DIR}"
        )

    if df is None or df.empty:
        raise ValueError("macro_data가 비어있습니다.")

    # ✅ drop duplicated column names (keep first)
    df = df.loc[:, ~df.columns.duplicated()].copy()

    # ✅ remove pandas auto columns if exist
    # (가끔 저장/복구 과정에서 "Unnamed: 0" 같은 게 생김)
    df = df.loc[:, [c for c in df.columns if not str(c).startswith("Unnamed:")]]

    cols = list(df.columns)

    # --------------------------------------------------
    # ✅ 핵심 FIX:
    # - 절대 df["date"]를 datetime으로 통째로 덮어쓰지 말 것
    # - date가 비었거나(=NaT) epoch(1970~)처럼 깨진 경우만 datetime으로 보정
    # --------------------------------------------------
    if "datetime" in df.columns:
        dt = pd.to_datetime(df["datetime"], errors="coerce")

        if "date" not in df.columns:
            # date가 없으면 새로 생성
            df["date"] = dt
        else:
            d = pd.to_datetime(df["date"], errors="coerce")

            # 1) date가 NaT인 곳만 datetime으로 채움
            d = d.where(d.notna(), dt)

            # 2) epoch(1970~)처럼 깨진 date는 datetime으로 교체 (datetime이 유효한 경우만)
            bad_epoch = d.notna() & (d.dt.year <= 1971) & dt.notna()
            d = d.where(~bad_epoch, dt)

            df["date"] = d

    # --------------------------------------------------
    # ✅ choose the best datetime column and normalize to "date"
    # --------------------------------------------------
    if "date" in df.columns:
        dt_col = "date"
    elif "datetime" in df.columns:
        dt_col = "datetime"
    else:
        # fallback: first column is usually datetime-like
        dt_col = cols[0]
        df = df.rename(columns={dt_col: "date"})
        dt_col = "date"

    if dt_col != "date":
        df = df.rename(columns={dt_col: "date"})

    # parse + clean
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # --------------------------------------------------
    # ✅ SAFETY: allow >=1 row
    # --------------------------------------------------
    if len(df) < 1:
        raise ValueError("macro_data에 유효한 date row가 없습니다.")

    return df
    
def load_fred_extras_df() -> pd.DataFrame:
    csv_path = DATA_DIR / "fred_macro_sctorallo.csv"
    expected_cols = [
        "date", "FCI", "REAL_RATE",
        "T10Y2Y", "T10YIE", "VIX", "DFII10", "DGS2"
    ]

    if not csv_path.exists():
        return pd.DataFrame(columns=expected_cols)

    df = pd.read_csv(csv_path)
    if df.empty:
        return pd.DataFrame(columns=expected_cols)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df

def load_sovereign_spreads_df() -> pd.DataFrame:
    csv_path = DATA_DIR / "sovereign_spreads.csv"
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return pd.DataFrame(columns=["date"])
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame(columns=["date"])

    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # drop duplicates
    df = df.loc[:, ~df.columns.duplicated()].copy()
    return df


def merge_sovereign_spreads_into_macro_df(df_macro: pd.DataFrame) -> pd.DataFrame:
    """
    A안 핵심:
    macro_data(df)에 sovereign_spreads(df)를 date 기준으로 merge해서
    df.columns에 KR10Y_SPREAD/IL10Y_SPREAD/...이 생기도록 만든다.
    """
    if df_macro is None or df_macro.empty:
        return df_macro

    s = load_sovereign_spreads_df()
    if s.empty:
        return df_macro

    # ensure datetime
    dfm = df_macro.copy()
    dfm["date"] = pd.to_datetime(dfm["date"], errors="coerce")

    # pick spread columns only (and optional *_Y if you want)
    keep_cols = [c for c in s.columns if c == "date" or c.endswith("_SPREAD")]
    s2 = s[keep_cols].copy()

    out = pd.merge(dfm, s2, on="date", how="left")

    # optional: ffill spreads (last available) – 권장
    spread_cols = [c for c in out.columns if c.endswith("_SPREAD")]
    for c in spread_cols:
        out[c] = pd.to_numeric(out[c], errors="coerce").ffill()

    # remove duplicates if any
    out = out.loc[:, ~out.columns.duplicated()].copy()
    return out

def attach_fred_extras_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    세연 님의 원본 로직을 유지하며 8번 필터용 지표들을 추가합니다.
    FCI, REAL_RATE 외에 T10Y2Y, T10YIE, VIX, DFII10, DXY, DGS2를 동일 구조로 주입합니다.
    """
    if market_data is None:
        market_data = {}

    # CSV 로드 (세연 님 원본 함수명 확인 필요)
    df = load_fred_extras_df() 
    if df is None or df.empty:
        market_data["_FCI_ASOF"] = None
        market_data["_REAL_ASOF"] = None
        return market_data

    df = df.copy()
    if "date" not in df.columns:
        return market_data

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # 1. 대상 컬럼 확장 (기존 2개 + 8번 필터용 6개)
    target_cols = ["FCI", "REAL_RATE", "T10Y2Y", "T10YIE", "DFII10", "DGS2"]
    
    for col in target_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = pd.NA

    # 2. 세연 님 원본 내부 함수 그대로 사용
    def _attach_one(key: str, asof_key: str):
        valid_df = df.dropna(subset=[key]).copy()
        if valid_df.empty:
            market_data[asof_key] = None
            return

        today_row = valid_df.iloc[-1]
        prev_row = valid_df.iloc[-2] if len(valid_df) >= 2 else None

        asof = pd.to_datetime(today_row["date"]).strftime("%Y-%m-%d")
        market_data[asof_key] = asof

        today_val = pd.to_numeric(today_row.get(key), errors="coerce")
        if pd.isna(today_val):
            return

        today_val_f = float(today_val)

        if prev_row is None:
            market_data[key] = {"today": today_val_f, "prev": None, "pct_change": None}
            return

        prev_val = pd.to_numeric(prev_row.get(key), errors="coerce")
        if pd.isna(prev_val):
            market_data[key] = {"today": today_val_f, "prev": None, "pct_change": None}
            return

        prev_val_f = float(prev_val)
        # pct_change 계산 로직 (원본 유지)
        pct = 0.0 if prev_val_f == 0 else ((today_val_f - prev_val_f) / prev_val_f) * 100.0
        market_data[key] = {"today": today_val_f, "prev": prev_val_f, "pct_change": pct}

    # 3. 모든 지표 실행 (ASOF 메타데이터는 기존 핵심 지표 위주로 유지)
    _attach_one("FCI", "_FCI_ASOF")
    _attach_one("REAL_RATE", "_REAL_ASOF")
    
    # 8번 필터용 지표들도 동일한 '세트 메뉴' 구조로 주입
    for extra_key in ["T10Y2Y", "T10YIE", "DFII10", "DGS2"]:
        _attach_one(extra_key, f"_{extra_key}_ASOF")

    return market_data
    
def load_liquidity_df() -> pd.DataFrame:
    csv_path = DATA_DIR / "liquidity_data.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    try:
        if csv_path.stat().st_size == 0:
            return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date", "TGA", "RRP", "WALCL", "NET_LIQ"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def load_credit_spread_df() -> pd.DataFrame:
    csv_path = DATA_DIR / "credit_spread_data.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=["date", "HY_OAS"])

    try:
        if csv_path.stat().st_size == 0:
            return pd.DataFrame(columns=["date", "HY_OAS"])
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame(columns=["date", "HY_OAS"])

    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date", "HY_OAS"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df

def load_fred_data_from_csv() -> pd.DataFrame:
    csv_path = "data/fred_macro_sctorallo.csv"
    
    # 🚨 DXY, VIX를 아예 삭제했습니다. 이제 FRED에서는 얘네 안 찾아요!
    target_cols = ["T10Y2Y", "T10YIE", "DFII10", "DGS2"]
    all_cols = ["date"] + target_cols

    if not os.path.exists(csv_path):
        return pd.DataFrame(columns=all_cols)

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[ERROR] load_fred_data_from_csv: {e}")
        return pd.DataFrame(columns=all_cols)

    df.columns = [str(c).strip() for c in df.columns]

    # 날짜 처리
    date_col = "date" if "date" in df.columns else "Date" if "Date" in df.columns else None
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).sort_values(date_col).reset_index(drop=True)
        df = df.rename(columns={date_col: "date"})

    # 🚨 존재하는 컬럼만 읽어오고, 나머지는 빈 칸 처리
    for col in target_cols:
        if col not in df.columns:
            df[col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df[["date"] + target_cols].ffill()


# -------------------------
# Builders
# -------------------------
def build_market_data(df: pd.DataFrame, today_idx: int) -> Dict[str, Any]:
    """
    Builds market_data dict using:
      - today value = df.iloc[today_idx][col]
      - prev value  = last available non-null value BEFORE today_idx
    This fixes "newly added columns" (XLK/XLF/XLE/XLRE) missing-prev issue.
    """
    market_data: Dict[str, Any] = {}

    def _to_num(x):
        v = pd.to_numeric(x, errors="coerce")
        return None if pd.isna(v) else float(v)

    def _find_prev_value(col: str) -> float | None:
        # scan backwards for last non-null
        for j in range(today_idx - 1, -1, -1):
            v = _to_num(df.iloc[j].get(col))
            if v is not None:
                return v
        return None

    today_row = df.iloc[today_idx]

    for col in df.columns:
        if col == "date" or col == "datetime":
            continue

        today_v = _to_num(today_row.get(col))
        if today_v is None:
            continue

        prev_v = _find_prev_value(col)
        if prev_v is None:
            # still store today (but pct_change is None)
            market_data[col] = {"today": today_v, "prev": None, "pct_change": None}
            continue

        pct = 0.0 if prev_v == 0 else ((today_v - prev_v) / prev_v) * 100.0
        market_data[col] = {"today": today_v, "prev": prev_v, "pct_change": pct}

    return market_data



def attach_liquidity_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach TGA/RRP/NET_LIQ into market_data using FRED 'last available valid' values.
    Adds meta: _LIQ_ASOF = 'YYYY-MM-DD'
    Also computes:
      - NET_LIQ dir: UP/DOWN/FLAT
      - NET_LIQ level_bucket: LOW/MID/HIGH
    """
    if market_data is None:
        market_data = {}

    liq_df = load_liquidity_df()
    if liq_df is None or liq_df.empty:
        market_data["_LIQ_ASOF"] = None
        market_data["TGA"] = {"today": None, "prev": None, "pct_change": None}
        market_data["RRP"] = {"today": None, "prev": None, "pct_change": None}
        market_data["NET_LIQ"] = {
            "today": None,
            "prev": None,
            "pct_change": None,
            "dir": "N/A",
            "level_bucket": "N/A",
        }
        return market_data

    if "date" not in liq_df.columns:
        market_data["_LIQ_ASOF"] = None
        market_data["TGA"] = {"today": None, "prev": None, "pct_change": None}
        market_data["RRP"] = {"today": None, "prev": None, "pct_change": None}
        market_data["NET_LIQ"] = {
            "today": None,
            "prev": None,
            "pct_change": None,
            "dir": "N/A",
            "level_bucket": "N/A",
        }
        return market_data

    liq_df = liq_df.copy()
    liq_df["date"] = pd.to_datetime(liq_df["date"], errors="coerce")

    for col in ["TGA", "RRP", "WALCL", "NET_LIQ"]:
        if col in liq_df.columns:
            liq_df[col] = pd.to_numeric(liq_df[col], errors="coerce")
        else:
            liq_df[col] = pd.NA

    liq_df = liq_df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # ✅ 마지막 row가 아니라 마지막 유효 liquidity row 사용
    valid_liq_df = liq_df.dropna(subset=["NET_LIQ"]).copy()

    if valid_liq_df.empty:
        market_data["_LIQ_ASOF"] = None
        market_data["TGA"] = {"today": None, "prev": None, "pct_change": None}
        market_data["RRP"] = {"today": None, "prev": None, "pct_change": None}
        market_data["NET_LIQ"] = {
            "today": None,
            "prev": None,
            "pct_change": None,
            "dir": "N/A",
            "level_bucket": "N/A",
        }
        return market_data

    liq_today = valid_liq_df.iloc[-1]
    liq_prev = valid_liq_df.iloc[-2] if len(valid_liq_df) >= 2 else None

    liq_asof = pd.to_datetime(liq_today["date"]).strftime("%Y-%m-%d")
    market_data["_LIQ_ASOF"] = liq_asof

    def _to_float(x) -> Optional[float]:
        if x is None:
            return None
        try:
            if pd.isna(x):
                return None
            return float(x)
        except Exception:
            try:
                x2 = str(x).replace(",", "").replace("%", "").strip()
                if x2 == "":
                    return None
                return float(x2)
            except Exception:
                return None

    def add_liq_key(key: str, today_val, prev_val):
        t = _to_float(today_val)
        p = _to_float(prev_val)

        if t is None:
            market_data[key] = {"today": None, "prev": None if p is None else p, "pct_change": None}
            return

        if p is None:
            market_data[key] = {"today": t, "prev": None, "pct_change": None}
            return

        pct = 0.0 if p == 0 else ((t - p) / p) * 100.0
        market_data[key] = {"today": t, "prev": p, "pct_change": pct}

    add_liq_key("TGA", liq_today.get("TGA"), None if liq_prev is None else liq_prev.get("TGA"))
    add_liq_key("RRP", liq_today.get("RRP"), None if liq_prev is None else liq_prev.get("RRP"))
    add_liq_key("NET_LIQ", liq_today.get("NET_LIQ"), None if liq_prev is None else liq_prev.get("NET_LIQ"))

    net = market_data.get("NET_LIQ") or {"today": None, "prev": None, "pct_change": None}
    net_today = _to_float(net.get("today"))
    net_prev = _to_float(net.get("prev"))

    if net_today is None or net_prev is None:
        net_dir = "N/A"
    else:
        if net_today > net_prev:
            net_dir = "UP"
        elif net_today < net_prev:
            net_dir = "DOWN"
        else:
            net_dir = "FLAT"

    level_bucket = "N/A"
    if net_today is not None and "NET_LIQ" in valid_liq_df.columns:
        series = pd.to_numeric(valid_liq_df["NET_LIQ"], errors="coerce").dropna()

        if len(series) >= 20:
            pct_rank = (series <= net_today).mean()
        else:
            vmin, vmax = float(series.min()), float(series.max())
            if vmax == vmin:
                pct_rank = 0.5
            else:
                pct_rank = (net_today - vmin) / (vmax - vmin)

        if pct_rank < 0.33:
            level_bucket = "LOW"
        elif pct_rank < 0.66:
            level_bucket = "MID"
        else:
            level_bucket = "HIGH"

    net["dir"] = net_dir
    net["level_bucket"] = level_bucket
    market_data["NET_LIQ"] = net

    market_data["NET_LIQ_DIR"] = net_dir
    market_data["NET_LIQ_LEVEL_BUCKET"] = level_bucket

    return market_data
    

def attach_credit_spread_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach HY_OAS (FRED last available valid) into market_data.
    Adds:
      - HY_OAS = {today, prev, pct_change}
      - _HY_ASOF = 'YYYY-MM-DD'
    """
    if market_data is None:
        market_data = {}

    df = load_credit_spread_df()
    if df is None or df.empty:
        market_data["_HY_ASOF"] = None
        return market_data

    df = df.copy()

    if "date" not in df.columns or "HY_OAS" not in df.columns:
        market_data["_HY_ASOF"] = None
        return market_data

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["HY_OAS"] = pd.to_numeric(df["HY_OAS"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # ✅ 마지막 row가 아니라 마지막 유효 HY_OAS row 사용
    valid_df = df.dropna(subset=["HY_OAS"]).copy()
    if valid_df.empty:
        market_data["_HY_ASOF"] = None
        return market_data

    today_row = valid_df.iloc[-1]
    prev_row = valid_df.iloc[-2] if len(valid_df) >= 2 else None

    asof = pd.to_datetime(today_row["date"]).strftime("%Y-%m-%d")
    market_data["_HY_ASOF"] = asof

    today_val_f = float(today_row["HY_OAS"])

    if prev_row is None or pd.isna(prev_row.get("HY_OAS")):
        market_data["HY_OAS"] = {"today": today_val_f, "prev": None, "pct_change": None}
        return market_data

    prev_val_f = float(prev_row["HY_OAS"])
    pct = 0.0 if prev_val_f == 0 else ((today_val_f - prev_val_f) / prev_val_f) * 100.0
    market_data["HY_OAS"] = {"today": today_val_f, "prev": prev_val_f, "pct_change": pct}
    return market_data


def attach_expectation_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach external expectation data into market_data safely.
    We don't assume any specific schema from fetch_expectation_data().
    Supported return types:
      - dict
      - list[dict]
      - pandas.DataFrame
    We store it under:
      - market_data["_EXP_ASOF"] (optional)
      - market_data["EXPECTATIONS"] (raw, lightweight)
    So it won't break existing filters until you explicitly use it.
    """
    if market_data is None:
        market_data = {}

    try:
        exp = fetch_expectation_data()
        # ✅ DEBUG: 액션 로그에서 확인 가능
        print("[DEBUG] fetch_expectation_data() type:", type(exp))
        if isinstance(exp, list):
            print("[DEBUG] expectations list len:", len(exp))
            print("[DEBUG] first item:", exp[0] if len(exp) > 0 else None)
        elif isinstance(exp, dict):
            print("[DEBUG] expectations dict keys:", list(exp.keys())[:30])
        else:
            print("[DEBUG] expectations repr:", repr(exp)[:500])
    except Exception as e:
        # ✅ DEBUG: 왜 실패했는지 액션 로그에 찍힘
        print("[DEBUG] fetch_expectation_data() ERROR:", type(e).__name__, str(e))
        market_data["_EXP_ERROR"] = f"{type(e).__name__}: {e}"
        return market_data

    # normalize "as of" if provided
    asof = None

    # DataFrame
    if isinstance(exp, pd.DataFrame):
        if not exp.empty:
            # if it has date column
            for c in ("date", "as_of", "asof", "updated_at"):
                if c in exp.columns:
                    try:
                        asof = pd.to_datetime(exp.iloc[-1][c]).strftime("%Y-%m-%d")
                    except Exception:
                        pass
                    break
            market_data["EXPECTATIONS"] = exp.tail(30).to_dict(orient="records")
        else:
            market_data["EXPECTATIONS"] = []
        market_data["_EXP_ASOF"] = asof
        return market_data

    # dict
    if isinstance(exp, dict):
        # common patterns: {"as_of": "...", "items": [...]}
        for c in ("as_of", "asof", "date", "updated_at"):
            v = exp.get(c)
            if isinstance(v, str) and v.strip():
                asof = v.strip()
                break
        items = exp.get("items", exp)
        market_data["EXPECTATIONS"] = items
        market_data["_EXP_ASOF"] = asof
        return market_data

    # list
    if isinstance(exp, list):
        market_data["EXPECTATIONS"] = exp
        market_data["_EXP_ASOF"] = None
        return market_data

    # fallback
    market_data["EXPECTATIONS"] = {"raw": str(exp)}
    market_data["_EXP_ASOF"] = None
    return market_data

# -------------------------
# Sentiment Proxy Layer (NO CNN)
# -------------------------
def attach_sentiment_proxy_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach SENTIMENT from our own sentiment_proxy.csv (Wall-Street style proxy).
    - No CNN Fear&Greed.
    - Never overwrites existing SENTIMENT unless proxy data is available.
    """
    if market_data is None:
        market_data = {}

    csv_path = DATA_DIR / "sentiment_proxy.csv"
    if (not csv_path.exists()) or csv_path.stat().st_size == 0:
        # No proxy file -> keep existing market_data as-is
        return market_data

    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return market_data

    if df.empty or "date" not in df.columns or "sentiment_proxy" not in df.columns:
        return market_data

    last = df.iloc[-1]
    try:
        val = float(last["sentiment_proxy"])
    except Exception:
        return market_data

    market_data["SENTIMENT"] = {
        "fear_greed": val,                 # keep key name for compatibility with Narrative Engine
        "source": str(last.get("used", "proxy")),
        "as_of": str(last.get("date", "")),
    }
    return market_data

def load_sovereign_yields_df() -> pd.DataFrame:
    csv_path = DATA_DIR / "sovereign_yields.csv"
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return pd.DataFrame(columns=["date"])

    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame(columns=["date"])

    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df

def load_sovereign_spreads_df() -> pd.DataFrame:
    csv_path = DATA_DIR / "sovereign_spreads.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=["date"])

    try:
        if csv_path.stat().st_size == 0:
            return pd.DataFrame(columns=["date"])
        df = pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame(columns=["date"])

    if df.empty or "date" not in df.columns:
        return pd.DataFrame(columns=["date"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def attach_sovereign_spread_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach sovereign yields/spreads from data/sovereign_spreads.csv using
    last available valid values (not just the last row).

    Adds meta:
      - _SOV_ASOF

    Adds keys (if exist):
      - KR10Y_SPREAD, JP10Y_SPREAD, DE10Y_SPREAD, IL10Y_SPREAD ...
      - KR10Y_Y, JP10Y_Y, DE10Y_Y, IL10Y_Y ...
      as {today, prev, pct_change}
    """
    if market_data is None:
        market_data = {}

    df = load_sovereign_spreads_df()
    if df is None or df.empty:
        market_data["_SOV_ASOF"] = None
        return market_data

    if "date" not in df.columns:
        market_data["_SOV_ASOF"] = None
        return market_data

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    # 숫자 컬럼 정리
    value_cols = [c for c in df.columns if c != "date"]
    for c in value_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    spread_cols = [c for c in df.columns if c.endswith("_SPREAD")]
    yield_cols = [c for c in df.columns if c.endswith("_Y")]
    target_cols = spread_cols + yield_cols

    # ✅ "하나라도 값이 있는 마지막 날짜"를 asof로 사용
    valid_any_df = df.dropna(subset=target_cols, how="all").copy() if target_cols else pd.DataFrame()
    if valid_any_df.empty:
        market_data["_SOV_ASOF"] = None
        return market_data

    latest_any_row = valid_any_df.iloc[-1]
    market_data["_SOV_ASOF"] = pd.to_datetime(latest_any_row["date"]).strftime("%Y-%m-%d")

    def _attach_one(col: str):
        if col not in df.columns:
            return

        valid_df = df.dropna(subset=[col]).copy()
        if valid_df.empty:
            return

        today_row = valid_df.iloc[-1]
        prev_row = valid_df.iloc[-2] if len(valid_df) >= 2 else None

        t = pd.to_numeric(today_row.get(col), errors="coerce")
        if pd.isna(t):
            return
        t = float(t)

        if prev_row is None:
            market_data[col] = {"today": t, "prev": None, "pct_change": None}
            return

        p = pd.to_numeric(prev_row.get(col), errors="coerce")
        if pd.isna(p):
            market_data[col] = {"today": t, "prev": None, "pct_change": None}
            return

        p = float(p)
        pct = 0.0 if p == 0 else ((t - p) / p) * 100.0
        market_data[col] = {"today": t, "prev": p, "pct_change": pct}

    for c in spread_cols:
        _attach_one(c)

    for c in yield_cols:
        _attach_one(c)

    return market_data

def _find_effective_market_idx(
    df: pd.DataFrame,
    core_cols: Optional[List[str]] = None,
    min_valid_count: int = 4,
) -> int:
    """
    마지막 행이 비어 있을 수 있으므로,
    핵심 지표가 충분히 채워진 마지막 유효 row index를 찾는다.
    기본은 core 5개 중 4개 이상 값이 있는 마지막 행.
    """
    if core_cols is None:
        core_cols = ["US10Y", "DXY", "WTI", "VIX", "USDKRW"]

    existing = [c for c in core_cols if c in df.columns]
    if not existing:
        return len(df) - 1

    tmp = df.copy()
    for c in existing:
        tmp[c] = pd.to_numeric(tmp[c], errors="coerce")

    valid_count = tmp[existing].notna().sum(axis=1)
    candidates = tmp.index[valid_count >= min_valid_count].tolist()

    if candidates:
        return int(candidates[-1])

    # fallback: 핵심지표 중 하나라도 있는 마지막 행
    candidates_any = tmp.index[tmp[existing].notna().any(axis=1)].tolist()
    if candidates_any:
        return int(candidates_any[-1])

    return len(df) - 1
    
    
    
def generate_daily_report() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # 0) ETF 통합 파일 확인 / 없을 때만 생성
    # -----------------------------
    etf_file_path = "data/country_etf_data_combined.csv"

    if not os.path.exists(etf_file_path):
        print("[INFO] country_etf_data_combined.csv not found. Running combined ETF download...")
        download_all_etfs_and_save()

    etf_check_df = load_etf_data_from_csv(etf_file_path)
    if etf_check_df.empty:
        print("[ERROR] No data available in country_etf_data_combined.csv")
        return

    print("[DEBUG] ETF combined shape:", etf_check_df.shape)
    print("[DEBUG] ETF combined columns:", list(etf_check_df.columns))

    # -----------------------------
    # 1) 기존 매크로 데이터 로드
    # -----------------------------
    df = load_macro_df()
    df = merge_sovereign_spreads_into_macro_df(df)

    today_idx = _find_effective_market_idx(
        df,
        core_cols=["US10Y", "DXY", "WTI", "VIX", "USDKRW"],
        min_valid_count=4,
    )

    data_as_of_date = pd.to_datetime(df.iloc[today_idx]["date"]).strftime("%Y-%m-%d")
    report_date = pd.Timestamp.now(tz="Asia/Seoul").strftime("%Y-%m-%d")

    print("[DEBUG] effective today_idx =", today_idx)
    print("[DEBUG] report_date (KST) =", report_date)
    print("[DEBUG] data_as_of_date =", data_as_of_date)
    print(
        df[["date", "US10Y", "DXY", "WTI", "VIX", "USDKRW"]]
        .tail(10)
        .to_string(index=False)
    )
    print("\n" + "="*50)
    print(f"!!! [BEFORE BUILD] CSV DXY (today_idx): {df.iloc[today_idx].get('DXY')}")
    print("="*50 + "\n")
    
    market_data = build_market_data(df, today_idx)
    
    print("\n" + "="*50)
    print(f"!!! [AFTER BUILD] MarketData DXY: {market_data.get('DXY', {}).get('today')}")
    print("="*50 + "\n")
    
    # -----------------------------
    # 2) Detect stale / market closed
    # -----------------------------
    stale = False
    try:
        last_date = pd.to_datetime(df.iloc[today_idx]["date"]).date()
        now_utc = pd.Timestamp.now("UTC")
        today_utc = now_utc.date()

        if now_utc.weekday() >= 5:  # 5=Sat, 6=Sun
            stale = True
        elif (today_utc - last_date).days >= 2:
            stale = True
    except Exception:
        stale = False

    market_data["_STALE"] = stale

    # -----------------------------
    # 3) Attach layers (기존 코드 시작)
    # -----------------------------
    market_data = attach_liquidity_layer(market_data) or market_data
    market_data = attach_credit_spread_layer(market_data) or market_data
    market_data = attach_fred_extras_layer(market_data) or market_data
    market_data = attach_sovereign_spread_layer(market_data) or market_data
    market_data = attach_expectation_layer(market_data) or market_data
    market_data = attach_geopolitical_ew_layer(market_data, df, today_idx) or market_data

    # 국가 ETF 리스크 레이어 먼저
    market_data = attach_country_risk_layer(market_data, df, today_idx) or market_data

    # Cosine Similarity는 country risk 이후
    market_data = attach_geo_similarity_layer(market_data) or market_data

    # Wall-Street Sentiment Proxy
    market_data = attach_sentiment_proxy_layer(market_data) or market_data

    # regime change monitor
    regime_result = check_regime_change_and_alert(market_data, data_as_of_date)

    # -------------------------
    # 4) FINAL_STATE 이후 overlay / RAROC 먼저 반영
    # -------------------------
    market_data = apply_geo_overlay_to_final_state(market_data) or market_data

    # -------------------------
    # 4.5) Inject FRED sector-allocation extras
    # -------------------------
    df_fred_extra = load_fred_data_from_csv()

    if not df_fred_extra.empty:
        latest_fred = df_fred_extra.iloc[-1]

        market_data["_FRED_EXTRA"] = {
            "T10Y2Y": float(latest_fred["T10Y2Y"]) if pd.notna(latest_fred["T10Y2Y"]) else 0.0,
            "T10YIE": float(latest_fred["T10YIE"]) if pd.notna(latest_fred["T10YIE"]) else 0.0,
            "DFII10": float(latest_fred["DFII10"]) if pd.notna(latest_fred.get("DFII10")) else 0.0,
            
            # 🚨 보정: FRED의 120 대신, 앞서 build_market_data에서 가져온 98.xx를 씁니다.
            "VIX": market_data["VIX"].get("today") if "VIX" in market_data else 20.0,
            "DXY": market_data["DXY"].get("today") if "DXY" in market_data else 100.0,

        print("[DEBUG] Fred Extra Saved:", market_data["_FRED_EXTRA"])
        print("[DEBUG BEFORE COMMENTARY] FINAL_STATE:", market_data.get("FINAL_STATE"))
    else:
        print("[DEBUG] Fred Extra Saved: skipped (empty fred df)")
    
    print("[DEBUG BEFORE COMMENTARY] FINAL_STATE:", market_data.get("FINAL_STATE"))
    commentary_block = build_strategist_commentary(market_data)
    # -------------------------
    # 6) Fred Data Loading and Injection
    # -------------------------

    # 5) Top layers
    exec_block = executive_summary_filter(market_data)
    decision_block = decision_layer_filter(market_data)
    scenario_block = scenario_generator_filter(market_data)
    transmission_block = transmission_layer_filter(market_data)

    # -------------------------
    # 6) Country ETF risk block
    # -------------------------
    country_risk_keys = sorted([k for k in market_data.keys() if k.startswith("COUNTRY_RISK_")])

    country_risk_lines = []
    if country_risk_keys:
        country_risk_lines.append("## 🌐 Country ETF Risk Monitor")
        country_risk_lines.append("")
        for key in country_risk_keys:
            country_risk = market_data[key]
            country_risk_lines.append(f"### {country_risk['country_etf']}")
            country_risk_lines.append(f"- **Crash?** {country_risk['crash']}")
            country_risk_lines.append(f"- **Risk Level:** {country_risk['risk_level']}")
            country_risk_lines.append(f"- **Z-Score (1d):** {country_risk['z_1d']}")
            country_risk_lines.append(f"- **Z-Score (5d):** {country_risk['z_5d']}")
            country_risk_lines.append("")
    else:
        country_risk_lines.append("## 🌐 Country ETF Risk Monitor")
        country_risk_lines.append("")
        country_risk_lines.append("- No country ETF risk data available.")
        country_risk_lines.append("")

    # -------------------------
    # Report assembly
    # -------------------------
    lines = []
    lines.append("# 🌍 Global Capital Flow – Daily Brief")
    lines.append(f"**Date:** {report_date}")
    lines.append(f"**Data as of:** {data_as_of_date}")
    lines.append("")
    lines.append("## 📊 Daily Macro Signals")
    lines.append("")

    # daily core signals
    if "US10Y" in market_data and market_data["US10Y"].get("today") is not None:
        prev = market_data["US10Y"].get("prev")
        pct = market_data["US10Y"].get("pct_change")
        lines.append(
            f"- **미국 10년물 금리**: {market_data['US10Y']['today']:.3f}  "
            f"({pct:+.2f}% vs {prev:.3f})" if (prev is not None and pct is not None) else
            f"- **미국 10년물 금리**: {market_data['US10Y']['today']:.3f}"
        )

    if "DXY" in market_data and market_data["DXY"].get("today") is not None:
        prev = market_data["DXY"].get("prev")
        pct = market_data["DXY"].get("pct_change")
        lines.append(
            f"- **달러 인덱스**: {market_data['DXY']['today']:.3f}  "
            f"({pct:+.2f}% vs {prev:.3f})" if (prev is not None and pct is not None) else
            f"- **달러 인덱스**: {market_data['DXY']['today']:.3f}"
        )

    if "WTI" in market_data and market_data["WTI"].get("today") is not None:
        prev = market_data["WTI"].get("prev")
        pct = market_data["WTI"].get("pct_change")
        lines.append(
            f"- **WTI 유가**: {market_data['WTI']['today']:.3f}  "
            f"({pct:+.2f}% vs {prev:.3f})" if (prev is not None and pct is not None) else
            f"- **WTI 유가**: {market_data['WTI']['today']:.3f}"
        )

    if "VIX" in market_data and market_data["VIX"].get("today") is not None:
        prev = market_data["VIX"].get("prev")
        pct = market_data["VIX"].get("pct_change")
        lines.append(
            f"- **변동성 지수 (VIX)**: {market_data['VIX']['today']:.3f}  "
            f"({pct:+.2f}% vs {prev:.3f})" if (prev is not None and pct is not None) else
            f"- **변동성 지수 (VIX)**: {market_data['VIX']['today']:.3f}"
        )

    if "USDKRW" in market_data and market_data["USDKRW"].get("today") is not None:
        prev = market_data["USDKRW"].get("prev")
        pct = market_data["USDKRW"].get("pct_change")
        lines.append(
            f"- **원/달러 환율**: {market_data['USDKRW']['today']:.3f}  "
            f"({pct:+.2f}% vs {prev:.3f})" if (prev is not None and pct is not None) else
            f"- **원/달러 환율**: {market_data['USDKRW']['today']:.3f}"
        )

    # Optional: Liquidity Snapshot block
    if SHOW_LIQUIDITY_SNAPSHOT:
        liq_asof = market_data.get("_LIQ_ASOF")
        tga = market_data.get("TGA", {}).get("today")
        rrp = market_data.get("RRP", {}).get("today")
        net = market_data.get("NET_LIQ", {}).get("today")

        if liq_asof and (tga is not None or rrp is not None or net is not None):
            lines.append("")
            lines.append("## 💧 Liquidity Snapshot (FRED last available)")
            lines.append(f"- **Liquidity as of**: **{liq_asof}** *(FRED latest)*")
            if tga is not None:
                lines.append(f"- **TGA**: {float(tga):.1f}")
            if rrp is not None:
                lines.append(f"- **RRP**: {float(rrp):.3f}")
            if net is not None:
                lines.append(f"- **NET_LIQ**: {float(net):.1f}")

    # ✅ Regime Change Monitor
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🚨 Regime Change Monitor (always-on)")

    if regime_result.get("status") == "DETECTED":
        lines.append(f"- **Status:** ✅ DETECTED")
        lines.append(f"- **Prev → Current:** {regime_result.get('prev_regime')} → {regime_result.get('current_regime')}")
        lines.append(f"- **File:** `insights/risk_alerts.txt` ✅ created")
        lines.append(f"- **Email:** {'✅ sent' if regime_result.get('email_sent') else '❌ not sent'} ({regime_result.get('email_note')})")
    elif regime_result.get("status") == "NOT_DETECTED":
        lines.append(f"- **Status:** ❎ NOT DETECTED")
        lines.append(f"- **Current Regime:** {regime_result.get('current_regime')}")
        lines.append(f"- **File:** not created")
        lines.append(f"- **Email:** not sent")
    else:
        lines.append(f"- **Status:** ⚪ BASELINE SET (first run)")
        lines.append(f"- **Current Regime:** {regime_result.get('current_regime')}")
        lines.append(f"- **File/Email:** not created (no previous regime to compare)")

    # -------------------------
    # Top layers first
    # -------------------------
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(commentary_block)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(exec_block)
    lines.append("")
    lines.append(decision_block)
    lines.append("")
    lines.append(scenario_block)
    lines.append("")
    lines.append(transmission_block)
    lines.append("")
    lines.append("---")
    lines.append("")

  

    # Optional country block append
    if country_risk_lines:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.extend(country_risk_lines)

    report_path = REPORTS_DIR / f"daily_report_{report_date}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Report written: {report_path}")
    return market_data
    
def generate_final_state_history():
    BACKTEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

    df = load_macro_df()
    df = merge_sovereign_spreads_into_macro_df(df)

    rows = []
    start_idx = max(0, len(df) - 30)  # 테스트용: 최근 30일만

    for idx in range(start_idx, len(df)):

        if idx % 5 == 0:
            print(f"[BACKTEST] processing {idx}/{len(df)}")

        try:
            market_data = build_market_data(df, idx)
            market_data["_STALE"] = False

            # 기존 리포트 파이프라인과 최대한 같은 순서 유지
            market_data = attach_liquidity_layer(market_data) or market_data
            market_data = attach_credit_spread_layer(market_data) or market_data
            market_data = attach_fred_extras_layer(market_data) or market_data
            market_data = attach_sovereign_spread_layer(market_data) or market_data
            market_data = attach_expectation_layer(market_data) or market_data
            market_data = attach_geopolitical_ew_layer(market_data, df, idx) or market_data
            market_data = attach_country_risk_layer(market_data, df, idx) or market_data
            market_data = attach_geo_similarity_layer(market_data) or market_data
            market_data = attach_sentiment_proxy_layer(market_data) or market_data

            # 1번 필터: MARKET_REGIME 저장
            market_regime_filter(market_data)

            # FINAL_STATE에 FRED extra 주입
            df_fred_extra = load_fred_data_from_csv()
            if not df_fred_extra.empty:
                current_date = pd.to_datetime(df.iloc[idx]["date"])
                fred_subset = df_fred_extra[df_fred_extra["date"] <= current_date]

                if not fred_subset.empty:
                    latest_fred = fred_subset.iloc[-1]

                    if "FINAL_STATE" not in market_data or market_data["FINAL_STATE"] is None:
                        market_data["FINAL_STATE"] = {}

                    market_data["FINAL_STATE"]["T10Y2Y"] = (
                        float(latest_fred["T10Y2Y"]) if pd.notna(latest_fred["T10Y2Y"]) else None
                    )
                    market_data["FINAL_STATE"]["T10YIE"] = (
                        float(latest_fred["T10YIE"]) if pd.notna(latest_fred["T10YIE"]) else None
                    )
                   market_data["FINAL_STATE"]["VIX"] = (
                        float(market_data["VIX"]["today"]) if "VIX" in market_data and market_data["VIX"] is not None 
                        else (float(latest_fred["VIX"]) if pd.notna(latest_fred["VIX"]) else market_data["FINAL_STATE"].get("VIX"))
                    )
                    market_data["FINAL_STATE"]["DFII10"] = (
                        float(latest_fred["DFII10"]) if pd.notna(latest_fred["DFII10"]) else None
                    )
                    market_data["FINAL_STATE"]["DXY"] = (
                        float(market_data["DXY"]["today"]) if "DXY" in market_data and market_data["DXY"] is not None 
                        else (float(latest_fred["DXY"]) if pd.notna(latest_fred["DXY"]) else None)
                    )
                    market_data["FINAL_STATE"]["DGS2"] = (
                        float(latest_fred["DGS2"]) if pd.notna(latest_fred["DGS2"]) else None
                    )
                    market_data["FINAL_STATE"]["FCI"] = (
                        float(latest_fred["FCI"]) if "FCI" in latest_fred and pd.notna(latest_fred["FCI"]) else None
                    )
                    market_data["FINAL_STATE"]["REAL_RATE"] = (
                        float(latest_fred["REAL_RATE"]) if "REAL_RATE" in latest_fred and pd.notna(latest_fred["REAL_RATE"]) else None
                    )

            # Narrative Engine이 FINAL_STATE 생성
            narrative_engine_filter(market_data)

            # Geo overlay 반영
            market_data = apply_geo_overlay_to_final_state(market_data) or market_data
            final_state = market_data.get("FINAL_STATE", {}) or {}

            rows.append({
                "date": pd.to_datetime(df.iloc[idx]["date"]).strftime("%Y-%m-%d"),
                "market_regime": market_data.get("MARKET_REGIME"),
                "phase": final_state.get("phase"),
                "phase_cap": final_state.get("phase_cap"),
                "risk_action": final_state.get("risk_action"),
                "risk_budget": final_state.get("risk_budget"),
                "structure_tag": final_state.get("structure_tag"),
                "sentiment_state": final_state.get("sentiment_state"),
                "sentiment_fear_greed": final_state.get("sentiment_fear_greed"),
                "credit_calm": final_state.get("credit_calm"),
                "hy_oas_today": final_state.get("hy_oas_today"),
                "liquidity_dir": final_state.get("liquidity_dir"),
                "liquidity_level_bucket": final_state.get("liquidity_level_bucket"),
                "net_liq_pct_change": final_state.get("net_liq_pct_change"),
                "T10Y2Y": final_state.get("T10Y2Y"),
                "T10YIE": final_state.get("T10YIE"),
                "VIX": final_state.get("VIX"),
                "DFII10": final_state.get("DFII10"),
                "DXY": final_state.get("DXY"),
                "DGS2": final_state.get("DGS2"),
                "FCI": final_state.get("FCI"),
                "REAL_RATE": final_state.get("REAL_RATE"),
                "narrative_line": final_state.get("narrative_line"),
            })

        except Exception as e:
            rows.append({
                "date": pd.to_datetime(df.iloc[idx]["date"]).strftime("%Y-%m-%d"),
                "market_regime": None,
                "phase": None,
                "phase_cap": None,
                "risk_action": None,
                "risk_budget": None,
                "structure_tag": None,
                "sentiment_state": None,
                "sentiment_fear_greed": None,
                "credit_calm": None,
                "hy_oas_today": None,
                "liquidity_dir": None,
                "liquidity_level_bucket": None,
                "net_liq_pct_change": None,
                "T10Y2Y": None,
                "T10YIE": None,
                "VIX": None,
                "DFII10": None,
                "DXY": None,
                "DGS2": None,
                "FCI": None,
                "REAL_RATE": None,
                "narrative_line": f"ERROR: {type(e).__name__}: {e}",
            })

    out_df = pd.DataFrame(rows)
    output_path = BACKTEST_DATA_DIR / "final_state_history.csv"
    out_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"[OK] Final state history written: {output_path}")
    print(out_df.tail(5).to_string(index=False))

    return out_df
        
            
          
    
if __name__ == "__main__":
    #백테스트
    
    generate_final_state_history()
    # 기존 리포트 실행
    real_market_data = generate_daily_report()

    # =========================
    # 🔥 ETF BACKTEST DEBUG BLOCK
    # =========================
    print("\n" + "=" * 60)
    print("🚀 ETF BACKTEST DEBUG START")
    #print(combined_df.index[0], combined_df.index[-1])

    try:
        from etf_returns import (
            build_regime_portfolio,
            build_portfolio_returns,
            calculate_returns,
            compare_portfolios,
            compare_against_benchmark,
            build_single_benchmark_returns,
            build_6040_benchmark_returns,
            base_weights,
        )

        # ETF 데이터 로드
        combined_df = calculate_returns(base_weights)

        if combined_df is not None:
            combined_df = combined_df.sort_index()

            # Base 포트폴리오
            base_returns = build_portfolio_returns(
                combined_df,
                base_weights,
                "Base"
            )

            market_data = real_market_data or {}

            market_data.setdefault("SECTOR_OW", ["Consumer Staples", "Utilities", "Health Care"])
            market_data.setdefault("SECTOR_UW", ["Technology", "Consumer Discretionary", "Real Estate"])

            # Regime 포트폴리오
            filtered_weights, scores, regime, style_tags = build_regime_portfolio(market_data)

            print("\n📊 Regime")
            print(regime)

            print("\n📊 Style Tags")
            print(style_tags)

            print("\n📊 ETF Scores")
            print(scores)

            print("\n📊 Auto Generated ETF Weights")
            print(filtered_weights)

            filtered_returns = build_portfolio_returns(
                combined_df,
                filtered_weights,
                "Filtered"
            )

            comparison = compare_portfolios(base_returns, filtered_returns)

            print("\n📊 Base vs Filtered Portfolio Comparison")
            print(comparison.round(4))

            # SPY benchmark 비교
            spy_returns = build_single_benchmark_returns(
                combined_df,
                symbol="SPY",
                benchmark_name="SPY_Return"
            )

            spy_comparison = compare_against_benchmark(
                filtered_returns,
                spy_returns,
                benchmark_label="SPY"
            )

            print("\n📊 Filtered Portfolio vs SPY")
            print(spy_comparison.round(4))

            # 60/40 benchmark 비교
            benchmark_6040_returns = build_6040_benchmark_returns(combined_df)

            benchmark_6040_comparison = compare_against_benchmark(
                filtered_returns,
                benchmark_6040_returns,
                benchmark_label="60_40"
            )

            print("\n📊 Filtered Portfolio vs 60/40")
            print(benchmark_6040_comparison.round(4))

        else:
            print("❌ ETF 데이터 없음")

    except Exception as e:
        print(f"❌ ETF BACKTEST ERROR: {e}")

    print("🚀 ETF BACKTEST DEBUG END")
    print("=" * 60)

    
