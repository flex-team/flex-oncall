# 급여 (Payroll) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 초과근무수당 올림 설정 (현재)
SELECT rounding_digit, rounding_method
FROM payroll_legal_payment_setting
WHERE customer_id = ? AND type = 'GROUP_EXCEEDED_WORK_EARNING';

-- 정산근거의 올림 스냅샷 (정산 생성 시점)
SELECT rounding_digit, rounding_method
FROM work_income_over_work_payment_calculation_basis
WHERE settlement_id = ?;

-- 정산 대상자의 부양가족 수 스냅샷 확인
SELECT user_id, dependent_families_count, under_age_dependent_families_count
FROM flex_payroll.work_income_settlement_payee
WHERE settlement_id = ? AND user_id = ?;
```

## 과거 사례

- **올림 설정 변경 후 기존 정산 미반영**: 정산 생성 시 올림 설정을 스냅샷. 100의 자리 → 10의 자리로 변경해도 기존 정산은 이전 설정 유지. 신규 정산에서 정상 반영 — **스펙** [CI-4131]
- **정산 재처리 시 소득세 변경 — 부양가족 수 최신화**: 정산 자물쇠 해제 후 재처리 시 PAYEES 단계에서 전체 대상자의 payee 스냅샷 최신화. 1차 정산 이후 부양가족 추가/변경이 있었으면 소득세 재계산됨 — **스펙** [CI-4149]
<!-- TODO: 시나리오 테스트 추가 권장 — 정산 재처리 시 payee 스냅샷 최신화로 소득세 변경 검증 -->
- **구독 해지 후 명세서 알림 발송**: payroll 스케줄러/pavement 모두 구독 상태 미체크. 알림은 정상 발송되나 급여 탭 접근 차단으로 실제 열람 불가. 1달 연장 안내 권장 — **스펙** [QNA-1933]
- **중도정산 확정해제 후 전년도 사회보험 금액 미리버트**: 확정 시 정산 결과에 저장된 사회보험 연말정산 금액이 확정해제 시 리버트되지 않음. 2월 말 합산 픽스 이후 이 금액이 납부한 보험료에 합산됨. **2026-03-20 핫픽스로 근본 수정 완료** (확정해제 시 리버트 추가). 핫픽스 이전 데이터 워크어라운드: 건강보험 제외→확정→확정해제→포함 변경 — **버그(수정완료)** [CI-4174]
