# 스케줄링 (Scheduling) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 일별 게시된 스케줄
SELECT * FROM v2_user_non_repetitive_work_plan
WHERE customer_id = ? AND user_id = ? AND date = ?;

-- 게시 이벤트
SELECT * FROM v2_user_work_plan
WHERE customer_id = ? AND user_id = ?;

-- 임시 저장된 스케줄 (게시 전)
SELECT * FROM v2_user_shift_schedule_draft
WHERE customer_id = ? AND user_id = ? AND date = ?;
```

## 과거 사례

- **주휴일 없는 게시 차단**: BE는 WARN 반환 정상, FE가 WARN=ERROR 처리 — **버그 (FE)** [CI-3862]
- **게시 안 된 스케줄 + 정시 전 출근 불가**: 임시 저장은 게시 아님, 정시 기준 제공 안 함 — **스펙** [CI-3866]
- **주 연장근무 비대칭**: 근무규칙 기반(40h) vs 스케줄 기반(32h) 계산 차이 — **보류** [CI-3839]
