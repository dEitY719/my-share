# my-share

사외(github.com) 개인 프로젝트를 git submodule 로 모아 일일/주간 업무 보고를
자동 생성하는 개인용 허브. (aie-share 구조 참고 — dEitY719/dotfiles#1219)

각 대상 repo 는 `docs/public/` 아래에 변경 이력을 두고, 의미 있는 변경 시 갱신한다.
이 허브가 그 changelog 를 수집·날짜 필터링해 보고서를 만든다. 두 형식을 모두 읽는다
(dEitY719/dotfiles#1471):

- `changelog.md` — 단일 파일. `## YYYY-MM-DD` 헤더 아래 `- ...` 항목들.
- `changelog.d/<YYYY-MM-DD>-<issue>.md` — PR 당 fragment 1개. 날짜는 **파일명**이
  들고 있어 파일 안에는 헤더가 없고, 한 줄 = 한 항목이다. 같은 날짜 안 순서는
  파일명 오름차순. 두 소스가 공존하면 같은 날짜를 한 섹션으로 병합한다.

## 구조

```
my-share/
├── <repo>/                      git submodule (사외 개인 repo, products.yml 참조)
├── products.yml                 대상 목록 (name/slug/path/url)
├── scripts/
│   ├── build_docs.py            submodule docs/public/ → docs/<slug>/ 수집
│   └── report_range.py          docs/<slug>/ changelog.md + changelog.d/ 날짜범위 필터·수집
├── docs/<slug>/                 수집 산출물 — changelog.md 및/또는 changelog.d/ (gitignore)
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
