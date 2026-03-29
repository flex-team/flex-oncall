# 김영준(Enhance) — Slack Knowledge Profile

> 생성일: 2026-03-27 | 분석 범위: 2022-01-01 ~ 2025-01-01
> 채널: #customer-issue (CRU35U9FC), #squad-tracking (CK7EUDG4S), #product-qna (C01G5AFKNFL)
> 분석 스레드: ~120개 / 추출 카드: ~100개
> 역할: Backend Engineer | EP BE2 (Time-Tracking)

---

## 인물 개요

### 전문 영역

김영준(Enhance, yj.kim)은 flex Time-Tracking 백엔드 엔지니어로, 2022년부터 근무/휴가/승인/연동 도메인 전반의 서버 구현을 담당한다. 주요 전문 영역:

1. **알림(Notification) 시스템**: flex-pavement-backend 알림 타입 추가/동기화, notificationGroup 구조, raccoon 어드민 동기화 도구
2. **세콤/캡스/텔레캅 연동**: 외부 단말기 타각 연동 구조, ODBC 드라이버, 다법인/다단말 처리
3. **GPS/IP 근무지 제한**: 근무지 제한 검증 로직, 최고관리자 예외, 캡스+IP 병합 검증
4. **휴가/승인 이벤트 구조**: `v2_user_time_off_event`, `v2_time_tracking_approval_event` 테이블 관계, 취소 승인 상태 관리
5. **초과근무/연장**: 연장·야간·휴일 근무 계산, 3종/7종 전환, minutesToHours 소수점 처리
6. **자동근무기록(위젯)**: 실시간 출퇴근 위젯, 자동퇴근(20시간), 세콤 타각 연동 구조

**주요 협업 대상**: 안희종(PM), 이지선(TT FE), 전우람(FE), 시재희(BE), 서영준(BE)

### 의사결정 원칙

1. **스펙과 버그를 빠르게 구분**: customer-issue 인입 시 "이것은 스펙", "버그 확인됨" 판단을 명확히 하고 즉시 안내. 모호한 경우 access log → DB 확인 → 원인 특정 순서

2. **반복 운영 작업은 제품화 방향 제시**: 알림 동기화 수동 작업을 raccoon 어드민 동기화 버튼으로 개선, 운영 처리 대신 제품 기능으로 해결하는 방향 지속 제안

3. **외부 연동 스펙은 명확히 문서화**: 세콤/캡스 연동 구조, 방화벽 설정, 커넥션 수 등 고객사 문의가 반복되는 사항을 스레드에 명확히 정리하고 Notion 문서로 이관

4. **소수점/타입 이슈 주의**: `minutesToHours()` 소수점 버림, Long vs Integer deserialize 버그 등 숫자 처리에서 발생하는 미묘한 버그를 반복 경험

### 응대 패턴

1. **즉시 원인 파악**: customer-issue 메시지 인입 후 수 시간 내 원인 특정 → 픽스 또는 스펙 안내 패턴 반복
2. **DB/어드민 도구 활용**: raccoon 어드민, SQL 직접 조회로 사용자별 알림 설정 확인, 운영 데이터 파악
3. **재현 조건 구체화**: "세콤 연동 후 위젯 미허용 근무유형이면 타각이 draft로 저장" 등 구체적 재현 조건을 제시하여 CS팀이 자체 해결 가능하도록 안내

---

## 지식 카드

### 1. 알림 시스템 (Notification)

---

#### 알림 그룹과 알림 설정 동기화 메커니즘

**스펙/규칙**
- 알림 설정은 개별 알림 타입별로 저장되며, `flex_pavement.user_notification_type_setting` 테이블에 disabled한 채널만 저장
- 사용자가 '근무/휴가' 그룹의 이메일 설정을 끄면, 해당 notificationGroup에 속하는 **모든 개별 알림**에 `disableChannel=EMAIL` 추가
- **신규 알림 타입이 추가되면 이 DB에 값이 없어서 기본값(발송)으로 동작** → 기존에 이메일을 끈 사용자에게도 신규 알림이 발송됨
- 동기화 방법: 신규 알림 추가 시 raccoon 어드민(`/notifications/home`)에서 동기화 버튼으로 기존 그룹 설정값을 기반으로 개별 알림 설정 동기화

**변경 이력**
- 2022-07: 참조자 알림(`FlexTimeTrackingWorkRecordStageInProgressReferMessageContext`) 신규 추가
- 2022-07-21: raccoon 어드민에 동기화 버튼 추가
- 2022-07: 알림 설정을 개별 타입이 아닌 그룹 설정으로 변경하는 방향 논의됨

**자주 오는 케이스**
- "이메일 알림을 껐는데 새로운 알림이 온다" → 신규 알림 타입 추가 후 동기화 미실행. raccoon 어드민에서 동기화 실행
- "알림 설정에 없는 그룹(PAVEMENT 그룹)의 알림을 끌 수 없다" → UI에서 설정 가능한 그룹: `TIME_TRACKING`, `WORKFLOW`, `DIGICON`, `YEAR_END_SETTLEMENT`, `REVIEW`. PAVEMENT 그룹은 웹 UI 설정 화면 없음

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1658370289917169)

---

#### 할 일(PAVEMENT) 알림과 웹 알림 설정 UI 미지원

**스펙/규칙**
- 할 일(Todo) 관련 알림 3종: 생성(`FLEX_PAVEMENT_TODO_CREATED`), 완료, 반려
- 할 일 알림의 notificationGroup은 `PAVEMENT`
- 웹 알림 설정 UI에서 `PAVEMENT` 그룹은 설정 불가 (TIME_TRACKING, WORKFLOW, DIGICON, YEAR_END_SETTLEMENT, REVIEW만 지원)
- 이메일 전체 비활성화해도 `FLEX_PAVEMENT_TODO_CREATED` 알림은 계속 발송됨
- 해결 방향: 알림 그룹을 WORKFLOW로 변경하거나, 해당 사용자 DB에서 직접 제외

**자주 오는 케이스**
- "이메일 알림을 껐는데 할 일 알림이 계속 온다" → PAVEMENT 그룹은 설정 불가한 구조적 제약

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1657099850036069)

---

#### 신규 알림 추가 시 참조자 알림 분리 원칙

**스펙/규칙**
- 근무 승인 요청 알림: 승인권자 대상(`StageInProgressMessageContext`)과 참조자 대상(`StageInProgressReferMessageContext`) 분리
- 참조자 알림에는 메일 채널 없이 제품 내 알림, 앱 푸시만 존재
- 신규 알림 타입 추가 시 Notion 알림 목록 문서에 별도 항목으로 추가 필요

**변경 이력**
- 2022-07: 근무 승인 참조자 알림(`FlexTimeTrackingWorkRecordStageInProgressReferMessageContext`) 신규 추가
- 2022-07: 휴가 승인 참조자 알림(`FlexTimeTrackingTimeOffStageInProgressReferMessageContext`) 신규 추가

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1658720620434729?thread_ts=1658370289.917169&cid=CRU35U9FC)

---

#### 알림 템플릿 endedAt 타입 버그 (Long vs Integer deserialize)

**스펙/규칙**
- time-tracking-api → pavement-api 내부 통신 시 데이터가 Map에 들어가는데, 메시지 렌더링을 위해 deserialize 할 때 `0` 값이 `Long`이 아닌 `Integer`로 인식되는 버그
- 증상: `SpelEvaluationException: Method toLocalizedDateTimeRange(java.lang.Long, java.lang.Integer) cannot be found`
- 원인: 0을 fallback 값으로 넣었을 때 JSON deserialize 시 Integer로 읽힘
- 해결: 알림 템플릿에 `endedAt != 0` 조건문 추가하거나, 타입을 명시적 `Instant`로 변경

**자주 오는 케이스**
- 근무 승인 알림 발송 실패 로그(`FLEX_TIME_TRACKING_WORK_RECORDS_REQUEST_APPROVED`) → endedAt 없는 케이스(승인에서 시간 미명시)에서 발생

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1658370289917169)

---

#### raccoon 어드민 알림 설정 확인 도구

**스펙/규칙**
- 어드민 URL: `https://flex-raccoon.grapeisfruit.com/notifications/home`
- 유저별 알림 설정 현황 확인 가능 (알림 설정 변경 이력 없으면 모두 활성화 상태)
- VOC 인입 시 사용자의 알림 설정 확인 첫 번째 수단으로 활용
- 신규 알림 추가 후 기존 설정과 동기화 버튼도 이 페이지에 위치

**자주 오는 케이스**
- "알림이 안 온다" → raccoon 어드민에서 해당 사용자 알림 설정 먼저 확인
- "알림 설정 화면에 값이 없다" → 한 번도 알림 설정 변경 안 한 유저. 모두 활성화 상태

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1659942050775029)

---

#### Slack 알림 flex_user_slack_user_mapping 의존성

**스펙/규칙**
- 슬랙 알림은 `USER` 기준으로 발송
- `flex_user_slack_user_mapping` 테이블에 해당 유저 값이 없으면 슬랙 연동이 안 되어 오류 발생
- 고객사가 슬랙 연동을 했더라도 특정 유저만 연동 안 된 경우 있음

**자주 오는 케이스**
- "슬랙 알림이 안 온다" → 고객사 슬랙 연동 여부 확인 → `flex_user_slack_user_mapping` 테이블에서 해당 user 값 존재 여부 확인
- customer는 등록됐는데 특정 사용자만 슬랙 알림 실패 → 해당 유저 슬랙 연동 미완료

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1667783626385599)

---

#### requestTypeNames 빈 배열 버그 (워크플로우 알림)

**스펙/규칙**
- 워크플로우 task 관련 알림에서 `requestTypeNames` 필드가 빈 배열(`[]`)로 전달된 경우 알림 로딩 오류 발생 (500 에러)
- 근무/휴가 이벤트와 연결되지 않은 workflow_task에서 발생
- 처리: 해당 알림 notification_deliver 삭제 → 알림 목록 API 정상 동작

**조회 SQL**:
```sql
select nd.receiver_id, n.notification_type, n.db_created_at, n.id as notification_id,
       n.message_data_map, json_extract(n.message_data_map, '$.taskKey')
from notification as n, notification_deliver as nd
where json_contains(n.message_data_map, json_array(), '$.requestTypeNames')
  and json_length(n.message_data_map, '$.requestTypeNames') = 0
  and n.id = nd.notification_id;
```

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1669769831159049)

---

### 2. 세콤/캡스/텔레캅 연동

---

#### 세콤 연동 시 실시간 위젯 근무유형 필수

**스펙/규칙**: 세콤/캡스 타각은 근무유형에서 실시간 기록(위젯) 허용 시에만 출퇴근 기록으로 확정됨. 위젯 미허용 근무유형이면 타각이 draft 상태로 저장되며 근무 기록으로 이어지지 않음.

**자주 오는 케이스**: 세콤 설치 후 타각이 기록에 반영 안 된다는 문의 → 근무유형 실시간 기록 허용 여부 확인.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1740114845182849)

---

#### 세콤/캡스 외부 연동 구조

**스펙/규칙**
- 세콤이 관리하는 프로그램: **세콤매니저**(근태식당), **클라우드매니저** 두 가지
- **세콤매니저**를 통해 flex 외부연동 지원 (MSSQL, 오라클, MySQL) — ODBC 프로토콜
- 세콤매니저에서 MS-SQL 방식과 ODBC 방식 **동시 지원 불가** (세콤 측 확인 사항)
- 세콤/캡스 연동 시 **근무지 제한 정책만 패스** (다른 제한들은 적용)
- 세콤 클라우드 서버로는 외부연동 **불가** — 세콤매니저(로컬 프로그램)를 통해서만 가능
- VM(버추얼 서버) 설치도 가능 — 외부 통신만 되면 무관
- 단말기 최대 **4개** 동시 연동 가능
- 80개 매장 연동 시 ODBC 드라이버를 각 매장에 설치하는 대신 서버 1대로 집중 연동이 베스트프랙티스
- 커넥션 기본값: 캡스/세콤 2개, KT텔레캅 3개

**자주 오는 케이스**
- "클라우드 서버에 세콤 설치해도 되나요?" → 안 된다고 안내
- "세콤 설치 후 근무표에서 수정 불가로 만들고 싶다" → 기본 근무 정책에 제한 걸어 세콤으로만 등록하게끔 우회 가능
- 대규모 매장 연동 시 아키텍처 문의 → 서버 집중 연동 권장

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1709094877), [스레드2](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1716777789), [스레드3](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1722475853)

---

#### 세콤 방화벽 설정

**스펙/규칙**: 세콤 설정 시 `flex-secom.flex.team` 도메인 기반으로 방화벽 허용. 고정 IP 미보장이므로 IP가 아닌 도메인으로 허용해야 함. 프로토콜 타입 = TCP.

**자주 오는 케이스**: 세콤 연동 후 통신 실패 → 방화벽 도메인 허용 여부 확인.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1773275932624219)

---

#### 세콤/캡스 구독 해지 및 재연동 절차

**스펙/규칙**
- 구독 해지 시: `connLimit=0`, `active=false` 처리
- 해지 후 **7일** 뒤 계정 삭제
- 재구독 시 기존 정보가 있으면 그대로 활성화
- 관련 Notion 문서: https://www.notion.so/f3de1de14146494e917881210bdc4d94

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1718068576), [스레드2](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1731997497)

---

#### 캡스 + IP 제한 병합 검증 실패

**스펙/규칙**: 출근을 웹으로, 퇴근을 캡스로 할 때, 이전에 IP 제한에 걸린 기록이 있으면 위젯 병합 시 해당 제한 기록도 포함되어 검증 실패 처리됨. 이는 현재 스펙 동작.

**자주 오는 케이스**: "캡스 연동 후 퇴근 기록이 안 된다" → 이전 IP 제한 기록 여부 확인.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1753432328584289)

---

#### 캡스 수동 동기화 동작 방식

**스펙/규칙**
- 수동 동기화: 그 시점의 상태에 맞춰 실시간 근무(근무 시작 → 근무 종료) 동작 처리
- 구성원이 이미 근무를 등록했거나 실시간 위젯이 진행 중이면 캡스 데이터가 전부 반영되지 않을 수 있음
- PC가 꺼진 기간 동안 근무를 등록하고 싶다면 → **벌크 업로드** 방법 사용 권장
- 세콤 단말기 아이디가 다른 기기에서 각각 출근 모드로 타각 시: **가장 처음 타각한 것**으로 반영

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1723012588)

---

#### KT텔레캅 event_datetime vs sync_datetime

**스펙/규칙**
- `event_datetime`: 실제 타각 시간
- `sync_datetime`: flex 서버에 저장된 시간
- PC 전원이 꺼진 상태에서 타각된 기록은 재기동 후 **14일 이내** 자동 동기화됨
- 전원 off 상태에서 찍힌 기록은 서버 재기동 후 sync_datetime이 9시로 잡히는 텔레캅 측 버그 존재

**자주 오는 케이스**: "텔레캅 PC 껐다가 켰더니 기록이 이상하다" → sync_datetime 9시 고정 버그 가능성.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1755133043632519)

---

#### 텔레캅 퇴근 기록 미생성 (미확정 상태)

**스펙/규칙**: 텔레캅 연동 후 퇴근 기록만 안 찍히는 케이스 → 미확정 상태가 원인. 근무확정 건너뛰기 미설정 시 유저가 직접 확정하거나 확정 스킵을 설정해야 함.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1760519399131719)

---

#### KT텔레캅 오픈 일정 (2024년 말 기준)

**스펙/규칙**: 2024년 12월 기준 테스트 환경 세팅 중. 2025년 1월 오픈 예상. 프로세스: KT텔레캅 측 내부 테스트 → 버그픽스 → KT텔레캅 가이드 작성 → 오픈.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1733910973)

---

#### 세콤/캡스 다법인 및 다단말 처리

**스펙/규칙**
- 세콤/캡스는 다법인 지원 가능
- 한 PC에서 최대 1개 flex 고객사만 연동 가능
- 사번이 같은 겸직자는 세콤에 등록된 사번으로 매핑된 회사로 타각됨
- 다른 공간이면 각 단말기에 각각 타각 가능
- 같은 회사라면 본관/별관 캡스 각 1대씩 총 2대 연동 가능
- 커넥션 수: admin-shell에서 직접 변경 가능

**자주 오는 케이스**: ODBC 커넥션 수 초과 오류 → 이미 연결된 상태에서 재확인 테스트 시 발생.

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1762840740588839), [스레드2](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1769162478506189), [스레드3](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1771494239963039)

---

### 3. GPS/IP 근무지 제한

---

#### GPS/IP 동시 제한 동작 방식

**스펙/규칙**
- GPS 제한 + IP 제한을 **동시에 설정**한 경우, 둘 다 해당하지 않는 곳에서는 근무 등록 불가
- 웹에서 IP/GPS 모두 제한 시 "근무지 내에서만 등록 가능" 메시지 표시 — 정상 스펙
- 근무지 설정에 **해외 주소**도 별다른 제약 없이 동작 (근무지 좌표만으로 검증)
- **권한자가 구성원 근무 등록할 때는 승인 발생하지 않음** (GPS 제한과 무관)
- GPS 근무예약: 예약 시작 시점에 GPS 판단이 이미 완료됨 (미리 등록 개념)
- **최고관리자는 GPS/IP 근무지 제한 예외** (제한을 받지 않음)
- 근무정책 생성 제한 없음 / 근무지 최대 **150개** / IP 접근 허용 최대 **200개**

**자주 오는 케이스**
- "근무지 밖에서도 관리자는 출근 처리 가능한가?" → 최고관리자는 예외
- "근무지 밖 GPS 거리가 km가 아닌 m로 표시된다" → 미터(m) 기준이 정상 스펙

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1706750070), [스레드2](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1768991135277039)

---

#### 슬랙 출근 리마인드 검증 실패 조건

**스펙/규칙**: 슬랙 출근 리마인드 알림 → 출근 버튼 클릭 → "근무 시작 시간을 확인해 주세요" 에러 발생 조건:
- 출퇴근 시간 < 호출 시간
- 출퇴근 시간 > (호출 시간 + 9시간 버퍼)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1762755141530349)

---

### 4. 위젯/자동근무기록

---

#### 자동근무기록(위젯) 리셋 시점

**스펙/규칙**
- 출근 후 **20시간** 뒤 자동 퇴근 처리 (리셋)
- 이른출근방지 옵션이 설정된 경우 별도 기준 적용
- 위젯으로 출근 → 퇴근 → 출근 연속 타각 시 각각 별도 기록으로 남겨짐 (하루 여러 번 출퇴근 기록 가능)
- 자동퇴근 처리됐는지 직접 타각인지 웹 화면에서 **구분 불가** (시작/종료시각만 남음)
- 자동근무기록은 근무유형에 의해 소정근로일에만 생성됨 → 주휴일을 평일로 대체해도 기존 일요일에는 자동 기록 미생성

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1707293777), [스레드2](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1765775167279069), [스레드3](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1738826519935069)

---

#### 출퇴근시각 vs 시작/종료시각 구분

**스펙/규칙**: 두 데이터는 다른 소스에서 옴.
- **출퇴근시각**: 실제 출퇴근 타각 기록
- **시작/종료시각**: 관리자가 근무수정권한으로 직접 수정한 기록 (별도 승인 절차 없음)

**자주 오는 케이스**: "출퇴근시각 없이 시작/종료시각만 있는 기록이 왜 있냐" → 관리자 직접 수정.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1773727508492049)

---

#### 출근 타각 invalid 처리 방법

**스펙/규칙**: 출근 타각을 invalid 처리하는 operation API **없음**. 직접 DB에서 work-clock event를 삭제해야 함.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1711675851)

---

### 5. 근무 정책/스펙

---

#### 근무 삭제 권한

**스펙/규칙**
- 최고관리자라도 **근무 승인자가 아니면** 여러 날 근무 삭제 불가 — 스펙
- 연장근무 반려되면 당일 근태기록이 모두 사라짐 — 스펙 (그 날에 대한 근무 등록 시 연장 근무로 판단된 것이 포함되었기 때문)

**자주 오는 케이스**: "연장근무가 반려됐는데 당일 근무 기록이 다 사라졌다" → 정상 스펙. 소정근로만큼 근무를 올리고 초과근로분을 다시 올리면 해결 가능.

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1706682260), [스레드2](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1724392771)

---

#### 관리자 본인 근무 편집 시 승인 발생 여부

**스펙/규칙**
- 관리자가 **내 근무 화면**에서 자신의 근무를 등록하면 → 승인 발생하지 않음
- 관리자가 **구성원 근무 화면**에서 본인 클릭 후 수정하면 → 승인 발생함
- `관리자인가` 판단 기준이 내 근무/휴가를 등록하는지로 판단하기 때문에 발생하는 한계 (현재 API 구조상 분리 불가)

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1729662733)

---

#### 출장 근무 등록 시 예약된 근무 우선 적용

**스펙/규칙**
- 오후에 출장 스케줄이 예약되어 있을 경우, 오전에 출근 버튼 누르면 → **등록된 근무(출장)로 근무 시작이 먼저 적용**됨
- 편의를 위한 스펙이지만 불편함을 주는 케이스도 있어 개선 논의됨 (미확정)

**자주 오는 케이스**: "오전에 출근 눌렀는데 왜 출장 근무로 시작됐나요?" → 의도된 스펙.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1718932192)

---

#### 근무 정책 동일 이름 허용

**스펙/규칙**
- 현재 근무 정책은 동일한 이름 생성 가능 (중복 허용) — 이후 사후 추가된 제약
- 근무 유형은 동일 이름 생성 불가 (이미 제약 있음)
- 근무기록 엑셀 업로드에서는 동일한 근무 정책이 존재하면 오류 발생 → 담당자가 이름 변경하는 방식으로 처리
- UI에서 신규 유입을 막고 점진적으로 정리 방향 채택

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1678167203865539)

---

#### 사번(employee ID) 정렬 방식

**스펙/규칙**
- 사번은 숫자가 아닌 **문자열**로 저장됨 → 사전식(lexicographic) 정렬
- 예: `1`, `10`, `100`, `2` 순으로 정렬됨
- 사번 자동 증가/저장 기능 없음
- 숫자 정렬을 원하면 고정 길이(예: `0001`) 또는 숫자 prefix 사용 권장

**자주 오는 케이스**: "사번 정렬이 숫자 크기 순이 아니다" → 사번은 문자열이므로 정상 동작.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1660010186741679)

---

#### 해외 근로자 타임존 처리

**스펙/규칙**
- 모든 타각 데이터는 UTC로 저장
- 현재 **한국 타임존(KST)만 지원**
- 출퇴근 시간/야간근무 체크 등 모두 한국시간 기준으로 해석
- 엑셀 출력도 한국시간 기준 생성
- 해외 근로자는 한국에서 반복일정 설정 후 사용 권장

**의사결정 배경**: 해외 지원 요청 있으나 현재 미지원. 한국 기준 일관 처리가 현재 스펙.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1756346056182339)

---

### 6. 초과근무/연장

---

#### 근무시간 초과 표기 (연장+야간 합산)

**스펙/규칙**: 근태 대시보드의 근무시간 초과 = 연장 + 야간 합산. PR #4778에서 `overNightWorkingMinutes` 추가됨. 동일 주기에 연장과 야간이 함께 있으면 "연장야간"으로 합쳐서 표시됨.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1756285599932569)

---

#### minutesToHours() 소수점 버림 이슈

**스펙/규칙**: 모든 연산은 분 단위로 수행하고 마지막에 시간 변환. `minutesToHours()` 함수가 소수점을 버림 처리함. 분단위 가산율 적용 시 소수점 버림 발생. TT 내 엑셀 관련 코드들이 이 함수를 사용함.

**의사결정 배경**: 설계상 소수점 버림이 의도된 것인지 확인 필요한 상태.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1764838336276949)

---

#### 3종/7종 전환 시 승인 처리

**스펙/규칙**
- 3종→7종 변경 시: 기존 승인이 3종 해석 기준 → 7종 해석 기준으로 일괄 수정됨
- 7종→3종 변경 시: 구성원 근무에서 구분 반영 시점 = 변경 즉시
- 법내연장 미사용 체크 시 반영 시점 = 해당 근무유형 적용 시점

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1757559780488739)

---

#### 3종 휴일 150% 보상휴가 계산 예시

**스펙/규칙**: 보상휴가 부여 가능 시간 계산 예시:
- 휴일 8시간 × 1.5 = 12시간
- 휴일연장 2시간36분 × 0.5 = 1시간18분 (추가분만)
- 총 13시간18분
- 포괄계약의 연장으로 차감된 시간 제외

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1765950099005679)

---

#### 보상휴가 초과근무시간 유형 정렬 순서

**스펙/규칙**: 보상휴가 탭 초과근무시간 유형 정렬 순서 (별도 정렬 조건 없이 조회 순서대로였다가 핫픽스로 수정):
1. 야간
2. 연장(법정근로 내)
3. 연장·야간(법정근로 내)
4. 연장
5. 휴일
6. 연장·야간
7. 연장·휴일
8. 휴일·야간
9. 연장·휴일·야간

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1722325394)

---

#### 선택적 근무제 연장근무 승인 조건 변경 대응

**스펙/규칙**: 연장근무 승인 조건 변경 후 고객사 불만 → **제품적 해결 방안 없음**. 법적 기준 변경에 따른 스펙이므로 되돌릴 수 없음. 근무 계획 작성 주기 단축 제안 (우회책).

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1714715817)

---

#### 포괄계약 근로시간 주 단위 vs 월 단위

**스펙/규칙**
- 급여는 월 1회 지급이므로 주 단위 입력해도 주→월 단위 변환 과정을 거침
- 주→월 변환 시 소수점 이슈 발생 → 월 단위 권장 (강제 아님)
- 포괄계약 고객사는 초과근무수당을 덜 주고 싶어하는 경우가 많으므로, 주 단위 계약을 월 단위로 바꾸면 초과근무가 발생하지 않을 수 있음

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1735541714)

---

### 7. 휴가/연차

---

#### 휴취승(휴가 취소 승인) 상태 관리

**스펙/규칙**
- 휴취승 플로우: 등록 승인 완료 → 취소 요청 → 취소 승인 대기 → 취소 승인 완료
- 취소 승인 시 상태는 `APPROVAL_COMPLETED`가 아닌 `CANCEL_APPROVAL_COMPLETED`로 변해야 함
- 참조 승인만 있는 경우 취소 요청 시 즉시 취소 처리되어 단건 조회 API에서 `CANCEL_APPROVAL_COMPLETE`로 응답해야 함

**버그 이력**
- 휴가 단건 조회 API(`time-off-uses/{TimeOffEventId}/root`)에서 취소 후 상태가 `TIME_OFF_CANCELED` 대신 `APPROVAL_COMPLETED`로 응답되는 버그 → PR #4135로 수정

**자주 오는 케이스**
- 등록 승인 O, 취소 승인 X일 때 취소 후 단건 조회 시 상태 불일치
- 본인이 승인권자일 때 상세보기에서 반려 버튼이 없는 현상 → 할일/알림 경유 시 노출되는 UI 차이

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1676517974584859), [스레드2](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1676274512350169)

---

#### 휴가/승인 이벤트 테이블 구조

**스펙/규칙**
- `v2_user_time_off_event`: 휴가 등록/취소 등 휴가 이벤트가 쌓이는 테이블 (append-only)
- `v2_time_tracking_approval_event`: 휴가/근무 승인 이벤트 테이블
  - `target_event_category = 'TIME_OFF'`, `target_event_id = v2_user_time_off_event.id` 조건으로 조회
  - `event_type` 라이프사이클: `REGISTER` → `APPROVE` or `DECLINED` or `CANCEL`
  - APPROVE 이벤트가 있으면 승인된 것으로 판단
- v1 테이블(`flex.user_time_off_use`)은 확인 불필요 — v2만 확인하면 됨

**승인권자 조회 방법**
1. `v2_time_tracking_approval_event`의 `taskKey`, `customerId`로 `workflow_task` 검색
2. `workflow_task.id`로 `workflow_task_stage` 검색 → `reviewer_targets` 필드가 승인권자

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1658395078774879)

---

#### 연차 조정값과 근무유형 변경

**스펙/규칙**: 연차 조정 시 근무유형의 1일 기준 시간이 달라지면 조정값이 재계산됨. 조정 발생 시점의 근무유형 기준 시간으로 고정되지 않고, 이후 근무유형 변경 시 의도와 다르게 동작하는 케이스 존재. 설계 한계.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1754993387793889)

---

#### 조정 플러스/마이너스 의미

**스펙/규칙**
- 조정 마이너스: 잔여 연차가 있는데 돈으로 줄 것을 반영
- 조정 플러스: 마이너스 연차 상태에서 0으로 맞추려고 플러스 처리

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1758095421930449)

---

#### 교대근무 맞춤휴가 등록/취소 미지원

**스펙/규칙**: 교대근무 관리에서 맞춤휴가 등록/취소 현재 미지원 (스펙). 툴팁에 "연차"라고 표시되는 별도 버그 존재 (TT-16578).

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1771464130890579)

---

#### 근태 IP 로그 제공 가능 여부

**스펙/규칙**
- 근태 IP 로그를 별도 저장 **하지 않음**
- 감사로그로 볼 수 있는 것은 **최대 90일** 한계

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1727337244)

---

#### 제헌절 공휴일 0일 처리 버그

**스펙/규칙**: 제헌절이 공휴일로 지정되어 해당일 휴가가 0일로 처리됨. 배포로 해결됨.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1770186806832619)

---

#### 법정 관련 대응

**스펙/규칙**
- **난임치료휴가 비밀누설 금지** (2025년 2월 23일 시행): 난임치료휴가를 신청한 근로자의 의사에 반하여 내용을 제3자에게 누설 금지. 대응: 근무 조회 권한만 주고 휴가 조회 권한 주지 않으면 휴가명 미노출 가능
- **모성보호법 개정** (2025년 2월 변경 적용): 유/사산휴가 기준 일부 변경
- **2025년 대체 휴일**: 2025년 5월 6일이 대체 휴일. 연말 대응 예정

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1731390191), [스레드2](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1732869444), [스레드3](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1732843115)

---

### 8. 승인

---

#### 삭제된 구성원의 승인라인 처리

**스펙/규칙**
- 현재 제품에서 삭제된 구성원의 승인라인 전환 방법 없음 (퇴직자 처리와 다름)
- 삭제된 구성원이 승인라인에 있으면 승인 진행 불가
- 퇴직자는 승인권자 교체 가능하지만, **삭제된 구성원은 불가**
- 운영으로 직접 처리하거나 PE 검토 필요

**변경 이력**: 유사 과거 사례 — CI-2367(퇴사 승인권자 교체 버그), CI-3769(삭제 구성원 잔여 승인건 강제 승인), CI-4228(삭제 구성원이 승인자로 있는 문서 강제 승인)

**자주 오는 케이스**: "승인이 진행 중인데 구성원을 삭제했더니 승인이 멈췄다" → 운영 개입 또는 PE 검토.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1774501349115049)

---

#### 일괄 승인 기능 미보유

**스펙/규칙**: 현재 일괄 승인 기능 미보유. 대안:
- 참조 승인만 걸어두기
- 승인 없이 관리 방법 사용

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1769675099235299)

---

#### 승구개 (승인 구독 개선) — 승인 조회 API 설계

**스펙/규칙**
- 승인 조회 API 엔드포인트: `/work-record/approvals/{approvalIdHash}`
- `decidedWorkRecordBlocks`: 사용자가 등록한 근무 블록을 계산해서 나온 블록들 (연장, 야간, 휴일 근무 등 포함)
- `workingHours` 필드의 type: `WORK_FORM`, `TIME_OFF`, `REST`
- 휴일/야간/연장근무가 발생하지 않으면 `emptyArray`로 응답
- mock API: `/work-record/approvals/mock` (`/mock` postfix)

**의사결정 배경**: 최대 근무 승인 + 휴가 등록 승인 + 휴가 취소 승인이 동시 발생 가능하여 timeline/diff 데이터 표현 필요.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1678083825664979)

---

### 9. 연동 (슬랙/캘린더)

---

#### 슬랙 연동 — flex에서 슬랙 상태 변경 기능

**스펙/규칙**
- flex에서 슬랙 상태를 변경하는 기능 **없음**
- 슬랙 봇은 모든 휴가를 단일 '휴가'로 표현 — 휴가 유형별 이모지 변경 **불가**
- 이유: 민감한 휴가(병가, 여성보건휴가 등)가 공개될 수 있어 의도적으로 휴가 유형 노출 제거
- 슬랙 연동 담당: 현재 플랫폼 팀(@platform-eng)에 문의

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1710134467), [스레드2](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1721195094)

---

#### 구글 캘린더 연동

**스펙/규칙**
- 구글 캘린더 연동 시 외근/출장/재택만 공유됨. **기본 근무 스케줄은 공유 불가** (rate limit 우려로 현재 미지원)
- calendarId 확인 없이 연동하면 어느 회사든 한 캘린더로 모일 수 있음 — 연동 전 calendarId 확인 필수
- 이벤트 기반으로 전환되면 기본 근무 공유 가능성 있음

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1709174207), [스레드2](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1760692174576899)

---

#### .ics 파일 / Outlook/Teams 일정 공유

**스펙/규칙**
- 현재 .ics 파일 제공 **없음**
- 계획 있음: ics 파일 제공 POC 진행 중 (2024년 9월 기준)
- 구글 캘린더 연동은 있으나 Teams 연동은 별도 계획 없음
- 두레이: ics 지원

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1726821774)

---

### 10. 개발/팀 프로세스

---

#### Linear 워크플로우 설계 (squad-tracking)

**스펙/규칙**: 최종 확정 상태 구조:
- **Triage**: 팀 외부 인원의 요청 (Linear 기능 별도 활성화 필요)
- **Backlog**: 미뤄진 이슈들 아이스박스/배팅 테이블
- **Todo**: 새로 등록되는 이슈의 default 상태 (GTD의 Inbox)
- **Ready**: WIP 제한 적용. 이번 사이클에 할 작업 대기열 (애자일의 Backlog)
- **In Progress**: 현재 작업 중
- **QA**: develop 브랜치 merge 완료됨을 의미 (qa 서버 배포를 의미하지 않음)
- **Done**: 최종 완료
- PR 머지 시 자동 QA 상태 전환 설정

**의사결정 배경**: "릴리즈만 마일스톤을 사용하자", "마일스톤 자동화 사용하지 말자" 방침 확정.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1669731538703679)

---

#### E2E 테스트 자동화 — Playwright + Cucumber

**스펙/규칙**
- Selenium에서 Playwright로 전환 이유: HTML element를 잘 못 찾음, 속도 10배 차이, 녹화 기능
- 조합: **Playwright + Cucumber** (PoC 완료)
- E2E 테스트 관련 문서: [Notion](https://www.notion.so/flexnotion/E2E-739171beea5440a28fc27b4957914ee9)
- 근무/휴가 관련 테스트는 시간 선택이 포함되어 작성하기 어려움 → 단계적으로 채워가는 방식

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1669194187445139)

---

#### API 설계 원칙 — 버전 관리 및 일반화

**스펙/규칙**
- BE에서 API 버저닝을 자유롭게 할 수 없는 구조 (`/v2/` prefix 제거 논의 있었음)
- 기간별 근무시간 API: 기존 API에 `ALL` 타입 추가하는 방식으로 일반화
- 하위 호환성 유지를 위해 FE가 할 수 없는 경우 서버 우선으로 처리

**출처**: [스레드](https://flex-cv82520.slack.com/archives/CK7EUDG4S/p1666847342974379)

---

### 11. 기타 운영

---

#### 프로필 사진 일괄 다운로드

**스펙/규칙**
- 제품 기능으로 일괄 다운로드 **없음**
- 브라우저 스크립트로 수동 지원 가능
- 우클릭 저장 불가는 스펙

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1708418789)

---

#### 목표 조회 및 정렬 스펙

**스펙/규칙**
- '내 목표'에서는 조직 목표 미노출
- '전체 목표 > 어사이드'에서 tree 구조로 조직 목표 열람 가능 (조직장에게만 담당 목표로 노출)
- 수동 정렬(드래그앤드롭): 전체 목표 정렬은 관리자/대표만 가능. 내 목표/구성원 목표는 누구나 정렬 가능. 정렬 값은 공유됨

**출처**: [스레드1](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1767860067105299), [스레드2](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1767860408345489)

---

#### 조직명 변경 방법

**스펙/규칙**: 조직명 변경: **조직도 → 조직 선택 → 오른쪽 클릭 → 고급 설정**에서 가능. 조직도에서 직접 변경 불가.

**출처**: [스레드](https://flex-cv82520.slack.com/archives/C01G5AFKNFL/p1722826795)

---

## 행동 패턴 요약

| 패턴 | 빈도 | 예시 |
|------|------|------|
| 스펙/버그 즉시 판단 후 안내 | 매우 높음 | "이것은 스펙입니다", "버그 확인됩니다, PR 올리겠습니다" |
| raccoon 어드민으로 알림 설정 확인 | 높음 | 알림 VOC 발생 시 첫 번째 확인 단계 |
| 세콤/캡스 연동 구조 설명 | 높음 | 위젯 미허용 근무유형, ODBC 방식, 방화벽 도메인 안내 |
| DB 직접 조회로 원인 파악 | 높음 | `flex_user_slack_user_mapping`, `v2_user_time_off_event` 조회 |
| 타입/소수점 이슈 주의 | 중간 | Long vs Integer, minutesToHours() 버림 |
| 제품화 방향 제안 | 중간 | 운영 수동 처리 대신 raccoon 어드민 동기화 버튼 추가 |
