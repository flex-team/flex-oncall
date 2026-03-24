# 용어집 (Glossary)

> 사용자/CS가 사용하는 표현 → 시스템 내 정식 용어 → 도메인 매핑.
> 이슈 인입 시 키워드 매칭에 활용. domain-map.ttl의 glossary 항목과 동기화된다.
>
> 출퇴근~Kafka/이벤트 섹션 출처: [Notion 온콜 가이드](https://www.notion.so/flexnotion/4e9ee4da0cf44dc0ba9542df30ca976c)

## 알림 (Notification)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 알림이 안 왔어요 | notification_deliver 수신자 역할 확인 | flex-pavement-backend |
| 메일 못 받았어요 | SES Delivery 확인 (flex-prod-ses-feedback-*) | flex-pavement-backend |
| 알림 클릭 시 이상한 곳으로 이동해요 | CTA locale 확인 (approve.refer vs approved.refer) | flex-pavement-backend |
| 메타베이스에서 알림 내용이 안 보여요 | Core 알림 title_meta_map 빈값 — 스펙 | flex-pavement-backend |

## 연차촉진 (Annual Time-Off Promotion)

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
| 근무유형 적용 시 오류가 나요 | v2_user_work_rule 마지막 이벤트 CANCEL 여부 확인 → 매핑 없는 상태면 데이터 보정 | flex-timetracking-backend |
| 대휴 기간 설정해주세요 | 주휴일 휴일대체 gap 커스텀 — customGapOfWeeklyHoliday config 변경 | flex-timetracking-config |

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
| ODBC 연결이 안 돼요 | `v2_customer_external_provider.odbc_connection_limit` 확인 — 0이면 CONNECTION LIMIT 0으로 전체 차단. Operation API로 변경 | flex-timetracking-backend |
| 캡스 연결이 안 돼요 / 방화벽 해제 방법 | CAPS 연동 연결 실패 — PW 오입력 or 방화벽 | flex-timetracking-backend |
| flex IP 주소 알려주세요 | IP 제공 불가 — 도메인 기반 예외처리 안내 | flex-timetracking-backend |

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
| 결제 취소 후 로그인이 안 돼요 | raccoon billing operation `force-open` → 카드 재등록 → `close-forced-open` | flex-raccoon |

## 조직 관리 (Department)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 구성원이 없는데 조직 종료가 안 돼요 | 예약발령 잔존 — 발령 실행 후 종료 처리, 또는 발령 취소 후 종료. DEPA_400_017 에러 | flex-core-backend |

## 승인 (Approval)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 퇴직자 승인자 교체 알림이 뜨는데 실제 건이 없어요 | 고아 승인 요청 target_uid 확인 메타베이스 #309 | flex-timetracking-backend |
| 승인 설정/라인 확인해주세요 | customer_workflow_task_template + _stage 테이블 조회 | flex-core-backend |
| 승인은 완료됐는데 데이터가 안 바뀌었어요 | cloud_event_entity → re-produce-messages Operation API | flex-timetracking-backend |
| 위젯 종료 시 승인이 안 돼요 | 기본 근무일 위젯 종료 시 승인 미발생 — 스펙 | flex-timetracking-backend |
| 승인 완료인데 진행중으로 보여요 | approval_process APPROVED인데 workflow_task ONGOING — 이벤트 동기화 실패. `sync-with-approval` Operation API로 보정 | flex-core-backend |
| 경력/학력 변경 댓글이 사라져요 / 중복으로 보여요 | FE가 UserDataApproval activities API를 sort=ASC&size=1로 호출하여 댓글 누락 — FE 버그 | flex-core-backend, flex-flow-backend |
| 승인 댓글이 보였다 사라졌다 해요 | FE activities 조회 size 파라미터 부족 — sort=ASC&size=1 요청이 action history만 반환, 댓글 제외 | flex-core-backend, flex-flow-backend |

## 평가 (Evaluation / Performance Management)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 리뷰 다운로드 | ReviewSetExcelService.getReviewSetAsExcel() — 리뷰셋 단위 엑셀 | flex-review-backend |
| 마감 리뷰 | progressStatus IN (ANSWER_NOT_OPEN, ANSWER_OPEN) | flex-review-backend |
| 평가지 생성 중 | evaluation_reviewer.user_form_ids = [] — UserForm 미초기화 상태 | flex-review-backend |
| 평가지가 안 보여요 | 후발 추가 reviewer의 UserForm lazy initialization 미트리거. Operation API `initialize-user-form`으로 해결 | flex-review-backend |
| 삭제된 평가 복구해주세요 | `evaluation` 테이블 soft delete 방식. `deleted_at = NULL, deleted_user_id = NULL`로 복구. `draft_evaluation`도 동일 구조. Operation API PR #5181 머지 후 API 복구 가능 | flex-review-backend |

## 데이터 추출 (Data Export)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 엑셀 다운로드가 안 돼요 | OkHttp 소켓 타임아웃 3초 core-api 확인 | flex-timetracking-backend |

## 목표 (Goal/OKR)

> 출처: [Notion 목표 리스트 API 연동 가이드](https://www.notion.so/flexnotion/API-26c0592a4a928059b6b0c1c401751d4f)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 다른 연도 목표가 보여요 | cross-year 트리 hit=false 회색 표시 — 스펙 | flex-goal-backend |
| 회색 목표가 뭐예요? | hit=false root-objectives API — detail null이거나 hit false여도 hasChild true면 노출 | flex-goal-backend |
| 내 목표가 안 보여요 | User Grouped API grouping 확인 (companyObjectives/departmentObjectives/personalObjectives/memberObjectives) | flex-goal-backend |
| 목표 검색 결과가 다르게 나와요 | 검색 시 트리/그룹핑 해제 — Search API 플랫 리스트 반환 | flex-goal-backend |
| 목표가 너무 많아서 안 나와요 | User Grouped API 최대 500건 제약 / Aside Root API 최대 5,000건 제약 | flex-goal-backend |
| 전체 목표에서 조직 선택하면 다르게 보여요 | Aside Root Objective API — 서버 트리 연산 후 최상위 목표 한번에 반환 | flex-goal-backend |
| 하위 목표가 안 펼쳐져요 | Search API ancestorObjectiveIds로 하위 탐색 — 클라이언트 트리 구성 | flex-goal-backend |

## 비용관리 (Expense Management / Fins)

> 출처: [CI-4179](./notes/CI-4179.md), [CI-4071](./notes/archive/CI-4071.md)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 세금계산서가 안 들어와요 | 국세청 스크래핑 수집 범위 확인 (최근 12개월) + 운영 도구 동기화 | flex-fins-backend |
| 이전 카드 내역 연동해주세요 | 카드사 연동 상태 확인 → 운영 도구로 희망 기간 동기화 | flex-fins-backend |
| 카드 부분 취소가 전체 취소로 나와요 | 카드사별 취소금액 필드 처리 확인 (하나카드 hotfix 이력) | flex-fins-backend |

## 급여 (Payroll)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 초과근무 계산이 이상해요 | 올림 자릿수 payroll_legal_payment_setting 확인 | flex-payroll-backend |
| 정산 수정했는데 소득세가 바뀌었어요 | 부양가족 수 최신화 dependent_families_count — 스펙 | flex-payroll-backend |
| 급여정산 해지하면 명세서 공개가 되나요? | 구독 해지 후 payslip 공개/알림 동작 — 스펙 | flex-payroll-backend |
| 건강보험 제외 대상인데 중도정산 시 사회보험 금액이 들어가요 | 중도정산 확정해제 시 사회보험 연말정산 금액 미리버트 — 버그(핫픽스 완료) | flex-payroll-backend |

## 근로기준법 용어 (Labor Law Terms)

> 출처: [Notion Tracking 도메인 지도](https://www.notion.so/flexnotion/Tracking-8b40cec73dcc4b1db1e6123569d7b9ce)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 소정근로시간이 뭐예요? | agreedWorkingMinutes — 회사와 근무자가 약속한 일하는 시간 (일반 사무직: 주 40시간, 일 8시간) | flex-timetracking-backend |
| 법정근로시간이 뭐예요? | statutoryWorkingMinutes — 법으로 지정한 최대 소정근로시간 (성인: 일 8시간/주 40시간, 연소: 일 7시간/주 35시간) | flex-timetracking-backend |
| 필수근로시간이 뭐예요? | requiredWorkingMinutes — 소정근로시간에 휴일대체·입퇴사·휴직 반영한 실제 근로 목표 시간 | flex-timetracking-backend |
| 계약근로시간이 뭐예요? | usualWorkingMinutes — 근로계약서상 일 근무시간. 소정근로시간 초과 가능하나 법정최대 초과 불가 | flex-timetracking-backend |
| 법정최대근로시간이 뭐예요? | maxStatutoryTotalWorkingMinutes — 법정근로(40H) + 법정최대연장(12H) = 주 52시간 | flex-timetracking-backend |
| 목표근로시간이 뭐예요? | 1.0 용어로 2.0에서 폐기. requiredWorkingMinutes(필수근로시간)로 대체. UI에서는 아직 사용되기도 함 | flex-timetracking-backend |
| 초과근로가 뭐예요? | 연장·야간·휴일 근로의 총칭. 시간외 근로라고도 불림 | flex-timetracking-backend |
| 연장근로 계산이 이상해요 | 일 단위(일 8시간 초과) + 주기 단위(주 40시간 초과) 이중 판단. 선택적 근무는 일 단위 연장 없음 | flex-timetracking-backend |
| 야간근로 가산이 이상해요 | 22시~06시 사이 근로, 0.5배 가산. 연장+야간 중복 시 1.0배 | flex-timetracking-backend |
| 휴일근로 가산이 이상해요 | 휴일 근로 0.5배 가산. 단, 주기 연장과 중복 시 0.5배만(연장 가산 미적용). 일 단위 연장은 별도 적용 | flex-timetracking-backend |
| 포괄임금 설정이 뭐예요? | flex 제품의 '포괄계약 근로시간 설정'은 실제로 고정OT 계약 (항목별 시간 명시). 포괄임금제와 다름 | flex-timetracking-backend |
| 보상휴가 시간이 이상해요 | 가산율 포함 시간 기준 부여 (예: 8시간 연장 × 1.5 = 12시간). 미사용 시 수당 지급 의무 있음 | flex-timetracking-backend |
| 단시간 근로자 연장이 이상해요 | 단시간 근로자는 소정근로시간 초과 시 연장근로 발생 (통상근로자는 법정근로시간 초과 기준) | flex-timetracking-backend |
| 초단시간 근로자 연차/주휴가 없어요 | 주 15시간 미만 → 퇴직금·연차·주휴일/주휴수당 의무 없음 — 스펙 | flex-timetracking-backend |
| 휴일 대체가 안 돼요 | 주휴일 대체는 6일 이내, 근로자의날은 대체 불가. 사전 24시간 통보 필수 | flex-timetracking-backend |
| 연차 촉진 절차가 뭐예요? | 3종류: 연차 촉진(소멸 6개월 전), 월차 1차(3개월 전), 월차 2차(1개월 전). 노무수령거부 의사표시 필요 | flex-timetracking-backend |
| 연차수당이 이상해요 | = 연차휴가미사용수당. 소멸된 연차 금전 보상. 퇴직 시 입사일 기준 재정산 가능(취업규칙 단서 필요) | flex-payroll-backend |

## 출퇴근 (Work Clock)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 출근/퇴근 버튼이 안 돼요 | work-clock start/stop API dry-run 응답 확인 | flex-timetracking-backend |
| 근무 위젯이 안 보여요 | work-clock current-status API 확인 | flex-timetracking-backend |
| 출근 타각을 취소하고 싶어요 | work-clock 개별 취소 UI 제공 (API도 존재) | flex-timetracking-backend |
| 자동 퇴근이 안 됐어요 | auto clock-out 설정 확인 | flex-timetracking-backend |

## 근태 대시보드 (Dashboard)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 근태 대시보드가 안 맞아요 | OpenSearch work-schedule document sync 확인 | flex-timetracking-backend |
| 휴가 사용 내역이 안 맞아요 | OpenSearch time-off-use document sync 확인 | flex-timetracking-backend |
| 대시보드 동기화가 필요해요 | POST /action/operation/v2/time-tracking/sync-es-work-schedule | flex-timetracking-backend |

## 연차 (Annual Time Off)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 잔여 연차가 이상해요 | operation API annual-time-off bucket 확인 | flex-timetracking-backend |
| 연차 지급/사용 내역 다운로드 | 제품 6개월씩 다운로드 또는 Metabase | flex-timetracking-backend |
| 연차 소멸일이 이상해요 | bucket 유효기간 확인 (종료일 이른 것 우선 소진) | flex-timetracking-backend |
| 휴가 내역에 사용일수가 0일이에요 | 휴일/휴직/휴일대체/주휴일/쉬는날 겹침 확인 | flex-timetracking-backend |

## 맞춤휴가 (Custom Time Off)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 맞춤휴가 잔여일이 이상해요 | v2_user_custom_time_off_assign 부여/회수/사용 확인 | flex-timetracking-backend |
| 맞춤휴가 합치고 싶어요 | 회수 후 재부여 권장. 합쳐쓰기는 assign 속성 동일 필요 | flex-timetracking-backend |
| 맞춤휴가 단위 변경하고 싶어요 | 회수 후 재부여 또는 assign 테이블 직접 변경 | flex-timetracking-backend |

## 근무지 (Work Place)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| GPS 밖에서 출근이 됐어요 | workplace 테이블 GPS 설정 + 관리자 IP 제한 패스 확인 | flex-timetracking-backend |
| 근무지 IP가 통과해요 | flex_auth.customer_ip_access_control_setting 확인 | flex-timetracking-backend |
| 출근 버튼이 안 눌려요 (위치 제한) | dry-run 로그 없이 current-status만 있으면 범위 바깥 | flex-timetracking-backend |

## 휴일 (Holiday)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 휴일이 안 보여요 | v2_user_holiday_group_mapping + v2_customer_holiday 확인 | flex-timetracking-backend |
| 휴일대체 기간이 안 맞아요 | flex-timetracking-config experimental.json gap 설정 | flex-timetracking-backend |
| 근로자의날 삭제해주세요 | operation API로 제거 (PR #7421 참조) | flex-timetracking-backend |
| 대체휴일이 적용 안 돼요 | v2_customer_holiday support_alternative 설정 확인 | flex-timetracking-backend |

## 캘린더 연동 (Calendar Integration)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| 구글 캘린더에 휴가가 안 떠요 | v2_time_tracking_flex_calendar_event_map 확인 | flex-timetracking-backend |
| 캘린더 연동이 안 돼요 | GoogleCalendarEventAdapter → FlexCalendarSyncEventConsumer 파이프라인 확인 | flex-timetracking-backend |

## Kafka / 이벤트 (Event Processing)

| 사용자 표현 | 시스템 용어 | 서브모듈 |
|------------|------------|---------|
| Kafka 컨슘 에러 발생 | message_consume_log ce_id로 operation API 재발행 | flex-timetracking-backend |
| 사용자 변경 이벤트 실패 | Workspace Operation API /action/operation/v2/workspace/users/produce 호출 (productType=USER) | flex-core-backend |
