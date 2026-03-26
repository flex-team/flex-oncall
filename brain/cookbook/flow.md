# 워크플로우 (Flow / Approval Document) — Tier-2

> Tier-1: [COOKBOOK.md](../COOKBOOK.md) > 워크플로우 섹션
> 과거 사례 상세, SQL 템플릿, 조사 기록을 이 파일에서 관리한다.

## 과거 사례

### CI-4220: 할일 작성하기 재진입 시 임시저장 초기화 — 버그

- **증상**: 기안서 작성 중 화면을 벗어난 후 돌아왔을 때 임시저장 문서가 사라짐
- **원인**: "할일 > 작성하기" 목록에서 작성하기를 다시 선택하면, 해당 양식의 임시저장 문서가 초기화(재생성)됨
- **해결**: draft data에서 HTML 본문을 추출하여 고객에게 전달
- **핵심 테이블**: `flex.workflow_task_draft` (자동저장 데이터), `flex.workflow_task` (문서 추적)
- **참고**: v3 approval-document 서비스는 flex-flow-backend에서 분리되어 별도 운영 (코드 접근 불가)

## SQL 템플릿

```sql
-- 사용자의 워크플로우 임시저장 문서 조회
SELECT id, customer_id, user_id, workflow_task_key, schema_version,
       created_date, last_modified_date
FROM flex.workflow_task_draft
WHERE user_id = ? AND customer_id = ?
ORDER BY last_modified_date DESC;

-- draft 데이터(본문) 확인 — headline, text 필드
SELECT id, workflow_task_key,
       SUBSTRING(data, LOCATE('"headline"', data), 200) as headline_area,
       LENGTH(data) as data_len
FROM flex.workflow_task_draft
WHERE id = ?;

-- 관련 workflow_task 존재 여부 확인
SELECT id, task_key, status, title, writer_id, created_date, deleted_date
FROM flex.workflow_task
WHERE task_key = ? AND customer_id = ?;
```
