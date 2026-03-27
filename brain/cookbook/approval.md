# 승인 (Approval) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 승인 설정 확인
SELECT * FROM customer_workflow_task_template WHERE customer_id = ?;

-- 승인 라인(단계) 확인
SELECT * FROM customer_workflow_task_template_stage
WHERE customer_id = ? AND customer_workflow_task_template_id = ?;

-- VOC 해당 근무 승인 건 확인
SELECT * FROM v2_user_work_record_approval_content
WHERE customer_id = ? AND user_id = ?;

-- 실제 승인 단계 상태 확인
SELECT * FROM workflow_task WHERE customer_id = ? AND task_key = ?;
SELECT * FROM workflow_task_stage WHERE customer_id = ? AND workflow_task_id = ?;
```

## 삭제된 구성원 승인건 강제 승인

> "퇴직자 승인자 교체"와 별개의 처리 절차. 삭제된 구성원은 퇴사 이벤트가 발행되지 않아 `approval_replacement_target`에 등록되지 않으므로 제품의 교체 기능이 동작하지 않는다.

### 사전 확인

1. [Metabase 퇴사자 미처리 승인 대시보드](https://metabase.dp.grapeisfruit.com/dashboard/245)에서 대상 userId로 미처리 건 확인
2. 퇴직자인지 삭제된 구성원인지 판별:

```sql
-- 대상 사용자 상태 확인
SELECT user_id, email, status, resigned_at, deleted_at
FROM view_user
WHERE customer_id = ? AND user_id = ?;
-- status가 DELETED이면 삭제된 구성원, RESIGNED이면 퇴직자
```

### 처리 절차

**퇴직자(resigned)** → 제품의 "퇴직자 승인자 교체" 기능 또는 `replacement-targets/migrate` Operation API 사용

**삭제된 구성원(deleted)** → `bulk-approve-for-user` API로 강제 승인:

```
POST /api/operation/v2/approval/process/customers/{customerId}/users/{userId}/bulk-approve-for-user
Body: { "categories": ["TIME_OFF", "WORK_RECORD"] }
```

- Swagger: `https://flex-raccoon.grapeisfruit.com/swagger/approval`
- category 값: `WORK_RECORD`(근무), `TIME_OFF`(휴가), `TIME_OFF_PROMOTION`(연차촉진) — 대상에 맞게 선택
- **반드시 고객에게 강제 승인 동의를 받은 후 실행**
- 응답의 `succeededProcesses` / `failedProcesses`로 결과 확인

### 주의사항

- `replacement-targets/migrate` API를 먼저 시도하면 삭제된 구성원은 퇴사 조회에 나오지 않아 교체 대상 미등록됨 → 곧바로 `bulk-approve-for-user`로 전환
- 이 패턴은 반복적으로 발생하는 운영 요청임 (CI-3769, CI-2345, CI-1128 등)

## 과거 사례

- **퇴직자 승인자 교체 — 고아 승인 요청**: "교체 필요 3건" 표시되나 실제 휴가 사용 건 없음. `target_uid`와 데이터 불일치. 수동 처리로 해결 — **버그 추정 (수동 대응)** [CI-3951]
- **승인 완료 문서가 진행중 표시 — 승인-워크플로우 이벤트 동기화 실패**: approval_process는 APPROVED인데 workflow_task가 ONGOING으로 잔류. 승인 이벤트가 워크플로우로 전파되지 않아 문서함에서 진행중으로 표시됨. `sync-with-approval` Operation API로 보정 — **버그 (운영 대응)** [CI-4019] [CI-4182]
- **승인 리마인드 발송자 추적**: 관리자가 갑자기 승인 확인 알림을 받았다고 문의. access log 조회로 실제 발송자(다른 관리자)를 특정 — **스펙 (로그 확인)** [CI-4203]
- **경력/학력 변경 요청 댓글 누락/중복**: FE가 UserDataApproval activities API를 `sort=ASC&size=1`로 호출하여 action history만 반환, 댓글 누락. BE 응답은 정상(targetUid 기반 UUID 고유키로 cross-contamination 없음). 동일 댓글 2회 POST도 확인(idempotency 미적용) — **버그 (FE)** [CI-4193]

## 코어 런북 보강 — 과거 사례 (추가)

- **삭제된 구성원 승인건 강제 승인**: 관리자가 2차 조직장 계정을 삭제하여 승인 라인 깨짐. 삭제된 사용자는 퇴사 이벤트 미발행 → `approval_replacement_target` 미등록 → 퇴직자 교체 불가. `bulk-approve-for-user` API로 강제 승인 처리 — **스펙 (운영 대응, 반복 패턴)** [CI-4228] [CI-3769]
- **승인 완료 후 데이터 반영 오류**: 승인 완료 이벤트 처리 중 오류 → ONGOING 상태 잔류. `re-produce-messages` Operation API로 이벤트 재발행하여 정상 처리 — **운영 대응** [코어 런북]
- **승인 완료 문서가 진행중 표시 (워크플로우 동기화)**: approval_process APPROVED인데 workflow_task ONGOING 잔류. `sync-with-approval` Operation API로 보정. 반복 발생 패턴 — **버그 (운영 대응)** [CI-4019] [CI-4182]
