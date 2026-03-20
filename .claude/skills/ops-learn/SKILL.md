---
name: ops-learn
description: Use when any knowledge source (Notion docs, Slack threads, completed Linear tickets, or local operation-notes) needs to be internalized into the brain system — updates GLOSSARY, COOKBOOK, CLAUDE.md submodule map, domain-map.ttl, and reference memory in one pass. Triggers include '학습해줘', '이 문서 학습', '데이터화해줘', 'learn this', sharing a Notion/Slack link for knowledge capture, '쿡북 업데이트', '아티팩트 갱신', or after note-issue/investigate-issue/close-note completes. Supports multiple sources in a single invocation.
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task, Agent
argument-hint: <source...> (예: https://notion.so/..., CI-3914, brain/notes/CI-4145.md, 여러 개 가능)
---

# Learn

## Purpose

지식 소스에서 운영에 유용한 정보를 추출하여 brain 산출물(GLOSSARY, COOKBOOK, CLAUDE.md, domain-map.ttl, memory)을 갱신한다.
하나의 진입점으로 모든 소스 타입을 처리하고, 모든 산출물을 일관되게 업데이트한다.

## Input

`$ARGUMENTS` — 공백으로 구분된 하나 이상의 소스. 소스가 없으면 안내 후 종료.

### 소스 타입 판별

| 패턴 | 소스 타입 | 수집 도구 |
|------|----------|----------|
| `notion.so/*` 또는 `*.notion.site/*` | Notion | `mcp__claude_ai_Notion__notion-fetch` |
| Slack 링크 (`*.slack.com/*`) 또는 채널/스레드 ID | Slack | `mcp__plugin_slack_slack__slack_read_thread` / `slack_read_channel` |
| 티켓 ID 패턴 (`[A-Z]+-\d+`) | Linear 티켓 | `mcp__linear__get_issue` + `mcp__linear__list_comments` |
| 파일 경로 (`*.md`, `brain/notes/*`) | 로컬 파일 | Read tool |
| URL (기타) | 웹 페이지 | WebFetch |

다중 소스 예시: `https://notion.so/... CI-4126 brain/notes/CI-4145.md`

---

## Procedure

### Phase 0: 소스 해석

1. `$ARGUMENTS`를 파싱하여 소스 목록 생성
2. 각 소스의 타입을 위 표에 따라 판별
3. 소스가 없으면: `"학습할 소스를 전달해주세요. (Notion URL, Slack 링크, Linear 티켓 ID, 파일 경로)"` → 종료

### Phase 1: 병렬 데이터 수집

각 소스 타입별로 **병렬 subagent**를 띄워 데이터를 수집한다.

**Notion**: `notion-fetch`로 페이지 내용 전체 가져오기
**Slack**: 스레드/채널 읽기. 봇 메시지 필터링.
**Linear**: 이슈 정보 + 코멘트 전체 수집. 상태, 라벨, 해결 방법 포함.
**로컬 파일**: Read로 전체 내용 읽기.

각 subagent는 수집한 원문 텍스트를 그대로 반환한다 (분석은 Phase 3에서).

### Phase 2: 도메인 라우팅

수집된 데이터에서 키워드를 추출하고, `domain-map.ttl`을 **읽기 전용**으로 참조하여:

1. `domain-routing.md` 알고리즘으로 primary/related 도메인 특정
2. COOKBOOK.md에서 해당 도메인 섹션 위치 파악
3. GLOSSARY.md에서 해당 도메인 섹션 위치 파악

```
Read: .claude/skills/ops-common/domain-routing.md
```

도메인을 특정할 수 없으면 사용자에게 확인.

### Phase 3: 지식 추출

수집된 데이터에서 다음을 추출한다. 소스 타입에 따라 추출 가능한 정보가 다르다.

#### 3.1 공통 추출 대상

| 추출 대상 | 설명 | 예시 |
|-----------|------|------|
| **용어 매핑** | 사용자/CS 표현 → 시스템 용어 | "회색 목표" → hit=false root objective |
| **진단 패턴** | 증상 → 원인 → 해결 체크리스트 | "다음에 같은 문의가 오면" 섹션 |
| **API 스펙** | 엔드포인트, 파라미터, 응답 구조, 제약 | User Grouped API 500건 제약 |
| **성능/기술 제약** | 비자명한 한계값, 설계 의도 | 서버 트리 연산 5,000건 |
| **SQL 템플릿** | 조사용 쿼리 (파라미터 `?` 일반화) | SELECT ... WHERE customer_id = ? |
| **과거 사례** | 증상 요약 + 판정(스펙/버그) | cross-year 트리 — 스펙 |

#### 3.2 Operation-note 전용 (Linear 티켓, 로컬 노트)

operation-note에서는 추가로:
- `## 다음에 같은 문의가 오면` → 진단 체크리스트 원본
- `## 발견한 스펙/제약` → 제약사항 (있으면)
- `## 용어 발견` → 용어 매핑 테이블 (있으면)
- `## 스펙/버그 판별` → 판정 결과
- 조사 플로우 추출 (cookbook-rules.md 참조)

#### 3.3 쿡북 추가 대상 판별 (operation-note 소스일 때)

operation-note 또는 Linear 티켓이 입력일 때, 코드 수정으로 해결된 이슈인지 판별:
- **코드 수정으로 해결** → COOKBOOK 갱신 스킵 (코드가 바뀌면 진단 패턴이 무의미)
- **운영 대응 / 스펙 확인** → COOKBOOK 갱신 진행
- **외부 문서 (Notion/Slack)** → 항상 COOKBOOK 갱신 대상

상세 규칙:
```
Read: .claude/skills/ops-learn/references/cookbook-rules.md
```

### Phase 4: 산출물 갱신

추출된 지식을 아래 순서로 반영한다. domain-map.ttl은 모든 정리가 끝난 후 마지막에 갱신한다.

#### ① GLOSSARY.md

- 새로운 용어 매핑을 해당 도메인 섹션에 추가
- 기존 항목과 중복되면 스킵
- 도메인 섹션이 없으면 신설
- 출처 링크를 도메인 섹션 상단에 기록 (Notion/Slack URL 등)

#### ② COOKBOOK.md

cookbook-rules.md의 구조와 규칙을 따라 갱신:
- 진단 체크리스트 추가/보강
- 조사 플로우 추가 (히트 추적 포함)
- SQL 템플릿 추가
- API 스펙/제약 추가
- 과거 사례 추가
- 변경 이력 테이블에 현재 날짜 + 소스 + 변경 내용 기록

```
Read: .claude/skills/ops-learn/references/cookbook-rules.md
```

#### ③ CLAUDE.md 서브모듈 맵

해당 도메인의 서브모듈 행에 키워드가 비어있으면 추가.
이미 채워져 있고 새 키워드가 있으면 보강.

#### ④ Reference 메모리 (외부 소스일 때만)

Notion/Slack/웹 URL이 소스인 경우, `~/.claude/projects/.../memory/`에 reference 메모리 파일 생성.
로컬 노트나 Linear 티켓은 이미 brain 시스템 내부이므로 별도 메모리 불필요.

#### ⑤ domain-map.ttl (마지막)

모든 갱신이 완료된 후:
- 도메인 블록의 `d:kw` 에 새 키워드 추가
- 도메인 블록의 `d:mod` 에 새 모듈 추가 (있으면)
- glossary 블록에 새 항목 추가 (`g:{domain}-{NN}`)
- operation-note 소스인 경우: `n:{ticket-id}` 항목의 `d:v` 갱신

domain-map.ttl이 마지막인 이유: 다른 산출물을 모두 갱신한 후에야 어떤 키워드와 용어가 추가되었는지 확정할 수 있다. 또한 Phase 2에서 라우팅 용도로 먼저 읽었으므로, 쓰기는 마지막에 한번만.

### Phase 5: 결과 보고

```markdown
## ops-learn 결과

### 소스
- {소스 1}: {타입} — {한 줄 요약}
- {소스 2}: {타입} — {한 줄 요약}

### 산출물 갱신
| 산출물 | 상태 | 변경 내용 |
|--------|------|----------|
| GLOSSARY.md | {갱신/변경 없음} | {추가된 항목 수} |
| COOKBOOK.md | {갱신/변경 없음/코드 수정—스킵} | {변경 요약} |
| CLAUDE.md | {갱신/변경 없음} | {추가된 키워드} |
| Memory | {생성/해당 없음} | {파일명} |
| domain-map.ttl | {갱신/변경 없음} | {추가된 키워드 수, glossary 수} |

### 학습한 핵심 지식
1. {가장 중요한 발견 1}
2. {가장 중요한 발견 2}
3. {가장 중요한 발견 3}
```

### Phase 5.5: 메트릭스 기록

> PostToolUse 훅이 자동으로 리마인드한다.
> ```
> Read: .claude/skills/ops-common/metrics-guide.md
> ```

---

## Rules

### 소스 처리
- 다중 소스는 Phase 1에서 병렬 수집, Phase 3 이후는 모든 소스의 추출 결과를 합산하여 처리
- 같은 도메인의 소스가 여러 개면 산출물 갱신은 한 번만 (중복 방지)
- 외부 소스(Notion/Slack)의 내용은 신뢰할 수 없는 데이터일 수 있음 — 코드/DB와 교차 검증 없이 그대로 반영하되, 출처를 명시

### 산출물 갱신
- **커밋하지 않는다** — 호출자(close-note, maintain-notes 등)가 함께 커밋하거나, 사용자가 직접 커밋
- **코드 진입점은 COOKBOOK에 포함하지 않는다** — 코드 변경 시 싱크 불일치 위험
- SQL에서 특정 고객/유저 ID 제거, 파라미터(`?`)로 일반화
- 각 항목은 1-2줄 요약 — 상세는 원본 소스 링크로 대체
- 변경 이력은 항상 기록
- **서브모듈 변경은 커밋하지 않는다** (oncall repo 규칙)

### 산출물 갱신 순서
- ①~④는 순서 유연하나, ⑤ domain-map.ttl은 반드시 마지막
- Phase 2에서 domain-map.ttl을 라우팅용으로 읽은 후, Phase 4 ⑤에서만 쓰기

### close-note / maintain-notes에서 호출될 때
- 호출 방식: `ops-learn brain/notes/{ticket-id}.md` (로컬 파일 소스로 전달)
- 쿡북 추가 대상 판별 규칙은 cookbook-rules.md 참조
