---
name: vscode
description: 티켓 ID나 Linear 이슈 URL을 받아 VSCode workspace를 열어줍니다. worktree가 있으면 바로 열고, 없으면 Linear 이슈 기반으로 worktree를 생성한 뒤 엽니다. 사용자가 "/vscode", "vscode 열어", "workspace 열어" 등을 요청할 때 사용합니다.
argument-hint: <ticket-id-or-linear-url>
---

# /vscode Command

티켓 ID 또는 Linear 이슈 URL을 받아 VSCode 티켓별 workspace를 생성/열기합니다.

```
/vscode <ticket-id-or-linear-url>
/vscode FLX-123
/vscode fe-2083-p2
/vscode https://linear.app/flexteam/issue/FLX-123/some-title
```

## 스크립트 경로

Workspace 생성 스크립트: `.claude/skills/vscode/scripts/generate-workspace.mjs`

## 워크플로우

### 1. 입력 파싱

- Linear URL이면 이슈 ID 추출 (예: `https://linear.app/flexteam/issue/FLX-123/...` → `FLX-123`)
- 이슈 ID면 그대로 사용 (예: `FLX-123`)
- 티켓 suffix면 그대로 사용 (예: `fe-2083-p2`, `ppd-180`)

### 2. Worktree 존재 확인

`{flex-fe 루트}/` 에서 `*--{ticket}` 패턴의 디렉토리를 검색합니다.

```bash
ls -d {flex-fe 루트}/*--{ticket} 2>/dev/null
```

### 3A. Worktree가 있는 경우 (재개)

1. workspace 파일 생성/갱신:

```bash
node .claude/skills/vscode/scripts/generate-workspace.mjs {ticket}
```

2. VSCode 열기:

```bash
code {flex-fe 루트}/workspaces/{ticket}.code-workspace
```

3. 컨텍스트 출력:

```
✅ VSCode workspace 열림

티켓: {TICKET}
Worktrees:
  - flex-frontend--{ticket} (frontend)
  - flex-frontend-apps-payroll--{ticket} (payroll)
  ...
```

### 3B. Worktree가 없는 경우 (신규 시작)

1. **Linear 이슈 조회** (MCP `get_issue`)
   - URL이면 이슈 ID 추출 후 조회
   - 이슈 정보 출력: 제목, 상태, 라벨, 담당자, 브랜치명

2. **작업 대상 레포 판단**
   - 이슈 제목/설명의 키워드로 대상 레포 추론
   - 코드베이스 검색으로 관련 파일이 어느 레포에 있는지 확인
   - 확신 있으면 바로 진행, 애매하면 사용자에게 질문

3. **Worktree 생성 (병렬)**

   각 대상 레포에 대해:

   ```bash
   cd {flex-fe 루트}/{repo} && git checkout develop && git pull origin develop
   git worktree add {flex-fe 루트}/{repo}--{ticket-suffix} -b {branch} develop
   ```

   **Worktree 네이밍 규칙:**
   - 형식: `{레포명}--{브랜치에서 슬래시 이후 부분 또는 전체}`
   - 위치: 기존 레포와 같은 부모 디렉토리 (형제 위치)

   **여러 레포가 대상인 경우 모든 worktree를 병렬로 생성합니다.**

4. **환경 초기화 (병렬)**

   각 worktree에서 `direnv allow` → `yarn install` 순서로 실행:

   ```bash
   cd {flex-fe 루트}/{repo}--{ticket-suffix} && direnv allow && yarn install
   ```

5. **이슈 상태 업데이트** (MCP `save_issue`)
   - 이슈 상태를 "In Progress"로 변경

6. **workspace 생성 + VSCode 열기**

   ```bash
   node .claude/skills/vscode/scripts/generate-workspace.mjs {ticket}
   code {flex-fe 루트}/workspaces/{ticket}.code-workspace
   ```

7. **컨텍스트 출력**

   ```
   ✅ 작업 준비 완료

   이슈: FLX-123 - 로그인 페이지 로딩 성능 개선
   상태: Todo → In Progress

   | 레포 | Worktree | 브랜치 |
   |------|----------|--------|
   | flex-frontend-apps-workflow | ...--ppd-180 | feature/ppd-180 |
   | flex-frontend | ...--ppd-180 | feature/ppd-180 |

   VSCode workspace가 열렸습니다.
   ```

## Linear MCP 도구 사용 (신규 시작 시)

- `get_issue` - 이슈 정보 조회
- `save_issue` - 이슈 상태 업데이트 (Todo → In Progress)

## 브랜치 네이밍

Linear에서 제공하는 브랜치 이름을 사용합니다.
