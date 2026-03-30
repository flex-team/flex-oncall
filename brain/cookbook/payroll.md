# 급여 (Payroll) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 도메인 컨텍스트

### 이 도메인이 하는 일

급여 정산(월급, 상여, 퇴직금), 원천징수, 사회보험 관리, 급여명세서 발행을 담당한다. 소득세법, 국민건강보험법, 고용보험법 등 법령에 직접 종속되며, 정산 로직의 대부분이 법적 요건을 구현한 것이다.

### 핵심 개념

- **정산(`settlement`)**: 급여 계산의 단위. 생성 시점에 올림 설정, 부양가족 수 등을 **스냅샷**으로 저장한다. 이후 설정이 변경되어도 기존 정산은 영향받지 않는다.
- **정산 대상자(`payee`)**: 정산에 포함된 구성원별 스냅샷. `dependent_families_count`(부양가족 수), `residence_qualification`(체류자격), `employment_status`(재직/휴직) 등 소득세 계산에 필요한 정보를 정산 생성 시점에 복사.
- **지급항목(`allowance_global`)**: 회사별로 정의하는 급여 구성 항목. 템플릿(`allowance_template`)과 실제 매핑(`customizable_allowance`)이 분리되어 있다.
- **중도정산**: 퇴직예정자 대상 정산. `RetireeYearEndSettlementSocialInsuranceRecipient`에 보험료를 1회 계산·저장하며, 이후 자동 재계산하지 않는다.

### 주요 흐름

1. **정산 생성**: 정산 템플릿 기반 → payee 스냅샷 생성(PAYEES 단계) → 각 단계별 계산 순차 진행
2. **정산 재처리**: 자물쇠 해제 → PAYEES 단계부터 재실행 → payee 스냅샷 **최신화** (부양가족 변경 반영)
3. **사회보험 연말정산**: 2월 말 합산 픽스. 확정/확정해제 시 사회보험 금액 동기화 필요.

### 비즈니스 규칙

- **스냅샷 원칙**: 정산은 생성 시점의 설정을 고정한다. 올림 자릿수, 부양가족 수, 체류자격 모두 스냅샷. "설정을 바꿨는데 왜 반영이 안 되나요?"라는 문의의 대부분은 이 원칙 때문.
- **외국인 고용보험**: 체류자격(F-4 등)에 따라 임의가입/당연가입이 나뉜다. 임의가입 대상자는 `employment_insurance_qualification_history`에 취득일이 등록되어 있어야 공제된다. 미등록 시 EXCLUDED 처리.
- **휴직자 지급항목**: `allowance_on_leave_rule`이 `DAILY_BASE`(기본값)이면 `paymentRatio`와 곱해진다. 육아휴직(`paymentRatio=0`)이면 0원. `FULL`로 변경하면 전액 지급.
- **구독 해지와 명세서**: 급여정산 구독 해지 후에도 명세서 알림은 발송된다. 급여 탭 접근만 차단되어 열람 불가.

### 자주 혼동되는 것들

- **"올림 설정 변경했는데 안 바뀌었어요"**: 현재 설정(`payroll_legal_payment_setting`)과 정산 스냅샷(`work_income_over_work_payment_calculation_basis`)이 다를 수 있다. 기존 정산은 이전 설정을 유지한다.
- **중도정산 보험료 vs 일반 정산 보험료**: 중도정산은 recipient 생성 시점에 1회 계산·저장. 이관 데이터 추가 후에도 자동 재계산 안 됨. 보험료 리셋(DELETE /premium → recalculate) 필요.
- **확정해제 리버트 범위**: 2026-03-20 핫픽스 이전에는 확정해제 시 사회보험 연말정산 금액이 리버트되지 않았다. 핫픽스 이전 데이터는 수동 워크어라운드 필요.

### 구현 특이사항

- **지급항목 이벤트 이중 발행**: v3.128.0 리팩토링(PR #8655)에서 `AllowanceGlobalCreatedEvent` 발행 경로가 활성화되어 리스너가 전체 템플릿에 매핑 자동 생성. `@Transactional` 부재로 allowance_global+매핑은 커밋되지만 customizable_allowance 미생성 → 고아 레코드. 핫픽스 PR #8686.
- **사회보험 연말정산 합산 로직**: `PaidSocialInsuranceCalculator.getYearEndTotalAmountByType()`이 귀속연도 필터 없이 전체 합산하는 이슈가 있었다(CI-4222).

---

## 지식 베이스

도메인 상세 지식(계산 로직, 법령 근거, 케이스별 스펙)은 payroll 백엔드 knowledge-base를 참조한다.

- `flex-payroll-backend/docs/knowledge-base/INDEX.md`

---

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

-- 외국인 고용보험 공제 상태 확인
SELECT eid.settlement_id, eidr.user_id,
  eidr.settled_employment_insurance, eidr.total_amount, eidr.remarks
FROM flex_payroll.employment_insurance_deduction eid
JOIN flex_payroll.employment_insurance_deduction_recipient eidr ON eidr.deduction_id = eid.id
WHERE eid.settlement_id = ? AND eidr.user_id = ?;

-- 고용보험 자격관리 이력 확인
SELECT eiqh.qualified_date, eiqh.disqualified_date
FROM flex_payroll.employment_insurance_qualification_history eiqh
JOIN flex_payroll.social_insurance_qualification_history siqh ON siqh.id = eiqh.id
WHERE siqh.user_id = ? AND siqh.customer_id = ?;

-- 정산 payee 체류자격 확인
SELECT settlement_id, user_id, residence_qualification
FROM flex_payroll.work_income_settlement_payee
WHERE customer_id = ? AND user_id = ? AND settlement_id = ?;

-- 체류자격 변경 이력 확인 (core DB)
SELECT rev, audit_created_at, residence_qualification, nationality, update_actor_id
FROM flex.user_personal_audit
WHERE user_id = ? ORDER BY audit_created_at;

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
- **외국인(F-4) 고용보험 미공제 — 체류자격 변경 + 자격관리 미등록**: 체류자격 UNKNOWN→F4 변경 후 정산 시 외국인 로직 적용. F-4는 임의가입 대상으로 employment_insurance_qualification_history에 취득일이 필요하나 0건 → EXCLUDED. 사회보험 자격관리에서 취득일 등록 안내 — **스펙** [CI-4241]
- **원천징수영수증 일괄 다운로드 실패 — 파일 서비스 밀림**: `async-bulk-download-withholding-receipts-by-filter` 비동기 태스크가 파일 서비스 merge 큐 지연(CI-4236)으로 실패. API 접수는 정상(~100ms)이나 백그라운드 파일 생성에서 실패/타임아웃. 파일 서비스 장애 해소 후 재시도로 정상화 — **Not a Bug(ops)** [CI-4240]
- **원천세 신고 생성 시 과거 연도 선택 불가 — FE 컴포넌트 재사용(의도된 동작)**: 지방소득세 모달의 귀속연월 picker(`FormField_귀속지급_연월.tsx`)가 "작년 1월"부터만 허용. 원천세 모달에서 재사용 시 도입 이전 연도(2020~2024) 귀속 신고 불가. BE에는 연도 제한 없음. 세금팀 확인 결과 의도된 동작으로 판정 — **Not a Bug(스펙)** [CI-4247]
- **정산 중 지급항목 추가 시 이벤트 이중 발행으로 고아 레코드 생성**: v3.128.0 리팩토링(PR #8655)에서 `allowanceGlobalCommandPort` → `customerAllowanceUseCase` 변경 시 `AllowanceGlobalCreatedEvent` 발행 경로 활성화. 리스너가 전체 템플릿에 매핑 자동 생성 → 이후 명시적 매핑 시 중복 오류. `@Transactional` 부재로 allowance_global+매핑은 커밋되지만 customizable_allowance 미생성. 121개 고객 488건 고아 레코드. 핫픽스 PR #8686 — **버그(핫픽스 완료, 데이터 패치 대기)** [CI-4216]
