from __future__ import annotations

"""
FILTER15 STAGED RESTORATION PARAMETER SENSITIVITY AUDIT

연구 질문
---------
현재 RAMP_3의 25% -> 50% -> 100% 경로가 특정 숫자에만 의존하는가,
아니면 주변의 단순한 staged restoration 경로에서도 같은 방향의
tail-risk 개선이 유지되는가?

중요
----
- Production 수정 금지
- 새로운 indicator 없음
- 새로운 release threshold 없음
- 미래 데이터 backfill 없음
- SIGNAL t -> RETURN t+1
- 최고 수익률 parameter를 고르는 최적화가 아님
- 기존 release candidate: HY_FALLING_VIX_LT_30
- candidate가 깨지면 0%로 re-brake
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "data" / "backtest" / "results"

EPISODE_PATH = RESULT_DIR / "filter15_release_failure_analysis.csv"
MASTER_PATH = ROOT / "data" / "backtest" / "master_panel.csv"

OUT_EPISODES = RESULT_DIR / "filter15_staged_restoration_parameter_sensitivity_episodes.csv"
OUT_SUMMARY = RESULT_DIR / "filter15_staged_restoration_parameter_sensitivity_summary.csv"
OUT_TXT = RESULT_DIR / "filter15_staged_restoration_parameter_sensitivity_audit.txt"

# 현재 25/50/100을 중심으로 주변의 단순한 경로만 검증.
# 이것은 "최고 숫자 찾기"가 아니라 구조적 안정성 확인용이다.
PATHS = {
    "STATIC_FULL": (1.00, 1.00, 1.00),
    "RAMP_3_20_50_100": (0.20, 0.50, 1.00),
    "RAMP_3_25_50_100": (0.25, 0.50, 1.00),
    "RAMP_3_30_60_100": (0.30, 0.60, 1.00),
    "RAMP_3_40_70_100": (0.40, 0.70, 1.00),
}

def n(x):
    return pd.to_numeric(x, errors="coerce")

def load_inputs():
    if not EPISODE_PATH.exists():
        raise FileNotFoundError(f"Missing: {EPISODE_PATH}")
    if not MASTER_PATH.exists():
        raise FileNotFoundError(f"Missing: {MASTER_PATH}")

    ep = pd.read_csv(EPISODE_PATH)
    mp = pd.read_csv(MASTER_PATH)

    ep_required = [
        "episode_id", "release_date", "production_end_signal_date",
        "release_full_exposure", "diagnosis",
    ]
    missing = [c for c in ep_required if c not in ep.columns]
    if missing:
        raise ValueError(f"Release artifact missing columns: {missing}")

    mp_required = ["signal_date", "VIX", "credit__HY_OAS"]
    missing = [c for c in mp_required if c not in mp.columns]
    if missing:
        raise ValueError(f"master_panel missing columns: {missing}")

    ep["release_date"] = pd.to_datetime(ep["release_date"], errors="coerce")
    ep["production_end_signal_date"] = pd.to_datetime(
        ep["production_end_signal_date"], errors="coerce"
    )
    ep["release_full_exposure"] = n(ep["release_full_exposure"])

    mp["signal_date"] = pd.to_datetime(mp["signal_date"], errors="coerce")
    mp["VIX"] = n(mp["VIX"])
    mp["credit__HY_OAS"] = n(mp["credit__HY_OAS"])

    # SPY 가격 컬럼을 안전하게 찾는다.
    spy_candidates = [
        "SPY", "spy", "SPY_Close", "spy_close",
        "SP500", "^GSPC", "SPX",
    ]
    spy_col = next((c for c in spy_candidates if c in mp.columns), None)

    if spy_col is None:
        # 이름에 SPY가 들어간 실제 숫자 컬럼을 마지막 후보로 탐색
        candidates = [
            c for c in mp.columns
            if "SPY" in c.upper()
            and pd.api.types.is_numeric_dtype(mp[c])
        ]
        if candidates:
            spy_col = candidates[0]

    if spy_col is None:
        raise ValueError(
            "master_panel에서 SPY 가격 컬럼을 찾지 못했습니다.\n"
            "잘못된 다른 자산으로 대체하지 않고 중단합니다."
        )

    mp[spy_col] = n(mp[spy_col])
    mp = mp.sort_values("signal_date").drop_duplicates("signal_date", keep="last")

    # signal t의 exposure는 다음 거래일 return에 적용.
    mp["spy_next_return"] = mp[spy_col].pct_change().shift(-1)

    return ep, mp, spy_col

def release_candidate(df):
    """
    기존 연구 candidate:
      HY_FALLING_VIX_LT_30

    HY OAS가 전 signal date보다 하락하고 VIX < 30.
    모든 판단은 해당 signal date에서 관측 가능한 값만 사용.
    """
    hy = df["credit__HY_OAS"]
    vix = df["VIX"]

    hy_falling = hy < hy.shift(1)
    vix_ok = vix < 30.0

    return (
        hy.notna()
        & hy.shift(1).notna()
        & vix.notna()
        & hy_falling
        & vix_ok
    )

def simulate_episode(ep_row, mp, path_name, stages):
    release_date = ep_row["release_date"]
    production_end = ep_row["production_end_signal_date"]
    full_exposure = float(ep_row["release_full_exposure"])

    if pd.isna(release_date) or pd.isna(production_end):
        return None

    if not np.isfinite(full_exposure):
        return None

    if full_exposure < 0 or full_exposure > 100:
        raise ValueError(
            f"Episode {ep_row['episode_id']}: invalid release_full_exposure={full_exposure}"
        )

    # Counterfactual window:
    # candidate release일부터 production deadman 종료일까지.
    w = mp[
        (mp["signal_date"] >= release_date)
        & (mp["signal_date"] <= production_end)
    ].copy()

    if w.empty:
        return None

    w["candidate"] = release_candidate(mp).reindex(w.index).fillna(False)

    stage_idx = 0
    exposures = []
    rebrake_days = 0
    invested_days = 0
    full_days = 0

    for _, row in w.iterrows():
        cand = bool(row["candidate"])

        if path_name == "STATIC_FULL":
            # release 이후 production 종료까지 full exposure.
            mult = 1.0
        else:
            if not cand:
                # recovery condition이 깨지면 즉시 0%로 re-brake.
                stage_idx = 0
                mult = 0.0
                rebrake_days += 1
            else:
                mult = stages[min(stage_idx, len(stages) - 1)]
                if stage_idx < len(stages) - 1:
                    stage_idx += 1

        exposure = full_exposure * mult
        exposures.append(exposure)

        if exposure > 0:
            invested_days += 1
        if np.isclose(mult, 1.0):
            full_days += 1

    w["cf_exposure"] = exposures

    # production baseline은 deadman 때문에 이 window에서 0%라는
    # 기존 release-failure research contract를 유지한다.
    w["cf_return"] = (
        w["cf_exposure"] / 100.0
    ) * w["spy_next_return"].fillna(0.0)

    equity = (1.0 + w["cf_return"]).cumprod()
    peak = equity.cummax()
    dd = equity / peak - 1.0

    total_return = float(equity.iloc[-1] - 1.0)
    mdd = float(dd.min()) if len(dd) else 0.0

    return {
        "episode_id": ep_row["episode_id"],
        "release_date": release_date,
        "production_end_signal_date": production_end,
        "diagnosis": ep_row["diagnosis"],
        "candidate_exposure": full_exposure,
        "path": path_name,
        "stage_1": stages[0],
        "stage_2": stages[1],
        "stage_3": stages[2],
        "total_return": total_return,
        "mdd": mdd,
        "avg_exposure": float(np.mean(exposures)) if exposures else 0.0,
        "invested_days": invested_days,
        "full_days": full_days,
        "rebrake_days": rebrake_days,
        "rows": len(w),
    }

def summarize(results):
    rows = []

    for path, g in results.groupby("path", sort=False):
        returns = g["total_return"]
        mdds = g["mdd"]

        rows.append({
            "path": path,
            "stage_1": g["stage_1"].iloc[0],
            "stage_2": g["stage_2"].iloc[0],
            "stage_3": g["stage_3"].iloc[0],
            "episodes": len(g),
            "positive_episodes": int((returns > 0).sum()),
            "negative_episodes": int((returns < 0).sum()),
            "total_episode_return": float(returns.sum()),
            "avg_episode_return": float(returns.mean()),
            "median_episode_return": float(returns.median()),
            "avg_mdd": float(mdds.mean()),
            "worst_mdd": float(mdds.min()),
            "avg_exposure": float(g["avg_exposure"].mean()),
            "avg_rebrake_days": float(g["rebrake_days"].mean()),
        })

    out = pd.DataFrame(rows)

    base = out[out["path"] == "STATIC_FULL"].iloc[0]

    out["return_delta_vs_static"] = (
        out["total_episode_return"] - base["total_episode_return"]
    )
    out["worst_mdd_improvement_vs_static"] = (
        out["worst_mdd"] - base["worst_mdd"]
    )

    return out

def excluding_2008(results):
    x = results[pd.to_datetime(results["release_date"]).dt.year != 2008].copy()
    return summarize(x)

def leave_one_out(results):
    ids = sorted(results["episode_id"].dropna().unique())
    rows = []

    for removed_id in ids:
        x = results[results["episode_id"] != removed_id].copy()
        s = summarize(x)

        static = s[s["path"] == "STATIC_FULL"].iloc[0]

        for _, r in s[s["path"] != "STATIC_FULL"].iterrows():
            rows.append({
                "removed_episode_id": removed_id,
                "path": r["path"],
                "return_better_than_static":
                    r["total_episode_return"] > static["total_episode_return"],
                "worst_mdd_better_than_static":
                    r["worst_mdd"] > static["worst_mdd"],
            })

    return pd.DataFrame(rows)

def main():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    ep, mp, spy_col = load_inputs()

    records = []

    for _, ep_row in ep.iterrows():
        for path_name, stages in PATHS.items():
            r = simulate_episode(
                ep_row=ep_row,
                mp=mp,
                path_name=path_name,
                stages=stages,
            )
            if r is not None:
                records.append(r)

    results = pd.DataFrame(records)

    if results.empty:
        raise RuntimeError("No sensitivity results produced.")

    summary = summarize(results)
    ex08 = excluding_2008(results)
    loo = leave_one_out(results)

    loo_summary = (
        loo.groupby("path", as_index=False)
        .agg(
            loo_return_pass_rate=("return_better_than_static", "mean"),
            loo_mdd_pass_rate=("worst_mdd_better_than_static", "mean"),
        )
    )

    summary = summary.merge(
        loo_summary,
        on="path",
        how="left",
    )

    results.to_csv(OUT_EPISODES, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)

    lines = []
    lines.append("=" * 78)
    lines.append("FILTER15 STAGED RESTORATION PARAMETER SENSITIVITY AUDIT")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"Episodes               : {results['episode_id'].nunique()}")
    lines.append(f"SPY Source Column      : {spy_col}")
    lines.append("Candidate              : HY_FALLING_VIX_LT_30")
    lines.append("Execution              : SIGNAL t -> RETURN t+1")
    lines.append("Re-brake               : candidate breaks -> 0%")
    lines.append("Production Modified    : NO")
    lines.append("Future Data Backfill   : NO")
    lines.append("New Indicator          : NO")
    lines.append("Threshold Optimization : NO")
    lines.append("")
    lines.append("===== FULL SAMPLE =====")
    lines.append(summary.to_string(index=False))
    lines.append("")
    lines.append("===== EXCLUDING 2008 =====")
    lines.append(ex08.to_string(index=False))
    lines.append("")
    lines.append("===== INTERPRETATION =====")
    lines.append("")
    lines.append(
        "1. 목적은 최고 수익률 parameter를 고르는 것이 아니라 "
        "staged restoration 구조가 주변 parameter에서도 살아남는지 확인하는 것이다."
    )
    lines.append("")
    lines.append(
        "2. 20/50/100, 25/50/100, 30/60/100, 40/70/100 중 "
        "여러 경로가 STATIC_FULL 대비 tail risk를 줄이면 구조적 robustness 근거가 된다."
    )
    lines.append("")
    lines.append(
        "3. 특정 한 경로에서만 결과가 좋으면 parameter overfit 가능성이 있으므로 "
        "Production 후보로 승격하지 않는다."
    )
    lines.append("")
    lines.append(
        "4. 2008 제외 및 Leave-One-Episode-Out에서도 방향이 유지되는지 함께 확인한다."
    )
    lines.append("")
    lines.append("PRODUCTION DECISION: NO CHANGE")
    lines.append("NEXT GATE: SENSITIVITY INTERPRETATION / PRODUCTION-CANDIDATE DECISION")

    text = "\n".join(lines)
    OUT_TXT.write_text(text, encoding="utf-8")

    print()
    print(text)
    print()
    print(f"Saved: {OUT_EPISODES}")
    print(f"Saved: {OUT_SUMMARY}")
    print(f"Saved: {OUT_TXT}")

if __name__ == "__main__":
    main()
