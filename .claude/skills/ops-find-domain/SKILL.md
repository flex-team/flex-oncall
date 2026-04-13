---
name: find-domain
description: Use when a problem, question, or inquiry needs domain routing — finds relevant domains, submodules, cookbook sections, and past notes from domain-map.ttl. Triggers include '도메인 찾아줘', '어디 봐야 해', '어떤 repo야', or when starting oncall issue triage before investigation.
allowed-tools: Read, Grep, Glob, Edit, Agent, Bash
argument-hint: <문제/질문 텍스트 또는 ticket-id> (예: "세콤 퇴근 정시로 찍혀요", CI-4145)
---

# Find Domain

## Purpose

입력 텍스트(문제/질문/문의)를 `brain/domain-map.ttl` 전체와 대조하여, 관련 도메인·서브모듈·쿡북 섹션·용어집 매칭·과거 노트를 찾아주는 **순수 라우팅 스킬**.

- 서브모듈 checkout, 노트 생성, DB 조회, 코드 변경은 하지 않는다
- 결과를 보고 사용자 또는 후속 스킬이 다음 행동을 결정한다

## Input

$ARGUMENTS

### Argument Resolution

- `$ARGUMENTS`가 비어있으면:
  1. 현재 대화 세션에서 언급된 이슈/질문 텍스트를 추출 시도
  2. 못 찾으면 `"라우팅할 텍스트를 전달해주세요. (예: /ops-find-domain 세콤 퇴근 정시로 찍혀요)"` 출력 후 **즉시 종료**

## Execution

### 1. 이슈 타입 분류

domain-router 에이전트를 호출하기 전에, 입력 텍스트에서 이슈 타입을 판별한다.

`brain/triage-signals.md` 의 키워드/판단 기준을 참조하여 5개 타입 중 하나로 분류:
**Error**(오류형) / **Data**(데이터형) / **Perf**(성능형) / **Auth**(권한형) / **Spec**(스펙질문형)

- 명확한 장애 신호(500, 타임아웃 등)가 있으면 해당 타입 우선
- 모호하면 Spec으로 시작
- 분류가 불가능하면 "미분류"로 표시하고 Fallback 전략 안내

### 2. 매칭 엔진 실행

도메인 매칭은 **Python 스크립트**로 수행한다. TTL 파싱과 2-pass 매칭 알고리즘을 코드로 실행하여 ~100ms 이내에 결과를 반환한다.

```
Bash("python3 brain/scripts/domain_router.py '{$ARGUMENTS}'")
```

스크립트는 JSON을 stdout으로 출력한다. `confidence` 필드로 결과 신뢰도를 판단한다:

- **`high`**: 결과를 바로 Step 3(렌더링)으로 진행
- **`low`**: LLM 폴백 — 스크립트가 반환한 상위 후보를 context로 제공하여 도메인 판단을 요청한다 (아래 참조)
- **`none`**: 매칭 없음 처리 (아래 "매칭 없음" 섹션)

#### LLM 폴백 (confidence=low)

스크립트 결과의 `score_breakdown` 에서 상위 3개 후보와 입력 텍스트를 LLM에 전달한다:

```
Agent(
  subagent_type: "general-purpose",
  model: haiku,
  description: "도메인 라우팅 판단 (폴백)",
  prompt: "다음 입력에 대해 가장 적합한 도메인을 선택하세요.

입력: {입력 텍스트}

후보:
{score_breakdown에서 상위 3개 도메인의 이름, 점수, 키워드 요약}

JSON으로 응답: {\"domain\": \":domain-id\"} 또는 모두 부적합하면 {\"domain\": null}"
)
```

이 폴백은 TTL 전체를 읽지 않고 후보 요약만 전달하므로 기존 대비 훨씬 빠르다.
low confidence이더라도 스크립트가 반환한 primary가 유효하면 그대로 사용해도 된다 — LLM 폴백은 판단이 어려울 때만 활용.

### 3. 결과 렌더링

에이전트가 반환한 JSON을 아래 마크다운 포맷으로 변환한다. **빈 섹션은 생략**한다.

```markdown
## 🔍 Domain Routing Result

[분류] {타입 한국어} ({타입 영어})
[첫 번째 액션] {triage-signals.md 해당 타입의 "첫 번째 액션"}

### Primary: :{domain-id} ({도메인 이름}) — score: {점수}
- **repo**: {서브모듈 목록, 쉼표 구분}
- **module**: {모듈 목록, 쉼표 구분}
- **cookbook**: "{COOKBOOK 섹션 이름}"
- **context**: `cookbook/{domain-id}.md#도메인-컨텍스트` (존재하면)
- **score breakdown**: {d:kw=N, g:q=N, phrase=N, ...}

### 관련 API 패턴
- {d:api 값들, 줄바꿈 구분}
  → access log 검색 시 `request_uri` 필터로 바로 활용 가능
  → OpenSearch 인덱스: `flex-app.be-*` (Error/Perf/Auth 타입일 때)

### Related
- :{domain-id} ({도메인 이름}) — `d:x` 연결
  - repo: {서브모듈}

### Glossary Hits
| ID | 사용자 표현 | 시스템 용어 |
|----|------------|-----------|
| {g:id} | {question} | {answer} |

### Related Notes
| ID | 요약 | verdict | 위치 |
|----|------|---------|------|
| {ticket-id} | {summary} | {verdict} | active/archive |
```

### 4. 다음 단계 안내

결과 출력 후, 사용자에게 다음 단계를 안내한다:

```markdown
### 다음 단계
- 📝 노트 만들려면: `/ops-note-issue {ticket-id}`
- 📋 문제 평가하려면: `/ops-assess-issue {ticket-id}`
- 🔍 (평가 후) 조사하려면: `/ops-investigate-issue {ticket-id}`
- 📖 쿡북 확인: `brain/COOKBOOK.md` > "{cookbook 섹션명}"
- 📂 서브모듈 갱신: `git submodule update --init --recursive {repo-path}`
```

## 매칭 없음

에이전트 JSON의 `no_match` 가 `true` 이면:
1. 입력 텍스트를 그대로 출력
2. "매칭된 도메인이 없습니다" 안내
3. CLAUDE.md의 서브모듈 맵 키워드 테이블을 fallback으로 제시
4. 사용자에게 도메인을 직접 지정하도록 요청
5. **미스 로그에 기록** (아래 "미스 로그" 섹션 참조)

## 피드백 로그

라우팅 실패/거부를 `brain/routing-misses.md` 에 기록하여, `ops-learn` 이 키워드를 자동 보강하는 데 활용한다.
(코드 대조 불일치(correction)는 `ops-investigate-issue`가 기록한다.)

### 기록 조건

다음 **두 가지** 상황에서 로그를 기록한다:

1. **매칭 없음 (`miss`)**: 어떤 도메인에도 스코어가 발생하지 않았을 때
2. **사용자 거부 (`reject`)**: 결과를 출력했으나 사용자가 "아니야", "다른 도메인인데" 등으로 결과를 거부했을 때

### 기록 방법

`brain/routing-misses.md` 의 `## 로그` 테이블 마지막 행에 추가한다:

```
| {YYYY-MM-DD} | miss | {입력 텍스트 원문} | {사용자가 지정한 도메인 또는 빈칸} | {왜 실패했는지 한 줄} |
| {YYYY-MM-DD} | reject | {입력 텍스트 원문} | {사용자가 지정한 올바른 도메인} | {거부 사유} |
```

- 날짜는 KST 기준
- 사용자가 도메인을 직접 지정했으면 "올바른 도메인·값" 칸에 기록
- 사용자가 지정하지 않았으면 빈칸으로 남김
