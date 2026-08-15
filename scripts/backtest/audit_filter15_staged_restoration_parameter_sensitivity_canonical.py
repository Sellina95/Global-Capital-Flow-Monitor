from __future__ import annotations

"""
FILTER15 PARAMETER SENSITIVITY — CANONICAL PATH REUSE

중요:
새로운 recovery state machine을 다시 구현하지 않는다.
이미 검증된 filter15_staged_restoration_daily.csv의 RAMP_3 경로를 그대로 사용하고,
그 경로에서 25/50/100 stage의 sizing 숫자만 주변 값으로 치환한다.

따라서:
- release timing 동일
- re-brake timing 동일
- invested days 동일
- state progression 동일
- return alignment 동일
- Production 수정 없음
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "data" / "backtest" / "results"

SRC = R / "filter15_staged_restoration_daily.csv"
OUT_DAILY = R / "filter15_staged_restoration_parameter_sensitivity_canonical_daily.csv"
OUT_EP = R / "filter15_staged_restoration_parameter_sensitivity_canonical_episodes.csv"
OUT_SUM = R / "filter15_staged_restoration_parameter_sensitivity_canonical_summary.csv"
OUT_TXT = R / "filter15_staged_restoration_parameter_sensitivity_canonical_audit.txt"

PATHS = {
    "RAMP_20_50_100": (0.20, 0.50, 1.00),
    "RAMP_25_50_100": (0.25, 0.50, 1.00),  # canonical parity check
    "RAMP_30_60_100": (0.30, 0.60, 1.00),
    "RAMP_40_70_100": (0.40, 0.70, 1.00),
}

TOL = 1e-10


def pick(cols, exact=(), contains=()):
    for c in exact:
        if c in cols:
            return c
    for token in contains:
        hits = [c for c in cols if token.lower() in c.lower()]
        if hits:
            return hits[0]
    return None


def main():
    if not SRC.exists():
        raise FileNotFoundError(f"Missing canonical artifact: {SRC}")

    df = pd.read_csv(SRC)
    cols = list(df.columns)

    # Canonical artifact의 실제 확인된 contract를 명시적으로 고정한다.
    # 자동 추측으로 다른 컬럼을 잘못 읽는 것을 방지한다.
    ep_col = "episode_id"
    path_col = "path"
    date_col = "signal_date"
    ret_col = "spy_return_t1"
    exp_col = "counterfactual_exposure"
    full_col = "candidate_exposure"

    required = {
        "episode_id": ep_col,
        "path": path_col,
        "return": ret_col,
        "canonical exposure": exp_col,
    }
    missing = [k for k, v in required.items() if v is None]
    if missing:
        print("\n===== AVAILABLE COLUMNS =====")
        print(cols)
        raise ValueError(
            "\nCanonical daily artifact에서 필요한 column을 자동 식별하지 못했습니다: "
            + ", ".join(missing)
            + "\n위 AVAILABLE COLUMNS 출력만 보내주세요."
        )

    # 기존 검증 RAMP_3만 사용.
    ramp = df[df[path_col].astype(str).str.upper().eq("RAMP_3")].copy()
    if ramp.empty:
        print("\n===== PATH VALUES =====")
        print(df[path_col].dropna().astype(str).value_counts().to_string())
        raise ValueError("Canonical daily artifact에 RAMP_3 path가 없습니다.")

    ramp[ret_col] = pd.to_numeric(ramp[ret_col], errors="coerce")
    ramp[exp_col] = pd.to_numeric(ramp[exp_col], errors="coerce")

    # full exposure column이 없으면 episode별 canonical exposure의 최대값 사용.
    if full_col is not None:
        ramp[full_col] = pd.to_numeric(ramp[full_col], errors="coerce")
        full = ramp[full_col].copy()
    else:
        full = ramp.groupby(ep_col)[exp_col].transform("max")

    if full.isna().any():
        raise ValueError("Full exposure를 복원할 수 없는 row가 있습니다.")

    ramp["_full"] = full
    ramp["_canonical_mult"] = np.where(
        ramp["_full"].abs() > TOL,
        ramp[exp_col] / ramp["_full"],
        0.0,
    )

    # canonical RAMP_3 stage를 분류.
    # 0 = re-brake, 1 = 25%, 2 = 50%, 3 = 100%
    def stage_of(x):
        if np.isclose(x, 0.0, atol=1e-6):
            return 0
        if np.isclose(x, 0.25, atol=1e-4):
            return 1
        if np.isclose(x, 0.50, atol=1e-4):
            return 2
        if np.isclose(x, 1.00, atol=1e-4):
            return 3
        return -1

    ramp["_stage"] = ramp["_canonical_mult"].map(stage_of)

    bad = ramp[ramp["_stage"] == -1]
    if not bad.empty:
        print("\n===== UNKNOWN CANONICAL MULTIPLIERS =====")
        print(
            bad[[ep_col, exp_col, "_full", "_canonical_mult"]]
            .head(30).to_string(index=False)
        )
        raise ValueError(
            "Canonical RAMP_3에서 0/25/50/100 이외 multiplier가 발견됐습니다. "
            "임의로 해석하지 않고 중단합니다."
        )

    records = []

    for name, stages in PATHS.items():
        x = ramp.copy()

        mapping = {
            0: 0.0,
            1: stages[0],
            2: stages[1],
            3: stages[2],
        }
        x["sensitivity_path"] = name
        x["sensitivity_multiplier"] = x["_stage"].map(mapping)
        x["sensitivity_exposure"] = x["_full"] * x["sensitivity_multiplier"]

        # canonical return alignment을 그대로 사용.
        x["sensitivity_return"] = (
            x["sensitivity_exposure"] / 100.0
        ) * x[ret_col].fillna(0.0)

        records.append(x)

    daily = pd.concat(records, ignore_index=True)

    ep_rows = []
    for (name, eid), g in daily.groupby(["sensitivity_path", ep_col], sort=False):
        eq = (1.0 + g["sensitivity_return"]).cumprod()
        peak = eq.cummax()
        dd = eq / peak - 1.0

        ep_rows.append({
            "path": name,
            "episode_id": eid,
            "release_date": g[date_col].iloc[0] if date_col else np.nan,
            "total_return": float(eq.iloc[-1] - 1.0),
            "mdd": float(dd.min()),
            "avg_exposure": float(g["sensitivity_exposure"].mean()),
            "invested_days": int((g["sensitivity_exposure"] > TOL).sum()),
            "full_days": int(
                np.isclose(
                    g["sensitivity_multiplier"], 1.0, atol=1e-8
                ).sum()
            ),
            "rebrake_days": int(
                np.isclose(
                    g["sensitivity_multiplier"], 0.0, atol=1e-8
                ).sum()
            ),
        })

    episodes = pd.DataFrame(ep_rows)

    sum_rows = []
    for name, g in episodes.groupby("path", sort=False):
        sum_rows.append({
            "path": name,
            "episodes": len(g),
            "positive_episodes": int((g["total_return"] > 0).sum()),
            "negative_episodes": int((g["total_return"] < 0).sum()),
            "total_episode_return": float(g["total_return"].sum()),
            "avg_episode_return": float(g["total_return"].mean()),
            "median_episode_return": float(g["total_return"].median()),
            "avg_mdd": float(g["mdd"].mean()),
            "worst_mdd": float(g["mdd"].min()),
            "avg_exposure": float(g["avg_exposure"].mean()),
        })

    summary = pd.DataFrame(sum_rows)

    # 가장 중요한 audit:
    # 25/50/100 재계산 결과가 canonical RAMP_3와 일치하는지 확인.
    canonical_ep = []
    for eid, g in ramp.groupby(ep_col, sort=False):
        rr = (g[exp_col] / 100.0) * g[ret_col].fillna(0.0)
        eq = (1.0 + rr).cumprod()
        peak = eq.cummax()
        dd = eq / peak - 1.0
        canonical_ep.append({
            "episode_id": eid,
            "canonical_return": float(eq.iloc[-1] - 1.0),
            "canonical_mdd": float(dd.min()),
        })

    canonical_ep = pd.DataFrame(canonical_ep)

    check = episodes[
        episodes["path"] == "RAMP_25_50_100"
    ][["episode_id", "total_return", "mdd"]].merge(
        canonical_ep, on="episode_id", how="outer"
    )

    check["return_error"] = (
        check["total_return"] - check["canonical_return"]
    ).abs()
    check["mdd_error"] = (
        check["mdd"] - check["canonical_mdd"]
    ).abs()

    max_ret_err = float(check["return_error"].max())
    max_mdd_err = float(check["mdd_error"].max())

    parity_pass = (
        max_ret_err <= 1e-12
        and max_mdd_err <= 1e-12
        and len(check) == ramp[ep_col].nunique()
    )

    daily.to_csv(OUT_DAILY, index=False)
    episodes.to_csv(OUT_EP, index=False)
    summary.to_csv(OUT_SUM, index=False)

    lines = [
        "=" * 78,
        "FILTER15 CANONICAL PARAMETER SENSITIVITY AUDIT",
        "=" * 78,
        "",
        f"Canonical Source        : {SRC.name}",
        "Canonical State Path    : RAMP_3",
        "Production Modified     : NO",
        "New Indicator           : NO",
        "New Threshold           : NO",
        "State Machine Rewritten : NO",
        "",
        "===== CANONICAL PARITY CHECK =====",
        f"25/50/100 Return Max Error : {max_ret_err}",
        f"25/50/100 MDD Max Error    : {max_mdd_err}",
        f"PARITY                    : {'PASS' if parity_pass else 'FAIL'}",
        "",
        "===== SENSITIVITY SUMMARY =====",
        summary.to_string(index=False),
        "",
    ]

    if parity_pass:
        lines += [
            "RESULT: CANONICAL SENSITIVITY VALID",
            "",
            "해석:",
            "25/50/100의 기존 검증 경로를 정확히 재현한 상태에서",
            "20/50/100, 30/60/100, 40/70/100의 sizing만 비교한다.",
            "여러 인접 parameter에서 방향이 유지되면 staged restoration 구조의",
            "robustness 근거가 강화된다.",
            "",
            "PRODUCTION DECISION: NO CHANGE",
            "NEXT GATE: FINAL FILTER15 RELEASE-LOGIC DECISION",
        ]
    else:
        lines += [
            "RESULT: FAIL — DO NOT INTERPRET SENSITIVITY",
            "",
            "25/50/100이 canonical RAMP_3를 재현하지 못했다.",
            "이 경우 sensitivity 숫자를 사용하지 않는다.",
            "",
            "PRODUCTION DECISION: HOLD",
        ]

    text = "\n".join(lines)
    OUT_TXT.write_text(text, encoding="utf-8")

    print("\n" + text)
    print(f"\nSaved: {OUT_DAILY}")
    print(f"Saved: {OUT_EP}")
    print(f"Saved: {OUT_SUM}")
    print(f"Saved: {OUT_TXT}")


if __name__ == "__main__":
    main()
