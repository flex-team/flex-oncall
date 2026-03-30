# 김영준(Enhance) — Slack Knowledge Profile

> 생성일: 2026-03-29 | 분석 범위: 2021-01-01 ~ 2026-04-01
> 채널: #product-qna, #customer-issue, #squad-tracking, #squad-tracking-be, #pj-tracking-계획실근로, #pj-tracking-주기연장일귀속, #pj-tracking-교대근무-근무지-근무표, #pj-연장근무단위, #tf-휴일대체, #tf-tracking-reframing, #tf-보상휴가-급여-연동, #tf-미사용연차수당
> 분석 스레드: ~680건 / 전체 메시지: ~4,900건 (squad-tracking 2022-07~2026-04 보충 추가)
> 역할: Product Engineer | EP BE2 (Time-Tracking)

---

## 인물 개요

### 전문 영역

김영준(Enhance, yj.kim)은 flex Time-Tracking 백엔드 엔지니어로, 2022년부터 근무/휴가/승인/연동 도메인 전반의 서버 구현을 담당한다.

1. **근무 스케줄 리프레이밍(v3 API)**: TT 날짜 컨벤션(local-date inclusive, timestamp exclusive), dry-run/wet-run 구조, validation 타입별 DTO 설계, 타임존 3축 개념, 승인 라인 서버 소유 전환
2. **초과근무/연장근무단위**: 연장·야간·휴일 근무 계산, 3종/7종 전환, 주기연장일귀속(분배 로직), 연장근무 단위 보정 API, 마법봉(Magic Wand) API
3. **알림(Notification) 시스템**: flex-pavement-backend 알림 타입 동기화, notificationGroup 구조, 앱 푸시 버전 분기, CTA link 분기 로직
4. **세콤/캡스/텔레캅 연동**: 외부 단말기 타각 연동 구조, ODBC 드라이버, 역순 전달 처리, 중복 데이터 skip 로직
5. **휴가/승인 이벤트 구조**: `v2_user_time_off_event`, `v2_time_tracking_approval_event` 테이블 관계, 2PC 패턴(start-approval-process / produce-event), 연차촉진 배치
6. **계획실근무(work-clock)**: action 단위 API 설계, START/STOP 개념, 날짜 귀속(targetTime vs realTime), OVERLAP 에러 코드 4종 분리
7. **보상휴가-급여 연동**: Internal API 설계, 법내연장야간 3종/7종 분리, 가산율 계산, BPO 검증 전략
8. **교대근무/근무지/근무표**: 엑셀 스케줄 업로드, 근무지제한 Phase 1, 조직 선택기 empty 처리, 데이터 모델(조직:스케줄:근무조:근무지)

**주요 협업 대상**: 안희종(PM), 이지선(TT FE), 전우람(FE), 전우균(BE), 서영준(PM)

### 의사결정 원칙

- **하위 호환성 우선 — API 강업 시점에 맞춰 제거**: 기존 클라이언트가 깨지지 않도록 API 변경 시 항상 하위 호환을 고려한다. nullable 필드는 매직넘버(-1) 대신 null로 저장하고 코드에서 처리한다 — 사례: "`gpsBasedCommuteRestrictionEnabled` 필드 제거는 API 강업과 함께 진행" [출처](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1704445730442549)

- **서버가 재료를 주고, 클라가 조합**: API는 특정 UI에 종속되지 않도록 설계한다. 서버는 데이터(재료)를 제공하고, 클라이언트가 화면에 맞게 조합해서 사용한다 — 사례: "포괄승인 컨텐츠는 UI에 종속된 인터페이스 설계 지양" [출처](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1742789408347069)

- **가설 전에 데이터부터 확인**: 이슈 조사 시 가설을 세우기 전에 DB/로그/access log를 먼저 확인한다. 실제 데이터로 현상을 재현한 후에 원인을 추론한다 — 사례: "세콘 퇴근시간 00:00 조정 분석: consumer 로그가 아닌 api 인덱스 확인 필요" [CI-3979](https://linear.app/flexteam/issue/CI-3979)

- **BPO 검증 → 대고객 오픈 (단계적 롤아웃)**: 새 기능은 BPO(급여 대행사)에서 먼저 검증한 후 대고객 오픈한다. BPO가 자체 로직으로 검산하므로 이상 시 잡을 수 있다 — 사례: "보상휴가-급여연동 페이롤 플래그: BPO 계정 오픈 → 1달 검증 → 대고객 오픈" [출처](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1732783162875339)

- **ERROR vs WARN — 차단 여부로 판단**: 로그 레벨과 validation 레벨 모두 "차단이 필요한가?"를 기준으로 구분한다 — 사례: "dry-run WARN vs ERROR: WARN은 게시 허용, ERROR만 차단" [CI-3862](https://linear.app/flexteam/issue/CI-3862)

- **플래그 기반 점진적 오픈**: 기능 오픈은 피처 플래그로 제어하고, 소프트오픈/하드오픈 단계를 거친다. 플래그 동기화가 완료될 때까지 레거시 코드를 유지한다 — 사례: "연장근무단위 `tt_exceeded_work_unit` 플래그, 66개사 사용 후 아카이브"

### 응대 패턴

1. **CS 문의 — "스펙인지 버그인지 먼저 판단"**
   - 전형적 질문: "X가 안 돼요", "왜 이렇게 나와요?"
   - 전형적 응답 흐름: 현상 확인 → DB/로그 데이터 조회 → 스펙이면 "이것은 스펙입니다" + 근거 설명 → 버그이면 "확인됨" + 해당 이슈 생성/핫픽스 배포

2. **외부 시스템 문제 — "저희 쿼리가 아닙니다"**
   - 전형적 질문: "세콘에서 쿼리 오류가 나요", "오라클 연동이 안 돼요"
   - 전형적 응답 흐름: 에러 로그 확인 → 플렉스 측 API/데이터 정상 확인 → 외부 시스템 문제로 판단 시 "저희가 가이드하는 쿼리가 아닌 것으로 보입니다" 안내

3. **동료 API 설계 문의 — "원칙 기반 답변"**
   - 전형적 질문: "이 필드 제거해도 되나?", "dry-run에 이 값도 필요한가?"
   - 전형적 응답 흐름: 하위 호환 영향 확인 → 클라이언트 사용 여부 확인 → 원칙(서버=재료, 클라=조합) 기반 판단 제시

4. **데이터 확인 순서 — "DB → ES → 로그"**
   - 알림: `notification_deliver` → SES 피드백 로그
   - 휴가 조회 안 됨: ES 동기화 확인 → 수동 동기화 트리거
   - 세콘 데이터: 메타베이스 쿼리로 확인 (question/3565)

---

## 도메인별 지식

### 알림/Notification (pavement)

#### 알림 설정 동기화 — 신규 알림 추가 시 기존 설정 무시

**스펙/규칙**
- `user_notification_type_setting` 테이블은 비활성화한 값만 저장
- 신규 알림 타입 추가 시 해당 타입에 대한 레코드 없음 → 기본값(활성화)으로 발송
- admin(`flex-raccoon.grapeisfruit.com/notifications/home`)에서 동기화 버튼 실행으로 해결

**자주 오는 케이스**
- "알림 그룹 이메일 껐는데 새 알림 온다" → 신규 알림 타입 동기화 필요

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1658370289917169), [스레드2](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1657691389529679)

#### 워크플로우/휴가 참조자 앱 알림 미발송

**스펙/규칙**
- `FlexTimeTrackingTimeOffRegisteredMessageContext`의 메시지 채널이 슬랙만 설정되어 있었음
- 워크플로우 참조 알림도 동일 이슈 (`FlexWorkflowTaskApproveMessageContext` 등)
- 해결: 해당 메시지 컨텍스트 코드에 채널 직접 추가

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1657691389529679)

#### 알림 발송 중복 — Consumer Pod 재시작

**스펙/규칙**
- 출퇴근 알림이 동일 내용으로 2회 발송, 로그에는 1회만 기록
- 원인 추정: Consumer pod 재시작 시 Kafka 메시지 중복 처리
- 발송 로그 미기록 시 정확한 원인 확정 불가

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1657590558082759), [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1658144017017879)

#### 포괄임금 승인 알림 Integer/Long 타입 혼동

**스펙/규칙**
- Kafka 메시지에 Long으로 직렬화된 값이 역직렬화 시 Integer로 처리 → null
- 해결: nullable 처리, Long 타입 통일

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1658144017017879)

#### 앱 푸시 알림 버전별 분기

**스펙/규칙**
- 수신 token의 앱 버전 확인 → 해당 버전 맞는 알림 템플릿 선택 발송
- CTA link에 `iosMinVersion`, `andMinVersion`, `fallbackScheme` 3개 queryParam으로 버전 분기
- `fallbackScheme` 없으면 업데이트 유도 바텀시트(`route/update`)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1673838829070379)

#### 휴가 확인하기 이메일 버튼 동작 분기

**스펙/규칙**
- 휴가 등록 알림(참조): `[확인하기]` → 할 일(To-do)로 이동
- 휴가 승인 알림(참조): `[확인하기]` → 홈피드로 이동
- CTA 코드: `flex.time-tracking.time-off.request.approve.refer`

**출처**: [CI-3914](https://linear.app/flexteam/issue/CI-3914)

#### 알림 수신 여부 조사 패턴

**스펙/규칙**
```sql
select nd.*, n.notification_type
from notification_deliver nd
left join notification n on nd.notification_id = n.id
where nd.receiver_id = {userId}
and n.notification_type = '{type}'
and n.db_created_at >= '{date}';
```
- `notification_deliver`에 데이터 없음 → 발송 자체 안 된 것
- 데이터 있는데 미수신 → SES 피드백 로그 확인

**출처**: [CI-3910](https://linear.app/flexteam/issue/CI-3910)

#### 공지사항 알림 — 작성자 본인에게 미발송

**스펙/규칙**
- 공지사항 작성자에게는 알림이 발송되지 않음 (의도된 정책)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1664243000000000)

#### 알림 메시지 한국어 조사 처리

**스펙/규칙**
- FE에는 `josa` 라이브러리 사용
- BE에서도 조사 포함한 알림 메시지 전송 시 당근마켓 오픈소스 `betterkoreankotlin` (Analyzer.kt) 활용 가능
- FE Josa.js 본체는 `jongseong` 라이브러리

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1667823051903769)

#### 휴가 참조자 알림 — 승인 완료 시 "등록했어요" 오는 이유

**스펙/규칙**
- 승인 완료 시 참조자에게 "등록했어요" 알림이 가는 것은 버그가 아닌 임시 구현
- **원인**: 뉴승인 이전에는 참조자 알림 없었음 → 뉴승인 이후 옵션 생기면서 추가. 당시 "승인 완료" 별도 참조 알림이 없어서 "휴가 사용 시 나가는 참조 알림"과 같이 발송
- **해결 방향**: 참조자용 승인완료 알림(FT-11053) 별도 정의 및 추가
  - 근무 승인 완료 참조자용 Notion: 753a4326bb26457a81d59c115a3a6f36
  - 휴가 승인 완료 참조자용 Notion: 03137bf8513249ee81311de68bf11763
  - 휴가 취소 승인 참조자용 Notion: d53bb483c5a2472f986f168923e099b3

**자주 오는 케이스**
- "휴가 승인 완료됐는데 참조자에게 '등록했어요' 알림이 왔다" → 임시 구현 결과. FT-11053으로 개선 예정

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1722833239852389)

#### 근태승인 알림 — 그룹 메일 수신 케이스

**스펙/규칙**
- 본인이 알림을 꺼둔 상태에서 이메일이 오면 그룹 메일 수신 여부 먼저 확인
- 메일 발송 로그가 없다면 그룹 메일로 받은 것인지 확인 필요

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1658144017017879)

#### Slack 유저 연동 미등록 알림 오류

**스펙/규칙**
- 신규 입사자나 슬랙 재연동 미완료 유저에서 `user_not_found` 오류
- 테이블: `flex_user_slack_user_mapping` 확인

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1667783626385599)

#### 새로운 소식 로딩 오류 — requestTypeNames 빈 배열

**스펙/규칙**
- pavement-api에서 `requestTypeNames`가 빈 배열인 `notification_deliver` 레코드로 인해 API 500 오류 발생
- 안드로이드 특정 앱 버전에서 비어있는 값이 들어오는 케이스
- 진단 쿼리: `json_contains(n.message_data_map, json_array(), '$.requestTypeNames') and json_length(...) = 0`

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1669000000000000)

---

### 휴가/연차 (time-off)

#### 연차촉진 UTC/KST 연도 경계 버그

**스펙/규칙**
- 연차촉진 배치: 매일 오전 8시(KST) 동작, DB에 UTC 저장
- 1/1 08:00 KST = 12/31 23:00 UTC → 2026년 조회 시 전년도 UTC 건 누락
- 오래된 버그 (특정 배포로 발생한 것 아님)

**자주 오는 케이스**
- "2026년 연차촉진 안 보임" → 2025년으로 조회하면 확인 가능

**출처**: [CI-3809](https://linear.app/flexteam/issue/CI-3809), [CI-3907](https://linear.app/flexteam/issue/CI-3907)

#### 연차촉진 관리자 작성 기간 필터

**스펙/규칙**
- 완료된 촉진이 있을 때 관리자 작성 기간 필터 적용 → 미표시
- 2021년 의도된 스펙, 버그 아님
- 코드: `AnnualTimeOffPromotionHistoryServiceImpl.kt#L80-L81`

**출처**: [CI-3777](https://linear.app/flexteam/issue/CI-3777)

#### 연차촉진 워크플로우 태스크 — 템플릿 이름 문제

**스펙/규칙**
- `TIME_OFF_BOOST` 태스크 작성 요청 시 v1에서 수정한 템플릿 이름이 그대로 발송 제목으로 사용
- 확인 쿼리: `select * from customer_workflow_task_template where task_type='TIME_OFF_BOOST' and name != '스마트 연차 사용 계획'`

**출처**: [FT-4129](https://linear.app/flexteam/issue/FT-4129)

#### 연차촉진 boostHistory status 미업데이트

**스펙/규칙**
- 작성 완료 후 `boostHistory`의 `status`/`contextStatus`가 `PENDING_WRITE`/`SHOULD_MANAGER_WRITE`에서 업데이트 안 되는 케이스
- 할일 쪽 도메인 업데이트 누락 시 발생
- 이미 발생한 데이터는 재시도하면 정상 처리

**변경 이력**
- 2023-04-05: 버그픽스 배포

**출처**: [FT-4165](https://linear.app/flexteam/issue/FT-4165)

#### 대표이사 연차촉진 — 미지급 연차정책

**스펙/규칙**
- 등기임원 → 연차 지급 대상 아님 → 촉진 결과 없음
- 정책 변경 이전에 생성된 이력만 존재

**출처**: [CI-3932](https://linear.app/flexteam/issue/CI-3932)

#### 휴가 개요 연차 잔여 -3일 표시 원인

**스펙/규칙**
- 현재 시점에서 당겨쓴 휴가 + 올해 받을 예정인 월차에서 미리 쓴 경우 → 부여량보다 사용량이 많아 음수 표시
- 0.5일이 다음 연차 버킷에서 빌려쓸 때 생기는 구조적 어색함 (TT-7958 관련)
- 월차의 미리쓰기가 휴가 개요에 들어가는 이유

**자주 오는 케이스**
- "연차 잔여가 -N일로 표시된다" → 당겨쓰기(월차 미리쓰기)로 인한 정상 동작. [TT-7958](https://linear.app/flexteam/issue/TT-7958) 참조

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1724930538783579)

#### 맞춤휴가 n년차마다 지급 정책

**스펙/규칙**
- "n년차마다 지급" 정책은 없음
- "n년차에 지급"하는 정책은 있음
- "n년차부터 매년 반복지급"하는 정책도 있음
- "n년차부터 매년 반복지급 but 입사일에" → **불가** (현재는 회계일로만 동작)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1727255617412049)

#### 맞춤휴가 최소/최대 일수

**스펙/규칙**
- flex 제품 정책상 최대 1년 (1.0과 동일)
- 조회: 메타베이스 `question/1309` (분 단위)
- 366일 이상 필요 시 두 번에 나누어서 사용하도록 안내
- 관련 코드: `TimeOffRegisterDayMaxSizeLimitVerifier`

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1677141672682839), [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1675700000000000)

#### 반려 휴가 미표시 — UI 조회 범위 이슈

**스펙/규칙**
- 반려된 휴가가 "사용 기록"에서 미래 날짜면 안 보임
- "반려기록 보기" 토글이 "사용 기록" 탭에 종속

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1681439317784179)

#### 휴일에 등록된 휴가 차감 처리

**스펙/규칙**
- 옵션 "기간 내 휴일 포함 등록": 휴일에 등록된 휴가도 수량에서 차감
- 휴가 버킷(지급량)은 차감되지 않음

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1706248492184899)

#### 휴가 코드 삭제 시 등록된 휴가 취소

**스펙/규칙**
- 교대근무 관리에서 기사용 휴가 코드 삭제 → 등록된 휴가 모두 취소 (의도된 스펙)

**출처**: [CI-4047](https://linear.app/flexteam/issue/CI-4047)

#### 연차 조정 일괄 취소

**스펙/규칙**
- side peek `...` 아이콘에서 일괄 취소 기능 추가 (CI-3923 배포 완료)

**출처**: [CI-3923](https://linear.app/flexteam/issue/CI-3923)

#### 휴가 사용 내역 조회 기간 6개월 제한

**스펙/규칙**
- 날짜 피커가 최대 6개월 범위로 제한
- 종료일을 먼저 이전 날짜로 설정 → 시작일 조정으로 과거 기간 조회 가능
- IA 개선 작업 이후 UX 개선 예정

**출처**: [FT-4109](https://linear.app/flexteam/issue/FT-4109)

#### 휴가 사용 내역 `to` 값 버그

**스펙/규칙**
- 휴가 데이터 저장 시 `to` 값이 다음날 `00:00:00`으로 저장
- 조회 시 `to` 파라미터가 `2021-12-31 00:00:00`으로 넘어가면 12/31 데이터 미조회
- PR #4609 핫픽스로 해결

**출처**: [FT-4196](https://linear.app/flexteam/issue/FT-4196)

#### ES 동기화 누락으로 구성원 휴가 내역 미노출

**스펙/규칙**
- 신규 입사 등으로 유저가 ES에 등록되지 않은 경우 휴가 사용 내역에서 조회 불가
- 운영 대응: 해당 유저 ES 동기화 처리 후 재조회

**출처**: [FT-4284](https://linear.app/flexteam/issue/FT-4284)

#### 맞춤휴가 정책 중복 생성 버그

**스펙/규칙**
- core `user-search` 온보딩 시 디폴트 맞춤휴가정책 중복 생성
- 확인: `v2_customer_time_off_form`에서 `category='COMPENSATION'` group by customer_id having count > 1

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1735798101715889)

#### 연차 회계연도 컬럼 ISO 8601 truncated format

**스펙/규칙**
- `--01-01` 형식 (ISO 8601 truncated date format)
- DB에 더블쿼터가 같이 들어가는 경우 있음

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1675907951911009)

#### 연차 operation API customer 범위 버그

**스펙/규칙**
- `/annual-time-off-adjust-assigns/by-until-date/{untilDate}` API가 유저 기준이 아닌 customer 기준으로 데이터 조회
- 수정: PR #8437 — user 기준으로 필터링 추가

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1722000000000000)

#### 보상휴가 데이터 조회 — Redash/Metabase 쿼리

**스펙/규칙**
- Redash query #507: 부여 내역 (사용 시각 기준)
- Metabase question #1309: 잔여 시간 확인 (사용하려는 날짜로 조회)
- 잔여 시간 = 부여 - 사용 이력으로 계산

**출처**: [FT-4585](https://linear.app/flexteam/issue/FT-4585)

---

### 근무기록/출퇴근 (work-record/commute)

#### 해외 근무자 타임존 이슈

**스펙/규칙**
- 귀속일 계산이 UTC 또는 서버 타임존 기준, 현지 타임존 미적용
- 타임존이 한국이 아닌 경우 휴가 등록 시 날짜 불일치 발생 (182건 확인)
- FE에서 클라이언트 타임존으로 YEAR-MONTH를 해석하면 1~12월이 다르게 보이는 문제 → KST 기준 고정 필요

**의사결정 배경**
- Jira DC-131 "시간 표현에 있어서의 다중 timezone 관련 정책 수립" 생성
- 사용자가 할 수 있는 유일한 방법: 머신을 서울 타임존으로 바꿔두고 근무등록 (불편한 해결책)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1674090139935679), [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1673838829070379)

#### 근무유형 적용일 1970-01-01 = 입사일

**스펙/규칙**
- `1970-01-01` = 입사일로 처리
- 그룹 입사일 기준 근무 조회는 지원하지 않음

**출처**: [CI-3773](https://linear.app/flexteam/issue/CI-3773), [CI-3902](https://linear.app/flexteam/issue/CI-3902)

#### 자동 퇴근 처리 스펙

**스펙/규칙**
- 출근 기록 후 n시간 이후 자동 퇴근 처리 (n 옵션: 소정근로시간 이후, 해당 귀속일 자정, 타각 무효처리 기준 20시간, 회사 설정값, 유저 설정값 등 논의 중)
- 자동 퇴근 시 근무지 제한 스펙과의 상호작용 미정의

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1717000000000000)

#### IP 제한 + 자동퇴근 상호작용

**스펙/규칙**
- 자동퇴근 시 근무지 판단 안 함 → IP 제한 설정 있어도 자동퇴근 통과
- 코드: `UserWorkClockStopByReserveRequestServiceImpl.kt#L142-L143`

**출처**: [CI-3501](https://linear.app/flexteam/issue/CI-3501)

#### 근무 기록 없을 때 이른출근 판단 불가

**스펙/규칙**
- 스케줄 게시 전 출근 타각 → 근무 없으므로 이른출근 판단 불가 → 출근 시간 그대로 입력

**출처**: [CI-3767](https://linear.app/flexteam/issue/CI-3767), [CI-3866](https://linear.app/flexteam/issue/CI-3866)

#### 반복근무 삭제 후 자동근무 미노출 — 0 vs null

**스펙/규칙**
- 반복근무 삭제 시 0 대신 null로 저장 → 자동근무 적용 조건 미충족
- 처리: 해당 기록 직접 DB 삭제

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1677765199704479)

#### 근무정책 삭제 후 근무 블록 비활성화

**스펙/규칙**
- Operation API 미지원 → DB 직접 삭제
```sql
DELETE FROM v2_user_work_record_event_block WHERE id = {id} AND user_id = {userId};
```

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1678094602766659)

#### 근무 조회 속도 개선 — 캐싱 전략

**스펙/규칙**
- `CustomerWorkRuleRepository.findByIdInAndActiveTrue` 단일 요청 451회 호출
- requestScope 캐싱: 11.96s → 5.57s~8s
- 향후 redisCacheManager 전역 캐시 검토

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1749086456522369), [TT-14144](https://linear.app/flexteam/issue/TT-14144)

#### Dry-run만 하고 확정 안 한 경우 근태기록 손실

**스펙/규칙**
- 모바일 앱에서 퇴근 타각 시 dry-run만 하고 확정(work-end) API를 호출하지 않은 것
- dry-run: `POST /action/v2/time-tracking/users/{userIdHash}/work-end/dry-run`
- 실제 퇴근: `POST /api/v2/time-tracking/users/{userIdHash}/work-end`
- 체크용 API를 별도로 분리해야 한다는 논의 (endpoint `/action/.../work-record-check`)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1674000000000000)

#### 근무 타각 이벤트 타입 확인

**스펙/규칙**
- 앱에서 '13:00에 근무 끝내기' vs '지금 이 시간에 끝내기' 버튼 각각 다른 이벤트 타입 전송
- 타각 타입 확인: Metabase question #1727 (파라미터: customerId, date_from, date_to, email)

**출처**: [FT-4615](https://linear.app/flexteam/issue/FT-4615)

#### 동료 캘린더에서 기본 근무 미노출

**스펙/규칙**
- 기본 정책은 캘린더에 안 보이는 것이 스펙 (모바일에선 노출 — 일관성 없음)
- 동료 캘린더 설정에서 팀 내 공유 또는 전사 공유로 변경 필요

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1685690138455219)

#### v2_customer_work_rule의 customer_id = -1 데이터

**스펙/규칙**
- 2022-06월 초중순에 생성된 근무 유형들의 customer_id가 -1로 잘못 설정
- PAC(PersistenceAccessControl)에서 validAccess로 처리되어 에러 발생
- 수정 쿼리: `UPDATE v2_customer_work_rule cw SET customer_id = (SELECT cwr.customer_id FROM v2_customer_work_record_rule cwr WHERE cw.customer_work_record_rule_id = cwr.id) WHERE customer_id = -1`

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1723000000000000)

---

### 계획실근무 (planned-actual-work / work-clock)

#### 계획실근무와 실시간 출퇴근 기록의 분리 구조

**스펙/규칙**
- 계획실근무(인정근무, recognized work)는 관리자가 승인하는 "어떤 시간을 인정할 것인가"
- 실시간 출퇴근 기록과 별도 레이어
- `beforeDecidedWorkRecordBlocks`: 승인 콘텐츠에서 초과근무 시간대 표시용

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1764041338381289)

#### work-clock API: action 단위 설계

**스펙/규칙**
- `dryRunToReplaceWorkClockEvents` / `executeToReplaceWorkClockEvents`
- `days` 배열 size=1 제약 (하루 단위 원자적 교체)
- `EVENT_TIME_OUT_OF_RANGE`: 이벤트 시각이 날짜 범위 밖일 때

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1764075322790859)

#### 위젯 START/STOP 개념

**스펙/규칙**
- START/STOP ≠ 출근/퇴근 (특정 근무 단위 시작/종료)
- 위젯 권한: granted-departments / granted-users 단위

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1767165436846199)

#### 전날 귀속 — targetTime vs realTime

**스펙/규칙**
- targetTime: 귀속 대상 날짜 기준 시각 (표시용)
- realTime: 실제 이벤트 발생 시각
- 00:00:00은 당일 귀속 (이전 코드에서 전날로 귀속하는 버그 있었음)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1772522353427029), [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1773106226140889)

#### PAST_DAY_OVERLAP / FUTURE_DAY_OVERLAP 에러 코드

**스펙/규칙**
- 4종류: `PAST_DAY_OVERLAP`, `FUTURE_DAY_OVERLAP`, `PAST_DAY_OPEN_PACK_OVERLAP`, `FUTURE_DAY_OPEN_PACK_OVERLAP`
- 클라이언트가 에러 종류에 따라 다른 안내 메시지 표시 필요

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1773314797374619)

#### work-clock 이벤트 수신 흐름 전체 구조

**스펙/규칙**
1. 외부(위젯/단말/API) → 이벤트 수신
2. `UserWorkRecordEventSource` 출처 태깅
3. beforeRegister (사전 검증)
4. 근무지제한 검증
5. 기록 저장 + 상태 기록
6. 계획실근무 승인 연계

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RSJM1S9K/p1773928337755169)

---

### 초과근무/연장 (exceeded-work)

#### 여러날 포괄근무 버그 — 주기 경계 초과 승인

**스펙/규칙**
- 선택적 근무에서 주기 승인 시 말일에 몰아주는 로직
- 10월 근무 수정인데 11월 포괄초과승인 발생 → 근무 주기가 월 경계를 넘는 경우 정상 동작

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1705563203300129)

#### 선택적 근무 주말 근무 계산 방식

**스펙/규칙**
- 계산 방식: `FLEXIBLE_CALENDAR_DAY_BASED` — 일수 기반으로 계산
- 주말에도 근무를 채울 수 있음
- 관련 Notion: https://www.notion.so/flexnotion/a426141a41ac417b844a220d2001a562

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1722577683845809)

#### 선택적 근무 연장 승인 버그 — 잔존 조건 로직

**스펙/규칙**
- 여러날 근무 등록 시 선택적 근무 승인 로직이 제거되었으나 반복근무 승인 체커에 조건 로직 잔존
- 관련 클래스: `WorkScheduleOverWorkApprovalChecker`, `WorkScheduleRegardedOverWorkApprovalChecker`
- 전체 오픈 플래그 켜다가 말았음 → prod에서 확인 필요

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1717000000000001)

#### 단시간근로자 휴무일 연장근무 판단 기준

**스펙/규칙**
- 기준: `(주 소정근로시간 / 5)` 초과 시 일 연장
- 고용노동부 가이드: 8시간 기준
- 코드: PR `flex-timetracking-backend/pull/7185`

**출처**: [CI-4048](https://linear.app/flexteam/issue/CI-4048)

---

### 연장근무단위 (exceeded-work-unit)

#### 마법봉(Magic Wand) API

**스펙/규칙**
- 타입별 제공: 추천휴게 마법봉 ≠ 연장근무 보정 마법봉
- 일괄 마법봉 제거 (예측 불가능한 동작)
- 법정 초과 마법봉은 클라 로직으로 구현

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C08SEPBTF2M/p1710000000000000)

#### 올림/내림 처리 정책

**스펙/규칙**
- 마법봉: 항상 내림
- 최소 입력 단위 미달: 무조건 내림
- 최소 입력 시간 미달: 무조건 내림 (올림 없음)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C08SEPBTF2M/p1710000000000001)

#### 보정 로직 순서

**스펙/규칙**
- 주기연장 → 일연장 순
- 타임블록 내림차순
- 편집 시도한 날짜에 대해서만 보정
- 휴가와 휴게는 건드리지 않음

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C08SEPBTF2M/p1710000000000002)

#### 위젯 stop → 확정 모달 퇴근 시각 조정

**스펙/규칙**
- 보정된 시각으로 확정 모달 진입
- `get-adjusted-work-stop-time-candidates` API: `[{ adjusted, from, to }, ...]`
- 최대 조회 범위: 20시간

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C08SEPBTF2M/p1710000000000003)

#### 플래그 및 출시 결과

**스펙/규칙**
- 플래그: `tt_exceeded_work_unit`
- 2025-08-14 기준: 66개사 사용, 156개 근무유형 적용
- 신규 온보딩 초기값: 설정 없음

**변경 이력**
- 2025-08: 출시 후 2주, 66개사 사용 확인. 채널 아카이브

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C08SEPBTF2M/p1723600000000000)

---

### 승인/워크플로우 (approval/workflow)

#### 휴가 DB 테이블 구조 및 승인 상태 흐름

**스펙/규칙**
- 휴가 등록 시 `v2_user_time_off_event`에 1건 INSERT
- 승인 상태는 `v2_time_tracking_approval_event`에서 조회: `target_event_category = 'TIME_OFF'`, `target_event_id = v2_user_time_off_event.id`
- 상태 전이: REGISTER → APPROVE → CANCEL / DECLINE (update가 아닌 누적 INSERT 방식)
- 승인권자 조회: `time_tracking_approval_event.taskKey + customerId` → `workflow_task` → `workflow_task_stage.reviewer_targets`

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1658395078774879)

#### 신승인 start-approval-process / produce-event 2PC 패턴

**스펙/규칙**
1. `startWithoutEventProduce` → `/start-approval-process`
2. `produceStartEvent` → `/start-approval-process/produce-event`
- produce-event 실패 시 `/rollback-started` 호출 필수
- 비정상 데이터 복구: `approval_process` + `approval_replacement_target` soft delete + TT 보상 처리

**자주 오는 케이스**
- 퇴직자 승인자 교체 → 승인에서 200인데 TT에서 400 → `/produce-event`가 미호출

**출처**: [CI-3951](https://linear.app/flexteam/issue/CI-3951)

#### 워크플로우 ALREADY_WRITTEN_TASK — 연차촉진 문서 중복

**스펙/규칙**
- 첫 요청 타임아웃 실패 → 두 번째 요청 시 "이미 작성한 문서" 오류
- 해결: 워크플로우에서 태스크 삭제 후 재처리

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1688432599250049)

#### 워크플로우 자동승인 — 1차 조직장 누락

**스펙/규칙**
- 1차 조직장이 퇴직/휴직 → stakeholder resolve 시 아무도 내려오지 않음
- 승인 정보 전부 삭제 후 유저가 직접 요청을 날린 상태
- 진단: templateKey로 workflow task를 찾아 stakeholder 상태 확인

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1660000000000000)

#### 휴가취소 승인 이벤트 중복 적재 버그

**스펙/규칙**
- 승인된 휴가 취소 시 `v2_time_tracking_approval_event`에 CANCEL 중복 적재
- 확인: `group by target_event_id having count(1) >= 3`

**변경 이력**
- 2023-02: `cancelRegisteredTimeOff` 로직 수정

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1675752277684569)

#### 휴가취소승인 복합 버그 (2023-02)

**스펙/규칙**
- 취소 승인 후 상태가 "취소승인 완료"가 아닌 "승인 완료"로 변경 (FE optimistic update 문제)
- 취소 승인 후 화면 클릭 안 됨 (FE deprecated 문서 판단 로직 누락)
- 취소 승인 후 사용 내역에서 상태가 `APPROVAL_COMPLETED` → `TIME_OFF_CANCELED`여야 함
- 참조 승인만 있는 휴가 취소 시 `CANCEL_APPROVAL_WAITING` → `CANCEL_APPROVAL_COMPLETE`여야 함 (참조승인 즉시 취소)
- **핵심 원인**: `/time-off-uses/search` ES 조회 API에서 취소 후 상태 미업데이트 (WF와의 타이밍 이슈)
- **수정**: PR flex-timetracking-backend#4135

**변경 이력**
- 2023-02: 위 5종 버그 수정 배포

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1676274512350169)

#### 승인 컨텐츠 nullable 버그 (workMinutes 없던 구버전)

**스펙/규칙**
- `workMinutes` 필드가 없던 시절(v0 버전) 생성된 승인 문서에서 null 발생
- 휴게시간 포함된 경우 end-start가 workMinutes가 아닐 수 있어 타입 체크 필요
- 해결: end-start로 채워서 문서 볼 수 있게 처리

**자주 오는 케이스**
- "과거 승인 문서가 열리지 않는다" → v0 버전 구 문서의 workMinutes null 문제 확인

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1712000000000000)

#### 과거근무 수정 승인 — 삭제도 변경에 포함

**스펙/규칙**
- 삭제도 "변경"에 포함됨 (팀 전원 동의)
- `WorkScheduleMultiDayPastRecordEditApprovalChecker`는 eventBlock만 봐서 비어있는 날로 수정 시 발생 안 함
- 관련 티켓: [TTB-964](https://linear.app/flexteam/issue/TTB-964)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1725846491684129)

#### 휴일 근무 승인 — 휴무일(토요일) 적용 제외

**스펙/규칙**
- 근무 정책의 "휴일 불가" 설정은 토요일(휴무일)에 해당하지 않음
- 휴일 근무 승인도 휴무일(토요일)에는 적용 안 됨 (둘 다 동일 스펙)

**자주 오는 케이스**
- "토요일 근무하는데 승인이 안 요청된다" → 휴무일은 휴일 근무 승인 대상이 아님

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1712000000000001)

#### Dry-run 성공 후 실제 근무 등록 실패 → 고아 태스크 발생

**스펙/규칙**
- dry-run으로 워크플로우 태스크/할일 생성 후 실제 근무 등록 실패(휴게 부족 등) → 고아 태스크 남음
- raccoon에서 해당 `taskKey`를 플로우 측 할일 제거 처리

**출처**: [FT-4171](https://linear.app/flexteam/issue/FT-4171)

---

### 세콤/캡스/외부연동 (external-integration)

#### 세콘(SICON) 연동 패턴

**스펙/규칙**
- 퇴근 → 출근 역순 전달 가능 → 퇴근미타각으로 노출
- 재전송해도 중복 데이터로 skip
- 비활성화 중 보낸 데이터는 소급 반영 안 됨

**해결 패턴**
- 역순 전달: 관리자 수동 근무 기록
- 특정 유저 동기화 안 됨: 세콘 사번 설정 오류 확인 필요

**출처**: [CI-3793](https://linear.app/flexteam/issue/CI-3793), [CI-3700](https://linear.app/flexteam/issue/CI-3700), [CI-3861](https://linear.app/flexteam/issue/CI-3861)

#### 세콥/캡스 타각 확인 화면 — dry-run 기반 구조

**스펙/규칙**
- 타각 확인(확정하려는) 화면은 dry-run 기반으로 렌더링
- 확정 후 화면은 `current-status` API 기준 (별도 스냅샷 없음)
- 어제 데이터를 확정하면 어제 시점의 "확정하기" 화면은 더이상 볼 수 없음
- BE 설계: 확정'하려는' 화면만 제공 / PD 요구사항: 확정'하려는' + 확정'된' 화면 구분

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1712000000000002)

#### 세콘 퇴근 시 퇴근시간 00:00 조정

**스펙/규칙**
- 해당 날 종일휴가가 있는 경우 → 00:00으로 조정
- 코드: `WorkClockTimeAdjuster.kt#L127`
- 조사 시 consumer 인덱스가 아닌 api 인덱스 확인

**출처**: [CI-3979](https://linear.app/flexteam/issue/CI-3979)

#### 세콘 쿼리 오류 — 저희 쿼리가 아닌 경우

**스펙/규칙**
- `syntax error at or near "DUPLICATE"` → 세콘 내부 쿼리 오류
- 대응: "저희가 가이드하는 쿼리가 아닌 것으로 보입니다"

**출처**: [CI-3953](https://linear.app/flexteam/issue/CI-3953)

#### 세콤/캡스 연동 가이드

**스펙/규칙**
- 고객사 사전 작업: 세콤/캡스 시스템에 플렉스 사번 연동
- flex 준비: 접속 계정 생성
- 세콤/캡스는 근무지 제한 영향 없음 (슈퍼패스)
- 세콤링크 = 설치형 세콤 프로그램의 외부전송DB 기능, 플렉스는 세콤매니저 ODBC만 지원

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1704962414234469)

#### TELECOP 외부 연동 — 타입 불일치 버그

**스펙/규칙**
- `TelecopEventEntity`의 terminalId/employeeId: String 선언이지만 실제 데이터 Int
- `v2_customer_external_provider`에 `work_clock_register_enabled` 플래그

**출처**: [PR](https://github.com/flex-team/flex-work-event-transmitter-backend/pull/98)

#### 슬랙 출퇴근과 IP 제한

**스펙/규칙**
- 슬랙은 사용자 IP를 전달하지 않음 → IP 제한 기능 구현 불가
- 슬랙: 출퇴근 트리거 역할만 (근무지 제한과 분리)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1704354493881509)

---

### 근무정책/설정 (work-rule/config)

#### 기본 근무 공유정책(usage_visibility) 기본값 변경 이력

**스펙/규칙**
- `v2_customer_work_form`의 `usage_visibility` 필드 제어
  - `NONE`: 공유 안함
  - `WITHIN_TEAM`: 팀 내 공유
  - `ALL`: 전사 공유
- 2023-01-31 마이그레이션: 기본 근무(`primary=true`)의 `usage_visibility`를 전사 공유 → 공유 안함으로 일괄 변경
- 변경 후 12개 고객사가 직접 설정 변경
- 구글 캘린더 연동에도 영향 (기본근무는 구캘 공유 대상에서 제외)
- 진단 쿼리: `select * from flex.v2_customer_work_form where primary = true and usage_visibility != 'NONE' order by db_updated_at desc`

**자주 오는 케이스**
- "기본 근무가 캘린더에 안 보인다" → `usage_visibility='NONE'` 확인 후 공유 설정 변경 안내

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1675155867812069)

#### forceMinimumRestTime 초기값 버그 (2023-01)

**스펙/규칙**
- 신규 회사 생성 시 기본 근무에서 "최소 연속 휴식 강제화" 옵션이 DB에는 false로 저장되나 UI에는 켜진 것처럼 보이는 버그
- 원인: FE fallback 값이 false(꺼짐)지만 저장 시 요청에 true로 전송 (UI 켜진=DB false 역전)
- 초기 회사 생성 메서드: `CustomerWorkRecordRuleUpdateServiceImpl#resisterNewDefault` → false 저장이 문제
- 수정: PR flex-timetracking-backend#3991

**변경 이력**
- 2023-01: 버그 수정

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1675066527721699)

#### 코어타임 일별 변경 가능 여부

**스펙/규칙**
- 현재 제품에서는 불가 (일마다 다른 코어타임 미지원)
- 구조적으로는 가능하도록 되어 있음
- 니즈가 간간이 인입되나 매우 적은 양 → 대응 계획 없음

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1723081655349849)

#### 근무 주기(WorkSchedulePeriod) 생성 기준

**스펙/규칙**
- 디폴트: 전체 기간(1970/1/1 ~ 9999/12/31)으로 설정, 근무유형 적용 기간에 따라 중간에 주기가 나뉨
- 주기 중간에 근무 유형이 바뀔 수 있으므로 "같게 보일 뿐" (항상 같아야 하는 것 아님)
- 1970부터 만들어 두는 이유: 입/퇴사, 휴직, 삭제 등 이벤트마다 근무유형기간 조절이 아닌 후처리로 동작
- 관련 PR: https://github.com/flex-team/flex-timetracking-backend/pull/8750

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1726192435420839)

#### 대시보드 타 customer 근무 유형 캐싱 버그

**스펙/규칙**
- 근무 유형 API 조회 시 `customerIdHash`를 `workspace-users/me` 응답에서 가져오는데, 이전에 내려온 다른 고객사의 값이 캐싱되어 타 고객사 근무 유형이 조회되는 버그
- 진단: `workspace-users/me` 응답의 `currentUser.user.customerIdHash`가 올바른지 확인

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1723772794699099)

#### 동일 이메일 재입사 유저 처리

**스펙/규칙**
- 퇴사 후 동일 이메일로 재입사 시 user가 새로 생기는 것이 올바른 처리 (입사일 변경으로 재입사 처리하면 안 됨)
- 입사일 변경으로 처리 시: 변경된 입사일 기준으로 월차/연차/근무 모두 재계산되어 제품 내 일관성 깨짐
- 퇴직 취소 처리된 케이스(특수)는 입사일 변경으로 재입사 처리됨
- 진단 SQL: `select customer_id, id as user_id, email from user where email like '%{email}%'`

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1724810363275659)

#### IP 제한 감사 로그

**스펙/규칙**
- 근무 위젯/스케줄 dry-run, wet-run 시 IP 제한으로 실패할 경우 감사 로그 추가
- 위젯에만 먼저 추가 (내근무 등록은 미적용)
- `AccessControlDeniedException` 에러 로그로 확인

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1712000000000003)

#### 회사 휴일 테이블 구조

**스펙/규칙**
```sql
v2_customer_holiday_group     -- 휴일 그룹
v2_customer_holiday           -- 실제 휴일 날짜 (group_id 연결)
v2_user_holiday_group_mapping -- 유저-그룹 매핑
v2_time_tracking_user_alternative_holiday_event -- 개인 대체휴일
```
- 조회: 매핑 → 그룹 → 휴일 순서 JOIN
- 한국 공휴일은 테이블에 저장 안 됨. 비활성화하는 경우 등에만 생성. 코드로 계산

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1675139131108269), [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1674500000000000)

#### 휴직 기간 근무기록 처리

**스펙/규칙**
- tracking-user에서 휴직 상태는 '현재' 기준만 가능 (기간 불가)
- 현재 기준 → 모든 근무 기록을 하루 종일 휴가처럼 처리

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1688433816996049)

#### GPS 근무 제한

**스펙/규칙**
- 권한자(최고관리자) 타인 근무 등록·수정 시 GPS 영향 안 받음
- 본인 근무 시에는 받음
- 근무예약은 등록 시점에 GPS 판단 완료, 예약 시간 도달 시 재확인 안 함

**출처**: product-qna QNA-GPS

#### 입사예정자 근무유형 이슈

**스펙/규칙**
- 입사예정자는 근무유형 설정 화면 미노출 → 삭제 가능 → DB `active=true` 복구 필요

**출처**: product-qna QNA-1382

---

### 리프레이밍 (reframing)

#### TT 날짜 컨벤션: local-date inclusive, timestamp exclusive

**스펙/규칙**
- local-date 파라미터: 양 끝 inclusive
- timestamp 파라미터: 끝점 exclusive

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1717341464000000)

#### 리프레이밍 API 버전 규칙: `/v3/`

**스펙/규칙**
- 신규 API 전부 `/v3/`로 시작
- 하위 호환 필요 없는 새 인터페이스

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1711516049000000)

#### dry-run/wet-run 응답 설계

**스펙/규칙**
- dry-run: `validationResults` 안에 근무/휴가 validation + verification 포함
- wet-run: 등록된 근무 주기 기록 + 승인 ID 목록
- lookup 응답: wet-run 결과와 동일
- dry-run과 wet-run은 abstract class 기반 템플릿 메서드 패턴

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1718622461000000)

#### validation 타입별 DTO 매핑

**스펙/규칙**

| validation 타입 | DTO |
|---|---|
| `LACK_OF_REST_MINUTES` | `LongValueWorkScheduleRegisterValidationDto` |
| `EXCEEDED_MAX_STATUTORY_TOTAL_WORK_MINUTES` | `LongValueWorkScheduleRegisterValidationDto` |
| `WORK_SCHEDULE_NOT_ALLOWED_WORKPLACE_IP` | `StringListWorkScheduleRegisterValidationDto` |
| `WORK_SCHEDULE_TIME_BLOCK_INVALID_WORKDAY` | `WorkScheduleRecordWorkScheduleRegisterValidationDto` |
| `EXCEEDED_USAGE_LIMIT` | `ExceededUsageLimitWorkScheduleRegisterValidationDto` |
| `TIME_OFF_BALANCE_INSUFFICIENT` | `TimeOffAmountWorkScheduleRegisterValidationDto` |
| `*` (default) | `DefaultWorkScheduleRegisterValidationDto` |

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1719499291000000)

#### 타임존 3축 개념

**스펙/규칙**
1. 내가 보는 시간대 (UI 표시)
2. 근무 계산 시간대
3. 근무 기록 등록 시간대

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1701676276000000)

#### 승인 라인 서버 제공 방향

**스펙/규칙**
- 기존: FE가 `approvalPolicyKey`로 직접 조회
- 변경: 서버가 승인 라인 생성 → FE는 표시만
- `approvalPolicyKeys` 대신 `approvalPolicies` 사용 (메모 필수 포함)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1721301010000000), [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1731040529844849)

#### 서머리 API 필드 매핑

**스펙/규칙**

| 필드 | 계산 방식 |
|---|---|
| `totalTimeOffMinutes` | paid + unpaid |
| `totalOverWorkingMinutes` | 여러 초과근무 타입 합산 |
| `requiredLegalWorkingMinutes` | 합의근무 - 유급휴일 |
| `totalActualWorkingMinutes` | 실제 근로 시간 |

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1719480031000000)

#### '전체 시간' 개념 정의

**스펙/규칙**
- 전체 = 목표(기본+야간+휴가) + 비목표(초과 중 야간 제외 8가지)
- 휴가 사용 시 최대 근무 버킷 증가 가능 (52h → 63h)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1721704433000000)

#### 근무/휴가/휴게 중첩 검증 — 서버 이관

**스펙/규칙**
- 예전: `[근무][휴게][근무]` 블록 패턴 저장 가능
- 현재(리프레이밍 이후): `[근무[휴게]][근무]` 형태. 휴게가 근무 안에 포함되어야 함
- 이 검증 로직이 클라이언트단에만 있다가 리프레이밍부터 서버에 추가됨

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1729218619446319)

#### v3 dry-run 후 v2 wet-run 혼용 버그

**스펙/규칙**
- v3에서 dry-run만 하다가 v2 API로 근무 입력하는 버그
- `clientMappingId`가 같다는 것이 원인
- TTB-1078로 스펙 변경 (중첩된 블록 병합 후 전송)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1729820844325629)

#### 종일 휴가 타임존 처리

**스펙/규칙**
- 종일 휴가 블록 DTO의 `startTimestamp`, `endTimestampExclusive`는 종일 휴가일 때 `undefined`
- 해결: `startTimestamp: { zoneId: string; timestamp?: number }` 형태로 zoneId만 전달 가능
- `timezoneAtRegistration`은 optional이며 종일 휴가일 때 존재

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1736746589494719)

#### `getUserWorkingPeriodByDateAt` API

**스펙/규칙**
- `/api/v2/work-rule/users/{userIdHash}/working-periods/by-date/{date}` (구 API, 호출 없음)
- 새 API: `getUserWorkingPeriodByDateAt` — plain date + timezone 파라미터로 근무주기 조회
- `registerWorkScheduleV3`의 `zoneId`: 근무 블록에는 사용 안 하고 휴가 블록 등록 시 사용

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1736746589494719)

---

### 보상휴가-급여연동 (compensatory-payroll)

#### 초과근무 Internal API 설계

**스펙/규칙**
- Request: `timestampRange` + `exceededWorkCalculationPeriod`(nullable)
- Response: `dailyResults` + `periodResults`
  - `exceededWorkTimes`, `deductedExceededWorkTimesByComprehensiveContract`, `recognizedExceedWorkTimes`, `compensatoryTimeOffAssignTimes`

**의사결정 배경**
- 페이롤에서 초과근무 산정주기를 요청 파라미터로 받지 않기로 결정 (하위호환 유지)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1732783162875339)

#### 3종 법내연장야간 분리 계산

**스펙/규칙**
- 법내연장야간 = 야간 + 법내연장으로 분리 계산 (가산율 다름)
- 7종 → 3종 변경 시 TT에 `법내야간` 타입 신설

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1731991283015599)

#### 가산율(additionalRate) null 처리

**스펙/규칙**
- persistence: null 가능, domain: null 불가
- null이면 `DefaultCompensatoryExceededWorkTimeOverPayPercent` 참조

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1733386552851339)

#### 보상휴가 초과부여 상태 체크 버그

**스펙/규칙**
- 부여 가능 여부 체크 시 서로 다른 기간 범위 비교 (버그)
- 코드: `UserCompensatoryTimeOffAssignUpdateService.kt#L690-L712`
- 해결: PR `flex-timetracking-backend/pull/11799`

**출처**: [CI-3858](https://linear.app/flexteam/issue/CI-3858)

#### 3종→7종 일괄 변경 (4845건)

**변경 이력**
- 2025-01-21: `TYPE_3+포함` → `TYPE_7+미포함` 일괄 변경, 12개사 제외
- 핫픽스 후 2개사 추가 보정

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1737444707297019)

#### 주기연장 연장야간 분해 버그

**스펙/규칙**
- 법내연장야간 → 주기연장-야간으로 분해 시 야간 시간 증발
- 2025-01 PR #9553 수정

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1736732747099019)

#### 휴일연장 포괄승인 타입 분리

**스펙/규칙**
- `ExceededWorkType` vs `ComprehensiveContractWorkType` 분리 (PR #10087)
- 3종: 3개 내림, 7종: 7개 내림
- 계약/초과/인정초과 모두 0이면 미노출

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1742789408347069)

#### 휴일야간 누락 버그

**스펙/규칙**
- 가산율: 휴일×1.5, 휴일야간×1.5, 휴일연장×0.5, 휴일연장야간×0.5
- 버그: 휴일야간×1.5 누락 → PR #10155 수정 (영향 8명)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1743399449866129)

#### 보상휴가 지급 내역 다운로드 엑셀

**스펙/규칙**
- 근무유형 단위, 동일 주기면 한 줄
- 가산율: 다운로드 시점 반영 (시계열 미관리)
- 시간 단위: 소수점 둘째 자리

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1734312821697149)

---

### 휴일대체 (alternative-holiday)

#### 대체 휴일 vs 휴일 대체 — 용어 정의

**스펙/규칙**
- **휴일 대체(holiday replacement)** (근로기준법 제55조제2항): substitute holiday — 법정 공휴일에 근무하고 다른 날 쉬는 것 (약정 기반). **TT 미지원**
- **대체 공휴일(대체 휴일)** (관공서 공휴일에 관한 규정 제3조): observed holiday — 공휴일이 주말과 겹칠 때 월요일로 이동
- **보상휴가(compensatory time off)**: 연장/야간/휴일 근무에 대한 보상으로 주는 휴가
- **휴무일**: 일반적으로 '쉬는 날'이지만 '근로기준법상의 휴일'은 아님
- TT 입장: 법정휴일/약정휴일 구분 불필요. 다 "근로기준법상 휴일"로 처리
- alternative는 두 의미가 혼재하여 사용 지양
- 구글 캘린더에서는 `Day off in lieu` 표현 사용

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1725000000000000), [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1722257124499499)

#### date-attributes API의 dayOffs 버그

**스펙/규칙**
- 주휴일 대체 날은 포함되지만 쉬는날(공휴일) 대체 날은 미포함
- 캘린더 초기 날짜가 아닌 클릭 시점 날짜 기준으로 조회

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07KV2K8KAN/p1730165138735279)

#### 모바일 휴일대체 API 가이드

**스펙/규칙**
- 대체 휴일 신청 가능 여부: `date-attributes` dry-run만으로 충분
- 전체 정보 필요 시: `original-holiday-info` 별도 호출

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07KV2K8KAN/p1731304764097569)

#### 여러 날 등록 시 휴일대체 중복 (TT-11671)

**스펙/규칙**
- 여러 날 등록 시 휴일대체 이벤트 중복 저장 → 취소 여러 번 필요
- 근본 원인: `TimeTrackingApprovalPostActionEventConsumer` 멱등 처리 누락
- 해결: 모두 취소 후 새로 등록

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07KV2K8KAN/p1732847325790259), [TT-11671](https://linear.app/flexteam/issue/TT-11671)

#### 휴일대체 플래그 및 테이블 구조

**스펙/규칙**
- 플래그: `tt_members_alternative_holiday` (모바일 별도 플래그 불필요)
- 신청 테이블: `v2_time_tracking_user_alternative_holiday_request`
- 이벤트 테이블: `v2_time_tracking_user_alternative_holiday_event` (`submission_type`: SELF/ADMIN)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C07KV2K8KAN/p1733377100353749)

#### 휴일대체 기간 설정 변경 제약

**스펙/규칙**
- 공휴일 기간 단축: 어려움
- 주휴일 기간 연장: 가능 (기존 6일 → 전후 2주)

**출처**: [CI-3897](https://linear.app/flexteam/issue/CI-3897)

---

### 주기연장일귀속 (period-over-daily-attribution)

#### 소프트오픈/하드오픈 전략

**스펙/규칙**
- 소프트오픈(11/24): 신규 고객만 자동 반영
- 하드오픈(1/31): 전체 2109개 customer 일제 마이그레이션
- 적용일: 02/01, 근무주기 월~일이면 하루만 주기 짤림 가능

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09S8UXL5R7/p1762929324754999), [스레드](https://flex-cv82520.slack.com/archives/C09S8UXL5R7/p1769391478938179)

#### 마이그레이션 방법

**스펙/규칙**
- 소프트오픈: `distribute_period_over_to_day = true` 변경 (미니 한정)
- 하드오픈: Operation API 호출 (`newApplyStartDate = 2026-02-01`)
- 미니 구별: `customer.product_code = 'LEAF'`

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09S8UXL5R7/p1763441273140379)

#### 핵심 계산 케이스 — 주기연장 분배

**스펙/규칙**
- 특정 일의 기본근무보다 주기연장이 많아서 과거로 넘치는 케이스
- 주기연장 분배 시 법내연장도 분배 대상으로 포함
- 분배 순서: 뒤에서부터 배분, 항목별 순서 없음

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09S8UXL5R7/p1763458912843759), [PR](https://github.com/flex-team/flex-timetracking-backend/pull/11384)

#### DB 스키마: apply_start_date_for_distribute_period_over

**스펙/규칙**
- `v2_customer_work_rule` 테이블:
  - `distribute_period_over_to_day`: Boolean
  - `apply_start_date_for_distribute_period_over`: Date (null이면 전체 기간)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09S8UXL5R7/p1769390875571679)

#### Operation API — 적용시작일 변경

**스펙/규칙**
- `CustomerWorkRuleMigrationOperationController`
- `customerWorkRuleIds: null` → 전체 변경
- `customerWorkRuleIds: [1729,1730]` → 특정 유형만 변경

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09S8UXL5R7/p1764134271358859)

---

### 교대근무/근무지/근무표 (shift-work/workplace)

#### 교대근무 엑셀 스케줄 업로드 시 연차 미반영

**스펙/규칙**
- 엑셀 업로드 시 다른 코드는 정상이나 연차만 미반영
- 해결: PR `flex-timetracking-backend/pull/11874`

**출처**: [CI-3998](https://linear.app/flexteam/issue/CI-3998)

#### 교대근무 스케줄 게시 — 기존 휴가 있는 날 오류

**스펙/규칙**
- `v2_user_shift_schedule_draft`의 `time_off_deletion` 필드에 삭제 예정 휴가 포함
- 해결: `time_off_deletion = '[]'` 업데이트

**출처**: [CI-3997](https://linear.app/flexteam/issue/CI-3997)

#### dry-run WARN vs ERROR — 게시 차단 여부

**스펙/규칙**
- ERROR: 게시 차단, WARN: 게시 허용
- FE 파서 변경으로 WARN도 차단된 이력 (hotfix: `flex-frontend-apps-time-tracking/pull/2101`)

**출처**: [CI-3862](https://linear.app/flexteam/issue/CI-3862)

#### 근무지 제한 승인 templateKey 누락 (뉴승인 전환 후)

**스펙/규칙**
- 뉴승인으로 전환 후 근무지 제한 승인에 templateKey가 없다는 오류 발생
- dev에서 먼저 발견 → prod 영향 여부 확인 필요
- 승인 생성 시 `approvalProcess`에 templateKey가 포함되어야 함

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1712000000000004)

#### 근무지제한 Phase 1 — 조직 선택기 empty 처리

**스펙/규칙**
- 서버에서 `null`을 받으면 무소속 구성원 포함 전체 구성원에 적용
- 빈 배열(empty list)로 저장 (전체 조직 ID 리스트 저장하면 조직 변경 시 자동 반영 안 됨)
- 필터(발라내는 것) vs 대상 선택(선택하는 것)은 다른 맥락

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1762764213234929)

#### 교대근무 데이터 모델

**스펙/규칙**
```
조직 : 근무스케줄 = 0~1 : 1
근무지 : 근무스케줄 = 0~1 : N
근무지 : 근무조   = 0~1 : N
근무조 : 구성원   = 1 : N
```
- 근무지 0개인 스케줄/근무조: 모든 근무지에서 쓸 수 있어서 '공용'으로 표기

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1769601596042849)

#### workplaceId 타입 불일치 이슈

**스펙/규칙**
- Core 쪽 API: `workplaceId`가 idHash 값
- Tracking 쪽: 기존에 그냥 id(int toString)
- FE에서 TT의 workplace 관련 API를 활용하도록 처리

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C09RPL4P0D9/p1769880015030400)

---

### API/아키텍처 (api/architecture)

#### 모바일 BFF nullable 필드 500 에러

**스펙/규칙**
- BFF에서 non-null 선언 → TT가 null 반환 → 500
- 입사 전 기간 조회 시 발생

**출처**: [CI-4051](https://linear.app/flexteam/issue/CI-4051)

#### TT 엑셀 다운로드 타임아웃

**스펙/규칙**
- 내부 API 호출 시 HTTP client 타임아웃 초과
- 해결: 별도 retrofit 빈 + 타임아웃 연장 (PR #11985)

**출처**: [CI-4055](https://linear.app/flexteam/issue/CI-4055)

#### 휴가사용내역 ES 동기화 — produce/consume 타이밍

**스펙/규칙**
- 트랜잭션 커밋 전 produce → consumer가 stale 데이터 참조
- 해결: transactional outbox 패턴 (`flexMessageRepository.insertAll`)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1675764455728029)

#### API 서버 리소스 튜닝 (2024-08)

**스펙/규칙**
- 기존: replica 8, cpu 8, ram 5, db pool 60
- 실험: replica 16, cpu 4, ram 5, db pool 30
- 최종 적정값: replica 12, cpu 4, ram 5, db pool 40 (총 480 connections)
- KEDA 스케일링: 최소 6대 → 최대 16대

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1723400000000000)

#### Google Calendar 동기화 아키텍처

**스펙/규칙**
- `COMMAND_CALENDAR_SYNC` 이벤트 → 2개 컨슈머 병렬 처리
  - `GoogleCalendarSyncEventConsumer`: 구글 배치 API → callback에서 `v2_external_calendar_event_map` 저장/삭제
  - `FlexCalendarSyncEventConsumer`: `v2_time_tracking_flex_calendar_event_map` 테이블에 매핑 저장
- history 테이블 추가 시 tracking 쪽도 함께 작업 필요

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1724000000000000)

#### Virtual Thread 성능 테스트 (2024-09)

**스펙/규칙**
- dev 환경 TT API에서 VT 20/50/100 VUser 테스트
- 결과: 메모리 사용 약간 감소, 스루풋 약간 감소 — 극적인 차이 없음
- 2024-09-10 Prod TT API에 VT 적용
- Notion: [Virtual Thread 성능 테스트](https://www.notion.so/flexnotion/Virtual-Thread-9672093cec854ec18df67df8fcec279c)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1725500000000000)

#### WorkClockStatusChangedEvent SSE enrichment

**스펙/규칙**
- 이벤트: `team.flex.work-clock.status.changed.v1`
- SSE에 current-status API 응답과 동일한 payload 담아서 발행 (별도 API 호출 불필요)
- 메시지 역전 방지: 이벤트 `time` 필드에 서버 기준 시각 담아 클라이언트에서 오래된 이벤트 무시

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1726000000000000)

#### Liquibase changelog lock 해제

**스펙/규칙**
- lock 걸렸을 때: 직접 `DATABASECHANGELOGLOCK` 테이블에서 lock 해제
- `ALGORITHM=INPLACE, LOCK=NONE` 불가 시 → `varchar(256)` 이상으로 컬럼 사이즈 확보

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1718175148068109)

#### MySQL 8 버전업 후 reserved word 충돌

**스펙/규칙**
- MySQL 8 업그레이드 후 `over`가 예약어 → SQL syntax error 발생
- 수정: 필드명 변경 또는 backtick 처리

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1727000000000000)

#### PAC(PersistenceAccessControl) 예외 처리 개선

**스펙/규칙**
- PAC 에러 발생 시 `validAccess`로 처리되어 에러 없이 통과되는 케이스 존재
- R(Read)만 에러 로그 찍고 CUD는 적용 시점부터 바로 차단하는 방향으로 개선
- 2024-08-08 PAC 재적용 완료

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1723200000000000)

#### Redis → RDB 이관 (2025)

**스펙/규칙**
- Redis 데이터를 RDB로 이관 작업 진행 중 (2025-06)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1750035039130539)

---

### 기타 (misc)

#### 근무/휴가 ERD 색상 가이드

**스펙/규칙**
- 휴가: 초록색, 근무: 노랑색, 승인: 분홍색

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1675080142414959)

#### Mockito nullable 인자 처리

**스펙/규칙**
- Kotlin + Mockito: nullable 파라미터에는 `anyOrNull()` 사용

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1676022185912129)

#### 보상휴가 초과근무 유형 정렬 순서

**스펙/규칙**
- 야간 → 연장(법정 내) → 연장·야간(법정 내) → 연장 → 휴일 → 연장·야간 → 연장·휴일 → 휴일·야간 → 연장·휴일·야간

**출처**: product-qna QNA-676

#### 캡스 수동 동기화

**스펙/규칙**
- 동기화 시점 상태 기준으로 실시간 근무(시작→종료) 처리
- 이미 등록 또는 위젯 진행 중이면 미반영
- 하루치 10분 내 처리

**출처**: product-qna QNA-688

#### Slack-휴가 유형 연동

**스펙/규칙**
- 휴가 유형 구분 없이 '휴가'로만 표시 (민감한 휴가 유형 보호)

**출처**: product-qna

---

## 의견 충돌 이력

### 승인 라인 데이터 소유권 (FE vs 서버)

- **맥락**: 기존에 FE가 `approvalPolicyKey`로 승인 라인을 직접 조회하여 렌더링하던 구조
- **김영준 입장**: FE에서 승인 스킵 위험이 있으므로 서버가 승인 라인을 소유해야 한다
- **상대 입장**: FE 자율성 유지 주장
- **결론**: 서버 소유로 변경. FE는 표시만 담당
- **출처**: [스레드](https://flex-cv82520.slack.com/archives/C05PQ22NQS1/p1721301010000000)

### 포괄승인 UI 인터페이스 설계

- **맥락**: 서버에서 승인 컨텐츠 전달 시 UI 구조를 서버가 인지해야 하는 상황
- **김영준 입장**: 서버는 UI 종속 인터페이스를 지양하고, 도메인 구조에 맞는 인터페이스를 제공해야 한다
- **상대 입장**: 클라이언트가 도메인 로직을 갖기 꺼림
- **결론**: 도메인 구조에 맞는 인터페이스 제공 방향으로 합의
- **출처**: [스레드](https://flex-cv82520.slack.com/archives/C07NB6AU1M5/p1742789408347069)

### 일괄 마법봉 제거

- **맥락**: 연장근무 단위 조정 시 일괄 마법봉(타입 구분 없는 조정) 기능 존재
- **김영준 입장**: 일괄 마법봉은 예측 불가능한 동작이므로 제거해야 한다. 타입별 독립 제공이 맞다
- **상대 입장**: 편의성 측면에서 일괄 조정이 유용할 수 있다
- **결론**: 일괄 마법봉 제거. 타입별 독립 제공으로 변경
- **출처**: [스레드](https://flex-cv82520.slack.com/archives/C08SEPBTF2M/p1710000000000000)

### 휴일대체 API 통합 vs 분리

- **맥락**: `date-attributes`와 `original-holiday-info`를 항상 조합해서 사용
- **김영준 입장**: 서버는 재료를 주고 클라가 조합하는 원칙에 따라 현행 분리 유지
- **상대 입장**: 항상 두 API를 함께 호출해야 하므로 통합이 편리
- **결론**: 현행 유지하되 향후 통합 검토. "당장 이번에 해야 하는 것은 아님"
- **출처**: [스레드](https://flex-cv82520.slack.com/archives/C07KV2K8KAN/p1731304764097569)
