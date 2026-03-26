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

-- 고아 매핑 탐지 (customizable_allowance_template에 대응 customizable_allowance 없음)
SELECT cat.id as template_id, cat.allowance_global_id, cat.allowance_global_code,
  cat.customer_id, cat.settlement_template_id, cat.is_active, cat.deleted_at
FROM flex_payroll.customizable_allowance_template cat
WHERE cat.db_created_at >= ?
AND NOT EXISTS (
  SELECT 1 FROM flex_payroll.customizable_allowance ca WHERE ca.template_id = cat.id
)
ORDER BY cat.customer_id, cat.db_created_at;

-- 지급항목 휴직규칙 확인 (Q02 보육수당 등)
SELECT id, name, non_taxable_code, contract_allowance_group_key,
       allowance_on_leave_rule, variability
FROM flex_payroll.allowance_global
WHERE customer_id = ? AND non_taxable_code = ? AND deleted_at IS NULL;

-- 휴직자 payee 급여비율 확인
SELECT user_id, employment_status, on_leave_payment_ratio, leave_of_absences
FROM flex_payroll.work_income_settlement_payee
WHERE customer_id = ? AND settlement_id = ? AND employment_status = 'ON_LEAVE';

-- 중도정산 사회보험 recipient 확인 (보험료 생성 시점·근무월수·정산월수)
SELECT id, settlement_id, year, working_months, settled_months,
       db_created_at, db_updated_at
FROM flex_payroll.retiree_year_end_settlement_social_insurance_recipient
WHERE user_id = ?
ORDER BY year;
```

## 과거 사례

- **올림 설정 변경 후 기존 정산 미반영**: 정산 생성 시 올림 설정을 스냅샷. 100의 자리 → 10의 자리로 변경해도 기존 정산은 이전 설정 유지. 신규 정산에서 정상 반영 — **스펙** [CI-4131]
- **정산 재처리 시 소득세 변경 — 부양가족 수 최신화**: 정산 자물쇠 해제 후 재처리 시 PAYEES 단계에서 전체 대상자의 payee 스냅샷 최신화. 1차 정산 이후 부양가족 추가/변경이 있었으면 소득세 재계산됨 — **스펙** [CI-4149]
<!-- TODO: 시나리오 테스트 추가 권장 — 정산 재처리 시 payee 스냅샷 최신화로 소득세 변경 검증 -->
- **구독 해지 후 명세서 알림 발송**: payroll 스케줄러/pavement 모두 구독 상태 미체크. 알림은 정상 발송되나 급여 탭 접근 차단으로 실제 열람 불가. 1달 연장 안내 권장 — **스펙** [QNA-1933]
- **중도정산 확정해제 후 전년도 사회보험 금액 미리버트**: 확정 시 정산 결과에 저장된 사회보험 연말정산 금액이 확정해제 시 리버트되지 않음. 2월 말 합산 픽스 이후 이 금액이 납부한 보험료에 합산됨. **2026-03-20 핫픽스로 근본 수정 완료** (확정해제 시 리버트 추가). 핫픽스 이전 데이터 워크어라운드: 건강보험 제외→확정→확정해제→포함 변경 — **버그(수정완료)** [CI-4174]
- **이관 회사 중도정산 보험료 불일치**: 중도정산 recipient의 보험료는 `RetireeYearEndSettlementSocialInsuranceRecipientFactory.createRecipient()`에서 생성 시점 보수총액 기반 1회 계산·저장. 이관 데이터 추가 후 자동 재계산 트리거 없음. 워크어라운드: 보험료 리셋(DELETE /premium → recalculate). 리셋 API: `RetireeYearEndSettlementSocialInsuranceUpdateApplicationService:268-286`. 이관 회사 전용 이슈 — 일반 회사에서는 해당 없음 — **버그(워크어라운드)** [CI-4212]
- **육아휴직자 보육수당 자동산정 0원**: `allowance_on_leave_rule=DAILY_BASE`(기본값) + `paymentRatio=0`(육아휴직) → `금액 × 0 = 0원`. 지급항목의 휴직월 지급 방법을 `FULL`로 변경하면 해결. 고객사 관리자가 UI에서 직접 변경 가능 — **스펙** [CI-4225]
- **정산 중 지급항목 추가 시 이벤트 이중 발행으로 고아 레코드 생성**: v3.128.0 리팩토링(PR #8655)에서 `allowanceGlobalCommandPort` → `customerAllowanceUseCase` 변경 시 `AllowanceGlobalCreatedEvent` 발행 경로 활성화. 리스너가 전체 템플릿에 매핑 자동 생성 → 이후 명시적 매핑 시 중복 오류. `@Transactional` 부재로 allowance_global+매핑은 커밋되지만 customizable_allowance 미생성. 121개 고객 488건 고아 레코드. 핫픽스 PR #8686 — **버그(핫픽스 완료, 데이터 패치 대기)** [CI-4216]
