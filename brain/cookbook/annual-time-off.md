# 연차 (Annual Time Off) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 도메인 컨텍스트

### 연차 버킷(Bucket) 구조

연차는 **버킷(bucket)** 단위로 관리된다. 부여·조정 이벤트마다 버킷이 하나씩 생성되며, 잔여일은 버킷별로 계산한 뒤 합산한다.

```
버킷 잔여일 = 버킷 잔여 시간(분) ÷ agreedDayWorkingMinutes(분/일)
전체 잔여일 = 모든 버킷 잔여일 합산 → setScale(3, HALF_UP)
```

**`agreedDayWorkingMinutes`** = 버킷 생성 시점(`assignedAt`)의 소정근로시간.
소정근로시간이 변경되어도 기존 버킷의 값은 변하지 않는다.

코드 경로:
```
UserAnnualTimeOffBuckets.getRemainingDays()
  → sumOf { remainingTimeOffMinutes / agreedDayWorkingMinutes }  (MathContext.DECIMAL64)
  → setScale(3, RoundingMode.HALF_UP)
```

버킷 타입 (`AnnualTimeOffAssignType`):
- `REGULAR` — 정기 부여 (연간/월별)
- `ADDITIONAL` — 추가 부여
- `ADJUST` — 관리자 조정 (양수 조정만. 음수 조정은 `FOR_MINUS`와 쌍으로 생성)
- `FOR_MINUS` — 음수 조정용 특수 버킷. **잔여일 계산(`getDetailRemainingDays`)에서 제외**됨

버킷 내부 값:
- `assignedTime` (분) = 부여된 총 시간
- `usedTime` (분) = 사용된 시간
- `remainingTimeOffMinutes` = `assignedTime - usedTime` (단순 차감)

### ADJUST 버킷의 assignedTime 계산

관리자가 "5시간" 또는 "0.833일"을 조정할 때, 내부에 저장되는 `assignedTime`(분)은 다음 공식으로 계산된다:

```
assignedTime = days × sojeong_at_assignedAt + hours × 60 + minutes
```

- `sojeong_at_assignedAt` = **조정 날짜(`assignedAt`) 기준의 소정근로시간**
- `days`는 DB의 `adjusted_days` (소수점 가능, 예: 0.833)
- `hours`, `minutes`는 DB의 `adjusted_time` JSON 필드

코드:
```kotlin
// AnnualTimeOffAdjustAssignProps.getMinutes()
fun getMinutes(workRuleModel): Minutes =
    (adjustedAmount.days * workRuleModel.getAverageDailyTimeOffMinutesPerWeekAtDate(assignedAt)) +
    (adjustedAmount.hours * 60) +
    adjustedAmount.minutes
```

**예시**: 2026-02-28(소정 360분) 에 5시간 조정
```
assignedTime = 0 × 360 + 5 × 60 + 0 = 300분
```

### 소정근로시간이 쓰이는 시점 정리

| 계산 항목 | 기준 시점 | 비고 |
|----------|----------|------|
| `agreedDayWorkingMinutes` (버킷 저장값) | `assignedAt` (버킷 생성일) | 변경되어도 기존 버킷값 불변 |
| ADJUST `assignedTime` 계산 | `assignedAt` (조정일) | `getMinutes()` 참조 |
| REGULAR `assignedTime` 계산 | `assignedAt` (부여일) | |
| `getRemainingMinutes()` (분 단위 잔여) | 요청 시점(`requestTime`) | 소정근로시간 변경 시 일수 환산값이 달라짐 |

→ 소정근로시간이 변경되면 **기존 버킷의 `agreedDayWorkingMinutes`는 고정**, 새 버킷부터 새 소정근로시간 적용.

### 잔여일 계산 전체 흐름 (`getDetailRemainingDays`)

```
① 버킷 필터링
   YEARLY 버킷: FOR_MINUS 제외, isUsableAt(요청날짜) 통과한 것만
   MONTHLY 버킷: 동일 조건
   ↓
② 버킷별 잔여일 합산 (setScale 3자리)
   usableYearlyTimeOffDays = YEARLY 버킷 합산
   usableMonthlyTimeOffDays = MONTHLY 버킷 합산
   ↓
③ 선사용(advance) 공제
   overUsedTimeOffDays = daysToUseInAdvance + daysToUseInEarly
   → MONTHLY에서 먼저 차감, 남으면 YEARLY에서 차감
   ↓
④ 최종 잔여일 = usableYearlyTimeOffDays + usableMonthlyTimeOffDays
```

> 잔여일이 버킷 합산과 미세하게 다르면 ③의 선사용 공제를 의심한다.

### Operation API로 버킷 조회

```
GET /api/operation/v2/time-tracking/time-off/customers/{customerId}/users/{userId}/annual-time-off-buckets/by-time-stamp/{timeStamp}?zoneId=Asia%2FSeoul
```
- `timeStamp`: 기준 시각 (epoch ms). 특정 시점의 잔여일을 재현할 때 사용
- 응답의 `remainingDays`가 화면 표시값과 일치

### 소정근로시간 변경이 잔여일에 미치는 영향

소정근로시간이 변경된 유저는 버킷마다 `agreedDayWorkingMinutes`가 다를 수 있다.
서로 다른 단위로 각 버킷의 잔여일을 계산한 뒤 합산하므로, 결과에 예상치 못한 소수점이 발생할 수 있다.

**예시 (CI-4349, 주식회사 무하유 customerId=69518)**:
```
REGULAR 버킷 (2026-01-01 부여, 소정 480분/일)
  → 잔여 5841분 ÷ 480 = 12.16875일

ADJUST 버킷 (2026-02-28 조정, 소정 360분/일로 변경 후)
  → 잔여 300분 ÷ 360 = 0.83333...일

합산: 13.00208... → setScale(3, HALF_UP) = 13.002일
```

이는 **버그가 아닌 설계된 동작**이다. 소수점 발생 원인이 소정근로시간 혼재인지 확인하려면:
1. Operation API로 버킷 전체 조회
2. 버킷별 `agreedDayWorkingMinutes` 값이 서로 다른지 확인
3. 버킷마다 `assignedTime ÷ agreedDayWorkingMinutes` 계산 → 합산 검증

> ⚠️ TT-6441: 버킷 간 `agreedDayWorkingMinutes` 혼재 상황 처리 개선 FIXME (현재 미해결)

스펙 참고: https://flex-cv82520.slack.com/archives/C038DUJJ5ND/p1755139378914669

---

## 데이터 접근

```sql
-- 휴직 설정 확인
SELECT * FROM flex.user_leave_of_absence WHERE user_id = ?;

-- 연차 정책 확인
SELECT * FROM flex.v2_customer_annual_time_off_policy WHERE customer_id = ?;

-- 연차 사용 이벤트
SELECT * FROM flex.v2_user_time_off_event WHERE user_id = ? AND customer_id = ?;

-- 연차 조정 이력 (최신순, 삭제 포함)
SELECT
    id, user_id, customer_id, adjust_type, adjust_group_id,
    assigned_at, assign_time, adjusted_time, adjusted_days, deleted_time_stamp,
    created_date_time
FROM flex.v2_user_annual_time_off_adjust_assign
WHERE user_id = ?
ORDER BY created_date_time DESC
LIMIT 50;
```

## 환경 재현 시 필요 테이블

- 입사일: `user_employee_audit`
- 근무유형: `v2_user_work_rule`, `v2_customer_work_rule`, `v2_customer_work_record_rule`
- 연차정책: `v2_customer_annual_time_off_policy`
- 연차사용/조정: `v2_user_time_off_event`, `v2_user_time_off_event_block`, `v2_user_annual_time_off_adjust_assign`
