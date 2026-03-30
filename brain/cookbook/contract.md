# 전자계약 (Contract/Digicon) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 삭제된 서식 목록 (soft delete)
SELECT id, name, deleted_at, created_at
FROM customer_digicon_template
WHERE customer_id = ? AND deleted_at IS NOT NULL
ORDER BY deleted_at DESC;

-- 서명 완료 계약서 조회 (삭제 불가 확인)
SELECT id, progress_status, file_key, created_date_time
FROM digicon
WHERE customer_id = ? AND user_id = ?
ORDER BY created_date_time DESC;

-- 삭제된 서식 복구 (Operation API)
POST /api/operation/v2/digicon/customers/{customerId}/restore-deleted-templates
```

## 과거 사례

- **서명 완료 계약서 삭제 불가**: SUCCEED 상태 계약서는 `cancelable() = this === IN_PROGRESS`로 취소 불가, Operation API에도 삭제 엔드포인트 없음. 법적 효력 보존이 설계 의도. 정석: 올바른 내용으로 재계약 발송 — **스펙** [CI-4152]
- **서식 삭제자 access log 추적**: 감사로그에 서식 삭제 미기록. access log traceId → permission-api 호출 체인으로 삭제자 특정 가능. soft delete로 Operation API 복구 가능 — **스펙 (개선 필요)** [CI-4168]
- **전자계약 일괄 다운로드 링크 미생성 — 파일 서비스 밀림**: admin-shell에서 bulk-download-pdf 요청 후 PDF 업로드(87건) 정상 완료, fileMergeId 발급 후 merge 큐가 ~3~8시간 지연. S3 임시 파일 TTL(600초) 초과로 병합 시 파일 부재 → ERROR. 병합 실패 callback이 digicon 서비스에 미전달(MEREGED 로그 0건). 구조적 문제: TTL < merge 큐 처리시간이면 항상 실패. 파일 서비스 장애 해소 후 재시도로 해결 — **Not a Bug(ops)** [CI-4248]
