"""docs/<slug>/changelog.md 에서 날짜 범위 [start, end] 항목만 골라 제품별로 모아 출력.

weekly/daily 스킬 공용. 담당자 매핑 없음(개인용). 범위 내 항목 없는 제품은 생략
(근거 없는 문구 생성 금지 — issue #1219 Error Cases).

    python3 scripts/report_range.py --start 2026-07-18 --end 2026-07-24 > out.md

changelog 포맷: `## YYYY-MM-DD` 헤더 아래 `- ...` 항목들.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from build_docs import REPO_ROOT, load_products

DATE_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$")


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


def entries_in_range(text: str, start: str, end: str) -> list[tuple[str, list[str]]]:
    """범위 내 (날짜, bullet 라인들). ISO 날짜라 문자열 비교로 충분."""
    out = []
    for d, lines in parse_sections(text):
        if start <= d <= end:
            bullets = [ln for ln in lines if ln.strip()]
            if bullets:
                out.append((d, bullets))
    return out


def build_report(start: str, end: str, docs_dir: Path, config: Path, title: str) -> str:
    products = load_products(config)
    lines = [f"# {title} — {start} ~ {end}", ""]
    any_hit = False
    for p in products:
        cl = docs_dir / p.slug / "changelog.md"
        if not cl.is_file():
            continue
        hits = entries_in_range(cl.read_text(encoding="utf-8"), start, end)
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
