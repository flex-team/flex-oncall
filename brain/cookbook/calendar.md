# 캘린더 연동 (Calendar Integration) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 도메인 컨텍스트

### 구현 특이사항

- **24년 10월 이전 데이터 싱크 금지**: 중복 생성 우려 — 해당 기간 데이터 재동기화는 비권장
- **Google Calendar API rate limit**: 한 번에 300건 이상 호출 시 rate limit 발생. batch 5~20건 + 2초 delay 권장
- **raccoon audit log URL 제한**: 50건 이상 bulk 시 raccoon audit log URL 길이 초과 오류 발생 가능
- **insufficientPermissions 오류**: 유저가 캘린더 쓰기권한 없는 토큰으로 연동한 경우. 기존 연동 해제 후 쓰기 권한 포함 재연동 안내 필요
- **퇴사자 연동 해제**: `v2_external_calendar_connection` + 연동된 `v2_oauth_user_token` 모두 삭제 필요 (어느 한쪽만 삭제하면 불완전)

### 비즈니스 규칙

- **연동 해제 ≠ 이벤트 삭제**: 그룹 구글캘린더 연동 해제는 "앞으로의 동기화를 차단"하는 것. DB의 연결 정보(`v2_external_calendar_connection`)만 삭제하며, 구글캘린더에 이미 생성된 이벤트를 삭제하지 않는다. 의도된 설계. [CI-4330]
- **force-sync-deleted / sync-deleted API 적용 범위**: 이 API들은 `google_calendar_event_delete_sync` 레코드가 있을 때만 동작. 연동 해제 케이스에는 해당 레코드가 생성되지 않으므로 적용 불가. [CI-4330]
- **cleansing API의 calendarConnectionHistoryId**: 이미 삭제된 연동에 대해서도 `calendarConnectionHistoryId`로 처리 가능. [CI-4330]

---

## 데이터 접근

```sql
-- 캘린더 이벤트 매핑 확인
SELECT * FROM flex.v2_time_tracking_flex_calendar_event_map WHERE user_id = ?;

-- 퇴사자 구글 캘린더 연동 현황 확인
SELECT * FROM flex.v2_external_calendar_connection WHERE user_id = ?;
SELECT * FROM flex.v2_oauth_user_token WHERE user_id = ?;

-- TT-캘린더 이벤트 삭제 누락 크로스체크 (customer 기준)
SELECT user_id FROM calendar
WHERE id IN (
    SELECT DISTINCT cea.calendar_id
    FROM flex_calendar.calendar_event ce
             LEFT JOIN flex_calendar.calendar_event_attendee cea ON ce.id = cea.event_id
    WHERE cea.index_event_type = 'WORK_RECORD'
      AND ce.start_date_time >= '2025-06-01'
      AND ce.customer_id = ?
      AND ce.deleted_at IS NULL
);

-- 연동 해제된 그룹 캘린더 이력 조회 (calendarConnectionHistoryId 확인)
SELECT id, customer_id, connection_type, connection_state, deleted_at
FROM flex.v2_external_calendar_connection_history
WHERE customer_id = ?
  AND connection_type = 'GROUP'
  AND connection_state = 'DISCONNECTED'
ORDER BY deleted_at DESC;

-- 그룹 캘린더 소유 계정의 OAuth 토큰 조회 (oauthTokenId 확인)
SELECT id, user_id, customer_id, email
FROM flex.v2_oauth_user_token
WHERE customer_id = ?
  AND email = ?;  -- 그룹 캘린더 소유 계정 이메일

-- 연동 해제 후 잔존 이벤트 ID 목록 조회 (flex_calendar DB - Metabase 사용 권장)
-- google_calendar_id: 그룹 캘린더 ID (보통 그룹 캘린더 소유 계정 이메일)
SELECT google_event_id
FROM flex_calendar.google_calendar_event_sync
WHERE query_key LIKE '{customerId}%'
  AND google_calendar_id = ?;  -- 그룹 캘린더 ID
-- ⚠️ flex_calendar DB는 MCP 화이트리스트 미허용 — Metabase 사용 필수
```

## 과거 사례

- **그룹 구글캘린더 연동 해제 후 휴가 일정 124건 잔존**: 유모스원(221855). 연동 해제 시 기존 이벤트 자동 삭제 없음이 스펙임을 확인. `calendarConnectionHistoryId`=48926, `oauthTokenId`=51560으로 cleansing API 20건씩 배치 호출 전체 200 OK. — **스펙+운영대응** [CI-4330]
