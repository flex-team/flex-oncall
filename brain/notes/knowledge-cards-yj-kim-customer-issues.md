# 김영준 #customer-issue 스레드 지식 카드

> 수집 기간: 2024년 이후 전체
> 출처: #customer-issue 채널 김영준 메시지 전수 수집 (89개 스레드)
> 작성일: 2026-03-29

---

## 목차

1. [세콘(SICON) 연동 패턴](#세콘sicon-연동-패턴)
2. [연차촉진 UTC/KST 연도 경계 버그](#연차촉진-utckst-연도-경계-버그)
3. [근무유형 적용일 1970-01-01 = 입사일](#근무유형-적용일-1970-01-01--입사일)
4. [IP 제한 + 자동퇴근 상호작용](#ip-제한--자동퇴근-상호작용)
5. [dry-run WARN vs ERROR — 게시 차단 여부](#dry-run-warn-vs-error--게시-차단-여부)
6. [보상휴가 초과부여 상태 체크 버그](#보상휴가-초과부여-상태-체크-버그)
7. [연차촉진 관리자 작성 기간 필터 스펙](#연차촉진-관리자-작성-기간-필터-스펙)
8. [주기내연장귀속일 Operation API](#주기내연장귀속일-operation-api)
9. [external_provider_event 재처리](#external_provider_event-재처리)
10. [근무 기록 없을 때 이른출근 판단 불가](#근무-기록-없을-때-이른출근-판단-불가)
11. [휴가 참조자 승인 알림 수신 실패 — notification_deliver 확인](#휴가-참조자-승인-알림-수신-실패--notification_deliver-확인)
12. [휴가 확인하기 이메일 버튼 동작 분기](#휴가-확인하기-이메일-버튼-동작-분기)
13. [대표이사 연차촉진 — 미지급 연차정책 + 뷰 권한 없음](#대표이사-연차촉진--미지급-연차정책--뷰-권한-없음)
14. [세콘 쿼리 오류 — 저희 쿼리가 아닌 경우](#세콘-쿼리-오류--저희-쿼리가-아닌-경우)
15. [캡스 수동 전송 중복 데이터 무시 스펙](#캡스-수동-전송-중복-데이터-무시-스펙)
16. [퇴직자 포함 데이터 추출 — Operation API](#퇴직자-포함-데이터-추출--operation-api)
17. [세콘 퇴근 시 퇴근시간 00:00 조정 원인 분석](#세콘-퇴근-시-퇴근시간-0000-조정-원인-분석)
18. [교대근무 엑셀 스케줄 업로드 시 연차 미반영 버그](#교대근무-엑셀-스케줄-업로드-시-연차-미반영-버그)
19. [교대근무 스케줄 게시 — 기존 휴가 있는 날 오류](#교대근무-스케줄-게시--기존-휴가-있는-날-오류)
20. [모바일 BFF nullable 필드 500 에러](#모바일-bff-nullable-필드-500-에러)
21. [TT 엑셀 다운로드 타임아웃 — HTTP client 타임아웃 조정](#tt-엑셀-다운로드-타임아웃--http-client-타임아웃-조정)
22. [신승인 start-approval-process / produce-event 2PC 패턴](#신승인-start-approval-process--produce-event-2pc-패턴)
23. [단시간근로자 휴무일 연장근무 판단 기준](#단시간근로자-휴무일-연장근무-판단-기준)
24. [휴일대체 기간 설정 변경 — Operation](#휴일대체-기간-설정-변경--operation)
25. [Central Dogma SSH 키 관리](#central-dogma-ssh-키-관리)
26. [오라클 연동 시 재직자/퇴직자 연차수당 분리 API](#오라클-연동-시-재직자퇴직자-연차수당-분리-api)
27. [월차촉진 연도 경계 버그 (CI-3809 동일)](#월차촉진-연도-경계-버그-ci-3809-동일)
28. [연차 조정 일괄 취소 기능 누락](#연차-조정-일괄-취소-기능-누락)
29. [휴가 코드 삭제 시 등록된 휴가 취소 스펙](#휴가-코드-삭제-시-등록된-휴가-취소-스펙)

---

### 세콘(SICON) 연동 패턴

**스펙/규칙** (현재 상태)
- 세콘 → flex 데이터 전달 시 **퇴근 → 출근 역순**으로 전달되는 경우 존재
  - 퇴근 이벤트 먼저 처리 → 출근기록 없어 오류 알림 발송 → 이후 출근 이벤트 처리 → 퇴근미타각으로 노출
- 재전송해도 **중복 데이터로 skip** (flex가 이미 받은 것으로 처리)
- 세콘에서 오류 발생 시 저희 쪽 로그에 안 찍힘 (세콘 자체 문제)
- 세콘 연동 비활성화 → 활성화 전환해도 비활성화 중에 보낸 데이터는 소급 반영 안 됨

**해결 패턴**
- 역순 전달 오류: 관리자가 퇴근 시간으로 수동 근무 기록
- 특정 유저만 동기화 안 됨: 세콘 자체 사번 설정 오류 확인 필요 (저희가 확인 불가)

**안희종 제안** (미구현): 실제 타각 시각 기반 priority queue 운영

**출처**: [CI-3793](https://linear.app/flexteam/issue/CI-3793), [CI-3700](https://linear.app/flexteam/issue/CI-3700), [CI-3861](https://linear.app/flexteam/issue/CI-3861), [CI-3864](https://linear.app/flexteam/issue/CI-3864), [CI-3849](https://linear.app/flexteam/issue/CI-3849)

---

### 연차촉진 UTC/KST 연도 경계 버그

**스펙/규칙** (현재 상태)
- 연차촉진 배치: **매일 오전 8시** 동작, 촉진일시가 8시로 DB에 저장됨
- DB 저장: **UTC 기준** → 1/1 08:00 KST = 12/31 23:00 UTC
- 연차촉진 목록 조회: **연도 단위**로 조회 → 2026년 조회 시 전년도 UTC 저장 건 누락
- 알림 발송: 상태만 보고 발송 → 목록에 안 보여도 알림은 발송됨
- **오래된 버그** (여태 계속 있던 문제, 특정 신규 배포로 발생한 것 아님)

**대응**
- 고객에게 "2025년 기준으로 조회하면 확인 가능"으로 안내
- 근본 수정 필요: 문서 목록 API의 연도 기반 쿼리(`firstDayOfYear`) → 연말 생성 촉진이 다음 해 화면에서 누락

**출처**: [CI-3809](https://linear.app/flexteam/issue/CI-3809), [CI-3907](https://linear.app/flexteam/issue/CI-3907)

---

### 근무유형 적용일 1970-01-01 = 입사일

**스펙/규칙**
- 근무유형 적용일이 `1970-01-01`이면 **입사일**로 표시/처리
- PR#8593 이후 dateFrom 기준으로 입사일만 보도록 변경됨
- "입사일"이라는 값을 서버로 전달할 때 `1970-01-01`로 지정
- 근태에서 그룹 입사일 기준 근무 조회는 원래 안 됨 (지원 없음)

**자주 오는 케이스**
- 게임듀오 CI-3773: 그룹 입사일 기준 근무 조회 안 됨 → 스펙상 불가
- 퍼슨헬스케어 CI-3902: 테스트 데이터 삭제 → 근무유형 1970-01-01로 덮은 뒤 다른 유형 삭제

**출처**: [CI-3773](https://linear.app/flexteam/issue/CI-3773), [CI-3902](https://linear.app/flexteam/issue/CI-3902)

---

### IP 제한 + 자동퇴근 상호작용

**스펙/규칙**
- **자동퇴근 시에는 근무지 안에서 되었다고 판단** → 따로 근무지 판단 안 함
- IP 제한 설정이 있어도 자동퇴근은 통과

**코드**: `UserWorkClockStopByReserveRequestServiceImpl.kt#L142-L143`

**자주 오는 케이스**
- 노브랜드 CI-3501: 기본근무 IP 등록 제한인데 집에서 퇴근 가능 → 자동퇴근이기 때문

**출처**: [CI-3501](https://linear.app/flexteam/issue/CI-3501)

---

### dry-run WARN vs ERROR — 게시 차단 여부

**스펙/규칙**
- 근무표 게시 전 dry-run 응답의 validation 결과:
  - **ERROR**: 게시 차단
  - **WARN**: 게시 허용 (무시)
- **버그 이력**: FE 파서 변경으로 WARN도 ERROR처럼 처리되어 게시 차단된 사례 발생
  - PR: `flex-frontend-apps-time-tracking/pull/2101`로 hotfix 배포 완료

**자주 오는 케이스**
- 시몬스 CI-3862: 주휴일 배치 주기 일주일 초과 허용 설정 → WARN으로 나와야 하는데 게시 막힘

**출처**: [CI-3862](https://linear.app/flexteam/issue/CI-3862)

---

### 보상휴가 초과부여 상태 체크 버그

**증상**
- 보상휴가 지급 시 "부여가능한 보상휴가 시간이 없어요" 오류

**원인**
- 부여 가능 여부 체크 시 **서로 다른 기간 범위를 비교** (버그)
  - 부여할 기간에 대해 (부여가능 - 부여할) < 0인지 체크해야 하는데 범위 불일치
- 코드: `UserCompensatoryTimeOffAssignUpdateService.kt#L690-L712`

**해결**
- PR: `flex-timetracking-backend/pull/11799` (로그 추가 → 핫픽스 배포 → 정상 지급 확인)

**출처**: [CI-3858](https://linear.app/flexteam/issue/CI-3858)

---

### 연차촉진 관리자 작성 기간 필터 스펙

**스펙/규칙**
- 연차촉진 목록에서 **"관리자 작성 필요" 상태** 촉진이 안 보이는 경우:
  - **이미 완료된 촉진이 있을 때** 관리자 작성 기간 필터가 작동 → 완료된 것과 섞여 미표시
  - 2021년 작업 의도: 완료된 촉진이 있을 때 관리자 작성 기간 필터 적용
  - **현재 스펙** (버그 아님)
- 대응: 관리자가 직접 해당 구성원에게 안내 후 종결

**코드**: `AnnualTimeOffPromotionHistoryServiceImpl.kt#L80-L81`

**출처**: [CI-3777](https://linear.app/flexteam/issue/CI-3777)

---

### 주기내연장귀속일 Operation API

**API**
```
POST /action/operation/v2/work-rule/modify-apply-start-date-for-distributed-period-over
```

**대상**: 선택적 근무유형 (임원, 전문연구, 부분 선택적)

**자주 오는 케이스**
- 코스모비 CI-3711: 적용일 2/1 → 2/2(월요일) 변경
- 더데이원랩 CI-3720: 선택적 근무유형 2/2(월)로 변경

**출처**: [CI-3711](https://linear.app/flexteam/issue/CI-3711), [CI-3720](https://linear.app/flexteam/issue/CI-3720)

---

### external_provider_event 재처리

**스펙/규칙**
- 세콘 등 외부 제공자 이벤트는 `external_provider_event` 테이블에 저장
- 재전송 시 **중복 이벤트는 skip** (이미 처리된 것으로 판단)
- 재처리가 필요하면 테이블에서 해당 이벤트를 찾아 상태 변경 필요

**출처**: [CI-3793](https://linear.app/flexteam/issue/CI-3793), [CI-3861](https://linear.app/flexteam/issue/CI-3861)

---

### 근무 기록 없을 때 이른출근 판단 불가

**스펙/규칙**
- 근무 스케줄 **게시 전에 출근 타각** → 근무 없으니 이른 출근인지 판단 불가 → 출근 시간 그대로 입력
- 관리자가 스케줄 게시 전에 구성원이 출근한 경우 발생

**자주 오는 케이스**
- 사쬬 CI-3767: 이른출근 비활성화로 변경 후 스케줄 미확정 상태에서 출근 → 이른출근 판단 불가
- 하이컨시 CI-3866: 스케줄 게시가 출근 이후 → 이른출근 판단 불가

**출처**: [CI-3767](https://linear.app/flexteam/issue/CI-3767), [CI-3866](https://linear.app/flexteam/issue/CI-3866)

---

### 휴가 참조자 승인 알림 수신 실패 — notification_deliver 확인

**조사 패턴**
```sql
-- 알림 설정 확인
select * from notification_settings where user_id = {userId};

-- 알림 발송 여부 확인
select nd.*, n.notification_type
from notification_deliver nd
left join notification n on nd.notification_id = n.id
where nd.receiver_id in ({userIds})
and n.notification_type = 'FLEX_TIME_TRACKING_TIME_OFF_REQUEST_APPROVE_REFER'
and n.db_created_at >= '2026-01-01';

-- topic으로 조회
select *
from flex_pavement.notification_deliver nd
left join flex_pavement.notification n on nd.notification_id = n.id
where nd.notification_topic_id = '{topicId}';
```

**주의사항**
- `notification_deliver`에 데이터가 없으면 발송 자체가 안 된 것
- 데이터는 있는데 고객이 못 받으면 → SES에서 고객사 메일 서버로 전달 실패 → SES 피드백 로그 확인

**자주 오는 케이스**
- 트러스테이 CI-3910: 참조자로 포함되어 있으나 알림 수신 못함 → SES 전송은 성공, 고객사 메일서버 누락

**출처**: [CI-3910](https://linear.app/flexteam/issue/CI-3910)

---

### 휴가 확인하기 이메일 버튼 동작 분기

**스펙/규칙**
- 이메일 알림의 `[확인하기]` 버튼 클릭 시 이동 위치:
  - **휴가 등록 알림** (참조): 할 일 목록(Todo) → 확인하기 클릭 시 **할 일(To-do)**로 이동
  - **휴가 승인 알림** (참조): 확인하기 클릭 시 **홈피드**로 이동
  - CTA 코드: `flex.time-tracking.time-off.request.approve.refer`

**출처**: [CI-3914](https://linear.app/flexteam/issue/CI-3914)

---

### 대표이사 연차촉진 — 미지급 연차정책 + 뷰 권한 없음

**스펙/규칙**
- 대표이사가 등기임원으로 등록된 경우 → 연차 지급 대상 아님
- 촉진 조회 시 미지급 연차정책 설정 구성원은 결과가 안 나옴 (연차 사용 안 함이라 0일 촉진 안됨)
- 촉진 이력은 정책 적용 이전에 생성된 것이라 당시 연차량만큼 나옴

**자주 오는 케이스**
- 오로라월드 CI-3932: 대표이사 연차촉진 내역 조회 → 미지급 연차정책으로 변경 이후라 결과 없음

**출처**: [CI-3932](https://linear.app/flexteam/issue/CI-3932)

---

### 세콘 쿼리 오류 — 저희 쿼리가 아닌 경우

**스펙/규칙**
- 세콘 연동 설정 가이드: `https://guide.flex.team/ko/articles/...`
- 세콘 프로그램 내에서 별도 쿼리를 입력하는 부분이 있음 → 이 쿼리가 잘못되면 저희가 처리 불가
- `syntax error at or near "DUPLICATE"` → 세콘 내부 쿼리 오류
- 고객사가 기존 쿼리를 남겨두고 새 쿼리를 추가한 경우 중복 문제 발생

**대응**: "저희가 가이드하는 쿼리가 아닌 것으로 보입니다. 세콘 프로그램 쿼리 관리에서 확인 필요"

**출처**: [CI-3953](https://linear.app/flexteam/issue/CI-3953)

---

### 캡스 수동 전송 중복 데이터 무시 스펙

**스펙/규칙**
- 캡스(CAPS) 수동 전송 시, 이미 flex에서 받아서 처리한 데이터는 **중복 데이터로 무시**
- 출근(START) 데이터가 이미 등록되어 있으면 수동 전송해도 재처리 안 됨
- 관련 스레드: [CI-3858 참고 링크](https://flex-cv82520.slack.com/archives/CRU35U9FC/p1769666076470469)

**출처**: [CI-3965](https://linear.app/flexteam/issue/CI-3965)

---

### 퇴직자 포함 데이터 추출 — Operation API

**API**
```
POST /action/operation/v2/time-off/customers/{customerId}/time-offs/excel/used

{
  "queryUserId": {adminUserId},
  "departmentIds": null,
  "dateFrom": "YYYY-MM-DD",
  "dateTo": "YYYY-MM-DD",
  "includeResignatedUsers": true
}
```

**주의사항**
- 조직 이동 간 삭제된 조직에 있는 구성원 → 삭제된 조직 포함 불가, 조직 없는 데이터로 남음
- 웹에서는 전체 조직을 조직 ID로 넘겨서 조직 없음을 받을 수 없음 → operation API로만 추출 가능

**출처**: [CI-3976](https://linear.app/flexteam/issue/CI-3976)

---

### 세콘 퇴근 시 퇴근시간 00:00 조정 원인 분석

**원인 패턴**
- 세콘 퇴근 타각 00:32:29 → flex에서 **00:00:00으로 조정**되는 경우
- `WorkClockTimeAdjuster.kt#L127` 참조
- **해당 날 종일휴가**가 있는 경우 → 00:00으로 조정됨 (종일 휴가가 있어 자정을 넘기지 않도록 처리)
- 조건 확인: 해당일 휴가 유무, 정시정보 유무, 유저선호퇴근옵션 (실시간/기본)

**확인 방법**
- consumer 로그 확인 시 consumer 인덱스가 아닌 **api 인덱스** 살펴야 함
- 조정 로그 보강 필요 (개선 예정)

**출처**: [CI-3979](https://linear.app/flexteam/issue/CI-3979)

---

### 교대근무 엑셀 스케줄 업로드 시 연차 미반영 버그

**증상**
- 교대근무에서 엑셀로 스케줄 업로드 시 다른 코드(근무유형 등)는 정상 반영되나 **연차만 반영 안됨**

**해결**
- PR: `flex-timetracking-backend/pull/11874`
- 같은 주 수요일에 배포 완료

**출처**: [CI-3998](https://linear.app/flexteam/issue/CI-3998)

---

### 교대근무 스케줄 게시 — 기존 휴가 있는 날 오류

**증상**
- 교대근무 스케줄 게시 시 "기타" 사유로 게시 불가
- 특정 날짜에 연차가 등록되어 있어 해당 날짜에 별도 입력한 내용이 없는데 게시 시 오류

**원인**
- `v2_user_shift_schedule_draft` 테이블의 `time_off_deletion` 필드에 삭제 예정 휴가 목록이 포함되어 있음
- 연차가 여러 날에 걸쳐 있을 때, 이미 편집 불가능한 날의 휴가 삭제가 포함되어 오류

**해결 방법**
```sql
UPDATE flex.v2_user_shift_schedule_draft
SET time_off_deletion = '[]'
WHERE id in ({draftIds})
  and customer_id = {customerId}
  and user_id = {userId};
```

**출처**: [CI-3997](https://linear.app/flexteam/issue/CI-3997)

---

### 모바일 BFF nullable 필드 500 에러

**원인 패턴**
- mobile-bff에서 TT API 응답 필드를 **non-null**로 선언했는데 실제로 **null 반환** → JSON 파싱 오류 → 500
- 특히 입사 전 기간 조회 시 발생 (3/1 조회인데 입사일이 3/5인 경우 해당 기간 데이터 null)

**확인 방법**
- BFF `/by-month` 엔드포인트 500 오류
- TT API swagger에서 `required = true` (별표) vs nullable 혼동 주의

**해결 방법**
- BFF에서 nullable로 처리하거나 TT DTO에서 필드 nullable 선언

**출처**: [CI-4051](https://linear.app/flexteam/issue/CI-4051)

---

### TT 엑셀 다운로드 타임아웃 — HTTP client 타임아웃 조정

**증상**
- 근무기록 관리에서 구성원 근무기록 다운로드 실패
- 권한이 있어도 다운로드 안 됨 → 타임아웃 오류

**원인**
- TT가 내부 API (storage) 호출 시 HTTP client 타임아웃 초과
- 휴가조회권한 있는 유저를 모두 조회하여 데이터량이 많을 때 발생

**해결 방법**
- `flex-timetracking-backend/pull/11985`: 해당 API 호출용 별도 retrofit 빈 생성 + 타임아웃 연장
- 임시: operation API로 직접 추출
- 관련 이전 작업: `flex-v2-backend-commons/pull/1114`

**출처**: [CI-4055](https://linear.app/flexteam/issue/CI-4055)

---

### 신승인 start-approval-process / produce-event 2PC 패턴

**스펙/규칙**
신승인 처리 시 2단계로 나뉨:
1. `startWithoutEventProduce` → `/start-approval-process`
2. `produceStartEvent` → `/start-approval-process/produce-event`

produce-event 실패 시 반드시 rollback:
- `/rollback-started` 호출 필요
- 코드: `ApprovalProcessCommandInternalService.rollbackStarted`

**비정상 상태 데이터 복구**
- `approval_process` 테이블에서 해당 건 soft delete
- `approval_replacement_target` 테이블에서도 soft delete
- TT 쪽 보상 처리 추가

**자주 오는 케이스**
- 노브랜드 CI-3951: 퇴직자 승인자 교체 → 승인에서 200인데 TT에서 400 → TT 테이블에 없는 상태
  - 원인: `/start-approval-process` 호출은 됐지만 `/produce-event`가 호출 안 됨
  - 해결: approval_process, approval_replacement_target soft delete + TT 보상 처리

**출처**: [CI-3951](https://linear.app/flexteam/issue/CI-3951)

---

### 단시간근로자 휴무일 연장근무 판단 기준

**스펙/규칙**
- 단시간 근로자의 **휴무일 연장근무 판단 기준**: `(주 소정근로시간 / 5)` 초과 시 일 연장
  - 과거 가이드라인 없어 주 소정근로시간/5 사용, 이후 8시간 기준으로 가이드 변경
  - PR: `flex-timetracking-backend/pull/7185` 참조
- 현재 구현: `(14 * 60 / 5)` = 2시간 48분 초과 시 일 연장으로 처리
  - 나머지 주 14시간 초과분은 주기 연장으로 처리

**주의**
- 휴무일 근무 시 연장 판단 기준 시간이 날짜별로 다르게 표시될 수 있음
- 고용노동부 가이드: 8시간 넘으면 연장

**출처**: [CI-4048](https://linear.app/flexteam/issue/CI-4048)

---

### 휴일대체 기간 설정 변경 — Operation

**API 패턴**
- 주휴일 / 공휴일 휴일대체 기간을 고객사 요청으로 변경

**제약**
- **공휴일 기간 단축**은 어려움 (이미 지정된 것 처리 이슈)
- **주휴일만 기간 연장** 가능 (기존 6일 → 전후 2주)

**Central Dogma 미러링 이슈**
- SSH 키가 특정 담당자 개인 키로 등록된 경우 담당자 퇴사/이직 시 미러링 실패
- 해결: 새 SSH 키 생성 → Central Dogma + GitHub 양쪽에 등록

**출처**: [CI-3897](https://linear.app/flexteam/issue/CI-3897)

---

### 오라클 연동 시 재직자/퇴직자 연차수당 분리 API

**배경**
- 미연수 9월 배포 이후 재직자/퇴직자 연차수당이 분리됨
- flex Open API로 연동하는 경우 재직자/퇴직자 모두 제공 중
- **외부 오라클 DB 연동**의 경우 외주사에서 만든 프로그램이 대응 안 된 것

**대응**
- flex 문제가 아니라 외주사 프로그램 수정 필요 → 외주사에 연락 요청
- 관련 API: Open API `getPayrollSettlementById` 참조

**출처**: [CI-3988](https://linear.app/flexteam/issue/CI-3988)

---

### 월차촉진 연도 경계 버그 (CI-3809 동일)

위의 [연차촉진 UTC/KST 연도 경계 버그](#연차촉진-utckst-연도-경계-버그) 참조.

월차 촉진도 동일한 패턴:
- 1/1 오전 8시(KST) 생성 → UTC로 저장 시 12/31 23:00으로 저장
- 2026년 목록 조회 시 누락 → 2025년으로 조회 시 확인 가능

**출처**: [CI-3809](https://linear.app/flexteam/issue/CI-3809)

---

### 연차 조정 일괄 취소 기능 누락

**증상**
- 연차 조정 내역을 개별 취소는 되지만 **일괄 취소 버튼 없음**

**현황**
- 미연수에는 있던 기능을 일반 연차 조정에는 슬쩍 넣음
- 이지선: side peek의 `...` 아이콘에서 일괄 취소 기능 추가 방향
- prod 배포 완료 (CI-3923)

**출처**: [CI-3923](https://linear.app/flexteam/issue/CI-3923)

---

### 휴가 코드 삭제 시 등록된 휴가 취소 스펙

**스펙/규칙**
- 교대근무 관리에서 **기사용 휴가 코드를 삭제**하면 → 등록된 휴가가 모두 취소됨
- **의도된 기능** (스펙)

**자주 오는 케이스**
- 테크타카로지스틱스 CI-4047: 교대근무 관리에서 휴가 코드 삭제 → 기등록 연차 모두 취소

**출처**: [CI-4047](https://linear.app/flexteam/issue/CI-4047)

---

## 공통 조사 패턴 (반복 사용)

### 세콘 데이터 확인 (메타베이스)
```
https://metabase.dp.grapeisfruit.com/question/3565?customerId={id}&date={date}&email={email}&provider_type=&work_event_type_only=0&order=1
```

### 알림 수신 여부 확인
```sql
select nd.*, n.notification_type
from notification_deliver nd
left join notification n on nd.notification_id = n.id
where nd.receiver_id = {userId}
and n.notification_type = '{type}'
and n.db_created_at >= '{date}';
```

### 연차촉진 대상 확인
```sql
select *
from annual_time_off_boost_history
where task_key = '{taskKey}';
```

### 승인 데이터 확인
```sql
-- 승인 이벤트
select *
from flex.v2_time_tracking_approval_event
where customer_id = {customerId}
and user_id = {userId}
and target_event_category = 'TIME_OFF'
and event_type = 'REGISTER';

-- 승인 프로세스
select *
from flex_flow.requested_todo_info
where customer_id = {customerId}
and reference_key in ('{taskKey1}', '{taskKey2}');
```
