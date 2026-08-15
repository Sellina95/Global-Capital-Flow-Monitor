from __future__ import annotations

# Filter15 durable-state wiring 후보 생성기.
# 실제 Production 파일은 수정하지 않고 후보 파일과 diff만 생성한다.

from pathlib import Path
import difflib
import py_compile

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "scripts" / "generate_report.py"
RESULTS = ROOT / "data" / "backtest" / "results"

OUT = RESULTS / "generate_report_filter15_state_candidate.py"
DIFF = RESULTS / "filter15_durable_state_wiring.diff"

FUNCTION_INSERT_MARKER = 'def get_sew_state(filepath: str = "insights/sew_state.json") -> dict:\n'

STATE_FUNCTIONS = '''def get_filter15_state(
    filepath: str = "insights/filter15_state.json",
) -> dict:
    # Filter15 staged re-risking 전일 상태를 로드한다.
    default = {
        "timestamp": None,
        "prev_deadman": False,
        "recovery_active": False,
        "recovery_streak": 0,
        "prev_hy_oas": None,
        "sew_status": "N/A",
        "recommended_exposure": None,
    }

    if not os.path.exists(filepath):
        return default

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "timestamp": data.get("timestamp"),
            "prev_deadman": bool(data.get("prev_deadman", False)),
            "recovery_active": bool(data.get("recovery_active", False)),
            "recovery_streak": int(data.get("recovery_streak", 0) or 0),
            "prev_hy_oas": data.get("prev_hy_oas"),
            "sew_status": data.get("sew_status", "N/A"),
            "recommended_exposure": data.get("recommended_exposure"),
        }

    except Exception as e:
        print(
            "[WARNING][FILTER15 STATE LOAD] "
            f"{type(e).__name__}: {e}"
        )
        return default


def save_filter15_state(
    market_data: Dict[str, Any],
    timestamp: str,
    filepath: str = "insights/filter15_state.json",
) -> None:
    # 다음 실행에 필요한 최소 state만 저장한다.
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "timestamp": timestamp,
        "prev_deadman": bool(
            market_data.get("FILTER15_PREV_DEADMAN", False)
        ),
        "recovery_active": bool(
            market_data.get("FILTER15_RECOVERY_ACTIVE", False)
        ),
        "recovery_streak": int(
            market_data.get("FILTER15_RECOVERY_STREAK", 0) or 0
        ),
        "prev_hy_oas": market_data.get("FILTER15_PREV_HY_OAS"),
        "sew_status": market_data.get("SEW_STATUS", "N/A"),
        "recommended_exposure": market_data.get(
            "RECOMMENDED_EXPOSURE"
        ),
    }

    tmp_path = path.with_suffix(path.suffix + ".tmp")

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(
            payload,
            f,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )

    # 같은 filesystem 안에서 atomic replace.
    os.replace(tmp_path, path)


'''

COMMENTARY_MARKER = '''    # -------------------------
    # 6) Commentary block 생성
    # -------------------------
    commentary_block = build_strategist_commentary(market_data)
'''

COMMENTARY_REPLACEMENT = '''    # -------------------------
    # 5.7) Filter15 persistent state 주입
    # -------------------------
    # Filter15 실행 직전에 전일 recovery state를 market_data에 넣는다.
    filter15_state = get_filter15_state()

    market_data["FILTER15_PREV_DEADMAN"] = filter15_state.get(
        "prev_deadman", False
    )
    market_data["FILTER15_RECOVERY_ACTIVE"] = filter15_state.get(
        "recovery_active", False
    )
    market_data["FILTER15_RECOVERY_STREAK"] = filter15_state.get(
        "recovery_streak", 0
    )
    market_data["FILTER15_PREV_HY_OAS"] = filter15_state.get(
        "prev_hy_oas"
    )

    print(
        "[DEBUG][FILTER15 STATE LOAD]",
        {
            "timestamp": filter15_state.get("timestamp"),
            "prev_deadman": market_data.get("FILTER15_PREV_DEADMAN"),
            "recovery_active": market_data.get(
                "FILTER15_RECOVERY_ACTIVE"
            ),
            "recovery_streak": market_data.get(
                "FILTER15_RECOVERY_STREAK"
            ),
            "prev_hy_oas": market_data.get("FILTER15_PREV_HY_OAS"),
        },
    )

    # -------------------------
    # 6) Commentary block 생성
    # -------------------------
    commentary_block = build_strategist_commentary(market_data)

    # Filter15 실행 후 갱신된 state를 다음 Production run용으로 저장.
    save_filter15_state(
        market_data=market_data,
        timestamp=str(data_as_of_date),
    )

    print(
        "[DEBUG][FILTER15 STATE SAVE]",
        {
            "prev_deadman": market_data.get("FILTER15_PREV_DEADMAN"),
            "recovery_active": market_data.get(
                "FILTER15_RECOVERY_ACTIVE"
            ),
            "recovery_streak": market_data.get(
                "FILTER15_RECOVERY_STREAK"
            ),
            "prev_hy_oas": market_data.get("FILTER15_PREV_HY_OAS"),
            "recommended_exposure": market_data.get(
                "RECOMMENDED_EXPOSURE"
            ),
            "sew_status": market_data.get("SEW_STATUS"),
        },
    )
'''


def main():
    if not SRC.exists():
        raise FileNotFoundError(SRC)

    RESULTS.mkdir(parents=True, exist_ok=True)
    original = SRC.read_text(encoding="utf-8")

    if "def get_filter15_state(" in original:
        raise RuntimeError(
            "generate_report.py에 이미 Filter15 state loader가 있습니다. "
            "중복 wiring을 중단합니다."
        )

    if original.count(FUNCTION_INSERT_MARKER) != 1:
        raise RuntimeError(
            "get_sew_state() marker를 정확히 1개 찾지 못했습니다."
        )

    if original.count(COMMENTARY_MARKER) != 1:
        raise RuntimeError(
            "build_strategist_commentary() 실행 marker를 정확히 1개 "
            "찾지 못했습니다."
        )

    candidate = original.replace(
        FUNCTION_INSERT_MARKER,
        STATE_FUNCTIONS + FUNCTION_INSERT_MARKER,
        1,
    )

    candidate = candidate.replace(
        COMMENTARY_MARKER,
        COMMENTARY_REPLACEMENT,
        1,
    )

    OUT.write_text(candidate, encoding="utf-8")

    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            candidate.splitlines(keepends=True),
            fromfile="scripts/generate_report.py",
            tofile=(
                "scripts/generate_report.py "
                "[FILTER15 DURABLE STATE CANDIDATE]"
            ),
        )
    )
    DIFF.write_text(diff, encoding="utf-8")

    py_compile.compile(str(OUT), doraise=True)

    print("=" * 78)
    print("FILTER15 DURABLE STATE WIRING CANDIDATE")
    print("=" * 78)
    print()
    print("Source Modified          : NO")
    print("Candidate Generated      : YES")
    print("Syntax Check             : PASS")
    print("State File               : insights/filter15_state.json")
    print("Existing SEW State       : UNCHANGED")
    print("Existing Flow State      : UNCHANGED")
    print("Load Timing              : BEFORE build_strategist_commentary")
    print("Save Timing              : AFTER build_strategist_commentary")
    print("New Market Indicator     : NO")
    print("Future-data Backfill     : NO")
    print()
    print("아직 실제 Production 파일은 수정하지 않는다.")
    print("다음 Gate에서 staged Filter15 후보와 함께 exact parity를 검증한다.")
    print()
    print(f"Candidate: {OUT}")
    print(f"Diff     : {DIFF}")
    print()
    print("PRODUCTION DECISION: NO CHANGE")
    print(
        "NEXT GATE: FILTER15 RESEARCH-vs-PRODUCTION "
        "EXACT PARITY REGRESSION"
    )


if __name__ == "__main__":
    main()
