# my-share

사외(github.com) 개인 프로젝트를 git submodule 로 모아 일일/주간 업무 보고를
자동 생성하는 개인용 허브. (aie-share 구조 참고 — dEitY719/dotfiles#1219)

각 대상 repo 는 `docs/public/changelog.md` 를 두고, 의미 있는 변경 시 갱신한다.
이 허브가 그 changelog 를 수집·날짜 필터링해 보고서를 만든다.

## 구조

```
my-share/
├── <repo>/                      git submodule (사외 개인 repo, products.yml 참조)
├── products.yml                 대상 목록 (name/slug/path/url)
├── scripts/
│   ├── build_docs.py            submodule docs/public/ → docs/<slug>/ 수집
│   └── report_range.py          docs/<slug>/changelog.md 날짜범위 필터·수집
├── docs/<slug>/changelog.md     수집 산출물 (gitignore)
├── reports/{daily,weekly}/      보고서 출력 (gitignore)
└── .claude/skills/{daily,weekly}-report/
```

## 실행 루틴

```bash
git submodule update --remote                              # 각 repo 최신 main
python3 scripts/build_docs.py --build-dir docs --no-build  # changelog 수집
# 그다음 Claude Code 에서:
/daily-report      # 오늘 하루  → reports/daily/
/weekly-report     # 지난 7일   → reports/weekly/
```

## 초기 세팅

```bash
git submodule update --init --recursive
```
