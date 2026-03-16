# CLAUDE.md

## 이 repo는 무엇인가

온콜 업무를 위한 인덱스 repo. 관련 프로젝트들을 git submodule로 묶고, 이슈가 어느 코드베이스에 있는지 빠르게 찾는 시작점 역할을 한다.

- Always respond in Korean

## 용어집

- **용어집**: `GLOSSARY.md` — 사용자/CS 표현 → 시스템 용어 → 서브모듈 매핑
- 이슈 인입 시 사용자의 표현이 어떤 도메인에 해당하는지 찾을 때 참조

## 서브모듈 맵

| 서브모듈 | 브랜치 | 도메인 | 키워드 |
|---------|--------|--------|--------|
| `flex-timetracking-backend` | develop | 근태, 휴가, 스케줄링, 초과근무, 보상휴가, 연차촉진, 포괄임금 | 근무기록, 연차, 휴일대체, 출퇴근, 근무유형, 급여계산 |
| `flex-pavement-backend` | develop | 알림, 푸시, 이메일 | 알림 미수신, CTA, notification |
| `flex-digicon-backend` | develop | | |
| `flex-core-backend` | develop | | |
| `flex-payroll-backend` | develop | | |
| `flex-yearend-backend` | develop | | |
| `flex-flow-backend` | develop | | |
| `flex-goal-backend` | develop | | |
| `flex-fins-backend` | develop | | |
| `flex-permission-backend` | develop | | |
| `flex-v2-backend-commons` | main | | |
| `flex-review-backend` | develop | | |
| `flex-work-event-transmitter-backend` | develop | | |
| `flex-openapi-backend` | develop | | |

> 서브모듈이 추가될 때마다 이 테이블을 업데이트할 것

## 도메인 → 코드 위치 가이드

### 근태/휴가 (`flex-timetracking-backend`)

- 근무유형(Work Rule): `/work-rule`
- 연차/맞춤휴가(Time Off): `/time-off`
- 근무기록(Work Record): `/work-record`
- 스케줄링(Work Schedule): `/work-schedule`
- 출퇴근(Work Clock): `/work-clock`
- 보상휴가(Compensatory Time Off): `/compensatory-time-off`
- 승인(Approval): `/approval`
- 외부 연동(External Work Clock): `/external-work-clock`
- 공휴일(Holiday): `/holiday`
- Operation API: 각 모듈의 `/operation-api` 하위

### 알림 (`flex-pavement-backend`)

- `flex-timetracking-backend` 알림 관련 코드가 이 repo를 참조

## 온콜 워크플로우

```
이슈 접수 (Linear/Slack)
  → 도메인 파악 (이 문서의 키워드 매핑 참조)
  → 쿡북 확인 (operation-notes/COOKBOOK.md)
  → 데이터 조사 (DB/OpenSearch/Kafka 스킬)
  → 원인 분석 및 해결
  → 운영 노트 기록
```

## 사용 가능한 조사 도구

온콜 이슈 조사에 쓸 수 있는 Claude Code 스킬:

| 스킬 | 용도 |
|------|------|
| `ops:investigate-issue` | Linear 이슈 조회/조사 → 원인 파악 → operation-note 기록 |
| `ops:note-issue` | Linear 이슈 조회 → operation-notes 문서 생성/업데이트 |
| `ops:fix-issue` | Linear 이슈 기반 코드 조사 → 구현 → PR 생성 |
| `db:db-query` | Aurora MySQL DB 쿼리 (dev/qa/prod) |
| `opensearch:os-query-log` | 애플리케이션 로그 검색 (Kibana) |
| `opensearch:os-query-service` | TT 서비스 문서 조회 (근무스케줄, 휴가사용 등) |
| `operation-api:ops-api` | flex-raccoon Operation API 호출 |
| `kafka:kafka-query` | Kafka 토픽/메시지/컨슈머그룹 조회 |
| `slack:slack-search` | Slack 메시지/파일/채널 검색 |

## 운영 지식 참조

- **쿡북**: `operation-notes/COOKBOOK.md` — 도메인별 진단 체크리스트, SQL 템플릿, 과거 사례
- **노트 인덱스**: `operation-notes/INDEX.md` — 키워드 → 문서 매핑 (전체 노트를 읽지 말고 여기서 관련 문서를 찾을 것)
- **진행 중 노트**: `operation-notes/{ticket-id}.md` — 루트에 위치한 active 이슈
- **해결 완료 노트**: `operation-notes/archive/{ticket-id}.md` — INDEX.md로 찾아서 필요한 것만 읽기
- **티켓 노트 작성 규칙**: `operation-notes/CLAUDE.md`
- **서브모듈별 운영 노트**: 각 서브모듈의 `.claude/operation-notes/` 디렉토리도 참조
  - 예: `flex-timetracking-backend/.claude/operation-notes/`
  - 이슈의 도메인이 파악되면 해당 서브모듈의 운영 노트를 우선 확인할 것
