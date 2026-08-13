import json
import os
from datetime import datetime
from typing import Any, Dict

import pandas as pd


def apply_slippage_to_trades(
    trade_df: pd.DataFrame,
    market_data: dict,
) -> pd.DataFrame:
    """
    Trade Log에 슬리피지 반영
    """
    vix_node = market_data.get("VIX", 20)

    if isinstance(vix_node, dict):
        vix = float(vix_node.get("today", 20) or 20)
    else:
        vix = float(vix_node or 20)

    def calc_slippage(row):
        slip = 0.1  # base 0.1%

        # 🔥 VIX 기반 (시장 발작)
        if vix > 30:
            slip += 0.4
        elif vix > 25:
            slip += 0.3
        elif vix > 20:
            slip += 0.1

        # 🔥 유동성 낮은 ETF
        low_liq = ["XLU", "XLRE"]
        if row["etf"] in low_liq:
            slip += 0.2

        # 🔥 거래 규모
        if abs(row["trade_weight"]) > 5:
            slip += 0.2

        return round(slip, 2)

    if trade_df.empty:
        trade_df["slippage_pct"] = []
        return trade_df

    trade_df["slippage_pct"] = trade_df.apply(calc_slippage, axis=1)

    return trade_df


def apply_transaction_cost(trade_df: pd.DataFrame) -> pd.DataFrame:
    """
    거래 수수료 + 세금 반영
    """

    def calc_cost(row):
        cost = 0.05  # 기본 0.05%

        if row["action"] == "SELL":
            cost += 0.1  # 매도 세금

        return round(cost, 2)

    if trade_df.empty:
        trade_df["transaction_cost_pct"] = []
        return trade_df

    trade_df["transaction_cost_pct"] = trade_df.apply(calc_cost, axis=1)

    return trade_df


def save_trade_log(
    prev_weights: dict,
    target_weights: dict,
    market_data: dict,
    filepath: str = "data/trade_log.csv",
):
    """
    이전 ETF 비중 vs 현재 목표 비중 비교해서 BUY/SELL/HOLD 로그 생성
    + slippage / transaction cost / total cost 반영

    핵심:
    - 거래가 없어도(HOLD only / Dead Man) 날짜 row는 반드시 저장
    """

    today = pd.Timestamp.now(tz="Asia/Seoul").strftime("%Y-%m-%d")
    rows = []

    all_etfs = sorted(set(prev_weights.keys()) | set(target_weights.keys()))

    # 🔥 ETF 자체가 하나도 없으면 CASH ONLY DAY라도 최소 snapshot row 생성
    if not all_etfs:
        rows.append(
            {
                "date": today,
                "etf": "CASH",
                "prev_weight": 100.0,
                "target_weight": 100.0,
                "trade_weight": 0.0,
                "action": "HOLD",
            }
        )

    else:
        for etf in all_etfs:
            prev_w = float(prev_weights.get(etf, 0.0) or 0.0)
            target_w = float(target_weights.get(etf, 0.0) or 0.0)
            diff_w = round(target_w - prev_w, 2)

            if diff_w > 0:
                action = "BUY"
            elif diff_w < 0:
                action = "SELL"
            else:
                action = "HOLD"

            rows.append(
                {
                    "date": today,
                    "etf": etf,
                    "prev_weight": round(prev_w, 2),
                    "target_weight": round(target_w, 2),
                    "trade_weight": diff_w,
                    "action": action,
                }
            )

    # 오늘 거래 로그 생성
    df_today = pd.DataFrame(rows)

    # 비용 계산 적용
    df_today = apply_slippage_to_trades(df_today, market_data)
    df_today = apply_transaction_cost(df_today)

    print("🔥 DEBUG COLUMNS:", df_today.columns)

    df_today["total_cost_pct"] = (
        df_today["slippage_pct"] + df_today["transaction_cost_pct"]
    ).round(2)

    df_today["trade_cost_impact_pct"] = (
        df_today["trade_weight"].abs() * df_today["total_cost_pct"] / 100
    ).round(4)

    # 🔥 총 거래 비용 계산
    total_cost_impact = df_today["trade_cost_impact_pct"].sum().round(4)

    print(f"💸 Total Trade Cost Impact: {total_cost_impact}%")

    MIN_ALPHA_THRESHOLD = 0.15

    if total_cost_impact > MIN_ALPHA_THRESHOLD:
        print("🚫 SKIP TRADE: 비용이 기대수익보다 클 가능성")
    else:
        print("✅ EXECUTE TRADE: 비용 감수 가능")

    # 기존 파일 있으면 오늘 row 제거 후 병합
    if os.path.exists(filepath):
        try:
            old_df = pd.read_csv(filepath)

            if not old_df.empty and "date" in old_df.columns:
                old_df["date"] = old_df["date"].astype(str)
                old_df = old_df[old_df["date"] != today].copy()

            df = pd.concat([old_df, df_today], ignore_index=True)

        except Exception:
            df = df_today
    else:
        df = df_today

    os.makedirs("data", exist_ok=True)
    df.to_csv(filepath, index=False)

    print(f"✅ Trade log saved/updated: {today}")
    print(f"✅ File path: {filepath}")


def load_previous_exposure(filepath: str = "data/paper_portfolio_log.csv") -> float:
    """
    paper_portfolio_log.csv에서 가장 최근 저장된 total_exposure를 읽는다.
    - 오늘 row는 제외
    - 없으면 50.0 반환
    """
    
    today = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(filepath):
        return 50.0

    try:
        df = pd.read_csv(filepath)
    except Exception:
        return 50.0

    if df.empty or "date" not in df.columns or "total_exposure" not in df.columns:
        return 50.0

    df["date"] = df["date"].astype(str)
    df = df[df["date"] != today].copy()

    if df.empty:
        return 50.0

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    if df.empty:
        return 50.0

    val = df.iloc[-1].get("total_exposure")

    try:
        return float(val)
    except Exception:
        return 50.0


def load_previous_weights(filepath: str = "data/paper_portfolio_log.csv") -> dict:
    """
    오늘 row를 제외하고 직전 ETF weights를 가져온다.
    """
    today = pd.Timestamp.now(tz="Asia/Seoul").strftime("%Y-%m-%d")

    if not os.path.exists(filepath):
        return {}

    try:
        df = pd.read_csv(filepath)
    except Exception:
        return {}

    if df.empty or "date" not in df.columns:
        return {}

    df["date"] = df["date"].astype(str)
    df = df[df["date"] != today].copy()

    if df.empty:
        return {}

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")

    if df.empty:
        return {}

    last = df.iloc[-1].to_dict()

    ignore_cols = {"date", "CASH", "total_exposure"}
    weights = {}

    for k, v in last.items():
        if k in ignore_cols:
            continue
        try:
            if pd.notna(v) and float(v) > 0:
                weights[k] = float(v)
        except Exception:
            continue

    return weights

# ============================================================
# Filter18 Rank Persistence State
# ============================================================

FILTER18_RANK_STATE_PATH = "data/filter18_rank_state.json"
FILTER18_RANK_STATE_VERSION = 1


def _default_filter18_rank_state() -> Dict[str, Any]:
    """
    Filter18 Rank Persistence의 안전한 초기 상태.

    원칙:
    - Production portfolio state와 분리
    - state 파일이 없거나 손상되어도 기존 Filter18 실행을 막지 않음
    - 첫 정상 실행에서 현재 rank를 INITIAL_ACCEPT 할 수 있도록 빈 상태 반환
    """
    return {
        "version": FILTER18_RANK_STATE_VERSION,
        "accepted_rank": "",
        "accepted_target_weights": {},
        "pending_rank": "",
        "pending_count": 0,
        "last_processed_date": "",
        "last_output_target_weights": {},
        "last_action": "UNINITIALIZED",
    }


def load_filter18_rank_state(
    filepath: str = FILTER18_RANK_STATE_PATH,
) -> Dict[str, Any]:
    """
    Filter18 Rank Persistence state를 읽는다.

    Fail-safe:
    - 파일 없음
    - JSON 손상
    - schema 이상

    위 경우 모두 default state 반환.

    주의:
    이 함수는 portfolio weights를 읽는 함수와 완전히 분리되어 있다.
    """

    default = _default_filter18_rank_state()

    if not os.path.exists(filepath):
        return default

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return default

    if not isinstance(raw, dict):
        return default

    state = dict(default)

    # --------------------------------------------------------
    # Scalar fields
    # --------------------------------------------------------

    state["version"] = raw.get(
        "version",
        FILTER18_RANK_STATE_VERSION,
    )

    state["accepted_rank"] = str(
        raw.get("accepted_rank", "") or ""
    )

    state["pending_rank"] = str(
        raw.get("pending_rank", "") or ""
    )

    state["last_processed_date"] = str(
        raw.get("last_processed_date", "") or ""
    )

    state["last_action"] = str(
        raw.get("last_action", "UNINITIALIZED")
        or "UNINITIALIZED"
    )

    try:
        state["pending_count"] = max(
            0,
            int(raw.get("pending_count", 0) or 0),
        )
    except Exception:
        state["pending_count"] = 0

    # --------------------------------------------------------
    # Weight dictionaries
    # --------------------------------------------------------

    for key in [
        "accepted_target_weights",
        "last_output_target_weights",
    ]:

        node = raw.get(key, {})

        if not isinstance(node, dict):
            state[key] = {}
            continue

        clean_weights: Dict[str, float] = {}

        for sector, value in node.items():
            try:
                weight = float(value)
            except (TypeError, ValueError):
                continue

            if pd.isna(weight):
                continue

            clean_weights[str(sector)] = round(
                weight,
                4,
            )

        state[key] = clean_weights

    return state


def save_filter18_rank_state(
    state: Dict[str, Any],
    filepath: str = FILTER18_RANK_STATE_PATH,
) -> None:
    """
    Filter18 Rank Persistence state를 atomic write한다.

    Production 원칙:
    - 임시 파일에 먼저 저장
    - 저장 성공 후 os.replace()
    - 중간 실패 시 기존 정상 state 파일 유지

    호출 시점:
    최종 portfolio/trade state 저장이 성공한 뒤에만 호출해야 한다.
    """

    if not isinstance(state, dict):
        raise TypeError(
            "Filter18 rank state must be a dictionary."
        )

    directory = os.path.dirname(filepath)

    if directory:
        os.makedirs(
            directory,
            exist_ok=True,
        )

    clean_state = _default_filter18_rank_state()

    clean_state["version"] = (
        FILTER18_RANK_STATE_VERSION
    )

    clean_state["accepted_rank"] = str(
        state.get("accepted_rank", "") or ""
    )

    clean_state["pending_rank"] = str(
        state.get("pending_rank", "") or ""
    )

    clean_state["last_processed_date"] = str(
        state.get("last_processed_date", "") or ""
    )

    clean_state["last_action"] = str(
        state.get("last_action", "UNKNOWN")
        or "UNKNOWN"
    )

    try:
        clean_state["pending_count"] = max(
            0,
            int(
                state.get(
                    "pending_count",
                    0,
                )
                or 0
            ),
        )
    except Exception:
        clean_state["pending_count"] = 0

    for key in [
        "accepted_target_weights",
        "last_output_target_weights",
    ]:

        source = state.get(
            key,
            {},
        )

        if not isinstance(source, dict):
            source = {}

        clean_weights: Dict[str, float] = {}

        for sector, value in source.items():

            try:
                weight = float(value)
            except (TypeError, ValueError):
                continue

            if pd.isna(weight):
                continue

            clean_weights[str(sector)] = round(
                weight,
                4,
            )

        clean_state[key] = clean_weights

    tmp_path = f"{filepath}.tmp"

    try:
        with open(
            tmp_path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                clean_state,
                f,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )

            f.flush()
            os.fsync(
                f.fileno()
            )

        os.replace(
            tmp_path,
            filepath,
        )

    finally:

        if os.path.exists(tmp_path):

            try:
                os.remove(
                    tmp_path
                )
            except Exception:
                pass


def clear_filter18_rank_state(
    filepath: str = FILTER18_RANK_STATE_PATH,
) -> None:
    """
    운영상 rollback / reset 용도.

    Production 로직에서는 자동 호출하지 않는다.
    명시적인 운영 판단이 있을 때만 사용.
    """

    if os.path.exists(filepath):
        os.remove(filepath)


def save_paper_portfolio(
    weights: Dict[str, float],
    cash_weight: float,
    exposure: float,
) -> None:
    """
    페이퍼 포트폴리오를 CSV에 저장한다.

    핵심:
    - 같은 날짜 overwrite
    - Dead Man / No ETF day라도 반드시 row 생성
    - weights 비어도 CASH row 강제 저장
    """

    filepath = "data/paper_portfolio_log.csv"

    today = pd.Timestamp.now(tz="Asia/Seoul").strftime("%Y-%m-%d")

    # 🔥 방어: weights 없으면 완전 현금 상태로 강제
    if not weights:
        weights = {}
        cash_weight = 100.0
        exposure = 0.0

    # 🔥 방어: exposure 0인데 cash 누락 방지
    if exposure <= 0 and cash_weight <= 0:
        cash_weight = 100.0

    # 1) 기존 파일 로드
    if os.path.exists(filepath):
        try:
            df = pd.read_csv(filepath)
        except Exception:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    # 2) 같은 날짜 기존 row 제거
    if not df.empty and "date" in df.columns:
        df["date"] = df["date"].astype(str)
        df = df[df["date"] != today].copy()

    # 3) 새 row 생성
    new_row = {"date": today}

    for ticker, weight in weights.items():
        try:
            w = round(float(weight), 2)
            if w > 0:
                new_row[ticker] = w
        except Exception:
            continue

    new_row["CASH"] = round(float(cash_weight), 2)
    new_row["total_exposure"] = round(float(exposure), 2)

    # 🔥 최소 안전장치
    if (
        len([k for k in new_row.keys() if k not in ["date", "CASH", "total_exposure"]])
        == 0
    ):
        new_row["CASH"] = 100.0
        new_row["total_exposure"] = 0.0

    # 4) append
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # 5) 컬럼 정리
    fixed_cols = ["date"]
    tail_cols = ["CASH", "total_exposure"]

    dynamic_cols = [c for c in df.columns if c not in fixed_cols + tail_cols]
    dynamic_cols = sorted(dynamic_cols)

    ordered_cols = fixed_cols + dynamic_cols + tail_cols
    df = df.reindex(columns=ordered_cols)

    # 6) 날짜 정렬
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date").reset_index(drop=True)
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # 7) 저장
    os.makedirs("data", exist_ok=True)
    df.to_csv(filepath, index=False)

    print(f"✅ Portfolio saved/updated: {today}")
    print(f"✅ File path: {filepath}")


if __name__ == "__main__":
    test_weights = {
        "XLK": 22.4,
        "XLI": 22.4,
        "XLY": 14.9,
        "XLF": 5.2,
    }

    save_paper_portfolio(
        weights=test_weights,
        cash_weight=35.0,
        exposure=65.0,
    )
