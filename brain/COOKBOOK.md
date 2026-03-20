# 운영 쿡북

> 이슈 조사 전에 이 문서를 먼저 참조하면 조사 시간을 단축할 수 있다.
> 각 항목의 상세는 출처 이슈 노트를 참조.

## 도메인별 진단 가이드

### 알림 (Notification)

#### 진단 체크리스트
문의: "알림이 안 왔어요" / "알림 클릭 시 이상한 곳으로 이동해요" / "메타베이스에서 알림 내용이 안 보여요" / "메일 알림을 못 받았어요"
1. 수신자가 승인자이면서 참조자인지 확인 → 중복 제거로 참조 알림 미수신 가능 (승인 알림은 정상 수신) [CI-3910]
2. `notification_deliver` 테이블에서 실제 발송된 `notification_type` 확인
3. 메타베이스에서 `title_meta_map`이 `[]`인 경우 → Core 알림은 토픽 제목이 고정("내 정보 변경" 등)이므로 정상. `notification.message_data_map`을 조회해야 실제 내용 확인 가능 [CI-4122]
4. 이메일 CTA 이동 대상이 이상한 경우 → 알림 유형 확인: `approve.refer`(등록했어요) vs `approved.refer`(승인되었어요) [CI-3914]
5. 클릭 시점에 승인이 이미 완료되었는지 확인 → 완료된 건은 할 일에 없으므로 홈피드로 리다이렉트 [CI-3914]
6. 수신자 locale 확인 → 디폴트 KOREAN, en/ko 템플릿 CTA URL이 다를 수 있음 [CI-3914]
7. **메일 미수신** 문의 → 아래 순서로 확인 [CI-4142]:
   1. `notification_deliver` + `notification` JOIN으로 인앱 알림 생성 확인
   2. 인앱 알림 있으면 → `user_notification_type_setting` EMAIL 비활성화 여부 확인
   3. OpenSearch `flex-app.be-consumer-*`에서 Kafka produce 로그 확인 (`prod.mail.cmd.mail-sending.v1 produced!`)
   4. **SES 이벤트 OpenSearch** (`flex-prod-ses-feedback-*`)에서 `MessageObject.mail.destination` 필터로 Delivery/Bounce 확인 (별도 클러스터, 별도 권한 필요)
   5. SES Delivery 확인됨 → flex 측 정상, 고객에게 수신 서버/스팸 필터 확인 요청

> ⚠️ `mail_send_history` 테이블은 BEI-151(2026-02-20)로 기록 중단됨. 메일 발송 여부는 SES 이벤트 OpenSearch로 확인해야 한다.

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.
> 여러 플로우가 후보이면 병렬로 실행하여 히트 여부를 빠르게 판별.

**F1: 알림 미수신 — 수신자 역할 중복 확인** · 히트: 1 · [CI-3910]
> 트리거: "알림이 안 왔어요" + 수신자가 승인자이면서 참조자

```
① notification_deliver에서 수신자의 발송 이력 조회
   receiver_id + 날짜 범위 → 실제 발송된 notification_type 목록 확인
   ↓
② 승인자/참조자 중복 여부 확인
   동일 건에 승인자 + 참조자로 동시 지정되었는지
   ├─ 중복 → 승인 알림 1건으로 통합, 참조 알림 미수신은 스펙
   └─ 중복 아님 → F2 시도
```

**F2: 알림 내용 확인 불가 — Core 알림 구조** · 히트: 1 · [CI-4122]
> 트리거: "메타베이스에서 알림 내용이 안 보여요" / title_meta_map이 `[]`

```
① notification_topic의 topic_type 확인
   ├─ Core 알림(FLEX_USER_DATA_CHANGE 등) → title_meta_map 빈값은 정상 (제목 고정)
   └─ TT 알림 → title_meta_map에 값이 있어야 정상, 없으면 버그
   ↓
② Core 알림이면 notification.message_data_map 조회
   실제 내용(changedDataName 등)은 이 필드에 저장
```

**F3: 이메일 CTA 이동 대상 불일치** · 히트: 1 · [CI-3914]
> 트리거: "알림 클릭 시 이상한 곳으로 이동해요"

```
① 알림 유형 확인
   notification_type → approve.refer(등록했어요) vs approved.refer(승인되었어요)
   ↓
② 클릭 시점의 승인 상태 확인
   ├─ 승인 완료된 건 → 할 일에 없으므로 홈피드로 리다이렉트 (스펙)
   └─ 미완료인데 이상한 곳 → ③으로
   ↓
③ 수신자 locale 확인
   member_setting.member_id → locale 확인 (디폴트: KOREAN)
   en/ko 템플릿 CTA URL이 다를 수 있음 (3건 알려진 불일치)
```

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

-- 메일 발송 확인 (mail_send_history — BEI-151 이후 기록 중단, 2026-02-20 이전 데이터만 존재)
SELECT status, requested_at FROM flex_pavement.mail_send_history
WHERE primary_recipient = ? ORDER BY requested_at DESC;
-- ⚠️ 2026-02-20 이후 메일 발송 확인은 SES 이벤트 OpenSearch (flex-prod-ses-feedback-*) 사용
```

#### 과거 사례
- **승인자=참조자 중복 알림 제거**: 동일 사용자가 승인자이면서 참조자일 때 승인 알림 1건으로 통합. 참조 알림 미수신은 정상 — **스펙** [CI-3910]
- **이메일 CTA 이동 대상 차이**: `approve.refer` → 할 일, `approved.refer` → 홈피드. 클릭 시점에 승인 완료된 건은 홈피드로 리다이렉트 — **스펙** [CI-3914]
- **en/ko 템플릿 CTA URL 불일치**: 3건 발견 (`approve.refer.cta-web`, `remind.work-record.missing.one.cta-web`, `workflow.task.request-view.request.cta-web`) — **별도 버그** [CI-3914]
- **Core 알림 title_meta_map 빈값**: Core 인사정보 변경 알림(`FLEX_USER_DATA_CHANGE`)의 토픽 제목은 고정("내 정보 변경")이므로 `titleMetaMap = emptyMap()` — **스펙**. 실제 내용은 `notification.message_data_map.changedDataName`으로 확인 [CI-4122]
- **메일 미수신 — SES Delivery 확인 후 고객 안내**: 인앱 알림 정상 + Kafka produce 정상 + SES Send/Delivery 확인 → flex 측 전체 정상. 수신자 메일 서버 내부 문제. `mail_send_history`는 BEI-151로 기록 중단(2026-02-20)되었으므로 SES 이벤트 OpenSearch 사용 필수 — **고객 안내** [CI-4142]

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
문의: "휴일대체 기간이 안 맞아요" / "보상휴가 부여 안 돼요" / "포괄 공제가 안 맞아요" / "휴일대체 탭에 날짜가 안 보여요" / "퇴사자 휴가 데이터 추출해주세요" / "퇴근 시간이 잘렸어요" / "퇴근이 정시로 찍혀요" / "휴직 기간에 휴가가 있어요" / "추천 휴게가 안 들어가요" / "연차 사용 내역이 사라졌어요" / "근태기록 리포트 컬럼이 이상해요" / "휴일대체 사후신청이 안 돼요" / "월별 잔여연차가 달라요" / "보상휴가 회수했는데 잠금이 안 풀려요"
1. 휴일대체 탭 미표기 → 먼저 OpenSearch dev tools로 해당 유저+날짜 문서 존재 확인 [CI-3949]
   - **문서 자체가 없음** → 근무를 건드리지 않은 유저는 sync 이벤트 미발생으로 OS 문서 미생성. 수동 sync 실행: `POST /action/operation/v2/time-tracking/sync-os-work-schedule-advanced` [CI-3949]
   - **문서는 있는데 `holidayProps`가 null** → 해당 날짜 **시점의** 활성 근무유형 확인 (현재 근무유형이 아님!). `v2_user_work_rule`에서 date_from/date_to 범위로 확인 → 해당 요일이 `WEEKLY_UNPAID_HOLIDAY`(휴무일)이면 스펙대로 제외. `WEEKLY_PAID_HOLIDAY`(주휴일)인데 null이면 버그 → 추가 조사 필요 [CI-3949]
2. 휴일대체 기간 문의 → 회사별 gap 커스텀 설정 확인 (`TrackingExperimentalDynamicConfig`) → config 변경으로 해결 가능 [CI-3897]
3. 보상휴가 "부여가능한 시간 없음" → `forAssign` 모드에 따른 기부여 필터 차이 확인. 우회: 1일 단위로 분리 부여 [CI-3858]
4. 포괄계약 공제 불일치 → 월 중 계약 변경 시 Range 분할 확인. `REGARDED_OVER`는 주기 종료일 포함 Range에만 귀속 [CI-3868]
5. 여러날 휴가 스케줄 편집 시 소실 → FE 버그, `timeoffEventId` 기반 판별 한계 [CI-3892]
6. 퇴사자 휴가 데이터 추출 → 웹 UI(휴가 관리 > 사용 내역)에서 "퇴직자 포함"으로 먼저 시도. 특정 구성원 누락 시 주조직 존재 여부 확인 → 주조직 없으면 Operation API 사용 (`departmentIds: null`, `includeResignatedUsers: true`) [CI-3976]
7. 세콤/캡스/텔레캅 퇴근이 **정시로 고정** → 아래 순서로 조사. **반드시 날짜별 퇴근 기록(이벤트 시간 vs 기록 시간)을 먼저 수집하여 변곡점을 특정**한 뒤, 설정 변경 시점과 대조 [CI-4145]
   1. 날짜별 퇴근 기록 비교 → 정상→비정상 전환 시점(변곡점) 특정
   2. `v2_time_tracking_user_config` WHERE `config_key='work-clock.stop.preference'` → `ON_TIME`이면 원인 확정, `updated_at`이 변곡점과 일치하는지 확인
   3. 동일 근무유형 다른 구성원도 동일 증상이면 → `v2_customer_work_record_rule.work_clock_stop_preference` 확인
   4. OpenSearch `PATCH /api/v2/time-tracking/user-config` 로그로 변경 주체(본인/관리자) 확인
   5. 본인 변경이면 → flex 앱에서 "현재 시각으로 퇴근" 또는 "회사 설정 따름"으로 재변경 안내
8. 퇴근 시간이 자정(00:00)으로 잘린 경우 → 대상 구성원의 **다음날 휴가** 등록 여부 확인. 다음날 종일휴가가 있으면 휴가 시작 시간(00:00)으로 조정되는 스펙. 안내: "자정을 넘긴 퇴근 시간이 다음날 종일휴가와 겹치면 휴가 시작 시간으로 조정됩니다" [CI-3979]
9. 휴직 기간에 휴가가 남아있는 경우 → 의도된 스펙. 휴가→휴직 허용(유즈케이스: 미래 휴가 등록 후 갑작스런 휴직 발생, 휴직 기간 휴가는 **잔여 미차감** 처리), 휴직→휴가 차단(유즈케이스 없음). 운영 가이드: 필요 시 휴직 등록 전 기존 휴가를 먼저 취소/조정 [CI-4120]
10. 추천 휴게 시간이 자동 입력 안 됨 → **실시간 기록 중**인지 **근무 확정 후**인지 구분. 실시간 기록 중에는 추천 휴게 미반영이 스펙 (근무 확정 시 판단). 확정 후에도 미입력이면 별도 등록 휴게와 시간 겹침 여부 확인 → 겹치면 추천 휴게 미등록이 정상 [QNA-1922]
11. 연차 사용 내역 사라짐 → 구성원에게 매핑된 연차 정책의 **부여 시작일** 확인. 부여 시작일 이전의 사용 내역은 제품 내에서 미표시(스펙). 엑셀에는 원시 데이터 존재. Metabase #5078로 부여 시작일 히스토리 확인 가능 [QNA-1920]
12. 근태기록 리포트 컬럼 문의 → 출근시각/퇴근시각(`realCheckInTime`)과 시작시간/종료시간(`startTime`)은 다른 데이터 소스. 승인 내역 없이 시작/종료시간만 존재 → 근무수정권한자(`ADMIN`)가 직접 수정한 기록(`ForceUserWorkRecordRegisterServiceImpl`). '당일 승인상태'의 '당일'은 해당 근무일 기준, 다운로드 시점에 조회한 현재 상태 [QNA-1928]
13. 휴일대체 사후신청 버튼 표시되나 승인 불가 → 1차 조직장 미배치(또는 퇴사자/휴직자 등 8가지 에러 사유) 여부 확인. 승인라인 리졸브 오류 시 버튼은 노출되지만 실제 승인 불가. 관리자가 근태관리 > 휴일대체에서 직접 대체일 지정 안내 [CI-4130]
14. 월별 연차 사용내역 vs 내휴가 잔여 차이 → 기준 시점 차이 확인. 월별 연차 사용내역은 연도 말(12/31) 기준, 내휴가는 현재 월 기준. 입사 1주년 시점 월차 소멸로 시점별 잔여 차이 발생 정상 [CI-4140]
15. 보상휴가 회수 후 잠금(🔒) 미해제 → 해당 날짜의 lock 이벤트를 assign별로 조회. 고객이 모든 assign을 회수했는지 확인. 미회수 assign이 있으면 회수 안내. 단일 부여에서 추출 0분 날짜에도 lock이 생성되는 비대칭 존재 (조사 중) [CI-4147]

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.
> 여러 플로우가 후보이면 병렬로 실행하여 히트 여부를 빠르게 판별.

**F1: 휴일대체 탭 미표기** · 히트: 1 · [CI-3949]
> 트리거: "휴일대체 탭에 날짜가 안 보여요"

```
① OpenSearch: 문서 존재 확인
   prod-v2-tracking-work-schedules → userId + date 조회
   ├─ 문서 없음 → ②로 (이슈 A: sync 누락)
   └─ 문서 있는데 holidayProps null → ③으로 (이슈 B: 근무유형 문제)

② [이슈 A] 수동 sync로 즉시 해결
   POST /action/operation/v2/time-tracking/sync-os-work-schedule-advanced
   → 근본 원인: 자동근무 미사용 + 근무 미수정 유저는 sync 이벤트 미발생

③ [이슈 B] 해당 날짜 시점의 활성 근무유형 확인
   v2_user_work_rule WHERE date_from <= {문의날짜} AND date_to >= {문의날짜}
   ⚠️ 현재 근무유형이 아닌 "문의 날짜 시점" 기준!
   ↓
④ 근무유형의 해당 요일 dayWorkingType 확인
   v2_customer_work_rule → 해당 요일 컬럼
   ├─ WEEKLY_UNPAID_HOLIDAY(휴무일) → 스펙 (휴일대체 대상 아님)
   └─ WEEKLY_PAID_HOLIDAY(주휴일)인데 null → 버그, 추가 조사 필요
```

> 💡 **함정**: 근무유형이 최근 변경된 경우 현재 유형과 문의 시점 유형이 다를 수 있음

**F2: 세콤/캡스/텔레캅 퇴근이 정시로 고정** · 히트: 1 · [CI-4145]
> 트리거: "퇴근이 정시로 찍혀요" / "퇴근 시간이 16시로 고정"

```
① 퇴근 기록 비교 — 변곡점 특정
   이벤트 시간(세콤 타각) vs 기록 시간(flex)을 날짜별 정리
   → 정상→비정상 전환 날짜 찾기
   ↓
② DB: 유저 개인 퇴근 preference 확인
   v2_time_tracking_user_config WHERE config_key='work-clock.stop.preference'
   ├─ ON_TIME → ③으로 (원인 유력)
   └─ CUSTOMER_DEFAULT → 회사 설정 확인 (v2_customer_work_record_rule)
   ↓
③ 설정 변경 시점 vs 변곡점 대조
   updated_at이 변곡점과 일치하는지 → 일치하면 인과관계 확정
   ↓
④ OpenSearch: 설정 변경 주체 추적
   flex-app.be-access-{날짜} → PATCH /api/v2/time-tracking/user-config
   → 본인/관리자/시스템 구분
   ↓
⑤ 안내
   본인 변경 → "현재 시각으로 퇴근" 또는 "회사 설정 따름" 재변경 안내
```

> 💡 퇴근이 **자정(00:00)**으로 잘리는 경우는 다른 원인 — F3 참조

**F3: 퇴근 시간이 자정(00:00)으로 잘림** · 히트: 1 · [CI-3979]
> 트리거: "퇴근 시간이 잘렸어요" / "퇴근이 00:00으로 찍혀요"

```
① 대상 구성원의 다음날 휴가 등록 여부 확인
   ├─ 다음날 종일휴가 있음 → 휴가 시작 시간(00:00)으로 조정되는 스펙
   └─ 휴가 없음 → 다른 원인, F2(정시 고정) 또는 별도 조사
```

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
<!-- TODO: 시나리오 테스트 추가 권장 — 선택적 근무 추천 휴게 자동 입력 조건 검증 -->
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

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.
> 여러 플로우가 후보이면 병렬로 실행하여 히트 여부를 빠르게 판별.

**F1: 교대근무 구성원 조회 누락** · 히트: 1 · [CI-4103]
> 트리거: "교대근무 관리 화면에서 일부 구성원만 조회됩니다"

```
① Access log: 메인 요청의 traceId로 내부 호출 추적
   log-dashboard → traceId 필터 → 시간순 API 호출 나열
   ↓
② 권한 체크 응답에서 병목 특정
   access-check 호출 2건 비교:
   - user_work_schedule READ → N명 통과
   - user_time_off_use READ → M명 통과
   ├─ M < N → 휴가 권한이 병목, ③으로
   └─ M = N → 권한 문제 아님, 다른 원인 조사 필요
   ↓
③ 관리자의 권한 범위 확인
   근무 조회 권한 범위 vs 휴가 조회 권한 범위
   ├─ 범위 다름 → 스펙. 고객에게 두 권한 범위 통일 안내
   └─ 범위 같은데 누락 → 코드 버그, 조직 필터 로직(교집합/합집합) 확인
```

#### 과거 사례
- **교대근무 관리 화면 구성원 일부 누락**: 근무 조회 권한(전체)과 휴가 조회 권한(소속 및 하위 조직)의 교집합으로 필터링되어 일부만 표시. 고객에게 두 권한 범위를 맞추도록 안내. — **스펙** [CI-4103]
- **교대근무 조직 필터링 합집합 버그**: 조직 레벨에서 합집합으로 구현되어 있던 것을 교집합으로 수정 (#11994). — **버그 (수정 완료)** [CI-4103]
- **교대근무 휴무일 퇴근 자동 조정 실패**: `baseAgreedDayWorkingMinutes=0`으로 일연장 조건이 null → 퇴근 자동 조정 불가. 유급휴일은 480분 기준 별도 처리되나 휴무일은 미고려 — **버그 (수정 예정)** [CI-4119]
- **초단시간 근로자 연장근무 과소 계산**: 휴무일의 `baseAgreedDayWorkingMinutes` 기준 비대칭. 노무 가이드 변경("휴무일도 8시간 기준") 미반영 추정 — **버그 추정** [CI-4048]

---

### 외부 연동 (Integration)

#### 진단 체크리스트
문의: "세콤 연동이 풀렸어요" / "수동 전송했는데 반영 안 돼요" / "세콤 연동 프로토콜 타입이 뭔가요?" / "세콤으로 퇴근했는데 정시로 찍혀요" / "세콤 출근이 반영 안 돼요" / "진행중 블럭이 여러 개 떠요"
1. 연동 비활성화 주체 확인 → 구독 해지 외 자동 변경 없음. log-dashboard에서 API 호출 이력 확인 [CI-3849]
2. 비활성화 상태에서 수동 전송 → 비활성화 기간 데이터는 소급 불가 [CI-3849]
3. 수동 전송 반영 안 됨 → 세콤 데이터 수신 순서 확인 (퇴근→출근 역순 수신 가능) [CI-3861]
4. 세콤/캡스/텔레캅 퇴근이 정시로 고정 → **근태/휴가 도메인의 항목 7** 참조. 외부 타각기 자체 문제가 아닌 유저 퇴근 preference 설정(`ON_TIME`) 문제. 날짜별 퇴근 기록 비교가 핵심 [CI-4145]
4. 프로토콜 확인 → **PostgreSQL (TCP/IP)** 고정. `CustomerExternalProviderConnectionInfoDto` 응답의 `url`, `port`, `user`, `password`, `database` 필드를 참조
5. 출입연동 커넥션 수 변경 요청 → admin-shell에서 직접 변경. 업체별 기본값: 캡스 2, 세콤 2, KT(텔레캅) 3 [QNA-1842]
6. 다법인 workspace에서 연동 등록 실패 (`하나의 계열사 안에 서로 다른 외부 연동 정보가 존재합니다`) → workspace 내 동일 providerType에 서로 다른 customerKey 존재 여부 확인. 다법인 지원 이전 데이터 마이그레이션 누락이 원인. 데이터 패치로 key 통일 필요 [TT-16783]
7. 세콤 출근 미반영 + 진행중 위젯 잔존 → **먼저 잔존 위젯 확인**. 이전 근무의 위젯이 미종료 상태이면 새 출근 이벤트가 dry-run validation에서 차단됨. Operation API로 잔존 위젯 수동 종료 후 재처리 [CI-4157]
8. 세콤/외부 이벤트로 진행중 블럭 다건 발생 → 다수 터미널에서 동시 이벤트 수신 시 Kafka 동시성 race condition으로 중복 START 등록 가능. `isDraftEventRegistrationAllowed`가 이벤트 타입(START/STOP) 미구분하여 통과시킴 [CI-4165]

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.
> 여러 플로우가 후보이면 병렬로 실행하여 히트 여부를 빠르게 판별.

**F1: 세콤 연동 해제/비활성화 원인 추적** · 히트: 1 · [CI-3849]
> 트리거: "세콤 연동이 풀렸어요" / "연동이 비활성화됐어요"

```
① log-dashboard에서 연동 상태 변경 API 호출 이력 확인
   json.ipath.keyword: /api/v2/time-tracking/customers/{id}/external-providers/{provider}
   json.authentication.customerId: 해당 회사 ID
   ├─ 호출 이력 있음 → 호출자(email) 확인 → 관리자/고객 본인이 변경
   └─ 호출 이력 없음 → 구독 해지 외 자동 비활성화 경로 없음, 추가 조사
   ↓
② 비활성화 기간 데이터 소급 여부
   ├─ 비활성화 기간 수신 데이터 → 소급 불가 (스펙)
   └─ 재활성화 후 수동 전송 → 반영 여부 확인 (F2)
```

**F2: 수동 전송 후 미반영** · 히트: 1 · [CI-3861]
> 트리거: "수동 전송했는데 반영 안 돼요"

```
① 세콤 이벤트 수신 순서 확인
   Metabase #3565 → 해당 날짜 이벤트 조회
   ├─ 퇴근→출근 역순 수신 → 위젯 draft 불일치 가능
   └─ 정상 순서 → 다른 원인, 위젯 draft 이벤트(#4716) 확인
```

**F3: 세콤 출근 미반영 — 잔존 위젯 차단** · 히트: 1 · [CI-4157]
> 트리거: "세콤 출근이 반영 안 돼요" + 진행중 위젯이 보임

```
① 세콤 이벤트 수신 확인
   v2_user_external_provider_event WHERE user_id=? AND event_time >= ?
   ├─ 이벤트 0건 → 세콤 PC/PostgreSQL 연결 확인 (transmitter 로그)
   └─ 이벤트 있음 → ②로
   ↓
② consumer 로그 확인
   OpenSearch: flex-app.be-api-{날짜}, app=time-tracking-consumer
   → "validation 실패" 또는 "dry-run 종료" 메시지 확인
   ├─ validation 실패 → ③으로
   └─ 로그 없음 → Kafka 수신 자체 실패, consumer lag 확인
   ↓
③ 잔존 위젯 확인
   이전 근무일의 위젯이 종료되지 않은 상태인지 확인
   ├─ 잔존 위젯 있음 → Operation API로 수동 종료 후 세콤 수동전송
   └─ 잔존 위젯 없음 → 다른 validation 실패 원인 조사
```

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
```

**로그 확인 (연동 상태 변경 추적):**
- log-dashboard → 조건:
  - `json.ipath.keyword`: `/api/v2/time-tracking/customers/{customerIdHash}/external-providers/{externalProvider}`
  - `json.authentication.customerId`: 해당 회사 ID
  - `json.authentication.email`: 변경한 사용자 이메일

#### 과거 사례
- **세콤 연동 비활성화 기간 데이터 소급 불가**: 시스템 설계상 비활성화 기간 수신 데이터 저장 안 함 — **스펙** [CI-3849]
- **세콤 수동 전송 미반영**: 퇴근→출근 역순 수신으로 위젯 draft 불일치 — **조사 중** [CI-3861]
- **세콤/캡스/텔레캅 퇴근이 정시로 고정**: 유저 본인이 flex 앱에서 `ON_TIME` 설정으로 변경한 것이 원인. 날짜별 퇴근 기록(이벤트 vs 기록)을 비교하여 변곡점 특정 → DB/OpenSearch로 설정 변경 시점·주체 확인 — **스펙** [CI-4145]
- **세콤 연동 프로토콜 타입 문의**: 고객사에서 방화벽 허용 설정을 위해 프로토콜 타입을 문의. PostgreSQL 고정 설계로 API에 별도 필드 없음. 고객사에 "TCP/PostgreSQL 프로토콜, 포트 5432" 직접 안내로 해결. — **스펙**
- **출입연동 커넥션 수 설정**: 업체별 PC당 커넥션 수 기본값 — 캡스 2, 세콤 2, KT(텔레캅) 3. admin-shell(`https://admin-shell.flexis.team/time-tracking/admin/external-provider.html`)에서 변경 — **운영 요청** [QNA-1842]
- **다법인 workspace customerKey 충돌**: 다법인 지원 코드 추가 시 기존 데이터 마이그레이션 누락으로 workspace 내 동일 providerType에 서로 다른 customerKey 존재 → 신규 등록 실패. 데이터 패치로 key 통일 필요 — **버그 (데이터 마이그레이션 누락)** [TT-16783]
- **세콤 출근 미반영 — 잔존 위젯에 의한 dry-run 차단**: 이전 근무 위젯 미종료 → 새 출근 이벤트의 dry-run validation 실패(`WORK_CLOCK_START_CONTINUOUS_NOT_ALLOWED`). Operation API로 잔존 위젯 수동 종료 후 재처리 — **스펙 (정상 차단)** [CI-4157]
- **세콤 다중 터미널 동시 이벤트 → 중복 START 등록**: Kafka 파티션 분산 + REQUIRES_NEW 트랜잭션 + REPEATABLE READ 격리 → 동시 dry-run에서 서로의 미커밋 데이터 미가시. `isDraftEventRegistrationAllowed`의 이벤트 타입 미구분도 기여 — **버그 (조사 중)** [CI-4165]

---

### 권한 (Permission)

#### 진단 체크리스트
문의: "누가 언제 권한을 부여했는지 확인해주세요" / "감사로그에서 권한 변경이 안 보여요"
1. `flex_authorization.flex_grant_subject`에서 대상 사용자의 grant 멤버십 확인 → `created_at`이 포함 시점, `created_by`가 수행자 [CI-4150]
2. 대상 사용자가 grant에 없으면 → 이미 회수됨 (물리 삭제로 이력 소실). 회사 최초 유저인지 확인 → 최초 유저라면 회사 생성 시 자동 부여된 것 [CI-4150]
3. 감사로그(Envers)는 권한 변경을 기록하지 않음 → 고객에게 "감사로그 기록 대상이 아닙니다" 안내 [CI-4150]

#### 데이터 접근
```sql
-- 특정 회사의 최고관리자 grant 멤버 조회
SELECT gs.subject_id, gs.created_by, gs.created_at
FROM flex_authorization.flex_grant_subject gs
  JOIN flex_authorization.flex_grant g ON g.id = gs.grant_id
WHERE gs.customer_id = ? AND g.title_key = 'authority.administrator_title';

-- 특정 사용자가 포함된 모든 grant 조회
SELECT gs.subject_id, gs.created_by, gs.created_at, g.title_text, g.title_key
FROM flex_authorization.flex_grant_subject gs
  JOIN flex_authorization.flex_grant g ON g.id = gs.grant_id
WHERE gs.customer_id = ? AND gs.subject_id = ?;
```

#### 과거 사례
- **최초 유저 최고관리자 자동 부여**: 회사 생성 시 첫 유저에게 자동 부여, 감사로그에 이력 없음. `flex_grant_subject` 물리 삭제로 회수 후 이력 추적 불가 — **스펙** [CI-4150]

---

### 계정/구성원 (Account / Member)

#### 진단 체크리스트
문의: "이메일 변경해주세요" / "구성원 이메일 일괄 변경해주세요" / "계열사 전환하면 로그인이 풀려요"
1. 단건 이메일 변경 → `PATCH /action/v2/operation/core/customers/{customerId}/users/{userId}/emails/change` [CI-4118]
2. 일괄 이메일 변경 → `PATCH /action/v2/operation/core/customers/{customerId}/emails/change/bulk` [CI-4124]
   - ⚠️ 존재하지 않는 oldEmail이 1건이라도 포함되면 **전체 실패** (`IllegalArgumentException`)
   - 사전에 DB에서 대상 이메일 존재 여부 확인 필수
3. 다법인 사용자 확인 → `primary_user_id`가 NULL이 아니면 primary 회사에서만 변경 가능 [CI-4118]
4. 검증된 이메일(verified) 확인 → 이미 검증된 이메일은 관리자가 변경 불가, Operation API 사용 필요 [CI-4118]
5. 계열사 전환 시 로그인 풀림 → 각 계열사의 **자동 로그아웃 설정 시간** 비교. 세션 시간이 긴 회사에서 짧은 회사로 전환 시 짧은 쪽 기준으로 세션 만료 판정 → 정상 동작(스펙). 두 회사 설정을 동일하게 맞추도록 안내 [CI-4166]

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
- **계열사 전환 시 로그인 풀림**: 계열사별 자동 로그아웃 설정이 독립적. 세션 시간이 긴 회사→짧은 회사로 전환 시 exchange API가 대상 회사 기준으로 세션 만료 판정. 두 회사 설정 동일하게 맞추면 해결 — **스펙** [CI-4166]

---

### 승인 (Approval)

#### 진단 체크리스트
문의: "퇴직자 승인자 교체 알림이 뜨는데 실제 건이 없어요"
1. 메타베이스 대시보드(#309)에서 `target_uid`로 승인 요청 확인 → 요청은 존재하나 대응하는 실제 휴가 사용 건이 없으면 고아 승인 요청 [CI-3951]
2. 퇴직자가 휴가 승인 정책에 여전히 포함되어 있는지 확인 → 승인 정책에서 퇴직자 제거 안내 [CI-3951]

#### 과거 사례
- **퇴직자 승인자 교체 — 고아 승인 요청**: "교체 필요 3건" 표시되나 실제 휴가 사용 건 없음. `target_uid`와 데이터 불일치. 수동 처리로 해결 — **버그 추정 (수동 대응)** [CI-3951]

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

### 전자계약 (Contract/Digicon)

#### 진단 체크리스트
문의: "서명된 계약서 삭제해주세요" / "계약서 서식이 삭제됐어요" / "서식 삭제자를 알고 싶어요"
1. 서명 완료(SUCCEED) 계약서 삭제/취소 요청 → **삭제 불가(스펙)**. `DigiconProgressStatus.cancelable()` = `this === IN_PROGRESS`만 허용. 올바른 내용으로 새 계약서 재발송 안내 [CI-4152]
2. 서식(template) 삭제자 추적 → access log에서 `DELETE /api/v2/digicon/templates` 검색 → traceId로 호출 체인 추적 → permission-api 호출에서 userId 확인 → view_user 테이블로 이메일 매핑. 감사로그에 서식 삭제 미기록 [CI-4168]
3. 양식 개수 제한 여부 → 제한 없음 [CI-4168]
4. 삭제된 서식 복구 → Operation API: `POST /api/operation/v2/digicon/customers/{customerId}/restore-deleted-templates` [CI-4168]

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.
> 여러 플로우가 후보이면 병렬로 실행하여 히트 여부를 빠르게 판별.

**F1: 전자계약 서식 삭제자 추적** · 히트: 1 · [CI-4168]
> 트리거: "서식이 삭제됐어요" / "삭제자를 알고 싶어요"

```
① DB: 삭제된 서식 목록 확인
   customer_digicon_template WHERE customer_id=? AND deleted_at IS NOT NULL
   → 삭제 시간 패턴 확인 (동일 초에 다건이면 일괄 삭제)
   ↓
② Access log: 삭제 API 호출 추적
   OpenSearch flex-app.be-access-{날짜} → DELETE /api/v2/digicon/templates + 서비스 digicon-api
   → traceId 추출
   ↓
③ traceId로 호출 체인 추적
   permission-api 호출에서 customers/{customerId}/users/{userId} 확인
   ↓
④ view_user 테이블에서 userId → 이메일/이름 매핑
   ├─ 문의자 본인 → 의도하지 않은 삭제인지, 계정 공유 여부 확인 안내
   └─ 다른 사용자 → 해당 사용자에게 확인 안내
```

#### 데이터 접근
```sql
-- 삭제된 서식 목록 (soft delete)
SELECT id, name, deleted_at, created_at
FROM customer_digicon_template
WHERE customer_id = ? AND deleted_at IS NOT NULL
ORDER BY deleted_at DESC;

-- 서명 완료 계약서 조회 (삭제 불가 확인)
SELECT id, progress_status, file_key, created_date_time
FROM digicon
WHERE customer_id = ? AND user_id = ?
ORDER BY created_date_time DESC;

-- 삭제된 서식 복구 (Operation API)
POST /api/operation/v2/digicon/customers/{customerId}/restore-deleted-templates
```

#### 과거 사례
- **서명 완료 계약서 삭제 불가**: SUCCEED 상태 계약서는 `cancelable() = this === IN_PROGRESS`로 취소 불가, Operation API에도 삭제 엔드포인트 없음. 법적 효력 보존이 설계 의도. 정석: 올바른 내용으로 재계약 발송 — **스펙** [CI-4152]
- **서식 삭제자 access log 추적**: 감사로그에 서식 삭제 미기록. access log traceId → permission-api 호출 체인으로 삭제자 특정 가능. soft delete로 Operation API 복구 가능 — **스펙 (개선 필요)** [CI-4168]

---

### 급여 (Payroll)

#### 진단 체크리스트
문의: "초과근무 계산이 이상해요" / "포괄 공제가 안 맞아요" / "올림 계산이 안 맞아요" / "급여정산 해지하면 명세서 공개가 되나요?"
1. 올림 자릿수 이상 문의 → 설정 변경 시점과 정산 생성 시점 비교. 정산 생성 시 올림 설정이 스냅샷됨 → 기존 진행 중 정산은 이전 설정 유지 [CI-4131]
   - `payroll_legal_payment_setting`(현재 설정)과 `work_income_over_work_payment_calculation_basis`(정산 스냅샷) 비교
   - 불일치하면 설정 변경 전 생성된 정산 → 신규 정산 생성 안내
2. 포괄임금계약 관련 → "근태/휴가" 도메인의 포괄계약 항목 참조 [CI-3868]
3. 보상휴가 부여 관련 → "근태/휴가" 도메인의 보상휴가 항목 참조 [CI-3858]
4. 주 연장근무 계산 → "스케줄링" 도메인의 연장근무 항목 참조 [CI-3839]
5. 정산 수정 후 소득세 변경 문의 → 정산 자물쇠 해제 후 재처리 시 소득세 변경 → 1차 정산 ~ 수정 정산 사이에 기본 공제 대상(부양가족 수)이 변경되었는지 확인. `work_income_settlement_payee`의 `dependent_families_count` 조회 [CI-4149]
6. 급여정산 해지 후 명세서 공개/알림 문의 → 알림은 해지와 무관하게 발송됨. 단, 구독 해지 시 급여 탭 접근 차단되어 실제 열람 불가. 1달 연장 권장 안내 [QNA-1933]

#### 데이터 접근
```sql
-- 초과근무수당 올림 설정 (현재)
SELECT rounding_digit, rounding_method
FROM payroll_legal_payment_setting
WHERE customer_id = ? AND type = 'GROUP_EXCEEDED_WORK_EARNING';

-- 정산근거의 올림 스냅샷 (정산 생성 시점)
SELECT rounding_digit, rounding_method
FROM work_income_over_work_payment_calculation_basis
WHERE settlement_id = ?;

-- 정산 대상자의 부양가족 수 스냅샷 확인
SELECT user_id, dependent_families_count, under_age_dependent_families_count
FROM flex_payroll.work_income_settlement_payee
WHERE settlement_id = ? AND user_id = ?;
```

#### 과거 사례
- **올림 설정 변경 후 기존 정산 미반영**: 정산 생성 시 올림 설정을 스냅샷. 100의 자리 → 10의 자리로 변경해도 기존 정산은 이전 설정 유지. 신규 정산에서 정상 반영 — **스펙** [CI-4131]
- **정산 재처리 시 소득세 변경 — 부양가족 수 최신화**: 정산 자물쇠 해제 후 재처리 시 PAYEES 단계에서 전체 대상자의 payee 스냅샷 최신화. 1차 정산 이후 부양가족 추가/변경이 있었으면 소득세 재계산됨 — **스펙** [CI-4149]
<!-- TODO: 시나리오 테스트 추가 권장 — 정산 재처리 시 payee 스냅샷 최신화로 소득세 변경 검증 -->
- **구독 해지 후 명세서 알림 발송**: payroll 스케줄러/pavement 모두 구독 상태 미체크. 알림은 정상 발송되나 급여 탭 접근 차단으로 실제 열람 불가. 1달 연장 안내 권장 — **스펙** [QNA-1933]

*(급여 도메인은 근태/휴가, 스케줄링과 겹치는 이슈가 많으며, 상세 진단은 해당 도메인 참조)*

---

### 평가 (Evaluation / Performance Management)

#### 진단 체크리스트
문의: "삭제한 평가가 다시 보여요" / "평가 리스트에 이상한 것이 있어요" / "리뷰 마이그레이션 에러"
1. API 응답에서 해당 평가의 `isDeleted` 값 확인 → `false`이면 삭제된 적 없는 DRAFT 평가. 고객에게 삭제 방법 안내 [CI-4158]
2. `isDeleted: true`인 평가가 목록에 나타나면 → 실제 버그. `draft_evaluation` 테이블에서 `deleted_at` 컬럼 확인 [CI-4158]
3. FE 배포 직후 발생한 경우 → FE에서 목록 필터링 로직이 변경되었을 가능성 확인 [CI-4158], [CI-4129]
4. 리뷰 마이그레이션 "Failed requirement." 에러 → raccoon **prod**(`flex-raccoon.grapeisfruit.com`)를 사용하고 있는지 확인. dev raccoon에 prod 해시를 쓰면 Hashids salt 불일치로 `INVALID_NUMBER` 반환 → `require(reviewSetId > 0L)` 실패 [QNA-1936]

#### 과거 사례
- **삭제한 평가가 다시 노출**: 실제로는 삭제된 적 없는 title=null DRAFT 평가가 FE 핫픽스로 정상 노출된 것. 고객이 "이전에 안 보이던 것이 보임"을 "삭제 복원"으로 오해 — **스펙** [CI-4158]
- **평가 공동편집자 아닌데 메뉴 노출**: title=null인 DRAFT 평가를 FE에서 필터링하여 노출 문제 — **버그 (FE)** [CI-4129]
<!-- TODO: 시나리오 테스트 추가 권장 — title=null DRAFT 평가 리스트 정상 노출 검증 -->
- **리뷰 마이그레이션 "Failed requirement." 에러**: dev raccoon에서 prod 해시 사용 → Hashids salt 불일치로 디코딩 실패(`INVALID_NUMBER`). prod raccoon에서 재시도하면 구체적 에러 정상 출력 — **운영 오류** [QNA-1936]

---

### 채용 (Recruitment)

#### 진단 체크리스트
문의: "채용사이트 주소 변경이 검토중이에요" / "subdomain 변경 신청 상태 확인"
1. `#alarm-recruiting-operation` 슬랙 채널에서 해당 회사의 변경 요청 알림 확인 [CI-4170]
2. `flex_recruiting.site_subdomain_change` 테이블에서 요청 건의 상태와 도메인명 확인 [CI-4170]
3. 도메인명이 적절하면 raccoon operation API로 승인/반려 처리 [CI-4170]
   - 승인: `POST /customers/{customerId}/subdomains/{siteSubdomainChangeId}/change/approve`
   - 반려: `POST /customers/{customerId}/subdomains/{siteSubdomainChangeId}/change/reject`

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.

**F1: 채용사이트 subdomain 변경 요청 방치** · 히트: 1 · [CI-4170]
> 트리거: "채용사이트 주소 변경 신청이 검토중 상태"

```
① #alarm-recruiting-operation 슬랙 채널에서 알림 확인
   해당 회사 이름 또는 Customer ID로 검색
   ├─ 알림 있음 → ②로 (처리 누락)
   └─ 알림 없음 → 알림 발송 자체가 실패했을 가능성, 추가 조사
   ↓
② DB: 변경 요청 상태 확인
   flex_recruiting.site_subdomain_change WHERE customer_id = ?
   → 요청 건의 상태, 요청된 도메인명 확인
   ↓
③ 도메인명 적절성 확인 후 operation API로 승인
   POST /customers/{customerId}/subdomains/{siteSubdomainChangeId}/change/approve
```

#### 데이터 접근
```sql
-- 채용사이트 subdomain 변경 요청 조회
SELECT * FROM flex_recruiting.site_subdomain_change
WHERE customer_id = ?
ORDER BY created_at DESC;
```

#### 과거 사례
- **subdomain 변경 검토중 방치**: 온콜 담당자가 `#alarm-recruiting-operation` 알림을 모니터링하지 않아 9일간 방치. operation API로 즉시 승인 처리 — **운영 요청** [CI-4170]

---

### 조직 관리 (Department)

> 출처: [코어 온콜 런북](https://www.notion.so/19d0592a4a928051956ec7773e47ef2d) — Core Squad

#### 진단 체크리스트
문의: "조직 삭제해주세요" / "조직 변경 예약을 취소할 수 없어요" / "조직 시계열 데이터 뽑아주세요" / "조직 종료일 변경 시 오류" / "종료된 조직에 조직코드 넣어주세요"
1. **조직 삭제 요청** → 시작일이 오늘인지 확인
   - 오늘이면 → 제품 상에서 처리 가능 (⚠️ **일반 설정**에서만 가능, 고급 설정은 종료일 처리가 다름). 일반 설정에서 오늘로 종료 처리 시 시작일=종료일이 되면서 삭제됨
   - 오늘이 아니면 → Operation API로 삭제. 사전에 구성원/하위조직 확인 필수
2. **조직 삭제 전 확인사항**:
   - `user_position_time_series` — 해당 조직에 **모든 시점**에 걸쳐 소속된 구성원이 없어야 함 (현재 시점뿐 아니라 과거 포함)
   - 하위 조직 존재 여부 → 있으면 CS를 통해 관리자와 처리 방향 합의
   - 변경 대상 테이블: `department`, `department_time_series_segment`, `department_time_series_snapshot`, `department_change_history_set`
3. **발령 예약 + 조직 변경 예약 데드락** → 미래 날짜 기준으로 발령과 조직 변경(삭제/생성)을 동시에 냈을 때:
   - 조직 변경 취소 → 발령이 해당 조직을 참조하므로 불가
   - 발령 취소 → 삭제된 조직으로 발령을 이어줘야 하므로 불가
   - 고급 설정 → 발령 걸려있으면 수정 불가
   - **해결**: SQL로 조직 종료일 임시 제거 → 발령 취소 → 종료일 복구 (아래 SQL 참조)
4. **조직 종료일 변경 시 오류** → 구성원 목록 필터에서 퇴직 상태 제외가 기본이므로 "아무도 없다"고 착각하는 경우 많음. 퇴직자 포함 여부 확인 + 400 응답 body 확인
   - 간혹 발령 처리가 안 되는 경우 → 조직 종료일을 수동으로 먼저 조정 → 발령 처리 → 종료일 다시 조정
5. **조직 시계열 데이터 조회** → metabase로 전환됨. [Metabase #5082](https://metabase.dp.grapeisfruit.com/question/5082?customerId=44879) 링크로 안내
6. **종료된 조직 코드 일괄 마이그레이션** → 엑셀을 받아서 이름으로 ID를 찾고 DML 수행. 팁: 시작일/이름 정렬 후 이름을 긁어서 쿼리하면 편함

#### 조사 플로우

**F1: 조직 삭제 처리** · [코어 런북]
> 트리거: "조직 삭제해주세요"

```
① 시작일이 오늘인지 확인
   ├─ 오늘 → 제품 일반 설정에서 오늘로 종료 처리 (시작일=종료일 → 자동 삭제)
   └─ 오늘 아님 → ②로
   ↓
② 조직에 소속된 구성원 확인 (모든 시점)
   user_position_time_series WHERE department_id = ?
   ├─ 있음 → CS 통해 관리자와 처리 방향 합의
   └─ 없음 → ③으로
   ↓
③ 하위 조직 확인 (시점별)
   department_time_series_segment WHERE parent_id = ?
   ├─ 있음 → 하위 조직도 함께 정리 필요
   └─ 없음 → ④로
   ↓
④ Operation API로 삭제
```

**F2: 발령+조직변경 데드락 해소** · [코어 런북]
> 트리거: "발령 예약과 조직 변경을 취소할 수 없어요"

```
① 문제 조직의 종료일 SQL 임시 제거
   UPDATE department SET end_date_time = '9999-12-31 23:59:59.999999'
   UPDATE department_time_series_segment SET end_date_time = '9999-12-31 23:59:59.999999'
   ↓
② 고객사에 예약 발령 취소 요청
   ↓
③ 발령 취소 확인 후 종료일 복구
   UPDATE department SET end_date_time = {원래 종료일}
   UPDATE department_time_series_segment SET end_date_time = {원래 종료일}
```

#### 데이터 접근
```sql
-- 조직 삭제 전: 해당 조직에 소속된 구성원 확인 (전 시점)
SELECT * FROM user_position_time_series
WHERE department_id = ? AND deleted_date_time IS NULL;

-- 조직 삭제 전: 하위 조직 확인
SELECT id, name, parent_id, begin_date_time, end_date_time
FROM department_time_series_segment
WHERE parent_id = ? AND deleted_date_time IS NULL;

-- 조직 시계열 데이터 조회 (Metabase #5082)
SELECT
    d.id AS '조직 ID', d.code AS '조직 코드',
    DATE_FORMAT(DATE_ADD(IF(d.begin_date_time = '1000-01-01 00:00:00', NULL, d.begin_date_time), INTERVAL 1 DAY), '%Y-%m-%d') AS '조직 시작일',
    DATE_FORMAT(DATE_ADD(IF(d.end_date_time = '9999-12-31 23:59:59', NULL, d.end_date_time), INTERVAL 1 DAY), '%Y-%m-%d') AS '조직 종료일',
    d_seg.id AS '시점별 정보 ID', d_seg.name AS '조직명', d_seg.parent_id AS '상위조직 ID',
    DATE_FORMAT(DATE_ADD(IF(d_seg.begin_date_time = '1000-01-01 00:00:00', NULL, d_seg.begin_date_time), INTERVAL 1 DAY), '%Y-%m-%d') AS '시점별 정보 시작일',
    DATE_FORMAT(DATE_ADD(IF(d_seg.end_date_time = '9999-12-31 23:59:59', NULL, d_seg.end_date_time), INTERVAL 1 DAY), '%Y-%m-%d') AS '시점별 정보 종료일'
FROM flex.department_time_series_segment d_seg
  JOIN flex.department d ON d_seg.department_id = d.id
WHERE d.customer_id = ? AND d_seg.deleted_date_time IS NULL AND d.deleted_at IS NULL
ORDER BY d.id, d_seg.begin_date_time;

-- 발령+조직변경 데드락: 예약 발령일 기준 종료되는 조직 조회
SELECT id FROM department
WHERE customer_id = ? AND end_date_time = ? AND deleted_at IS NULL;

SELECT id FROM department_time_series_segment
WHERE department_id IN (?) AND deleted_date_time IS NULL AND end_date_time = ?;

-- 조직 종료일 임시 제거 (데드락 해소용)
UPDATE flex.department SET end_date_time = '9999-12-31 23:59:59.999999'
WHERE customer_id = ? AND id IN (?) AND end_date_time = ?;

UPDATE flex.department_time_series_segment SET end_date_time = '9999-12-31 23:59:59.999999'
WHERE customer_id = ? AND id IN (?) AND department_id IN (?) AND end_date_time = ?;
```

> ⚠️ **일반 설정 vs 고급 설정의 종료일 처리 차이**: 일반 설정은 오늘의 00:00, 고급 설정은 해당 날짜의 23:59.999999로 종료일 적용

#### 과거 사례
- **발령+조직변경 데드락**: 미래 날짜 기준 발령과 조직 삭제/생성 동시 예약 → 상호 참조로 양쪽 다 취소 불가. SQL로 종료일 임시 제거→발령 취소→종료일 복구로 해소 — **운영 대응** [코어 런북]
- **조직 삭제 — 시작일=오늘 우회**: 제품 상 삭제 기능은 없지만, 일반 설정에서 오늘 종료 처리 시 시작일=종료일이 되면서 삭제됨 — **스펙 (우회 경로)**
- **조직 시계열 조회 → Metabase 전환**: 쿼리 대응에서 Metabase #5082로 전환. 문의 시 링크 안내 — **운영 요청**
- **종료된 조직 코드 마이그레이션**: 과거 발령 마이그레이션 위해 종료된 조직에 코드 입력 필요. 엑셀→DML — **운영 요청**

---

### 인사발령 (Personnel Appointment)

> 출처: [코어 온콜 런북](https://www.notion.so/19d0592a4a928051956ec7773e47ef2d) — Core Squad

#### 진단 체크리스트
문의: "인사발령 엑셀 데이터 뽑아주세요" / "특정 시점의 조직 정보 추출해주세요"
1. **인사발령 엑셀 데이터 요청** → 반드시 워크플로우(`고객사의 개인정보 접근 및 처리를 위한 검토 및 승인 요청`) 먼저 작성. 고객사 사전 동의 첨부 권장
   - Operation API: `POST /action/operation/v2/core/personnel-appointment/customers/{customerId}/export/excel`
   - 전체 요청 시 body 없이 요청
   - 타임아웃 발생 시 → user id 기준으로 적절히 나눠서 여러 번 호출 후 엑셀 병합
2. **특정 시점 조직 추출** → `user_position_time_series_segment` + `department` JOIN으로 `union all` 쿼리 구성 (아래 SQL 참조)

#### 데이터 접근
```sql
-- 인사발령 엑셀 추출 (Operation API)
POST /action/operation/v2/core/personnel-appointment/customers/{customerId}/export/excel

-- 유저별 특정 시점 조직 추출
SELECT pt.user_id, GROUP_CONCAT(d.name ORDER BY pt.is_primary DESC SEPARATOR ', ') AS names
FROM user_position_time_series_segment pt, department d
WHERE pt.department_id = d.id
  AND pt.customer_id = ?
  AND pt.deleted_date_time IS NULL
  AND pt.user_id = ?
  AND pt.begin_date_time < ?  -- target_date
  AND (pt.end_date_time > ? OR pt.end_date_time = '9999-12-31 23:59:59.999999')
-- 여러 유저는 UNION ALL로 연결
```

#### 과거 사례
- **인사발령 엑셀 타임아웃**: 대규모 고객사에서 타임아웃 발생 → user id 기준 분할 호출 후 병합 — **운영 요청**
- **특정 시점 조직 추출**: 유저 리스트+시점 기반 union all 쿼리로 대응 — **운영 요청**

---

### 체크리스트/온보딩 (Checklist / Onboarding)

> 출처: [코어 온콜 런북](https://www.notion.so/19d0592a4a928051956ec7773e47ef2d) — Core Squad

#### 진단 체크리스트
문의: "체크리스트가 발송되지 않았어요"
1. **언급한 Task가 존재하지 않는 경우** → 템플릿을 변경했을 때 기존 체크리스트에 자동 적용되지 않음. 이미 생성된 체크리스트에 템플릿의 task를 추가할 수 없음 (스펙)
2. **온보딩 완료 처리 여부** → 온보딩 완료 기능으로 완료 처리된 경우 체크리스트가 발송되지 않음

#### 과거 사례
- **체크리스트 미발송 — 템플릿 변경**: 관리자가 템플릿을 변경 후 기존 체크리스트에도 적용될 것으로 기대했으나, 이미 생성된 체크리스트에는 반영 안 됨 — **스펙**
- **체크리스트 미발송 — 온보딩 완료 처리**: 온보딩 완료 처리된 구성원에게는 체크리스트 미발송 — **스펙**

---

### 계정/구성원 (Account / Member) — 코어 런북 보강

> 아래는 기존 계정/구성원 섹션에 추가되는 코어 런북 항목

#### 진단 체크리스트 (추가)
문의: "입사일 변경해주세요" / "삭제된 구성원 복구해주세요" / "개인정보 보유현황 파악" / "이메일 대량 변경해주세요"
1. **입사일 변경 요청** → 입사일을 미래로 설정해 접속 불가한 경우. 어드민 페이지 생성됨 (확인 필요)
   - Operation API: `PATCH /action/operation/v2/core/bundle/user-basic/update-join-date`
   - ⚠️ patch 스펙이 아니므로 `company_join_date`, `company_group_join_date`, `is_company_group_join_date_used`를 모두 채워야 함
   - [Metabase #7227](https://metabase.dp.grapeisfruit.com/question/7227?userId=911010&userEmail=)로 기존 값 확인
2. **삭제된 구성원 정보 복구** →
   1. 삭제 처리 시기 파악 → DB Snapshot 복구 요청
   2. Snapshot에서 삭제된 정보 확인 및 복구 ([복구 가이드 참조](https://www.notion.so/1df7b0f913a94fbaa0c2fd2610f6b95f))
   3. opensearch, bullseye 동기화:
      - bullseye: `/action/operation/v2/bullseye/users/produce`
      - opensearch: `/action/operation/v2/workspace/users/produce`
3. **개인정보 보유현황 파악** → 시즈널, 대기업 컴플라이언스 목적. 아래 SQL 참조
4. **이메일 대량 변경** (기존 일괄 변경 보강) → `PATCH /action/v2/operation/core/customers/{customerId}/emails/change/bulk`
   - 자동화됨 (Operation API Y)

#### 데이터 접근 (추가)
```sql
-- 입사일 변경 전 기존 값 확인 (Metabase #7227)
SELECT c.name AS '고객사명', u.id, u.email,
       ue.company_join_date, m.company_group_join_date, m.is_company_group_join_date_used
FROM user u
  LEFT JOIN user_employee ue ON u.id = ue.user_id
  LEFT JOIN member_user_mapping ON u.id = member_user_mapping.user_id
  LEFT JOIN flex.member m ON member_user_mapping.member_id = m.id
  LEFT JOIN customer c ON u.customer_id = c.id
WHERE ue.user_id = ?;

-- 개인정보 보유현황: 이름/이메일 (user 테이블 — 필수값이므로 유저 수와 동일)
-- name_in_office (닉네임)
SELECT COUNT(*) FROM user
WHERE customer_id = ? AND deleted_date IS NULL
  AND name_in_office != '{cipher}44062be3131a4b6ffcdc870e02696817';

-- 사번
SELECT COUNT(*) FROM user_employee
WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL)
  AND employee_number IS NOT NULL;

-- 주민등록번호
SELECT COUNT(*) FROM member
WHERE id IN (SELECT member_id FROM member_user_mapping
             WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL))
  AND ssn IS NOT NULL;

-- 생년월일 / 휴대폰번호 / 국적 / 집주소
SELECT COUNT(*) FROM user_personal
WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL)
  AND birth_date IS NOT NULL;
-- phone_number: != '{cipher}44062be3131a4b6ffcdc870e02696817'
-- nationality: != 'UNKNOWN'
-- address_full: != '{cipher}44062be3131a4b6ffcdc870e02696817'

-- 계좌번호
SELECT COUNT(*) FROM user_bank_account
WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL);

-- 경력사항 / 학력사항
SELECT COUNT(*) FROM user_work_experience
WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL);

SELECT COUNT(*) FROM user_education_experience
WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL);
```

> ⚠️ `{cipher}44062be3131a4b6ffcdc870e02696817`은 공백을 의미

#### 과거 사례 (추가)
- **입사일 변경 — 미래 입사일로 접속 불가**: 최고관리자 1명인 고객사에서 미래 입사일 설정 → 접속 차단 → CS 인입. Operation API로 입사일 변경 — **운영 요청** [코어 런북]
- **삭제된 구성원 복구**: 휴먼 에러로 마스킹 처리 → DB Snapshot에서 복구 → opensearch/bullseye 동기화 — **운영 요청** [코어 런북]
- **개인정보 보유현황 파악**: 시즈널 요청. 삭제되지 않은 유저 대상 테이블별 count — **운영 요청** [코어 런북]

---

### 승인 (Approval) — 코어 런북 보강

> 아래는 기존 승인 섹션에 추가되는 코어 런북 항목

#### 진단 체크리스트 (추가)
문의: "승인은 완료됐는데 데이터가 안 바뀌었어요"
1. **승인 완료 후 데이터 반영 오류** → 승인 라인 모든 승인 완료 후 실제 코어 데이터 변경 과정에서 오류 발생
   - 승인은 아직 ONGOING 상태로 남아있음
   - 코어 데이터는 변경되지 않은 채 남아있음
   - 대응: `cloud_event_entity`에서 문제 이벤트 ID 조회 → `/action/operation/v2/approval/re-produce-messages` Operation API로 이벤트 재발행
   - 이후 approval process 상태가 APPROVED로 변경 및 코어 데이터 변경 확인

#### 과거 사례 (추가)
- **승인 완료 후 데이터 반영 오류**: 승인 완료 이벤트 처리 중 오류 → ONGOING 상태 잔류. `re-produce-messages` Operation API로 이벤트 재발행하여 정상 처리 — **운영 대응** [코어 런북]

---

### OpenSearch sync / 조직도 통계 — 코어 런북 보강

> 아래는 기존 도메인에 추가되는 항목

#### 진단 체크리스트 (추가)
문의: "검색에서 구성원이 안 나와요" / "조직도 월별 통계 오류"
1. **OpenSearch sync 깨진 경우 보정** → Operation API로 대응
   - produce type: `USER` → `userIds`만, `CUSTOMER` → `customerId` (null이면 `customerIdRange`), `ALL` → 전체 싱크
   - `deletedUsersOnly: true` → 삭제된 유저만 필터링 sync
   - ⚠️ 구성원 삭제 → 퇴직 정보 삭제 과정에서 `user data changed` 이벤트 발행으로 다시 생성될 수 있음
2. **조직도 월별 통계 오류** (`Key XXX is missing in the map`) → 삭제된 구성원 데이터가 ES에 남아서 발생. projection은 삭제된 구성원 포함, search는 제외 → 불일치. ES 싱크 한 번 맞추면 해결
3. **청구일 구성원 수 불일치** → 매월 5일 09:05 청구 시점 vs 이후 조회 시점 차이
   - 줄어드는 경우: 청구일 이후 퇴직일을 청구일 이전으로 설정 / 구성원 삭제
   - 늘어나는 경우: 청구일 이후 입사일을 청구일 이전으로 설정 / 입사 예정자 포함(as-is)

#### 데이터 접근 (추가)
```sql
-- 청구일 구성원 수 불일치: 청구일 이후 퇴직 처리된 구성원
SELECT * FROM flex.user_resignation
WHERE status = 'VALID' AND customer_id = ?
  AND db_updated_at > ?  -- paid_date
  AND begin_date < ?     -- paid_date
ORDER BY db_updated_at DESC;

-- 청구일 이후 입사 처리된 구성원 (입사일이 청구일 이전)
SELECT * FROM flex.user_employee
WHERE deleted_at IS NULL AND customer_id = ?
  AND db_created_at > ?      -- paid_date
  AND company_join_date < ?  -- paid_date
ORDER BY db_updated_at DESC;

-- 이메일 인증 요청 조회
SELECT * FROM flex_auth.email_verification
WHERE email LIKE '%@{some-domain}' ORDER BY db_created_at DESC;
```

#### 과거 사례 (추가)
- **조직도 월별 통계 오류**: 삭제된 구성원이 ES에 잔존 → projection/search 결과 불일치. ES 싱크로 즉시 해결 — **버그 (설계 한계)** [코어 런북]
- **청구일 구성원 수 불일치**: 청구 시점 스냅샷 vs 현재 시점 조회 차이. 퇴직/입사 처리 시점 확인으로 원인 설명 — **스펙** [코어 런북]

---

### 메일 미수신 — 코어 런북 보강

> 아래는 기존 알림 도메인 보강

#### 진단 체크리스트 (추가)
문의: "메일이 오지 않아요" (코어 런북 관점)
1. opensearch mgmt에서 해당 email의 발송 이력 확인 (별도 권한 필요)
   - `MessageObject.mail.destination`에 문제 이메일 검색
   - EventType: Send(전송 요청 성공) → Delivery(메일 서버 전송 성공) → Bounce(수신 거부) → Open(클라이언트 확인)
2. 해당 email 도메인의 MX record 확인 → [MX Lookup](https://mxtoolbox.com/)
3. **주로 문제가 되는 케이스**:
   - 수신 메일 서버 문제 → Send만 찍히고 Delivery 없음 → MX record로 서버 상태 확인
   - 유효하지 않은 이메일로 초대메일 발송 → 즉시 suppress list 등록 → CS팀이 수동 초대메일 발송하도록 유도
4. ⚠️ flex team 내부 메일은 **Mailgun**으로 발송 → opensearch mgmt의 SES 인덱스에서 확인 불가

---

### 출퇴근 (Work Clock)

> 출처: Notion 온콜 가이드

#### 진단 체크리스트
문의: "출근이 안 돼요" / "퇴근이 안 됐어요" / "근무 위젯이 이상해요"
1. Kibana에서 access log 확인: `json.authentication.email` + `json.ipath` 필터
2. 주요 API 경로 확인:
   - `/action/v2/time-tracking/work-clock/users/{userIdHash}/start/dry-run`
   - `/api/v2/time-tracking/work-clock/users/{userIdHash}/start`
   - `/api/v2/time-tracking/work-clock/users/{userIdHash}/stop`
   - `/api/v2/time-tracking/work-place/users/{userIdHash}/current-status`
3. `/current-status` 로그만 있고 `/start/dry-run` 없으면 → 근무지 범위 바깥
4. 관리자의 경우 IP 제한 패스 가능 (확인 필요)

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 시도한다.

**F1: 출근 불가 — 근무지 범위 확인** · [Notion 온콜 가이드]
> 트리거: "출근이 안 돼요" / "출근 버튼이 안 눌려요"

```
① Kibana access log에서 해당 유저의 요청 흐름 확인
   json.authentication.email + json.ipath 필터
   ↓
② API 호출 패턴 분석
   ├─ /current-status만 있고 /start/dry-run 없음 → 근무지 범위 바깥
   │   → 근무지 설정 확인 (GPS: flex.workplace / IP: flex_auth.customer_ip_access_control_setting)
   ├─ /start/dry-run 호출됐으나 /start 없음 → dry-run 실패, 응답 body 확인
   └─ /start 호출됐으나 에러 → 에러 응답 확인
```

#### 데이터 접근
- 서비스: `time-tracking-api` (K8s label: `flex-prod-prod-time-tracking-api`)
- 근무 위젯 편집기 요청 시 사용된 IP → Kibana access log에서 확인

---

### 근태 대시보드 (Dashboard)

> 출처: Notion 온콜 가이드

#### 진단 체크리스트
문의: "근태 대시보드 수치가 안 맞아요" / "휴가 사용 내역이 다르게 보여요"
1. 대시보드는 OpenSearch(ES) 기반 → 원본 데이터(MySQL)와 ES 동기화 상태 확인
2. 근무 동기화: `POST /action/operation/v2/time-tracking/sync-es-work-schedule`
3. 휴가 삭제 동기화: `POST /action/operation/v2/time-tracking/time-off/time-off-uses/produce-delete`
4. ES document 직접 삭제가 필요한 경우 별도 처리 (sync가 아닌 delete)

#### 조사 플로우

**F1: 대시보드 수치 불일치 — ES 동기화 확인** · [Notion 온콜 가이드]
> 트리거: "근태 대시보드 수치가 안 맞아요"

```
① MySQL 원본 데이터 확인
   해당 유저+날짜의 근무기록/휴가사용 실제 데이터 조회
   ↓
② OpenSearch 문서 확인
   prod-v2-tracking-work-schedules / prod-v2-tracking-time-off-uses 인덱스
   ├─ 문서 없음 → sync 누락, ③으로
   └─ 문서 있으나 내용 불일치 → sync 누락, ③으로
   ↓
③ 수동 동기화 실행
   ├─ 근무: POST /action/operation/v2/time-tracking/sync-es-work-schedule
   └─ 휴가: POST /action/operation/v2/time-tracking/time-off/time-off-uses/produce-delete
   ⚠️ ES document가 잔존하는데 원본이 삭제된 경우 → sync가 아닌 delete 처리 필요
```

---

### 연차 (Annual Time Off)

> 출처: Notion 온콜 가이드

#### 진단 체크리스트
문의: "잔여 연차가 이상해요" / "연차 소멸이 안 맞아요" / "사용일수가 0일이에요"
1. operation API에서 annual-time-off bucket 확인
2. 연차 사용 순서: (1) 유효기간 종료일 이른 것 우선 (2) 종료일 같으면 시작일 이른 것 우선
3. 사용일수 0일 → 해당일에 다음 항목 겹침 확인:
   - 휴일: `v2_customer_holiday`
   - 휴직: `user_leave_of_absence`
   - 휴일대체: `v2_time_tracking_user_alternative_holiday_event`
   - 주휴일: `v2_customer_work_rule` 요일별 설정
   - 쉬는날
4. 월차는 입사 후 1년간 사용 가능, 막달 받은 연차는 그 다음달에 소멸
5. Metabase에서 조회 후 jsongrid.com에서 가독성 확인

#### 조사 플로우

**F1: 잔여 연차 불일치 — 버킷 확인** · [Notion 온콜 가이드]
> 트리거: "잔여 연차가 이상해요" / "연차 소멸이 안 맞아요"

```
① operation API에서 annual-time-off bucket 조회
   → 부여/사용/소멸/조정 내역 전체 확인
   ↓
② 사용 순서 검증
   유효기간 종료일 이른 것 우선 → 종료일 같으면 시작일 이른 것 우선
   ↓
③ 불일치 원인 분류
   ├─ 조정 이력 누락 → v2_user_annual_time_off_adjust_assign 확인
   ├─ 소멸 시점 차이 → 월차 소멸 규칙 확인 (입사 1년 기준)
   └─ 겹침으로 인한 0일 사용 → F2 시도
```

**F2: 사용일수 0일 — 겹침 확인** · [Notion 온콜 가이드]
> 트리거: "사용일수가 0일이에요"

```
① 해당일에 겹치는 항목 확인
   ├─ v2_customer_holiday → 휴일 등록 여부
   ├─ user_leave_of_absence → 휴직 기간
   ├─ v2_time_tracking_user_alternative_holiday_event → 휴일대체
   ├─ v2_customer_work_rule → 해당 요일이 주휴일/쉬는날
   └─ 위 항목 중 하나라도 해당 → 사용일수 0일은 스펙
```

#### 데이터 접근
```sql
-- 휴직 설정 확인
SELECT * FROM flex.user_leave_of_absence WHERE user_id = ?;

-- 연차 정책 확인
SELECT * FROM flex.v2_customer_annual_time_off_policy WHERE customer_id = ?;

-- 연차 사용 이벤트
SELECT * FROM flex.v2_user_time_off_event WHERE user_id = ? AND customer_id = ?;

-- 연차 조정 이력
SELECT * FROM flex.v2_user_annual_time_off_adjust_assign WHERE user_id = ?;
```

#### 환경 재현 시 필요 테이블
- 입사일: `user_employee_audit`
- 근무유형: `v2_user_work_rule`, `v2_customer_work_rule`, `v2_customer_work_record_rule`
- 연차정책: `v2_customer_annual_time_off_policy`
- 연차사용/조정: `v2_user_time_off_event`, `v2_user_time_off_event_block`, `v2_user_annual_time_off_adjust_assign`

---

### 맞춤휴가 (Custom Time Off)

> 출처: Notion 온콜 가이드

#### 진단 체크리스트
문의: "맞춤휴가 잔여가 이상해요" / "휴가 합치고 싶어요" / "단위 변경하고 싶어요"
1. 부여 내역: Metabase question/2452
2. 사용/취소 내역: Metabase question/2166
3. 합쳐쓰기 조건: 서로 다른 `v2_user_custom_time_off_assign`을 코드 해석으로 묶는 것 (DB 합치기 아님). assign 속성(사용 단위 등)이 동일해야 함
4. 합치기 요청 → 회수 후 재부여 권장. DML 직접 보정은 operation API 없어 최후의 수단
5. 단위 변경 → 바꾸면 못 쓰는 휴가 발생 가능. 회수 후 재부여 또는 assign 테이블에서 변경

#### 조사 플로우

**F1: 맞춤휴가 잔여 불일치** · [Notion 온콜 가이드]
> 트리거: "맞춤휴가 잔여가 이상해요"

```
① Metabase에서 부여/사용/취소 내역 확인
   부여: question/2452 → 사용/취소: question/2166
   ↓
② 부여 총량 - 사용량 - 회수량 = 잔여 계산
   ├─ 계산 일치 → 고객 오해, 내역 설명
   └─ 계산 불일치 → assign/withdrawal 테이블 직접 조회
```

#### 데이터 접근
```sql
-- 맞춤휴가 부여 확인
SELECT * FROM flex.v2_user_custom_time_off_assign WHERE user_id = ? AND customer_id = ?;

-- 맞춤휴가 회수 확인
SELECT * FROM flex.v2_user_custom_time_off_assign_withdrawal WHERE customer_id = ?;

-- 일괄 부여 확인
SELECT * FROM flex.v2_customer_bulk_time_off_assign WHERE customer_id = ?;
```

---

### 근무지 (Work Place)

> 출처: Notion 온콜 가이드

#### 진단 체크리스트
문의: "근무지 밖에서 출근이 됐어요" / "IP 제한이 안 먹혀요" / "출근 버튼이 안 눌려요"
1. GPS 설정: `flex.workplace` 테이블에서 좌표/반경 확인
2. IP 설정: `flex_auth.customer_ip_access_control_setting` 확인
3. `/current-status` 로그만 있고 `/start/dry-run` 없으면 → 범위 바깥으로 판단된 상태
4. 관리자는 IP 제한 패스 가능 (수정 예정)
5. 클라이언트 WorkPlaceTicket V1 파싱으로 상세 정보 확인 가능

#### 데이터 접근
```sql
-- GPS/근무지 설정 확인
SELECT * FROM flex.workplace WHERE customer_id = ?;

-- IP 제한 설정 확인
SELECT * FROM flex_auth.customer_ip_access_control_setting WHERE customer_id = ?;
```

---

### 휴일 (Holiday)

> 출처: Notion 온콜 가이드

#### 진단 체크리스트
문의: "휴일이 안 보여요" / "대체휴일이 적용 안 돼요" / "근로자의날 삭제해주세요"
1. 유저-휴일 매핑: `v2_user_holiday_group_mapping` → `v2_customer_holiday_group` → `v2_customer_holiday`
2. 대체휴일: `v2_customer_holiday`의 `support_alternative`, `supports_saturday_alternative` 확인
3. 휴일대체 범위(gap): `flex-timetracking-config` repo의 `experimental.json`
4. 휴일대체 Metabase: question/5062
5. 근로자의날 삭제 → operation API로 제거 (PR #7421 참조)
6. 특정 유저의 휴일 조회 → operation API 사용

#### 조사 플로우

**F1: 휴일 미표시 — 매핑 확인** · [Notion 온콜 가이드]
> 트리거: "휴일이 안 보여요"

```
① 유저-휴일그룹 매핑 확인
   v2_user_holiday_group_mapping WHERE user_id = ?
   ├─ 매핑 없음 → 휴일 그룹 미배정
   └─ 매핑 있음 → ②로
   ↓
② 휴일 그룹에 해당 휴일 등록 여부 확인
   v2_customer_holiday_group → v2_customer_holiday
   ├─ 휴일 미등록 → 관리자에게 등록 안내
   └─ 휴일 등록됨 → 날짜/타입 확인, 대체휴일 설정 확인
```

#### 데이터 접근
```sql
-- 유저의 휴일 그룹 매핑
SELECT * FROM flex.v2_user_holiday_group_mapping WHERE user_id = ?;

-- 휴일 그룹 상세
SELECT * FROM flex.v2_customer_holiday_group WHERE customer_id = ?;

-- 개별 휴일 목록
SELECT * FROM flex.v2_customer_holiday WHERE customer_holiday_group_id = ?;

-- 휴일대체 이벤트
SELECT * FROM flex.v2_time_tracking_user_alternative_holiday_event WHERE user_id = ?;
```

---

### 캘린더 연동 (Calendar Integration)

> 출처: Notion 온콜 가이드

#### 진단 체크리스트
문의: "구글 캘린더에 휴가가 안 떠요" / "캘린더 연동이 안 돼요"
1. 연동 파이프라인: TT → 플렉스 캘린더 → 구글 캘린더
2. `GoogleCalendarEventAdapter`가 토픽에 발행 → `FlexCalendarSyncEventConsumer`가 컨슘
3. 구캘 등록 조건:
   - 근무: 근무 정책별 상이
   - 휴가: 승인 완료 후 구캘 등록, 취소 승인 완료 후 구캘 삭제
4. 동기화 안 됐을 경우 담당: `@ug-team-service-platform-on-call`
5. ⚠️ 캘린더 지원 종료 예정: 2025. 7. 9

#### 조사 플로우

**F1: 구글 캘린더 동기화 실패** · [Notion 온콜 가이드]
> 트리거: "구글 캘린더에 휴가가 안 떠요"

```
① 승인 상태 확인
   ├─ 미승인 → 승인 완료 후 동기화되는 스펙
   └─ 승인 완료 → ②로
   ↓
② flex_calendar_event_map 테이블에서 이벤트 매핑 확인
   v2_time_tracking_flex_calendar_event_map WHERE user_id = ?
   ├─ 매핑 없음 → Kafka produce 실패 가능성, 로그 확인
   └─ 매핑 있음 → 플렉스 캘린더 → 구글 캘린더 구간 문제
       → 담당: @ug-team-service-platform-on-call
```

#### 데이터 접근
```sql
-- 캘린더 이벤트 매핑 확인
SELECT * FROM flex.v2_time_tracking_flex_calendar_event_map WHERE user_id = ?;
```

---

### Kafka 메시지 재발행

> 출처: Notion 온콜 가이드

#### 진단 체크리스트
1. 에러 메시지에서 `<topic>@<offset>` 값으로 offset 확인
2. kafka-ui에서 해당 offset의 메시지를 찾아 `ce_id` (cloud_event) 확인
3. `ce_id` 또는 `consume_log`로 operation API 호출하여 재발행
4. `cloud_event_entity`: 프로듀싱 때 쌓임. 프로듀싱 실패 시 `produced_at`이 안 쌓임
5. `message_consume_log`: ce_id 단위로 insert. 실패 시 백오프 후 마지막까지 실패하면 에러 로그 찍고 commit

#### 조사 플로우

**F1: Kafka 컨슘 실패 — 메시지 재발행** · [Notion 온콜 가이드]
> 트리거: Kafka Consumer Error 로그 / 컨슘 실패 알림

```
① 에러 메시지에서 topic@offset 추출
   ↓
② kafka-ui에서 해당 offset 메시지 확인
   → ce_id (cloud_event) 값 추출
   ↓
③ operation API로 재발행
   ce_id 또는 consume_log 기반 호출
   ↓
④ 재발행 후 정상 처리 확인
   message_consume_log에서 상태 확인
```

**F2: 사용자 변경 이벤트 컨슘 실패** · [Notion 온콜 가이드]
> 트리거: `Kafka Consumer Error[userDataChangedEvent]. identities: [SimpleCustomerUserIdentity(...)]`

```
① 에러 로그에서 customerUserIdentity 추출
   ↓
② Workspace Operation API 호출
   POST /action/operation/v2/workspace/users/produce
   body: { productType: "USER", identities: [...] }
```

---

### 근무 기록 삭제/복구

> 출처: Notion 온콜 가이드

#### 진단 체크리스트
문의: "근무 기록 삭제해주세요" / "삭제한 데이터 복구해주세요" / "휴가 기록 삭제해주세요"

**원칙: DB 직접 수정은 하지 않음. 고객이 직접 처리하도록 안내**

근무 기록 삭제 시 영향 테이블:
- `v2_user_work_record_event` (근무 이벤트)
- `v2_user_work_record_event_block` (블럭)
- `v2_user_work_record_approval_content` (승인 문서)
- `v2_user_work_record_event_approval_mapping` (매핑)
- `v2_time_tracking_approval_event` (승인 상태)

휴가 기록 삭제 시 영향 테이블:
- 부여/조정: `v2_user_custom_time_off_assign`, `v2_user_custom_time_off_assign_withdrawal`, `v2_customer_bulk_time_off_assign`, `v2_user_compensatory_time_off_assign`, `v2_user_compensatory_time_off_assign_times`, `v2_user_annual_time_off_adjust_assign`
- 사용: `v2_user_time_off_use`, `v2_user_time_off_event`, `v2_user_time_off_event_block`
- 연촉: `v2_annual_time_off_boost_setting`, `annual_time_off_boost_history`, `v2_user_annual_time_off_boost_evidence_record`
- 승인: `v2_time_off_approval_content`, `v2_time_off_approval_content_unit`, `v2_time_tracking_time_off_approval_content`
- ES: document 삭제 필요 (sync가 아닌 delete)

#### 조사 플로우

**F1: 근무/휴가 기록 삭제 요청 대응** · [Notion 온콜 가이드]
> 트리거: "근무 기록 삭제해주세요" / "휴가 기록 삭제해주세요"

```
① 요청 유형 분류
   ├─ 근무 기록 삭제 → 고객이 직접 처리하도록 안내 (DB 직접 수정 불가)
   ├─ 삭제 데이터 복구 → 별도 절차 문서 참조
   ├─ 휴가 기록 삭제 → DB 직접 건드리지 않음, 고객 안내
   └─ 변경 예정 근무유형 삭제 → 제품에서 한 명씩 처리, 벌크는 operation API 필요
```

FAQ:
- 근무 기록 삭제 → 안 됨. 고객이 직접 처리
- 삭제 데이터 복구 → 별도 절차 문서 참조
- 휴가 기록 삭제 → DB 직접 건드리지 않음
- 변경 예정 근무유형 삭제 → 제품에서 한 명씩, 벌크는 operation API 필요

---

### 시스템 모니터링

> 출처: Notion 온콜 가이드

#### 진단 체크리스트

#### 모니터링 도구 가이드
| 대상 | 도구 | 비고 |
|------|------|------|
| 최근 10분 에러 | Kibana, Splunk(SignalFx) | |
| SpringBoot APM | Grafana | API/CRON 별도 대시보드 |
| Database | AWS RDS Grafana 대시보드 | |
| Kafka consumer | Grafana Kafka consumer dashboard | |
| 특정 API 속도 추이 | Kibana 대시보드 | |

Kibana 참고:
- prod 로그 보관: 1개월 (검색 가능)
- 유저 액세스 로그: `json.authentication.email` 필터로 조회

---

### 난제 사례 (Edge Cases)

> 출처: Notion 온콜 가이드

#### 진단 체크리스트

#### 부여된 휴가보다 더 사용한 케이스
원인: 휴가 사용 → 해당일에 휴일 등록 → 버킷 복구 → 또 휴가 사용 → 휴일 삭제 순서로 발생

#### 공동연차 패턴
시즌오프일에 휴일 설정 → 출근자는 휴일근무로 등록 → 휴일 제거. 이 과정에서 맞춤휴가(보상휴가) 버킷 초과 사용 가능

---

## 변경 이력

| 날짜 | 이슈 | 변경 내용 |
|------|------|----------|
| 2026-03-20 | Notion 온콜 가이드 | 신규 도메인 11개 추가 — 출퇴근, 근태 대시보드, 연차, 맞춤휴가, 근무지, 휴일, 캘린더 연동, Kafka 메시지 재발행, 근무 기록 삭제/복구, 시스템 모니터링, 난제 사례 |
| 2026-03-19 | [코어 온콜 런북](https://www.notion.so/19d0592a4a928051956ec7773e47ef2d) | Core Squad 온콜 런북 18개 항목 반영 — 신규 도메인 3개(조직 관리, 인사발령, 체크리스트), 기존 도메인 보강(계정/구성원, 승인, OpenSearch/통계, 메일), domain-map.ttl 도메인·키워드·glossary 추가 |
| 2026-03-19 | 전체 | --rebuild 전체 재구성 — domain-map verdict 3건 수정(CI-4117/CI-4132/CI-4151 → bug), 계정 도메인에 CI-4166(계열사 전환 스펙) 추가, 평가 도메인에 QNA-1936(raccoon 환경 불일치) 추가, glossary 항목 추가 |
| 2026-03-19 | 전체 | 전체 재구성 — 전자계약 도메인 신규 추가(CI-4152, CI-4168), 근태/휴가(CI-4130, CI-4140, CI-4147), 외부 연동(CI-4157, CI-4165), 인증(CI-4166), 평가(CI-4158), 채용(CI-4170) 반영, 급여 중복 정리 |
| 2026-03-18 | QNA-1933 | 급여 도메인에 구독 해지 후 명세서 알림 발송 스펙 + 1달 연장 안내 권장 추가 |
| 2026-03-18 | CI-4150 | 권한 도메인 추가 — 최고관리자 자동 부여 스펙, 감사로그 미기록 안내, grant_subject SQL 추가 |
| 2026-03-18 | CI-4149 | 급여 도메인에 정산 재처리 시 부양가족 수 최신화로 소득세 변경 스펙 추가 |
| 2026-03-18 | CI-4142 | 알림 도메인에 메일 미수신 SES 진단 흐름·mail_send_history 중단 안내·사례 추가 |
| 2026-03-18 | 일괄 유지보수 | 근태/휴가 도메인 — QNA-1920(연차 부여 시작일 스펙), QNA-1928(리포트 컬럼 스펙) 추가 |
| 2026-03-18 | QNA-1933 | 급여 도메인 — 구독 해지 후 명세서 공개/알림 동작 스펙 추가 |
| 2026-03-18 | 전체 | 조사 플로우 섹션 추가 — 알림(F1-F3), 근태/휴가(F1-F3), 교대근무(F1), 외부 연동(F1-F2) |
| 2026-03-18 | CI-4145 | 근태/휴가 + 외부 연동 도메인 — 세콤/캡스/텔레캅 퇴근 정시 고정 진단 체크리스트·사례 추가 |
| 2026-03-17 | CI-4131 | 급여 도메인에 올림 설정 스냅샷 진단 체크리스트·SQL·사례 추가 |
| 2026-03-17 | CI-3951 | 승인 도메인 추가 — 퇴직자 승인자 교체 고아 승인 요청 진단 가이드 |
| 2026-03-17 | TT-16783 | 외부 연동 도메인 — 다법인 workspace customerKey 충돌 진단 가이드 추가 |
| 2026-03-17 | QNA-1922 | 근태/휴가 도메인 — 선택적 근무 추천 휴게 자동 입력 스펙 추가 |
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
