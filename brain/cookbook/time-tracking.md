# 근태/휴가 (Time Tracking) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

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
<!-- TODO: 시나리오 테스트 추가 권장 — 선택적 근무 추천 휴게 자동 입력 조건 검증 -->
<!-- TODO: 시나리오 테스트 추가 권장 — 휴직 기간 휴가 등록 차단 + 휴가 기간 휴직 등록 허용 비대칭 검증 -->
