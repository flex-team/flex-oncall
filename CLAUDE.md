# CLAUDE.md

## 이 repo는 무엇인가

온콜 업무를 위한 인덱스 repo. 관련 프로젝트들을 git submodule로 묶고, 이슈가 어느 코드베이스에 있는지 빠르게 찾는 시작점 역할을 한다. 이슈 파악과 운영 노트 기록이 목적이며, 코드 변경은 각 서브모듈 repo에서 수행한다.

- Always respond in Korean
- **이 repo는 도메인 스펙을 관리하지 않는다.** 도메인 스펙은 각 서브모듈 repo에서 관리한다. 이 repo는 운영 이슈 조사·기록·패턴 축적만 담당한다.
- **서브모듈 변경은 이 repo에 커밋하지 않는다.** 서브모듈은 코드 탐색·조사 용도로만 사용하며, PR과 커밋은 각 서브모듈 repo에서 직접 수행한다. `git add` 시 서브모듈 경로(`flex-*`)는 항상 제외할 것.

## 도메인 라우팅

- **도메인 맵**: `brain/domain-map.ttl` — 키워드/동의어 → 도메인 → repo/모듈 매핑 (이슈 라우팅의 단일 소스)
- 서브모듈 목록·브랜치는 `.gitmodules` 에서 확인
- 서브모듈 추가 시: `git submodule add -b <branch> git@github.com:flex-team/<repo>.git <dir>` → `CLAUDE.md` 서브모듈 맵도 갱신할 것
- 이슈 인입 시 `ops-find-domain` 스킬이 domain-map.ttl을 자동 탐색

## 온콜 워크플로우

> **트리거**: `~하려면 어떻게 해`, `누가 했는지`, `어디서 봐야 해`, `왜 이런 거야` 등
> 조사·추적 방법을 묻는 질문은 모두 온콜 워크플로우 진입점이다.
> 일반 질문으로 분류하지 말고, 반드시 도메인 파악 → 쿡북 확인 순서를 따를 것.

```
이슈 접수 (Linear/Slack)
  → 도메인 파악 (ops-find-domain)
  → 쿡북 확인 (brain/COOKBOOK.md — 히트율 순 진단 플로우)
  → API 이슈일 때: 가설 전에 access log부터 확인
  → 데이터 조사 (DB/OpenSearch/Kafka)
  → 원인 분석 및 해결
  → 운영 노트 기록 (ops-note-issue / ops-investigate-issue)
  → 마감 (ops-close-note → brain 산출물 자동 갱신)
```

## 사용 가능한 스킬

### 이슈 라이프사이클

| 스킬 | 용도 |
|------|------|
| `ops-find-domain` | 이슈 키워드로 도메인 라우팅 — 관련 서브모듈, 쿡북 섹션, 과거 노트 탐색 |
| `ops-note-issue` | Linear 이슈 조회 → operation-notes 문서 생성/업데이트 |
| `ops-investigate-issue` | Linear 이슈 조사 → 원인 파악 → operation-note 기록 |
| `ops-fix-issue` | Linear 이슈 기반 코드 조사 → 구현 → PR 생성 |
| `ops-close-note` | 완료된 이슈의 note 동기화 + 파생 산출물(COOKBOOK) 갱신 |

### 데이터 조사

| 스킬 | 용도 |
|------|------|
| `ops-db-query-builder` | 도메인 라우팅 → Entity 탐색 → 근거 있는 SQL 구성 |
| `db:db-query` | Aurora MySQL DB 쿼리 (dev/qa/prod) |
| `db:db-data-sync` | prod → dev 데이터 복제 (INSERT 생성) |
| `opensearch:os-query-log` | 애플리케이션 로그 검색 (Kibana) |
| `opensearch:os-query-service` | TT 서비스 문서 조회 (근무스케줄, 휴가사용 등) |
| `kafka:kafka-query` | Kafka 토픽/메시지/컨슈머그룹 조회 |
| `slack:slack-search` | Slack 메시지/파일/채널 검색 |

### 운영 도구

| 스킬 | 용도 |
|------|------|
| `operation-api:ops-api` | flex-raccoon Operation API 호출 |
| `operation:hashed-id` | DB Long ID ↔ HashedId 변환 |
| `operation:log-analysis` | OpenSearch URL/Slack 에러/traceId 기반 로그 분석 |

### 로컬 개발

| 스킬 | 용도 |
|------|------|
| `local-dev:local-server` | 로컬 Spring Boot 서버 기동/종료/모니터링 |
| `local-dev:local-debug` | 로컬 서버 디버깅 (브라우저+대시보드) |
| `dev-tools:dev-loop` | dev 환경 통합 검증 루프 (서버, DB, Kafka, API) |

### 지식 관리

| 스킬 | 용도 |
|------|------|
| `ops-learn` | 지식 소스(Notion/Slack/Linear/노트)에서 brain 산출물 전체 갱신 |
| `ops-compact` | brain 산출물 컴팩션 — 농축 → 퇴출 → COOKBOOK 계층 조정 → 히트율 리포트 |
| `ops-maintain-notes` | 활성 노트 일괄 유지보수 + 아카이브. `--rebuild` 로 전체 재구성 |

## 운영 지식 참조

- **쿡북**: `brain/COOKBOOK.md` — 도메인별 진단 체크리스트, SQL 템플릿, 과거 사례
- **진행 중 노트**: `brain/notes/{ticket-id}.md` — notes/ 루트에 위치한 active 이슈
- **해결 완료 노트**: `brain/notes/archive/{ticket-id}.md` — domain-map.ttl로 찾아서 필요한 것만 읽기
- **티켓 노트 작성 규칙**: `brain/CLAUDE.md`
- **서브모듈별 운영 노트**: 각 서브모듈의 `.claude/operation-notes/` 디렉토리도 참조
  - 예: `flex-timetracking-backend/.claude/operation-notes/`
  - 이슈의 도메인이 파악되면 해당 서브모듈의 운영 노트를 우선 확인할 것
