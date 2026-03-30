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

## 휴일 삭제 (Operation API)

> 사례: [CI-4252] — 해외 법인 기본 휴일 정책에서 근로자의 날(LABOR_DAY) 삭제

### 절차

**Step 1: 휴일 그룹 ID 조회**

```sql
SELECT id, name FROM flex.v2_customer_holiday_group WHERE customer_id = ?;
-- 여러 정책이 있으면 고객에게 어떤 정책에서 삭제할지 재확인
```

**Step 2: Operation API로 공휴일 삭제**

```
POST /action/operation/v2/holiday/customers/customer-holiday-groups/delete
{
  "actorCustomerId": ?,
  "actorUserId": ?,
  "targetCustomerHolidayGroupId": ?,
  "publicHolidayName": "LABOR_DAY",
  "selectedYear": "2026",
  "appliedEveryHoliday": true,
  "rootHoliday": "--05-01"
}
```

| 파라미터 | 설명 |
|---------|------|
| `publicHolidayName` | 삭제할 공휴일 enum (예: `LABOR_DAY`, `NEW_YEARS_DAY` 등) |
| `selectedYear` | 적용 시작 연도 |
| `appliedEveryHoliday` | `true` → 해당 연도부터 **매년** 삭제, `false` → 해당 연도만 삭제 |
| `rootHoliday` | 월-일 (`--MM-dd` 형식) |

### 주의사항

- **근로자의 날은 법정유급휴일** (근로자의 날 제정에 관한 법률 제1조). 국내 법인 기본 정책에서 삭제 요청 시 **반드시 법령 위반 여부 검토 후 진행**
- 해외 법인 적용 목적이면 법적 문제 없음
- `appliedEveryHoliday: true` 설정 시 이후 연도 모두 영향받으므로 고객에게 범위 재확인 권장
