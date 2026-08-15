from __future__ import annotations

"""
Filter15 Production State-Persistence Scope Audit

목적
----
Deadman 이후 staged re-risking을 Production에 넣기 전에,
현재 Production 실행 구조가 전일 Filter15 상태를 실제로 다음 실행까지
보존하는지 확인한다.

중요
----
- Production 코드 수정 없음
- Backtest 로직 수정 없음
- 새 전략/threshold 없음
- 파일을 읽기만 함
- PREV_EXPOSURE 하나만 보고 state persistence가 있다고 가정하지 않음
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]

SEARCH_DIRS = [
    ROOT / "scripts",
    ROOT / "filters",
    ROOT / ".github",
]

TOKENS = [
    "PREV_EXPOSURE",
    "RECOMMENDED_EXPOSURE",
    "SEW_STATUS",
    "hard_deadman",
    "HARD_DEADMAN",
    "previous_state",
    "prev_state",
    "state_file",
    "state.json",
    "runtime_state",
]

TEXT_SUFFIXES = {
    ".py", ".yml", ".yaml", ".json", ".md", ".txt", ".sh"
}

FILTER15_FILE = ROOT / "filters" / "strategist_filters.py"


def iter_files():
    seen = set()

    for base in SEARCH_DIRS:
        if not base.exists():
            continue

        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in TEXT_SUFFIXES:
                continue

            # 결과물/캐시/가상환경 제외
            parts = set(p.parts)
            if "__pycache__" in parts or ".git" in parts:
                continue

            rp = p.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            yield p


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def find_hits():
    hits = []

    for path in iter_files():
        text = read_text(path)
        if not text:
            continue

        lines = text.splitlines()

        for i, line in enumerate(lines, start=1):
            matched = [t for t in TOKENS if t.lower() in line.lower()]
            if not matched:
                continue

            hits.append({
                "path": str(path.relative_to(ROOT)),
                "line": i,
                "tokens": ", ".join(matched),
                "text": line.strip()[:220],
            })

    return hits


def classify_hits(hits):
    writes_prev = []
    reads_prev = []
    persistence_io = []
    workflow_hits = []

    write_patterns = [
        re.compile(r'["\']PREV_EXPOSURE["\']\s*\]\s*='),
        re.compile(r'\.update\s*\([^)]*PREV_EXPOSURE', re.I),
    ]

    read_patterns = [
        re.compile(r'\.get\s*\(\s*["\']PREV_EXPOSURE["\']'),
        re.compile(r'\[\s*["\']PREV_EXPOSURE["\']\s*\]'),
    ]

    persistence_patterns = [
        re.compile(r'json\.dump', re.I),
        re.compile(r'json\.load', re.I),
        re.compile(r'to_json', re.I),
        re.compile(r'read_json', re.I),
        re.compile(r'write_text', re.I),
        re.compile(r'read_text', re.I),
        re.compile(r'pickle', re.I),
        re.compile(r'shelve', re.I),
        re.compile(r'sqlite', re.I),
        re.compile(r'runtime_state', re.I),
        re.compile(r'state_file', re.I),
        re.compile(r'state\.json', re.I),
    ]

    for h in hits:
        line = h["text"]
        path = h["path"]

        if "PREV_EXPOSURE" in line:
            if any(p.search(line) for p in write_patterns):
                writes_prev.append(h)

            # assignment line은 read로 세지 않음
            if (
                any(p.search(line) for p in read_patterns)
                and not any(p.search(line) for p in write_patterns)
            ):
                reads_prev.append(h)

        if any(p.search(line) for p in persistence_patterns):
            persistence_io.append(h)

        if path.startswith(".github/"):
            workflow_hits.append(h)

    return writes_prev, reads_prev, persistence_io, workflow_hits


def print_hits(title, rows, limit=40):
    print(f"\n===== {title} =====")
    if not rows:
        print("NONE")
        return

    for h in rows[:limit]:
        print(
            f'{h["path"]}:{h["line"]} | '
            f'{h["tokens"]} | {h["text"]}'
        )

    if len(rows) > limit:
        print(f"... +{len(rows) - limit} more")


def inspect_filter15_contract():
    print("\n===== FILTER15 CURRENT CONTRACT =====")

    if not FILTER15_FILE.exists():
        print("strategist_filters.py NOT FOUND")
        return

    text = read_text(FILTER15_FILE)

    checks = {
        "PREV_EXPOSURE write":
            'market_data["PREV_EXPOSURE"] = exposure' in text,

        "PREV_EXPOSURE read":
            bool(re.search(
                r'market_data\.get\(\s*["\']PREV_EXPOSURE["\']',
                text
            )),

        "SEW_STATUS write":
            'market_data["SEW_STATUS"] = status' in text,

        "previous recovery-stage state":
            bool(re.search(
                r'(RECOVERY_STAGE|RERISK_STAGE|RE_RISK_STAGE|'
                r'DEADMAN_PREV|PREV_DEADMAN)',
                text,
                re.I
            )),
    }

    for k, v in checks.items():
        print(f"{k:32}: {'YES' if v else 'NO'}")


def main():
    print("=" * 78)
    print("FILTER15 PRODUCTION STATE-PERSISTENCE SCOPE AUDIT")
    print("=" * 78)

    print("\nProduction Modified      : NO")
    print("Research Modified        : NO")
    print("Purpose                  : staged re-risking 전 state contract 확인")

    inspect_filter15_contract()

    hits = find_hits()
    writes_prev, reads_prev, persistence_io, workflow_hits = classify_hits(hits)

    print_hits("PREV_EXPOSURE WRITES", writes_prev)
    print_hits("PREV_EXPOSURE READS", reads_prev)
    print_hits("PERSISTENCE / STATE I-O CANDIDATES", persistence_io)
    print_hits("GITHUB WORKFLOW RELATED HITS", workflow_hits)

    # Filter15 외부에서 PREV_EXPOSURE를 읽는지
    external_prev_reads = [
        h for h in reads_prev
        if h["path"] != "filters/strategist_filters.py"
    ]

    # 명시적인 durable state I/O가 있는지 보수적으로 판정.
    # 단순 strategist_filters.py 내부 read_text 등은 제외.
    durable_candidates = [
        h for h in persistence_io
        if h["path"] != "filters/strategist_filters.py"
    ]

    print("\n===== FINAL SCOPE DECISION =====")

    if external_prev_reads or durable_candidates:
        print("STATUS : STATE_CONTRACT_NEEDS_TARGETED_INSPECTION")
        print()
        print("의미:")
        print("- 전일 상태를 이어받을 가능성이 있는 코드가 발견됨.")
        print("- 아래 후보를 확인한 뒤 기존 persistence contract를 재사용해야 함.")
        print("- 아직 새 state 파일을 만들지 않는다.")
    else:
        print("STATUS : NO_DURABLE_FILTER15_STATE_FOUND")
        print()
        print("의미:")
        print("- 현재 확인 범위에서는 PREV_EXPOSURE를 다음 일자로 영속화하는")
        print("  명확한 Production contract를 찾지 못함.")
        print("- market_data 안에 값을 쓰는 것과 다음 실행까지 보존되는 것은 다름.")
        print("- staged re-risking 패치 전에 최소 state persistence contract가 필요함.")

    print("\n===== PATCH RULE =====")
    print("1. 기존 Hard Deadman trigger는 수정하지 않는다.")
    print("2. 기존 정상 Filter15 exposure 계산도 수정하지 않는다.")
    print("3. 검증된 recovery candidate만 사용한다.")
    print("4. staged recovery state만 최소 추가한다.")
    print("5. recovery candidate가 깨지면 즉시 re-brake 한다.")
    print("6. Research에서 검증하지 않은 지표/threshold는 추가하지 않는다.")
    print("7. 패치 후 research-vs-production exact parity regression을 수행한다.")

    print("\nPRODUCTION DECISION: NO CHANGE")
    print("NEXT GATE: MINIMAL STATE CONTRACT + STAGED RE-RISK PATCH")


if __name__ == "__main__":
    main()
