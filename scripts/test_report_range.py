"""report_range 자체 점검: 범위 필터 + 범위 밖 제외 + 빈 제품 생략.

    python3 scripts/test_report_range.py
"""

import tempfile
from pathlib import Path

from report_range import build_report, entries_in_range, fragment_sections, product_sections

CL = """# Changelog

## 2026-07-24
- 변경: **오늘 것**

## 2026-07-10
- 변경: **범위 밖 옛것**
"""


def test_range_filter():
    hits = entries_in_range(CL, "2026-07-18", "2026-07-24")
    assert [d for d, _ in hits] == ["2026-07-24"], hits
    assert hits[0][1] == ["- 변경: **오늘 것**"]
    # 범위 밖
    assert entries_in_range(CL, "2026-07-01", "2026-07-05") == []


def test_build_report_skips_empty_products():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs" / "a").mkdir(parents=True)
        (root / "docs" / "a" / "changelog.md").write_text(CL, encoding="utf-8")
        (root / "docs" / "b").mkdir(parents=True)
        (root / "docs" / "b" / "changelog.md").write_text("# Changelog\n\n## 2020-01-01\n- 변경: **old**\n", encoding="utf-8")
        cfg = root / "products.yml"
        cfg.write_text(
            "products:\n"
            "  - {name: A, slug: a, path: a}\n"
            "  - {name: B, slug: b, path: b}\n",
            encoding="utf-8",
        )
        out = build_report("2026-07-18", "2026-07-24", root / "docs", cfg, "주간")
        assert "## A" in out
        assert "오늘 것" in out
        assert "## B" not in out  # 범위 내 항목 없어 생략
        # 아무 것도 없을 때
        empty = build_report("2000-01-01", "2000-01-02", root / "docs", cfg, "주간")
        assert "(범위 내 변경 없음)" in empty


def test_fragment_sections_reads_date_from_filename():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "changelog.d"
        d.mkdir()
        (d / "2026-08-13-1103.md").write_text("- 변경: **A**\n", encoding="utf-8")
        assert fragment_sections(d) == [("2026-08-13", ["- 변경: **A**"])]


def test_product_sections_merges_changelog_md_and_fragments():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "changelog.md").write_text(
            "# Changelog\n\n## 2026-08-13\n- 변경: **md 쪽**\n", encoding="utf-8"
        )
        d = root / "changelog.d"
        d.mkdir()
        (d / "2026-08-13-1103.md").write_text("- 변경: **fragment 쪽**\n", encoding="utf-8")
        assert product_sections(root) == [
            ("2026-08-13", ["- 변경: **md 쪽**", "- 변경: **fragment 쪽**"])
        ]


def test_build_report_collects_fragment_only_product():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        d = root / "docs" / "a" / "changelog.d"
        d.mkdir(parents=True)
        (d / "2026-07-24-1471.md").write_text("- 변경: **fragment 전용**\n", encoding="utf-8")
        cfg = root / "products.yml"
        cfg.write_text("products:\n  - {name: A, slug: a, path: a}\n", encoding="utf-8")
        out = build_report("2026-07-18", "2026-07-24", root / "docs", cfg, "주간")
        assert "## A" in out
        assert "### 2026-07-24" in out
        assert "- 변경: **fragment 전용**" in out


def test_fragment_ignores_internal_date_header():
    """날짜는 파일명이 SSOT — 내부 `## ` 헤더가 새어 들어와도 보고서를 깨지 않는다."""
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "changelog.d"
        d.mkdir()
        (d / "2026-08-13-1103.md").write_text(
            "## 2026-01-01\n- 변경: **본문**\n", encoding="utf-8"
        )
        assert fragment_sections(d) == [("2026-08-13", ["- 변경: **본문**"])]


def test_same_date_fragments_sort_by_filename_ascending():
    """같은 날짜 안 순서는 파일명 오름차순 — 생성 순서/파일시스템 순서에 의존하지 않는다."""
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "changelog.d"
        d.mkdir()
        # 일부러 내림차순으로 생성한다
        (d / "2026-08-26-1471.md").write_text("- 변경: **늦은 이슈**\n", encoding="utf-8")
        (d / "2026-08-26-1460.md").write_text("- 변경: **이른 이슈**\n", encoding="utf-8")
        assert fragment_sections(d) == [
            ("2026-08-26", ["- 변경: **이른 이슈**"]),
            ("2026-08-26", ["- 변경: **늦은 이슈**"]),
        ]
        assert product_sections(Path(tmp)) == [
            ("2026-08-26", ["- 변경: **이른 이슈**", "- 변경: **늦은 이슈**"])
        ]


def test_fragment_dir_ignores_non_conforming_filenames_and_empty_files():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "changelog.d"
        d.mkdir()
        (d / "README.md").write_text("- 변경: **규약 밖**\n", encoding="utf-8")
        (d / "2026-08-26.md").write_text("- 변경: **이슈번호 없음**\n", encoding="utf-8")
        (d / "2026-08-26-1471.txt").write_text("- 변경: **md 아님**\n", encoding="utf-8")
        (d / "2026-08-26-1472.md").write_text("\n\n", encoding="utf-8")
        (d / "2026-08-26-1473.md").write_text("- 변경: **유일한 유효 항목**\n", encoding="utf-8")
        assert fragment_sections(d) == [("2026-08-26", ["- 변경: **유일한 유효 항목**"])]


def test_changelog_md_only_product_is_unchanged_by_dual_support():
    """다른 6개 product 회귀 방지 — changelog.md 만 있는 제품 출력이 이전과 동일."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs" / "stock-steward").mkdir(parents=True)
        (root / "docs" / "stock-steward" / "changelog.md").write_text(CL, encoding="utf-8")
        cfg = root / "products.yml"
        cfg.write_text(
            "products:\n  - {name: stock-steward, slug: stock-steward, path: stock-steward}\n",
            encoding="utf-8",
        )
        out = build_report("2026-07-18", "2026-07-24", root / "docs", cfg, "주간")
        assert out == (
            "# 주간 — 2026-07-18 ~ 2026-07-24\n"
            "\n"
            "## stock-steward\n"
            "### 2026-07-24\n"
            "- 변경: **오늘 것**\n"
        )


def test_interleaved_dates_are_emitted_newest_first():
    """두 소스의 날짜가 서로 끼어들어도 보고서 섹션은 날짜 내림차순이다."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        slug = root / "docs" / "a"
        (slug / "changelog.d").mkdir(parents=True)
        # changelog.md 는 내림차순, fragment 는 파일명(=날짜) 오름차순으로 읽힌다.
        (slug / "changelog.md").write_text(
            "# Changelog\n\n## 2026-07-24\n- 변경: **md 최신**\n"
            "\n## 2026-07-20\n- 변경: **md 옛것**\n",
            encoding="utf-8",
        )
        (slug / "changelog.d" / "2026-07-22-1471.md").write_text(
            "- 변경: **fragment 중간**\n", encoding="utf-8"
        )
        (slug / "changelog.d" / "2026-07-25-1472.md").write_text(
            "- 변경: **fragment 최신**\n", encoding="utf-8"
        )
        cfg = root / "products.yml"
        cfg.write_text("products:\n  - {name: A, slug: a, path: a}\n", encoding="utf-8")
        out = build_report("2026-07-18", "2026-07-25", root / "docs", cfg, "주간")
        assert [ln for ln in out.splitlines() if ln.startswith("### ")] == [
            "### 2026-07-25",
            "### 2026-07-24",
            "### 2026-07-22",
            "### 2026-07-20",
        ], out


def test_fragment_dir_skips_directories_matching_the_pattern():
    """규약 이름을 가진 디렉터리가 있어도 IsADirectoryError 로 죽지 않는다."""
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "changelog.d"
        d.mkdir()
        (d / "2026-08-26-1471.md").mkdir()
        (d / "2026-08-26-1472.md").write_text("- 변경: **정상 항목**\n", encoding="utf-8")
        assert fragment_sections(d) == [("2026-08-26", ["- 변경: **정상 항목**"])]


if __name__ == "__main__":
    test_range_filter()
    test_build_report_skips_empty_products()
    test_fragment_sections_reads_date_from_filename()
    test_product_sections_merges_changelog_md_and_fragments()
    test_build_report_collects_fragment_only_product()
    test_fragment_ignores_internal_date_header()
    test_same_date_fragments_sort_by_filename_ascending()
    test_fragment_dir_ignores_non_conforming_filenames_and_empty_files()
    test_changelog_md_only_product_is_unchanged_by_dual_support()
    test_interleaved_dates_are_emitted_newest_first()
    test_fragment_dir_skips_directories_matching_the_pattern()
    print("OK")
