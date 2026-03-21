---
name: find-domain
description: Use when a problem, question, or inquiry needs domain routing — finds relevant domains, submodules, cookbook sections, and past notes from domain-map.ttl. Triggers include '도메인 찾아줘', '어디 봐야 해', '어떤 repo야', or when starting oncall issue triage before investigation.
allowed-tools: Read, Grep, Glob, Edit, Agent
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

### 1. domain-router 에이전트 호출

TTL 파싱과 매칭 알고리즘은 **domain-router 에이전트**에 위임한다.

```
Agent(
  subagent_type: "general-purpose",
  description: "TTL 파싱 및 도메인 라우팅",
  prompt: ".claude/agents/domain-router.md 의 지시를 읽고 따라라. 입력 텍스트: {$ARGUMENTS}"
)
```

에이전트는 compact JSON을 반환한다. TTL 원문은 에이전트 컨텍스트 안에서만 사용되고, 호출자(이 스킬)에게는 결과 JSON만 전달된다.

### 2. 결과 렌더링

에이전트가 반환한 JSON을 아래 마크다운 포맷으로 변환한다. **빈 섹션은 생략**한다.

```markdown
## 🔍 Domain Routing Result

### Primary: :{domain-id} ({도메인 이름}) — score: {점수}
- **repo**: {서브모듈 목록, 쉼표 구분}
- **module**: {모듈 목록, 쉼표 구분}
- **cookbook**: "{COOKBOOK 섹션 이름}"
- **score breakdown**: {d:kw=N, g:q=N, phrase=N, ...}

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

### 3. 다음 단계 안내

결과 출력 후, 사용자에게 다음 단계를 안내한다:

```markdown
### 다음 단계
- 🔍 조사하려면: `/ops-investigate-issue {ticket-id}`
- 📝 노트 만들려면: `/ops-note-issue {ticket-id}`
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
