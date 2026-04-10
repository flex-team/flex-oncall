# CLAUDE.md

## 프로젝트 개요

온콜 업무를 위한 통합 워크스페이스. FE와 BE 코드베이스를 하나의 환경에서 탐색하고, Claude Code로 이슈를 분석한다.

- Always respond in Korean
- 서브모듈 변경은 이 repo에 커밋하지 않는다. 코드 수정과 PR은 각 서브모듈 내에서 수행한다.
- **OpenSearch 로그 조회는 반드시 `opensearch:os-query-log` 스킬(MCP 플러그인)을 사용한다. curl로 OpenSearch/Elasticsearch를 직접 호출하지 않는다.** 이유: curl 직접 호출은 인덱스 패턴, 쿼리 포맷, 인증 등을 매번 수동 구성해야 하고 오류가 잦다. `os-query-log` 스킬이 이를 모두 추상화한다.

## 워크스페이스 구조

| 디렉토리 | 용도 | 상세 |
|----------|------|------|
| `flex-fe/` | FE 코드 탐색/수정 | 21개 FE 레포 (submodule). `flex-fe/CLAUDE.md` 참조 |
| `flex-support-oncall/` | BE 코드 탐색 + 운영 지식 | 27개 BE 레포 + brain/. `flex-support-oncall/CLAUDE.md` 참조 |

## 온콜 워크플로우

```
이슈 접수 (Slack #customer-issue / Linear)
  → FE vs BE 판단
    → FE 이슈: flex-fe/ 에서 조사. 서비스 영역 → 레포 매핑 후 해당 레포에서 코드 추적
    → BE 이슈: flex-support-oncall/ 에서 조사. opensearch 로그 + DB 쿼리로 원인 파악
  → 원인 분석 및 슬랙 공유
  → 코드 수정 시 해당 서브모듈 내에서 worktree 생성 → PR
```

## FE 이슈 조사 시

`flex-fe/` 하위에서 작업한다. 서비스 영역별 레포 매핑:

| 서비스 영역 | 대상 레포 |
|-------------|-----------|
| 비용관리, 지출결의, 영수증, 법인카드 | `flex-frontend-apps-fins` |
| 근태관리, 출퇴근, 휴가, 초과근무 | `flex-frontend-apps-time-tracking` |
| 평가, 리뷰, 목표 | `flex-frontend-apps-performance-management` |
| 급여, 정산 | `flex-frontend-apps-payroll` |
| 채용, 지원자 | `flex-frontend-apps-recruiting` |
| 전자결재, 워크플로우 | `flex-frontend-apps-workflow` |
| 인사정보, 조직 | `flex-frontend-apps-people` |
| 로그인, 인증 | `flex-frontend-apps-auth` |
| GNB, 홈, 설정, 문서 | `flex-frontend` |

## BE 이슈 조사 시

`flex-support-oncall/` 하위에서 작업한다. `flex-support-oncall/CLAUDE.md`의 도메인 라우팅과 brain/ 지식 시스템을 활용한다.
