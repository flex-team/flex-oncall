# 용어집 (Glossary)

> 사용자/CS가 사용하는 표현 → 시스템 내 정식 용어 → 도메인 매핑.
> 이슈 인입 시 키워드 매칭에 활용. domain-map.ttl의 glossary 항목과 동기화된다.

## 알림 (Notification)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 알림이 안 왔어요 | notification_deliver 수신자 역할 확인 | flex-pavement-backend |
| 메일 못 받았어요 | SES Delivery 확인 (flex-prod-ses-feedback-*) | flex-pavement-backend |
| 알림 클릭 시 이상한 곳으로 이동해요 | CTA locale 확인 (approve.refer vs approved.refer) | flex-pavement-backend |
| 메타베이스에서 알림 내용이 안 보여요 | Core 알림 title_meta_map 빈값 — 스펙 | flex-pavement-backend |

## 연차 촉진 (Annual Time-Off Promotion)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 연차 사용 계획 작성 알림이 계속 와요 | annual_time_off_boost_history status/boosted_at 확인 | flex-timetracking-backend |
| 촉진 문서가 화면에 안 보여요 | 히든 스펙 필터링 확인 | flex-timetracking-backend |
| 연차 대상이 아닌데 촉진 알림이 와요 | 정책 변경 후 PENDING_WRITE 잔존 확인 | flex-timetracking-backend |

## 근태/휴가 (Time Tracking)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 휴일대체 기간이 안 맞아요 | TrackingExperimentalDynamicConfig gap 설정 확인 | flex-timetracking-backend |
| 보상휴가 부여 안 돼요 | forAssign exceeded-work 부여가능 시간 확인 | flex-timetracking-backend |
| 포괄 공제가 안 맞아요 | REGARDED_OVER Range 분할 월 중 변경 확인 | flex-timetracking-backend |
| 휴일대체 탭에 날짜가 안 보여요 | OpenSearch holidayProps sync v2_user_work_rule 확인 | flex-timetracking-backend |
| 퇴근 시간이 잘렸어요 | 다음날 종일휴가 자정 조정 adjustWorkClockStopTime | flex-timetracking-backend |
| 퇴근이 정시로 찍혀요 | work-clock.stop.preference=ON_TIME v2_time_tracking_user_config | flex-timetracking-backend |
| 추천 휴게가 안 들어가요 | 선택적 근무 실시간 기록 시 추천 휴게 미입력 — 스펙 | flex-timetracking-backend |
| 연차 사용 내역이 사라졌어요 | 부여 시작일 이전 미표시 grant_start_date | flex-timetracking-backend |
| 퇴사자 휴가 데이터 추출해주세요 | Operation API departmentIds includeResignatedUsers | flex-raccoon |

## 스케줄링 (Scheduling)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 스케줄 게시가 안 돼요 | dry-run API validationLevel WARN/ERROR 확인 | flex-timetracking-backend |
| 정시 전 출근 불가가 안 먹혀요 | 임시 저장 vs 게시 v2_user_non_repetitive_work_plan 확인 | flex-timetracking-backend |
| 연장근무가 이상해요 | agreedWorkingMinutes requiredWorkingMinutes 비교 | flex-timetracking-backend |

## 교대근무 (Shift)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 교대근무 관리 화면에서 일부 구성원만 조회됩니다 | 근무 권한 + 휴가 권한 교집합 access-check | flex-timetracking-backend |
| 퇴근 자동 조정이 안 돼요 | baseAgreedDayWorkingMinutes 휴무일 연장근무 확인 | flex-timetracking-backend |

## 외부 연동 (Integration)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 세콤 연동이 풀렸어요 | 비활성화 기간 데이터 소급 불가 — 스펙 | flex-timetracking-backend |
| 수동 전송했는데 반영 안 돼요 | 이벤트 수신 순서 역순 확인 | flex-timetracking-backend |
| 세콤으로 퇴근했는데 정시로 찍혀요 | 퇴근 타각 자정 조정 preference=ON_TIME | flex-timetracking-backend |

## 권한 (Permission)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 누가 언제 권한을 부여했는지 확인해주세요 | flex_grant_subject created_at/created_by + Envers 이력 | flex-core-backend |
| 감사로그에서 권한 변경이 안 보여요 | 물리 삭제로 Envers 미기록 — 스펙 | flex-core-backend |

## 계정/구성원 (Account / Member)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 이메일 변경해주세요 | Operation API UserEmailChange (단건) | flex-raccoon |
| 구성원 이메일 일괄 변경해주세요 | Operation API 일괄 이메일 변경 | flex-raccoon |

## 승인 (Approval)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 퇴직자 승인자 교체 알림이 뜨는데 실제 건이 없어요 | 고아 승인 요청 target_uid 확인 메타베이스 #309 | flex-timetracking-backend |

## 데이터 추출 (Data Export)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 엑셀 다운로드가 안 돼요 | OkHttp 소켓 타임아웃 3초 core-api 확인 | flex-timetracking-backend |

## 목표 (Goal/OKR)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 다른 연도 목표가 보여요 | cross-year 트리 hit=false 회색 표시 — 스펙 | flex-goal-backend |
| 회색 목표가 뭐예요? | hit=false root-objectives API Matrix 필터 | flex-goal-backend |

## 급여 (Payroll)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 초과근무 계산이 이상해요 | 올림 자릿수 payroll_legal_payment_setting 확인 | flex-payroll-backend |
| 정산 수정했는데 소득세가 바뀌었어요 | 부양가족 수 최신화 dependent_families_count — 스펙 | flex-payroll-backend |
| 급여정산 해지하면 명세서 공개가 되나요? | 구독 해지 후 payslip 공개/알림 동작 — 스펙 | flex-payroll-backend |
