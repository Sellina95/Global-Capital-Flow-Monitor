from __future__ import annotations
from filters.decision_layer import decision_layer_filter
from filters.transmission_layer import transmission_layer_filter

from pathlib import Path
from typing import Dict, Any
import pandas as pd

from filters.strategist_filters import build_strategist_commentary
from filters.executive_layer import executive_summary_filter
from filters.scenario_layer import scenario_generator_filter
from scripts.risk_alerts import check_regime_change_and_alert
from scripts.fetch_expectation_data import fetch_expectation_data  # external expectations
from scripts.fetch_sentiment import fetch_cnn_fear_greed


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

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
    csv_path = DATA_DIR / "fred_macro_extras.csv"
    if not csv_path.exists():
        return pd.DataFrame(columns=["date", "FCI", "REAL_RATE"])

    df = pd.read_csv(csv_path)
    if df.empty:
        return pd.DataFrame(columns=["date", "FCI", "REAL_RATE"])

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def attach_fred_extras_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach FCI & REAL_RATE using FRED 'last available' values.
    Adds meta:
      - _FCI_ASOF, _REAL_ASOF (same as last row date)
    Adds series:
      - FCI, REAL_RATE as {today, prev, pct_change}
    """
    df = load_fred_extras_df()
    if df.empty:
        market_data["_FCI_ASOF"] = None
        market_data["_REAL_ASOF"] = None
        return market_data

    today_row = df.iloc[-1]
    asof = pd.to_datetime(today_row["date"]).strftime("%Y-%m-%d")
    market_data["_FCI_ASOF"] = asof
    market_data["_REAL_ASOF"] = asof

    prev_row = df.iloc[-2] if len(df) >= 2 else None

    def add_key(key: str):
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
        pct = 0.0 if prev_val_f == 0 else ((today_val_f - prev_val_f) / prev_val_f) * 100.0
        market_data[key] = {"today": today_val_f, "prev": prev_val_f, "pct_change": pct}

    add_key("FCI")
    add_key("REAL_RATE")
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
    Attach TGA/RRP/NET_LIQ into market_data using FRED 'last available' values.
    Adds meta: _LIQ_ASOF = 'YYYY-MM-DD'
    Also computes:
      - NET_LIQ dir: UP/DOWN/FLAT
      - NET_LIQ level_bucket: LOW/MID/HIGH (never N/A if today exists)
    """
    if market_data is None:
        market_data = {}

    liq_df = load_liquidity_df()
    if liq_df is None or liq_df.empty:
        market_data["_LIQ_ASOF"] = None
        # ensure keys exist to avoid downstream N/A confusion
        market_data.setdefault("NET_LIQ", {"today": None, "prev": None, "pct_change": None, "dir": "N/A", "level_bucket": "N/A"})
        return market_data

    # --- normalize columns safety ---
    # expected: date, TGA, RRP, WALCL, NET_LIQ
    if "date" not in liq_df.columns:
        market_data["_LIQ_ASOF"] = None
        market_data.setdefault("NET_LIQ", {"today": None, "prev": None, "pct_change": None, "dir": "N/A", "level_bucket": "N/A"})
        return market_data

    liq_df = liq_df.copy()
    liq_df["date"] = pd.to_datetime(liq_df["date"], errors="coerce")
    liq_df = liq_df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)

    liq_today = liq_df.iloc[-1]
    liq_asof = pd.to_datetime(liq_today["date"]).strftime("%Y-%m-%d")
    market_data["_LIQ_ASOF"] = liq_asof

    liq_prev = liq_df.iloc[-2] if len(liq_df) >= 2 else None

    def _to_float(x) -> Optional[float]:
        if x is None:
            return None
        try:
            return float(x)
        except Exception:
            try:
                return float(str(x).replace(",", "").replace("%", "").strip())
            except Exception:
                return None

    def add_liq_key(key: str, today_val, prev_val):
        t = _to_float(today_val)
        p = _to_float(prev_val)
        if t is None:
            return
        if p is None:
            market_data[key] = {"today": t, "prev": None, "pct_change": None}
            return
        pct = 0.0 if p == 0 else ((t - p) / p) * 100.0
        market_data[key] = {"today": t, "prev": p, "pct_change": pct}

    add_liq_key("TGA", liq_today.get("TGA"), None if liq_prev is None else liq_prev.get("TGA"))
    add_liq_key("RRP", liq_today.get("RRP"), None if liq_prev is None else liq_prev.get("RRP"))
    add_liq_key("NET_LIQ", liq_today.get("NET_LIQ"), None if liq_prev is None else liq_prev.get("NET_LIQ"))

    # -------------------------
    # ✅ NET_LIQ dir + level bucket
    # -------------------------
    net = market_data.get("NET_LIQ") or {"today": None, "prev": None, "pct_change": None}
    net_today = _to_float(net.get("today"))
    net_prev = _to_float(net.get("prev"))

    # dir
    if net_today is None or net_prev is None:
        net_dir = "N/A"
    else:
        if net_today > net_prev:
            net_dir = "UP"
        elif net_today < net_prev:
            net_dir = "DOWN"
        else:
            net_dir = "FLAT"

    # level bucket (HIGH/MID/LOW) — never N/A if net_today exists
    level_bucket = "N/A"
    if net_today is not None and "NET_LIQ" in liq_df.columns:
        series = pd.to_numeric(liq_df["NET_LIQ"], errors="coerce").dropna()

        # if we have enough samples -> percentile bucket
        if len(series) >= 20:
            # percentile rank of latest value within history
            pct_rank = (series <= net_today).mean()  # 0~1
        else:
            # small sample fallback -> min/max position bucket
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

    # store back into NET_LIQ dict (Narrative에서 바로 쓰기 좋게)
    net["dir"] = net_dir
    net["level_bucket"] = level_bucket
    market_data["NET_LIQ"] = net

    # optional: also store top-level convenience keys
    market_data["NET_LIQ_DIR"] = net_dir
    market_data["NET_LIQ_LEVEL_BUCKET"] = level_bucket

    return market_data
    

def attach_credit_spread_layer(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach HY_OAS (FRED last available) into market_data.
    Adds:
      - HY_OAS = {today, prev, pct_change}
      - _HY_ASOF = 'YYYY-MM-DD'
    """
    if market_data is None:
        market_data = {}

    df = load_credit_spread_df()
    if df.empty:
        market_data["_HY_ASOF"] = None
        return market_data

    today_row = df.iloc[-1]
    asof = pd.to_datetime(today_row["date"]).strftime("%Y-%m-%d")
    market_data["_HY_ASOF"] = asof

    prev_row = df.iloc[-2] if len(df) >= 2 else None
    today_val = pd.to_numeric(today_row.get("HY_OAS"), errors="coerce")
    if pd.isna(today_val):
        return market_data

    today_val_f = float(today_val)

    if prev_row is None:
        market_data["HY_OAS"] = {"today": today_val_f, "prev": None, "pct_change": None}
        return market_data

    prev_val = pd.to_numeric(prev_row.get("HY_OAS"), errors="coerce")
    if pd.isna(prev_val):
        market_data["HY_OAS"] = {"today": today_val_f, "prev": None, "pct_change": None}
        return market_data

    prev_val_f = float(prev_val)
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


# -------------------------
# Report
# -------------------------
def generate_daily_report() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_macro_df()
    today_idx = len(df) - 1
    as_of_date = pd.to_datetime(df.iloc[today_idx]["date"]).strftime("%Y-%m-%d")

    market_data = build_market_data(df, today_idx)
   
    # -------------------------
    # Attach layers
    # -------------------------
    market_data = attach_liquidity_layer(market_data) or market_data
    market_data = attach_credit_spread_layer(market_data) or market_data
    market_data = attach_fred_extras_layer(market_data) or market_data
    market_data = attach_expectation_layer(market_data) or market_data
    market_data = attach_geopolitical_ew_layer(market_data, df, today_idx) or market_data

    # ✅ Wall-Street Sentiment Proxy only (NO CNN, NO overwrite after this)
    market_data = attach_sentiment_proxy_layer(market_data) or market_data

    # ✅ regime change monitor (always computed)
    regime_result = check_regime_change_and_alert(market_data, as_of_date)

    # -------------------------
    # 1) Run Strategist Commentary FIRST to build FINAL_STATE (Narrative Engine sets it)
    # -------------------------
    commentary_block = build_strategist_commentary(market_data)

    # 2) Top layers (need FINAL_STATE)
    exec_block = executive_summary_filter(market_data)
    decision_block = decision_layer_filter(market_data)
    scenario_block = scenario_generator_filter(market_data)
    transmission_block = transmission_layer_filter(market_data)

    # -------------------------
    # Report assembly
    # -------------------------
    lines = []
    lines.append("# 🌍 Global Capital Flow – Daily Brief")
    lines.append(f"**Date:** {as_of_date}")
    lines.append("")
    lines.append("## 📊 Daily Macro Signals")
    lines.append("")

    # daily core signals
    if "US10Y" in market_data and market_data["US10Y"].get("today") is not None:
        lines.append(
            f"- **미국 10년물 금리**: {market_data['US10Y']['today']:.3f}  "
            f"({market_data['US10Y']['pct_change']:+.2f}% vs {market_data['US10Y']['prev']:.3f})"
        )
    if "DXY" in market_data and market_data["DXY"].get("today") is not None:
        lines.append(
            f"- **달러 인덱스**: {market_data['DXY']['today']:.3f}  "
            f"({market_data['DXY']['pct_change']:+.2f}% vs {market_data['DXY']['prev']:.3f})"
        )
    if "WTI" in market_data and market_data["WTI"].get("today") is not None:
        lines.append(
            f"- **WTI 유가**: {market_data['WTI']['today']:.3f}  "
            f"({market_data['WTI']['pct_change']:+.2f}% vs {market_data['WTI']['prev']:.3f})"
        )
    if "VIX" in market_data and market_data["VIX"].get("today") is not None:
        lines.append(
            f"- **변동성 지수 (VIX)**: {market_data['VIX']['today']:.3f}  "
            f"({market_data['VIX']['pct_change']:+.2f}% vs {market_data['VIX']['prev']:.3f})"
        )
    if "USDKRW" in market_data and market_data["USDKRW"].get("today") is not None:
        lines.append(
            f"- **원/달러 환율**: {market_data['USDKRW']['today']:.3f}  "
            f"({market_data['USDKRW']['pct_change']:+.2f}% vs {market_data['USDKRW']['prev']:.3f})"
        )

    # Optional: Liquidity Snapshot block (independent)
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

    # ✅ Regime Change Monitor (ALWAYS ON) — moved OUT of SHOW_LIQUIDITY_SNAPSHOT
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🚨 Regime Change Monitor (always-on)")

    if regime_result["status"] == "DETECTED":
        lines.append(f"- **Status:** ✅ DETECTED")
        lines.append(f"- **Prev → Current:** {regime_result['prev_regime']} → {regime_result['current_regime']}")
        lines.append(f"- **File:** `insights/risk_alerts.txt` ✅ created")
        lines.append(f"- **Email:** {'✅ sent' if regime_result['email_sent'] else '❌ not sent'} ({regime_result['email_note']})")
    elif regime_result["status"] == "NOT_DETECTED":
        lines.append(f"- **Status:** ❎ NOT DETECTED")
        lines.append(f"- **Current Regime:** {regime_result['current_regime']}")
        lines.append(f"- **File:** not created")
        lines.append(f"- **Email:** not sent")
    else:
        lines.append(f"- **Status:** ⚪ BASELINE SET (first run)")
        lines.append(f"- **Current Regime:** {regime_result['current_regime']}")
        lines.append(f"- **File/Email:** not created (no previous regime to compare)")

    # -------------------------
    # Top layers first
    # -------------------------
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

    # Detailed commentary last
    lines.append(commentary_block)

    report_path = REPORTS_DIR / f"daily_report_{as_of_date}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Report written: {report_path}")
   
     



if __name__ == "__main__":
    generate_daily_report()
