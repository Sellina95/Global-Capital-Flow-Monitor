from __future__ import annotations

"""
FILTER15 STAGED RESTORATION RECONCILIATION AUDIT

목적
----
직전 두 연구 artifact 사이의 숫자 불일치를 episode-by-episode로 추적한다.

비교 대상
1) filter15_staged_restoration_episodes.csv
   - 기존 staged restoration path audit
2) filter15_staged_restoration_parameter_sensitivity_episodes.csv
   - parameter sensitivity audit

핵심 질문
---------
- 동일 episode / 동일 STATIC_FULL의 return, MDD, exposure가 왜 다른가?
- 동일 episode / 동일 25->50->100 RAMP_3의 return, MDD, exposure가 왜 다른가?
- 최초 divergence가 어느 episode에서 발생하는가?
- divergence가 return 계산인지, window인지, exposure인지 식별할 수 있는가?

원칙
----
- Production 수정 금지
- 전략 로직 수정 금지
- 새로운 threshold/indicator 없음
- 기존 artifact만 비교
- 차이가 있으면 숨기지 않고 FAIL/HOLD
"""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "data" / "backtest" / "results"

OLD_PATH = RESULT_DIR / "filter15_staged_restoration_episodes.csv"
NEW_PATH = RESULT_DIR / "filter15_staged_restoration_parameter_sensitivity_episodes.csv"

OUT_DETAIL = RESULT_DIR / "filter15_staged_restoration_reconciliation_detail.csv"
OUT_SUMMARY = RESULT_DIR / "filter15_staged_restoration_reconciliation_summary.csv"
OUT_TXT = RESULT_DIR / "filter15_staged_restoration_reconciliation_audit.txt"

TOL = 1e-12

PATH_MAP = {
    "STATIC_FULL": "STATIC_FULL",
    "RAMP_3": "RAMP_3_25_50_100",
}


def num(s):
    return pd.to_numeric(s, errors="coerce")


def require_file(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"필요 artifact가 없습니다: {path}")


def load_old():
    require_file(OLD_PATH)
    df = pd.read_csv(OLD_PATH)

    required = [
        "episode_id",
        "release_date",
        "path",
        "total_return",
        "mdd",
        "avg_exposure",
        "invested_days",
        "full_days",
        "rebrake_days",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"기존 staged restoration artifact missing: {missing}")

    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    for c in [
        "episode_id", "total_return", "mdd", "avg_exposure",
        "invested_days", "full_days", "rebrake_days",
    ]:
        df[c] = num(df[c])

    df["path"] = df["path"].astype(str).str.strip().str.upper()

    return df


def load_new():
    require_file(NEW_PATH)
    df = pd.read_csv(NEW_PATH)

    required = [
        "episode_id",
        "release_date",
        "path",
        "total_return",
        "mdd",
        "avg_exposure",
        "invested_days",
        "full_days",
        "rebrake_days",
        "rows",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"parameter sensitivity artifact missing: {missing}")

    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    for c in [
        "episode_id", "total_return", "mdd", "avg_exposure",
        "invested_days", "full_days", "rebrake_days", "rows",
    ]:
        df[c] = num(df[c])

    df["path"] = df["path"].astype(str).str.strip().str.upper()

    return df


def close(a, b):
    if pd.isna(a) and pd.isna(b):
        return True
    if pd.isna(a) or pd.isna(b):
        return False
    return bool(np.isclose(float(a), float(b), atol=TOL, rtol=0.0))


def compare_path(old, new, old_path, new_path):
    a = old[old["path"] == old_path].copy()
    b = new[new["path"] == new_path].copy()

    if a.empty:
        raise ValueError(f"기존 artifact에 path 없음: {old_path}")
    if b.empty:
        raise ValueError(f"신규 artifact에 path 없음: {new_path}")

    a = a.rename(columns={
        "release_date": "old_release_date",
        "total_return": "old_total_return",
        "mdd": "old_mdd",
        "avg_exposure": "old_avg_exposure",
        "invested_days": "old_invested_days",
        "full_days": "old_full_days",
        "rebrake_days": "old_rebrake_days",
    })

    b = b.rename(columns={
        "release_date": "new_release_date",
        "total_return": "new_total_return",
        "mdd": "new_mdd",
        "avg_exposure": "new_avg_exposure",
        "invested_days": "new_invested_days",
        "full_days": "new_full_days",
        "rebrake_days": "new_rebrake_days",
        "rows": "new_rows",
    })

    a_cols = [
        "episode_id", "old_release_date", "old_total_return", "old_mdd",
        "old_avg_exposure", "old_invested_days", "old_full_days",
        "old_rebrake_days",
    ]
    b_cols = [
        "episode_id", "new_release_date", "new_total_return", "new_mdd",
        "new_avg_exposure", "new_invested_days", "new_full_days",
        "new_rebrake_days", "new_rows",
    ]

    m = a[a_cols].merge(
        b[b_cols],
        on="episode_id",
        how="outer",
        indicator=True,
    )

    m.insert(1, "comparison", f"{old_path} vs {new_path}")

    m["release_date_match"] = [
        x == y if not (pd.isna(x) or pd.isna(y)) else pd.isna(x) and pd.isna(y)
        for x, y in zip(m["old_release_date"], m["new_release_date"])
    ]

    metric_pairs = [
        ("total_return", "old_total_return", "new_total_return"),
        ("mdd", "old_mdd", "new_mdd"),
        ("avg_exposure", "old_avg_exposure", "new_avg_exposure"),
        ("invested_days", "old_invested_days", "new_invested_days"),
        ("full_days", "old_full_days", "new_full_days"),
        ("rebrake_days", "old_rebrake_days", "new_rebrake_days"),
    ]

    for name, oc, nc in metric_pairs:
        m[f"{name}_delta"] = m[nc] - m[oc]
        m[f"{name}_match"] = [
            close(x, y) for x, y in zip(m[oc], m[nc])
        ]

    match_cols = [
        "release_date_match",
        *[f"{x[0]}_match" for x in metric_pairs],
    ]

    m["exact_match"] = (
        (m["_merge"] == "both")
        & m[match_cols].all(axis=1)
    )

    # 최초로 무엇이 달라졌는지 사람이 바로 읽을 수 있게 분류
    def reason(row):
        if row["_merge"] != "both":
            return "EPISODE_SET_MISMATCH"
        if not row["release_date_match"]:
            return "RELEASE_DATE_MISMATCH"
        if not row["invested_days_match"] or not row["full_days_match"] or not row["rebrake_days_match"]:
            return "WINDOW_OR_STATE_PATH_MISMATCH"
        if not row["avg_exposure_match"]:
            return "EXPOSURE_PATH_MISMATCH"
        if not row["total_return_match"]:
            return "RETURN_CALCULATION_MISMATCH"
        if not row["mdd_match"]:
            return "MDD_CALCULATION_MISMATCH"
        return "MATCH"

    m["primary_divergence"] = m.apply(reason, axis=1)

    return m


def make_summary(detail):
    rows = []

    for comparison, g in detail.groupby("comparison", sort=False):
        rows.append({
            "comparison": comparison,
            "episodes": len(g),
            "exact_matches": int(g["exact_match"].sum()),
            "mismatches": int((~g["exact_match"]).sum()),
            "release_date_mismatches": int((~g["release_date_match"]).sum()),
            "return_mismatches": int((~g["total_return_match"]).sum()),
            "mdd_mismatches": int((~g["mdd_match"]).sum()),
            "exposure_mismatches": int((~g["avg_exposure_match"]).sum()),
            "invested_days_mismatches": int((~g["invested_days_match"]).sum()),
            "full_days_mismatches": int((~g["full_days_match"]).sum()),
            "rebrake_days_mismatches": int((~g["rebrake_days_match"]).sum()),
            "max_abs_return_delta": float(g["total_return_delta"].abs().max()),
            "max_abs_mdd_delta": float(g["mdd_delta"].abs().max()),
            "max_abs_exposure_delta": float(g["avg_exposure_delta"].abs().max()),
        })

    return pd.DataFrame(rows)


def main():
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    old = load_old()
    new = load_new()

    pieces = []

    for old_path, new_path in PATH_MAP.items():
        pieces.append(
            compare_path(
                old=old,
                new=new,
                old_path=old_path,
                new_path=new_path,
            )
        )

    detail = pd.concat(pieces, ignore_index=True)
    detail = detail.sort_values(["comparison", "episode_id"]).reset_index(drop=True)

    summary = make_summary(detail)

    detail.to_csv(OUT_DETAIL, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)

    bad = detail[~detail["exact_match"]].copy()

    lines = []
    lines.append("=" * 78)
    lines.append("FILTER15 STAGED RESTORATION RECONCILIATION AUDIT")
    lines.append("=" * 78)
    lines.append("")
    lines.append(f"Old Artifact : {OLD_PATH.name}")
    lines.append(f"New Artifact : {NEW_PATH.name}")
    lines.append("Production Modified : NO")
    lines.append("Strategy Modified   : NO")
    lines.append("Purpose             : FIND FIRST DIVERGENCE")
    lines.append("")
    lines.append("===== SUMMARY =====")
    lines.append(summary.to_string(index=False))
    lines.append("")
    lines.append("===== DIVERGENCE TYPES =====")
    if bad.empty:
        lines.append("NONE")
    else:
        lines.append(
            bad.groupby(
                ["comparison", "primary_divergence"]
            ).size().rename("rows").reset_index().to_string(index=False)
        )

    lines.append("")
    lines.append("===== FIRST 20 MISMATCHES =====")

    if bad.empty:
        lines.append("모든 비교가 정확히 일치합니다.")
    else:
        show_cols = [
            "comparison",
            "episode_id",
            "old_release_date",
            "new_release_date",
            "old_total_return",
            "new_total_return",
            "total_return_delta",
            "old_mdd",
            "new_mdd",
            "mdd_delta",
            "old_avg_exposure",
            "new_avg_exposure",
            "avg_exposure_delta",
            "old_invested_days",
            "new_invested_days",
            "old_full_days",
            "new_full_days",
            "old_rebrake_days",
            "new_rebrake_days",
            "new_rows",
            "primary_divergence",
        ]
        lines.append(
            bad[show_cols].head(20).to_string(index=False)
        )

    lines.append("")
    lines.append("===== INTERPRETATION =====")
    lines.append("")
    lines.append("1. STATIC_FULL부터 맞지 않으면 parameter 문제가 아니라 baseline/window/return contract 문제다.")
    lines.append("")
    lines.append("2. invested/full/rebrake day가 다르면 먼저 simulation window 또는 state-transition 구현을 비교한다.")
    lines.append("")
    lines.append("3. exposure path는 같은데 return만 다르면 SPY return alignment 또는 t -> t+1 계산을 비교한다.")
    lines.append("")
    lines.append("4. STATIC_FULL은 맞고 25/50/100만 다르면 RAMP stage progression/re-brake 구현을 비교한다.")
    lines.append("")
    lines.append("5. reconciliation 완료 전 sensitivity 결과로 Production 결정을 내리지 않는다.")
    lines.append("")
    lines.append("PRODUCTION DECISION: HOLD")
    lines.append("NEXT GATE: FIX THE IDENTIFIED CONTRACT DIVERGENCE, THEN RE-RUN SENSITIVITY")

    text = "\n".join(lines)
    OUT_TXT.write_text(text, encoding="utf-8")

    print()
    print(text)
    print()
    print(f"Saved: {OUT_DETAIL}")
    print(f"Saved: {OUT_SUMMARY}")
    print(f"Saved: {OUT_TXT}")


if __name__ == "__main__":
    main()
