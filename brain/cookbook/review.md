# 평가 (Evaluation / Performance Management) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 도메인 컨텍스트

### 이 도메인이 하는 일

성과 평가 주기 운영(평가 생성/편집/삭제), 평가지(UserForm) 생성·작성, 등급 배분, 리뷰 마이그레이션(구→신 성과관리 전환)을 담당한다. `flex-review-backend` 에서 관리하며, 별도의 평가 데이터베이스(`flex_review`)를 사용한다.

### 핵심 개념

- **평가(`evaluation`)**: 하나의 평가 주기. DRAFT(초안) → BEFORE_START(시작 전) → 진행 중 → 완료의 생명주기를 가진다. soft delete(`deleted_at`)로 관리.
- **평가지(`UserForm`, `form_user_form`)**: 리뷰어가 리뷰이에 대해 작성하는 개별 양식. `evaluation_reviewer` 테이블의 `user_form_ids`로 연결. finalize 이후 추가된 reviewer는 메시지 큐로 UserForm을 초기화하는데, 이 단계에서 실패하면 "생성 중" 상태로 잔류한다.
- **등급 배분(`grades_to_calculate`)**: 평가 완료 단계에서 등급 산출에 사용되는 설정. 비어있으면(`[]`) finalize 시 `DraftEvaluationStageValidator` 검증 실패.
- **뉴성과관리 마이그레이션**: `MigrationScheduler`에 의해 구 리뷰(`review_set`)를 신 평가(`evaluation`)로 전환. 구 리뷰는 soft delete 처리.

### 주요 흐름

1. **평가 생성/편집**: 관리자가 평가 주기 설정 → DRAFT 상태 → 항목·역량·등급 체계 구성
2. **평가 진행**: 리뷰이-리뷰어 매핑 → UserForm 생성 → 작성 요청 발송 → 작성·제출
3. **등급 산출·완료**: 등급 배분 설정 → 자동 산출 → finalize

### 비즈니스 규칙

- **title=null DRAFT 평가**: 과거 버그로 title이 null인 DRAFT 평가가 존재할 수 있다. FE에서 목록 필터링으로 비노출 처리했으나, FE 핫픽스 이후 정상 노출되면서 고객이 "삭제했던 것이 복원됐다"고 오인하는 패턴.
- **삭제된 평가 복구**: soft delete이므로 `deleted_at = NULL` DML로 복구 가능. Operation API(PR #5181) 머지 후에는 API로도 복구 가능.
- **raccoon 환경 불일치**: 리뷰 마이그레이션 시 dev raccoon에 prod 해시를 사용하면 Hashids salt 불일치로 디코딩 실패. 반드시 prod raccoon 사용.
- **평가 단계 시작 후 설정 변경 불가**: 평가 진행 중에는 등급 배분율(`evaluation_grade_distribution`) 설정 UI 편집이 잠긴다. 변경이 필요하면 DML 보정으로만 가능하다. `allow_submission_if_exceed`: 0=초과 시 제출 차단, 1=초과해도 제출 허용. [CI-4327]

### 자주 혼동되는 것들

- **구 리뷰(`review_set`) vs 신 평가(`evaluation`)**: 뉴성과관리 전환 후 두 테이블이 공존한다. `review_set.deleted=1`은 마이그레이션에 의한 의도적 삭제이지 사용자 삭제가 아니다. `evaluation` soft delete와 혼동 주의.
- **"평가 공동편집자 아닌데 메뉴가 보여요"**: title=null DRAFT 평가의 FE 필터링 이슈. 실제 권한 문제가 아니라 데이터 이상.
- **"평가지 생성 중"**: `user_form_ids`가 `[]`이면 UserForm 초기화가 실패한 것. `initialize-user-form` Operation API로 수동 해결.

### 구리뷰(Legacy Review) 특이사항

- **구리뷰 섹션명 저장**: `review_question` 테이블에 `question_type = 'SUBTITLE'` 행으로 저장. 별도 섹션 테이블(`review_question_section`)에는 name 컬럼 없음.
- **진행 중 구리뷰 질문 수정**: 제품 UI 미지원. `review_question.question` UPDATE + `question_log.content` 동기화 DML로만 가능. 텍스트 수정만 허용, 추가/삭제/타입 변경 불가. (선례: FT-12322, FT-2557)
- **question_log 동기화 필수**: `review_question.question` 변경 후 반드시 `question_log.content`도 UPDATE해야 리뷰어 화면에 반영됨.
- **review_set ↔ template 연결**: `review_model` 테이블이 중간 연결자. `review_model.review_set_id` + `review_model.onetime_template_id`로 각 단계(셀프/하향/상향)의 템플릿을 찾는다.
- **오퍼레이션 허용 범위** (FT-12322 선례 기준): 질문 제목/설명 텍스트 수정 → 가능. 질문 추가/삭제/선택형 수정/타입 변경 → 불가.

### 구현 특이사항

- **Vaadin admin**: 평가 관련 일부 관리 기능은 Vaadin 기반 어드민 화면을 사용한다. 일반 API와 다른 UI 스택.
- **마이그레이션 스케줄러**: `MigrationScheduler`는 뉴성과관리 전환 시 구 리뷰를 자동 soft delete. OpenSearch 로그에서 `[migrate]` 태그로 추적 가능.
- **EvaluationStep 크론 자동 복구**: `EvaluationStepScheduler`가 **매분 0초**에 실행되어 `RESERVED` 상태 단계를 `IN_PROGRESS`로 자동 전환한다. "지금 시작" 후 FE-BE 시간차로 RESERVED 상태가 된 경우 최대 1분 내 자동 복구. 고객 문의 시 "잠시 후 자동으로 해결됐습니다"라고 안내 가능. [CI-4164]
- **"지금 시작" vs "예약" 구분**: `period.start`가 서버 현재 시각보다 미래이면 BE는 무조건 `RESERVED`로 판정한다(`now < period.start` strict 비교). FE-BE 시계 차이가 수 초 이상이면 "지금 시작"이 "예약"으로 저장될 수 있다. API 변경으로 근본 수정됨(2026-03). [CI-4164]
- **삭제 전략 불일치**: `evaluation`(평가 세션)은 soft delete(`deleted_at`, `deleted_user_id`)이나, `evaluation_reviewee`(평가 대상자)는 **hard delete**. 대상자 삭제 시 `evaluation_reviewer`, `form_user_form` 등 6개 테이블이 연쇄 물리 삭제되어 복구 불가. [CI-4387]

---

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

```sql
-- 등급 배분율 설정 확인
SELECT id, evaluation_id, grade_factor_id, allow_submission_if_exceed
FROM flex_review.evaluation_grade_distribution
WHERE customer_id = ? AND evaluation_id = ?;

-- 등급 배분율 제출 제한 해제 (결재 필요)
UPDATE flex_review.evaluation_grade_distribution
SET allow_submission_if_exceed = 1
WHERE customer_id = ? AND evaluation_id = ? AND id = ?;

-- 롤백
-- UPDATE flex_review.evaluation_grade_distribution
-- SET allow_submission_if_exceed = 0
-- WHERE id = ?;
```

```sql
-- 구리뷰 진행 중 질문 텍스트/섹션명 수정 (결재 필요)
-- Step 1: 백업 — 변경 전 반드시 보관
SELECT rq.id, rq.template_id, rq.question_type, rq.question, rq.description
FROM flex_review.review_question rq
WHERE rq.template_id = ?
  AND rq.question_type IN ('SUBTITLE', 'LONG_TEXT', 'RATING');

-- Step 2: 질문 텍스트 수정
UPDATE flex_review.review_question
SET question = '수정할 텍스트'
WHERE id = ?
  AND template_id = ?;

-- Step 3: question_log 동기화 (필수 — 누락 시 리뷰어 화면 미반영)
UPDATE flex_review.question_log ql
JOIN flex_review.review_question rq ON ql.question_id = rq.id
SET ql.content = rq.question,
    ql.description = rq.description
WHERE rq.template_id = ?
  AND (rq.question != ql.content OR rq.description != ql.description);
```

## 과거 사례

- **삭제한 평가가 다시 노출**: 실제로는 삭제된 적 없는 title=null DRAFT 평가가 FE 핫픽스로 정상 노출된 것. 고객이 "이전에 안 보이던 것이 보임"을 "삭제 복원"으로 오해 — **스펙** [CI-4158]
- **평가 공동편집자 아닌데 메뉴 노출**: title=null인 DRAFT 평가를 FE에서 필터링하여 노출 문제 — **버그 (FE)** [CI-4129]
<!-- TODO: 시나리오 테스트 추가 권장 — title=null DRAFT 평가 리스트 정상 노출 검증 -->
- **리뷰 마이그레이션 "Failed requirement." 에러**: dev raccoon에서 prod 해시 사용 → Hashids salt 불일치로 디코딩 실패(`INVALID_NUMBER`). prod raccoon에서 재시도하면 구체적 에러 정상 출력 — **운영 오류** [QNA-1936]
- **후발 추가 reviewer 평가지 미생성**: finalize 이후 추가된 reviewer의 UserForm이 메시지 큐 실패로 초기화 안 됨. admin 화면에서 "생성 중" 표시. Operation API `initialize-user-form`으로 수동 해결 — **운영 대응** [CI-4188]
- **삭제된 진행 중 평가 복구**: 고객 관리자가 다른 평가를 삭제하려다 진행 중 평가까지 삭제. `evaluation` 테이블 soft delete(`deleted_at`, `deleted_user_id`) NULL 복구 DML로 해결. Operation API PR #5181 머지 후 API 복구 가능 — **운영 대응** [CI-4195]
- **등급 배분율 초과 시 제출 차단 설정 보정**: 평가 진행 중 `evaluation_grade_distribution.allow_submission_if_exceed = 0` 상태에서 배분율 초과 시 제출 불가. 평가 단계 시작 후 UI 편집 잠김 — DML로만 보정 가능. `evaluation_id`와 레코드 `id` 모두 WHERE 조건 필요 — **운영 대응** [CI-4327]
- **진행 중 구리뷰 질문 텍스트 수정**: 리뷰 게시 후 질문 수정은 제품 비지원(스펙). 단, 질문 제목/설명 텍스트 수정만 예외 오퍼레이션 가능. `review_question.question` UPDATE 후 반드시 `question_log.content` 동기화 필요 — 섹션명도 `question_type='SUBTITLE'` 행으로 동일 처리. **불가 범위**: 질문 추가/삭제/타입 변경, 선택형 수정 — **운영 대응** [CI-4338]
- **평가 대상자(reviewee) 삭제 복구 요청**: `evaluation`(세션) 삭제는 soft delete이나, `evaluation_reviewee`(대상자) 삭제는 **hard delete**. 대상자 삭제 시 `evaluation_reviewer`, `form_user_form`, `evaluation_reviewee_step_mapping`, `reviewee_evaluation_item`, `evaluation_reviewer_nomination` 6개 테이블 연쇄 물리 삭제. 애플리케이션 복구 불가 → 고객에게 대상자 재추가 + 평가 재작성 안내 — **운영 대응 (복구 불가)** [CI-4387]
