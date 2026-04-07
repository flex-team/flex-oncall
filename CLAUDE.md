# CLAUDE.md

## 이 repo는 무엇인가

온콜 업무를 위한 인덱스 repo. 관련 프로젝트들을 git submodule로 묶고, 이슈가 어느 코드베이스에 있는지 빠르게 찾는 시작점 역할을 한다. 이슈 파악과 운영 노트 기록이 목적이며, 코드 변경은 각 서브모듈 repo에서 수행한다.

- Always respond in Korean
- **이 repo는 도메인 스펙을 관리하지 않는다.** 도메인 스펙은 각 서브모듈 repo에서 관리한다. 이 repo는 운영 이슈 조사·기록·패턴 축적만 담당한다.
- **서브모듈 변경은 이 repo에 커밋하지 않는다.** 서브모듈은 코드 탐색·조사 용도로만 사용하며, PR과 커밋은 각 서브모듈 repo에서 직접 수행한다. `git add` 시 서브모듈 경로(`flex-*`)는 항상 제외할 것.

## 이상향

이 시스템의 궁극적 목표: **사람은 트리거링만 하고, 시스템이 도메인 전문가처럼 조사한다.**

현재는 그 단계가 아니다. 아래 플라이휠을 반복하며 점진적으로 도달한다:

> 이슈 처리 → 노트 기록 → 패턴 축적(COOKBOOK·domain-map) → 스킬/프롬프트 개선 → 더 정확한 조사 → …

매 세션에서 지켜야 할 원칙:

1. **경험을 반드시 남겨라.** 이슈를 처리했으면 운영 노트를 기록하고, 반복 패턴이 보이면 COOKBOOK에 올려라. 기록되지 않은 경험은 사라진다.
2. **도메인별 특성을 존중하라.** 도메인마다 조사 방법이 다르다 — 트래킹은 소급적용 영향도, 페이롤은 스냅샷 시점, 승인은 결재선 구조. 쿡북에 축적된 도메인별 진단 흐름을 따르고, 새 패턴을 발견하면 갱신하라.
3. **진입점을 빠르게 좁혀라.** 전체 repo를 탐색하지 말고 domain-map으로 라우팅하라. 넓게 찾는 것보다 정확히 찾는 것이 빠르다.
4. **누가 써도 안전하게.** 온콜 담당자가 도메인을 몰라도, 스킬과 쿡북이 올바른 조사 경로로 안내해야 한다.
5. **조사 경로를 패턴으로 남겨라.** 결론뿐 아니라 "어떤 로그를 봤고, 어떤 쿼리를 돌렸고, 왜 그 가설을 세웠는지"를 기록하라. 그것이 다음 담당자의 쿡북이 된다. (개별 이슈의 raw 데이터가 아니라 재사용 가능한 조사 패턴을 말한다.)

## 도메인 라우팅

- **도메인 맵**: `brain/domain-map.ttl` — 키워드/동의어 → 도메인 → repo/모듈 매핑 (이슈 라우팅의 단일 소스)
- 서브모듈 목록·브랜치는 `.gitmodules` 에서 확인
- 서브모듈 추가 시: `git submodule add -b <branch> git@github.com:flex-team/<repo>.git <dir>` → `CLAUDE.md` 서브모듈 맵도 갱신할 것
- 이슈 인입 시 `ops-find-domain` 스킬이 domain-map.ttl을 자동 탐색

## 온콜 워크플로우

> **트리거**: `~하려면 어떻게 해`, `누가 했는지`, `어디서 봐야 해`, `왜 이런 거야` 등
> 조사·추적 방법을 묻는 질문은 모두 온콜 워크플로우 진입점이다.
> 일반 질문으로 분류하지 말고, 반드시 타입 분류 → 도메인 파악 → 쿡북 확인 순서를 따를 것.

```
이슈 접수 (Linear/Slack)
  → 이슈 타입 분류 (triage-signals.md 참조: Error/Data/Perf/Auth/Spec/Render)
  → 도메인 파악 (ops-find-domain)
  → d:api로 관련 API 패턴 확인 (있으면 즉시 사용, 없으면 코드 탐색)
  → 타입별 첫 번째 액션:
    - Error/Perf/Auth → access log 확인
    - Data → DB 쿼리
    - Spec → 도메인 스펙 문서 확인 (의도된 동작인지 판별)
    - Render → access log로 API 응답 확인 → 정상이면 FE 코드 탐색
  → 쿡북 확인 (brain/COOKBOOK.md — 히트율 순 진단 플로우)
  → 데이터 조사 (DB/OpenSearch/Kafka)
  → 원인 분석 및 해결
  → 운영 노트 기록 (ops-note-issue / ops-investigate-issue)
  → 마감 (ops-close-note → brain 산출물 자동 갱신)
```

## 사용 가능한 스킬

### 이슈 라이프사이클

| 스킬 | 용도 |
|------|------|
| `ops-find-domain` | 이슈 타입 분류 + 도메인 라우팅 — 관련 서브모듈, API 패턴, 쿡북 섹션, 과거 노트 탐색 |
| `ops-note-issue` | Linear 이슈 조회 → operation-notes 문서 생성/업데이트 |
| `ops-investigate-issue` | Linear 이슈 조사 → 원인 파악 → operation-note 기록 |
| `ops-fix-issue` | Linear 이슈 기반 코드 조사 → 구현 → PR 생성 |
| `ops-close-note` | 완료된 이슈의 note 동기화 + 파생 산출물(COOKBOOK) 갱신 |

### 데이터 조사

> **⚠️ DB 조회 규칙**: DB 조회가 필요하면 **반드시 `ops-db-query-builder` 를 통해 수행**한다. `db:db-query` MCP 도구를 직접 호출하지 않는다.
> - `ops-db-query-builder`가 도메인 라우팅 → Entity 탐색 → SQL 구성 → 실행까지 일괄 처리한다.
> - 예외: `db_show_tables`, `db_describe` 등 스키마 탐색 목적의 단순 조회는 직접 허용.
> - 테이블명을 "알고 있다고 생각"해도 건너뛰지 않는다. Entity 출처 없는 SQL은 실행하지 않는다.
> - **`db_query` 실행은 반드시 메인 세션에서 직접 수행한다.**

| 스킬 | 용도 |
|------|------|
| `ops-db-query-builder` | 도메인 라우팅 → Entity 탐색 → 근거 있는 SQL 구성 → 실행 |
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
