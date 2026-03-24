# 근무지 (Work Place) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- GPS/근무지 설정 확인
SELECT * FROM flex.workplace WHERE customer_id = ?;

-- IP 제한 설정 확인
SELECT * FROM flex_auth.customer_ip_access_control_setting WHERE customer_id = ?;
```
