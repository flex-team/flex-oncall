# 맞춤휴가 (Custom Time Off) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 맞춤휴가 부여 확인
SELECT * FROM flex.v2_user_custom_time_off_assign WHERE user_id = ? AND customer_id = ?;

-- 맞춤휴가 회수 확인
SELECT * FROM flex.v2_user_custom_time_off_assign_withdrawal WHERE customer_id = ?;

-- 일괄 부여 확인
SELECT * FROM flex.v2_customer_bulk_time_off_assign WHERE customer_id = ?;
```
