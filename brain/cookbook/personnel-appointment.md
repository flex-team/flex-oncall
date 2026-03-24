# 인사발령 (Personnel Appointment) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 인사발령 엑셀 추출 (Operation API)
POST /action/operation/v2/core/personnel-appointment/customers/{customerId}/export/excel

-- 유저별 특정 시점 조직 추출
SELECT pt.user_id, GROUP_CONCAT(d.name ORDER BY pt.is_primary DESC SEPARATOR ', ') AS names
FROM user_position_time_series_segment pt, department d
WHERE pt.department_id = d.id
  AND pt.customer_id = ?
  AND pt.deleted_date_time IS NULL
  AND pt.user_id = ?
  AND pt.begin_date_time < ?  -- target_date
  AND (pt.end_date_time > ? OR pt.end_date_time = '9999-12-31 23:59:59.999999')
-- 여러 유저는 UNION ALL로 연결
```

## 과거 사례

- **인사발령 엑셀 타임아웃**: 대규모 고객사에서 타임아웃 발생 → user id 기준 분할 호출 후 병합 — **운영 요청**
- **특정 시점 조직 추출**: 유저 리스트+시점 기반 union all 쿼리로 대응 — **운영 요청**
