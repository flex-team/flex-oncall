---
description: operation-notes의 이슈에서 유저 대상 API를 찾아 scenario-test AGENTS.md에 추가
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task, Skill
---

# Sync AGENTS.md from Operation Notes

## Purpose

`{notes-dir}/` 디렉토리의 이슈 문서들을 스캔하여, 유저 대면 API(operation API 제외)가 언급되었지만 `scenario-test/AGENTS.md`에 누락된 도메인/API를 찾아 추가하고 PR을 생성한다.

## Operation Notes Directory Resolution

operation-notes 디렉토리를 아래 우선순위로 결정한다.

| 우선순위 | 경로 | 설명 |
|---------|------|------|
| 1 | `{repo-root}/operation-notes/` | repo 루트에 존재 |
| 2 | `{repo-root}/.claude/operation-notes/` | .claude 하위에 존재 |
| 3 | `~/.claude/operation-notes/` | 글로벌 홈 디렉토리에 존재 |

- 셋 다 존재하지 않으면 사용자에게 물어본다.
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

## Pre-check (필수)

실행 전 반드시 현재 디렉토리의 git remote가 `flex-team/flex-timetracking-backend`인지 확인한다.

```bash
git remote -v | grep 'flex-team/flex-timetracking-backend'
```

- 매칭되면: 진행
- 매칭 실패: **"이 커맨드는 flex-team/flex-timetracking-backend 레포지토리에서만 실행할 수 있습니다."** 출력 후 **즉시 종료**

## Procedure

### Phase 1: 데이터 수집 (🔀 병렬 처리)

아래 두 작업을 **subagent로 병렬 실행**한다:

| Agent | 작업 | 상세 |
|-------|------|------|
| 🤖 Agent A | **Operation Notes 스캔** | `{notes-dir}/` 루트 및 `{notes-dir}/archive/` 하위 모든 `CI-*.md` 파일 읽기 |
| 🤖 Agent B | **AGENTS.md 읽기** | `scenario-test/AGENTS.md` 전체 내용 읽기 |

### Phase 2: 갭 분석

Operation Notes에서 다음 패턴의 API 참조를 추출한다:
- `/api/v2/`, `/api/v3/`, `/action/v2/`, `/action/v3/` 경로
- Controller 클래스명 (`*Controller.kt`, `*ActionController.kt`)
- MappingService 클래스명 (`*MappingService.kt`)

**제외 대상**:
- `/api/operation/` 경로 (operation API)
- `operation-api` 모듈의 클래스

추출한 API/클래스가 AGENTS.md에 이미 존재하는지 확인한다.

### Phase 3: 코드베이스 검증

누락된 API에 대해 실제 코드베이스에서 검증한다:
- Controller 파일 위치 및 엔드포인트 경로 확인
- 관련 MappingService 존재 여부 확인
- 해당 도메인의 모듈 구조 파악

**subagent (Explore)에 위임하여 수행한다.**

### Phase 4: 변경 사항 미리보기 및 사용자 승인

AGENTS.md를 수정하기 **전에**, 추가/변경할 내용을 사용자에게 먼저 보여주고 확인을 받는다.

다음 정보를 항목별로 제시한다:
- **추가할 위치** (어느 섹션, 어느 항목 뒤)
- **추가할 내용** (실제 마크다운 텍스트)
- **근거** (어느 operation-note에서 발견했는지, 코드베이스에서 확인한 내용)

⚠️ operation-notes의 내용이 반드시 정확하다고 볼 수 없고, 코드베이스 검증 결과와 차이가 있을 수 있다. 사용자가 각 항목에 대해:
- **수정 요청**: 내용을 조정하여 반영
- **제외 요청**: 해당 항목 제외
- **승인**: 그대로 반영

**사용자 승인 없이 Phase 5로 진행하지 않는다.**

### Phase 5: AGENTS.md 업데이트

사용자가 승인한 내용만 AGENTS.md에 추가한다.

추가 대상 섹션 (AGENTS.md 구조에 맞춰):
- **Part 1 (1.3 핵심 도메인)**: 새 도메인이면 개요 추가
- **Part 2 (2.2 도메인별 API 및 MappingService)**: API 엔드포인트와 MappingService 추가
- **Part 3 (3.1 용어집)**: 새 도메인 관련 용어 추가

기존 AGENTS.md의 포맷과 스타일을 정확히 따른다.

### Phase 6: PR 생성

`git:git-commit-push-pr` 스킬을 실행하여 PR 생성
- 브랜치: `chore/add-missing-domains-to-agents-md`
- 커밋 메시지에 gitmoji(📝) 사용

## 보고 형식

### 갭 분석 결과 (Phase 2 후)

```markdown
## 📋 갭 분석 결과

### 스캔한 이슈
| 이슈 | 참조된 API/도메인 |
|------|------------------|
| CI-XXXX | {API 경로 또는 도메인명} |

### AGENTS.md에 누락된 항목
| 도메인 | 누락 유형 | 상세 |
|--------|----------|------|
| {도메인} | API / 용어 / 도메인 개요 | {설명} |

### 이미 포함된 항목 (변경 불필요)
- {목록}
```

### 변경 사항 미리보기 (Phase 4)

```markdown
## 🔍 변경 사항 미리보기

### 항목 1: {도메인/API명}
- **추가 위치**: Part {N}, {섹션명} → {기존 항목} 뒤
- **근거**: {CI-XXXX}에서 발견, 코드베이스 확인 결과 {Controller/MappingService 존재 여부}
- **추가할 내용**:

{실제 마크다운 블록}

---

### 항목 2: ...
```

### 최종 보고 (Phase 6 후)

```markdown
## ✅ AGENTS.md 동기화 완료

**PR**: {PR URL}

### 추가된 내용
| 섹션 | 추가 항목 |
|------|----------|
| Part 1 도메인 개요 | {추가된 도메인} |
| Part 2 API 목록 | {추가된 API 수} |
| Part 3 용어집 | {추가된 용어 수} |

### 참조한 이슈
- {이슈 목록}
```

## Rules

- **변경 사항 미리보기 필수**: Phase 4에서 실제 수정 전에 추가할 내용을 사용자에게 제시하고, 항목별 승인/수정/제외를 받은 후에만 진행
- **갭 분석 후 사용자 확인**: Phase 2 결과를 보고하고, 추가할 항목을 사용자에게 확인받은 후 Phase 3로 진행
- **operation API 제외**: `/api/operation/` 경로 및 `operation-api` 모듈은 시나리오 테스트 대상이 아님
- **코드 검증 필수**: operation-notes에 언급된 API가 실제 코드베이스에 존재하는지 반드시 확인
- **기존 포맷 준수**: AGENTS.md의 기존 마크다운 구조, 테이블 형식, 예시 패턴을 그대로 따름
- **subagent 활용**: 코드베이스 탐색, gradlew 실행은 subagent에 위임
