"""build_docs.collect 자체 점검: 수집 1건 + docs/public 없는 repo 스킵.

    python3 scripts/test_build_docs.py
"""

import tempfile
from pathlib import Path

from build_docs import Product, collect


def test_collect_and_skip():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # repo A: docs/public/changelog.md 존재
        pub = root / "repoA" / "docs" / "public"
        pub.mkdir(parents=True)
        (pub / "changelog.md").write_text("## 2026-07-24\n- 변경: **x**\n", encoding="utf-8")
        # repo B: docs/public 없음 → 스킵 대상
        (root / "repoB").mkdir()

        products = [
            Product(name="A", slug="a", path="repoA"),
            Product(name="B", slug="b", path="repoB"),
        ]
        results = collect(products, root, root / "docs")

        by = {r.product.slug: r for r in results}
        assert by["a"].files == ["changelog.md"], by["a"].files
        assert not by["a"].warnings
        assert (root / "docs" / "a" / "changelog.md").is_file()
        assert by["b"].files == []
        assert by["b"].warnings and "docs/public 없음" in by["b"].warnings[0]


if __name__ == "__main__":
    test_collect_and_skip()
    print("OK")
