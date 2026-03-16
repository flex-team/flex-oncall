# 운영 노트 인덱스

> 이슈 조사 시 전체 문서를 읽지 말고, 이 인덱스에서 키워드로 관련 문서를 찾아 해당 문서만 읽을 것.
> COOKBOOK.md는 도메인별 진단 가이드이므로 항상 먼저 참조.

## 도메인별 문서 목록

### 연차 촉진 (Annual Time-Off Promotion)

| 문서 | 요약 | 키워드 |
|------|------|--------|
| [CI-3777](./CI-3777-hidden-spec-issue.md) | 연차촉진 히든 스펙으로 알림/화면 불일치 | 연차촉진, 히든스펙, 알림 불일치, 관리자 종료, 필터링 |
| [CI-3809](./CI-3809-monthly-final-promotion-issue.md) | 월차 2차 완료 후 1차 알림 지속 발송 | 연차촉진, MONTHLY, MONTHLY_FINAL, 알림 지속, UTC/KST |
| [CI-3907](./CI-3907.md) | 연촉 문서 작성 필요시기 경과 후 알림 지속 | 연차촉진, boosted_at, 연도 경계, UTC/KST, 목록 누락 |
| [CI-3932](./CI-3932.md) | 등기임원인데 연차촉진 표시 — 정책 변경 후 잔존 | 연차촉진, PENDING_WRITE, 정책 변경, 등기임원, annual_time_off_boost_history |

### 알림 (Notification)

| 문서 | 요약 | 키워드 |
|------|------|--------|
| [CI-3910](./CI-3910.md) | 휴가 참조자 이메일 알림 미수신 | 알림, 이메일, 참조자, 승인자, 중복 제거, notification_deliver |
| [CI-3914](./CI-3914.md) | 이메일 CTA 클릭 시 할 일/홈피드 이동 기준 | 알림, 이메일, CTA, approve.refer, approved.refer, locale |

### 근태/휴가 (Time Tracking / Time Off)

| 문서 | 요약 | 키워드 |
|------|------|--------|
| [CI-3858](./CI-3858.md) | 보상휴가 부여 시 '부여가능한 시간 없음' | 보상휴가, forAssign, exceeded-work, 부여 불가 |
| [CI-3868](./CI-3868.md) | 포괄계약 시간만큼 공제 안 됨 | 포괄임금, 포괄계약, REGARDED_OVER, Range 분할, 월 중 변경 |
| [CI-3892](./CI-3892.md) | 교대근무 스케줄에서 여러날 휴가 미표시/배치 불가 | 교대근무, 여러날 휴가, 스케줄 편집, timeoffEventId, 소실 |
| [CI-3897](./CI-3897.md) | 휴일대체 지정 기간 변경 요청 | 휴일대체, gap, TrackingExperimentalDynamicConfig, 기간 커스텀 |
| [CI-3949](./CI-3949.md) | 휴일대체 탭에 날짜 미표기 | 휴일대체, OpenSearch, holidayProps, sync, v2_user_work_rule, DayWorkingType |
| [CI-3976](./CI-3976.md) | 퇴사자 휴가 사용일자 데이터 추출 | 퇴사자, 휴가, 엑셀, Operation API, departmentIds, includeResignatedUsers |
| [CI-4048](./CI-4048.md) | 초단시간 근로자 연장근무 9시간 발생 | 초단시간, 연장근무, agreedWorkingMinutes, requiredWorkingMinutes |
| [CI-4120](./CI-4120.md) | 휴직/휴가 검증 비대칭 — 휴직→휴가 차단되나 휴가→휴직은 허용 (스펙) | 휴직, 휴가, 비대칭 검증, LeaveOfAbsence, TimeOff, 서비스 경계, Prevention forward |
| [CI-4121](./CI-4121.md) | sk 케미칼 근무 기록 다운로드 실패 (타임아웃 의심) | 근무 기록, 다운로드, 엑셀, 타임아웃, export, sk 케미칼 |

### 스케줄링 (Scheduling)

| 문서 | 요약 | 키워드 |
|------|------|--------|
| [CI-3839](./CI-3839.md) | 주 연장근무 발생 원인 확인 | 연장근무, agreedWorkingMinutes, requiredWorkingMinutes, 스케줄 |
| [CI-3862](./CI-3862.md) | 주휴일 배치 초과 허용인데 근무표 게시 제한 | 게시 차단, dry-run, validationLevel, WARN, ERROR |
| [CI-3866](./CI-3866.md) | 스케줄 게시 후 정시 전 출근 불가 미작동 | 정시 전 출근 불가, 게시, 임시 저장, v2_user_non_repetitive_work_plan |

### 교대근무 (Shift)

| 문서 | 요약 | 키워드 |
|------|------|--------|
| [CI-4103](./CI-4103.md) | 교대근무 관리 화면 조회 권한 일부 누락 | 교대근무, 조회 권한, 근무 권한, 휴가 권한, 교집합, access-check |
| [CI-4119](./CI-4119.md) | 교대근무 휴무일+스케줄 근무 시 퇴근 자동 조정 실패 | 교대근무, 휴무일, 스케줄, 퇴근 자동 조정, baseAgreedDayWorkingMinutes, 연장근무, 세콤 |

### 계정/구성원 (Account / Member)

| 문서 | 요약 | 키워드 |
|------|------|--------|
| [CI-4118](./CI-4118.md) | 서울히어로즈 관리자 계정 이메일 변경 요청 (퇴사자 계정) | 관리자, 이메일 변경, 퇴사자, 스폰서십, 온보딩, Operation API, UserEmailChange |

### 외부 연동 (Integration / SECOM)

| 문서 | 요약 | 키워드 |
|------|------|--------|
| [CI-3849](./CI-3849.md) | 세콤 연동 활성화 풀림 및 수동 전송 미반영 | 세콤, 연동 비활성화, 수동 전송, 소급 불가 |
| [CI-3861](./CI-3861.md) | 세콤 수동 전송 미반영 | 세콤, 수동 전송, 역순 수신, 위젯 draft |
| [CI-3979](./CI-3979.md) | 세콤 퇴근 타각 시 근무 기록 시간 조정 | 세콤, 퇴근 타각, 시간 조정, 근무 기록 |
| [external-work-clock-event-failure-20260304](./external-work-clock-event-failure-20260304.md) | 외부 타각기 위젯 이벤트 처리 실패 (53건) | 세콤, CAPS, WORK_STOP, consumer 실패, 외부 타각기 |
| [QNA-1842](./QNA-1842.md) | 출입연동 커넥션 수 설정 | 출입연동, 커넥션 수, PostgreSQL, 세콤 |

### 승인 (Approval)

| 문서 | 요약 | 키워드 |
|------|------|--------|
| [CI-3951](./CI-3951.md) | 퇴직자 승인자 교체 — 승인 대기 건 확인 불가 | 퇴직자, 승인자 교체, 승인 대기, 데이터 불일치 |

### 권한 (Permission)

| 문서 | 요약 | 키워드 |
|------|------|--------|
| [TT-16674](./TT-16674.md) | 실시간 기록 조회 권한 분기 처리 | 권한, DomainAuthorityModel, AccessCheckApiService, 실시간 기록 |
