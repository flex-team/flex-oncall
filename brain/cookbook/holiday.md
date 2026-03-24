# 휴일 (Holiday) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 유저의 휴일 그룹 매핑
SELECT * FROM flex.v2_user_holiday_group_mapping WHERE user_id = ?;

-- 휴일 그룹 상세
SELECT * FROM flex.v2_customer_holiday_group WHERE customer_id = ?;

-- 개별 휴일 목록
SELECT * FROM flex.v2_customer_holiday WHERE customer_holiday_group_id = ?;

-- 휴일대체 이벤트
SELECT * FROM flex.v2_time_tracking_user_alternative_holiday_event WHERE user_id = ?;
```
