"""대상 repo 의 AI 컨텍스트 파일 안 changelog 지시 블록을 허브에서 한 번에 ON/OFF 한다.

각 repo 의 CLAUDE.md / AGENTS.md / GEMINI.md 에 있는 changelog 섹션을 마커
(`<!-- my-share:changelog:begin -->` ~ `:end -->`) 로 감싼 공통 블록으로 통일하고, 그 블록
본문만 ON/OFF 로 바꾼다. 첫 실행 시 기존 섹션(한글/영문, 헤더 레벨 무관)을 마커 블록으로
이관한다. ON 문구는 products.yml 의 `changelog`(changelog.md 기본 / changelog.d) 에 따라
고른다. 마커 **밖**에 둔 repo 고유 규칙은 토글해도 보존된다.

    python3 scripts/changelog_toggle.py status
    python3 scripts/changelog_toggle.py off
    python3 scripts/changelog_toggle.py on

--repo-root 로 서브모듈이 채워진 체크아웃을 지정할 수 있다(워크트리에서 실행할 때).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from build_docs import REPO_ROOT, load_products

BEGIN = "<!-- my-share:changelog:begin -->"
END = "<!-- my-share:changelog:end -->"

CONTEXT_FILES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md")

HEADING = "## 변경 기록 (changelog)"

# repo 의 changelog 포맷(products.yml `changelog`)별 ON 문구.
ON_RULES = {
    "changelog.md": "사용자 가시·운영·스키마·배포·비자명 동작 변경을 완료하면 `docs/public/changelog.md` 를 갱신한다(항목이 불필요하면 그 이유를 명시). 포맷: `## YYYY-MM-DD` 헤더 아래 `- 변경: **요약**`.",
    "changelog.d": "사용자 가시·운영·스키마·배포·비자명 동작 변경을 완료하면 `docs/public/changelog.d/<YYYY-MM-DD>-<issue>.md` fragment 를 1개 만든다(항목이 불필요하면 그 이유를 명시). 헤더 없이 한 줄 = 한 항목, 포맷: `- 변경: **요약**`.",
}

OFF_RULE = """- 현재 OFF. changelog 를 갱신하지 않는다(허브 수집 일시 중단).
- 재활성화는 my-share 에서 `python3 scripts/changelog_toggle.py on`."""


def body(state: str, fmt: str) -> str:
    if state == "off":
        return f"{HEADING}\n\n{OFF_RULE}"
    rule = ON_RULES[fmt]
    return (
        f"{HEADING}\n\n- {rule}\n"
        "- 이 changelog 는 일일/주간 보고 허브(my-share)가 수집해 보고서를 생성한다."
    )


# 마커 없는 기존 섹션(한글 "변경 기록" / 영문 "Changelog", 헤더 레벨 1~6).
LEGACY_HEADING = re.compile(
    r"^(?P<hashes>\#{1,6})[ \t]+.*(?:changelog|변경 기록).*$",
    re.IGNORECASE | re.MULTILINE,
)


def block(state: str, fmt: str) -> str:
    return f"{BEGIN}\n{body(state, fmt)}\n{END}\n"


def apply_state(text: str, state: str, fmt: str = "changelog.md") -> str | None:
    """마커 블록을 state 로 교체. 마커가 없으면 기존 섹션을 이관. 대상 없으면 None."""
    if BEGIN in text and END in text:
        start = text.index(BEGIN)
        end = text.index(END) + len(END)
        return text[:start] + block(state, fmt).rstrip("\n") + text[end:]

    match = LEGACY_HEADING.search(text)
    if not match:
        return None
    level = len(match.group("hashes"))
    # 같거나 더 상위 레벨의 다음 헤더까지가 이 섹션.
    following = re.compile(rf"^\#{{1,{level}}}[ \t]+", re.MULTILINE).search(text, match.end())
    end = following.start() if following else len(text)
    return text[: match.start()] + block(state, fmt) + ("\n" if following else "") + text[end:]


def read_state(text: str, fmt: str = "changelog.md") -> str:
    """파일의 현재 상태: on / off / custom(마커는 있으나 본문이 다름) / legacy / none."""
    if BEGIN in text and END in text:
        current = text[text.index(BEGIN) + len(BEGIN) : text.index(END)].strip()
        for state in ("on", "off"):
            if current == body(state, fmt):
                return state
        return "custom"
    return "legacy" if LEGACY_HEADING.search(text) else "none"


def targets(repo_root: Path, config_path: Path) -> list[tuple[Path, str]]:
    """(AI 컨텍스트 파일, changelog 포맷) 목록 — changelog 섹션이 있는 파일만."""
    found = []
    for product in load_products(config_path):
        for name in CONTEXT_FILES:
            path = repo_root / product.path / name
            if path.is_file() and read_state(path.read_text(encoding="utf-8")) != "none":
                found.append((path, product.changelog))
    return found


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=("status", "on", "off"), nargs="?", default="status")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "products.yml")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args(argv)

    paths = targets(args.repo_root, args.config)
    if not paths:
        print("대상 없음 — 서브모듈이 비어 있는지 확인 (git submodule update --init)")
        return 1

    changed = 0
    for path, fmt in paths:
        text = path.read_text(encoding="utf-8")
        before = read_state(text, fmt)
        rel = path.relative_to(args.repo_root).as_posix()
        if args.action == "status":
            print(f"  {before:>6}  {rel}")
            continue
        updated = apply_state(text, args.action, fmt)
        if updated is None or updated == text:
            print(f"  {'유지':>4}  {rel} ({before})")
            continue
        path.write_text(updated, encoding="utf-8")
        changed += 1
        print(f"  {before} -> {args.action}  {rel}")

    if args.action != "status":
        print(f"changelog {args.action.upper()}: {changed}/{len(paths)} 파일 변경")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
