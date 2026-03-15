---
description: Linear 이슈를 기반으로 코드 조사 → 구현 → PR 생성까지 수행
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
  2. 브랜치에서 못 찾으면 현재 디렉토리명에서 추출 시도
  3. 찾은 경우: 사용자에게 `"티켓 ID를 {추출한ID}로 인식했습니다. 맞습니까?"` 확인 후 진행
  4. 못 찾은 경우: `"티켓 ID를 특정할 수 없습니다. 티켓 ID를 인자로 전달해주세요. (예: /ops:fix-issue CI-3861)"` 출력 후 **즉시 종료**

## Procedure

### Phase 1: 이슈 파악 (🤖 Linear 에이전트)
**subagent에 위임하여** MCP CLI로 Linear 이슈 정보를 수집한다. **반드시 `mcp-cli info`로 스키마를 먼저 확인한 후 호출한다.**

1. `mcp-cli call linear/get_issue`로 이슈 조회 (includeRelations: true)
2. `mcp-cli call linear/list_comments`로 코멘트 조회 (추가 컨텍스트 확인)
3. 수집 정보: 제목, 설명, 우선순위, 라벨, 코멘트
4. `mcp-cli call linear/update_issue`로 이슈 상태를 **In Progress**로 변경

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
   - **문서 포맷팅**: `~/.claude/commands/ops/note-issue.md`의 "문서 포맷팅 규칙" 섹션을 따른다. 특히:
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

## Rules
- **Phase 3 → Phase 4 사이에 반드시 사용자 승인**: 조사 결과를 보고하고 구현 방향 승인을 받아야 함
- **빌드/테스트는 subagent**: gradlew 실행은 로그가 길으므로 반드시 subagent에 위임
- **이슈 상태 관리**: 시작 시 In Progress, PR 생성 후 댓글 연결
- **조사 문서화**: Phase 3의 조사 문서에는 `note-issue.md`의 "문서 작성 원칙"(출처 표기, 과정 기록, 용어 설명)과 "문서 포맷팅 규칙"(시각 요소 선택 기준, 테이블 작성, 데이터 가공)을 모두 준수한다. subagent에 위임 시 해당 규칙을 읽도록 지시한다.
- **근로기준법 고려** (근태/근무/휴가 관련 이슈): 구현 방향 결정 시 근로자 유불리를 판단한다. 근로기준법은 근로자 보호법이므로, **근로자에게 유리하면서 구현이 간단한 방향을 우선 권장**한다. 근로자에게 불리한 방향의 변경은 사용자에게 법적 리스크를 안내한다.
