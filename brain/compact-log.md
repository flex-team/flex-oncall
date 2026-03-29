# 컴팩션 이력

> ops-compact 스킬이 자동으로 기록한다. 오판 발견 시 git revert로 복원 가능.

| 날짜 | 티켓 | 기준 | 흡수된 신호 | 사유 |
|------|------|------|-----------|------|
| 2026-03-29 | CI-4229 | compact | d:syn+1 d:kw+2 | fins: transactedTime/시간정책 |
| 2026-03-29 | CI-4225 | compact | — (기존 g:pay-08 커버) | payroll: DAILY_BASE+paymentRatio |
| 2026-03-29 | CI-4209 | compact | d:syn+1 d:kw+2 | scheduling: WorkPlanTemplate/isInvalidSchedule |
| 2026-03-29 | CI-4217 | compact | d:syn+1 d:kw+2 | time-tracking: alteredHoliday/work-schedule-sync-to-es |
| 2026-03-29 | CI-4147 | compact | d:syn+1 d:kw+2 | time-tracking: lock_event/assign_times |
| 2026-03-29 | CI-4165 | compact | d:syn+1 d:kw+2 | integration: isDraftEventRegistrationAllowed/checkWorkClockStatus |
| 2026-03-29 | CI-3998 | compact | d:syn+1 d:kw+2 | shift: filterIsInstance/DraftTimeOff |
| 2026-03-29 | CI-4094 | compact | d:syn+1 d:kw+2 | time-tracking: actorNow/onTimeRecord |
| 2026-03-29 | CI-4222 | compact | d:syn+1 d:kw+3 | payroll: getYearEndTotalAmountByType/YEAR_END_REASON_CODES/74번코드 |
| 2026-03-29 | CI-4201 | compact | — (기존 g:dept-06 커버) | department: 예약발령 종료 차단 |
| 2026-03-29 | CI-4188 | compact | — (기존 g:review-03/04 커버) | review: UserForm 미초기화 |
| 2026-03-29 | CI-4174 | compact | — (기존 g:pay-05 커버) | payroll: 확정해제 리버트 누락 |
| 2026-03-29 | CI-4179 | compact | — (기존 g:fins-01 커버) | fins: 세금계산서 소급 동기화 |
| 2026-03-29 | CI-4176 | compact | d:syn+1 | account: OTP 해제 |
| 2026-03-29 | (74건) | bulk-compact | — | 오래된 archive 노트 일괄 d:st "C" 마킹 |
| 2026-03-29 | CI-4186 | R3 retire | — | CI-3897 동일 패턴 (주휴일 휴일대체 기간) |
| 2026-03-29 | CI-4199 | R3 retire | — | CI-3897/CI-4186 동일 패턴 |
| 2026-03-29 | CI-4200 | R3 retire | — | CI-4124 동일 패턴 (일괄 이메일 변경) |
| 2026-03-29 | QNA-1933-archive | R3 retire | — | QNA-1933 중복 copy |
