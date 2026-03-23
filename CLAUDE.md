# CLAUDE.md

## 이 repo는 무엇인가

온콜 업무를 위한 인덱스 repo. 관련 프로젝트들을 git submodule로 묶고, 이슈가 어느 코드베이스에 있는지 빠르게 찾는 시작점 역할을 한다. 이슈 파악과 운영 노트 기록이 목적이며, 코드 변경은 각 서브모듈 repo에서 수행한다.

- Always respond in Korean
- **이 repo는 도메인 스펙을 관리하지 않는다.** 도메인 스펙은 각 서브모듈 repo에서 관리한다. 이 repo는 운영 이슈 조사·기록·패턴 축적만 담당한다.
- **서브모듈 변경은 이 repo에 커밋하지 않는다.** 서브모듈은 코드 탐색·조사 용도로만 사용하며, PR과 커밋은 각 서브모듈 repo에서 직접 수행한다. `git add` 시 서브모듈 경로(`flex-*`)는 항상 제외할 것.

## 용어집

- **용어집**: `brain/GLOSSARY.md` — 사용자/CS 표현 → 시스템 용어 → 서브모듈 매핑
- 이슈 인입 시 사용자의 표현이 어떤 도메인에 해당하는지 찾을 때 참조

## 서브모듈 맵

| 서브모듈 | 브랜치 | 도메인 | 키워드 |
|---------|--------|--------|--------|
| `flex-timetracking-backend` | main | 근태, 휴가, 연차, 근무, 초과근무, 보상휴가, 연차촉진 | 근무스케줄, 근무기록, 연차, 휴일대체, 출퇴근, 근무유형, 포괄임금 |
| `flex-pavement-backend` | main | 알림, 푸시, 이메일 | notification |
| `flex-digicon-backend` | main | | |
| `flex-core-backend` | main | 구성원, 직급, 직책, 직무, 직위 | 직4, 직5 |
| `flex-payroll-backend` | main | 급여 | |
| `flex-yearend-backend` | main | 연말정산, 공제, 퇴직소득, 세금정책 | 연말정산, 공제, 증빙서류, 퇴직정산, 정산보고서 |
| `flex-flow-backend` | main | 협업, 커뮤니케이션 | 공지사항, 스레드, 할일, 미팅, 이슈, 요약, 음성전사, 협업문서 |
| `flex-goal-backend` | main | 목표, OKR | 목표 리스트, objective, cycle, 내 목표, 전체 목표, 구성원 목표 |
| `flex-fins-backend` | main | 비용관리, 경비 | 카드, 지출, 가맹점, 분개, 비용정책, 데이터동기화, codef |
| `flex-permission-backend` | main | 권한, 인가 | OpenFGA, 분산락, PIP |
| `flex-v2-backend-commons` | main | | |
| `flex-review-backend` | main | 평가, 리뷰 | evaluation, form, grade, 평가주기, 역량, AI프롬프트 |
| `flex-work-event-transmitter-backend` | main | 출퇴근 이벤트 전송 | CAPS, SECOM, TELECOP, 캡콤 |
| `flex-openapi-backend` | main | 외부 API, 데이터 통합 | OpenAPI, 토큰, SAP, 급여전기, 인사연동, 회계연동 |
| `flex-timetracking-config` | prod | 근태 설정 | 피처플래그, feature flag |
| `flex-raccoon` | main | Operation API, 운영 도구 | raccoon, operation-api, 운영 API |
| `flex-admin-shell` | main | 관리자 쉘, 운영 콘솔 | admin-shell, 운영 콘솔, 설정 변경 |
| `flex-github-actions` | main | GitHub Actions, CI/CD | github-actions, workflow, CI, CD |
| `flex-timetracking-frontend` | main | 근태 프론트엔드 | 근태 UI, 프론트엔드, React |

> 서브모듈이 추가될 때마다 이 테이블을 업데이트할 것

## 도메인 → 코드 위치 가이드

### 근태/휴가 (`flex-timetracking-backend`)

- 근무유형(Work Rule): `/work-rule`
- 연차/맞춤휴가(Time Off): `/time-off`
- 근무기록(Work Record): `/work-record`
- 근무스케줄(Work Schedule): `/work-schedule`
- 출퇴근(Work Clock): `/work-clock`
- 보상휴가(Compensatory Time Off): `/compensatory-time-off`
- 승인(Approval): `/approval`
- 외부 연동(External Work Clock): `/external-work-clock`
- 공휴일(Holiday): `/holiday`
- Operation API: 각 모듈의 `/operation-api` 하위

### 알림 (`flex-pavement-backend`)

- `flex-timetracking-backend` 알림 관련 코드가 이 repo를 참조

## 온콜 워크플로우

> **트리거**: `~하려면 어떻게 해`, `누가 했는지`, `어디서 봐야 해`, `왜 이런 거야` 등
> 조사·추적 방법을 묻는 질문은 모두 온콜 워크플로우 진입점이다.
> 일반 질문으로 분류하지 말고, 반드시 도메인 파악 → 쿡북 확인 순서를 따를 것.

```
이슈 접수 (Linear/Slack)
  → 도메인 파악 (ops-find-domain 스킬 사용)
  → 쿡북 확인 (brain/COOKBOOK.md)
  → 데이터 조사 (DB/OpenSearch/Kafka 스킬)
  → 원인 분석 및 해결
  → 운영 노트 기록
  → ops-learn으로 brain 산출물 갱신 (GLOSSARY/COOKBOOK/domain-map.ttl)
```

## 사용 가능한 조사 도구

온콜 이슈 조사에 쓸 수 있는 Claude Code 스킬:

| 스킬 | 용도 |
|------|------|
| `ops-find-domain` | 이슈 키워드로 도메인 라우팅 — 관련 서브모듈, 쿡북 섹션, 과거 노트 탐색 |
| `ops-close-note` | 완료된 이슈의 note 동기화 + 파생 산출물(COOKBOOK) 갱신 |
| `ops-investigate-issue` | Linear 이슈 조회/조사 → 원인 파악 → operation-note 기록 |
| `ops-note-issue` | Linear 이슈 조회 → operation-notes 문서 생성/업데이트 |
| `ops-fix-issue` | Linear 이슈 기반 코드 조사 → 구현 → PR 생성 |
| `ops-learn` | 지식 소스(Notion/Slack/Linear/노트)에서 brain 산출물 전체 갱신 |
| `ops-maintain-notes` | 활성 노트 일괄 유지보수 + 아카이브. `--rebuild` 로 전체 재구성 |
| `ops-db-query-builder` | DB 쿼리 필요 시 도메인 라우팅 → Entity 탐색 → 근거 있는 SQL 구성 |
| `db:db-query` | Aurora MySQL DB 쿼리 (dev/qa/prod) |
| `opensearch:os-query-log` | 애플리케이션 로그 검색 (Kibana) |
| `opensearch:os-query-service` | TT 서비스 문서 조회 (근무스케줄, 휴가사용 등) |
| `operation-api:ops-api` | flex-raccoon Operation API 호출 |
| `kafka:kafka-query` | Kafka 토픽/메시지/컨슈머그룹 조회 |
| `slack:slack-search` | Slack 메시지/파일/채널 검색 |

## 운영 지식 참조

- **쿡북**: `brain/COOKBOOK.md` — 도메인별 진단 체크리스트, SQL 템플릿, 과거 사례
- **도메인 맵**: `brain/domain-map.ttl` — 키워드 → 문서 매핑 (전체 노트를 읽지 말고 여기서 관련 문서를 찾을 것)
- **진행 중 노트**: `brain/notes/{ticket-id}.md` — notes/ 루트에 위치한 active 이슈
- **해결 완료 노트**: `brain/notes/archive/{ticket-id}.md` — domain-map.ttl로 찾아서 필요한 것만 읽기
- **티켓 노트 작성 규칙**: `brain/CLAUDE.md`
- **용어집**: `brain/GLOSSARY.md`
- **서브모듈별 운영 노트**: 각 서브모듈의 `.claude/operation-notes/` 디렉토리도 참조
  - 예: `flex-timetracking-backend/.claude/operation-notes/`
  - 이슈의 도메인이 파악되면 해당 서브모듈의 운영 노트를 우선 확인할 것
