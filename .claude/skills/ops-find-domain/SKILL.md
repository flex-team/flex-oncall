---
name: find-domain
description: Use when a problem, question, or inquiry needs domain routing — finds relevant domains, submodules, cookbook sections, and past notes from domain-map.ttl. Triggers include '도메인 찾아줘', '어디 봐야 해', '어떤 repo야', or when starting oncall issue triage before investigation.
allowed-tools: Read, Grep, Glob
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

### 1. 라우팅 로직 수행

> **공통 가이드**: `domain-routing.md` 를 반드시 읽고 수행한다.
> ```
> Read: .claude/skills/ops-common/domain-routing.md
> ```
> 매칭 알고리즘(Step 1~5), 가중치 테이블, 동점 처리, 결과 구조가 모두 해당 파일에 정의되어 있다.

**수행 순서:**

1. `brain/domain-map.ttl` 을 Read로 전체 읽기
2. `domain-routing.md` 의 Step 1~5를 순서대로 수행
3. 결과를 아래 출력 포맷으로 렌더링

### 2. 결과 출력

아래 포맷으로 마크다운 출력한다. **빈 섹션은 생략**한다.

```markdown
## 🔍 Domain Routing Result

### Primary: :{domain-id} ({도메인 이름})
- **repo**: {서브모듈 목록, 쉼표 구분}
- **module**: {모듈 목록, 쉼표 구분}
- **cookbook**: "{COOKBOOK 섹션 이름}"

### Related
- :{domain-id} ({도메인 이름}) — `d:x` 연결
  - repo: {서브모듈}

### Glossary Hits
| ID | 사용자 표현 | 시스템 용어 |
|----|------------|-----------|
| {g:id} | {d:q 값} | {d:a 값} |

### Related Notes
| ID | 요약 | verdict | 위치 |
|----|------|---------|------|
| {ticket-id} | {d:s 값} | {d:v 값} | active/archive |
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

어떤 도메인에도 매칭되지 않으면:
1. 입력 텍스트를 그대로 출력
2. "매칭된 도메인이 없습니다" 안내
3. CLAUDE.md의 서브모듈 맵 키워드 테이블을 fallback으로 제시
4. 사용자에게 도메인을 직접 지정하도록 요청
