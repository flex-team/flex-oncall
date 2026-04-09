# CLAUDE.md

## 이 repo는 무엇인가

온콜 업무를 위한 인덱스 repo. 관련 프로젝트들을 git submodule로 묶고, 이슈가 어느 코드베이스에 있는지 빠르게 찾는 시작점 역할을 한다. 이슈 파악과 운영 노트 기록이 목적이며, 코드 변경은 각 서브모듈 repo에서 수행한다.

- Always respond in Korean

### 설계 공리: 코드가 진실이다

스펙의 단일 소스(Single Source of Truth)는 **각 서브모듈의 코드와 테스트**다. 이 repo에 스펙을 복사하면 코드가 변할 때 반드시 부패한다.

이 repo가 **하는 것**:
- 도메인을 찾는다 (domain-map → 라우팅)
- 문의를 판단한다 (assess → 성격/범위/긴급도)
- 조사 패턴을 축적한다 (COOKBOOK → "어떻게 조사하느냐")
- 사용자가 올바른 질문을 하도록 유도한다 (triage-signals → 타입 분류)

이 repo가 **하지 않는 것**:
- 도메인 스펙을 저장하지 않는다 — 스펙은 해당 repo의 코드에서 파악한다
- 서브모듈을 변경하지 않는다 — 코드 수정은 각 서브모듈 repo에서 수행한다 (`git add` 시 `flex-*` 경로 항상 제외)

COOKBOOK이 스펙 데이터베이스가 아닌 이유: 쿡북은 "이런 문의가 오면 어떻게 조사하라"는 절차이지, "스펙이 이렇다"는 정의가 아니다. 그래서 신선도를 관리한다 — 코드가 변하면 쿡북의 조사 절차도 변해야 하니까.

**도메인 지식의 위치 원칙**:
- 도메인 지식은 **도메인 오너가 관리하는 곳**에 둔다 — repo 내 마크다운, 시나리오 테스트(Gherkin), Notion 등 형태와 위치는 도메인마다 다르고, 그 선택은 도메인 오너의 몫이다
- 해당 도메인 repo의 CLAUDE.md에 "우리 도메인 지식은 여기 있다"가 안내되어 있으면, investigate가 서브모듈 탐색 시 자연스럽게 발견한다
- **support-oncall에 특정 도메인의 KB 링크나 전용 인프라를 두지 않는다** — 위치가 바뀔 때 감지 못 하고 부패한다. support-oncall이 아는 건 "어떤 repo를 보라"까지이고, 그 안에서 뭘 보는지는 해당 repo가 안내한다
- KB 사용 효과 측정은 기존 메트릭(`cookbook_verdict`, `pipeline_feedback.retrospective`)으로 수행한다

## 이상향

이 시스템의 궁극적 목표: **사람은 트리거링만 하고, 시스템이 도메인 전문가처럼 조사한다.**

현재는 그 단계가 아니다. 아래 플라이휠을 반복하며 점진적으로 도달한다:

> 이슈 처리 → 노트 기록 → 패턴 축적(COOKBOOK·domain-map) → 스킬/프롬프트 개선 → 더 정확한 조사 → …

### 파이프라인이 추구하는 접근 방식

단편적으로 "이 유저의 문제"만 해결하는 것이 아니라, **시니어처럼 구조적으로 접근**한다:

1. **먼저 생각하고, 그 다음에 조사하라.** 왜 문제인지, 어디가 문제인지, 얼마나 문제인지를 먼저 판단한다. "1명만 문의했다 ≠ 1명만 영향"이다.
2. **기존 지식을 먼저 참조하라.** 전수 검색이 아니라, domain-map과 COOKBOOK에서 이미 축적된 패턴을 활용하여 접근 범위를 좁힌다. 시니어의 노하우는 도메인 지식에서 온다.
3. **판단이 맞았는지 기록하고 회고하라.** assess의 범위 추정이 실제와 맞았는지, 조사 방향이 적절했는지를 pipeline_feedback으로 남긴다. 잘못된 판단도 기록해야 다음에 더 정확해진다.
4. **파이프라인 자체도 진화한다.** 스킬과 프로세스는 경험에서 자라는 도구이지, 처음부터 완벽한 설계가 아니다. 5건 회고로 불필요한 단계를 제거하고 부족한 단계를 추가한다.

### 매 세션에서 지켜야 할 원칙

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
  → 이슈 타입 분류 + 도메인 파악 (ops-find-domain)
  → 운영 노트 생성 (ops-note-issue)
  → 문제 평가 (ops-assess-issue)
    - 문제 성격 / 영향 범위 / 긴급도 / 조사 전략
    - 여기서 끝나도 됨 (스펙 확인 완료 또는 범위 보고만 필요한 경우)
    - escape hatch: 명백히 단순한 이슈는 생략 가능 (노트에 사유 기록)
  → 기술 조사 (ops-investigate-issue)
    - assess의 전략 기반 가설 수립 → 소거 루프 → 원인 확정
  → [버그 판정 시] 영향 분석 (ops-impact-analyze)
    - 사이드이펙트 + 해결안 + 수정 범위
  → 마감 (ops-close-note → brain 산출물 자동 갱신)
```

## 사용 가능한 스킬

### 이슈 라이프사이클

| 스킬 | 용도 |
|------|------|
| `ops-find-domain` | 이슈 타입 분류 + 도메인 라우팅 — 관련 서브모듈, API 패턴, 쿡북 섹션, 과거 노트 탐색 |
| `ops-note-issue` | Linear 이슈 조회 → operation-notes 문서 생성/업데이트 |
| `ops-assess-issue` | 조사 전 문제 평가 — 성격/범위/긴급도 판단 + 조사 전략 수립 |
| `ops-investigate-issue` | 기술 조사 — 가설 소거 루프 + 근본 원인 파악 (assess 선행 필수) |
| `ops-impact-analyze` | 버그 확정 후 영향 분석 — 사이드이펙트 + 해결안 도출 |
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
