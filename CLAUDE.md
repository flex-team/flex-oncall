# CLAUDE.md

## 이 repo는 무엇인가

온콜 업무를 위한 인덱스 repo. 관련 프로젝트들을 git submodule로 묶고, 이슈가 어느 코드베이스에 있는지 빠르게 찾는 시작점 역할을 한다.

- Always respond in Korean

## 셋업

```bash
# 처음 클론할 때 (서브모듈 포함)
git clone --recurse-submodules <repo-url>

# 이미 클론한 상태에서 서브모듈 초기화
git submodule update --init --recursive

# 서브모듈을 최신으로 업데이트
git submodule update --remote
```

### 서브모듈 추가하기

```bash
git submodule add <repo-url> <directory-name>
# 예: git submodule add https://github.com/flex-team/flex-timetracking-backend.git flex-timetracking-backend
```

## 서브모듈 맵

| 서브모듈 | 도메인 | 키워드 |
|---------|--------|--------|
| `flex-timetracking-backend` | 근태, 휴가, 스케줄링, 초과근무, 보상휴가, 연차촉진, 포괄임금 | 근무기록, 연차, 휴일대체, 출퇴근, 근무유형, 급여계산 |
| `flex-pavement-backend` | 알림, 푸시, 이메일 | 알림 미수신, CTA, notification |

> 서브모듈이 추가될 때마다 이 테이블을 업데이트할 것

## 도메인 → 코드 위치 가이드

### 근태/휴가 (`flex-timetracking-backend`)

- 근무유형(Work Rule): `/work-rule`
- 연차/맞춤휴가(Time Off): `/time-off`
- 근무기록(Work Record): `/work-record`
- 스케줄링(Work Schedule): `/work-schedule`
- 출퇴근(Work Clock): `/work-clock`
- 보상휴가(Compensatory Time Off): `/compensatory-time-off`
- 승인(Approval): `/approval`
- 외부 연동(External Work Clock): `/external-work-clock`
- 공휴일(Holiday): `/holiday`
- Operation API: 각 모듈의 `/operation-api` 하위

### 알림 (`flex-pavement-backend`)

- `flex-timetracking-backend` 알림 관련 코드가 이 repo를 참조

## 온콜 워크플로우

```
이슈 접수 (Linear/Slack)
  → 도메인 파악 (이 문서의 키워드 매핑 참조)
  → 쿡북 확인 (~/.claude/operation-notes/COOKBOOK.md)
  → 데이터 조사 (DB/OpenSearch/Kafka 스킬)
  → 원인 분석 및 해결
  → 운영 노트 기록 (~/.claude/operation-notes/{ticket-id}.md)
```

## 사용 가능한 조사 도구

온콜 이슈 조사에 쓸 수 있는 Claude Code 스킬:

| 스킬 | 용도 |
|------|------|
| `db:db-query` | Aurora MySQL DB 쿼리 (dev/qa/prod) |
| `opensearch:os-query-log` | 애플리케이션 로그 검색 (Kibana) |
| `opensearch:os-query-service` | TT 서비스 문서 조회 (근무스케줄, 휴가사용 등) |
| `operation-api:ops-api` | flex-raccoon Operation API 호출 |
| `kafka:kafka-query` | Kafka 토픽/메시지/컨슈머그룹 조회 |
| `slack:slack-search` | Slack 메시지/파일/채널 검색 |

## 운영 지식 참조

- **쿡북**: `~/.claude/operation-notes/COOKBOOK.md` — 도메인별 진단 체크리스트, SQL 템플릿, 과거 사례
- **티켓 노트**: `~/.claude/operation-notes/{ticket-id}.md` — 개별 티켓 분석/해결 기록
- **티켓 노트 작성 규칙**: `~/.claude/operation-notes/CLAUDE.md`
