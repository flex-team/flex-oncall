# Brain — 온콜 지식 관리 시스템

## 핵심 원칙

- 이 repo는 도메인 스펙을 관리하지 않는다. 스펙은 각 서브모듈 repo에 있다.
- brain/ 은 도메인 간 관계, 라우팅, 운영 절차만 관리한다.
- specs/ 디렉토리를 만들지 않는다.

## 설계 의도

### 왜 TTL인가
- RDF/Turtle은 주어-술어-목적어 트리플로 도메인 간 관계를 자연스럽게 표현한다
- 텍스트 기반이라 git diff가 명확하고, AI가 직접 읽고 쓸 수 있다
- 별도 DB 없이 파일 하나로 지식 그래프를 유지할 수 있다

### 왜 COOKBOOK은 2계층인가
- Tier-1 (COOKBOOK.md): 이슈 접수 시 빠르게 스캔하는 진입점. 히트율로 정렬.
- Tier-2 (cookbook/*.md): 특정 도메인 깊이 조사 시 참조. 도메인 컨텍스트, SQL 템플릿, 과거 사례.
- 하나로 합치면 토큰 비용 과다, 셋 이상으로 나누면 라우팅 복잡도 증가.

### 왜 도메인 스펙을 이 repo에 넣지 않는가
- 스펙의 단일 소스(single source of truth)는 각 서브모듈 repo의 코드와 테스트이다.
- 이 repo에 스펙을 복사하면 반드시 부패한다. 코드 변경 시 동기화가 보장되지 않으므로.
- 대신 "왜 이런 스펙인지"(배경, 법적 근거)는 cookbook 도메인 컨텍스트에 기록한다. 이 지식은 코드 변경과 무관하게 유효하다.

### 왜 메트릭을 쌓는가
- 지식 관리 시스템이 실제로 효과가 있는지 검증하기 위함이다.
- 만들기만 하고 측정하지 않으면 복잡성만 증가한다.
- 스킬 사용 패턴, 조사 효율, 지식 신선도를 추적하여 데이터 기반으로 튜닝한다.

## 디렉토리 구조

```
brain/
├── CLAUDE.md              # 이 파일
├── domain-map.ttl         # 중앙 도메인 지도 (Turtle/RDF)
├── COOKBOOK.md             # Tier-1: 진단 체크리스트 + 조사 플로우 + 레퍼런스
├── cookbook/               # Tier-2: 도메인별 SQL 템플릿 + 과거 사례
│   └── {domain-id}.md
├── ontology.md            # domain-map.ttl 작성 규칙
├── routing-misses.md      # 라우팅 미스 로그 (ops-learn이 소비)
└── notes/                 # 이슈 노트
    ├── {ticket-id}.md
    └── archive/
```

## 문서 참조 우선순위

1. **domain-map.ttl** — 도메인 특정 + 관련 문서 찾기 (용어집 `g:*` 블록 포함)
2. **COOKBOOK.md** — 진단 플로우 (히트율 순, 가장 먼저 시도)
3. **cookbook/{domain}.md** — 도메인 컨텍스트(있으면) + SQL 템플릿 + 과거 사례
4. **notes/** — 과거 이슈 상세

## 이슈 대응 워크플로우

```
이슈 인입 (Linear/Slack)
  → domain-map.ttl에서 키워드 + 용어집(g:*)으로 도메인 특정 및 용어 변환
  → COOKBOOK.md에서 진단 플로우 확인 (히트율 순)
  → 필요한 서브모듈만 recursive update
  → 조사 수행 → 노트 기록
  → 해결 완료 시 → close-note로 전체 갱신
```

## 노트 파일 규칙

### 파일 위치

- 새 노트: `brain/notes/{ticket-id}.md` (루트)에 생성
- 해결 완료 시: `git mv brain/notes/{ticket-id}.md brain/notes/archive/` 로 이동
- 연관 이슈 탐색: `notes/` 루트의 active 노트만 전체 스캔. archive는 `domain-map.ttl` 로 찾기

### 파일 네이밍

- `{ticket-id}.md` (예: `CI-1234.md`)

### 파일 템플릿

```markdown
# {ticket-id}: {제목}

## 증상

- 사용자 보고 내용, 에러 로그, 재현 조건 등

## 원인 분석

- 조사 과정과 발견 사항

## 해결

- 수행한 조치 (코드 수정, 데이터 패치, 설정 변경 등)
- PR 링크 (있으면)

## 비고

- 관련 이슈 링크
- 향후 주의사항

## 각주

- 참고한 슬랙 스레드, 문서 링크 등

## Claude 활동 로그 (선택)

> ⚠️ 활동 로그는 `metrics/{user}/{date}.jsonl` 에서 자동 수집되므로 노트에 작성하지 않아도 된다.
> `ops-close-note` Phase 3(정제)에서 기존 활동 로그는 제거된다.
```

### 농축 규칙

close-note(Phase 3) 또는 ops-compact에서 archive 이전에 수행한다:

1. **사용자 표현 흡수**: 노트 "증상"의 문의 표현 → domain-map.ttl `d:syn` (새로운 것만)
2. **키워드 흡수**: 유효한 진단 키워드 → domain-map.ttl `d:kw` (도메인 고유 용어만)
3. **COOKBOOK 보강**: 재사용 가능한 원인 패턴 → COOKBOOK 플로우 등록/보강
4. **상태 설정**: domain-map.ttl의 `n:{ticket-id}` 에 `d:st "C"` + `d:ca "YYYY-MM-DD"` 추가

농축 완료 후 노트 정제:
- 제거: Claude 활동 로그, 소거된 가설, DB 원시 데이터, 상세 코드 트레이스
- 유지: 증상 요약, 확정 원인, 해결 조치, PR 링크, Gherkin

### 상대 링크 규칙

- 루트 → archive 참조: `./archive/{ticket-id}.md`
- archive → 루트 참조: `../{ticket-id}.md`
- archive → archive 참조: `./{ticket-id}.md`

## 운영 업무 진행 절차

### 1. 티켓 확인

- Linear 이슈 내용을 읽고 증상을 정리한다.
- domain-map.ttl 키워드 매칭으로 도메인을 특정한다.
- domain-map.ttl g:* 블록에서 사용자 표현을 시스템 용어로 변환한다.

### 2. 분석 기록

- 노트 파일을 생성하고 증상 섹션을 작성한다.
- domain-map.ttl에 노트 항목을 추가한다 (verdict: `"investigating"`).

### 3. 원인 조사

- COOKBOOK.md에서 해당 도메인 진단 플로우를 먼저 확인한다.
- API 이슈일 때: **가설 세우기 전에 access log부터 확인**하여 요청/응답을 파악한다.
- 필요한 서브모듈만 `git submodule update --recursive` 로 갱신한다.
- DB, OpenSearch, Kafka 등 조사 도구를 활용한다.

### 4. 해결

- 코드 수정이 필요하면 해당 서브모듈 repo에서 PR을 생성한다.
- 운영 조치(데이터 패치 등)는 노트에 상세히 기록한다.
- 노트의 해결 섹션을 업데이트한다.

### 5. 회고

- close-note 스킬로 노트를 마감한다.
  - verdict 확정
  - domain-map.ttl 갱신
  - COOKBOOK.md 갱신 (재사용 가능한 진단 패턴 발견 시)
  - 노트를 archive로 이동

## 자동 갱신 규칙

### ops 스킬 실행 시

| 스킬 | domain-map.ttl | COOKBOOK.md | 노트 |
|------|---------------|------------|------|
| `note-issue` | 노트 항목 추가 | ops-learn 갱신 | 생성/갱신 |
| `investigate-issue` | 노트 항목 추가 | ops-learn 갱신 | 생성/갱신 |
| `close-note` | verdict 확정 | ops-learn 갱신 | archive 이동 |
| `fix-issue` | - | - | 갱신 |
| `ops-learn` | 키워드/glossary 갱신 | 진단 패턴 갱신 | - |
| `maintain-notes` | ops-learn/재구축 | ops-learn/재구축 | 일괄 정리 |

### domain-map.ttl 갱신 시점

- 노트 생성: `n:{ticket-id}` 트리플 추가
- 노트 마감: `d:v` 를 확정 verdict로 변경
- 새 도메인 발견: 도메인 블록 추가
- 새 용어 발견: 용어 블록 추가
- cross-domain 관계 발견: `d:x` 추가

## domain-map.ttl 작성 규칙

상세 규칙은 `ontology.md` 를 참조한다.

## Claude 활동 로그

활동 로그는 각 노트 최하단에 기록한다. 전체 활동 메트릭은 `metrics/{user}/{date}.jsonl` 에 자동 수집되며, `ops-compact` 실행 시 on-demand 집계된다.

### 로그 형식

```markdown
## Claude 활동 로그

| 시각(KST) | 활동 |
|-----------|------|
| 2026-03-19 09:00 | 이슈 조사 시작 |
| 2026-03-19 09:15 | DB 조회로 원인 파악 |
| 2026-03-19 09:30 | PR 생성 완료 |
```

- 시각은 항상 KST(UTC+9) 기준이다.
- 주요 활동 전환점만 기록한다 (모든 명령어를 기록하지 않는다).
