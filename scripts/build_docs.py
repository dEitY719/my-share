"""서브모듈의 docs/public/ 을 docs/<slug>/ 로 수집한다 (개인 허브용, mkdocs 없음).

aie-share scripts/build_docs.py 에서 수집 로직만 이식 — mkdocs nav/roadmap/site 제거.
파일 없으면 경고 후 스킵(빌드 실패 아님).

    python3 scripts/build_docs.py --build-dir docs --no-build

--no-build 는 aie-share 호출 관례와의 호환용으로 받기만 하고 무시한다(이 버전은 항상 수집만).
"""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Product:
    name: str
    slug: str
    path: str  # 서브모듈 디렉터리 (repo 루트 기준 상대 경로)
    changelog: str = "changelog.md"  # changelog.md | changelog.d


@dataclass
class CollectResult:
    product: Product
    files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def load_products(config_path: Path) -> list[Product]:
    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    products: list[Product] = []
    for entry in data.get("products", []):
        missing = [k for k in ("name", "slug", "path") if k not in entry]
        if missing:
            raise ValueError(f"products.yml 항목에 필수 키 누락 {missing}: {entry}")
        products.append(
            Product(
                name=entry["name"],
                slug=entry["slug"],
                path=entry["path"],
                changelog=entry.get("changelog", "changelog.md"),
            )
        )
    return products


def collect(products: list[Product], repo_root: Path, build_dir: Path) -> list[CollectResult]:
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    results: list[CollectResult] = []
    for product in products:
        result = CollectResult(product=product)
        src = repo_root / product.path / "docs" / "public"
        dest = build_dir / product.slug

        if not src.is_dir() or not any(src.iterdir()):
            result.warnings.append(f"{product.name}: docs/public 없음 또는 비어 있음 ({src})")
        else:
            shutil.copytree(src, dest)
            result.files = [
                p.relative_to(dest).as_posix() for p in sorted(dest.rglob("*")) if p.is_file()
            ]
        results.append(result)
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "products.yml")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--build-dir", type=Path, default=REPO_ROOT / "docs")
    parser.add_argument("--no-build", action="store_true", help="호환용 no-op(항상 수집만)")
    args = parser.parse_args(argv)

    products = load_products(args.config)
    results = collect(products, args.repo_root, args.build_dir)

    built = sum(1 for r in results if r.files)
    print(f"수집 완료: {built}/{len(products)} 제품")
    for warning in (w for r in results for w in r.warnings):
        print(f"  경고: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
