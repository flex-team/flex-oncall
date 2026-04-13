---
name: find-domain
description: Use when a problem, question, or inquiry needs domain routing — finds relevant domains, submodules, cookbook sections, and past notes from domain-map.ttl. Triggers include '도메인 찾아줘', '어디 봐야 해', '어떤 repo야', or when starting oncall issue triage before investigation.
allowed-tools: Bash, Agent, Edit
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

### 1. 이슈 텍스트 확보

입력이 티켓 ID 형식(CI-1234, TT-567 등)이면:
1. Linear MCP로 이슈 조회
2. title + description을 결합하여 "라우팅 텍스트"로 사용

평문이면 그대로 "라우팅 텍스트"로 사용한다.

### 2. 매칭 엔진 실행

Python 스크립트가 JSON으로 매칭 결과를 반환한다.
티켓 ID가 있으면 `--ticket` 으로 전달한다.

```
Bash("python3 brain/scripts/domain_router.py --ticket={ticket-id} '{라우팅 텍스트}'")
```

### 3. 결과 처리

JSON 응답의 `confidence` 필드로 분기한다:

- `"high"` 또는 `"low"` → 렌더링 단계로 진행
- `"low"` → 추가로 haiku 폴백 실행 (아래 참조) 후 렌더링
- `"none"` → 매칭 없음 처리 (아래 참조)

### 4. 렌더링

JSON 데이터를 기반으로 상황에 맞게 마크다운으로 렌더링한다.

**항상 포함:**
- triage 분류 (`[분류]`, `[첫 번째 액션]`)
- primary 도메인: 도메인 ID, 이름, repo, module, cookbook
- related 도메인: 도메인 ID, 이름, repo

**선택 포함 (데이터가 있을 때):**
- glossary_hits — 상위 3개
- related_notes — 상위 5개
- API 패턴 (primary의 `apis` 필드)
- 다음 단계 안내 (ticket ID가 있을 때)

**생략:**
- score_breakdown (내부 디버깅용, 사용자에게 불필요)

### confidence=low 폴백

JSON의 `score_breakdown`에서 상위 3개 후보를 haiku 서브에이전트에 전달한다:

```
Agent(
  subagent_type: "general-purpose",
  model: "haiku",
  description: "도메인 라우팅 판단 (폴백)",
  prompt: "다음 입력에 대해 가장 적합한 도메인을 선택하세요.

입력: {라우팅 텍스트}

후보:
{score_breakdown에서 상위 3개 도메인의 이름, 점수, 키워드 요약}

JSON으로 응답: {\"domain\": \":domain-id\"} 또는 모두 부적합하면 {\"domain\": null}"
)
```

판단 결과를 반영하여 primary 도메인을 교체한 뒤 렌더링한다.
low confidence이더라도 스크립트가 반환한 primary가 유효하면 그대로 사용해도 된다.

### 매칭 없음

JSON의 `no_match`가 true이면:
1. "매칭된 도메인이 없습니다" + 입력 텍스트 출력
2. `brain/routing-misses.md` 의 `## 로그` 테이블에 miss 행 추가:
   `| {YYYY-MM-DD} | miss | {라우팅 텍스트} | | {실패 사유} |`

## 피드백 로그 (사용자 거부)

결과 출력 후 사용자가 "아니야", "다른 도메인인데" 등으로 거부하면, `brain/routing-misses.md` 의 `## 로그` 테이블에 추가한다:

```
| {YYYY-MM-DD} | reject | {입력 텍스트 원문} | {사용자가 지정한 올바른 도메인} | {거부 사유} |
```

- 날짜는 KST 기준
- 사용자가 도메인을 직접 지정했으면 "올바른 도메인" 칸에 기록
- 사용자가 지정하지 않았으면 빈칸으로 남김
