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

#### 3.3 쿡북 추가 대상 사전 판별 (operation-note 소스일 때)

> 이 단계는 Phase 3.5 Triage Gate의 입력으로 사용된다.
> 코드 수정 이슈라도 S1(새 키워드), S2(새 표현) 등 다른 시그널이 있으면 해당 산출물은 갱신된다.

operation-note 또는 Linear 티켓이 입력일 때, 해결 방식에 태그를 붙인다:
- **코드 수정으로 해결** → `resolution:code-fix` — Phase 3.5에서 S3/S4 시그널 제외 (진단 패턴이 코드 변경으로 무의미해짐)
- **운영 대응 / 스펙 확인** → `resolution:ops` — 모든 시그널 대상
- **외부 문서 (Notion/Slack)** → `resolution:external` — 모든 시그널 대상

상세 규칙:
```
Read: .claude/skills/ops-learn/references/cookbook-rules.md
```

### Phase 3.5: Triage Gate — 학습 가치 분류

Phase 3에서 추출된 각 지식 조각을 **"어디에 무엇을 넣을지"** 분류한다.
목적은 쓰레기를 걸러내는 것이 아니라, **각 조각의 정확한 목적지를 결정**하는 것이다.

#### 분류 매트릭스

추출된 각 항목에 대해 해당하는 시그널을 체크한다:

| # | 시그널 | 목적지 | 판별 기준 |
|---|--------|--------|----------|
| S1 | 새 키워드→도메인 매핑 | `d:kw` / `d:syn` 추가 | domain-map.ttl의 기존 `d:kw`에 없는 용어가 라우팅에 기여 |
| S2 | 새 사용자 표현 | `g:*` glossary 추가 | 기존 glossary `d:q`에 없는 자연어 패턴 |
| S3 | 해결 방안 존재 | COOKBOOK 항목 추가/갱신 | 운영 대응·스펙 확인·외부 문서 등 **어떤 형태로든 해결 경로가 있음** |
| S4 | 진단 경로(순서) 존재 | COOKBOOK 플로우 추가/갱신 | 로그 확인 1단계로 끝났더라도 **그 방법이 정답 경로** |
| S5 | 기존 패턴과 동일 | 히트율 +1 / 컨피던스 ↑ | 기존 COOKBOOK 플로우의 트리거·경로와 일치 |
| S6 | 크로스도메인 발견 | `d:x` 관계 추가 | 증상 도메인 ≠ 원인 도메인 |
| S7 | 재사용 SQL 패턴 | COOKBOOK SQL 템플릿 | 조사에 사용한 쿼리가 일반화 가능 |

#### 판정 로직

```
추출된 항목들을 시그널 매트릭스에 대조
  → 각 항목에 해당 시그널 태깅

  S5(기존 패턴 동일)만 해당 → 히트율/컨피던스만 갱신, 새 항목 추가 없음
  S1-S4, S6-S7 중 하나 이상 → 해당 목적지에만 정확히 갱신
  어떤 시그널에도 해당 없음 → SKIP (Phase 4 진행하지 않음)
```

#### SKIP 조건 (학습하지 않는 경우)

다음 **모두**에 해당할 때만 SKIP:
- 추출된 키워드가 이슈 고유명(고객사명, 특정 사번, 티켓번호)뿐임
- 기존 COOKBOOK/glossary에 이미 동일 내용 존재
- 새로운 진단 경로나 해결 방안이 없음 (스펙대로 동작, 추가 인사이트 없음)

> **원칙**: "넣을까 말까"가 아니라 "어디에 무엇을 넣을까"를 결정하는 것이 triage의 역할이다.
> 의심스러우면 SKIP하지 말고 넣되, 목적지를 정확히 지정한다.

#### 결과 포맷

Phase 3.5 완료 후 내부적으로 다음 구조를 확정한다:

```
triage_result:
  signals: [S1, S3, S4]          # 해당하는 시그널 목록
  skip: false
  targets:                        # Phase 4에서 갱신할 산출물과 내용
    glossary: [{term: "...", mapping: "..."}]
    cookbook: [{type: "flow|checklist|sql|case", content: "..."}]
    domain_map: [{field: "d:kw|d:syn|d:x", value: "..."}]
    hit_updates: [{flow_id: "F3", issue: "CI-XXXX"}]
```

SKIP인 경우 Phase 5 결과 보고에 SKIP 사유를 명시한다.

### Phase 4: 산출물 갱신

Phase 3.5의 triage 결과에 따라, **해당하는 산출물만** 아래 순서로 반영한다. domain-map.ttl은 모든 정리가 끝난 후 마지막에 갱신한다.

#### ① GLOSSARY.md (S2 해당 시)

- 새로운 용어 매핑을 해당 도메인 섹션에 추가
- 기존 항목과 중복되면 스킵
- 도메인 섹션이 없으면 신설
- 출처 링크를 도메인 섹션 상단에 기록 (Notion/Slack URL 등)

#### ② COOKBOOK (S3, S4, S5, S7 해당 시)

cookbook-rules.md의 구조와 규칙을 따라, triage 시그널에 따라 갱신한다.

**Tier-1/Tier-2 판단:**
- **새 조사 플로우 추가 (S4)**: COOKBOOK.md(Tier-1)에 추가한다. 히트 기회를 주기 위해 먼저 Tier-1에 배치.
- **과거 사례 상세, SQL 템플릿 (S3, S7)**: `brain/cookbook/{domain-id}.md`(Tier-2)에 추가한다. Tier-2 파일이 없으면 새로 생성.
- **히트 갱신 (S5)**: Tier-1의 해당 플로우 히트 +1, 출처 이슈 추가만 (새 항목 추가 없음).
- **히트 0인 플로우의 Tier-2 강등은 ops-compact의 역할이므로 여기서는 하지 않는다.**

**Tier-1 갱신 (COOKBOOK.md):**
- 진단 체크리스트 추가/보강 (S3)
- 조사 플로우 추가 — 1단계 진단이라도 그 방법이 정답 경로면 기록 (S4)
- 히트 +1 (S5)
- API 스펙/제약 추가
- 변경 이력 테이블에 현재 날짜 + 소스 + 변경 내용 기록

**Tier-2 갱신 (`brain/cookbook/{domain-id}.md`):**
- 과거 사례 상세 추가 (S3)
- SQL 템플릿 추가 (S7)
- Tier-2 파일이 없으면 해당 도메인 섹션 헤더와 함께 새로 생성

```
Read: .claude/skills/ops-learn/references/cookbook-rules.md
```

#### ③ CLAUDE.md 서브모듈 맵 (S1 해당 시)

해당 도메인의 서브모듈 행에 키워드가 비어있으면 추가.
이미 채워져 있고 새 키워드가 있으면 보강.

#### ④ Reference 메모리 (외부 소스일 때만)

Notion/Slack/웹 URL이 소스인 경우, `~/.claude/projects/.../memory/`에 reference 메모리 파일 생성.
로컬 노트나 Linear 티켓은 이미 brain 시스템 내부이므로 별도 메모리 불필요.

#### ⑤ domain-map.ttl (마지막, S1/S2/S5/S6 해당 시)

모든 갱신이 완료된 후:
- **S1**: 도메인 블록의 `d:kw` 에 새 키워드 추가, `d:mod` 에 새 모듈 추가 (있으면)
- **S2**: 도메인 블록의 `d:syn` 에 새 사용자 표현 문장 추가, glossary 블록에 새 항목 추가 (`g:{domain}-{NN}`)
- **S5**: 기존 glossary 항목의 재확인 (히트 근거), `n:{ticket-id}` 의 `d:v` 갱신
- **S6**: 도메인 블록의 `d:x` 에 크로스도메인 관계 추가
- operation-note 소스인 경우: `n:{ticket-id}` 항목의 `d:v` 갱신 (시그널 무관, 항상)

domain-map.ttl이 마지막인 이유: 다른 산출물을 모두 갱신한 후에야 어떤 키워드와 용어가 추가되었는지 확정할 수 있다. 또한 Phase 2에서 라우팅 용도로 먼저 읽었으므로, 쓰기는 마지막에 한번만.

#### ⑥ routing-misses.md 처리 (⑤ 이후)

`brain/routing-misses.md` 에 미처리 항목이 있으면 유형별로 처리한다:

**`miss` / `reject` 행:**
1. "올바른 도메인·값" 칸이 채워진 행을 찾는다
2. 각 행의 "입력 텍스트"에서 키워드를 추출
3. 해당 도메인의 `d:kw` 또는 `d:syn` 에 누락된 키워드가 있으면 추가
4. "올바른 도메인·값"이 비어있는 행은 그대로 유지 (수동 확인 필요)

**`correction` 행:**
1. investigate-issue가 이미 즉시 수정을 완료한 경우가 대부분이다
2. 수정이 실제로 반영되었는지 domain-map.ttl / COOKBOOK.md를 대조 검증한다
3. 미반영된 correction이 있으면 이 시점에 반영한다

**공통:**
- 처리 완료된 행은 테이블에서 **삭제** (처리 이력은 domain-map.ttl 갱신 및 git log로 남음)
- 미처리 행만 남긴다

> ⑥은 소스 갱신과 독립적이므로, 매 ops-learn 실행마다 수행한다.

### Phase 5: 결과 보고

```markdown
## ops-learn 결과

### 소스
- {소스 1}: {타입} — {한 줄 요약}
- {소스 2}: {타입} — {한 줄 요약}

### Triage 판정
| 시그널 | 해당 | 목적지 |
|--------|------|--------|
| S1 새 키워드→도메인 | {✅/—} | {d:kw 추가 내용} |
| S2 새 사용자 표현 | {✅/—} | {glossary 추가 내용} |
| S3 해결 방안 | {✅/—} | {COOKBOOK 항목} |
| S4 진단 경로 | {✅/—} | {COOKBOOK 플로우} |
| S5 기존 패턴 동일 | {✅/—} | {히트 +1 대상} |
| S6 크로스도메인 | {✅/—} | {d:x 관계} |
| S7 SQL 패턴 | {✅/—} | {SQL 템플릿} |

> 판정: **{LEARN/PARTIAL/SKIP}** {SKIP이면 사유}

### 산출물 갱신
| 산출물 | 상태 | 변경 내용 |
|--------|------|----------|
| GLOSSARY.md | {갱신/변경 없음/해당 없음} | {추가된 항목 수} |
| COOKBOOK.md | {갱신/히트 갱신/변경 없음/해당 없음} | {변경 요약} |
| CLAUDE.md | {갱신/변경 없음/해당 없음} | {추가된 키워드} |
| Memory | {생성/해당 없음} | {파일명} |
| domain-map.ttl | {갱신/변경 없음/해당 없음} | {추가된 키워드 수, glossary 수} |
| routing-misses.md | {N건 처리/해당 없음} | {보강된 키워드 요약} |

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
