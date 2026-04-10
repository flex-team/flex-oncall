# Host + Remote 로컬 디버깅

Module Federation 구조에서 Remote 앱의 코드 변경을 Host를 통해 확인하는 방법.

## 설정 방법

### 1. Host의 .env.local에 Remote URL 추가

```bash
# flex-frontend-apps-host/web-applications/host/.env.local
MF_REMOTES_INSIGHT_BASE_URL=http://localhost:3008
# MF_REMOTES_GNB_BASE_URL=http://localhost:3002
# MF_REMOTES_SETTINGS_BASE_URL=http://localhost:3101
```

환경변수 형식: `MF_REMOTES_{APP_NAME}_BASE_URL=http://localhost:{PORT}`
APP_NAME은 대문자 (INSIGHT, GNB, HOME, SETTINGS 등)

### 2. Remote/Host 포트 매핑

| Remote | 포트 | 환경변수 |
|--------|------|----------|
| GNB | 3002 | MF_REMOTES_GNB_BASE_URL |
| Home | 3007 | MF_REMOTES_HOME_BASE_URL |
| Insight | 3008 | MF_REMOTES_INSIGHT_BASE_URL |
| Payroll | 3009 | MF_REMOTES_PAYROLL_BASE_URL |
| Settings | 3101 | MF_REMOTES_SETTINGS_BASE_URL |

### 3. 실행 순서

1. Remote: `yarn dev:standalone`
2. Host: `yarn turbo dev --filter=@flex-apps/host`
3. `http://localhost:3000/{path}` 에서 확인

## 트러블슈팅

- `.env.local` 수정 후 Host dev 서버 재시작 필수
- 캐시 무시 새로고침: `Cmd+Shift+R`
- remoteEntry.js가 `localhost:{PORT}`에서 로드되는지 확인
