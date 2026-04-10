# 배포 프로세스

## 패키지 레포 (packages/services/design-system)

1. 코드 수정 및 PR: main 브랜치로 PR 생성
2. Release: Release Action 실행 (마이너 버전 자동 증가)
3. Publish: Publish Action 실행 (Nexus Registry에 배포)
4. 앱 레포 업데이트: `yarn packages:update-version` 실행

## 애플리케이션 레포

### 일반 개발

1. Feature 브랜치 생성
2. develop PR → 머지 → dev 자동 배포
3. qa PR (develop → qa) → 머지 → qa 자동 배포
4. main PR (qa → main) → 머지 → 릴리즈 태그 자동 → 수동 배포
5. 백머지 확인

### 핫픽스

1. main 기준 PR 생성
2. 머지 후 릴리즈 태그 자동 생성
3. 변경된 앱들 수동 배포
4. 백머지 확인

## Commit Convention

`<type>(<scope>): <subject>`

Types: feat, fix, docs, style, refactor, test, chore

PR 제목도 Conventional Commits 형식
