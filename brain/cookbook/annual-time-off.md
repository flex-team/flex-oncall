# 연차 (Annual Time Off) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 휴직 설정 확인
SELECT * FROM flex.user_leave_of_absence WHERE user_id = ?;

-- 연차 정책 확인
SELECT * FROM flex.v2_customer_annual_time_off_policy WHERE customer_id = ?;

-- 연차 사용 이벤트
SELECT * FROM flex.v2_user_time_off_event WHERE user_id = ? AND customer_id = ?;

-- 연차 조정 이력
SELECT * FROM flex.v2_user_annual_time_off_adjust_assign WHERE user_id = ?;
```

## 환경 재현 시 필요 테이블

- 입사일: `user_employee_audit`
- 근무유형: `v2_user_work_rule`, `v2_customer_work_rule`, `v2_customer_work_record_rule`
- 연차정책: `v2_customer_annual_time_off_policy`
- 연차사용/조정: `v2_user_time_off_event`, `v2_user_time_off_event_block`, `v2_user_annual_time_off_adjust_assign`
