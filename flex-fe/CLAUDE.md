# CLAUDE.md

## 프로젝트 개요

Flex HR SaaS 프론트엔드 프로젝트. 이 디렉토리는 **git submodule로 구성된 폴리레포 워크스페이스**이며, 각 서브모듈은 독립된 Yarn workspace monorepo이다.

서브모듈은 코드 탐색·조사 용도로 사용하며, 코드 수정과 PR은 각 서브모듈 내에서 수행한다. 이 umbrella repo에 서브모듈 변경을 커밋하지 않는다.

## 레포지토리 구조

### 패키지 레포 (Nexus Registry 배포, trunk based - main만)

| 레포 | 스코프 | 역할 |
|------|--------|------|
| `flex-frontend-packages` | `@flex-packages/*` | 공유 유틸리티 (eslint, prettier, test, i18n, api-client-generator 등). Flex 도메인 비종속 |
| `flex-frontend-services` | `@flex-services/*` | Flex 비즈니스 로직 서비스 레이어 |
| `flex-frontend-services-platform` | `@flex-services/*` | 플랫폼 서비스 레이어 (Changesets, Turbo 사용) |
| `flex-frontend-design-system` | `@flex-design-system/*` | UI 컴포넌트 (fx2, fx-composition, fx-extension, fx-icons). Radix UI + Vanilla Extract + Storybook |

### 애플리케이션 레포 (Jenkins 배포, develop → qa → main)

| 레포 | 역할 |
|------|------|
| `flex-frontend` | 공용 앱 (webview, remotes-home, remotes-gnb, remotes-document, remotes-settings) |
| `flex-frontend-apps-host` | Module Federation Host (Next.js) |
| `flex-frontend-apps-{domain}` | 스쿼드별 도메인 앱 (auth, people, payroll, recruiting, performance-management, time-tracking, workflow, fins, digicon, insight, brain, playground) |

## 공통 개발 커맨드

각 레포는 독립된 Yarn workspace monorepo이므로, 해당 레포 디렉토리에서 실행한다.

```bash
yarn install               # 의존성 설치
yarn dev                   # host 연동 개발 서버 (web-applications/{app}/ 에서)
yarn dev:standalone        # 독립 실행 개발 서버
yarn lint                  # ESLint
yarn fix:lint              # ESLint 자동 수정
yarn fix:format            # Prettier 포맷팅
yarn type-check            # TypeScript 타입 체크
yarn test                  # Jest 테스트
yarn build-app             # 프로덕션 빌드 (web-applications/ 하위에서)
yarn apis:create-api       # OpenAPI 기반 API 클라이언트 생성 (레포 루트에서)
yarn apis:create-hooks     # API hooks 패키지 생성 (레포 루트에서)
yarn packages:update-version --scope="@flex-packages" --version="1.x.x"
yarn locale:check          # 번역 키 일관성 확인
yarn locale:collect        # 번역 키 수집
yarn locale:translate      # 번역 실행
```

## 공통 아키텍처 패턴

### 애플리케이션 레포 공통 구조

```
{repo}/
├── apis/                    # OpenAPI 자동 생성 API 클라이언트 (@flex-apis/*)
├── packages/                # 내부 공유 패키지
└── web-applications/
    └── remotes-{domain}/
        ├── microApps/       # Module Federation으로 노출되는 React 컴포넌트
        └── src/
            ├── domains/     # 도메인별 비즈니스 로직 (components, hooks, models, specs)
            ├── libs/        # 도메인 비종속 공통 유틸리티
            ├── query/       # React Query 관련 코드 (도메인별 정리)
            └── web-pages/   # 페이지 컴포넌트
```

### 기술 스택

- **프레임워크**: Next.js (Host), React
- **Module Federation**: Podo 프레임워크 (`mf.config.ts`)
- **패키지 매니저**: Yarn Berry v4 (PnP 모드)
- **빌드**: Turborepo (원격 캐시)
- **상태 관리**: Jotai, XState (복잡한 상태 머신)
- **UI**: @flex-design-system (Radix UI 기반, Vanilla Extract)
- **데이터 페칭**: TanStack Query + 커스텀 Generator 패턴
- **폼**: react-hook-form + Zod
- **테스트**: Jest + React Testing Library + Fishery (mock factory)
- **다국어**: i18next (@flex-packages/i18n)
- **API**: OpenAPI Generator (@flex-packages/api-client-generator)
- **환경 관리**: direnv

### 네이밍 컨벤션

| 항목 | 규칙 |
|------|------|
| 디렉토리 | kebab-case |
| 컴포넌트 | PascalCase (`*.tsx`) |
| 훅 | camelCase + `use` prefix |
| 모델 | PascalCase (`Model.ts`) |
| 파서 | `Model.parser.ts` |
| Query Options | `{action}{Entity}QueryOptions.ts` |
| Mutation Options | `use{Action}{Entity}MutationOptions.ts` |

### 금지 사항

- `export default` 사용 금지 → named export만 사용
- `export *` 사용 금지 → 명시적 export만
- `any` 타입 사용 금지 → `unknown` 또는 구체 타입 사용
- API 타입 직접 정의 금지 → `@flex-apis/*`에서 import
- `libs/`에서 `domains/` import 금지 (의존성 방향 위반)

## 브랜치 전략

- **패키지 레포**: trunk based (main만)
- **애플리케이션 레포**: develop → qa → main
  - develop 머지 → dev 환경 자동 배포
  - main 머지 → 수동 배포 (캘린더 버저닝: `v2.{yyyy-MM-dd}.{count}`)

## 커밋 & PR 규칙

- 커밋 메시지는 **한국어**로 작성 (Conventional Commits 형식, scope는 kebab-case)
- PR은 draft로 먼저 생성
- 커밋 전 반드시 `yarn type-check && yarn lint` 통과 확인
- 커밋 수정 시 `--amend` 하지 말고, 새 커밋을 만든 뒤 interactive rebase로 squash/fixup 정리할 것

## 서브 레포별 CLAUDE.md

주요 도메인 레포에는 각각의 `CLAUDE.md`가 있다. 해당 레포에서 작업할 때는 반드시 해당 파일을 먼저 참조할 것.

## 개발 가이드

- [Host + Remote 로컬 디버깅](docs/host-remote-debugging.md)
- [로컬 패키지 디버깅 (yarn link/portal)](docs/local-package-debugging.md)
- [배포 프로세스](docs/deployment.md)
