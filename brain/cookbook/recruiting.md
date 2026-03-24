# 채용 (Recruitment) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 채용사이트 subdomain 변경 요청 조회
SELECT * FROM flex_recruiting.site_subdomain_change
WHERE customer_id = ?
ORDER BY created_at DESC;
```

## 과거 사례

- **subdomain 변경 검토중 방치**: 온콜 담당자가 `#alarm-recruiting-operation` 알림을 모니터링하지 않아 9일간 방치. operation API로 즉시 승인 처리 — **운영 요청** [CI-4170]
