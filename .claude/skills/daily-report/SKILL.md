---
name: daily-report
description: my-share 허브의 각 submodule docs/public/changelog.md 를 오늘 하루 범위로 수집해 reports/daily/ 에 일일 업무 보고를 생성한다. 사용자가 /daily-report, "오늘 보고 만들어", "일일 보고 정리" 라고 할 때 사용. 개인용(담당자 매핑 없음). weekly-report 와 Phase 1(날짜 범위)만 다르다.
---

# daily-report — 일일 업무 보고

products.yml 기반으로 각 제품의 changelog 를 오늘 하루치 모아 일일 보고를 만든다.
[[weekly-report]] 와 동일하되 날짜 범위만 "오늘 하루".

## Help

arg #1 이 `-h`/`--help`/`help` → 이 파일의 Phase 설명만 출력하고 중단.

## Phase 1 — 날짜 범위 계산

오늘 하루: `END=$(date +%F)`, `START="$END"`.
사용자가 특정 날짜를 주면 그 날짜를 START=END 로 쓴다.

## Phase 2 — 수집 (최신화 + 소스 문서)

허브 루트에서:

```bash
git submodule update --remote --quiet            # 각 repo 최신 main 당김(선택)
python3 scripts/build_docs.py --build-dir docs --no-build   # docs/<slug>/ 재수집
mkdir -p reports/daily
python3 scripts/report_range.py --start "$START" --end "$END" \
  --title "일일 보고" > "reports/daily/${END}-source.md"
```

`report_range.py` 는 범위 내 항목 없는 제품을 생략한다(근거 없는 문구 생성 금지).
소스가 `(범위 내 변경 없음)` 이면 그 사실만 보고하고 Phase 3 을 건너뛴다.

## Phase 3 — 최종 보고서 작성

`reports/daily/${END}-source.md` 를 읽고, 제품별 요약을 다듬어
`reports/daily/${END}.md` 로 저장한다. 규칙:

- 소스에 있는 changelog 항목만 근거로 쓴다. 없는 내용 지어내지 않는다.
- 제품별 그룹 유지, 각 항목은 사용자 관점 한 줄 요약.
- 헤더에 날짜(`${END}`)와 제품 수를 명시.

## 출력

`[OK] 일일 보고 생성 — reports/daily/${END}.md (제품 N개, ${END})`
