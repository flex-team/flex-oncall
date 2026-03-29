---
name: fix-issue
description: Use when an issue needs a code change — bug fix, feature implementation, or config update — going through to PR creation. Triggers include '수정해줘', '코드 고쳐줘', 'PR 만들어줘', or when investigation concluded the issue requires code fix. Not for investigation-only (use ops-investigate-issue) or documentation-only (use ops-note-issue).
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, Task, Skill
argument-hint: <ticket-id> (예: FLX-1234, CI-5678)
---

# Fix Issue

## Purpose
Linear 이슈 ID를 받아 이슈 내용을 파악하고, 코드 조사 → 구현 → PR 생성까지 수행한다.
운영/CS 이슈 기록은 `ops:note-issue`, 조사는 `ops:investigate-issue`를 사용할 것.

## Input
$ARGUMENTS

### Argument Resolution
- `$ARGUMENTS`가 비어있거나 티켓 ID 패턴(`[A-Z]+-\d+`, 예: CI-3861)이 없으면:
  1. 현재 git 브랜치명에서 티켓 ID 패턴을 추출 시도 (예: `fix/CI-3861-some-desc` → `CI-3861`)
  2. 현재 대화 세션에서 언급된 티켓 ID를 추출 시도 (직전 사용자 메시지, 이전에 실행한 커맨드 인자 등)
  3. 브랜치/대화에서 못 찾으면 현재 디렉토리명에서 추출 시도
  4. 찾은 경우: 사용자에게 `"티켓 ID를 {추출한ID}로 인식했습니다. 맞습니까?"` 확인 후 진행
  5. 못 찾은 경우: `"티켓 ID를 특정할 수 없습니다. 티켓 ID를 인자로 전달해주세요. (예: /ops:fix-issue CI-3861)"` 출력 후 **즉시 종료**

## Note File Resolution

operation-note 파일(`{ticket-id}.md`)을 찾을 때 아래 순서로 탐색한다:
1. `{notes-dir}/{ticket-id}.md` (active — 진행 중)
2. `{notes-dir}/archive/{ticket-id}.md` (archive — 해결 완료)

- 파일을 **새로 생성**할 때는 항상 `{notes-dir}/` (루트)에 생성한다.
- 이슈가 **해결 완료**되면 `{notes-dir}/archive/`로 이동한다.
- 상대 링크 규칙:
  - 루트 → archive: `./archive/{ticket-id}.md`
  - archive → 루트: `../{ticket-id}.md`
  - archive → archive: `./{ticket-id}.md`

## Procedure

### Phase 0: 도메인 라우팅 + 선행 문서 확인

코드 수정 전에 어떤 도메인/서브모듈에서 작업할지 특정하고, 이슈 맥락이 정리된 문서가 필요하다.

**도메인 라우팅:**
> ```
> Read: .claude/skills/ops-common/domain-routing.md
> ```
> Linear 이슈 제목으로 라우팅을 수행하여 primary 도메인의 `d:repo`(작업 대상 서브모듈)와 `d:mod`(모듈 경로)를 확인한다. 필요한 서브모듈만 `git submodule update --init` 한다.

**선행 문서 확인:**
문서 상태에 따라 선행 커맨드를 실행한다.

1. `{notes-dir}/{ticket-id}.md` 또는 `{notes-dir}/archive/{ticket-id}.md` 존재 여부 확인
2. **문서 없음** → `note-issue.md` 를 읽고 Step 1~5를 실행하여 operation-note 생성, 이어서 `investigate-issue.md` 를 읽고 조사 수행
   ```
   Read: .claude/skills/ops-note-issue/SKILL.md
   Read: .claude/skills/ops-investigate-issue/SKILL.md
   ```
3. **문서 있음, 조사 결과 없음** (원인 분석/해결안 섹션 미존재) → `investigate-issue.md` 를 읽고 조사 수행
4. **문서 있음, 조사 결과 있음** → Phase 1로 바로 진행

### Phase 1: 이슈 파악 (🤖 Linear 에이전트)
**subagent에 위임하여** MCP CLI로 Linear 이슈 정보를 수집한다. **반드시 `mcp-cli info` 로 스키마를 먼저 확인한 후 호출한다.**

1. `mcp-cli call linear/get_issue` 로 이슈 조회 (includeRelations: true)
2. `mcp-cli call linear/list_comments` 로 코멘트 조회 (추가 컨텍스트 확인)
3. 수집 정보: 제목, 설명, 우선순위, 라벨, 코멘트
4. `mcp-cli call linear/update_issue` 로 이슈 상태를 **In Progress**로 변경

### Phase 2: 브랜치 생성
`git:git-branch-and-commit` 스킬을 사용하여 브랜치를 생성한다.

| 이슈 유형 | prefix |
|-----------|--------|
| Bug | fix/ |
| Feature | feature/ |
| Improvement, Chore 등 | chore/ |

이 시점에 커밋할 변경사항은 없으므로 브랜치 생성만 수행.

### Phase 3: 조사
`utils:investigate` 스킬의 접근법을 따라 코드를 조사한다.

1. 이슈 설명에서 언급된 클래스/서비스를 검색
2. 관련 코드의 구조와 패턴 파악
3. 조사 결과를 `/tmp/claude-work-YYYYMMDD/investigation-{이슈ID}.md`에 저장
   - 조사 문서에는 **어떤 코드를 왜 확인했는지 과정을 기록** (파일 경로:라인 포함)
   - 핵심 로직의 코드 스니펫 포함
   - 설계 옵션별 장단점 근거 명시
   - **문서 포맷팅**: `note-writing-guide.md`의 "문서 포맷팅 규칙" 섹션을 따른다. 특히:
     - 코드 위치는 `*(코드: {모듈}/{상대경로}:{라인})*` 형식으로 출처 표기
     - 판단 근거는 `> 💡 **판단 근거**: {단서} → {확인} → {결론}` 형식
     - 구조화된 데이터 비교에는 테이블, 분기 흐름에는 mermaid flowchart 활용 (단순 선형이면 번호 목록)
     - 설계 옵션은 테이블로 비교 (옵션명, 장점, 단점, 영향 범위)
4. **설계 옵션을 사용자에게 제시하고 승인을 받음**

⚠️ **승인 없이 구현을 시작하지 않음**

### Phase 4: 구현
사용자가 승인한 방향으로 구현한다.

1. 코드 변경 수행
2. 필요시 테스트 추가/수정
3. 빌드 검증 (`./gradlew build` — subagent에 위임)
4. 테스트 검증 (`./gradlew test` — subagent에 위임)

빌드/테스트 실패 시 수정 후 재검증. 통과할 때까지 반복.

### Phase 5: PR 생성
`git:git-commit-push-pr` 스킬을 실행한다.

- 커밋 메시지에 이슈 ID 포함
- PR 본문에 이슈 링크 포함
- PR은 draft로 생성

### Phase 6: 마무리
1. `mcp-cli call linear/create_comment`로 이슈에 PR 링크를 댓글로 추가
2. 완료 보고

## 보고 형식

```markdown
## ✅ {이슈ID} 작업 완료

**이슈**: {제목}
**브랜치**: {브랜치명}
**PR**: {PR URL}

### 변경 요약
- {변경 내용 1}
- {변경 내용 2}

### 검증
- 빌드: ✅
- 테스트: ✅ ({N}개 통과)
```

### Phase 7: 메트릭스 기록

> 이 단계는 PostToolUse 훅이 자동으로 리마인드한다. 기록 규칙 상세는 아래 가이드를 참조.
> ```
> Read: .claude/skills/ops-common/metrics-guide.md
> ```

1. **노트 활동 로그**: `{notes-dir}/{ticket-id}.md` 하단 `## Claude 활동 로그` 테이블에 행 추가
   - subagent total_tokens/duration_ms 합산, 쿡북 참조 = `—`

## Rules
- **Phase 3 → Phase 4 사이에 반드시 사용자 승인**: 조사 결과를 보고하고 구현 방향 승인을 받아야 함
- **빌드/테스트는 subagent**: gradlew 실행은 로그가 길으므로 반드시 subagent에 위임
- **이슈 상태 관리**: 시작 시 In Progress, PR 생성 후 댓글 연결
- **조사 문서화**: Phase 3의 조사 문서에는 `note-writing-guide.md`의 "문서 작성 원칙"(출처 표기, 과정 기록, 용어 설명)과 "문서 포맷팅 규칙"(시각 요소 선택 기준, 테이블 작성, 데이터 가공)을 모두 준수한다. subagent에 위임 시 해당 규칙을 읽도록 지시한다.
- **근로기준법 고려** (근태/근무/휴가 관련 이슈): 구현 방향 결정 시 근로자 유불리를 판단한다. 근로기준법은 근로자 보호법이므로, **근로자에게 유리하면서 구현이 간단한 방향을 우선 권장**한다. 근로자에게 불리한 방향의 변경은 사용자에게 법적 리스크를 안내한다.
