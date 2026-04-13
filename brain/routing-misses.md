# Routing Feedback Log

라우팅 실패, 사용자 거부, 코드 대조 불일치를 기록한다.
`ops-learn` 실행 시 이 로그를 읽어 `d:kw`/`d:syn` 보강 및 `d:mod`/COOKBOOK 수정에 활용한다.

## 유형 정의

| 유형 | 설명 | 기록 주체 |
|------|------|----------|
| `miss` | 매칭된 도메인 없음 | ops-find-domain |
| `reject` | 매칭됐으나 사용자가 거부 | ops-find-domain |
| `correction` | 코드 확인 결과 TTL/쿡북 정보가 실제와 불일치 | ops-investigate-issue |
| `stale` | cookbook 플로우를 따랐으나 참조 아티팩트가 변경/삭제됨 | ops-investigate-issue, ops-compact |

## 로그

| 날짜 | 유형 | 입력 텍스트 / 불일치 내용 | 올바른 도메인·값 | 비고 |
|------|------|-------------------------|----------------|------|
| ~~2026-03-31~~ | ~~miss~~ | ~~"문서함", "신분증", "증명서", "서류함"~~ | ~~`:account`~~ | ~~CI-4256~~ — **처리 완료** (2026-04-02): `:account` d:kw에 "문서함", "UserDocument", "UserDocumentFile" 추가, d:syn에 "문서함 삭제 복구 가능한가요" 등 추가 |
| ~~2026-04-07~~ | ~~correction~~ | ~~"감사로그" + "스케줄 삭제 이력" → `:account` 감사로그 플로우로 라우팅~~ | ~~`:shift` + DB 직접 조회~~ | ~~CI-4351~~ — **처리 완료** (2026-04-13): `:shift` d:syn에 이미 반영됨 확인 |
| 2026-04-13 | correction | `:flow` d:repo=`flex-flow-backend` 로 매핑되어 있으나 "결재 문서/양식"(approval-document, approval-document-template, 관련 키워드 `workflow_task_template`/`customer_workflow_task_template`/`workflow_task_draft`/`approval-document` 등)의 실제 코드는 `flex-impact-backend` 하위 모듈에 있음 | 신규 도메인 `:approval-document` 도입 또는 `:flow`에 `flex-impact-backend` repo + `approval-document`, `approval-document-template`, `electronic-approval` 모듈 추가. 기존 `:flow` (notice/thread/todo/meeting 등)는 별개 유지 | CI-4416 — 결재 양식 가시성 체크 누락 조사 중 발견. flex-impact-backend/CLAUDE.md가 "결재 문서 관리" 모듈 존재 확인. ops-learn/ops-compact 단계에서 domain-map.ttl 보정 필요 |
