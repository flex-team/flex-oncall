# 평가 (Evaluation / Performance Management) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 삭제된 평가 조회
SELECT id, name, status, deleted_at, deleted_user_id
FROM flex_review.evaluation
WHERE customer_id = ? AND deleted_at IS NOT NULL
ORDER BY deleted_at DESC;

-- 삭제된 평가 복구 (결재 필요)
UPDATE flex_review.evaluation
SET deleted_at = NULL, deleted_user_id = NULL
WHERE id = ?;

-- 복구 롤백
-- UPDATE flex_review.evaluation
-- SET deleted_at = '{원래_deleted_at}', deleted_user_id = {원래_deleted_user_id}
-- WHERE id = ?;
```

```sql
-- 평가지 미생성 reviewer 조회
SELECT id, reviewee, reviewer, step_type, user_form_ids, writing_requested_at, created_at
FROM evaluation_reviewer
WHERE customer_id = ? AND evaluation_id = ?
ORDER BY created_at;

-- form 생성 확인
SELECT id, created_at FROM form_user_form
WHERE id IN (?);
```

## 과거 사례

- **삭제한 평가가 다시 노출**: 실제로는 삭제된 적 없는 title=null DRAFT 평가가 FE 핫픽스로 정상 노출된 것. 고객이 "이전에 안 보이던 것이 보임"을 "삭제 복원"으로 오해 — **스펙** [CI-4158]
- **평가 공동편집자 아닌데 메뉴 노출**: title=null인 DRAFT 평가를 FE에서 필터링하여 노출 문제 — **버그 (FE)** [CI-4129]
<!-- TODO: 시나리오 테스트 추가 권장 — title=null DRAFT 평가 리스트 정상 노출 검증 -->
- **리뷰 마이그레이션 "Failed requirement." 에러**: dev raccoon에서 prod 해시 사용 → Hashids salt 불일치로 디코딩 실패(`INVALID_NUMBER`). prod raccoon에서 재시도하면 구체적 에러 정상 출력 — **운영 오류** [QNA-1936]
- **후발 추가 reviewer 평가지 미생성**: finalize 이후 추가된 reviewer의 UserForm이 메시지 큐 실패로 초기화 안 됨. admin 화면에서 "생성 중" 표시. Operation API `initialize-user-form`으로 수동 해결 — **운영 대응** [CI-4188]
- **삭제된 진행 중 평가 복구**: 고객 관리자가 다른 평가를 삭제하려다 진행 중 평가까지 삭제. `evaluation` 테이블 soft delete(`deleted_at`, `deleted_user_id`) NULL 복구 DML로 해결. Operation API PR #5181 머지 후 API 복구 가능 — **운영 대응** [CI-4195]
