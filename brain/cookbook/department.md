# 조직 관리 (Department) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 조직 삭제 전: 해당 조직에 소속된 구성원 확인 (전 시점)
SELECT * FROM user_position_time_series
WHERE department_id = ? AND deleted_date_time IS NULL;

-- 조직 삭제 전: 하위 조직 확인
SELECT id, name, parent_id, begin_date_time, end_date_time
FROM department_time_series_segment
WHERE parent_id = ? AND deleted_date_time IS NULL;

-- 조직 시계열 데이터 조회 (Metabase #5082)
SELECT
    d.id AS '조직 ID', d.code AS '조직 코드',
    DATE_FORMAT(DATE_ADD(IF(d.begin_date_time = '1000-01-01 00:00:00', NULL, d.begin_date_time), INTERVAL 1 DAY), '%Y-%m-%d') AS '조직 시작일',
    DATE_FORMAT(DATE_ADD(IF(d.end_date_time = '9999-12-31 23:59:59', NULL, d.end_date_time), INTERVAL 1 DAY), '%Y-%m-%d') AS '조직 종료일',
    d_seg.id AS '시점별 정보 ID', d_seg.name AS '조직명', d_seg.parent_id AS '상위조직 ID',
    DATE_FORMAT(DATE_ADD(IF(d_seg.begin_date_time = '1000-01-01 00:00:00', NULL, d_seg.begin_date_time), INTERVAL 1 DAY), '%Y-%m-%d') AS '시점별 정보 시작일',
    DATE_FORMAT(DATE_ADD(IF(d_seg.end_date_time = '9999-12-31 23:59:59', NULL, d_seg.end_date_time), INTERVAL 1 DAY), '%Y-%m-%d') AS '시점별 정보 종료일'
FROM flex.department_time_series_segment d_seg
  JOIN flex.department d ON d_seg.department_id = d.id
WHERE d.customer_id = ? AND d_seg.deleted_date_time IS NULL AND d.deleted_at IS NULL
ORDER BY d.id, d_seg.begin_date_time;

-- 발령+조직변경 데드락: 예약 발령일 기준 종료되는 조직 조회
SELECT id FROM department
WHERE customer_id = ? AND end_date_time = ? AND deleted_at IS NULL;

SELECT id FROM department_time_series_segment
WHERE department_id IN (?) AND deleted_date_time IS NULL AND end_date_time = ?;

-- 조직 종료일 임시 제거 (데드락 해소용)
UPDATE flex.department SET end_date_time = '9999-12-31 23:59:59.999999'
WHERE customer_id = ? AND id IN (?) AND end_date_time = ?;

UPDATE flex.department_time_series_segment SET end_date_time = '9999-12-31 23:59:59.999999'
WHERE customer_id = ? AND id IN (?) AND department_id IN (?) AND end_date_time = ?;
```

> ⚠️ **일반 설정 vs 고급 설정의 종료일 처리 차이**: 일반 설정은 오늘의 00:00, 고급 설정은 해당 날짜의 23:59.999999로 종료일 적용

## 과거 사례

- **발령+조직변경 데드락**: 미래 날짜 기준 발령과 조직 삭제/생성 동시 예약 → 상호 참조로 양쪽 다 취소 불가. SQL로 종료일 임시 제거→발령 취소→종료일 복구로 해소 — **운영 대응** [코어 런북]
- **조직 삭제 — 시작일=오늘 우회**: 제품 상 삭제 기능은 없지만, 일반 설정에서 오늘 종료 처리 시 시작일=종료일이 되면서 삭제됨 — **스펙 (우회 경로)**
- **조직 시계열 조회 → Metabase 전환**: 쿼리 대응에서 Metabase #5082로 전환. 문의 시 링크 안내 — **운영 요청**
- **종료된 조직 코드 마이그레이션**: 과거 발령 마이그레이션 위해 종료된 조직에 코드 입력 필요. 엑셀→DML — **운영 요청**
- **구성원 없는 조직 종료 불가 — 예약발령 잔존**: 구성원이 모두 타조직으로 이동 예정이어도, 예약발령 실행 전이면 validator가 미래 position을 감지하여 차단(`DEPA_400_017`). 발령 실행 후 종료 또는 발령 취소→종료→재발령으로 해소 — **스펙** [CI-4201]
<!-- TODO: 시나리오 테스트 추가 권장 -->
