# 외부 API / 데이터 통합 (OpenAPI)

## 도메인 컨텍스트

### 이 도메인이 하는 일
flex의 HR 데이터를 외부 시스템에 제공하는 OpenAPI 서비스. 고객사가 자체 시스템과 flex를 연동할 때 사용한다.

### 핵심 개념
- **CUSTOMER 토큰**: 회사 단위로 발급되는 API 토큰. userId=0으로 표시됨
- **grant configuration**: 토큰별 API 권한 세분화 설정. grantConfigurationId가 null이면 모든 action 허용, NOT null이면 명시적으로 허용된 action만 접근 가능
- **OpenAPI action**: `open_api_user_work_schedule`, `open_api_user_basic_info` 등 23종의 granular action

### 비즈니스 규칙
- grant configuration이 설정된 토큰은 해당 configuration에 포함된 action만 접근 가능 (스펙)
- `/v2/departments/all`, `/v2/users/employee-numbers`는 access check를 수행하지 않아 grant configuration과 무관하게 항상 접근 가능

### 구현 특이사항
- 권한 체크는 2단계: (1) DB에 grant configuration 저장 (2) OpenFGA에 튜플 동기화. DB와 OpenFGA 사이에 동기화 문제가 발생할 수 있음
- `AUTHZ_403_000`은 authorization-api에서 반환하는 에러 코드, `OPENAPI_403_001`은 open-api 자체 IP ACL 실패 코드 — 둘 다 HTTP 403이지만 원인이 다름

---

## 데이터 접근

```sql
-- grant configuration 조회
SELECT id, service_key, customer_id, title_text, status, created_at, created_by
FROM flex_authorization.flex_grant
WHERE id = ? -- grantConfigurationId
```

```sql
-- grant에 포함된 authority group (허용 action) 목록
SELECT id, grant_id, authority_group_key, accessible_relations, created_at
FROM flex_authorization.flex_grant_authority_group
WHERE grant_id = ? -- grantConfigurationId
```

```sql
-- session state와 grant configuration 매핑
SELECT id, session_state_id, grant_configuration_id, db_created_at
FROM flex_openapi.token_session_state_grant_configuration_mapping
WHERE grant_configuration_id = ?
```

## 과거 사례
- **OpenAPI 403 — grant configuration DB↔OpenFGA 동기화**: customerId 96860. DB에 23개 action 모두 설정되어 있으나 OpenFGA batch-check에서 allowed=false. 동기화 문제 추정 — **조사 중** [CI-4270]
