# 권한 (Permission) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 특정 회사의 최고관리자 grant 멤버 조회
SELECT gs.subject_id, gs.created_by, gs.created_at
FROM flex_authorization.flex_grant_subject gs
  JOIN flex_authorization.flex_grant g ON g.id = gs.grant_id
WHERE gs.customer_id = ? AND g.title_key = 'authority.administrator_title';

-- 특정 사용자가 포함된 모든 grant 조회
SELECT gs.subject_id, gs.created_by, gs.created_at, g.title_text, g.title_key
FROM flex_authorization.flex_grant_subject gs
  JOIN flex_authorization.flex_grant g ON g.id = gs.grant_id
WHERE gs.customer_id = ? AND gs.subject_id = ?;
```

## 과거 사례

- **최초 유저 최고관리자 자동 부여**: 회사 생성 시 첫 유저에게 자동 부여, 감사로그에 이력 없음. `flex_grant_subject` 물리 삭제로 회수 후 이력 추적 불가 — **스펙** [CI-4150]
- **퇴사자 최고관리자 증명 자료 요청**: DB 물리삭제로 이력 없으나, **OpenSearch 감사로그에서 권한 변경 이벤트 확인 가능** (보존 기간 내). Envers/raccoon audit API는 미포함. 증빙 필요 시 이메일 발송 — **해결 가능** [CI-4377]
