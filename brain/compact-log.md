# 컴팩션 이력

> ops-compact 스킬이 자동으로 기록한다. 오판 발견 시 git revert로 복원 가능.

| 날짜 | 티켓 | 기준 | 흡수된 신호 | 사유 |
|------|------|------|-----------|------|
| 2026-04-02 | CI-4197 | R1 retire | — | payroll: FE 포커스 버그, 핫픽스(#1708) 완료, COOKBOOK 미등록, 재현 불가 |
| 2026-04-02 | CI-4165 | R3 retire | — | integration: CI-4207 동일 원인(checkWorkClockStatus PR #12058), COOKBOOK이 CI-4207 대표 등록 |
| 2026-04-01 | CI-4178 | orphan-compact | d:v, d:st "C" 설정 | payroll: CI-4174 동일 원인 재정산 버그. 파일 없는 orphan 항목 정리 |
| 2026-03-31 | (38건) | bulk-compact | d:syn+7 d:kw+11 | 농축 미완료 archive 노트 일괄 d:st "C" 마킹 + syn/kw 흡수 + 활동 로그 17건 정제 |
| 2026-03-31 | CI-4148 | compact | d:syn+1 d:kw+2 | time-tracking: UserWorkRuleAllowCancelMappingCalculator 예약 취소 검증 버그. COOKBOOK 체크리스트 19번 추가 |
| 2026-03-31 | CI-4132 | compact | d:syn+1 d:kw+2 | shift: DailyShiftConverter/timeBlockGroups 정렬 버그. COOKBOOK 체크리스트 5번 추가 |
| 2026-03-31 | CI-4151 | compact | d:kw+3 | payroll: 76번코드/HealthInsuranceSettlementReasonCode 2중합산. COOKBOOK 체크리스트 13번 추가 |
| 2026-03-31 | CI-4159 | compact | d:syn+1 d:kw+2 | payroll: HealthInsuranceMonthsCalculator 병합 누락. COOKBOOK 체크리스트 14번 추가 |
| 2026-03-30 | CI-4226 | compact | d:syn+2 | account: 엑셀 미리보기 중복 표현 흡수. code-fix이지만 COOKBOOK 진단 체크리스트 추가 |
| 2026-03-30 | CI-4238 | compact | — (기존 g:review-08/09 커버) | review: reviewee_evaluation_item 버그. COOKBOOK 체크리스트 추가 |
| 2026-03-30 | CI-4239 | compact | d:syn+1 | time-tracking: 테스트 근무기록 삭제 표현 흡수 |
| 2026-03-30 | CI-4245 | compact | — (g:acct-09 갱신) | account: 겸직 스펙 확정. g:acct-09 내용 업데이트 |
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
