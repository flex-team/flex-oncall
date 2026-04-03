# 전자계약 (Contract/Digicon) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 도메인 컨텍스트

### 구현 특이사항
- **PDF 실시간 렌더링**: digicon의 PDF는 저장/캐시하지 않고 열람 시마다 DB에서 `placeholder_values`를 읽어 renderer(flex-html)로 렌더링한다. 따라서 DB 값 수정 = 재발송 없이 즉시 반영.
- **placeholder_values 암호화**: `{cipher}` prefix로 암호화되어 SQL 직접 UPDATE 불가. 데이터 보정은 반드시 애플리케이션 레벨(Operation API)에서 수행해야 한다.
- **flex-html renderer 전화번호 검증**: hyphen 포함 전화번호를 유효하지 않은 데이터로 판단하여 placeholder 치환을 skip한다.

---

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

-- 계열사에 서식 복제 (Operation API)
POST /api/operation/v2/digicon/duplicate-templates
-- body: {"originalCustomerId": ?, "targetCustomerIds": [?], "postfix": ""}
-- placeholder + template 모두 복제됨. postfix=""이면 원본 제목 유지.

-- candidate set 기준 계약서 현황 (placeholder 값 포함)
SELECT id, progress_status, placeholder_values, file_key, render_version
FROM digicon
WHERE digicon_candidate_set_id = ? AND customer_id = ?
ORDER BY id;

-- placeholder 값 sanitize (Operation API)
POST /api/operation/v2/digicon/customers/{customerId}/sanitize-placeholder-values
-- body: {"digiconCandidateSetId": ?, "placeholderLabel": "?", "sanitizeString": "-"}
-- 멱등성 보장: 이미 제거된 경우 modifiedCount=0
```

## 과거 사례

- **서명 완료 계약서 삭제 불가**: SUCCEED 상태 계약서는 `cancelable() = this === IN_PROGRESS`로 취소 불가, Operation API에도 삭제 엔드포인트 없음. 법적 효력 보존이 설계 의도. 정석: 올바른 내용으로 재계약 발송 — **스펙** [CI-4152]
- **서식 삭제자 access log 추적**: 감사로그에 서식 삭제 미기록. access log traceId → permission-api 호출 체인으로 삭제자 특정 가능. soft delete로 Operation API 복구 가능 — **스펙 (개선 필요)** [CI-4168]
- **선택 발송 시 미선택 임시저장 계약서 삭제**: CandidateSet = 한 번의 발송 단위로 설계. `execute()` 시 `targetDigiconCandidateUnitIdHashes`에 포함되지 않은 CandidateUnit은 `deleteAllById()`로 물리 삭제. 복구 불가. VOC-2410으로 UX 개선 요청 등록됨 — **스펙** [CI-4257]
- **계열사 전자계약 서식 복제**: 계열사 간 서식 공유 기능이 제품에 없어 Operation API `duplicateTemplates`로 수동 복제. 원본 placeholder + template을 대상 고객사에 복사, form HTML의 placeholder ID도 자동 치환. 비엔지니어도 가능한 수준(customerId 입력이 전부)이나 아직 어드민 셸 메뉴 미구현 — **ops** [CI-4283]
- **전자계약 일괄 다운로드 링크 미생성 — 파일 서비스 밀림**: admin-shell에서 bulk-download-pdf 요청 후 PDF 업로드(87건) 정상 완료, fileMergeId 발급 후 merge 큐가 ~3~8시간 지연. S3 임시 파일 TTL(600초) 초과로 병합 시 파일 부재 → ERROR. 병합 실패 callback이 digicon 서비스에 미전달(MEREGED 로그 0건). 구조적 문제: TTL < merge 큐 처리시간이면 항상 실패. 파일 서비스 장애 해소 후 재시도로 해결 — **Not a Bug(ops)** [CI-4248]
- **전자계약 엑셀 업로드 후 연락처 공란**: `placeholder_values`에 hyphen 포함 전화번호(010-1111-2222) 저장 → flex-html renderer가 유효하지 않은 값으로 판단하여 미치환. PDF는 실시간 렌더링이므로 DB 값 수정 시 즉시 반영. `placeholder_values`는 `{cipher}` 암호화되어 DB 직접 UPDATE 불가, `sanitize-placeholder-values` Operation API 사용. FE 핫픽스로 재발 방지 — **code-fix** [CI-4297]
