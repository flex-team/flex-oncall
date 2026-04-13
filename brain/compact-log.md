# 컴팩션 이력

> ops-compact 스킬이 자동으로 기록한다. 오판 발견 시 git revert로 복원 가능.

| 날짜 | 티켓 | 기준 | 흡수된 신호 | 사유 |
| 2026-04-13 | (전체) | ops-compact | 농축 0건, 퇴출 0건, COOKBOOK 강등 0건, 승격 0건 | Step 2: archive 신규 스캔 시 ttl 미등록 9건 탐지(CI-4165/4172/4181/4186/4197/4199/4200/4208/QNA-2004) — 전수 확인 결과 **이미 2026-03-29~04-03 기간에 R1/R3 retire 완료된 항목**. 재추가 방지 주의. Step 3: R2 90일 경과 노트 없음(최고령 d:ca 2026-03-24). Step 4: 히트 0 플로우(F-pay-2 CI-4240 d:ca 2026-04-03, F7 CI-4314, F5 CI-4312) 모두 추가일 60일 미경과로 강등 대상 아님. Tier-2→Tier-1 승격 후보 없음. Step 6: 신선도 검증 생략(직전 실행 2026-04-08 유지) |
| 2026-04-11 | CI-4342,CI-4345,CI-4353,CI-4371,CI-4372,CI-4374,CI-4375,CI-4376,CI-4379,CI-4384 | maintain+compact | 농축 10건 d:st "C" | maintain-notes: 10건 아카이브. CI-4342(ops 승인정책교체), CI-4345(wontfix 전자계약), CI-4353(ops 캡스역순수신), CI-4371(ops Matrix재색인), CI-4372(spec 위젯설정), CI-4374(ops 연장근무), CI-4375(bug 퇴사자노출), CI-4376(code-fix 평가빈박스), CI-4379(spec 샘플근무유형), CI-4384(known-issue 대시보드불일치). COOKBOOK 추가 스킵 — 대부분 기존 패턴 또는 code-fix |
| 2026-04-08 | (전체) | ops-compact | 농축 0건, 퇴출 0건, COOKBOOK 강등 0건, 승격 0건 | Step 2: archive 노트 전체 d:st "C" 완료 상태. Step 3: R2 90일 경과 노트 없음(최고령 d:ca 2026-03-24), R1/R3 이전 컴팩션에서 처리됨. Step 4: 히트 0인 F-pay-2는 추가일 2026-03-30 기준 60일 미경과로 강등 대상 아님. Tier-2→Tier-1 승격 대상 없음. |
| 2026-04-07 | CI-4335, CI-4338 | maintain+compact | COOKBOOK review 질문수정 S3+S7, account 알림 스펙 d:st C | maintain-notes: 2건 아카이브. CI-4338 구리뷰 질문 텍스트 수정 DML 패턴 COOKBOOK 추가 + cookbook/review.md SQL 템플릿. CI-4335 Not a Bug 확정 |
| 2026-04-06 | CI-4117, CI-4227, CI-4256 | dup-clean | — | domain-map.ttl 중복 항목 3건 제거 (이전 compact 시 구 항목 미삭제 잔존) |
| 2026-04-04 | CI-4304 | compact | COOKBOOK 대시보드-F2 신규 | time-tracking: 고스트 periodicWorkSchedule 조회 미필터링 패턴. 재동기화 불가 핵심 |
| 2026-04-04 | CI-4301 | compact | COOKBOOK 평가-F2 히트+1 | review: CI-4188 동일 패턴 재발, 히트율 반영 |
| 2026-04-04 | CI-4297 | compact | COOKBOOK 전자계약 체크리스트 8번 추가 | contract: hyphen 포함 전화번호 renderer 미치환 + placeholder 암호화 패턴 |
| 2026-04-04 | CI-4117 | compact | COOKBOOK 평가-F3 히트+1 | review: 등급 validation 코드픽스, 히트율 반영 |
| 2026-04-04 | CI-4259 | compact | — (code-fix, COOKBOOK 스킵) | time-tracking: all-day event UTC 타임존 버그. 코드 수정으로 해결 |
| 2026-04-04 | CI-4227 | compact | — (code-fix, COOKBOOK 스킵) | payroll: backfill 누락. PR #8691 코드 수정으로 해결 |
| 2026-04-04 | CI-4307,CI-4309,CI-4259(old) | dup-clean | — | domain-map.ttl 중복 항목 3건 제거 |
|------|------|------|-----------|------|
| 2026-04-03 | CI-4172 | R1 retire | — | integration: 세콤 퇴근 후 근무 확정 시 GPS null 검증 누락 버그. 코드 수정, COOKBOOK 미등록 |
| 2026-04-03 | CI-4181 | R1 retire | — | approval: ApprovalPolicy.update() 교체 흐름 validateHasCustomerSuperAdmin 오류. 코드 수정, COOKBOOK 미등록 |
| 2026-04-03 | CI-4208 | R1 retire | — | payroll: 원천징수확인서 발급번호 자동채번 미지원, 서식 수정. COOKBOOK 미등록 |
| 2026-04-03 | MEMO-20260320 | compact | d:st "C" 설정 | annual-promotion: 연차촉진 크론 간헐적 OkHttp 타임아웃. 모니터링 메모 보존 |
| 2026-04-03 | CI-4025, CI-4096, CI-4164 | compact | d:st "C" + d:ca | maintain-notes: 3건 아카이브 — CI-4025(expected-behavior), CI-4096(wont-fix), CI-4164(bug+code-fix) |
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
| 2026-04-13 | CI-4389 | compact | — | goal: 목표 마이그레이션 스펙 확인 (Not a Bug) |
| 2026-04-13 | CI-4404 | compact | — | review: 평가 등급 산출 상태 경합 스펙 확인 |
