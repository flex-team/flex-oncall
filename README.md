# flex-oncall

온콜 업무를 위한 통합 워크스페이스. FE와 BE 코드베이스를 하나의 환경에서 탐색하고, Claude Code로 이슈를 분석할 수 있다.

## Setup

```bash
git clone --recursive git@github.com:flex-team/flex-oncall.git
cd flex-oncall
```

서브모듈 전체 업데이트:

```bash
git submodule update --remote --merge --recursive
```

## 구조

```
flex-oncall/
├── flex-fe/                    ← FE 폴리레포 (21개 서브모듈)
│   ├── flex-frontend/
│   ├── flex-frontend-apps-*/
│   ├── flex-frontend-packages/
│   └── ...
└── flex-support-oncall/        ← BE 온콜 레포 (27개 서브모듈 + brain/)
    ├── flex-core-backend/
    ├── flex-payroll-backend/
    ├── brain/                  ← 운영 지식 (COOKBOOK, domain-map, notes)
    └── ...
```

## Claude Code 실행

### FE 이슈 조사

```bash
cd flex-oncall/flex-fe
claude --dangerously-skip-permissions
```

### BE 이슈 조사

```bash
cd flex-oncall/flex-support-oncall
claude --dangerously-skip-permissions
```

### 전체 워크스페이스

```bash
cd flex-oncall
claude --dangerously-skip-permissions
```

## 추가 셋업 (선택)

### flex-fe 플러그인

```bash
cd flex-oncall/flex-fe
claude
# Claude Code 내에서:
/plugin marketplace add git@github.com:flex-team-experimental/flex-frontend-claude-plugin.git
/plugin install create-pull-request@flex-frontend
/plugin install i18n-extractor@flex-frontend
/plugin install figma-codegen@flex-frontend
```

### Skills

`/vscode`, `/sync-repos`, `/cleanup-worktrees` 스킬은 `flex-fe/.claude/skills/`에 포함되어 있다. 레포 clone 시 자동으로 사용 가능.

### Scheduled Tasks (세션 한정)

Claude Code 세션 내에서 설정:

- **레포 동기화**: 평일 아침 전체 레포 `git fetch --all --prune` + develop/main checkout
- **Worktree 정리**: 주 1회 stale worktree 스캔 및 정리
