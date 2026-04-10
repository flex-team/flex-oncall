# AGENTS.md

## Sub-Agent Patterns

이 워크스페이스에서 사용할 수 있는 sub-agent 패턴입니다.

### package-impact

패키지 레포 변경이 어떤 앱 레포에 영향을 미치는지 확인합니다.

- **사용 시점**: 패키지 레포(packages, services, design-system) 수정 후
- **방법**: 변경된 패키지의 스코프(@flex-packages/*, @flex-services/*, @flex-design-system/*)를 각 앱 레포의 package.json에서 검색
- **결과**: 영향받는 앱 레포 목록과 사용 위치

### cross-repo-search

여러 레포에 걸쳐 특정 패턴이나 코드를 검색합니다.

- **사용 시점**: 특정 API, 컴포넌트, 패턴의 사용처를 전체 프로젝트에서 찾을 때
- **방법**: 워크스페이스 루트에서 모든 flex-* 디렉토리를 대상으로 grep
- **주의**: worktree 디렉토리(-- 패턴)는 제외

### migration-checker

여러 레포에 걸친 일괄 변경이 일관되게 적용되었는지 확인합니다.

- **사용 시점**: 패키지 버전 업데이트, ESLint 규칙 변경, 디자인 시스템 마이그레이션 등
- **방법**: 각 레포에서 특정 조건 확인 (예: package.json의 버전, import 경로 등)
- **결과**: 레포별 적용 상태 테이블

### review-assistant

PR 리뷰 시 변경사항의 영향 범위와 잠재적 이슈를 분석합니다.

- **사용 시점**: PR 리뷰 요청 시
- **방법**: git diff 분석, 타입 체크, 관련 테스트 실행
- **결과**: 변경 요약, 영향 범위, 잠재적 이슈 목록
