# 맞춤휴가 (Custom Time Off) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 도메인 컨텍스트

### 핵심 개념

- **분 단위 내부 관리**: 맞춤휴가 잔여량은 내부적으로 **분(minute) 단위**로 저장된다. 화면/엑셀에 표시되는 일 단위 값은 `잔여 분 ÷ 1일 소정근로시간`으로 환산한 결과이다.
- **조회 시점 기준 환산**: 분→일 환산은 **조회/다운로드 시점의 소정근로시간**을 기준으로 한다. 과거 잔여량도 현재 소정근로시간 기준으로 다시 환산된다.

### 구현 특이사항

- **소정근로시간 변경 시 잔여 일수 변동 (스펙)**: 육아기 단축근무 등으로 1일 소정근로시간이 변경되면 동일한 분 잔여라도 일 단위 표시값이 달라진다. 예: 480분 잔여, 소정 480분→240분 변경 시 1일→2일로 증가. [CI-4025]

---

## 과거 사례

- **대체휴가 잔여 일수 이유 없이 증가**: 육아기 단축근무 적용으로 소정근로시간이 480분→240분으로 변경된 뒤, 엑셀 다운로드 시점에서 분→일 환산값이 2배로 증가. 시스템 버그 아님, 조회 시점 소정근로시간 기준으로 환산되는 스펙. — **expected-behavior** [CI-4025]

---

## 데이터 접근

```sql
-- 맞춤휴가 부여 확인
SELECT * FROM flex.v2_user_custom_time_off_assign WHERE user_id = ? AND customer_id = ?;

-- 맞춤휴가 회수 확인
SELECT * FROM flex.v2_user_custom_time_off_assign_withdrawal WHERE customer_id = ?;

-- 일괄 부여 확인
SELECT * FROM flex.v2_customer_bulk_time_off_assign WHERE customer_id = ?;
```
