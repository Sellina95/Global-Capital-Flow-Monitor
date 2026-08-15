from __future__ import annotations

"""
FILTER15 CRISIS PATH / HISTORY AUDIT

목적
----
현재 snapshot만으로 구분되지 않았던
2008 false stabilization과 successful recovery의
"release 이전 경로(path/history)"를 비교한다.

검증 대상
---------
1. Deadman 지속 기간
2. HY/VIX 최근 peak
3. 최근 peak 대비 normalization
4. HY/VIX 개선 연속일
5. 5/10/20 거래일 trajectory

원칙
----
- Production 수정 금지
- master_panel의 PIT 데이터 사용
- signal t 정보까지만 사용
- execution = t+1
- 미래 데이터 backfill 금지
- threshold optimization 금지
- 5/10/20은 diagnostic horizon일 뿐 production rule이 아님
"""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "data" / "backtest" / "results"

MASTER_PATH = ROOT / "data" / "backtest" / "master_panel.csv"

EPISODE_PATH = (
    RESULT_DIR / "filter15_crisis_severity_episode.csv"
)

OUT_EPISODE = (
    RESULT_DIR / "filter15_crisis_path_history_episode.csv"
)

OUT_SUMMARY = (
    RESULT_DIR / "filter15_crisis_path_history_summary.csv"
)

OUT_TXT = (
    RESULT_DIR / "filter15_crisis_path_history_audit.txt"
)

HORIZONS = (5, 10, 20)


# ============================================================
# Helpers
# ============================================================

def n(s):
    return pd.to_numeric(s, errors="coerce")


def mean(s):
    x = n(s).dropna()
    return float(x.mean()) if len(x) else np.nan


def median(s):
    x = n(s).dropna()
    return float(x.median()) if len(x) else np.nan


def consecutive_true(s: pd.Series) -> int:
    count = 0

    for x in reversed(
        s.fillna(False).astype(bool).tolist()
    ):
        if not x:
            break
        count += 1

    return count


# ============================================================
# Load PIT master panel
# ============================================================

def load_master() -> pd.DataFrame:

    if not MASTER_PATH.exists():
        raise FileNotFoundError(MASTER_PATH)

    df = pd.read_csv(MASTER_PATH)

    required = [
        "signal_date",
        "execution_date",
        "VIX",
        "credit__HY_OAS",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"master_panel missing columns: {missing}"
        )

    df["signal_date"] = pd.to_datetime(
        df["signal_date"],
        errors="coerce",
    )

    df["execution_date"] = pd.to_datetime(
        df["execution_date"],
        errors="coerce",
    )

    df["VIX"] = n(df["VIX"])
    df["credit__HY_OAS"] = n(
        df["credit__HY_OAS"]
    )

    df = (
        df
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # Point-in-time direction
    # --------------------------------------------------------

    df["hy_change_1d"] = (
        df["credit__HY_OAS"].diff()
    )

    df["vix_change_1d"] = (
        df["VIX"].diff()
    )

    df["hy_improving"] = (
        df["hy_change_1d"] < 0
    )

    df["vix_improving"] = (
        df["vix_change_1d"] < 0
    )

    df["dual_improving"] = (
        df["hy_improving"]
        & df["vix_improving"]
    )

    # --------------------------------------------------------
    # Production hard crisis boundary used ONLY for
    # historical diagnostic state.
    #
    # 새 threshold가 아니다.
    # --------------------------------------------------------

    df["diagnostic_hard_crisis"] = (
        (df["credit__HY_OAS"] >= 6.0)
        | (df["VIX"] >= 30.0)
    )

    # --------------------------------------------------------
    # Historical rolling windows
    #
    # 모든 rolling 값은 현재 signal date까지의 데이터만 사용.
    # --------------------------------------------------------

    for h in HORIZONS:

        hy_roll = (
            df["credit__HY_OAS"]
            .rolling(h, min_periods=1)
        )

        vix_roll = (
            df["VIX"]
            .rolling(h, min_periods=1)
        )

        df[f"hy_peak_{h}"] = hy_roll.max()
        df[f"vix_peak_{h}"] = vix_roll.max()

        df[f"hy_low_{h}"] = hy_roll.min()
        df[f"vix_low_{h}"] = vix_roll.min()

        df[f"hy_norm_abs_{h}"] = (
            df[f"hy_peak_{h}"]
            - df["credit__HY_OAS"]
        )

        df[f"vix_norm_abs_{h}"] = (
            df[f"vix_peak_{h}"]
            - df["VIX"]
        )

        df[f"hy_norm_pct_{h}"] = np.where(
            df[f"hy_peak_{h}"].abs() > 1e-12,
            (
                df[f"hy_peak_{h}"]
                - df["credit__HY_OAS"]
            )
            / df[f"hy_peak_{h}"]
            * 100.0,
            np.nan,
        )

        df[f"vix_norm_pct_{h}"] = np.where(
            df[f"vix_peak_{h}"].abs() > 1e-12,
            (
                df[f"vix_peak_{h}"]
                - df["VIX"]
            )
            / df[f"vix_peak_{h}"]
            * 100.0,
            np.nan,
        )

        # horizon 시작점 -> 현재
        df[f"hy_path_{h}"] = (
            df["credit__HY_OAS"]
            - df["credit__HY_OAS"].shift(h - 1)
        )

        df[f"vix_path_{h}"] = (
            df["VIX"]
            - df["VIX"].shift(h - 1)
        )

    return df


# ============================================================
# Load previously classified release episodes
# ============================================================

def load_episodes() -> pd.DataFrame:

    if not EPISODE_PATH.exists():
        raise FileNotFoundError(
            f"{EPISODE_PATH}\n"
            "먼저 crisis severity audit을 실행하세요."
        )

    df = pd.read_csv(EPISODE_PATH)

    required = [
        "episode_id",
        "release_date",
        "diagnosis",
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"episode file missing columns: {missing}"
        )

    df["release_date"] = pd.to_datetime(
        df["release_date"],
        errors="coerce",
    )

    df["diagnosis"] = (
        df["diagnosis"]
        .fillna("UNKNOWN")
        .astype(str)
        .str.upper()
    )

    return df


# ============================================================
# Extract historical state at each release
# ============================================================

def build_episode_panel(
    master: pd.DataFrame,
    episodes: pd.DataFrame,
) -> pd.DataFrame:

    rows = []

    for _, ep in episodes.iterrows():

        release_date = ep["release_date"]

        if pd.isna(release_date):
            continue

        current_rows = master[
            master["signal_date"] == release_date
        ]

        if current_rows.empty:
            raise ValueError(
                f"Release date missing from master_panel: "
                f"{release_date.date()}"
            )

        current = current_rows.iloc[-1]

        history = master[
            master["signal_date"] <= release_date
        ].copy()

        row = ep.to_dict()

        row["history_signal_date"] = (
            current["signal_date"]
        )

        row["history_execution_date"] = (
            current["execution_date"]
        )

        row["history_hy"] = (
            current["credit__HY_OAS"]
        )

        row["history_vix"] = (
            current["VIX"]
        )

        row["hy_change_1d"] = (
            current["hy_change_1d"]
        )

        row["vix_change_1d"] = (
            current["vix_change_1d"]
        )

        # ----------------------------------------------------
        # Improvement persistence
        # ----------------------------------------------------

        row["hy_improving_streak"] = (
            consecutive_true(
                history["hy_improving"]
            )
        )

        row["vix_improving_streak"] = (
            consecutive_true(
                history["vix_improving"]
            )
        )

        row["dual_improving_streak"] = (
            consecutive_true(
                history["dual_improving"]
            )
        )

        # ----------------------------------------------------
        # Crisis duration immediately preceding release
        # ----------------------------------------------------

        crisis = (
            history["diagnostic_hard_crisis"]
            .fillna(False)
            .astype(bool)
            .tolist()
        )

        idx = len(crisis) - 1

        # release 당일 crisis가 해제된 경우
        # 직전 crisis run을 찾는다.
        while idx >= 0 and not crisis[idx]:
            idx -= 1

        crisis_run = 0

        while idx >= 0 and crisis[idx]:
            crisis_run += 1
            idx -= 1

        row["preceding_crisis_run"] = (
            crisis_run
        )

        # ----------------------------------------------------
        # Rolling path features
        # ----------------------------------------------------

        for h in HORIZONS:

            fields = [
                f"hy_peak_{h}",
                f"vix_peak_{h}",
                f"hy_low_{h}",
                f"vix_low_{h}",
                f"hy_norm_abs_{h}",
                f"vix_norm_abs_{h}",
                f"hy_norm_pct_{h}",
                f"vix_norm_pct_{h}",
                f"hy_path_{h}",
                f"vix_path_{h}",
            ]

            for field in fields:
                row[field] = current[field]

        rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# Group summary
# ============================================================

def build_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:

    features = [
        "history_hy",
        "history_vix",
        "hy_change_1d",
        "vix_change_1d",
        "preceding_crisis_run",
        "hy_improving_streak",
        "vix_improving_streak",
        "dual_improving_streak",
    ]

    for h in HORIZONS:
        features += [
            f"hy_peak_{h}",
            f"vix_peak_{h}",
            f"hy_norm_abs_{h}",
            f"vix_norm_abs_{h}",
            f"hy_norm_pct_{h}",
            f"vix_norm_pct_{h}",
            f"hy_path_{h}",
            f"vix_path_{h}",
        ]

    groups = [
        "TIMING_RISK",
        "SUCCESSFUL_RELEASE",
        "AMBIGUOUS_FAILURE",
    ]

    rows = []

    for feature in features:

        if feature not in df.columns:
            continue

        row = {
            "feature": feature
        }

        for group_name in groups:

            g = df[
                df["diagnosis"] == group_name
            ]

            row[
                f"{group_name}_mean"
            ] = mean(g[feature])

            row[
                f"{group_name}_median"
            ] = median(g[feature])

        timing = row.get(
            "TIMING_RISK_mean",
            np.nan,
        )

        success = row.get(
            "SUCCESSFUL_RELEASE_mean",
            np.nan,
        )

        if (
            pd.notna(timing)
            and pd.notna(success)
        ):
            row["timing_minus_success"] = (
                timing - success
            )
        else:
            row["timing_minus_success"] = (
                np.nan
            )

        rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# Main
# ============================================================

def main():

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    master = load_master()
    episodes = load_episodes()

    result = build_episode_panel(
        master,
        episodes,
    )

    summary = build_summary(
        result
    )

    result.to_csv(
        OUT_EPISODE,
        index=False,
    )

    summary.to_csv(
        OUT_SUMMARY,
        index=False,
    )

    timing = result[
        result["diagnosis"]
        == "TIMING_RISK"
    ]

    success = result[
        result["diagnosis"]
        == "SUCCESSFUL_RELEASE"
    ]

    ambiguous = result[
        result["diagnosis"]
        == "AMBIGUOUS_FAILURE"
    ]

    ranked = (
        summary
        .dropna(
            subset=["timing_minus_success"]
        )
        .assign(
            abs_difference=lambda x:
            x["timing_minus_success"].abs()
        )
        .sort_values(
            "abs_difference",
            ascending=False,
        )
    )

    # --------------------------------------------------------
    # Compact episode display
    # --------------------------------------------------------

    display = [
        "episode_id",
        "release_date",
        "diagnosis",
        "history_hy",
        "history_vix",
        "preceding_crisis_run",
        "hy_improving_streak",
        "vix_improving_streak",
        "dual_improving_streak",
    ]

    for h in HORIZONS:
        display += [
            f"hy_peak_{h}",
            f"hy_norm_pct_{h}",
            f"vix_peak_{h}",
            f"vix_norm_pct_{h}",
        ]

    display += [
        "full_incremental_return",
        "full_incremental_mdd",
    ]

    display = [
        c for c in display
        if c in result.columns
    ]

    lines = []

    lines.append("=" * 78)
    lines.append(
        "FILTER15 CRISIS PATH / HISTORY AUDIT"
    )
    lines.append("=" * 78)
    lines.append("")

    lines.append(
        f"Episodes            : {len(result)}"
    )
    lines.append(
        f"Successful          : {len(success)}"
    )
    lines.append(
        f"Timing Risk         : {len(timing)}"
    )
    lines.append(
        f"Ambiguous           : {len(ambiguous)}"
    )

    lines.append("")
    lines.append(
        "PIT Source           : data/backtest/master_panel.csv"
    )
    lines.append(
        "Signal Date          : master_panel.signal_date"
    )
    lines.append(
        "Execution Date       : master_panel.execution_date"
    )
    lines.append(
        "HY OAS Source        : master_panel.credit__HY_OAS"
    )
    lines.append(
        "VIX Source           : master_panel.VIX"
    )
    lines.append(
        "Execution Convention : SIGNAL t -> RETURN t+1"
    )
    lines.append(
        "Future Backfill      : NO"
    )
    lines.append(
        "Production Modified  : NO"
    )
    lines.append(
        "Threshold Optimize   : NO"
    )

    lines.append("")
    lines.append(
        "===== TIMING RISK / 2008 PATH ====="
    )

    if timing.empty:
        lines.append("NONE")
    else:
        lines.append(
            timing[display].to_string(
                index=False
            )
        )

    lines.append("")
    lines.append(
        "===== SUCCESSFUL RELEASE PATHS ====="
    )

    if success.empty:
        lines.append("NONE")
    else:
        lines.append(
            success[display].to_string(
                index=False
            )
        )

    lines.append("")
    lines.append(
        "===== LARGEST PATH DIFFERENCES ====="
    )

    ranked_cols = [
        "feature",
        "TIMING_RISK_mean",
        "SUCCESSFUL_RELEASE_mean",
        "SUCCESSFUL_RELEASE_median",
        "AMBIGUOUS_FAILURE_mean",
        "timing_minus_success",
    ]

    lines.append(
        ranked[ranked_cols]
        .head(25)
        .to_string(index=False)
    )

    lines.append("")
    lines.append(
        "===== INTERPRETATION GATE ====="
    )

    lines.append(
        "1. 2008만 분리되는 숫자를 production rule로 채택하지 않는다."
    )
    lines.append(
        "2. Successful recovery 여러 건에서 반복되는 path 특성이 있는지 본다."
    )
    lines.append(
        "3. HY/VIX peak normalization과 improvement persistence를 우선 본다."
    )
    lines.append(
        "4. path/history도 분리력이 약하면 recovery timing 예측보다 "
        "staged re-risking/sizing을 다음 연구 대상으로 이동한다."
    )
    lines.append(
        "5. 본 Audit은 진단용이며 Production 변경을 승인하지 않는다."
    )

    lines.append("")
    lines.append(
        "RESULT: RESEARCH DIAGNOSTIC ONLY"
    )
    lines.append(
        "NEXT GATE: PATH SEPARATION OR STAGED RE-RISKING"
    )

    text = "\n".join(lines)

    OUT_TXT.write_text(
        text,
        encoding="utf-8",
    )

    print()
    print(text)
    print()

    print(f"Saved: {OUT_EPISODE}")
    print(f"Saved: {OUT_SUMMARY}")
    print(f"Saved: {OUT_TXT}")


if __name__ == "__main__":
    main()
