# 캘린더 연동 (Calendar Integration) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 캘린더 이벤트 매핑 확인
SELECT * FROM flex.v2_time_tracking_flex_calendar_event_map WHERE user_id = ?;
```
