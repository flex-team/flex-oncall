# 근태/휴가 (Time Tracking) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 도메인 컨텍스트

### 이 도메인이 하는 일

출퇴근 기록, 근무시간 계산, 휴가(연차/보상휴가/커스텀) 관리, 휴일대체, 근무유형 관리를 담당한다. flex HR 제품의 가장 큰 도메인이며, 근로기준법에 직접 영향을 받는 영역이 많다.

### 핵심 개념

- **근무유형(`v2_customer_work_rule`)**: 회사별로 정의하는 근무 규칙 단위. 요일별 `DayWorkingType`(근무일/주휴일/휴무일)과 근무시간을 포함한다.
- **유저-근무유형 매핑(`v2_user_work_rule`)**: time-series 구조. REGISTER/CANCEL 이벤트가 쌓이며, 특정 날짜의 활성 근무유형은 `date_from`/`date_to` 범위로 해석한다. "현재" 근무유형이 아니라 **해당 날짜 시점의** 근무유형이 기준이다.
- **OpenSearch 문서**: 근무스케줄, 휴일대체 등 조회 성능을 위해 OpenSearch에 비정규화된 문서를 관리한다. 근무를 건드리지 않은 유저는 sync 이벤트가 발생하지 않아 문서 자체가 없을 수 있다.
- **근무시간 타입**: 법정근로시간(`statutoryWorkingMinutes`), 소정근로시간(`agreedWorkingMinutes`), 필수근로시간(`requiredWorkingMinutes`), 계약근로시간(`usualWorkingMinutes`) — 각각 법적 근거와 계산 기준이 다르다.

### 주요 흐름

1. **출퇴근 기록**: 앱/웹/외부기기(세콤 등) → Work Clock 이벤트 → 근무기록 생성
2. **휴일대체**: 약정휴일/주휴일을 근무일로 바꾸고, 다른 날을 쉬는 날로 지정. 교대근무는 약정휴일만, 비교대는 약정휴일+주휴일이 대상.
3. **휴가 사용**: 연차/보상휴가/커스텀 휴가 신청 → 승인 → 잔여 차감. 연차 정책의 부여 시작일 이전 사용 내역은 제품 내 미표시.
4. **보상휴가**: 초과근무 발생 → 보상휴가 부여 (단일/벌크) → lock 생성 → 근무 수정 차단

### 비즈니스 규칙

- **퇴근 타각 자정 조정**: 자정을 넘긴 퇴근이 다음날 종일휴가와 겹치면 휴가 시작 시간(00:00)으로 조정. 근로기준법상 휴가 시간과 근무 시간이 겹치면 안 되기 때문.
- **휴직/휴가 비대칭**: 휴가→휴직은 허용(갑작스런 휴직 발생, 기존 휴가 잔여 미차감), 휴직→휴가는 차단(유즈케이스 없음). 서비스 경계가 분리되어 있어(`flex-core-backend` / `flex-timetracking-backend`) 상호 검증이 의도적으로 비대칭.
- **추천 휴게**: 실시간 기록 시점이 아닌 **근무 확정 시점**에 판단/입력. 별도 등록 휴게와 겹치면 추천 휴게는 미등록.
- **포괄임금계약**: 월 중 계약 변경 시 Range별 독립 관리, 잔여량 이월 없음. `REGARDED_OVER`는 주기 종료일 포함 Range에만 귀속.

### 자주 혼동되는 것들

- **"현재 근무유형" vs "해당 날짜 시점 근무유형"**: 유저의 근무유형이 변경되었을 때, 문의 날짜 기준으로 `v2_user_work_rule`의 `date_from`/`date_to` 범위를 확인해야 한다. 현재 시점 기준으로 보면 원인을 못 찾는다.
- **OpenSearch 문서 없음 vs 데이터 이상**: 문서가 없는 것은 sync가 안 된 것이지 데이터 이상이 아니다. 수동 sync로 해결된다.
- **Work Clock(출퇴근 시각) vs Work Record(근무 기록)**: 출근시각/퇴근시각(`realCheckInTime`)은 물리적 타각, 시작시간/종료시간(`startTime`)은 이벤트 블록 기반 기록. 다른 데이터 소스다.
- **canCreateWorkRecordWithWorkClock 설정**: false이면 위젯 STOP 시 work_record_event는 REGISTER 타입으로 생성되지만 블럭(인정 근무)은 비어있음. null이면 기본값 true. FE 근무유형 설정에서 아무것도 안 건드리고 저장하면 true로 전달되므로, false는 관리자의 명시적 의도.
- **월별 연차 잔여 vs 내휴가 잔여**: 월별 연차 사용내역은 연도 말(12/31) 기준, 내휴가는 현재 월 기준. 입사 1주년 시점 월차 소멸로 차이 발생.
- **`ON_TIME` 퇴근 설정**: 유저 본인이 flex 앱에서 변경 가능. 정시 이후 모든 퇴근이 정시로 기록되므로, 외부기기 연동 환경에서 의도치 않은 결과 발생.

### 구현 특이사항

- **OpenSearch sync 지연**: 휴일대체 수정(CANCEL+재등록) 후 OpenSearch에 구 eventId가 잔존할 수 있다. `NON_NULL` + `doc()` partial update 조합이 원인. `/sync-os-work-schedule-advanced`로 재동기화 필요.
- **보상휴가 lock 비대칭**: 단일 부여에서 추출 0분인 날짜에도 lock이 생성되지만, 벌크 부여에서는 필터링된다. 미회수 assign의 lock이 잔존하여 근무 수정을 차단할 수 있다.
- **근무유형 삭제는 soft-delete**: `v2_customer_work_rule.active=false`. 유저 매핑(`v2_user_work_rule`)은 time-series라 매핑 존재 자체가 삭제를 막지 않는다. 해석 결과에서 해당 근무유형이 없으면 삭제 가능.
- **work-schedule-sync consumer group 구조**: `@FlexMessageKafkaListener` 21개가 1개 group ID(`workqueue-kafka-timetracking-search-work-schedule-sync-prod`)를 공유하며, 20개 토픽(75 파티션)을 구독. concurrency=3으로 pod당 63 consumer 인스턴스, 3 pod 기준 ~189 멤버. 이 구성에서 `CooperativeStickyAssignor` 단독 전환 시 STABLE↔PREPARING_REBALANCE 무한 루프 발생 확인(2026-04-01). pod 1대(60 멤버)로 줄여도 동일 현상. 공식 2단계 전환 절차를 따랐음에도 불안정하므로, 이 consumer group에서는 `RangeAssignor` 병행 설정 필수. 중장기로 group ID 분리 검토 필요.

---

## 데이터 접근

```sql
-- 휴일대체 미표기: 해당 유저+날짜 시점의 활성 근무유형 확인
SELECT uwr.id, uwr.user_id, uwr.customer_work_rule_id, uwr.date_from, uwr.date_to,
       cwr.name AS work_rule_name
FROM v2_user_work_rule uwr
  JOIN v2_customer_work_rule cwr ON uwr.customer_work_rule_id = cwr.id
WHERE uwr.customer_id = ? AND uwr.user_id = ?
  AND uwr.date_from <= ? AND uwr.date_to >= ?  -- ? = 문의 날짜
ORDER BY uwr.date_from DESC;

-- 휴일대체 미표기: 근무유형의 요일별 dayWorkingType 확인
-- v2_customer_work_rule에서 해당 요일 컬럼의 dayWorkingType 확인
-- WEEKLY_PAID_HOLIDAY(주휴일) = 휴일대체 대상, WEEKLY_UNPAID_HOLIDAY(휴무일) = 제외

-- 휴일대체 미표기: 수동 OS sync
POST /action/operation/v2/time-tracking/sync-os-work-schedule-advanced

-- 보상휴가 관련 Operation API
POST /api/operation/v2/exceeded-work/customers/{customerId}/users/{userId}/exceeded-works
GET /api/operation/v2/time-off/customers/{customerId}/users/{userId}/compensatory-time-off-status?fromDate=?&toDate=?

-- 퇴사자 포함 휴가 사용 현황 엑셀 다운로드 (주조직 없는 퇴직자도 포함)
POST /action/operation/v2/time-off/customers/{customerId}/time-offs/excel/used
-- Body: {"queryUserId": ?, "departmentIds": null, "dateFrom": "?", "dateTo": "?", "includeResignatedUsers": true}
-- departmentIds: null → 조직 필터 미적용, includeResignatedUsers: true → 퇴직자 포함
```

## 참고: 휴일대체 대상 판별 설계 테이블

| 근무유형 | 약정휴일 | 주휴일 | 휴무일 |
|---------|---------|--------|--------|
| 교대근무 | O | X | X |
| 그 외 | O | O | X |

- `DayWorkingType`: `WORKING_DAY`(근무일), `WEEKLY_PAID_HOLIDAY`(주휴일/유급), `WEEKLY_UNPAID_HOLIDAY`(휴무일/무급)

```sql
-- canCreateWorkRecordWithWorkClock 설정 확인
SELECT id, can_create_work_record_with_work_clock
FROM v2_customer_work_record_rule
WHERE id = ?;  -- ? = v2_customer_work_rule.customer_work_record_rule_id

-- 설정 변경 이력 확인
SELECT id, can_create_work_record_with_work_clock, rev, revtype
FROM v2_customer_work_record_rule_aud
WHERE id = ?
ORDER BY rev DESC;

-- 근무 이벤트 + 블럭 존재 확인
SELECT wre.id, wre.user_id, wre.date_from, wre.event_type
FROM v2_user_work_record_event wre
WHERE wre.user_id = ? AND wre.date_from >= ?;

SELECT * FROM v2_user_work_record_event_block
WHERE user_work_record_event_id = ?;
-- 블럭이 비어있고 이벤트 타입이 REGISTER(REGISTER_BY_WORK_CLOCK 아님)이면
-- canCreateWorkRecordWithWorkClock = false 가능성 높음
```

## 과거 사례

- **휴일대체 탭 미표기 — OS 문서 미생성**: 근무를 건드리지 않은 유저는 sync 이벤트 미발생 → OS 문서 없음 → 조회 누락. 수동 sync로 즉시 대응 — **버그 (설계 한계)** [CI-3949]
- **휴일대체 탭 미표기 — holidayProps null**: 문의 날짜 시점의 활성 근무유형에서 해당 요일이 휴무일(`WEEKLY_UNPAID_HOLIDAY`)이면 제외. 근무유형 변경 이력에 주의 (현재 근무유형이 아닌 **해당 날짜 시점** 기준) — **스펙** [CI-3949]
- **포괄계약 월 중 변경 시 공제 차이**: Range별 독립 관리, 잔여량 이월 없음 — **스펙** [CI-3868]
- **보상휴가 부여 불가 (10/17 비대칭)**: V3 조회 API와 부여 API의 `forAssign` 모드 차이로 기부여 필터 불일치 — **버그** [CI-3858]
- **휴일대체 기간 커스텀**: 회사별 config 변경으로 해결, 코드 수정 불필요 — **스펙** [CI-3897] [CI-4186] [CI-4199]
- **여러날 휴가 스케줄 편집 시 소실**: FE 판별 로직 한계 + BE 응답에 published 휴가일 정보 누락 — **버그** [CI-3892]
- **퇴사자 휴가 데이터 웹 UI 누락**: 주조직 없는 퇴직자가 조직 기반 필터링에서 제외됨. Operation API(`departmentIds: null`)로 우회 추출 — **스펙 (웹 UI 한계)** [CI-3976]
- **세콤/캡스/텔레캅 퇴근이 정시로 고정**: 유저 본인이 flex 앱에서 퇴근 설정을 `ON_TIME`(정시)으로 변경 → 정시 이후 모든 퇴근이 정시로 기록. 날짜별 퇴근 기록 비교로 변곡점 특정 → DB/OpenSearch로 설정 변경 시점·주체 확인 → 본인 변경 확인 → 설정 재변경 안내 — **스펙** [CI-4145]
- **퇴근 타각 자정 조정**: 자정 넘긴 퇴근이 다음날 종일휴가와 겹치면 휴가 시작 시간(00:00)으로 조정. `adjustWorkClockStopTime()` 휴가 겹침 체크에 의한 정상 동작 — **스펙** [CI-3979]
- **위젯 퇴근 후 근무 그래프 미표시**: `canCreateWorkRecordWithWorkClock = false` 설정 시 위젯 STOP은 200 반환하지만 work_record_event_block 미생성(인정 근무 미반영). 관리자가 의도적으로 설정 변경한 경우 고객 소통으로 전환 — **스펙** [CI-4372]
- **휴직/휴가 비대칭 검증**: 유즈케이스 기반 의도적 설계. 휴가→휴직 허용(갑작스런 휴직 발생 시, 기존 휴가 잔여 미차감 처리), 휴직→휴가 차단(유즈케이스 없음). 서비스 경계 분리: 휴직(`flex-core-backend`) / 휴가(`flex-timetracking-backend`) — **스펙** [CI-4120]
- **선택적 근무 추천 휴게 미입력**: 추천 휴게는 실시간 기록 시점이 아닌 **근무 확정 시점**에 판단/입력. 별도 등록 휴게와 겹치지 않으면 자동 등록, 겹치면 미등록 — **스펙** [QNA-1922]
- **연차 사용 내역 사라짐**: 연차 정책 부여 시작일 이전 사용 내역은 제품 내 미표시. 엑셀에는 원시 데이터 존재. — **스펙** [QNA-1920]
- **근태기록 리포트 컬럼 차이**: 출근시각/퇴근시각(Work Clock)과 시작/종료시간(이벤트 블록)은 다른 소스. 승인 없는 기록은 관리자 직접 수정. 당일 승인상태는 다운로드 시점 기준 — **스펙** [QNA-1928]
- **휴일대체 사후신청 버튼 — 승인라인 미검증 노출**: `original-holiday-info` API가 승인라인 유효성을 체크하지 않아, 1차 조직장 미배치 등 승인 불가 구성원에게도 사후신청 버튼 표시. 관리자 직접 대체일 지정으로 우회 — **버그** [CI-4130]
- **월별 연차 사용내역 vs 내휴가 잔여 차이**: `totalRemainingDays`는 연도 말(12/31) 기준, 내휴가는 현재 월 기준. 입사 1주년 시점 월차 소멸로 시점별 잔여 차이 발생 — **스펙** [CI-4140]
<!-- TODO: 시나리오 테스트 추가 권장 — 입사 1주년 전후 월별 연차 사용내역 vs 내휴가 잔여 검증 -->
- **보상휴가 회수 후 잠금 미해제 — 고아 lock**: 단일 부여 경로에서 추출 0분인 날짜에도 lock 생성 (벌크 부여는 필터링됨). 미회수 assign의 lock이 잔존하여 근무 수정 차단 — **조사 중 (버그 추정)** [CI-4147]
- **근무유형 적용 시 500 오류 — 매핑 없는 유저**: `validateBulk`의 `.first {}` 호출이 매핑 없는 유저에서 `NoSuchElementException` 발생. 원인: 근무유형 삭제 후 유저 맵핑 취소 시 비활성 근무유형이 잔존하여 유효 매핑 없는 상태. 데이터 보정(CANCEL INSERT)으로 즉시 대응, `.firstOrNull {}` 방어 처리 코드 수정 예정 — **버그** [CI-4180]
- **휴일대체 취소 불가 — OpenSearch sync 지연**: 휴일대체 수정(CANCEL+재등록) 후 OpenSearch 문서에 구 eventId가 잔존하여 FE가 이미 CANCEL된 ID로 취소 요청 → 400 오류. `NON_NULL` + `doc()` partial update 조합이 원인. `/sync-os-work-schedule-advanced`로 재동기화하여 해결 — **버그 (OpenSearch sync)** [CI-4217]
- **Kafka consumer rebalance 무한 루프**: `flex-v2-backend-commons` #1451에서 `CooperativeStickyAssignor` 단독 적용 후, `work-schedule-sync` consumer group이 STABLE↔PREPARING_REBALANCE 반복. `CommitFailedException` 200건+ 발생. 21개 리스너 × 1 group ID × 20토픽 구성에서 cooperative 전환 불안정. assignor를 `RangeAssignor,CooperativeStickyAssignor`로 오버라이드하여 정상화 — **인프라 (config 오버라이드)** [kafka-rebalance-issue-report]
<!-- TODO: 시나리오 테스트 추가 권장 — 선택적 근무 추천 휴게 자동 입력 조건 검증 -->
<!-- TODO: 시나리오 테스트 추가 권장 — 휴직 기간 휴가 등록 차단 + 휴가 기간 휴직 등록 허용 비대칭 검증 -->
