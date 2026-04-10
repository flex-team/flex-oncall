---
name: assess-issue
description: Use when an oncall issue needs pre-investigation assessment — problem characterization, scope estimation, urgency judgment, and investigation strategy. Triggers include '평가해줘', '얼마나 심각해', '범위 파악', or before starting ops-investigate-issue. Not for technical investigation (use ops-investigate-issue).
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task
argument-hint: <ticket-id> (예: CI-3861)
---

# Assess Issue

## Purpose
조사에 들어가기 전에, 문제의 성격·범위·긴급도를 판단하여 조사 전략을 수립한다.
단편적 유저 해결이 아닌 구조적 접근의 시작점.

> 이 스킬은 v1이다. 실제 이슈 5건 처리 후 회고를 통해 진화시킨다.

## Input
$ARGUMENTS

### Argument Resolution
- `$ARGUMENTS`가 비어있거나 티켓 ID 패턴(`[A-Z]+-\d+`, 예: CI-3861)이 없으면:
  1. 현재 git 브랜치명에서 티켓 ID 패턴을 추출 시도 (예: `fix/CI-3861-some-desc` → `CI-3861`)
  2. 현재 대화 세션에서 언급된 티켓 ID를 추출 시도 (직전 사용자 메시지, 이전에 실행한 커맨드 인자 등)
  3. 브랜치/대화에서 못 찾으면 현재 디렉토리명에서 추출 시도
  4. 찾은 경우: 사용자에게 `"티켓 ID를 {추출한ID}로 인식했습니다. 맞습니까?"` 확인 후 진행
  5. 못 찾은 경우: `"티켓 ID를 특정할 수 없습니다. 티켓 ID를 인자로 전달해주세요. (예: /ops:assess-issue CI-3861)"` 출력 후 **즉시 종료**

### Operation Notes Directory Resolution

operation-notes 파일을 저장할 디렉토리를 아래 우선순위로 결정한다.
**스킬 실행 시작 시 한 번만 해석하고, 이후 모든 경로에 동일하게 적용한다.**

| 우선순위 | 경로 | 설명 |
|---------|------|------|
| 1 | `{repo-root}/brain/notes/` | repo 루트 brain/notes 디렉토리가 존재 |
| 2 | `{repo-root}/.claude/operation-notes/` | .claude 하위에 존재 (서브모듈용) |
| 3 | `~/.claude/operation-notes/` | 글로벌 홈 디렉토리에 존재 |

- 디렉토리 **존재 여부**로 판단한다 (파일이 아닌 디렉토리).
- 셋 다 존재하지 않으면 사용자에게 `"operation-notes 디렉토리를 찾을 수 없습니다. 어디에 저장할까요?"` 로 물어본다.
- 해석된 경로를 이하 `{notes-dir}`로 표기한다.

### Note File Resolution

`{ticket-id}.md` 파일을 찾을 때 아래 순서로 탐색한다:
1. `{notes-dir}/{ticket-id}.md` (active — 진행 중)
2. `{notes-dir}/archive/{ticket-id}.md` (archive — 해결 완료)

- 파일을 **새로 생성**할 때는 항상 `{notes-dir}/` (루트)에 생성한다.
- 이슈가 **해결 완료**되면 `{notes-dir}/archive/`로 이동한다.
- 상대 링크 규칙:
  - 루트 → archive: `./archive/{ticket-id}.md`
  - archive → 루트: `../{ticket-id}.md`
  - archive → archive: `./{ticket-id}.md`

## Procedure

### Step 1: 맥락 수집 + 타입별 사실 검증

operation-note와 Linear 이슈에서 문제의 전체 그림을 파악하고, 이슈 타입에 맞는 사실 검증을 수행한다.

1. operation-note 읽기 (증상, 현재까지 파악된 내용)
2. Linear 이슈 코멘트 확인 (추가 맥락) — MCP CLI로 조회
3. find-domain 결과 활용:
   - domain-routing.md를 읽고 라우팅 수행
   - primary 도메인의 d:cb로 COOKBOOK 섹션 확인
   - 연관 노트 확인
   - **이슈 타입 확인** (Error/Data/Perf/Auth/Spec/Render)

4. 타입별 사실 검증:

   find-domain이 분류한 이슈 타입에 따라, `brain/triage-signals.md` 의 첫 번째 액션을 실행한다.
   이것은 **기본 경로**이며, 상황에 따라 건너뛰거나 순서를 바꿀 수 있다.

   | 타입 | 첫 번째 액션 | 목적 |
   |------|------------|------|
   | Error/Perf/Auth | access log 조회 | HTTP 상태코드, 응답시간, 에러 내용 확인 |
   | Data | DB 상태 확인 | 데이터가 실제로 잘못되어 있는지 |
   | Spec | 코드/스펙 문서 확인 | 의도된 동작인지 판별 |
   | Render | access log → API 정상이면 FE 코드 | API vs FE 문제 구분 |

   각 타입의 상세 검색 조건(OpenSearch 인덱스, 필드)은 `brain/triage-signals.md` 를 참조한다.

   **실행할 수 없을 때의 대안:**

   access log 조회나 DB 확인을 실행할 수 없으면, 코드 분석으로 대체한다:
   - Error/Perf/Auth: 해당 API의 에러 핸들링·응답 패턴을 코드에서 분석 + 로그 검색 조건을 위임 포맷(`delegation-guide.md`)으로 제안
   - Data: Entity 코드 분석으로 데이터 구조 파악 + 확인 쿼리를 위임 포맷으로 제안
   - Render: FE 코드 직접 분석 (컴포넌트·페이지 탐색) + API 응답 확인을 위임 포맷으로 제안
   - 관련 API 엔드포인트의 코드 경로 추적 (Controller → Service → Repository)은 항상 수행

   **이 검증에서 추가로 수행할 것:**
   - 관련 API/코드 식별 → 현재 동작이 의도된 스펙인지 초기 판단
   - 문의 내용 vs 실제 동작 대조 → 문제 정의 보정

   **건너뛰는 조건:**
   - 문제가 이미 명확한 경우 (스크린샷, 에러 메시지 포함 등)
   - 첫 번째 액션의 결과가 이미 노트에 있는 경우
   - 배치/스케줄러 등 백그라운드 처리 이슈 (로그/코드 기반 접근)

   > 표준 플레이북을 알되, 상황에 맞게 적용한다.
   > 이 검증 결과가 Step 2 판단의 근거가 된다.

### Step 2: 핵심 판단 3개

세 가지만 판단한다. 분류표나 매트릭스에 끼워 맞추지 않는다. 자유 서술로 기록하되 판단 근거를 반드시 포함.

**1. 문제 성격**: 이게 뭔가?
- 자유 서술. "값이 잘못 저장된 데이터 이상", "특정 조건에서 로직이 의도와 다르게 동작" 등
- 판단 근거 필수 (코드 위치, 로그 내용 등)

**2. 영향 범위**: 누가 영향받나?
- "1명만 문의했다 ≠ 1명만 영향" — 이 구분이 핵심
- 범위 추정을 위해 COUNT 쿼리를 실행한다. 실행할 수 없으면 Entity 분석으로 쿼리를 구성하고 위임 포맷(`delegation-guide.md`)으로 제안한다.
- 현재 진행형 여부: 지금도 잘못된 데이터가 쌓이고 있는지

**3. 긴급도**: 지금 해야 하나?
- 데이터 계속 오염 중? → 즉시
- 금전적/법적 영향? → 즉시
- 이미 끝난 일회성? → 일반
- 판단 근거와 함께 기록

### Step 3: 조사 방향 잡기

- 쿡북에 매칭되는 플로우가 있는지 확인 (있으면 번호 기록)
- 뭘 먼저 확인할지 1-2줄로 정리
- **여기서 끝나도 됨** — 범위 파악만 필요하거나, 사실 검증에서 스펙임이 확인된 경우
- 스펙 확인으로 조사 없이 종료하는 경우, `## 문제 평가` 섹션에 `**verdict**: \`spec\`` 마커를 기록한다 (investigate 없이 close-note가 최종 결론을 추출할 수 있도록)

### Step 4: operation-note 업데이트

operation-note의 `## 증상` 다음에 `## 문제 평가` 섹션을 추가한다.

출력 형식:
```markdown
## 문제 평가
> assess 완료 — {날짜}

- **도메인**: :{domain-id} ({도메인 이름}) — repo: {서브모듈}
- **이슈 타입**: {Error/Data/Perf/Auth/Spec/Render}

### 성격
{자유 서술 + 근거}

### 영향 범위
{추정 범위 + 진행형 여부}

### 긴급도
{즉시/일반 + 근거}

### 조사 방향
{쿡북 섹션 번호 또는 첫 번째 확인 항목}
```

### Step 5: 사용자 보고 + 다음 단계 안내

평가 결과 요약 보고:
- 핵심 판단 3개 요약
- 다음 단계 안내: `ops-investigate-issue {ticket-id}` 로 기술 조사 진행

## Escape Hatch

증상을 읽고 "설정 확인만으로 끝날 건"이 명백하면 assess를 생략하고 바로 investigate 가능.
단, 생략 시 operation-note에 이유를 기록:
```markdown
## 문제 평가
> assess 생략 — 사유: {이유}
```

## Rules
- 외부 시스템 조회(DB, OpenSearch) 전 사용자 확인 필수
- 실행할 수 없는 조회/검색은 코드 분석으로 대체하고, 그래도 필요한 쿼리는 `delegation-guide.md` 위임 포맷으로 제안
- MCP CLI 호출 전 mcp-cli info로 스키마 확인
- 문서는 한국어로 작성
- 추론/예측과 사실을 명확히 구분
- DB 쿼리 실행은 메인 세션에서 직접 수행 (subagent 위임 금지)

## v1 이후 진화 포인트

이 스킬은 가설이다. 5건 처리 후 회고할 때 확인할 것:
- 성격 분류가 조사 방향 결정에 실제로 도움이 됐는지
- 범위 추정이 정확했는지 (조사 후 실제 범위와 비교)
- 긴급도 판단이 적절했는지
- assess 없이 바로 investigate 했으면 더 빨랐을 케이스가 있는지
