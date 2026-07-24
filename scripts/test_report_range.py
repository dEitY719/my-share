"""report_range 자체 점검: 범위 필터 + 범위 밖 제외 + 빈 제품 생략.

    python3 scripts/test_report_range.py
"""

import tempfile
from pathlib import Path

from report_range import build_report, entries_in_range

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


if __name__ == "__main__":
    test_range_filter()
    test_build_report_skips_empty_products()
    print("OK")
