# 알림 (Notification) — 상세 진단 가이드

> COOKBOOK.md Tier-1에서 참조되는 상세 SQL 템플릿과 과거 사례 모음

## 데이터 접근

```sql
-- 수신자의 알림 발송 이력
SELECT nd.*, n.notification_type, n.message_data_map
FROM notification_deliver nd
  LEFT JOIN notification n ON nd.notification_id = n.id
WHERE nd.receiver_id = ?
  AND n.db_created_at >= ?;

-- 특정 승인 건의 알림 이력 (notification_topic_id 기준)
SELECT *
FROM notification_deliver nd
  LEFT JOIN notification n ON nd.notification_id = n.id
WHERE nd.notification_topic_id = ?;

-- Core 알림 실제 내용 확인 (title_meta_map이 빈 경우)
SELECT nd.id, n.notification_type, n.message_data_map, nt.topic_type, nt.title_meta_map,
       FROM_UNIXTIME(nd.created_at / 1000) AS delivered_at
FROM notification_deliver nd
  JOIN notification n ON n.id = nd.notification_id
  LEFT JOIN notification_topic nt ON nd.notification_topic_id = nt.id
WHERE nd.id = ?;

-- 수신자 locale 확인 (디폴트: KOREAN)
SELECT * FROM member_setting WHERE member_id = ?;

-- file merge 중복 요청 확인 (동일 파일명 수백건이면 render 타임아웃 재시도)
SELECT customer_id, status, merged_file_name, COUNT(*) AS cnt
FROM flex.v2_file_merge
WHERE customer_id = ?
GROUP BY customer_id, status, merged_file_name
ORDER BY cnt DESC;

-- 메일 발송 확인 (mail_send_history — BEI-151 이후 기록 중단, 2026-02-20 이전 데이터만 존재)
SELECT status, requested_at FROM flex_pavement.mail_send_history
WHERE primary_recipient = ? ORDER BY requested_at DESC;
-- ⚠️ 2026-02-20 이후 메일 발송 확인은 SES 이벤트 OpenSearch (flex-prod-ses-feedback-*) 사용
```

## 과거 사례

- **문서/개인정보 변경 알림 — 권한 기반 발송**: 수신자 결정은 "문서변경 참조" 설정이 아닌 권한(`CORE_USER_ATTACHMENT_UPDATE`, `CORE_USER_PERSONAL_UPDATE`) 보유 여부. 알림을 끄려면 해당 권한 제거 안내. 개인정보 변경은 대상자 본인에게도 알림, 관리자 직접 수정 시엔 2단계 알림 스킵 — **스펙** [CI-4335]
- **승인자=참조자 중복 알림 제거**: 동일 사용자가 승인자이면서 참조자일 때 승인 알림 1건으로 통합. 참조 알림 미수신은 정상 — **스펙** [CI-3910]
- **이메일 CTA 이동 대상 차이**: `approve.refer` → 할 일, `approved.refer` → 홈피드. 클릭 시점에 승인 완료된 건은 홈피드로 리다이렉트 — **스펙** [CI-3914]
- **en/ko 템플릿 CTA URL 불일치**: 3건 발견 (`approve.refer.cta-web`, `remind.work-record.missing.one.cta-web`, `workflow.task.request-view.request.cta-web`) — **별도 버그** [CI-3914]
- **Core 알림 title_meta_map 빈값**: Core 인사정보 변경 알림(`FLEX_USER_DATA_CHANGE`)의 토픽 제목은 고정("내 정보 변경")이므로 `titleMetaMap = emptyMap()` — **스펙**. 실제 내용은 `notification.message_data_map.changedDataName`으로 확인 [CI-4122]
- **메일 미수신 — SES Delivery 확인 후 고객 안내**: 인앱 알림 정상 + Kafka produce 정상 + SES Send/Delivery 확인 → flex 측 전체 정상. 수신자 메일 서버 내부 문제. `mail_send_history`는 BEI-151로 기록 중단(2026-02-20)되었으므로 SES 이벤트 OpenSearch 사용 필수 — **고객 안내** [CI-4142]
- **메일 중복 발신 — file merge 무한 재시도**: 워크플로우 문서 일괄 다운로드(1만건) → render→impact→file 3단계에서 2단계 처리 시간 > 1단계 타임아웃 → render가 1분 주기 재시도 → file merge 요청 827건 폭증 → 매 merge 완료마다 `FLEX_FILE_STORAGE_DOWNLOAD_PREPARATION_COMPLETED` 알림 → 메일 수백통. 즉시 대응: `max.poll.interval.ms` 증가 + CPU 증설 + `v2_file_merge` TODO→DONE UPDATE. 근본: renderer 타임아웃 개선 ([EPBE-230](https://linear.app/flexteam/issue/EPBE-230)) — **버그/resolution:ops** [CI-4236]

## 메일 미수신 — 코어 런북 보강

### 진단 체크리스트 (추가)

문의: "메일이 오지 않아요" (코어 런북 관점)
1. opensearch mgmt에서 해당 email의 발송 이력 확인 (별도 권한 필요)
   - `MessageObject.mail.destination`에 문제 이메일 검색
   - EventType: Send(전송 요청 성공) → Delivery(메일 서버 전송 성공) → Bounce(수신 거부) → Open(클라이언트 확인)
2. 해당 email 도메인의 MX record 확인 → [MX Lookup](https://mxtoolbox.com/)
3. **주로 문제가 되는 케이스**:
   - 수신 메일 서버 문제 → Send만 찍히고 Delivery 없음 → MX record로 서버 상태 확인
   - 유효하지 않은 이메일로 초대메일 발송 → 즉시 suppress list 등록 → CS팀이 수동 초대메일 발송하도록 유도
4. ⚠️ flex team 내부 메일은 **Mailgun**으로 발송 → opensearch mgmt의 SES 인덱스에서 확인 불가
