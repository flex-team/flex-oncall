# 운영 쿡북

> 이슈 조사 전에 이 문서를 먼저 참조하면 조사 시간을 단축할 수 있다.
> 각 항목의 상세는 출처 이슈 노트를 참조.
> SQL 템플릿과 과거 사례는 `cookbook/` 디렉토리의 도메인별 파일에 있다.

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
   4. **admin-shell 이메일 발송 로그**로 Delivery/Bounce 확인: admin-shell → pavement-admin → 이메일 발송 로그 탭 (https://admin-shell.flexis.team/pavement/mail/ses-feedback). 또는 SES 이벤트 OpenSearch (`flex-prod-ses-feedback-*`)에서 `MessageObject.mail.destination` 필터
   5. SES Delivery 확인됨 → flex 측 정상, 고객에게 수신 서버/스팸 필터 확인 요청

> ⚠️ `mail_send_history` 테이블은 BEI-151(2026-02-20)로 기록 중단됨. 메일 발송 여부는 admin-shell 이메일 발송 로그 또는 SES 이벤트 OpenSearch로 확인해야 한다.

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

**F4: 메일 중복 발신 — file merge 무한 재시도** · 히트: 1 · [CI-4236]
> 트리거: "다운로드 완료 메일이 계속 와요" / "메일을 수백통 받았어요" / 알림 타입 `FLEX_FILE_STORAGE_DOWNLOAD_PREPARATION_COMPLETED`

```
① Kafka consumer group 상태 확인
   prod Kafka UI → consumer group: prod-flex-file-storage-api-file-storage-merge-command-handler
   topic: prod.command.flex.file-storage.merge.v1
   ├─ PREPARING_REBALANCE + lag 증가 → 무한 리밸런스 확인 → ②
   └─ STABLE + lag 0 → 다른 원인 (F1~F3 시도)
   ↓
② DB에서 동일 요청 반복 생성 확인
   SELECT customer_id, status, merged_file_name, COUNT(*) FROM flex.v2_file_merge
   WHERE customer_id = ? GROUP BY customer_id, status, merged_file_name
   ├─ 동일 파일명 수백건 → render 타임아웃으로 인한 재시도 폭증 → ③
   └─ 정상 건수 → consumer max.poll.interval.ms 초과 단순 케이스 → 설정 조정
   ↓
③ 즉시 대응
   a. max.poll.interval.ms 증가 (10분+) → consumer 안정화
   b. CPU 증설 (file-storage consumer 스로틀링 확인)
   c. 잔여 TODO 건을 DONE으로 UPDATE → consumer skip 유도
   ↓
④ 근본 해결: renderer 타임아웃 개선 (EPBE-230 참조)
```

→ 상세: [cookbook/notification.md](cookbook/notification.md)

---

### 연차촉진 (Annual Time-Off Promotion)

#### 진단 체크리스트
문의: "연차 사용 계획 작성 알림이 계속 와요" / "촉진 문서가 화면에 안 보여요" / "연차 대상이 아닌데 촉진 알림이 와요"
1. `annual_time_off_boost_history` 테이블에서 해당 건의 `status`, `boosted_at` 확인
2. `boosted_at`이 UTC 기준 연도 경계(12/31 23:xx)인지 확인 → KST 변환 시 다음 연도인데 UTC로는 이전 연도 → 목록 조회에서 누락 [CI-3907], [CI-3809]
3. 관리자에 의해 종료된 이력이 있는지 확인 → 히든 스펙: 종료 이력 있으면 기한 지난 건은 목록에서 필터링, 단 알림은 필터링 안 됨 [CI-3777]
4. MONTHLY/MONTHLY_FINAL 간 연동 여부 확인 → 1차/2차는 독립 동작, 2차 완료해도 1차 알림 지속 가능 [CI-3809]
5. 사용자의 연차 정책이 변경되었는지 확인 → `v2_user_customer_annual_time_off_policy_mapping`의 `modified_at`과 촉진 이력의 `created_date` 비교. 정책이 `enabled_annual_time_off_policy = false`인데 PENDING_WRITE 이력이 있으면 정책 변경 전 잔존 이력 → TODO/알림 수동 정리 필요 [CI-3932]

→ 상세: [cookbook/annual-promotion.md](cookbook/annual-promotion.md)

---

### 근태/휴가 (Time Tracking)

#### 진단 체크리스트
문의: "휴일대체 기간이 안 맞아요" / "보상휴가 부여 안 돼요" / "포괄 공제가 안 맞아요" / "휴일대체 탭에 날짜가 안 보여요" / "퇴사자 휴가 데이터 추출해주세요" / "퇴근 시간이 잘렸어요" / "퇴근이 정시로 찍혀요" / "휴직 기간에 휴가가 있어요" / "추천 휴게가 안 들어가요" / "연차 사용 내역이 사라졌어요" / "근태기록 리포트 컬럼이 이상해요" / "휴일대체 사후신청이 안 돼요" / "월별 잔여연차가 달라요" / "보상휴가 회수했는데 잠금이 안 풀려요" / "휴일대체 취소가 안 돼요"
1. 휴일대체 탭 미표기 → 먼저 OpenSearch dev tools로 해당 유저+날짜 문서 존재 확인 [CI-3949]
   - **문서 자체가 없음** → 근무를 건드리지 않은 유저는 sync 이벤트 미발생으로 OS 문서 미생성. 수동 sync 실행: `POST /action/operation/v2/time-tracking/sync-os-work-schedule-advanced` [CI-3949]
   - **문서는 있는데 `holidayProps`가 null** → 해당 날짜 **시점의** 활성 근무유형 확인 (현재 근무유형이 아님!). `v2_user_work_rule`에서 date_from/date_to 범위로 확인 → 해당 요일이 `WEEKLY_UNPAID_HOLIDAY`(휴무일)이면 스펙대로 제외. `WEEKLY_PAID_HOLIDAY`(주휴일)인데 null이면 버그 → 추가 조사 필요 [CI-3949]
2. 휴일대체 기간 문의 → 회사별 gap 커스텀 설정 확인 (`TrackingExperimentalDynamicConfig`) → config 변경으로 해결 가능 [CI-3897] [CI-4186] [CI-4199]
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
16. **근무유형 적용 시 500 오류** → `v2_user_work_rule`에서 해당 유저의 마지막 이벤트가 `CANCEL`인지 확인. CANCEL이면 유효 매핑 없는 상태 → 비활성(`active=0`) 근무유형의 CANCEL INSERT로 데이터 보정 [CI-4180]
17. 근무유형 삭제 불가 ("근무 예약이 있어서 삭제 못 합니다") → 아래 구조 이해 후 대응
   - **근무유형(`v2_customer_work_rule`)은 soft-delete** — 삭제 시 `active=false` 비활성화
   - **유저-근무유형 매핑(`v2_user_work_rule`)은 time-series** — REGISTER/CANCEL 이벤트가 쌓이는 구조. 매핑 존재 ≠ 삭제 불가 (해석 결과에서 해당 근무유형이 없으면 삭제 가능)
   - **미래 예약만 취소 가능**, 벌크 취소 기능 없음 (유저 단건 처리만 가능)
   - **동일 근무유형으로 벌크 변경 시** core에서 validation 에러 발생 (대량 변경 테이블에서 같은 근무유형으로 변경 불가)
   - **운영 대응**:
     ◦ 급한 경우: DB에서 `v2_user_work_rule` row 삭제 → ES sync
     ◦ 여유 있는 경우: Operation API `DELETE /api/v2/work-rule/users/{userId}/work-rules/{userWorkRuleId}` 반복 호출 (검증 유/무 분리된 operation API 존재, PR flex-timetracking-backend#7800)
18. **휴일대체 취소 불가** ("대체 휴일을 찾을 수 없습니다") → 휴일대체 수정(CANCEL+재등록) 후 OpenSearch sync 지연으로 FE에 구 eventId가 전달되는 케이스. access log에서 `search/by-departments` 응답의 `alteredHoliday.eventId` 확인 → DB(`v2_time_tracking_user_alternative_holiday_event`)의 유효 이벤트 ID와 비교 → 불일치 시 `/sync-os-work-schedule-advanced`로 재동기화 [CI-4217]

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

**F4: 휴일대체 취소 불가 — OpenSearch sync 지연** · 히트: 1 · [CI-4217]
> 트리거: "휴일대체 취소가 안 돼요" / "대체 휴일을 찾을 수 없습니다"

```
① access log: search/by-departments 응답에서 해당 유저의
   alteredHoliday.trackingUserAlternativeHolidayEventId 확인
   ↓
② DB: v2_time_tracking_user_alternative_holiday_event에서
   해당 유저의 유효 이벤트 ID 확인 (CANCEL되지 않은 최신 이벤트)
   ├─ access log eventId == DB eventId → 다른 원인 조사
   └─ 불일치 → ③으로 (OpenSearch sync 지연)
   ↓
③ operation API로 OpenSearch 재동기화
   POST /action/operation/v2/time-tracking/sync-os-work-schedule-advanced
   ↓
④ 동기화 후 OpenSearch 문서의 holidayProps.alteredHoliday.eventId 정상 확인
   ↓
⑤ 고객 안내: 페이지 새로고침 후 취소 재시도
```

> 💡 원인: 휴일대체 수정(CANCEL+재등록) 시 `NON_NULL` + `doc()` partial update 조합으로 null 필드가 기존값 유지 → 구 eventId 잔존

→ 상세: [cookbook/time-tracking.md](cookbook/time-tracking.md)

---

### 스케줄링 (Scheduling)

#### 진단 체크리스트
문의: "스케줄 게시가 안 돼요" / "정시 전 출근 불가가 안 먹혀요" / "연장근무가 이상해요"
1. 게시 차단 문의 → dry-run API 응답의 `validationLevel` 확인 (WARN vs ERROR). FE가 WARN을 ERROR로 처리하는 버그 있음 [CI-3862]
2. 정시 전 출근 불가 미작동 → 스케줄이 실제로 **게시**되었는지 확인 (임시 저장 ≠ 게시). 게시 안 된 상태면 정시 기준 없음 [CI-3866]
3. 주 연장근무 발생 → `agreedWorkingMinutes`(근무규칙) vs `requiredWorkingMinutes`(스케줄) 차이 확인 [CI-3839]

→ 상세: [cookbook/scheduling.md](cookbook/scheduling.md)

#### 조사 플로우

### 근무 기록 업로드 오류 (F-sched-upload)

> 트리거: "근무 기록 업로드 오류", "업로드 시 에러", "벌크 업로드 실패"
> 히트: 1 (CI-4221)

1. access log에서 `bulk-upload` 요청의 `responseStatus` + `elapsedTime` 확인
   - 400 (dry-run) → 엑셀 데이터 검증 실패. 반환 엑셀의 오류 표시 확인 안내
   - 200 + elapsedTime > **180초** → CloudFront origin_read_timeout 초과로 유저에게 504 표시. 서버는 정상 처리 완료. 파일 분할 안내
   - 200 + elapsedTime 60~180초 → CF 통과하지만 느림. 파일 분할 권장
   - 500 → 서버 에러. traceId로 app log 추적
2. 대량 데이터(구성원 × 날짜 많음)면 분할 업로드 안내
3. 근본 원인: N+1 순차 처리 패턴. 후속 개선은 비동기 전환 검토 중 [CI-4221]

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

→ 상세: [cookbook/shift.md](cookbook/shift.md)

---

### 외부 연동 (Integration)

#### 진단 체크리스트
문의: "세콤 연동이 풀렸어요" / "수동 전송했는데 반영 안 돼요" / "세콤 연동 프로토콜 타입이 뭔가요?" / "세콤으로 퇴근했는데 정시로 찍혀요" / "세콤 출근이 반영 안 돼요" / "진행중 블럭이 여러 개 떠요" / "ODBC 연결이 안 돼요" / "수동 동기화 실패" / "캡스 연결이 안 돼요" / "방화벽 해제 방법 알려주세요" / "flex IP 주소 알려주세요"
1. 연동 비활성화 주체 확인 → 구독 해지 외 자동 변경 없음. log-dashboard에서 API 호출 이력 확인 [CI-3849]
2. 비활성화 상태에서 수동 전송 → 비활성화 기간 데이터는 소급 불가 [CI-3849]
3. 수동 전송 반영 안 됨 → 세콤 데이터 수신 순서 확인 (퇴근→출근 역순 수신 가능) [CI-3861]
4. 세콤/캡스/텔레캅 퇴근이 정시로 고정 → **근태/휴가 도메인의 항목 7** 참조. 외부 타각기 자체 문제가 아닌 유저 퇴근 preference 설정(`ON_TIME`) 문제. 날짜별 퇴근 기록 비교가 핵심 [CI-4145]
4. 프로토콜 확인 → **PostgreSQL (TCP/IP)** 고정. `CustomerExternalProviderConnectionInfoDto` 응답의 `url`, `port`, `user`, `password`, `database` 필드를 참조
5. 출입연동 커넥션 수 변경 요청 → admin-shell에서 직접 변경. 업체별 기본값: 캡스 2, 세콤 2, KT(텔레캅) 3 [QNA-1842]
6. 다법인 workspace에서 연동 등록 실패 (`하나의 계열사 안에 서로 다른 외부 연동 정보가 존재합니다`) → workspace 내 동일 providerType에 서로 다른 customerKey 존재 여부 확인. 다법인 지원 이전 데이터 마이그레이션 누락이 원인. 데이터 패치로 key 통일 필요 [TT-16783]
7. 세콤 출근 미반영 + 진행중 위젯 잔존 → **먼저 잔존 위젯 확인**. 이전 근무의 위젯이 미종료 상태이면 새 출근 이벤트가 dry-run validation에서 차단됨. Operation API로 잔존 위젯 수동 종료 후 재처리 [CI-4157]
8. 세콤/외부 이벤트로 진행중 블럭 다건 발생 → 다수 터미널에서 동시 이벤트 수신 시 Kafka 동시성 race condition으로 중복 START 등록 가능. `isDraftEventRegistrationAllowed`가 이벤트 타입(START/STOP) 미구분하여 통과시킴 [CI-4165]
   - 세콤 배치 동기화 중복 START → `checkWorkClockStatus()` 의 `eventTimeStamp` vs `targetTime` 역전 버그. `min(eventTimeStamp, targetTime)` 으로 수정 완료 [CI-4207, PR #12058]
9. ODBC 연결 실패 (CONNECTION LIMIT 0) → `v2_customer_external_provider`에서 `odbc_connection_limit` 조회. 0이면 PostgreSQL ROLE의 `CONNECTION LIMIT 0`으로 모든 연결 차단. Operation API로 connectionLimit을 기본값(SECOM/CAPS=2, TELECOP=3)으로 변경 [CI-4190]
10. 캡스 수동 동기화 "전송 실패" → Grafana 캡스 RDB 모니터링에서 로그 확인. `e_date` 컬럼이 보이면 **테이블 매핑 설정 오류**. 고객에게 올바른 매핑 설정 가이드 안내 [CI-4202]
11. 캡스/세콤 연결 실패 + "방화벽 문제" 주장 → **먼저 DB 로그에서 패스워드 실패 여부 확인**. 고객/기사의 PW 오입력이 원인인 경우가 많음. ODBC 연결 성공했다면 방화벽은 거의 아님 [FT-12290]
12. 방화벽 해제 / flex IP 요청 → **IP는 변경될 수 있으므로 제공 불가**. 도메인(`flex-caps.flex.team`, `flex-secom.flex.team`) 기반 예외처리를 안내. CMD 명령어(`nslookup`, `telnet`, `tracert`)로 네트워크 연결 상태 확인 후 결과 전달 요청 [FT-12290]

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

**F4: ODBC 연결 실패 — CONNECTION LIMIT 0 차단** · 히트: 1 · [CI-4190]
> 트리거: "ODBC 연결 오류" / "PostgreSQL 연결 거부" / 세콤 초기 연동 설정 중 연결 실패

```
① v2_customer_external_provider 조회
   SELECT customer_id, provider_type, odbc_connection_limit, active
   FROM v2_customer_external_provider WHERE customer_id = ?;
   ├─ odbc_connection_limit = 0 → CONNECTION LIMIT 0으로 전체 차단. ②로
   ├─ odbc_connection_limit >= 1 + active=true → SSL/방화벽/ODBC 드라이버 설정 확인
   └─ 레코드 없음 → provider 계정 미생성. 초기 연동 프로세스 재확인
   ↓
② Operation API로 connectionLimit 변경
   POST /api/operation/v2/time-tracking/external-provider/customers/{customerId}/providers/{providerType}/db-connection-info
   Body: { "connectionLimit": 2 }  (SECOM/CAPS=2, TELECOP=3)
   → MySQL(odbc_connection_limit) + PostgreSQL ROLE(CONNECTION LIMIT) 모두 변경됨
```

**F5: 캡스/세콤 연결 실패 — 인증 오류 vs 방화벽 구분** · 히트: 1 · [FT-12290]
> 트리거: "캡스 연결이 안 돼요" / "방화벽 해제해주세요" / "flex IP 알려주세요"

```
① 고객이 "방화벽 문제"라고 단정 → 검증 필요, 바로 수용하지 않음
   ↓
② DB 로그에서 패스워드 실패 여부 확인
   ├─ PW 실패 로그 있음 → 인증 정보 재입력 안내 (캡스 기사/고객에게)
   └─ PW 실패 없음 → ③으로
   ↓
③ 고객에게 CMD 진단 명령어 실행 요청
   nslookup flex-caps.flex.team  → amazonaws 나오면 DNS 정상
   telnet flex-caps.flex.team 5432 → 빈 화면이면 연결 성공, "연결 불가"면 차단
   tracert flex-caps.flex.team
   ├─ 연결 차단 확인 → 도메인 기반 방화벽 예외처리 안내 (IP 제공 불가)
   └─ 연결 정상 → 캡스/세콤 프로그램 설정 재확인
```

> ⚠️ **IP 제공 불가 정책**: flex 서버 IP는 변경될 수 있으므로 고객에게 직접 제공하지 않음.
> 도메인 기반 예외처리를 안내하고, ODBC 연결 성공 여부로 방화벽 문제를 판별.

**고객사 방화벽 허용 설정 안내값:**

| 항목 | 값 |
|------|-----|
| 프로토콜 | TCP |
| 접속 방식 | PostgreSQL 직접 연결 (ODBC/JDBC) |
| 대상 호스트 | `flex-secom.flex.team` (세콤) / `flex-caps.flex.team` (캡스) |
| 포트 | `5432` |
| 데이터베이스 | `postgres` |

→ 상세: [cookbook/integration.md](cookbook/integration.md)

---

### 권한 (Permission)

#### 진단 체크리스트
문의: "누가 언제 권한을 부여했는지 확인해주세요" / "감사로그에서 권한 변경이 안 보여요"
1. `flex_authorization.flex_grant_subject`에서 대상 사용자의 grant 멤버십 확인 → `created_at`이 포함 시점, `created_by`가 수행자 [CI-4150]
2. 대상 사용자가 grant에 없으면 → 이미 회수됨 (물리 삭제로 이력 소실). 회사 최초 유저인지 확인 → 최초 유저라면 회사 생성 시 자동 부여된 것 [CI-4150]
3. 감사로그(Envers)는 권한 변경을 기록하지 않음 → 고객에게 "감사로그 기록 대상이 아닙니다" 안내 [CI-4150]

→ 상세: [cookbook/permission.md](cookbook/permission.md)

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
5. 계열사 전환 시 로그인 풀림 → **인증 방식 확인**. SSO(OAuth2/SAML2/OIDC) PC웹 로그인은 workspace refresh token 미발급 → workspace access token(12h) 만료 후 계열사 전환 불가(스펙). 재로그인하면 12시간간 전환 가능. 비밀번호 로그인이면 refresh token 발급되어 7일간 유효. 코드: `flex-authentication/.../AuthorizationStrategy.kt` [CI-4166]
6. OTP 설정 확인 → `SELECT required FROM flex_auth.customer_credential_t_otp_setting WHERE customer_id = ?` [CI-4176]
7. required=1이면 → 증적 확보 후 `UPDATE required = 0` [CI-4176]
8. SSO 설정 있으면 → SSO 로그인으로 우회 가능 [CI-4176]

문의: "결제 취소 후 로그인이 안 돼요" / "체험 종료일 변경해주세요"
1. 결제 취소로 인한 접근 차단 여부 확인 [CI-4169]
2. raccoon > billing operation > `force-open` 실행하여 임시 접근 허용 [CI-4169]
3. 고객에게 로그인 → 카드 등록 안내 [CI-4169]
4. 카드 등록 완료 확인 후 `close-forced-open`으로 원복 [CI-4169]
5. 체험 종료일 직접 변경은 불가 — 0원 구독 또는 청구 시작일 조정으로 대응 [CI-4169]

문의: "OTP 때문에 로그인이 안 돼요" / "최고관리자가 OTP를 켜고 퇴사했어요"

문의: "요청 정보가 올바르지 않습니다" / "주소 변경 시 오류"
1. access log에서 traceId로 에러 코드 확인 [CI-4213]
2. `UPER_400_011`이면 → `personalEmail` RFC 5322 검증 실패
3. 해당 구성원의 `personalEmail` 값 확인 (FE 프로필 화면 또는 DB 조회)
4. `personalEmail`을 올바른 형식으로 수정하거나 비우면 해결
   - ⚠️ API는 전체 개인정보를 번들로 받아 검증하므로, 주소만 변경해도 기존 `personalEmail`이 검증 대상이 됨
   - 2024-01-19 이전에 검증 없이 입력된 레거시 데이터가 원인일 가능성

#### 조사 플로우

**F1: Billing force-open (결제 취소 접근 차단)** · 히트: 1 · [CI-4169]
> 트리거: "결제 취소 후 로그인 불가", "체험 종료일 변경", "카드 등록 불가"

```
① 결제 취소 여부 및 접근 차단 상태 확인
   고객사 Metabase 대시보드에서 구독 상태 확인
   ↓
② raccoon > billing operation > force-open 실행
   → 고객사 임시 접근 허용
   ↓
③ 고객에게 로그인 → 카드 등록 안내
   → 카드 등록 완료 확인
   ↓
④ close-forced-open 실행
   → 강제 진입 플래그 원복
   ├─ 체험 종료일 변경 요청 시 → 결제 이력 있으면 변경 불가 안내
   └─ 청구서 삭제 요청 시 → 삭제 불가 안내
```

**F2: OTP 2차인증 해제** · 히트: 1 · [CI-4176]
> 트리거: "OTP 로그인 불가", "관리자 퇴사 후 OTP 해제 요청", "2차인증 해제"

①  OTP 설정 상태 확인
   `SELECT id, customer_id, required FROM flex_auth.customer_credential_t_otp_setting WHERE customer_id = ?`
   → required=1이면 OTP 필수 상태
   ↓
② 증적 확보
   CS팀 경유 고객사 요청 확인 (서면/메시지)
   ↓
③ UPDATE 실행
   `UPDATE flex_auth.customer_credential_t_otp_setting SET required = 0 WHERE customer_id = ?`
   ├─ 쿼리 승인자 필요 (보안 규정)
   └─ 실행 후 고객 로그인 확인 요청

#### 진단 체크리스트 (코어 런북 보강)
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
3. **개인정보 보유현황 파악** → 시즈널, 대기업 컴플라이언스 목적. SQL은 cookbook/account.md 참조
4. **이메일 대량 변경** (기존 일괄 변경 보강) → `PATCH /action/v2/operation/core/customers/{customerId}/emails/change/bulk`
   - 자동화됨 (Operation API Y)

#### 진단 체크리스트 (OpenSearch sync / 조직도 통계)
문의: "검색에서 구성원이 안 나와요" / "조직도 월별 통계 오류"
1. **OpenSearch sync 깨진 경우 보정** → Operation API로 대응
   - produce type: `USER` → `userIds`만, `CUSTOMER` → `customerId` (null이면 `customerIdRange`), `ALL` → 전체 싱크
   - `deletedUsersOnly: true` → 삭제된 유저만 필터링 sync
   - ⚠️ 구성원 삭제 → 퇴직 정보 삭제 과정에서 `user data changed` 이벤트 발행으로 다시 생성될 수 있음
2. **조직도 월별 통계 오류** (`Key XXX is missing in the map`) → 삭제된 구성원 데이터가 ES에 남아서 발생. projection은 삭제된 구성원 포함, search는 제외 → 불일치. ES 싱크 한 번 맞추면 해결
3. **청구일 구성원 수 불일치** → 매월 5일 09:05 청구 시점 vs 이후 조회 시점 차이
   - 줄어드는 경우: 청구일 이후 퇴직일을 청구일 이전으로 설정 / 구성원 삭제
   - 늘어나는 경우: 청구일 이후 입사일을 청구일 이전으로 설정 / 입사 예정자 포함(as-is)

→ 상세: [cookbook/account.md](cookbook/account.md)

#### 진단 체크리스트 (구성원 검색 페이지네이션)
문의: "사번 정렬 시 무한 스크롤이 발생해요" / "사번 정렬 시 겸직 인원이 중복으로 보여요"
1. **확인**: 사번/오름차순 정렬 시 무한 스크롤인지 확인 (새로고침하면 복구, 다시 정렬하면 재발) [CI-4232]
2. **판별**: 해당 회사에 사번이 null인 구성원이 있는지 확인 — 사번 null 구성원이 있는 **모든 회사**에서 재현 가능 (겸직과 무관)
3. **원인**: `ValuesContinuation.print()`에서 `joinToString()`이 null을 문자열 "null"로 변환 → OpenSearch `search_after`에서 keyword 필드의 null(missing)과 "null"은 다른 정렬 위치 → 커서가 null 구간 앞으로 되돌아가며 무한 반복
4. **조치**: `ValuesContinuation`의 null 직렬화 버그 수정 PR 머지 여부 확인. 수정 전이면 버그로 안내

→ 상세: [cookbook/account.md](cookbook/account.md)

#### 진단 체크리스트 (겸직 등록)
문의: "직책 2개 설정이 안 돼요" / "같은 조직에 겸직 등록이 안 돼요"
1. 겸직 등록하려는 조직이 주조직과 **동일한지** 확인 [CI-4245]
2. **동일 조직이면** → 같은 조직 내 직책 겸직 발령은 **스펙상 불가**. 직책은 조직과 결합된 정보로 취급됨 → 고객에게 안내
3. **다른 조직이면** → 겸직 정상 동작해야 함 → 별도 조사 필요
4. 엑셀 일괄등록: 서버 측 validation에서 "겸조직이 동일 조직" 오류로 차단
5. 프로필 UI: 저장은 허용되지만 재조회 시 겸직 정보 미노출 (동작 불일치 — UX 개선 여지)

---

### 승인 (Approval)

#### 진단 체크리스트
문의: "퇴직자 승인자 교체 알림이 뜨는데 실제 건이 없어요"
1. 메타베이스 대시보드(#309)에서 `target_uid`로 승인 요청 확인 → 요청은 존재하나 대응하는 실제 휴가 사용 건이 없으면 고아 승인 요청 [CI-3951]
2. 퇴직자가 휴가 승인 정책에 여전히 포함되어 있는지 확인 → 승인 정책에서 퇴직자 제거 안내 [CI-3951]

문의: "삭제된 구성원이 승인 라인에 있어서 승인이 안 돼요" / "삭제한 사람 승인건 처리해주세요"
1. [Metabase 퇴사자 미처리 승인 대시보드](https://metabase.dp.grapeisfruit.com/dashboard/245)에서 대상 userId의 미처리 승인건 확인 [CI-4228]
2. **퇴직자 vs 삭제된 구성원 구분**: 퇴직자는 제품의 "퇴직자 승인자 교체" 기능 사용 가능. 삭제된 구성원은 퇴사 이벤트가 발행되지 않아 `approval_replacement_target`에 미등록 → 교체 불가, Operation API로 강제 승인 필요 [CI-4228] [CI-3769]
3. 고객에게 "강제 승인 처리" 동의 확인 후 `bulk-approve-for-user` API 호출:
   - `POST /api/operation/v2/approval/process/customers/{customerId}/users/{userId}/bulk-approve-for-user`
   - Body: `{ "categories": ["TIME_OFF", "WORK_RECORD"] }` (카테고리는 대상에 맞게 조정)
4. 응답의 `succeededProcesses` / `failedProcesses`로 처리 결과 확인

문의: "승인 설정/라인을 확인해주세요" / "위젯 종료 시 근무 승인이 안 돼요"
1. 승인 설정 확인: `customer_workflow_task_template` + `customer_workflow_task_template_stage`
2. 위젯 종료 시 기본 근무일은 승인 미발생이 정상 동작 (스펙)
3. 주휴일인데 휴일 근무 승인 발생 → 주휴일 설정 일시와 휴일 근무 등록 일시 간 시간차 확인

#### Operation API
- Swagger: `https://flex-raccoon.grapeisfruit.com/swagger/approval`
- category 값: `WORK_RECORD`(근무), `TIME_OFF`(휴가), `TIME_OFF_PROMOTION`(연차촉진)

#### 진단 체크리스트 (추가)
문의: "승인 완료된 문서가 진행중으로 보여요"
1. `approval_process` 테이블에서 해당 문서의 승인 상태 확인 → APPROVED인지 확인
2. `workflow_task` 테이블에서 동일 문서의 워크플로우 상태 확인 → ONGOING이면 동기화 실패
3. 대응: `/action/operation/v2/approval/sync-with-approval` Operation API 호출로 워크플로우 상태 보정
4. 보정 후 문서함에서 정상 표시 확인

문의: "누가 리마인드 알림을 보냈는지 확인해주세요" / "승인 확인 요청 알림이 갑자기 왔어요"
1. access log 조회 — `flex-app.be-access-{날짜}` 인덱스에서 `json.ipath: "remind/pending-approval"` + `json.authentication.customerId` 필터 [CI-4203]
2. 결과의 `json.authentication.email`로 발송자 특정, `json.requestBody.userIdHashes`로 대상 사용자 특정
3. 알림 수신자는 대상 사용자의 승인 프로세스에서 ONGOING 상태인 미승인 승인권자

#### 진단 체크리스트 (코어 런북 보강)
문의: "승인은 완료됐는데 데이터가 안 바뀌었어요"
1. **승인 완료 후 데이터 반영 오류** → 승인 라인 모든 승인 완료 후 실제 코어 데이터 변경 과정에서 오류 발생
   - 승인은 아직 ONGOING 상태로 남아있음
   - 코어 데이터는 변경되지 않은 채 남아있음
   - 대응: `cloud_event_entity`에서 문제 이벤트 ID 조회 → `/action/operation/v2/approval/re-produce-messages` Operation API로 이벤트 재발행
   - 이후 approval process 상태가 APPROVED로 변경 및 코어 데이터 변경 확인

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.

**F1: 삭제된 구성원 승인건 강제 승인** · 히트: 1 · [CI-4228] [CI-3769]
> 트리거: "삭제된 구성원이 승인 라인에 있어 승인 불가" / "삭제한 사람 승인건 처리"

```
① Metabase 대시보드(#245)에서 미처리 승인건 확인
   https://metabase.dp.grapeisfruit.com/dashboard/245 에서 userId 검색
   ↓
② 퇴직자 vs 삭제된 구성원 판별
   ├─ 퇴직자(resigned) → 제품의 "퇴직자 승인자 교체" 기능 사용
   └─ 삭제된 구성원(deleted) → 퇴사 이벤트 미발행, approval_replacement_target 미등록 → ③으로
   ↓
③ 고객에게 강제 승인 동의 확인
   ↓
④ bulk-approve-for-user API 호출
   POST /api/operation/v2/approval/process/customers/{customerId}/users/{userId}/bulk-approve-for-user
   Body: { "categories": ["TIME_OFF", "WORK_RECORD"] }
   ↓
⑤ 응답 확인
   ├─ succeededProcesses 에 대상 건 포함 → 완료
   └─ failedProcesses 에 건 포함 → 실패 원인 확인 (로그 조회)
```

**F2: 승인 리마인드 발송자 추적** · 히트: 1 · [CI-4203]
> 트리거: "누가 리마인드 보냈나요" / "승인 확인 요청 알림이 갑자기 왔어요"

```
① access log에서 remind API 호출 조회
   OpenSearch flex-app.be-access-{날짜}: json.ipath = "remind/pending-approval" + json.authentication.customerId = ?
   ↓
② 발송자 특정
   json.authentication.email → 실제 발송한 사람
   json.requestBody.userIdHashes → 리마인드 대상 사용자
   ├─ 문의자가 지목한 사람의 호출 있음 → 발송 확인
   └─ 호출 없음 → 다른 사용자가 발송한 것. 결과 목록에서 실제 발송자 안내
```

→ 상세: [cookbook/approval.md](cookbook/approval.md)

---

### 데이터 추출 (Data Export)

#### 진단 체크리스트
문의: "엑셀 다운로드가 안 돼요" / "다운로드 실패해요"
1. 근무 기록 다운로드 실패 → consumer → core-api 내부 호출 시 OkHttp 소켓 타임아웃(3초) 확인. 대규모 데이터(수백 명) 다운로드 시 타임아웃 발생 가능 [CI-4121]
2. 특정 구성원만 누락 → "근태/휴가" 도메인의 퇴사자 휴가 데이터 추출 항목 참조 [CI-3976]

→ 상세: [cookbook/data-export.md](cookbook/data-export.md)

---

### 목표 (Goal/OKR)

> 스펙 문서: [Notion 목표 리스트 API 연동 가이드](https://www.notion.so/flexnotion/API-26c0592a4a928059b6b0c1c401751d4f)

#### 진단 체크리스트
문의: "다른 연도 목표가 보여요" / "목표 필터가 안 먹혀요" / "회색 목표가 뭐예요?"
1. **cross-year 트리 구조 확인** → 사용자가 이전 연도 root 목표 하위에 올해 자식 목표를 배치했는지 확인 [CI-4126]
   - `root-objectives` API는 올해 목표의 root를 트리 탐색으로 찾으므로, root가 이전 연도면 `hit=false`로 포함
   - FE는 `hit=false` 목표를 **회색으로 구분 표시** — 이는 의도된 스펙
2. 회색 목표의 의미 → "직접 필터에 해당하지는 않지만, 하위에 해당하는 목표가 있어서 관계성을 보여주기 위해 표시"
3. `root-objectives-by-aside` API는 Matrix 기반 검색이므로 cycle 필터 정상 적용 — 이 API에서는 cross-year 문제 없음

문의: "내 목표가 안 보여요" / "목표가 너무 많아 안 나와요"
1. **User Grouped API 확인** → 내 목표/구성원 목표 탭에서 사용
   - 서버가 `companyObjectives`, `departmentObjectives`, `personalObjectives`, `memberObjectives`로 그룹핑
   - 요청자가 **대표가 아니면** `companyObjectives`는 항상 empty
   - 요청자가 **조직장이 아니면** `departmentObjectives`는 항상 empty
   - ⚠️ **최대 500건** 내부 제약 — 500건 초과 시 기획적 논의 필요
2. 구성원 목표 탭은 **동일 API를 클라이언트에서 병렬 호출**하여 화면 구성

문의: "전체 목표에서 조직 선택하면 다르게 보여요" / "조직 목표가 안 나와요"
1. **전체 탭 — 전체 옵션**: Root Objectives API (pagination 적용)
   - cycle 필수. filter 미적용 (필터 시 트리 해제)
   - 응답: `objectiveId`, `detail`(권한 없으면 null), `hasChild`, `hit`(cycle 매치 여부)
   - **detail null이거나 hit false인데 hasChild false인 경우는 없음** (하위에 볼 수 있는 목표가 있어야 포함)
2. **전체 탭 — 조직 옵션**: Aside Root Objective API (한번에 반환, pagination 없음)
   - 서버 내부에서 트리를 그려서 최상위 목표를 찾아 반환
   - ⚠️ **서버 트리 연산 최대 5,000건** 제약 — 현재 3년치 조직 목표 5,000건 초과 고객사 없으나 추후 대응 필요
   - 어사이드 적용 시 권한이 항상 있으므로 `detail`은 필수값
   - 응답: `objectiveId`, `detail`, `hasChild` (hit 필드 없음)

문의: "하위 목표가 안 펼쳐져요" / "목표 트리가 이상해요"
1. **하위 목표 탐색**: Search API + `ancestorObjectiveIds` 사용
   - 주어진 ID의 **모든 하위**를 한번에 가져옴
   - 클라이언트에서: ① 첫 뎁스 목표 하위 전체 탐색 → ② 트리 구성 → ③ 끼인 상태 목표 추가 연산
   - 설계 배경: 뎁스마다 hasChild 연산 반복 시 서버 부하 → 전체를 한번에 가져오는 방식 채택

문의: "목표 검색 결과가 다르게 나와요"
1. **검색 시 공통 동작**: 모든 탭에서 검색 적용 시 **트리 및 그룹핑 해제** → 플랫 리스트 반환
2. 검색 필터 조합:
   - 내 목표 검색: `relatedFilter.userIdHashes` + cycle
   - 전체 목표 검색 (전체): cycle만
   - 전체 목표 검색 (조직): `relatedFilter.departmentIdHashesWithDescendants` + cycle
   - 구성원 목표 검색 (사용자): `relatedFilter.userIdHashes` + cycle
   - 구성원 목표 검색 (조직): `relatedFilter.departmentIdHashes` + cycle

#### API 매핑 (탭 → API)

| 탭 | 조건 | API | 비고 |
|----|------|-----|------|
| 내 목표 | 검색 없음 | User Grouped API | 그룹핑 반환, 500건 제약 |
| 내 목표 | 검색 있음 | Search API + `relatedFilter.userIdHashes` | 플랫 리스트 |
| 전체 목표 | 전체 + 검색 없음 | Root Objectives API | pagination, hit 필드 |
| 전체 목표 | 조직 + 검색 없음 | Aside Root Objective API | 한번에 반환, 5,000건 제약 |
| 전체 목표 | 전체 + 검색 있음 | Search API + cycle | 플랫 리스트 |
| 전체 목표 | 조직 + 검색 있음 | Search API + `relatedFilter.departmentIdHashesWithDescendants` | 플랫, 하위 조직 포함 |
| 구성원 목표 | 검색 없음 | User Grouped API | 내 목표와 동일 API, 클라이언트 병렬 호출 |
| 구성원 목표 | 검색 있음 (사용자) | Search API + `relatedFilter.userIdHashes` | 플랫 리스트 |
| 구성원 목표 | 검색 있음 (조직) | Search API + `relatedFilter.departmentIdHashes` | 플랫, 해당 조직만 |
| 하위 탐색 | 펼치기 | Search API + `ancestorObjectiveIds` | 전체 하위 일괄 반환 |

#### Swagger 링크
- [User Grouped API](https://flex-gateway.dev.flexis.team/swagger-ui/index.html?urls.primaryName=goal-v3#/objective-search-v-3-api-controller/objective.search.user.grouped)
- [Root Objectives API](https://flex-gateway.dev.flexis.team/swagger-ui/index.html?urls.primaryName=goal-v3#/objective-search-v-3-api-controller/objective.root)
- [Aside Root Objective API](https://flex-gateway.dev.flexis.team/swagger-ui/index.html?urls.primaryName=goal-v3#/objective-search-v-3-api-controller/objective.root.by.aside)
- [Search API](https://flex-gateway.dev.flexis.team/swagger-ui/index.html?urls.primaryName=goal-v3#/objective-search-v-3-api-controller/objective.search)

#### 스펙: root-objectives API의 hit 필드
- BE `ObjectiveSearchServiceImpl.filterRootObjective()`에서 `hitMap` 생성:
  ```kotlin
  // cycle 조건에 맞지 않을 수 있다. Hit 여부를 어플리케이션 레벨에서 처리
  val cycleIds = cycles.toSet()
  val hitMap = objectives.associate { it.identity.id.toString() to (it.cycle in cycleIds) }
  ```
- `findRootObjectives` SQL: 서브쿼리에서 요청 cycle에 해당하는 목표를 찾고, `root_objective_id`로 root를 JOIN하되 **root에는 cycle 필터를 적용하지 않음** (설계 의도)
- FE: `hit=true` → 정상 표시, `hit=false` → 회색 표시

#### 스펙: 응답 필드 Matrix

| 필드 | Root Objectives | Aside Root Objective | User Grouped | Search |
|------|----------------|---------------------|--------------|--------|
| objectiveId | 필수 | 필수 | 그룹별 리스트 | 필수 |
| detail | 권한 없으면 null | 필수 (항상 권한 있음) | 포함 | 포함 |
| hasChild | ✅ | ✅ | — | — |
| hit | ✅ (cycle 매치) | — | — | — |

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

#### 고객 안내 예시 (목표 건수 제약)
> 내 목표 탭에서 최대 500건까지 표시됩니다. 500건을 초과하는 경우 검색 기능을 활용해주세요.
> 전체 목표 > 조직 선택 시 서버 내부적으로 최대 5,000건의 목표를 처리합니다.

→ 상세: [cookbook/goal.md](cookbook/goal.md)

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

→ 상세: [cookbook/contract.md](cookbook/contract.md)

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
7. 중도정산 시 건강보험 제외 대상인데 사회보험 금액 표시 → 확정→확정해제→최신정보반영 경로를 거쳤는지 확인. 워크어라운드: 건강보험 제외→확정→확정해제→포함 변경 [CI-4174]
8. 이관 회사 중도정산 보험료(건강보험/장기요양) 불일치 → 이관 회사 여부 확인 → 맞으면 보험료 리셋(DELETE /premium → recalculate) 안내. 원인: recipient 생성 시점의 불완전한 보수총액으로 1회 계산·저장되며 이관 데이터 추가 후 자동 재계산 안 됨 — 히트: 1 (CI-4212) [CI-4212]
9. 사회보험 연말정산 기납보험료에 전년도 분할납부 합산 문의 → `HealthInsuranceSettlementReasonCode`의 `YEAR_END_REASON_CODES`에 74번(정산분할고지보험료) 포함 여부 확인 → `PaidSocialInsuranceCalculator.getYearEndTotalAmountByType()`이 귀속연도 필터 없이 전체 합산하는 버그. CI-4174 핫픽스 파생 — 버그 (수정 대기) [CI-4222]

10. 휴직자 지급항목 금액 0원 문의 → `allowance_global` 테이블에서 해당 항목의 `allowance_on_leave_rule` 확인. `DAILY_BASE`이고 `paymentRatio=0`(육아휴직 등)이면 정상 동작. 고객에게 해당 항목의 "휴직월 지급 방법"을 `FULL`(전액지급)로 변경 안내 — 히트: 1 (CI-4225) [CI-4225]

11. 외국인 고용보험 미공제 문의 → `work_income_settlement_payee`의 `residence_qualification` 확인. UNKNOWN이 아닌 외국인 체류자격이면 → `employment_insurance_qualification_history`에서 취득일 존재 여부 확인. 취득일 없음 → 사회보험 자격관리에서 고용보험 취득일 등록 안내 — 스펙 (임의가입 대상) [CI-4241]

#### 조사 플로우

**F-pay-1: 외국인 고용보험 공제 제외 — 체류자격+자격관리 확인** · 히트: 1 · [CI-4241]
> 트리거: "외국인 고용보험이 빠졌어요" / 특정 월부터 고용보험 미공제

```
① work_income_settlement_payee에서 해당 정산의 residence_qualification 확인
   ├─ UNKNOWN → 외국인 로직 미적용 (한국인 동일 처리) → 체류자격 미등록 문제
   └─ F4 등 외국인 체류자격 → ②로
   ↓
② employment_insurance_deduction_recipient의 remarks 확인
   ├─ EXCLUDED 포함 → ③으로
   └─ EXCLUDED 미포함 → 다른 원인 조사
   ↓
③ employment_insurance_qualification_history에서 취득일 조회
   ├─ 취득일 없음 → 사회보험 자격관리에서 취득일 등록 안내
   └─ 취득일 있음 + 상실일 유효 → 상실일 이후 정산이라 EXCLUDED
```

*(급여 도메인은 근태/휴가, 스케줄링과 겹치는 이슈가 많으며, 상세 진단은 해당 도메인 참조)*

→ 상세: [cookbook/payroll.md](cookbook/payroll.md)

---

### 평가 (Evaluation / Performance Management)

#### 진단 체크리스트
문의: "삭제한 평가가 다시 보여요" / "평가 리스트에 이상한 것이 있어요" / "리뷰 마이그레이션 에러"
1. API 응답에서 해당 평가의 `isDeleted` 값 확인 → `false`이면 삭제된 적 없는 DRAFT 평가. 고객에게 삭제 방법 안내 [CI-4158]
2. `isDeleted: true`인 평가가 목록에 나타나면 → 실제 버그. `draft_evaluation` 테이블에서 `deleted_at` 컬럼 확인 [CI-4158]
3. FE 배포 직후 발생한 경우 → FE에서 목록 필터링 로직이 변경되었을 가능성 확인 [CI-4158], [CI-4129]
4. 리뷰 마이그레이션 "Failed requirement." 에러 → raccoon **prod**(`flex-raccoon.grapeisfruit.com`)를 사용하고 있는지 확인. dev raccoon에 prod 해시를 쓰면 Hashids salt 불일치로 `INVALID_NUMBER` 반환 → `require(reviewSetId > 0L)` 실패 [QNA-1936]

문의: "삭제된 평가 복구해주세요"
1. `flex_review.evaluation` 테이블에서 해당 회사의 `deleted_at IS NOT NULL` 레코드 조회 — 삭제된 평가 목록과 삭제 시점 확인 [CI-4195]
2. 고객에게 삭제 시점과 대상 평가명 확인. 여러 건이면 평가 상태(`BEFORE_START` vs 진행 중)와 `deleted_at` 시점으로 대상 특정 [CI-4195]
3. Operation API PR #5181 머지 여부 확인
   - 머지됨 → Operation API로 복구
   - 미머지 → DML 실행 (`deleted_at = NULL, deleted_user_id = NULL`), 결재 필요 [CI-4195]

문의: "평가 등급 배분 완료 시 오류" / "평가 finalize 시 알 수 없는 오류"
1. Sentry/OpenSearch에서 `EvaluationValidationException` + `DraftEvaluationStageValidator.assertToComplete` 스택 확인 [CI-4204]
2. 해당 evaluation ID로 `draft_evaluation.grades_to_calculate` 값 확인 → 비어있으면(`[]`) 등급 산출 설정 누락 [CI-4204]
3. 고객에게 해당 평가가 기존 평가의 복제본인지 확인 — 과거 버그 수정 전 평가를 복제한 경우 잔존 데이터로 발생 [CI-4204]
4. 고객이 원하는 등급 산출 방식 확인 후 `draft_evaluation` DML 보정 [CI-4204]

문의: "뉴성과관리 전환 후 평가가 사라졌어요" / "뉴성과관리 업데이트 후 진행 중 평가가 없어요"
1. `MigrationScheduler`에 의한 의도적 삭제(스펙) 확인 — OpenSearch에서 `[migrate]` 로그 + traceId로 마이그레이션 실행 여부 추적 [CI-4210]
2. `flex_review.review_set` 테이블에서 `deleted = 1`인 리뷰셋 조회 — soft delete된 건 확인 [CI-4210]
3. 복구 필요 시 `review_set` 테이블의 `deleted = 0, deletedAt = NULL`로 복구 가능. 단, 뉴성과관리 전환 완료 상태에서 구 리뷰 복구 적절성은 담당자 확인 필요 [CI-4210]
4. `evaluation` 테이블(뉴 성과관리)은 마이그레이션에 영향받지 않음 — `evaluation` soft delete와 혼동 주의 [CI-4210]

문의: "평가지 생성 중" / "평가지가 안 보여요"
1. `evaluation_reviewer` 테이블에서 해당 reviewee-reviewer 조합의 `user_form_ids`가 `[]`인지 확인 [CI-4188]
2. 빈 배열이면 `created_at`을 일괄 생성 레코드와 비교하여 후발 추가 여부 확인 [CI-4188]
3. 후발 추가 확인 시 → raccoon Operation API `initialize-user-form` 호출하여 수동 초기화 [CI-4188]

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.

**F1: 삭제된 평가 복구** · 히트: 1 · [CI-4195]
> 트리거: "삭제된 평가 복구해주세요" — 고객이 진행 중 평가를 실수로 삭제한 경우

```
① 삭제된 평가 조회
   SELECT id, name, status, deleted_at, deleted_user_id
   FROM flex_review.evaluation
   WHERE customer_id = ? AND deleted_at IS NOT NULL
   ORDER BY deleted_at DESC
   ├─ 복구 대상 특정 가능 → ②로
   └─ 여러 건 → 고객에게 평가명/삭제 시점 확인하여 대상 특정
   ↓
② Operation API 사용 가능 여부 확인 (PR #5181)
   ├─ 머지됨 → Operation API로 복구
   └─ 미머지 → ③으로
   ↓
③ DML로 soft delete 복구 (결재 필요)
   UPDATE flex_review.evaluation
   SET deleted_at = NULL, deleted_user_id = NULL
   WHERE id = ?
   → 고객에게 복구 확인 요청
```

**F3: 평가 등급 배분 완료 시 validation 오류** · 히트: 1 · [CI-4204]
> 트리거: "등급 배분 완료 시 알 수 없는 오류", "EvaluationValidationException at assertToComplete" — 과거 버그 데이터가 평가 복제로 전파된 경우

```
① Sentry/OpenSearch에서 스택트레이스 확인
   DraftEvaluationStageValidator.assertToComplete → EvaluationValidationException
   → evaluation ID 확보
   ↓
② draft_evaluation 테이블에서 등급 설정 확인
   SELECT id, grades_to_calculate, factor_grade_calculations
   FROM flex_review.draft_evaluation WHERE id = ?
   ├─ grades_to_calculate = '[]' (비어있음) → ③으로
   └─ 값이 있음 → 다른 validation 항목 조사 필요
   ↓
③ 고객에게 원하는 등급 산출 방식 확인
   "하향평가에서 커스텀 평가 요소 등급 산출을 원하시나요?"
   → 확인 후 DML 보정 (적용 + 백업 쿼리)
```

**F4: 뉴성과관리 전환 후 구 리뷰 사라짐** · 히트: 1 · [CI-4210]
> 트리거: "뉴성과관리 업데이트 후 진행 중 평가가 사라졌어요" — 마이그레이션 예약 실행 후 구 리뷰셋 삭제

```
① OpenSearch에서 마이그레이션 실행 로그 확인
   키워드: "[migrate]" + customerId
   → traceId 확보, "review sets sessions.size N" 로그로 삭제 건수 확인
   ├─ 삭제 로그 있음 → ②로 (MigrationScheduler 의도적 삭제 — 스펙)
   └─ 삭제 로그 없음 → 다른 원인 조사
   ↓
② review_set 테이블에서 soft delete 건 확인
   SELECT id, title, progressStatus, deletedAt
   FROM flex_review.review_set
   WHERE customerId = ? AND deleted = 1
   ORDER BY deletedAt DESC
   → 삭제된 리뷰셋 목록과 삭제 시점 확인
   ↓
③ 복구 적절성 판단
   뉴성과관리 전환 완료 상태에서 구 리뷰 복구가 의미 있는지 담당자 확인
   ├─ 복구 진행 → ④로
   └─ 복구 불필요 → 고객에게 스펙 안내 (마이그레이션 시 진행 중 리뷰 삭제는 의도된 동작)
   ↓
④ review_set soft delete 복구 (결재 필요)
   UPDATE flex_review.review_set
   SET deleted = 0, deletedAt = NULL
   WHERE id = ?
```

**F2: 후발 추가 reviewer UserForm 미초기화** · 히트: 1 · [CI-4188]
> 트리거: "특정 구성원 평가지가 생성 중", "평가지가 안 보여요" — finalize 이후 추가된 reviewer에서 발생

```
① evaluation_reviewer 테이블에서 user_form_ids 확인
   SELECT id, reviewee, reviewer, user_form_ids, created_at
   FROM evaluation_reviewer WHERE customer_id = ? AND evaluation_id = ? AND user_form_ids = '[]'
   ├─ 빈 배열 레코드 있음 → ②로
   └─ 모든 레코드에 form_ids 존재 → 다른 원인 조사 (API 응답, FE 필터링 등)
   ↓
② 후발 추가 여부 판별
   동일 evaluation의 다른 레코드 created_at과 비교
   ├─ 유의미한 시간차 (수시간~수일) → 후발 추가 확정, ③으로
   └─ 비슷한 시간대 → 일괄 생성 시 누락, 추가 조사 필요
   ↓
③ raccoon Operation API initialize-user-form 호출
   → form_user_form 생성 확인 → user_form_ids 채워짐 → 해결
```

→ 상세: [cookbook/review.md](cookbook/review.md)

#### 데이터 접근
```sql
-- 삭제된 평가 조회
SELECT id, name, status, deleted_at, deleted_user_id
FROM flex_review.evaluation
WHERE customer_id = ? AND deleted_at IS NOT NULL
ORDER BY deleted_at DESC;

-- 삭제된 평가 복구 (결재 필요)
UPDATE flex_review.evaluation
SET deleted_at = NULL, deleted_user_id = NULL
WHERE id = ?;

-- 복구 롤백
-- UPDATE flex_review.evaluation
-- SET deleted_at = '{원래_deleted_at}', deleted_user_id = {원래_deleted_user_id}
-- WHERE id = ?;
```

```sql
-- 등급 산출 설정 확인
SELECT id, grades_to_calculate, factor_grade_calculations
FROM flex_review.draft_evaluation
WHERE id = ?;

-- 등급 산출 설정 보정 (고객 확인 후 적용, 결재 필요)
UPDATE flex_review.draft_evaluation SET
  grades_to_calculate = '["FACTOR_GRADE"]',
  factor_grade_calculations = '[{"calculation": "WEIGHTED", "evaluationFactorType": "CUSTOM"}]'
WHERE id = ?;
```

```sql
-- 뉴성과관리 마이그레이션으로 삭제된 리뷰셋 조회
SELECT id, title, progressStatus, deletedAt
FROM flex_review.review_set
WHERE customerId = ? AND deleted = 1
ORDER BY deletedAt DESC;

-- 리뷰셋 soft delete 복구 (결재 필요)
UPDATE flex_review.review_set
SET deleted = 0, deletedAt = NULL
WHERE id = ?;
```

```sql
-- 평가지 미생성 reviewer 조회
SELECT id, reviewee, reviewer, step_type, user_form_ids, writing_requested_at, created_at
FROM evaluation_reviewer
WHERE customer_id = ? AND evaluation_id = ?
ORDER BY created_at;

-- form 생성 확인
SELECT id, created_at FROM form_user_form
WHERE id IN (?);
```

#### 과거 사례
- **삭제한 평가가 다시 노출**: 실제로는 삭제된 적 없는 title=null DRAFT 평가가 FE 핫픽스로 정상 노출된 것. 고객이 "이전에 안 보이던 것이 보임"을 "삭제 복원"으로 오해 — **스펙** [CI-4158]
- **평가 공동편집자 아닌데 메뉴 노출**: title=null인 DRAFT 평가를 FE에서 필터링하여 노출 문제 — **버그 (FE)** [CI-4129]
<!-- TODO: 시나리오 테스트 추가 권장 — title=null DRAFT 평가 리스트 정상 노출 검증 -->
- **리뷰 마이그레이션 "Failed requirement." 에러**: dev raccoon에서 prod 해시 사용 → Hashids salt 불일치로 디코딩 실패(`INVALID_NUMBER`). prod raccoon에서 재시도하면 구체적 에러 정상 출력 — **운영 오류** [QNA-1936]
- **후발 추가 reviewer 평가지 미생성**: finalize 이후 추가된 reviewer의 UserForm이 메시지 큐 실패로 초기화 안 됨. admin 화면에서 "생성 중" 표시. Operation API `initialize-user-form`으로 수동 해결 — **운영 대응** [CI-4188]
- **삭제된 진행 중 평가 복구**: 고객 관리자가 다른 평가를 삭제하려다 진행 중 평가까지 삭제. `evaluation` 테이블 soft delete(`deleted_at`, `deleted_user_id`) NULL 복구 DML로 해결. Operation API PR #5181 머지 후 API 복구 가능 — **운영 대응** [CI-4195]
- **평가 등급 배분 완료 시 validation 오류**: 과거 버그 수정 전 평가를 복제하여 `grades_to_calculate`가 비어있는 상태로 전파. `draft_evaluation` DML 보정으로 해결 — **운영 대응** [CI-4204]
- **뉴성과관리 전환 후 진행 중 평가 사라짐**: `MigrationScheduler`가 구 리뷰 → 뉴 성과관리 전환 시 진행 중 리뷰셋을 의도적으로 soft delete. `review_set` 테이블 `deleted=0, deletedAt=NULL` 복구 가능 — **스펙** [CI-4210]

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

→ 상세: [cookbook/recruiting.md](cookbook/recruiting.md)

---

### 조직 관리 (Department)

> 출처: [코어 온콜 런북](https://www.notion.so/19d0592a4a928051956ec7773e47ef2d) — Core Squad

#### 진단 체크리스트
문의: "조직 삭제해주세요" / "조직 변경 예약을 취소할 수 없어요" / "조직 시계열 데이터 뽑아주세요" / "조직 종료일 변경 시 오류" / "종료된 조직에 조직코드 넣어주세요" / "구성원이 없는데 조직 종료가 안 돼요"
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
   - **해결**: SQL로 조직 종료일 임시 제거 → 발령 취소 → 종료일 복구 (상세 SQL은 cookbook/department.md 참조)
4. **조직 종료일 변경 시 오류** → 구성원 목록 필터에서 퇴직 상태 제외가 기본이므로 "아무도 없다"고 착각하는 경우 많음. 퇴직자 포함 여부 확인 + 400 응답 body 확인
   - 간혹 발령 처리가 안 되는 경우 → 조직 종료일을 수동으로 먼저 조정 → 발령 처리 → 종료일 다시 조정
5. **조직 시계열 데이터 조회** → metabase로 전환됨. [Metabase #5082](https://metabase.dp.grapeisfruit.com/question/5082?customerId=44879) 링크로 안내
6. **종료된 조직 코드 일괄 마이그레이션** → 엑셀을 받아서 이름으로 ID를 찾고 DML 수행. 팁: 시작일/이름 정렬 후 이름을 긁어서 쿼리하면 편함
7. **"구성원이 없는데 조직 종료 안 됨" + DEPA_400_017** → 예약발령이 잔존하여 validator가 차단하는 스펙. 구성원이 모두 이동 완료되어도 예약발령 실행 전이면 차단됨 → 발령 실행 후 종료 처리 안내 (옵션 A), 급하면 발령 취소→종료→재발령 (옵션 B) [CI-4201]

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

→ 상세: [cookbook/department.md](cookbook/department.md)

---

### 인사발령 (Personnel Appointment)

> 출처: [코어 온콜 런북](https://www.notion.so/19d0592a4a928051956ec7773e47ef2d) — Core Squad

#### 진단 체크리스트
문의: "인사발령 엑셀 데이터 뽑아주세요" / "특정 시점의 조직 정보 추출해주세요"
1. **인사발령 엑셀 데이터 요청** → 반드시 워크플로우(`고객사의 개인정보 접근 및 처리를 위한 검토 및 승인 요청`) 먼저 작성. 고객사 사전 동의 첨부 권장
   - Operation API: `POST /action/operation/v2/core/personnel-appointment/customers/{customerId}/export/excel`
   - 전체 요청 시 body 없이 요청
   - 타임아웃 발생 시 → user id 기준으로 적절히 나눠서 여러 번 호출 후 엑셀 병합
2. **특정 시점 조직 추출** → `user_position_time_series_segment` + `department` JOIN으로 `union all` 쿼리 구성 (상세 SQL은 cookbook/personnel-appointment.md 참조)

→ 상세: [cookbook/personnel-appointment.md](cookbook/personnel-appointment.md)

---

### 체크리스트/온보딩 (Checklist / Onboarding)

> 출처: [코어 온콜 런북](https://www.notion.so/19d0592a4a928051956ec7773e47ef2d) — Core Squad

#### 진단 체크리스트
문의: "체크리스트가 발송되지 않았어요"
1. **언급한 Task가 존재하지 않는 경우** → 템플릿을 변경했을 때 기존 체크리스트에 자동 적용되지 않음. 이미 생성된 체크리스트에 템플릿의 task를 추가할 수 없음 (스펙)
2. **온보딩 완료 처리 여부** → 온보딩 완료 기능으로 완료 처리된 경우 체크리스트가 발송되지 않음

→ 상세: [cookbook/checklist.md](cookbook/checklist.md)

---

### 출퇴근 (Work Clock)

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

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

**F1: 출근 불가 — 근무지 범위 확인** · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
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

→ 상세: [cookbook/work-clock.md](cookbook/work-clock.md)

---

### 근태 대시보드 (Dashboard)

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

#### 진단 체크리스트
문의: "근태 대시보드 수치가 안 맞아요" / "휴가 사용 내역이 다르게 보여요"
1. 대시보드는 OpenSearch(ES) 기반 → 원본 데이터(MySQL)와 ES 동기화 상태 확인
2. 근무 동기화: `POST /action/operation/v2/time-tracking/sync-es-work-schedule`
3. 휴가 삭제 동기화: `POST /action/operation/v2/time-tracking/time-off/time-off-uses/produce-delete`
4. ES document 직접 삭제가 필요한 경우 별도 처리 (sync가 아닌 delete)

#### 조사 플로우

**F1: 대시보드 수치 불일치 — ES 동기화 확인** · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
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

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

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
6. ⚠️ 연차는 **분(minutes) 단위**로 관리됨: 7200분=15일, 4320분=9일 (1일=480분=8시간). bucket 값 해석 시 주의

#### 조사 플로우

**F1: 잔여 연차 불일치 — 버킷 확인** · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
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

**F2: 사용일수 0일 — 겹침 확인** · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
> 트리거: "사용일수가 0일이에요"

```
① 해당일에 겹치는 항목 확인
   ├─ v2_customer_holiday → 휴일 등록 여부
   ├─ user_leave_of_absence → 휴직 기간
   ├─ v2_time_tracking_user_alternative_holiday_event → 휴일대체
   ├─ v2_customer_work_rule → 해당 요일이 주휴일/쉬는날
   └─ 위 항목 중 하나라도 해당 → 사용일수 0일은 스펙
```

→ 상세: [cookbook/annual-time-off.md](cookbook/annual-time-off.md)

---

### 맞춤휴가 (Custom Time Off)

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

#### 진단 체크리스트
문의: "맞춤휴가 잔여가 이상해요" / "휴가 합치고 싶어요" / "단위 변경하고 싶어요"
1. 부여 내역: Metabase question/2452
2. 사용/취소 내역: Metabase question/2166
3. 합쳐쓰기 조건: 서로 다른 `v2_user_custom_time_off_assign`을 코드 해석으로 묶는 것 (DB 합치기 아님). assign 속성(사용 단위 등)이 동일해야 함
4. 합치기 요청 → 회수 후 재부여 권장. DML 직접 보정은 operation API 없어 최후의 수단
5. 단위 변경 → 바꾸면 못 쓰는 휴가 발생 가능. 회수 후 재부여 또는 assign 테이블에서 변경

#### 조사 플로우

**F1: 맞춤휴가 잔여 불일치** · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
> 트리거: "맞춤휴가 잔여가 이상해요"

```
① Metabase에서 부여/사용/취소 내역 확인
   부여: question/2452 → 사용/취소: question/2166
   ↓
② 부여 총량 - 사용량 - 회수량 = 잔여 계산
   ├─ 계산 일치 → 고객 오해, 내역 설명
   └─ 계산 불일치 → assign/withdrawal 테이블 직접 조회
```

→ 상세: [cookbook/custom-time-off.md](cookbook/custom-time-off.md)

---

### 근무지 (Work Place)

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

#### 진단 체크리스트
문의: "근무지 밖에서 출근이 됐어요" / "IP 제한이 안 먹혀요" / "출근 버튼이 안 눌려요"
1. GPS 설정: `flex.workplace` 테이블에서 좌표/반경 확인
2. IP 설정: `flex_auth.customer_ip_access_control_setting` 확인
3. `/current-status` 로그만 있고 `/start/dry-run` 없으면 → 범위 바깥으로 판단된 상태
4. 관리자는 IP 제한 패스 가능 (수정 예정)
5. 클라이언트 WorkPlaceTicket V1 파싱으로 상세 정보 확인 가능

→ 상세: [cookbook/work-place.md](cookbook/work-place.md)

---

### 휴일 (Holiday)

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

#### 진단 체크리스트
문의: "휴일이 안 보여요" / "대체휴일이 적용 안 돼요" / "근로자의날 삭제해주세요"
1. 유저-휴일 매핑: `v2_user_holiday_group_mapping` → `v2_customer_holiday_group` → `v2_customer_holiday`
2. 대체휴일: `v2_customer_holiday`의 `support_alternative`, `supports_saturday_alternative` 확인
3. 휴일대체 범위(gap): `flex-timetracking-config` repo의 `experimental.json`
4. 휴일대체 Metabase: question/5062
5. 근로자의날 삭제 → operation API로 제거 (PR #7421 참조)
6. 특정 유저의 휴일 조회 → operation API 사용

#### 조사 플로우

**F1: 휴일 미표시 — 매핑 확인** · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
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

→ 상세: [cookbook/holiday.md](cookbook/holiday.md)

---

### 캘린더 연동 (Calendar Integration)

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

#### 진단 체크리스트
문의: "구글 캘린더에 휴가가 안 떠요" / "캘린더 연동이 안 돼요"
1. 연동 파이프라인: TT → 플렉스 캘린더 → 구글 캘린더
2. `FlexCalendarEventAdapter`가 토픽에 발행 → `FlexCalendarSyncEventConsumer`가 컨슘 <!-- corrected via CI-4235 investigation: GoogleCalendarEventAdapter → FlexCalendarEventAdapter -->
3. 구캘 등록 조건:
   - 근무: 근무 정책별 상이
   - 휴가: 승인 완료 후 구캘 등록, 취소 승인 완료 후 구캘 삭제
4. 동기화 안 됐을 경우 담당: `@ug-team-service-platform-on-call`
5. ~~캘린더 지원 종료 예정: 2025. 7. 9~~ → 2026-03 기준 코드 활성 상태 확인됨 (CI-4235 조사) <!-- corrected via CI-4235 investigation -->
6. **미연동 건 대응**: Metabase 대시보드(`/dashboard/244?email=`)에서 미연동 건 확인 → raccoon Operation API로 재동기화 (batch 5건, 2초 delay) [SP팀 가이드](https://www.notion.so/04010959f43d486aaabe63a144a68339)

#### 조사 플로우

**F1: 구글 캘린더 동기화 실패** · 히트: 1 · [CI-4235] · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c) · [SP팀 가이드](https://www.notion.so/04010959f43d486aaabe63a144a68339)
> 트리거: "구글 캘린더에 휴가가 안 떠요" / "미연동 일정 재연동 요청"

```
① 승인 상태 확인
   ├─ 미승인 → 승인 완료 후 동기화되는 스펙
   └─ 승인 완료 → ②로
   ↓
② Metabase 대시보드에서 미연동 건 확인
   /dashboard/244?email={사용자이메일}
   → 하단 "개발자를 위한 미연동 건 걸러보기"에서 calendar event ID 추출
   ├─ 미연동 건 있음 → ③으로
   └─ 미연동 건 없음 → flex_calendar_event_map 테이블 확인 (Kafka produce 실패 가능성)
   ↓
③ raccoon Operation API로 재동기화
   엔드포인트: /proxy/calendar/api/operation/v2/calendar/customers/{customerId}/google-calendar-events/sync-created-member-schedule-group-calendar-by-ids
   Metabase 쿼리 7387로 eventIds 추출 → batch 5건 + 2초 delay
   ⚠️ 24년 10월 이전 데이터는 중복 생성 우려로 비권장
```

→ 상세: [cookbook/calendar.md](cookbook/calendar.md)

---

### Kafka 메시지 재발행

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

#### 진단 체크리스트
1. 에러 메시지에서 `<topic>@<offset>` 값으로 offset 확인
2. kafka-ui에서 해당 offset의 메시지를 찾아 `ce_id` (cloud_event) 확인
3. `ce_id` 또는 `consume_log`로 operation API 호출하여 재발행
4. `cloud_event_entity`: 프로듀싱 때 쌓임. 프로듀싱 실패 시 `produced_at`이 안 쌓임
5. `message_consume_log`: ce_id 단위로 insert. 실패 시 백오프 후 마지막까지 실패하면 에러 로그 찍고 commit

#### 조사 플로우

**F1: Kafka 컨슘 실패 — 메시지 재발행** · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
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

**F2: 사용자 변경 이벤트 컨슘 실패** · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
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

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

#### 진단 체크리스트
문의: "근무 기록 삭제해주세요" / "삭제한 데이터 복구해주세요" / "휴가 기록 삭제해주세요"

**원칙: DB 직접 수정은 하지 않음. 고객이 직접 처리하도록 안내**

#### 조사 플로우

**F1: 근무/휴가 기록 삭제 요청 대응** · 히트: 1 · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c), [CI-4239]
> 트리거: "근무 기록 삭제해주세요" / "휴가 기록 삭제해주세요" / "테스트 데이터 삭제하고 싶어요"

```
① 요청 유형 분류
   ├─ 근무 기록 삭제 → 고객이 직접 처리하도록 안내 (DB 직접 수정 불가)
   │  └─ 테스트 데이터 일괄 초기화 → 벌크 업로드로 빈 값 덮어씌우기 workaround 안내 [CI-4239]
   ├─ 삭제 데이터 복구 → 별도 절차 문서 참조
   ├─ 휴가 기록 삭제 → DB 직접 건드리지 않음, 고객 안내
   └─ 변경 예정 근무유형 삭제 → 제품에서 한 명씩 처리, 벌크는 operation API 필요
```

→ 상세: [cookbook/work-record.md](cookbook/work-record.md)

---

### 시스템 모니터링

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

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

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

#### 진단 체크리스트

상세 사례는 cookbook/edge-cases.md 참조

→ 상세: [cookbook/edge-cases.md](cookbook/edge-cases.md)

---

### 근로기준법 용어/제도 (Labor Law Reference)

> 출처: [Notion Tracking 도메인 지도](https://www.notion.so/flexnotion/Tracking-8b40cec73dcc4b1db1e6123569d7b9ce)
> 근태 이슈 조사 시 노동법 개념이 필요할 때 참조. flex 시스템 변수명과 대응 관계에 주의.

#### 시스템 변수 — 노동법 용어 매핑

| 시스템 변수 | 노동법 용어 | 설명 |
|------------|-----------|------|
| `agreedWorkingMinutes` | 소정근로시간 | 회사와 근무자가 약속한 근로시간. 법정근로시간 한도 내 |
| `statutoryWorkingMinutes` | 법정근로시간 | 법정 최대 소정근로시간 (성인: 일 8h/주 40h, 연소: 일 7h/주 35h) |
| `maxStatutoryTotalWorkingMinutes` | 법정최대근로시간 | 법정근로 + 최대연장 = 주 52시간 |
| `usualWorkingMinutes` | 계약근로시간 | 근로계약서상 일 근무시간 |
| `requiredWorkingMinutes` | 필수근로시간 | 소정근로시간에 휴일대체·입퇴사·휴직 반영한 실제 목표 |
| `baseAgreedDayWorkingMinutes` | 일 소정근로시간 | 해당 일의 소정근로시간 (교대근무에서 중요) |
| `exceedStatutoryWorkingMinutesSettingEnabled` | 법정근로시간 초과 허용 | 설정 시 법정 이상 근무 등록 가능 |

#### 가산율 레퍼런스

| 근로 유형 | 가산율 | 비고 |
|----------|--------|------|
| 연장근로 (일/주기) | 0.5배 | 법정근로시간 초과분 |
| 야간근로 (22시~06시) | 0.5배 | |
| 휴일근로 | 0.5배 | |
| 연장 + 야간 | 1.0배 | 합산 적용 |
| 휴일 + 일단위연장 | 1.0배 | 합산 적용 |
| 휴일 + 주기연장 | 0.5배 | 주기 연장 가산 미적용 (휴일만) |
| 휴일 + 연장 + 야간 | 1.5배 | |

#### 근로자 유형별 차이

| 유형 | 정의 | 연장근로 기준 | 연차/주휴 |
|------|------|-------------|----------|
| 통상 근로자 | 같은 업무 중 최장 주당 소정근로시간 | 법정근로시간 초과 | 정상 부여 |
| 단시간 근로자 | 통상 근로자 대비 소정근로시간 짧음 | **소정근로시간** 초과 (주의) | 비례 축소 |
| 초단시간 근로자 | 주 15시간 미만 | 소정근로시간 초과 | 퇴직금·연차·주휴 **면제** |
| 연소 근로자 | 만 18세 미만 | 일 7h/주 35h 기준 | 정상 부여 |
| 임신 근로자 | 임신 중 | 초과근로 **금지** | 출산휴가 90일 보장 |

#### 주요 제도 요약

- **보상휴가**: 초과근로 수당 대신 **가산율 포함 시간**으로 휴가 부여 (8h 연장 × 1.5 = 12h). 미사용 시 수당 지급 의무 있음. 연차촉진 대상 아님
- **휴일 대체**: 소정근로일↔휴일 속성 교환. 주휴일은 6일 이내 대체, **근로자의날 대체 불가**. 사전 24시간 통보 필수
- **포괄임금 vs 고정OT**: flex '포괄계약 근로시간 설정'은 실제 고정OT 계약 (항목별 시간 명시). 포괄임금제(근로시간 측정 곤란한 경우만 유효)와 다름
- **탄력적 근무시간제**: 평균 40시간 유지하되 시기별 법정근로시간 변동 가능. 2주 이내(최대 48h/주), 3개월 이내/초과(최대 52h/주)
- **연차 촉진**: 3종류 — 연차(소멸 6개월 전), 월차 1차(3개월 전), 월차 2차(1개월 전). 노무수령거부 의사표시 필요. flex '스마트 연차 촉진' 기능으로 자동화
- **연차휴가미사용수당**: 소멸 연차 금전 보상. 퇴직 시 입사일 기준 재정산 가능(취업규칙 단서 필요). 소멸시효 3년
- **5인 미만 사업장**: 연차 부여 의무 없음, 가산 수당 의무 없음, 주52시간제 미적용, 법정공휴일 미보장

---

### 비용관리 (Expense Management / Fins)

#### 진단 체크리스트
문의: "카드 내역이 안 들어와요" / "세금계산서 연동 요청" / "이전 데이터 연동 요청" / "증빙이 시간 정책 위반으로 나와요"
1. 연동 대상 확인 (카드사 / 국세청 / 홈택스 등) → 금융사마다 연동 가능 범위가 다름 [CI-4179]
2. 해당 데이터 소스가 연동되어 있는지 확인 → 미연동이면 고객사에서 직접 연동 필요 [CI-4179]
3. 연동 완료 상태이면 → 어드민쉘 수동 동기화로 희망 기간 데이터 동기화 가능 [CI-4179]
4. 카드 데이터 특정 기간 이전 동기화 실패 → 승인/매입 API별 조회 가능 기간이 상이. 범위 초과 시 담당 개발자에게 별도 코드 작업 요청 필요 [CI-4179]
5. **수동 증빙 시간 정책 위반 표시** → 수동 추가 증빙(ETC spending)은 `transactedTime=null`로 전달되어 RANGE 평가에서 무조건 FAIL 처리됨 — **버그**(EP팀 수정 예정). 카드 증빙은 영향 없음(transactedTime 존재). 정책 생성 시점 이전 증빙에는 위반 미발생(활성 정책 없음) [CI-4229]

#### 조사 플로우

**F1: 데이터 소급 동기화 요청 처리** · 히트: 1 · [CI-4179]
> 트리거: "이전 데이터 연동", "과거 내역 동기화", "세금계산서/카드 내역 소급 요청"

```
① 연동 대상 및 기간 확인
   고객 문의에서 대상(카드사/국세청 등) + 희망 기간 추출
   ↓
② 현재 연동 상태 확인
   해당 고객사에 대상 서비스가 연동되어 있는지 확인
   ├─ 미연동 → 고객사에서 직접 연동 후 재요청 안내
   └─ 연동 완료 → ③으로
   ↓
③ 스크래핑 수집 범위 확인
   Notion 스크래핑 대상 문서에서 해당 서비스의 수집 가능 기간 확인
   ├─ 범위 내 → ④로
   └─ 범위 외 → 수집 불가 안내
   ↓
④ 어드민쉘 수동 동기화 실행
   어드민쉘 > 파이낸스 > 고객사 통합 조회 > 금융기관 연동 상태
   > 대상 회사 > 금융사 카드 더보기 > 수동 동기화 > 기간 설정 > 시작
   결과 확인: #squad_finance_notification_critical
   ├─ 성공 → 고객에게 확인 요청
   └─ 실패 (API 기간 제한) → 담당 개발자에게 별도 코드 작업 요청
```

→ 상세: [cookbook/fins.md](cookbook/fins.md)

---

### 워크플로우 (Flow / Approval Document)

#### 진단 체크리스트
문의: "임시저장된 문서가 사라졌어요" / "작성하던 문서가 날라갔어요"
1. `workflow_task_draft` 테이블에서 해당 사용자의 draft 존재 여부 확인 [CI-4220]
2. draft가 있고 내용 초기화 → "할일 > 작성하기" 재진입에 의한 초기화 (access log에서 18:25:42 패턴 확인) [CI-4220]
3. draft가 없음 → 보관 기한 만료 또는 다른 원인 조사
4. 복구 요청 시 → draft data의 `text` 필드에서 HTML 본문 추출하여 고객 전달. DB INSERT 복구는 지양.

#### 조사 플로우

**F1: 워크플로우 임시저장 문서 소실** · 히트: 1 · [CI-4220]
> 트리거: "임시저장/작성하던 문서가 사라졌어요" + 워크플로우 기안서

```
① workflow_task_draft에서 user_id + customer_id로 draft 조회
   SQL → 레코드 존재 여부 확인
   ├─ 레코드 있음 → ②
   └─ 레코드 없음 → 보관 기한 만료 가능성, access log에서 삭제 시점 확인
   ↓
② draft data의 headline, text 필드에서 사용자 작성 내용 확인
   내용이 초기화된 상태인지 확인
   ├─ 초기화됨 → "작성하기 재진입" 원인 (access log에서 재진입 시점 확인)
   └─ 내용 존재 → 조회 문제, workflow_task 레코드 존재 여부 확인
```

#### 데이터 접근
```sql
-- 워크플로우 임시저장 문서 조회
SELECT id, customer_id, user_id, workflow_task_key, created_date, last_modified_date
FROM flex.workflow_task_draft
WHERE user_id = ? AND customer_id = ?
ORDER BY last_modified_date DESC;
```

#### 과거 사례
- **할일 작성하기 재진입 시 임시저장 초기화**: 사용자가 "할일 > 작성하기"를 다시 선택하면 기존 draft가 초기화됨 — **버그** [CI-4220]

→ 상세: [cookbook/flow.md](cookbook/flow.md)

---

### 단체보험 (Group Insurance)

#### 진단 체크리스트
문의: "보험 탭이 안 보여요" / "수동 가입했는데 보험이 안 보여요" / "보험증권 요청" / "보험금 청구 방법"

1. **보험 탭 미노출** → 가입 방법 확인: 청약 시 등록인지, 중도 가입인지, 수동 가입인지 [CI-4233]
   - 청약 시 등록 → 제품 내 확인 가능 (정상)
   - 중도 가입(기존 구성원/복직자) → Operation API로 상태 변경 필요. #tf-finance-insurance에서 fin squad에 요청
   - 수동 가입(메리츠 직접 요청) → **제품 미반영 스펙**. 고객에게 안내
2. **보험증권 요청** → flex가 계약자이므로 고객에 증권 제공 의무 없음. 협약서/약관/보장범위로 대체 안내
3. **보험금 청구 방법** → 피보험자 본인이 메리츠화재 홈페이지/앱에서 직접 청구. 미성년 자녀는 팩스/우편. 단체상해상담센터 1811-8412
4. **보험 탭 노출 조건 (백엔드)**: `hasActiveFeature(INSURANCE)` + `InsuredUserProfileOptions.profileActive` 모두 true 필요

#### 핵심 테이블
- `flex_impact.insurance` — 회사별 보험 계약 정보
- `flex_impact.insurance_insured_user` — 피보험자 목록 (user_id로 구성원 매핑)
- `flex_impact.insurance_insured_user_family_member` — 피보험자 가족 정보

#### 중도 가입 케이스 매트릭스 (Notion 운영 프로세스 v2.0)
| 케이스 | 제품 내 확인 |
|--------|-------------|
| 최초 청약 시 등록 | 가능 |
| 중도 — 신규 입사 구성원 | 가능 (제품에서 바로) |
| 중도 — 기존 구성원(미가입)/복직자 | Operation API 상태 변경 후 가능 |
| 중도 — 가족만 추가 | 불가 (메리츠 직접) |
| 수동 가입 (메리츠 직접) | 불가 — 스펙 |

> 운영 프로세스 상세: [Notion 보험 운영 프로세스 v2.0](https://www.notion.so/flexnotion/v2-0-1f80592a4a928085a50ce6d11cba662a)
> 담당: 보험 PM (남지선/윤진한), BE (송지호), 채널: #tf-finance-insurance

---

## 변경 이력

| 날짜 | 이슈 | 변경 내용 |
|------|------|----------|
| 2026-03-29 | CI-4217 | 근태/휴가: 휴일대체 취소 불가(OpenSearch sync 지연) — 체크리스트#18 + F4 플로우 + 과거 사례 추가. CANCEL+재등록 시 `NON_NULL` partial update로 구 eventId 잔존, 재동기화로 해결 |
| 2026-03-29 | CI-4229 | 비용관리: 수동 증빙 시간 정책 위반 오표시 — 체크리스트#5 + 과거 사례 추가. `transactedTime=null` → RANGE FAIL 버그, EP팀 수정 예정 |
| 2026-03-29 | CI-4094, CI-4209 | GLOSSARY: 출근 시간 불일치(`actorNow` stale), 교대근무 엑셀 스케줄 누락(WorkForm/WorkPlanTemplate 혼동) 용어 추가. code-fix이므로 COOKBOOK 스킵 |
| 2026-03-29 | CI-4236 | 알림: 메일 중복 발신(file merge 무한 재시도) — F4 플로우 추가. render→impact→file 타임아웃 → Kafka consumer 리밸런스 → 동일 merge 요청 827건 폭증 패턴 |
| 2026-03-27 | CI-4245 | 계정/구성원: 겸직 등록 진단 체크리스트 추가 — 같은 조직 겸직 불가 스펙 확인 |
| 2026-03-27 | CI-4241 | 급여: 외국인 고용보험 공제 제외 진단 플로우(F-pay-1) 추가, 체크리스트 #11 추가 |
| 2026-03-27 | CI-4239 | 근무 기록 삭제/복구: F1 히트 +1, 테스트 데이터 벌크 업로드 빈 값 workaround 분기 추가 |
| 2026-03-26 | CI-4207 | 외부 연동: 세콤 배치 동기화 중복 START — 체크리스트#8에 코드 수정 참조 추가 (code-fix, PR #12058) |
| 2026-03-26 | CI-4221 | 스케줄링: F-sched-upload 보강 — CF origin_read_timeout(180초) 기준 추가, N+1 근본 원인 명시 |
| 2026-03-26 | CI-4221 | 스케줄링: F-sched-upload 추가 (근무기록 업로드 타임아웃) |
| 2026-03-26 | CI-4232 | 계정/구성원: 사번 정렬 무한 스크롤 — 진단 체크리스트(구성원 검색 페이지네이션) + 과거 사례 추가. code-fix이므로 조사 플로우 스킵 |
| 2026-03-26 | CI-4233 | 단체보험(Group Insurance) 도메인 신규 추가 — 진단 체크리스트, 중도 가입 케이스 매트릭스, 핵심 테이블, Notion 운영 프로세스 링크 |
| 2026-03-26 | CI-4220 | 워크플로우: 임시저장 문서 소실 — 진단 체크리스트 + 플로우(F1) + SQL 템플릿 + 과거 사례 추가 (버그) |
| 2026-03-26 | CI-4225 | 급여: 휴직자 지급항목 0원 — 체크리스트#10 추가, SQL 템플릿(휴직규칙/payee) 추가, GLOSSARY 보육수당/휴직자수당 매핑 추가 |
| 2026-03-26 | CI-4222 | 급여: 사회보험 연말정산 기납보험료에 전년도 74번 분할납부 합산 버그 — 체크리스트#9 추가, GLOSSARY 분할납부/기납보험료 매핑 추가 |
| 2026-03-25 | CI-4216 | 급여: 정산 중 지급항목 이벤트 이중 발행 고아 레코드 — 과거 사례 + SQL 템플릿(고아 매핑 탐지) + glossary(g:pay-07) 추가. code-fix이므로 진단 플로우 스킵 |
| 2026-03-25 | CI-4163 | 계정/구성원: 일괄 이메일 변경 히트 +1 (원텍 256건, CI-4124/CI-4200과 동일 패턴) |
| 2026-03-25 | CI-4210 | 평가: 뉴성과관리 전환 후 구 리뷰 사라짐 — 진단 체크리스트 + 플로우(F4) + SQL 템플릿(review_set 조회/복구) + 과거 사례 추가 (스펙) |
| 2026-03-25 | CI-4213 | 계정/구성원: personalEmail RFC 5322 검증 실패 진단 체크리스트 추가 (UPER_400_011, 레거시 데이터 원인) |
| 2026-03-24 | 전체 | COOKBOOK.md를 Tier-1/Tier-2로 분리 — 과거 사례·SQL 템플릿을 cookbook/ 디렉토리로 이동, 진단 체크리스트·조사 플로우·레퍼런스는 유지 |
| 2026-03-24 | CI-4193 | 승인: 경력/학력 변경 댓글 누락 — 과거 사례 추가 (FE 버그, code-fix이므로 플로우 스킵) |
| 2026-03-24 | CI-4142 | 알림: 메일 미수신 진단 체크리스트#7.4 — admin-shell 이메일 발송 로그 조회 도구 반영 |
| 2026-03-24 | CI-4203 | 승인: 리마인드 발송자 추적 — 체크리스트 + F1 플로우 + 과거 사례 추가 (스펙) |
| 2026-03-24 | CI-4201 | 조직 관리: 예약발령 잔존으로 조직 종료 불가 — 체크리스트#7 + 과거 사례 추가 (스펙) |
| 2026-03-24 | CI-4204 | 평가: 등급 배분 완료 시 validation 오류 — 진단 체크리스트 + 플로우(F3) + SQL 템플릿 + 과거 사례 추가 |
| 2026-03-24 | CI-4179 | 비용관리: 어드민쉘 수동 동기화 절차 + 카드 API 기간 제약 보강, 과거 사례 갱신 |
| 2026-03-24 | CI-4199 | 근태/휴가: 휴일대체 기간 커스텀 — 체크리스트#2 히트 +1, 과거 사례에 CI-4199 추가 |
| 2026-03-24 | CI-4202 | 외부 연동: 캡스 테이블 매핑 설정 오류 — 진단 체크리스트 #10 + 과거 사례 추가 |
| 2026-03-24 | CI-4200 | 계정/구성원: 일괄 이메일 변경 과거 사례에 CI-4200 히트 추가 (주식회사 이도, 문의성 — CI-4124와 동일 패턴) |
| 2026-03-24 | CI-4195 | 평가: 삭제된 평가 복구 — 진단 체크리스트 + 플로우(F1) + SQL 템플릿(조회/복구/롤백) + 과거 사례 추가 |
| 2026-03-25 | CI-4212 | 급여: 이관 회사 중도정산 보험료 불일치 — 체크리스트#8 + 과거 사례 + SQL 템플릿 추가. recipient 생성 시점 보수총액 1회 계산, 리셋 워크어라운드 |
| 2026-03-23 | CI-4188 | 평가: 후발 추가 reviewer UserForm 미초기화 — 진단 체크리스트 + 플로우(F1→F2) + SQL 템플릿 + 과거 사례 추가 |
| 2026-03-23 | CI-4190 | 외부 연동: ODBC 연결 실패(CONNECTION LIMIT 0) 체크리스트#9 + 플로우(F4) + SQL 템플릿 + 과거 사례 추가 |
| 2026-03-23 | CI-4180 | 근태/휴가: 근무유형 적용 500 오류 체크리스트#16 + 과거 사례 추가 — validateBulk .first{} 방어 처리 부재, 데이터 보정 대응 |
| 2026-03-23 | CI-4186 | 근태/휴가: 휴일대체 기간 체크리스트#2 + 과거 사례에 CI-4186 히트 추가 |
| 2026-03-23 | CI-4169 | 계정/구성원: billing force-open 진단 체크리스트·플로우(F1) 추가, 결제 취소 접근 차단 사례 추가 |
| 2026-03-23 | CI-4179 | 비용관리: 신규 도메인 섹션 추가 — 데이터 소급 동기화 플로우, 카드 부분취소 사례 |
| 2026-03-23 | CI-4174 | 급여: 중도정산 확정해제 사회보험 미리버트 — 핫픽스 완료 반영, 워크어라운드→수정완료로 갱신 |
| 2026-03-20 | CI-4174 | 급여: 중도정산 확정해제 후 사회보험 금액 미리버트 워크어라운드 추가 |
| 2026-03-20 | CI-4176 | 계정/구성원: OTP 2차인증 해제 플로우 추가 |
| 2026-03-21 | [Notion Tracking 도메인 지도](https://www.notion.so/flexnotion/Tracking-8b40cec73dcc4b1db1e6123569d7b9ce) | 근로기준법 용어/제도 레퍼런스 섹션 추가 — 시스템 변수 매핑, 가산율 테이블, 근로자 유형별 차이, 주요 제도 요약 (36개 페이지 학습) |
| 2026-03-20 | Notion 3개 소스 재학습 | 승인 도메인에 SQL 템플릿·Operation API swagger·category 값 추가, 연차 도메인에 minutes 단위 스펙 추가, GLOSSARY 승인 용어 3건 추가 |
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
| 2026-03-20 | 전체 | 목표(Goal/OKR) 대폭 확장 — Notion API 연동 가이드 학습, 탭별 API 매핑·성능 제약·응답 필드 Matrix 추가 |
| 2026-03-17 | CI-4126 | 목표(Goal/OKR) 도메인 추가 — cross-year 트리 + hit 필드 스펙, 고객 안내 가이드 |
| 2026-03-16 | 전체 | 전체 재구성 — QNA-1842(출입연동 커넥션 수) 외부 연동 섹션 추가 |
| 2026-03-16 | CI-4120 | 휴직/휴가 비대칭 — 안희종 답변 반영 (유즈케이스 기반 설계, 잔여 미차감 처리) |
| 2026-03-16 | 전체 | 전체 재구성 — 신규 도메인 2개(계정/구성원, 데이터 추출) 추가, CI-3979/CI-4048/CI-4118/CI-4119/CI-4120/CI-4121/CI-4124 반영 |
| 2026-03-15 | 전체 | 두 COOKBOOK 통합 (글로벌 + flex-timetracking-backend) → oncall repo로 이전 |
| 2026-03-13 | CI-4103 | 교대근무 진단 가이드 추가, 스펙 코드 permalink 추가, 버그 수정 이력 반영 |
| 2026-03-12 | 세콤 | 외부 연동(세콤) 프로토콜 진단 가이드 추가 |
| 2026-02-26 | CI-3976 | 근태/휴가 도메인에 퇴사자 휴가 데이터 추출 진단 항목·API 템플릿·사례 추가 |
| 2026-02-24 | CI-3949 | 근태/휴가 도메인에 휴일대체 탭 미표기 진단 패턴 2건 추가 |
| 2026-02-20 | CI-3932 | 연차촉진 도메인에 정책 변경 후 PENDING_WRITE 잔존 진단 항목 추가 |
| 2026-02-15 | 전체 | 초기 버전 — 기존 14개 노트에서 전체 추출 |
