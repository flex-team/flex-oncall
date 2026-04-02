# 인사발령 (Personnel Appointment) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 도메인 컨텍스트

### 구현 특이사항

- **displayOrder 설정 경로 불일치**: 인사발령에는 API 발령과 엑셀 발령 두 경로가 존재한다. 엑셀 발령은 `displayOrder = index`(리스트 인덱스 기반)로 올바르게 설정하지만, API 발령은 `displayOrder ?: 0`으로 fallback하여 프론트가 null을 보내면 모든 직무가 동일 순서(0)가 된다. [CI-4288](../notes/archive/CI-4288.md)
- **대표 직무 정렬 함수 2종**: `UserPositionModel.sortedByPrimaryFirstOrder()`는 `userPositionId` tiebreaker 포함(정상), `UserInfoLookUpServiceImpl.sortedByPrimaryFirstOrder()`는 tiebreaker 없음(displayOrder 동일 시 비결정적). [CI-4288](../notes/archive/CI-4288.md)

---

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

-- 복수 직무 display_order 확인 (대표 직무 표시 불일치 조사용)
SELECT pt.user_id, pt.id AS segment_id, d.name AS position_name,
       pt.display_order, pt.is_primary, pt.begin_date_time
FROM user_position_time_series_segment pt
JOIN department d ON pt.department_id = d.id
WHERE pt.customer_id = ?
  AND pt.deleted_date_time IS NULL
  AND pt.begin_date_time = ?
  AND (pt.end_date_time > NOW() OR pt.end_date_time = '9999-12-31 23:59:59.999999')
GROUP BY pt.user_id, pt.id
HAVING COUNT(*) OVER (PARTITION BY pt.user_id) > 1
ORDER BY pt.user_id, pt.display_order, pt.id
```

## 과거 사례

- **인사발령 엑셀 타임아웃**: 대규모 고객사에서 타임아웃 발생 → user id 기준 분할 호출 후 병합 — **운영 요청**
- **특정 시점 조직 추출**: 유저 리스트+시점 기반 union all 쿼리로 대응 — **운영 요청**
- **API 발령 displayOrder fallback 버그**: API 발령 시 `displayOrder ?: 0` fallback으로 복수 직무 순서 유실 → 대표 직무 표시 비결정적. 엑셀 발령은 `index` 사용으로 정상 — **버그** [CI-4288](../notes/CI-4288.md)
