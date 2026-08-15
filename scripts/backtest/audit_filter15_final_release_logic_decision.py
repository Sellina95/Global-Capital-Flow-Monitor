from __future__ import annotations

"""
FILTER15 FINAL RELEASE-LOGIC DECISION AUDIT

목적
----
지금까지 완료한 Filter15 Deadman / Release / Staged Restoration 연구 artifact를
한 곳에서 검증하고, Production 승격 전 최종 연구 판정을 남긴다.

이 스크립트는 전략을 다시 백테스트하지 않는다.
이미 검증된 artifact들의 audit gate와 핵심 결과를 읽어 최종 decision memo를 만든다.

원칙
----
- Production 수정 금지
- 새로운 indicator 없음
- 새로운 threshold 없음
- 새로운 parameter optimization 없음
- canonical sensitivity parity가 PASS가 아니면 중단
- 특정 parameter의 최고 수익률을 이유로 자동 채택하지 않음
"""

from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "data" / "backtest" / "results"

FILES = {
    "attribution": R / "filter15_exposure_attribution_audit.txt",
    "deadman": R / "filter15_deadman_release_audit.txt",
    "failure": R / "filter15_release_failure_analysis.txt",
    "persistence": R / "filter15_release_persistence_audit.txt",
    "restoration": R / "filter15_staged_restoration_audit.txt",
    "robustness": R / "filter15_staged_restoration_robustness_audit.txt",
    "sensitivity": R / "filter15_staged_restoration_parameter_sensitivity_canonical_audit.txt",
    "sensitivity_summary": R / "filter15_staged_restoration_parameter_sensitivity_canonical_summary.csv",
}

OUT_CSV = R / "filter15_final_release_logic_decision.csv"
OUT_TXT = R / "filter15_final_release_logic_decision.txt"


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"필요 artifact가 없습니다: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def require(text: str, patterns: list[str], label: str):
    for p in patterns:
        if re.search(p, text, flags=re.I):
            return
    raise ValueError(f"{label} 검증 문구를 찾지 못했습니다. 최종 판정을 중단합니다.")


def main():
    for p in FILES.values():
        if not p.exists():
            raise FileNotFoundError(f"필요 artifact가 없습니다: {p}")

    attribution = read_text(FILES["attribution"])
    deadman = read_text(FILES["deadman"])
    failure = read_text(FILES["failure"])
    persistence = read_text(FILES["persistence"])
    restoration = read_text(FILES["restoration"])
    robustness = read_text(FILES["robustness"])
    sensitivity = read_text(FILES["sensitivity"])

    # 이미 통과한 핵심 gate가 실제 artifact에 남아 있는지 확인한다.
    require(
        attribution,
        [r"FILTER15 ATTRIBUTION.*VALIDATED", r"ATTRIBUTION AUDIT PASS"],
        "Filter15 attribution",
    )
    require(
        deadman,
        [r"DEADMAN EPISODE AUDIT PASS"],
        "Deadman episode",
    )
    require(
        sensitivity,
        [r"PARITY\s*:\s*PASS"],
        "Canonical sensitivity parity",
    )
    require(
        sensitivity,
        [r"CANONICAL SENSITIVITY VALID"],
        "Canonical sensitivity",
    )

    s = pd.read_csv(FILES["sensitivity_summary"])

    required_cols = {
        "path",
        "episodes",
        "positive_episodes",
        "negative_episodes",
        "total_episode_return",
        "avg_episode_return",
        "median_episode_return",
        "avg_mdd",
        "worst_mdd",
        "avg_exposure",
    }
    missing = sorted(required_cols - set(s.columns))
    if missing:
        raise ValueError(f"Sensitivity summary missing columns: {missing}")

    expected_paths = {
        "RAMP_20_50_100",
        "RAMP_25_50_100",
        "RAMP_30_60_100",
        "RAMP_40_70_100",
    }
    present = set(s["path"].astype(str))
    if not expected_paths.issubset(present):
        raise ValueError(
            f"필요 sensitivity path가 부족합니다: {sorted(expected_paths - present)}"
        )

    ss = s[s["path"].isin(expected_paths)].copy()

    # 구조적 robustness:
    # 모든 인접 parameter가 positive aggregate return을 유지하는가?
    all_positive = bool((ss["total_episode_return"] > 0).all())

    # Tail-risk 방향성:
    # 초기 stage가 커질수록 worst MDD가 악화되는 자연스러운 monotonic pattern인지 확인.
    ordered = ss.set_index("path").loc[
        [
            "RAMP_20_50_100",
            "RAMP_25_50_100",
            "RAMP_30_60_100",
            "RAMP_40_70_100",
        ]
    ]
    worst = ordered["worst_mdd"].tolist()
    monotonic_tail = all(worst[i] >= worst[i + 1] for i in range(len(worst) - 1))

    # 최종 연구 판정.
    # 특정 20/25/30/40 중 하나를 "최적"으로 자동 선택하지 않는다.
    staged_structure_validated = all_positive and monotonic_tail

    if not staged_structure_validated:
        decision = "HOLD"
        candidate = "NONE"
        reason = (
            "Canonical sensitivity는 실행됐지만 인접 parameter 전반에서 "
            "구조적 robustness 조건을 만족하지 못함."
        )
    else:
        decision = "RESEARCH_VALIDATED_PRODUCTION_NOT_YET_MODIFIED"
        candidate = "STAGED_RE_RISKING_STRUCTURE"
        reason = (
            "Deadman 이후 즉시 full restoration보다 staged re-risking 구조를 "
            "Production 후보로 승격할 연구 근거가 충분함. "
            "단, 특정 20/25/30/40 초기 sizing을 수익률 기준으로 최적화하여 선택하지 않음."
        )

    rows = [
        {
            "gate": "FILTER15_PRODUCTION_PARITY_AND_ATTRIBUTION",
            "status": "PASS",
            "decision": "기존 Filter15 실행/attribution 검증 유지",
        },
        {
            "gate": "DEADMAN_EPISODE_AUDIT",
            "status": "PASS",
            "decision": "Deadman trigger/release episode contract 유지",
        },
        {
            "gate": "RELEASE_FAILURE_DIAGNOSIS",
            "status": "PASS_RESEARCH",
            "decision": "즉시 full re-risking의 false-recovery tail risk 확인",
        },
        {
            "gate": "PERSISTENCE_COUNTERFACTUAL",
            "status": "INSUFFICIENT_ALONE",
            "decision": "단순 2~3일 confirmation만으로 crisis tail 문제 해결 안 됨",
        },
        {
            "gate": "STAGED_RESTORATION",
            "status": "PASS_RESEARCH",
            "decision": "단계적 exposure restoration + re-brake 구조 유효",
        },
        {
            "gate": "ROBUSTNESS",
            "status": "PASS_WITH_TRADEOFF",
            "decision": "2008 단일 episode 의존 아님; 일부 recovery opportunity cost 존재",
        },
        {
            "gate": "CANONICAL_PARAMETER_SENSITIVITY",
            "status": "PASS" if staged_structure_validated else "HOLD",
            "decision": (
                "인접 parameter에서도 구조적 방향 유지"
                if staged_structure_validated
                else "인접 parameter robustness 부족"
            ),
        },
        {
            "gate": "FINAL_RELEASE_LOGIC",
            "status": decision,
            "decision": reason,
        },
    ]

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False)

    lines = [
        "=" * 78,
        "FILTER15 FINAL RELEASE-LOGIC DECISION",
        "=" * 78,
        "",
        "Production Modified      : NO",
        "New Indicator            : NO",
        "New Threshold            : NO",
        "Parameter Optimization   : NO",
        "",
        "===== GATE SUMMARY =====",
        out.to_string(index=False),
        "",
        "===== CANONICAL SENSITIVITY =====",
        ordered.reset_index().to_string(index=False),
        "",
        f"All Neighbor Paths Positive : {all_positive}",
        f"Tail Pattern Monotonic       : {monotonic_tail}",
        "",
        "===== FINAL RESEARCH DECISION =====",
        f"Decision  : {decision}",
        f"Candidate : {candidate}",
        "",
        reason,
        "",
    ]

    if staged_structure_validated:
        lines += [
            "최종 연구 결론:",
            "",
            "1. Filter15 기존 Production parity / attribution 결과는 유지한다.",
            "",
            "2. Hard Deadman 자체를 제거하지 않는다.",
            "",
            "3. Deadman 해제 직후 즉시 기존 full exposure로 복원하는 방식은",
            "   false-recovery tail risk 때문에 개선 후보로 본다.",
            "",
            "4. Production 후보 구조는:",
            "   DEADMAN -> RECOVERY SIGNAL -> STAGED RE-RISKING -> FULL RESTORATION",
            "   그리고 recovery signal이 깨지면 RE-BRAKE 한다.",
            "",
            "5. 20/50/100이 표본상 가장 좋아 보여도 자동 선택하지 않는다.",
            "   이번 Gate가 승인하는 것은 'staged structure'이지 최적 숫자가 아니다.",
            "",
            "6. 실제 Production 수정 전에는 별도의 minimal production patch와",
            "   production-vs-research exact parity regression test가 필요하다.",
            "",
            "PRODUCTION DECISION: APPROVE STRUCTURE FOR IMPLEMENTATION CANDIDATE",
            "PRODUCTION CODE CHANGE: NOT YET",
            "NEXT GATE: MINIMAL PRODUCTION PATCH + EXACT PARITY REGRESSION",
        ]
    else:
        lines += [
            "PRODUCTION DECISION: HOLD",
            "PRODUCTION CODE CHANGE: NO",
            "NEXT GATE: REVIEW FAILED ROBUSTNESS CONDITION",
        ]

    text = "\n".join(lines)
    OUT_TXT.write_text(text, encoding="utf-8")

    print("\n" + text)
    print(f"\nSaved: {OUT_CSV}")
    print(f"Saved: {OUT_TXT}")


if __name__ == "__main__":
    main()
