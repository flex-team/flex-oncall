---
description: note-issue + update-cookbook 증분을 한번에 처리하는 통합 커맨드
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task
argument-hint: <ticket-id> (예: CI-3861)
---

# Capture Issue

## Purpose
이슈 번호 하나로 **note-issue + update-cookbook 증분**을 한번에 처리한다.
Linear 데이터 수집 → operation-note 생성/업데이트 → COOKBOOK 증분 반영까지 자동 진행.

개별 커맨드(`note-issue`, `update-cookbook`)는 그대로 유지되며, 이 커맨드는 둘을 오케스트레이션한다.

## Input
$ARGUMENTS

### Argument Resolution
`note-issue.md`의 Argument Resolution 규칙을 그대로 따른다:
- 티켓 ID 패턴(`[A-Z]+-\d+`)이 있으면 사용
- 없으면 git 브랜치명 → 대화 세션 컨텍스트 → 디렉토리명 순으로 추출 시도
- 못 찾으면 안내 후 즉시 종료

## Procedure

### Phase 1: Operation Note 생성/업데이트

`commands/ops/note-issue.md`를 읽고 **Step 1~6을 그대로 수행**한다.

```
Read: .claude/commands/ops/note-issue.md
```

수행 범위:
- Step 1-2: 데이터 수집 (Linear 이슈 + 연관 이슈 탐색, 병렬)
- Step 3: 문서 생성 또는 업데이트
- Step 4: Gherkin 시나리오 작성 (해결 완료 시)
- Step 4-1: 문서 검토 (검토 에이전트)
- Step 5: 연관 이슈 역방향 링크
- Step 6: 결과 보고 — **단, 이 시점에서 `update-cookbook` 안내는 생략** (Phase 2에서 자동 처리)

Phase 1 완료 후 산출물: `operation-notes/{ticket-id}.md`

### Phase 2: COOKBOOK 증분 반영 (자동 판단)

Phase 1에서 생성/업데이트된 노트를 읽고, **쿡북에 반영할 내용이 있는지 판단**한다.

#### 반영 대상 판단 기준
아래 중 **하나 이상** 해당하면 쿡북 업데이트를 실행한다:

| 조건 | 노트에서 확인할 섹션/내용 |
|------|-------------------------|
| 진단 가이드 | `## 다음에 같은 문의가 오면` 섹션이 존재 |
| SQL 쿼리 | ` ```sql ` 코드 블록이 존재 |
| 원인 확정 | `## 원인 분석`, `### 확정된 원인`, `### 근본 원인`, `### 원인` 중 하나 존재 |
| 스펙/버그 판별 | `## 스펙/버그 판별` 섹션이 존재 |

#### 반영할 내용이 있는 경우
`update-cookbook.md`를 읽고 **증분 모드(Step 1~6)를 수행**한다.

```
Read: .claude/commands/ops/update-cookbook.md
```

#### 반영할 내용이 없는 경우
스킵하고 최종 보고에 "쿡북 반영할 내용 없음 (진단 가이드/SQL/원인 확정 섹션 미존재)" 표기.

### Phase 3: 최종 보고

Phase 1 + Phase 2 결과를 통합하여 한번에 보고한다.

```
## capture-issue 결과: {ticket-id}

### Phase 1: Operation Note
- 파일: `operation-notes/{ticket-id}.md`
- 모드: {신규 생성 | 업데이트}
- 핵심 내용 3줄 요약
- 연관 이슈: {있으면 목록, 없으면 "없음"}
- 시나리오: {Gherkin 작성했으면 내용 요약, 아니면 "해당 없음"}

### Phase 2: COOKBOOK
- 상태: {반영 완료 | 반영할 내용 없음}
- (반영 시) 변경 내용 요약

### 다음 단계
- 조사가 필요하면 → `ops:investigate-issue {ticket-id}`
- 코드 수정이 필요하면 → `ops:fix-issue {ticket-id}`
- 시나리오 테스트 추가가 필요하면 → `ops:sync-scenario-agents-md`
```

## Rules
- Phase 1의 모든 규칙은 `note-issue.md`를 따른다
- Phase 2의 모든 규칙은 `update-cookbook.md`를 따른다
- Phase 2에서 COOKBOOK.md가 아직 존재하지 않으면, 사용자에게 전체 스캔 모드 전환 여부를 확인한다
- 최종 보고에서 `update-cookbook` 안내는 제외한다 (이미 Phase 2에서 처리했으므로)
- Phase 1과 Phase 2 사이에 별도 사용자 확인 없이 자동 진행한다
- **서브모듈 변경은 커밋하지 않는다**
