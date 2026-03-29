---
name: close-note
description: Use when an issue is resolved/done and needs final wrap-up — syncs the operation-note with latest Linear data AND updates COOKBOOK in one step. Triggers include '마무리해줘', '클로즈해줘', '노트 정리', or after investigation/fix is complete. Not for issue intake (use ops-note-issue).
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task
argument-hint: <ticket-id> (예: CI-3861)
---

# Close Note

## Purpose
완료된 이슈에 대해 **operation-note 동기화 + brain 산출물 갱신**을 한번에 처리한다.
Linear 최신 정보로 note를 업데이트하고, COOKBOOK/domain-map.ttl 반영까지 자동 진행.

> 이슈 **접수** 시점에는 이 커맨드가 아닌 `note-issue` 를 사용한다.
> 이 커맨드는 이슈가 **완료**된 후 데이터화할 때 사용한다.

개별 커맨드(`note-issue`, `ops-learn`)는 그대로 유지되며, 이 커맨드는 둘을 오케스트레이션한다.

## Input
$ARGUMENTS

### Argument Resolution
`note-issue.md` 의 Argument Resolution 규칙을 그대로 따른다:
- 티켓 ID 패턴(`[A-Z]+-\d+`)이 있으면 사용
- 없으면 git 브랜치명 → 대화 세션 컨텍스트 → 디렉토리명 순으로 추출 시도
- 못 찾으면 안내 후 즉시 종료

## Procedure

### Phase 1: Operation Note 동기화

`commands/ops/note-issue.md` 를 읽고 **Step 1~6을 그대로 수행**한다.

```
Read: .claude/skills/ops-note-issue/SKILL.md
```

수행 범위:
- Step 1-2: 데이터 수집 (Linear 이슈 + 연관 이슈 탐색, 병렬)
- Step 3: 문서 생성 또는 업데이트
- Step 4: Gherkin 시나리오 작성 (해결 완료 시)
- Step 4-1: 문서 검토 (검토 에이전트)
- Step 5: 연관 이슈 역방향 링크
- Step 6: 결과 보고 — **단, 이 시점에서 `ops-learn` 안내는 생략** (Phase 2에서 자동 처리)

Phase 1 완료 후 산출물: `brain/notes/{ticket-id}.md`

### Phase 2: Brain 산출물 갱신 (자동 판단)

Phase 1에서 생성/업데이트된 노트를 `ops-learn`에 전달하여 brain 산출물을 갱신한다.

```
Read: .claude/skills/ops-learn/SKILL.md
```

입력: `brain/notes/{ticket-id}.md` (로컬 파일 소스로 전달)

ops-learn이 자동으로 판단:
- COOKBOOK: 진단 가이드/SQL/원인 확정/스펙 판별 반영 (코드 수정 해결 시 스킵)
- domain-map.ttl: 키워드/glossary 항목 갱신

### Phase 3: 노트 농축 + 정제

> 이슈가 **완료 상태**(Done/Closed)인 경우에만 이 Phase를 수행한다.
> 아직 조사 중이거나 미완료이면 이 Phase를 건너뛴다.

archive 이동 전에 유효한 신호를 상위 산출물에 흡수하고, 노트를 정제한다.

#### 3-1. 농축 (정제보다 반드시 먼저 수행)

노트에서 재사용 가능한 신호를 추출하여 상위 산출물에 흡수한다:

1. **사용자 표현 흡수**: 노트 "증상" 섹션의 문의 표현 중 domain-map.ttl의 해당 도메인 `d:syn` 에 없는 것 → 추가
2. **키워드 흡수**: 조사에서 유효했던 진단 키워드 중 해당 도메인 `d:kw` 에 없는 도메인 고유 키워드 → 추가
3. **COOKBOOK 보강**: 확정된 원인 패턴이 재사용 가능하면 → Phase 2의 ops-learn에서 이미 처리됨. 추가 필요 시 COOKBOOK 체크리스트/플로우에 반영
4. **domain-map.ttl 상태 설정**: 해당 노트 `n:{ticket-id}` 에 `d:st "C"` + `d:ca "YYYY-MM-DD"` (오늘 날짜) 추가

#### 3-2. 정제

농축 완료 후 노트에서 불필요한 내용을 제거한다:

**제거 대상**:
- `## Claude 활동 로그` 테이블 전체 (JSONL 메트릭스로 대체됨)
- 가설 목록에서 소거된 가설 (확정된 가설/원인만 유지)
- DB 쿼리 결과 테이블 (원시 데이터, 시점 종속)
- 상세 코드 트레이스 (COOKBOOK에 요약 반영된 것)

**유지 대상**:
- 증상 1-2줄 요약
- 확정 원인
- 해결 조치 + PR 링크
- 참조 링크/각주
- Gherkin 시나리오

정제 후 노트 상단에 기록:
```markdown
> **compact**: 원본 {N}줄 → 정제 {M}줄 ({날짜}). git log로 원본 추적 가능.
```

### Phase 4: 최종 보고

Phase 1~3 결과를 통합하여 한번에 보고한다.

```
## close-note 결과: {ticket-id}

### Phase 1: Operation Note
- 파일: `brain/notes/{ticket-id}.md`
- 모드: {신규 생성 | 업데이트}
- 핵심 내용 3줄 요약
- 연관 이슈: {있으면 목록, 없으면 "없음"}
- 시나리오: {Gherkin 작성했으면 내용 요약, 아니면 "해당 없음"}

### Phase 2: Brain 산출물
- COOKBOOK: {반영 완료 | 반영할 내용 없음 | 코드 수정으로 해결 — 스킵}
- domain-map.ttl: {갱신 | 변경 없음}

### Phase 3: 농축+정제
- 농축: d:syn {N}건 흡수, d:kw {N}건 흡수, d:st "C" + d:ca 설정
- 정제: {N}줄 → {M}줄 (활동 로그/가설/원시 데이터 제거)
- {건너뜀 — 이슈 미완료}

### 다음 단계
- 일괄 아카이브가 필요하면 → `ops:maintain-notes`
```

### Phase 5: 메트릭스

> 쿡북 히트 기록이 필요한 경우(investigate-issue 전용)만 COOKBOOK.md를 갱신한다.
> ```
> Read: .claude/skills/ops-common/metrics-guide.md
> ```

## Rules
- Phase 1의 모든 규칙은 `note-issue.md` 를 따른다
- Phase 2의 모든 규칙은 `ops-learn` 스킬을 따른다
- Phase 1과 Phase 2 사이에 별도 사용자 확인 없이 자동 진행한다
- **서브모듈 변경은 커밋하지 않는다**
- **QNA 팀 이슈 예외**: QNA 이슈(`QNA-` 접두사)는 Linear 상태가 관리되지 않는다. 이슈 완료 여부는 코멘트 맥락(답변 완료 여부, 후속 액션 유무)으로 판단한다.
