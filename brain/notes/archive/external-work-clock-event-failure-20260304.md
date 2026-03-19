# 외부 타각기 위젯 이벤트 처리 실패 (2026-03-04)

## 증상

- 2026-03-04 15:14 ~ 2026-03-05 09:01 (KST) 사이에 SECOM/CAPS 외부 타각기의 WORK_STOP 이벤트 53건이 consumer에서 처리 실패
- 로그: "근무 위젯 이벤트 처리 실패" (`ExternalWorkClockEventRegisterServiceImpl`)
- 영향: 8개 고객사, 43명 유저

## 원인 분석

- `WorkClockEventSnapshotConverter`에서 `require()` 예외 발생 (근무일 불일치 케이스)
- 외부 타각기 이벤트는 배치/수동 전송으로 9~24시간 지연 수신되는 경우가 있음
- 지연 수신 시 근무일 판단 로직에서 불일치가 발생하여 예외

## 해결

- 수정 PR: [#11890](https://github.com/flex-team/flex-timetracking-backend/pull/11890)
- consumer 배포: 2026-03-05 09:00

## 재처리

### Operation API
```
POST /api/operation/v2/time-tracking/external-work-clock/customers/{customerId}/produce
Body: { "externalProviderIds": [이벤트 ID 목록] }
```

### 재처리 결과 (53건)

| 분류 | 건수 | 상세 |
|------|------|------|
| STOP+근무기록 정상 생성 | 34건 | ikokr 1 + v3z2j 1 + 5m0nw 6 + mv0aa 16 + marhenj 10 |
| produce 성공, 메모필수로 자동등록 불가 | 14건 | korot 10 + lifehacking 3 + 5m0nw 1 |
| produce 성공, 사용자 확인 대기 | 4건 | 210pdky 4 |
| 기존 STOP 존재 (재처리 대상 아님) | 1건 | mv0aa 910012 |

### 자동등록 실패 원인

1. **메모필수 정책** (`WorkScheduleRequiredMemoValidatorLogic`): "과거근무수정" 승인에 `requiredMemo=true` 설정된 고객사에서, 서버 자동 요청에는 메모가 없어 검증 실패. draft event로만 저장됨.
2. **STOP_CONFIRM 대기**: produce → draft event 생성 → `FLEX_TIME_TRACKING_WORK_CLOCK_STOP_CONFIRM` 알림 발송. 사용자가 확인해야 최종 반영.

### 고객사별 상세

| account | customer_id | 건수 | 결과 |
|---------|------------|------|------|
| secom_ikokr | 34333 | 1 | 재처리 완료 (STOP+근무기록+승인콘텐츠) |
| caps_v3z2j9kgzm | 220475 | 1 | 재처리 완료 |
| secom_5m0nwxopz6 | 201510 | 7 | 6건 완료, 1건(941781) 메모필수 |
| secom_mv0aall30z | 219447 | 17 | 16건 완료, 1건(910012) 기존 STOP |
| secom_marhenj | 102980 | 10 | 전건 완료 (approval_id NULL) |
| secom_korot | 119380 | 10 | 전건 메모필수로 자동등록 불가 |
| caps_lifehacking | 147374 | 3 | 전건 메모필수로 자동등록 불가 |
| secom_210pdky40x | 204584 | 4 | 전건 STOP_CONFIRM 대기 |

## 재처리 검증 절차

1. `v2_user_work_clock_event` — STOP 이벤트 생성 확인
2. `v2_user_work_record_event` — REGISTER_BY_WORK_CLOCK 생성 확인
3. `v2_user_work_record_event_approval_mapping` — 승인 매핑 확인 (approval_id NULL이면 승인 없음)
4. `v2_user_work_record_approval_content` — 승인 콘텐츠 확인 (approval_id가 있을 때만)
5. (STOP 없는 경우) OpenSearch `flex-app.be-cron-*` 인덱스에서 produce 로그 확인

## 비고

- approval_id가 NULL인 매핑 = 승인이 생성되지 않은 상태 (자동승인 미적용)
- 외부 타각기 produce는 cron 서비스에서 실행됨 → 로그 인덱스는 `flex-app.be-cron-*`
- 상세 CSV: `/tmp/widget-event-failure-20260304.csv` (세션 종료 시 소실)
- 상세 보고서 원본: `/tmp/widget-event-failure-20260304-report.md` (세션 종료 시 소실)
