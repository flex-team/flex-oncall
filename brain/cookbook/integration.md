# 외부 연동 (Integration) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 세콤 이벤트 조회 (Metabase)
-- https://metabase.dp.grapeisfruit.com/question/3565

-- 위젯 draft 이벤트 (Metabase)
-- https://metabase.dp.grapeisfruit.com/question/4716-draft

-- 특정 유저의 세콤 이벤트 조회 (수신 확인)
SELECT id, event_time, event_type, created_at
FROM v2_user_external_provider_event
WHERE customer_external_provider_id = ? AND user_id = ?
  AND event_time >= ?
ORDER BY event_time;

-- 출퇴근 위젯 draft 이벤트 (중복 등록 확인)
SELECT id, event_time, target_time, fail_message, registered_user_work_clock_event_id
FROM v2_user_work_clock_draft_event
WHERE user_id = ? AND created_at >= ?
ORDER BY created_at;

-- 외부 연동 provider 설정 조회 (ODBC connection limit 확인)
SELECT id, customer_id, provider_type, account_id, odbc_connection_limit, active,
       work_clock_register_enabled, date_from, date_to
FROM v2_customer_external_provider
WHERE customer_id = ?;
```

**로그 확인 (연동 상태 변경 추적):**
- log-dashboard → 조건:
  - `json.ipath.keyword`: `/api/v2/time-tracking/customers/{customerIdHash}/external-providers/{externalProvider}`
  - `json.authentication.customerId`: 해당 회사 ID
  - `json.authentication.email`: 변경한 사용자 이메일

## 과거 사례

- **세콤 연동 비활성화 기간 데이터 소급 불가**: 시스템 설계상 비활성화 기간 수신 데이터 저장 안 함 — **스펙** [CI-3849]
- **세콤 수동 전송 미반영**: 퇴근→출근 역순 수신으로 위젯 draft 불일치 — **조사 중** [CI-3861]
- **세콤/캡스/텔레캅 퇴근이 정시로 고정**: 유저 본인이 flex 앱에서 `ON_TIME` 설정으로 변경한 것이 원인. 날짜별 퇴근 기록(이벤트 vs 기록)을 비교하여 변곡점 특정 → DB/OpenSearch로 설정 변경 시점·주체 확인 — **스펙** [CI-4145]
- **세콤 연동 프로토콜 타입 문의**: 고객사에서 방화벽 허용 설정을 위해 프로토콜 타입을 문의. PostgreSQL 고정 설계로 API에 별도 필드 없음. 고객사에 "TCP/PostgreSQL 프로토콜, 포트 5432" 직접 안내로 해결. — **스펙**
- **출입연동 커넥션 수 설정**: 업체별 PC당 커넥션 수 기본값 — 캡스 2, 세콤 2, KT(텔레캅) 3. admin-shell(`https://admin-shell.flexis.team/time-tracking/admin/external-provider.html`)에서 변경 — **운영 요청** [QNA-1842]
- **다법인 workspace customerKey 충돌**: 다법인 지원 코드 추가 시 기존 데이터 마이그레이션 누락으로 workspace 내 동일 providerType에 서로 다른 customerKey 존재 → 신규 등록 실패. 데이터 패치로 key 통일 필요 — **버그 (데이터 마이그레이션 누락)** [TT-16783]
- **세콤 출근 미반영 — 잔존 위젯에 의한 dry-run 차단**: 이전 근무 위젯 미종료 → 새 출근 이벤트의 dry-run validation 실패(`WORK_CLOCK_START_CONTINUOUS_NOT_ALLOWED`). Operation API로 잔존 위젯 수동 종료 후 재처리 — **스펙 (정상 차단)** [CI-4157]
- **세콤 다중 터미널 동시 이벤트 → 중복 START 등록**: Kafka 파티션 분산 + REQUIRES_NEW 트랜잭션 + REPEATABLE READ 격리 → 동시 dry-run에서 서로의 미커밋 데이터 미가시. `isDraftEventRegistrationAllowed`의 이벤트 타입 미구분도 기여 — **버그 (조사 중)** [CI-4165]
- **세콤 ODBC 연결 실패 — CONNECTION LIMIT 0**: `odbc_connection_limit=0`으로 PostgreSQL ROLE의 CONNECTION LIMIT 0 적용, 모든 ODBC 연결 차단. JPA Entity 기본값이 0이므로 계정 생성 시 `getDefaultConnectionLimit()` 누락 가능. Operation API로 connectionLimit=2 변경으로 해결 — **설정 오류** [CI-4190]
- **캡스 수동 동기화 전송 실패 — 테이블 매핑 설정 오류**: Grafana 캡스 RDB 모니터링에서 `e_date` 컬럼 오류 확인 → 고객이 캡스 테이블 매핑을 가이드대로 설정하지 않은 것이 원인. 고객 안내로 해결 — **고객 설정 오류** [CI-4202]
- **캡스 연동 연결 실패 — 방화벽 아닌 PW 오입력**: 캡스 기사가 원격 지원 중 PW를 잘못 입력하여 연결 실패. 고객은 방화벽 문제로 추정했으나 DB 로그에서 PW 실패 확인. 2차 문의(시작→정지 복귀)에서는 실제 방화벽 차단 → 도메인 기반 예외처리 안내 — **운영 (고객 환경)** [FT-12290]
