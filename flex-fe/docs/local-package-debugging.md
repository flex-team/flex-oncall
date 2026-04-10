# 로컬 패키지 디버깅 (yarn link/portal)

패키지 레포(services, packages)의 코드를 수정하고 앱 레포에서 실시간으로 확인하는 방법.

## 워크플로우

```bash
# 1. 앱 레포에서 패키지 레포를 link
cd flex-frontend
yarn link -A -r -p ../flex-frontend-services
yarn link -A -r -p ../flex-frontend-packages

# 2. 패키지 수정 후 빌드
cd ../flex-frontend-services/services/{패키지명}
yarn build

# 3. HMR로 자동 반영하거나 재시작
```

## 주의사항

- 패키지 수정 후 반드시 `yarn build` 실행 (dist 갱신 필수)
- 디버깅 완료 후 해제: `yarn unlink -A -r -p ../flex-frontend-services`
- **커밋 전 반드시 복원**: `git checkout -- package.json yarn.lock`
  - portal 연결 시 package.json에 portal 프로토콜이 추가됨 — 절대 커밋 금지

## Worktree에서 Portal 연결 시

- worktree 내 모든 패키지가 빌드되어 있어야 함
- 빠른 빌드: `git stash → yarn turbo run build → git stash pop → 수정 패키지만 빌드`

## 트러블슈팅

- 변경 반영 안 되면 yarn link 재실행
- 그래도 안 되면 dev 서버 재시작
