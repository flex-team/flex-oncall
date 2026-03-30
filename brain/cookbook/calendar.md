# 캘린더 연동 (Calendar Integration) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 도메인 컨텍스트

### 구현 특이사항

- **24년 10월 이전 데이터 싱크 금지**: 중복 생성 우려 — 해당 기간 데이터 재동기화는 비권장
- **Google Calendar API rate limit**: 한 번에 300건 이상 호출 시 rate limit 발생. batch 5~20건 + 2초 delay 권장
- **raccoon audit log URL 제한**: 50건 이상 bulk 시 raccoon audit log URL 길이 초과 오류 발생 가능
- **insufficientPermissions 오류**: 유저가 캘린더 쓰기권한 없는 토큰으로 연동한 경우. 기존 연동 해제 후 쓰기 권한 포함 재연동 안내 필요
- **퇴사자 연동 해제**: `v2_external_calendar_connection` + 연동된 `v2_oauth_user_token` 모두 삭제 필요 (어느 한쪽만 삭제하면 불완전)

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
```
