# flex-oncall

온콜 업무를 위한 통합 워크스페이스. FE와 BE 코드베이스를 하나의 환경에서 탐색하고, Claude Code로 이슈를 분석할 수 있다.

## Setup

### 1. 레포 클론

```bash
git clone --recursive git@github.com:flex-team/flex-oncall.git
cd flex-oncall
```

> `--recursive` 옵션으로 모든 서브모듈(FE 21개 + BE 27개)이 자동으로 초기화된다. 첫 클론은 10-20분 소요될 수 있다.

### 2. Claude Code 실행

```bash
cd flex-oncall
claude --dangerously-skip-permissions
```

루트에서 실행하면 FE + BE 모든 코드와 스킬에 접근 가능하다.

### 3. MCP 및 플러그인 확인

온콜 스킬이 정상적으로 동작하려면 아래 MCP/플러그인이 연결되어 있어야 한다. Claude Code에서 `/mcp` 명령어로 현재 연결 상태를 확인할 수 있다.

| MCP / 플러그인 | 용도 | 필수 여부 |
|----------------|------|-----------|
| **Slack** | CS 이슈 스레드 읽기, 배포 채널 확인 | 필수 |
| **Linear** | 이슈 조회, 상태 업데이트, 연관 이슈 검색 | 필수 |
| **Sentry** | FE 런타임 에러 확인, 스택트레이스로 원인 파일 특정 | 권장 |
| **Figma** | 코드 수정 시 디자인 스펙 참조 | 권장 |
| **Chrome DevTools** | 브라우저에서 직접 재현, 네트워크 탭 확인 | 선택 |

### 4. OpenSearch 플러그인 설치 (권장)

BE 이슈 조사나 FE↔BE 교차 조사 시 access log를 확인하려면 OpenSearch MCP가 필요하다.

```bash
claude
# Claude Code 내에서:
/plugin marketplace add git@github.com:flex-yj-kim/flex-claude-skills-yj-kim.git
/plugin install opensearch
```

### 5. flex-fe 플러그인 설치 (선택)

온콜 이슈 수정 시 PR 생성, i18n, Figma 코드 생성을 자동화할 수 있다.

```bash
claude
# Claude Code 내에서:
/plugin marketplace add git@github.com:flex-team-experimental/flex-frontend-claude-plugin.git
/plugin install create-pull-request@flex-frontend
/plugin install i18n-extractor@flex-frontend
/plugin install figma-codegen@flex-frontend
```

## 구조

```
flex-oncall/
├── .claude/
│   ├── settings.json              ← 마켓플레이스, 훅 설정
│   ├── scripts/auto-sync-submodules.sh
│   └── skills/                    ← 온콜 스킬 5개
│       ├── oncall/                   전체 워크플로우 오케스트레이터
│       ├── oncall-triage/            이슈 접수 및 FE/BE 판별
│       ├── oncall-investigate/       FE 코드 조사 + BE 교차 조사
│       ├── oncall-summarize/         슬랙 공유용 메시지 생성
│       └── oncall-dry-run/           분석 역량 훈련용
│
├── flex-fe/                       ← FE 폴리레포 (21개 서브모듈)
│   ├── .claude/
│   │   ├── skills/                ← FE 유틸리티 스킬 3개
│   │   │   ├── vscode/               worktree + VSCode workspace 생성
│   │   │   ├── sync-repos/           전체 레포 동기화
│   │   │   └── cleanup-worktrees/    stale worktree 정리
│   │   ├── settings.json
│   │   └── launch.json
│   ├── CLAUDE.md                  ← FE 코드 컨벤션, 기술 스택
│   ├── AGENTS.md                  ← 서브 에이전트 패턴 정의
│   ├── docs/                      ← 배포, 디버깅 가이드
│   ├── flex-frontend/
│   ├── flex-frontend-apps-*/
│   ├── flex-frontend-packages/
│   └── ...
│
└── flex-support-oncall/           ← BE 온콜 레포 (서브모듈)
    ├── flex-core-backend/
    ├── flex-payroll-backend/
    ├── brain/                     ← 운영 지식 (COOKBOOK, domain-map, notes)
    └── ...
```

## 온콜 워크플로우

```
이슈 인입 (Slack / Linear)
  → /oncall 실행
    ├─ Phase 1: /oncall-triage     맥락 파악 + FE/BE 판별
    │
    ├─ 분기 판단
    │   ├─ BE / 스펙 / Not a bug → Phase 3으로 건너뜀
    │   └─ FE / 판단 불가       → Phase 2 진행
    │
    ├─ Phase 2: /oncall-investigate  코드 추적 + 가설 소거
    │
    └─ Phase 3: /oncall-summarize    슬랙 공유용 메시지 생성
```

각 서브 스킬은 독립적으로도 사용할 수 있다:

| 상황 | 스킬 |
|------|------|
| triage만 하고 BE로 라우팅 | `/oncall-triage CI-4500` |
| 이미 원인을 알고 슬랙 포맷만 필요 | `/oncall-summarize` + 원인 설명 |
| triage 없이 바로 조사 | `/oncall-investigate` + 이슈 설명 |

## 유지보수

| 명령어 | 용도 | 비고 |
|--------|------|------|
| `git submodule update --remote --merge` | 전체 서브모듈 최신화 | SessionStart 훅으로 24시간마다 자동 실행 |
| `/sync-repos` | FE 레포 동기화 (fetch + develop checkout) | |
| `/cleanup-worktrees` | 머지 완료된 worktree 정리 | |
| `/vscode {ticket-id}` | 티켓 기반 worktree + VSCode workspace 생성 | |

## 참고 자료

- [FE 온콜 가이드 (Notion)](https://www.notion.so/flexnotion/FE-33b0592a4a92814684c7df95e57f41d6) — 셋업부터 실전까지
- [flex-support-oncall (GitHub)](https://github.com/flex-team/flex-support-oncall) — BE 온콜 레포
- [지난 1주간 온콜 이슈 (Linear)](https://linear.app/flexteam/view/%EC%A7%80%EB%82%9C-1%EC%A3%BC%EA%B0%84-%EC%98%A8%EC%BD%9C-%EC%9D%B4%EC%8A%88-13e4abe72fd1)
