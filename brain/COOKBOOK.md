# 운영 쿡북

> 이슈 조사 전에 이 문서를 먼저 참조하면 조사 시간을 단축할 수 있다.
> 각 항목의 상세는 출처 이슈 노트를 참조.
> SQL 템플릿과 과거 사례는 `cookbook/` 디렉토리의 도메인별 파일에 있다.

## 타입별 빠른 참조

> 이슈 접수 시 타입을 먼저 분류하면 관련 플로우를 빠르게 찾을 수 있다.
> 타입 정의: **Error**(오류/버그/장애) · **Data**(데이터 누락/불일치/조회) · **Perf**(성능/타임아웃) · **Auth**(접근 차단/권한/인증) · **Spec**(스펙 확인/운영 절차)

- **오류형 (Error)**: 알림-F3(이메일 CTA 이동 불일치), 알림-F4(메일 중복 발신), 근태-F4(휴일대체 취소 불가), 교대근무-F2(스케줄 게시 확인 필요), 외부연동-F3(세콤 출근 미반영), 외부연동-F4(ODBC 연결 실패), 전자계약-F2(일괄 다운로드 링크 미생성), 평가-F3(등급 배분 validation 오류), 평가-F2(UserForm 미초기화), 조직관리-F2(발령+조직 데드락), 캘린더-F1(구글 캘린더 동기화 실패), Kafka-F1(컨슘 실패), Kafka-F2(사용자 변경 이벤트 실패), Kafka-F3(Rebalance 무한 루프)
- **데이터형 (Data)**: 알림-F2(Core 알림 내용 확인), 근태-F1(휴일대체 탭 미표기), 근태-F2(퇴근 정시 고정), 외부연동-F1(세콤 연동 해제 추적), 외부연동-F2(수동 전송 미반영), 계정-F3(문서함 삭제 복구), 승인-F1(비활성 사용자 강제 승인), 승인-F2(리마인드 발송자 추적), 전자계약-F1(서식 삭제자 추적), 전자계약-F3(계열사 서식 복제), 평가-F1(삭제 평가 복구), 평가-F4(뉴성과관리 전환 후 리뷰 소실), 채용-F1(subdomain 변경 요청 방치), 조직관리-F1(조직 삭제 처리), 대시보드-F1(수치 불일치), 대시보드-F2(고스트 periodicWorkSchedule 미달 오표시), 연차-F1(잔여 불일치), 연차-F2(사용일수 0일), 맞춤휴가-F1(잔여 불일치), 휴일-F1(휴일 미표시), 휴일-F2(공휴일 삭제 요청), 근무기록-F1(삭제 요청 대응), 비용관리-F1(데이터 소급 동기화), 비용관리-F4(수정 팝업 영수증 건수 초과), 워크플로우-F1(임시저장 문서 소실)
- **성능형 (Perf)**: 없음
- **권한형 (Auth)**: 교대근무-F1(구성원 조회 누락), 외부연동-F5(캡스/세콤 인증 오류), 계정-F1(Billing 접근 차단), 계정-F2(OTP 2차인증 해제), 출퇴근-F1(출근 불가 근무지 범위), OpenAPI-F1(403 grant configuration)
- **렌더형 (Render)**: 연차-F4(iOS 미리쓰기 매핑 실수)
- **스펙질문형 (Spec)**: 알림-F1(수신자 역할 중복), 근태-F3(퇴근 자정 잘림), 맞춤휴가-F2(소정근로시간 변경 후 잔여 변동), 근태-IP제한+자동퇴근, 연차촉진-UTC연도경계, 외부연동-세콘쿼리오류, 인사발령-F1(Flagsmith 엑셀 발령 오픈)

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

문의: "초대메일이 안 와요" / "초대 이메일 재발송해도 안 받아요"
1. admin-shell 이메일 발송 로그 또는 SES 이벤트 OpenSearch(`flex-prod-ses-feedback-*`)에서 대상 이메일의 이벤트 확인
2. **Bounce 이벤트** 확인 → 유효하지 않은 이메일로 발송 시 즉시 suppress list 등록
3. suppress list에 등록된 이메일은 직접 제거 불가 → CS팀을 통해 수동 초대메일 발송 유도
4. **Send만 찍히고 Delivery 없음** → 수신 메일 서버 문제. [MX record 확인](https://mxtoolbox.com/)으로 수신 서버 존재 여부 검증

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.
> 여러 플로우가 후보이면 병렬로 실행하여 히트 여부를 빠르게 판별.

**F1: 알림 미수신 — 수신자 역할 중복 확인** · 타입: Spec · 히트: 1 · [CI-3910]
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

**F2: 알림 내용 확인 불가 — Core 알림 구조** · 타입: Data · 히트: 1 · [CI-4122]
> 트리거: "메타베이스에서 알림 내용이 안 보여요" / title_meta_map이 `[]`

```
① notification_topic의 topic_type 확인
   ├─ Core 알림(FLEX_USER_DATA_CHANGE 등) → title_meta_map 빈값은 정상 (제목 고정)
   └─ TT 알림 → title_meta_map에 값이 있어야 정상, 없으면 버그
   ↓
② Core 알림이면 notification.message_data_map 조회
   실제 내용(changedDataName 등)은 이 필드에 저장
```

**F3: 이메일 CTA 이동 대상 불일치** · 타입: Error · 히트: 1 · [CI-3914]
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

**F4: 메일 중복 발신 — file merge 무한 재시도** · 타입: Error · 히트: 1 · [CI-4236]
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
6. **연차촉진 연도 경계 누락 (UTC/KST)** → 고객이 특정 연도(예: 2026년)로 조회 시 촉진이 안 보이는 경우: 배치가 오전 8시(KST) 동작하여 `boosted_at`이 UTC 기준 전년도 12/31 23:xx로 저장됨 → 연도 단위 쿼리에서 누락. "이전 연도로 조회하면 확인 가능"으로 안내. 월차 촉진도 동일 패턴 [CI-3809] [CI-3907]
7. **대표이사 연차촉진 결과 없음** → 등기임원이면 연차 지급 대상 아님 → 촉진 조회 결과 없음이 정상. 정책 변경 이전 생성된 이력은 당시 연차량으로 남아있을 수 있음 [CI-3932]
8. **연차촉진 관리자 작성 기간 필터** → 완료된 촉진이 있으면 "관리자 작성 기간 필터"가 작동하여 PENDING_WRITE 상태 촉진이 목록에서 누락될 수 있음 — 스펙 (버그 아님). 관리자가 직접 해당 구성원에게 안내 후 종결 [CI-3777]

→ 상세: [cookbook/annual-promotion.md](cookbook/annual-promotion.md)

---

### 근태/휴가 (Time Tracking)

→ 도메인 이해: [cookbook/time-tracking.md#도메인-컨텍스트](cookbook/time-tracking.md#도메인-컨텍스트)

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
18. **"실시간 기록을 사용할 수 없어요" (WORKCLOCK_400_005)** → 아래 순서로 조사
   1. access log에서 실제 에러 시각·API path 확인 (`json.responseStatus >= 400`, `json.authentication.userId`)
   2. `v2_user_work_rule` WHERE user_id={id} ORDER BY event_time_stamp — 에러 시점에 적용된 근무유형 특정 (date_from/apply_time_stamp_from 기준)
   3. 특정된 `customer_work_rule_id` → `v2_customer_work_rule.customer_work_record_rule_id` → `v2_customer_work_record_rule.real_time_record_enabled` 확인
   4. **핵심**: 실시간 기록 가능 여부는 **대상 날짜의 근무스케줄**에 적용된 근무유형으로 결정됨. 전일 근무 종료 시 전일 날짜 기준 규칙이 적용됨
   5. 근무유형 재배정 시 두 규칙이 순차 등록되며 `apply_from`이 다를 수 있음 — 날짜별로 다른 규칙 적용 주의 [CI-4278]
19. **휴일대체 취소 불가** ("대체 휴일을 찾을 수 없습니다") → 휴일대체 수정(CANCEL+재등록) 후 OpenSearch sync 지연으로 FE에 구 eventId가 전달되는 케이스. access log에서 `search/by-departments` 응답의 `alteredHoliday.eventId` 확인 → DB(`v2_time_tracking_user_alternative_holiday_event`)의 유효 이벤트 ID와 비교 → 불일치 시 `/sync-os-work-schedule-advanced`로 재동기화 [CI-4217]
19. **근무유형 변경 예약 취소 불가** ("근무 유형을 취소할 수 없어요" / WORKRULE_400_005) → `UserWorkRuleAllowCancelMappingCalculator` 조건3이 `distributePeriodOverToDay`만 확인하고 `applyStartDateForDistributePeriodOver`를 미고려 → 실질 주기연장일귀속을 false로 오판. PR flex-timetracking-backend#12027 — **버그** [CI-4148]
20. **근무유형 적용일 `1970-01-01` = 입사일** → 적용일이 `1970-01-01`로 표시되는 경우 "입사일부터 적용"을 의미하는 특수값. PR#8593 이후 `dateFrom` 기준 입사일만 보도록 변경. 그룹 입사일 기준 근무 조회는 지원하지 않음(스펙) [CI-3773] [CI-3902]
21. **IP 제한 + 자동퇴근** → 자동퇴근(예약 퇴근) 시에는 근무지/IP 체크 없이 근무지 안에서 퇴근한 것으로 판단 — 스펙 (`UserWorkClockStopByReserveRequestServiceImpl.kt#L142-L143`). IP 제한이 있어도 자동퇴근은 통과 [CI-3501]
22. **교대근무 스케줄 게시 시 기존 휴가 있는 날 오류** → draft의 `time_off_deletion` 필드에 이미 편집 불가능한 날의 연차 삭제가 포함된 경우 오류 발생. 해당 구성원 draft의 `time_off_deletion = '[]'`로 UPDATE 후 재게시 [CI-3997]
23. **external_provider_event 재처리** → 세콤 등 외부 이벤트 재전송 시 이미 처리된 이벤트는 중복으로 skip. 재처리가 필요하면 `external_provider_event` 테이블에서 해당 이벤트 상태 변경 필요 [CI-3793] [CI-3861]
24. **휴가 코드 삭제 시 등록된 휴가 취소** → 교대근무 관리에서 기사용 휴가 코드를 삭제하면 등록된 휴가가 모두 취소됨 — 의도된 스펙 [CI-4047]
25. **연차 조정 일괄 취소** → side peek의 `...` 아이콘에서 일괄 취소 가능 (개별 취소만 가능하다는 오해 多) [CI-3923]
26. **dry-run WARN vs ERROR** → 스케줄 게시 전 dry-run 응답: `ERROR`는 게시 차단, `WARN`은 게시 허용. FE 파서 버그로 WARN이 ERROR로 처리되어 게시 차단된 사례 있음(PR: flex-frontend-apps-time-tracking/pull/2101 hotfix 완료) [CI-3862]
27. **휴가 취소 후 사용 내역 상태가 "승인완료"로 유지** → DB에서 CANCEL 이벤트 존재 여부 먼저 확인 [CI-4337]
    - `v2_user_time_off_event`에서 CANCEL 이벤트(reference_time_off_event_id로 REGISTER와 연결)가 정상 저장되어 있으면 취소 자체는 완료된 것
    - "휴가 사용 내역" UI 상태는 Event Sourcing 기반 — `UserTimeOffUseLookUpMappingService`가 CANCEL 이벤트 존재 여부와 approval 레코드 상태를 결합하여 표시 상태 결정
    - ⚠️ 근본 원인 미확정(조사 중): H1 CANCEL 이벤트 누락 감지 문제, H2 approval 레코드 상태 불일치, H3 직접 취소 시 cancelApproval() 별도 트랜잭션 문제
    - 엑셀 다운로드에서도 동일 상태 표시이면 API 응답 레벨 문제. `v2_user_time_off_use`는 취소 시 물리 삭제되므로 0건이면 실제 계산 영향 없음

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.
> 여러 플로우가 후보이면 병렬로 실행하여 히트 여부를 빠르게 판별.

**F1: 휴일대체 탭 미표기** · 타입: Data · 히트: 1 · [CI-3949]
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

**F2: 세콤/캡스/텔레캅 퇴근이 정시로 고정** · 타입: Data · 히트: 1 · [CI-4145]
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

**F3: 퇴근 시간이 자정(00:00)으로 잘림** · 타입: Spec · 히트: 1 · [CI-3979]
> 트리거: "퇴근 시간이 잘렸어요" / "퇴근이 00:00으로 찍혀요"

```
① 대상 구성원의 다음날 휴가 등록 여부 확인
   ├─ 다음날 종일휴가 있음 → 휴가 시작 시간(00:00)으로 조정되는 스펙
   └─ 휴가 없음 → 다른 원인, F2(정시 고정) 또는 별도 조사
```

**F4: 휴일대체 취소 불가 — OpenSearch sync 지연** · 타입: Error · 히트: 1 · [CI-4217]
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

> 트리거: "근무 기록 업로드 오류", "업로드 시 에러", "벌크 업로드 실패", "업로드 후 근무정보 안 보임"
> 히트: 1 (CI-4221) / 참조: 1 (CI-4251)

1. **신규 회사 여부 확인** — 신규 가입 회사면 구성원별 조직설정 완료 여부 먼저 확인. 조직설정 미설정 시 업로드 성공해도 UI에 미표시 [CI-4251]
2. access log에서 `bulk-upload` 요청의 `responseStatus` + `elapsedTime` 확인
   - 400 (dry-run) → 엑셀 데이터 검증 실패. 반환 엑셀의 오류 표시 확인 안내. `.xls` 포맷이면 `.xlsx`로 변환 안내 [CI-4251]
   - 200 + elapsedTime > **180초** → CloudFront origin_read_timeout 초과로 유저에게 504 표시. 서버는 정상 처리 완료. 파일 분할 안내
   - 200 + elapsedTime 60~180초 → CF 통과하지만 느림. 파일 분할 권장
   - 500 → 서버 에러. traceId로 app log 추적
3. 대량 데이터(구성원 × 날짜 많음)면 분할 업로드 안내
4. 근본 원인: N+1 순차 처리 패턴. 후속 개선은 비동기 전환 검토 중 [CI-4221]

---

### 교대근무 (Shift)

#### 진단 체크리스트
문의: "교대근무 관리 화면에서 일부 구성원만 조회됩니다" / "퇴근 자동 조정이 안 돼요" / "초단시간 근로자 연장근무가 이상해요" / "교대근무 리포트 시간이 다릅니다" / "교대근무 스케줄 게시 시 확인 필요 오류"

1. 구성원 조회 누락 → 해당 관리자의 **근무 권한**과 **휴가 권한** 범위 확인 → 전체 구성원 vs 소속 및 하위 조직 [CI-4103]
2. 두 권한 중 **범위가 좁은 쪽**이 최종 조회 범위를 결정함. 권한 범위를 맞추도록 안내
3. 교대근무 휴무일에 스케줄 근무 시 퇴근 자동 조정 실패 → `baseAgreedDayWorkingMinutes`가 휴무일에 0이 되어 일연장 조건이 null로 평가 — **버그 (수정 예정)** [CI-4119]
4. 초단시간 근로자 연장근무 계산 이상 → `baseAgreedDayWorkingMinutes`가 휴무일에 법적 소정근로시간(예: 168분)으로 사용되어 일연장이 과소 계산. 주휴일은 480분(8시간) 고정인데 휴무일만 비대칭 — **버그 추정** [CI-4048]
5. 교대근무 일별 리포트 스케줄 시간 불일치 → `DailyShiftUserWorkScheduleExportDataNightType5Converter`에서 `timeBlockGroups` 미정렬 + `associateBy` 덮어쓰기 2중 결함. 2개 이상 교대배치 시 잘못된 블록의 시간 출력 — **버그** [CI-4132]
6. 여러날 휴가 등록 구성원에 스케줄 게시 시 "확인 필요" 오류 → draft에 `timeOffDeletion` 잔존 여부 확인. `MultiDayTimeOffCancellationValidator`가 여러날 휴가 삭제를 감지하여 ERROR 반환. 해당 구성원의 draft에서 `timeOffDeletion` 제거로 해결 [CI-4268]
7. 교대근무 스케줄이 안 보인다 / 삭제된 것 같다 → `v2_customer_work_plan_template` 에서 `name + customer_id` 로 직접 조회 [CI-4351]
   - 존재하면 → 삭제 안됨. 스코프 변경으로 안 보인 것 가능성 높음. 고객에게 스코프 설정 확인 안내
   - 없으면 → 실제 삭제됨. 별도 삭제 이력 저장 없으므로 access log에서 DELETE 주체 확인
   - ⚠️ raccoon audit API(감사로그)는 이 케이스 미적용 — 계정/구성원 정보 전용

**고객 안내 예시 (구성원 누락):**
> 교대근무 관리 화면에서는 **근무 권한**과 **휴가 권한**을 **모두** 보유한 조직의 구성원만 표시됩니다.
> 전체 구성원을 조회하시려면 두 권한 모두 동일한 범위로 설정해 주세요.

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.
> 여러 플로우가 후보이면 병렬로 실행하여 히트 여부를 빠르게 판별.

**F1: 교대근무 구성원 조회 누락** · 타입: Auth · 히트: 1 · [CI-4103]
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

**F2: 교대근무 게시 시 여러날 휴가 "확인 필요" — draft timeOffDeletion 잔존** · 타입: Error · 히트: 2 · [CI-4268] [CI-3997]
> 트리거: "교대근무 스케줄 게시 시 확인 필요 오류" + 여러날 휴가 등록 구성원

```
① Access log: dry-run 응답에서 validationType 확인
   → TIME_OFF_MULTI_DAY_CANCELLATION_NOT_ALLOWED 이면 ②로
   ↓
② 해당 구성원의 draft DB에서 timeOffDeletion 확인
   UserShiftScheduleDraftEntity에서 해당 월/구성원의 timeOffDeletion 컬럼 조회
   ├─ 여러날 휴가의 eventId 잔존 → ③으로
   └─ 없음 → 다른 validator 원인 조사
   ↓
③ draft에서 timeOffDeletion 제거
   UPDATE flex.v2_user_shift_schedule_draft
   SET time_off_deletion = '[]'
   WHERE id in ({draftIds})
     and customer_id = {customerId}
     and user_id = {userId};
   → 재게시 시도
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
13. 연동 이벤트 미반영 (이벤트 지연 + 수동 START 충돌) → `v2_user_external_provider_event`에서 이벤트 수신 시각 확인 (발생 시각 vs DB 저장 시각) → 이벤트 지연이 있으면 사용자가 그 사이 수동 START 했는지 컨슈머 로그 확인 → `v2_user_work_clock_draft_event`에서 해당 이벤트 기준 start 레코드 유무 확인 [CI-4237]
14. 세콤 수동전송 시 중복 START 이벤트 → PC·모바일 표시 불일치로 나타남. `v2_user_work_clock_event`에서 해당 유저/날짜 CANCEL 대상 이벤트 탐색. 잘못된 START 이벤트를 CANCEL 처리 [CI-4246]
15. 캡스 기기 변경 후 동기화 불량 → 캡스 프로그램 근태처리옵션 계정 재설정 여부 확인. 원본선택 항목이 가이드와 다르면 캡스 버전 차이일 수 있음 (캡스 담당자에게 확인) [CI-4249]
16. **세콘 `syntax error at or near "DUPLICATE"` 오류** → 세콘 프로그램 내부 쿼리 오류 (flex 책임 아님). 세콘 프로그램 쿼리 관리 화면에서 기존 쿼리와 새 쿼리가 중복 입력된 것이 원인. 대응: "저희가 가이드하는 쿼리가 아닌 것으로 보입니다. 세콘 쿼리 관리에서 확인 필요" 안내 [CI-3953]
17. **캡스 수동 전송 중복 데이터 무시** → 캡스 수동 전송 시 이미 flex에서 처리한 START 데이터는 중복으로 무시됨 — 스펙. 재처리가 필요하면 `external_provider_event` 테이블에서 상태 변경 필요 [CI-3965]

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.
> 여러 플로우가 후보이면 병렬로 실행하여 히트 여부를 빠르게 판별.

**F1: 세콤 연동 해제/비활성화 원인 추적** · 타입: Data · 히트: 1 · [CI-3849]
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

**F2: 수동 전송 후 미반영** · 타입: Data · 히트: 1 · [CI-3861]
> 트리거: "수동 전송했는데 반영 안 돼요"

```
① 세콤 이벤트 수신 순서 확인
   Metabase #3565 → 해당 날짜 이벤트 조회
   ├─ 퇴근→출근 역순 수신 → 위젯 draft 불일치 가능
   └─ 정상 순서 → 다른 원인, 위젯 draft 이벤트(#4716) 확인
```

**F3: 세콤 출근 미반영 — 잔존 위젯 차단** · 타입: Error · 히트: 1 · [CI-4157]
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

**F4: ODBC 연결 실패 — CONNECTION LIMIT 0 차단** · 타입: Error · 히트: 1 · [CI-4190]
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

**F5: 캡스/세콤 연결 실패 — 인증 오류 vs 방화벽 구분** · 타입: Auth · 히트: 1 · [FT-12290]
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

### 외부 API (OpenAPI)

#### 진단 체크리스트
문의: "OpenAPI로 부서 조회 시 null 리턴돼요" / "OpenAPI 호출하면 403이 나요" / "특정 API만 403이고 나머지는 돼요"
1. 부서(departments) 필드 null 응답 → `department.code` 미등록 확인. SELECT code FROM department WHERE id = {고객사 customerId} — null이면 고객에게 flex 설정에서 조직 코드 등록 안내. [FAQ 문서](https://developers.flex.team/reference/faq-limitation#항목-별-사전-코드-등록-필요) [CI-4049]
2. OpenAPI 403(AUTHZ_403_000) 발생 시 → grant-configuration 확인: `grantConfigurationId` null이면 모든 action 허용, NOT null이면 명시적 허용 action만 접근 가능 — 스펙. 특정 API만 403이고 다른 API는 정상이면 grant-configuration 설정 확인. DB↔OpenFGA 동기화 이상 가능성도 확인 [CI-4270]
3. `/v2/departments/all`, `/v2/users/employee-numbers`는 access check가 없어 grant configuration에 무관하게 항상 접근 가능 (bypass 설계) [CI-4270]

→ 상세: [cookbook/integration.md](cookbook/integration.md)

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

문의: "등록한 구성원이 로그인이 안 돼요" / "초대했는데 로그인 오류가 나요" / "비밀번호를 설정 안 한 것 같아요"
1. **온보딩 미완료(인증 계정 미생성)** → 구성원 등록(초대) 후 이메일 수락 + 비밀번호 설정까지 완료해야 인증 계정이 생성됨 [CI-4280]
   - 초대 메일 수락은 했으나 비밀번호 설정 단계를 건너뛰면 로그인 불가
   - 조치: 구성원에게 초대 메일 재발송 → 비밀번호 설정 완료 안내
   - ⚠️ 구성원 등록 완료 ≠ 로그인 가능 (온보딩 완료까지 필요)
2. **겸직 주법인 변경 필요 여부** → 온보딩 완료 상태인데도 로그인 불가이면 겸직 구조 확인

문의: "OTP 때문에 로그인이 안 돼요" / "최고관리자가 OTP를 켜고 퇴사했어요"
1. OTP 설정 상태 확인: `SELECT required FROM flex_auth.customer_credential_t_otp_setting WHERE customer_id = ?`
2. **OTP 잠김 케이스**: 24시간 이내 누적 10번 OTP 입력 실패 시 잠김 → 관리자가 해당 구성원의 OTP 재설정 필요 (구성원 직접 재설정 불가)
3. **최고관리자 OTP 잠김**: Operation API 없음. 유일한 우회법은 회사의 2차인증 설정을 끄는 것 → 증적 필수 (CS팀 경유 서면/메시지 확인)
4. SSO 설정 있으면 → SSO 로그인으로 우회 가능 (OTP 확인 없음)
5. OTP 설정 해제 필요 시 → F2: OTP 2차인증 해제 플로우 참조 [CI-4176]

문의: "요청 정보가 올바르지 않습니다" / "주소 변경 시 오류"
1. access log에서 traceId로 에러 코드 확인 [CI-4213]
2. `UPER_400_011`이면 → `personalEmail` RFC 5322 검증 실패
3. 해당 구성원의 `personalEmail` 값 확인 (FE 프로필 화면 또는 DB 조회)
4. `personalEmail`을 올바른 형식으로 수정하거나 비우면 해결
   - ⚠️ API는 전체 개인정보를 번들로 받아 검증하므로, 주소만 변경해도 기존 `personalEmail`이 검증 대상이 됨
   - 2024-01-19 이전에 검증 없이 입력된 레거시 데이터가 원인일 가능성

#### 조사 플로우

**F1: Billing 접근 차단 (결제 취소 / 무료체험 종료)** · 타입: Auth · 히트: 2 · [CI-4169] [CI-4291]
> 트리거: "결제 취소 후 로그인 불가", "무료체험 종료 후 접속 불가", "구독 추가했는데 로그인 안 됨", "체험 종료일 변경", "카드 등록 불가"

```
① 라쿤 > 빠른 회사 검색 > 상세 정보에서 확인
   - 무료체험 종료일
   - 카드 등록 여부
   - 구독 상태
   ↓
② 원인 분기
   ├─ 무료체험 종료 + 카드 미등록 → ③-A
   └─ 결제 취소 / 기타 차단 → ③-B
   ↓
③-A 무료체험 종료일을 오늘 이후로 변경
   → 고객에게 로그인 → 카드 등록 안내
   → 카드 등록 완료 확인 → 결제 생성
   ⚠️ 구독 플랜만 추가해도 접속 불가 (카드 체크가 피처 체크보다 선행)
   ↓
③-B raccoon > billing operation > force-open 실행
   → 고객사 임시 접근 허용
   → 카드 등록 완료 확인
   → close-forced-open 실행
   ├─ 체험 종료일 변경 요청 시 → 결제 이력 있으면 변경 불가 안내
   └─ 청구서 삭제 요청 시 → 삭제 불가 안내
```

**F2: OTP 2차인증 해제** · 타입: Auth · 히트: 1 · [CI-4176]
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

#### 진단 체크리스트 (문서/개인정보 변경 알림)
문의: "문서변경 참조에 없는데 알림이 와요" / "개인정보 등록 알림이 가요" / "신규입사자 가입 시 다른 분들에게 알림이 가요"
1. **핵심**: 문서/개인정보 변경 알림 수신자는 "문서변경 참조" 설정이 아닌 **권한** 기반 [CI-4335]
   - 문서 변경 알림: `CORE_USER_ATTACHMENT_UPDATE` 권한 보유자 전원에게 발송
   - 개인정보 변경 알림: `CORE_USER_PERSONAL_UPDATE` 권한 보유자 전원에게 발송
   - 승인정책관리 > 구성원정보 > 문서변경 참조 설정과는 **무관**
2. 알림을 받지 않으려면 → 수신자의 해당 권한을 제거하도록 안내 (스펙이므로 버그 아님)
3. 개인정보 변경 시 추가 패턴: 대상자 본인에게도 1단계 알림 발송. 단, 권한 보유자(관리자)가 직접 수정한 경우엔 2단계 알림 스킵

#### 진단 체크리스트 (문서함/서류)
문의: "삭제한 문서함 복구 가능한가요" / "실수로 문서함을 삭제했어요"
1. **즉시 답변 가능**: 문서함 삭제는 **hard delete** — 복구 불가 [CI-4256]
2. 업로드된 서류 파일도 문서함 삭제 시 연계 삭제됨 (`UserDocumentFile` 100건씩 배치 hard delete)
3. S3 파일 자체는 삭제되지 않으나, DB 레코드가 없어 접근 불가
4. `@Audited`(Hibernate Envers)로 audit 테이블(`user_document_aud`)에 이력이 남을 수 있으나, 복구 가능 여부는 별도 확인 필요

#### 진단 체크리스트 (접속 기록/감사로그)
문의: "마지막 접속 기록 추출해주세요" / "접속 기록 데이터 제공 가능한가요"
1. **직접 제공 불가**: 마지막 접속 기록 데이터는 시스템에 저장하지 않음 [QNA-1972]
   - `user.z_last_login_at` 컬럼은 2024-10-16에 DROP됨
   - `login_history`는 로그인 시도만 기록, 이후 활동 미추적
   - access log의 유저별 마지막 시간을 저장하는 별도 테이블/로직 없음
2. **대안 안내**: 감사로그에서 최근 로그를 엑셀 다운로드 → 사용자별 피벗을 돌려 "마지막 활동 시점"을 간접 확인
3. 고객이 원하는 "접속 기록"의 정확한 정의를 먼저 파악 (마지막 로그인 vs 마지막 활동)

#### 진단 체크리스트 (감사로그 다운로드)
문의: "감사로그 다운로드 요청드립니다" / "감사로그 데이터 추출해주세요" / "장기간 감사로그가 필요합니다"
> ⚠️ **도메인 특화 삭제 이력 요청** (교대근무 스케줄 삭제 이력 등)은 이 체크리스트 아님 → 해당 도메인 DB 직접 조회 먼저. 교대근무 스케줄이면 `:shift` 체크리스트 #7 참조 [CI-4351]
1. **제품 내 기능**: 감사로그 다운로드는 **7일 기간 제한** — 장기간 요청 시 Operation API 필요 [CI-4309]
2. **법적 대응 목적**: 법적 요건으로 협조 필요 — 엔터프라이즈 유도 목적 제한이지만 거부 불가 [CI-4309]
3. **Operation API 실행**: raccoon Swagger `https://flex-raccoon.grapeisfruit.com/swagger/audit` → "audit operation" [CI-4309]
   - `POST /action/operation/v2/audit/{customerId}/download?userId={userId}`
   - `personalInformationType`: 근태_근무정보, 근태_휴가정보, 기타 등 (enum 목록은 CI-4309 노트 참조)
   - `eventCategory`: CREATE, UPDATE, DELETE
   - `from`/`to`: KST 기준 ISO 8601
4. **응답은 200만 반환** — 파일은 userId의 **이메일로 비동기 발송**. 중복 클릭 주의 [CI-4309]
5. **참고 문서**: [감사로그데이터 전달 대응 관련 Notion 문서](https://www.notion.so/flexnotion/2450592a4a928024b02eebe84fd722b6)

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

#### 진단 체크리스트 (겸직 주법인 변경)
문의: "대표회사 바꿔주세요" / "겸직 주법인 전환해주세요"
1. **대상자별 겸직 매핑 확인** — `member_user_mapping` 기반으로 **1명씩 개별 조회** (IN으로 일괄 조회 금지 — member_id 교차오염 발생) [CI-4271]
   ```sql
   SELECT customer_id, id AS user_id, email FROM flex.view_user
   WHERE id IN (SELECT user_id FROM flex.member_user_mapping
   WHERE member_id = (SELECT member_id FROM flex.member_user_mapping
   WHERE user_id = (SELECT id FROM flex.view_user WHERE email = trim('{이메일}'))));
   ```
   - 2건 → 겸직 등록됨, 주법인 변경 가능
   - 1건 → 겸직 미등록 → 변경 불가, 고객에게 겸직 등록 선행 안내
2. 전환 조건 확인 — **양쪽 유저 모두** 퇴직 예정이 아니어야 하고 온보딩 완료 상태여야 함
3. 변경 방법: Operation API `PUT /action/v2/operation/core/users/primaryUser`
   - `sourceUserId`: 현재 주법인(변경 전) user_id / `targetUserId`: 새 주법인(변경 후) user_id
4. 주법인 전환 후 이메일/인증은 새 주법인 기준으로 변경됨 — 고객에게 안내 필요
5. 겸직 해지 불가 케이스 확인: (1) 대표회사 비소속, (2) 계열사 비소속, (3) 해지 대상이 계열사 마지막 최고관리자

#### 진단 체크리스트 (정보 일괄 변경 엑셀 미리보기)
문의: "기본 정보 변경 엑셀 미리보기에서 구성원이 중복으로 나와요" / "미리보기에서 알 수 없음이 표시돼요"
1. access log에서 해당 customer의 `POST /action/v2/bulk-changes/candidates/search-by-filter` 호출 횟수 확인 [CI-4226]
2. 2회 호출되었고 1차 요청의 `employeeNumbers`에 이메일 형식(`@` 포함) 값이 들어있으면 → 프론트엔드 엑셀 파싱 버그 (사번 컬럼을 이메일로 잘못 파싱)
3. 1차(이메일 파싱, 0건) + 2차(사번 파싱, N건) 결과가 합쳐져 중복 표시 / 이메일 기반 엔트리는 "알 수 없음" 표시
4. 백엔드 이슈 아님 — FE 팀에 버그 전달 (validate API 호출은 0건이므로 미리보기 단계에서만 발생)

#### 진단 체크리스트 (문서함 삭제 복구)
문의: "문서함을 삭제했는데 복구해주세요" / "신분증 문서함이 사라졌어요"
1. 문서함 삭제 방식 확인 → **Hard Delete** (물리 삭제, soft delete 없음) [CI-4256]
2. Hibernate Envers audit 테이블에 이력 존재 → `user_document_audit`, `user_document_file_audit` 조회 [CI-4256]
3. audit 테이블에서 삭제 전 데이터 확인:
   - `user_document_audit`에서 삭제된 문서함 설정(preset_type, name 등) 확인
   - `user_document_file_audit`에서 해당 문서함의 파일 목록(file_key, user_id 등) 확인
4. 복구 판별:
   - audit 데이터 있고 + S3 파일 잔존 → INSERT로 문서함 + 파일 복원 가능
   - audit 데이터 없음 → DB Snapshot 복구 요청 (삭제된 구성원 복구 절차 동일)
   - 원칙: **고객이 직접 삭제한 데이터는 원칙적으로 복구 불가** [QNA-1180]
5. 삭제 API: `POST /action/v2/core/customers/{customerIdHash}/user-documents/delete-bulk` [CI-4256]

#### 조사 플로우 (문서함)

**F3: 문서함 삭제 복구 검토** · 타입: Data · 히트: 1 · [CI-4256]
> 트리거: "문서함 삭제 복구", "문서함이 사라졌어요", "신분증/이력서 문서함 복구"

```
① user_document_audit 테이블에서 삭제 이력 확인
   SELECT * FROM user_document_audit WHERE customer_id = ? AND preset_type = ?
   ↓
② audit 데이터 존재 여부 판별
   ├─ 있음 → ③으로
   └─ 없음 → DB Snapshot 복구 요청 (DBA 협조)
   ↓
③ user_document_file_audit에서 파일 목록 확인
   SELECT * FROM user_document_file_audit WHERE customer_id = ? AND user_document_id = ?
   → file_key 목록 추출
   ↓
④ S3 파일 잔존 확인
   ├─ 파일 존재 → INSERT로 user_document + user_document_file 복원
   └─ 파일 삭제됨 → 메타데이터만 복원 가능, 파일은 불가 안내
```

---

### 승인 (Approval)

→ 도메인 이해: [cookbook/approval.md#도메인-컨텍스트](cookbook/approval.md#도메인-컨텍스트)

#### 진단 체크리스트
문의: "퇴직자 승인자 교체 알림이 뜨는데 실제 건이 없어요"
1. 메타베이스 대시보드(#309)에서 `target_uid`로 승인 요청 확인 → 요청은 존재하나 대응하는 실제 휴가 사용 건이 없으면 고아 승인 요청 [CI-3951]
2. 퇴직자가 휴가 승인 정책에 여전히 포함되어 있는지 확인 → 승인 정책에서 퇴직자 제거 안내 [CI-3951]

문의: "삭제된 구성원이 승인 라인에 있어서 승인이 안 돼요" / "삭제한 사람 승인건 처리해주세요"
1. [Metabase 퇴사자 미처리 승인 대시보드](https://metabase.dp.grapeisfruit.com/dashboard/245)에서 대상 userId의 미처리 승인건 확인 [CI-4228]
2. **퇴직자 vs 삭제된 구성원 구분**: 퇴직자는 제품의 "퇴직자 승인자 교체" 기능 사용 가능. 삭제된 구성원은 퇴사 이벤트가 발행되지 않아 `approval_replacement_target`에 미등록 → 교체 불가, Operation API로 강제 승인 필요 [CI-4228] [CI-3769]
3. 고객에게 "강제 승인 처리" 동의 확인 후 `bulk-approve-for-user` API 호출:
   - `POST /api/operation/v2/approval/process/customers/{customerId}/users/{userId}/bulk-approve-for-user`
   - Body: `{ "categories": ["TIME_OFF", "WORK_RECORD", "APPROVAL_DOCUMENT"] }` (카테고리는 대상에 맞게 조정, 워크플로우 문서는 `APPROVAL_DOCUMENT` 포함 [CI-4286])
4. 응답의 `succeededProcesses` / `failedProcesses`로 처리 결과 확인

문의: "휴직자가 승인 라인에 있어서 승인이 안 돼요" / "휴직 예정자 승인건 처리해주세요" / "대결 요청"
1. 휴직자는 퇴직자가 아니므로 제품의 "퇴직자 승인자 교체" 기능 사용 **불가** — `replacement-targets`는 퇴사 이벤트 기반 퇴직자 전용 [CI-4266]
2. `approval_process` 조회 시 미처리 상태값은 **`ONGOING`** (REQUESTED/IN_PROGRESS 아님) [CI-4266]
3. 고객에게 "강제 승인 처리" 동의 확인 후 `bulk-approve-for-user` API 호출 (F1 플로우와 동일)
4. 향후 방지: 고객에게 승인 정책에서 휴직자를 다른 승인자로 변경하도록 안내

문의: "승인 설정/라인을 확인해주세요" / "위젯 종료 시 근무 승인이 안 돼요"
1. 승인 설정 확인: `customer_workflow_task_template` + `customer_workflow_task_template_stage`
2. 위젯 종료 시 기본 근무일은 승인 미발생이 정상 동작 (스펙)
3. 주휴일인데 휴일 근무 승인 발생 → 주휴일 설정 일시와 휴일 근무 등록 일시 간 시간차 확인

문의: "요승설이 뭐가 적용됐나요" / "어떤 승인 정책이 매칭됐는지 알고 싶어요"
1. 요승설 매칭 결과는 **DB에 저장되지 않음** — 서버 로그에만 남음
2. 문서 요청 시간대 access log에서 `/match-step` traceId 확인
3. traceId로 앱 로그 필터 → `[ApprovalPolicy] 요승설 매칭 category {category} policy key {key}` 로그 확인
4. 승인 정책(`customer_workflow_task_template`) 조회 시 `policy_key`로 매핑 가능

문의: "승인 정책 복구해주세요" / "삭제한 요승설 되돌려주세요"
1. **기본 기조는 복구하지 않음** — 삭제된 정책은 되돌리지 않는다
2. 메타베이스에서 삭제된 정책 조회 후 엑셀로 전달 (CC팀 접근 권한 없음)
3. [요청자별 승인 현황 Metabase](https://metabase.dp.grapeisfruit.com/dashboard/218?email=) / [승인자별 승인 현황](https://metabase.dp.grapeisfruit.com/dashboard/224?email=)

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

문의: "승인 프로세스가 시작됐는데 TT에서 400 오류 / 승인 항목이 비정상 상태"
1. **신승인 start-approval-process / produce-event 2PC 패턴** → 신승인 처리는 2단계:
   - Step 1: `startWithoutEventProduce` → `/start-approval-process`
   - Step 2: `produceStartEvent` → `/start-approval-process/produce-event`
   - produce-event 실패 시 반드시 rollback: `/rollback-started` 호출 (`ApprovalProcessCommandInternalService.rollbackStarted`)
2. **비정상 상태 데이터 복구** → `approval_process` 테이블에서 해당 건 soft delete + `approval_replacement_target` 테이블에서 soft delete + TT 보상 처리 [CI-3951]

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.

**F1: 비활성 사용자(삭제/휴직/퇴직) 승인건 강제 승인** · 타입: Data · 히트: 3 · [CI-4228] [CI-3769] [CI-4266] [CI-4286]
> 트리거: "삭제된 구성원이 승인 라인에 있어 승인 불가" / "삭제한 사람 승인건 처리" / "휴직자 승인건 처리" / "퇴사자 미승인건 처리" / "대결 요청"

```
① 대상 사용자 상태 확인
   view_user에서 status/deleted_date 확인
   ├─ 퇴직자(resigned) → 제품의 "퇴직자 승인자 교체" 기능 사용
   ├─ 삭제된 구성원(deleted) → ②로
   └─ 휴직자/퇴직자(UI 교체 불가) → ②로 (replacement-targets 미지원)
   ↓
② approval_process에서 미처리 건 확인
   ⚠️ 미처리 상태값은 ONGOING (REQUESTED/IN_PROGRESS 아님)
   approval_line_actor에서 해당 userId가 PENDING인 건 조회
   ↓
③ 고객에게 강제 승인 동의 확인
   ↓
④ bulk-approve-for-user API 호출
   POST /api/operation/v2/approval/process/customers/{customerId}/users/{userId}/bulk-approve-for-user
   Body: { "categories": ["TIME_OFF", "WORK_RECORD", "APPROVAL_DOCUMENT"] }
   ⚠️ categories는 대상 문서 유형에 맞게 조정 (워크플로우 문서는 APPROVAL_DOCUMENT)
   ↓
⑤ 응답 확인
   ├─ succeededProcesses 에 대상 건 포함 → ⑥으로
   └─ failedProcesses 에 건 포함 → 실패 원인 확인 (로그 조회)
   ↓
⑥ workflow_task 상태 확인
   workflow_task.status가 여전히 IN_PROGRESS이면 → sync-with-approval API 호출
   POST /api/v2/operation/workflow/customers/{customerId}/users/{writerId}/approval-document/{documentKey}/sync-with-approval
   ├─ DONE으로 변경 → 완료
   └─ 이미 DONE → ⑤에서 완료
```

**F2: 승인 리마인드 발송자 추적** · 타입: Data · 히트: 1 · [CI-4203]
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
3. **퇴직자 포함 휴가 데이터 추출** (삭제된 조직 소속 구성원 포함) → 웹 UI에서 "퇴직자 포함" 옵션으로 먼저 시도. 삭제된 조직 소속 구성원은 웹 UI에서 추출 불가 → Operation API 사용:
   ```
   POST /action/operation/v2/time-off/customers/{customerId}/time-offs/excel/used
   { "queryUserId": {adminUserId}, "departmentIds": null,
     "dateFrom": "YYYY-MM-DD", "dateTo": "YYYY-MM-DD",
     "includeResignatedUsers": true }
   ```
   [CI-3976]

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

#### 진단 체크리스트 (엑셀 업로드)
문의: "목표 엑셀 업로드 시 조직명이 안 맞아요" / "담당 주체를 잘못 입력했다고 나와요"
1. 오류가 발생하는 조직의 **생성일**과 엑셀에 설정된 **목표 시작일**을 비교 [CI-4284]
   - 목표 시작일이 조직 생성일보다 이전이면 → 시계열 매칭 실패가 원인
   - 조직은 시계열 데이터이므로, 엑셀 업로드 시 목표 시작일 기준으로 해당 시점에 존재하는 조직만 매칭됨
2. **조치**: 목표 시작일을 조직 생성일과 동일하거나 이후로 설정 후 업로드 안내. 업로드 완료 후 목표 시작일은 자유롭게 변경 가능
3. 근본 개선 티켓: [EPBE-317](https://linear.app/flexteam/issue/EPBE-317/) (부서 name 매칭 개선), [EPBE-318](https://linear.app/flexteam/issue/EPBE-318/) (validation message 개선) — backlog

→ 상세: [cookbook/goal.md](cookbook/goal.md)

---

### 전자계약 (Contract/Digicon)

#### 진단 체크리스트
문의: "서명된 계약서 삭제해주세요" / "계약서 서식이 삭제됐어요" / "서식 삭제자를 알고 싶어요" / "일괄 다운로드 링크가 안 나와요" / "임시저장한 계약서가 사라졌어요" / "전자계약 서식 계열사에 복사해달라" / "계약서 필드가 비어있어요" / "연락처가 공란이에요"
1. 서명 완료(SUCCEED) 계약서 삭제/취소 요청 → **삭제 불가(스펙)**. `DigiconProgressStatus.cancelable()` = `this === IN_PROGRESS`만 허용. 올바른 내용으로 새 계약서 재발송 안내 [CI-4152]
2. 서식(template) 삭제자 추적 → access log에서 `DELETE /api/v2/digicon/templates` 검색 → traceId로 호출 체인 추적 → permission-api 호출에서 userId 확인 → view_user 테이블로 이메일 매핑. 감사로그에 서식 삭제 미기록 [CI-4168]
3. 양식 개수 제한 여부 → 제한 없음 [CI-4168]
4. 삭제된 서식 복구 → Operation API: `POST /api/operation/v2/digicon/customers/{customerId}/restore-deleted-templates` [CI-4168]
5. 선택 발송 후 임시저장 계약서 삭제 문의 → **현재 스펙**. CandidateSet = 한 번의 발송 단위로 설계되어, 선택 발송 시 미선택 CandidateUnit은 물리 삭제됨. 복구 불가. VOC-2410으로 개선 요청 등록됨 [CI-4257]
6. 계열사에 전자계약 서식 복제 요청 → raccoon prod `POST /api/operation/v2/digicon/duplicate-templates` 실행. `originalCustomerId`(주법인) + `targetCustomerIds`(계열사 목록) + `postfix`("" = 원본 제목 유지) [CI-4283]
7. 일괄 다운로드 링크 미생성 → 비동기 처리 구조이므로 API 자체는 정상 응답. app log에서 `[DIGICON UPLOAD]` + `[File Merge]` 확인. 임시 파일 TTL=600초이므로 merge 큐 지연 시 실패. 파일 서비스 장애 여부 확인 후 **재시도** [CI-4248]
8. 계약서 필드 공란 / placeholder 미치환 → `digicon` 테이블에서 `placeholder_values` 확인. 값 자체가 정상이면 **renderer(flex-html)의 유효성 검증 문제** — hyphen 등 특수문자 포함 시 미치환. `sanitize-placeholder-values` Operation API로 특수문자 제거 (멱등성 보장) [CI-4297]

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.
> 여러 플로우가 후보이면 병렬로 실행하여 히트 여부를 빠르게 판별.

**F1: 전자계약 서식 삭제자 추적** · 타입: Data · 히트: 1 · [CI-4168]
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

**F3: 계열사 전자계약 서식 복제** · 타입: Data · 히트: 1 · [CI-4283]
> 트리거: "전자계약 서식 계열사에 복사해달라" / "주법인 서식 이관"

```
① 주법인 customer_id와 대상 계열사 customer_id 목록 파악
   → Linear 이슈 설명 또는 CS 문의에서 확인
   ↓
② raccoon prod Swagger → digicon → duplicate-templates 실행
   POST /api/operation/v2/digicon/duplicate-templates
   {"originalCustomerId": ?, "targetCustomerIds": [?], "postfix": ""}
   → 200 OK 확인
   ↓
③ 고객사에 복제 결과 확인 요청
   ├─ 서식 목록 정상 노출 + 편집 가능 → 완료
   └─ 문제 있음 → 서식/placeholder DB 직접 확인
```

**F2: 전자계약 일괄 다운로드 링크 미생성** · 타입: Error · 히트: 1 · [CI-4248]
> 트리거: "일괄 다운로드 링크가 안 나와요" / "대량 다운로드 실패"

```
① Access log: API 호출 확인
   OpenSearch be-access → POST /api/operation/v2/digicon/bulk-download-pdf
   → 호출 없으면 admin-shell 조작 문제
   ↓
② App log: PDF 업로드 완료 확인
   traceId로 "[DIGICON UPLOAD] upload done" 검색
   → digiconSize 확인 (0이면 대상 계약서 없음)
   ↓
③ App log: 파일 병합 결과 확인
   fileMergeId로 "[File Merge]" 검색
   ├─ ERROR "S3 파일 다운로드 예외" → 임시 파일 만료 (merge 큐 지연)
   │   → 파일 서비스 장애 확인 + 재시도
   └─ 로그 없음 → merge 큐가 아직 처리 안 함 / 파일 서비스 장애
```

> 핵심: 임시 파일 TTL=600초(10분). merge 큐가 밀리면 항상 실패하는 구조.

---

### 급여 (Payroll)

→ 도메인 이해: [cookbook/payroll.md#도메인-컨텍스트](cookbook/payroll.md#도메인-컨텍스트)

#### 진단 체크리스트
문의: "초과근무 계산이 이상해요" / "포괄 공제가 안 맞아요" / "올림 계산이 안 맞아요" / "급여정산 해지하면 명세서 공개가 되나요?" / "원천징수영수증 일괄 다운로드 실패" / "중도정산 건강보험이 2배에요" / "휴직자 건강보험 근무월수가 이상해요" / "주휴수당 대상자에 안 불러와져요"
1. 올림 자릿수 이상 문의 → 설정 변경 시점과 정산 생성 시점 비교. 정산 생성 시 올림 설정이 스냅샷됨 → 기존 진행 중 정산은 이전 설정 유지 [CI-4131]
   - `payroll_legal_payment_setting`(현재 설정)과 `work_income_over_work_payment_calculation_basis`(정산 스냅샷) 비교
   - 불일치하면 설정 변경 전 생성된 정산 → 신규 정산 생성 안내
2. 포괄임금계약 관련 → "근태/휴가" 도메인의 포괄계약 항목 참조 [CI-3868]
3. 보상휴가 부여 관련 → "근태/휴가" 도메인의 보상휴가 항목 참조 [CI-3858]
4. 주 연장근무 계산 → "스케줄링" 도메인의 연장근무 항목 참조 [CI-3839]
5. 정산 수정 후 소득세 변경 문의 → 정산 자물쇠 해제 후 재처리 시 소득세 변경 → 1차 정산 ~ 수정 정산 사이에 기본 공제 대상(부양가족 수)이 변경되었는지 확인. `work_income_settlement_payee`의 `dependent_families_count` 조회 [CI-4149]
6. 급여정산 해지 후 명세서 공개/알림 문의 → 알림은 해지와 무관하게 발송됨. 단, 구독 해지 시 급여 탭 접근 차단되어 실제 열람 불가. 1달 연장 권장 안내 [QNA-1933]
7. 중도정산 시 건강보험 제외 대상인데 사회보험 금액 표시 → 확정→확정해제→최신정보반영 경로를 거쳤는지 확인. 워크어라운드: 건강보험 제외→확정→확정해제→포함 변경 [CI-4174]
8. 이관 회사 중도정산 보험료(건강보험/장기요양) 불일치 → 이관 회사 여부 확인 → 맞으면 보험료 리셋(DELETE /premium → recalculate) 안내. 원인: recipient 생성 시점의 불완전한 보수총액으로 1회 계산·저장되며 이관 데이터 추가 후 자동 재계산 안 됨 — 히트: 2 (CI-4212) [CI-4212]
9. 사회보험 연말정산 기납보험료에 전년도 분할납부 합산 문의 → `HealthInsuranceSettlementReasonCode`의 `YEAR_END_REASON_CODES`에 74번(정산분할고지보험료) 포함 여부 확인 → `PaidSocialInsuranceCalculator.getYearEndTotalAmountByType()`이 귀속연도 필터 없이 전체 합산하는 버그. CI-4174 핫픽스 파생 — 버그 (수정 대기) [CI-4222]

10. 휴직자 지급항목 금액 0원 문의 → `allowance_global` 테이블에서 해당 항목의 `allowance_on_leave_rule` 확인. `DAILY_BASE`이고 `paymentRatio=0`(육아휴직 등)이면 정상 동작. 고객에게 해당 항목의 "휴직월 지급 방법"을 `FULL`(전액지급)로 변경 안내 — 히트: 1 (CI-4225) [CI-4225]

11. 외국인 고용보험 미공제 문의 → `work_income_settlement_payee`의 `residence_qualification` 확인. UNKNOWN이 아닌 외국인 체류자격이면 → `employment_insurance_qualification_history`에서 취득일 존재 여부 확인. 취득일 없음 → 사회보험 자격관리에서 고용보험 취득일 등록 안내 — 스펙 (임의가입 대상) [CI-4241]

12. 원천징수영수증 일괄 다운로드 실패 → 비동기 백그라운드 태스크 구조. access log에서 `POST /action/v2/payroll/work-income/settlement-results/async-bulk-download-withholding-receipts-by-filter` 호출 확인 → 파일 서비스 장애(CI-4236 유사) 여부 확인. 장애 해소 후 **재시도**로 해결 [CI-4240]
13. **중도정산 건강보험료 2배** → 76번 코드(휴복직보험료)가 `HealthInsuranceSettlementReasonCode`에서 `LEAVE_OF_ABSENCE_REASON_CODES`와 `SETTLEMENT_REASON_CODES` 양쪽에 속해 `RetireeYearEndHealthInsuranceCalculatorImpl.calculate()`에서 2중 합산. 74번 코드는 영향 없음 — **버그** [CI-4151]
14. **사회보험 연말정산 휴직자 건강보험 근무월수 오집계** → 연속 휴직(예: 04-01~09-28, 09-29~이후)이 개별 루프로 처리되어 경계 월(9월)이 어느 쪽에도 포함되지 않고 근무월로 잘못 카운트. `HealthInsuranceMonthsCalculator.calculateOnLeaveMonths()` 에서 병합 로직 부재 — **버그** [CI-4159]
15. 급여정산 실행 시 "알 수 없는 오류" + 대상자 0명 stuck → 사업장 담당자 계정 여부 확인 → 회사 전체 구성원 수 확인(2,000명↑ 위험). 원인: 인가 로직이 전체 구성원 조회 → `resolveAccessibleUsers` 타임아웃. flex-permission-backend v3.58.3(6초→10초) + payroll hotfix #8714로 수정됨 [CI-4260]

15. **정산 실행 시 "알 수 없는 오류" + 대상자 0명** → 대규모 회사(1,000명+)에서 사업장 담당자 계정으로 정산 실행 시 인가 타임아웃(`resolveAccessibleUsers`) 발생 가능. settlement은 커밋되지만 payee 초기화 실패 → 0명 IN_PROGRESS stuck. 깨진 정산 CANCELED 처리 필요 [CI-4260]

16. **정산 상세 지급액 0원 (실지급액은 정상)** → `work_income_payment_settlement_payee_result_item` 테이블에 해당 payee result 항목이 존재하는지 확인. 0건이면 2025-03-19 backfill 누락. customer_id 기준 미마이그레이션 payee 수 조회 → 다수이면 Operation API `migrate-ci4227/{customerId}?dryRun=true`로 확인 후 `dryRun=false`로 실행 — 히트: 2 (CI-4227, CI-4265) [CI-4265]

17. **퇴직자 급여정산 주휴수당 미노출** → 정산 템플릿의 `work_record_import` 확인. `NONE`이면 TT 주휴수당 미조회 → default recipient 생성 시 dateRange가 전체 기간으로 설정됨 → 월 중도 퇴사자는 base payment dateRange와 불일치 → items:[] 반환 (Known Issue). 워크어라운드: 지급 항목 별도 추가로 수동 반영 [CI-4307]

#### 조사 플로우

**F-pay-3: 정산 실행 타임아웃 — 인가 조회 + 정합성 확인** · 히트: 1 · [CI-4260]
> 트리거: "급여정산 실행 시 알 수 없는 오류" / "정산 대상자가 0명이에요" / 대규모 회사 사업장 담당자

```
① Sentry에서 FlexRemoteUnknownStateException: timeout 확인
   ├─ 있음 → ②로
   └─ 없음 → 다른 원인 (F-pay-1~2 시도)
   ↓
② 고객사 전체 구성원 수 확인
   ├─ 1,000명+ → 인가 타임아웃 가능성 높음 → ③으로
   └─ 소규모 → 다른 원인 조사
   ↓
③ 깨진 정산 조회
   SELECT s.id, s.settlement_status, COUNT(p.id)
   FROM work_income_settlement s
   LEFT JOIN work_income_settlement_payee p ON p.settlement_id = s.id
   WHERE s.customer_id = {cid} AND s.created_at >= '{date}'
   GROUP BY s.id
   ├─ payee 0명 + IN_PROGRESS → CANCELED 처리
   └─ 정상 → 일시적 네트워크 문제
```

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

**F-pay-2: 원천징수영수증 일괄 다운로드 실패 — 파일 서비스 밀림 확인** · 히트: 0 · [CI-4240]
> 트리거: "원천징수영수증 일괄 다운로드 실패" / "다운로드 준비중 무한 로딩"

```
① Access log: API 호출 확인
   OpenSearch be-access → POST /action/v2/payroll/.../async-bulk-download-withholding-receipts-by-filter
   → 호출 없으면 프론트엔드/네트워크 문제
   ↓
② 비동기 태스크 상태 확인
   API 자체는 즉시 응답(~100ms). 백그라운드 태스크가 파일 생성 담당
   ├─ 태스크 성공 → 정상 (네트워크 일시 문제 가능성)
   └─ 태스크 실패/타임아웃 → ③으로
   ↓
③ 파일 서비스 장애 확인
   동일 시간대 파일 서비스 밀림(CI-4236 유사) 여부 확인
   ├─ 장애 확인 → 장애 해소 후 재시도 안내
   └─ 장애 없음 → app log에서 상세 에러 추적
```

> 핵심: 전자계약 F2 플로우와 동일 패턴 — 파일 merge 큐 지연 시 임시 파일 TTL(600초) 초과로 실패.

**F-pay-4: 퇴직자 정산 주휴수당 미노출 — work_record_import + dateRange 불일치** · 히트: 1 · [CI-4307]
> 트리거: "주휴수당 대상자에 안 불러와져요" / "퇴직자 급여정산 주휴수당이 안 나와요" / 월 중도 퇴사자 주휴수당

```
① 정산 템플릿의 work_record_import 확인
   SELECT work_record_import FROM work_income_settlement_template WHERE id = ?
   ├─ FLEX → TT 연동 회사, 이 플로우 해당 없음 → 다른 원인 조사
   └─ NONE → ②로
   ↓
② 대상자 퇴사일 확인
   work_income_settlement_payee에서 offboarded_date 확인
   ├─ 정산 기간 말일 = 퇴사일 → 이 버그 해당 없음
   └─ 정산 기간 중도 퇴사 → ③으로 (Known Issue 확정)
   ↓
③ 워크어라운드 안내
   지급 항목 별도 추가(커스텀 지급 항목)로 주휴수당 수동 반영
   근본 수정은 스쿼드 과제 대기 중
```

*(급여 도메인은 근태/휴가, 스케줄링과 겹치는 이슈가 많으며, 상세 진단은 해당 도메인 참조)*

→ 상세: [cookbook/payroll.md](cookbook/payroll.md)

---

### 평가 (Evaluation / Performance Management)

→ 도메인 이해: [cookbook/review.md#도메인-컨텍스트](cookbook/review.md#도메인-컨텍스트)

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

문의: "구리뷰 진행 중 질문 문구 수정해주세요" / "리뷰 섹션명 변경해주세요" / "리뷰 문항 텍스트가 잘못됐어요"
1. "질문 추가/삭제/타입 변경"인지 "텍스트 오타/문구 수정"인지 먼저 구분
   - 추가/삭제/타입 변경 → **불가능** (제품 정책상 미지원, 고객 안내 후 종료) [CI-4338]
   - 텍스트 수정만 → ②로 [CI-4338]
2. `review_model` 테이블에서 해당 review_set_id로 하향/셀프/상향 단계의 `onetime_template_id` 조회 [CI-4338]
3. `review_question` 테이블에서 해당 template_id로 수정 대상 question_id 특정 (섹션명은 `question_type='SUBTITLE'`) [CI-4338]
4. 기안 후 `review_question` UPDATE 3건 + `question_log` 동기화 UPDATE 실행 [CI-4338]

문의: "구리뷰로 원복 가능한가요?" / "구리뷰 메뉴가 안 보여요" / "평가 → 구리뷰 전환 요청"
1. flag 설정으로 구리뷰 메뉴 재노출 가능 여부 확인 — 담당자(김보라님)에게 flag 설정 요청 [CI-4331]
2. 마감된 리뷰의 작성기간 수정이 필요한 경우 → `flex_review.review_set.progress_status`가 `ANSWER_NOT_OPEN`이면 `IN_PROGRESS`로 변경해야 관리자가 기간 수정 가능 [CI-4331]
3. **주의**: 기간 수정은 반드시 리뷰관리자(고객)가 직접 수행해야 할일 발송됨. 데이터 보정으로 날짜를 직접 변경하면 할일 미발송 [CI-4331]
4. 구리뷰 잔존 고객사는 Notion 리스트에 추가 필요 [CI-4331]

문의: "진행 중인 구리뷰 질문을 수정해주세요" / "리뷰 질문 문구를 바꿔주세요" / "섹션명 수정 요청"
1. **제품 비지원**: 진행 중인 리뷰의 질문지 수정은 제품에서 지원하지 않음. 단, **질문 제목/설명 텍스트 수정만** 예외적으로 오퍼레이션 가능 [CI-4338]
2. 섹션명도 `review_question.question_type = 'SUBTITLE'` 행의 `question` 값이므로 동일 방법으로 수정 가능
3. **불가 범위**: 질문 추가/삭제/타입 변경, 선택형 문항 수정
4. 조치: template_id + question ID 확인 → `review_question.question` UPDATE → `question_log.content` 동기화 (결재 필요, SQL은 cookbook/review.md 참조) [CI-4338]

문의: "평가지 생성 중" / "평가지가 안 보여요"
1. `evaluation_reviewer` 테이블에서 해당 reviewee-reviewer 조합의 `user_form_ids`가 `[]`인지 확인 [CI-4188]
2. 빈 배열이면 `created_at`을 일괄 생성 레코드와 비교하여 후발 추가 여부 확인 [CI-4188]
3. 후발 추가 확인 시 → raccoon Operation API `initialize-user-form` 호출하여 수동 초기화 [CI-4188]

문의: "평가 항목 작성 요청 했는데 할일이 안 왔어요" / "평가 준비 > 평가 항목에서 대상자가 없어요"
1. `reviewee_evaluation_item` 테이블에서 해당 `evaluation_id`로 조회 — 0건이면 항목 생성 단계에서 필터링된 것 [CI-4238]
2. 0건이면 → `evaluation_reviewee`의 `evaluate_step_and_factors`에 COMPETENCY factor가 있는지, `competency_group_mappings`가 `[]`인지 확인
3. `evaluation.use_competency_item = 0` + COMPETENCY factor 존재 + `competency_group_mappings = []` 세 조건 모두 해당 시 → 이 버그에 해당 (PR#5199로 수정됨) [CI-4238]
4. 버그 해당 시 조치: ① 항목 요청 초기화 → ② 대상자 전원 제외 → ③ 대상자 재추가 → ④ 항목 요청 재실행

문의: "배분율 초과 시 제출이 안 돼요" / "등급 배분율 설정 변경이 안 돼요" / "인원 초과 시 제출 제한 비활성화하고 싶어요"
1. `flex_review.evaluation_grade_distribution`에서 해당 evaluation의 `allow_submission_if_exceed` 값 확인 → `0`이면 배분율 초과 시 제출 차단 설정 [CI-4327]
2. 평가가 이미 시작된 경우 UI에서 변경 불가 (시스템 스펙) → DML 보정 필요 [CI-4327]
3. 조치: 결재 후 `allow_submission_if_exceed = 1` UPDATE (`evaluation_id`와 레코드 `id` 모두 WHERE 조건으로 사용)

문의: "평가지 질문을 필수에서 선택으로 변경했는데 제출이 안 돼요" / "제출에 실패했어요"
1. `form_question` 테이블에서 해당 질문의 `required` 값 확인 → `0`(선택)인데 제출 실패이면 ②로 [CI-4314]
2. `form_user_answer` 테이블에서 같은 질문의 `required` 값 확인 → `1`(필수)이면 이 버그에 해당 [CI-4314]
3. 조치: `form_user_answer.required = 0` UPDATE (결재 필요). 답변이 비어있는 경우 status도 확인 [CI-4314]
4. 근본 원인: `RequiredChangeInfo`가 필수→선택(turned OFF) 변경을 추적하지 않음. EPBE-336에서 코드 수정 예정 [CI-4314], [CI-4238]

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.

**F1: 삭제된 평가 복구** · 타입: Data · 히트: 1 · [CI-4195]
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

**F3: 평가 등급 배분 완료 시 validation 오류** · 타입: Error · 히트: 2 · [CI-4204] [CI-4117]
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

**F4: 뉴성과관리 전환 후 구 리뷰 사라짐** · 타입: Data · 히트: 1 · [CI-4210]
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

**F5: 등급 배분율 초과 시 제출 차단 설정 보정** · 타입: Spec · 히트: 1 · [CI-4327]
> 트리거: "배분율 초과인데 제출이 안 돼요", "등급 배분율 설정을 바꾸고 싶어요" — 평가 진행 중 `allow_submission_if_exceed` 보정 필요

```
① evaluation_grade_distribution 현재 설정 확인
   SELECT id, evaluation_id, grade_factor_id, allow_submission_if_exceed
   FROM flex_review.evaluation_grade_distribution
   WHERE customer_id = ? AND evaluation_id = ?
   ├─ allow_submission_if_exceed = 0 → 배분율 초과 시 제출 차단 상태, ②로
   └─ allow_submission_if_exceed = 1 → 이미 허용 상태, 다른 원인 조사
   ↓
② 평가 단계 시작 여부 확인
   UI에서 설정 변경 불가 상태인지 고객 확인 (진행 중이면 UI 잠김)
   → DML 보정 필요, ③으로
   ↓
③ DML 보정 (결재 필요)
   -- 적용
   UPDATE flex_review.evaluation_grade_distribution
   SET allow_submission_if_exceed = 1
   WHERE customer_id = ? AND evaluation_id = ? AND id = ?
   → 고객에게 제출 재시도 요청
```

**F6: 구리뷰 진행 중 질문 텍스트 수정** · 타입: Spec · 히트: 1 · [CI-4338]
> 트리거: "진행 중 리뷰 섹션명/질문 문구 수정 요청" — 텍스트 오타·표현 변경 한정 (추가/삭제 불가)

```
① 수정 유형 판별
   텍스트 수정(오타·문구 변경) vs 질문 추가/삭제/타입 변경
   ├─ 추가/삭제/타입 변경 → 정책상 불가. 고객 안내 후 종료
   └─ 텍스트 수정만 → ②로
   ↓
② review_set 확인 + 단계별 template_id 조회
   SELECT id, onetime_template_id, review_type
   FROM flex_review.review_model
   WHERE review_set_id = ? AND deleted = 0
   → 하향/셀프/상향 단계 중 수정 대상 단계의 onetime_template_id 확인
   ↓
③ 수정 대상 question_id 조회
   SELECT id, question_type, question, display_order
   FROM flex_review.review_question
   WHERE template_id = ? ORDER BY display_order
   - 섹션명: question_type = 'SUBTITLE'
   - 일반 질문: question_type = 'LONG_TEXT' / 'RATING' 등
   ↓
④ 백업 SELECT 실행 후 결과 보관
   SELECT id, template_id, question_type, question, description
   FROM flex_review.review_question WHERE id IN (?, ?, ?)
   + SELECT ql.* FROM flex_review.question_log ql WHERE ql.question_id IN (?, ?, ?)
   ↓
⑤ review_question UPDATE (결재 필요)
   UPDATE flex_review.review_question SET question = '새 문구' WHERE id = ?
   — 수정 대상 행 수만큼 반복
   ↓
⑥ question_log 동기화 (필수, 결재 필요)
   UPDATE flex_review.question_log ql
   JOIN flex_review.review_question rq ON ql.question_id = rq.id
   SET ql.content = rq.question, ql.description = rq.description
   WHERE rq.template_id = ?
     AND (rq.question != ql.content OR rq.description != ql.description)
   → 영향 행 수 확인 (수정 건수와 일치해야 함)
```

**F2: 후발 추가 reviewer UserForm 미초기화** · 히트: 2 · [CI-4188] [CI-4301]
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

```sql
-- 등급 배분율 설정 확인
SELECT id, evaluation_id, grade_factor_id, allow_submission_if_exceed
FROM flex_review.evaluation_grade_distribution
WHERE customer_id = ? AND evaluation_id = ?;

-- 등급 배분율 제출 제한 해제 (결재 필요)
UPDATE flex_review.evaluation_grade_distribution
SET allow_submission_if_exceed = 1
WHERE customer_id = ? AND evaluation_id = ? AND id = ?;

-- 롤백
-- UPDATE flex_review.evaluation_grade_distribution
-- SET allow_submission_if_exceed = 0
-- WHERE id = ?;
```

#### 과거 사례
- **삭제한 평가가 다시 노출**: 실제로는 삭제된 적 없는 title=null DRAFT 평가가 FE 핫픽스로 정상 노출된 것. 고객이 "이전에 안 보이던 것이 보임"을 "삭제 복원"으로 오해 — **스펙** [CI-4158]
- **평가 공동편집자 아닌데 메뉴 노출**: title=null인 DRAFT 평가를 FE에서 필터링하여 노출 문제 — **버그 (FE)** [CI-4129]
<!-- TODO: 시나리오 테스트 추가 권장 — title=null DRAFT 평가 리스트 정상 노출 검증 -->
- **리뷰 마이그레이션 "Failed requirement." 에러**: dev raccoon에서 prod 해시 사용 → Hashids salt 불일치로 디코딩 실패(`INVALID_NUMBER`). prod raccoon에서 재시도하면 구체적 에러 정상 출력 — **운영 오류** [QNA-1936]
- **후발 추가 reviewer 평가지 미생성**: finalize 이후 추가된 reviewer의 UserForm이 메시지 큐 실패로 초기화 안 됨. admin 화면에서 "생성 중" 표시. Operation API `initialize-user-form`으로 수동 해결 — **운영 대응** [CI-4188] [CI-4301]
- **삭제된 진행 중 평가 복구**: 고객 관리자가 다른 평가를 삭제하려다 진행 중 평가까지 삭제. `evaluation` 테이블 soft delete(`deleted_at`, `deleted_user_id`) NULL 복구 DML로 해결. Operation API PR #5181 머지 후 API 복구 가능 — **운영 대응** [CI-4195]
- **평가 등급 배분 완료 시 validation 오류**: 과거 버그 수정 전 평가를 복제하여 `grades_to_calculate`가 비어있는 상태로 전파. `draft_evaluation` DML 보정으로 해결 — **운영 대응** [CI-4204]
- **뉴성과관리 전환 후 진행 중 평가 사라짐**: `MigrationScheduler`가 구 리뷰 → 뉴 성과관리 전환 시 진행 중 리뷰셋을 의도적으로 soft delete. `review_set` 테이블 `deleted=0, deletedAt=NULL` 복구 가능 — **스펙** [CI-4210]
- **등급 배분율 초과 시 제출 차단 설정 보정**: 평가 진행 중 `evaluation_grade_distribution.allow_submission_if_exceed = 0` 상태. UI 편집이 잠겨있어 DML로만 보정 가능 — **운영 대응** [CI-4327]

---

### 채용 (Recruitment)

→ 도메인 이해: [cookbook/recruiting.md#도메인-컨텍스트](cookbook/recruiting.md#도메인-컨텍스트)

#### 진단 체크리스트
문의: "채용사이트 주소 변경이 검토중이에요" / "subdomain 변경 신청 상태 확인"
1. `#alarm-recruiting-operation` 슬랙 채널에서 해당 회사의 변경 요청 알림 확인 [CI-4170]
2. `flex_recruiting.site_subdomain_change` 테이블에서 요청 건의 상태와 도메인명 확인 [CI-4170]
3. 도메인명이 적절하면 raccoon operation API로 승인/반려 처리 [CI-4170]
   - 승인: `POST /customers/{customerId}/subdomains/{siteSubdomainChangeId}/change/approve`
   - 반려: `POST /customers/{customerId}/subdomains/{siteSubdomainChangeId}/change/reject`

#### 조사 플로우

> 비슷한 문의가 들어오면 아래 플로우를 **히트율 순으로** 시도한다.

**F1: 채용사이트 subdomain 변경 요청 방치** · 타입: Data · 히트: 1 · [CI-4170]
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

**F1: 조직 삭제 처리** · 타입: Data · [코어 런북]
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

**F2: 발령+조직변경 데드락 해소** · 타입: Error · [코어 런북]
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

문의: "엑셀 인사발령 기능 오픈해주세요" / "엑셀로 발령 기능 사용하고 싶어요"
1. **엑셀 인사발령 = Flagsmith feature flag**로 고객사별 제어됨 [CI-4313] [CI-4352]
2. 절차:
   1. prod Flagsmith 접속: https://flagsmith.flexis.team/
   2. Segments > `인사발령_엑셀업로드_우선_오픈_고객사` 클릭
   3. Description에 회사명 추가, `customer_id` 값에 해당 ID 추가 (**공백 금지**)
   4. [Update Segment] 클릭
3. **사전 안내 필수**: 임시 제공 기능, 엑셀에 기재된 정보로 **덮어쓰기** (미기재 정보 소실 위험), 과거 발령 히스토리 손실 가능
4. **CI-4214 버그 확인**: 엑셀 발령 후 "정보 변경하러가기" 버튼 미동작 FE 버그 수정 여부 확인 후 미수정 시 고객 안내

#### 조사 플로우

**F1: 엑셀 인사발령 기능 오픈 (Flagsmith)** · 타입: Spec · 히트: 2 · [CI-4313] [CI-4352]
> 트리거: "엑셀 인사발령 기능 오픈해주세요" / "엑셀로 인사발령 사용 요청"

```
① 고객 안내 완료 여부 확인
   덮어쓰기 특성, 임시 제공, 히스토리 손실 위험 안내
   ├─ 안내 완료 + 고객 확인 → ②로
   └─ 미안내 → 안내 후 확인 대기
   ↓
② CI-4214 FE 버그 수정 여부 확인
   "정보 변경하러가기" 버튼 미동작 버그 수정됐는지 확인
   ├─ 수정됨 → ③으로
   └─ 미수정 → 고객에게 해당 제한사항 추가 안내 → ③으로
   ↓
③ prod Flagsmith에서 segment 업데이트
   https://flagsmith.flexis.team/
   Segments > 인사발령_엑셀업로드_우선_오픈_고객사
   → customer_id 추가 (앞뒤 공백 주의) → [Update Segment]
   ↓
④ 고객에게 기능 오픈 완료 안내
```

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

**F1: 출근 불가 — 근무지 범위 확인** · 타입: Auth · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
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

**F1: 대시보드 수치 불일치 — ES 동기화 확인** · 타입: Data · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
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

**F2: 근무시간미달 대시보드 — 고스트 periodicWorkSchedule 노출** · 타입: Data · 히트: 1 · [CI-4304]
> 트리거: "근무시간미달에 실제 미달 없는 구성원이 표시돼요" / "주기 단위 근무시간미달이 잘못 나와요"

```
① 해당 유저의 ES periodicWorkSchedule 조회
   prod-v2-tracking-work-schedules, routing: {customerId}_{userId}
   → startDateOfPeriod 목록 확인
   ↓
② dayOfMonth 불일치 확인
   startDateOfPeriod의 dayOfMonth vs 규칙 beginDate.dayOfMonth
   ├─ 일치 → 정상 문서
   └─ 불일치 → 고스트 후보, ③으로
   ↓
③ 고스트 판별
   workingMinutes=0 + lackOfWorkingMinutes > 0 이면 고스트 확정
   DB 초과근무 API (DB 기반)로 해당 주기 실제 존재 여부 교차 확인
   ↓
④ ES에서 직접 삭제
   ⚠️ 재동기화(sync)로는 해결 불가 — 문서 ID 기반 upsert이므로 고스트를 덮어쓰지 않음
   고스트 문서 ID로 DELETE 직접 실행
```

> 💡 **발생 패턴**: 근무규칙을 짧은 시간 내 여러 번 변경(변경→원복) 시, boundary clamp로 생성된 중간 주기 문서가 클린업되지 않고 잔존. `startDateOfPeriod`가 1일이 아닌 날짜(예: 3/23)이면 고스트.
> ⚠️ **재동기화 불가**: 재동기화는 정상 문서만 갱신, 고스트 ID는 다르므로 삭제 안 됨

---

### 연차 (Annual Time Off)

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

#### 진단 체크리스트
문의: "잔여 연차가 이상해요" / "연차 소멸이 안 맞아요" / "사용일수가 0일이에요" / "잔여일에 소수점이 있어요"
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
7. 잔여일 소수점이 예상보다 크거나 이상한 경우 → 버킷별 `agreedDayWorkingMinutes` 확인 → **소정근로시간 변경 여부 확인** → F3 참조 [CI-4349]

#### 조사 플로우

**F1: 잔여 연차 불일치 — 버킷 확인** · 타입: Data · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
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
   ├─ 잔여일 소수점 이상 → F3 시도
   └─ 겹침으로 인한 0일 사용 → F2 시도
```

**F2: 사용일수 0일 — 겹침 확인** · 타입: Data · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
> 트리거: "사용일수가 0일이에요"

```
① 해당일에 겹치는 항목 확인
   ├─ v2_customer_holiday → 휴일 등록 여부
   ├─ user_leave_of_absence → 휴직 기간
   ├─ v2_time_tracking_user_alternative_holiday_event → 휴일대체
   ├─ v2_customer_work_rule → 해당 요일이 주휴일/쉬는날
   └─ 위 항목 중 하나라도 해당 → 사용일수 0일은 스펙
```

**F4: iOS 연차 미리쓰기 안내 문구 계산 불일치** · 타입: Render · 히트: 1 · [CI-4276]
> 트리거: "연차 등록 시 '다음에 지급 받을 휴가 X일 Y분'이 이상해요" + iOS 사용자

```
① 플랫폼 확인
   ├─ Android → 해당 안내 문구 미표시 (해당 없음)
   └─ iOS → ②로
   ↓
② access log에서 dry-run 응답 확인
   traceId로 postAnnualTimeOffNextAssignTime 값 확인
   ├─ postAnnualTimeOffNextAssignTime = X (큰 값, 예: 16일) 인데 화면에 작은 값 표시
   │  → iOS 매핑 실수 확정 — ③으로
   └─ postAnnualTimeOffNextAssignTime도 이상한 값 → 백엔드 계산 로직 확인 필요
   ↓
③ 표시된 값의 출처 파악
   preAmountToEarlyUse.timeOffTimeAmount 값과 화면 표시값 대조
   ├─ 일치 → iOS에서 postAmountToEarlyUse(미리쓰기 누적량)를 다음 부여 예정 연차 라벨에 매핑 중 확정
   └─ 불일치 → 다른 필드 매핑 문제 추가 조사
   ↓
④ 고객 안내
   "iOS 앱에서 '다음에 지급 받을 휴가' 표시 값이 잘못된 필드를 참조하는 알려진 버그입니다.
    다음 버전에서 수정 예정입니다. 실제 계산에는 영향 없으며, 정확한 값은 [버킷 조회로] X일입니다."
```

> 💡 **원인**: iOS에서 `postAnnualTimeOffNextAssignTime`(다음 부여 예정 연차 잔여) 대신
> `postAmountToEarlyUse`(미리쓰기 누적 사용량)를 매핑. 클라이언트 변수명은 `nextAssignTime`이었으나 매핑 실수.
> **Android는 해당 없음.** YEARLY 버킷 기준 가장 가까운 미래 부여 예정 연차를 합산한 값이 정상값.

**F3: 잔여일 소수점 이상 — 소정근로시간 혼재 확인** · 타입: Spec · [CI-4349]
> 트리거: "잔여 연차에 이상한 소수점이 있어요" / "0.002일이 어디서 났어요"

```
① operation API로 버킷 전체 조회
   GET /api/operation/v2/time-tracking/time-off/customers/{customerId}/users/{userId}
       /annual-time-off-buckets/by-time-stamp/{timeStamp}?zoneId=Asia%2FSeoul
   ↓
② 버킷별 agreedDayWorkingMinutes 값 비교
   → 값이 서로 다르면 소정근로시간 변경 이력 있음
   ↓
③ 수기 검증: 버킷별 (assignedTime ÷ agreedDayWorkingMinutes) 합산 → setScale(3, HALF_UP)
   → 화면 표시값과 일치하면 정상 동작 (스펙)
   ↓
④ 고객 안내
   "소정근로시간 변경으로 인해 연차 버킷 간 계산 단위가 달라져 소수점이 발생한 정상 동작"
   ⚠️ TT-6441: 혼재 상황 처리 개선 예정 (미해결)
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
6. 소정근로시간 변경(육아기 단축근무 등) 후 잔여 일수가 변동된 경우 → F2 참조 [CI-4025]

#### 조사 플로우

**F1: 맞춤휴가 잔여 불일치** · 타입: Data · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
> 트리거: "맞춤휴가 잔여가 이상해요"

```
① Metabase에서 부여/사용/취소 내역 확인
   부여: question/2452 → 사용/취소: question/2166
   ↓
② 부여 총량 - 사용량 - 회수량 = 잔여 계산
   ├─ 계산 일치 → 고객 오해, 내역 설명
   └─ 계산 불일치 → assign/withdrawal 테이블 직접 조회
```

**F2: 소정근로시간 변경 후 맞춤휴가 잔여 일수 변동** · 타입: Spec · 히트: 1 · [CI-4025]
> 트리거: "맞춤휴가 잔여가 이유 없이 늘었어요/줄었어요" + 소정근로시간 변경(육아기 단축근무 등) 이력이 있는 경우

```
① 해당 구성원의 근무유형 변경 이력 확인
   근무유형 변경 전후 1일 소정근로시간 차이 확인
   ├─ 소정근로시간 변경 없음 → F1 플로우로 진행
   └─ 소정근로시간 변경 있음 → ②로
   ↓
② 고객 안내 (스펙 확정, 코드 버그 아님)
   "맞춤휴가 잔여량은 내부적으로 분 단위로 관리됩니다.
    잔여 일수 표시는 조회/다운로드 시점의 소정근로시간을 기준으로 환산됩니다.
    소정근로시간이 변경되면 동일한 분 잔여라도 표시 일수가 달라집니다."
   예: 잔여 480분, 소정 480분→240분 변경 시 1일→2일로 표시 변동
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
5. 공휴일 삭제 (근로자의날 등) → `v2_customer_holiday_group`으로 대상 그룹 특정 후 Operation API `POST .../customer-holiday-groups/delete` 호출. ⚠️ 국내 법인 법정유급휴일 삭제 시 법령 위반 검토 필수 · 히트: 1 · [CI-4252] · 상세: [cookbook/holiday.md](cookbook/holiday.md)
6. 특정 유저의 휴일 조회 → operation API 사용

#### 조사 플로우

**F1: 휴일 미표시 — 매핑 확인** · 타입: Data · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
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

**F2: 공휴일(쉬는 날) 삭제 요청** · 타입: Data · 히트: 1 · [CI-4252]
> 트리거: "근로자의 날 삭제해주세요" / "쉬는 날 기본유형에서 OO 삭제해주세요"

```
① 대상 휴일 그룹 특정
   v2_customer_holiday_group WHERE customer_id = ?
   ├─ 그룹이 여러 개 → 고객에게 어떤 정책에서 삭제할지 재확인
   └─ 그룹 특정됨 → ②로
   ↓
② 국내/해외 법인 확인
   ├─ 국내 법인 + 법정유급휴일(근로자의 날 등) → 법령 위반 리스크 검토 필수
   └─ 해외 법인 또는 비법정 휴일 → ③으로
   ↓
③ Operation API 호출
   POST /action/operation/v2/holiday/customers/customer-holiday-groups/delete
   - appliedEveryHoliday: true → 매년 삭제
   - appliedEveryHoliday: false → 해당 연도만 삭제
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

**F1: 구글 캘린더 동기화 실패** · 타입: Error · 히트: 4 · [CI-4235] [CI-4262] [CI-4285] [CI-4306] · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c) · [SP팀 가이드](https://www.notion.so/04010959f43d486aaabe63a144a68339)
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
   ⚠️ **Rate limit 주의**: 한 번에 300건 이상 호출 시 Google Calendar API rate limit 발생
   ⚠️ 50건 이상 시 raccoon audit log URL 길이 초과 오류 가능 — batch 5~20건 + 2초 delay 권장
```

문의: "퇴사자 캘린더 연동 끊어주세요" / "퇴직한 구성원 구글 캘린더 연동 해제"
1. `v2_external_calendar_connection` 에서 해당 유저 연동 정보 확인
2. 연동된 `v2_oauth_user_token` 도 함께 삭제 필요 (토큰만 삭제하면 연동 항목이 남음)
3. 퇴사자 기준으로 두 테이블 모두 DELETE 처리

문의: "구글 캘린더 연동 시 권한 오류가 나요" / "insufficientPermissions 오류"
1. 유저가 캘린더 쓰기권한 없는 토큰으로 연동한 경우
2. 기존 연동 해제 후 **쓰기 권한 포함**하여 재연동 가이드

문의: "그룹 구글캘린더 연동 해제했는데 기존 일정이 아직 떠요" / "연동 해제 후 구글캘린더에 휴가 일정이 남아있어요"
1. **스펙 안내**: 연동 해제는 앞으로의 동기화만 차단. 기존 이벤트는 자동 삭제되지 않음 — 의도된 동작
2. **수동 삭제 요청 시**: cleansing API 사용 (F2 참조)

**F2: 그룹 구글캘린더 연동 해제 후 잔존 이벤트 수동 삭제** · 타입: Spec · 히트: 1 · [CI-4330]
> 트리거: "그룹 캘린더 연동 해제 후에도 구글캘린더에 휴가 일정이 남아있어요"

```
① 스펙 확인
   연동 해제 = 앞으로의 동기화 차단. 기존 이벤트 삭제 없음이 현재 스펙
   → 고객에게 스펙 안내. 수동 삭제를 원하면 ②로

② 연동 이력 조회 (calendarConnectionHistoryId 확인)
   DB: flex.v2_external_calendar_connection_history
   WHERE customer_id = ? AND connection_type = 'GROUP' AND connection_state = 'DISCONNECTED'
   → id = calendarConnectionHistoryId

③ OAuth 토큰 조회 (oauthTokenId 확인)
   DB: flex.v2_oauth_user_token
   WHERE customer_id = ? AND email = '{그룹캘린더 소유 계정 이메일}'
   → id = oauthTokenId

④ 잔존 이벤트 ID 목록 조회
   Metabase 사용 필수 (flex_calendar DB는 MCP 화이트리스트 미허용)
   DB: flex_calendar.google_calendar_event_sync
   WHERE query_key LIKE '{customerId}%' AND google_calendar_id = '{그룹캘린더ID}'
   → google_event_id 목록 추출

⑤ raccoon 브라우저 세션에서 cleansing API 호출
   POST /proxy/calendar/api/operation/v2/calendar/customers/{customerId}/events/cleansing
   {
     "oauthTokenId": <③>,
     "calendarConnectionHistoryId": <②>,
     "googleEventIds": [<④ 목록>]
   }
   ⚠️ 300건 이상 시 20건씩 배치 + 2초 delay (Google Calendar API rate limit)
```

<!-- TODO: 시나리오 테스트 추가 권장 -->

**F3: 휴가 취소 승인 후 구글 캘린더 이벤트 미회수 (버그)** · 타입: Error · 히트: 1 · [CI-4350]
> 트리거: "취소 승인 완료됐는데 구글 캘린더에 일정이 남아있어요" + Metabase에서 미연동 없음으로 표시됨

```
① calendar_event 상태 확인 (F1과 구분 포인트)
   Metabase dashboard/244 → "연동됨" 표시 = deleted_at=NULL + sync row 존재
   DB: flex_calendar.calendar_event
   WHERE id = '{event_id}'
   → deleted_at=NULL + status=CONFIRMED → 취소 승인 플로우 버그 확정
   → delete_sync 테이블에 event_id 없음도 함께 확인

② google_calendar_event_id 조회
   DB: flex_calendar.google_calendar_event_sync
   WHERE event_id IN ('{id1}', '{id2}', ...)
   → google_calendar_event_id 목록 추출

③ calendarConnectionId 조회
   DB: flex.v2_external_calendar_connection
   WHERE customer_id = ? AND calendar_type = 'GROUP'
   → id = calendarConnectionId

④ cleansing API 호출 (raccoon 브라우저 세션)
   POST /proxy/calendar/api/operation/v2/calendar/customers/{customerId}/events/cleansing
   {
     "oauthTokenId": 1,
     "calendarConnectionId": <③>,
     "calendarConnectionHistoryId": null,
     "googleEventIds": [<② 목록>]
   }
   ⚠️ oauthTokenId는 API 내부에서 사용되지 않음 — 임의값(1) 가능
   ⚠️ 300건 이상 시 20건씩 배치 + 2초 delay
```

근본 원인: 취소 승인 플로우에서 `calendar_event.deleted_at` 업데이트 로직 누락 버그 — 별도 코드 수정 필요

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
6. `CommitFailedException` + consumer group STABLE↔PREPARING_REBALANCE 반복 → `partition.assignment.strategy` 설정 변경 여부 확인. `CooperativeStickyAssignor` 단독 전환 시 대규모 group(멤버 100+, 토픽 10+)에서 rebalance 루프 발생 가능. assignor 오버라이드로 `RangeAssignor` 병행 복원 [kafka-rebalance-issue-report]

#### 조사 플로우

**F1: Kafka 컨슘 실패 — 메시지 재발행** · 타입: Error · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
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

**F2: 사용자 변경 이벤트 컨슘 실패** · 타입: Error · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)
> 트리거: `Kafka Consumer Error[userDataChangedEvent]. identities: [SimpleCustomerUserIdentity(...)]`

```
① 에러 로그에서 customerUserIdentity 추출
   ↓
② Workspace Operation API 호출
   POST /action/operation/v2/workspace/users/produce
   body: { productType: "USER", identities: [...] }
```

**F3: Consumer Group Rebalance 무한 루프** · 타입: Error · 히트: 1 · [kafka-rebalance-issue-report]
> 트리거: `CommitFailedException` 반복 + Kafka UI에서 consumer group이 STABLE↔PREPARING_REBALANCE 반복

```
① Kafka UI에서 consumer group 상태 확인
   ├─ STABLE + lag 정상 → 다른 원인 (F1~F2 시도)
   └─ PREPARING_REBALANCE 반복 → ②로
   ↓
② consumer group 멤버 수 / 구독 토픽 수 확인
   → 멤버 100+ 또는 토픽 10+ → 대규모 group 의심 → ③으로
   ↓
③ partition.assignment.strategy 설정 확인
   서비스 application.yml 또는 commons consumer.properties 확인
   ├─ CooperativeStickyAssignor 단독 → ④로 (eager→cooperative 전환 문제)
   └─ RangeAssignor 포함 → 다른 원인 (네트워크, max.poll.interval.ms 등)
   ↓
④ 즉시 대응: assignor 오버라이드 배포
   application.yml에 RangeAssignor,CooperativeStickyAssignor 병행 설정
   ⚠️ flex.v2.message-queue.kafka.consumer.properties 경로로 오버라이드
      (spring.kafka.consumer.properties가 아님)
   → 배포 후 Kafka UI에서 STABLE 안정화 확인
```

---

### 근무 기록 삭제/복구

> 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

#### 진단 체크리스트
문의: "근무 기록 삭제해주세요" / "삭제한 데이터 복구해주세요" / "휴가 기록 삭제해주세요"

**원칙: DB 직접 수정은 하지 않음. 고객이 직접 처리하도록 안내**

#### 조사 플로우

**F1: 근무/휴가 기록 삭제 요청 대응** · 타입: Data · 히트: 1 · [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c), [CI-4239]
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

→ 도메인 이해: [cookbook/fins.md#도메인-컨텍스트](cookbook/fins.md#도메인-컨텍스트)

#### 진단 체크리스트
문의: "카드 내역이 안 들어와요" / "세금계산서 연동 요청" / "이전 데이터 연동 요청" / "증빙이 시간 정책 위반으로 나와요" / "영수증 업데이트하기 클릭 시 선택 초기화돼요" / "지출결의 반려했는데 영수증 제출 화면에서 진행중으로 보여요" / "지출결의 수정 시 특정 시점 이전 영수증이 목록에 없어요"
1. 연동 대상 확인 (카드사 / 국세청 / 홈택스 등) → 금융사마다 연동 가능 범위가 다름 [CI-4179]
2. 해당 데이터 소스가 연동되어 있는지 확인 → 미연동이면 고객사에서 직접 연동 필요 [CI-4179]
3. 연동 완료 상태이면 → 어드민쉘 수동 동기화로 희망 기간 데이터 동기화 가능 [CI-4179]
4. 카드 데이터 특정 기간 이전 동기화 실패 → 승인/매입 API별 조회 가능 기간이 상이. 범위 초과 시 담당 개발자에게 별도 코드 작업 요청 필요 [CI-4179]
5. **수동 증빙 시간 정책 위반 표시** → 수동 추가 증빙(ETC spending)은 `transactedTime=null`로 전달되어 RANGE 평가에서 무조건 FAIL 처리됨 — **버그**(EP팀 수정 예정). 카드 증빙은 영향 없음(transactedTime 존재). 정책 생성 시점 이전 증빙에는 위반 미발생(활성 정책 없음) [CI-4229]
6. **지출결의 영수증 "업데이트 하기" 클릭 시 선택 초기화** → access log에서 compare API(`/api/v2/electronic-approval/documents/receipts/compare`) 응답 `list`가 빈 배열인지 확인. 빈 배열이면 Bullseye 매트릭스(`fins_spending_entire_v1`) 색인 누락 — 임형태에게 전체 고객사 재동기화 요청 [CI-4324]
7. **지출결의 반려 후 영수증 > 제출 화면에서 진행중 표시** → impact → fins Vespa 인덱스(`fins_spending_entire_v1`) 동기화 오류. DB에서 `document_id` 확인 후 operation API로 재동기화: `POST /api/operation/v3/impact/electronic-approval/customers/{customerId}/documents/{documentId}/publish` [CI-4332]
8. **지출결의 수정 팝업에서 특정 시점 이전 영수증 미표시** → 해당 사용자의 영수증 건수 확인. 현재 FE 조회 limit은 1000건으로, 1000건 초과 시 이전 영수증이 잘림 — **F4** [CI-4334]

#### 조사 플로우

**F1: 데이터 소급 동기화 요청 처리** · 타입: Data · 히트: 1 · [CI-4179]
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

**F2: 지출결의 영수증 선택 초기화 (Bullseye 색인 누락)** · 타입: Error · 히트: 1 · [CI-4324]
> 트리거: "영수증 업데이트 하기 클릭 시 선택 영수증 전부 사라짐" / "업데이트 후 다시 업데이트 하라고 함" / 다수 고객사 동시 인입

```
① access log에서 compare API 응답 확인
   대상 사용자 + ipath=receipts/compare 필터
   ├─ list 비어있지 않음 → modified/needCheck 확인 (정상 동작 여부 판별)
   └─ list=[] (빈 배열) → ②로
   ↓
② Bullseye 매트릭스 색인 이슈 확정
   임형태에게 Slack으로 연락: 해당 고객사 + "매트릭스 색인 이슈" 키워드
   ↓
③ 재동기화 요청
   임형태: fins_spending_entire_v1 재색인 + 전체 고객사 재동기화
   완료 후 고객사에 재발 여부 확인 요청
```

**F3: 지출결의 전자결재 반려 후 영수증 > 제출 화면 상태 불일치** · 타입: Data · 히트: 1 · [CI-4332]
> 트리거: "지출결의를 반려했는데 영수증 제출 화면에서 진행중으로 보여요" / 비용관리 진행상태는 반려인데 영수증 > 제출 화면만 진행중 표시

```
① DB에서 전자결재 문서 ID 확인
   SELECT document_id FROM flex_fins.spending_evidence_electronic_approval_document
   WHERE customer_id = ? AND evidence_id = ?
   ↓
② impact → fins Vespa 인덱스 동기화 오류 확정
   electronicApprovalSubmissionStatus = IN_PROGRESS 잔존 (실제 상태는 REJECTED)
   ↓
③ operation API로 수동 동기화
   POST /api/operation/v3/impact/electronic-approval/customers/{customerId}/documents/{documentId}/publish
   ↓
④ 고객 확인
   영수증 > 제출 화면 새로고침 후 상태 정상 여부 확인
```
> ⚠️ DB 테이블(`spending_evidence_electronic_approval_document`)도 IN_PROGRESS 잔존 시 → CI-4312 패턴 (Kafka 소비 실패, 별도 조사 필요)

**F4: 지출결의 수정 팝업 영수증 건수 초과로 이전 영수증 미표시** · 타입: Data · 히트: 1 · [CI-4334]
> 트리거: "지출결의서 수정 시 특정 날짜 이전 영수증이 안 보여요" / 지출결의 수정 팝업에서 이전에 첨부한 영수증이 목록에 없음

```
① 해당 사용자(member_id)의 영수증 총 건수 확인
   SELECT COUNT(*) FROM flex_fins.spending s
   WHERE s.customer_id = ? AND s.member_id = ? AND s.deleted_at IS NULL
   ↓ 1000건 초과면 F4 확정
② FE 조회 limit 초과 확정
   수정 팝업 영수증 조회 시 size=1000(Bullseye limit) → 초과 영수증은 잘림
   Bullseye(`fins_spending_entire_v1`)는 MatrixQL 기반, continuation 토큰 미지원 → 페이징 불가
   ↓
③ 한도 내 영수증인지 확인
   문제 영수증 생성일 기준으로 최신 1000건 안에 포함되는지 대조
   ↓
④ 조치: FE size 값 변경 코드 수정 필요 — 운영 수동 해결 불가
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

**F1: 워크플로우 임시저장 문서 소실** · 타입: Data · 히트: 1 · [CI-4220]
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

### 빌링 (Billing)

> 출처: [Notion 이슈 대응 공통 가이드](https://www.notion.so/flexnotion/04010959f43d486aaabe63a144a68339)

#### 진단 체크리스트
문의: "기능이 안 보여요" / "이 기능을 사용하려면 어떻게 해야 하나요"
1. raccoon > 빌링에서 고객사 구독 상태 확인
2. 특정 기능이 안 보일 때 체크리스트:
   - 해당 피처에 연관된 플랜 존재 여부
   - 피처 그룹 및 플랜 매핑 확인
   - customer feature로만 제공 가능한 피처인지 확인 (customer feature 설정 유무)
   - flagsmith 등으로 제어되는 기능인지 확인

문의: "서비스 이용이 안 돼요" / "결제했는데 기능이 잠겨있어요"
1. **구독 만료** → 구독 추가 (기본 구독 반드시 포함) + 일할 결제 필요 시 수동청구
2. **카드 미등록** → raccoon billing `force-open`으로 임시 진입 허용 → 고객에게 카드 등록 안내 → 미결제분 수동 청구
3. **미결제 차단** → raccoon에서 임시차단해제
4. **무료체험 종료 + 카드 미등록** → 구독 플랜만 추가해도 접속 차단 유지 (isShutdownActivated에서 카드 null 체크가 피처 체크보다 선행). 무료체험 종료일을 오늘 이후로 연장 → 고객 카드 등록 → 결제 생성 [CI-4291]

문의: "영수증 발급해주세요" / "크레딧 결제 영수증 주세요"
1. PG 카드 결제 영수증은 기본 제공
2. **크레딧 결제 전자 영수증은 미지원** — 고객에게 안내

### 외부 API / 데이터 통합 (OpenAPI)

#### 진단 체크리스트
문의: "OpenAPI에서 403 에러가 나요" / "OpenAPI 호출이 안 돼요" / "일부 API만 에러가 나요"
1. access log에서 응답 코드 확인 → 403이면 아래 분기, 401이면 토큰/ownerType 문제 [CI-4270]
2. 403일 때 `flexErrorCode` 확인 → `AUTHZ_403_000`이면 grant configuration 권한 세분화 이슈 [CI-4270]
3. `OPENAPI_403_001`이면 IP ACL 검증 실패 → `client-real-ip`와 허용 IP 대조
4. 일부 API만 성공하는 경우 → bypass API 목록 확인: `/v2/departments/all`, `/v2/users/employee-numbers`는 access check 없음 [CI-4270]

#### 조사 플로우

**F1: OpenAPI 403 — grant configuration 권한 세분화** · 타입: Auth · 히트: 1 · [CI-4270]
> 트리거: OpenAPI 호출 시 AUTHZ_403_000 에러, 일부 API만 성공

```
① access log에서 403 응답의 traceId 추출
   flex-app.be-access-* / customerId + responseStatus=403
   ↓
② 같은 traceId로 전체 요청 흐름 추적
   grant-configuration 조회 응답 확인
   ├─ grantConfigurationId = null → 권한 제한 없음 (다른 원인)
   └─ grantConfigurationId != null → ③으로
   ↓
③ batch-check 요청/응답 확인
   action별 allowed 값 확인
   ├─ allowed=false → grant configuration에 해당 action 미설정 또는 OpenFGA 동기화 문제
   └─ allowed=true → 다른 원인 (컨트롤러 레벨 검증 등)
   ↓
④ DB 대조: flex_authorization.flex_grant + flex_grant_authority_group
   DB에 action 존재하는데 batch-check 거부 → OpenFGA 동기화 문제
```

---

### 외부 API / 데이터 통합 (OpenAPI)

#### 진단 체크리스트
문의: "Open API 부서 조회 시 null이 나와요" / "API에서 부서 정보가 안 내려와요"
1. Open API에서 부서(departments) 필드가 null → 해당 고객사의 **조직 코드** 등록 여부 확인. 미등록이면 null 반환이 스펙 [CI-4049]
   - DB: `SELECT code FROM department WHERE id = ?` — null이면 코드 미등록
   - 참조: [Open API FAQ — 사전 코드 등록 필요](https://developers.flex.team/reference/faq-limitation#항목-별-사전-코드-등록-필요)
2. 조직 코드 등록 후에도 null → 캐시 갱신 시점 확인 (API 호출 시 실시간 반영되는지)

---

## 변경 이력

| 날짜 | 이슈 | 변경 내용 |
|------|------|----------|
| 2026-04-08 | CI-4276 | 연차: iOS 연차 미리쓰기 안내 문구 계산 불일치 — F4 플로우 신설. `postAmountToEarlyUse`(미리쓰기 누적)를 `postAnnualTimeOffNextAssignTime`(다음 부여 예정) 라벨에 매핑하는 iOS 버그. Android 해당 없음. 다음 버전 수정 예정. d:kw/d:syn 추가 |
| 2026-04-08 | CI-4280 | 계정/구성원: 온보딩 미완료로 로그인 불가 — 체크리스트 신규 항목("등록한 구성원이 로그인이 안 돼요") 추가. 초대 수락 후 비밀번호 설정 미완료 시 인증 계정 미생성, 재초대 안내 패턴. d:kw/d:syn 추가 |
| 2026-04-08 | CI-4337 | 근태/휴가: 휴가 취소 후 사용 내역 상태 "승인완료" 유지 — 체크리스트#27 추가(증상 패턴, 근본 원인 미확정). CANCEL 이벤트 DB 존재 확인, v2_user_time_off_use 물리 삭제 구조 주의사항 기록. d:kw/d:syn 추가 |
| 2026-04-08 | CI-4352 | 인사발령: 엑셀 인사발령 Flagsmith 오픈 — 진단 체크리스트(운영 요청 패턴) + F1 플로우 신설, 히트 2(CI-4313+CI-4352). Flagsmith segment 절차, 사전 안내 내용, CI-4214 버그 확인 사항 기록 |
| 2026-04-07 | CI-4351 | 교대근무: 스케줄 미노출/삭제 오해 체크리스트(#7) 추가 — `v2_customer_work_plan_template` 직접 조회 + 스코프 확인 패턴. 계정/구성원 감사로그 체크리스트에 도메인 특화 삭제 이력 cross-ref 추가. domain-map.ttl d:kw/d:syn 보강, n:CI-4351 `:shift` 등록 |
| 2026-04-07 | CI-4338 | 평가: 진행 중 구리뷰 질문/섹션명 텍스트 수정 오퍼레이션 — 진단 체크리스트 추가(텍스트 수정만 가능, SUBTITLE 타입=섹션명). cookbook/review.md SQL 템플릿(review_question UPDATE + question_log 동기화) + 과거 사례 추가 |
| 2026-04-07 | CI-4335 | 계정/구성원: 문서/개인정보 변경 알림 수신자 스펙 확인 — 기존 COOKBOOK 체크리스트(권한 기반 발송) domain-map.ttl d:st "C" 완료 처리 |
| 2026-04-07 | CI-4334 | 비용관리: 지출결의 수정 팝업 영수증 건수 초과 미표시 — 체크리스트#8 + F4 플로우 추가. Bullseye(`fins_spending_entire_v1`) MatrixQL continuation 미지원, FE size 1000 limit 구조 추가. cookbook/fins.md 구현 특이사항 + 과거 사례 + SQL 템플릿(영수증 건수 조회) 추가 |
| 2026-04-06 | CI-4330 | 캘린더 연동: 그룹 구글캘린더 연동 해제 후 잔존 이벤트 수동 삭제 — F2 플로우 신설 (cleansing API 패턴), 문의 유형 추가. cookbook/calendar.md 비즈니스 규칙(연동 해제≠이벤트 삭제) + SQL 템플릿(잔존 이벤트 조회) + 과거 사례 추가. domain-map.ttl d:kw/d:syn 추가 |
| 2026-04-06 | CI-4331 | 평가: 구리뷰 원복 및 리뷰 작성기간 수정 — 진단 체크리스트 추가(flag 설정으로 구리뷰 메뉴 재노출, review_set progress_status=IN_PROGRESS 보정). domain-map.ttl d:kw/d:syn 보강 |
| 2026-04-06 | CI-4327 | 평가: 등급 배분율 초과 시 제출 차단 설정 보정 — 진단 체크리스트 추가, F5 플로우 신설, SQL 템플릿 추가, 과거 사례 추가. cookbook/review.md 비즈니스 규칙 보강. domain-map.ttl d:kw/d:syn 추가 |
| 2026-04-06 | CI-4325 | OpenAPI: 토큰 생성 접근오류 — 설정 조회 불필요 권한 요구 버그, hotfix로 해결. 코드 수정 해결이므로 COOKBOOK 플로우 추가 없음 |
| 2026-04-05 | knowledge-cards-yj-kim + squad-tracking-2024H2 | ops-learn 일괄 갱신. 연차촉진: UTC/KST 연도 경계 누락(#6), 대표이사 등기임원(#7), 관리자 작성 기간 필터(#8) 체크리스트 추가. 근태/휴가: 1970-01-01=입사일(#20), IP제한+자동퇴근(#21), 교대근무 timeOffDeletion(#22), external_provider_event 재처리(#23), 휴가코드 삭제 스펙(#24), 연차조정 일괄취소(#25), dry-run WARN vs ERROR(#26) 추가. 교대근무-F2 SQL + 히트+1. 외부연동: 세콘 쿼리오류(#16), 캡스 중복skip(#17) 추가. 승인: 신승인 2PC 패턴 추가. 데이터추출: 퇴직자 포함 Operation API 추가. domain-map.ttl 키워드/동의어 보강 + 지식카드 소스 항목 등록 |
| 2026-04-03 | CI-4025 | 맞춤휴가: 소정근로시간 변경 후 잔여 일수 변동 — 체크리스트#6 + F2 플로우(Spec) 추가. cookbook/custom-time-off.md 도메인 컨텍스트 + 과거 사례 추가 |
| 2026-04-03 | CI-4164 | 평가: cookbook/review.md 구현 특이사항에 EvaluationStep 크론 자동 복구 + "지금 시작" vs "예약" 구분 메커니즘 추가 |
| 2026-04-02 | CI-4307 | 급여: 퇴직자 정산 주휴수당 미노출(work_record_import=NONE + 월 중도 퇴사자 dateRange 불일치) — 체크리스트#16 + F-pay-4 플로우 추가, 과거 사례 추가, glossary g:pay-16 추가. domain-map.ttl d:kw/d:syn 보강 |
| 2026-04-02 | CI-4309 | 계정/구성원: 감사로그 다운로드 체크리스트 신설 — raccoon audit operation API, 7일 제한 스펙, 이메일 비동기 발송 패턴 |
| 2026-04-02 | CI-4301 | 평가: F2(후발 추가 reviewer UserForm 미초기화) 히트 +1, 과거 사례에 CI-4301 추가 — CI-4188 동일 패턴 재발 |
| 2026-04-02 | CI-4049, CI-4212, CI-4241, CI-4256, CI-4268, CI-4271, CI-4284, QNA-1972, CI-4219, CI-4230 | 완료 이슈 10건 일괄 갱신. OpenAPI 도메인 신규 추가(CI-4049 조직 코드 미입력). 교대근무 여러날 휴가 체크리스트#6+F2(CI-4268). 계정/구성원 문서함 삭제(CI-4256)+접속기록(QNA-1972) 체크리스트 추가. 목표 엑셀 업로드 시계열 매칭(CI-4284) 체크리스트 추가. 급여 중도정산 보험료 히트+1(CI-4212), 겸직 주법인 히트+1(CI-4271). domain-map.ttl 11개 노트 verdict 확정 + 키워드/사용자표현 보강 |
| 2026-04-01 | kafka-rebalance-issue-report | Kafka 메시지 재발행: consumer group rebalance 루프 진단 체크리스트(#6) + F3 플로우 추가. Tier-2 (cookbook/time-tracking.md) 구현 특이사항 + 과거 사례 추가. domain-map.ttl `CommitFailedException`/`CooperativeStickyAssignor`/`partition.assignment.strategy`/`PREPARING_REBALANCE` 키워드 추가 |
| 2026-04-01 | CI-4288 | 인사발령: API 발령 displayOrder fallback 버그 — code-fix이므로 진단 플로우 스킵. Tier-2 도메인 컨텍스트(구현 특이사항) + SQL 템플릿(복수 직무 display_order 조회) + 과거 사례 추가. d:kw/d:syn 보강 |
| 2026-04-01 | CI-4291 | 빌링: "서비스 이용이 안 돼요" 체크리스트#4 추가 (무료체험 종료+카드 미등록). F1 히트 +1 (2), 무료체험 종료 분기 추가. 과거 사례 추가 |
| 2026-04-01 | CI-4283 | 전자계약: 계열사 서식 복제 체크리스트(#6) + F3 플로우 추가. d:kw "복제"/"duplicateTemplates", d:syn 추가 |
| 2026-04-01 | CI-4286 | 승인: F1 히트 +1 (3), APPROVAL_DOCUMENT 카테고리 추가, sync-with-approval 단계(⑥) 추가. 퇴사자 트리거 보강 |
| 2026-04-01 | CI-4279 | 급여: 원천세 신고서 전월미환급세액 미반영 — 과거 사례 추가, SQL 템플릿 추가, glossary g:pay-15 추가. domain-map.ttl d:kw/d:syn 보강 |
| 2026-04-01 | CI-4260 | 급여: 급여정산 실행 시 인가 타임아웃 → 대상자 0명 stuck — 체크리스트#15 추가. flex-permission v3.58.3(6초→10초) + hotfix #8714 수정. domain-map.ttl verdict bug-fix + closed |
| 2026-04-01 | CI-4049, CI-4270 | 외부 API(OpenAPI) 섹션 신규 추가. 부서 null(조직 코드 미등록) + 403(grantConfigurationId granular 권한 체크). domain-map.ttl :openapi d:kw 보강 + verdicts closed |
| 2026-04-02 | CI-4306 | 캘린더 연동: F1 히트 +1 (구캘 미연동 349건 재동기화, 이노바이드 199157) |
| 2026-04-03 | CI-4297 | 전자계약: placeholder 미치환(연락처 공란) — 체크리스트#8 추가, Tier-2 과거 사례/SQL 템플릿/도메인 컨텍스트 추가. domain-map.ttl d:kw 8개(placeholder/sanitize/flex-html/렌더링 등) + d:syn 3개 + d:api 추가. verdict bug + closed |
| 2026-04-01 | CI-4212, CI-4241, CI-4257, CI-4256 | domain-map.ttl d:st "C" + d:ca 일괄 설정 (이미 COOKBOOK 반영 완료된 이슈 마감 처리) |
| 2026-03-31 | CI-4270 | OpenAPI: 403 권한 세분화 진단 — 체크리스트 + F1 플로우 신설. Tier-2 openapi.md 생성 (도메인 컨텍스트 + 과거 사례 + SQL). d:kw/glossary 추가 |
| 2026-03-31 | CI-4237, CI-4246, CI-4249 | 외부 연동: 이벤트 지연+수동START 충돌 진단(#13), 수동전송 중복 START 진단(#14), 캡스 기기 변경 후 근태처리옵션 계정 재설정(#15) 체크리스트 추가. domain-map.ttl 키워드·사용자 표현 추가 |
| 2026-03-30 | CI-4236 | 알림: ops-learn — Tier-2 (cookbook/notification.md) file merge 중복 확인 SQL 템플릿 + 과거 사례 추가. domain-map.ttl `render_job`/`max.poll.interval.ms` 키워드 추가, verdict closed |
| 2026-03-31 | CI-4256 | 계정/구성원: 문서함 삭제 복구 — 진단 체크리스트 + 플로우(F3) 추가. hard delete + Envers audit 기반 복구 검토 패턴. d:kw "문서함"/"user_document", d:syn 추가 |
| 2026-03-31 | CI-4262 | 캘린더 연동: F1 히트 +1 (구글캘린더 수동 연동 365건, Operation API batch 처리) |
| 2026-04-01 | CI-4285 | 캘린더 연동: F1 히트 +1 (구캘 미연동 41건 재동기화, 알피 189332) |
| 2026-03-31 | CI-4257 | 전자계약: 선택 발송 시 미선택 CandidateUnit 삭제는 스펙 — 체크리스트#5 추가, 과거 사례 추가, d:kw/d:syn 보강 |
| 2026-03-30 | CI-4240, CI-4248 | 파일 서비스 밀림(CI-4236) 연관 다운로드 실패 패턴 통합 학습. 급여: 원천징수영수증 일괄 다운로드 실패 — 체크리스트#12 + F-pay-2 플로우 추가, 과거 사례 추가. 전자계약: 과거 사례 추가. domain-map.ttl verdict `"ops"` + `d:st "C"` 완료 |
| 2026-03-30 | CI-4248 | 전자계약: 일괄 다운로드 링크 미생성 — 진단 체크리스트 #5 추가, F2 플로우 추가 (merge 큐 지연 → 임시 파일 만료 패턴), domain-map.ttl 키워드(대량 다운로드/bulk-download/fileMergeId) + 사용자 표현 추가 |
| 2026-03-30 | CI-4247 | 급여: 원천세 신고 과거 연도 선택 불가 — Not a Bug(스펙)로 verdict 변경. Tier-2 과거 사례 갱신, domain-map.ttl verdict `"spec"` + `d:st "C"` 완료 |
| 2026-03-30 | Notion | 빌링 섹션 신규 추가. 알림 suppress list 케이스 추가. 계정 OTP 잠김(10번 제한) + 겸직 주법인 변경 진단 추가. 승인 요승설 확인/정책 복구 기조 추가. 캘린더 rate limit 경고 + 퇴사자 연동 해제 + insufficientPermissions 케이스 추가 |
| 2026-03-30 | CI-4238 | 평가: 역량 항목 미사용 시 할일 미발송 — 진단 체크리스트 추가. `useCompetencyItem=false` + COMPETENCY factor + `competencyGroupMappings=[]` → createAll 필터 버그. PR#5199 수정됨 |
| 2026-04-06 | CI-4332 | 비용관리: 지출결의 반려 후 영수증 제출 화면 상태 불일치 — 체크리스트#7 + F3 플로우 추가. impact→fins Vespa 인덱스 동기화 오류, operation API로 수동 재동기화 |
| 2026-04-06 | CI-4324 | 비용관리: 지출결의 영수증 선택 초기화 — 체크리스트#6 + F2 플로우 추가. Bullseye `fins_spending_entire_v1` 색인 누락 → compare API 빈 배열 → 전체 고객사 재동기화로 해결 |
| 2026-03-30 | CI-4226 | 계정/구성원: 정보 일괄 변경 엑셀 미리보기 중복 로우 — 진단 체크리스트 추가. 프론트엔드가 이메일 컬럼을 사번으로 잘못 파싱, 두 번 검색 결과 합산 |
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
| 2026-04-07 | CI-4338 | 평가 — 구리뷰 진행 중 질문 텍스트 수정 진단 항목 + F6 플로우 추가 |
| 2026-02-15 | 전체 | 초기 버전 — 기존 14개 노트에서 전체 추출 |
