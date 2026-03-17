# 운영 쿡북

> 이슈 조사 전에 이 문서를 먼저 참조하면 조사 시간을 단축할 수 있다.
> 각 항목의 상세는 출처 이슈 노트를 참조.

## 도메인별 진단 가이드

### 알림 (Notification)

#### 진단 체크리스트
문의: "알림이 안 왔어요" / "알림 클릭 시 이상한 곳으로 이동해요" / "메타베이스에서 알림 내용이 안 보여요"
1. 수신자가 승인자이면서 참조자인지 확인 → 중복 제거로 참조 알림 미수신 가능 (승인 알림은 정상 수신) [CI-3910]
2. `notification_deliver` 테이블에서 실제 발송된 `notification_type` 확인
3. 메타베이스에서 `title_meta_map`이 `[]`인 경우 → Core 알림은 토픽 제목이 고정("내 정보 변경" 등)이므로 정상. `notification.message_data_map`을 조회해야 실제 내용 확인 가능 [CI-4122]
4. 이메일 CTA 이동 대상이 이상한 경우 → 알림 유형 확인: `approve.refer`(등록했어요) vs `approved.refer`(승인되었어요) [CI-3914]
5. 클릭 시점에 승인이 이미 완료되었는지 확인 → 완료된 건은 할 일에 없으므로 홈피드로 리다이렉트 [CI-3914]
6. 수신자 locale 확인 → 디폴트 KOREAN, en/ko 템플릿 CTA URL이 다를 수 있음 [CI-3914]

#### 데이터 접근
```sql
-- 수신자의 알림 발송 이력
SELECT nd.*, n.notification_type, n.message_data_map
FROM notification_deliver nd
  LEFT JOIN notification n ON nd.notification_id = n.id
WHERE nd.receiver_id = ?
  AND n.db_created_at >= ?;

-- 특정 승인 건의 알림 이력 (notification_topic_id 기준)
SELECT *
FROM notification_deliver nd
  LEFT JOIN notification n ON nd.notification_id = n.id
WHERE nd.notification_topic_id = ?;

-- Core 알림 실제 내용 확인 (title_meta_map이 빈 경우)
SELECT nd.id, n.notification_type, n.message_data_map, nt.topic_type, nt.title_meta_map,
       FROM_UNIXTIME(nd.created_at / 1000) AS delivered_at
FROM notification_deliver nd
  JOIN notification n ON n.id = nd.notification_id
  LEFT JOIN notification_topic nt ON nd.notification_topic_id = nt.id
WHERE nd.id = ?;

-- 수신자 locale 확인 (디폴트: KOREAN)
SELECT * FROM member_setting WHERE member_id = ?;
```

#### 과거 사례
- **승인자=참조자 중복 알림 제거**: 동일 사용자가 승인자이면서 참조자일 때 승인 알림 1건으로 통합. 참조 알림 미수신은 정상 — **스펙** [CI-3910]
- **이메일 CTA 이동 대상 차이**: `approve.refer` → 할 일, `approved.refer` → 홈피드. 클릭 시점에 승인 완료된 건은 홈피드로 리다이렉트 — **스펙** [CI-3914]
- **en/ko 템플릿 CTA URL 불일치**: 3건 발견 (`approve.refer.cta-web`, `remind.work-record.missing.one.cta-web`, `workflow.task.request-view.request.cta-web`) — **별도 버그** [CI-3914]
- **Core 알림 title_meta_map 빈값**: Core 인사정보 변경 알림(`FLEX_USER_DATA_CHANGE`)의 토픽 제목은 고정("내 정보 변경")이므로 `titleMetaMap = emptyMap()` — **스펙**. 실제 내용은 `notification.message_data_map.changedDataName`으로 확인 [CI-4122]

---

### 연차 촉진 (Annual Time-Off Promotion)

#### 진단 체크리스트
문의: "연차 사용 계획 작성 알림이 계속 와요" / "촉진 문서가 화면에 안 보여요" / "연차 대상이 아닌데 촉진 알림이 와요"
1. `annual_time_off_boost_history` 테이블에서 해당 건의 `status`, `boosted_at` 확인
2. `boosted_at`이 UTC 기준 연도 경계(12/31 23:xx)인지 확인 → KST 변환 시 다음 연도인데 UTC로는 이전 연도 → 목록 조회에서 누락 [CI-3907], [CI-3809]
3. 관리자에 의해 종료된 이력이 있는지 확인 → 히든 스펙: 종료 이력 있으면 기한 지난 건은 목록에서 필터링, 단 알림은 필터링 안 됨 [CI-3777]
4. MONTHLY/MONTHLY_FINAL 간 연동 여부 확인 → 1차/2차는 독립 동작, 2차 완료해도 1차 알림 지속 가능 [CI-3809]
5. 사용자의 연차 정책이 변경되었는지 확인 → `v2_user_customer_annual_time_off_policy_mapping`의 `modified_at`과 촉진 이력의 `created_date` 비교. 정책이 `enabled_annual_time_off_policy = false`인데 PENDING_WRITE 이력이 있으면 정책 변경 전 잔존 이력 → TODO/알림 수동 정리 필요 [CI-3932]

#### 데이터 접근
```sql
-- 촉진 이력 조회
SELECT id, customer_id, user_id, status, boost_type, boosted_at, dissipated_at, canceled_at
FROM annual_time_off_boost_history
WHERE customer_id = ? AND user_id = ?
ORDER BY boosted_at DESC;

-- 즉시 대응: 촉진 이력 취소 처리
UPDATE annual_time_off_boost_history
SET status = 'CANCELED',
    canceled_at = NOW(),
    canceled_user_id = 0,
    last_modified_date = NOW(),
    last_modified_by = 'operation'
WHERE id = ?;

-- 정책 변경 후 PENDING_WRITE 잔존 확인 (정책 변경 시점 vs 촉진 생성 시점 비교)
SELECT h.id, h.user_id, h.status, h.boosted_at, h.created_date,
       m.modified_at AS policy_mapped_at,
       p.enabled_annual_time_off_policy
FROM annual_time_off_boost_history h
  JOIN v2_user_customer_annual_time_off_policy_mapping m
    ON h.customer_id = m.customer_id AND h.user_id = m.user_id
  JOIN v2_customer_annual_time_off_policy p
    ON m.annual_time_off_policy_id = p.id
WHERE h.customer_id = ? AND h.user_id = ?
  AND h.status = 'PENDING_WRITE'
  AND p.enabled_annual_time_off_policy = false;
```

#### 과거 사례
- **연말 촉진 → 다음 해 목록 누락**: `boosted_at` UTC 저장 vs 조회 범위 KST 연도 기준 → 연도 경계 불일치 — **버그** [CI-3907]
- **월차 2차 완료 후 1차 알림 지속**: MONTHLY/MONTHLY_FINAL 독립 동작 + UTC/KST 연도 경계 불일치 — **버그** [CI-3809]
- **히든 스펙 필터링 → 알림-화면 불일치**: 관리자 종료 시 목록에서 제외하는 히든 스펙(PR #750)이 알림에는 미적용 — **버그** [CI-3777]
- **정책 변경(미지급) 후 PENDING_WRITE 잔존**: 연차 미지급 정책으로 변경 시 기존 촉진 이력/TODO/알림 자동 정리 로직 없음 → 홈피드에 표시되나 델리에서는 버킷 매칭 숨김 처리로 미표시 — **버그** [CI-3932]

---

### 근태/휴가 (Time Tracking)

#### 진단 체크리스트
문의: "휴일대체 기간이 안 맞아요" / "보상휴가 부여 안 돼요" / "포괄 공제가 안 맞아요" / "휴일대체 탭에 날짜가 안 보여요" / "퇴사자 휴가 데이터 추출해주세요" / "퇴근 시간이 잘렸어요" / "휴직 기간에 휴가가 있어요"
1. 휴일대체 탭 미표기 → 먼저 OpenSearch dev tools로 해당 유저+날짜 문서 존재 확인 [CI-3949]
   - **문서 자체가 없음** → 근무를 건드리지 않은 유저는 sync 이벤트 미발생으로 OS 문서 미생성. 수동 sync 실행: `POST /action/operation/v2/time-tracking/sync-os-work-schedule-advanced` [CI-3949]
   - **문서는 있는데 `holidayProps`가 null** → 해당 날짜 **시점의** 활성 근무유형 확인 (현재 근무유형이 아님!). `v2_user_work_rule`에서 date_from/date_to 범위로 확인 → 해당 요일이 `WEEKLY_UNPAID_HOLIDAY`(휴무일)이면 스펙대로 제외. `WEEKLY_PAID_HOLIDAY`(주휴일)인데 null이면 버그 → 추가 조사 필요 [CI-3949]
2. 휴일대체 기간 문의 → 회사별 gap 커스텀 설정 확인 (`TrackingExperimentalDynamicConfig`) → config 변경으로 해결 가능 [CI-3897]
3. 보상휴가 "부여가능한 시간 없음" → `forAssign` 모드에 따른 기부여 필터 차이 확인. 우회: 1일 단위로 분리 부여 [CI-3858]
4. 포괄계약 공제 불일치 → 월 중 계약 변경 시 Range 분할 확인. `REGARDED_OVER`는 주기 종료일 포함 Range에만 귀속 [CI-3868]
5. 여러날 휴가 스케줄 편집 시 소실 → FE 버그, `timeoffEventId` 기반 판별 한계 [CI-3892]
6. 퇴사자 휴가 데이터 추출 → 웹 UI(휴가 관리 > 사용 내역)에서 "퇴직자 포함"으로 먼저 시도. 특정 구성원 누락 시 주조직 존재 여부 확인 → 주조직 없으면 Operation API 사용 (`departmentIds: null`, `includeResignatedUsers: true`) [CI-3976]
7. 퇴근 시간이 자정(00:00)으로 잘린 경우 → 대상 구성원의 **다음날 휴가** 등록 여부 확인. 다음날 종일휴가가 있으면 휴가 시작 시간(00:00)으로 조정되는 스펙. 안내: "자정을 넘긴 퇴근 시간이 다음날 종일휴가와 겹치면 휴가 시작 시간으로 조정됩니다" [CI-3979]
8. 휴직 기간에 휴가가 남아있는 경우 → 의도된 스펙. 휴가→휴직 허용(유즈케이스: 미래 휴가 등록 후 갑작스런 휴직 발생, 휴직 기간 휴가는 **잔여 미차감** 처리), 휴직→휴가 차단(유즈케이스 없음). 운영 가이드: 필요 시 휴직 등록 전 기존 휴가를 먼저 취소/조정 [CI-4120]

#### 데이터 접근
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

#### 참고: 휴일대체 대상 판별 설계 테이블
| 근무유형 | 약정휴일 | 주휴일 | 휴무일 |
|---------|---------|--------|--------|
| 교대근무 | O | X | X |
| 그 외 | O | O | X |

- `DayWorkingType`: `WORKING_DAY`(근무일), `WEEKLY_PAID_HOLIDAY`(주휴일/유급), `WEEKLY_UNPAID_HOLIDAY`(휴무일/무급)

#### 과거 사례
- **휴일대체 탭 미표기 — OS 문서 미생성**: 근무를 건드리지 않은 유저는 sync 이벤트 미발생 → OS 문서 없음 → 조회 누락. 수동 sync로 즉시 대응 — **버그 (설계 한계)** [CI-3949]
- **휴일대체 탭 미표기 — holidayProps null**: 문의 날짜 시점의 활성 근무유형에서 해당 요일이 휴무일(`WEEKLY_UNPAID_HOLIDAY`)이면 제외. 근무유형 변경 이력에 주의 (현재 근무유형이 아닌 **해당 날짜 시점** 기준) — **스펙** [CI-3949]
- **포괄계약 월 중 변경 시 공제 차이**: Range별 독립 관리, 잔여량 이월 없음 — **스펙** [CI-3868]
- **보상휴가 부여 불가 (10/17 비대칭)**: V3 조회 API와 부여 API의 `forAssign` 모드 차이로 기부여 필터 불일치 — **버그** [CI-3858]
- **휴일대체 기간 커스텀**: 회사별 config 변경으로 해결, 코드 수정 불필요 — **스펙** [CI-3897]
- **여러날 휴가 스케줄 편집 시 소실**: FE 판별 로직 한계 + BE 응답에 published 휴가일 정보 누락 — **버그** [CI-3892]
- **퇴사자 휴가 데이터 웹 UI 누락**: 주조직 없는 퇴직자가 조직 기반 필터링에서 제외됨. Operation API(`departmentIds: null`)로 우회 추출 — **스펙 (웹 UI 한계)** [CI-3976]
- **퇴근 타각 자정 조정**: 자정 넘긴 퇴근이 다음날 종일휴가와 겹치면 휴가 시작 시간(00:00)으로 조정. `adjustWorkClockStopTime()` 휴가 겹침 체크에 의한 정상 동작 — **스펙** [CI-3979]
- **휴직/휴가 비대칭 검증**: 유즈케이스 기반 의도적 설계. 휴가→휴직 허용(갑작스런 휴직 발생 시, 기존 휴가 잔여 미차감 처리), 휴직→휴가 차단(유즈케이스 없음). 서비스 경계 분리: 휴직(`flex-core-backend`) / 휴가(`flex-timetracking-backend`) — **스펙** [CI-4120]
<!-- TODO: 시나리오 테스트 추가 권장 — 휴직 기간 휴가 등록 차단 + 휴가 기간 휴직 등록 허용 비대칭 검증 -->

---

### 스케줄링 (Scheduling)

#### 진단 체크리스트
문의: "스케줄 게시가 안 돼요" / "정시 전 출근 불가가 안 먹혀요" / "연장근무가 이상해요"
1. 게시 차단 문의 → dry-run API 응답의 `validationLevel` 확인 (WARN vs ERROR). FE가 WARN을 ERROR로 처리하는 버그 있음 [CI-3862]
2. 정시 전 출근 불가 미작동 → 스케줄이 실제로 **게시**되었는지 확인 (임시 저장 ≠ 게시). 게시 안 된 상태면 정시 기준 없음 [CI-3866]
3. 주 연장근무 발생 → `agreedWorkingMinutes`(근무규칙) vs `requiredWorkingMinutes`(스케줄) 차이 확인 [CI-3839]

#### 데이터 접근
```sql
-- 일별 게시된 스케줄
SELECT * FROM v2_user_non_repetitive_work_plan
WHERE customer_id = ? AND user_id = ? AND date = ?;

-- 게시 이벤트
SELECT * FROM v2_user_work_plan
WHERE customer_id = ? AND user_id = ?;

-- 임시 저장된 스케줄 (게시 전)
SELECT * FROM v2_user_shift_schedule_draft
WHERE customer_id = ? AND user_id = ? AND date = ?;
```

#### 과거 사례
- **주휴일 없는 게시 차단**: BE는 WARN 반환 정상, FE가 WARN=ERROR 처리 — **버그 (FE)** [CI-3862]
- **게시 안 된 스케줄 + 정시 전 출근 불가**: 임시 저장은 게시 아님, 정시 기준 제공 안 함 — **스펙** [CI-3866]
- **주 연장근무 비대칭**: 근무규칙 기반(40h) vs 스케줄 기반(32h) 계산 차이 — **보류** [CI-3839]

---

### 교대근무 (Shift)

#### 진단 체크리스트
문의: "교대근무 관리 화면에서 일부 구성원만 조회됩니다" / "퇴근 자동 조정이 안 돼요" / "초단시간 근로자 연장근무가 이상해요"

1. 구성원 조회 누락 → 해당 관리자의 **근무 권한**과 **휴가 권한** 범위 확인 → 전체 구성원 vs 소속 및 하위 조직 [CI-4103]
2. 두 권한 중 **범위가 좁은 쪽**이 최종 조회 범위를 결정함. 권한 범위를 맞추도록 안내
3. 교대근무 휴무일에 스케줄 근무 시 퇴근 자동 조정 실패 → `baseAgreedDayWorkingMinutes`가 휴무일에 0이 되어 일연장 조건이 null로 평가 — **버그 (수정 예정)** [CI-4119]
4. 초단시간 근로자 연장근무 계산 이상 → `baseAgreedDayWorkingMinutes`가 휴무일에 법적 소정근로시간(예: 168분)으로 사용되어 일연장이 과소 계산. 주휴일은 480분(8시간) 고정인데 휴무일만 비대칭 — **버그 추정** [CI-4048]

**고객 안내 예시 (구성원 누락):**
> 교대근무 관리 화면에서는 **근무 권한**과 **휴가 권한**을 **모두** 보유한 조직의 구성원만 표시됩니다.
> 전체 구성원을 조회하시려면 두 권한 모두 동일한 범위로 설정해 주세요.

#### 과거 사례
- **교대근무 관리 화면 구성원 일부 누락**: 근무 조회 권한(전체)과 휴가 조회 권한(소속 및 하위 조직)의 교집합으로 필터링되어 일부만 표시. 고객에게 두 권한 범위를 맞추도록 안내. — **스펙** [CI-4103]
- **교대근무 조직 필터링 합집합 버그**: 조직 레벨에서 합집합으로 구현되어 있던 것을 교집합으로 수정 (#11994). — **버그 (수정 완료)** [CI-4103]
- **교대근무 휴무일 퇴근 자동 조정 실패**: `baseAgreedDayWorkingMinutes=0`으로 일연장 조건이 null → 퇴근 자동 조정 불가. 유급휴일은 480분 기준 별도 처리되나 휴무일은 미고려 — **버그 (수정 예정)** [CI-4119]
- **초단시간 근로자 연장근무 과소 계산**: 휴무일의 `baseAgreedDayWorkingMinutes` 기준 비대칭. 노무 가이드 변경("휴무일도 8시간 기준") 미반영 추정 — **버그 추정** [CI-4048]

---

### 외부 연동 (Integration)

#### 진단 체크리스트
문의: "세콤 연동이 풀렸어요" / "수동 전송했는데 반영 안 돼요" / "세콤 연동 프로토콜 타입이 뭔가요?"
1. 연동 비활성화 주체 확인 → 구독 해지 외 자동 변경 없음. log-dashboard에서 API 호출 이력 확인 [CI-3849]
2. 비활성화 상태에서 수동 전송 → 비활성화 기간 데이터는 소급 불가 [CI-3849]
3. 수동 전송 반영 안 됨 → 세콤 데이터 수신 순서 확인 (퇴근→출근 역순 수신 가능) [CI-3861]
4. 프로토콜 확인 → **PostgreSQL (TCP/IP)** 고정. `CustomerExternalProviderConnectionInfoDto` 응답의 `url`, `port`, `user`, `password`, `database` 필드를 참조
5. 출입연동 커넥션 수 변경 요청 → admin-shell에서 직접 변경. 업체별 기본값: 캡스 2, 세콤 2, KT(텔레캅) 3 [QNA-1842]

**고객사 방화벽 허용 설정 안내값:**

| 항목 | 값 |
|------|-----|
| 프로토콜 | TCP |
| 접속 방식 | PostgreSQL 직접 연결 (ODBC/JDBC) |
| 대상 호스트 | `flex-secom.flex.team` |
| 포트 | `5432` |
| 데이터베이스 | `postgres` |

#### 데이터 접근
```sql
-- 세콤 이벤트 조회 (Metabase)
-- https://metabase.dp.grapeisfruit.com/question/3565

-- 위젯 draft 이벤트 (Metabase)
-- https://metabase.dp.grapeisfruit.com/question/4716-draft
```

**로그 확인 (연동 상태 변경 추적):**
- log-dashboard → 조건:
  - `json.ipath.keyword`: `/api/v2/time-tracking/customers/{customerIdHash}/external-providers/{externalProvider}`
  - `json.authentication.customerId`: 해당 회사 ID
  - `json.authentication.email`: 변경한 사용자 이메일

#### 과거 사례
- **세콤 연동 비활성화 기간 데이터 소급 불가**: 시스템 설계상 비활성화 기간 수신 데이터 저장 안 함 — **스펙** [CI-3849]
- **세콤 수동 전송 미반영**: 퇴근→출근 역순 수신으로 위젯 draft 불일치 — **조사 중** [CI-3861]
- **세콤 연동 프로토콜 타입 문의**: 고객사에서 방화벽 허용 설정을 위해 프로토콜 타입을 문의. PostgreSQL 고정 설계로 API에 별도 필드 없음. 고객사에 "TCP/PostgreSQL 프로토콜, 포트 5432" 직접 안내로 해결. — **스펙**
- **출입연동 커넥션 수 설정**: 업체별 PC당 커넥션 수 기본값 — 캡스 2, 세콤 2, KT(텔레캅) 3. admin-shell(`https://admin-shell.flexis.team/time-tracking/admin/external-provider.html`)에서 변경 — **운영 요청** [QNA-1842]

---

### 계정/구성원 (Account / Member)

#### 진단 체크리스트
문의: "이메일 변경해주세요" / "구성원 이메일 일괄 변경해주세요"
1. 단건 이메일 변경 → `PATCH /action/v2/operation/core/customers/{customerId}/users/{userId}/emails/change` [CI-4118]
2. 일괄 이메일 변경 → `PATCH /action/v2/operation/core/customers/{customerId}/emails/change/bulk` [CI-4124]
   - ⚠️ 존재하지 않는 oldEmail이 1건이라도 포함되면 **전체 실패** (`IllegalArgumentException`)
   - 사전에 DB에서 대상 이메일 존재 여부 확인 필수
3. 다법인 사용자 확인 → `primary_user_id`가 NULL이 아니면 primary 회사에서만 변경 가능 [CI-4118]
4. 검증된 이메일(verified) 확인 → 이미 검증된 이메일은 관리자가 변경 불가, Operation API 사용 필요 [CI-4118]

#### 데이터 접근
```sql
-- 대상 구성원 조회 (이메일 변경 전 확인)
SELECT id, customer_id, email, primary_user_id, deleted_date
FROM user
WHERE customer_id = ?
  AND deleted_date IS NULL
ORDER BY email;

-- 특정 이메일 사용자 조회
SELECT id, customer_id, email, primary_user_id, deleted_date
FROM user
WHERE customer_id = ?
  AND email LIKE ?;
```

#### 과거 사례
- **단건 이메일 변경 (퇴사자 관리자 계정)**: 스폰서십 등록 계정의 관리자 이메일이 퇴사자. Operation API 단건 변경으로 처리 — **운영 요청** [CI-4118]
- **일괄 이메일 변경 (도메인 변경)**: 회사 도메인 변경으로 43명 이메일 일괄 변경. 1차 호출 시 미존재 이메일 1건으로 전체 실패 → 제외 후 재호출로 성공 — **운영 요청** [CI-4124]

---

### 데이터 추출 (Data Export)

#### 진단 체크리스트
문의: "엑셀 다운로드가 안 돼요" / "다운로드 실패해요"
1. 근무 기록 다운로드 실패 → consumer → core-api 내부 호출 시 OkHttp 소켓 타임아웃(3초) 확인. 대규모 데이터(수백 명) 다운로드 시 타임아웃 발생 가능 [CI-4121]
2. 특정 구성원만 누락 → "근태/휴가" 도메인의 퇴사자 휴가 데이터 추출 항목 참조 [CI-3976]

#### 과거 사례
- **근무 기록 다운로드 타임아웃**: consumer → core-api 간 OkHttp 3초 타임아웃으로 `SocketTimeoutException`. 32건 실패 — **버그 (조사 중)** [CI-4121]

---

### 목표 (Goal/OKR)

#### 진단 체크리스트
문의: "다른 연도 목표가 보여요" / "목표 필터가 안 먹혀요" / "회색 목표가 뭐예요?"
1. **cross-year 트리 구조 확인** → 사용자가 이전 연도 root 목표 하위에 올해 자식 목표를 배치했는지 확인 [CI-4126]
   - `root-objectives` API는 올해 목표의 root를 트리 탐색으로 찾으므로, root가 이전 연도면 `hit=false`로 포함
   - FE는 `hit=false` 목표를 **회색으로 구분 표시** — 이는 의도된 스펙
2. 회색 목표의 의미 → "직접 필터에 해당하지는 않지만, 하위에 해당하는 목표가 있어서 관계성을 보여주기 위해 표시"
3. `root-objectives-by-aside` API는 Matrix 기반 검색이므로 cycle 필터 정상 적용 — 이 API에서는 cross-year 문제 없음

#### 스펙: root-objectives API의 hit 필드
- BE `ObjectiveSearchServiceImpl.filterRootObjective()`에서 `hitMap` 생성:
  ```kotlin
  // cycle 조건에 맞지 않을 수 있다. Hit 여부를 어플리케이션 레벨에서 처리
  val cycleIds = cycles.toSet()
  val hitMap = objectives.associate { it.identity.id.toString() to (it.cycle in cycleIds) }
  ```
- `findRootObjectives` SQL: 서브쿼리에서 요청 cycle에 해당하는 목표를 찾고, `root_objective_id`로 root를 JOIN하되 **root에는 cycle 필터를 적용하지 않음** (설계 의도)
- FE: `hit=true` → 정상 표시, `hit=false` → 회색 표시
- 스펙 문서: [Notion API 스펙](https://www.notion.so/flexnotion/API-26c0592a4a928059b6b0c1c401751d4f)

#### 코드 위치
| 파일 | 설명 |
|------|------|
| `flex-goal-backend` > `objective/api/.../ObjectiveSearchV3ApiController.kt:186` | `getRootObjectives` 엔드포인트 |
| `flex-goal-backend` > `objective/service/.../ObjectiveSearchServiceImpl.kt:173` | `filterRootObjective` — hitMap 로직 |
| `flex-goal-backend` > `objective/repository/.../ObjectiveV3JpaRepository.kt:206` | `findRootObjectives` SQL |

#### 고객 안내 예시 (cross-year 트리)
> 2025년 목표(회색)가 표시되는 이유는, 해당 목표 하위에 2026년 목표가 존재하기 때문입니다.
> 회색 목표를 펼치시면 2026년 목표가 있는 것을 확인하실 수 있습니다.
> 2025년 목표 하위에서 2026년 목표를 분리하시면 2025년 목표가 더 이상 표시되지 않습니다.

#### 과거 사례
- **cross-year 트리로 이전 연도 목표 노출**: 고객이 2025 root 하위에 2026 자식 배치 → `hit=false`로 회색 표시. FE·BE 모두 정상 동작 — **스펙** [CI-4126]

---

### 급여 (Payroll)

#### 진단 체크리스트
문의: "초과근무 계산이 이상해요" / "포괄 공제가 안 맞아요"
1. 포괄임금계약 관련 → "근태/휴가" 도메인의 포괄계약 항목 참조 [CI-3868]
2. 보상휴가 부여 관련 → "근태/휴가" 도메인의 보상휴가 항목 참조 [CI-3858]
3. 주 연장근무 계산 → "스케줄링" 도메인의 연장근무 항목 참조 [CI-3839]

*(급여 도메인은 근태/휴가, 스케줄링과 겹치는 이슈가 많으며, 상세 진단은 해당 도메인 참조)*

---

## 변경 이력

| 날짜 | 이슈 | 변경 내용 |
|------|------|----------|
| 2026-03-17 | CI-4122 | 알림 도메인 — Core 알림 title_meta_map 빈값 스펙, 메타베이스 쿼리 개선 사례 추가 |
| 2026-03-17 | CI-4126 | 목표(Goal/OKR) 도메인 추가 — cross-year 트리 + hit 필드 스펙, 고객 안내 가이드 |
| 2026-03-16 | 전체 | 전체 재구성 — QNA-1842(출입연동 커넥션 수) 외부 연동 섹션 추가 |
| 2026-03-16 | CI-4120 | 휴직/휴가 비대칭 — 안희종 답변 반영 (유즈케이스 기반 설계, 잔여 미차감 처리) |
| 2026-03-16 | 전체 | 전체 재구성 — 신규 도메인 2개(계정/구성원, 데이터 추출) 추가, CI-3979/CI-4048/CI-4118/CI-4119/CI-4120/CI-4121/CI-4124 반영 |
| 2026-03-15 | 전체 | 두 COOKBOOK 통합 (글로벌 + flex-timetracking-backend) → oncall repo로 이전 |
| 2026-03-13 | CI-4103 | 교대근무 진단 가이드 추가, 스펙 코드 permalink 추가, 버그 수정 이력 반영 |
| 2026-03-12 | 세콤 | 외부 연동(세콤) 프로토콜 진단 가이드 추가 |
| 2026-02-26 | CI-3976 | 근태/휴가 도메인에 퇴사자 휴가 데이터 추출 진단 항목·API 템플릿·사례 추가 |
| 2026-02-24 | CI-3949 | 근태/휴가 도메인에 휴일대체 탭 미표기 진단 패턴 2건 추가 |
| 2026-02-20 | CI-3932 | 연차 촉진 도메인에 정책 변경 후 PENDING_WRITE 잔존 진단 항목 추가 |
| 2026-02-15 | 전체 | 초기 버전 — 기존 14개 노트에서 전체 추출 |
