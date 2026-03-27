# 근무 기록 삭제/복구 — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 근무 기록 삭제 시 영향 테이블

- `v2_user_work_record_event` (근무 이벤트)
- `v2_user_work_record_event_block` (블럭)
- `v2_user_work_record_approval_content` (승인 문서)
- `v2_user_work_record_event_approval_mapping` (매핑)
- `v2_time_tracking_approval_event` (승인 상태)

## 휴가 기록 삭제 시 영향 테이블

- 부여/조정: `v2_user_custom_time_off_assign`, `v2_user_custom_time_off_assign_withdrawal`, `v2_customer_bulk_time_off_assign`, `v2_user_compensatory_time_off_assign`, `v2_user_compensatory_time_off_assign_times`, `v2_user_annual_time_off_adjust_assign`
- 사용: `v2_user_time_off_use`, `v2_user_time_off_event`, `v2_user_time_off_event_block`
- 연촉: `v2_annual_time_off_boost_setting`, `annual_time_off_boost_history`, `v2_user_annual_time_off_boost_evidence_record`
- 승인: `v2_time_off_approval_content`, `v2_time_off_approval_content_unit`, `v2_time_tracking_time_off_approval_content`
- ES: document 삭제 필요 (sync가 아닌 delete)

## FAQ

- 근무 기록 삭제 → 안 됨. 고객이 직접 처리
- 삭제 데이터 복구 → 별도 절차 문서 참조
- 휴가 기록 삭제 → DB 직접 건드리지 않음
- 변경 예정 근무유형 삭제 → 제품에서 한 명씩, 벌크는 operation API 필요
- 테스트 데이터 일괄 초기화 → 완전 삭제(hard delete) 불가. 벌크 업로드로 빈 값 덮어씌우기 workaround 가능 (UI상 시간 미표시) [CI-4239]

## 과거 사례

- **테스트 근무기록 완전 삭제 요청**: 첫 결제 후 테스트 중인 고객사가 실 근무 시작 전 테스트 데이터 삭제 요청. 정책상 hard delete 불가 → 벌크 업로드 빈 값 덮어씌우기로 UI상 초기화 가능. 근태 외 다른 데이터도 포함될 수 있으므로 VOC로 수집 — **스펙** [CI-4239]
