# flex-fe

`flex-team/flex-oncall` 레포의 하위 디렉토리. 21개 FE 레포지토리를 git submodule로 포함하며, Claude Code 워크스페이스에서 탐색/개발할 수 있게 한다.

## Setup

flex-oncall 클론 시 `--recursive` 옵션으로 함께 체크아웃된다:

```bash
git clone --recursive git@github.com:flex-team/flex-oncall.git
cd flex-oncall/flex-fe
```

서브모듈 업데이트:

```bash
cd flex-oncall
git submodule update --remote --merge
```

## Claude Code 실행

부모 디렉토리(flex-oncall)에서 실행하면 FE + BE 모든 하위 레포에 접근 가능하다.

## 구조

```
flex-fe/
├── 📦 패키지 레포 (Nexus Registry 배포, trunk-based)
│   ├── flex-frontend-packages/
│   ├── flex-frontend-services/
│   ├── flex-frontend-services-platform/
│   └── flex-frontend-design-system/
│
├── 🖥️ 애플리케이션 레포 (Jenkins 배포, develop → qa → main)
│   ├── flex-frontend/              (공용 Remote: home, gnb, settings 등)
│   ├── flex-frontend-apps-host/    (Module Federation Host)
│   └── flex-frontend-apps-{domain}/
│
└── 🔀 Git Worktree (작업 브랜치별, .gitignore로 제외)
    └── flex-frontend-apps-fins--ci-4334/
```
