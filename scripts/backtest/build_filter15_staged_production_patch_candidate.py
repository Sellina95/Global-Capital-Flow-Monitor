from __future__ import annotations

"""
Filter15 staged re-risking 최소 Production 패치 후보 생성기.

이 스크립트는 filters/strategist_filters.py를 직접 수정하지 않는다.
후보 파일과 diff만 생성한다.
"""

from pathlib import Path
import difflib
import py_compile

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "filters" / "strategist_filters.py"
RESULTS = ROOT / "data" / "backtest" / "results"
OUT = RESULTS / "strategist_filters_filter15_staged_candidate.py"
DIFF = RESULTS / "filter15_staged_production_patch.diff"

MARKER = """    # --------------------------------------------------
    # 7️⃣ Final Override
    # --------------------------------------------------
    if hard_deadman:
        exposure = 0
        status = "HARD_DEADMAN"
    elif risk_compression:
        status = "RISK_COMPRESSION"
    else:
        status = "NORMAL"

    exposure = _clamp(exposure)

    market_data["RECOMMENDED_EXPOSURE"] = exposure
    market_data["PREV_EXPOSURE"] = exposure
    market_data["SEW_STATUS"] = status
"""

PATCH = """    # --------------------------------------------------
    # 7️⃣ Final Override + Deadman Recovery State
    # --------------------------------------------------
    # 기존 Hard Deadman trigger와 정상 exposure 계산은 그대로 둔다.
    # 검증된 recovery candidate: HY_FALLING_VIX_LT_30
    #
    # Production caller가 전일 persistent state를 주입해야 한다:
    # FILTER15_PREV_DEADMAN
    # FILTER15_RECOVERY_ACTIVE
    # FILTER15_RECOVERY_STREAK
    # FILTER15_PREV_HY_OAS

    prev_deadman = bool(market_data.get("FILTER15_PREV_DEADMAN", False))
    recovery_active = bool(
        market_data.get("FILTER15_RECOVERY_ACTIVE", False)
    )

    try:
        recovery_streak = int(
            market_data.get("FILTER15_RECOVERY_STREAK", 0) or 0
        )
    except Exception:
        recovery_streak = 0

    prev_hy_level = _to_float(
        market_data.get("FILTER15_PREV_HY_OAS")
    )

    recovery_candidate = (
        hy_level is not None
        and prev_hy_level is not None
        and hy_level < prev_hy_level
        and vix_today is not None
        and vix_today < 30
    )

    if hard_deadman:
        exposure = 0
        status = "HARD_DEADMAN"
        recovery_active = False
        recovery_streak = 0

    else:
        if prev_deadman or recovery_active:
            if recovery_candidate:
                recovery_active = True
                recovery_streak += 1

                if recovery_streak == 1:
                    exposure *= 0.25
                    status = "RECOVERY_STAGE_1"

                elif recovery_streak == 2:
                    exposure *= 0.50
                    status = "RECOVERY_STAGE_2"

                else:
                    # 3회 연속 recovery 확인 후 정상 Filter15 exposure 복원.
                    recovery_active = False
                    recovery_streak = 0
                    status = (
                        "RISK_COMPRESSION"
                        if risk_compression
                        else "NORMAL"
                    )

            else:
                # Recovery 조건이 깨지면 즉시 re-brake.
                exposure = 0
                recovery_active = True
                recovery_streak = 0
                status = "RECOVERY_REBRAKE"

        elif risk_compression:
            status = "RISK_COMPRESSION"

        else:
            status = "NORMAL"

    exposure = _clamp(exposure)

    market_data["RECOMMENDED_EXPOSURE"] = exposure
    market_data["PREV_EXPOSURE"] = exposure
    market_data["SEW_STATUS"] = status

    # 다음 실행으로 넘길 Filter15 persistent state.
    market_data["FILTER15_PREV_DEADMAN"] = bool(hard_deadman)
    market_data["FILTER15_RECOVERY_ACTIVE"] = bool(recovery_active)
    market_data["FILTER15_RECOVERY_STREAK"] = int(recovery_streak)
    market_data["FILTER15_PREV_HY_OAS"] = hy_level
"""


def main():
    if not SRC.exists():
        raise FileNotFoundError(SRC)

    RESULTS.mkdir(parents=True, exist_ok=True)
    original = SRC.read_text(encoding="utf-8")

    if "FILTER15_RECOVERY_STREAK" in original:
        raise RuntimeError(
            "이미 Filter15 recovery state가 존재합니다. 중복 patch를 중단합니다."
        )

    count = original.count(MARKER)
    if count != 1:
        raise RuntimeError(
            "Filter15 Final Override marker는 정확히 1개여야 합니다. "
            f"발견={count}"
        )

    candidate = original.replace(MARKER, PATCH, 1)
    OUT.write_text(candidate, encoding="utf-8")

    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            candidate.splitlines(keepends=True),
            fromfile="filters/strategist_filters.py",
            tofile="filters/strategist_filters.py [FILTER15 STAGED CANDIDATE]",
        )
    )
    DIFF.write_text(diff, encoding="utf-8")

    py_compile.compile(str(OUT), doraise=True)

    print("=" * 78)
    print("FILTER15 MINIMAL PRODUCTION PATCH CANDIDATE")
    print("=" * 78)
    print()
    print("Source Modified         : NO")
    print("Candidate Generated     : YES")
    print("Syntax Check            : PASS")
    print("Hard Deadman Changed    : NO")
    print("Normal Exposure Changed : NO")
    print("New Indicator           : NO")
    print("Recovery Candidate      : HY_FALLING_VIX_LT_30")
    print("Canonical Path          : 25% -> 50% -> 100%")
    print("Re-brake                : candidate break -> 0%")
    print()
    print("아직 Production에 적용하지 않는다.")
    print("다음 Gate: durable state wiring + research exact parity regression")
    print()
    print(f"Candidate: {OUT}")
    print(f"Diff     : {DIFF}")
    print()
    print("PRODUCTION DECISION: NO CHANGE")


if __name__ == "__main__":
    main()
