# 스냅샷형 추가 섹션

> **해당 도메인**: 페이롤, 연말정산
>
> **특성**: 단계별 상태 머신을 거치며 각 단계에서 결과를 고정 저장.
> 확정(COMPLETED/FINAL_CONFIRM) 이후 과거 스냅샷은 불변.
>
> **핵심**: 정산 상태 머신의 현재 위치가 가능한 조작을 결정한다.
> 급여: `PAYEES → PAYMENT → DEDUCTION → SETTLEMENT_REVIEW → PREVIEW → COMPLETED`
> 연말정산: `NOT_PREPARED → PREPARED → IN_PROGRESS → SUBMITTED → FINAL_CONFIRM`

## 추가 섹션 (영향 범위 ~ 해결 사이에 삽입)

```markdown
## 정산 상태 확인

- 어떤 정산/처리 기간의 데이터인가 (귀속월 vs 지급일 구분)
- 정산 상태 머신의 현재 위치 (어떤 단계의 어떤 상태인가)
  - 급여: SettlementProgressType + ProgressStatus
  - 연말정산: SettlementStatusType + 스케줄 기간(reportingPeriod, confirmingPeriod)
- COMPLETED/FINAL_CONFIRM 이후인가 — 이후라면 일반적 수정 불가
- 정산 유형 확인: REGULAR / RETIREE_YEAR_END / ONLY_RETIREE_YEAR_END

## 소급 적용 / 재정산

- 과거 스냅샷 수정이 필요한가 → 마이그레이션 필요 (PayrollMigrationJob 프레임워크)
- 재정산 차수(round) 확인 — 직전 차수 데이터 존재 여부
- 원천징수 신고서 반영 방식: FULL(전액) vs DIFF(차액) 확인
- 원천 데이터(TT 근무기록/연차) 변경이 정산 완료 전인지 후인지
- 분납(Installment) 잔액과 상태 (GRACE_PERIOD/PAYMENT/PAYMENT_IN_FULL)

## 금전적 영향

- 급여/수당/공제 오류 금액 산출
- 4대보험 요율 적용 연도 확인 (연도별 하드코딩 — 건강보험 상한/하한 포함)
- 고용보험 Tier(기업 규모)와 고객사 설정 일치 여부
- 세금/4대보험 신고에 미치는 영향 (원천징수 수정신고 필요 여부)
- 이미 지급된 건이면 차액 처리 방법
```
