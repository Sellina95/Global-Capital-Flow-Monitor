from pathlib import Path
import py_compile
import shutil

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "filters" / "strategist_filters.py"
BACKUP = ROOT / "data" / "backtest" / "results" / "strategist_filters_pre_filter15_patch_v2.py"

START = "    # 7️⃣ Final Override + Deadman Recovery State"
END = "    brake_drivers = _dedupe(brake_drivers)"

NEW_BLOCK = """    # --------------------------------------------------
    # 7️⃣ Final Override + Deadman Recovery State
    # --------------------------------------------------
    # 기존 hard_deadman trigger 계산은 변경하지 않는다.
    # 검증된 release candidate: HY_FALLING_VIX_LT_30
    #
    # Contract:
    # - 새 Deadman 최초 진입은 기존대로 0%.
    # - 전일부터 Deadman 상태였거나 recovery 중이면,
    #   hard_deadman이 현재도 True여도 recovery candidate를 평가한다.
    # - candidate 연속 1/2/3회 -> 25% / 50% / 100%.
    # - candidate break -> 즉시 0% re-brake.

    prev_deadman = bool(
        market_data.get("FILTER15_PREV_DEADMAN", False)
    )
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

    in_recovery_contract = prev_deadman or recovery_active

    if in_recovery_contract:
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

    elif hard_deadman:
        # 새 Deadman 최초 진입은 기존 Production contract 유지.
        exposure = 0
        recovery_active = False
        recovery_streak = 0
        status = "HARD_DEADMAN"

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
    text = TARGET.read_text(encoding="utf-8")

    marker = text.find(START)
    if marker < 0:
        raise RuntimeError("Filter15 staged block start not found; source unchanged.")

    start = text.rfind("    # --------------------------------------------------", 0, marker)
    if start < 0:
        raise RuntimeError("Filter15 block separator not found; source unchanged.")

    end = text.find(END, marker)
    if end < 0:
        raise RuntimeError("Filter15 staged block end not found; source unchanged.")

    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TARGET, BACKUP)

    new_text = text[:start] + NEW_BLOCK + text[end:]
    TARGET.write_text(new_text, encoding="utf-8")

    try:
        py_compile.compile(str(TARGET), doraise=True)
    except Exception:
        shutil.copy2(BACKUP, TARGET)
        raise

    print("=" * 78)
    print("FILTER15 MINIMAL CONTROL-FLOW PATCH V2")
    print("=" * 78)
    print("Syntax Check          : PASS")
    print("Hard Deadman Trigger  : UNCHANGED")
    print("Recovery Candidate    : HY_FALLING_VIX_LT_30")
    print("Recovery Path         : 25% -> 50% -> 100%")
    print("Re-brake              : candidate break -> 0%")
    print("Production main       : NOT TOUCHED")
    print("NEXT                   : POST-PATCH REGRESSION")
    print("DO NOT COMMIT until regression PASS.")
    print("Backup                 :", BACKUP)

if __name__ == "__main__":
    main()
