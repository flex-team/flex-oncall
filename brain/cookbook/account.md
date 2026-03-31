# 계정/구성원 (Account / Member) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 도메인 컨텍스트
### 구현 특이사항
- **isShutdownActivated() 판단 순서**: 서비스 접근 차단 판단 시 `billingRule 없음 → 차단 상태 → 차단 비활성화(force-open) → 무료체험 기간 내 → 카드 없음 → 활성 피처 확인` 순으로 평가. 카드 null 체크(조건 5)가 활성 피처 체크(조건 6)보다 선행하므로, 카드 미등록 상태에서는 구독 플랜 유무와 무관하게 차단된다 [CI-4291]

---

## 데이터 접근

```sql
-- 겸직 그룹/주법인 상태 조회
-- Metabase dashboard/212?고객사_id= 로 확인 가능
-- 겸직 user_id 조회: Metabase question/3332-user-id?email=

-- 대표회사 변경 (workspace_customer_mapping)
-- 주법인으로 설정할 행: is_primary = 1
-- 기존 주법인 행: is_primary = 0
-- (두 쿼리를 트랜잭션 내에서 실행)
UPDATE flex.workspace_customer_mapping SET is_primary = 1 WHERE id = ?;
UPDATE flex.workspace_customer_mapping SET is_primary = 0 WHERE id = ?;

-- 삭제된 구성원 복원 확인 (Snapshot에서 복원 대상 조회)
SET @member_id = ?;
SELECT * FROM flex.member WHERE id = @member_id;
SELECT * FROM flex_auth.account WHERE member_id = @member_id;
SET @account_id = ?;
SELECT * FROM flex_auth.account_user_mapping WHERE account_id = @account_id;
SELECT * FROM flex_auth.authentication_method WHERE account_id = @account_id;
-- 복원 대상 테이블: member(UPDATE), account/account_user_mapping/authentication_method(INSERT)

-- 대상 구성원 조회 (이메일 변경 전 확인)
SELECT id, customer_id, email, primary_user_id, deleted_date
FROM user
WHERE customer_id = ?
  AND deleted_date IS NULL
ORDER BY email;

-- 특정 이메일 사용자 조회
SELECT id, customer_id, email, primary_user_id, deleted_date
FROM user
WHERE customer_id = ?
  AND email LIKE ?;

-- OTP 2차인증 설정 확인
SELECT id, customer_id, required, db_created_at, db_updated_at
FROM flex_auth.customer_credential_t_otp_setting
WHERE customer_id = ?;
```

## 겸직 매핑 조회 — ⚠️ 반드시 1명씩 개별 조회

겸직 구성원의 양쪽 회사 user_id를 찾을 때 `member_user_mapping`을 사용한다.

> ⚠️ **절대 IN으로 여러 이메일을 한 번에 조회하지 않는다.**
> 서브쿼리가 여러 `member_id`를 반환하면, 바깥 쿼리가 여러 member에 속한 사용자를 모두 섞어서 반환한다.
> 결과 건수가 얼핏 맞아 보여도 user_id 매핑이 잘못된다.

**올바른 방법 — 이메일 1개씩 개별 조회:**
```sql
SELECT customer_id, id AS user_id, email
FROM flex.view_user
WHERE id IN (
    SELECT user_id FROM flex.member_user_mapping
    WHERE member_id = (
        SELECT member_id FROM flex.member_user_mapping
        WHERE user_id = (
            SELECT id FROM flex.view_user WHERE email = trim('{이메일}')
        )
    )
);
```
→ 3명이면 이 쿼리를 3번 실행한다. [^account-concurrent-1]

**결과 해석:**
- 2건 반환 → 겸직 등록됨 (이스트소프트 1건 + 이스트시큐리티 1건)
- 1건 반환 → 해당 회사에만 유저가 있음 → **겸직 미등록** → 주법인 변경 불가

[^account-concurrent-1]: CI-4271 — IN 일괄 조회 시 member_id 교차오염 확인. leezho/jina가 같은 member에 속해 잘못된 매핑이 반환됨.

## 과거 사례

- **단건 이메일 변경 (퇴사자 관리자 계정)**: 스폰서십 등록 계정의 관리자 이메일이 퇴사자. Operation API 단건 변경으로 처리 — **운영 요청** [CI-4118]
- **일괄 이메일 변경 (도메인 변경)**: 회사 도메인 변경으로 이메일 일괄 변경. 미존재/이미 변경된 이메일 포함 시 전체 실패 → DB 사전 검증 후 제외하여 재호출로 성공 — **운영 요청** [CI-4124] [CI-4200] [CI-4163]
- **계열사 전환 시 로그인 풀림 (SSO)**: SSO(OAuth2/SAML2/OIDC) PC웹 로그인 시 workspace refresh token 미발급(보안 설계). workspace access token(12h) 만료 후 계열사 전환(`/tokens/customer-user/exchange`) 시 401. 단일 회사 사용은 customer-user token(7일)으로 정상 — **스펙** [CI-4166]
- **관리자 퇴사 후 OTP 해제 불가**: 기존 관리자가 OTP 설정을 켜고 퇴사 → 신규 관리자 로그인 차단 → DB UPDATE로 해제 — **스펙** [CI-4176]
- **결제 취소 후 로그인 차단 → 카드 재등록 불가**: 결제 취소 시 접근 차단(스펙). raccoon billing `force-open`으로 임시 접근 허용 → 카드 등록 → `close-forced-open` 원복. 체험 종료일은 결제 이력 있는 고객 변경 불가 — **스펙** [CI-4169]
- **무료체험 종료 + 카드 미등록 → 구독 추가만으로 접속 불가**: `isShutdownActivated()`에서 카드 null 체크(조건 5)가 활성 피처 체크(조건 6)보다 선행 → 구독 플랜 추가해도 카드 없으면 `return true`(차단). 무료체험 종료일을 오늘 이후로 연장 → 카드 등록 → 결제 생성으로 해결 — **스펙** [CI-4291]

## 코어 런북 보강 — 데이터 접근 (추가)

```sql
-- 입사일 변경 전 기존 값 확인 (Metabase #7227)
SELECT c.name AS '고객사명', u.id, u.email,
       ue.company_join_date, m.company_group_join_date, m.is_company_group_join_date_used
FROM user u
  LEFT JOIN user_employee ue ON u.id = ue.user_id
  LEFT JOIN member_user_mapping ON u.id = member_user_mapping.user_id
  LEFT JOIN flex.member m ON member_user_mapping.member_id = m.id
  LEFT JOIN customer c ON u.customer_id = c.id
WHERE ue.user_id = ?;

-- 개인정보 보유현황: 이름/이메일 (user 테이블 — 필수값이므로 유저 수와 동일)
-- name_in_office (닉네임)
SELECT COUNT(*) FROM user
WHERE customer_id = ? AND deleted_date IS NULL
  AND name_in_office != '{cipher}44062be3131a4b6ffcdc870e02696817';

-- 사번
SELECT COUNT(*) FROM user_employee
WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL)
  AND employee_number IS NOT NULL;

-- 주민등록번호
SELECT COUNT(*) FROM member
WHERE id IN (SELECT member_id FROM member_user_mapping
             WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL))
  AND ssn IS NOT NULL;

-- 생년월일 / 휴대폰번호 / 국적 / 집주소
SELECT COUNT(*) FROM user_personal
WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL)
  AND birth_date IS NOT NULL;
-- phone_number: != '{cipher}44062be3131a4b6ffcdc870e02696817'
-- nationality: != 'UNKNOWN'
-- address_full: != '{cipher}44062be3131a4b6ffcdc870e02696817'

-- 계좌번호
SELECT COUNT(*) FROM user_bank_account
WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL);

-- 경력사항 / 학력사항
SELECT COUNT(*) FROM user_work_experience
WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL);

SELECT COUNT(*) FROM user_education_experience
WHERE user_id IN (SELECT id FROM user WHERE customer_id = ? AND deleted_date IS NULL);
```

> ⚠️ `{cipher}44062be3131a4b6ffcdc870e02696817`은 공백을 의미

## 코어 런북 보강 — 과거 사례 (추가)

- **입사일 변경 — 미래 입사일로 접속 불가**: 최고관리자 1명인 고객사에서 미래 입사일 설정 → 접속 차단 → CS 인입. Operation API로 입사일 변경 — **운영 요청** [코어 런북]
- **삭제된 구성원 복구**: 휴먼 에러로 마스킹 처리 → DB Snapshot에서 복구 → opensearch/bullseye 동기화 — **운영 요청** [코어 런북]
- **개인정보 보유현황 파악**: 시즈널 요청. 삭제되지 않은 유저 대상 테이블별 count — **운영 요청** [코어 런북]

## OpenSearch sync / 조직도 통계 — 데이터 접근 (추가)

```sql
-- 청구일 구성원 수 불일치: 청구일 이후 퇴직 처리된 구성원
SELECT * FROM flex.user_resignation
WHERE status = 'VALID' AND customer_id = ?
  AND db_updated_at > ?  -- paid_date
  AND begin_date < ?     -- paid_date
ORDER BY db_updated_at DESC;

-- 청구일 이후 입사 처리된 구성원 (입사일이 청구일 이전)
SELECT * FROM flex.user_employee
WHERE deleted_at IS NULL AND customer_id = ?
  AND db_created_at > ?      -- paid_date
  AND company_join_date < ?  -- paid_date
ORDER BY db_updated_at DESC;

-- 이메일 인증 요청 조회
SELECT * FROM flex_auth.email_verification
WHERE email LIKE '%@{some-domain}' ORDER BY db_created_at DESC;
```

## OpenSearch sync / 조직도 통계 — 과거 사례 (추가)

- **조직도 월별 통계 오류**: 삭제된 구성원이 ES에 잔존 → projection/search 결과 불일치. ES 싱크로 즉시 해결 — **버그 (설계 한계)** [코어 런북]
- **청구일 구성원 수 불일치**: 청구 시점 스냅샷 vs 현재 시점 조회 차이. 퇴직/입사 처리 시점 확인으로 원인 설명 — **스펙** [코어 런북]

## 구성원 검색 페이지네이션 — 과거 사례

- **사번 정렬 무한 스크롤 + 겸직 인원 중복 표시**: `ValuesContinuation.print()`에서 `joinToString()`이 null을 "null" 문자열로 변환 → OpenSearch `search_after`에서 keyword 필드의 null(missing)과 "null"은 다른 정렬 위치 → 커서가 null 구간을 벗어나지 못하고 무한 반복. 사번 null 구성원이 있는 모든 회사에서 재현. 겸직은 무관(1 user = 1 document) — **버그** [CI-4232]
