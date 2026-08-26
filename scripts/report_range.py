"""docs/<slug>/ 에서 날짜 범위 [start, end] 항목만 골라 제품별로 모아 출력.

weekly/daily 스킬 공용. 담당자 매핑 없음(개인용). 범위 내 항목 없는 제품은 생략
(근거 없는 문구 생성 금지 — issue #1219 Error Cases).

    python3 scripts/report_range.py --start 2026-07-18 --end 2026-07-24 > out.md

두 가지 changelog 소스를 **합집합**으로 읽는다(issue #1, dEitY719/dotfiles#1471):

1. `changelog.md` — 단일 파일. `## YYYY-MM-DD` 헤더 아래 `- ...` 항목들.
2. `changelog.d/<YYYY-MM-DD>-<issue>.md` — PR 당 fragment 1개. 날짜는 **파일명**이
   들고 있어 파일 안에는 헤더가 없다(중복 헤더 클래스 원천 차단). 한 줄 = 한 항목.

같은 날짜가 양쪽에 있으면 한 섹션으로 병합하며, 그 안의 순서는
`changelog.md` 항목 → fragment 항목(파일명 오름차순)으로 결정론적이다.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from build_docs import REPO_ROOT, load_products

DATE_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$")
FRAGMENT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-.+\.md$")


def parse_sections(text: str) -> list[tuple[str, list[str]]]:
    """changelog 본문을 (날짜, 본문라인들) 목록으로 분해."""
    sections: list[tuple[str, list[str]]] = []
    cur_date: str | None = None
    cur: list[str] = []
    for line in text.splitlines():
        m = DATE_RE.match(line)
        if m:
            if cur_date:
                sections.append((cur_date, cur))
            cur_date, cur = m.group(1), []
        elif cur_date is not None:
            cur.append(line)
    if cur_date:
        sections.append((cur_date, cur))
    return sections


def fragment_sections(changelog_d: Path) -> list[tuple[str, list[str]]]:
    """changelog.d/<YYYY-MM-DD>-<issue>.md 들을 (날짜, bullet 라인들)로 수집."""
    sections: list[tuple[str, list[str]]] = []
    for path in sorted(changelog_d.glob("*.md"), key=lambda p: p.name):
        m = FRAGMENT_RE.match(path.name)
        if not m or not path.is_file():
            continue
        bullets = [
            ln
            for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.lstrip().startswith("#")
        ]
        if bullets:
            sections.append((m.group(1), bullets))
    return sections


def product_sections(product_dir: Path) -> list[tuple[str, list[str]]]:
    """제품 디렉터리의 changelog.md 와 changelog.d/ 를 합집합으로 수집.

    같은 날짜는 한 섹션으로 병합하며, 그 안의 순서는 changelog.md 항목 →
    fragment 항목(파일명 오름차순)이다.
    """
    # dict 는 삽입 순서를 보존하므로 별도 순서 리스트가 필요 없다.
    merged: dict[str, list[str]] = {}

    cl = product_dir / "changelog.md"
    if cl.is_file():
        for day, lines in parse_sections(cl.read_text(encoding="utf-8")):
            bullets = [ln for ln in lines if ln.strip()]
            if bullets:
                merged.setdefault(day, []).extend(bullets)

    frag_dir = product_dir / "changelog.d"
    if frag_dir.is_dir():
        for day, bullets in fragment_sections(frag_dir):
            merged.setdefault(day, []).extend(bullets)

    return list(merged.items())


def sections_in_range(
    sections: list[tuple[str, list[str]]], start: str, end: str
) -> list[tuple[str, list[str]]]:
    """범위 내 (날짜, bullet 라인들). ISO 날짜라 문자열 비교로 충분."""
    out = []
    for d, lines in sections:
        if start <= d <= end:
            bullets = [ln for ln in lines if ln.strip()]
            if bullets:
                out.append((d, bullets))
    return out


def entries_in_range(text: str, start: str, end: str) -> list[tuple[str, list[str]]]:
    """changelog.md 본문 문자열에 대한 범위 필터(단일 파일 형식 전용 진입점)."""
    return sections_in_range(parse_sections(text), start, end)


def build_report(start: str, end: str, docs_dir: Path, config: Path, title: str) -> str:
    products = load_products(config)
    lines = [f"# {title} — {start} ~ {end}", ""]
    any_hit = False
    for p in products:
        hits = sections_in_range(product_sections(docs_dir / p.slug), start, end)
        if not hits:
            continue
        any_hit = True
        lines.append(f"## {p.name}")
        for d, bullets in sorted(hits, reverse=True):
            lines.append(f"### {d}")
            lines.extend(bullets)
            lines.append("")
    if not any_hit:
        lines.append("(범위 내 변경 없음)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--start", required=True, help="YYYY-MM-DD (포함)")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD (포함)")
    parser.add_argument("--docs-dir", type=Path, default=REPO_ROOT / "docs")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "products.yml")
    parser.add_argument("--title", default="변경 수집")
    args = parser.parse_args(argv)

    for v in (args.start, args.end):
        date.fromisoformat(v)  # 형식 검증(잘못되면 ValueError)
    if args.start > args.end:
        parser.error(f"--start({args.start}) > --end({args.end})")

    print(build_report(args.start, args.end, args.docs_dir, args.config, args.title), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
